"""Sanity checks for a neighbourhood map JSON without opening Unity.

Rasterises every collider (objects + blockers) on a fine grid, then checks that:
  * every sprite referenced by the layout exists on disk;
  * the player spawn and every portal target are free;
  * Yuuki can walk from the spawn to every door, exit and NPC route (flood fill with her
    feet capsule, 0.5 x 0.26 tiles);
  * patrol/wander routes of the villagers never cross a collider.
  * every exit to another map lands on a free spot there, outside that map's own exits.
Run: python3 scripts/bairro/validate_map.py            (all maps)
     python3 scripts/bairro/validate_map.py <map.json>
"""
import json
import sys
from collections import deque
from pathlib import Path

import numpy as np
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
RES = 10  # cells per tile
FEET = (0.5, 0.26)


MAPS = ROOT / "Assets/Game/Bairro/Maps"


def load_all():
    maps = {}
    for p in sorted(MAPS.glob("*.json")):
        d = json.loads(p.read_text(encoding="utf-8"))
        maps[d["scene"]] = d
    return maps


def main(path, all_maps):
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    print(f"== {data['name']}")
    problems = []
    ids = {s["id"] for s in data["sprites"]}
    for s in data["sprites"]:
        if not (ROOT / s["path"]).exists():
            problems.append("missing file " + s["path"])
    refs = [o["sprite"] for o in data["objects"]] + [a["ground"] for a in data["areas"]]
    for v in data["npcVariants"]:
        refs += v["walkLeft"] + v["walkRight"] + [v["idleLeft"], v["idleRight"]]
    fx = data["fx"]
    refs += fx["leaves"] + fx["pigeon"] + [fx["dust"], fx["paper"], fx["cloud"], fx["smoke"]]
    problems += [f"unknown sprite id {r}" for r in refs if r not in ids]

    x1 = max(a["x"] + a["w"] for a in data["areas"]) + 2
    y1 = max(a["y"] + a["h"] for a in data["areas"]) + 2
    W, H = int(x1 * RES), int(y1 * RES)
    solid = np.zeros((H, W), bool)

    def fill(cx, cy, w, h):
        xa, xb = int((cx - w / 2) * RES), int(np.ceil((cx + w / 2) * RES))
        ya, yb = int((cy - h / 2) * RES), int(np.ceil((cy + h / 2) * RES))
        solid[max(0, ya):max(0, yb), max(0, xa):max(0, xb)] = True

    for o in data["objects"]:
        if o["colW"] > 0:
            fill(o["x"] + o["colX"], o["y"] + o["colY"], o["colW"], o["colH"])
    for b in data["blockers"]:
        fill(b["x"], b["y"], b["w"], b["h"])
    # Walkable space = outside the areas is solid too.
    inside = np.zeros_like(solid)
    for a in data["areas"]:
        inside[int(a["y"] * RES):int((a["y"] + a["h"]) * RES), int(a["x"] * RES):int((a["x"] + a["w"]) * RES)] = True
    solid |= ~inside
    # Grow obstacles by the feet capsule so a single cell stands for the player's centre.
    grown = ndi.binary_dilation(solid, structure=np.ones((int(FEET[1] * RES) | 1, int(FEET[0] * RES) | 1)))

    def cell(x, y, feet_offset=0.13):
        return int((y + feet_offset) * RES), int(x * RES)

    def free(x, y):
        r, c = cell(x, y)
        return 0 <= r < H and 0 <= c < W and not grown[r, c]

    sp = data["player"]
    if not free(sp["x"], sp["y"]):
        problems.append("spawn blocked")

    def reach(x, y):
        seen = np.zeros_like(grown)
        start = cell(x, y)
        if grown[start]:
            return seen
        q = deque([start])
        seen[start] = True
        while q:
            r, c = q.popleft()
            for dr, dc in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                nr, nc = r + dr, c + dc
                if 0 <= nr < H and 0 <= nc < W and not seen[nr, nc] and not grown[nr, nc]:
                    seen[nr, nc] = True
                    q.append((nr, nc))
        return seen

    def touches(region, cx, cy, w, h):
        ya, yb = int((cy - h / 2) * RES) - 2, int((cy + h / 2) * RES) + 3
        xa, xb = int((cx - w / 2) * RES) - 2, int((cx + w / 2) * RES) + 3
        return region[max(0, ya):yb, max(0, xa):xb].any()

    outside = reach(sp["x"], sp["y"])
    print(f"walkable from spawn: {outside.sum() / RES / RES:.1f} tiles^2")
    for p in data["portals"]:
        if not free(p["targetX"], p["targetY"]):
            problems.append(f"portal {p['id']} target blocked")
        region = reach(p["targetX"], p["targetY"])
        back = [q for q in data["portals"] if q is not p and touches(region, q["x"], q["y"], q["w"], q["h"])]
        target_area = next((a for a in data["areas"] if a["id"] == p["area"]), None)
        if target_area is not None and not target_area["outdoor"] and not back:
            problems.append(f"no way back from {p['id']}")
        if p["id"] == "porta-casa-yuuki" and not touches(outside, p["x"], p["y"], p["w"], p["h"]):
            problems.append("front door unreachable")
    for e in data["exits"]:
        if not touches(outside, e["x"], e["y"], e["w"], e["h"]):
            problems.append(f"exit {e['id']} unreachable")
        if e.get("targetMap"):
            other = all_maps.get(e["targetMap"])
            if other is None:
                problems.append(f"exit {e['id']} targets missing map {e['targetMap']}")
                continue
            tx, ty = e["targetX"], e["targetY"]
            for oe in other["exits"]:
                if abs(tx - oe["x"]) < oe["w"] / 2 + 0.4 and abs(ty + 0.13 - oe["y"]) < oe["h"] / 2 + 0.2:
                    problems.append(f"exit {e['id']} lands inside {other['name']} exit {oe['id']}")
            blocked = [b for b in other["blockers"] if abs(tx - b["x"]) < b["w"] / 2 + 0.25 and
                       abs(ty + 0.13 - b["y"]) < b["h"] / 2 + 0.13]
            if blocked:
                problems.append(f"exit {e['id']} lands on a blocker in {other['name']}")
    for n in data["npcs"]:
        pts = [(p["x"], p["y"]) for p in n["points"]]
        if n["mode"] == "wander":
            r = n["rect"]
            pts = [(r["x"] + r["w"] * i / 6, r["y"] + r["h"] * j / 4) for i in range(7) for j in range(5)]
            bad = [p for p in pts if not free(*p)]
            if bad:
                problems.append(f"npc {n['id']} wander area overlaps colliders at {bad[:3]}")
            continue
        for a, b in zip(pts, pts[1:]):
            for t in np.linspace(0, 1, 60):
                x, y = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
                if not free(x, y):
                    problems.append(f"npc {n['id']} route blocked near ({x:.1f}, {y:.1f})")
                    break
        if pts and not outside[cell(*pts[0])]:
            problems.append(f"npc {n['id']} starts outside the reachable street")

    # Debug picture of the collision map.
    from PIL import Image
    img = np.zeros((H, W, 3), np.uint8)
    img[~grown] = (70, 60, 50)
    img[outside] = (120, 170, 110)
    img[solid & inside] = (40, 30, 30)
    out = ROOT / f"docs/bairro/{data['map']}-colisao.png"
    Image.fromarray(img[::-1][::-1]).resize((W // 2, H // 2), Image.NEAREST).transpose(Image.FLIP_TOP_BOTTOM).save(out)
    print("collision map ->", out)
    if problems:
        print("PROBLEMS:")
        for p in problems:
            print("  -", p)
        return 1
    print("OK: sprites, spawn, doors, exits and NPC routes are consistent")
    return 0


if __name__ == "__main__":
    everything = load_all()
    paths = sys.argv[1:] or [MAPS / f"{d['map']}.json" for d in everything.values()]
    sys.exit(max(main(p, everything) for p in paths))
