#if UNITY_EDITOR
using System.Linq;
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.U2D.Sprites;
using UnityEngine;

public static class YuukiAtlasImporter
{
    private const string ClipFolder = "Assets/Game/Animation/Clips";
    private const string ControllerPath = "Assets/Game/Animation/Yuuki.controller";
    private const int Cell = 512;
    private static readonly int[] FeetFromTop = { 400, 400, 400, 396, 408, 403 };
    private static readonly string[] Rows =
    {
        "walk_left", "walk_right", "run_left", "run_right", "jump_left", "jump_right"
    };

    [MenuItem("Yuuki/Importar atlas de movimento")]
    public static void Import()
    {
        var names = Rows.SelectMany(row => Enumerable.Range(0, 6).Select(col => row + "_" + col.ToString("00"))).ToArray();
        var sprites = Slice("Assets/Game/Art/Yuuki/Yuuki_Movement_6x6.png", 6, 6, names,
            Enumerable.Range(0, 36).Select(index => FeetFromTop[index / 6]).ToArray());
        var idleSprites = Slice("Assets/Game/Art/Yuuki/Yuuki_Idle_2x1.png", 2, 1,
            new[] { "idle_left_00", "idle_right_00" }, new[] { 400, 400 });
        foreach (var item in idleSprites)
            sprites.Add(item.Key, item.Value);

        EnsureFolder("Assets/Game/Animation");
        EnsureFolder(ClipFolder);

        AnimationClip[] clips = new AnimationClip[6];
        for (int row = 0; row < Rows.Length; row++)
        {
            bool looping = row < 4;
            int fps = row == 2 || row == 3 ? 12 : row < 4 ? 8 : 10;
            clips[row] = CreateClip(Rows[row], sprites, fps, looping);
        }

        AnimationClip idleLeft = CreateClip("idle_left", sprites, 1, true, "idle_left_00");
        AnimationClip idleRight = CreateClip("idle_right", sprites, 1, true, "idle_right_00");
        BuildController(clips, idleLeft, idleRight);
        AssetDatabase.SaveAssets();
        AssetDatabase.Refresh();
        Debug.Log("Atlas fatiado; seis animacoes, dois estados idle e Yuuki.controller criados.");
    }

    private static Dictionary<string, Sprite> Slice(string path, int columns, int rows, string[] names, int[] feet)
    {
        AssetDatabase.ImportAsset(path, ImportAssetOptions.ForceUpdate);
        var importer = AssetImporter.GetAtPath(path) as TextureImporter;
        if (importer == null)
            throw new System.InvalidOperationException("Atlas ausente: " + path);
        importer.textureType = TextureImporterType.Sprite;
        importer.spriteImportMode = SpriteImportMode.Multiple;
        importer.filterMode = FilterMode.Point;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.mipmapEnabled = false;
        importer.npotScale = TextureImporterNPOTScale.None;
        importer.maxTextureSize = 4096;
        importer.alphaIsTransparency = true;
        importer.spritePixelsPerUnit = 200;
        importer.SaveAndReimport();
        var texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        if (texture.width != columns * Cell || texture.height != rows * Cell)
            throw new System.InvalidOperationException("Dimensoes incorretas: " + path);

        var factory = new SpriteDataProviderFactories();
        factory.Init();
        var provider = factory.GetSpriteEditorDataProviderFromObject(importer);
        provider.InitSpriteEditorDataProvider();
        var existing = provider.GetSpriteRects().ToDictionary(sprite => sprite.name);
        var metadata = names.Select((name, index) => new SpriteRect
        {
            name = name,
            spriteID = existing.ContainsKey(name) ? existing[name].spriteID : GUID.Generate(),
            rect = new Rect((index % columns) * Cell, texture.height - (index / columns + 1) * Cell, Cell, Cell),
            alignment = SpriteAlignment.Custom,
            pivot = new Vector2(0.5f, (Cell - feet[index]) / (float)Cell)
        }).ToArray();
        provider.SetSpriteRects(metadata);
        provider.GetDataProvider<ISpriteNameFileIdDataProvider>().SetNameFileIdPairs(
            metadata.Select(sprite => new SpriteNameFileIdPair(sprite.name, sprite.spriteID)).ToList());
        provider.Apply();
        importer.SaveAndReimport();
        var sprites = AssetDatabase.LoadAllAssetsAtPath(path).OfType<Sprite>().ToDictionary(sprite => sprite.name);
        if (metadata.Any(item => !sprites.ContainsKey(item.name)))
            throw new System.InvalidOperationException("Fatiamento incompleto: " + path);
        return sprites;
    }

    private static AnimationClip CreateClip(
        string name, System.Collections.Generic.Dictionary<string, Sprite> sprites,
        int fps, bool looping, string singleSprite = null)
    {
        var clip = new AnimationClip { name = name, frameRate = fps };
        int count = singleSprite == null ? 6 : 1;
        // Give the last frame a full interval; otherwise Unity loops at its start.
        var keys = new ObjectReferenceKeyframe[count > 1 ? count + 1 : count];

        for (int frame = 0; frame < count; frame++)
        {
            string spriteName = singleSprite ?? name + "_" + frame.ToString("00");
            keys[frame] = new ObjectReferenceKeyframe
            {
                time = frame / (float)fps,
                value = sprites[spriteName]
            };
        }

        if (count > 1)
            keys[count] = new ObjectReferenceKeyframe
            {
                time = count / (float)fps,
                value = keys[looping ? 0 : count - 1].value
            };

        AnimationUtility.SetObjectReferenceCurve(
            clip,
            new EditorCurveBinding
            {
                path = "",
                type = typeof(SpriteRenderer),
                propertyName = "m_Sprite"
            },
            keys);

        AnimationClipSettings settings = AnimationUtility.GetAnimationClipSettings(clip);
        settings.loopTime = looping;
        AnimationUtility.SetAnimationClipSettings(clip, settings);

        string assetPath = ClipFolder + "/" + name + ".anim";
        var existing = AssetDatabase.LoadAssetAtPath<AnimationClip>(assetPath);
        if (existing != null)
        {
            EditorUtility.CopySerialized(clip, existing);
            Object.DestroyImmediate(clip);
            EditorUtility.SetDirty(existing);
            return existing;
        }
        AssetDatabase.CreateAsset(clip, assetPath);
        return clip;
    }

    private static void BuildController(AnimationClip[] clips, AnimationClip idleLeft, AnimationClip idleRight)
    {
        var controller = AssetDatabase.LoadAssetAtPath<AnimatorController>(ControllerPath);
        if (controller != null)
        {
            // Keep GUIDs and state references in the open scene when refreshing art.
            var stateClips = new Dictionary<string, AnimationClip>
            {
                { "Idle Left", idleLeft }, { "Idle Right", idleRight },
                { "Walk Left", clips[0] }, { "Walk Right", clips[1] },
                { "Run Left", clips[2] }, { "Run Right", clips[3] },
                { "Jump Left", clips[4] }, { "Jump Right", clips[5] }
            };
            foreach (var child in controller.layers[0].stateMachine.states)
            {
                if (stateClips.TryGetValue(child.state.name, out var motion))
                {
                    child.state.motion = motion;
                    EditorUtility.SetDirty(child.state);
                }
            }
            ConfigureJumpTiming(controller);
            EditorUtility.SetDirty(controller);
            return;
        }
        controller = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
        controller.AddParameter("HorizontalSpeed", AnimatorControllerParameterType.Float);
        controller.AddParameter("Moving", AnimatorControllerParameterType.Bool);
        controller.AddParameter("Running", AnimatorControllerParameterType.Bool);
        controller.AddParameter("FacingLeft", AnimatorControllerParameterType.Bool);
        controller.AddParameter("Grounded", AnimatorControllerParameterType.Bool);
        controller.AddParameter("Jump", AnimatorControllerParameterType.Trigger);

        AnimatorStateMachine machine = controller.layers[0].stateMachine;
        AnimatorState idleL = machine.AddState("Idle Left");
        AnimatorState walkL = machine.AddState("Walk Left");
        AnimatorState runL = machine.AddState("Run Left");
        AnimatorState jumpL = machine.AddState("Jump Left");
        AnimatorState idleR = machine.AddState("Idle Right");
        AnimatorState walkR = machine.AddState("Walk Right");
        AnimatorState runR = machine.AddState("Run Right");
        AnimatorState jumpR = machine.AddState("Jump Right");

        idleL.motion = idleLeft;
        walkL.motion = clips[0];
        runL.motion = clips[2];
        jumpL.motion = clips[4];
        idleR.motion = idleRight;
        walkR.motion = clips[1];
        runR.motion = clips[3];
        jumpR.motion = clips[5];
        machine.defaultState = idleR;

        Link(idleL, walkL, "Moving", AnimatorConditionMode.If, "FacingLeft", AnimatorConditionMode.If);
        Link(idleL, idleR, "FacingLeft", AnimatorConditionMode.IfNot);
        Link(idleR, walkR, "Moving", AnimatorConditionMode.If, "FacingLeft", AnimatorConditionMode.IfNot);
        Link(idleR, idleL, "FacingLeft", AnimatorConditionMode.If);

        Link(walkL, idleL, "Moving", AnimatorConditionMode.IfNot);
        Link(walkL, runL, "Running", AnimatorConditionMode.If);
        Link(walkL, walkR, "FacingLeft", AnimatorConditionMode.IfNot, "Moving", AnimatorConditionMode.If);
        Link(walkR, idleR, "Moving", AnimatorConditionMode.IfNot);
        Link(walkR, runR, "Running", AnimatorConditionMode.If);
        Link(walkR, walkL, "FacingLeft", AnimatorConditionMode.If, "Moving", AnimatorConditionMode.If);

        Link(runL, idleL, "Moving", AnimatorConditionMode.IfNot);
        Link(runL, walkL, "Running", AnimatorConditionMode.IfNot, "Moving", AnimatorConditionMode.If);
        Link(runL, runR, "FacingLeft", AnimatorConditionMode.IfNot, "Moving", AnimatorConditionMode.If);
        Link(runR, idleR, "Moving", AnimatorConditionMode.IfNot);
        Link(runR, walkR, "Running", AnimatorConditionMode.IfNot, "Moving", AnimatorConditionMode.If);
        Link(runR, runL, "FacingLeft", AnimatorConditionMode.If, "Moving", AnimatorConditionMode.If);

        AnimatorStateTransition toJumpL = machine.AddAnyStateTransition(jumpL);
        toJumpL.hasExitTime = false;
        toJumpL.duration = 0.03f;
        toJumpL.AddCondition(AnimatorConditionMode.If, 0, "Jump");
        toJumpL.AddCondition(AnimatorConditionMode.If, 0, "FacingLeft");

        AnimatorStateTransition toJumpR = machine.AddAnyStateTransition(jumpR);
        toJumpR.hasExitTime = false;
        toJumpR.duration = 0.03f;
        toJumpR.AddCondition(AnimatorConditionMode.If, 0, "Jump");
        toJumpR.AddCondition(AnimatorConditionMode.IfNot, 0, "FacingLeft");

        AddLandingTransitions(jumpL, idleL, walkL, runL, idleR, walkR, runR);
        AddLandingTransitions(jumpR, idleL, walkL, runL, idleR, walkR, runR);
        ConfigureJumpTiming(controller);
    }

    private static void ConfigureJumpTiming(AnimatorController controller)
    {
        if (!controller.parameters.Any(parameter => parameter.name == "JumpProgress"))
            controller.AddParameter("JumpProgress", AnimatorControllerParameterType.Float);
        foreach (var child in controller.layers[0].stateMachine.states)
        {
            if (!child.state.name.StartsWith("Jump ")) continue;
            child.state.timeParameter = "JumpProgress";
            child.state.timeParameterActive = true;
            EditorUtility.SetDirty(child.state);
        }
    }

    private static void AddLandingTransitions(
        AnimatorState jump,
        AnimatorState idleLeft, AnimatorState walkLeft, AnimatorState runLeft,
        AnimatorState idleRight, AnimatorState walkRight, AnimatorState runRight)
    {
        Link(jump, idleLeft, "Grounded", AnimatorConditionMode.If, "Moving", AnimatorConditionMode.IfNot, "FacingLeft", AnimatorConditionMode.If);
        Link(jump, walkLeft, "Grounded", AnimatorConditionMode.If, "Moving", AnimatorConditionMode.If, "Running", AnimatorConditionMode.IfNot, "FacingLeft", AnimatorConditionMode.If);
        Link(jump, runLeft, "Grounded", AnimatorConditionMode.If, "Running", AnimatorConditionMode.If, "FacingLeft", AnimatorConditionMode.If);

        Link(jump, idleRight, "Grounded", AnimatorConditionMode.If, "Moving", AnimatorConditionMode.IfNot, "FacingLeft", AnimatorConditionMode.IfNot);
        Link(jump, walkRight, "Grounded", AnimatorConditionMode.If, "Moving", AnimatorConditionMode.If, "Running", AnimatorConditionMode.IfNot, "FacingLeft", AnimatorConditionMode.IfNot);
        Link(jump, runRight, "Grounded", AnimatorConditionMode.If, "Running", AnimatorConditionMode.If, "FacingLeft", AnimatorConditionMode.IfNot);
    }

    private static void Link(
        AnimatorState from, AnimatorState to, string firstParameter, AnimatorConditionMode firstMode)
    {
        AnimatorStateTransition transition = BasicTransition(from, to);
        transition.AddCondition(firstMode, 0, firstParameter);
    }

    private static void Link(
        AnimatorState from, AnimatorState to,
        string firstParameter, AnimatorConditionMode firstMode,
        string secondParameter, AnimatorConditionMode secondMode)
    {
        AnimatorStateTransition transition = BasicTransition(from, to);
        transition.AddCondition(firstMode, 0, firstParameter);
        transition.AddCondition(secondMode, 0, secondParameter);
    }

    private static void Link(
        AnimatorState from, AnimatorState to,
        string firstParameter, AnimatorConditionMode firstMode,
        string secondParameter, AnimatorConditionMode secondMode,
        string thirdParameter, AnimatorConditionMode thirdMode)
    {
        AnimatorStateTransition transition = BasicTransition(from, to);
        transition.AddCondition(firstMode, 0, firstParameter);
        transition.AddCondition(secondMode, 0, secondParameter);
        transition.AddCondition(thirdMode, 0, thirdParameter);
    }

    private static void Link(
        AnimatorState from, AnimatorState to,
        string firstParameter, AnimatorConditionMode firstMode,
        string secondParameter, AnimatorConditionMode secondMode,
        string thirdParameter, AnimatorConditionMode thirdMode,
        string fourthParameter, AnimatorConditionMode fourthMode)
    {
        AnimatorStateTransition transition = BasicTransition(from, to);
        transition.AddCondition(firstMode, 0, firstParameter);
        transition.AddCondition(secondMode, 0, secondParameter);
        transition.AddCondition(thirdMode, 0, thirdParameter);
        transition.AddCondition(fourthMode, 0, fourthParameter);
    }

    private static AnimatorStateTransition BasicTransition(AnimatorState from, AnimatorState to)
    {
        AnimatorStateTransition transition = from.AddTransition(to);
        transition.hasExitTime = false;
        transition.duration = 0.03f;
        return transition;
    }

    private static void EnsureFolder(string path)
    {
        if (AssetDatabase.IsValidFolder(path))
            return;

        string parent = System.IO.Path.GetDirectoryName(path).Replace("\\", "/");
        string folder = System.IO.Path.GetFileName(path);
        if (!AssetDatabase.IsValidFolder(parent))
            EnsureFolder(parent);
        AssetDatabase.CreateFolder(parent, folder);
    }
}
#endif
