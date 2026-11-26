"""Durable Mac publishing outbox. Browser work is separate from article generation."""
import argparse,contextlib,fcntl,hashlib,json,os,re,shutil,signal,subprocess,sys
from datetime import datetime,timedelta
from pathlib import Path
from urllib.request import Request,urlopen
from runtime import read,write,now,WordPress,notify
PLATFORMS=('tiktok','youtube','instagram')
CHANNEL='UCUEIkqP0ZYY7R7GEV5wwhvA'
TERMINAL={'published','scheduled'}

def location(root):return Path(root)/'videos/distribution'
@contextlib.contextmanager
def locked(root):
    folder=location(root);folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    with (folder/'state.lock').open('a+') as stream:
        fcntl.flock(stream,fcntl.LOCK_EX);yield folder

def canonical(platform,url):
    patterns={'tiktok':r'https://www\.tiktok\.com/@datogedon/video/[0-9]+',
              'youtube':r'https://www\.youtube\.com/shorts/[A-Za-z0-9_-]{11}',
              'instagram':r'https://www\.instagram\.com/datogedon/reel/[A-Za-z0-9_-]+/'}
    return bool(re.fullmatch(patterns[platform],url or ''))

def enqueue(root,post,video,kind):
    config=read(root/'editorial-config.json',{}).get('video',{}).get('distribution',{})
    if not config.get('enabled'):return {'status':'disabled'}
    if post['status']!='publish' or video.get('status')!='ready_for_review':raise ValueError('Published article and verified video required')
    if post['id']!=video['post_id'] or post['link']!=video['article_url']:raise ValueError('Video/article mismatch')
    path=Path(video['output'])/'video.mp4'
    if not path.is_file() or hashlib.sha256(path.read_bytes()).hexdigest()!=video['video_sha256']:raise ValueError('Video integrity check failed')
    with locked(root) as folder:
        outbox=read(folder/'outbox.json',{'jobs':{}});key=str(post['id'])
        if key in outbox['jobs']:
            if outbox['jobs'][key]['video_sha256']!=video['video_sha256']:raise ValueError('Existing distribution uses another master')
            return outbox['jobs'][key]
        platforms={}
        for platform in PLATFORMS:
            prior=video.get('platforms',{}).get(platform,video.get(platform,{}))
            platforms[platform]=dict(prior) if prior.get('status') in TERMINAL else {'status':'pending','attempts':0}
        job={'post_id':post['id'],'title':post['title'].get('raw',post['title'].get('rendered','')),'article_url':post['link'],
             'kind':kind,'output':video['output'],'video_sha256':video['video_sha256'],'created_at':now().isoformat(),'platforms':platforms}
        outbox['jobs'][key]=job;write(folder/'outbox.json',outbox)
    return job

def wake(root):
    # The durable outbox is committed before this best-effort local signal.
    try:return subprocess.run(['launchctl','kickstart',f'gui/{os.getuid()}/com.datogedon.social-publisher'],capture_output=True,timeout=10).returncode==0
    except (OSError,subprocess.TimeoutExpired):return False

def record(root,post_id,platform,status,url=None,proof=None,reason=None):
    if platform not in PLATFORMS or status not in ['draft','submitted','published','blocked','uncertain']:raise ValueError('Unsupported result')
    if url and not canonical(platform,url):raise ValueError('Unexpected video URL')
    if status=='published':
        if not url or not proof:raise ValueError('Public URL and browser evidence required')
        for field in ['owner_verified','public_verified','ai_label_verified','caption_verified','playback_verified']:
            if proof.get(field) is not True:raise ValueError('Missing browser verification: '+field)
        if platform=='youtube' and proof.get('channel_id')!=CHANNEL:raise ValueError('Wrong YouTube channel')
        if platform!='youtube' and proof.get('account')!='@datogedon':raise ValueError('Wrong social account')
        artifact=Path(proof.get('snapshot_path','')).resolve();review=(Path.home()/'Movies/Datogedon/review').resolve()
        if not artifact.is_relative_to(review) or not artifact.is_file():raise ValueError('Browser proof snapshot required')
    with locked(root) as folder:
        outbox=read(folder/'outbox.json');entry=outbox['jobs'][str(post_id)]['platforms'][platform]
        if entry.get('url') and url and entry['url']!=url:raise ValueError('Remote URL differs; reconcile without uploading again')
        if entry['status']=='published' and status!='published':raise ValueError('Published result is immutable')
        entry.update(status=status,updated_at=now().isoformat())
        if url:entry['url']=url
        if proof:entry['proof']=proof
        if reason:entry['reason']=reason
        if status=='blocked':entry.update(retryable=False)
        if status=='published':entry.update(published=True,blog_reference='pending')
        write(folder/'outbox.json',outbox)
    return entry

def eligible(entry):
    if entry.get('status')=='pending':return True
    if entry.get('status') in ['in_progress','draft','submitted','uncertain']:
        return entry.get('attempts',0)<3 and now()>=datetime.fromisoformat(entry.get('next_attempt_at','1970-01-01T00:00:00+00:00'))
    return False

def command(work,root):
    codex=shutil.which('codex')
    if not codex:raise RuntimeError('Codex is unavailable')
    return [codex,'-c','default_permissions="datogedon-social"','-c','permissions.datogedon-social.extends=":workspace"',
            '-c','permissions.datogedon-social.network.enabled=true','exec','--skip-git-repo-check','--ephemeral',
            '-C',str(work),'--add-dir',str(location(root)),'--add-dir',str(Path.home()/'Movies/Datogedon/review'),
            '--color','never','-o',str(work/'last-result.txt'),'-']

def verify_article(job,wp):
    post=wp.get(f"posts/{job['post_id']}?context=edit")[0]
    if post['status']!='publish' or post['link']!=job['article_url']:raise ValueError('Article is not public at its expected URL')
    date=datetime.fromisoformat(post.get('date_gmt','1970-01-01T00:00:00')).replace(tzinfo=now().tzinfo)
    if date>now():raise ValueError('Article publication is in the future')
    req=Request(job['article_url'],headers={'User-Agent':'DatogedonEditorial/2.0'})
    with urlopen(req,timeout=30) as response:
        if response.status!=200:raise ValueError('Article permalink is unavailable')
    return post

def link_references(root):
    folder=location(root);jobs=read(folder/'outbox.json',{'jobs':{}})['jobs']
    for key,job in jobs.items():
        for platform,entry in job['platforms'].items():
            if entry.get('status')!='published' or entry.get('blog_reference')=='linked':continue
            result=subprocess.run([sys.executable,str(Path(__file__).with_name('link-video.py')),'--post-id',key,'--video-url',entry['url'],'--state-dir',str(root),'--confirmed-public','--apply'],capture_output=True,text=True,timeout=90)
            with locked(root):
                latest=read(folder/'outbox.json');target=latest['jobs'][key]['platforms'][platform]
                target['blog_reference']='linked' if result.returncode==0 else 'pending';write(folder/'outbox.json',latest)

def sync_receipts(root):
    """Mirror confirmed receipts without replacing another render's queue entry."""
    jobs=read(location(root)/'outbox.json',{'jobs':{}})['jobs']
    queue_path=root/'videos/queue.json'
    with queue_path.with_name('queue-state.lock').open('a+') as lock:
        fcntl.flock(lock,fcntl.LOCK_EX);queue=read(queue_path,{'jobs':{}})
        for key,job in jobs.items():
            target=queue['jobs'].get(key)
            if not target or target.get('video_sha256')!=job['video_sha256']:continue
            for platform,entry in job['platforms'].items():
                if entry['status'] in ['pending','in_progress']:continue
                target.setdefault('platforms',{})[platform]=dict(entry)
            target['published']=any(e.get('status')=='published' for e in target.get('platforms',{}).values())
            write(Path(job['output'])/'automatic-distribution.json',job)
        write(queue_path,queue)

def run(root):
    folder=location(root);folder.mkdir(parents=True,exist_ok=True,mode=0o700)
    lock=(folder/'worker.lock').open('a+')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:return {'status':'busy'}
    with lock:
        config=read(root/'editorial-config.json',{}).get('video',{}).get('distribution',{})
        if not config.get('enabled'):return {'status':'disabled'}
        wp=WordPress(Path.home()/'.local/share/datogedon-mcp/credentials.json')
        processed=[]
        try:link_references(root)
        except Exception:pass
        sync_receipts(root)
        while True:
            jobs=read(folder/'outbox.json',{'jobs':{}})['jobs']
            candidates=[j for j in jobs.values() if any(eligible(e) for e in j['platforms'].values())]
            if not candidates:break
            job=candidates[0];key=str(job['post_id']);work=folder/key;work.mkdir(mode=0o700,exist_ok=True)
            try:
                verify_article(job,wp)
                video=Path(job['output'])/'video.mp4'
                if hashlib.sha256(video.read_bytes()).hexdigest()!=job['video_sha256']:raise ValueError('Master changed after enqueue')
                # Open the correct Chrome profile outside the child workspace sandbox.
                opener=Path.home()/'.local/share/datogedon-browser/open-datogedon.mjs'
                subprocess.run(['node',str(opener),'https://studio.youtube.com/','https://www.instagram.com/datogedon/','https://www.tiktok.com/tiktokstudio/content'],check=True,capture_output=True,timeout=30)
                selected={}
                with locked(root):
                    latest=read(folder/'outbox.json');current=latest['jobs'][key]
                    for platform,entry in current['platforms'].items():
                        if not eligible(entry):continue
                        selected[platform]={'mode':'upload_if_absent' if entry['status']=='pending' else 'reconcile_only','previous':dict(entry)}
                        entry.update(status='in_progress',attempts=entry.get('attempts',0)+1,started_at=now().isoformat(),next_attempt_at=(now()+timedelta(minutes=20)).isoformat())
                    write(folder/'outbox.json',latest)
                write(work/'job.json',{**job,'selected_platforms':selected})
                source=Path(__file__).resolve().parent
                prompt=(source/'social-publication.txt').read_text()+f'\n\nEJECUCIÓN AUTOMÁTICA AUTORIZADA\nLee job.json. Publica únicamente post_id={key} en selected_platforms. No necesitas aprobación humana. No generes ni modifiques videos/artículos.\nBrowser helper: {sys.executable} {source/"browser-call.py"} JSON\nJSON ejemplo: {{"tool":"list_pages","args":{{}}}}. Para schemas: {{"operation":"tools","names":["click","upload_file"]}}.\nRegistrar resultado: {sys.executable} {source/"social.py"} --state-dir {root} record --post-id {key} --platform PLATFORM --status STATUS [--url URL] [--proof ARCHIVO_JSON] [--reason TEXTO]\nPruebas UI en ~/Movies/Datogedon/review/social-{key}-PLATFORM.txt.\nNo edites outbox.json directamente. Cada plataforma es independiente; registrar su resultado antes de pasar a la siguiente. Si mode=reconcile_only, está prohibido subir de nuevo: localizar/publicar el mismo borrador o verificar URL ya asignada. Si la sesión no permite confirmar identidad, registra blocked y sigue con otras plataformas.\nPrimero consulta list_pages en el relay. No inicies otro session.mjs ni otro Chrome MCP. No leas archivos de claves, cookies, conversaciones ni sesiones de asistentes. Antes de CARGAR registra draft sin URL; desde ese momento un corte exige conciliación, nunca una segunda carga. Guardar URL tan pronto esté asignada. Todo publicado requiere proof.json con owner_verified/public_verified/ai_label_verified/caption_verified/playback_verified=true y snapshot_path existente; YouTube channel_id verificado, otros account=@datogedon. No inventes pruebas.\nSi encuentras video ya publicado aunque el registro local no lo conozca, verifica y registra el existente sin duplicarlo. Si no puedes resolver una plataforma, registra blocked con la causa exacta y sigue; no abandones las demás.\n'
                with (work/'worker.log').open('a') as log:
                    os.chmod(log.name,0o600);process=subprocess.Popen(command(work,root),stdin=subprocess.PIPE,stdout=log,stderr=log,text=True,start_new_session=True)
                    try:process.communicate(prompt,timeout=2100)
                    except subprocess.TimeoutExpired:
                        os.killpg(process.pid,signal.SIGTERM)
                        try:process.wait(timeout=10)
                        except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
                with locked(root):
                    latest=read(folder/'outbox.json')
                    for platform in selected:
                        entry=latest['jobs'][key]['platforms'][platform]
                        if entry['status']=='in_progress':entry.update(status='uncertain',reason='Worker ended without a confirmed platform receipt')
                    write(folder/'outbox.json',latest)
                processed.append(key)
            except Exception as error:
                with locked(root):
                    latest=read(folder/'outbox.json')
                    for entry in latest['jobs'][key]['platforms'].values():
                        if entry['status']=='pending':entry.update(status='blocked',reason=type(error).__name__+': '+str(error),retryable=False)
                        elif entry['status']=='in_progress':entry.update(status='uncertain',reason=type(error).__name__)
                    write(folder/'outbox.json',latest)
                processed.append(key)
            # A failed reference update must not undo a confirmed platform publication.
            try:link_references(root)
            except Exception:pass
            sync_receipts(root)
        jobs=read(folder/'outbox.json',{'jobs':{}})['jobs'];pending=[{'post_id':key,'platform':p,'status':e['status'],'reason':e.get('reason')} for key,j in jobs.items() for p,e in j['platforms'].items() if e['status'] not in TERMINAL or e.get('status')=='published' and e.get('blog_reference')!='linked']
        report={'checked_at':now().isoformat(),'processed':processed,'pending':pending,'status':'pending' if pending else 'ok'};write(folder/'status.json',report)
        if pending:notify(root,'social_pending','Hay videos pendientes de distribución. Revisa videos/distribution/status.json.')
        return report

if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state-dir',type=Path,required=True);sub=p.add_subparsers(dest='action',required=True)
    sub.add_parser('run');q=sub.add_parser('record');q.add_argument('--post-id',type=int,required=True);q.add_argument('--platform',choices=PLATFORMS,required=True);q.add_argument('--status',required=True);q.add_argument('--url');q.add_argument('--proof',type=Path);q.add_argument('--reason')
    a=p.parse_args();root=a.state_dir.resolve()
    result=run(root) if a.action=='run' else record(root,a.post_id,a.platform,a.status,a.url,read(a.proof) if a.proof else None,a.reason)
    print(json.dumps(result,ensure_ascii=False))
