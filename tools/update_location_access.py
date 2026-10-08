from pathlib import Path
import json,hashlib,collections,sys,re
root=Path(__file__).resolve().parents[1];site=root/'site';runtime=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root.parent/'monato-restoration-server-plan'
d=json.loads((site/'catalog.json').read_text(encoding='utf-8'));policy=json.loads((runtime/'src/Monato.LocalRuntime/source-travel-policy.json').read_text(encoding='utf-8'));quests={q['Id']:q for q in json.loads((runtime/'src/Monato.LocalRuntime/starter-quests.json').read_text(encoding='utf-8'))}
catalog_code=(runtime/'src/Monato.LocalRuntime/SourceTravelCatalog.cs').read_text(encoding='utf-8');assert 'FromZone==4&&TargetZone==5&&MoveEvent==602981132' in catalog_code
isildra=(runtime/'src/Monato.LocalRuntime/IsildraTravelSession.cs').read_text(encoding='utf-8');rhea=(runtime/'src/Monato.LocalRuntime/RheaTravelSession.cs').read_text(encoding='utf-8');assert 'FinalStarterQuest=500000003' in isildra and '500010001u' in rhea
Q={q['id']:q for q in d['quests']};N={n['id']:n for n in d['npcs']};I={i['id']:i for i in d['items']};assert 50000 in I
zone_map={z:(l,v) for l in d['locations'] for v in l['variants'] for z in v['zones']};routes=[]
for key,kind in [('NpcRoutes','npc'),('RegionRoutes','portal'),('IncompleteSourceRoutes','portal')]:
 for i,r in enumerate(policy[key]):
  assert r['FromZone'] in zone_map and r['TargetZone'] in zone_map
  blocked=r['FromZone']==4 and r['TargetZone']==5 and r['MoveEvent']==602981132
  reason=r.get('Reason');enabled=not reason and not blocked
  disabled={'ru':'Точка прибытия заблокирована; этот переход выключен в текущих правилах.','en':'The arrival point is blocked; this route is disabled in current rules.'} if blocked else {'ru':'В исходных ресурсах не заданы области активации; рабочий вход не подтверждён.','en':'Source trigger areas are missing; a working entry is unconfirmed.'} if reason else None
  routes.append({'id':f'{key}:{i}','kind':kind,'fromZone':r['FromZone'],'targetZone':r['TargetZone'],'fromLocation':zone_map[r['FromZone']][0]['id'],'targetLocation':zone_map[r['TargetZone']][0]['id'],'minimumLevel':r['MinimumLevel'],'npcId':r.get('NpcId'),'menuGroup':r.get('MenuGroup'),'menuIndex':r.get('MenuIndex'),'fee':r['Fee'],'sourceFee':r.get('SourceGold'),'delayMs':r['DelayMs'],'parentEvent':r['ParentEvent'],'moveEvent':r['MoveEvent'],'enabled':enabled,'disabledReason':disabled,'sourceReason':reason,'questRequirement':None,'questStatus':'no_additional_route_quest','requiresMainWorldAccess':r['TargetZone'] not in [9,502],'nearNpcRadius':600 if kind=='npc' else None,'source':r.get('Source'),'itemId':None})
assert len(routes)==92 and sum(r['enabled'] for r in routes)==77
main_q=500000003;main_level=quests[main_q]['MinLevel'];rhea_q=500010001
routes += [
 {'id':'starter:rhea','kind':'npc','fromZone':9,'targetZone':502,'fromLocation':zone_map[9][0]['id'],'targetLocation':zone_map[502][0]['id'],'minimumLevel':quests[rhea_q]['MinLevel'],'npcId':50001,'menuGroup':1,'menuIndex':0,'fee':0,'sourceFee':0,'delayMs':0,'parentEvent':0,'moveEvent':458832488,'enabled':True,'disabledReason':None,'questRequirement':{'id':rhea_q,'state':'active_or_completed','previous':quests[rhea_q]['Previous']},'questStatus':'required','requiresMainWorldAccess':False,'nearNpcRadius':600,'itemId':None,'source':'RheaTravelSession.Entry: active or completed500010001, selected Rhea, alive, near600; completed lesson retains access'},
 {'id':'starter:isildra-scroll','kind':'item','fromZone':9,'targetZone':1,'fromLocation':zone_map[9][0]['id'],'targetLocation':zone_map[1][0]['id'],'minimumLevel':main_level,'npcId':None,'menuGroup':None,'menuIndex':None,'fee':0,'sourceFee':None,'delayMs':0,'parentEvent':None,'moveEvent':None,'enabled':True,'disabledReason':None,'questRequirement':{'id':main_q,'state':'completed','previous':quests[main_q]['Previous']},'questStatus':'required','requiresMainWorldAccess':True,'nearNpcRadius':None,'itemId':50000,'itemCount':1,'source':'IsildraTravelSession.CanEnter/Consume: completed500000003, account main-world access and one owned accessible scroll50000 consumed'},
 {'id':'starter:rhea-return','kind':'portal','fromZone':502,'targetZone':9,'fromLocation':zone_map[502][0]['id'],'targetLocation':zone_map[9][0]['id'],'minimumLevel':1,'npcId':None,'menuGroup':None,'menuIndex':None,'fee':0,'sourceFee':0,'delayMs':600,'parentEvent':2742592317,'moveEvent':3618380664,'enabled':True,'disabledReason':None,'questRequirement':None,'questStatus':'no_additional_route_quest','requiresMainWorldAccess':False,'nearNpcRadius':None,'itemId':None,'source':'RheaTravelSession.Areas: original separate exit areas, one600ms scheduled child; recovery crystal is not an exit'}]
routes.append(dict(routes[-1],id='starter:rhea-return-second',parentEvent=3458442099,moveEvent=3367774504))
# Minimax thresholds start at character creation and include the mandatory main-world graduation gate.
levels={9:1};paths={9:[]}
for _ in range(len(zone_map)):
 changed=False
 for r in routes:
  if not r['enabled'] or r['fromZone'] not in levels:continue
  required=max(levels[r['fromZone']],r['minimumLevel'],main_level if r['requiresMainWorldAccess'] else 1)
  if r['targetZone'] not in levels or required<levels[r['targetZone']]:levels[r['targetZone']]=required;paths[r['targetZone']]=paths[r['fromZone']]+[r['id']];changed=True
 if not changed:break
for r in routes:
 r['knownEntryLevel']=max(r['minimumLevel'],main_level if r['requiresMainWorldAccess'] else 1)
 r['sourcePathConfirmed']=r['fromZone'] in levels
 r['effectiveRouteLevel']=max(levels[r['fromZone']],r['knownEntryLevel']) if r['sourcePathConfirmed'] else None
for l in d['locations']:
 for v in l['variants']:
  incoming=[r for r in routes if r['targetZone'] in v['zones']];outgoing=[r for r in routes if r['fromZone'] in v['zones']];valid=[r for r in incoming if r['enabled']]
  mapped=[z for z in v['zones'] if z in levels]
  level=min((levels[z] for z in mapped),default=None);best=next((z for z in mapped if levels[z]==level),None)
  status='start' if 9 in v['zones'] else 'available_by_rules' if mapped else 'routes_disabled' if incoming and not valid else 'source_route_only' if valid else 'entry_unconfirmed' if v['zones'] else 'archive_unregistered'
  v['access']={'status':status,'knownEntryMinimumLevel':min((r['knownEntryLevel'] for r in valid),default=None),'minimumReachableLevel':level,'minimumLevelKind':'calculated_from_route_and_global_quest_gates' if level is not None else 'unconfirmed','requiresMainWorldAccess':bool(v['zones']) and all(z not in [9,502] for z in v['zones']),'globalQuest':main_q if v['zones'] and all(z not in [9,502] for z in v['zones']) else None,'incomingRoutes':[r['id'] for r in incoming],'outgoingRoutes':[r['id'] for r in outgoing],'minimumLevelPath':paths.get(best,[]),'explicitEntryQuest':rhea_q if 502 in v['zones'] else None,'date':'2026-10-08'}
source_files=['src/Monato.LocalRuntime/source-travel-policy.json','src/Monato.LocalRuntime/SourceTravelCatalog.cs','src/Monato.LocalRuntime/SourceTravelSession.cs','src/Monato.LocalRuntime/RheaTravelSession.cs','src/Monato.LocalRuntime/IsildraTravelSession.cs','src/Monato.LocalRuntime/LocalHost.cs','src/Monato.LocalRuntime/starter-quests.json']
audit={'meta':{'date':'2026-10-08','sourceRoutes':92,'enabledSourceRoutes':77,'disabledOrUnconfirmedSourceRoutes':15,'specialRules':4,'locations':len(d['locations']),'variants':sum(len(l['variants']) for l in d['locations']),'mainWorldMinimumQuestLevel':main_level,'mainWorldQuest':main_q,'levelsMeaning':'Minimum reachable character level is derived by minimax over enabled route thresholds, starting from Moonrise Beach, and includes completed starter quest500000003 at level5 for main-world access. Quest/item/account checks remain separate mandatory conditions; monster levels are never used as entry levels.','sourceSnapshot':{p:hashlib.sha256((runtime/p).read_bytes()).hexdigest() for p in source_files}},'routes':routes,'locations':[{'id':l['id'],'name':l['name'],'variants':[{'world':v['world'],'zones':v['zones'],'access':v['access']} for v in l['variants']]} for l in d['locations']]}
d['locationAccess']={'date':'2026-10-08','mainWorldQuest':main_q,'mainWorldMinimumQuestLevel':main_level,'routes':routes};d['meta']['locationAccessAuditDate']='2026-10-08'
for p in source_files:
 if p not in d['meta']['sources']:d['meta']['sources'].append(p)
payload=json.dumps(d,ensure_ascii=False,separators=(',',':'));(site/'catalog.json').write_text(payload,encoding='utf-8');(site/'data.js').write_text('window.ATLAS='+payload+';',encoding='utf-8');(site/'location-access-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'routeCount':len(routes),'locations':[(l['id'],l['name']['en'],[(v['zones'],v['access']['minimumReachableLevel'],v['access']['status']) for v in l['variants'] if v['zones']]) for l in d['locations']]},ensure_ascii=False))
