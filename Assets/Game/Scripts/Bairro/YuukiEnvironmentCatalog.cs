using System;
using UnityEngine;

[Serializable]
public sealed class YuukiEnvironmentCatalog
{
    public int version;
    public string title;
    public YuukiEnvironmentAsset[] assets;

    public static YuukiEnvironmentCatalog Load()
    {
        var json = Resources.Load<TextAsset>("Environment/catalog");
        if (json == null) throw new InvalidOperationException("Catálogo de cenários ausente.");
        return JsonUtility.FromJson<YuukiEnvironmentCatalog>(json.text);
    }
}

[Serializable]
public sealed class YuukiEnvironmentAsset
{
    public string id, name, category, resource, path, source, note;
    public int width, height;
    public float ppu, tileWidth, pivotX, pivotY, colliderWidth, colliderHeight;
    public bool floor, decal;
}
