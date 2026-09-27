using System;
using System.Collections;
using System.IO;
using System.Linq;
using UnityEngine;
using UnityEngine.SceneManagement;

// Opt-in integration checks in the actual Windows player. Never runs on a normal
// launch. Screenshots and the result stay outside Assets, in the ignored Logs folder.
public sealed class YuukiPrototypeSmoke : MonoBehaviour
{
#if UNITY_EDITOR || DEVELOPMENT_BUILD
    private string output;
    private float deadline;

    [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
    private static void Boot()
    {
        if (!Environment.GetCommandLineArgs().Contains("--yuuki-smoke-test")) return;
        var go = new GameObject("Prototype integration checks");
        DontDestroyOnLoad(go);
        go.AddComponent<YuukiPrototypeSmoke>();
    }

    private void Check(bool condition, string message)
    {
        if (condition) { Debug.Log("CHECK_OK: " + message); return; }
        Debug.LogError("CHECK_FAILED: " + message);
        Application.Quit(2);
        throw new InvalidOperationException(message);
    }

    private void Update()
    {
        if (Time.realtimeSinceStartup > deadline) { Debug.LogError("SMOKE_TIMEOUT"); Application.Quit(3); }
    }

    private IEnumerator Capture(string name)
    {
        yield return new WaitForEndOfFrame();
        var camera=Camera.main;
        if (camera!=null && YuukiBairro.Instance!=null)
        {
            // Read the game's camera directly: a hidden Windows player's backbuffer
            // may be black even though its scene renders correctly. No desktop capture.
            var previous=camera.targetTexture;
            var active=RenderTexture.active;
            var target=RenderTexture.GetTemporary(1280,720,24);
            camera.targetTexture=target; camera.Render(); RenderTexture.active=target;
            var pixels=new Texture2D(1280,720,TextureFormat.RGB24,false);
            pixels.ReadPixels(new Rect(0,0,1280,720),0,0); pixels.Apply();
            File.WriteAllBytes(Path.Combine(output,name+".png"),pixels.EncodeToPNG());
            camera.targetTexture=previous; RenderTexture.active=active;
            RenderTexture.ReleaseTemporary(target); Destroy(pixels);
        }
        else ScreenCapture.CaptureScreenshot(Path.Combine(output, name + ".png"));
        yield return new WaitForSecondsRealtime(.4f);
    }

    private IEnumerator Start()
    {
        deadline = Time.realtimeSinceStartup + 120;
        Application.runInBackground = true;
        var args = Environment.GetCommandLineArgs();
        int index = Array.IndexOf(args, "--smoke-output");
        output = index >= 0 && index+1 < args.Length ? args[index+1] : Application.temporaryCachePath;
        Directory.CreateDirectory(output);
        yield return new WaitForSecondsRealtime(1);
        var menu = FindFirstObjectByType<YuukiMenu>();
        Check(menu != null && SceneManager.GetActiveScene().name == YuukiMenu.SceneName, "starts at main menu");
        var catalog = YuukiEnvironmentCatalog.Load();
        Check(menu.GalleryCount == 61, "61 environment pieces in gallery");
        foreach (var asset in catalog.assets)
            Check(Resources.Load<Texture2D>(asset.resource) != null, "texture " + asset.id);
        yield return Capture("01-menu");
        menu.ShowGallery();
        yield return Capture("02-gallery");
        menu.StartGame();
        yield return new WaitForSecondsRealtime(1.2f);
        var map = YuukiBairro.Instance;
        Check(map != null && SceneManager.GetActiveScene().name == "Bairro_RuaDeCasa", "enter Rua de Casa");
        Check(map.player.GetComponentInChildren<Animator>().runtimeAnimatorController != null, "Yuuki animator exists");
        yield return Capture("03-rua-de-casa");
        map.player.GetComponent<Rigidbody2D>().linearVelocity = Vector2.right * 4;
        map.SetPaused(true);
        Check(map.Paused && map.player.InputBlocked && Time.timeScale == 0, "pause blocks game");
        Check(map.player.GetComponent<Rigidbody2D>().linearVelocity == Vector2.zero, "pause stops momentum immediately");
        yield return Capture("04-pause");
        map.SetPaused(false);
        Check(!map.Paused && !map.player.InputBlocked && Time.timeScale == 1, "resume restores movement");
        // Exercise the real physics trigger, not just the confirmation UI method.
        var exit = FindObjectsByType<YuukiMapExit>(FindObjectsSortMode.None).First(e => e.targetMap == "Bairro_Moradias");
        map.player.Teleport(exit.transform.position);
        Physics2D.SyncTransforms();
        yield return new WaitForSecondsRealtime(.3f);
        Check(map.AwaitingTravel && map.player.InputBlocked, "edge trigger asks before travel");
        Check(SceneManager.GetActiveScene().name == "Bairro_RuaDeCasa", "no travel before consent");
        Check(!map.RequestMapChange("duplicate", "Bairro_Moradias", exit.target), "no overlapping travel requests");
        yield return Capture("05-travel-confirmation");
        map.CancelMapChange();
        Check(!map.AwaitingTravel && !map.player.InputBlocked && Time.timeScale == 1, "cancel restores current map");
        Check(SceneManager.GetActiveScene().name == "Bairro_RuaDeCasa", "cancel keeps scene");
        map.player.Teleport(new Vector2(2, 22.65f));
        yield return new WaitForSecondsRealtime(.2f);
        map.player.Teleport(exit.transform.position);
        yield return new WaitForSecondsRealtime(.3f);
        Check(map.AwaitingTravel, "exit re-arms after leaving trigger");
        Vector2 arrival = exit.target;
        map.ConfirmMapChange();
        yield return new WaitForSecondsRealtime(1.5f);
        map = YuukiBairro.Instance;
        Check(SceneManager.GetActiveScene().name == "Bairro_Moradias", "confirmed travel loads Moradias");
        Check(Vector2.Distance(map.player.transform.position, arrival) < .05f && !map.AwaitingTravel && !map.player.InputBlocked,
            "destination spawn is safe, unblocked, without a repeat prompt");
        yield return Capture("06-moradias");
        exit = FindObjectsByType<YuukiMapExit>(FindObjectsSortMode.None).First(e => e.targetMap == "Bairro_RuaDeCasa");
        map.player.Teleport(exit.transform.position);
        yield return new WaitForSecondsRealtime(.3f);
        Check(map.AwaitingTravel, "return exit asks too");
        map.ConfirmMapChange();
        yield return new WaitForSecondsRealtime(1.5f);
        map = YuukiBairro.Instance;
        Check(SceneManager.GetActiveScene().name == "Bairro_RuaDeCasa", "round trip returns home");
        Check(FindObjectsByType<YuukiPortal>(FindObjectsSortMode.None).Length==0, "no remote-room portals remain");
        // Former solid rectangles covered these visibly empty patches next to Yuuki's house.
        foreach(var spot in new[]{new Vector2(7.7f,12),new Vector2(7.7f,16),new Vector2(16,12)})
        {
            var hits=Physics2D.OverlapCapsuleAll(spot+Vector2.up*.13f,new Vector2(.5f,.26f),CapsuleDirection2D.Horizontal,0);
            Check(!hits.Any(c=>!c.isTrigger),"grass is walkable at "+spot);
        }
        var houses=FindObjectsByType<YuukiCutawayHouse>(FindObjectsSortMode.None);
        Check(houses.Length==2,"two cutaway houses");
        foreach(var house in houses)
        {
            string scene=SceneManager.GetActiveScene().name;
            map.player.Teleport(house.threshold-Vector2.up*.4f);
            Physics2D.SyncTransforms();
            var from=(Vector2)map.player.transform.position;
            Check(house.TryEnter(),"enter "+house.houseName);
            Check(!house.TryEnter(),"no duplicate door transition");
            yield return new WaitForSecondsRealtime(.14f);
            Check(house.door.enabled && house.doorHinge.localScale.x<1,"door visibly opens before interior");
            Check(map.player.InputBlocked,"door transition owns input");
            yield return new WaitForSecondsRealtime(1.2f);
            Check(house.Inside && house.interior.activeSelf && !house.exterior.enabled,"room replaces its roof");
            Check(!map.Current.outdoor && !map.player.InputBlocked && !map.TransitionBusy,"interior remains playable");
            Check(SceneManager.GetActiveScene().name==scene && Vector2.Distance(from,map.player.transform.position)<1.6f,
                "same scene and footprint during entry");
            Physics2D.SyncTransforms();
            var overlap=Physics2D.OverlapCapsuleAll((Vector2)map.player.transform.position+Vector2.up*.13f,
                new Vector2(.5f,.26f),CapsuleDirection2D.Horizontal,0);
            Check(!overlap.Any(c=>!c.isTrigger && c.gameObject!=map.player.gameObject),"door arrives on free floor");
            yield return Capture("07-"+house.name.Replace(' ','-'));
            Check(house.TryExit(),"exit "+house.houseName);
            yield return new WaitForSecondsRealtime(1.2f);
            Check(map.Current.outdoor && !house.Inside && !house.interior.activeSelf && house.exterior.enabled && house.exteriorCollider.enabled,
                "outside art and collisions restored");
            Check(!map.player.InputBlocked && !map.TransitionBusy,"exit restores movement");
        }
        var animation=map.player.GetComponent<YuukiRpgAnimation>();
        Check(animation!=null && !map.player.GetComponentInChildren<Animator>().enabled,"RPG animation owns sprites");
        var spriteCatalog=JsonUtility.FromJson<YuukiRpgAnimation.Catalog>(Resources.Load<TextAsset>("RpgRevision/yuuki").text);
        foreach(var clip in spriteCatalog.clips)
        {
            if(clip.name.StartsWith("idle_")) Check(clip.frames.Length==3,"idle has exactly three drawings: "+clip.name);
            foreach(var resource in clip.frames) Check(Resources.Load<Sprite>(resource)!=null,"sprite "+resource);
        }
        map.player.enabled=false;
        foreach(var direction in new[]{Vector2.up,Vector2.down,Vector2.left,Vector2.right})
        {
            for(int i=0;i<10;i++) animation.Tick(direction,false,.1f);
            string side=direction.y>0?"up":direction.y<0?"down":direction.x>0?"right":"left";
            Check(animation.Facing==side && animation.art.sprite.name.StartsWith("walk_"+side),"walk faces "+side);
            var first=animation.art.sprite;
            animation.Tick(direction,false,.14f);
            Check(first!=animation.art.sprite,"walk advances its feet");
            animation.Tick(Vector2.zero,false,.2f);
            Check(animation.State=="stow","stopping stows staff");
            animation.Tick(Vector2.zero,false,.7f);
            Check(animation.State=="idle" && animation.art.sprite.name.StartsWith("idle_"+side),"idle breathes facing "+side);
            animation.Tick(direction,false,.01f);
            Check(animation.State=="draw","movement draws staff back out");
        }
        animation.Tick(Vector2.right,true,1);
        Check(animation.art.sprite.name.StartsWith("run_right_"),"approved right run preserved");
        map.player.enabled=true;
        map.SetPaused(true);
        map.ReturnToMenu();
        yield return new WaitForSecondsRealtime(.8f);
        menu = FindFirstObjectByType<YuukiMenu>();
        Check(menu != null && Time.timeScale == 1, "menu resumes time after paused return");
        menu.StartGame();
        yield return new WaitForSecondsRealtime(1);
        Check(SceneManager.GetActiveScene().name == "Bairro_RuaDeCasa" && !YuukiBairro.Instance.player.InputBlocked,
            "second entry starts cleanly");
        File.WriteAllText(Path.Combine(output, "result.txt"), "PASS: menu, 61 environment assets, pause, real exit triggers, cancel, round trip, two same-footprint interiors, door animation, free doorstep, grass regressions, 44 RPG frames, four directions, stow/draw, 3-frame idle, approved right run, re-entry.\n");
        Debug.Log("YUUKI_SMOKE_OK");
        Application.Quit(0);
    }
#endif
}
