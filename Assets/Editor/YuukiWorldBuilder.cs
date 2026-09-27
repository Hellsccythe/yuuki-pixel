#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEditor.Build.Reporting;
using UnityEngine;

public static class YuukiWorldBuilder
{
    private const string Root = "Assets/Game/Resources/World";
    private const string ScenePath = "Assets/Game/Scenes/AngelSuburbs.unity";
    private static YuukiWorldData world;

    public static void BuildAndExportForBatch()
    {
        Build();
        string output = Environment.GetEnvironmentVariable("YUUKI_PLAYER_OUTPUT");
        if (string.IsNullOrEmpty(output)) output = Path.GetFullPath("Builds/Neighborhood/Yuuki.exe");
        Directory.CreateDirectory(Path.GetDirectoryName(output));
        PlayerSettings.productName = "Yuuki - Cidade dos Anjos";
        PlayerSettings.companyName = "Yuuki Pixel";
        PlayerSettings.defaultScreenWidth = 1280;
        PlayerSettings.defaultScreenHeight = 800;
        PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
        {
            scenes = new[] { ScenePath },
            locationPathName = output,
            target = BuildTarget.StandaloneWindows64,
            options = BuildOptions.None
        });
        if (report.summary.result != BuildResult.Succeeded)
            throw new InvalidOperationException("World player build failed: " + report.summary.result);
        Debug.Log("YUUKI_PLAYER_OK: " + output);
    }

    [MenuItem("Yuuki/Mundo/Construir suburbios (vista de cima)")]
    public static void Build()
    {
        // Preserve any user edits in an open scene before a manual rebuild.
        if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        Directory.CreateDirectory(Root + "/Modules");
        Directory.CreateDirectory(Root + "/Areas");
        AssetDatabase.Refresh();
        foreach (string path in Directory.GetFiles(Root, "*.png", SearchOption.AllDirectories))
            ImportTexture(path.Replace('\\', '/'));
        world = JsonUtility.FromJson<YuukiWorldData>(File.ReadAllText(Root + "/angel-suburbs.json"));
        foreach (var module in world.modules)
        {
            var root = new GameObject(module.id);
            foreach (var item in module.objects) AddObject(root.transform, item);
            foreach (var point in module.points) AddPoint(root.transform, point);
            PrefabUtility.SaveAsPrefabAsset(root, Root + "/Modules/" + module.id + ".prefab");
            UnityEngine.Object.DestroyImmediate(root);
        }
        foreach (var map in world.maps) BuildArea(map);
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var player = new GameObject("Yuuki");
        player.transform.localScale = Vector3.one * .64f;
        var sprite = player.AddComponent<SpriteRenderer>();
        sprite.sprite = AssetDatabase.LoadAllAssetsAtPath("Assets/Game/Art/Yuuki/Yuuki_Idle_2x1.png").OfType<Sprite>().First(s => s.name == "idle_right_00");
        var animator = player.AddComponent<Animator>();
        animator.runtimeAnimatorController = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>("Assets/Game/Animation/Yuuki.controller");
        var body = player.AddComponent<Rigidbody2D>();
        body.gravityScale = 0;
        body.freezeRotation = true;
        body.interpolation = RigidbodyInterpolation2D.Interpolate;
        body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
        var feet = player.AddComponent<CircleCollider2D>();
        feet.radius = .1875f;
        var movement = player.AddComponent<YuukiTopDownMovement>();
        player.AddComponent<YuukiDepthSort>();
        var cameraObject = new GameObject("Main Camera");
        cameraObject.tag = "MainCamera";
        var camera = cameraObject.AddComponent<Camera>();
        camera.orthographic = true;
        camera.orthographicSize = 3.2f;
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(.11f,.14f,.10f);
        var cameraFollow = cameraObject.AddComponent<YuukiWorldCamera>();
        cameraFollow.target = player.transform;
        var controller = new GameObject("World").AddComponent<YuukiWorldController>();
        controller.player = movement;
        controller.worldCamera = cameraFollow;
        // Editor preview of the exterior; runtime replaces it with the same prefab.
        var preview = (GameObject)PrefabUtility.InstantiatePrefab(AssetDatabase.LoadAssetAtPath<GameObject>(Root + "/Areas/" + world.startMap + ".prefab"));
        preview.name = "World preview (editor only)";
        preview.AddComponent<YuukiEditorWorldPreview>();
        var start = world.maps.First(m => m.id == world.startMap);
        player.transform.position = Position(start.spawnX,start.spawnY);
        cameraFollow.SetBounds(start.width/100f,start.height/100f);
        if (!EditorSceneManager.SaveScene(scene, ScenePath)) throw new InvalidOperationException("Cannot save world scene");
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
        AssetDatabase.SaveAssets();
        Debug.Log("YUUKI_WORLD_OK: " + world.modules.Length + " modular prefabs, " + world.maps.Length + " maps, 20 art assets, scene " + ScenePath);
    }

    private static void ImportTexture(string path)
    {
        AssetDatabase.ImportAsset(path,ImportAssetOptions.ForceUpdate);
        var importer = (TextureImporter)AssetImporter.GetAtPath(path);
        importer.textureType = TextureImporterType.Sprite;
        importer.spriteImportMode = SpriteImportMode.Single;
        importer.spritePixelsPerUnit = 100;
        importer.filterMode = FilterMode.Point;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.mipmapEnabled = false;
        importer.npotScale = TextureImporterNPOTScale.None;
        importer.maxTextureSize = 4096;
        importer.alphaIsTransparency = true;
        var settings = new TextureImporterSettings();
        importer.ReadTextureSettings(settings);
        settings.spriteAlignment = (int)SpriteAlignment.Custom;
        settings.spritePivot = path.Contains("/Floors/") ? new Vector2(0,1) : new Vector2(.5f,0);
        settings.spriteMeshType = SpriteMeshType.FullRect;
        importer.SetTextureSettings(settings);
        importer.SaveAndReimport();
    }

    private static Vector3 Position(float x,float y) { return new Vector3(x/100f,-y/100f,0); }
    private static void AddObject(Transform parent, YuukiWorldObject item)
    {
        var root = new GameObject(item.asset);
        root.transform.SetParent(parent,false);
        root.transform.localPosition = Position(item.x,item.y);
        var visual = new GameObject("Art");
        visual.transform.SetParent(root.transform,false);
        var renderer = visual.AddComponent<SpriteRenderer>();
        renderer.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(Root + "/Art/" + item.asset + ".png");
        if (renderer.sprite == null) throw new InvalidOperationException("Missing art " + item.asset);
        visual.transform.localScale = new Vector3(item.width/renderer.sprite.rect.width,item.height/renderer.sprite.rect.height,1);
        root.AddComponent<YuukiDepthSort>();
        if (item.solid)
        {
            root.layer = 8;
            var collider = root.AddComponent<BoxCollider2D>();
            collider.size = new Vector2(item.footprint[2],item.footprint[3])/100f;
            collider.offset = new Vector2(item.footprint[0]+item.footprint[2]/2,-item.footprint[1]-item.footprint[3]/2)/100f;
        }
    }

    private static void AddPoint(Transform parent,YuukiWorldPoint point)
    {
        var item = new GameObject(point.id);
        item.transform.SetParent(parent,false);
        item.transform.localPosition = Position(point.x,point.y);
        item.AddComponent<YuukiWorldInteractable>().point = point;
    }

    private static void BuildArea(YuukiMapData map)
    {
        var root = new GameObject(map.id);
        var floor = new GameObject("Ground");
        floor.transform.SetParent(root.transform,false);
        var renderer = floor.AddComponent<SpriteRenderer>();
        renderer.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(Root + "/Floors/" + map.id + ".png");
        renderer.sortingOrder = -32000;
        foreach (var instance in map.instances)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(Root + "/Modules/" + instance.module + ".prefab");
            var child = (GameObject)PrefabUtility.InstantiatePrefab(prefab);
            child.transform.SetParent(root.transform,false);
            child.transform.localPosition = Position(instance.x,instance.y);
        }
        foreach (var item in map.objects) AddObject(root.transform,item);
        foreach (var point in map.points) AddPoint(root.transform,point);
        float side = map.id == "suburbs" ? 20 : 45;
        AddBoundary(root.transform,0,0,map.width,map.id == "suburbs" ? 20 : 55);
        AddBoundary(root.transform,0,0,side,map.height);
        AddBoundary(root.transform,map.width-side,0,side,map.height);
        AddBoundary(root.transform,0,map.height-35,map.width,35);
        PrefabUtility.SaveAsPrefabAsset(root,Root + "/Areas/" + map.id + ".prefab");
        UnityEngine.Object.DestroyImmediate(root);
    }
    private static void AddBoundary(Transform parent,float x,float y,float w,float h)
    {
        var item = new GameObject("Boundary");
        item.transform.SetParent(parent,false);
        item.transform.localPosition = Position(x+w/2,y+h/2);
        item.layer = 8;
        item.AddComponent<BoxCollider2D>().size = new Vector2(w,h)/100f;
    }
}
#endif
