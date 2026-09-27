const base = '../Assets/Game/Resources/World/';
const canvas = document.querySelector('#game');
const ctx = canvas.getContext('2d');
const keys = new Set();
const images = new Map();
const visited = new Map();
const overlay = document.querySelector('#overlay');
let world, level, objects, points, solid, floor, player, nearby, time = 0, last = 0;
let camera = {x:0,y:0};
const width=960,height=640,heroScale=.32;
const clips={walk_left:0,walk_right:1,run_left:2,run_right:3};
const hero=await load('../Assets/Game/Art/Yuuki/Yuuki_Movement_6x6.png?v=3');
const idle=await load('../Assets/Game/Art/Yuuki/Yuuki_Idle_2x1.png?v=3');

function load(url){return new Promise((resolve,reject)=>{const im=new Image();im.onload=()=>resolve(im);im.onerror=()=>reject(new Error('Não foi possível carregar '+url));im.src=url;});}
function getMap(id){return world.maps.find(map=>map.id===id);}
function enter(id,x,y){
  level=getMap(id);objects=[...level.objects];points=[...level.points];
  for(const instance of level.instances){
    const module=world.modules.find(m=>m.id===instance.module);
    objects.push(...module.objects.map(o=>({...o,x:o.x+instance.x,y:o.y+instance.y})));
    points.push(...module.points.map(p=>({...p,x:p.x+instance.x,y:p.y+instance.y})));
  }
  solid=objects.filter(o=>o.solid).map(o=>({x:o.x+o.footprint[0],y:o.y+o.footprint[1],w:o.footprint[2],h:o.footprint[3]}));
  floor=images.get('floor-'+id);player={x:x??level.spawnX,y:y??level.spawnY,facing:'right',moving:false,running:false};
  if(id!=='suburbs'){
    solid.push({x:0,y:0,w:level.width,h:55},{x:0,y:0,w:45,h:level.height},{x:level.width-45,y:0,w:45,h:level.height},{x:0,y:level.height-35,w:level.width,h:35});
  }
  time=0;nearby=null;updateCamera(true);updateLocation();
}
function blocked(x,y){const radius=12;return x<20||y<20||x>level.width-20||y>level.height-20||solid.some(r=>x+radius>r.x&&x-radius<r.x+r.w&&y+radius>r.y&&y-radius<r.y+r.h);}
function updateCamera(){camera.x=Math.max(0,Math.min(level.width-width,player.x-width*.5));camera.y=Math.max(0,Math.min(level.height-height,player.y-height*.57));}
function updateLocation(){const region=level.regions.find(r=>player.x>=r.x&&player.x<r.x+r.w&&player.y>=r.y&&player.y<r.y+r.h);document.querySelector('#location').textContent=region?.name||level.name;}
function panel(title,body){keys.clear();document.querySelector('#dialogTitle').textContent=title;document.querySelector('#dialogBody').replaceChildren(body);overlay.hidden=false;}
function paragraph(text){const p=document.createElement('p');p.textContent=text;return p;}
function close(){overlay.hidden=true;keys.clear();canvas.focus();}
function interact(){
  if(!overlay.hidden){close();return;}
  if(!nearby)return;
  if(nearby.target){enter(nearby.target,nearby.targetX,nearby.targetY);return;}
  if(nearby.journal)visited.set(nearby.id,nearby.title);
  document.querySelector('#progress').textContent=`Lembranças do bairro · ${visited.size}/5`;
  panel(nearby.title,paragraph(nearby.text));
}
function journal(){const wrap=document.createElement('div');wrap.append(paragraph('Conheça os caminhos da infância: a casa, o beco, a escola e o limiar da cidade.'));
  const ul=document.createElement('ul');for(const title of visited.values()){const li=document.createElement('li');li.textContent=title;ul.append(li);}wrap.append(ul);
  if(!visited.size)wrap.append(paragraph('As lembranças encontradas vão aparecer aqui. Aproxime-se de um ponto de interesse e pressione E.'));
  panel('Os caminhos de casa',wrap);
}
function showMap(){const wrap=document.createElement('div');wrap.innerHTML='<svg class="map" viewBox="0 0 768 512" role="img" aria-label="Mapa do bairro"><path d="M0 184H768M148 120V360M300 190V360M130 355H620M535 190V355"/><rect x="95" y="63" width="70" height="67"/><rect x="260" y="62" width="57" height="63"/><rect x="419" y="54" width="65" height="68"/><rect x="210" y="248" width="65" height="58"/><rect x="327" y="240" width="50" height="65"/><rect x="485" y="230" width="88" height="90"/><rect x="625" y="80" width="112" height="65"/><text x="94" y="152">Casa de Yuuki</text><text x="225" y="332">Beco da cerca</text><text x="485" y="342">Escola</text><text x="625" y="165">Portão do centro</text></svg>';
  if(level.id==='suburbs'){const dot=document.createElementNS('http://www.w3.org/2000/svg','circle');dot.setAttribute('cx',player.x/4);dot.setAttribute('cy',player.y/4);dot.setAttribute('r','6');dot.setAttribute('fill','#993f39');dot.setAttribute('stroke','#fff1c7');dot.setAttribute('stroke-width','2');wrap.querySelector('svg').append(dot);}
  const hint=paragraph(level.id==='suburbs'?'Você está no ponto vermelho.':'Você está dentro de '+level.name.toLowerCase()+'.');hint.className='hint';wrap.append(hint);panel('O bairro',wrap);
}
function update(dt){
  if(!overlay.hidden)return;
  let dx=(keys.has('d')||keys.has('arrowright')?1:0)-(keys.has('a')||keys.has('arrowleft')?1:0);
  let dy=(keys.has('s')||keys.has('arrowdown')?1:0)-(keys.has('w')||keys.has('arrowup')?1:0);
  const length=Math.hypot(dx,dy);if(length){dx/=length;dy/=length;}
  if(dx)player.facing=dx<0?'left':'right';
  player.running=keys.has('shift');const speed=player.running?265:155;
  const oldX=player.x,oldY=player.y;
  const steps=Math.max(1,Math.ceil(speed*dt/6));
  for(let i=0;i<steps;i++){if(!blocked(player.x+dx*speed*dt/steps,player.y))player.x+=dx*speed*dt/steps;if(!blocked(player.x,player.y+dy*speed*dt/steps))player.y+=dy*speed*dt/steps;}
  player.moving=Math.hypot(player.x-oldX,player.y-oldY)>.05;time=player.moving?time+dt:0;
  nearby=points.filter(p=>Math.hypot(p.x-player.x,p.y-player.y)<76).sort((a,b)=>Math.hypot(a.x-player.x,a.y-player.y)-Math.hypot(b.x-player.x,b.y-player.y))[0];
  const prompt=document.querySelector('#prompt');prompt.hidden=!nearby;if(nearby){prompt.replaceChildren();const k=document.createElement('kbd');k.textContent='E';prompt.append(k,nearby.title);}
  updateCamera();updateLocation();
}
function drawObject(o){const image=images.get(o.asset);ctx.drawImage(image,Math.round(o.x-o.width/2-camera.x),Math.round(o.y-o.height-camera.y),o.width,o.height);}
function drawHero(){
  const source=player.moving?hero:idle;const direction=player.facing;
  const col=player.moving?Math.floor(time*(player.running?12:8))%6:(direction==='left'?0:1);
  const row=player.moving?clips[(player.running?'run_':'walk_')+direction]:0;
  const pivot=player.moving&&player.running&&direction==='right'?396:400;
  ctx.fillStyle='#242d233b';ctx.beginPath();ctx.ellipse(Math.round(player.x-camera.x),Math.round(player.y-camera.y)-2,23,7,0,0,Math.PI*2);ctx.fill();
  ctx.drawImage(source,col*512,row*512,512,512,Math.round(player.x-256*heroScale-camera.x),Math.round(player.y-pivot*heroScale-camera.y),512*heroScale,512*heroScale);
}
function render(){
  ctx.imageSmoothingEnabled=false;ctx.clearRect(0,0,width,height);ctx.drawImage(floor,Math.round(-camera.x),Math.round(-camera.y));
  if(level.id!=='suburbs'){
    ctx.fillStyle='#302a20';ctx.fillRect(-camera.x,-camera.y,level.width,52);ctx.fillRect(-camera.x,-camera.y,42,level.height);ctx.fillRect(level.width-42-camera.x,-camera.y,42,level.height);ctx.fillRect(-camera.x,level.height-32-camera.y,level.width,32);
    const door=points.find(p=>p.target);ctx.fillStyle='#9a8058';ctx.fillRect(door.x-43-camera.x,level.height-50-camera.y,86,32);
  }
  const visible=objects.filter(o=>o.x+o.width/2>camera.x&&o.x-o.width/2<camera.x+width&&o.y>camera.y&&o.y-o.height<camera.y+height);
  visible.push({hero:true,y:player.y});visible.sort((a,b)=>a.y-b.y);for(const o of visible)o.hero?drawHero():drawObject(o);
  for(const p of points){if(Math.hypot(p.x-player.x,p.y-player.y)>135)continue;ctx.fillStyle=p.target?'#f3d69a':'#eadca8';const x=Math.round(p.x-camera.x),y=Math.round(p.y-camera.y)-13;ctx.beginPath();ctx.moveTo(x,y-4);ctx.lineTo(x+4,y);ctx.lineTo(x,y+4);ctx.lineTo(x-4,y);ctx.fill();}
}
function tick(now){const dt=Math.min(.04,(now-(last||now))/1000);last=now;update(dt);render();requestAnimationFrame(tick);}
window.addEventListener('keydown',e=>{const key=e.key.toLowerCase();if(['arrowleft','arrowright','arrowup','arrowdown',' '].includes(key))e.preventDefault();if(e.repeat)return;if(key==='e'){interact();return;}if(key==='escape'){close();return;}if(key==='j'){journal();return;}if(key==='m'){showMap();return;}if(overlay.hidden)keys.add(key);});
window.addEventListener('keyup',e=>keys.delete(e.key.toLowerCase()));window.addEventListener('blur',()=>keys.clear());
document.querySelector('#closeDialog').onclick=close;document.querySelector('#journalButton').onclick=journal;document.querySelector('#mapButton').onclick=showMap;document.querySelector('#touchAction').onclick=interact;
for(const button of document.querySelectorAll('[data-key]')){button.onpointerdown=e=>{e.preventDefault();button.setPointerCapture(e.pointerId);keys.add(button.dataset.key);};button.onpointerup=button.onpointercancel=button.onlostpointercapture=()=>keys.delete(button.dataset.key);}
try{
  const response=await fetch(base+'angel-suburbs.json');if(!response.ok)throw new Error('Mapa indisponível');world=await response.json();
  const names=new Set([...world.modules.flatMap(m=>m.objects),...world.maps.flatMap(m=>m.objects)].map(o=>o.asset));
  await Promise.all([...names].map(async name=>images.set(name,await load(base+'Art/'+name+'.png'))));
  await Promise.all(world.maps.map(async map=>images.set('floor-'+map.id,await load(base+'Floors/'+map.id+'.png'))));
  enter(world.startMap);document.querySelector('#loading').hidden=true;requestAnimationFrame(tick);
  // Read-only state is useful for accessibility and automated traversal checks.
  window.yuukiWorld={snapshot:()=>({map:level.id,x:player.x,y:player.y,moving:player.moving,nearby:nearby?.id,visited:[...visited.keys()],camera:{...camera},solids:solid,points:points.map(p=>({id:p.id,x:p.x,y:p.y,target:p.target}))})};
}catch(error){document.querySelector('#loading').textContent='Não foi possível abrir o bairro. '+error.message;throw error;}
