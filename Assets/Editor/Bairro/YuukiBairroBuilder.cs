#if UNITY_EDITOR
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

// Builds the playable scene of each modular neighbourhood map from the JSON layout written by
// scripts/bairro/build_bairro.py. Rebuilding replaces the scene, so tweak the layout
// in the Python script (or edit the scene afterwards and stop rebuilding it).
public static class YuukiBairroBuilder
{
    private const string MapsFolder = "Assets/Game/Bairro/Maps/";
    private const string ScenesFolder = "Assets/Game/Scenes/";
    // Order of the modular maps in the Build Settings (the first one opens a build).
    private static readonly string[] MapOrder = { "rua-de-casa", "moradias", "dungeon" };
    private const string LightingFolder = "Assets/Game/Bairro/Lighting/";
    private const string PhysicsPath = "Assets/Game/Bairro/Physics/SemAtrito.physicsMaterial2D";
    private const string YuukiIdle = "Assets/Game/Art/Yuuki/Yuuki_Idle_2x1.png";
    private const string YuukiController = "Assets/Game/Animation/Yuuki.controller";
    private const float YuukiScale = 1.15f;

    [MenuItem("Yuuki/Bairro/Construir todo o bairro")]
    public static void BuildAll()
    {
        if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        // Build in reverse so the first map (Rua de Casa) is the scene left open.
        foreach (var id in MapOrder.Reverse()) Build(id);
    }

    [MenuItem("Yuuki/Bairro/Construir Rua de Casa")]
    public static void BuildRuaDeCasa()
    {
        if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        Build("rua-de-casa");
    }

    [MenuItem("Yuuki/Bairro/Construir Moradias")]
    public static void BuildMoradias()
    {
        if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        Build("moradias");
    }

    [MenuItem("Yuuki/Bairro/Construir Dungeon")]
    public static void BuildDungeon()
    {
        if (!Application.isBatchMode && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
        Build("dungeon");
    }

    public static void Build(string mapId)
    {
        AssetDatabase.Refresh();
        YuukiRpgRevisionBuilder.Import();
        var data = JsonUtility.FromJson<YuukiBairroData>(File.ReadAllText(MapsFolder + mapId + ".json"));
        string scenePath = ScenesFolder + data.scene + ".unity";
        var sprites = ImportSprites(data);

        // Stardew-style depth: whatever stands lower on screen is drawn in front.
        GraphicsSettings.transparencySortMode = TransparencySortMode.CustomAxis;
        GraphicsSettings.transparencySortAxis = new Vector3(0f, 1f, 0f);

        var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
        var map = new GameObject("Mapa - " + data.name).transform;

        var grounds = new GameObject("Chao").transform;
        grounds.SetParent(map, false);
        foreach (var area in data.areas)
        {
            var go = new GameObject(area.name);
            go.transform.SetParent(grounds, false);
            go.transform.position = new Vector3(area.x, area.y + area.h, 0f); // pivot on the top-left corner
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = Get(sprites, area.ground);
            sr.sortingOrder = -1000;
        }

        BuildObjects(data, sprites, map);
        BuildColliders(data, map);
        // Guard the outer edge even after declining an exit. Triggers remain inside
        // these walls, so travel still works but walking off a cancelled edge cannot.
        foreach (var a in data.areas)
        {
            var boundary = new GameObject("Limites - " + a.id).transform;
            boundary.SetParent(map, false);
            void Edge(string name, Vector2 center, Vector2 size)
            {
                var go = new GameObject(name);
                go.transform.SetParent(boundary, false);
                go.transform.position = center;
                go.AddComponent<BoxCollider2D>().size = size;
            }
            Edge("Oeste", new Vector2(a.x-.3f, a.y+a.h/2), new Vector2(.6f, a.h));
            Edge("Leste", new Vector2(a.x+a.w+.3f, a.y+a.h/2), new Vector2(.6f, a.h));
            Edge("Sul", new Vector2(a.x+a.w/2, a.y-.3f), new Vector2(a.w, .6f));
            Edge("Norte", new Vector2(a.x+a.w/2, a.y+a.h+.3f), new Vector2(a.w, .6f));
        }
        var player = BuildPlayer(data);
        var cameraFollow = BuildCamera(player.transform);
        var outdoorOnly = new List<GameObject>();
        BuildLights(data, map);
        BuildInteractables(data, map);
        BuildLighting(data, cameraFollow.GetComponent<Camera>());

        if (data.wind)
        {
            var wind = new GameObject("Vento");
            var fx = wind.AddComponent<YuukiWindFx>();
            fx.followCamera = cameraFollow.GetComponent<Camera>();
            var outside = data.areas.First(a => a.outdoor);
            fx.mapBounds = new Rect(outside.x, outside.y, outside.w, outside.h);
            fx.leaves = data.fx.leaves.Select(id => Get(sprites, id)).ToArray();
            fx.dust = Get(sprites, data.fx.dust);
            fx.paper = Get(sprites, data.fx.paper);
            fx.cloud = Get(sprites, data.fx.cloud);
            outdoorOnly.Add(wind);
        }

        var smokeRoot = new GameObject("Fumaca das chamines").transform;
        outdoorOnly.Add(smokeRoot.gameObject);
        foreach (var s in data.smoke.Where(s => !s.interior))
        {
            var go = new GameObject("Fumaca");
            go.transform.SetParent(smokeRoot, false);
            go.transform.position = new Vector3(s.x, s.y, 0f);
            go.AddComponent<YuukiChimneySmoke>().puff = Get(sprites, data.fx.smoke);
        }

        BuildLife(data, sprites, player.transform);

        var manager = new GameObject("Bairro").AddComponent<YuukiBairro>();
        manager.player = player;
        manager.cameraFollow = cameraFollow;
        manager.outdoorOnly = outdoorOnly.ToArray();
        manager.regionName = string.IsNullOrEmpty(data.region) ? "Os Subúrbios" : data.region;
        manager.clockRuns = data.clockRuns;
        var background = data.background != null && data.background.a > 0 ? data.background.ToColor() : new Color(0.17f, 0.15f, 0.11f);
        manager.areas = data.areas.Select(a => new YuukiBairro.Area
        {
            id = a.id,
            name = a.name,
            bounds = new Rect(a.x, a.y, a.w, a.h),
            outdoor = a.outdoor,
            background = a.outdoor ? background : new Color(0.03f, 0.02f, 0.02f)
        }).ToArray();

        YuukiRpgRevisionBuilder.AddHouses(map);
        YuukiRpgRevisionBuilder.AddGenericHouses(map, data);
        if (!EditorSceneManager.SaveScene(scene, scenePath))
            throw new InvalidOperationException("Nao foi possivel salvar " + scenePath);
        RegisterScene(scenePath);
        AssetDatabase.SaveAssets();
        Selection.activeGameObject = player.gameObject;
        Debug.Log($"YUUKI_BAIRRO_OK: {data.name} com {data.objects.Length} objetos, {data.npcs.Length} NPCs, " +
                  $"{data.blockers.Length} bloqueios. Cena salva em {scenePath}. Aperte Play.");
    }

    // Keeps every bairro map in the Build Settings (needed to walk between them), in map order.
    private static void RegisterScene(string scenePath)
    {
        var scenes = EditorBuildSettings.scenes.Where(s => s.path != scenePath).ToList();
        scenes.Add(new EditorBuildSettingsScene(scenePath, true));
        int Rank(EditorBuildSettingsScene s)
        {
            if (s.path == ScenesFolder + YuukiMenu.SceneName + ".unity") return -1;
            for (int i = 0; i < MapOrder.Length; i++)
            {
                string mapJson = MapsFolder + MapOrder[i] + ".json";
                if (!File.Exists(mapJson)) continue;
                var info = JsonUtility.FromJson<YuukiBairroData>(File.ReadAllText(mapJson));
                if (s.path == ScenesFolder + info.scene + ".unity") return i;
            }
            return MapOrder.Length;
        }
        EditorBuildSettings.scenes = scenes.OrderBy(Rank).ToArray();
    }

    // ------------------------------------------------------------------ sprites
    private static Dictionary<string, Sprite> ImportSprites(YuukiBairroData data)
    {
        AssetDatabase.StartAssetEditing();
        try
        {
            foreach (var info in data.sprites)
            {
                var importer = AssetImporter.GetAtPath(info.path) as TextureImporter;
                if (importer == null)
                {
                    Debug.LogError("Sprite nao encontrado: " + info.path);
                    continue;
                }
                importer.textureType = TextureImporterType.Sprite;
                importer.spriteImportMode = SpriteImportMode.Single;
                importer.spritePixelsPerUnit = info.ppu;
                importer.filterMode = FilterMode.Point;
                importer.textureCompression = TextureImporterCompression.Uncompressed;
                importer.mipmapEnabled = false;
                importer.alphaIsTransparency = true;
                importer.wrapMode = TextureWrapMode.Clamp;
                importer.npotScale = TextureImporterNPOTScale.None;
                importer.maxTextureSize = 4096;
                var settings = new TextureImporterSettings();
                importer.ReadTextureSettings(settings);
                settings.spriteAlignment = (int)SpriteAlignment.Custom;
                settings.spritePivot = new Vector2(info.pivotX, info.pivotY);
                settings.spriteMeshType = SpriteMeshType.FullRect;
                settings.spriteExtrude = 1;
                importer.SetTextureSettings(settings);
                importer.SaveAndReimport();
            }
        }
        finally
        {
            AssetDatabase.StopAssetEditing();
        }
        var result = new Dictionary<string, Sprite>();
        foreach (var info in data.sprites)
        {
            var sprite = AssetDatabase.LoadAssetAtPath<Sprite>(info.path);
            if (sprite == null) Debug.LogError("Sprite nao importado: " + info.path);
            else result[info.id] = sprite;
        }
        return result;
    }

    private static Sprite Get(Dictionary<string, Sprite> sprites, string id)
    {
        if (!string.IsNullOrEmpty(id) && sprites.TryGetValue(id, out var sprite)) return sprite;
        Debug.LogError("Sprite ausente no layout: " + id);
        return null;
    }

    private static SpriteRenderer AddArt(Transform parent, Sprite sprite, bool flipX, float scale = 1f)
    {
        var art = new GameObject("Arte");
        art.transform.SetParent(parent, false);
        art.transform.localScale = Vector3.one * scale;
        var sr = art.AddComponent<SpriteRenderer>();
        sr.sprite = sprite;
        sr.flipX = flipX;
        sr.spriteSortPoint = SpriteSortPoint.Pivot;
        return sr;
    }

    // ------------------------------------------------------------------ scenery
    private static void BuildObjects(YuukiBairroData data, Dictionary<string, Sprite> sprites, Transform map)
    {
        var root = new GameObject("Objetos").transform;
        root.SetParent(map, false);
        var groups = new Dictionary<string, Transform>();
        foreach (var o in data.objects)
        {
            Transform parent = root;
            if (!string.IsNullOrEmpty(o.group))
            {
                if (!groups.TryGetValue(o.group, out parent))
                {
                    // The group sorts as one piece from its first (anchor) object's feet.
                    var g = new GameObject("Grupo " + o.group);
                    g.transform.SetParent(root, false);
                    g.transform.position = new Vector3(o.x, o.y, 0f);
                    g.AddComponent<SortingGroup>();
                    groups[o.group] = parent = g.transform;
                }
            }
            var go = new GameObject(o.sprite);
            go.transform.SetParent(parent, false);
            go.transform.position = new Vector3(o.x, o.y, 0f);
            var sr = AddArt(go.transform, Get(sprites, o.sprite), o.flipX);
            // Inside a sorting group: laundry in front of its rope, torches in front of their wall.
            sr.sortingOrder = o.order != 0 ? o.order : o.swing ? 1 : 0;
            if (o.light != null && o.light.radius > 0f)
            {
                var light = go.AddComponent<YuukiLight>();
                ConfigureLight(light, o.light.radius, o.light.intensity, o.light.r, o.light.g, o.light.b, o.light.flicker,
                    o.light.night);
                light.offset = new Vector2(o.light.ox, o.light.oy);
                if (!string.IsNullOrEmpty(o.light.offSprite))
                {
                    light.lampRenderer = sr;
                    light.onSprite = sr.sprite;
                    light.offSprite = Get(sprites, o.light.offSprite);
                }
            }
            if (o.sway > 0f)
            {
                var sway = sr.gameObject.AddComponent<YuukiWindSway>();
                sway.amplitude = o.sway;
                sway.hanging = o.swing;
            }
            if (o.colW > 0f && o.colH > 0f)
            {
                var box = go.AddComponent<BoxCollider2D>();
                box.size = new Vector2(o.colW, o.colH);
                box.offset = new Vector2(o.colX, o.colY);
            }
            go.isStatic = o.sway <= 0f;
        }
    }

    private static void BuildColliders(YuukiBairroData data, Transform map)
    {
        var root = new GameObject("Bloqueios").transform;
        root.SetParent(map, false);
        foreach (var b in data.blockers)
        {
            var go = new GameObject(b.kind == "hole" ? "Buraco" : "Parede");
            go.transform.SetParent(root, false);
            go.transform.position = new Vector3(b.x, b.y, 0f);
            go.AddComponent<BoxCollider2D>().size = new Vector2(b.w, b.h);
            go.isStatic = true;
        }
        var doors = new GameObject("Portas").transform;
        doors.SetParent(map, false);
        foreach (var p in data.portals)
        {
            var go = new GameObject("Porta " + p.id);
            go.transform.SetParent(doors, false);
            go.transform.position = new Vector3(p.x, p.y, 0f);
            var box = go.AddComponent<BoxCollider2D>();
            box.size = new Vector2(p.w, p.h);
            box.isTrigger = true;
            var portal = go.AddComponent<YuukiPortal>();
            portal.target = new Vector2(p.targetX, p.targetY);
            portal.areaId = p.area;
        }
        var exits = new GameObject("Saidas do mapa").transform;
        exits.SetParent(map, false);
        foreach (var e in data.exits)
        {
            var go = new GameObject("Saida " + e.id);
            go.transform.SetParent(exits, false);
            go.transform.position = new Vector3(e.x, e.y, 0f);
            var box = go.AddComponent<BoxCollider2D>();
            box.size = new Vector2(e.w, e.h);
            box.isTrigger = true;
            var exit = go.AddComponent<YuukiMapExit>();
            exit.label = e.label;
            exit.targetMap = e.targetMap;
            exit.target = new Vector2(e.targetX, e.targetY);
            exit.outward = new Vector2(e.outwardX, e.outwardY);
        }
    }

    // ------------------------------------------------------------------ light and interaction
    private static void ConfigureLight(YuukiLight light, float radius, float intensity, float r, float g, float b,
        float flicker, bool night)
    {
        light.radius = radius;
        light.intensity = intensity;
        light.color = new Color(r, g, b);
        light.flicker = flicker;
        light.mode = night ? YuukiLight.Mode.NightOnly : YuukiLight.Mode.Always;
    }

    private static void BuildLights(YuukiBairroData data, Transform map)
    {
        if (data.lights == null) return;
        var root = new GameObject("Luzes").transform;
        root.SetParent(map, false);
        foreach (var l in data.lights)
        {
            var go = new GameObject(l.night ? "Luz noturna" : "Luz");
            go.transform.SetParent(root, false);
            go.transform.position = new Vector3(l.x, l.y, 0f);
            ConfigureLight(go.AddComponent<YuukiLight>(), l.radius, l.intensity, l.r, l.g, l.b, l.flicker, l.night);
        }
    }

    private static void BuildInteractables(YuukiBairroData data, Transform map)
    {
        if (data.interactables == null) return;
        var root = new GameObject("Interações (F)").transform;
        root.SetParent(map, false);
        foreach (var i in data.interactables)
        {
            var go = new GameObject((i.kind == "stairs" ? "Escada - " : i.kind == "books" ? "Estante - " : "Placa - ") + i.title);
            go.transform.SetParent(root, false);
            go.transform.position = new Vector3(i.x, i.y, 0f);
            YuukiInteractable item;
            switch (i.kind)
            {
                case "stairs":
                    var stairs = go.AddComponent<YuukiStairs>();
                    stairs.destinationName = i.title;
                    stairs.targetMap = i.targetMap;
                    stairs.target = new Vector2(i.targetX, i.targetY);
                    item = stairs;
                    break;
                case "books":
                    var shelf = go.AddComponent<YuukiBookshelf>();
                    shelf.shelfName = i.title;
                    shelf.bookIds = i.bookIds ?? new string[0];
                    item = shelf;
                    break;
                default:
                    var sign = go.AddComponent<YuukiSign>();
                    sign.title = i.title;
                    sign.text = i.text;
                    item = sign;
                    break;
            }
            if (!string.IsNullOrEmpty(i.prompt)) item.prompt = i.prompt;
            item.radius = i.radius > 0 ? i.radius : 1.2f;
        }
    }

    // Darkness overlay in front of the camera (day/night outdoors, always dark underground).
    private static void BuildLighting(YuukiBairroData data, Camera camera)
    {
        Directory.CreateDirectory(LightingFolder);
        string spritePath = LightingFolder + "branco.png";
        if (!File.Exists(spritePath))
        {
            var tex = new Texture2D(4, 4);
            tex.SetPixels(Enumerable.Repeat(Color.white, 16).ToArray());
            File.WriteAllBytes(spritePath, tex.EncodeToPNG());
            UnityEngine.Object.DestroyImmediate(tex);
            AssetDatabase.ImportAsset(spritePath);
        }
        var importer = (TextureImporter)AssetImporter.GetAtPath(spritePath);
        if (importer.textureType != TextureImporterType.Sprite || importer.spritePixelsPerUnit != 4)
        {
            importer.textureType = TextureImporterType.Sprite;
            importer.spriteImportMode = SpriteImportMode.Single;
            importer.spritePixelsPerUnit = 4;
            importer.filterMode = FilterMode.Point;
            importer.SaveAndReimport();
        }
        string materialPath = LightingFolder + "Escuridao.mat";
        var material = AssetDatabase.LoadAssetAtPath<Material>(materialPath);
        if (material == null)
        {
            var shader = Shader.Find("Yuuki/Darkness");
            if (shader == null) throw new InvalidOperationException("Shader Yuuki/Darkness não encontrado.");
            material = new Material(shader);
            AssetDatabase.CreateAsset(material, materialPath);
        }
        var go = new GameObject("Iluminação");
        go.transform.SetParent(camera.transform, false);
        var sr = go.AddComponent<SpriteRenderer>();
        sr.sprite = AssetDatabase.LoadAssetAtPath<Sprite>(spritePath);
        sr.sharedMaterial = material;
        sr.sortingOrder = 1000;
        var lighting = go.AddComponent<YuukiLighting>();
        lighting.target = camera;
        lighting.followClock = data.followClock;
        if (data.ambient != null) lighting.fixedAmbient = data.ambient.ToColor();
    }

    // ------------------------------------------------------------------ player & camera
    private static PhysicsMaterial2D NoFriction()
    {
        var material = AssetDatabase.LoadAssetAtPath<PhysicsMaterial2D>(PhysicsPath);
        if (material != null) return material;
        Directory.CreateDirectory(Path.GetDirectoryName(PhysicsPath));
        material = new PhysicsMaterial2D("SemAtrito") { friction = 0f, bounciness = 0f };
        AssetDatabase.CreateAsset(material, PhysicsPath);
        return material;
    }

    private static YuukiPlayerTopDown BuildPlayer(YuukiBairroData data)
    {
        var go = new GameObject("Yuuki");
        go.transform.position = new Vector3(data.player.x, data.player.y, 0f);
        var body = go.AddComponent<Rigidbody2D>();
        body.gravityScale = 0f;
        body.freezeRotation = true;
        body.interpolation = RigidbodyInterpolation2D.Interpolate;
        body.collisionDetectionMode = CollisionDetectionMode2D.Continuous;
        body.sleepMode = RigidbodySleepMode2D.NeverSleep;
        // Collision only at the feet, like Stardew: the body and head overlap walls behind.
        var feet = go.AddComponent<CapsuleCollider2D>();
        feet.direction = CapsuleDirection2D.Horizontal;
        feet.size = new Vector2(0.5f, 0.26f);
        feet.offset = new Vector2(0f, 0.13f);
        feet.sharedMaterial = NoFriction();

        var idle = AssetDatabase.LoadAllAssetsAtPath(YuukiIdle).OfType<Sprite>()
            .FirstOrDefault(s => s.name == "idle_right_00");
        var art = AddArt(go.transform, idle, false, YuukiScale);
        var animator = art.gameObject.AddComponent<Animator>();
        animator.runtimeAnimatorController = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>(YuukiController);
        if (animator.runtimeAnimatorController == null) Debug.LogError("Animator nao encontrado: " + YuukiController);
        var rpg = go.AddComponent<YuukiRpgAnimation>();
        rpg.art = art;
        var movement = AssetDatabase.LoadAllAssetsAtPath("Assets/Game/Art/Yuuki/Yuuki_Movement_6x6.png").OfType<Sprite>();
        rpg.runLeft = movement.Where(s => s.name.StartsWith("run_left_")).OrderBy(s => s.name).ToArray();
        rpg.runRight = movement.Where(s => s.name.StartsWith("run_right_")).OrderBy(s => s.name).ToArray();
        var controller = go.AddComponent<YuukiPlayerTopDown>();
        go.AddComponent<YuukiInteractor>();
        return controller;
    }

    private static YuukiBairroCamera BuildCamera(Transform target)
    {
        var go = new GameObject("Main Camera");
        go.tag = "MainCamera";
        var cam = go.AddComponent<Camera>();
        cam.orthographic = true;
        cam.orthographicSize = 5.4f; // about 19 x 11 tiles on a 16:9 screen
        cam.clearFlags = CameraClearFlags.SolidColor;
        cam.backgroundColor = Color.black;
        cam.transparencySortMode = TransparencySortMode.CustomAxis;
        cam.transparencySortAxis = new Vector3(0f, 1f, 0f);
        cam.nearClipPlane = 0.1f;
        cam.farClipPlane = 50f;
        go.AddComponent<AudioListener>();
        go.transform.position = new Vector3(target.position.x, target.position.y, -10f);
        var follow = go.AddComponent<YuukiBairroCamera>();
        follow.target = target;
        return follow;
    }

    // ------------------------------------------------------------------ villagers & birds
    private static void BuildLife(YuukiBairroData data, Dictionary<string, Sprite> sprites, Transform player)
    {
        var root = new GameObject("Moradores").transform;
        foreach (var n in data.npcs)
        {
            var variant = data.npcVariants.First(v => v.id == n.variant);
            var go = new GameObject("NPC " + n.id);
            go.transform.SetParent(root, false);
            Vector2 start = n.points != null && n.points.Length > 0
                ? n.points[0]
                : new Vector2(n.rect.x + n.rect.w / 2f, n.rect.y + n.rect.h / 2f);
            go.transform.position = start;
            var body = go.AddComponent<Rigidbody2D>();
            body.bodyType = RigidbodyType2D.Kinematic;
            body.interpolation = RigidbodyInterpolation2D.Interpolate;
            var feet = go.AddComponent<CapsuleCollider2D>();
            feet.direction = CapsuleDirection2D.Horizontal;
            feet.size = new Vector2(0.45f * n.scale, 0.24f);
            feet.offset = new Vector2(0f, 0.12f);
            var sr = AddArt(go.transform, Get(sprites, variant.idleRight), false, n.scale);
            var walker = go.AddComponent<YuukiNpcWalker>();
            walker.mode = n.mode == "wander" ? YuukiNpcWalker.Mode.Wander : YuukiNpcWalker.Mode.Patrol;
            walker.points = n.points ?? new Vector2[0];
            walker.wanderArea = new Rect(n.rect.x, n.rect.y, n.rect.w, n.rect.h);
            walker.speed = n.speed;
            walker.waitMin = n.waitMin;
            walker.waitMax = n.waitMax;
            walker.spriteRenderer = sr;
            walker.walkLeft = variant.walkLeft.Select(id => Get(sprites, id)).ToArray();
            walker.walkRight = variant.walkRight.Select(id => Get(sprites, id)).ToArray();
            walker.idleLeft = Get(sprites, variant.idleLeft);
            walker.idleRight = Get(sprites, variant.idleRight);
            walker.player = player;
        }
        var birds = new GameObject("Pombos").transform;
        foreach (var b in data.birds)
        {
            var go = new GameObject("Bando");
            go.transform.SetParent(birds, false);
            go.transform.position = new Vector3(b.x, b.y, 0f);
            var flock = go.AddComponent<YuukiPigeonFlock>();
            flock.frames = data.fx.pigeon.Select(id => Get(sprites, id)).ToArray();
            flock.count = b.count;
            flock.player = player;
        }
        if (data.chickens == null) return;
        var yard = new GameObject("Galinhas").transform;
        foreach (var c in data.chickens)
        {
            var go = new GameObject("Bando de galinhas");
            go.transform.SetParent(yard, false);
            go.transform.position = new Vector3(c.x, c.y, 0f);
            var hens = go.AddComponent<YuukiChickens>();
            hens.frames = c.frames.Select(id => Get(sprites, id)).ToArray();
            hens.radius = c.radius;
            hens.count = Mathf.Clamp(Mathf.RoundToInt(c.radius * 2f), 2, 5);
            hens.player = player;
        }
    }
}
#endif
