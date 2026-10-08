from pathlib import Path
import json,hashlib,collections,sys
root=Path(__file__).resolve().parents[1];site=root/'site';runtime=Path(sys.argv[1]).resolve() if len(sys.argv)>1 else root.parent/'monato-restoration-server-plan';data=json.loads((site/'catalog.json').read_text(encoding='utf-8'));audit=json.loads((site/'skill-access-audit.json').read_text(encoding='utf-8'));rules=json.loads((runtime/'src/Monato.LocalRuntime/skill-rules.json').read_text(encoding='utf-8'));R={r['Id']:r for r in rules};dur={r['Id']:r['DurationMs'] for r in json.loads((runtime/'src/Monato.LocalRuntime/source-temporal-durations.json').read_text(encoding='utf-8'))};assert len(R)==len(data['skills'])==160
labels={100:('Физический урон','Physical damage','%'),101:('Магический урон','Magic damage','%'),102:('Физический урон с частичным обходом защиты','Physical damage with partial defense bypass','%'),103:('Конверсия потраченного HP в MP','Conversion of spent HP to MP','%'),104:('Физический урон с поглощением HP','Physical damage with HP absorption','%'),106:('Cruel Weapon: коэффициент атаки','Cruel Weapon attack coefficient','%'),107:('Физическая атака','Physical attack','%'),108:('Магическая атака','Magic attack','%'),109:('Физическая защита','Physical defense','%'),110:('Магическая защита','Magic defense','%'),111:('Максимум HP','Maximum HP','%'),112:('Максимум MP','Maximum MP','%'),113:('Блок','Block',''),114:('Физическая защита','Physical defense',''),115:('Скорость атаки','Attack speed',''),116:('Скорость подготовки навыков','Skill preparation speed',''),117:('Все пять характеристик','All five attributes',''),118:('Критический шанс магических навыков','Magic skill critical chance',''),119:('Снижение физической атаки','Physical attack reduction','%'),120:('Снижение магической атаки','Magic attack reduction','%'),121:('Снижение физической защиты','Physical defense reduction','%'),122:('Снижение магической защиты','Magic defense reduction','%'),123:('Снижение скорости движения','Movement speed reduction','%'),124:('База магического лечения','Base magic healing',''),125:('Восстановление от максимального HP','Recovery of maximum HP','%'),126:('Магический урон с поглощением MP','Magic damage with MP absorption','%'),127:('Магический урон с поглощением HP','Magic damage with HP absorption','%'),128:('Передача потраченного HP','Transfer of spent HP','%'),129:('Передача потраченного MP','Transfer of spent MP','%'),130:('Параметр угрозы','Threat parameter',''),131:('HP при воскрешении','HP on resurrection','%')}
for pid,ru,en in [(1019,'Максимум HP','Maximum HP'),(1020,'Максимум MP','Maximum MP'),(1021,'Физическая защита','Physical defense'),(1022,'Магическая защита','Magic defense'),(1023,'Физическая атака','Physical attack'),(1024,'Магическая атака','Magic attack')]:labels[pid]=(ru,en,'%')
notes={
102:('Частично ослабляет влияние защиты; не означает полное игнорирование брони.','Partially reduces defense mitigation; it does not ignore all armor.'),
103:('Расходует до 20% максимального HP, оставляя не менее 1 HP. MP возвращается как указанный процент реально потраченного HP.','Spends up to 20% of maximum HP, leaving at least 1 HP. MP gain is the listed percentage of HP actually spent.'),
104:('Восстанавливает HP в размере 20% × ранг от рассчитанного урона, с ограничением максимумом HP.','Restores HP equal to 20% × rank of generated damage, capped at maximum HP.'),
106:('Расходует прочность оружия; итоговый коэффициент зависит от реально доступной прочности.','Consumes weapon durability; the final coefficient depends on available durability.'),
115:('Параметр 250 уменьшает базовый период атаки на 25%; минимальный период — 40% базового.','A value of 250 reduces the base attack period by 25%; the period is bounded to 40% of the base.'),
116:('Параметр 250 сокращает подготовку на 25%; минимальная подготовка — 40% базовой. Не ускоряет фазу анимации.','A value of 250 reduces preparation by 25%, bounded to 40% of base preparation. It does not speed up the action phase.'),
124:('Лечение зависит от магической атаки и уровня: база × (1 + магический бросок × 0,002 + уровень × 0,02), с исходным округлением и ограничением максимума HP.','Healing depends on magic attack and level: base × (1 + magic roll × 0.002 + level × 0.02), using source rounding and the maximum HP cap.'),
126:('Восстанавливает MP в размере 20% × ранг от рассчитанного урона. У монстра не вычитается выдуманный запас MP.','Restores MP equal to 20% × rank of generated damage. No invented monster MP pool is drained.'),
127:('Восстанавливает HP в размере 20% × ранг от рассчитанного урона, с ограничением максимумом HP.','Restores HP equal to 20% × rank of generated damage, capped at maximum HP.'),
128:('Расходует до 20% максимального HP заклинателя, оставляя 1 HP; союзник получает указанный процент потраченного HP.','Spends up to 20% of the caster’s maximum HP, leaving 1 HP; the ally receives the listed percentage of HP spent.'),
129:('Расходует до 20% максимального MP заклинателя, оставляя 1 MP; союзник получает указанный процент потраченного MP.','Spends up to 20% of the caster’s maximum MP, leaving 1 MP; the ally receives the listed percentage of MP spent.')}
changed=[]
for s in data['skills']:
 r=R[s['id']];a=s['access'];assert a['recordSha256']==r['RecordSha256'];old=a.get('local');active=r['MinLevel'] is not None;assert bool(old)==active
 a['nativeLevelField']=r['NativeMinLevel'];a['nativeLevelFieldMeaning']={'ru':'Порог byte193 принят как уровень персонажа в политике восстановленного сервера; равенство уровня профессии и уровня персонажа в оригинале не доказано.','en':'The byte193 threshold is mapped to character level by restored-server policy; original job-level versus character-level equivalence is not established.'}
 if active:
  level=max(r['MinLevel'],old.get('classAcquisitionLevel') or 1);changed.append({'id':s['id'],'before':old['earliestCharacterLevel'],'after':level})
  old.update(minimumLevel=r['MinLevel'],earliestCharacterLevel=level,prerequisites=r['Prerequisites'] or [],rankMinimumLevels=[level]*r['MaxRank'],higherRankLevelGate=False,source='Monato.LocalRuntime/skill-rules.json; user-approved progression policy 2026-10-04; SkillRules.Accessible/Allocate')
 a['rankCosts']=r['RankCosts'][:r['MaxRank']]
 s.update(skillType=r['Type'],passive=r['Type']==1,rank=r['MaxRank'],mp=r['MpBase'],mpIncrement=r['MpIncrement'],casting=r['CastingMs'],cooldown=r['CooldownMs'],range=r['Range'],classMask=r['ClassMask'],weaponMask=r['WeaponMask'])
 effects=[];segments={'ru':[],'en':[]};detailnotes={'ru':[],'en':[]}
 for e in r['Effects']:
  if not e['PropertyId']:continue
  pid=e['PropertyId'];label=labels.get(pid,(e.get('PropertyDescription') or f'Свойство {pid}',e.get('PropertyDescription') or f'Property {pid}',''))
  vals=[e['Base']+e['Increment']*i for i in range(r['MaxRank'])];effects.append({**e,'label':{'ru':label[0],'en':label[1]},'unit':label[2] if active else '', 'rankValues':vals if e['Flag']==0 else None,'rankFormulaVerified':active and e['Flag']==0})
  if active:
   value=str(vals[0]) if vals[0]==vals[-1] else f'{vals[0]}–{vals[-1]}'
   for lang,k in [('ru',0),('en',1)]:segments[lang].append(f'{label[k]}: {value}{label[2]}')
   if pid in notes:
    for lang,k in [('ru',0),('en',1)]:detailnotes[lang].append(notes[pid][k])
 target={'ru':'Исходные поля цели сохранены; условия не подтверждены.','en':'Source target fields are preserved; applicability is unconfirmed.'}
 if active:
  if r['Type']==1:target={'ru':'Пассивный эффект на изучившего персонажа','en':'Passive effect on the character who learned it'}
  elif s['id']==17008:target={'ru':'Выбранная точка земли; живые видимые монстры в радиусе 1000','en':'Selected ground point; live visible monsters within radius 1000'}
  elif s['id']==12005:target={'ru':'Видимые монстры в радиусе 1600 вокруг персонажа','en':'Visible monsters within radius 1600 of the caster'}
  elif s['id']==12002:target={'ru':'Один выбранный видимый живой монстр','en':'One selected visible live monster'}
  elif r['TargetKind']==5:target={'ru':'Один видимый живой монстр','en':'One visible live monster'}
  elif r['TargetKind']==1 and r['TargetRelation']==2:target={'ru':'Персонаж и участники его группы в радиусе 1200','en':'Caster and party members within radius 1200'}
  elif r['TargetKind']==1:target={'ru':'Сам персонаж','en':'The caster'}
  elif r['TargetKind']==3:target={'ru':'Погибший другой персонаж в той же локации','en':'Another dead character in the same world'}
  elif r['TargetKind']==2:target={'ru':'Живой участник своей группы в той же локации','en':'A live member of the caster’s party in the same world'}
  elif r['TargetKind']==4:target={'ru':'Живой дружественный персонаж в той же локации','en':'A live friendly character in the same world'}
 if s['id']==17002:
  detailnotes['ru'].append('Не наносит прямого урона.');detailnotes['en'].append('Does not deal direct damage.')
 if s['id']==12009:
  detailnotes['ru'].append('Восстанавливает HP живого заклинателя; не воскрешает погибшего союзника.');detailnotes['en'].append('Restores the living caster’s HP; it does not resurrect a dead ally.')
 m={'currentServerRule':active,'preparationMs':r['PreparationMs'],'actionMs':r['CastingMs'],'projectileType':r['ProjectileType'],'projectileSpeed':r['ProjectileSpeed'],'effectDurationMs':dur.get(s['id']),'targetKind':r['TargetKind'],'targetRelation':r['TargetRelation'],'target':target,'effects':effects,'notes':detailnotes,'ranks':[],'movementLocked':active and r['Type']==2}
 for i in range(r['MaxRank']):m['ranks'].append({'rank':i+1,'level':a['local']['earliestCharacterLevel'] if active else None,'points':a['rankCosts'][i],'totalPoints':sum(a['rankCosts'][:i+1]),'mp':r['MpBase']+r['MpIncrement']*i,'effectValues':[e['rankValues'][i] if e['rankValues'] else None for e in effects]})
 s['mechanics']=m
 if active:
  s['originalDescription']=s.get('originalDescription',dict(s['description']))
  for lang in ['ru','en']:
   text='; '.join(segments[lang])+'.'
   if m['effectDurationMs']:text+=(' Длительность: ' if lang=='ru' else ' Duration: ')+str(m['effectDurationMs']//1000)+(' с.' if lang=='ru' else ' s.')
   if s['id'] in [17002,12009]:text+=' '+detailnotes[lang][-1]
   s['description'][lang]=text
for c in data['classes']:
 c['skillCoverage']={'current':sum(s['family']==c['id'] and s['mechanics']['currentServerRule'] for s in data['skills']),'archive':sum(s['family']==c['id'] and not s['mechanics']['currentServerRule'] for s in data['skills']),'date':'2026-10-08'}
sources=['src/Monato.LocalRuntime/skill-rules.json','src/Monato.LocalRuntime/SkillRules.cs','src/Monato.LocalRuntime/source-temporal-durations.json','src/Monato.LocalRuntime/TemporalStatistics.cs','src/Monato.LocalRuntime/NativeSkillMath.cs','src/Monato.LocalRuntime/SharedMoonriseCombat.cs']
audit['meta'].update(date='2026-10-08',currentServerSkillCount=67,correctedUnlockCount=sum(x['before']!=x['after'] for x in changed) or audit['meta'].get('correctedUnlockCount',0),sourceSnapshot={p:hashlib.sha256((runtime/p).read_bytes()).hexdigest() for p in sources},visibility='Saved and access-eligible skills are listed; rank0 is not learned. One allocated point per click; rank derives from cumulative source costs.',rankProgression='The same access level applies to all ranks; no extra per-rank level gates are configured.',classLevelPolicy='User-approved 2026-10-04 mapping of skill.dat byte193 to character level, combined with acquiring a class from level5. Original job-level equivalence is unconfirmed.',relatedSessions=['Сайт Monato Esprit и Server','Скилл $monato-location-restoration','Current conversation: confirmed casting movement lock 2026-10-08'])
audit['skills']=[{'id':s['id'],'name':s['name'],'family':s['family'],'generation':s['generation'],'access':s['access'],'mechanics':s['mechanics']} for s in data['skills']]
data['meta']['skillAuditDate']='2026-10-08';data['meta']['sources']+= [p for p in sources if p not in data['meta']['sources']]
(site/'skill-access-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');(site/'catalog.json').write_text(json.dumps(data,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
(site/'data.js').write_text('window.ATLAS='+json.dumps(data,ensure_ascii=False,separators=(',',':'))+';',encoding='utf-8')
print(json.dumps({'records':160,'currentSkills':67,'changedUnlocks':audit['meta']['correctedUnlockCount'],'classes':[c['skillCoverage']|{'class':c['id']} for c in data['classes']]},ensure_ascii=False))
