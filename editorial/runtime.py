"""Private daily editorial orchestration. No evidence or credentials belong in Git."""
import argparse,base64,fcntl,json,os,re,shlex,shutil,signal,subprocess,sys,tempfile
from collections import Counter
from datetime import datetime,timedelta,timezone
from html.parser import HTMLParser
from pathlib import Path
from urllib.request import Request,urlopen
from zoneinfo import ZoneInfo
from collector import collect

TZ=ZoneInfo('America/Guatemala')
def now():return datetime.now(timezone.utc)
def write(path,value):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    fd,name=tempfile.mkstemp(dir=path.parent,prefix='.'+path.name)
    try:
        os.fchmod(fd,0o600)
        with os.fdopen(fd,'w') as stream:json.dump(value,stream,ensure_ascii=False,indent=2)
        os.replace(name,path)
    finally:
        if os.path.exists(name):os.unlink(name)
def read(path,default=None):
    try:return json.loads(Path(path).read_text())
    except FileNotFoundError:return default

def cycle_context(root):return read(root/'private/cycle-context.json',{}) or {}
def success_path(root):
    key=cycle_context(root).get('key')
    if key and re.fullmatch(r'[a-z0-9:-]+',key):return root/'private/cycle-success'/(key+'.json')
    return root/'private/last-success.json'

def merge_sources(fresh,archived):
    merged={}
    for host,items,is_fresh in [('macbook',fresh,True),*[(host,items,False) for host,items in archived]]:
        for entry in items:
            item=dict(entry);item['source_host']=host;item['source_hosts']=[host]
            item['source_freshness']={host:is_fresh};item['archived_only']=not is_fresh
            old=merged.get(item['key'])
            if old:
                # Newest activity wins; verbosity is only a tiebreaker, never freshness.
                score=lambda x:(x['last_event'],len(json.dumps(x.get('assistant_text',[])))+len(json.dumps(x.get('user_text_candidates',[]))))
                chosen=item if score(item)>score(old) else old
                chosen=dict(chosen);chosen['source_hosts']=sorted(set(old['source_hosts'])|{host})
                chosen['source_freshness']={**old['source_freshness'],host:is_fresh}
                chosen['archived_only']=not any(chosen['source_freshness'].values())
                item=chosen
            merged[item['key']]=item
    return sorted(merged.values(),key=lambda x:x['last_event'],reverse=True)

def next_slots(posts,current,catch_up=True,limit=2):
    times=['08:00','16:00'] if catch_up else ['08:00'];daily_cap=len(times)
    occupied=set();counts=Counter()
    for post in posts:
        if post['status'] not in ['publish','future']:continue
        date=datetime.fromisoformat(post['date']).replace(tzinfo=TZ)
        counts[date.date()]+=1;occupied.add(date)
    slots=[];start=current.astimezone(TZ)
    for offset in range(90):
        day=start.date()+timedelta(days=offset)
        for clock in times:
            candidate=datetime.combine(day,datetime.strptime(clock,'%H:%M').time(),tzinfo=TZ)
            if candidate<current.astimezone(TZ)+timedelta(minutes=30) or candidate in occupied or counts[day]>=daily_cap:continue
            slots.append(candidate.strftime('%Y-%m-%d %H:%M:%S'));counts[day]+=1
            if len(slots)>=limit:return slots
    raise RuntimeError('No hay horarios libres en 90 días')

class Body(HTMLParser):
    def __init__(self):super().__init__();self.text=[];self.images=[];self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ['script','style']:self.skip+=1
        if tag=='img':self.images.append(dict(attrs))
    def handle_endtag(self,tag):
        if tag in ['script','style'] and self.skip:self.skip-=1
    def handle_data(self,text):
        if not self.skip:self.text.append(text)
def quality(post,media,kind="experience"):
    parser=Body();parser.feed(post['content'].get('raw',post['content'].get('rendered','')))
    words=len(re.findall(r'\b[\wáéíóúñü]+\b',' '.join(parser.text),re.I));problems=[]
    if not ((80<=words<=1600) if kind=='news' else (400<=words<=650)):problems.append('extensión fuera de rango editorial')
    thumb=media.get(post.get('featured_media'));details=(thumb or {}).get('media_details',{})
    if not thumb or thumb.get('mime_type')!='image/webp' or details.get('width')!=1200 or details.get('height')!=630 or not thumb.get('alt_text'):problems.append('miniatura o metadatos incompletos')
    size=details.get('filesize',0)
    if not isinstance(size,int) or size<=0:problems.append('tamaño de miniatura no verificado')
    if size>180*1024:problems.append('miniatura supera 180 KB')
    if not post.get('excerpt',{}).get('raw',post.get('excerpt',{}).get('rendered','')).strip():problems.append('extracto ausente')
    if not post.get('categories'):problems.append('categoría ausente')
    if any(not img.get('alt') for img in parser.images):problems.append('imagen interior sin alt')
    if re.search(r'(?i)(?:/Users/|/home/|/Volumes/|\b(?:sk-proj-|ghp_|github_pat_)[A-Za-z0-9_-]{20,}|-----BEGIN .*PRIVATE KEY)', ' '.join(parser.text)):problems.append('posible dato privado')
    return {'words':words,'inline_images':len(parser.images),'problems':problems}

class WordPress:
    def __init__(self,credentials):
        c=read(credentials);self.auth='Basic '+base64.b64encode((c['username']+':'+c['password']).encode()).decode()
    def get(self,resource):
        req=Request('https://datogedon.com/wp-json/wp/v2/'+resource,headers={'Authorization':self.auth,'User-Agent':'DatogedonEditorial/2.0'})
        with urlopen(req,timeout=30) as response:return json.load(response),int(response.headers.get('X-WP-TotalPages','1'))
    def posts(self,status,after=''):
        result=[];page=1
        while True:
            query=f'posts?context=edit&status={status}&per_page=100&page={page}&_fields=id,status,date,date_gmt'
            if after:query+='&after='+after
            data,pages=self.get(query);result+=data
            if page>=pages:return result
            page+=1

def reconcile(root,wp):
    queue=read(root/'queue.json');snapshot=[];issues=[];media={}
    for item in queue['posts']:
        post,_=wp.get(f"posts/{int(item['post_id'])}?context=edit")
        old=item.get('status');item['status']={'publish':'published','future':'scheduled'}.get(post['status'],post['status'])
        item['remote_status']=post['status'];item['remote_checked_at']=now().isoformat();item['remote_date']=post['date'].replace('T',' ')
        if item.get('date') and item['date']!=item['remote_date']:issues.append({'post_id':post['id'],'issue':'fecha remota distinta; no se modificó'})
        if post['status']=='future':
            if post['featured_media'] and post['featured_media'] not in media:media[post['featured_media']]=wp.get(f"media/{post['featured_media']}?context=edit")[0]
            check=quality(post,media);item['quality_check']=check
            issues.extend({'post_id':post['id'],'issue':x} for x in check['problems'])
            if datetime.fromisoformat(post['date_gmt']).replace(tzinfo=timezone.utc)<now()-timedelta(minutes=10):issues.append({'post_id':post['id'],'issue':'publicación vencida en WordPress'})
        snapshot.append({k:post[k] for k in ['id','status','date','date_gmt','featured_media']})
    write(root/'queue.json',queue)
    day=now().astimezone(TZ).date().isoformat()
    calendar=wp.posts('future')+wp.posts('publish',day+'T00:00:00')
    config=read(root/'editorial-config.json');catch_up=config['publication_schedule']['catch_up']
    cycle=cycle_context(root)
    cyclic=bool(cycle or config.get('news_schedule'))
    slots=[] if cyclic else next_slots(calendar,now(),catch_up,2 if catch_up else 1)
    counts=Counter(p['date'][:10] for p in calendar if p['status'] in ['publish','future'])
    # Preserve existing dates; report collisions rather than silently rescheduling them.
    issues.extend({'date':d,'issue':'más publicaciones que el límite diario'} for d,c in counts.items() if c>2 and not cyclic)
    result={'checked_at':now().isoformat(),'posts':snapshot,'next_slots':slots,'calendar':calendar,'issues':issues,'cycle':cycle}
    write(root/'private/editorial-calendar.json',result);return result

def notify(root,code,message):
    stamp=now().astimezone(TZ).date().isoformat()+':'+code
    previous=read(root/'private/last-alert.json',{})
    sent=[key for key in previous.get('sent',[]) if key.startswith(stamp[:10]+':')]
    if stamp in sent:return
    # Local operating-system alert, never email, chat or an external recipient.
    script='on run argv\n display notification (item 1 of argv) with title "Datogedon editorial"\nend run'
    try:requested=subprocess.run(['osascript','-e',script,message],capture_output=True,text=True).returncode==0
    except OSError:requested=False
    write(root/'private/last-alert.json',{'key':stamp,'sent':sent+[stamp],'at':now().isoformat(),'notification_requested':requested,'message':message})

def execute(root,args):
    private=root/'private';private.mkdir(mode=0o700,exist_ok=True);os.chmod(private,0o700)
    current=now().astimezone(TZ);day=current.date().isoformat();config=read(root/'editorial-config.json')
    cycle=cycle_context(root)
    if not cycle and not any([args.force,args.health,args.verify_only,args.collect_only]) and current.hour<13:
        write(private/'last-wakeup.json',{'at':now().isoformat(),'stage':'not_due'});return 0
    success=read(success_path(root),{})
    if success.get('date')==day and not any([args.force,args.health,args.verify_only,args.collect_only]):
        report={'at':now().isoformat(),'stage':'already_completed','verified_post_ids':success['post_ids']}
        write(private/'last-wakeup.json',report);print(json.dumps(report));return 0
    lock=(private/'worker.lock').open('w')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:
        lock.close()
        started=read(root/'daily-status.json',{}).get('started_at')
        if args.health and started and now()-datetime.fromisoformat(started)>timedelta(hours=1):notify(root,'still_running','El proceso editorial lleva más de una hora activo; revisa su estado local.')
        return 0
    try:return _locked(root,args,current,day,config,private)
    finally:lock.close()

def _locked(root,args,current,day,config,private):
    if args.health or args.verify_only:
        snapshot=reconcile(root,WordPress(args.credentials));issues=list(snapshot['issues'])
        success=read(success_path(root),{})
        if args.adopt_today:
            previous=read(root/'daily-status.json',{})
            scheduled=previous.get('editorial',{}).get('scheduled',[])
            ids={p['id'] for p in snapshot['posts'] if p['status'] in ['publish','future']}
            completed=datetime.fromisoformat(previous.get('finished_at','1970-01-01T00:00:00+00:00')).astimezone(TZ).date().isoformat()==day
            if not completed or previous.get('worker_exit_code')!=0 or not scheduled or not all(p['post_id'] in ids for p in scheduled) or issues:raise RuntimeError('La ejecución anterior no cumple los requisitos para adoptarla')
            success={'date':day,'verified_at':now().isoformat(),'post_ids':[p['post_id'] for p in scheduled],'kind':'adopted_verified_run'};write(success_path(root),success)
        if args.health and current.hour>=14 and success.get('date')!=day:issues.append({'issue':'no hay ejecución verificada de hoy'})
        future=[p for p in snapshot['posts'] if p['status']=='future']
        if not future and not cycle:issues.append({'issue':'no hay entradas futuras en la cola'})
        report={'checked_at':now().isoformat(),'healthy':not issues,'future_posts':len(future),'next_slots':snapshot['next_slots'],'issues':issues}
        write(root/'editorial-health.json',report)
        if issues:notify(root,'health_failed','Hay un problema en la cola editorial. Revisa editorial-health.json.');return 1
        print(json.dumps(report));return 0
    status={'started_at':now().isoformat(),'sources':{},'stage':'collecting'};write(root/'daily-status.json',status)
    try:
        cycle=cycle_context(root)
        if cycle.get('mode')!='news':
            fresh=collect()['sessions']
            if not fresh:raise RuntimeError('La fuente local no devolvió sesiones; se conserva el archivo anterior')
            write(private/'macbook-evidence.json',{'sessions':fresh})
            archived=[]
            for source in config.get('archived_sources',[]):
                bundle=read(root/source['evidence_file'],{'sessions':[]});archived.append((source['id'],bundle['sessions']))
            sessions=merge_sources(fresh,archived);write(private/'evidence.json',{'sessions':sessions})
            index=[]
            for item in sessions:
                write(private/'sessions'/(item['key']+'.json'),item)
                index.append({k:item[k] for k in ['key','first_event','last_event','project_key','source_digest','source_hosts','archived_only']})
            write(private/'evidence-index.json',index)
            status.update(sources={'macbook':{'ok':True,'sessions':len(fresh)}},unique_sessions=len(sessions),archived_sources=[h for h,_ in archived],stage='collected')
            if args.collect_only:write(root/'daily-status.json',status);return 0
        else:
            status.update(stage='researching',sources={'web':{'required':True}})
        wp=WordPress(args.credentials);before=reconcile(root,wp)
        if before['issues']:raise RuntimeError('La cola necesita revisión antes de generar nuevas entradas')
        success=read(success_path(root),{})
        if not args.force and success.get('date')==day:
            status.update(stage='already_completed',status='ok',verified_post_ids=success['post_ids']);write(root/'daily-status.json',status);print(json.dumps(status));return 0
        snapshot={'checked_at':now().isoformat()}
        for taxonomy in ['categories','tags']:
            items=[];page=1
            while True:
                data,pages=wp.get(f'{taxonomy}?per_page=100&page={page}&_fields=id,name,slug');items+=data
                if page>=pages:break
                page+=1
            snapshot[taxonomy]=items
        write(root/'wordpress-taxonomies.json',snapshot)
        status['stage']='writing';write(root/'daily-status.json',status)
        original_ids={p['id'] for p in before['posts'] if not cycle or p['status']!='draft'};command=shutil.which('codex')
        if not command:raise RuntimeError('Codex no está en PATH')
        prompt=(root/('NEWS-TASK.txt' if cycle.get('mode')=='news' else 'DAILY-TASK.txt')).read_text().replace('{{CHECK_POST}}',shlex.join([sys.executable,str(Path(__file__).with_name('check-post.py'))]))+('\nLee private/cycle-context.json: una entrada como máximo, publicación en este ciclo y fecha local de hoy; no reserves días futuros.\n' if cycle else '\nConsulta private/editorial-calendar.json; usa solo sus next_slots para nuevas entradas. No cambies fechas existentes.\n')
        prompt+='\n'+Path(__file__).with_name('common-task.txt').read_text().replace('{{CHECK_POST}}',shlex.join([sys.executable,str(Path(__file__).with_name('check-post.py'))])).replace('{{LINK_CHECK}}',shlex.join([sys.executable,str(Path(__file__).with_name('internal_links.py'))]))
        from internal_links import catalog
        if cycle:write(private/'internal-link-catalog.json',catalog(wp))
        with (private/'worker.log').open('a') as log:
            os.chmod(private/'worker.log',0o600)
            process=subprocess.Popen([command,*(['--search'] if cycle.get('mode')=='news' else []),'exec','--skip-git-repo-check','-C',str(root),'-s','workspace-write','--color','never','-o',str(private/'last-editorial-run.txt'),'-'],stdin=subprocess.PIPE,stdout=log,stderr=log,text=True,start_new_session=True)
            try:process.communicate(prompt,timeout=2700)
            except subprocess.TimeoutExpired:
                os.killpg(process.pid,signal.SIGTERM)
                try:process.wait(timeout=10)
                except subprocess.TimeoutExpired:os.killpg(process.pid,signal.SIGKILL);process.wait()
                raise RuntimeError('La redacción superó 45 minutos; verificar antes de reintentar')
        after=reconcile(root,wp);new=[p for p in after['posts'] if p['id'] not in original_ids]
        latest=read(root/'daily-status.json',{})
        if latest.get('editorial'):status['editorial']=latest['editorial']
        if cycle:
            from internal_links import audit
            if len(new)>1:raise RuntimeError('Más de una entrada en el ciclo')
            for summary in new:
                post=wp.get(f"posts/{summary['id']}?context=edit")[0]
                media={post['featured_media']:wp.get(f"media/{post['featured_media']}?context=edit")[0]} if post.get('featured_media') else {}
                check=quality(post,media,cycle['mode'])
                if post['status']!='publish' or post['date'][:10]!=day or (cycle['mode']=='news' and post['author']!=135) or check['problems'] or audit(post,catalog(wp))['problems']:raise RuntimeError('Publicación del ciclo no verificada')
        elif any(p['status']!='future' or p['date'].replace('T',' ') not in before['next_slots'] for p in new):raise RuntimeError('No se pudo verificar una nueva programación completa')
        if process.returncode or after['issues']:raise RuntimeError('El ciclo editorial no terminó correctamente')
        if not new:
            reviewed=read(root/'queue.json').get('evidence_review',{}).get('reviewed_at','')
            if latest.get('status')!='no_story' or not latest.get('reason') or not reviewed or datetime.fromisoformat(reviewed)<datetime.fromisoformat(status['started_at']):raise RuntimeError('La ejecución terminó sin programación ni revisión nueva verificable')
        write(success_path(root),{'date':day,'verified_at':now().isoformat(),'post_ids':[p['id'] for p in new],'kind':'worker_verified' if new else 'reviewed_no_story'})
        status.update(stage='verified' if new else 'reviewed_no_story',status='ok',scheduled=new,worker_exit_code=0)
    except Exception as error:
        status.update(stage='failed',status='blocked',reason=str(error) if isinstance(error,RuntimeError) else type(error).__name__)
        notify(root,'run_failed','La ejecución editorial falló. Revisa daily-status.json; se conservó el progreso.')
    status['finished_at']=now().isoformat();write(root/'daily-status.json',status)
    with (root/'run-history.jsonl').open('a') as stream:os.chmod(root/'run-history.jsonl',0o600);stream.write(json.dumps(status)+'\n')
    print(json.dumps(status));return 0 if status.get('status')=='ok' else 1

def main():
    parser=argparse.ArgumentParser(description=__doc__);parser.add_argument('--state-dir',required=True,type=Path)
    parser.add_argument('--credentials',type=Path,default=Path.home()/'.local/share/datogedon-mcp/credentials.json')
    for flag in ['collect-only','verify-only','adopt-today','health','force']:parser.add_argument('--'+flag,action='store_true')
    args=parser.parse_args();root=args.state_dir.resolve()
    try:return execute(root,args)
    except Exception as error:
        report={'checked_at':now().isoformat(),'healthy':False,'reason':str(error) if isinstance(error,RuntimeError) else type(error).__name__};write(root/'editorial-health.json',report)
        notify(root,'preflight_failed','No se pudo comprobar el flujo editorial. Revisa editorial-health.json.');return 1
if __name__=='__main__':sys.exit(main())
