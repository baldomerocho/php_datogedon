#!/usr/bin/env python3
"""Install a verified source artifact into one WordPress app; rollback on failure."""
import concurrent.futures,fcntl,hashlib,io,json,os,pwd,re,shutil,subprocess,sys,tarfile,time,urllib.request
from pathlib import Path

if os.geteuid()!=0:sys.exit('Use the restricted deployment command through sudo.')
if len(sys.argv) not in (3,4) or not re.fullmatch('[0-9a-f]{40}',sys.argv[1]):sys.exit('Expected commit SHA and artifact path.')
sha=sys.argv[1];artifact=Path(sys.argv[2]).resolve()
if not artifact.is_file() or not str(artifact).startswith('/opt/datogedon-runner/_work/'):sys.exit('Artifact outside the dedicated runner workspace.')
exercise=len(sys.argv)==4 and sys.argv[3]=='--exercise-rollback'
config=json.loads(Path('/etc/datogedon-deploy.json').read_text())
site=Path(config['site_root']).resolve();url=config['public_url'].rstrip('/');owner=int(config['owner_id'])
if not (site/'wp-config.php').is_file():sys.exit('WordPress root not found.')
account=pwd.getpwnam(config.get('site_user','runcloud'))
base=Path(config['private_root']);base.mkdir(parents=True,exist_ok=True);os.chmod(base,0o700);os.chown(base,account.pw_uid,account.pw_gid)
lock=(base/'deploy.lock').open('w');fcntl.flock(lock,fcntl.LOCK_EX)
stamp=sha+'-'+str(int(time.time()));work=base/stamp;work.mkdir(mode=0o700);os.chown(work,account.pw_uid,account.pw_gid)
release=work/'release';release.mkdir();os.chown(release,account.pw_uid,account.pw_gid)
with tarfile.open(artifact) as archive:
    size=0
    for member in archive.getmembers():
        name=member.name.removeprefix('./');size+=member.size
        if member.issym() or member.islnk() or name.startswith('/') or '..' in Path(name).parts:sys.exit('Unsafe archive member.')
        if name!='RELEASE_SHA' and not any(name==p or name.startswith(p+'/') for p in ['theme','mu-plugins','plugins','scripts','ops']):sys.exit('Unexpected archive path.')
    if size>30*1024*1024:sys.exit('Artifact too large.')
    archive.extractall(release,filter='data')
if (release/'RELEASE_SHA').read_text().strip()!=sha:sys.exit('Artifact SHA mismatch.')
# Independently verify provenance; runner workspace and archives are not trusted.
def github(path):
    request=urllib.request.Request('https://api.github.com/repos/baldomerocho/php_datogedon/'+path,headers={'User-Agent':'DatogedonDeploy/1.0','Accept':'application/vnd.github+json'})
    with urllib.request.urlopen(request,timeout=30) as response:return response.read()
head=json.loads(github('git/ref/heads/main'))
if head['object']['sha']!=sha:sys.exit('Only the current main commit may deploy.')
checks=json.loads(github('commits/'+sha+'/check-runs'))
if not any(c['name']=='validate' and c.get('conclusion')=='success' and c.get('app',{}).get('slug')=='github-actions' for c in checks['check_runs']):sys.exit('Hosted validation is not successful.')
expected={}
with tarfile.open(fileobj=io.BytesIO(github('tarball/'+sha))) as source:
    for member in source.getmembers():
        name='/'.join(Path(member.name).parts[1:])
        if member.isfile() and any(name.startswith(p+'/') for p in ['theme','mu-plugins','plugins','scripts','ops']):expected[name]=source.extractfile(member).read()
actual={str(p.relative_to(release)):p.read_bytes() for p in release.rglob('*') if p.is_file() and p.name!='RELEASE_SHA'}
if actual!=expected:sys.exit('Artifact differs from approved public source.')
for path in release.rglob('*'):
    os.chown(path,account.pw_uid,account.pw_gid)
    if path.is_file() and path.suffix=='.php':subprocess.run(['/usr/bin/php','-l',str(path)],check=True,stdout=subprocess.DEVNULL)

def wp(*args):
    result=subprocess.run(['runuser','-u',account.pw_name,'--','/usr/local/bin/wp','--path='+str(site),*map(str,args)],capture_output=True,text=True,timeout=120)
    if result.returncode:
        (work/'wp-error.log').write_text(result.stdout+'\n'+result.stderr);os.chmod(work/'wp-error.log',0o600)
        raise RuntimeError('WP-CLI failed; details retained in private journal.')
    return result.stdout.strip()
def inventory():return json.loads(wp('eval-file',release/'scripts/route-inventory.php'))
def health(path='/'):
    req=urllib.request.Request(url+path,headers={'User-Agent':'DatogedonDeploy/1.0'})
    with urllib.request.urlopen(req,timeout=20) as response:
        body=response.read();assert response.status==200 and b'<html' in body.lower()
    return True
before=inventory();previous=wp('option','get','stylesheet');(work/'routes-before.json').write_text(json.dumps(before))
journal=work/'options-before.json'
wp('eval-file',release/'scripts/config-journal.php','save',journal,owner)
mu=site/'wp-content/mu-plugins/datogedon-site.php';mu.parent.mkdir(exist_ok=True)
previous_mu=mu.read_bytes() if mu.exists() else None
plugin=site/'wp-content/plugins/datogedon-editorial-mcp'
if plugin.exists():shutil.copytree(plugin,work/'editorial-before')
theme_name='datogedon-reader-'+sha[:12]
theme_dest=site/'wp-content/themes'/theme_name
if not theme_dest.exists():shutil.copytree(release/'theme/datogedon-reader',theme_dest)
for p in theme_dest.rglob('*'):os.chown(p,account.pw_uid,account.pw_gid)
def write_mu(content):
    tmp=mu.with_suffix('.php.next');tmp.write_bytes(content);os.chown(tmp,account.pw_uid,account.pw_gid);os.replace(tmp,mu)
def purge():
    # Global object-cache flush can clear a shared Redis database or Memcached.
    # WordPress invalidates modified objects; purge only this site's HTML pages.
    wp('eval',"if(class_exists('\\LiteSpeed\\Purge') && method_exists('\\LiteSpeed\\Purge','purge_all_lscache')) \\LiteSpeed\\Purge::purge_all_lscache('Datogedon deploy');")
# Native WordPress scheduling belongs to this app's deployment, not a shared cron.
unit_names=['datogedon-wp-cron.service','datogedon-wp-cron.timer']
unit_dir=Path('/etc/systemd/system')
previous_units={name:(unit_dir/name).read_bytes() if (unit_dir/name).exists() else None for name in unit_names}
timer_enabled=subprocess.run(['systemctl','is-enabled','--quiet',unit_names[1]]).returncode==0
ops_changed=False
def apply_ops():
    global ops_changed
    required={'User='+account.pw_name,'WorkingDirectory='+str(site),'ExecStart=/usr/bin/php '+str(site/'wp-cron.php')}
    if not required.issubset(set((release/'ops'/unit_names[0]).read_text().splitlines())):raise RuntimeError('Native cron unit does not target this WordPress application.')
    subprocess.run(['systemd-analyze','verify',*[str(release/'ops'/name) for name in unit_names]],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    for name in unit_names:
        content=(release/'ops'/name).read_bytes()
        if content!=previous_units[name]:
            temporary=unit_dir/(name+'.next');temporary.write_bytes(content);os.chmod(temporary,0o644);os.replace(temporary,unit_dir/name);ops_changed=True
    if ops_changed:subprocess.run(['systemctl','daemon-reload'],check=True)
    subprocess.run(['systemctl','enable','--now',unit_names[1]],check=True,stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    if ops_changed:subprocess.run(['systemctl','restart',unit_names[1]],check=True)
    subprocess.run(['systemctl','is-active','--quiet',unit_names[1]],check=True)
def restore_ops():
    if not ops_changed:return
    for name,content in previous_units.items():
        if content is None:(unit_dir/name).unlink(missing_ok=True)
        else:(unit_dir/name).write_bytes(content)
    subprocess.run(['systemctl','daemon-reload'],check=True)
    if timer_enabled:subprocess.run(['systemctl','restart',unit_names[1]],check=True)
    else:subprocess.run(['systemctl','disable','--now',unit_names[1]],check=True)
started=time.time();result={'sha':sha,'previous_theme':previous,'artifact_sha256':hashlib.sha256(artifact.read_bytes()).hexdigest(),'started_at':started}
try:
    apply_ops()
    write_mu((release/'mu-plugins/datogedon-site.php').read_bytes())
    # Existing editorial integration stays live; update individual PHP files atomically.
    for source in (release/'plugins/datogedon-editorial-mcp').rglob('*'):
        if source.is_file():
            dest=plugin/source.relative_to(release/'plugins/datogedon-editorial-mcp');dest.parent.mkdir(parents=True,exist_ok=True)
            tmp=dest.with_suffix(dest.suffix+'.next');shutil.copy2(source,tmp);os.chown(tmp,account.pw_uid,account.pw_gid);os.replace(tmp,dest)
    wp('theme','activate',theme_name)
    wp('user','update',owner,'--display_name='+config['owner_name'],'--description='+config['owner_description'])
    wp('datogedon','configure','--owner='+str(owner))
    after=inventory();new={p['id']:p['url'] for p in after['posts']}
    assert all(new.get(p['id'])==p['url'] for p in before['posts']),'Existing permalinks changed.'
    (work/'routes-after.json').write_text(json.dumps(after))
    purge()
    if exercise:raise RuntimeError('Intentional health failure to exercise rollback.')
    paths=['/','/temas/','/acerca-de/','/experiencias-con-ia/']
    from urllib.parse import urlsplit
    paths += [urlsplit(p['url']).path for p in before['posts'] if p['status']=='publish']
    list(concurrent.futures.ThreadPoolExecutor(max_workers=4).map(health,paths))
    result.update(status='healthy',checked_paths=len(paths),preserved_routes=len(before['posts']),active_theme=theme_name,native_cron_timer='active')
except Exception as error:
    restore_ops()
    result['failure']=str(error)
    wp('theme','activate',previous)
    wp('eval-file',release/'scripts/config-journal.php','restore',journal,owner)
    if previous_mu is None:mu.unlink(missing_ok=True)
    else:write_mu(previous_mu)
    if (work/'editorial-before').exists():
        for source in (work/'editorial-before').rglob('*'):
            if source.is_file():shutil.copy2(source,plugin/source.relative_to(work/'editorial-before'))
    purge();health()
    result.update(status='rollback_verified',active_theme=previous)
    (base/'last-deployment.json').write_text(json.dumps(result,indent=2))
    if exercise:print('ROLLBACK_TEST_OK');sys.exit(0)
    raise
result['finished_at']=time.time();(base/'last-deployment.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
