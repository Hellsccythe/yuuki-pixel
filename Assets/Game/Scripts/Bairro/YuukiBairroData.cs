using System;
using UnityEngine;

// Layout exported by scripts/bairro/build_rua_de_casa.py (Assets/Game/Bairro/Maps/*.json).
// Coordinates are Unity units: x to the right, y up, 1 unit = 1 tile.
[Serializable] public sealed class YuukiBairroData
{
    public int version;
    public string map, name;
    public YuukiSpriteInfo[] sprites;
    public YuukiAreaInfo[] areas;
    public YuukiObjectInfo[] objects;
    public YuukiBlockerInfo[] blockers;
    public YuukiPortalInfo[] portals;
    public YuukiExitInfo[] exits;
    public YuukiNpcInfo[] npcs;
    public YuukiNpcVariantInfo[] npcVariants;
    public YuukiBirdInfo[] birds;
    public YuukiSmokeInfo[] smoke;
    public YuukiSpawnInfo player;
    public YuukiFxInfo fx;
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
}

[Serializable] public sealed class YuukiBlockerInfo { public float x, y, w, h; public string kind; }

[Serializable] public sealed class YuukiPortalInfo
{
    public string id, area;
    public float x, y, w, h, targetX, targetY;
}

[Serializable] public sealed class YuukiExitInfo { public string id, label; public float x, y, w, h; }

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

[Serializable] public sealed class YuukiSmokeInfo { public float x, y; public bool interior; }

[Serializable] public sealed class YuukiSpawnInfo { public float x, y; public string area; }

[Serializable] public sealed class YuukiFxInfo
{
    public string[] leaves, pigeon;
    public string dust, paper, cloud, smoke;
}
