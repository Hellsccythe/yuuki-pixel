#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;

public static class YuukiBairroReleaseBuilder
{
    private const string MenuPath = "Assets/Game/Scenes/Bairro_Menu.unity";
    private const string Prefabs = "Assets/Game/Environment/Prefabs/";

    [MenuItem("Yuuki/Protótipo/Preparar menu e assets")]
    public static void Prepare()
    {
        PrepareInternal();
    }

    private static bool PrepareInternal()
    {
        if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return false;
        AssetDatabase.Refresh();
        var catalog = JsonUtility.FromJson<YuukiEnvironmentCatalog>(
            File.ReadAllText("Assets/Game/Resources/Environment/catalog.json"));
        ImportEnvironment(catalog);
        foreach (string id in new[] { "rua-de-casa", "moradias" })
        {
            var map = JsonUtility.FromJson<YuukiBairroData>(File.ReadAllText("Assets/Game/Bairro/Maps/" + id + ".json"));
            // Don't overwrite hand-edited map scenes when merely refreshing the menu.
            if (!File.Exists("Assets/Game/Scenes/" + map.scene + ".unity")) YuukiBairroBuilder.Build(id);
        }
        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var camera = new GameObject("Main Camera").AddComponent<Camera>();
        camera.tag = "MainCamera";
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(.065f, .083f, .077f);
        camera.gameObject.AddComponent<AudioListener>();
        var menu = new GameObject("Menu inicial").AddComponent<YuukiMenu>();
        menu.hero = AssetDatabase.LoadAllAssetsAtPath("Assets/Game/Art/Yuuki/Yuuki_Idle_2x1.png")
            .OfType<Sprite>().First(s => s.name == "idle_right_00");
        EditorSceneManager.SaveScene(scene, MenuPath);
        var paths = new[] { MenuPath, "Assets/Game/Scenes/Bairro_RuaDeCasa.unity", "Assets/Game/Scenes/Bairro_Moradias.unity" };
        EditorBuildSettings.scenes = paths.Select(p => new EditorBuildSettingsScene(p, true)).ToArray();
        AssetDatabase.SaveAssets();
        Validate(catalog);
        Debug.Log("YUUKI_RELEASE_READY: menu, 2 mapas, " + catalog.assets.Length + " assets e prefabs.");
        return true;
    }

    private static void ImportEnvironment(YuukiEnvironmentCatalog catalog)
    {
        Directory.CreateDirectory(Prefabs);
        AssetDatabase.Refresh();
        foreach (var asset in catalog.assets)
        {
            var importer = AssetImporter.GetAtPath(asset.path) as TextureImporter;
            if (importer == null) throw new InvalidOperationException(asset.path);
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = asset.ppu;
            importer.filterMode = FilterMode.Point;
            importer.textureCompression = TextureImporterCompression.Uncompressed;
            importer.mipmapEnabled = false;
            importer.alphaIsTransparency = true;
            importer.wrapMode = asset.floor ? TextureWrapMode.Repeat : TextureWrapMode.Clamp;
            importer.npotScale = TextureImporterNPOTScale.None;
            importer.maxTextureSize = 2048;
            var settings = new TextureImporterSettings();
            importer.ReadTextureSettings(settings);
            settings.spriteAlignment = (int)SpriteAlignment.Custom;
            settings.spritePivot = new Vector2(asset.pivotX, asset.pivotY);
            settings.spriteMeshType = SpriteMeshType.FullRect;
            importer.SetTextureSettings(settings);
            importer.SaveAndReimport();
            var go = new GameObject(asset.name);
            var renderer = go.AddComponent<SpriteRenderer>();
            renderer.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(asset.path);
            renderer.spriteSortPoint = SpriteSortPoint.Pivot;
            renderer.sortingOrder = asset.floor ? -1000 : asset.decal ? -10 : 0;
            if (asset.colliderWidth > 0)
            {
                var collider = go.AddComponent<BoxCollider2D>();
                collider.size = new Vector2(asset.colliderWidth, asset.colliderHeight);
                collider.offset = new Vector2(0, asset.colliderHeight/2);
            }
            PrefabUtility.SaveAsPrefabAsset(go, Prefabs + asset.id + ".prefab");
            UnityEngine.Object.DestroyImmediate(go);
        }
    }

    private static void Validate(YuukiEnvironmentCatalog catalog)
    {
        if (catalog.assets.Select(a => a.id).Distinct().Count() != catalog.assets.Length)
            throw new InvalidOperationException("IDs de assets duplicados.");
        foreach (var a in catalog.assets)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(Prefabs + a.id + ".prefab");
            if (prefab == null || prefab.GetComponent<SpriteRenderer>().sprite == null)
                throw new InvalidOperationException("Prefab incompleto: " + a.id);
            var importer = (TextureImporter)AssetImporter.GetAtPath(a.path);
            if (importer.filterMode != FilterMode.Point || importer.mipmapEnabled)
                throw new InvalidOperationException("Filtro indevido: " + a.id);
        }
        if (EditorBuildSettings.scenes[0].path != MenuPath)
            throw new InvalidOperationException("O menu deve abrir primeiro.");
    }

    [MenuItem("Yuuki/Protótipo/Exportar jogo para Windows")]
    public static void BuildAndExport()
    {
        if (!PrepareInternal()) return;
        PlayerSettings.companyName = "Yuuki Pixel";
        PlayerSettings.productName = "Yuuki - Os Subúrbios";
        PlayerSettings.defaultScreenWidth = 1280;
        PlayerSettings.defaultScreenHeight = 720;
        PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
        PlayerSettings.resizableWindow = true;
        Directory.CreateDirectory("Builds/Bairro");
        var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions {
            scenes = EditorBuildSettings.scenes.Where(s => s.enabled).Select(s => s.path).ToArray(),
            locationPathName = "Builds/Bairro/Yuuki.exe",
            target = BuildTarget.StandaloneWindows64,
            options = BuildOptions.Development
        });
        if (report.summary.result != BuildResult.Succeeded)
            throw new InvalidOperationException("Build falhou: " + report.summary.result);
        Debug.Log("YUUKI_BUILD_OK: " + report.summary.totalSize + " bytes.");
    }
}
#endif
