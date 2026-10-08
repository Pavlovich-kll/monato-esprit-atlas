process.chdir(require('path').resolve(__dirname,'..'));
const fs=require('fs'),vm=require('vm'),assert=require('assert');
const c=vm.createContext({window:{},localStorage:{getItem:()=>null},document:{},classEquipmentLabel:()=> 'Source equipment'});
vm.runInContext(fs.readFileSync('site/data.js','utf8'),c);vm.runInContext(fs.readFileSync('site/skill-access.js','utf8'),c);
let app=fs.readFileSync('site/app.js','utf8');assert(app.includes('skillMechanicsDetails(x)'));assert(app.includes('x.originalDescription?.en||x.description.en'));
vm.runInContext(app.slice(0,app.indexOf('const mechanics=')),c);
const data=JSON.parse(fs.readFileSync('site/catalog.json','utf8'));
for(const lang of ['ru','en']){
 vm.runInContext(`lang=${JSON.stringify(lang)}`,c);
 for(const cls of data.classes){const html=vm.runInContext(`classPage(${JSON.stringify(cls.id)})`,c);assert(!html.includes('undefined'));assert(!html.includes('No separate later unlock thresholds'));}
 for(const skill of data.skills){const html=vm.runInContext(`skillAccessDetails(S.get(${skill.id}))+skillMechanicsDetails(S.get(${skill.id}))`,c);assert(!html.includes('undefined'));assert(!html.includes('NaN'));}
}
console.log('Rendered all 8 class sections and 160 skill details in RU/EN');
