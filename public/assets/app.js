document.addEventListener('DOMContentLoaded',function(){
var AS={};try{var q=new URLSearchParams(location.search);
['n_media','n_query','n_rank','n_keyword','utm_source','utm_term'].forEach(function(k){if(q.get(k)){AS[k]=q.get(k);}});
if(Object.keys(AS).length){sessionStorage.setItem('adsrc',JSON.stringify(AS));}
else{AS=JSON.parse(sessionStorage.getItem('adsrc')||'{}');}}catch(e){}
var TL={};
function trk(kind){var n=Date.now();if(TL[kind]&&n-TL[kind]<10000){return;}TL[kind]=n;
try{if(window.wcs&&wcs.trans){var T={phone:'call',phone_copy:'call',kakao:'add_contact_method',form:'lead'};wcs.trans({type:T[kind]||'custom001'});}}catch(e){}
if(window.gtag){gtag('event','generate_lead',{method:kind,ad_keyword:AS.n_query||AS.n_keyword||AS.utm_term||'(none)',
ad_media:AS.n_media||AS.utm_source||'(organic)',ad_rank:AS.n_rank||''});}}
document.addEventListener('click',function(e){var a=e.target.closest&&e.target.closest('a');if(!a){return;}
var h=a.getAttribute('href')||'';if(h.indexOf('tel:')===0){trk('phone');}
else if(h.indexOf('open.kakao.com')>-1){trk('kakao');}},true);
document.addEventListener('copy',function(){
if(/010[- .]?[0-9]{4}[- .]?[0-9]{4}/.test(String(window.getSelection()||''))){trk('phone_copy');}});
var mb=document.getElementById('menubtn'),mm=document.getElementById('mmenu'),
    mx=document.getElementById('mmclose');
if(mb&&mm){
  var open=function(){mm.hidden=false;document.body.style.overflow='hidden';
    mb.setAttribute('aria-expanded','true');};
  var close=function(){mm.hidden=true;document.body.style.overflow='';
    mb.setAttribute('aria-expanded','false');};
  mb.addEventListener('click',open);
  if(mx){mx.addEventListener('click',close);}
  mm.querySelectorAll('a').forEach(function(a){a.addEventListener('click',close);});
  document.addEventListener('keydown',function(e){if(e.key==='Escape'&&!mm.hidden){close();}});
}
var f=document.getElementById('cform');
if(f){var fm=document.getElementById('fmsg'),fb=document.getElementById('fbtn');
function say(t,ok){fm.textContent=t;fm.hidden=false;fm.className='formmsg'+(ok?' ok':' err');}
f.addEventListener('submit',function(e){e.preventDefault();var u=f.getAttribute('action');
if(!u){say('현재 온라인 접수 준비 중입니다. 전화(010-2754-1552)나 카카오톡으로 연락해 주세요.',false);return;}
fb.disabled=true;fb.textContent='접수 중…';
fetch(u,{method:'POST',body:new FormData(f),headers:{'Accept':'application/json'}}).then(function(r){
if(r.ok){f.reset();trk('form');say('상담 신청이 접수되었습니다. 확인 후 남겨주신 연락처로 연락드리겠습니다.',true);}
else{throw 0;}}).catch(function(){say('접수 중 문제가 생겼습니다. 번거로우시겠지만 전화(010-2754-1552)나 카카오톡으로 연락해 주세요.',false);})
.then(function(){fb.disabled=false;fb.textContent='상담 신청하기';});});}
document.querySelectorAll('.more-btn').forEach(function(b){b.addEventListener('click',function(){
document.getElementById(b.getAttribute('data-for')).classList.add('open');b.remove();});});
var lb=document.getElementById('lb'),lbi=lb.querySelector('img');
document.querySelectorAll('[data-full]').forEach(function(el){el.addEventListener('click',function(){
lbi.src=el.getAttribute('data-full');lb.classList.add('open');});});
lb.addEventListener('click',function(){lb.classList.remove('open');lbi.src='';});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){lb.classList.remove('open');}});
});