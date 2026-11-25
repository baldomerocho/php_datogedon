"""Link a confirmed public social video to its existing published article."""
import argparse,hashlib,html,json,re
from pathlib import Path
from urllib.request import Request,urlopen
from runtime import WordPress,write,now

START='<!-- datogedon-video:start -->'
END='<!-- datogedon-video:end -->'

def provider(url):
    for name,pattern in [
        ('TikTok',r'https://www\.tiktok\.com/@datogedon/video/[0-9]+'),
        ('YouTube',r'https://www\.youtube\.com/shorts/[A-Za-z0-9_-]{11}'),
        ('Instagram',r'https://www\.instagram\.com/datogedon/reel/[A-Za-z0-9_-]+/'),
    ]:
        if re.fullmatch(pattern,url):return name
    raise ValueError('Expected a canonical Datogedon video URL; verify YouTube channel ownership separately')

def reference(content,url):
    name=provider(url);links={};existing=None
    if START in content or END in content:
        if content.count(START)!=1 or content.count(END)!=1:raise ValueError('Ambiguous video section')
        existing=re.search(re.escape(START)+r'.*?'+re.escape(END),content,flags=re.S)
        if not existing:raise ValueError('Invalid video section order')
        for old in re.findall(r'<a\b[^>]*\bhref="([^"]+)"',existing.group(),flags=re.I):
            old=html.unescape(old);old_name=provider(old)
            if old_name in links and links[old_name]!=old:raise ValueError('Multiple videos for the same platform')
            links[old_name]=old
    if name in links and links[name]!=url:raise ValueError('A different video is already linked for this platform')
    links[name]=url
    block=START+'\n<h2>Resumen en video</h2>\n'+'\n'.join('<p><a href="'+html.escape(link,quote=True)+'">Ver el resumen en '+label+' · @datogedon</a></p>' for label,link in links.items())+'\n'+END
    if existing:
        return re.sub(re.escape(START)+r'.*?'+re.escape(END),lambda _:block,content,flags=re.S)
    sources=re.search(r'<h2\b[^>]*>\s*Fuentes\s*</h2>',content,re.I)
    if sources:return content[:sources.start()]+block+'\n\n'+content[sources.start():]
    return content.rstrip()+'\n\n'+block+'\n'

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--post-id',type=int,required=True);p.add_argument('--video-url',required=True)
    p.add_argument('--state-dir',type=Path,required=True)
    p.add_argument('--confirmed-public',action='store_true',help='Operator verified public visibility and the Datogedon account/channel; not merely uploaded or scheduled')
    p.add_argument('--apply',action='store_true');a=p.parse_args()
    if not a.confirmed_public:p.error('Confirm the video is public before linking it')
    wp=WordPress(Path.home()/'.local/share/datogedon-mcp/credentials.json')
    resource=f'posts/{a.post_id}?context=edit';before,_=wp.get(resource)
    if before['status']!='publish':raise ValueError('Article must already be published')
    with urlopen(Request(before['link'],headers={'User-Agent':'DatogedonEditorial/2.0'}),timeout=30) as r:
        if r.status!=200:raise ValueError('Article is not publicly available')
    old=before['content']['raw'];new=reference(old,a.video_url)
    if old==new:print(json.dumps({'post_id':a.post_id,'status':'already_linked'}));return
    if not a.apply:print(json.dumps({'post_id':a.post_id,'status':'ready','article_url':before['link']}));return
    evidence=a.state_dir.expanduser()/'private/video-links'/str(a.post_id)/now().strftime('%Y%m%dT%H%M%SZ')
    write(evidence/'before.json',before)
    fresh,_=wp.get(resource)
    if fresh['modified_gmt']!=before['modified_gmt'] or fresh['content']['raw']!=old:raise RuntimeError('Article changed; review before writing')
    write(evidence/'attempt.json',{'video_url':a.video_url,'started_at':now().isoformat(),'content_sha256':hashlib.sha256(new.encode()).hexdigest()})
    # One write only. An uncertain response must be reconciled, never blindly retried.
    req=Request('https://datogedon.com/wp-json/wp/v2/posts/'+str(a.post_id),data=json.dumps({'content':new}).encode(),headers={'Authorization':wp.auth,'User-Agent':'DatogedonEditorial/2.0','Content-Type':'application/json'},method='POST')
    with urlopen(req,timeout=45) as r:json.load(r)
    after,_=wp.get(resource);write(evidence/'after.json',after)
    if a.video_url not in after['content']['raw'] or START not in after['content']['raw']:raise RuntimeError('Saved link not verified')
    for key in ['id','slug','status','date','date_gmt','link','title','author','featured_media','categories','tags','comment_status']:
        if after[key]!=before[key]:raise RuntimeError('Unexpected change: '+key)
    print(json.dumps({'post_id':a.post_id,'status':'linked','article_url':after['link'],'video_url':a.video_url,'backup':str(evidence)}))

if __name__=='__main__':main()
