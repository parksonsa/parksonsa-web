document.addEventListener('DOMContentLoaded',function(){
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
if(f&&!f.getAttribute('action')){f.addEventListener('submit',function(e){e.preventDefault();
document.getElementById('fmsg').hidden=false;});}
document.querySelectorAll('.more-btn').forEach(function(b){b.addEventListener('click',function(){
document.getElementById(b.getAttribute('data-for')).classList.add('open');b.remove();});});
var lb=document.getElementById('lb'),lbi=lb.querySelector('img');
document.querySelectorAll('[data-full]').forEach(function(el){el.addEventListener('click',function(){
lbi.src=el.getAttribute('data-full');lb.classList.add('open');});});
lb.addEventListener('click',function(){lb.classList.remove('open');lbi.src='';});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){lb.classList.remove('open');}});
});