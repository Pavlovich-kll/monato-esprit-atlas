"""Read verified client archive/table parser and transcode exact recipe icons."""
import ast,struct,zlib,re,io,sys,json,hashlib
from pathlib import Path
from PIL import Image
project,game=map(Path,sys.argv[1:3]);site=Path(__file__).resolve().parents[1]/'site'
tree=ast.parse((project/'monato-esprit-local/diagnostics/client1004-equipment-skills-20261005/audit.py').read_text(encoding='utf-8-sig'));ns={'struct':struct,'zlib':zlib,'re':re,'Path':Path}
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,(ast.ClassDef,ast.FunctionDef))and getattr(n,'name','')in['Archive','parseitems']],type_ignores=[]),'source-reader','exec'),ns)
arc=ns['Archive'](game);rows={r['Id']:r for r in ns['parseitems'](arc.read('Data/itemInfo.iif'))};data=json.loads((site/'craft-data.js').read_text(encoding='utf8').removeprefix('window.CRAFT_DATA=').rstrip(';\n'));audit=[]
for x in data['items']:
 source=rows[x['id']]['Icon']
 try:raw=arc.read(source)
 except KeyError:
  fallback=project/'monato-client-analysis/client'/source.replace('\\','/')
  if not fallback.is_file():audit.append({'id':x['id'],'source':source,'missing':True});continue
  raw=fallback.read_bytes()
 target=site/f'assets/item-{x["id"]}.webp';Image.open(io.BytesIO(raw)).convert('RGBA').save(target,format='WEBP',lossless=True);audit.append({'id':x['id'],'source':source,'sha256':hashlib.sha256(raw).hexdigest()})
(site/'craft-icon-audit.json').write_text(json.dumps(audit,indent=2)+'\n');print(json.dumps({'exported':len(audit)}))
