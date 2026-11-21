
'use strict';
const $=s=>document.querySelector(s), main=$('#main'),dlg=$('#dlg'),body=$('#body'),key='dailyform-v1',subjects=['Biology 9700','Chemistry 9701','Physics 9702','Pure Mathematics 1'],methods=['Active recall','Past paper','Corrections','Notes'],esc=s=>String(s).replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
const now=new Date(),iso=d=>[d.getFullYear(),String(d.getMonth()+1).padStart(2,'0'),String(d.getDate()).padStart(2,'0')].join('-'),today=iso(now),fmt=(d,o)=>new Intl.DateTimeFormat('en-GB',o).format(d),monday=new Date(now);monday.setDate(now.getDate()-(now.getDay()+6)%7);
let selected=today,tab='Overview',rows=[],locked=true,revision=0,busy=false;
function valid(r){return r&&typeof r.id==='string'&&typeof r.title==='string'&&r.title.trim()&&typeof r.date==='string'&&/^\d{4}-\d\d-\d\d$/.test(r.date)&&iso(new Date(r.date+'T12:00'))===r.date&&(r.type==='Academic'?subjects.includes(r.subject)&&methods.includes(r.method)&&Number.isInteger(r.minutes)&&r.minutes>0:r.type==='Gym'&&Number.isInteger(r.reps)&&r.reps>0&&Number.isInteger(r.sets)&&r.sets>0&&Number.isFinite(r.kg)&&r.kg>=0)}
function parse(s){let v=JSON.parse(s);if(!Array.isArray(v)||!v.every(valid)||new Set(v.map(x=>x.id)).size!==v.length)throw Error();return v}

const syncStatus=$('#syncstatus');
function showStatus(message){syncStatus.textContent=message}
function setBusy(value){
    busy=value;
    document.querySelectorAll('dialog button,dialog input,dialog select,#refresh').forEach(el=>el.disabled=value);
}
async function loadRecords(){
    if(busy)return;
    setBusy(true);
    showStatus('Loading your records…');
    try{
        const response=await fetch('/api/records/',{cache:'no-store'});
        if(response.status===401){location.assign('/login/');return}
        if(!response.ok)throw Error('Could not load your records. Try Refresh records.');
        const data=await response.json();
        rows=parse(JSON.stringify(data.records));
        revision=data.revision;
        locked=false;
        render();
        showStatus('Records saved to your account');
    }catch(error){showStatus(error.message)}
    finally{setBusy(false)}
}
async function save(next){
    if(locked||busy){alert('Wait for your account records to finish loading.');return false}
    setBusy(true);
    showStatus('Saving…');
    try{
        const token=document.querySelector('[name=csrfmiddlewaretoken]').value;
        const response=await fetch('/api/records/',{
            method:'PUT',
            headers:{'Content-Type':'application/json','X-CSRFToken':token},
            body:JSON.stringify({records:next,revision})
        });
        if(response.status===401)throw Error('Your session expired. Sign in again, then retry your edit.');
        if(response.status===403)throw Error('Your sign-in changed. Reload this page and try again.');
        const data=await response.json();
        if(!response.ok)throw Error(data.error||'Unable to save. Please try again.');
        revision=data.revision;
        rows=next;
        showStatus('Records saved to your account');
        return true;
    }catch(error){showStatus(error.message);alert(error.message);return false}
    finally{setBusy(false)}
}
$('#refresh').onclick=loadRecords;
$('#close-dialog').onclick=()=>{if(!busy)dlg.close()};
dlg.addEventListener('cancel',event=>{if(busy)event.preventDefault()});
const book='<svg viewBox="0 0 160 140" aria-hidden="true"><g transform="rotate(-13 85 75)" stroke="#262b37" stroke-width="2.4" stroke-linejoin="round"><path fill="#ab95d5" d="m20 58 83-20 38 47-84 25z"/><path fill="#fff7df" d="m23 57 79-19 36 41-82 24z"/><path fill="#9881c6" d="m17 47 84-20 39 45-85 25z"/><path fill="#fff9df" d="m25 46 76-18 33 37-79 22z"/><path fill="#bfaae4" d="m18 37 81-20 36 42-82 23z"/><path fill="none" d="m32 34 36 43m-8-37 27-7m-24 11 19-5"/></g></svg>';
const bell='<svg viewBox="0 0 160 140" aria-hidden="true"><g transform="rotate(-29 80 70)" stroke="#26342e" stroke-width="2.5" stroke-linejoin="round"><rect x="23" y="63" width="116" height="14" rx="5" fill="#f3f6df"/><g fill="#88ac83"><rect x="24" y="44" width="14" height="51" rx="5"/><rect x="39" y="34" width="18" height="71" rx="5"/><rect x="101" y="34" width="18" height="71" rx="5"/><rect x="120" y="44" width="14" height="51" rx="5"/></g><path d="M45 41v56m62-56v56" stroke="#cfdfbc"/></g></svg>';
function card(a){return '<article class="card '+(a?'':'gym')+'"><span class="tag">'+(a?'Study log':'Workout log')+'</span><h2>'+(a?'Academic':'Gym')+'</h2><p>'+(a?'Subjects, topics & revision time':'Exercises, sets & working loads')+'</p>'+ (a?book:bell)+'<button data-add="'+(a?'Academic':'Gym')+'">＋ Log '+(a?'revision':'exercise')+'</button></article>'}
function list(items){return items.length?items.map(r=>'<div class="row"><span class="badge '+(r.type==='Gym'?'g':'')+'">'+(r.type==='Gym'?'G':'A')+'</span><div class="text"><b>'+esc(r.title)+'</b><small>'+esc(r.type==='Academic'?r.subject+' · '+r.method+' · '+r.minutes+' min':r.sets+' sets × '+r.reps+' reps · '+r.kg+' kg')+' · '+esc(r.date)+'</small></div><button class="plain" data-edit="'+esc(r.id)+'">Edit</button></div>').join(''):'<p class="empty">No entries yet.</p>'}
function render(){document.querySelectorAll('[data-tab]').forEach(b=>b.setAttribute('aria-current',b.dataset.tab===tab?'page':'false'));let overview=tab==='Overview',a=tab==='Academic',items=rows.filter(r=>r.type===tab).sort((x,y)=>y.date.localeCompare(x.date));main.innerHTML='<div class="date">'+fmt(now,{weekday:'long',day:'numeric',month:'long',year:'numeric'})+'</div><h1>'+(overview?'Your dashboard':a?'Academic log':'Gym log')+'</h1><p>'+(overview?'Your revision and training in one place.':a?'Track the topics you revise across your four A-Level subjects.':'Record each exercise and compare your training over time.')+'</p>'+(locked?'<p id="msg">Your account records are loading. Use Refresh records if loading fails.</p>':'');
if(overview){let days='';for(let i=0;i<7;i++){let d=new Date(monday);d.setDate(d.getDate()+i);let date=iso(d);days+='<button class="day '+(date===selected?'active ':'')+(rows.some(r=>r.date===date)?'logged':'')+'" data-day="'+date+'" aria-pressed="'+(date===selected)+'">'+fmt(d,{weekday:'short'})+'<b>'+d.getDate()+'</b><i></i></button>'}main.innerHTML+='<div class="cards">'+card(true)+card(false)+'</div><section class="section"><div class="weekhead"><h2>This week</h2><span class="muted">Week of '+fmt(monday,{month:'short',day:'numeric'})+'</span></div><div class="days">'+days+'</div><div class="list">'+list(rows.filter(r=>r.date===selected))+'</div></section>'}
else{main.innerHTML+='<section class="section"><div class="heading"><h2>History</h2><button class="primary" data-add="'+tab+'">＋ Log '+(a?'revision':'exercise')+'</button></div><div class="stats">'+(a?'<div><b>'+items.reduce((n,r)=>n+r.minutes,0)+'</b><span>Minutes revised</span></div>':'<div><b>'+items.reduce((n,r)=>n+r.sets,0)+'</b><span>Sets logged</span></div>')+'<div><b>'+new Set(items.map(r=>r.date)).size+'</b><span>Active days</span></div></div><label>Filter '+(a?'by subject':'by exercise')+'<select id="filter"><option value="">All '+(a?'subjects':'exercises')+'</option>'+opts(a?subjects:[...new Set(items.map(r=>r.title))])+'</select></label><div class="list" id="history">'+list(items)+'</div></section>';$('#filter').onchange=e=>$('#history').innerHTML=list(items.filter(r=>!e.target.value||(a?r.subject:r.title)===e.target.value));}
}function opts(v){return v.map(x=>'<option>'+esc(x)+'</option>').join('')}
function modal(t,html){$('#dt').textContent=t;body.innerHTML=html;dlg.showModal()}
function form(type,r){let a=type==='Academic';modal((r?'Edit ':'Log ')+(a?'revision':'exercise'),'<form><label>Date<input required name="date" type="date"></label>'+(a?'<label>Subject<select name="subject">'+opts(subjects)+'</select></label>':'')+'<label>'+(a?'Chapter or topic':'Exercise')+'<input required maxlength="120" name="title" placeholder="'+(a?'e.g. Gas exchange':'e.g. Iso-lateral row')+'"></label>'+(a?'<label>Revision method<select name="method">'+opts(methods)+'</select></label><label>Duration (minutes)<input required type="number" min="1" name="minutes"></label>':'<label>Sets<input required type="number" min="1" name="sets"></label><label>Reps per set<input required type="number" min="1" name="reps"></label><label>Weight (kg, 0 for bodyweight)<input required type="number" min="0" step="any" name="kg"></label>')+'<button class="primary">Save entry</button>'+(r?'<button type="button" class="action" id="remove">Delete entry</button>':'')+'</form>');let f=body.querySelector('form');for(const [k,v] of Object.entries(r||{date:tab==='Overview'?selected:today})){if(f.elements.namedItem(k))f.elements.namedItem(k).value=v}f.onsubmit=async e=>{e.preventDefault();let data=Object.fromEntries(new FormData(f));data.title=data.title.trim();for(let k of ['minutes','sets','reps','kg'])if(k in data)data[k]=Number(data[k]);let entry={...data,type,id:r?r.id:crypto.randomUUID()};if(!valid(entry)){alert('Check the entry details.');return}if(await save(r?rows.map(x=>x.id===r.id?entry:x):[entry,...rows])){dlg.close();render()}};if(r)$('#remove').onclick=async()=>{if(confirm('Delete this entry?')&&await save(rows.filter(x=>x.id!==r.id))){dlg.close();render()}}}
document.addEventListener('click',e=>{let b=e.target.closest('button');if(!b)return;let d=b.dataset;if(d.tab){tab=d.tab;render()}if(d.day){selected=d.day;render()}if(d.add)form(d.add);if(d.edit){let r=rows.find(x=>x.id===d.edit);if(r)form(r.type,r)}});
$('#settings').onclick=()=>{modal('App & backup','<p>On your phone, open the hosted site in Safari or Chrome and choose Add to Home Screen from the share or browser menu.</p><p style="margin-top:12px">Your records are stored in your account. Sign in on another device and use Refresh records to load the latest entries. Export a backup to keep a copy. You can import a backup from the original Dailyform.</p><button class="action" id="backup">Export records</button><label>Import records (merges by entry ID)<input type="file" id="restore" accept=".json,application/json"></label>');$('#backup').onclick=()=>{let url=URL.createObjectURL(new Blob([JSON.stringify(rows,null,2)],{type:'application/json'})),a=document.createElement('a');a.href=url;a.download='dailyform-'+today+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),2000)};$('#restore').onchange=async e=>{try{if(e.target.files[0].size>1500000)throw Error();let incoming=parse(await e.target.files[0].text()),merged=new Map(rows.map(r=>[r.id,r]));incoming.forEach(r=>merged.set(r.id,r));if(await save([...merged.values()])){dlg.close();render()}}catch{alert('Choose a valid Dailyform JSON backup.')}}};

render();
loadRecords();
if(location.protocol==='https:'&&'serviceWorker' in navigator){
    navigator.serviceWorker.register('/sw.js').catch(()=>{});
}
