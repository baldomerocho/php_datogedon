"""Only promote related, owned YouTube guides whose public release was verified."""
import re
from runtime import read
CHANNEL='UCUEIkqP0ZYY7R7GEV5wwhvA'

def public_guides(state):
    try:videos=read(state/'extended-catalog.json',{'videos':{}}).get('videos',{})
    except (ValueError,OSError,AttributeError):return []
    if not isinstance(videos,dict):return []
    return [{k:v[k] for k in ['post_id','title','url','channel_id','status','owner_verified','public_verified']} for v in videos.values() if isinstance(v,dict) and isinstance(v.get('post_id'),int) and isinstance(v.get('title'),str) and v.get('status')=='published' and v.get('owner_verified') is True
            and v.get('public_verified') is True and v.get('channel_id')==CHANNEL
            and re.fullmatch(r'https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}',v.get('url',''))]

def related_guide(state,brief):
    target=brief.get('extended_post_id',brief['post_id'])
    return next(({'post_id':v['post_id'],'url':v['url'],'title':v['title'],'channel_id':CHANNEL,
                  'status':'published','owner_verified':True,'public_verified':True}
                 for v in public_guides(state) if v['post_id']==target),None)

def outro_target(brief):
    v=brief.get('extended_video',{}) or {}
    if v.get('status')=='published' and v.get('owner_verified') is True and v.get('public_verified') is True and v.get('channel_id')==CHANNEL and re.fullmatch(r'https://www\.youtube\.com/watch\?v=[A-Za-z0-9_-]{11}',v.get('url','')):
        return v
    return None
