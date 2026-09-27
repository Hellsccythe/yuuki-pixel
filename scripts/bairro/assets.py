"""Shared sprite set of the neighbourhood (buildings, props, FX, placeholder NPCs).

Every map of the bairro references these sprites by id; build_bairro.py regenerates them
once and then lays out each map.
"""
import shutil

import numpy as np
from PIL import Image

from common import ROOT, OUT, WORLD_ART, load_rgba, save_rgba, crop_alpha, weather, board_window
import props
import props_moradias as pm

G = 64  # ground pixels per tile
SPRITES = OUT / "Sprites"
MAPS = OUT / "Maps"

sprites = {}  # id -> dict(id, path, ppu, pivotX, pivotY, w, h)


def register(sid, arr, ppu, pivot=(0.5, 0.0), group="Props"):
    path = SPRITES / group / f"{sid}.png"
    save_rgba(arr, path)
    sprites[sid] = dict(id=sid, path=str(path.relative_to(ROOT)).replace("\\", "/"), ppu=ppu,
                        pivotX=round(pivot[0], 4), pivotY=round(pivot[1], 4),
                        w=arr.shape[1], h=arr.shape[0])
    return sid


def register_ground(sid, path, w_tiles, h_tiles):
    sprites[sid] = dict(id=sid, path=str(path.relative_to(ROOT)).replace("\\", "/"), ppu=G, pivotX=0, pivotY=1,
                        w=w_tiles * G, h=h_tiles * G)


def size_units(sid):
    s = sprites[sid]
    return s["w"] / s["ppu"], s["h"] / s["ppu"]


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
    a = weather(art["timber-house"], 18, desat=0.3, darken=0.1, grime=0.7, cracks=8)
    a = pm.abandoned(a, 18)
    a = board_window(a, (196, 400, 246, 468), 18)  # door nailed shut
    register("casa-abandonada", a, 60, feet(a), b)
    # Plank shacks with patched tin roofs (Moradias).
    for i, (w, curtain, pipe, lean) in enumerate([(4.4, False, True, False), (3.6, True, False, False),
                                                   (5.0, False, False, True), (4.0, True, True, False),
                                                   (3.8, False, False, False), (4.6, True, False, True)]):
        a, pivot_y = pm.shack(200 + i, w, curtain_door=curtain, stovepipe=pipe, lean_to=lean)
        # Pivot on the stone step line; lean-to shacks are offset by their extra 70px on the left.
        px = ((a.shape[1] - 70) / 2 + 70) / a.shape[1] if lean else 0.5
        register(f"barraco-{i}", a, 60, (px, 1 - pivot_y), b)

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
    for i, kind in enumerate(["sheet", "shirt", "pants", "towel", "shirt", "sheet", "pants", "towel"]):
        a = props.laundry(kind, 70 + i)
        register(f"roupa-{i}", a, 64, (0.5, 1.0))  # pivot at the pegs so cloth swings
    for name, fn, seed, ppu in (("lenha", pm.woodpile, 110, 64), ("lixo", pm.trash_heap, 111, 64),
                                ("carroca-quebrada", pm.broken_cart, 112, 64), ("barris-agua", pm.water_barrels, 113, 64),
                                ("galinheiro", pm.chicken_coop, 114, 46)):
        a = fn(seed)
        register(name, a, ppu, (0.5, 3 / a.shape[0]))
    a = pm.trash_heap(115)
    register("lixo-2", a, 64, (0.5, 3 / a.shape[0]))

    # --- interior
    for name, ppu in (("cama", 150), ("estante", 140), ("mesa", 140)):
        src = {"cama": "bed", "estante": "bookshelf", "mesa": "table"}[name]
        a = weather(art[src], 80 + len(name), desat=0.15, darken=0.03, grime=0.2, cracks=0)
        register(name, a, ppu, feet(a), "Interior")
    for i in range(3):
        register(f"livros-{i}", props.book_pile(90 + i), 64, (0.5, 2 / 34), "Interior")
    register("fogao", props.stove(), 64, (0.5, 2 / 110), "Interior")

    # --- FX and animals
    for i, f in enumerate(props.pigeon_frames()):
        register(f"pombo-{i}", f, 64, (0.5, 0.05), "FX")
    for c, (name, col) in enumerate((("branca", (236, 230, 214)), ("ruiva", (176, 108, 58)),
                                     ("carijo", (132, 124, 116)))):
        for i, f in enumerate(pm.chicken_frames(col, 120 + c)):
            register(f"galinha-{name}-{i}", f, 54, (0.5, 2 / 24), "FX")
    for i in range(4):
        register(f"folha-{i}", props.leaf(100 + i), 64, (0.5, 0.5), "FX")
    register("poeira", props.dust(), 64, (0.5, 0.5), "FX")
    register("papel", props.paper(), 64, (0.5, 0.5), "FX")
    register("nuvem-sombra", props.soft_blob(420, 260, (18, 20, 34), 255, 26), 26, (0.5, 0.5), "FX")
    register("fumaca", props.smoke_puff(), 64, (0.5, 0.5), "FX")


NPC_TINTS = {
    "morador": (150, 118, 88), "idosa": (170, 164, 156), "crianca-a": (132, 146, 104),
    "crianca-b": (120, 138, 160), "lavadeira": (168, 120, 106), "artesao": (126, 100, 80),
    "andarilho": (142, 140, 124), "idoso": (136, 128, 118), "vizinha": (160, 136, 110),
    "crianca-c": (156, 118, 112),
}


def build_npcs():
    atlas = load_rgba(ROOT / "Assets/Game/Art/Yuuki/Yuuki_Movement_6x6.png")
    idle = load_rgba(ROOT / "Assets/Game/Art/Yuuki/Yuuki_Idle_2x1.png")
    out = []
    for name, tint in NPC_TINTS.items():
        frames, pivot = props.npc_silhouettes(atlas, idle, tint, name, SPRITES / "NPC")
        ids = {}
        for label, c, fname in frames:
            sid = f"npc-{name}-{label}-{c}"
            path = SPRITES / "NPC" / name / fname
            h, w = load_rgba(path).shape[:2]
            sprites[sid] = dict(id=sid, path=str(path.relative_to(ROOT)).replace("\\", "/"), ppu=200,
                                pivotX=round(pivot[0], 4), pivotY=round(pivot[1], 4), w=w, h=h)
            ids.setdefault(label, []).append(sid)
        out.append(dict(id=name, walkLeft=ids["walk_left"], walkRight=ids["walk_right"],
                        idleLeft=ids["idle_left"][0], idleRight=ids["idle_right"][0]))
    return out


FX = dict(leaves=[f"folha-{i}" for i in range(4)], dust="poeira", paper="papel", cloud="nuvem-sombra",
          smoke="fumaca", pigeon=[f"pombo-{i}" for i in range(4)])

CHICKENS = {name: [f"galinha-{name}-{i}" for i in range(4)] for name in ("branca", "ruiva", "carijo")}
