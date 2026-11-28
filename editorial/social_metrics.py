"""Opportunistic measurements from creator UI already opened by a publishing job."""
import hashlib,json,math
from datetime import datetime,timezone
from pathlib import Path

METRICS=['views','likes','comments','shares','saves','average_watch_seconds','completion_percent','for_you_percent']

def targets(jobs,current):
    result=[]
    for key,job in jobs.items():
        for platform,entry in job.get('platforms',{}).items():
            stamp=entry.get('published_at') or entry.get('updated_at')
            if entry.get('status')!='published' or not entry.get('url') or not stamp:continue
            try:age=(current-datetime.fromisoformat(stamp)).total_seconds()/3600
            except (ValueError,TypeError):continue
            if 0<=age<=48:result.append({'post_id':int(key),'platform':platform,'url':entry['url'],'public_confirmed_at':stamp})
    return result[-30:]

def ingest(root,work,jobs):
    from runtime import read,write
    try:observations=read(Path(work)/'observations.json',[])
    except (ValueError,OSError):return 0
    if not isinstance(observations,list):return 0
    dest=Path(root)/'videos/distribution/metrics.json';saved=read(dest,{'observations':{}});added=0
    review=(Path.home()/'Movies/Datogedon/review').resolve();current=datetime.now(timezone.utc)
    for row in observations[:30]:
        try:
            entry=jobs[str(row['post_id'])]['platforms'][row['platform']]
            if row.get('url')!=entry.get('url') or entry.get('status')!='published':continue
            artifact=Path(row.get('snapshot_path','')).resolve()
            if not artifact.is_relative_to(review) or not artifact.is_file():continue
            captured=datetime.fromisoformat(row['captured_at']);public=datetime.fromisoformat(entry.get('published_at') or entry['updated_at'])
            age=(captured-public).total_seconds()/3600
            if not 0<=age<=49 or abs((current-captured).total_seconds())>3600:continue
            metrics={k:row.get(k) for k in METRICS}
            if all(v is None for v in metrics.values()):continue
            if any(v is not None and (isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or v<0 or k.endswith('_percent') and v>100) for k,v in metrics.items()):continue
            record={'post_id':int(row['post_id']),'platform':row['platform'],'url':row['url'],'captured_at':captured.isoformat(),
                    'public_confirmed_at':public.isoformat(),'age_hours':round(age,3),'snapshot_path':str(artifact),**metrics}
            key=hashlib.sha256(json.dumps([record[k] for k in ['post_id','platform','captured_at']],sort_keys=True).encode()).hexdigest()
            if key not in saved['observations']:saved['observations'][key]=record;added+=1
        except (ValueError,KeyError,TypeError,AttributeError):continue
    if added:write(dest,saved)
    return added
