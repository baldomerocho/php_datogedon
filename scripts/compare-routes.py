import json,sys
before=json.load(open(sys.argv[1]));after=json.load(open(sys.argv[2]));new={p['id']:p['url'] for p in after['posts']}
errors=[p for p in before['posts'] if new.get(p['id'])!=p['url']]
if errors:
    print(json.dumps(errors,ensure_ascii=False,indent=2));sys.exit('Existing post/page permalinks changed')
print('Existing post/page permalinks preserved:',len(before['posts']))
