process.chdir(require('path').resolve(__dirname,'..'));
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const context=vm.createContext({window:{},localStorage:{getItem:()=>null},document:{addEventListener:()=>{}},wingCanonicalId:id=>id,potionAttributes:()=>'',wingProfile:()=>'',recoverySummary:()=>''});
for(const file of ['data.js','attributes.js','scroll-variants.js','item-stats.js','equipment-filters.js'])vm.runInContext(fs.readFileSync('site/'+file,'utf8'),context);
const app=fs.readFileSync('site/app.js','utf8');vm.runInContext(app.slice(0,app.indexOf('const mechanics=')),context);
for(const line of app.split('\n'))if(line.startsWith('function itemHTML(')||line.startsWith('function itemImages(')||line.startsWith('function paginate(')||line.startsWith('function filterChips('))vm.runInContext(line,context);
const source=JSON.parse(fs.readFileSync('site/catalog.json','utf8')),audit=JSON.parse(fs.readFileSync('site/equipment-filter-audit.json','utf8'));let checks=0;
function set(category,filters={}){context.filterInput={classId:'',minLevel:'',maxLevel:'',type:'',...filters};context.categoryInput=category;vm.runInContext('category=categoryInput;Object.assign(equipmentFilters,filterInput)',context);}
function rows(){return vm.runInContext('equipmentFilteredItems()',context)}
function check(value){checks++;assert(value)}
set('all');check(rows().length===source.items.length);check(Object.keys(audit.nativeTypes).length===309);
set('all',{maxLevel:'0'});check(rows().some(x=>x.id===1001));check(rows().every(x=>x.equipment&&x.equipment.minLevel===0));
for(let id=1;id<=8;id++){set('all',{classId:String(id)});check(rows().some(x=>x.id===1001));check(rows().every(x=>(x.equipment.classMask&(1<<(id-1)))!==0));check(!rows().some(x=>x.enchantment));}
set('weapons',{type:'weapon:52'});check(rows().length===2);check(rows().some(x=>x.id===110000));
set('clothing',{type:'slot:6'});check(rows().length===40);check(rows().every(x=>x.equipment.slot===6));
set('accessories',{type:'slot:17'});check(rows().length===11);set('wings',{type:'slot:8'});check(rows().length===12);
set('weapons',{classId:'7',maxLevel:'20'});check(rows().length>0);check(rows().every(x=>x.equipment.minLevel<=20&&(x.equipment.classMask&64)));
set('all',{minLevel:'20',maxLevel:'20'});check(rows().length>0);check(rows().every(x=>x.equipment.minLevel===20));
for(const f of [{minLevel:'21',maxLevel:'20'},{minLevel:'-1'},{maxLevel:'41'},{minLevel:'1.5'}]){set('all',f);check(rows().length===0);check(vm.runInContext('equipmentFilterIssue()',context).length>0);}
set('scrolls',{classId:'7',maxLevel:'1',type:'weapon:59'});check(rows().length===116);check(vm.runInContext('equipmentFilterHTML()',context)==='');
set('potions',{classId:'1',minLevel:'40'});check(rows().length>0);check(rows().every(x=>x.recovery));
for(const language of ['ru','en']){vm.runInContext(`lang=${JSON.stringify(language)}`,context);set('weapons',{type:'weapon:59',maxLevel:'20'});const html=vm.runInContext('equipmentFilterHTML()',context);check(html.includes('equipment-class'));check(html.includes('weapon:59'));check(!html.includes('slot:6'));check(html.includes('value="20"'));}
check(source.items.every(x=>!x.equipment||audit.nativeTypes[x.id]!==undefined));
console.log(`PASS ${checks} equipment filter checks: classes, inclusive levels, exact original weapon types, clothing slots, unrestricted Pouch, invalid ranges, non-equipment categories and RU/EN.`);
