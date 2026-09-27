using System;
using UnityEngine;

[Serializable] public sealed class YuukiWorldData
{
    public int version;
    public string startMap;
    public YuukiMapModule[] modules;
    public YuukiMapData[] maps;
}
[Serializable] public sealed class YuukiMapModule
{
    public string id;
    public YuukiWorldObject[] objects;
    public YuukiWorldPoint[] points;
}
[Serializable] public sealed class YuukiMapInstance { public string module; public float x, y; }
[Serializable] public sealed class YuukiWorldObject
{
    public string asset;
    public float x, y, width, height;
    public bool solid;
    public float[] footprint;
}
[Serializable] public sealed class YuukiWorldPoint
{
    public string id, title, text, target;
    public float x, y, targetX, targetY;
    public bool journal;
}
[Serializable] public sealed class YuukiWorldRegion { public string name; public float x, y, w, h; }
[Serializable] public sealed class YuukiMapData
{
    public string id, name;
    public float width, height, spawnX, spawnY;
    public YuukiMapInstance[] instances;
    public YuukiWorldObject[] objects;
    public YuukiWorldPoint[] points;
    public YuukiWorldRegion[] regions;
}
