const supportParams=new URLSearchParams(location.search);const requestedPort=Number(supportParams.get('apiPort'));const supportApiPort=Number.isInteger(requestedPort)&&requestedPort>=1024&&requestedPort<=65535?requestedPort:8000;const SUPPORT_API='http://'+(location.hostname==='localhost'?'localhost':'127.0.0.1')+':'+supportApiPort;
let supportKey='';
const q=function(selector){return document.querySelector(selector);};
function setSupportStatus(target,message,kind){target.textContent=message;target.dataset.kind=kind||'';}
function supportHeaders(json){const headers={'X-Support-Agent-Key':supportKey};if(json)headers['Content-Type']='application/json';return headers;}
async function loadSupportCases(){
 const feedback=q('#support-feedback'),list=q('#support-case-list'),filter=q('#support-filter').value;
 setSupportStatus(feedback,'Haetaan tukipyyntöjä...');list.replaceChildren();
 let url=SUPPORT_API+'/support/cases';if(filter!=='all')url+='?status='+encodeURIComponent(filter);
 try{
  const response=await fetch(url,{headers:supportHeaders(false),cache:'no-store'});const data=await response.json().catch(function(){return{};});
  if(!response.ok){if(response.status===503)throw new Error('Käsittelijän rajapinta ei ole määritetty. Tarkista backend/.env ja SUPPORT_AGENT_API_KEY.');throw new Error(data.detail||'Tukipyyntöjä ei voitu hakea.');}
  q('#support-workspace').hidden=false;q('#support-login-panel').hidden=true;
  q('#support-count').textContent=data.length+' pyyntöä / tila: '+({open:'avoinna',answered:'vastattu',closed:'suljettu',all:'kaikki'}[filter]||filter);
  if(!data.length){const empty=document.createElement('p');empty.className='support-empty';empty.textContent='Tässä näkymässä ei ole tukipyyntöjä.';list.appendChild(empty);}
  data.forEach(renderSupportCase);setSupportStatus(feedback,'Jono päivitetty.','success');
 }catch(error){setSupportStatus(feedback,error.message||'Tukipyyntöjä ei voitu hakea.','error');throw error;}
}
function renderSupportCase(item){
 const list=q('#support-case-list'),card=document.createElement('article');card.className='support-case';
 const head=document.createElement('div');head.className='support-case-head';const id=document.createElement('span');id.className='support-case-id';id.textContent=item.id;
 const status=document.createElement('span');status.className='support-case-badge';status.dataset.status=item.status;status.textContent=({open:'Odottaa vastausta',answered:'Vastattu',closed:'Suljettu'}[item.status]||item.status);head.append(id,status);card.appendChild(head);
 if(item.created_at){const date=document.createElement('time');date.className='support-case-time';date.dateTime=item.created_at;const parsed=new Date(item.created_at);date.textContent=Number.isNaN(parsed.getTime())?item.created_at:parsed.toLocaleString('fi-FI');card.appendChild(date);}
 const question=document.createElement('p');question.className='support-case-question';question.textContent=item.question||'Tukipyynnöllä ei ole viestitekstiä.';card.appendChild(question);
 if(item.human_response){const reply=document.createElement('p');reply.className='support-existing-reply';reply.textContent=(item.demo_response?'Aiempi simuloitu demovastaus: ':'Aiempi vastaus: ')+item.human_response;card.appendChild(reply);}
 if(item.status!=='closed'){
  const form=document.createElement('form');form.className='support-reply-form';const area=document.createElement('textarea');area.className='support-reply';area.maxLength=4000;area.required=true;area.placeholder='Kirjoita asiakkaalle näkyvä vastaus...';form.appendChild(area);
  const actions=document.createElement('div');actions.className='support-actions';const replyButton=document.createElement('button');replyButton.type='submit';replyButton.textContent='Lähetä vastaus';actions.appendChild(replyButton);
  const closeButton=document.createElement('button');closeButton.type='button';closeButton.className='support-quiet';closeButton.textContent='Sulje pyyntö';closeButton.addEventListener('click',function(){closeSupportCase(item.id);});actions.appendChild(closeButton);form.appendChild(actions);
  form.addEventListener('submit',function(event){event.preventDefault();sendSupportReply(item.id,area.value,replyButton);});card.appendChild(form);
 }
 list.appendChild(card);
}
async function sendSupportReply(caseId,message,button){
 button.disabled=true;
 try{const response=await fetch(SUPPORT_API+'/support/cases/'+encodeURIComponent(caseId)+'/reply',{method:'POST',headers:supportHeaders(true),body:JSON.stringify({response:message})});const data=await response.json().catch(function(){return{};});if(!response.ok)throw new Error(data.detail||'Vastausta ei voitu lähettää.');setSupportStatus(q('#support-feedback'),'Vastaus lähetetty. Se näkyy asiakkaalle tilillä ja avoinna olevassa chatissa.','success');await loadSupportCases();}
 catch(error){setSupportStatus(q('#support-feedback'),error.message||'Vastausta ei voitu lähettää.','error');}
 finally{button.disabled=false;}
}
async function closeSupportCase(caseId){
 try{const response=await fetch(SUPPORT_API+'/support/cases/'+encodeURIComponent(caseId)+'/close',{method:'POST',headers:supportHeaders(false)});const data=await response.json().catch(function(){return{};});if(!response.ok)throw new Error(data.detail||'Pyyntöä ei voitu sulkea.');setSupportStatus(q('#support-feedback'),'Tukipyyntö suljettu.','success');await loadSupportCases();}
 catch(error){setSupportStatus(q('#support-feedback'),error.message||'Pyyntöä ei voitu sulkea.','error');}
}
q('#support-login-form').addEventListener('submit',async function(event){
 event.preventDefault();supportKey=q('#support-key').value.trim();const status=q('#support-login-status');
 try{await loadSupportCases();q('#support-key').value='';setSupportStatus(status,'','');}
 catch(error){supportKey='';q('#support-key').value='';if(error.message)setSupportStatus(status,error.message,'error');}
});
q('#support-filter').addEventListener('change',function(){loadSupportCases().catch(function(){});});
q('#support-refresh').addEventListener('click',function(){loadSupportCases().catch(function(){});});
q('#support-logout').addEventListener('click',function(){supportKey='';q('#support-workspace').hidden=true;q('#support-login-panel').hidden=false;setSupportStatus(q('#support-login-status'),'Avain poistettiin muistista.','success');});
