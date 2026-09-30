const API='http://127.0.0.1:8000';
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
let favorites=new Set();let cart=[];let selectedProduct=null;let selectedColor='';let selectedSize='';
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
  if(!color||!color.stock.includes(size)||!Number.isSafeInteger(quantity)||quantity<1||quantity>99)return;
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
function toast(message){const el=qs('#toast');el.textContent=message;el.hidden=false;el.classList.add('visible');clearTimeout(window.koivuToast);window.koivuToast=setTimeout(function(){el.classList.remove('visible');setTimeout(function(){if(!el.classList.contains('visible'))el.hidden=true;},220);},2100);}
function renderProducts(){
 let visible=products.filter(function(p){return(filter.category==='kaikki'||p.category===filter.category)&&((p.name+' '+p.material+' '+p.colors.map(function(c){return c.name;}).join(' ')).toLocaleLowerCase('fi').includes(filter.query.toLocaleLowerCase('fi')))&&(!filter.favorite||favorites.has(p.id));});
 if(filter.sort==='low')visible=visible.slice().sort(function(a,b){return a.price-b.price;});
 if(filter.sort==='high')visible=visible.slice().sort(function(a,b){return b.price-a.price;});
 if(filter.sort==='name')visible=visible.slice().sort(function(a,b){return a.name.localeCompare(b.name,'fi');});
 qs('#product-count').textContent=visible.length+' '+(filter.favorite?'suosikkia':filter.query?'tuotetta löytyi':'huolella valittua tuotetta');
 qs('#product-grid').innerHTML=visible.length?visible.map(function(p,index){
   const c=firstColor(p);
   return '<article class="card" style="animation-delay:'+index*.035+'s"><div class="product-photo"><img src="'+esc(p.image)+'" alt="'+esc(p.alt)+'" loading="lazy" decoding="async">'+(p.badge?'<span class="badge">'+esc(p.badge)+'</span>':'')+
   '<button class="heart" type="button" data-act="favorite" data-id="'+esc(p.id)+'" aria-pressed="'+favorites.has(p.id)+'" aria-label="'+(favorites.has(p.id)?'Poista suosikeista: ':'Lisää suosikkeihin: ')+esc(p.name)+'"><svg viewBox="0 0 24 24"><path d="M20.5 8.9c0 4-8.5 10.4-8.5 10.4S3.5 12.9 3.5 8.9a4.5 4.5 0 0 1 8.5-2.1 4.5 4.5 0 0 1 8.5 2.1Z"/></svg></button><button class="quick" type="button" data-act="open" data-id="'+esc(p.id)+'">Valitse koko &amp; väri　→</button></div>'+
   '<div class="info"><p class="category">'+(p.category==='neuleet'?'Luonnonmateriaalit':p.category==='asusteet'?'Ajaton asuste':'Vaatteet jokapäiväiseen käyttöön')+'</p><div class="title-row"><button class="name" type="button" data-act="open" data-id="'+esc(p.id)+'">'+esc(p.name)+'</button><span class="price">'+p.price+' €</span></div><p class="material">'+esc(p.material)+'</p><div class="swatches" aria-label="Värivaihtoehdot">'+p.colors.map(function(col){return '<button class="swatch" type="button" style="background:'+esc(col.hex)+'" title="'+esc(col.name)+(col.stock.length?'':' · Loppuunmyyty')+'" aria-label="'+esc(col.name)+(col.stock.length?'':' · Loppuunmyyty')+'" aria-pressed="'+(col.name===c.name)+'" '+(!col.stock.length?'disabled':'')+' data-act="color" data-id="'+esc(p.id)+'" data-color="'+esc(col.name)+'"></button>';}).join('')+'</div></div></article>';
 }).join(''):'<p class="empty"><strong>'+ (filter.favorite?'Ei vielä suosikkeja.':'Tuotteita ei löytynyt.')+'</strong>Lisää tuotteita suosikkeihin painamalla sydäntä, tai kokeile uutta hakusanaa.</p>';
}
function renderFavorites(){qs('#favorite-count').textContent=favorites.size;qs('#favorite-count').hidden=!favorites.size;qs('#favorites-toggle').setAttribute('aria-pressed',filter.favorite);}
function saveFavorites(){try{localStorage.setItem('koivu-favorites',JSON.stringify(Array.from(favorites)));}catch(e){}renderFavorites();renderProducts();}
function openOverlay(id){closeOverlay();qs(id).hidden=false;document.body.classList.add('overlay-open');const button=qs('button',qs(id));if(button)button.focus();}
function closeOverlay(){document.querySelectorAll('.overlay:not([hidden])').forEach(function(el){el.hidden=true;});document.body.classList.remove('overlay-open');selectedProduct=null;}
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
 qs('#progress').style.width=Math.min(sum/150*100,100)+'%';qs('#cart-footer').style.display=cart.length?'':'none';
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
 if(b.dataset.act==='open')openProduct(b.dataset.id);
 if(b.dataset.act==='color'){const wrap=b.closest('.swatches');wrap.querySelectorAll('.swatch').forEach(function(s){s.setAttribute('aria-pressed',String(s===b));});}
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
 if(button.dataset.cart==='plus')item.quantity++;if(button.dataset.cart==='minus')item.quantity--;if(button.dataset.cart==='remove'||item.quantity<1)cart=cart.filter(function(c){return c.key!==item.key;});renderCart();
});
document.querySelectorAll('.overlay').forEach(function(overlay){overlay.addEventListener('click',function(e){if(e.target===overlay||e.target.closest('[data-close]'))closeOverlay();});});
qs('#product-detail').addEventListener('click',function(e){
 const color=e.target.closest('[data-color-option]');if(color){selectedColor=color.dataset.colorOption;renderDetail();return;}
 const size=e.target.closest('[data-size]');if(size&&!size.disabled){selectedSize=size.dataset.size;renderDetail();return;}
 if(e.target.closest('#add-product'))addToCart();
 if(e.target.closest('#size-guide')){e.preventDefault();toast('Kokotaulukko: paita XS 76–80 cm · S 80–84 cm · M 84–88 cm · L 88–94 cm rinnanympärys.');}
});
qs('#checkout').addEventListener('click',function(){toast('Kassa avautuu pian. Valitsemasi tuotteet säilyvät ostoskorissa.');});
function openChat(){const win=qs('#chat-window');if(!win.classList.contains('open')){win.classList.add('open');qs('#chat-toggle').setAttribute('aria-expanded','true');if(!qs('#chat-messages').children.length)initChat();}qs('#chat-input').focus();}
qs('#chat-help').addEventListener('click',openChat);
let humanMode=false,isLoading=false,isInitializing=false,conversationHistory=[];
const WELCOME_MESSAGE='Hei! Olen Koivun AI-asiakaspalvelija. Voin auttaa sinua löytämään sopivan tuotteen, tarkistamaan saatavuuden ja vastaamaan kysymyksiin. Miten voin auttaa? 🌿';
function initChat(){
 if(isInitializing)return;isInitializing=true;qs('#chat-reset').disabled=true;qs('#chat-send').disabled=true;
 fetch(API+'/setup',{method:'POST'}).catch(function(e){console.warn('Backend ei ole käynnissä:',e);}).finally(function(){
 if(!conversationHistory.length){addMessage('bot',WELCOME_MESSAGE);conversationHistory.push({role:'assistant',content:WELCOME_MESSAGE});}
 isInitializing=false;qs('#chat-reset').disabled=false;qs('#chat-send').disabled=false;
 });
}
qs('#chat-toggle').addEventListener('click',function(){
 const open=qs('#chat-window').classList.toggle('open');this.setAttribute('aria-expanded',String(open));
 if(open&&!qs('#chat-messages').children.length)initChat();if(open)qs('#chat-input').focus();
});
qs('#chat-minimize').addEventListener('click',function(){qs('#chat-window').classList.remove('open');qs('#chat-toggle').setAttribute('aria-expanded','false');});
qs('#chat-reset').addEventListener('click',function(){
 if(isLoading||isInitializing)return;humanMode=false;conversationHistory=[];removeTyping();qs('#chat-messages').replaceChildren();qs('#chat-input').value='';qs('#escalate-btn').style.display='none';
 qs('#chat-avatar').textContent='✦';qs('#chat-name').textContent='Koivu Tuki';qs('#chat-status').textContent='AI-assistentti · Vastaa heti';
 addMessage('bot',WELCOME_MESSAGE);conversationHistory.push({role:'assistant',content:WELCOME_MESSAGE});
});
qs('#chat-form').addEventListener('submit',async function(e){
 e.preventDefault();if(isLoading||isInitializing)return;const input=qs('#chat-input'),message=input.value.trim();if(!message)return;input.value='';addMessage('user',message);showTyping();isLoading=true;qs('#chat-send').disabled=true;qs('#chat-reset').disabled=true;
 try{
  const endpoint=humanMode?'/human-chat':'/chat';
  const response=await fetch(API+endpoint,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({message:message,history:conversationHistory.slice(-12)})});
  removeTyping();if(!response.ok)throw new Error('API-virhe');const data=await response.json();
  addMessage(humanMode?'human-agent':'bot',data.answer);conversationHistory.push({role:'user',content:message});conversationHistory.push({role:'assistant',content:data.answer});
  if(data.should_escalate&&!humanMode)qs('#escalate-btn').style.display='block';
 }catch(error){removeTyping();addMessage('bot','Yhteysvirhe. Tarkista että backend on käynnissä (uvicorn main:app --reload).');}
 finally{isLoading=false;qs('#chat-send').disabled=false;qs('#chat-reset').disabled=false;input.focus();}
});
qs('#escalate-btn').addEventListener('click',function(){
 humanMode=true;this.style.display='none';qs('#chat-avatar').textContent='👤';qs('#chat-name').textContent='Maija – Asiakaspalvelu';qs('#chat-status').textContent='Demo · AI-simuloitu asiakaspalvelija';
 const intro='Hei, Maija täällä Koivun asiakaspalvelusta! Olen lukenut keskustelun läpi. Miten voin auttaa sinua? 🌿';addMessage('human-agent',intro);conversationHistory.push({role:'assistant',content:intro});
});
function addMessage(type,text){const bubble=document.createElement('div');bubble.className='msg msg-'+type;bubble.textContent=text;const box=qs('#chat-messages');box.appendChild(bubble);box.scrollTop=box.scrollHeight;}
function showTyping(){const t=document.createElement('div');t.id='typing';t.className='typing-indicator';t.innerHTML='<span class="typing-dot"></span><span class="typing-dot"></span><span class="typing-dot"></span>';qs('#chat-messages').appendChild(t);}
function removeTyping(){const t=qs('#typing');if(t)t.remove();}
document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!qs('#cart-overlay').hidden){closeOverlay();qs('#cart-toggle').focus();}else if(e.key==='Escape'&&!qs('#product-overlay').hidden){closeOverlay();}});
renderProducts();renderFavorites();renderCart();
