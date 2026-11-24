"""Structural smoke tests, not a claim of Google indexing or rich-result eligibility."""
import json,os,sys,urllib.request,urllib.error
from html.parser import HTMLParser
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urlsplit
class HTML(HTMLParser):
    def __init__(self):
        super().__init__();self.meta={};self.canonical=[];self.h1=0;self.ld=[];self.buffer=None
    def handle_starttag(self,t,attrs):
        a=dict(attrs)
        if t=='h1':self.h1+=1
        if t=='meta':self.meta[a.get('name',a.get('property',''))]=a.get('content','')
        if t=='link' and a.get('rel')=='canonical':self.canonical.append(a.get('href'))
        if t=='script' and a.get('type')=='application/ld+json':self.buffer=''
    def handle_data(self,s):
        if self.buffer is not None:self.buffer+=s
    def handle_endtag(self,t):
        if t=='script' and self.buffer is not None:self.ld.append(json.loads(self.buffer));self.buffer=None
def fetch(url):
    req=urllib.request.Request(url,headers={'User-Agent':'DatogedonStructure/1.0'})
    try:
        with urllib.request.urlopen(req,timeout=30) as r:return r.status,r.url,r.read().decode('utf-8')
    except urllib.error.HTTPError as e:return e.code,e.url,e.read().decode('utf-8')
def nodes(page):
    return [n for block in page.ld for n in block.get('@graph',[block])]
def types(page):
    return {t for n in nodes(page) for t in (n.get('@type',[]) if isinstance(n.get('@type',[]),list) else [n.get('@type')])}
base=sys.argv[1].rstrip('/')
paths=['/','/temas/','/experiencias-con-ia/','/politica-editorial/','/colabora/','/acerca-de/','/page/2/']
def check(path):
    code,url,body=fetch(base+path);assert code==200,(path,code)
    p=HTML();p.feed(body);assert p.h1==1,(path,'h1',p.h1);assert len(p.canonical)==1,(path,'canonical',p.canonical);assert 'noindex' not in p.meta.get('robots',''),path
    assert urlsplit(p.canonical[0]).path.rstrip('/')==path.rstrip('/'),(path,p.canonical)
    assert p.ld,(path,'schema missing')
    if path in ['/temas/','/experiencias-con-ia/','/politica-editorial/','/colabora/','/acerca-de/']:
        assert not {'Article','BlogPosting'} & types(p),(path,types(p))
    if path in ['/temas/','/experiencias-con-ia/']:
        assert 'CollectionPage' in types(p),(path,types(p))
    if path=='/acerca-de/':
        assert 'AboutPage' in types(p) and not {'Article','BlogPosting'} & types(p)
    if path=='/':
        assert {'Person','WebSite'} <= types(p)
        assert p.meta.get('og:image','').endswith('/assets/social.png'),p.meta.get('og:image')
        publisher=next(n for n in nodes(p) if n.get('@id')==base+'/#person')
        code,profile_url,body=fetch(publisher['url']);assert code==200
        profile=HTML();profile.feed(body);assert 'ProfilePage' in types(profile)
        assert 'noindex' not in profile.meta.get('robots','')
    return path
for path in ThreadPoolExecutor(max_workers=4).map(check,paths):print('OK',path)
code,url,body=fetch(base+'/category/inteligencia-artificial/');assert code==200
code,url,body=fetch(base+'/inteligencia-artificial/');assert code==200 and urlsplit(url).path=='/category/inteligencia-artificial/',url
class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs):return None
try:
    urllib.request.build_opener(NoRedirect).open(base+'/inteligencia-artificial/page/2/',timeout=30)
    raise AssertionError('Legacy category pagination must redirect')
except urllib.error.HTTPError as redirect:
    assert redirect.code==301 and urlsplit(redirect.headers['Location']).path=='/category/inteligencia-artificial/page/2/',(redirect.code,dict(redirect.headers))
code,url,body=fetch(base+'/no-existe-estructura-404/');assert code==404,code
p=HTML();p.feed(body);assert 'noindex' in p.meta.get('robots','')
code,url,body=fetch(base+'/?s=integracion');p=HTML();p.feed(body);assert 'noindex' in p.meta.get('robots','')
code,url,body=fetch(base+'/robots.txt');assert 'sitemap.html' not in body and 'wp-sitemap.xml' not in body;assert '/sitemap.xml' in body,(code,url,body[:2000]);assert body.count('Sitemap:')==1,body
if len(sys.argv)>2:
    inventory=json.load(open(sys.argv[2]))
    posts=inventory.get('posts',inventory)
    def check_post(post):
        if post.get('status')!='publish':return
        target=base+urlsplit(post['url']).path
        code,url,body=fetch(target);assert code==200,(post['id'],code,target)
        p=HTML();p.feed(body);assert len(p.canonical)==1;assert urlsplit(p.canonical[0]).path==urlsplit(post['url']).path,(post['id'],p.canonical)
    list(ThreadPoolExecutor(max_workers=4).map(check_post,posts))
    print('OK all published routes:',len([p for p in posts if p.get('status')=='publish']))
print('SEO structure checks passed')
