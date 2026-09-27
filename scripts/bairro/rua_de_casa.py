"""Map 1 of the bairro: "Rua de Casa", Yuuki's street, plus the interior of her house.

Houses of Yuuki and Tenebris (neighbours), the alley of the story, the well square and the
exits to the other three maps (school north, Moradias west, commercial district east).
"""
import random

import numpy as np
from PIL import Image, ImageDraw

from common import fbm, smoothstep, tile, desaturate, terrain_textures
from assets import G
from mapkit import MapLayout
import moradias

MAP_W, MAP_H = 48, 36
ROOM_X0, ROOM_W, ROOM_H = 80, 13, 10  # the interior lives far to the right of the street


def layout(m):
    rng = random.Random(7)
    # --------------------------------------------------------------- ground areas
    m.roads.extend([
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
    m.cobble.extend([(25.3, 15.6, 9.0, 12), (35, 11.5, 13, 3.7), (20.2, 1, 3.6, 5)])
    m.yards.extend([(7.6, 24.8, 8.2, 2.7)])
    m.puddles.extend([(9.4, 12.5, 0.8, 0.35), (26.4, 14.4, 1.1, 0.4), (41.2, 13.7, 0.7, 0.3),
                    (8.4, 8.2, 0.6, 0.3), (15, 29.2, 0.9, 0.35), (44.5, 32.6, 0.8, 0.35),
                    (22.4, 3.2, 0.7, 0.3), (36.5, 9.6, 0.6, 0.25)])

    # ------------------------------------------------------------ north border
    m.block(0, 0, 20, 3.4)
    m.block(24, 0, 24, 3.4)
    for x in (1.2, 4.6, 8.5, 12.4, 16.2, 27, 31, 35, 39.5, 43.2, 46.8):
        m.obj("arvore" if x not in (8.5, 35) else "arvore-seca", x + rng.uniform(-.3, .3), 3.2 + rng.uniform(-.2, .2),
            (0.9, 0.5, 0.0), sway=1.0 + rng.random() * .6, shadow=2.4)
    # north block: houses fronting the main street
    m.building("casa-pedra", 4.2, 11.2, smoke_at=None)
    m.building("oficina", 14.6, 11.2, smoke_at=(355, 20))
    m.building("casa-velha", 28.8, 11.2, smoke_at=(96, 18))
    m.building("casa-pedra-gasta", 44.0, 11.2)
    # the alley: dirt floor, cracked walls, crooked fence and stacked crates at the end
    m.block(6.9, 3.4, 0.5, 8.0)
    m.block(10.4, 3.4, 0.5, 8.0)
    m.obj("muro-gasto", 8.9, 4.7, (4.2, 0.6, 0.0), shadow=4)
    m.block(7.4, 3.4, 3.0, 1.9)
    m.obj("cerca-torta", 8.9, 5.6, (3.0, 0.45, 0.0), shadow=2.6)
    m.obj("caixotes", 7.95, 6.4, (1.4, 0.55, 0.0), shadow=1.5)
    m.obj("caixotes", 9.95, 6.1, (1.4, 0.55, 0.0), shadow=1.5, flip=True)
    m.obj("entulho-0", 9.6, 8.6)
    m.obj("mato-3", 7.6, 9.6, sway=6)
    m.obj("mato-0", 10.1, 7.2, sway=6)
    # vacant lot between the old houses
    m.obj("arvore-seca", 36.2, 6.8, (0.8, 0.45, 0.0), sway=1.6, shadow=2.2)
    m.obj("muro-gasto", 34.4, 5.2, (4.2, 0.6, 0.0), shadow=4)
    m.obj("entulho-1", 38.9, 6.2)
    m.obj("entulho-2", 33.6, 9.3)
    m.obj("caixotes", 39.6, 10.4, (1.4, 0.55, 0.0), shadow=1.5)
    m.hole(38.2, 8.6, 1.25, 0.75)
    for (x, y, k) in ((33.2, 7.2, 0), (35.3, 9.9, 3), (37.4, 10.6, 5), (40.2, 7.8, 1), (32.8, 10.6, 4)):
        m.obj(f"mato-{k}", x, y, sway=6)

    # --------------------------------------------------------------- main street
    m.hole(6.2, 13.9, 0.55, 0.35)
    m.hole(33.2, 12.6, 0.75, 0.42)
    m.hole(15.6, 14.6, 0.42, 0.28)
    m.obj("placa", 19.2, 11.9, (0.4, 0.3, 0.0), shadow=0.8)   # "Escola" signpost by the north road
    m.obj("placa", 26.1, 16.2, (0.4, 0.3, 0.0), shadow=0.8, flip=True)
    m.obj("entulho-2", 1.6, 15.2)
    m.obj("mato-1", 24.6, 11.6, sway=6)
    m.obj("mato-4", 47.3, 15.2, sway=6)

    # ------------------------------------------ south block: low cracked walls on the street
    m.wall_row("muro", 7.4, 24.8, 16.3)
    m.wall_row("muro", 35.6, 43.4, 16.3)
    m.block(7.4, 15.7, 17.4, 8.8)   # behind Yuuki's and Tenebris' houses (roofs, back yards)
    m.block(35.6, 15.7, 7.8, 8.8)
    # Yuuki's home: old but carefully kept
    door_x = m.building("casa-yuuki", 11.5, 24.8, depth=0.5, door=0.62, smoke_at=(95, 14))
    m.obj("cerca-esq", 8.75, 27.45, (2.0, 0.4, 0.0), shadow=2)
    m.obj("cerca-esq", 10.75, 27.45, (2.0, 0.4, 0.0), shadow=2)
    m.obj("cerca-dir", 14.05, 27.45, (2.2, 0.4, 0.0), shadow=2)
    m.obj("cerca-dir", 15.2, 27.4, (1.0, 0.4, 0.0), shadow=1)
    m.obj("horta", 8.9, 26.9, (2.2, 1.0, 0.1))
    m.obj("caixotes", 15.0, 26.5, (1.3, 0.5, 0.0), shadow=1.4)
    m.block(7.3, 24.3, 0.3, 3.2)
    m.block(15.8, 24.3, 0.3, 3.2)
    m.portals.append(dict(id="porta-casa-yuuki", x=door_x, y=24.95, w=1.0, h=0.4,
                        targetX=ROOM_X0 + 6.5, targetY=8.6, area="casa-yuuki"))
    # Tenebris' family, next door
    m.building("casa-tenebris", 20.8, 24.8, depth=0.5, smoke_at=None)
    m.obj("banco", 23.6, 26.5, (1.8, 0.45, 0.0), shadow=1.9)
    m.obj("mato-2", 17.6, 26.9, sway=6)
    m.obj("mato-0", 24.6, 25.0, sway=6)
    # small square with the old well
    m.obj("poco", 29.6, 21.4, (1.9, 0.9, 0.0), shadow=2.2)
    m.obj("banco", 32.6, 23.8, (1.8, 0.45, 0.0), shadow=1.9)
    m.obj("arvore", 33.4, 18.4, (0.9, 0.5, 0.0), sway=1.2, shadow=2.4)
    m.obj("mato-4", 25.6, 26.8, sway=6)
    m.obj("entulho-0", 34.0, 26.6)
    # house to the east of the square and an empty corner
    m.building("casa-madeira-gasta", 39.5, 24.8, depth=0.5, smoke_at=(313, 16))
    m.obj("arvore-seca", 45.6, 21.6, (0.8, 0.45, 0.0), sway=1.8, shadow=2.2)
    m.obj("entulho-1", 44.4, 25.4)
    m.obj("caixotes", 46.6, 26.2, (1.4, 0.55, 0.0), shadow=1.5)
    m.block(43.4, 15.7, 4.6, 3.2)
    m.obj("mato-5", 44.2, 18.6, sway=6)
    # west path
    m.obj("arvore-seca", 1.4, 20.6, (0.8, 0.45, 0.0), sway=1.8, shadow=2.2)
    m.block(0, 15.7, 2.8, 12.0)
    m.block(6.0, 15.7, 1.3, 8.6)
    m.obj("mato-1", 6.6, 26.6, sway=6)
    m.obj("entulho-2", 2.2, 26.8)

    # ------------------------------------------------------ south strip (back lots)
    m.wall_row("muro", 0, 48, 35.9)
    m.block(0, 34.9, 48, 1.1)
    m.laundry_line(30.7, 32.6, "varal")
    m.hole(8.6, 32.6, 2.1, 0.7)
    m.hole(40.4, 31.9, 1.2, 0.8)
    m.obj("arvore-seca", 3.4, 33.6, (0.8, 0.45, 0.0), sway=1.8, shadow=2.2)
    m.obj("arvore", 22.6, 34.4, (0.9, 0.5, 0.0), sway=1.2, shadow=2.4)
    m.obj("caixotes", 17.8, 33.4, (1.4, 0.55, 0.0), shadow=1.5)
    m.obj("caixotes", 18.9, 33.9, (1.4, 0.55, 0.0), shadow=1.5, flip=True)
    m.obj("banco", 25.8, 32.2, (1.8, 0.45, 0.0), shadow=1.9)
    m.obj("entulho-0", 13.6, 33.8)
    m.obj("entulho-1", 36.6, 33.6)
    m.obj("entulho-2", 45.8, 33.2)
    for (x, y, k) in ((5.6, 31.2, 0), (12.2, 31.6, 3), (15.4, 34.2, 1), (27.4, 34.4, 5), (34.2, 31.4, 2),
                      (43.3, 34.3, 0), (47.2, 31.0, 3), (20.4, 31.2, 4), (1.0, 31.9, 1)):
        m.obj(f"mato-{k}", x, y, sway=6)
    # scattered weeds in the dry grass strips and along walls
    for (x, y, k) in ((2.1, 11.0, 0), (19.6, 16.9, 3), (35.0, 16.9, 5), (24.4, 17.4, 1),
                      (30.2, 26.9, 2), (46.0, 11.6, 3), (0.6, 27.3, 4)):
        m.obj(f"mato-{k}", x, y, sway=6)

    # ------------------------------------------------------------------ exits
    m.exits.extend([
        dict(id="saida-escola", x=22.0, y=0.9, w=4.0, h=0.8, label="Escola do bairro — em breve",
             targetMap="", targetX=0, targetY=0),
        dict(id="saida-moradias", x=0.4, y=13.35, w=0.8, h=3.9, label="Moradias",
             targetMap="Bairro_Moradias", targetX=moradias.ENTRY[0], targetY=moradias.ENTRY[1]),
        dict(id="saida-comercio", x=47.6, y=13.35, w=0.8, h=3.9, label="Distrito comercial — em breve",
             targetMap="", targetX=0, targetY=0),
    ])
    m.block(20, -0.6, 4, 0.8)
    m.block(-0.6, 11.4, 0.7, 3.9)
    m.block(47.9, 11.4, 0.7, 3.9)
    m.block(-0.6, 27.7, 0.7, 2.6)
    m.block(47.9, 27.7, 0.7, 2.6)

    # ------------------------------------------------------------------- life
    m.npcs.extend([
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
    m.birds.extend([dict(x=31.2, y=25.8, count=3), dict(x=22.2, y=13.0, count=4), dict(x=35.4, y=10.4, count=3),
                  dict(x=12.0, y=30.8, count=2)])


def interior_layout(m):
    X = ROOM_X0
    m.block(X - 1, -1, ROOM_W + 2, 4.0)            # back wall
    m.block(X - 1, 0, 1.45, ROOM_H + 1)             # left wall
    m.block(X + ROOM_W - 0.45, 0, 1.45, ROOM_H + 1)  # right wall
    m.block(X, ROOM_H - 0.35, 5.9, 1.4)
    m.block(X + 7.1, ROOM_H - 0.35, 5.9, 1.4)
    m.block(X + 5.9, ROOM_H + 0.45, 1.2, 0.6)       # behind the door mat
    m.obj("cama", X + 1.5, 5.6, (1.35, 2.0, 0.0), shadow=1.4)
    m.obj("estante", X + 4.1, 3.75, (1.6, 0.5, 0.0))
    m.obj("estante", X + 5.85, 3.75, (1.6, 0.5, 0.0), flip=True)
    m.obj("livros-0", X + 7.3, 3.9, (0.5, 0.3, 0.0))
    m.obj("livros-1", X + 1.0, 9.1, (0.5, 0.3, 0.0))
    m.obj("livros-2", X + 7.75, 4.0)
    m.obj("mesa", X + 9.3, 7.0, (1.8, 0.8, 0.0), shadow=1.8)
    m.obj("fogao", X + 11.7, 4.1, (0.9, 0.55, 0.0), shadow=1.0)
    m.obj("caixotes", X + 11.6, 9.3, (1.3, 0.5, 0.0), shadow=1.3)
    door = next(p for p in m.portals if p["id"] == "porta-casa-yuuki")
    m.portals.append(dict(id="porta-saida", x=X + 6.5, y=ROOM_H - 0.1, w=1.2, h=0.4,
                          targetX=door["x"], targetY=door["y"] + 0.95, area="rua-de-casa"))


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


def build():
    m = MapLayout("rua-de-casa", "Rua de Casa", "Bairro_RuaDeCasa", MAP_W, MAP_H, seed=3)
    m.ruts = [(12.9, (11.4, 15.3)), (14.1, (11.4, 15.3)), (28.5, (27.7, 30.3)), (29.4, (27.7, 30.3))]
    layout(m)
    interior_layout(m)
    m.extra_areas.append(dict(id="casa-yuuki", name="Casa da Yuuki", x=ROOM_X0, y=0, w=ROOM_W, h=ROOM_H,
                              painter=paint_interior))
    door = next(p for p in m.portals if p["id"] == "porta-casa-yuuki")
    m.spawn = (door["x"], door["y"] + 1.0)
    return m
