"""Build map 1 of Yuuki's neighbourhood: "Rua de Casa" (her street) plus her house interior.

Outputs (all regenerated from scratch, deterministic):
  Assets/Game/Bairro/Sprites/**.png   weathered buildings, props, FX, placeholder NPCs
  Assets/Game/Bairro/Maps/*.png       painted ground of the street and of the interior
  Assets/Game/Bairro/Maps/rua-de-casa.json   layout read by Yuuki > Bairro > Construir Rua de Casa
  docs/bairro/rua-de-casa-preview.png        quick visual check of the composed map

Design coordinates are in tiles (1 tile = 1 Unity unit), x to the right and y DOWN from the
top-left corner, like a drawing. The JSON is exported in Unity coordinates (y up).
Run:  python3 scripts/bairro/build_rua_de_casa.py
"""
import json
import math
import random
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

sys.path.insert(0, str(Path(__file__).resolve().parent))
from common import (ROOT, OUT, WORLD_ART, fbm, value_noise, smoothstep, tile, desaturate, lum,
                    terrain_textures, load_rgba, save_rgba, crop_alpha, weather, board_window)
import props

G = 64                 # ground pixels per tile
MAP_W, MAP_H = 48, 36  # outdoor map in tiles
ROOM_X0, ROOM_W, ROOM_H = 80, 13, 10  # interior lives far to the right of the street
SPRITES = OUT / "Sprites"
MAPS = OUT / "Maps"

sprites = {}   # id -> dict(path, ppu, pivotX, pivotY, arr)


def register(sid, arr, ppu, pivot=(0.5, 0.0), group="Props"):
    path = SPRITES / group / f"{sid}.png"
    save_rgba(arr, path)
    sprites[sid] = dict(id=sid, path=str(path.relative_to(ROOT)).replace("\\", "/"), ppu=ppu,
                        pivotX=round(pivot[0], 4), pivotY=round(pivot[1], 4),
                        w=arr.shape[1], h=arr.shape[0], arr=arr)
    return sid


def size_units(sid):
    s = sprites[sid]
    return s["w"] / s["ppu"], s["h"] / s["ppu"]


# ============================================================================ SPRITES
def build_sprites():
    if SPRITES.exists():
        shutil.rmtree(SPRITES)
    art = {n: load_rgba(WORLD_ART / f"{n}.png") for n in
           ["home", "timber-house", "stone-house", "workshop", "wall", "fence", "tree", "crates",
            "well", "bench", "sign", "bed", "bookshelf", "table"]}
    feet = lambda arr: (0.5, 3 / arr.shape[0])  # 4px transparent padding below the steps

    # --- buildings (60 px per tile keeps doors ~1.8 tiles tall next to a 1.6-tile Yuuki)
    b = "Buildings"
    a = weather(art["home"], 11, desat=0.12, darken=0.03, grime=0.18, cracks=3)
    register("casa-yuuki", a, 60, feet(a), b)
    a = weather(art["timber-house"], 12, desat=0.22, darken=0.07, grime=0.45, cracks=6)
    register("casa-tenebris", a, 60, feet(a), b)
    a = weather(art["home"], 13, desat=0.42, darken=0.14, grime=0.8, cracks=12, dust=(0.98, 0.9, 0.78))
    a = board_window(a, (80, 238, 150, 296), 13)
    register("casa-velha", a, 60, feet(a), b)
    a = weather(art["stone-house"], 14, desat=0.34, darken=0.1, grime=0.7, cracks=16)
    register("casa-pedra", a, 60, feet(a), b)
    a = weather(art["stone-house"], 15, desat=0.46, darken=0.16, grime=0.9, cracks=20, dust=(0.95, 0.9, 0.82))
    a = board_window(a, (140, 150, 200, 200), 15)
    register("casa-pedra-gasta", a, 60, feet(a), b)
    a = weather(art["workshop"], 16, desat=0.28, darken=0.08, grime=0.6, cracks=8)
    register("oficina", a, 60, feet(a), b)
    a = weather(art["timber-house"], 17, desat=0.4, darken=0.15, grime=0.85, cracks=10, dust=(0.97, 0.9, 0.8))
    a = board_window(a, (230, 105, 290, 150), 17)
    register("casa-madeira-gasta", a, 60, feet(a), b)

    # --- walls & fences
    a = weather(art["wall"], 21, desat=0.3, darken=0.08, grime=0.7, cracks=14, crack_zone=(0.25, 0.9))
    register("muro", a, 105, feet(a))
    a = weather(art["wall"], 22, desat=0.42, darken=0.14, grime=0.9, cracks=22, crack_zone=(0.2, 0.95))
    register("muro-gasto", a, 105, feet(a))
    fence = weather(art["fence"], 23, desat=0.2, darken=0.06, grime=0.4, cracks=0)
    left, right = crop_alpha(fence[:, :228]), crop_alpha(fence[:, 342:])
    register("cerca-esq", left, 110, feet(left))
    register("cerca-dir", right, 110, feet(right))
    gate = crop_alpha(fence[:, 222:348])
    register("portao", gate, 110, feet(gate))
    crooked = weather(art["fence"], 24, desat=0.4, darken=0.14, grime=0.8, cracks=0)
    crooked = np.asarray(Image.fromarray(np.clip(crooked, 0, 255).astype(np.uint8)).rotate(
        -3, resample=Image.NEAREST, expand=True)).astype(float)
    crooked = crop_alpha(crooked)
    register("cerca-torta", crooked, 110, feet(crooked))

    # --- nature & street props
    a = weather(art["tree"], 31, desat=0.2, darken=0.05, grime=0, cracks=0)
    register("arvore", a, 88, (0.5, 12 / a.shape[0]))
    a = props.dry_tree(art["tree"], 32)
    register("arvore-seca", a, 88, (0.5, 12 / a.shape[0]))
    for name, ppu, seed in (("caixotes", 140, 33), ("poco", 115, 34), ("banco", 140, 35), ("placa", 140, 36)):
        src = {"caixotes": "crates", "poco": "well", "banco": "bench", "placa": "sign"}[name]
        a = weather(art[src], seed, desat=0.25, darken=0.06, grime=0.5, cracks=0)
        register(name, a, ppu, feet(a))
    for i, kind in enumerate(["dry", "dry", "green", "straw", "green", "dry"]):
        register(f"mato-{i}", props.weeds(40 + i, kind), 46, (0.5, 3 / 46))
    for i in range(3):
        a = props.rubble(50 + i)
        register(f"entulho-{i}", a, 40, (0.5, 4 / a.shape[0]))
    a = props.garden_bed(60)
    register("horta", a, 64, (0.5, 3 / a.shape[0]))
    a = props.clothesline()
    register("varal", a, 64, (0.5, 2 / a.shape[0]))
    for i, kind in enumerate(["sheet", "shirt", "pants", "towel", "shirt"]):
        a = props.laundry(kind, 70 + i)
        register(f"roupa-{i}", a, 64, (0.5, 1.0))  # pivot at the pegs so cloth swings

    # --- interior
    for name, ppu in (("cama", 150), ("estante", 140), ("mesa", 140)):
        src = {"cama": "bed", "estante": "bookshelf", "mesa": "table"}[name]
        a = weather(art[src], 80 + len(name), desat=0.15, darken=0.03, grime=0.2, cracks=0)
        register(name, a, ppu, feet(a), "Interior")
    for i in range(3):
        register(f"livros-{i}", props.book_pile(90 + i), 64, (0.5, 2 / 34), "Interior")
    register("fogao", props.stove(), 64, (0.5, 2 / 110), "Interior")

    # --- FX
    for i, f in enumerate(props.pigeon_frames()):
        register(f"pombo-{i}", f, 64, (0.5, 0.05), "FX")
    for i in range(4):
        register(f"folha-{i}", props.leaf(100 + i), 64, (0.5, 0.5), "FX")
    register("poeira", props.dust(), 64, (0.5, 0.5), "FX")
    register("papel", props.paper(), 64, (0.5, 0.5), "FX")
    register("nuvem-sombra", props.soft_blob(420, 260, (18, 20, 34), 255, 26), 26, (0.5, 0.5), "FX")
    register("fumaca", props.smoke_puff(), 64, (0.5, 0.5), "FX")


def build_npcs():
    atlas = load_rgba(ROOT / "Assets/Game/Art/Yuuki/Yuuki_Movement_6x6.png")
    idle = load_rgba(ROOT / "Assets/Game/Art/Yuuki/Yuuki_Idle_2x1.png")
    variants = {
        "morador": (150, 118, 88), "idosa": (170, 164, 156), "crianca-a": (132, 146, 104),
        "crianca-b": (120, 138, 160), "lavadeira": (168, 120, 106), "artesao": (126, 100, 80),
        "andarilho": (142, 140, 124),
    }
    out = []
    for name, tint in variants.items():
        frames, pivot = props.npc_silhouettes(atlas, idle, tint, name, SPRITES / "NPC")
        ids = {}
        for label, c, fname in frames:
            sid = f"npc-{name}-{label}-{c}"
            path = SPRITES / "NPC" / name / fname
            arr = load_rgba(path)
            sprites[sid] = dict(id=sid, path=str(path.relative_to(ROOT)).replace("\\", "/"), ppu=200,
                                pivotX=round(pivot[0], 4), pivotY=round(pivot[1], 4),
                                w=arr.shape[1], h=arr.shape[0], arr=arr)
            ids.setdefault(label, []).append(sid)
        out.append(dict(id=name, walkLeft=ids["walk_left"], walkRight=ids["walk_right"],
                        idleLeft=ids["idle_left"][0], idleRight=ids["idle_right"][0]))
    return out


# ============================================================================= LAYOUT
objects, blockers, portals, exits, npcs, birds, smoke = [], [], [], [], [], [], []
shadows = []  # (x, y, w) contact shadows painted into the ground


def obj(sid, x, y, col=None, sway=0.0, swing=False, shadow=None, flip=False, bias=0.0, group=""):
    """Place a sprite with its pivot (feet) at design (x, y). col = (w, h, lift) in tiles."""
    o = dict(sprite=sid, x=x, y=y, sway=sway, swing=swing, flipX=flip, sortBias=bias, group=group,
             colW=0.0, colH=0.0, colX=0.0, colY=0.0)
    if col:
        w, h, lift = col
        o.update(colW=w, colH=h, colX=0.0, colY=lift + h / 2)
    objects.append(o)
    if shadow:
        shadows.append((x, y, shadow))
    return o


def building(sid, cx, feet_y, depth=0.52, door=None, smoke_at=None):
    w, h = size_units(sid)
    obj(sid, cx, feet_y, (w * 0.9, h * depth - 0.35, 0.35), shadow=w * 0.95)
    if smoke_at:
        sx, sy = smoke_at  # chimney top in sprite pixels (from the top-left)
        s = sprites[sid]
        smoke.append(dict(x=cx + (sx - s["w"] / 2) / s["ppu"], y=feet_y - (s["h"] - sy) / s["ppu"]))
    if door is not None:
        return cx - w / 2 + door * w
    return None


def block(x, y, w, h, kind="wall"):
    """Axis-aligned blocker given by its top-left corner in design coordinates."""
    blockers.append(dict(x=x + w / 2, y=y + h / 2, w=w, h=h, kind=kind))


def hole(x, y, rx, ry):
    HOLES.append((x, y, rx, ry))
    block(x - rx * 0.85, y - ry * 0.75, rx * 1.7, ry * 1.5, "hole")


def wall_row(sid, x0, x1, feet_y, gap_every=None):
    w, _ = size_units(sid)
    x = x0 + w / 2
    i = 0
    while x - w / 2 < x1 - 0.5:
        obj(sid if i % 3 != 2 else "muro-gasto", min(x, x1 - w / 2), feet_y, (w * 0.96, 0.6, 0.0),
            shadow=w * 0.9, flip=i % 2 == 1)
        x += w * 0.97
        i += 1


ROADS, COBBLE, PUDDLES, HOLES, GRASSY, YARDS = [], [], [], [], [], []


def layout():
    rng = random.Random(7)
    # --------------------------------------------------------------- ground areas
    ROADS.extend([
        (0, 11.4, 48, 3.9),      # main street (west: Moradias, east: Distrito comercial)
        (20, 0, 4, 11.6),        # road north to the school
        (0, 27.7, 48, 2.6),      # lower lane in front of the houses
        (7.3, 4.2, 3.2, 7.4),    # the alley (beco) of the story
        (2.8, 15, 3.2, 12.9),    # west path joining both streets
        (25, 15, 9.6, 12.8),     # small square with the well
        (11.6, 24.6, 1.4, 3.2),  # Yuuki's gate path
        (20.2, 24.6, 1.4, 3.2),  # Tenebris' door path
        (39.6, 24.6, 1.4, 3.2),
    ])
    COBBLE.extend([(25.3, 15.6, 9.0, 12), (35, 11.5, 13, 3.7), (20.2, 1, 3.6, 5)])
    YARDS.extend([(7.6, 24.8, 8.2, 2.7)])
    PUDDLES.extend([(9.4, 12.5, 0.8, 0.35), (26.4, 14.4, 1.1, 0.4), (41.2, 13.7, 0.7, 0.3),
                    (8.4, 8.2, 0.6, 0.3), (15, 29.2, 0.9, 0.35), (44.5, 32.6, 0.8, 0.35),
                    (22.4, 3.2, 0.7, 0.3), (36.5, 9.6, 0.6, 0.25)])

    # ------------------------------------------------------------ north border
    block(0, 0, 20, 3.4)
    block(24, 0, 24, 3.4)
    for x in (1.2, 4.6, 8.5, 12.4, 16.2, 27, 31, 35, 39.5, 43.2, 46.8):
        obj("arvore" if x not in (8.5, 35) else "arvore-seca", x + rng.uniform(-.3, .3), 3.2 + rng.uniform(-.2, .2),
            (0.9, 0.5, 0.0), sway=1.0 + rng.random() * .6, shadow=2.4)
    # north block: houses fronting the main street
    building("casa-pedra", 4.2, 11.2, smoke_at=None)
    building("oficina", 14.6, 11.2, smoke_at=(355, 20))
    building("casa-velha", 28.8, 11.2, smoke_at=(96, 18))
    building("casa-pedra-gasta", 44.0, 11.2)
    # the alley: dirt floor, cracked walls, crooked fence and stacked crates at the end
    block(6.9, 3.4, 0.5, 8.0)
    block(10.4, 3.4, 0.5, 8.0)
    obj("muro-gasto", 8.9, 4.7, (4.2, 0.6, 0.0), shadow=4)
    block(7.4, 3.4, 3.0, 1.9)
    obj("cerca-torta", 8.9, 5.6, (3.0, 0.45, 0.0), shadow=2.6)
    obj("caixotes", 7.95, 6.4, (1.4, 0.55, 0.0), shadow=1.5)
    obj("caixotes", 9.95, 6.1, (1.4, 0.55, 0.0), shadow=1.5, flip=True)
    obj("entulho-0", 9.6, 8.6)
    obj("mato-3", 7.6, 9.6, sway=6)
    obj("mato-0", 10.1, 7.2, sway=6)
    # vacant lot between the old houses
    obj("arvore-seca", 36.2, 6.8, (0.8, 0.45, 0.0), sway=1.6, shadow=2.2)
    obj("muro-gasto", 34.4, 5.2, (4.2, 0.6, 0.0), shadow=4)
    obj("entulho-1", 38.9, 6.2)
    obj("entulho-2", 33.6, 9.3)
    obj("caixotes", 39.6, 10.4, (1.4, 0.55, 0.0), shadow=1.5)
    hole(38.2, 8.6, 1.25, 0.75)
    for (x, y, k) in ((33.2, 7.2, 0), (35.3, 9.9, 3), (37.4, 10.6, 5), (40.2, 7.8, 1), (32.8, 10.6, 4)):
        obj(f"mato-{k}", x, y, sway=6)

    # --------------------------------------------------------------- main street
    hole(6.2, 13.9, 0.55, 0.35)
    hole(33.2, 12.6, 0.75, 0.42)
    hole(15.6, 14.6, 0.42, 0.28)
    obj("placa", 19.2, 11.9, (0.4, 0.3, 0.0), shadow=0.8)   # "Escola" signpost by the north road
    obj("placa", 26.1, 16.2, (0.4, 0.3, 0.0), shadow=0.8, flip=True)
    obj("entulho-2", 1.6, 15.2)
    obj("mato-1", 24.6, 11.6, sway=6)
    obj("mato-4", 47.3, 15.2, sway=6)

    # ------------------------------------------ south block: low cracked walls on the street
    wall_row("muro", 7.4, 24.8, 16.3)
    wall_row("muro", 35.6, 43.4, 16.3)
    block(7.4, 15.7, 17.4, 8.8)   # behind Yuuki's and Tenebris' houses (roofs, back yards)
    block(35.6, 15.7, 7.8, 8.8)
    # Yuuki's home: old but carefully kept
    door_x = building("casa-yuuki", 11.5, 24.8, depth=0.5, door=0.62, smoke_at=(95, 14))
    obj("cerca-esq", 8.75, 27.45, (2.0, 0.4, 0.0), shadow=2)
    obj("cerca-esq", 10.75, 27.45, (2.0, 0.4, 0.0), shadow=2)
    obj("cerca-dir", 14.05, 27.45, (2.2, 0.4, 0.0), shadow=2)
    obj("cerca-dir", 15.2, 27.4, (1.0, 0.4, 0.0), shadow=1, bias=-0.01)
    obj("horta", 8.9, 26.9, (2.2, 1.0, 0.1))
    obj("caixotes", 15.0, 26.5, (1.3, 0.5, 0.0), shadow=1.4)
    block(7.3, 24.3, 0.3, 3.2)
    block(15.8, 24.3, 0.3, 3.2)
    portals.append(dict(id="porta-casa-yuuki", x=door_x, y=24.95, w=1.0, h=0.4,
                        targetX=ROOM_X0 + 6.5, targetY=8.6, area="casa-yuuki"))
    # Tenebris' family, next door
    building("casa-tenebris", 20.8, 24.8, depth=0.5, smoke_at=None)
    obj("banco", 23.6, 26.5, (1.8, 0.45, 0.0), shadow=1.9)
    obj("mato-2", 17.6, 26.9, sway=6)
    obj("mato-0", 24.6, 25.0, sway=6)
    # small square with the old well
    obj("poco", 29.6, 21.4, (1.9, 0.9, 0.0), shadow=2.2)
    obj("banco", 32.6, 23.8, (1.8, 0.45, 0.0), shadow=1.9)
    obj("arvore", 33.4, 18.4, (0.9, 0.5, 0.0), sway=1.2, shadow=2.4)
    obj("mato-4", 25.6, 26.8, sway=6)
    obj("entulho-0", 34.0, 26.6)
    # house to the east of the square and an empty corner
    building("casa-madeira-gasta", 39.5, 24.8, depth=0.5, smoke_at=(313, 16))
    obj("arvore-seca", 45.6, 21.6, (0.8, 0.45, 0.0), sway=1.8, shadow=2.2)
    obj("entulho-1", 44.4, 25.4)
    obj("caixotes", 46.6, 26.2, (1.4, 0.55, 0.0), shadow=1.5)
    block(43.4, 15.7, 4.6, 3.2)
    obj("mato-5", 44.2, 18.6, sway=6)
    # west path
    obj("arvore-seca", 1.4, 20.6, (0.8, 0.45, 0.0), sway=1.8, shadow=2.2)
    block(0, 15.7, 2.8, 12.0)
    block(6.0, 15.7, 1.3, 8.6)
    obj("mato-1", 6.6, 26.6, sway=6)
    obj("entulho-2", 2.2, 26.8)

    # ------------------------------------------------------ south strip (back lots)
    wall_row("muro", 0, 48, 35.9)
    block(0, 34.9, 48, 1.1)
    obj("varal", 30.7, 32.6, None, shadow=None, group="varal")
    for i, px in enumerate((34, 76, 118, 160, 200)):
        s = sprites["varal"]
        x = 30.7 + (px - s["w"] / 2) / 64
        y = 32.6 - (s["h"] - props.rope_y(px)) / 64
        obj(f"roupa-{i}", x, y, swing=True, sway=10 + i, group="varal")
    block(28.8, 32.35, 0.25, 0.3)
    block(32.5, 32.35, 0.25, 0.3)
    hole(8.6, 32.6, 2.1, 0.7)
    hole(40.4, 31.9, 1.2, 0.8)
    obj("arvore-seca", 3.4, 33.6, (0.8, 0.45, 0.0), sway=1.8, shadow=2.2)
    obj("arvore", 22.6, 34.4, (0.9, 0.5, 0.0), sway=1.2, shadow=2.4)
    obj("caixotes", 17.8, 33.4, (1.4, 0.55, 0.0), shadow=1.5)
    obj("caixotes", 18.9, 33.9, (1.4, 0.55, 0.0), shadow=1.5, flip=True)
    obj("banco", 25.8, 32.2, (1.8, 0.45, 0.0), shadow=1.9)
    obj("entulho-0", 13.6, 33.8)
    obj("entulho-1", 36.6, 33.6)
    obj("entulho-2", 45.8, 33.2)
    for (x, y, k) in ((5.6, 31.2, 0), (12.2, 31.6, 3), (15.4, 34.2, 1), (27.4, 34.4, 5), (34.2, 31.4, 2),
                      (43.3, 34.3, 0), (47.2, 31.0, 3), (20.4, 31.2, 4), (1.0, 31.9, 1)):
        obj(f"mato-{k}", x, y, sway=6)
    # scattered weeds in the dry grass strips and along walls
    for (x, y, k) in ((2.1, 11.0, 0), (19.6, 16.9, 3), (35.0, 16.9, 5), (24.4, 17.4, 1),
                      (30.2, 26.9, 2), (46.0, 11.6, 3), (0.6, 27.3, 4)):
        obj(f"mato-{k}", x, y, sway=6)

    # ------------------------------------------------------------------ exits
    exits.extend([
        dict(id="saida-escola", x=22.0, y=0.9, w=4.0, h=0.8, label="Escola do bairro — em breve"),
        dict(id="saida-moradias", x=0.4, y=13.35, w=0.8, h=3.9, label="Moradias — em breve"),
        dict(id="saida-comercio", x=47.6, y=13.35, w=0.8, h=3.9, label="Distrito comercial — em breve"),
    ])
    block(20, -0.6, 4, 0.8)
    block(-0.6, 11.4, 0.7, 3.9)
    block(47.9, 11.4, 0.7, 3.9)
    block(-0.6, 27.7, 0.7, 2.6)
    block(47.9, 27.7, 0.7, 2.6)

    # ------------------------------------------------------------------- life
    npcs.extend([
        dict(id="morador", variant="morador", scale=1.22, speed=1.3, mode="patrol",
             points=[(3.5, 12.9), (18.5, 12.9), (31, 13.7), (45.5, 13.4)], waitMin=1.5, waitMax=4),
        dict(id="idosa", variant="idosa", scale=1.08, speed=0.7, mode="wander",
             rect=(26.2, 16.9, 6.2, 3.0), waitMin=2, waitMax=6),
        dict(id="crianca-a", variant="crianca-a", scale=0.82, speed=2.3, mode="wander",
             rect=(25.8, 22.6, 5.6, 4.6), waitMin=0.3, waitMax=1.6),
        dict(id="crianca-b", variant="crianca-b", scale=0.8, speed=2.1, mode="wander",
             rect=(25.8, 22.6, 5.6, 4.6), waitMin=0.3, waitMax=1.8),
        dict(id="lavadeira", variant="lavadeira", scale=1.14, speed=0.8, mode="patrol",
             points=[(29.2, 33.5), (32.2, 33.5)], waitMin=3, waitMax=7),
        dict(id="artesao", variant="artesao", scale=1.2, speed=0.9, mode="patrol",
             points=[(12.2, 12.2), (16.6, 12.0)], waitMin=3, waitMax=8),
        dict(id="andarilho", variant="andarilho", scale=1.15, speed=1.1, mode="patrol",
             points=[(1.5, 29.0), (24, 28.8), (46.5, 29.1)], waitMin=2, waitMax=5),
    ])
    birds.extend([dict(x=31.2, y=25.8, count=3), dict(x=22.2, y=13.0, count=4), dict(x=35.4, y=10.4, count=3),
                  dict(x=12.0, y=30.8, count=2)])


def interior_layout():
    X = ROOM_X0
    block(X - 1, -1, ROOM_W + 2, 4.0)            # back wall
    block(X - 1, 0, 1.45, ROOM_H + 1)             # left wall
    block(X + ROOM_W - 0.45, 0, 1.45, ROOM_H + 1)  # right wall
    block(X, ROOM_H - 0.35, 5.9, 1.4)
    block(X + 7.1, ROOM_H - 0.35, 5.9, 1.4)
    block(X + 5.9, ROOM_H + 0.45, 1.2, 0.6)       # behind the door mat
    obj("cama", X + 1.5, 5.6, (1.35, 2.0, 0.0), shadow=1.4)
    obj("estante", X + 4.1, 3.75, (1.6, 0.5, 0.0))
    obj("estante", X + 5.85, 3.75, (1.6, 0.5, 0.0), flip=True)
    obj("livros-0", X + 7.3, 3.9, (0.5, 0.3, 0.0))
    obj("livros-1", X + 1.0, 9.1, (0.5, 0.3, 0.0))
    obj("livros-2", X + 7.75, 4.0)
    obj("mesa", X + 9.3, 7.0, (1.8, 0.8, 0.0), shadow=1.8)
    obj("fogao", X + 11.7, 4.1, (0.9, 0.55, 0.0), shadow=1.0)
    obj("caixotes", X + 11.6, 9.3, (1.3, 0.5, 0.0), shadow=1.3)
    portals.append(dict(id="porta-saida", x=X + 6.5, y=ROOM_H - 0.1, w=1.2, h=0.4,
                        targetX=None, targetY=None, area="rua-de-casa"))


# ============================================================================= GROUND
def rect_mask(rects, h, w, blur, noise_amt, rng, cell=40):
    m = np.zeros((h, w))
    for (x, y, rw, rh) in rects:
        m[int(y * G):int((y + rh) * G), int(x * G):int((x + rw) * G)] = 1
    m = ndi.gaussian_filter(m, blur)
    n = fbm(h, w, cell, rng) - 0.5
    return smoothstep(0.42, 0.58, m + n * noise_amt)


def ellipse_field(h, w, cx, cy, rx, ry, rng, wobble=0.18):
    yy, xx = np.mgrid[0:h, 0:w]
    d = ((xx - cx * G) / (rx * G)) ** 2 + ((yy - cy * G) / (ry * G)) ** 2
    n = value_noise(h, w, 10, rng) - 0.5
    return d + n * wobble * 4


def paint_ground():
    rng = np.random.default_rng(3)
    prng = random.Random(3)
    tex = terrain_textures()
    h, w = MAP_H * G, MAP_W * G
    grass = tile(tex["grass"], h, w)
    dirt = tile(tex["dirt"], h, w, 37, 91)
    cobble = tile(tex["cobble"], h, w, 120, 12)
    # Dry, patchy grass: faded, yellowed, bald patches of earth everywhere.
    dry = desaturate(grass, 0.5) * np.array([1.12, 1.02, 0.74])
    grass = desaturate(grass, 0.25) * np.array([1.0, 0.97, 0.86])
    mix = fbm(h, w, 90, rng)
    ground = grass * (1 - mix[..., None]) + dry * mix[..., None]
    bald = smoothstep(0.55, 0.66, fbm(h, w, 60, rng))
    ground = ground * (1 - bald[..., None]) + (dirt * 0.92) * bald[..., None]

    # Packed-dirt streets with worn tone variation.
    road = rect_mask(ROADS, h, w, 14, 0.55, rng)
    tone = 0.84 + 0.26 * fbm(h, w, 70, rng)
    street = dirt * tone[..., None]
    # Wheel ruts along the main street and the lower lane.
    yy, xx = np.mgrid[0:h, 0:w]
    ruts = np.zeros((h, w))
    for base in (12.9, 14.1, 28.5, 29.4):
        wob = np.sin(xx / G * 0.45 + base) * 0.18 * G + (value_noise(h, w, 80, rng) - 0.5) * 0.4 * G
        dy = np.abs(yy - base * G - wob)
        ruts += np.exp(-(dy / 6) ** 2) * 0.9 - np.exp(-((dy - 9) / 4) ** 2) * 0.25
    lanes = ((yy > 11.4 * G) & (yy < 15.3 * G)) | ((yy > 27.7 * G) & (yy < 30.3 * G))
    ruts *= lanes * (0.6 + 0.4 * value_noise(h, w, 50, rng))
    street *= (1 - ruts[..., None] * 0.2)
    ground = ground * (1 - road[..., None]) + street * road[..., None]

    # Old broken cobbles: stones missing, dirt showing between.
    cob = rect_mask(COBBLE, h, w, 10, 0.6, rng, 30)
    broken = smoothstep(0.4, 0.55, fbm(h, w, 26, rng))
    cob *= broken
    worn_cobble = desaturate(cobble, 0.35) * 0.92
    ground = ground * (1 - cob[..., None]) + worn_cobble * cob[..., None]

    # Swept yard in front of Yuuki's house: lighter, tidier earth.
    yard = rect_mask(YARDS, h, w, 6, 0.2, rng)
    ground = ground * (1 - yard[..., None] * 0.5) + (dirt * 1.08) * yard[..., None] * 0.5

    # Stains, cracks, pebbles and scraps of paper.
    img = Image.fromarray(np.clip(ground, 0, 255).astype(np.uint8))
    over = Image.new("RGBA", img.size, (0, 0, 0, 0))
    d = ImageDraw.Draw(over)
    road_pts = np.argwhere(road > 0.8)
    for _ in range(260):   # cracks in the dry earth
        y, x = road_pts[prng.randrange(len(road_pts))]
        pts = [(x, y)]
        a = prng.uniform(0, math.tau)
        for _ in range(prng.randint(4, 12)):
            a += prng.uniform(-0.8, 0.8)
            x += math.cos(a) * 4
            y += math.sin(a) * 4
            pts.append((x, y))
        d.line(pts, fill=(58, 42, 30, 120), width=1)
    for _ in range(1400):  # pebbles
        y, x = road_pts[prng.randrange(len(road_pts))]
        c = prng.choice([(170, 156, 132), (140, 126, 106), (190, 178, 150)])
        d.rectangle([x, y, x + prng.choice([1, 2]), y + 1], fill=c + (220,))
        d.point((x, y + 2), fill=(50, 38, 28, 140))
    for _ in range(40):    # litter: scraps of paper and straw
        y, x = road_pts[prng.randrange(len(road_pts))]
        if prng.random() < 0.5:
            d.polygon([(x, y), (x + 7, y - 1), (x + 8, y + 5), (x + 1, y + 6)], fill=(214, 204, 178, 230),
                      outline=(130, 120, 100, 200))
        else:
            for _ in range(4):
                d.line([(x, y), (x + prng.randint(-6, 6), y + prng.randint(-2, 2))], fill=(196, 170, 100, 220))
    for _ in range(90):    # dark damp stains
        y, x = road_pts[prng.randrange(len(road_pts))]
        r = prng.randint(6, 18)
        d.ellipse([x - r, y - r * .6, x + r, y + r * .6], fill=(40, 30, 22, 38))
    img = Image.alpha_composite(img.convert("RGBA"), over).convert("RGB")
    ground = np.asarray(img).astype(float)

    # Contact shadows under buildings, walls and props.
    sh = np.zeros((h, w))
    for (x, y, sw) in shadows:
        e = ((xx - x * G) / (sw * G / 2)) ** 2 + ((yy - (y - 0.15) * G) / (0.42 * G)) ** 2
        sh = np.maximum(sh, np.clip(1 - e, 0, 1))
    sh = ndi.gaussian_filter(sh, 5)
    ground *= (1 - sh[..., None] * 0.45)

    # Puddles with sky reflections.
    for (cx, cy, rx, ry) in PUDDLES:
        f = ellipse_field(h, w, cx, cy, rx, ry, rng, 0.12)
        wet = smoothstep(1.9, 1.0, f)
        water = smoothstep(1.05, 0.9, f)
        ground *= (1 - wet[..., None] * 0.28)
        refl = np.array([118, 132, 146]) * (0.75 + 0.35 * smoothstep(cy * G + ry * G, cy * G - ry * G, yy))[..., None]
        ground = ground * (1 - water[..., None] * 0.85) + refl * water[..., None] * 0.85
        glint = water * (np.abs(((xx - yy * 0.6) % 23) - 3) < 1) * 0.5
        ground += glint[..., None] * 60

    # Holes: earthy far wall visible at the top, deep darkness at the bottom, crumbled rim.
    for (cx, cy, rx, ry) in HOLES:
        f = ellipse_field(h, w, cx, cy, rx, ry, rng, 0.14)
        inside = smoothstep(1.02, 0.9, f)
        rim = smoothstep(1.7, 1.05, f) * (1 - inside)
        v = np.clip((yy - (cy - ry) * G) / (2 * ry * G), 0, 1)
        wall = np.array([104, 78, 56]) * (1 - v[..., None] * 0.9)
        deep = np.array([22, 16, 12])
        pit = wall * (1 - smoothstep(0.35, 0.7, v)[..., None]) + deep * smoothstep(0.35, 0.7, v)[..., None]
        ground = ground * (1 - inside[..., None]) + pit * inside[..., None]
        top = rim * (yy < cy * G)
        bottom = rim * (yy >= cy * G)
        ground *= (1 - top[..., None] * 0.35)
        ground = ground * (1 - bottom[..., None] * 0.35) + np.array([176, 150, 116]) * bottom[..., None] * 0.35

    # Global grade: dusty, slightly desaturated afternoon.
    ground = desaturate(ground, 0.12) * np.array([1.03, 0.99, 0.92])
    return np.clip(ground, 0, 255)


def paint_interior():
    rng = np.random.default_rng(9)
    prng = random.Random(9)
    tex = terrain_textures()
    h, w = ROOM_H * G, ROOM_W * G
    wood = tile(tex["wood"], h, w, 11, 5)
    floor = desaturate(wood, 0.22) * (0.8 + 0.2 * fbm(h, w, 50, rng))[..., None] * np.array([0.98, 0.94, 0.88])
    img = Image.fromarray(np.clip(floor, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    # Back wall: vertical planks, baseboard, two windows with daylight.
    wall_h = int(3.0 * G)
    x = 0
    while x < w:
        pw = prng.randint(26, 40)
        c = prng.choice([(120, 88, 60), (112, 82, 56), (128, 94, 64), (104, 76, 52)])
        d.rectangle([x, 0, x + pw, wall_h], fill=c + (255,))
        d.line([(x, 0), (x, wall_h)], fill=(64, 44, 30, 255), width=2)
        for _ in range(3):
            ky = prng.randint(10, wall_h - 20)
            d.ellipse([x + pw / 2 - 2, ky, x + pw / 2 + 2, ky + 5], fill=(84, 60, 40, 255))
        x += pw
    d.rectangle([0, int(0.3 * G), w, int(0.45 * G)], fill=(84, 60, 40, 255))  # beam
    d.rectangle([0, wall_h - 12, w, wall_h], fill=(70, 50, 34, 255))           # baseboard
    for wx in (2.6, 9.6):
        x0, y0 = int(wx * G), int(0.9 * G)
        d.rectangle([x0 - 4, y0 - 4, x0 + 84, y0 + 74], fill=(70, 50, 34, 255))
        d.rectangle([x0, y0, x0 + 80, y0 + 70], fill=(170, 206, 226, 255))
        d.rectangle([x0, y0 + 46, x0 + 80, y0 + 70], fill=(150, 180, 150, 255))  # distant trees
        d.line([(x0 + 40, y0), (x0 + 40, y0 + 70)], fill=(70, 50, 34, 255), width=4)
        d.line([(x0, y0 + 35), (x0 + 80, y0 + 35)], fill=(70, 50, 34, 255), width=4)
        d.rectangle([x0 - 22, y0 - 2, x0 - 5, y0 + 72], fill=(96, 70, 46, 255), outline=(52, 36, 24, 255))
        d.rectangle([x0 + 85, y0 - 2, x0 + 102, y0 + 72], fill=(96, 70, 46, 255), outline=(52, 36, 24, 255))
    # Side walls and front wall with the door.
    d.rectangle([0, 0, int(0.45 * G), h], fill=(76, 54, 36, 255))
    d.rectangle([w - int(0.45 * G), 0, w, h], fill=(76, 54, 36, 255))
    d.rectangle([0, h - int(0.35 * G), w, h], fill=(76, 54, 36, 255))
    dx0, dx1 = int(5.9 * G), int(7.1 * G)
    d.rectangle([dx0, h - int(0.35 * G), dx1, h], fill=(58, 40, 26, 255))
    d.rectangle([dx0 + 8, h - int(0.7 * G), dx1 - 8, h - int(0.36 * G)], fill=(150, 120, 80, 255),
                outline=(100, 76, 50, 255))  # door mat
    # Patched rug in the middle of the room.
    rx0, ry0, rx1, ry1 = int(3.6 * G), int(5.2 * G), int(7.6 * G), int(8.3 * G)
    d.rectangle([rx0, ry0, rx1, ry1], fill=(132, 84, 70, 255), outline=(84, 50, 42, 255))
    d.rectangle([rx0 + 8, ry0 + 8, rx1 - 8, ry1 - 8], outline=(176, 146, 100, 255), width=3)
    for _ in range(3):
        px, py = prng.randint(rx0 + 14, rx1 - 40), prng.randint(ry0 + 14, ry1 - 34)
        c = prng.choice([(120, 132, 110), (150, 120, 90), (110, 110, 140)])
        d.rectangle([px, py, px + 24, py + 18], fill=c + (255,), outline=(70, 60, 50, 255))
    arr = np.asarray(img.convert("RGB")).astype(float)
    # Daylight falling from the windows onto the floor.
    yy, xx = np.mgrid[0:h, 0:w]
    for wx in (2.6, 9.6):
        cx = (wx + 0.62) * G
        beam = np.exp(-(((xx - cx - (yy - 3 * G) * 0.35) / (0.9 * G)) ** 4)) * smoothstep(3 * G, 3.4 * G, yy) * \
            smoothstep(8.5 * G, 4.5 * G, yy)
        arr += beam[..., None] * np.array([40, 34, 18])
    # Soft shadows at the foot of the walls.
    edge = smoothstep(3.6 * G, 3.0 * G, yy) * (yy > 3 * G)
    arr *= (1 - edge[..., None] * 0.35)
    return np.clip(arr, 0, 255)


# ============================================================================= EXPORT
def to_unity(y):
    return round(MAP_H - y, 4)


def export(npc_variants, spawn):
    MAPS.mkdir(parents=True, exist_ok=True)
    Image.fromarray(paint_ground().astype(np.uint8)).save(MAPS / "rua-de-casa_chao.png", optimize=True)
    Image.fromarray(paint_interior().astype(np.uint8)).save(MAPS / "casa-yuuki_chao.png", optimize=True)
    for name, size in (("rua-de-casa_chao", (MAP_W, MAP_H)), ("casa-yuuki_chao", (ROOM_W, ROOM_H))):
        sprites[name] = dict(id=name, path=f"Assets/Game/Bairro/Maps/{name}.png", ppu=G, pivotX=0, pivotY=1,
                             w=size[0] * G, h=size[1] * G)
    exterior_door = next(p for p in portals if p["id"] == "porta-casa-yuuki")
    for p in portals:
        if p["targetX"] is None:
            p["targetX"], p["targetY"] = exterior_door["x"], exterior_door["y"] + 0.95
    data = dict(
        version=1, map="rua-de-casa", name="Rua de Casa",
        sprites=[{k: v for k, v in s.items() if k not in ("arr", "w", "h")} for s in sprites.values()],
        areas=[
            dict(id="rua-de-casa", name="Rua de Casa", x=0, y=0, w=MAP_W, h=MAP_H, ground="rua-de-casa_chao",
                 outdoor=True),
            dict(id="casa-yuuki", name="Casa da Yuuki", x=ROOM_X0, y=MAP_H - ROOM_H, w=ROOM_W, h=ROOM_H,
                 ground="casa-yuuki_chao", outdoor=False),
        ],
        objects=[dict(o, y=to_unity(o["y"])) for o in objects],
        blockers=[dict(b, y=to_unity(b["y"])) for b in blockers],
        portals=[dict(p, y=to_unity(p["y"]), targetY=to_unity(p["targetY"])) for p in portals],
        exits=[dict(e, y=to_unity(e["y"])) for e in exits],
        npcs=[dict(id=n["id"], variant=n["variant"], scale=n["scale"], speed=n["speed"], mode=n["mode"],
                   waitMin=n["waitMin"], waitMax=n["waitMax"],
                   points=[dict(x=p[0], y=to_unity(p[1])) for p in n.get("points", [])],
                   rect=dict(x=n["rect"][0], y=to_unity(n["rect"][1] + n["rect"][3]), w=n["rect"][2],
                             h=n["rect"][3]) if "rect" in n else dict(x=0, y=0, w=0, h=0))
              for n in npcs],
        npcVariants=npc_variants,
        birds=[dict(b, y=to_unity(b["y"])) for b in birds],
        smoke=[dict(x=s["x"], y=to_unity(s["y"]), interior=s.get("interior", False)) for s in smoke],
        player=dict(x=spawn[0], y=to_unity(spawn[1]), area="rua-de-casa"),
        fx=dict(leaves=[f"folha-{i}" for i in range(4)], dust="poeira", paper="papel", cloud="nuvem-sombra",
                smoke="fumaca", pigeon=[f"pombo-{i}" for i in range(4)]),
    )
    (MAPS / "rua-de-casa.json").write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
    return data


def preview(data, scale=24):
    """Compose ground + sprites with Y sorting to check the map without Unity."""
    ground = Image.open(MAPS / "rua-de-casa_chao.png").convert("RGBA")
    k = scale / G
    canvas = ground.resize((int(ground.width * k), int(ground.height * k)), Image.LANCZOS)
    room = Image.open(MAPS / "casa-yuuki_chao.png").convert("RGBA")
    room = room.resize((int(room.width * k), int(room.height * k)), Image.LANCZOS)
    full = Image.new("RGBA", (canvas.width + room.width + scale * 2, canvas.height), (12, 12, 14, 255))
    full.alpha_composite(canvas)
    ox_room = canvas.width + scale * 2
    full.alpha_composite(room, (ox_room, 0))
    varal_y = {o["group"]: o["y"] for o in data["objects"] if o["sprite"] == "varal"}
    draw_list = [((varal_y[o["group"]] - 0.001) if o.get("swing") else o["y"], o) for o in data["objects"]]
    for n in data["npcs"]:
        p = n["points"][0] if n["points"] else dict(x=n["rect"]["x"] + n["rect"]["w"] / 2,
                                                   y=n["rect"]["y"] + n["rect"]["h"] / 2)
        v = next(v for v in data["npcVariants"] if v["id"] == n["variant"])
        draw_list.append((p["y"], dict(sprite=v["walkRight"][1], x=p["x"], y=p["y"], scale=n["scale"])))
    draw_list.append((data["player"]["y"], dict(sprite="__yuuki", x=data["player"]["x"], y=data["player"]["y"])))
    yuuki = Image.open(ROOT / "Assets/Game/Art/Yuuki/Yuuki_Idle_2x1.png").convert("RGBA").crop((512, 0, 1024, 512))
    for _, o in sorted(draw_list, key=lambda t: -t[0]):
        if o["sprite"] == "__yuuki":
            im, ppu, pv, sc = yuuki, 200, (0.5, 112 / 512), 1.15
        else:
            s = sprites[o["sprite"]]
            im = Image.open(ROOT / s["path"]).convert("RGBA")
            ppu, pv, sc = s["ppu"], (s["pivotX"], s["pivotY"]), o.get("scale", 1.0)
            if o.get("flipX"):
                im = im.transpose(Image.FLIP_LEFT_RIGHT)
        f = scale / ppu * sc
        im = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))), Image.LANCZOS)
        ux, uy = o["x"], o["y"]
        if ux >= ROOM_X0:
            px = ox_room + (ux - ROOM_X0) * scale
            py = (MAP_H - uy) * scale
        else:
            px, py = ux * scale, (MAP_H - uy) * scale
        full.alpha_composite(im, (int(px - pv[0] * im.width), int(py - (1 - pv[1]) * im.height)))
    out = ROOT / "docs/bairro/rua-de-casa-preview.png"
    out.parent.mkdir(parents=True, exist_ok=True)
    full.convert("RGB").save(out, optimize=True)
    return out


def main():
    build_sprites()
    variants = build_npcs()
    layout()
    interior_layout()
    door = next(p for p in portals if p["id"] == "porta-casa-yuuki")
    data = export(variants, (door["x"], door["y"] + 1.0))
    out = preview(data)
    print(f"{len(sprites)} sprites, {len(objects)} objects, {len(blockers)} blockers, {len(npcs)} NPCs -> {out}")


if __name__ == "__main__":
    main()
