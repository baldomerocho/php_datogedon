"""Mac-only editorial windows. One durable attempt per window; no missed-slot bursts."""
import argparse,fcntl,json,os,sys
from argparse import Namespace
from datetime import datetime,timedelta
from pathlib import Path
from runtime import TZ,now,read,write,execute,notify
HOURS={'experience':[13,15,18],'news':[6,9,11]}
def due(current,mode,catch_up=True):
    current=current.astimezone(TZ)
    hours=HOURS[mode] if mode=='news' or catch_up else [13]
    eligible=[current.replace(hour=h,minute=0,second=0,microsecond=0) for h in hours if h<=current.hour]
    if not eligible:return None
    slot=max(eligible)
    if current-slot>timedelta(minutes=75 if mode=='news' else 120):return None
    return {'key':slot.strftime('%Y-%m-%d')+':'+mode+':'+slot.strftime('%H%M'),'mode':mode,'slot':slot.isoformat(),'day':slot.date().isoformat(),'author':135 if mode=='news' else None,'publication':'publish_after_checks_same_day','max_posts':1}

def run(root,mode,health=False):
    private=root/'private';private.mkdir(mode=0o700,parents=True,exist_ok=True)
    config=read(root/'editorial-config.json',{})
    current=now();cycle=due(current,mode,config.get('publication_schedule',{}).get('catch_up',True))
    lock=(private/'cycles.lock').open('w')
    try:fcntl.flock(lock,fcntl.LOCK_EX|fcntl.LOCK_NB)
    except BlockingIOError:return {'stage':'busy','mode':mode}
    with lock:
        ledger=read(private/'cycles.json',{})
        if health:
            issues=[{'key':key,'status':value['status']} for key,value in ledger.items() if key.startswith(current.astimezone(TZ).date().isoformat()) and (value['status']=='failed' or value['status']=='started' and current-datetime.fromisoformat(value['started_at'])>timedelta(minutes=60))]
            for candidate_mode in HOURS:
                expected=due(current,candidate_mode,config.get('publication_schedule',{}).get('catch_up',True))
                if expected and current-datetime.fromisoformat(expected['slot'])>timedelta(minutes=50) and expected['key'] not in ledger:issues.append({'key':expected['key'],'status':'missing'})
            report={'checked_at':current.isoformat(),'healthy':not issues,'issues':issues};write(root/'editorial-health.json',report)
            if issues:notify(root,'cycle_failed','Hay un ciclo editorial que requiere revisión; no se reintentó a ciegas.')
            return report
        if not cycle:return {'stage':'not_due','mode':mode}
        if cycle['key'] in ledger:return {'stage':'already_attempted','key':cycle['key'],'status':ledger[cycle['key']]['status']}
        work=root/'news' if mode=='news' else root
        if mode=='news':
            work.mkdir(mode=0o700,exist_ok=True)
            # Share only technical helpers; news never collects private assistant sessions.
            for name in ['wp-mcp-transport.py']:
                dest=work/name
                if not dest.exists():dest.symlink_to(root/name)
            write(work/'editorial-config.json',{'publication_schedule':{'catch_up':True},'video':config.get('video',{})})
            if not (work/'queue.json').exists():write(work/'queue.json',{'posts':[],'evidence_review':{}})
            template=Path(__file__).with_name('news-task.txt').read_text()
            (work/'NEWS-TASK.txt').write_text(template);os.chmod(work/'NEWS-TASK.txt',0o600)
        # The transport uses its own file location; a news-root copy keeps request state separate.
        if mode=='news' and (work/'wp-mcp-transport.py').is_symlink():
            (work/'wp-mcp-transport.py').unlink();(work/'wp-mcp-transport.py').write_bytes((root/'wp-mcp-transport.py').read_bytes());os.chmod(work/'wp-mcp-transport.py',0o600)
        cycle['started_at']=current.isoformat();write(work/'private/cycle-context.json',cycle)
        if mode=='experience':
            (work/'DAILY-TASK.txt').write_text(Path(__file__).with_name('task.txt').read_text());os.chmod(work/'DAILY-TASK.txt',0o600)
        ledger[cycle['key']]={'status':'started','started_at':current.isoformat()};write(private/'cycles.json',ledger)
        args=Namespace(force=False,health=False,verify_only=False,collect_only=False,adopt_today=False,credentials=Path.home()/'.local/share/datogedon-mcp/credentials.json')
        try:
            result=execute(work,args)
            ledger[cycle['key']].update(status='completed' if result==0 else 'failed',finished_at=now().isoformat(),result=result)
        except Exception as error:
            ledger[cycle['key']].update(status='failed',finished_at=now().isoformat(),error=type(error).__name__)
        write(private/'cycles.json',ledger)
        return {'key':cycle['key'],**ledger[cycle['key']]}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--state-dir',type=Path,required=True);p.add_argument('--mode',choices=HOURS,default='experience');p.add_argument('--health',action='store_true');a=p.parse_args()
    r=run(a.state_dir.resolve(),a.mode,a.health);print(json.dumps(r,ensure_ascii=False));sys.exit(1 if r.get('status')=='failed' or r.get('healthy') is False else 0)
