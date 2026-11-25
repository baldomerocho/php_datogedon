#!/usr/bin/env python3
"""Read-only Matomo verification. Token travels only in a HTTPS POST body."""
import argparse,json,os,re,stat,sys,urllib.error,urllib.parse,urllib.request
from pathlib import Path

CATEGORIES={'Interface','Navigation','Search','Reading','Collaboration','Discussion'}
ACTIONS={'theme_change','open','contact_open','related_open','article_open','section_open','autocomplete_select','submit','results','progress_50','progress_90','view','start','reply','featured_open','received'}

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env',required=True,type=Path,help='Private dotenv file containing APIKEY')
    parser.add_argument('--url',default='https://analytics.iimm.biz/')
    parser.add_argument('--site-id',type=int,default=1)
    parser.add_argument('--expected-host',default='datogedon.com')
    parser.add_argument('--date',default='today')
    args=parser.parse_args()
    target=urllib.parse.urlsplit(args.url)
    if target.scheme!='https' or not target.hostname or target.username or target.password or target.query or target.fragment:parser.error('--url must be HTTPS without credentials, query or fragment')
    if stat.S_IMODE(args.env.stat().st_mode)&0o077:parser.error('Protect the env file first: chmod 600 <file>')
    values={}
    for line in args.env.read_text().splitlines():
        line=line.strip().removeprefix('export ')
        if line and not line.startswith('#') and '=' in line:
            key,value=line.split('=',1);values[key.strip()]=value.strip().strip('\"\'')
    token=values.get('APIKEY')
    if not token:parser.error('APIKEY is missing')
    def api(method,**params):
        fields=dict(module='API',method=method,idSite=args.site_id,period='day',date=args.date,format='JSON',format_metrics=0,token_auth=token)
        fields.update(params)
        req=urllib.request.Request(args.url.rstrip('/')+'/index.php',data=urllib.parse.urlencode(fields).encode(),headers={'User-Agent':'DatogedonAnalyticsAudit/1.2'})
        # Do not redirect an authenticated POST to another destination.
        class NoRedirect(urllib.request.HTTPRedirectHandler):
            def redirect_request(self,*a,**kw):return None
        try:
            with urllib.request.build_opener(NoRedirect).open(req,timeout=30) as response:data=json.load(response)
        except (urllib.error.URLError,ValueError):raise RuntimeError(method+': HTTP/API response could not be verified') from None
        if isinstance(data,dict) and data.get('result')=='error':raise RuntimeError(method+': API denied the request')
        return data
    site=api('SitesManager.getSiteFromId')
    if isinstance(site,list):site=site[0] if site else {}
    if urllib.parse.urlsplit(site.get('main_url','')).hostname!=args.expected_host:raise RuntimeError('Site ID does not match the expected hostname')
    visits=api('VisitsSummary.get');actions=api('Actions.get')
    categories=api('Events.getCategory',filter_limit=100)
    live=api('Live.getLastVisitsDetails',filter_limit=20)
    events=[];native={}
    for visit in live if isinstance(live,list) else []:
        for action in visit.get('actionDetails',[]):
            kind=action.get('type','unknown');native[kind]=native.get(kind,0)+1
            if kind!='event':continue
            category=action.get('eventCategory');action_name=action.get('eventAction')
            if category not in CATEGORIES or action_name not in ACTIONS:continue
            name=action.get('eventName','')
            # Discard arbitrary labels; never export visitor IDs, IPs or search phrases.
            if not re.fullmatch(r'post:[0-9]+|light|dark|header|footer|content|hero|results|found|empty|home|topics|experiences|about|mobile_menu|article|comment',str(name)):name=None
            events.append({'category':category,'action':action_name,'name':name,'time':action.get('serverTimePretty')})
    report={'site_id':args.site_id,'hostname':args.expected_host,'timezone':site.get('timezone'),'date':args.date,
        'visits':{k:visits[k] for k in ['nb_visits','nb_uniq_visitors','nb_actions'] if k in visits},
        'actions':{k:actions[k] for k in ['nb_pageviews','nb_downloads','nb_outlinks','nb_searches'] if k in actions},
        'reported_event_categories':[{k:r[k] for k in ['label','nb_events','nb_visits'] if k in r} for r in categories if r.get('label') in CATEGORIES],
        'live_action_types':native,'live_site_events':events}
    print(json.dumps(report,ensure_ascii=False,indent=2).replace(token,'[REDACTED]'))
if __name__=='__main__':
    try:main()
    except (OSError,RuntimeError) as error:
        print('Matomo audit failed: '+str(error) if isinstance(error,RuntimeError) else 'Matomo audit failed: private env file could not be read',file=sys.stderr);sys.exit(1)
