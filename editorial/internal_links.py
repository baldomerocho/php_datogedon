"""Audit contextual links without rewriting HTML. Public WordPress reads only."""
import argparse,json,sys
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit
from runtime import WordPress
class Links(HTMLParser):
    def __init__(self):super().__init__();self.links=[];self.link=None;self.skip=0
    def handle_starttag(self,tag,attrs):
        if tag in ['pre','code','script','style']:self.skip+=1
        if tag=='a':self.link={'href':dict(attrs).get('href',''),'text':'','in_code':bool(self.skip)}
    def handle_data(self,data):
        if self.link:self.link['text']+=data
    def handle_endtag(self,tag):
        if tag=='a' and self.link:self.links.append(self.link);self.link=None
        if tag in ['pre','code','script','style'] and self.skip:self.skip-=1

def audit(post,catalog):
    parser=Links();parser.feed(post['content'].get('raw',post['content'].get('rendered','')))
    known={urlsplit(p['link']).path.rstrip('/'):p for p in catalog if p['status']=='publish' and not p.get('password')}
    found=[];issues=[];seen=set()
    for link in parser.links:
        url=urlsplit(link['href'])
        if url.hostname and url.hostname not in ['datogedon.com','www.datogedon.com']:continue
        if not url.path or url.path.startswith('/wp-content/'):continue
        path=url.path.rstrip('/');target=known.get(path)
        if not target:issues.append('destino interno no publicado o fuera del catálogo');continue
        if target['id']==post['id']:issues.append('enlace al propio artículo')
        if target['id'] in seen:issues.append('destino interno repetido')
        if link['in_code']:issues.append('enlace dentro de código')
        if not link['text'].strip() or link['text'].strip().lower() in ['aquí','aqui','clic aquí','leer más']:issues.append('ancla interna poco descriptiva')
        seen.add(target['id']);found.append({'target_id':target['id'],'anchor':link['text']})
    if len(found)>3:issues.append('más de tres enlaces contextuales; revisar selección')
    return {'internal_links':found,'problems':issues,'note':'La revisión semántica corresponde al redactor; no se exige un mínimo de enlaces.'}

def catalog(wp):
    result=[];page=1
    while True:
        data,pages=wp.get(f'posts?context=edit&status=publish&per_page=100&page={page}&_fields=id,status,link,password,title,excerpt,date,categories,tags')
        result+=[{k:v for k,v in item.items() if k!="password"} for item in data if not item.get("password")]
        if page>=pages:return result
        page+=1
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--post-id',type=int,required=True);a=p.parse_args()
    try:
        wp=WordPress(Path.home()/'.local/share/datogedon-mcp/credentials.json');post=wp.get(f'posts/{a.post_id}?context=edit')[0]
        report=audit(post,catalog(wp));print(json.dumps(report,ensure_ascii=False));sys.exit(bool(report['problems']))
    except Exception:
        print('No se pudo verificar el enlazado interno.',file=sys.stderr);sys.exit(1)
