"""Export source character parts at the shared AA pose; archives are read only.
Run: python export_calculator_assets.py PROJECT_ROOT ATLAS_ROOT GAME_DIR
Requires the project's verified tmd/export_npcs modules and NumPy/Pillow.
"""
from pathlib import Path
import sys,ast,json,struct,zlib,hashlib,io,math,tempfile
import numpy as np
from PIL import Image
sys.dont_write_bytecode=True
root,repo,game=map(Path,sys.argv[1:4]);sys.path.insert(0,str(root/'monato-client-analysis'))
from tmd import Reader
import export_npcs as ex
tree=ast.parse((root/'monato-esprit-local/diagnostics/client1004-equipment-skills-20261005/audit.py').read_text(encoding='utf-8-sig'))
ns={'struct':struct,'zlib':zlib,'re':__import__('re')}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef)) and getattr(n,'name','') in ['Archive','parseitems']],type_ignores=[]),'source-reader','exec'),ns)
arc=ns['Archive'](game);read=arc.read
def find(p):
 key=p.lower().replace('\\','/')
 if key not in arc.entries:raise StopIteration(p)
 return arc.entries[key]
source_by_hash={};original_parse=ex.parse
def recorded_read(p):
 b=read(p)
 if p.lower().endswith('.tmd'):source_by_hash[hashlib.sha256(b).hexdigest()]=find(p)['path']
 return b
def contextual_parse(b,**kwargs):
 model=original_parse(b,**kwargs);source=source_by_hash.get(hashlib.sha256(b).hexdigest(),'');directory=source.replace('\\','/').rsplit('/',1)[0]
 for o in model['objects']:
  for m in o.get('materials',[]):
   ref=m['texture'].replace('\\','/');name=ref.rsplit('/',1)[-1]
   # Workstation absolute paths are stale. Prefer the texture beside this TMD,
   # rather than another resource with the same basename in another folder.
   if ref.lower() not in arc.entries and (directory+'/'+name).lower() in arc.entries:m['texture']=find(directory+'/'+name)['path']
 return model
ex.read=recorded_read;ex.find=find;ex.INDEX=list(arc.entries.values());ex.parse=contextual_parse
dest=repo/'site/assets/calculator';dest.mkdir(parents=True,exist_ok=True)
temporary=tempfile.TemporaryDirectory(prefix='monato-calculator-');temp=Path(temporary.name);ex.OUT=temp
manifest={};cache={};texture_cache={};failures=[]
catalog=json.loads((repo/'site/catalog.json').read_text(encoding='utf8'))
live={x['Id']:x for x in ns['parseitems'](read('Data/iteminfo.iif'))}
def mod(path):
 r=Reader(read(path));assert r.string()=='Modifiers';assert abs(r.unpack('f')[0]-.1)<1e-5
 base=r.string();parts=[];overrides={};effects=[]
 for _ in range(r.count()):
  kind=r.string();v=r.unpack('f')[0]
  if kind=='Equip':
   assert abs(v-1.1)<1e-5
   source,bone,animation=r.string(),r.string(),r.string();assert r.count()==0
   textures={r.count():r.string() for _ in range(r.count())}
   if animation and animation.lower()!=base.lower():parts.append(dict(source=animation,bone=bone or None,textures={}))
   parts.append(dict(source=source,bone=bone or None,textures=textures))
  elif kind=='Texture':
   assert abs(v-.1)<1e-5
   slot,mesh,texture=r.count(),r.string(),r.string();overrides[(mesh,slot)]=texture
  elif kind=='Effect':
   assert abs(v-.2)<1e-5;effects.append(r.string());assert r.unpack('2B')==(0,0)
  else:raise ValueError('Unsupported MOD '+kind)
 assert r.pos==len(r.data),'MOD trailing bytes'
 return base,parts,overrides,effects
def quat(q):
 x,y,z,w=np.array(q)/max(np.linalg.norm(q),1e-10);m=np.eye(4)
 m[:3,:3]=[[1-2*y*y-2*z*z,2*x*y-2*z*w,2*x*z+2*y*w],[2*x*y+2*z*w,1-2*x*x-2*z*z,2*y*z-2*x*w],[2*x*z-2*y*w,2*y*z+2*x*w,1-2*x*x-2*y*y]];return m
def bake(path,key):
 raw=path.read_bytes();jl=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jl]);bn=raw[28+jl:]
 def acc(i):
  a=doc['accessors'][i];b=doc['bufferViews'][a['bufferView']];dim={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
  return np.frombuffer(bn,dtype={5126:'<f4',5123:'<u2'}[a['componentType']],count=a['count']*dim,offset=b.get('byteOffset',0)+a.get('byteOffset',0)).reshape(-1,dim).copy()
 nodes=[dict(n) for n in doc['nodes']]
 for ch in doc.get('animations',[{'channels':[]}])[0]['channels']:
  s=doc['animations'][0]['samplers'][ch['sampler']];nodes[ch['target']['node']][ch['target']['path']]=acc(s['output'])[0].tolist()
 local=[]
 for n in nodes:
  m=quat(n.get('rotation',[0,0,0,1]));m[:3,:3]*=np.array(n.get('scale',[1,1,1]))[None,:];m[:3,3]=n.get('translation',[0,0,0]);local.append(m)
 parents={c:i for i,n in enumerate(nodes) for c in n.get('children',[])};world={}
 def wm(i):
  if i not in world:world[i]=wm(parents[i])@local[i] if i in parents else local[i]
  return world[i]
 images=[]
 for im in doc['images']:
  v=doc['bufferViews'][im['bufferView']];b=bn[v['byteOffset']:v['byteOffset']+v['byteLength']];h=hashlib.sha256(b).hexdigest()[:20];file=h+'.webp'
  if h not in texture_cache:
   image=Image.open(io.BytesIO(b)).convert('RGBA');image.save(dest/file,'WEBP',lossless=True);texture_cache[h]=file
  images.append(file)
 primitives=[];binary=bytearray()
 def block(a,dtype):
  binary.extend(b'\0'*(-len(binary)%4));offset=len(binary);raw=np.asarray(a,dtype=dtype).tobytes();binary.extend(raw);return [offset,len(raw)]
 for ni,n in enumerate(nodes):
  if 'mesh' not in n:continue
  for p in doc['meshes'][n['mesh']]['primitives']:
   at=p['attributes'];pos=acc(at['POSITION']);pos4=np.c_[pos,np.ones(len(pos))]
   if 'skin' in n:
    skin=doc['skins'][n['skin']];ib=acc(skin['inverseBindMatrices']);joint=acc(at['JOINTS_0']).astype(int);weights=acc(at['WEIGHTS_0']);result=np.zeros_like(pos4)
    mats=np.array([wm(j)@m.reshape(4,4,order='F') for j,m in zip(skin['joints'],ib)])
    for k in range(4):result+=np.einsum('nij,nj->ni',mats[joint[:,k]],pos4)*weights[:,k,None]
    pos=result[:,:3]
   else:pos=(wm(ni)@pos4.T).T[:,:3]
   mat=doc['materials'][p['material']];ti=mat['pbrMetallicRoughness']['baseColorTexture']['index'];texture=images[doc['textures'][ti]['source']]
   idx=acc(p['indices']).ravel();norm=np.zeros_like(pos)
   for a,b,c in idx.reshape(-1,3):
    normal=np.cross(pos[b]-pos[a],pos[c]-pos[a]);norm[a]+=normal;norm[b]+=normal;norm[c]+=normal
   norm/=np.maximum(np.linalg.norm(norm,axis=1)[:,None],1e-9)
   assert np.isfinite(pos).all() and len(pos)<65536
   primitives.append({'position':block(pos,'<f4'),'normal':block(norm,'<f4'),'uv':block(acc(at['TEXCOORD_0']),'<f4'),'indices':block(idx,'<u2'),'count':len(idx),'texture':texture,'alpha':mat.get('alphaMode','OPAQUE')})
 assert primitives,'No wearable geometry'
 header=json.dumps({'primitives':primitives},separators=(',',':')).encode();header+=b' '*(-len(header)%4)
 (dest/(key+'.mesh')).write_bytes(struct.pack('<I',len(header))+header+binary)
 return key+'.mesh'
def convert(path,sex,parts_override=None):
 key=hashlib.sha256((path.lower()+sex).encode()).hexdigest()[:20]
 if key in cache:return cache[key]
 base,parts,overrides,effects=mod(path) if parts_override is None else (f'Characters/{"female" if sex=="f" else "male"}_ani_all.tmd',parts_override,{},[])
 setup={'parts':[{'source':base,'bone':None,'textures':{}}]+parts,'overrides':overrides,'scale':[1.3]*3,'animation':base,'editor_translation':[0,0,0]}
 info=ex.convert({'id':0,'assembly':path if parts_override is None else base,'setup':setup,'requested_clips':['AA'],'require_idle':False,'texture_root':'Characters/'})
 file=bake(temp/info['output'],key);cache[key]=file
 for x in info['manifest']:manifest[x['source']]=x['sha256']
 if parts_override is None:manifest[find(path)['path']]=hashlib.sha256(read(path)).hexdigest()
 return file
data={'defaults':{},'items':{},'constants':json.loads((root/'monato-esprit-local/fixtures/moonrise-trial/progression_original.json').read_text(encoding='utf8'))['Constants']}
for sex in ['f','m']:
 defaults={}
 for slot,p in [('4','upper'),('5','lower'),('6','hands'),('7','foot')]:defaults[slot]=convert(f'Characters/Figures/{p}({sex}).mod',sex)
 face='Characters/Girl_face_01.TMD' if sex=='f' else 'Characters/Boy_face_01.TMD'
 hair=f'Characters/Hair/{sex}_hair_a_a.TMD'
 defaults['face']=convert('face-'+sex,sex,[{'source':face,'bone':'Bip01 Head','textures':{}}])
 defaults['hair']=convert('hair-'+sex,sex,[{'source':hair,'bone':'Bip01 Head','textures':{}}])
 data['defaults'][sex]=defaults
for x in catalog['items']:
 if not x.get('equipment') or x['equipment']['slot'] not in [1,2,3,4,5,6,7,8]:continue
 model=x.get('appearance',{}).get('model') or x.get('wing',{}).get('model') or live[x['id']]['Model']
 profiles={}
 for sex in ['f','m']:
  path=str(Path(model).with_suffix(''))+f'({sex}).mod'
  try:
   if path.lower().replace('\\','/') not in arc.entries:path=model
   profiles[sex]=convert(path,sex)
  except Exception as e:failures.append({'id':x['id'],'sex':sex,'model':path,'error':str(e)})
 data['items'][str(x['id'])]=profiles
 if len(data['items'])%40==0:print('Exported',len(data['items']),flush=True)
(repo/'site/calculator-data.js').write_text("'use strict';\nconst calculatorData="+json.dumps(data,separators=(',',':'))+';\n',encoding='utf8')
assert hashlib.sha256(read('Data/ConstTable.ini')).hexdigest()==json.loads((root/'monato-esprit-local/fixtures/moonrise-trial/progression_original.json').read_text(encoding='utf8'))['Sources']['ConstTable.ini']
audit={'date':'2026-10-10','constantsSource':'Data/ConstTable.ini','constantsSha256':hashlib.sha256(read('Data/ConstTable.ini')).hexdigest(),'appearanceSource':'Active client archives; item source IDs and current atlas appearance overrides','pose':'Shared source AA first frame; original skin weights and bone attachments, editor positions ignored','files':list(cache.values()),'textures':list(texture_cache.values()),'manifest':manifest,'failures':failures,'notes':'Jewelry has no character mesh in the selected source records; icons and all source bonuses remain available. Effects/particles are not rendered.'}
audit['formulaSources']=[{'path':str(f.relative_to(root)).replace('\\','/'),'sha256':hashlib.sha256(f.read_bytes()).hexdigest()} for f in [root/'monato-esprit-local/fixtures/moonrise-trial/progression_original.json',root/'monato-esprit-local/diagnostics/progression-20261001/formulas.md',root/'monato-esprit-local/local_enchant_protocol.ps1']]
audit['formulaScope']='Source class/level baseline plus intact equipment and one compatible source enchantment per item; no refinement, birth sign, learned passives or temporary buffs.'
(repo/'site/calculator-assets-audit.json').write_text(json.dumps(audit,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
print('DONE',len(cache),'models',len(texture_cache),'textures',len(failures),'failures',flush=True)
if failures:print(json.dumps(failures[:8]),flush=True)



expected=set(audit['files']+audit['textures'])
resolved=dest.resolve();assert resolved.is_relative_to((repo/'site').resolve()) and resolved.name=='calculator'
for p in dest.iterdir():
 if p.name not in expected:
  assert p.is_file() and p.resolve().parent==resolved;p.unlink()
temporary.cleanup()
