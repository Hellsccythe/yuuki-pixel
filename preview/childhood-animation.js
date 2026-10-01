'use strict';
const $=id=>document.getElementById(id),canvas=$('preview'),ctx=canvas.getContext('2d');
const BASE='../Assets/Game/Resources/', images=new Map(), keys=new Set();
const names={walk:'Andar',run:'Correr',idle:'Respiração',up:'Costas',down:'Frente',left:'Esquerda',right:'Direita'};
let catalog,clips,clip,haloSource,haloPixels,haloCanvas=document.createElement('canvas'),ready=false;
let direction='left',motion='run',elapsed=0,playing=true,last=0,wasMoving=false,activeIndex=-1;
let position={x:320,y:363};
ctx.imageSmoothingEnabled=false;
const imageLoad=src=>new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(new Error(src));im.src=src;});
function colorHalo(){
 if(!haloPixels)return;
 const c=$('tint').value.match(/[0-9a-f]{2}/gi).map(n=>parseInt(n,16));
 const pixels=new Uint8ClampedArray(haloPixels.data);
 for(let i=0;i<pixels.length;i+=4)for(let ch=0;ch<3;ch++)pixels[i+ch]=Math.round(pixels[i+ch]*c[ch]/255);
 haloCanvas.getContext('2d').putImageData(new ImageData(pixels,haloPixels.width,haloPixels.height),0,0);
}
function select(nextMotion=motion,nextDirection=direction){
 motion=nextMotion;direction=nextDirection;clip=clips.get(motion+'_'+direction);elapsed=0;activeIndex=-1;
 $('motion').value=motion;document.querySelectorAll('[data-direction]').forEach(b=>b.setAttribute('aria-pressed',String(b.dataset.direction===direction)));
 $('badge').textContent=names[motion]+' · '+names[direction];
 $('sequence').textContent='Ordem do ciclo: '+clip.sequence.map(i=>i+1).join(' → ');
 $('frames').replaceChildren(...clip.frames.map((path,i)=>{
  const b=document.createElement('button');b.setAttribute('aria-label','Ver quadro '+(i+1));b.type='button';
  const im=document.createElement('img');im.src=BASE+path+'.png';im.alt='';b.append(im,document.createTextNode(String(i+1).padStart(2,'0')));
  b.onclick=()=>{playing=false;elapsed=clip.sequence.indexOf(i)/clip.fps;updatePlay();draw();};return b;
 }));
}
function updatePlay(){$('play').textContent=playing?'Pausar':'Reproduzir';}
function step(delta){
 playing=false;updatePlay();
 const current=Math.floor(elapsed*clip.fps+1e-7);
 elapsed=((current+delta+clip.sequence.length)%clip.sequence.length)/clip.fps;
 draw();
}
function index(){return clip.sequence[Math.floor(elapsed*clip.fps+1e-7)%clip.sequence.length];}
function draw(){
 if(!ready)return;
 ctx.clearRect(0,0,640,440);
 const i=index(),im=images.get(clip.frames[i]),anchor=clip.haloAnchors[i];
 // Integer positions and nearest-neighbor rendering prevent blurred movement.
 const x=Math.round(position.x),y=Math.round(position.y);
 if($('guide').checked){ctx.strokeStyle='#d9bb83';ctx.lineWidth=1;ctx.beginPath();ctx.moveTo(x-90,y+.5);ctx.lineTo(x+90,y+.5);ctx.stroke();ctx.fillStyle='#d9bb83';ctx.fillRect(x-2,y-2,4,4);}
 ctx.drawImage(im,x-256,y-400);
 if($('halo').checked)ctx.drawImage(haloCanvas,x-256+anchor.x-48,y-400+anchor.y-14);
 if(i!==activeIndex){
  activeIndex=i;$('status').textContent=names[motion]+' · '+names[direction]+' · quadro '+(i+1)+' de '+clip.frames.length;
  [...$('frames').children].forEach((b,j)=>{b.classList.toggle('active',i===j);b.setAttribute('aria-pressed',String(i===j));});
 }
}
function tick(now){
 const dt=Math.min(.05,(now-last)/1000||0);last=now;
 if(ready){
  let dx=Number(keys.has('d')||keys.has('arrowright'))-Number(keys.has('a')||keys.has('arrowleft'));
  let dy=Number(keys.has('s')||keys.has('arrowdown'))-Number(keys.has('w')||keys.has('arrowup'));
  const moving=!!(dx||dy);
  if(moving){
   const facing=Math.abs(dy)>Math.abs(dx)?(dy<0?'up':'down'):(dx<0?'left':'right');
   const state=keys.has('shift')?'run':'walk';
   if(facing!==direction||state!==motion)select(state,facing);
   playing=true;updatePlay();
   const distance=(state==='run'?100:58)*dt/Math.hypot(dx,dy);
   position.x=Math.max(120,Math.min(520,position.x+dx*distance));
   position.y=Math.max(275,Math.min(418,position.y+dy*distance));
  }else if(wasMoving){select('idle');playing=true;updatePlay();}
  wasMoving=moving;
  if(playing)elapsed+=dt*Number($('speed').value);
  draw();
 }
 requestAnimationFrame(tick);
}
$('play').onclick=()=>{playing=!playing;updatePlay();};
$('next').onclick=()=>step(1);$('previous').onclick=()=>step(-1);
$('reset').onclick=()=>{position={x:320,y:363};draw();};
$('motion').onchange=()=>{select($('motion').value);playing=true;updatePlay();};
document.querySelectorAll('[data-direction]').forEach(b=>b.onclick=()=>{select(motion,b.dataset.direction);draw();});
$('speed').oninput=()=>{$('speed-label').textContent=$('speed').value+'×';};
$('tint').oninput=()=>{colorHalo();draw();};
document.querySelectorAll('[data-color]').forEach(b=>b.onclick=()=>{$('tint').value=b.dataset.color;colorHalo();draw();});
$('halo').onchange=$('guide').onchange=draw;
$('background').onclick=()=>{const light=$('stage').classList.toggle('light');$('background').textContent=light?'Usar fundo escuro':'Usar fundo claro';};
canvas.addEventListener('keydown',event=>{
 const key=event.key.toLowerCase();if(['w','a','s','d','arrowup','arrowdown','arrowleft','arrowright','shift'].includes(key)){event.preventDefault();keys.add(key);}
});
window.addEventListener('keyup',event=>keys.delete(event.key.toLowerCase()));
function blur(){keys.clear();if(ready&&wasMoving){select('idle');wasMoving=false;}}
canvas.addEventListener('blur',blur);window.addEventListener('blur',blur);
document.addEventListener('visibilitychange',()=>{if(document.hidden)blur();});
async function init(){
 const response=await fetch(BASE+'Childhood/Yuuki/animations.json',{cache:'no-store'});if(!response.ok)throw Error('Catálogo indisponível');
 catalog=await response.json();clips=new Map(catalog.clips.map(c=>[c.name,c]));
 $('frame-count').textContent=catalog.clips.reduce((total,c)=>total+c.frames.length,0)+' quadros · 4 direções · idle com 3 desenhos';
 await Promise.all([...new Set(catalog.clips.flatMap(c=>c.frames))].map(async path=>images.set(path,await imageLoad(BASE+path+'.png'))));
 haloSource=await imageLoad(BASE+catalog.halo.resource+'.png');haloCanvas.width=haloSource.width;haloCanvas.height=haloSource.height;
 const hc=haloCanvas.getContext('2d');hc.drawImage(haloSource,0,0);haloPixels=hc.getImageData(0,0,haloSource.width,haloSource.height);colorHalo();
 document.querySelectorAll('button:disabled,select:disabled').forEach(b=>b.disabled=false);
 ready=true;select();draw();requestAnimationFrame(tick);
}
init().catch(e=>{$('status').textContent='Falha ao carregar a prévia. Atualize a página para tentar novamente.';$('badge').textContent='Falha ao carregar';console.error(e);});
