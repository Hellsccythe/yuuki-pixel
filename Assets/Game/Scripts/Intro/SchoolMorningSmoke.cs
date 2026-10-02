using System;
using System.IO;
using UnityEngine;
using UnityEngine.SceneManagement;
namespace YuukiIntro
{
    // Opt-in player integration check. Normal builds never drive or teleport Yuuki.
    public sealed class SchoolMorningSmoke : MonoBehaviour
    {
        string last="",output;int ticks;bool ending,gateCaptured;
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Boot()
        {
            var args=Environment.GetCommandLineArgs();if(Array.IndexOf(args,"--yuuki-intro-smoke")<0)return;
            var g=new GameObject("Opt-in intro smoke");DontDestroyOnLoad(g);g.AddComponent<SchoolMorningSmoke>();SceneManager.LoadScene("Intro_Main");
        }
        void Start()
        {
            var args=Environment.GetCommandLineArgs();int p=Array.IndexOf(args,"--smoke-output");output=p>=0?args[p+1]:Path.Combine(Application.dataPath,"../Logs/IntroSmoke");Directory.CreateDirectory(output);
        }
        void LateUpdate()
        {
            if(ending)return;var game=FindFirstObjectByType<SchoolMorningGame>();if(!game)return;var m=game.Model;if(m==null)return;
            try
            {
                if(m.GateOffset>=235 && !gateCaptured){gateCaptured=true;game.RefreshPresentationForCapture();Capture("gate-talk");}
                if(last!=m.Current.id && (m.Current.id!="exhaust" || m.StepTime>.6f) && (m.Current.id!="gate-talk" || m.GateOffset>=235)){last=m.Current.id;if(last=="flower"||last=="gate-talk"||last=="ball-pick"||last=="wings-talk"||last=="exhaust"||last=="arrival"){game.RefreshPresentationForCapture();Capture(last);}}
                if(m.Completed){File.WriteAllText(Path.Combine(output,"result.json"),"{\"nativePlayerRoute\":true,\"rendered\":true,\"arrival\":true}");Debug.Log("SCHOOL_INTRO_PLAYER_QA_OK");ending=true;Application.Quit(0);return;}
                // Actual model movement at fixed small steps; no position assignment.
                for(int n=0;n<5;n++)
                {
                    var s=m.Current;Vector2 delta=s.Target-m.Yuuki,input=delta.magnitude>20?delta.normalized:Vector2.zero;
                    if(s.kind=="tutorial")input=Vector2.right;
                    if(s.kind=="race" && delta.magnitude<30 && m.SprintSeconds<s.seconds)input=m.Yuuki.y<820?Vector2.down:Vector2.up;
                    m.Tick(.05f,input,s.kind=="tutorial"||s.kind=="race",m.ActionPrompt!=null,true);if(m.Completed)break;
                }
                if(++ticks>10000)throw new Exception("Native route stalled: "+m.Current.id);
            }
            catch(Exception e){Debug.LogException(e);File.WriteAllText(Path.Combine(output,"failure.txt"),e.ToString());ending=true;Application.Quit(1);}
        }
        void Capture(string name)
        {
            var camera=Camera.main;var rt=RenderTexture.GetTemporary(1280,720,24);var oldTarget=camera.targetTexture;var oldActive=RenderTexture.active;
            try{camera.targetTexture=rt;camera.Render();RenderTexture.active=rt;var im=new Texture2D(1280,720,TextureFormat.RGB24,false);im.ReadPixels(new Rect(0,0,1280,720),0,0);im.Apply();File.WriteAllBytes(Path.Combine(output,name+".png"),im.EncodeToPNG());Destroy(im);}
            finally{camera.targetTexture=oldTarget;RenderTexture.active=oldActive;RenderTexture.ReleaseTemporary(rt);}
        }
    }
}
