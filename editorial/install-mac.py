"""Install the tested editorial source and Mac LaunchAgents; no credentials are copied."""
import argparse,datetime,json,os,plistlib,re,shutil,subprocess,sys
from pathlib import Path
from runtime import read,write

def plist(label,root,python,script,hours,mode=None,health=False):
    args=[python,str(script),'--state-dir',str(root)]
    if mode:args+=['--mode',mode]
    if health:args+=['--health']
    return {'Label':label,'ProgramArguments':args,'WorkingDirectory':str(root),'RunAtLoad':True,
        'StartCalendarInterval':[{'Hour':hour,'Minute':0} for hour in hours],
        'EnvironmentVariables':{'PATH':str(Path.home()/'.local/bin')+':/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin','TZ':'America/Guatemala'},
        'StandardOutPath':str(root/'private'/(label+'.log')),'StandardErrorPath':str(root/'private'/(label+'-error.log'))}

def social_plists(root,python,base,node):
    environment={'PATH':str(Path.home()/'.local/bin')+':/opt/homebrew/bin:/usr/bin:/bin:/usr/sbin:/sbin','TZ':'America/Guatemala'}
    result=[]
    for name,args in [('browser-relay',[node,str(base/'current/social-browser.mjs')]),
                      ('publisher',[python,str(base/'current/social.py'),'--state-dir',str(root),'run'])]:
        label='com.datogedon.social-'+name
        definition={'Label':label,'ProgramArguments':args,'WorkingDirectory':str(root),'RunAtLoad':True,
                    'EnvironmentVariables':environment,'StandardOutPath':str(root/'private'/(label+'.log')),
                    'StandardErrorPath':str(root/'private'/(label+'-error.log'))}
        if name=='browser-relay':definition.update(KeepAlive=True,ThrottleInterval=20)
        else:definition['StartCalendarInterval']=[{'Hour':hour,'Minute':12} for hour in [6,9,11,13,15,18]]
        result.append((label,definition))
    return result

def main():
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state-dir',type=Path,required=True);p.add_argument('--sha',required=True);a=p.parse_args()
    if sys.platform!='darwin':p.error('macOS required')
    source=Path(__file__).resolve().parent;repo=source.parent
    sha=subprocess.check_output(['git','rev-parse','HEAD'],cwd=repo,text=True).strip()
    if a.sha!=sha or not re.fullmatch('[a-f0-9]{40}',sha):p.error('Requested SHA must be the checked-out Git commit')
    subprocess.run(['git','diff','--quiet','HEAD','--','editorial'],cwd=repo,check=True)
    root=a.state_dir.resolve();private=root/'private';private.mkdir(parents=True,mode=0o700,exist_ok=True)
    backup=private/'config-backups'/datetime.datetime.now(datetime.timezone.utc).strftime('%Y%m%dT%H%M%SZ');backup.mkdir(parents=True,mode=0o700)
    config=read(root/'editorial-config.json');write(backup/'editorial-config.json',config)
    base=Path.home()/'.local/share/datogedon-editorial';release=base/'releases'/sha;release.mkdir(parents=True,exist_ok=True)
    for path in source.iterdir():
        if path.is_file() and path.suffix in ['.py','.txt','.mjs']:shutil.copy2(path,release/path.name)
    previous=os.readlink(base/'current') if (base/'current').is_symlink() else None
    write(backup/'release.json',{'previous':previous,'new':sha})
    temp=base/'current-next';temp.unlink(missing_ok=True);temp.symlink_to(release);os.replace(temp,base/'current')
    config['publication_schedule'].update(posts_per_day_catch_up=3,times_catch_up=['13:00','15:00','18:00'],posts_per_day_normal=1,times_normal=['13:00'],new_posts_policy='Una historia por ciclo; borrador verificado y publicación inmediata el mismo día. Conservar fechas existentes.')
    config['news_schedule']={'times':['06:00','09:00','11:00'],'author':135,'timezone':'America/Guatemala','max_posts_per_cycle':1,'publish':'immediate_after_verification','host':'macbook'}
    write(root/'editorial-config.json',config)
    definitions=[('com.datogedon.editorial-daily',[13,15,18],'experience',False),('com.datogedon.editorial-news',[6,9,11],'news',False),('com.datogedon.editorial-health',[7,10,12,14,16,19],None,True)]
    for label,hours,mode,health in definitions:
        path=Path.home()/'Library/LaunchAgents'/(label+'.plist')
        if path.exists():shutil.copy2(path,backup/path.name)
        subprocess.run(['launchctl','bootout',f'gui/{os.getuid()}/{label}'],capture_output=True)
        path.write_bytes(plistlib.dumps(plist(label,root,sys.executable,base/'current/cycles.py',hours,mode,health)))
        subprocess.run(['plutil','-lint',str(path)],check=True,capture_output=True)
        subprocess.run(['launchctl','bootstrap',f'gui/{os.getuid()}',str(path)],check=True)
    if config.get('video',{}).get('distribution',{}).get('enabled'):
        node=shutil.which('node')
        if not node:raise RuntimeError('Node is required for the browser relay')
        for label,definition in social_plists(root,sys.executable,base,node):
            path=Path.home()/'Library/LaunchAgents'/(label+'.plist')
            if path.exists():shutil.copy2(path,backup/path.name)
            subprocess.run(['launchctl','bootout',f'gui/{os.getuid()}/{label}'],capture_output=True)
            path.write_bytes(plistlib.dumps(definition));subprocess.run(['plutil','-lint',str(path)],check=True,capture_output=True)
            subprocess.run(['launchctl','bootstrap',f'gui/{os.getuid()}',str(path)],check=True)
    print(json.dumps({'installed_sha':sha,'host':'macbook','experience_hours':[13,15,18],'news_hours':[6,9,11],'news_author':135,'backup':str(backup)}))
if __name__=='__main__':main()
