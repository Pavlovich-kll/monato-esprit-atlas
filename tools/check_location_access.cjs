process.chdir(require('path').resolve(__dirname,'..'));
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const c=vm.createContext({window:{},localStorage:{getItem:()=>null},document:{},classEquipmentLabel:()=> 'Source equipment'});
vm.runInContext(fs.readFileSync('site/data.js','utf8'),c);
vm.runInContext(fs.readFileSync('site/skill-access.js','utf8'),c);
vm.runInContext(fs.readFileSync('site/location-access.js','utf8'),c);
const app=fs.readFileSync('site/app.js','utf8');vm.runInContext(app.slice(0,app.indexOf('const mechanics=')),c);
const d=JSON.parse(fs.readFileSync('site/catalog.json','utf8')),audit=JSON.parse(fs.readFileSync('site/location-access-audit.json','utf8'));
assert.strictEqual(d.locations.length,28);assert.strictEqual(d.locations.reduce((n,l)=>n+l.variants.length,0),37);
assert.strictEqual(audit.routes.length,96);assert.strictEqual(audit.meta.enabledSourceRoutes,77);
const a=zone=>d.locations.flatMap(l=>l.variants).find(v=>v.zones.includes(zone)).access;
assert.strictEqual(a(502).explicitEntryQuest,500010001);assert.strictEqual(a(1).globalQuest,500000003);
for(const [zone,level] of [[506,5],[510,8],[514,13],[518,18],[522,23],[526,28],[530,33],[534,38],[538,38],[542,40]])assert.strictEqual(a(zone).minimumReachableLevel,level);
assert.strictEqual(a(5).status,'routes_disabled');assert.strictEqual(a(10).minimumReachableLevel,null);assert.strictEqual(a(3).status,'source_route_only');
const warehouse=d.locationAccess.routes.find(r=>r.kind==='npc'&&r.targetZone===506);assert.strictEqual(warehouse.minimumLevel,3);assert.strictEqual(warehouse.effectiveRouteLevel,5);
const temple=d.locationAccess.routes.find(r=>r.kind==='npc'&&r.targetZone===522);assert.strictEqual(temple.questRequirement,null);
for(const lang of ['ru','en']){
 vm.runInContext(`lang=${JSON.stringify(lang)}`,c);
 for(const l of d.locations){let html=vm.runInContext(`locationAccessBadge(L.get(${JSON.stringify(l.id)}))`,c);assert(!html.includes('undefined'));
  for(let i=0;i<l.variants.length;i++){html=vm.runInContext(`locationAccessPanel(L.get(${JSON.stringify(l.id)}),L.get(${JSON.stringify(l.id)}).variants[${i}])`,c);assert(!html.includes('undefined'));assert(!html.includes('NaN'));if(!l.variants[i].zones.length)assert(!html.includes('Lv 23'));}
 }
}
assert(fs.readFileSync('site/index.html','utf8').includes('location-access.js?v=20261008'));
console.log('All 28 locations / 37 variants render in RU and EN; 96 route rules, quest gates, effective levels and disabled/archive cases verified.');
