"""The small dungeon under the suburbs ("Ossário Esquecido").

Reached by the hidden stairs in the abandoned corner of the Moradias. Five cramped spaces:
the entrance with the stairs back up, a corridor, the ossuary hall (bones, chains, a charred
angel wing, a locked cell), the alcove of the broken altar with its circle of candles and a
flooded side room. Only torches light it. Built from the Codex dungeon set
(Assets/Game/Resources/Environment).
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from common import ROOT, fbm, value_noise, smoothstep, tile, desaturate
from assets import env_info, size_units, env
from mapkit import MapLayout

MAP_W, MAP_H = 40, 28
ENTRY = (6.3, 22.9)            # arriving from the Moradias stairs

# Floors (x, y, w, h) in tiles, y down.
ENTRANCE = (3, 16, 8, 8)
STAIRS = (5.2, 24, 2.2, 3.4)
CORRIDOR_WEST = (11, 19, 5, 2.2)
HALL = (16, 12, 12.3, 11)
CELL = (24.4, 9.2, 2.5, 2.8)
CORRIDOR_NORTH = (19.1, 8, 2.2, 4.2)
ALTAR = (14.2, 4.4, 9.3, 3.8)
CORRIDOR_EAST = (28.3, 16, 3.7, 2.2)
FLOODED = (32, 13, 6, 8)
FLAGSTONES = [HALL, ALTAR, CORRIDOR_NORTH]
DIRT = [ENTRANCE, CORRIDOR_WEST, CELL, CORRIDOR_EAST, FLOODED]
WALKABLE = [ENTRANCE, (5.2, 24, 2.2, 1.1), CORRIDOR_WEST, HALL, CORRIDOR_NORTH, ALTAR, CORRIDOR_EAST, FLOODED]

TORCH = dict(radius=5.2, intensity=1.15, color=(1.0, 0.6, 0.28), flicker=0.55)


def north_wall(m, x0, x1, y, gaps=(), group_prefix="n"):
    """Wall faces standing on the top edge of a floor, filling the stretches between openings."""
    sid = env("parede-dungeon")
    w, _ = size_units(sid)
    cuts = sorted(gaps)
    stretches, start = [], x0
    for g0, g1 in cuts:
        stretches.append((start, g0))
        start = g1
    stretches.append((start, x1))
    segments, i = [], 0
    for a, b in stretches:
        length = b - a
        if length < 0.4:
            continue
        n = max(1, int(round(length / (w * 0.95))))
        centers = [(a + b) / 2] if n == 1 else [a + w / 2 + k * (length - w) / (n - 1) for k in range(n)]
        for cx in centers:
            group = f"{group_prefix}{i}"
            m.obj(sid, cx, y, None, flip=i % 2 == 1, group=group)
            segments.append((cx, group))
            i += 1
    return segments


def side_wall(m, x, y0, y1, gaps=()):
    sid = env("parede-vertical")
    y = y0 + 1.0
    while y <= y1 + 0.45:
        if not any(g0 - 0.2 < y < g1 + 1.1 for g0, g1 in gaps):
            m.obj(sid, x, y, None)
        y += 1.0


def wall_decor(m, segments, index, asset, dy, light=None, dx=0.0):
    """Hang a piece (torch, chains, web) on the face of a wall segment, drawn in front of it.

    A torch lights the floor in front of the wall, so its light sits below the flame.
    """
    cx, group = segments[index % len(segments)]
    wall_y = m_y(group, m)
    sid = "tocha-parede" if asset == "tocha" else env(asset)
    m.obj(sid, cx + dx, wall_y - dy, None, group=group, order=1)
    if light:
        m.light(cx + dx, wall_y + 0.7, radius=light["radius"], intensity=light["intensity"], color=light["color"],
                flicker=light["flicker"], night=False)


def m_y(group, m):
    for o in m.objects:
        if o["group"] == group:
            return o["y"]
    raise KeyError(group)


def layout(m, moradias_door):
    rng = random.Random(51)
    m.block_outside(WALKABLE)

    # ------------------------------------------------------------------ walls
    entrance = north_wall(m, ENTRANCE[0], ENTRANCE[0] + ENTRANCE[2], ENTRANCE[1], group_prefix="a")
    corridor = north_wall(m, CORRIDOR_WEST[0], CORRIDOR_WEST[0] + CORRIDOR_WEST[2], CORRIDOR_WEST[1], group_prefix="c")
    hall = north_wall(m, HALL[0], HALL[0] + HALL[2], HALL[1],
                      gaps=[(CORRIDOR_NORTH[0], CORRIDOR_NORTH[0] + CORRIDOR_NORTH[2]), (CELL[0], CELL[0] + CELL[2])],
                      group_prefix="h")
    altar = north_wall(m, ALTAR[0], ALTAR[0] + ALTAR[2], ALTAR[1], group_prefix="t")
    cell = north_wall(m, CELL[0], CELL[0] + CELL[2], CELL[1], group_prefix="k")
    east = north_wall(m, CORRIDOR_EAST[0], CORRIDOR_EAST[0] + CORRIDOR_EAST[2], CORRIDOR_EAST[1], group_prefix="e")
    flooded = north_wall(m, FLOODED[0], FLOODED[0] + FLOODED[2], FLOODED[1], group_prefix="f")
    # Side walls (x just outside the floor), leaving the openings of the corridors.
    side_wall(m, ENTRANCE[0] - 0.55, ENTRANCE[1], ENTRANCE[1] + ENTRANCE[3])
    side_wall(m, ENTRANCE[0] + ENTRANCE[2] + 0.55, ENTRANCE[1], ENTRANCE[1] + ENTRANCE[3],
              gaps=[(CORRIDOR_WEST[1], CORRIDOR_WEST[1] + CORRIDOR_WEST[3])])
    side_wall(m, HALL[0] - 0.55, HALL[1], HALL[1] + HALL[3], gaps=[(CORRIDOR_WEST[1], CORRIDOR_WEST[1] + CORRIDOR_WEST[3])])
    side_wall(m, HALL[0] + HALL[2] + 0.55, HALL[1], HALL[1] + HALL[3],
              gaps=[(CORRIDOR_EAST[1], CORRIDOR_EAST[1] + CORRIDOR_EAST[3])])
    side_wall(m, CORRIDOR_NORTH[0] - 0.55, ALTAR[1] + ALTAR[3], HALL[1])
    side_wall(m, CORRIDOR_NORTH[0] + CORRIDOR_NORTH[2] + 0.55, ALTAR[1] + ALTAR[3], HALL[1])
    side_wall(m, ALTAR[0] - 0.55, ALTAR[1], ALTAR[1] + ALTAR[3])
    side_wall(m, ALTAR[0] + ALTAR[2] + 0.55, ALTAR[1], ALTAR[1] + ALTAR[3])
    side_wall(m, FLOODED[0] - 0.55, FLOODED[1], FLOODED[1] + FLOODED[3],
              gaps=[(CORRIDOR_EAST[1], CORRIDOR_EAST[1] + CORRIDOR_EAST[3])])
    side_wall(m, FLOODED[0] + FLOODED[2] + 0.55, FLOODED[1], FLOODED[1] + FLOODED[3])

    # --------------------------------------------------------------- torches
    wall_decor(m, entrance, 1, "tocha", 1.15, TORCH)
    wall_decor(m, corridor, 0, "tocha", 1.15, TORCH, dx=0.4)
    for i in (0, len(hall) - 1):
        wall_decor(m, hall, i, "tocha", 1.15, TORCH)
    wall_decor(m, altar, 0, "tocha", 1.15, TORCH, dx=-0.3)
    wall_decor(m, altar, len(altar) - 1, "tocha", 1.15, TORCH, dx=0.3)
    wall_decor(m, flooded, 1, "tocha", 1.15, dict(TORCH, radius=4.4, intensity=0.95))
    # Stairs: a thin cold light falling from the surface.
    m.light(6.3, 24.2, radius=4.0, intensity=0.9, color=(0.62, 0.72, 0.95), flicker=0.05, night=False)

    # ---------------------------------------------------------- the entrance
    wall_decor(m, entrance, 0, "teia", 1.75, dx=-0.6)
    m.env("ossos", 9.2, 22.6)
    m.env("penas", 4.4, 18.6)
    m.stairs(6.3, 24.4, "Subir a escada", "Moradias", "Bairro_Moradias", moradias_door, radius=1.2)

    # ------------------------------------------------------------ the ossuary
    wall_decor(m, hall, 1, "correntes", 1.05)
    wall_decor(m, hall, 3 if len(hall) > 3 else 1, "correntes", 1.05, dx=0.3)
    m.env("asa-carbonizada", 17.6, 13.8)
    m.inspect(17.8, 14.3, "Asa carbonizada", "Uma asa inteira, queimada até as penas virarem carvão. "
              "Teias cobrem os ossos finos.", radius=1.2)
    m.env("simbolo-apagado", 22.0, 17.6)
    m.inspect(22.0, 17.4, "Símbolo apagado", "Um halo quebrado e duas asas cortadas, riscados no chão com "
              "alguma coisa pontuda.", radius=1.2)
    for (x, y) in ((25.8, 21.8), (19.0, 21.4), (26.6, 14.6)):
        m.env("ossos", x, y)
    m.env("penas", 20.6, 15.0)
    m.env("poca", 17.8, 19.6)
    m.env("velas", 24.4, 19.2)
    m.light(24.4, 18.6, radius=3.0, intensity=0.8, color=(1.0, 0.78, 0.48), flicker=0.35, night=False)
    # The locked cell behind the bars.
    m.env("grade-dungeon", CELL[0] + CELL[2] / 2, HALL[1] + 0.05)
    m.block(CELL[0] - 0.2, HALL[1] - 0.45, CELL[2] + 0.4, 0.5)
    m.inspect(CELL[0] + CELL[2] / 2, HALL[1] + 0.5, "Grade trancada", "A fechadura enferrujou por dentro. "
              "Lá atrás, correntes presas à parede e ossos pequenos demais.", radius=1.2)
    wall_decor(m, cell, 0, "correntes", 1.0)
    m.env("ossos", CELL[0] + 1.5, CELL[1] + 2.2)

    # -------------------------------------------------------- the broken altar
    m.env("altar", 18.9, 6.6)
    m.inspect(18.9, 7.2, "Altar partido", "A pedra foi quebrada a marteladas. Restos de velas derretidas e "
              "ossos arrumados em círculo, como numa oração ao contrário.", radius=1.3)
    m.env("velas", 16.2, 7.7)
    m.light(16.2, 7.2, radius=3.2, intensity=0.9, color=(1.0, 0.78, 0.48), flicker=0.35, night=False)
    wall_decor(m, altar, 1, "teia", 1.75, dx=0.8)
    m.env("penas", 21.6, 7.6)

    # -------------------------------------------------------- the flooded room
    m.env("poca", 34.2, 16.2)
    m.env("poca", 36.4, 19.4)
    m.env("ossos", 36.6, 14.6)
    wall_decor(m, flooded, 0, "correntes", 1.05)
    m.inspect(35.0, 18.0, "Água parada", "A água escura reflete a tocha de um jeito torto. Algo se arrasta "
              "longe, no eco.", radius=1.4)


# ------------------------------------------------------------------ ground painter
def _floor_texture(asset, h, w, G, ox=0, oy=0):
    info = env_info(asset)
    img = Image.open(ROOT / info["path"]).convert("RGB")
    px = max(8, int(round(img.width * G / info["ppu"])))
    img = img.resize((px, px), Image.LANCZOS)
    return tile(np.asarray(img).astype(float), h, w, ox, oy)


def paint(m):
    G = m.G
    h, w = m.h * G, m.w * G
    rng = np.random.default_rng(9)
    prng = random.Random(9)
    yy, xx = np.mgrid[0:h, 0:w]
    void = np.array([9, 8, 11]) * (0.8 + 0.4 * value_noise(h, w, 40, rng))[..., None]
    ground = np.broadcast_to(void, (h, w, 3)).copy()

    def mask(rects, grow=0.0):
        mm = np.zeros((h, w), bool)
        for (x, y, rw, rh) in rects:
            mm[max(0, int((y - grow) * G)):int((y + rh + grow) * G), max(0, int((x - grow) * G)):int((x + rw + grow) * G)] = True
        return mm

    floors = WALKABLE + [CELL, STAIRS]
    walk = mask(floors)
    ledge = mask(floors, 0.42) & ~walk
    flag = mask(FLAGSTONES)
    dirt = mask(DIRT + [STAIRS])
    lajes = desaturate(_floor_texture("lajes-dungeon", h, w, G), 0.15) * 0.8
    terra = _floor_texture("terra-dungeon", h, w, G, 31, 17) * 0.85
    ground[flag] = lajes[flag]
    ground[dirt & ~flag] = terra[dirt & ~flag]
    # Worn edges between flagstones and dirt.
    blend = ndi.gaussian_filter(flag.astype(float), G * 0.25)
    edge = walk & ~flag & (blend > 0.02)
    ground[edge] = (terra[edge] * (1 - blend[edge, None]) + lajes[edge] * blend[edge, None])
    # Wall tops (side and south walls seen from above).
    stone = desaturate(lajes, 0.4) * 0.55 + 12
    ground[ledge] = stone[ledge]
    top = ledge & ~np.roll(ledge, 3, axis=0)
    ground[top] = ground[top] * 1.35
    # Ambient occlusion: floors darken near the walls, deeper along the north faces.
    dist = ndi.distance_transform_edt(walk) / G
    ao = np.clip(1 - dist / 0.9, 0, 1) * walk
    ground *= (1 - ao[..., None] * 0.55)
    # Stairs going up to the surface: steps getting lighter toward the top of the flight.
    sx0, sy0, sw, sh = STAIRS
    for k in range(int(sh / 0.42) + 1):
        y0 = int((sy0 + k * 0.42) * G)
        y1 = int((sy0 + (k + 1) * 0.42) * G)
        x0, x1 = int(sx0 * G), int((sx0 + sw) * G)
        tone = 0.75 + 0.1 * k
        ground[y0:y1, x0:x1] = stone[y0:y1, x0:x1] * tone * 1.3
        ground[y0:y0 + 3, x0:x1] *= 0.55
    # Stains, pebbles, bone chips.
    stains = smoothstep(0.62, 0.75, fbm(h, w, 60, rng)) * walk
    ground *= (1 - stains[..., None] * 0.35)
    img = Image.fromarray(np.clip(ground, 0, 255).astype(np.uint8)).convert("RGBA")
    d = ImageDraw.Draw(img)
    pts = np.argwhere(walk)
    for _ in range(900):
        y, x = pts[prng.randrange(len(pts))]
        c = prng.choice([(120, 112, 100), (90, 84, 78), (170, 160, 140)])
        d.rectangle([x, y, x + prng.choice([1, 2]), y + 1], fill=c + (200,))
    for _ in range(90):
        y, x = pts[prng.randrange(len(pts))]
        a = prng.uniform(0, math.tau)
        d.line([(x, y), (x + math.cos(a) * 6, y + math.sin(a) * 6)], fill=(210, 200, 176, 220), width=2)
    for _ in range(160):
        y, x = pts[prng.randrange(len(pts))]
        pts2, a = [(x, y)], prng.uniform(0, math.tau)
        for _ in range(prng.randint(4, 10)):
            a += prng.uniform(-0.7, 0.7)
            x += math.cos(a) * 5
            y += math.sin(a) * 5
            pts2.append((x, y))
        d.line(pts2, fill=(20, 16, 14, 150), width=1)
    ground = np.asarray(img.convert("RGB")).astype(float)
    # Flooded room: dark standing water with a faint sheen.
    fx, fy, fw, fh = FLOODED
    water = ((xx - (fx + fw * 0.55) * G) / (fw * 0.42 * G)) ** 2 + ((yy - (fy + fh * 0.62) * G) / (fh * 0.3 * G)) ** 2
    water += (value_noise(h, w, 18, rng) - 0.5) * 0.8
    wm = smoothstep(1.0, 0.8, water) * walk
    sheen = (np.abs(((xx * 0.6 + yy) % 37) - 3) < 1) * 0.3
    ground = ground * (1 - wm[..., None] * 0.8) + (np.array([22, 26, 30]) + sheen[..., None] * 40) * wm[..., None] * 0.8
    return np.clip(ground, 0, 255)


def build():
    import moradias
    m = MapLayout("dungeon", "Ossário Esquecido", "Bairro_Dungeon", MAP_W, MAP_H, seed=41)
    m.G = 96
    m.region = "Sob os subúrbios"
    m.follow_clock = False
    m.fixed_ambient = (0.012, 0.01, 0.022, 0.86)
    m.wind = False
    m.background = (0.02, 0.018, 0.024)
    m.painter = paint
    layout(m, moradias.DUNGEON_DOOR)
    m.spawn = ENTRY
    return m
