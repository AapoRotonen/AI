const localApiPort = new URLSearchParams(location.search).get('apiPort');
const parsedApiPort = Number(localApiPort);
const API_PORT = Number.isInteger(parsedApiPort) && parsedApiPort >= 1024 && parsedApiPort <= 65535 ? parsedApiPort : 8000;
const API='http://'+(location.hostname==='localhost'?'localhost':'127.0.0.1')+':'+API_PORT;
const products=[
 {id:'merino',name:'Merinovillapaita Klassik',material:'100 % merinovilla · 180 g/m²',price:89,category:'neuleet',badge:'ARKISUOSIKKI',image:'https://images.unsplash.com/photo-1577393439344-b89b65dfd169?auto=format&fit=crop&w=760&q=82',alt:'Neulottu merinovillapaita luonnonläheisessä värissä',description:'Ajaton merinovillapaita sopii arkeen ja juhlaan. Lämmin mutta hengittävä, ei kutita. Konepesu 30 asteessa.',sizes:['XS','S','M','L','XL','XXL'],colors:[{name:'Forest',hex:'#385b49',stock:['XS','S','M','L','XL','XXL']},{name:'Navy',hex:'#344255',stock:['XS','S','M','L','XL','XXL']},{name:'Charcoal',hex:'#55534f',stock:['XS','S','M','L','XL','XXL']},{name:'Ivory',hex:'#eae4d7',stock:['XS','S','M','L','XL','XXL']}]},
 {id:'pellava',name:'Pellavahousut Rento',material:'100 % pellava',price:120,category:'vaatteet',badge:'LUONNONMATERIAALI',image:'https://images.unsplash.com/photo-1715233749622-3216fe49e682?auto=format&fit=crop&w=760&q=82',alt:'Rennosti laskeutuvat pellavahousut',description:'Väljät, hengittävät pellavahousut lämpimiin päiviin. Konepesu 40 asteessa. Beige ja White saatavilla kaikissa koissa.',sizes:['XS','S','M','L','XL'],colors:[{name:'Beige',hex:'#c9b99b',stock:['XS','S','M','L','XL']},{name:'White',hex:'#f0eee7',stock:['XS','S','M','L','XL']},{name:'Sage',hex:'#96a390',stock:['XS','S','M']},{name:'Camel',hex:'#bca27b',stock:[]}]},
 {id:'vyö',name:'Nahkavyö Slim',material:'Italialainen pehmeä nahka · messinkilukko',price:45,category:'asusteet',image:'https://images.unsplash.com/photo-1664286074176-5206ee5dc878?auto=format&fit=crop&w=760&q=82',alt:'Pehmeä nahkainen asuste luonnollisessa sävyssä',description:'Italialaisesta pehmeästä nahasta valmistettu kapea vyö. Ajaton messinkilukko sopii housujen ja hameen kanssa.',sizes:['75 cm','80 cm','85 cm','90 cm','95 cm','100 cm'],colors:[{name:'Cognac',hex:'#936542',stock:['75 cm','80 cm','85 cm','90 cm','95 cm','100 cm']},{name:'Black',hex:'#333430',stock:['75 cm','80 cm','85 cm','90 cm','95 cm','100 cm']},{name:'Tan',hex:'#c9a782',stock:['75 cm','90 cm','95 cm','100 cm']}]},
 {id:'kasmir',name:'Kasmirhuivi Luxe',material:'100 % mongolialainen kasmir · 200 × 70 cm',price:160,category:'neuleet',badge:'PEHMEÄ SUOSIKKI',image:'https://images.unsplash.com/photo-1550614412-40be4484c638?auto=format&fit=crop&w=760&q=82',alt:'Pehmeästi laskeutuva villahuivi',description:'Pehmeä ja lämmin kaksikerroksisesta mongolialaisesta kasmirista kudottu huivi. 200 × 70 cm. Käsinpesu kylmässä vedessä tai kuivapesu.',sizes:['Yksi koko'],colors:[{name:'Forest',hex:'#41584a',stock:['Yksi koko']},{name:'Camel',hex:'#b79b74',stock:['Yksi koko']},{name:'Dusty Rose',hex:'#c9a5a2',stock:['Yksi koko']},{name:'Midnight',hex:'#444e5f',stock:['Yksi koko']}]},
 {id:'denim',name:'Denim-takki Vintage',material:'100 % puuvilla · 12 oz denim',price:185,category:'vaatteet',image:'https://images.unsplash.com/photo-1559475464-ffe519cfb9f1?auto=format&fit=crop&w=760&q=82',alt:'Klassinen sininen denimtakki',description:'Vintagetyylinen denimtakki, jossa on neljä taskua ja metallinapit. Konepesu nurinpäin 30 asteessa, ilmakuivaus.',sizes:['XS','S','M','L','XL','XXL'],colors:[{name:'Washed Blue',hex:'#697b8d',stock:['XS','S','M','L','XL','XXL']},{name:'Dark Indigo',hex:'#354256',stock:['S','M','L']},{name:'Ecru',hex:'#ddd7c9',stock:[]}]},
 {id:'silkki',name:'Silkkipaita Elegance',material:'100 % mulberry-silkki · 19 momme',price:135,category:'vaatteet',badge:'HARKITTU VALINTA',image:'https://images.unsplash.com/photo-1565544758282-1582ed828211?auto=format&fit=crop&w=760&q=82',alt:'Tyylikäs luonnonvaalea silkkipaita',description:'Pehmeästi laskeutuvaa 19 mommen mulberry-silkkiä. Klassinen paita juhlaan tai arkeen.',sizes:['XS','S','M','L','XL'],colors:[{name:'Ivory',hex:'#eee8dc',stock:['XS','S','M','L','XL']},{name:'Blush',hex:'#ddbab8',stock:['XS','S','M']},{name:'Champagne',hex:'#c9b898',stock:[]},{name:'Black',hex:'#393934',stock:['XS','S','M','L','XL']}]}
];

const qs=function(s,root){return(root||document).querySelector(s);};
const esc=function(value){return String(value).replaceAll('&','&amp;').replaceAll('<','&lt;').replaceAll('>','&gt;').replaceAll('"','&quot;').replaceAll("'","&#39;");};
const money=function(value){return value.toLocaleString('fi-FI',{minimumFractionDigits:2,maximumFractionDigits:2})+' €';};
const filter={category:'kaikki',query:'',favorite:false,sort:'recommended'};
let favorites=new Set();let cart=[];let selectedProduct=null;let selectedColor='';let selectedSize='';let pendingCheckout=false,isOrdering=false;
try{favorites=new Set(JSON.parse(localStorage.getItem('koivu-favorites')||'[]'));}catch(e){}
function restoreCart(entries){
 if(!Array.isArray(entries))return[];
 const restored=[];
 entries.slice(0,products.length*24).forEach(function(entry){
  if(!entry||typeof entry!=='object')return;
  const product=products.find(function(item){return item.id===entry.id;});
  if(!product)return;
  const color=product.colors.find(function(item){return item.name===entry.color;});
  const size=product.sizes.find(function(item){return item===entry.size;});
  const quantity=entry.quantity;
  if(!color||!color.stock.includes(size)||!Number.isSafeInteger(quantity)||quantity<1||quantity>20)return;
  const key=product.id+'|'+color.name+'|'+size;
  const existing=restored.find(function(item){return item.key===key;});
  if(existing){existing.quantity=Math.min(existing.quantity+quantity,99);return;}
  restored.push({key:key,id:product.id,name:product.name,color:color.name,size:size,price:product.price,image:product.image,quantity:quantity});
 });
 return restored;
}
try{cart=restoreCart(JSON.parse(localStorage.getItem('koivu-cart')||'[]'));}catch(e){cart=[];}
const available=function(product,color){return product.colors.find(function(item){return item.name===color;})||{stock:[]};};
const firstColor=function(product){return product.colors.find(function(item){return item.stock.length;})||product.colors[0];};
const selectedCardColors=Object.fromEntries(products.map(function(product){return[product.id,firstColor(product).name];}));
function toast(message){const el=qs('#toast');el.textContent=message;el.hidden=false;el.classList.add('visible');clearTimeout(window.koivuToast);window.koivuToast=setTimeout(function(){el.classList.remove('visible');setTimeout(function(){if(!el.classList.contains('visible'))el.hidden=true;},220);},2100);}
function renderProducts(){
 let visible=products.filter(function(p){return(filter.category==='kaikki'||p.category===filter.category)&&((p.name+' '+p.material+' '+p.colors.map(function(c){return c.name;}).join(' ')).toLocaleLowerCase('fi').includes(filter.query.toLocaleLowerCase('fi')))&&(!filter.favorite||favorites.has(p.id));});
 if(filter.sort==='low')visible=visible.slice().sort(function(a,b){return a.price-b.price;});
 if(filter.sort==='high')visible=visible.slice().sort(function(a,b){return b.price-a.price;});
 if(filter.sort==='name')visible=visible.slice().sort(function(a,b){return a.name.localeCompare(b.name,'fi');});
 qs('#product-count').textContent=visible.length+' '+(filter.favorite?'suosikkia':filter.query?'tuotetta löytyi':'huolella valittua tuotetta');
 qs('#product-grid').innerHTML=visible.length?visible.map(function(p,index){
   const c=available(p,selectedCardColors[p.id]||firstColor(p).name);
   return '<article class="card" style="animation-delay:'+index*.035+'s"><div class="product-photo"><img src="'+esc(p.image)+'" alt="'+esc(p.alt)+'" loading="lazy" decoding="async">'+(p.badge?'<span class="badge">'+esc(p.badge)+'</span>':'')+
   '<button class="heart" type="button" data-act="favorite" data-id="'+esc(p.id)+'" aria-pressed="'+favorites.has(p.id)+'" aria-label="'+(favorites.has(p.id)?'Poista suosikeista: ':'Lisää suosikkeihin: ')+esc(p.name)+'"><svg viewBox="0 0 24 24"><path d="M20.5 8.9c0 4-8.5 10.4-8.5 10.4S3.5 12.9 3.5 8.9a4.5 4.5 0 0 1 8.5-2.1 4.5 4.5 0 0 1 8.5 2.1Z"/></svg></button><button class="quick" type="button" data-act="open" data-id="'+esc(p.id)+'">Valitse koko &amp; väri　→</button></div>'+
   '<div class="info"><p class="category">'+(p.category==='neuleet'?'Luonnonmateriaalit':p.category==='asusteet'?'Ajaton asuste':'Vaatteet jokapäiväiseen käyttöön')+'</p><div class="title-row"><button class="name" type="button" data-act="open" data-id="'+esc(p.id)+'">'+esc(p.name)+'</button><span class="price">'+p.price+' €</span></div><p class="material">'+esc(p.material)+'</p><div class="swatches" aria-label="Värivaihtoehdot">'+p.colors.map(function(col){return '<button class="swatch" type="button" style="background:'+esc(col.hex)+'" title="'+esc(col.name)+(col.stock.length?'':' · Loppuunmyyty')+'" aria-label="'+esc(col.name)+(col.stock.length?'':' · Loppuunmyyty')+'" aria-pressed="'+(col.name===c.name)+'" '+(!col.stock.length?'disabled':'')+' data-act="color" data-id="'+esc(p.id)+'" data-color="'+esc(col.name)+'"></button>';}).join('')+'</div></div></article>';
 }).join(''):'<p class="empty"><strong>'+ (filter.favorite?'Ei vielä suosikkeja.':'Tuotteita ei löytynyt.')+'</strong>Lisää tuotteita suosikkeihin painamalla sydäntä, tai kokeile uutta hakusanaa.</p>';
}
function renderFavorites(){qs('#favorite-count').textContent=favorites.size;qs('#favorite-count').hidden=!favorites.size;qs('#favorites-toggle').setAttribute('aria-pressed',filter.favorite);}
function saveFavorites(){try{localStorage.setItem('koivu-favorites',JSON.stringify(Array.from(favorites)));}catch(e){}renderFavorites();renderProducts();}
function openOverlay(id){closeOverlay(id==='#product-overlay');qs(id).hidden=false;document.body.classList.add('overlay-open');const button=qs('button',qs(id));if(button)button.focus();}
function closeOverlay(preserveProduct){document.querySelectorAll('.overlay:not([hidden])').forEach(function(el){el.hidden=true;});document.body.classList.remove('overlay-open');if(!preserveProduct)selectedProduct=null;}
function openProduct(id,color){
 selectedProduct=products.find(function(p){return p.id===id;});if(!selectedProduct)return;
 selectedColor=color||firstColor(selectedProduct).name;const stock=available(selectedProduct,selectedColor).stock;
 selectedSize=stock[0]||'';
 renderDetail();openOverlay('#product-overlay');
}
function renderDetail(){
 const p=selectedProduct;if(!p)return;const stock=available(p,selectedColor).stock;if(!stock.includes(selectedSize))selectedSize=stock[0]||'';
 qs('#product-detail').innerHTML='<div class="detail-photo"><img src="'+esc(p.image)+'" alt="'+esc(p.alt)+'"></div><div class="detail-copy"><p class="kicker">'+(p.category==='asusteet'?'Tarkoin valittu asuste':'Pehmeitä luonnonkuituja')+'</p><h2 id="detail-heading">'+esc(p.name)+'</h2><p class="detail-material">'+esc(p.material)+'</p><p class="detail-price">'+p.price+' €</p><p class="detail-description">'+esc(p.description)+'</p><span class="option-label">Väri — '+esc(selectedColor)+'</span><div class="detail-colors">'+p.colors.map(function(c){return'<button class="color-option" type="button" data-color-option="'+esc(c.name)+'" aria-pressed="'+(c.name===selectedColor)+'">'+esc(c.name)+(c.stock.length?'':' · loppuunmyyty')+'</button>';}).join('')+'</div><span class="option-label">'+(p.sizes.length===1?'Malli':'Valitse koko')+'</span><div class="sizes">'+p.sizes.map(function(s){return'<button class="size-option" type="button" data-size="'+esc(s)+'" aria-pressed="'+(s===selectedSize)+'" '+(stock.includes(s)?'':'disabled')+'>'+esc(s)+'</button>';}).join('')+'</div><p class="stock '+(stock.length?'':'sold-out')+'" aria-live="polite">'+(stock.length?(stock.length===p.sizes.length?'Saatavilla':stock.join(', ')+' saatavilla'):'Väri loppuunmyyty')+'</p><button class="primary" id="add-product" type="button" '+(selectedSize?'':'disabled')+'>Lisää ostoskoriin · '+p.price+' €</button>'+(p.sizes.length>1?'<br><a class="size-guide" href="#kokotaulukko" id="size-guide">Apua koon valintaan</a>':'')+'</div>';
}
function renderCart(){
 const count=cart.reduce(function(n,c){return n+c.quantity;},0);qs('#cart-count').textContent=count;qs('#cart-count').hidden=!count;qs('#drawer-count').textContent=count?'· '+count:'';
 const sum=cart.reduce(function(n,c){return n+c.price*c.quantity;},0);qs('#subtotal').textContent=money(sum);qs('#shipping-note').textContent=!sum?'Lisää koriin tuotteita, joista pidät.':sum>=150?'Hienoa, tilauksesi toimitetaan maksutta!':'Lisää vielä '+money(150-sum)+', niin toimitus on ilmainen.';
 qs('#progress').style.width=Math.min(sum/150*100,100)+'%';qs('#cart-footer').style.display=cart.length?'':'none';qs('#cart-disclaimer').textContent=signedInUser?'Paikallinen demotilaus tallentuu tilillesi. Maksua ei veloiteta.':'Kirjaudu sisään tallentaaksesi tilauksen tilillesi. Maksua ei veloiteta.';
 qs('#cart-items').innerHTML=cart.length?cart.map(function(c){return'<article class="cart-line"><img class="cart-image" src="'+esc(c.image)+'" alt="" loading="lazy"><div><p class="cart-name">'+esc(c.name)+'</p><p class="cart-option">'+esc(c.color)+' · '+esc(c.size)+'</p><div class="quantity"><button type="button" aria-label="Vähennä määrää" data-cart="minus" data-key="'+esc(c.key)+'">−</button><span>'+esc(c.quantity)+'</span><button type="button" aria-label="Lisää määrää" data-cart="plus" data-key="'+esc(c.key)+'">+</button></div></div><div class="line-aside"><span class="line-price">'+money(c.price*c.quantity)+'</span><button type="button" class="remove" data-cart="remove" data-key="'+esc(c.key)+'">Poista</button></div></article>';}).join(''):'<div class="cart-empty"><strong>Ostoskorisi odottaa.</strong>Et ole vielä lisännyt tuotteita.<br><button id="continue-shopping" class="primary" style="margin-top:14px" type="button">Tutustu mallistoon →</button></div>';
 try{localStorage.setItem('koivu-cart',JSON.stringify(cart));}catch(e){}
}
function addToCart(){
 const p=selectedProduct;if(!p||!selectedSize)return;
 const c=available(p,selectedColor);if(!c.stock.includes(selectedSize)){toast('Valitse saatavilla oleva väri ja koko.');return;}
 const key=p.id+'|'+selectedColor+'|'+selectedSize;const prior=cart.find(function(x){return x.key===key;});
 if(prior)prior.quantity++;else cart.push({key:key,id:p.id,name:p.name,color:selectedColor,size:selectedSize,price:p.price,image:p.image,quantity:1});
 const name=p.name;renderCart();closeOverlay();toast(name+' lisätty ostoskoriin');
}
qs('#product-grid').addEventListener('click',function(e){
 const b=e.target.closest('[data-act]');if(!b)return;
 if(b.dataset.act==='favorite'){if(favorites.has(b.dataset.id))favorites.delete(b.dataset.id);else favorites.add(b.dataset.id);saveFavorites();}
 if(b.dataset.act==='open')openProduct(b.dataset.id,selectedCardColors[b.dataset.id]);
 if(b.dataset.act==='color'){selectedCardColors[b.dataset.id]=b.dataset.color;const wrap=b.closest('.swatches');wrap.querySelectorAll('.swatch').forEach(function(s){s.setAttribute('aria-pressed',String(s===b));});}
});
document.querySelectorAll('.filter').forEach(function(button){button.addEventListener('click',function(){filter.category=button.dataset.filter;document.querySelectorAll('.filter').forEach(function(b){b.setAttribute('aria-pressed',String(b===button));});renderProducts();});});
qs('#sort').addEventListener('change',function(e){filter.sort=e.target.value;renderProducts();});
qs('#search-toggle').addEventListener('click',function(){const panel=qs('#search');panel.hidden=!panel.hidden;this.setAttribute('aria-expanded',String(!panel.hidden));if(panel.hidden){qs('#search-input').value='';filter.query='';renderProducts();}else qs('#search-input').focus();});
qs('#search-input').addEventListener('input',function(e){filter.query=e.target.value.trim();if(filter.favorite&&filter.query){filter.favorite=false;renderFavorites();}renderProducts();});
qs('#favorites-toggle').addEventListener('click',function(){filter.favorite=!filter.favorite;renderFavorites();renderProducts();qs('#products').scrollIntoView({behavior:'smooth'});});
qs('#cart-toggle').addEventListener('click',function(){renderCart();openOverlay('#cart-overlay');});
qs('#cart-items').addEventListener('click',function(e){
 if(e.target.id==='continue-shopping'){closeOverlay();qs('#products').scrollIntoView({behavior:'smooth'});return;}
 const button=e.target.closest('[data-cart]');if(!button)return;const item=cart.find(function(c){return c.key===button.dataset.key;});if(!item)return;
 if(button.dataset.cart==='plus'){if(item.quantity>=20){toast('Enintään 20 kappaletta samaa tuotetta.');return;}item.quantity++;}if(button.dataset.cart==='minus')item.quantity--;if(button.dataset.cart==='remove'||item.quantity<1)cart=cart.filter(function(c){return c.key!==item.key;});renderCart();
});
document.querySelectorAll('.overlay').forEach(function(overlay){overlay.addEventListener('click',function(e){if(e.target===overlay||e.target.closest('[data-close]'))closeOverlay();});});
qs('#product-detail').addEventListener('click',function(e){
 const color=e.target.closest('[data-color-option]');if(color){selectedColor=color.dataset.colorOption;renderDetail();return;}
 const size=e.target.closest('[data-size]');if(size&&!size.disabled){selectedSize=size.dataset.size;renderDetail();return;}
 if(e.target.closest('#add-product'))addToCart();
 if(e.target.closest('#size-guide')){e.preventDefault();toast('Kokotaulukko: paita XS 76–80 cm · S 80–84 cm · M 84–88 cm · L 88–94 cm rinnanympärys.');}
});
async function checkoutCart(){
 if(isOrdering||!cart.length)return;
 isOrdering=true;const button=qs('#checkout');button.disabled=true;
 try{
  const response=await fetch(API+'/orders',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({items:cart.map(function(item){return{product_id:item.id,color:item.color,size:item.size,quantity:item.quantity};})})});
  const result=await response.json().catch(function(){return{};});
  if(response.status===401){pendingCheckout=true;toast('Kirjaudu sisään, niin tallennan tilauksen tilillesi.');if(!qs('#account-dialog').open)qs('#account-dialog').showModal();await refreshAccount();return;}
  if(!response.ok)throw new Error(result.detail||'Demotilausta ei voitu tallentaa.');
  pendingCheckout=false;cart=[];renderCart();closeOverlay();toast('Tilaus '+result.id+' tallennettiin tilillesi. Maksua ei veloitettu.');
  if(!qs('#account-dialog').open)qs('#account-dialog').showModal();await refreshAccount();
 }catch(error){toast(error.message==='Failed to fetch'?'Backend ei vastaa. Tarkista palvelimen tila.':error.message||'Demotilausta ei voitu tallentaa.');}
 finally{isOrdering=false;button.disabled=false;}
}
qs('#checkout').addEventListener('click',checkoutCart);
let isLoading=false,isInitializing=false,conversationHistory=[];let signedInUser=null;let registerMode=false;let pendingChatMessage=null;
const WELCOME_MESSAGE='Hei! Olen Koivun AI-assistentti. Autan tuotteissa, koon valinnassa, tyylissä ja ajankohtaisessa tiedossa. Oman tilauksen tarkistus ja asiakaspalvelijalle välitettävä pyyntö vaativat kirjautumisen, jotta voin liittää asian oikeaan tiliin. 🌿';
function openChat(){const win=qs('#chat-window');if(!win.classList.contains('open')){win.classList.add('open');qs('#chat-toggle').setAttribute('aria-expanded','true');if(!qs('#chat-messages').children.length)initChat();}qs('#chat-input').focus();}
qs('#chat-help').addEventListener('click',openChat);
document.querySelectorAll('[data-demo-prompt]').forEach(function(button){button.addEventListener('click',function(){openChat();const input=qs('#chat-input');input.value=button.dataset.demoPrompt;input.focus();});});
const supportConsoleLink=qs('#support-console-link');if(supportConsoleLink)supportConsoleLink.href='support.html?apiPort='+API_PORT;
const supportDemoLink=qs('#support-console-demo-link');if(supportDemoLink)supportDemoLink.href='support.html?apiPort='+API_PORT;
let activeHumanCaseId=null,humanReplyPollTimer=null,humanReplyPollDeadline=0,humanReplyPollBusy=false,lastHumanReplySeen=null;
function stopHumanReplyPolling(){if(humanReplyPollTimer){window.clearInterval(humanReplyPollTimer);humanReplyPollTimer=null;}activeHumanCaseId=null;}
async function sendDemoSupportReply(caseId){
 try{
  const response=await fetch(API+'/support/my-cases/'+encodeURIComponent(caseId)+'/demo-reply',{method:'POST',credentials:'include'});
  const data=await response.json().catch(function(){return{};});if(!response.ok)throw new Error(data.detail||'Demovastausta ei voitu näyttää.');
  await pollForHumanReply();
 }catch(error){
  await pollForHumanReply();
  if(activeHumanCaseId===caseId){qs('#chat-status').textContent='Demokäsittelijä ei tavoitettavissa';toast(error.message||'Demovastausta ei voitu näyttää.');}
 }
}
async function pollForHumanReply(){
 if(!activeHumanCaseId||humanReplyPollBusy)return;
 if(Date.now()>humanReplyPollDeadline){stopHumanReplyPolling();return;}
 if(document.hidden)return;
 humanReplyPollBusy=true;
 try{
  const response=await fetch(API+'/support/cases/'+encodeURIComponent(activeHumanCaseId),{credentials:'include'});
  if(response.status===401||response.status===404){stopHumanReplyPolling();return;}
  if(!response.ok)return;
  const item=await response.json();
  if(item.human_response&&item.human_response!==lastHumanReplySeen){
   lastHumanReplySeen=item.human_response;const message=(item.demo_response?'Asiakaspalvelija (demo): ':'Asiakaspalvelija: ')+item.human_response;
   addMessage('human-agent',message);conversationHistory.push({role:'assistant',content:message});
   qs('#chat-status').textContent=item.demo_response?'Asiakaspalvelun demovastaus':'Asiakaspalvelija vastasi';toast(item.demo_response?'Demokäsittelijä vastasi chattiin.':'Sait vastauksen asiakaspalvelijalta.');stopHumanReplyPolling();
  }else if(item.status==='closed'){qs('#chat-status').textContent='Tukipyyntö suljettu';stopHumanReplyPolling();}
 }catch(error){}finally{humanReplyPollBusy=false;}
}
function watchForHumanReply(caseId){
 if(humanReplyPollTimer)window.clearInterval(humanReplyPollTimer);
 activeHumanCaseId=caseId;lastHumanReplySeen=null;humanReplyPollDeadline=Date.now()+30*60*1000;
 qs('#chat-status').textContent='Asiakaspalvelija liittyy chattiin…';
 pollForHumanReply();humanReplyPollTimer=window.setInterval(pollForHumanReply,4000);
}
function queueDemoHumanReply(caseId){
 window.setTimeout(function(){sendDemoSupportReply(caseId);},700);
}
function initChat(){if(isInitializing)return;isInitializing=true;if(!conversationHistory.length){addMessage('bot',WELCOME_MESSAGE);conversationHistory.push({role:'assistant',content:WELCOME_MESSAGE});}isInitializing=false;}
qs('#chat-toggle').addEventListener('click',function(){const open=qs('#chat-window').classList.toggle('open');this.setAttribute('aria-expanded',String(open));if(open&&!qs('#chat-messages').children.length)initChat();if(open)qs('#chat-input').focus();});
qs('#chat-minimize').addEventListener('click',function(){qs('#chat-window').classList.remove('open');qs('#chat-toggle').setAttribute('aria-expanded','false');});
qs('#chat-reset').addEventListener('click',function(){if(isLoading||isInitializing)return;pendingChatMessage=null;conversationHistory=[];removeTyping();qs('#chat-messages').replaceChildren();qs('#chat-input').value='';addMessage('bot',WELCOME_MESSAGE);conversationHistory.push({role:'assistant',content:WELCOME_MESSAGE});});
qs('#chat-form').addEventListener('submit',async function(e){
 e.preventDefault();if(isLoading||isInitializing)return;const input=qs('#chat-input'),message=input.value.trim();if(!message)return;input.value='';addMessage('user',message);showTyping();isLoading=true;qs('#chat-send').disabled=true;qs('#chat-reset').disabled=true;
 try{
  const response=await fetch(API+'/chat',{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:message,history:conversationHistory.slice(-12).map(function(turn){return{role:turn.role,content:turn.content.slice(0,1500)};})})});
  removeTyping();const data=await response.json().catch(function(){return{};});if(!response.ok)throw new Error(data.detail||'Pyyntöä ei voitu käsitellä.');
  const answer=data.answer;
  const bubble=addMessage('bot',answer,data.path);conversationHistory.push({role:'user',content:message});conversationHistory.push({role:'assistant',content:answer});if(data.support_case_id){watchForHumanReply(data.support_case_id);queueDemoHumanReply(data.support_case_id);}
  if(data.auth_required){pendingChatMessage=message;addLoginAction(bubble,message);}
 }catch(error){removeTyping();addMessage('bot',error.message==='Failed to fetch'?'Yhteysvirhe. Tarkista että backend on käynnissä.':error.message||'Pyyntöä ei voitu käsitellä.');}
 finally{isLoading=false;qs('#chat-send').disabled=false;qs('#chat-reset').disabled=false;input.focus();}
});
function addMessage(type,text,route){const bubble=document.createElement('div');bubble.className='msg msg-'+type;const content=document.createElement('span');content.textContent=text;bubble.appendChild(content);if(route){const path=document.createElement('small');path.className='msg-route';path.textContent='Agenttipolku - '+route;bubble.appendChild(path);}const box=qs('#chat-messages');box.appendChild(bubble);box.scrollTop=box.scrollHeight;return bubble;}
function addLoginAction(bubble,message){
 const actions=document.createElement('div');actions.className='msg-actions';
 const button=document.createElement('button');button.type='button';button.textContent='Kirjaudu ja jatka';
 button.addEventListener('click',async function(){pendingChatMessage=message;if(!qs('#account-dialog').open)qs('#account-dialog').showModal();await refreshAccount();});
 actions.appendChild(button);bubble.appendChild(actions);
}
function showTyping(){const t=document.createElement('div');t.id='typing';t.className='typing-indicator';t.innerHTML='<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';qs('#chat-messages').appendChild(t);}
function removeTyping(){const t=qs('#typing');if(t)t.remove();}

function setAccountMode(createAccount){registerMode=createAccount;qs('#account-title').textContent=createAccount?'Luo tili':'Kirjaudu sisään';qs('#account-submit').textContent=createAccount?'Luo tili':'Kirjaudu sisään';qs('#account-mode').textContent=createAccount?'Minulla on jo tili':'Luo uusi tili';qs('#account-password').autocomplete=createAccount?'new-password':'current-password';qs('#account-password').minLength=createAccount?12:1;qs('#account-error').textContent='';}
async function loadAccountData(){
 if(!signedInUser)return;
 const ordersBox=qs('#account-orders'),casesBox=qs('#account-cases');ordersBox.replaceChildren();casesBox.replaceChildren();
 try{
  const results=await Promise.all([fetch(API+'/orders',{credentials:'include'}),fetch(API+'/support/my-cases',{credentials:'include'})]);
  const orders=results[0].ok?await results[0].json():[];const cases=results[1].ok?await results[1].json():[];
  if(!orders.length){const empty=document.createElement('p');empty.className='account-empty';empty.textContent='Ei demotilauksia vielä.';ordersBox.appendChild(empty);}
  const orderStatusLabels={processing:'Käsittelyssä',confirmed:'Vahvistettu',shipped:'Lähetetty',delivered:'Toimitettu'};
  orders.forEach(function(order){
   const row=document.createElement('div');row.className='account-row';
   const strong=document.createElement('strong');strong.textContent=order.id+' · '+(orderStatusLabels[order.status]||order.status);row.appendChild(strong);
   if(order.items&&order.items.length){
    const details=document.createElement('p');details.className='case-question';details.textContent=order.items.map(function(item){return item.quantity+' × '+item.name+' · '+item.color+' · '+item.size;}).join(' / ');row.appendChild(details);
    if(order.total_cents){const total=document.createElement('p');total.className='case-question';total.textContent='Yhteensä '+money(order.total_cents/100)+' · demo, maksua ei veloitettu';row.appendChild(total);}
   }else{row.appendChild(document.createTextNode(' · vanha demotilaus'));}
   const cancel=document.createElement('button');cancel.type='button';cancel.className='order-cancel';cancel.textContent='Peru tilaukseni';
   cancel.addEventListener('click',async function(){
    if(!window.confirm('Perutaanko tämä paikallinen demotilaus? Se poistuu tältä tililtä. Maksua ei ole veloitettu.'))return;
    cancel.disabled=true;
    try{
     const response=await fetch(API+'/orders/'+encodeURIComponent(order.id),{method:'DELETE',credentials:'include'});
     if(!response.ok){const result=await response.json().catch(function(){return{};});throw new Error(result.detail||'Demotilausta ei voitu perua.');}
     toast('Tilaus '+order.id+' peruttiin.');await loadAccountData();
    }catch(error){toast(error.message||'Demotilausta ei voitu perua.');cancel.disabled=false;}
   });
   row.appendChild(cancel);ordersBox.appendChild(row);
  });
  if(!cases.length){const empty=document.createElement('p');empty.className='account-empty';empty.textContent='Ei tukipyyntöjä.';casesBox.appendChild(empty);}
  const statusLabels={open:'Odottaa asiakaspalvelijaa',answered:'Asiakaspalvelija vastasi',closed:'Suljettu'};qs('#account-cases-reset').hidden=!cases.length;cases.forEach(function(item){const row=document.createElement('div');row.className='account-row';const strong=document.createElement('strong');const stateLabel=item.demo_response?'Demovastaus näytetty':(statusLabels[item.status]||item.status);strong.textContent=item.id+' / '+stateLabel;row.appendChild(strong);if(item.question){const question=document.createElement('p');question.className='case-question';question.textContent=item.question;row.appendChild(question);}if(item.human_response){const answer=document.createElement('p');answer.className='case-response';answer.textContent=(item.demo_response?'Asiakaspalvelijan demovastaus: ':'Asiakaspalvelija: ')+item.human_response;row.appendChild(answer);}if(item.status==='open'){const follow=document.createElement('button');follow.type='button';follow.className='case-chat-link';follow.textContent='Jatka tätä pyyntöä chatissa';follow.addEventListener('click',function(){qs('#account-dialog').close();openChat();const bubble=addMessage('bot','Jatketaan tukipyyntöä '+item.id+': '+item.question);watchForHumanReply(item.id);queueDemoHumanReply(item.id);});row.appendChild(follow);}casesBox.appendChild(row);});
 }catch(error){const empty=document.createElement('p');empty.className='account-empty';empty.textContent='Tilin tietoja ei saatu ladattua.';ordersBox.appendChild(empty);}
}
async function refreshAccount(){
 try{const response=await fetch(API+'/auth/me',{credentials:'include'});const data=await response.json();signedInUser=data.authenticated?data.user:null;}catch(error){signedInUser=null;}
 qs('#account-open').textContent=signedInUser?'Oma tili':'Kirjaudu';qs('#account-signed-out').hidden=!!signedInUser;qs('#account-signed-in').hidden=!signedInUser;
 if(signedInUser){qs('#account-email-display').textContent=signedInUser.email;qs('#account-description').textContent='Tilaus- ja tukipyyntötiedot näkyvät vain tällä tilillä.';await loadAccountData();}
 else{qs('#account-description').textContent='Kirjautuminen suojaa tilaus- ja tukipyyntötietosi.';}
}
async function resumePendingChat(){if(!pendingChatMessage||!signedInUser||isLoading)return;const message=pendingChatMessage;pendingChatMessage=null;if(qs('#account-dialog').open)qs('#account-dialog').close();qs('#chat-input').value=message;qs('#chat-form').requestSubmit();}
async function resumePendingCheckout(){if(!pendingCheckout||!signedInUser||isOrdering)return;pendingCheckout=false;await checkoutCart();}
qs('#account-open').addEventListener('click',async function(){if(!qs('#account-dialog').open)qs('#account-dialog').showModal();await refreshAccount();await resumePendingChat();await resumePendingCheckout();});
qs('#account-mode').addEventListener('click',function(){setAccountMode(!registerMode);});
qs('#account-form').addEventListener('submit',async function(event){
 event.preventDefault();const email=qs('#account-email').value.trim(),password=qs('#account-password').value;const endpoint=registerMode?'/auth/register':'/auth/login';qs('#account-submit').disabled=true;qs('#account-error').textContent='';
 try{const response=await fetch(API+endpoint,{method:'POST',credentials:'include',headers:{'Content-Type':'application/json'},body:JSON.stringify({email:email,password:password})});const result=await response.json().catch(function(){return{};});if(!response.ok)throw new Error(result.detail||'Kirjautuminen epäonnistui.');qs('#account-password').value='';setAccountMode(false);await refreshAccount();await resumePendingChat();await resumePendingCheckout();}
 catch(error){qs('#account-error').textContent=error.message==='Failed to fetch'?'Backend ei vastaa. Tarkista palvelimen tila.':error.message||'Kirjautuminen epäonnistui.';}
 finally{qs('#account-submit').disabled=false;}
});
qs('#account-cases-reset').addEventListener('click',async function(){if(!signedInUser||!window.confirm('Poistetaanko tämän tilin kaikki demoasiakaspalvelupyynnöt? Tätä ei voi perua.'))return;this.disabled=true;try{const response=await fetch(API+'/support/my-cases/reset',{method:'POST',credentials:'include'});const result=await response.json().catch(function(){return{};});if(!response.ok)throw new Error(result.detail||'Tukipyyntöjä ei voitu nollata.');toast('Nollattiin '+result.deleted+' tukipyyntöä.');await loadAccountData();}catch(error){toast(error.message||'Tukipyyntöjä ei voitu nollata.');}finally{this.disabled=false;}});
qs('#account-logout').addEventListener('click',async function(){
 this.disabled=true;
 try{await fetch(API+'/auth/logout',{method:'POST',credentials:'include'});signedInUser=null;pendingCheckout=false;pendingChatMessage=null;stopHumanReplyPolling();await refreshAccount();renderCart();toast('Kirjauduit ulos.');}
 catch(error){toast('Uloskirjautuminen ei onnistunut.');}
 finally{this.disabled=false;}
});
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!qs('#cart-overlay').hidden){closeOverlay();qs('#cart-toggle').focus();}else if(e.key==='Escape'&&!qs('#product-overlay').hidden){closeOverlay();}});
refreshAccount();renderProducts();renderFavorites();renderCart();
