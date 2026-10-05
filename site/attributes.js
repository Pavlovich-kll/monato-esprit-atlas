'use strict';
// Labels and colors describe the source fields; no values are recalculated.
function attributeCell(label,value,tone='neutral',note='') {
  return `<div class="attribute-cell attribute-${tone}"><dt>${label}${note?`<small>${note}</small>`:''}</dt><dd>${value}</dd></div>`;
}
function attributeMeta(label,value,wide=false) {
  return `<div${wide?' class="attribute-wide"':''}><dt>${label}</dt><dd>${value}</dd></div>`;
}
function attributeEntries(stats,bonus=false) {
  const entries=[],value=v=>(bonus&&v>0?'+':'')+v;
  const add=(label,val,tone='neutral',note='')=>entries.push({label,value:val,tone,note});
  for(const [lo,hi,ru,en,tone] of [[8,9,'Физический урон','Physical damage','physical'],[10,11,'Магический урон','Magic damage','magic']]) {
    if(stats[lo]||stats[hi])add(t(ru,en),bonus?`<span class="attribute-range"><span><small>${t('мин.','min.')}</small> ${value(stats[lo])}</span><span><small>${t('макс.','max.')}</small> ${value(stats[hi])}</span></span>`:range([stats[lo],stats[hi]]),tone);
  }
  const labels={
    19:['Макс. здоровье · HP','Max. health · HP','health'],20:['Макс. мана · MP','Max. mana · MP','magic'],
    12:['Физическая защита','Physical defense','physical'],13:['Магическая защита','Magic defense','magic'],
    3:['Сила · STR','Strength · STR','primary'],4:['Телосложение · CON','Constitution · CON','primary'],
    5:['Ловкость · DEX','Dexterity · DEX','primary'],6:['Интеллект · INT','Intelligence · INT','primary'],7:['Мудрость · WIS','Wisdom · WIS','primary'],
    14:['Критический удар','Critical','physical',t('показатель','rating')],17:['Точность','Hit','primary',t('показатель','rating')],
    18:['Уклонение','Evasion','primary',t('показатель','rating')],21:['Блок','Block','physical',t('показатель','rating')],
    2:['Скорость движения','Movement speed','primary',t('единицы клиента','client units')]
  };
  for(const key of [19,20,12,13,3,4,5,6,7,14,17,18,21,2])if(stats[key]){const [ru,en,tone,note]=labels[key];add(t(ru,en),value(stats[key]),tone,note)}
  if(stats[0])add(t('Интервал атак','Attack interval'),`${stats[0]>0?'−':'+'}${Math.abs(stats[0])/10}%`,'physical',t('изменение','modifier'));
  if(stats[1])add(t('Скорость произнесения','Casting speed'),value(stats[1]),'magic',t('поле клиента · единицы не установлены','client field · units unresolved'));
  return entries;
}
function attributePreview(stats,bonus=false) {
  const entries=attributeEntries(stats,bonus);
  return `<div class="attribute-preview">${entries.slice(0,4).map(x=>`<span class="attribute-${x.tone}"><span>${x.label}${x.note?`<small>${x.note}</small>`:''}</span><strong>${x.value}</strong></span>`).join('')}</div>${entries.length>4?`<p class="attribute-preview-more">${t('Ещё показателей в карточке: ','More attributes in the profile: ')}${entries.length-4}</p>`:''}`;
}
function monsterAttributes(x) {
  return `<section class="detail-section compact-attributes"><div class="attribute-heading"><h3>${t('Характеристики','Attributes')}</h3>${badge(t('Оригинальный клиент','Original client'),'muted')}</div><dl class="attribute-grid">${attributeCell(t('Здоровье · HP','Health · HP'),range(x.hp),'health')}${attributeCell(t('Физический урон','Physical damage'),range(x.physical),'physical')}${attributeCell(t('Магический урон','Magic damage'),range(x.magic),'magic')}</dl></section>`;
}
