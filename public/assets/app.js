document.addEventListener('DOMContentLoaded',function(){
var f=document.getElementById('cform');
if(f&&!f.getAttribute('action')){f.addEventListener('submit',function(e){e.preventDefault();
document.getElementById('fmsg').hidden=false;});}
var lb=document.getElementById('lb'),lbi=lb.querySelector('img');
document.querySelectorAll('[data-full]').forEach(function(el){el.addEventListener('click',function(){
lbi.src=el.getAttribute('data-full');lb.classList.add('open');});});
lb.addEventListener('click',function(){lb.classList.remove('open');lbi.src='';});
document.addEventListener('keydown',function(e){if(e.key==='Escape'){lb.classList.remove('open');}});
});