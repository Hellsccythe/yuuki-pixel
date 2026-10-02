export const length=(v)=>Math.hypot(v.x,v.y);
const sub=(a,b)=>({x:a.x-b.x,y:a.y-b.y}), dist=(a,b)=>length(sub(a,b));
const facing=(v,old)=>length(v)<.1?old:Math.abs(v.y)>Math.abs(v.x)?v.y<0?'up':'down':v.x<0?'left':'right';
export class SchoolMorningModel {
  constructor(data){this.data=data;this.yuuki={...data.start};this.tenebris={...data.companionStart};this.yv={x:0,y:0};this.tv={x:0,y:0};this.stepIndex=0;this.lineIndex=0;this.time=0;this.stepTime=0;this.lineTime=0;this.actionTime=-1;this.sprintSeconds=0;this.runDistance=0;this.gateOpen=false;this.tenebrisVisible=false;this.waiting=false;this.paused=false;this.tutorialUnlocked=false;this.yf='down';this.tf='left';}
  get current(){return this.data.steps[this.stepIndex];}
  get tutorial(){return this.current.kind==='tutorial';}
  get completed(){return this.current.kind==='finish';}
  get actionPlaying(){return this.current.kind==='action'&&this.actionTime>=0;}
  get speech(){return this.current.lines[this.lineIndex]??null;}
  get ballHeld(){return this.current.id==='ball-talk'&&this.lineIndex<2;}
  get ballOnGround(){return ['ball-walk','ball-pick'].includes(this.current.id);}
  get ballVisible(){return this.ballOnGround||this.ballHeld||this.ballReturnedAt!==undefined;}
  get ballPosition(){
    if(this.ballOnGround)return {x:2184,y:954};if(this.ballHeld)return {x:this.yuuki.x+13,y:this.yuuki.y-50};
    const elapsed=this.time-(this.ballReturnedAt??this.time);
    if(elapsed<1){const t=elapsed;return {x:this.ballThrowFrom.x+(2230-this.ballThrowFrom.x)*t,y:this.ballThrowFrom.y+(940-this.ballThrowFrom.y)*t-60*Math.sin(t*Math.PI)};}
    const phase=((elapsed-1)%4)/2,t=phase<=1?phase:2-phase;return {x:2230+130*t,y:940+70*t-55*Math.sin(t*Math.PI)};
  }
  get waitingHint(){return this.waiting&&!this.waitingDismissed&&(this.waitingTime||0)<3.5;}
  get yuukiSpecial(){return this.actionPlaying&&!this.actionApproaching?this.current.action:this.current.id==='gate-help'?'grasp':this.current.action==='exhaust'?'exhaust':this.ballHeld?'pickup':['worry-walk','wings-talk'].includes(this.current.id)&&length(this.yv)<1?'strap_grip':null;}
  get tenebrisSpecial(){return this.current.action==='tenebris_grasp'?'tenebris_grasp':null;}
  get actionPrompt(){return this.current.kind==='action'&&!this.actionPlaying&&this.yuuki.y>=(this.current.minY||0)&&dist(this.yuuki,this.current)<=this.current.range?this.current.prompt:null;}
  passable(p){const inside=(b)=>p.x>b.x-12&&p.x<b.x+b.w+12&&p.y>b.y-10&&p.y<b.y+b.h+10;return p.x>=35&&p.x<=this.data.width-35&&p.y>=80&&p.y<=this.data.height-35&&!this.data.blockers.some(inside)&&((this.gateOffset||0)>=235||!inside(this.data.gate.collider));}
  move(p,delta){let q={x:p.x+delta.x,y:p.y};if(this.passable(q))p=q;q={x:p.x,y:p.y+delta.y};return this.passable(q)?q:p;}
  next(){if(this.completed)return;if(this.current.id==='close-gate')this.gateOpen=false;this.stepIndex++;this.stepTime=this.lineTime=0;this.lineIndex=0;this.actionTime=-1;this.actionApproaching=false;this.waiting=false;this.waitingTime=0;this.waitingDismissed=false;if(this.current.id==='gate-help')this.tenebrisVisible=true;if(this.current.id==='gate-talk')this.gateOpen=true;}
  tick(dt,input={x:0,y:0},run=false,action=false,nextLine=false){
    dt=Math.min(.05,Math.max(0,dt));let norm=Math.max(1,length(input));input={x:input.x/norm,y:input.y/norm};this.yv={x:0,y:0};this.tv={x:0,y:0};if(this.paused)return;
    if(this.tutorial){if(!run||length(input)<.1||dist(this.move(this.yuuki,{x:input.x*230*dt,y:input.y*230*dt}),this.yuuki)<.01)return;this.tutorialUnlocked=true;this.next();}
    this.time+=dt;this.stepTime+=dt;
    const target=this.gateOpen?235:0,offset=this.gateOffset||0;this.gateOffset=offset+Math.sign(target-offset)*Math.min(Math.abs(target-offset),180*dt);
    if(!this.actionPlaying&&this.current.kind!=='script'){
      let before=this.yuuki,speed=run?230:this.current.id==='school-walk'?115:138;
      this.yuuki=this.move(before,{x:input.x*speed*dt,y:input.y*speed*dt});this.yv={x:(this.yuuki.x-before.x)/(dt||1),y:(this.yuuki.y-before.y)/(dt||1)};this.yf=facing(this.yv,this.yf);
      if(this.current.kind==='race'&&run&&length(this.yv)>1){this.sprintSeconds+=dt;this.runDistance+=dist(before,this.yuuki);}
    }
    const wasWaiting=this.waiting;this.waiting=this.tenebrisVisible&&dist(this.yuuki,this.tenebris)>(this.waiting?115:190);
    if(this.waiting){if(!wasWaiting){this.waitingTime=0;this.waitingDismissed=false;}this.waitingTime=(this.waitingTime||0)+dt;if(nextLine&&!this.speech)this.waitingDismissed=true;}else{this.waitingTime=0;this.waitingDismissed=false;}
    if(this.tenebrisVisible){
      let target=this.tenebris;if(this.current.id==='gate-help')target={x:this.yuuki.x+55,y:this.yuuki.y+60};else if(this.current.id==='exhaust')target={x:this.yuuki.x+52,y:this.yuuki.y+8};else if(['talk','finish'].includes(this.current.kind)&&dist(this.yuuki,this.tenebris)<65)target={x:this.yuuki.x+65,y:this.yuuki.y-12};else if(['move','race'].includes(this.current.kind)&&!this.waiting)target={x:this.current.x+52,y:this.current.y-12};
      let v=sub(target,this.tenebris),d=length(v),speed=this.current.id==='exhaust'?160:this.current.speed,travel=Math.min(d,speed*dt),before=this.tenebris;
      this.tenebris={x:before.x+v.x/(d||1)*travel,y:before.y+v.y/(d||1)*travel};this.tv={x:(this.tenebris.x-before.x)/(dt||1),y:(this.tenebris.y-before.y)/(dt||1)};this.tf=facing(this.tv,this.tf);
    }
    if(!this.waiting)this.lineTime+=dt;
    if(this.speech&&((nextLine&&this.time-(this.lastLineAdvance??-10)>.2)||this.lineTime>Math.max(2.1,this.speech.text.length*.046))){this.lineIndex++;this.lineTime=0;this.lastLineAdvance=this.time;}
    if(this.current.id==='ball-talk'&&this.lineIndex>=2&&this.ballReturnedAt===undefined){this.ballReturnedAt=this.time;this.ballThrowFrom={x:this.yuuki.x+13,y:this.yuuki.y-50};}
    if(this.current.kind==='action'){
      if(action&&this.actionPrompt){this.actionTime=0;this.actionApproaching=dist(this.yuuki,this.current)>6;}
      if(this.actionPlaying){
        if(this.actionApproaching){let before=this.yuuki,v=sub(this.current,before),d=length(v),travel=Math.min(d,138*dt);this.yuuki=this.move(before,{x:v.x/(d||1)*travel,y:v.y/(d||1)*travel});this.yv={x:(this.yuuki.x-before.x)/(dt||1),y:(this.yuuki.y-before.y)/(dt||1)};this.yf=facing(this.yv,this.yf);if(dist(this.yuuki,this.current)<=6)this.actionApproaching=false;}
        else{this.yf=['grasp','kick'].includes(this.current.action)?'right':'down';this.actionTime+=dt;if(this.actionTime>=this.current.seconds)this.next();}
      }
    }else if(this.current.kind==='script'){if(!this.speech&&this.stepTime>=this.current.seconds)this.next();}
    else if(this.current.kind==='talk'){if(!this.speech)this.next();}
    else if(['move','race'].includes(this.current.kind)){
      if(dist(this.yuuki,this.current)<this.current.range&&dist(this.tenebris,this.current)<this.current.range+52&&!this.speech&&(this.current.kind!=='race'||this.sprintSeconds>=this.current.seconds))this.next();
    }
  }
}
