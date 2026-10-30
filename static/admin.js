 'use strict';
const $=s=>document.querySelector(s);let csrf='',results=null,deleting=null,refreshing=false,authorized=false,reviewing=null;
async function api(path,body,method='GET'){const res=await fetch(path,{method,cache:'no-store',headers:{'Content-Type':'application/json','X-CSRF-Token':csrf},...(body?{body:JSON.stringify(body)}:{})});const data=await res.json();if(!res.ok){const error=new Error(data.error||'Error de conexión');error.status=res.status;throw error;}return data;}
function formatTime(ms){return String(Math.floor(ms/60000)).padStart(2,'0')+':'+String(Math.floor(ms%60000/1000)).padStart(2,'0')+'.'+String(ms%1000).padStart(3,'0');}
function node(tag,text,className){const el=document.createElement(tag);if(text!==undefined)el.textContent=text;if(className)el.className=className;return el;}
function statusName(value){return value===true?'Correcta':value===false?'Incorrecta':'Pendiente';}
function lock(){authorized=false;results=null;$('#results-body').replaceChildren();$('#results-panel').hidden=true;$('#login-panel').hidden=false;}
function drawResults(){
 const expanded=new Set([...document.querySelectorAll('.comparison-details[open]')].map(d=>d.dataset.id));
 const tbody=$('#results-body');tbody.replaceChildren();
 results.leaderboard.forEach((entry,i)=>{
  const tr=node('tr',undefined,'result-row');tr.dataset.id=entry.id;
  const rank=node('td',(i===0?'♛ ':i===1?'♜ ':i===2?'♟ ':'')+'#'+(i+1),'rank rank-cell '+(['rank-one','rank-two','rank-three'][i]||''));
  const club=node('td',undefined,'club-cell');club.append(node('strong',entry.club));club.append(node('small',entry.team?'Equipo asignado '+entry.team:'Registro anterior','club-team'));
  const seq=node('td',undefined,'answers-cell');const badges=node('div',undefined,'answer-badges');
  entry.comparison.forEach(item=>{const badge=node('span',String(item.stage).padStart(2,'0')+' '+(item.correct===true?'✓':item.correct===false?'×':'—'),'answer-badge '+(item.correct===true?'correct':item.correct===false?'incorrect':'pending'));badge.title=item.title+': '+statusName(item.correct);badge.setAttribute('aria-label',badge.title);badges.append(badge);});
  const details=node('details',undefined,'comparison-details');details.dataset.id=entry.id;details.open=expanded.has(entry.id);
  details.append(node('summary','Comparar respuestas enviadas y reales'));
  const list=node('div',undefined,'comparison-list');entry.comparison.forEach(item=>{const card=node('article',undefined,'comparison-item');card.dataset.status=item.correct===true?'correct':item.correct===false?'incorrect':'pending';const heading=node('h4',String(item.stage).padStart(2,'0')+' · '+item.title);heading.append(node('span',item.manual_approved?'Validada por organización':statusName(item.correct),'comparison-status'));const dl=node('dl');for(const [label,value] of [['Enviada',item.submitted||'Sin respuesta'],['Respuesta real',item.expected||'Sin clave definida en esta versión']]){const pair=node('div');pair.append(node('dt',label),node('dd',value));dl.append(pair);}card.append(heading,dl);if(item.correct===false||item.manual_approved){const review=node('button',item.manual_approved?'Deshacer validación':'Validar como correcta','secondary review-answer');review.type='button';review.setAttribute('aria-label',(item.manual_approved?'Deshacer validación':'Validar como correcta')+' · reto '+item.stage+' · '+entry.club);review.onclick=()=>openReview(entry,item);card.append(review);}list.append(card);});details.append(list);seq.append(badges,details);
  const score=node('td',entry.score+'/10','score-cell');score.dataset.label='Aciertos';const time=node('td',formatTime(entry.time_ms),'time-cell');time.dataset.label='Tiempo total';
  const actions=node('td',undefined,'actions-cell');const btn=node('button','Borrar','secondary');btn.type='button';btn.setAttribute('aria-label','Borrar registro de '+entry.club);btn.onclick=()=>{deleting=entry.id;$('#delete-description').textContent='Se eliminará el registro de '+entry.club+'. Esta acción no se puede deshacer.';$('#delete-password').value='';$('#delete-error').textContent='';$('#delete-dialog').showModal();$('#delete-password').focus();};actions.append(btn);tr.append(rank,club,seq,score,time,actions);tbody.append(tr);
 });
 if(!results.leaderboard.length){const tr=node('tr'),td=node('td','Ningún gremio ha terminado todavía.','empty-state');td.colSpan=6;tr.append(td);tbody.append(tr);}
}
async function refresh(){if(refreshing||!authorized)return;refreshing=true;try{results=await api('/api/results');$('#login-panel').hidden=true;$('#results-panel').hidden=false;drawResults();const ready=await api('/api/admin/readiness');$('#readiness').replaceChildren();ready.teams.forEach(t=>$('#readiness').append(node('span','Equipo '+t.team+' · Pantalla '+t.screen+' · Dilo con emojis')));$('#results-error').textContent='';}catch(err){if(err.status===401){lock();$('#login-error').textContent='Vuelve a introducir la contraseña para entrar.';}else $('#results-error').textContent=err.message;}finally{refreshing=false;}}
function openReview(entry,item){
 reviewing={id:entry.id,stage:item.stage,approved:!item.manual_approved};
 $('#review-title').textContent=reviewing.approved?'Validar respuesta como correcta':'Deshacer validación';
 $('#review-description').textContent=entry.club+' · Reto '+item.stage+' · '+item.title;
 $('#review-submitted').textContent=item.submitted||'Sin respuesta';$('#review-expected').textContent=item.expected||'Sin clave definida';
 $('#review-effect').textContent=reviewing.approved?'Se sumará un acierto y se actualizará la clasificación. La respuesta original se conserva.':'Se retirará el acierto añadido por organización.';
 $('#review-confirm').textContent=reviewing.approved?'Validar como correcta':'Deshacer validación';$('#review-error').textContent='';$('#review-dialog').showModal();
}
$('#review-cancel').onclick=()=>$('#review-dialog').close();
$('#review-form').onsubmit=async e=>{e.preventDefault();const btn=e.submitter;btn.disabled=true;try{await api('/api/results/'+encodeURIComponent(reviewing.id)+'/review',{stage:reviewing.stage,approved:reviewing.approved},'POST');$('#review-dialog').close();await refresh();}catch(err){$('#review-error').textContent=err.message;}finally{btn.disabled=false;}};
$('#login-form').onsubmit=async e=>{e.preventDefault();const btn=e.submitter;btn.disabled=true;try{await api('/api/admin/login',{password:$('#password').value},'POST');$('#password').value='';authorized=true;await transition(refresh);}catch(err){$('#login-error').textContent=err.message;}finally{btn.disabled=false;}};
$('#refresh').onclick=refresh;
$('#logout').onclick=async()=>{try{await api('/api/admin/logout',{},'POST');lock();}catch(err){$('#results-error').textContent=err.message;}};
$('#delete-cancel').onclick=()=>{$('#delete-dialog').close();$('#delete-password').value='';};
$('#delete-form').onsubmit=async e=>{e.preventDefault();const btn=e.submitter;btn.disabled=true;try{await api('/api/results/'+encodeURIComponent(deleting),{password:$('#delete-password').value},'DELETE');$('#delete-password').value='';$('#delete-dialog').close();await refresh();}catch(err){$('#delete-error').textContent=err.message;}finally{btn.disabled=false;}};
$('#export').onclick=()=>{if(!results)return;const url=URL.createObjectURL(new Blob([JSON.stringify({exported_at:new Date().toISOString(),leaderboard:results.leaderboard},null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download='codigo-secreto-resultados-'+new Date().toISOString().slice(0,10)+'.json';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);};
let transitioning=false;
async function transition(work){if(transitioning)return;transitioning=true;const overlay=$('#transition');overlay.classList.add('active');const reduced=matchMedia('(prefers-reduced-motion: reduce)').matches;await new Promise(r=>setTimeout(r,reduced?0:450));try{await work();await new Promise(r=>setTimeout(r,reduced?100:1100));}finally{overlay.classList.remove('active');transitioning=false;}}
document.querySelectorAll('a[href="/"]').forEach(a=>a.addEventListener('click',e=>{if(e.ctrlKey||e.metaKey||e.shiftKey)return;e.preventDefault();transition(async()=>{await new Promise(r=>setTimeout(r,1100));location.href=a.href;});}));
(async()=>{try{const data=await api('/api/state');csrf=data.csrf;lock();}catch(err){$('#login-error').textContent=err.message;}})();
window.addEventListener('pageshow',e=>{if(e.persisted)location.reload();});
setInterval(()=>{if(!document.hidden&&authorized&&!$('#delete-dialog').open&&!$('#review-dialog').open&&!transitioning&&!document.querySelector('.comparison-details[open]'))refresh();},3000);
