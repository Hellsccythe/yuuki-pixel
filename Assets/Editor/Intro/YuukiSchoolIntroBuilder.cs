using System;
using System.IO;
using UnityEngine;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Build.Reporting;
using YuukiIntro;

public static class YuukiSchoolIntroBuilder
{
    static void Check(bool value,string message){if(!value)throw new Exception(message);}
    static T Load<T>(string p)=>JsonUtility.FromJson<T>(Resources.Load<TextAsset>(p).text);
    public static void Validate()
    {
        var story=Load<Story>("SchoolMorning/story");
        foreach(var p in story.maps)foreach(var obj in Load<Map>(p).objects)Check(Resources.Load<Texture2D>(obj.resource),"Missing map asset: "+obj.resource);
        foreach(var path in new[]{"Childhood/YuukiV2/animations","Childhood/Tenebris/animations"})
        {
            var cat=Load<Catalog>(path);Check(Resources.Load<Texture2D>(cat.halo.resource),"Missing halo");ValidateClips(cat.clips);
        }
        ValidateClips(Load<ActionCatalog>("SchoolMorning/actions").clips);
        ValidateClips(Load<Catalog>("SchoolMorning/npcs").clips);
        var m=new SchoolMorningModel(story);int firstAttempts=0;bool waitChecked=false,tipChecked=false,exhaustChecked=false;string last="";
        for(int tick=0;tick<35000 && !m.Completed;tick++)
        {
            var step=m.Current;
            if(last!=step.id)
            {
                if(step.id=="gate-first"||step.id=="gate-again")firstAttempts++;
                if(step.id=="bread-walk")
                {
                    var previous=m.Tenebris;
                    for(int k=0;k<200;k++)m.Tick(.05f,Vector2.zero,false,false,false);
                    Check(m.Waiting,"Escort must wait for the player");var waiting=m.Tenebris;
                    m.Tick(.05f,Vector2.zero,false,false,false);Check(m.Tenebris==waiting,"Waiting escort moved");waitChecked=true;
                }
                if(step.kind=="tutorial")
                {
                    var frozen=m.Time;var yp=m.Yuuki;var tp=m.Tenebris;
                    m.Tick(.05f,Vector2.zero,true,true,true);m.Tick(.05f,Vector2.right,false,true,true);
                    Check(m.Tutorial && m.Time==frozen && m.Yuuki==yp && m.Tenebris==tp,"Tutorial unlocked without running");tipChecked=true;
                }
                if(step.id=="exhaust")exhaustChecked=true;
                last=step.id;
            }
            Vector2 delta=step.Target-m.Yuuki;Vector2 input=delta.magnitude>20?delta.normalized:Vector2.zero;
            if(step.kind=="tutorial")input=Vector2.right;
            // Continue a short loop if the endpoint is reached before three actual running seconds.
            if(step.kind=="race" && delta.magnitude<30 && m.SprintSeconds<step.seconds)input=m.Yuuki.y<820?Vector2.down:Vector2.up;
            m.Tick(.05f,input,step.kind=="tutorial"||step.kind=="race",m.ActionPrompt!=null,true);
        }
        Check(m.Completed,"Route stalled at "+m.Current.id+" ("+m.Yuuki+")");Check(firstAttempts==2 && waitChecked && tipChecked && exhaustChecked,"Missing opening beats");
        Check(m.TutorialUnlocked && m.SprintSeconds>=3 && !m.GateOpen,"Missing action/tutorial completion");
        Directory.CreateDirectory("Art/Story/SchoolMorning-v1");
        File.WriteAllText("Art/Story/SchoolMorning-v1/unity-model-qa.json","{\"completeRoute\":true,\"gateAttempts\":2,\"escortWait\":true,\"tutorialRequiresActualRun\":true,\"exhaustion\":true,\"maxFrames\":4}");
        Debug.Log("SCHOOL_INTRO_MODEL_QA_OK");
    }
    static void ValidateClips(Clip[] clips)
    {
        foreach(var clip in clips){Check(clip.frames.Length<=4 && clip.frames.Length>0,"Too many frames: "+clip.name);Check(clip.haloAnchors.Length==clip.frames.Length,"Halo alignment");foreach(var f in clip.frames)Check(Resources.Load<Texture2D>(f),"Missing frame "+f);}
    }
    public static void BuildAndExport()
    {
        Validate();Directory.CreateDirectory("Assets/Game/Scenes/Intro");
        var menu=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);new GameObject("Intro menu").AddComponent<SchoolMorningMenu>();
        var camera=new GameObject("Main Camera").AddComponent<Camera>();camera.tag="MainCamera";camera.backgroundColor=new Color(.08f,.13f,.14f);
        EditorSceneManager.SaveScene(menu,"Assets/Game/Scenes/Intro/Intro_Menu.unity");
        var game=EditorSceneManager.NewScene(NewSceneSetup.EmptyScene,NewSceneMode.Single);new GameObject("School morning").AddComponent<SchoolMorningGame>();
        camera=new GameObject("Main Camera").AddComponent<Camera>();camera.tag="MainCamera";
        EditorSceneManager.SaveScene(game,"Assets/Game/Scenes/Intro/Intro_Main.unity");
        AssetDatabase.SaveAssets();
        Directory.CreateDirectory("Builds/SchoolMorning");
        var report=BuildPipeline.BuildPlayer(new BuildPlayerOptions{scenes=new[]{"Assets/Game/Scenes/Intro/Intro_Menu.unity","Assets/Game/Scenes/Intro/Intro_Main.unity"},locationPathName="Builds/SchoolMorning/Yuuki.exe",target=BuildTarget.StandaloneWindows64,options=BuildOptions.Development});
        if(report.summary.result!=BuildResult.Succeeded)throw new Exception("Intro build failed: "+report.summary.result);
        Debug.Log("SCHOOL_INTRO_BUILD_OK "+report.summary.totalSize);
    }
}
