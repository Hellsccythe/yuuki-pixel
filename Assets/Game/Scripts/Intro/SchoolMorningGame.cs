using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

namespace YuukiIntro
{
    [Serializable] public sealed class ActionCatalog { public Clip[] clips; }
    public sealed class SchoolMorningGame : MonoBehaviour
    {
        public SchoolMorningModel Model { get; private set; }
        public const float Unit=96, BodyScale=.42f;
        readonly Dictionary<string,Sprite> sprites=new Dictionary<string,Sprite>();
        readonly Dictionary<string,Vector2> speakers=new Dictionary<string,Vector2>();
        readonly List<Tuple<Map,GameObject>> modules=new List<Tuple<Map,GameObject>>();
        Camera cam; Actor yuuki,tenebris; Catalog yc,tc,npcCatalog; ActionCatalog actions;
        SpriteRenderer gate,ball;
        readonly List<Tuple<Prop,Actor>> residents=new List<Tuple<Prop,Actor>>();
        bool clickAction,clickNext; GUIStyle text,title,bubble,label;
        Texture2D panel;
        sealed class Actor
        {
            public GameObject root; public SpriteRenderer body,halo,pack,straps;
            public string clip; public float since; public Vector2 head;
        }
        T Load<T>(string path) { var asset=Resources.Load<TextAsset>(path);if(!asset)throw new Exception("Missing story: "+path);return JsonUtility.FromJson<T>(asset.text); }
        Sprite Sprite(string path,bool body=false)
        {
            string key=path+(body?"@feet":"");if(sprites.TryGetValue(key,out var s))return s;
            var t=Resources.Load<Texture2D>(path);if(!t)throw new Exception("Missing image: "+path);
            t.filterMode=FilterMode.Point;
            s=UnityEngine.Sprite.Create(t,new Rect(0,0,t.width,t.height),body?new Vector2(.5f,.21875f):new Vector2(.5f,0),Unit,0,SpriteMeshType.FullRect);
            sprites.Add(key,s);return s;
        }
        static Vector3 World(Vector2 p)=>new Vector3(p.x/Unit,-p.y/Unit,0);
        SpriteRenderer Make(string name,string resource,Vector2 feet,float width,Transform parent=null)
        {
            var g=new GameObject(name);if(parent)g.transform.SetParent(parent);
            var r=g.AddComponent<SpriteRenderer>();r.sprite=Sprite(resource);g.transform.position=World(feet);
            g.transform.localScale=Vector3.one*(width/r.sprite.texture.width);r.sortingOrder=(int)feet.y;return r;
        }
        Actor MakeActor(string name,Catalog cat)
        {
            var a=new Actor{root=new GameObject(name)};
            a.body=new GameObject("Body").AddComponent<SpriteRenderer>();a.body.transform.SetParent(a.root.transform,false);a.body.transform.localScale=Vector3.one*BodyScale;
            a.halo=new GameObject("Separate recolorable halo").AddComponent<SpriteRenderer>();a.halo.transform.SetParent(a.root.transform,false);a.halo.sprite=Sprite(cat.halo.resource);a.halo.transform.localScale=Vector3.one*BodyScale;
            a.halo.color=new Color(.82f,.93f,1,cat.halo.alphaBaked?1:cat.halo.opacity>0?cat.halo.opacity:.75f);
            a.pack=new GameObject("School backpack").AddComponent<SpriteRenderer>();a.pack.transform.SetParent(a.root.transform,false);a.pack.sprite=Sprite("SchoolMorning/Props/backpack");a.pack.transform.localScale=Vector3.one*(24f/a.pack.sprite.texture.width);
            a.straps=new GameObject("Visible shoulder straps").AddComponent<SpriteRenderer>();a.straps.transform.SetParent(a.root.transform,false);a.straps.sprite=Sprite("SchoolMorning/Props/straps");a.straps.transform.localScale=Vector3.one*(27f/a.straps.sprite.texture.width);
            return a;
        }
        void Awake()
        {
            Time.timeScale=1;
            Model=new SchoolMorningModel(Load<Story>("SchoolMorning/story"));yc=Load<Catalog>("Childhood/YuukiV2/animations");tc=Load<Catalog>("Childhood/Tenebris/animations");npcCatalog=Load<Catalog>("SchoolMorning/npcs");actions=Load<ActionCatalog>("SchoolMorning/actions");
            cam=Camera.main;if(!cam)cam=new GameObject("Main Camera").AddComponent<Camera>();
            cam.orthographic=true;cam.clearFlags=CameraClearFlags.SolidColor;cam.orthographicSize=640f/(2*Unit);cam.backgroundColor=new Color(.31f,.39f,.27f);cam.transform.position=CameraTarget();
            foreach(var path in Model.Data.maps)
            {
                var map=Load<Map>(path);var root=new GameObject(map.name);modules.Add(Tuple.Create(map,root));
                for(float x=map.start;x<map.end;x+=256)for(float y=0;y<Model.Data.height;y+=256)
                {
                    Make("Grass","SchoolMorning/Ground/grass",new Vector2(x+128,y+256),256,root.transform).sortingOrder=-300;
                    float road=Mathf.Lerp(950,755,Mathf.InverseLerp(1500,4170,x));
                    if(y<=road && y+256>road-30)Make("Street","SchoolMorning/Ground/dirt",new Vector2(x+128,road+110),256,root.transform).sortingOrder=-200;
                }
                foreach(var p in map.objects)
                {
                    if(p.group=="gate")continue;
                    if(p.group=="residents"){var resident=MakeActor(p.id,npcCatalog);resident.root.transform.SetParent(root.transform);residents.Add(Tuple.Create(p,resident));continue;}
                    var r=Make(p.id,p.resource,new Vector2(p.x,p.y),p.w,root.transform);
                    if(p.group=="ground")r.sortingOrder=-150;
                    if(p.h>0)r.transform.localScale=new Vector3(p.w/r.sprite.texture.width,p.h/r.sprite.texture.height,1);
                }
            }
            gate=Make("Sliding rusty gate","SchoolMorning/Props/gate",new Vector2(Model.Data.gate.x,Model.Data.gate.y),235);
            ball=Make("Cloth ball","SchoolMorning/Props/ball",new Vector2(2184,954),28);
            Make("Loose stone","World/Art/stone",new Vector2(3030,820),16);
            yuuki=MakeActor("Yuuki",yc);tenebris=MakeActor("Tenebris",tc);
            Render();
        }
        Clip Find(Clip[] clips,string name){foreach(var c in clips)if(c.name==name)return c;throw new Exception("Missing clip: "+name);}
        void Animate(Actor actor,Catalog cat,Vector2 feet,Vector2 velocity,string facing,string special,bool isYuuki)
        {
            string name=special??((velocity.sqrMagnitude<1?"idle":velocity.magnitude>185?"run":"walk")+"_"+facing);
            var clip=Find(special==null?cat.clips:actions.clips,name);
            if(actor.clip!=name){actor.clip=name;actor.since=Model.Time;}
            float elapsed=Model.Time-actor.since;int count=clip.sequence.Length,index;
            if(special=="strap_grip")index=clip.sequence[(int)(elapsed*clip.fps)%count];
            else if(special=="exhaust")index=elapsed<.35f?0:clip.sequence[(int)((elapsed-.35f)*clip.fps)%count];
            else if(isYuuki && Model.BallHeld)index=3;
            else if(special!=null)
            {
                float seconds=isYuuki?Model.Current.seconds:1.5f;
                float phase=isYuuki && Model.ActionPlaying?Model.ActionTime:Model.StepTime;
                if(Model.Current.id=="close-gate")phase=(phase%.8f)/.8f;
                else phase=phase/Mathf.Max(.1f,seconds);
                index=Mathf.Clamp((int)(phase*4),0,3);
            }
            else index=clip.sequence[(int)(elapsed*clip.fps)%count];
            actor.body.sprite=Sprite(clip.frames[index],true);actor.root.transform.position=World(feet);
            int order=(int)feet.y;actor.body.sortingOrder=order;actor.halo.sortingOrder=order+1;
            Anchor anchor=clip.haloAnchors[index];
            actor.halo.transform.localPosition=new Vector3((anchor.x-256)*BodyScale/Unit,(400-anchor.y)*BodyScale/Unit,0);
            actor.head=feet+new Vector2((anchor.x-256)*BodyScale,(anchor.y-400)*BodyScale-18);
            actor.pack.enabled=facing=="up" && special==null;
            actor.pack.sortingOrder=order+1;actor.pack.transform.localPosition=new Vector3(0,30/Unit,0);
            actor.straps.enabled=special==null && facing!="up";actor.straps.sortingOrder=order+1;
            actor.straps.transform.localPosition=new Vector3(0,25/Unit,0);
            actor.straps.transform.localScale=new Vector3((facing=="down"?27:10)/actor.straps.sprite.texture.width,27/actor.straps.sprite.texture.width,1);
        }
        void AnimateResident(Prop prop,Actor a)
        {
            string name=prop.resource.Substring(prop.resource.LastIndexOf('/')+1);var clip=Find(npcCatalog.clips,name);bool dog=name=="dog";
            float phase=Model.Time+(prop.x%13)*.07f;int i=clip.sequence[(int)(phase*clip.fps)%clip.sequence.Length];
            Vector2 feet=new Vector2(prop.x+(dog?45*Mathf.Sin(Model.Time*.65f):0),prop.y);a.root.transform.position=World(feet);
            a.body.sprite=Sprite(clip.frames[i],true);a.body.sortingOrder=(int)feet.y;a.body.flipX=dog && Mathf.Cos(Model.Time*.65f)<0;
            a.pack.enabled=a.straps.enabled=false;a.halo.enabled=!dog;
            var anchor=clip.haloAnchors[i];a.halo.transform.localPosition=new Vector3((anchor.x-256)*BodyScale/Unit,(400-anchor.y)*BodyScale/Unit,0);a.halo.sortingOrder=(int)feet.y+1;
            a.head=feet+new Vector2((anchor.x-256)*BodyScale,(anchor.y-400)*BodyScale-15);speakers[prop.id]=a.head;
        }
        void Update()
        {
            if(Input.GetKeyDown(KeyCode.Escape))Model.Paused=!Model.Paused;
            var dir=new Vector2(Input.GetAxisRaw("Horizontal"),-Input.GetAxisRaw("Vertical"));
            Model.Tick(Time.unscaledDeltaTime,dir,Input.GetKey(KeyCode.LeftShift)||Input.GetKey(KeyCode.RightShift),Input.GetKeyDown(KeyCode.F)||clickAction,Input.GetKeyDown(KeyCode.Space)||Input.GetKeyDown(KeyCode.Return)||clickNext);
            clickAction=clickNext=false;Time.timeScale=Model.Paused||Model.Tutorial?0:1;
            Render();
        }
        void Render()
        {
            Animate(yuuki,yc,Model.Yuuki,Model.YuukiVelocity,Model.YuukiFacing,Model.YuukiSpecial,true);
            tenebris.root.SetActive(Model.TenebrisVisible);
            if(Model.TenebrisVisible)Animate(tenebris,tc,Model.Tenebris,Model.TenebrisVelocity,Model.TenebrisFacing,Model.TenebrisSpecial,false);
            foreach(var r in residents)AnimateResident(r.Item1,r.Item2);
            gate.transform.position=World(new Vector2(Model.Data.gate.x-Model.GateOffset,Model.Data.gate.y));
            ball.enabled=Model.BallVisible;ball.transform.position=World(Model.BallPosition);ball.transform.localScale=Vector3.one*((Model.BallOnGround?28:18)/ball.sprite.texture.width);ball.sortingOrder=Model.BallOnGround?974:1085;
            float dt=Model.Paused||Model.Tutorial?0:Time.unscaledDeltaTime;
            var desired=CameraTarget();cam.transform.position=Vector3.Lerp(cam.transform.position,desired,1-Mathf.Exp(-6*dt));
            foreach(var m in modules)m.Item2.SetActive(Model.Yuuki.x>m.Item1.start-1200 && Model.Yuuki.x<m.Item1.end+1200);
        }
        Vector3 CameraTarget()
        {
            float half=cam.orthographicSize*cam.aspect*Unit;
            return World(new Vector2(Mathf.Clamp(Model.Yuuki.x,half,Model.Data.width-half),Mathf.Clamp(Model.Yuuki.y-96,320,Model.Data.height-320)))+new Vector3(0,0,-10);
        }
        public void RefreshPresentationForCapture(){Render();cam.transform.position=CameraTarget();}
        Vector2 ScreenPoint(Vector2 p){var v=cam.WorldToScreenPoint(World(p));return new Vector2(v.x,Screen.height-v.y);}
        void Styles()
        {
            if(panel)return;panel=new Texture2D(1,1);panel.SetPixel(0,0,new Color(.07f,.12f,.12f,.93f));panel.Apply();
            text=new GUIStyle(GUI.skin.label){fontSize=18,wordWrap=true};text.normal.textColor=new Color(.96f,.94f,.86f);
            title=new GUIStyle(text){fontSize=28,fontStyle=FontStyle.Bold};label=new GUIStyle(text){fontSize=14};
            bubble=new GUIStyle(text){padding=new RectOffset(15,15,12,12),alignment=TextAnchor.MiddleLeft};
        }
        void Box(Rect rect){GUI.DrawTexture(rect,panel);}
        void Balloon(string name,string message,Vector2 pos)
        {
            var p=ScreenPoint(pos);float width=Mathf.Min(310,Screen.width-28);float height=bubble.CalcHeight(new GUIContent(name+"\n"+message),width)+4;
            var rect=new Rect(Mathf.Clamp(p.x-width/2,14,Screen.width-width-14),Mathf.Clamp(p.y-height,115,Screen.height-height-95),width,height);
            Box(rect);GUI.Label(rect,name+"\n"+message,bubble);GUI.Label(new Rect(Mathf.Clamp(p.x-10,rect.x,rect.xMax-20),rect.yMax-5,20,20),"▼",label);
        }
        void OnGUI()
        {
            if(Model==null)return;Styles();
            Box(new Rect(12,12,Mathf.Min(490,Screen.width-24),91));
            int minutes=405+(int)(Model.Time/30);
            GUI.Label(new Rect(26,18,455,30),((minutes/60)%24).ToString("00")+":"+(minutes%60).ToString("00")+"  ·  Os Subúrbios",text);
            GUI.Label(new Rect(26,50,455,46),Model.Current.title,text);
            if(Model.Speech!=null)
            {
                var l=Model.Speech;Vector2 head=l.speaker=="Yuuki"?yuuki.head:l.speaker=="Tenebris"?tenebris.head:speakers.TryGetValue(l.speaker,out var h)?h:Model.Yuuki+new Vector2(70,-120);
                Balloon(l.speaker,l.text,head);
            }
            else if(Model.WaitingHint)Balloon("Tenebris","Eu espero aqui, Yuuki.",tenebris.head);
            if(Model.TenebrisVisible && !Model.Tutorial && !Model.Paused)
            {
                var p=ScreenPoint(Model.Tenebris);if(p.x<0||p.x>Screen.width)GUI.Label(new Rect(Screen.width-310,112,294,40),(p.x<0?"←":"→")+" Tenebris está esperando",text);
            }
            Box(new Rect(0,Screen.height-47,Screen.width,47));GUI.Label(new Rect(18,Screen.height-40,Screen.width-200,34),"WASD / setas · andar    Shift · correr    F · ação    Espaço · fala    Esc · pausa",label);
            if(Model.ActionPrompt!=null && GUI.Button(new Rect(Screen.width/2-160,Screen.height-101,320,45),"F · "+Model.ActionPrompt))clickAction=true;
            if((Model.Speech!=null || Model.WaitingHint) && GUI.Button(new Rect(Screen.width-170,Screen.height-41,154,31),"Espaço · próxima"))clickNext=true;
            if(Model.BallOnGround){var p=ScreenPoint(new Vector2(2184,954));GUI.Label(new Rect(p.x-50,p.y+6,110,25),"Bola de pano",label);}
            if(Model.Completed){Box(new Rect(Screen.width/2-230,115,460,77));GUI.Label(new Rect(Screen.width/2-216,127,430,55),"Vocês chegaram à escola.\nFim desta primeira parte do prólogo.",text);}
            if(Model.Paused || Model.Tutorial)
            {
                GUI.color=new Color(1,1,1,.84f);GUI.DrawTexture(new Rect(0,0,Screen.width,Screen.height),panel);GUI.color=Color.white;
                float x=Screen.width/2-255,y=Screen.height/2-120;Box(new Rect(x,y,510,240));
                GUI.Label(new Rect(x+25,y+20,460,45),Model.Tutorial?"Corra atrás do Tenebris":"Pausa",title);
                GUI.Label(new Rect(x+25,y+76,460,85),Model.Tutorial?"Segure Shift + uma direção (WASD ou setas).\nO mundo continua quando Yuuki começar a correr.":"F é o botão de ação: portão, flor, bola e objetos próximos.",text);
                if(!Model.Tutorial){if(GUI.Button(new Rect(x+25,y+175,210,40),"Continuar"))Model.Paused=false;if(GUI.Button(new Rect(x+250,y+175,235,40),"Menu inicial")){Time.timeScale=1;SceneManager.LoadScene("Intro_Menu");}}
            }
        }
        void OnDestroy(){Time.timeScale=1;foreach(var s in sprites.Values)Destroy(s);if(panel)Destroy(panel);}
    }
}
