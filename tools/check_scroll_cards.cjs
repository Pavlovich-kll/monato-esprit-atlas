process.chdir(require('path').resolve(__dirname,'..'));
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const c=vm.createContext({window:{},localStorage:{getItem:()=>null},document:{},wingCanonicalId:id=>id,potionAttributes:()=>'',wingProfile:()=>'',recoverySummary:()=>''});
for(const f of ['data.js','attributes.js','item-stats.js'])vm.runInContext(fs.readFileSync('site/'+f,'utf8'),c);
const app=fs.readFileSync('site/app.js','utf8');vm.runInContext(app.slice(0,app.indexOf('const mechanics=')),c);for(const line of app.split('\n'))if(line.startsWith('function itemHTML(')||line.startsWith('function itemImages('))vm.runInContext(line,c);
const data=JSON.parse(fs.readFileSync('site/catalog.json','utf8')),scrolls=data.items.filter(x=>x.enchantment);assert.equal(scrolls.length,52);
let count=0;
for(const language of ['ru','en']){
 vm.runInContext(`lang=${JSON.stringify(language)}`,c);
 for(const x of scrolls){c.testItem=x;const html=vm.runInContext('itemHTML(testItem,2,1)',c),entries=vm.runInContext('attributeEntries(testItem.enchantment.stats,true)',c);
 assert(html.includes('scroll-card')&&html.includes(`data-id="${x.id}"`)&&html.includes('type="button"'));
 assert(html.includes('×2'));assert(html.includes(language==='ru'?'На выбор':'Reward choice'));
 assert(html.includes(vm.runInContext('esc(equipmentSlot(testItem.enchantment.slot))',c)));
 assert.equal((html.match(/class="scroll-effect"/g)||[]).length,entries.length);
 for(const entry of entries){assert(html.includes(entry.label));assert(html.includes(entry.value));if(entry.note)assert(html.includes(entry.note));}
 assert(!/Успех|Плата|Стоимость|Success|Cost|Fee/.test(html));
 const detail=vm.runInContext('itemCharacteristics(testItem)',c);assert(!/Успех ·|Стоимость ·|Success ·|Cost ·/.test(detail));count++;
 }
 const ordinary=data.items.find(x=>x.equipment&&!x.enchantment);c.testItem=ordinary;assert(!vm.runInContext('itemHTML(testItem)',c).includes('scroll-card'));
 const normal=vm.runInContext('itemHTML(70008)',c);assert(normal.includes('scroll-card')&&normal.includes('70008'));
}
console.log(`PASS ${count} source enchantment cards: RU/EN, all effects, correct equipment slot, list/loot IDs, reward counts, no success/fee; normal items retain their layout.`);
