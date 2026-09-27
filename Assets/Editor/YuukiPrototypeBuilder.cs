#if UNITY_EDITOR
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.SceneManagement;

public static class YuukiPrototypeBuilder
{
    private const string AtlasPath = "Assets/Game/Art/Yuuki/Yuuki_Movement_6x6.png";
    private const string ControllerPath = "Assets/Game/Animation/Yuuki.controller";
    private const string ScenePath = "Assets/Game/Scenes/YuukiPrototype.unity";
    private const int GroundLayer = 8;

    [MenuItem("Yuuki/Criar cena jogavel")]
    public static void Build()
    {
        AssetDatabase.ImportAsset(AtlasPath, ImportAssetOptions.ForceUpdate);
        Texture2D texture = AssetDatabase.LoadAssetAtPath<Texture2D>(AtlasPath);
        if (texture == null)
            throw new System.InvalidOperationException("Atlas da Yuuki nao encontrado em " + AtlasPath);

        Selection.activeObject = texture;
        YuukiAtlasImporter.Import();

        RuntimeAnimatorController controller = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(ControllerPath);
        Sprite initialSprite = AssetDatabase.LoadAllAssetsAtPath("Assets/Game/Art/Yuuki/Yuuki_Idle_2x1.png")
            .OfType<Sprite>()
            .FirstOrDefault(sprite => sprite.name == "idle_right_00");
        if (controller == null || initialSprite == null)
            throw new System.InvalidOperationException("Clipes ou Animator Controller nao foram importados.");

        NameGroundLayer();
        Scene scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);

        Material groundMaterial = GetMaterial("Ground", new Color(0.29f, 0.23f, 0.35f));
        Material platformMaterial = GetMaterial("Platform", new Color(0.62f, 0.45f, 0.58f));
        Material libraryMaterial = GetMaterial("Library", new Color(0.2f, 0.14f, 0.27f));

        CreateSolid("Chao da periferia", new Vector2(0f, -3.6f), new Vector2(32f, 0.7f), groundMaterial);
        CreateSolid("Plataforma 1", new Vector2(-1f, -2.45f), new Vector2(2.5f, 0.25f), platformMaterial);
        CreateSolid("Plataforma 2", new Vector2(4.5f, -2.35f), new Vector2(2.5f, 0.25f), platformMaterial);
        CreateSolid("Plataforma 3", new Vector2(9f, -2.45f), new Vector2(2.5f, 0.25f), platformMaterial);
        CreateDecoration("Biblioteca da periferia (cenario)", new Vector2(12.3f, -2.05f), new Vector2(2.2f, 2.4f), libraryMaterial);

        GameObject player = new GameObject("Yuuki");
        player.transform.position = new Vector3(-7f, -3.2f, 0f);
        SpriteRenderer renderer = player.AddComponent<SpriteRenderer>();
        renderer.sprite = initialSprite;
        renderer.sortingOrder = 10;
        Animator animator = player.AddComponent<Animator>();
        animator.runtimeAnimatorController = controller;
        Rigidbody2D body = player.AddComponent<Rigidbody2D>();
        body.gravityScale = 3f;
        body.interpolation = RigidbodyInterpolation2D.Interpolate;
        body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
        CapsuleCollider2D collider = player.AddComponent<CapsuleCollider2D>();
        collider.size = new Vector2(0.65f, 1.1f);
        collider.offset = new Vector2(0f, 0.5f);

        GameObject groundCheck = new GameObject("GroundCheck");
        groundCheck.transform.SetParent(player.transform, false);
        groundCheck.transform.localPosition = new Vector3(0f, -0.08f, 0f);

        YuukiMovement movement = player.AddComponent<YuukiMovement>();
        SerializedObject movementFields = new SerializedObject(movement);
        movementFields.FindProperty("groundCheck").objectReferenceValue = groundCheck.transform;
        movementFields.FindProperty("groundLayers").intValue = 1 << GroundLayer;
        movementFields.ApplyModifiedPropertiesWithoutUndo();

        GameObject cameraObject = new GameObject("Main Camera");
        cameraObject.tag = "MainCamera";
        cameraObject.transform.position = new Vector3(-5f, 0f, -10f);
        Camera camera = cameraObject.AddComponent<Camera>();
        camera.orthographic = true;
        camera.orthographicSize = 4.5f;
        camera.clearFlags = CameraClearFlags.SolidColor;
        camera.backgroundColor = new Color(0.10f, 0.08f, 0.17f);
        YuukiCameraFollow follow = cameraObject.AddComponent<YuukiCameraFollow>();
        follow.SetTarget(player.transform);

        if (!EditorSceneManager.SaveScene(scene, ScenePath))
            throw new System.InvalidOperationException("Unity nao salvou a cena " + ScenePath);
        EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
        AssetDatabase.SaveAssets();
        Selection.activeGameObject = player;
        Debug.Log("Yuuki prototype ready: " + ScenePath);
    }

    public static void BuildForBatch()
    {
        Build();
    }

    public static void OpenForReview()
    {
        Scene scene = EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
        if (!scene.IsValid())
            throw new System.InvalidOperationException("A cena jogavel nao foi encontrada: " + ScenePath);
        EditorApplication.delayCall += () => EditorApplication.isPlaying = true;
    }

    private static GameObject CreateSolid(string name, Vector2 position, Vector2 size, Material material)
    {
        GameObject item = CreateDecoration(name, position, size, material);
        item.layer = GroundLayer;
        item.AddComponent<BoxCollider2D>();
        return item;
    }

    private static GameObject CreateDecoration(string name, Vector2 position, Vector2 size, Material material)
    {
        GameObject item = GameObject.CreatePrimitive(PrimitiveType.Quad);
        item.name = name;
        item.transform.position = new Vector3(position.x, position.y, 1f);
        item.transform.localScale = new Vector3(size.x, size.y, 1f);
        Collider legacyCollider = item.GetComponent<Collider>();
        if (legacyCollider != null)
            Object.DestroyImmediate(legacyCollider);
        item.GetComponent<MeshRenderer>().sharedMaterial = material;
        return item;
    }

    private static Material GetMaterial(string name, Color color)
    {
        string path = "Assets/Game/Materials/" + name + ".mat";
        Material material = AssetDatabase.LoadAssetAtPath<Material>(path);
        if (material != null)
            return material;

        Shader shader = Shader.Find("Unlit/Color");
        if (shader == null)
            shader = Shader.Find("Sprites/Default");
        if (shader == null)
            throw new System.InvalidOperationException("No unlit shader found.");
        material = new Material(shader);
        material.name = name;
        material.color = color;
        AssetDatabase.CreateAsset(material, path);
        return material;
    }

    private static void NameGroundLayer()
    {
        Object[] assets = AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset");
        if (assets.Length == 0)
            return;
        SerializedObject tags = new SerializedObject(assets[0]);
        SerializedProperty layers = tags.FindProperty("layers");
        if (layers != null && layers.arraySize > GroundLayer)
        {
            layers.GetArrayElementAtIndex(GroundLayer).stringValue = "YuukiGround";
            tags.ApplyModifiedPropertiesWithoutUndo();
        }
    }
}
#endif
