"""Verify one editorial draft/future post without exposing its body or credentials."""
import argparse,json,sys
from pathlib import Path
from runtime import WordPress,quality
p=argparse.ArgumentParser(description=__doc__);p.add_argument('--post-id',required=True,type=int);p.add_argument('--expect',choices=['draft','future','publish'],required=True)
a=p.parse_args()
try:
 wp=WordPress(Path.home()/'.local/share/datogedon-mcp/credentials.json');post,_=wp.get(f'posts/{a.post_id}?context=edit')
 media={}
 if post.get('featured_media'):media[post['featured_media']]=wp.get(f"media/{post['featured_media']}?context=edit")[0]
 check=quality(post,media)
 if post['status']!=a.expect:check['problems'].append('estado distinto del esperado')
 print(json.dumps({'post_id':a.post_id,'status':post['status'],'date':post['date'],'featured_media':post['featured_media'],**check},ensure_ascii=False))
 sys.exit(bool(check['problems']))
except Exception:
 print('No se pudo verificar la entrada; no considerar completada su programación.',file=sys.stderr);sys.exit(1)
