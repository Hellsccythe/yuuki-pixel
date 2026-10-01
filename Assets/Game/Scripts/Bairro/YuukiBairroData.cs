using System;
using UnityEngine;

// Layout exported by scripts/bairro/build_bairro.py (Assets/Game/Bairro/Maps/*.json).
// Coordinates are Unity units: x to the right, y up, 1 unit = 1 tile.
[Serializable] public sealed class YuukiBairroData
{
    public int version;
    public string map, name, scene;
    public YuukiSpriteInfo[] sprites;
    public YuukiAreaInfo[] areas;
    public YuukiObjectInfo[] objects;
    public YuukiBlockerInfo[] blockers;
    public YuukiPortalInfo[] portals;
    public YuukiExitInfo[] exits;
    public YuukiNpcInfo[] npcs;
    public YuukiNpcVariantInfo[] npcVariants;
    public YuukiBirdInfo[] birds;
    public YuukiChickenInfo[] chickens;
    public YuukiSmokeInfo[] smoke;
    public YuukiSpawnInfo player;
    public YuukiFxInfo fx;
    public YuukiPointLightInfo[] lights;
    public YuukiInteractableInfo[] interactables;
    public YuukiHouseInfo[] houses;
    public string region;
    public bool followClock = true, clockRuns = true, wind = true;
    public YuukiColorInfo ambient, background;
}

[Serializable] public sealed class YuukiColorInfo
{
    public float r, g, b, a = 1f;
    public Color ToColor() => new Color(r, g, b, a);
}

// Light carried by an object (street lamp): offset from its feet, optional daytime sprite.
[Serializable] public sealed class YuukiLightInfo
{
    public float radius, intensity, r, g, b, flicker, ox, oy;
    public bool night;
    public string offSprite;
}

[Serializable] public sealed class YuukiPointLightInfo
{
    public float x, y, radius, intensity, r, g, b, flicker;
    public bool night;
}

// kind: "sign" (text), "books" (bookshelf), "stairs" (to another map)
[Serializable] public sealed class YuukiInteractableInfo
{
    public string kind, prompt, title, text, targetMap;
    public float x, y, radius, targetX, targetY;
    public string[] bookIds;
}

// A building Yuuki can walk into: the room is built inside its footprint (theme picks the furniture).
[Serializable] public sealed class YuukiHouseInfo
{
    public string sprite, name, theme, door;
    public float x, y, doorX, doorY, doorWidth, roomW, roomH;
    public bool flip;
    public int seed, floors = 1;
}

[Serializable] public sealed class YuukiSpriteInfo { public string id, path; public float ppu, pivotX, pivotY; }

[Serializable] public sealed class YuukiAreaInfo
{
    public string id, name, ground;
    public float x, y, w, h;
    public bool outdoor;
}

[Serializable] public sealed class YuukiObjectInfo
{
    public string sprite, group;
    public float x, y, sway, sortBias;
    public bool swing, flipX;
    public float colW, colH, colX, colY;
    public int order;
    public YuukiLightInfo light;
}

[Serializable] public sealed class YuukiBlockerInfo { public float x, y, w, h; public string kind; }

[Serializable] public sealed class YuukiPortalInfo
{
    public string id, area;
    public float x, y, w, h, targetX, targetY;
}

[Serializable] public sealed class YuukiExitInfo
{
    public string id, label, targetMap;
    public float x, y, w, h, targetX, targetY, outwardX, outwardY;
}

[Serializable] public sealed class YuukiRectInfo { public float x, y, w, h; }

[Serializable] public sealed class YuukiNpcInfo
{
    public string id, variant, mode;
    public float scale, speed, waitMin, waitMax;
    public Vector2[] points;
    public YuukiRectInfo rect;
}

[Serializable] public sealed class YuukiNpcVariantInfo
{
    public string id, idleLeft, idleRight;
    public string[] walkLeft, walkRight;
}

[Serializable] public sealed class YuukiBirdInfo { public float x, y; public int count; }

[Serializable] public sealed class YuukiChickenInfo { public float x, y, radius; public string[] frames; }

[Serializable] public sealed class YuukiSmokeInfo { public float x, y; public bool interior; }

[Serializable] public sealed class YuukiSpawnInfo { public float x, y; public string area; }

[Serializable] public sealed class YuukiFxInfo
{
    public string[] leaves, pigeon;
    public string dust, paper, cloud, smoke;
}
