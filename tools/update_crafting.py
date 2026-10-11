"""Export every supported source recipe; no player data or private settings."""
import argparse,json,hashlib
from pathlib import Path
def export(root):
 site=Path(__file__).resolve().parents[1]/'site';src=root/'src/Monato.LocalRuntime';catalog=json.loads((site/'catalog.json').read_bytes());items={i['id']:i for i in catalog['items']};names={i['Id']:i['Name']for i in json.loads((src/'market-item-names.json').read_bytes())['Items']};gear={i['ItemId']:i for i in json.loads((src/'equipment-stats.json').read_bytes())['Equipment']};recipes=[];extra={};hashes={}
 for file,kind in [('source-production.json','production'),('source-alchemy.json','alchemy')]:
  data=(src/file).read_bytes();hashes[file]=hashlib.sha256(data).hexdigest()
  for r in json.loads(data):
   rid=r['BlueprintItemId'] if kind=='production' else r['RecipeItemId'];refs=[rid,r['OutputItemId']]+[i['ItemId']for i in r['Ingredients']]
   for id in refs:
    if id not in items and id not in extra:
     x={'id':id,'name':{'ru':names.get(id,f'Item #{id}'),'en':names.get(id,f'Item #{id}')},'defined':id in names};asset=f'assets/item-{id}.webp'
     if (site/asset).exists():x['image']=asset
     if id in gear:
      g=gear[id];x['equipment']={'slot':g['Slot'],'minLevel':g['MinLevel'],'classMask':g['ClassMask'],'sex':g['Sex'],'stats':g['NativeStats'],'attackPeriodMs':g['NativeAttackPeriodMs'],'enchantable':False}
     extra[id]=x
   output=items.get(r['OutputItemId'],extra.get(r['OutputItemId']));g=gear.get(r['OutputItemId'])
   recipes.append({'key':f'{kind}-{r["Id"]}','kind':kind,'id':r['Id'],'recipeItem':rid,'output':r['OutputItemId'],'count':r['OutputCount'],'ingredients':[{'id':i['ItemId'],'count':i['Count']}for i in r['Ingredients']],'sourceLevel':r['NativeLevel'],'fee':r['Fee'],'successPercent':r['SuccessPercent'],'level':g['MinLevel']if g else None,'classMask':g['ClassMask']if g else 255,'slot':g['Slot']if g else None,'nativeType':g['NativeItemType']if g else None})
 assert len(recipes)==145 and len({r['key']for r in recipes})==145
 assert all(id in items or extra[id]['defined']for r in recipes for id in [r['recipeItem'],r['output']]+[i['id']for i in r['ingredients']])
 payload={'recipes':recipes,'items':list(extra.values())};(site/'craft-data.js').write_text('window.CRAFT_DATA='+json.dumps(payload,ensure_ascii=False,separators=(',',':'))+';\n',encoding='utf-8')
 (site/'craft-audit.json').write_text(json.dumps({'recipes':145,'production':80,'alchemy':65,'extraItems':len(extra),'sources':hashes,'requirements':'Finished item equipment requirements; source recipe levels are informational','serverPolicy':'SourceProduction/StarterAlchemy: fee1, success100; blueprints consumed, alchemy learned once'},indent=2)+'\n',encoding='utf-8')
 print(json.dumps({'recipes':len(recipes),'extraItems':len(extra)}))
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('server',type=Path);export(p.parse_args().server)
