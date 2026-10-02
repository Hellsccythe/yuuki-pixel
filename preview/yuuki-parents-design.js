'use strict';
const BASE='../Assets/Game/Resources/',names=['Sara','Kled'],assets=new Map();
let color='#ffffff',ready=false;
const loadImage=src=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(Error(src));im.src=src;});
function render(){
 if(!ready)return;
 for(const name of names){
  const a=assets.get(name),canvas=document.getElementById(name),ctx=canvas.getContext('2d');
  ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,384,400);ctx.drawImage(a.body,-64,-32);
  if(document.getElementById('halo').checked){
   const scratch=document.createElement('canvas');scratch.width=a.halo.width;scratch.height=a.halo.height;
   const hc=scratch.getContext('2d');hc.drawImage(a.halo,0,0);
   const pixels=hc.getImageData(0,0,scratch.width,scratch.height),rgb=color.match(/[0-9a-f]{2}/gi).map(x=>parseInt(x,16));
   for(let i=0;i<pixels.data.length;i+=4)for(let ch=0;ch<3;ch++)pixels.data[i+ch]=Math.round(pixels.data[i+ch]*rgb[ch]/255);
   hc.putImageData(pixels,0,0);
   const h=a.profile.halo;ctx.save();ctx.globalAlpha=h.opacity;
   ctx.drawImage(scratch,h.anchor.x-64-Math.floor(scratch.width/2),h.anchor.y-32-Math.floor(scratch.height/2));ctx.restore();
  }
 }
}
document.getElementById('halo').onchange=render;
document.getElementById('background').onclick=()=>{const light=document.body.classList.toggle('light');document.getElementById('background').textContent=light?'Usar fundo escuro':'Usar fundo claro';};
document.querySelectorAll('[data-color]').forEach(b=>b.onclick=()=>{color=b.dataset.color;document.querySelectorAll('[data-color]').forEach(x=>x.setAttribute('aria-pressed',String(x===b)));render();});
async function init(){
 await Promise.all(names.map(async name=>{
  const response=await fetch(BASE+'Parents/'+(name==='Kled'?'KledV2':name)+'/design.json',{cache:'no-store'});if(!response.ok)throw Error('Design indisponível');
  const profile=await response.json();const [body,halo]=await Promise.all([loadImage(BASE+profile.body+'.png'),loadImage(BASE+profile.halo.resource+'.png')]);
  assets.set(name,{profile,body,halo});
 }));
 ready=true;render();document.getElementById('status').textContent='Sara e Kled · modelos aprovados';
}
init().catch(e=>{document.getElementById('status').textContent='Não foi possível carregar os sprites. Atualize a página para tentar novamente.';console.error(e);});
