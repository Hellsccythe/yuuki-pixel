// Functional traversal with real keyboard input; no teleporting test hooks.
const assert=require('node:assert/strict');
const path=require('node:path');
const fs=require('node:fs');
const {chromium}=require(process.env.PLAYWRIGHT_PATH||'playwright');
(async()=>{
 const browser=await chromium.launch({channel:'msedge',headless:true});
 const page=await browser.newPage({viewport:{width:1200,height:920}});
 const errors=[];page.on('pageerror',e=>errors.push(e.message));page.on('response',r=>{if(r.status()>=400)errors.push(r.status()+': '+r.url());});
 const output=path.resolve(__dirname,'../Temp/world-qa');fs.mkdirSync(output,{recursive:true});
 try{
  await page.goto('http://127.0.0.1:8765/preview/world.html');await page.waitForFunction(()=>window.yuukiWorld);
  await page.clock.install();await page.clock.pauseAt(new Date());
  const snap=()=>page.evaluate(()=>window.yuukiWorld.snapshot());
  const advance=ms=>page.clock.runFor(Math.max(20,Math.round(ms)));
  async function move(key,ms){await page.keyboard.down(key);await advance(ms);await page.keyboard.up(key);await advance(20);}
  // Diagonal normalization: measure away from buildings on the wide main street.
  let state=await snap();let before={...state};await move('d',350);let after=await snap();const straight=Math.hypot(after.x-before.x,after.y-before.y);
  before=after;await page.keyboard.down('d');await move('s',350);await page.keyboard.up('d');after=await snap();const diagonal=Math.hypot(after.x-before.x,after.y-before.y);
  assert(Math.abs(straight-diagonal)<6,`Diagonal speed differs: ${straight}/${diagonal}`);
  async function route(id){
   const state=await snap(),target=state.points.find(p=>p.id===id);assert(target,id);
   const size=24,cols=140,rows=95;
   const free=(x,y)=>x>22&&y>22&&!state.solids.some(r=>x+15>r.x&&x-15<r.x+r.w&&y+15>r.y&&y-15<r.y+r.h);
   const start=[Math.round(state.x/size),Math.round(state.y/size)];const key=(x,y)=>y*cols+x;
   const queue=[start],seen=new Map([[key(...start),null]]);let end;
   for(let i=0;i<queue.length;i++){
    const [x,y]=queue[i];if(Math.hypot(x*size-target.x,y*size-target.y)<49){end=[x,y];break;}
    for(const [dx,dy] of [[1,0],[-1,0],[0,1],[0,-1]]){const nx=x+dx,ny=y+dy,k=key(nx,ny);if(nx<1||nx>=cols||ny<1||ny>=rows||seen.has(k)||!free(nx*size,ny*size))continue;seen.set(k,[x,y]);queue.push([nx,ny]);}
   }
   assert(end,'No reachable path to '+id);const steps=[];
   for(let cursor=end;cursor;cursor=seen.get(key(...cursor)))steps.push(cursor);steps.reverse();
   const corners=[];
   for(let i=0;i<steps.length;i++){if(i===0||i===steps.length-1||steps[i+1][0]-steps[i][0]!==steps[i][0]-steps[i-1][0]||steps[i+1][1]-steps[i][1]!==steps[i][1]-steps[i-1][1])corners.push(steps[i]);}
   await page.keyboard.down('Shift');
   for(const [gx,gy] of corners){
    for(const axis of ['x','y']){
     for(let correction=0;correction<3;correction++){
      const s=await snap(),distance=(axis==='x'?gx:gy)*size-s[axis];if(Math.abs(distance)<4)break;
      const key=axis==='x'?(distance>0?'d':'a'):(distance>0?'s':'w');await move(key,Math.abs(distance)/265*1000);
     }
    }
   }
   await page.keyboard.up('Shift');await advance(30);const arrived=await snap();
   assert.equal(arrived.nearby,id,`Route to ${id} ended at ${arrived.x},${arrived.y}, near ${arrived.nearby}`);
  }
  async function use(){await page.keyboard.press('e');await advance(50);}
  await route('home-door');await use();assert.equal((await snap()).map,'home');
  await page.screenshot({path:path.join(output,'home.png')});
  await route('home-book');await use();assert((await snap()).visited.includes('home-book'));
  const frozen=await snap();await move('w',400);assert.equal((await snap()).y,frozen.y,'Dialog must stop movement');await use();
  await route('home-exit');await use();assert.equal((await snap()).map,'suburbs');
  await route('family-gate');await use();await use();
  // A solid front wall must stop the player.
  await route('home-door');await move('w',1300);state=await snap();assert(state.y>=556,'Walked through house front');
  await page.screenshot({path:path.join(output,'street.png')});
  await route('alley-memory');await page.screenshot({path:path.join(output,'alley.png')});await use();await use();
  await route('school-door');await page.screenshot({path:path.join(output,'school.png')});await use();assert.equal((await snap()).map,'library');
  await route('library-shelf');await page.screenshot({path:path.join(output,'library.png')});await use();await use();
  await route('library-exit');await use();assert.equal((await snap()).map,'suburbs');
  await route('city-gate');await page.screenshot({path:path.join(output,'gate.png')});await use();await use();
  assert.equal((await snap()).visited.length,5);
  await page.keyboard.press('m');assert.equal(await page.locator('#dialogTitle').textContent(),'O bairro');await page.screenshot({path:path.join(output,'map.png')});await page.keyboard.press('Escape');
  await page.keyboard.press('j');assert.match(await page.locator('#dialogBody').textContent(),/O refúgio de Yuuki/);await page.keyboard.press('Escape');
  assert.deepEqual(errors,[]);
  console.log(JSON.stringify({passed:true,diagonalNormalized:true,collision:true,portals:'home + library, both ways',journal:5,screenshots:output}));
 }finally{await browser.close();}
})().catch(e=>{console.error(e);process.exitCode=1;});
