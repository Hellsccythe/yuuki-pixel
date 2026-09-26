#if UNITY_EDITOR
using System;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class YuukiAtlasImporter
{
    [MenuItem("Yuuki/Criar clipes experimentais")]
    public static void Import()
    {
        var texture = Selection.activeObject as Texture2D;
        if (texture == null) { Debug.LogError("Selecione uma textura de atlas Yuuki 6x6."); return; }
        var path = AssetDatabase.GetAssetPath(texture);
        var importer = AssetImporter.GetAtPath(path) as TextureImporter;
        if (importer == null) return;
        if (!EditorUtility.DisplayDialog("Atlas experimental",
            "Cria 36 sprites e seis clipes. Nao corrige asas, cortes ou continuidade. Substitui o fatiamento desta textura. Continuar?", "Criar", "Cancelar")) return;
        importer.textureType = TextureImporterType.Sprite;
        importer.spriteImportMode = SpriteImportMode.Multiple;
        importer.filterMode = FilterMode.Point;
        importer.textureCompression = TextureImporterCompression.Uncompressed;
        importer.mipmapEnabled = false;
        importer.npotScale = TextureImporterNPOTScale.None;
        importer.maxTextureSize = 8192;
        importer.alphaIsTransparency = true;
        importer.spritePixelsPerUnit = 200;
        importer.SaveAndReimport();
        texture = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        var names = new[] { "walk_left", "walk_right", "run_left", "run_right", "jump_left", "jump_right" };
        var data = new SpriteMetaData[36];
        for (int row = 0; row < 6; row++)
            for (int col = 0; col < 6; col++)
            {
                int x0 = col * texture.width / 6, x1 = (col + 1) * texture.width / 6;
                int top = row * texture.height / 6, bottom = (row + 1) * texture.height / 6;
                data[row * 6 + col] = new SpriteMetaData {
                    name = names[row] + "_" + col.ToString("00"),
                    rect = new Rect(x0, texture.height - bottom, x1 - x0, bottom - top),
                    alignment = (int)SpriteAlignment.Custom, pivot = new Vector2(.5f, .05f)
                };
            }
#pragma warning disable 0618
        importer.spritesheet = data;
#pragma warning restore 0618
        importer.SaveAndReimport();
        var sprites = AssetDatabase.LoadAllAssetsAtPath(path).OfType<Sprite>().ToDictionary(s => s.name);
        if (data.Any(d => !sprites.ContainsKey(d.name))) {
            Debug.LogError("Fatiamento nao produziu todos os sprites. Confira a compatibilidade da API na sua versao Unity.");
            return;
        }
        string output = AssetDatabase.GenerateUniqueAssetPath("Assets/YuukiExperimentalClips");
        AssetDatabase.CreateFolder("Assets", System.IO.Path.GetFileName(output));
        for (int row = 0; row < 6; row++) {
            float rate = row == 2 || row == 3 ? 12 : 8;
            var clip = new AnimationClip { frameRate = rate };
            var keys = new ObjectReferenceKeyframe[7];
            for (int col = 0; col < 7; col++) keys[col] = new ObjectReferenceKeyframe {
                time = col / rate, value = sprites[names[row] + "_" + (col < 6 ? col : row < 4 ? 0 : 5).ToString("00")]
            };
            AnimationUtility.SetObjectReferenceCurve(clip, new EditorCurveBinding {
                path = "", type = typeof(SpriteRenderer), propertyName = "m_Sprite"
            }, keys);
            var settings = AnimationUtility.GetAnimationClipSettings(clip);
            settings.loopTime = row < 4;
            AnimationUtility.SetAnimationClipSettings(clip, settings);
            AssetDatabase.CreateAsset(clip, output + "/" + names[row] + ".anim");
        }
        AssetDatabase.SaveAssets();
        Debug.Log("Clipes experimentais criados em " + output + ". Revisao visual obrigatoria; usar direcoes separadas, nao flipX.");
    }
}
#endif
