import assert from 'node:assert/strict';
import fs from 'node:fs';
import {SchoolMorningModel,length} from './school-morning-model.mjs';
const root=process.argv[2]||'D:/yuuki-pixel';const data=JSON.parse(fs.readFileSync(root+'/Assets/Game/Resources/SchoolMorning/story.json','utf8'));
const m=new SchoolMorningModel(data);let visited=[],last='',wait=false,tip=false,actions=0;
for(let tick=0;tick<35000&&!m.completed;tick++){
  const s=m.current;
  if(last!==s.id){visited.push(s.id);last=s.id;
    if(s.kind==='action'){
      const before=m.stepIndex;for(let n=0;n<60;n++)m.tick(.05,{x:0,y:0},false,false,false);assert.equal(m.stepIndex,before,'An action must require F');actions++;
    }
    if(s.id==='bread-walk'){for(let n=0;n<200;n++)m.tick(.05);assert(m.waiting);let p={...m.tenebris};m.tick(.05);assert.deepEqual(m.tenebris,p);wait=true;}
    if(s.kind==='tutorial'){
      const snapshot=JSON.stringify([m.time,m.yuuki,m.tenebris]);for(let n=0;n<100;n++)m.tick(.05,{x:1,y:0},false,true,true);assert(m.tutorial);assert.equal(JSON.stringify([m.time,m.yuuki,m.tenebris]),snapshot);
      m.tick(.05,{x:0,y:0},true);assert(m.tutorial);
      // Running into a boundary is not running. Use a separate model to test collision without altering the real route.
      const blocked=new SchoolMorningModel(data);blocked.stepIndex=m.stepIndex;blocked.yuuki={x:35,y:1200};blocked.tick(.05,{x:-1,y:0},true);assert(blocked.tutorial);assert.equal(blocked.time,0);tip=true;
    }
    if(s.id==='exhaust'){const p={...m.yuuki};m.tick(.05,{x:1,y:0},true,true);assert.deepEqual(m.yuuki,p);assert.equal(m.yuukiSpecial,'exhaust');}
  }
  let dx=s.x-m.yuuki.x,dy=s.y-m.yuuki.y,d=Math.hypot(dx,dy),input=d>20?{x:dx/d,y:dy/d}:{x:0,y:0};
  if(s.kind==='tutorial')input={x:1,y:0};if(s.kind==='race'&&d<30&&m.sprintSeconds<s.seconds)input={x:0,y:m.yuuki.y<820?1:-1};
  m.tick(.05,input,['tutorial','race'].includes(s.kind),Boolean(m.actionPrompt),true);
}
assert(m.completed,'Stalled at '+m.current.id+' '+JSON.stringify(m.yuuki));assert(wait&&tip&&m.tutorialUnlocked);assert(m.sprintSeconds>=3);assert(!m.gateOpen);assert.equal(actions,6);
const pauses=new SchoolMorningModel(data);pauses.paused=true;pauses.tick(.05,{x:1,y:1},true,true,true);assert.equal(pauses.time,0);assert.deepEqual(pauses.yuuki,data.start);
const edge=new SchoolMorningModel(data);edge.yuuki={x:602,y:815};edge.stepIndex=data.steps.findIndex(s=>s.id==='gate-help');edge.tenebrisVisible=true;for(let n=0;n<350;n++)edge.tick(.05,{x:0,y:0},false,false,true);assert.notEqual(edge.current.id,'gate-help','Gate assistance softlocked at an action-range edge');
for(const p of ['Childhood/YuukiV2/animations','Childhood/Tenebris/animations','SchoolMorning/actions','SchoolMorning/npcs']){const c=JSON.parse(fs.readFileSync(root+'/Assets/Game/Resources/'+p+'.json','utf8'));for(const clip of c.clips){assert(clip.frames.length<=4);assert.equal(clip.frames.length,clip.haloAnchors.length);for(const f of clip.frames)assert(fs.existsSync(root+'/Assets/Game/Resources/'+f+'.png'));}}
// Explore all reachable garden positions; the closed gate must be the only exit.
function yardCanEscape(open){const q=new SchoolMorningModel(data);q.gateOffset=open?235:0;const queue=[{x:460,y:777}],seen=new Set();for(let i=0;i<queue.length;i++){const p=queue[i];if(p.y>930||p.x<170||p.x>870||p.y<310)return true;for(const [dx,dy] of [[10,0],[-10,0],[0,10],[0,-10]]){const n={x:p.x+dx,y:p.y+dy},key=n.x+','+n.y;if(!seen.has(key)&&q.passable(n)){seen.add(key);queue.push(n);}}}return false;}
assert.equal(yardCanEscape(false),false,'Garden can be bypassed without opening the gate');assert.equal(yardCanEscape(true),true,'Fully opened gate does not release the exit');
const gateCheck=new SchoolMorningModel(data);gateCheck.gateOpen=true;gateCheck.tick(.05);assert(!gateCheck.passable({x:670,y:900}),'Gate collider opened before panel cleared');for(let i=0;i<40;i++)gateCheck.tick(.05);assert.equal(gateCheck.gateOffset,235);assert(gateCheck.passable({x:670,y:900}));
const dialogue=new SchoolMorningModel(data);dialogue.stepIndex=data.steps.findIndex(s=>s.id==='bread-talk');dialogue.tenebrisVisible=true;dialogue.tenebris={x:1300,y:950};dialogue.lineTime=0;dialogue.tick(.05,{x:0,y:0},false,false,true);assert(dialogue.waiting);assert.equal(dialogue.lineIndex,1,'Space/Enter must advance a fresh line even while escort waits');
dialogue.lineIndex=dialogue.current.lines.length;dialogue.stepIndex=data.steps.findIndex(s=>s.id==='leave-yard');dialogue.tick(.05);assert(dialogue.waitingHint);dialogue.tick(.05,{x:0,y:0},false,false,true);assert(!dialogue.waitingHint);dialogue.tick(.05);assert(!dialogue.waitingHint,'Dismissed wait balloon reappeared');
const nervous=new SchoolMorningModel(data);nervous.stepIndex=data.steps.findIndex(s=>s.id==='worry-walk');nervous.yuuki={x:2690,y:850};nervous.tick(.05);assert.equal(nervous.yuukiSpecial,'strap_grip');nervous.tick(.05,{x:1,y:0});assert.equal(nervous.yuukiSpecial,null,'Walking should remain under player control');
const spacing=new SchoolMorningModel(data);spacing.stepIndex=data.steps.findIndex(s=>s.id==='wings-talk');spacing.tenebrisVisible=true;spacing.yuuki={x:2690,y:850};spacing.tenebris={...spacing.yuuki};for(let i=0;i<25;i++)spacing.tick(.05);assert(Math.hypot(spacing.yuuki.x-spacing.tenebris.x,spacing.yuuki.y-spacing.tenebris.y)>=60,'Companion hides Yuuki during dialogue');
const ballCheck=new SchoolMorningModel(data);ballCheck.stepIndex=data.steps.findIndex(s=>s.id==='ball-pick');ballCheck.yuuki={x:2160,y:930};assert(ballCheck.ballVisible);assert(ballCheck.ballPosition.x>ballCheck.yuuki.x+12&&ballCheck.ballPosition.y>ballCheck.yuuki.y,'Ball is hidden under the player');ballCheck.stepIndex=data.steps.findIndex(s=>s.id==='ball-talk');ballCheck.lineIndex=2;ballCheck.tick(.05);assert(ballCheck.ballVisible&&ballCheck.ballReturnedAt>=0,'Ball disappeared instead of being returned');
for(const path of data.maps){const map=JSON.parse(fs.readFileSync(root+'/Assets/Game/Resources/'+path+'.json','utf8'));assert(!map.objects.some(p=>p.group==='gate'),'Duplicate fixed gate');}
const report={completeRoute:true,steps:visited,actionCount:actions,escortWait:true,actionRequiresF:true,tutorialFreezesSimulation:true,tutorialRequiresActualRun:true,blockedRunDoesNotUnlock:true,pause:true,gateAssistanceAtRangeEdge:true,gardenCannotBeBypassed:true,fullGateSlide:true,dialogueWhileWaiting:true,dismissibleWaitingBalloon:true,visibleBallAndReturn:true,subtleBackpackGesture:true,npcAnimations:6,sprintSeconds:m.sprintSeconds,maxFrames:4};
console.log(JSON.stringify(report,null,2));
if(process.argv[3])fs.writeFileSync(process.argv[3],JSON.stringify(report,null,2)+'\n');
