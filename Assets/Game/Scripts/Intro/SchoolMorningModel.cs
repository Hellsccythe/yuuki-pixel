using System;
using UnityEngine;

namespace YuukiIntro
{
    [Serializable] public sealed class Point { public float x,y; public Vector2 Vector => new Vector2(x,y); }
    [Serializable] public sealed class Block { public float x,y,w,h; public string id; }
    [Serializable] public sealed class Line { public string speaker,text; }
    [Serializable] public sealed class Step { public string id,kind,title,action,prompt; public float x,y,range,speed,seconds,minY; public bool guide; public Line[] lines; public Vector2 Target => new Vector2(x,y); }
    [Serializable] public sealed class Prop { public string id,resource,group; public float x,y,w,h; }
    [Serializable] public sealed class Map { public string id,name; public float start,end; public Prop[] objects; }
    [Serializable] public sealed class Gate { public float x,y; public Block collider; }
    [Serializable] public sealed class Story { public string title,chapter,startHour; public int storyAge; public float width,height; public Point start,companionStart; public Gate gate; public string[] maps; public Block[] blockers; public Step[] steps; }
    [Serializable] public sealed class Anchor { public float x,y; }
    [Serializable] public sealed class Clip { public string name; public string[] frames; public Anchor[] haloAnchors; public float fps; public int[] sequence; public bool loop; }
    [Serializable] public sealed class Halo { public string resource; public float opacity; public bool alphaBaked; }
    [Serializable] public sealed class Catalog { public Clip[] clips; public Halo halo; }

    // Pure progression/movement model used by the player and opt-in integration checks.
    // Inputs are intentions; only a successful displacement unlocks the running tutorial.
    public sealed class SchoolMorningModel
    {
        public readonly Story Data;
        public Vector2 Yuuki,Tenebris,YuukiVelocity,TenebrisVelocity;
        public int StepIndex,LineIndex;
        public float Time,StepTime,LineTime,ActionTime=-1,SprintSeconds,RunDistance;
        public bool GateOpen,TenebrisVisible,Waiting,Paused,TutorialUnlocked;
        public bool ActionApproaching;
        public float GateOffset,WaitingTime;
        public bool WaitingDismissed;
        public float BallReturnedAt=-1;
        public Vector2 BallThrowFrom;
        public float LastLineAdvance=-10;
        public string YuukiFacing="down",TenebrisFacing="left";
        public Step Current => Data.steps[StepIndex];
        public bool Tutorial => Current.kind=="tutorial";
        public bool Completed => Current.kind=="finish";
        public bool ActionPlaying => Current.kind=="action" && ActionTime>=0;
        public Line Speech => LineIndex<Current.lines.Length?Current.lines[LineIndex]:null;
        public bool BallHeld => Current.id=="ball-talk" && LineIndex<2;
        public bool BallOnGround => Current.id=="ball-walk" || Current.id=="ball-pick";
        public bool BallVisible => BallOnGround || BallHeld || BallReturnedAt>=0;
        public Vector2 BallPosition
        {
            get
            {
                if(BallOnGround)return new Vector2(2184,954);if(BallHeld)return Yuuki+new Vector2(13,-50);
                float elapsed=Time-(BallReturnedAt<0?Time:BallReturnedAt);
                if(elapsed<1)return Vector2.Lerp(BallThrowFrom,new Vector2(2230,940),elapsed)+new Vector2(0,-60*Mathf.Sin(elapsed*Mathf.PI));
                float phase=((elapsed-1)%4)/2,t=phase<=1?phase:2-phase;return new Vector2(2230+130*t,940+70*t-55*Mathf.Sin(t*Mathf.PI));
            }
        }
        public bool WaitingHint => Waiting && !WaitingDismissed && WaitingTime<3.5f;
        public string YuukiSpecial => ActionPlaying && !ActionApproaching?Current.action:Current.id=="gate-help"?"grasp":Current.action=="exhaust"?"exhaust":BallHeld?"pickup":(Current.id=="worry-walk" || Current.id=="wings-talk") && YuukiVelocity.sqrMagnitude<1?"strap_grip":null;
        public string TenebrisSpecial => Current.action=="tenebris_grasp"?"tenebris_grasp":null;
        public string ActionPrompt => Current.kind=="action" && !ActionPlaying && Yuuki.y>=Current.minY && Vector2.Distance(Yuuki,Current.Target)<=Current.range?Current.prompt:null;
        public SchoolMorningModel(Story data) { Data=data;Yuuki=data.start.Vector;Tenebris=data.companionStart.Vector; }
        public bool Passable(Vector2 p)
        {
            if(p.x<35 || p.y<80 || p.x>Data.width-35 || p.y>Data.height-35)return false;
            foreach(var b in Data.blockers)if(Inside(p,b))return false;
            return GateOffset>=235 || !Inside(p,Data.gate.collider);
        }
        private static bool Inside(Vector2 p,Block b) => p.x>b.x-12 && p.x<b.x+b.w+12 && p.y>b.y-10 && p.y<b.y+b.h+10;
        private Vector2 Move(Vector2 p,Vector2 delta)
        {
            var next=p+new Vector2(delta.x,0);if(Passable(next))p=next;
            next=p+new Vector2(0,delta.y);if(Passable(next))p=next;
            return p;
        }
        private static string Facing(Vector2 v,string old) => v.sqrMagnitude<.01f?old:Mathf.Abs(v.y)>Mathf.Abs(v.x)?v.y<0?"up":"down":v.x<0?"left":"right";
        private void Next()
        {
            if(Completed)return;
            if(Current.id=="close-gate")GateOpen=false;
            StepIndex++;StepTime=LineTime=WaitingTime=0;LineIndex=0;ActionTime=-1;ActionApproaching=false;Waiting=false;WaitingDismissed=false;
            if(Current.id=="gate-help")TenebrisVisible=true;
            if(Current.id=="gate-talk")GateOpen=true;
        }
        public void Tick(float dt,Vector2 input,bool run,bool action,bool nextLine)
        {
            dt=Mathf.Clamp(dt,0,.05f);input=Vector2.ClampMagnitude(input,1);YuukiVelocity=TenebrisVelocity=Vector2.zero;
            if(Paused)return;
            if(Tutorial)
            {
                // Shift on its own, F, and confirming the tip never unfreeze the world.
                if(!run || input.sqrMagnitude<.01f || Vector2.Distance(Move(Yuuki,input*230*dt),Yuuki)<.01f)return;
                TutorialUnlocked=true;Next();
            }
            Time+=dt;StepTime+=dt;
            GateOffset=Mathf.MoveTowards(GateOffset,GateOpen?235:0,180*dt);
            bool locked=ActionPlaying || Current.kind=="script";
            if(!locked)
            {
                var before=Yuuki;float speed=run?230:Current.id=="school-walk"?115:138;
                Yuuki=Move(Yuuki,input*speed*dt);YuukiVelocity=dt>0?(Yuuki-before)/dt:Vector2.zero;
                YuukiFacing=Facing(YuukiVelocity,YuukiFacing);
                if(Current.kind=="race" && run && YuukiVelocity.sqrMagnitude>1){SprintSeconds+=dt;RunDistance+=Vector2.Distance(before,Yuuki);}
            }
            float distance=Vector2.Distance(Yuuki,Tenebris);
            bool wasWaiting=Waiting;Waiting=TenebrisVisible && (Waiting?distance>115:distance>190);
            if(Waiting){if(!wasWaiting){WaitingTime=0;WaitingDismissed=false;}WaitingTime+=dt;if(nextLine && Speech==null)WaitingDismissed=true;}
            else{WaitingTime=0;WaitingDismissed=false;}
            if(TenebrisVisible)
            {
                Vector2 target=Tenebris;
                if(Current.id=="gate-help")target=Yuuki+new Vector2(55,60);
                else if(Current.id=="exhaust")target=Yuuki+new Vector2(52,8);
                else if((Current.kind=="talk" || Current.kind=="finish") && distance<65)target=Yuuki+new Vector2(65,-12);
                else if((Current.kind=="move" || Current.kind=="race") && !Waiting)target=Current.Target+new Vector2(52,-12);
                var before=Tenebris;float speed=Current.id=="exhaust"?160:Current.speed;
                Tenebris=Vector2.MoveTowards(Tenebris,target,speed*dt);TenebrisVelocity=dt>0?(Tenebris-before)/dt:Vector2.zero;
                TenebrisFacing=Facing(TenebrisVelocity,TenebrisFacing);
            }
            // Dialogue stays above its speaker, and waits while the player is far behind.
            if(!Waiting)LineTime+=dt;
            if(Speech!=null && ((nextLine && Time-LastLineAdvance>.2f) || LineTime>Mathf.Max(2.1f,Speech.text.Length*.046f))) {LineIndex++;LineTime=0;LastLineAdvance=Time;}
            if(Current.id=="ball-talk" && LineIndex>=2 && BallReturnedAt<0){BallReturnedAt=Time;BallThrowFrom=Yuuki+new Vector2(13,-50);}
            if(Current.kind=="action")
            {
                if(action && ActionPrompt!=null){ActionTime=0;ActionApproaching=Vector2.Distance(Yuuki,Current.Target)>6;}
                if(ActionPlaying)
                {
                    if(ActionApproaching)
                    {
                        var before=Yuuki;var delta=Current.Target-Yuuki;Yuuki=Move(Yuuki,Vector2.ClampMagnitude(delta,138*dt));
                        YuukiVelocity=dt>0?(Yuuki-before)/dt:Vector2.zero;YuukiFacing=Facing(YuukiVelocity,YuukiFacing);
                        if(Vector2.Distance(Yuuki,Current.Target)<=6)ActionApproaching=false;
                    }
                    else {YuukiFacing=Current.action=="grasp" || Current.action=="kick"?"right":"down";ActionTime+=dt;if(ActionTime>=Current.seconds)Next();}
                }
            }
            else if(Current.kind=="script") {if(Speech==null && StepTime>=Current.seconds)Next();}
            else if(Current.kind=="talk") {if(Speech==null)Next();}
            else if(Current.kind=="move" || Current.kind=="race")
            {
                bool arrived=Vector2.Distance(Yuuki,Current.Target)<Current.range && Vector2.Distance(Tenebris,Current.Target)<Current.range+52;
                if(arrived && Speech==null && (Current.kind!="race" || SprintSeconds>=Current.seconds))Next();
            }
        }
    }
}
