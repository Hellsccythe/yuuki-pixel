import {SchoolMorningModel,length} from './school-morning-model.mjs';
const $=id=>document.getElementById(id),canvas=$('world'),ctx=canvas.getContext('2d'),base='../Assets/Game/Resources/';
const json=async p=>{let r=await fetch(base+p+'.json');if(!r.ok)throw Error(p);return r.json();};
const assets=new Map();async function asset(p){if(assets.has(p))return assets.get(p);let im=new Image();im.src=base+p+'.png';await im.decode();assets.set(p,im);return im;}
let m,maps,yc,tc,actions,npcs,started=false,last=0,cam={x:460,y:695},keys=new Set(),actionIntent=false,nextIntent=false;
const actorStates={yuuki:{name:'',since:0},tenebris:{name:'',since:0}};
// Explicit opt-in visual integration check; ordinary players always control Yuuki.
const qa=new URLSearchParams(location.search).has('verificar'),qaSeen=new Set();let qaHolding=false;
if(qa){const button=document.createElement('button');button.id='qaContinue';button.textContent='Continuar verificação';button.hidden=true;document.querySelector('header').append(button);button.onclick=()=>{qaHolding=false;button.hidden=true;};}
function qaTick(dt){
  if(qaHolding)return;
  for(let n=0;n<5;n++){
    const s=m.current,puddle=s.id==='worry-walk'&&!qaSeen.has('puddle'),target=puddle?{x:2510,y:953}:s,d=Math.hypot(target.x-m.yuuki.x,target.y-m.yuuki.y);let input=d>20?{x:(target.x-m.yuuki.x)/d,y:(target.y-m.yuuki.y)/d}:{x:0,y:0};
    if(s.kind==='tutorial')input={x:1,y:0};if(s.kind==='race'&&d<30&&m.sprintSeconds<s.seconds)input={x:0,y:m.yuuki.y<820?1:-1};
    const checkpoint=puddle?'puddle':['gate-talk','leave-yard'].includes(s.id)?'gate':s.id;
    const ready=puddle&&d<20||checkpoint==='gate'&&m.gateOffset>=235||s.id==='ball-pick'&&m.actionPrompt||s.id==='wings-talk'&&m.stepTime>.5||s.id==='run-tip'||s.id==='exhaust'&&m.stepTime>.7||s.id==='arrival';
    if(ready&&!qaSeen.has(checkpoint)){qaSeen.add(checkpoint);m.tick(.01,{x:0,y:0},false,false,false);qaHolding=true;$('qaContinue').hidden=false;break;}
    m.tick(.05,input,['tutorial','race'].includes(s.kind),Boolean(m.actionPrompt),true);
    if(m.completed)break;
  }
}
function fit(){canvas.width=Math.round($('stage').clientWidth);canvas.height=Math.round($('stage').clientHeight);ctx.imageSmoothingEnabled=false;}new ResizeObserver(fit).observe($('stage'));
function start(){m=new SchoolMorningModel(m.data);started=true;cam={x:m.yuuki.x,y:m.yuuki.y-80};keys.clear();if(qa){qaSeen.clear();qaHolding=false;$('qaContinue').hidden=true;}Object.values(actorStates).forEach(a=>{a.name='';a.since=0;});$('menu').hidden=true;canvas.focus();}
$('start').onclick=start;$('resume').onclick=()=>{m.paused=false;canvas.focus();};$('restart').onclick=()=>{started=false;m.paused=false;keys.clear();$('pause').hidden=true;$('menu').hidden=false;};
$('pauseButton').onclick=()=>{if(started){m.paused=!m.paused;keys.clear();}};$('action').onclick=$('touchAction').onclick=()=>{actionIntent=true;canvas.focus();};$('next').onclick=()=>{nextIntent=true;canvas.focus();};
$('fullscreen').onclick=()=>document.fullscreenElement?document.exitFullscreen():$('stage').requestFullscreen();
window.addEventListener('keydown',e=>{if(!started)return;const k=e.key.length===1?e.key.toLowerCase():e.key;if(['ArrowUp','ArrowDown','ArrowLeft','ArrowRight',' ','Shift'].includes(k))e.preventDefault();keys.add(k);if(!e.repeat){if(k==='f')actionIntent=true;if(k===' '||k==='Enter')nextIntent=true;if(k==='Escape'){m.paused=!m.paused;keys.clear();}}});
window.addEventListener('keyup',e=>keys.delete(e.key.length===1?e.key.toLowerCase():e.key));window.addEventListener('blur',()=>keys.clear());
document.querySelectorAll('[data-key]').forEach(b=>{const k=b.dataset.key;b.addEventListener('pointerdown',e=>{b.setPointerCapture(e.pointerId);keys.add(k);});for(const event of ['pointerup','pointercancel','lostpointercapture'])b.addEventListener(event,()=>keys.delete(k));});
const screen=p=>({x:Math.round(p.x-cam.x+canvas.width/2),y:Math.round(p.y-cam.y+canvas.height/2)});
const clock=()=>{const minutes=405+Math.floor(m.time/30);return String(Math.floor(minutes/60)%24).padStart(2,'0')+':'+String(minutes%60).padStart(2,'0')+' · Os Subúrbios';};
function draw(p,x,y,w,feet=0,height=0){const im=assets.get(p),h=height||w*im.height/im.width;ctx.drawImage(im,Math.round(x-w/2),Math.round(y-(feet?feet/im.height*h:h)),Math.round(w),Math.round(h));}
function resident(p){
  const name=p.resource.split('/').pop(),clip=npcs.clips.find(c=>c.name===name),dog=name==='dog';
  const phase=m.time+(p.x%13)*.07,i=clip.sequence[Math.floor(phase*clip.fps)%clip.sequence.length];
  const world={x:p.x+(dog?45*Math.sin(m.time*.65):0),y:p.y},s=screen(world);
  if(dog&&Math.cos(m.time*.65)<0){ctx.save();ctx.translate(s.x,s.y);ctx.scale(-1,1);draw(clip.frames[i],0,0,512*.42,400);ctx.restore();}
  else draw(clip.frames[i],s.x,s.y,512*.42,400);
  if(!dog){const a=clip.haloAnchors[i],h={x:s.x+(a.x-256)*.42,y:s.y+(a.y-400)*.42};draw(npcs.halo.resource,h.x,h.y,assets.get(npcs.halo.resource).width*.42);return {x:h.x,y:h.y-15};}
  return {x:s.x,y:s.y-55};
}
function actor(name,cat,pos,v,face,special){
  const state=actorStates[name],motion=length(v)<1?'idle':length(v)>185?'run':'walk',clipName=special||motion+'_'+face;
  if(state.name!==clipName){state.name=clipName;state.since=m.time;}
  const clip=(special?actions.clips:cat.clips).find(c=>c.name===clipName),elapsed=m.time-state.since;let i;
  if(special==='strap_grip')i=clip.sequence[Math.floor(elapsed*clip.fps)%clip.sequence.length];
  else if(special==='exhaust')i=elapsed<.35?0:clip.sequence[Math.floor((elapsed-.35)*clip.fps)%clip.sequence.length];
  else if(name==='yuuki'&&m.ballHeld)i=3;
  else if(special){let seconds=name==='yuuki'?m.current.seconds:1.5,phase=name==='yuuki'&&m.actionPlaying?m.actionTime:m.stepTime;phase=m.current.id==='close-gate'?(phase%.8)/.8:phase/Math.max(.1,seconds);i=Math.max(0,Math.min(3,Math.floor(phase*4)));}
  else i=clip.sequence[Math.floor(elapsed*clip.fps)%clip.sequence.length];
  const p=screen(pos),scale=.42;draw(clip.frames[i],p.x,p.y,512*scale,400);
  const a=clip.haloAnchors[i],head={x:p.x+(a.x-256)*scale,y:p.y+(a.y-400)*scale};const im=assets.get(cat.halo.resource);draw(cat.halo.resource,head.x,head.y,im.width*scale);
  if(face==='up'&&!special)draw('SchoolMorning/Props/backpack',p.x,p.y-30,24);
  if(!special&&face==='down')draw('SchoolMorning/Props/straps',p.x,p.y-25,27);
  if(!special&&['left','right'].includes(face)){ctx.save();ctx.beginPath();ctx.rect(face==='left'?p.x-9:p.x, p.y-55,9,33);ctx.clip();draw('SchoolMorning/Props/straps',p.x+(face==='left'?4:-4),p.y-26,23);ctx.restore();}
  return {x:head.x,y:head.y-20};
}
function render(){
  ctx.clearRect(0,0,canvas.width,canvas.height);ctx.imageSmoothingEnabled=false;
  const left=cam.x-canvas.width/2,top=cam.y-canvas.height/2;
  let grass=assets.get('SchoolMorning/Ground/grass'),dirt=assets.get('SchoolMorning/Ground/dirt');
  for(let x=Math.floor(left/256)*256;x<left+canvas.width+256;x+=256)for(let y=Math.floor(top/256)*256;y<top+canvas.height+256;y+=256){let p=screen({x,y});ctx.drawImage(grass,p.x,p.y,256,256);}
  for(let x=Math.floor(left/128)*128;x<left+canvas.width+128;x+=128){let road=950+(755-950)*Math.max(0,Math.min(1,(x-1500)/(4170-1500))),p=screen({x,y:road-145});ctx.drawImage(dirt,0,0,128,256,p.x,p.y,128,256);}
  const list=[];for(const map of maps)if(m.yuuki.x>map.start-1000&&m.yuuki.x<map.end+1000)for(const p of map.objects)if(p.group!=='gate')list.push({...p,type:p.group==='residents'?'resident':'prop'});
  list.push({x:m.data.gate.x-(m.gateOffset||0),y:m.data.gate.y,w:235,resource:'SchoolMorning/Props/gate',type:'prop'});
  list.push({x:3030,y:820,w:16,resource:'World/Art/stone',type:'prop'});
  list.push({...m.yuuki,type:'yuuki'});if(m.tenebrisVisible)list.push({...m.tenebris,type:'tenebris'});let heads={};
  for(const p of list.sort((a,b)=>(a.group==='ground'?-150:a.y)-(b.group==='ground'?-150:b.y))){const s=screen(p);if(p.type==='prop'){if(s.x>-p.w&&s.x<canvas.width+p.w)draw(p.resource,s.x,s.y,p.w,0,p.h);}else if(p.type==='resident')heads[p.id]=resident(p);else if(p.type==='yuuki')heads.Yuuki=actor('yuuki',yc,m.yuuki,m.yv,m.yf,m.yuukiSpecial);else heads.Tenebris=actor('tenebris',tc,m.tenebris,m.tv,m.tf,m.tenebrisSpecial);}
  if(m.ballVisible){const b=screen(m.ballPosition);draw('SchoolMorning/Props/ball',b.x,b.y,m.ballOnGround?28:18);if(m.ballOnGround){ctx.fillStyle='#263b30';ctx.font='bold 12px sans-serif';ctx.textAlign='center';ctx.fillText('Bola de pano',b.x,b.y+18);}}
  $('hud').hidden=!started;$('objective').textContent=m.current.title;$('clock').textContent=clock();$('location').textContent=maps.find(a=>m.yuuki.x>=a.start&&m.yuuki.x<a.end)?.name||'';
  let line=m.speech;if(!line&&m.waitingHint)line={speaker:'Tenebris',text:'Eu espero aqui, Yuuki.'};
  const speech=$('speech');speech.hidden=!started||!line||m.tutorial||m.paused;if(line){speech.querySelector('b').textContent=line.speaker;speech.querySelector('p').textContent=line.text;let head=heads[line.speaker]||screen(m.yuuki),w=speech.offsetWidth,h=speech.offsetHeight,x=Math.max(12,Math.min(canvas.width-w-12,head.x-w/2)),y=Math.max(115,Math.min(canvas.height-h-80,head.y-h));speech.style.left=x+'px';speech.style.top=y+'px';speech.style.setProperty('--tail',Math.max(15,Math.min(w-30,head.x-x))+'px');}
  $('action').hidden=!started||!m.actionPrompt||m.tutorial||m.paused;if(m.actionPrompt)$('action').textContent='F · '+m.actionPrompt;
  $('tip').hidden=!started||!m.tutorial||m.paused;$('pause').hidden=!started||!m.paused;$('arrival').hidden=!started||!m.completed;
  const tp=screen(m.tenebris);$('waiting').hidden=!started||!m.tenebrisVisible||!(tp.x<0||tp.x>canvas.width);$('waiting').textContent=(tp.x<0?'←':'→')+' Tenebris'+(m.waiting?' está esperando':' está adiante');
  $('status').textContent=started?'Etapa '+(m.stepIndex+1)+'/'+m.data.steps.length+' · '+m.current.title:'Cenário pronto · animações com até quatro quadros · mapas conectados';
}
function frame(t){let dt=Math.min(.05,(t-last)/1000||0);last=t;if(m){if(started){let input={x:(keys.has('d')||keys.has('ArrowRight')?1:0)-(keys.has('a')||keys.has('ArrowLeft')?1:0),y:(keys.has('s')||keys.has('ArrowDown')?1:0)-(keys.has('w')||keys.has('ArrowUp')?1:0)};if(qa)qaTick(dt);else m.tick(dt,input,keys.has('Shift'),actionIntent,nextIntent);actionIntent=nextIntent=false;if(!m.paused&&!m.tutorial){let k=1-Math.exp(-6*dt);cam.x+=(m.yuuki.x-cam.x)*k;cam.y+=(m.yuuki.y-80-cam.y)*k;}}render();}requestAnimationFrame(frame);}
try{
  const story=await json('SchoolMorning/story');[maps,yc,tc,actions]=await Promise.all([Promise.all(story.maps.map(json)),json('Childhood/YuukiV2/animations'),json('Childhood/Tenebris/animations'),json('SchoolMorning/actions')]);
  npcs=await json('SchoolMorning/npcs');
  const paths=new Set(['SchoolMorning/Ground/grass','SchoolMorning/Ground/dirt','SchoolMorning/Props/gate','SchoolMorning/Props/backpack','SchoolMorning/Props/straps','SchoolMorning/Props/ball','World/Art/stone',yc.halo.resource,tc.halo.resource,npcs.halo.resource]);
  for(const map of maps)for(const p of map.objects)paths.add(p.resource);for(const cat of [yc,tc,actions,npcs])for(const clip of cat.clips)for(const f of clip.frames)paths.add(f);
  await Promise.all([...paths].map(asset));m=new SchoolMorningModel(story);$('start').disabled=false;$('start').textContent=qa?'Verificar percurso automaticamente':'Iniciar caminhada';fit();requestAnimationFrame(frame);
}catch(e){$('status').textContent='Erro ao carregar: '+e.message;$('start').textContent='Falha ao carregar cenário';console.error(e);}
