'use strict';
const $=s=>document.querySelector(s);
let csrf='', mission=null, currentView='welcome', switching=false, signalAbort=null, timerInterval=null, editingName=false;
const titles=['Cuenta bien, lee mejor','La contraseña imposible','El algoritmo corrompido','Compuertas en serie','Haz zoom','Encuentra las diferencias','La transmisión interceptada','Transmisión de doble cifrado','Señales intermitentes','Mensaje final'];
const kinds=['LECTURA Y BÚSQUEDA','DEDUCCIÓN NUMÉRICA','LÓGICA DE PYTHON','LÓGICA DIGITAL','OBSERVACIÓN DIGITAL','ATENCIÓN VISUAL','ESCUCHA Y RAZONAMIENTO','CRIPTOGRAFÍA Y AUDIO','CÓDIGO MORSE','INTEGRACIÓN DE PISTAS'];
const sleep=ms=>new Promise(r=>setTimeout(r,ms));
function updateMusic(){
  let scene=currentView;
  if(scene==='challenge') scene=mission.stage<4?'early':mission.stage<8?'middle':'final';
  window.CodigoMusic.setScene(scene,{paused:currentView==='challenge'&&[6,7,8].includes(mission.stage)});
}
async function api(path,body,method='POST'){
  const res=await fetch(path,{method,headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},...(body?{body:JSON.stringify(body)}:{})});
  const data=await res.json();if(!res.ok)throw new Error(data.error||'No se pudo completar la solicitud.');return data;
}
async function transition(work){
  while(switching)await sleep(40);switching=true;
  stopSignal();
  const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;
  const overlay=$('#transition');overlay.classList.add('active');
  await sleep(reduced?40:450);
  try{await work();await sleep(reduced?100:1100);}finally{overlay.classList.remove('active');switching=false;await sleep(reduced?0:350);}
}
function show(name){document.querySelectorAll('.view').forEach(v=>v.hidden=v.id!==name);currentView=name;$('#back-home').hidden=name==='welcome';updateMusic();window.scrollTo(0,0);}
function showHome(){
  clearInterval(timerInterval);stopSignal();
  const active=mission&&!mission.finished;$('#welcome').classList.toggle('has-active-mission',Boolean(active));
  $('#resume').hidden=!active;$('#edit-club-name').hidden=!active;$('#resume-note').hidden=!active;$('#begin').hidden=Boolean(active);
  $('#resume-note').textContent=active?(mission.club_name===('Equipo '+mission.team)?'Equipo '+mission.team:mission.club_name+' · Equipo '+mission.team)+' · Reto '+(mission.stage+1)+' de 10':'';
  show('welcome');
}
function saveDraft(){if(mission&&!mission.finished&&currentView==='challenge'){try{sessionStorage.setItem('codigo-draft',JSON.stringify({stage:mission.stage,answer:$('#answer').value}));}catch{}}}
function draftAnswer(){try{const d=JSON.parse(sessionStorage.getItem('codigo-draft')||'null');return d&&d.stage===mission.stage?d.answer:'';}catch{return '';}}
async function returnHome(){saveDraft();await transition(showHome);}
$('#back-home').onclick=returnHome;$('#finish-home').onclick=returnHome;
$('#resume').onclick=()=>transition(renderMission);
$('a.event-lockup').addEventListener('click',e=>{if(e.ctrlKey||e.metaKey||e.shiftKey)return;e.preventDefault();returnHome();});
$('#begin').onclick=()=>transition(()=>{editingName=false;$('#team').disabled=false;show('identify');$('#club-name').focus();});
$('#edit-club-name').onclick=()=>transition(()=>{editingName=true;$('#club-name').value=baseText(mission.club_name);$('#team').value=String(mission.team);$('#team').disabled=true;show('identify');$('#club-name').focus();});
$('#team-form').onsubmit=async e=>{e.preventDefault();const btn=e.submitter;btn.disabled=true;$('#team-error').textContent='';try{const data=await api(editingName?'/api/mission/name':'/api/start',{team:Number($('#team').value),club_name:$('#club-name').value.trim()});mission=data.mission;await transition(renderMission);}catch(err){$('#team-error').textContent=err.message;}finally{btn.disabled=false;}};
function tick(){if(!mission||mission.finished)return;const seconds=mission.started?Math.max(0,Math.floor(Date.now()/1000-mission.started)):0;$('#timer').textContent=String(Math.floor(seconds/60)).padStart(2,'0')+':'+String(seconds%60).padStart(2,'0');}
function resource(html){$('#resource').innerHTML=html;}
function stopSignal(){if(signalAbort)signalAbort.abort();signalAbort=null;$('#lamp')?.classList.remove('lit');}
async function startSignal(){
  stopSignal();const controller=new AbortController();signalAbort=controller;const btn=$('#signal-play');btn.textContent='Detener';
  const pause=async ms=>{await sleep(ms);if(controller.signal.aborted)throw new Error('stopped');};
  try{while(!controller.signal.aborted){for(const digit of mission.signal){for(let i=0;i<digit.length;i++){$('#lamp').classList.add('lit');await pause(digit[i]==='.'?400:1200);$('#lamp').classList.remove('lit');if(i<digit.length-1)await pause(400);}await pause(1500);}await pause(1500);}}catch{}finally{if(signalAbort===controller){signalAbort=null;$('#lamp')?.classList.remove('lit');if($('#signal-play'))$('#signal-play').textContent='Reproducir';}}
}
function numericLength(stage){return [1,2,3,5,6,7].includes(stage)?1:stage===8?3:0;}
function baseText(value){return value.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toUpperCase();}
function cleanAnswer(value){
 const length=numericLength(mission.stage);
 if(length)return value.replace(/[^0-9]/g,'').slice(0,length);
 const base=baseText(value);
 return mission.stage===4?base.replace(/[^A-Z0-9 -]/g,'').slice(0,60):base.replace(/[^A-Z ]/g,' ').replace(/ {2,}/g,' ').slice(0,300);
}
function normalizeInput(e){if(e.isComposing)return;const input=e.target;const caret=input.selectionStart;const prefix=cleanAnswer(input.value.slice(0,caret));input.value=cleanAnswer(input.value);if(caret!==null)input.setSelectionRange(prefix.length,prefix.length);}
$('#answer').addEventListener('input',normalizeInput);$('#answer').addEventListener('compositionend',normalizeInput);
$('#club-name').addEventListener('input',e=>{if(!e.isComposing)e.target.value=baseText(e.target.value);});
function showNotice(title,lines,button='Entendido →',action=null){
 const dialog=$('#notice-dialog');$('#notice-title').textContent=title;$('#notice-body').replaceChildren();
 for(const line of lines){const p=document.createElement('p');p.textContent=line;$('#notice-body').append(p);}
 $('#notice-error').textContent='';const confirm=$('#notice-confirm');confirm.textContent=button;
 dialog.oncancel=e=>{if(action)e.preventDefault();};
 confirm.onclick=async()=>{confirm.disabled=true;try{if(action)await action();dialog.close();}catch(err){$('#notice-error').textContent=err.message;}finally{confirm.disabled=false;}};
 if(!dialog.open)dialog.showModal();
}
function showClassroom(){showNotice('Destino del reto 6',[mission.classroom,'Busca allí la carta del reto 6.']);}
function showMorse(){
 showNotice('Morse: números',['Punto: señal corta. Raya: señal larga.']);
 const table=document.createElement('div');table.className='morse-reference';
 ['-----','·----','··---','···--','····-','·····','-····','--···','---··','----·'].forEach((pattern,i)=>{const cell=document.createElement('div');cell.textContent=i+'  '+pattern;table.append(cell);});$('#notice-body').append(table);
}
function renderMission(){
 if(mission.finished){show('finish');$('#finish-note').textContent='Desafío finalizado.';clearInterval(timerInterval);return;}
 if(mission.awaiting_start){
  show('challenge');$('#answer-form').hidden=true;resource('');$('#challenge-title').textContent='Primer reto resuelto';$('#question').textContent='';$('#challenge-help').hidden=true;$('#team-label').textContent=mission.club_name;$('#assigned-team').textContent='Equipo '+mission.team;$('#stage-label').textContent='01 / 10';$('#stage-kind').textContent='';$('#progress-fill').style.width='10%';$('#feedback').textContent='';clearInterval(timerInterval);tick();
  showNotice('¡Primer reto resuelto!',[mission.first_destination+'.','Busca los sobres en ese lugar.','Al pulsar «Comenzar reto 2» empieza a contar tu tiempo.'],'Comenzar reto 2 →',async()=>{const data=await api('/api/mission/begin-timed',{});mission=data.mission;renderMission();});return;
 }
 const n=mission.stage;show('challenge');$('#team-label').textContent=mission.club_name;$('#assigned-team').textContent='Equipo '+mission.team;$('#stage-label').textContent=String(n+1).padStart(2,'0')+' / 10';$('#stage-kind').textContent='';$('#progress-fill').style.width=(n/10*100)+'%';$('#challenge-title').textContent=mission.title;$('#question').textContent=mission.question;
 const input=$('#answer'),length=numericLength(n);input.maxLength=length|| (n===4?60:300);input.inputMode=length?'numeric':'text';input.className=length===1?'digit-answer':length===3?'signal-answer':'text-answer';input.placeholder='';input.value=cleanAnswer(draftAnswer());
 if(length)input.setAttribute('pattern',length===1?'[0-9]':'[0-9]{3}');else input.removeAttribute('pattern');
 $('#feedback').textContent='';$('#feedback').dataset.error='false';$('#monitor').hidden=true;$('#answer-form').hidden=false;resource('');
 const help=$('#challenge-help');help.hidden=![5,8].includes(n);help.textContent=n===8?'ⓘ Tabla Morse':'ⓘ Ver aula';help.setAttribute('aria-label',n===8?'Ver tabla Morse de números':'Recordar aula asignada');help.onclick=n===8?showMorse:showClassroom;
 if(n===4){
  resource('<div class="zoom-toolbar"><button class="secondary" type="button" id="zoom-out" aria-label="Reducir imagen">−</button><span id="zoom-label">100%</span><button class="secondary" type="button" id="zoom-in" aria-label="Ampliar imagen">+</button></div><div class="photo-viewport"><img id="photo" alt="Fotografía asignada al equipo"></div><p class="pending-tag" id="photo-status"></p>');
  $('#photo').src=mission.photo.url;let zoom=1;const applyZoom=()=>{$('#photo').style.width=(zoom*100)+'%';$('#zoom-label').textContent=Math.round(zoom*100)+'%';};$('#zoom-in').onclick=()=>{zoom=Math.min(4,zoom+.25);applyZoom();};$('#zoom-out').onclick=()=>{zoom=Math.max(1,zoom-.25);applyZoom();};applyZoom();$('#photo-status').textContent=mission.photo.pending?'Fotografía pendiente.':'';
 }
 if(n===8){resource('<div class="signal-stage"><div id="lamp" class="signal-lamp" role="img" aria-label="Señales luminosas Morse"></div></div><button class="secondary" id="signal-play" type="button">Reproducir</button>');$('#signal-play').onclick=()=>{if(signalAbort){stopSignal();$('#signal-play').textContent='Reproducir';}else startSignal();};}
 if(n===9){resource('<div class="word-bank" id="words"></div>');mission.words.forEach((word,i)=>{const cell=document.createElement('div'),number=document.createElement('b');number.textContent=String(i+1);cell.append(number,document.createTextNode(word));$('#words').append(cell);});}
 clearInterval(timerInterval);tick();timerInterval=setInterval(tick,500);input.focus({preventScroll:true});
}
function confirmAnswer(value){return new Promise(resolve=>{const dialog=$('#confirm-dialog');$('#confirm-text').textContent=mission.confirmation.replace('{respuesta}',value);dialog.returnValue='cancel';dialog.addEventListener('close',()=>resolve(dialog.returnValue==='confirm'),{once:true});dialog.showModal();});}
$('#answer-form').onsubmit=async e=>{e.preventDefault();const value=cleanAnswer($('#answer').value).trim();$('#answer').value=value;if(!value||switching)return;const btn=$('#answer-submit');btn.disabled=true;try{if(!await confirmAnswer(value))return;const data=await api('/api/answer',{answer:value,stage:mission.stage});$('#feedback').textContent=data.message;$('#feedback').dataset.error=String(!data.accepted);if(data.accepted){try{sessionStorage.removeItem('codigo-draft');}catch{}const showRoom=mission.stage===4;mission=data.mission;await transition(renderMission);if(showRoom)showClassroom();}}catch(err){$('#feedback').textContent=err.message;$('#feedback').dataset.error='true';}finally{btn.disabled=false;}};
$('#monitor').onclick=()=>{$('#password-dialog').showModal();$('#monitor-password').focus();};$('#monitor-cancel').onclick=()=>{$('#password-dialog').close();$('#monitor-password').value='';};
$('#monitor-form').onsubmit=async e=>{e.preventDefault();const btn=e.submitter;btn.disabled=true;try{const data=await api('/api/monitor/advance-photo',{password:$('#monitor-password').value});$('#monitor-password').value='';$('#password-dialog').close();mission=data.mission;await transition(renderMission);}catch(err){$('#monitor-error').textContent=err.message;}finally{btn.disabled=false;}};
document.querySelectorAll('[data-transition]').forEach(link=>link.addEventListener('click',e=>{if(e.ctrlKey||e.metaKey||e.shiftKey)return;e.preventDefault();transition(()=>{location.href=link.href;});}));
window.addEventListener('pagehide',()=>{saveDraft();stopSignal();});
(async()=>{try{const res=await fetch('/api/state');if(!res.ok)throw new Error('No se pudo recuperar la misión.');const data=await res.json();csrf=data.csrf;mission=data.mission;showHome();}catch(err){$('#team-error').textContent=err.message;} })();
