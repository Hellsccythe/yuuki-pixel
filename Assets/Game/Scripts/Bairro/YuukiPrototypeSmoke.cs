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
        ScreenCapture.CaptureScreenshot(Path.Combine(output, name + ".png"));
        yield return new WaitForSecondsRealtime(.4f);
    }

    private IEnumerator Start()
    {
        deadline = Time.realtimeSinceStartup + 75;
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
        var portal = FindObjectsByType<YuukiPortal>(FindObjectsSortMode.None)
            .First(p => map.GetArea(p.areaId) != null && !map.GetArea(p.areaId).outdoor);
        map.player.Teleport(portal.transform.position);
        yield return new WaitForSecondsRealtime(1.2f);
        Check(!map.Current.outdoor && !map.player.InputBlocked, "house entrance still works");
        yield return Capture("07-house");
        portal = FindObjectsByType<YuukiPortal>(FindObjectsSortMode.None)
            .First(p => map.Current.bounds.Contains(p.transform.position) && map.GetArea(p.areaId).outdoor);
        map.player.Teleport(portal.transform.position);
        yield return new WaitForSecondsRealtime(1.2f);
        Check(map.Current.outdoor, "house exit still works");
        map.SetPaused(true);
        map.ReturnToMenu();
        yield return new WaitForSecondsRealtime(.8f);
        menu = FindFirstObjectByType<YuukiMenu>();
        Check(menu != null && Time.timeScale == 1, "menu resumes time after paused return");
        menu.StartGame();
        yield return new WaitForSecondsRealtime(1);
        Check(SceneManager.GetActiveScene().name == "Bairro_RuaDeCasa" && !YuukiBairro.Instance.player.InputBlocked,
            "second entry starts cleanly");
        File.WriteAllText(Path.Combine(output, "result.txt"), "PASS: menu, 61 assets, pause, real exit triggers, cancel, round trip, interior, re-entry.\n");
        Debug.Log("YUUKI_SMOKE_OK");
        Application.Quit(0);
    }
#endif
}
