"""Procedural sprites for the Moradias map: plank shacks with patched tin roofs, an abandoned
house, chickens, woodpile, trash heap, broken cart and water barrels.

Drawn in the same 3/4 top-down view as the Codex buildings (roof surface seen from above,
south facade facing the camera), at 60 px per tile for buildings and 64 px for props.
"""
import math
import random

import numpy as np
from PIL import Image, ImageDraw, ImageFilter
from scipy import ndimage as ndi

from common import value_noise, fbm, desaturate, smoothstep

OUTLINE = (40, 28, 20, 255)


def _shade(c, k):
    return tuple(int(max(0, min(255, v * k))) for v in c[:3]) + ((c[3],) if len(c) > 3 else (255,))


def _outline(img, color=OUTLINE, width=2):
    arr = np.asarray(img).copy()
    body = arr[..., 3] > 30
    ring = ndi.binary_dilation(body, iterations=width) & ~body
    arr[ring] = color
    return Image.fromarray(arr, "RGBA")


def _texture_noise(img, seed, amount=0.12, cell=5):
    """Break flat fills into pixel clusters (keeps the 32-bit RPG feel)."""
    arr = np.asarray(img).astype(float)
    rng = np.random.default_rng(seed)
    n = value_noise(arr.shape[0], arr.shape[1], cell, rng) - 0.5
    fine = rng.random(arr.shape[:2]) - 0.5
    k = 1 + n * amount * 2 + fine * amount * 0.6
    arr[..., :3] *= k[..., None]
    return Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")


# ------------------------------------------------------------------------ shack
def shack(seed, width_tiles=4.4, door_side=None, curtain_door=False, stovepipe=False, lean_to=False):
    """Plank shack, single-slope corrugated tin roof seen from above, door facing south."""
    rng = random.Random(seed)
    P = 60
    W = int(width_tiles * P)
    roof_d = int(rng.uniform(1.7, 2.1) * P)      # visible depth of the roof surface
    wall_h = int(rng.uniform(1.95, 2.1) * P)      # front wall (door ~1.8 tiles)
    base_h = 8
    side = 16                                      # visible east side wall (depth cue)
    pad = 6
    H = roof_d + wall_h + base_h + pad * 2
    img = Image.new("RGBA", (W + side + pad * 2 + 16, H + 8), (0, 0, 0, 0))
    d = ImageDraw.Draw(img)
    x0, x1 = pad + 8, pad + 8 + W
    wall_top = pad + roof_d
    wall_bot = wall_top + wall_h

    # --- side wall (east), darker, receding upwards
    d.polygon([(x1, wall_top - 4), (x1 + side, wall_top - 18), (x1 + side, wall_bot - 12), (x1, wall_bot)],
              fill=(88, 62, 42, 255))
    for yy in range(wall_top, wall_bot, 12):
        d.line([(x1, yy), (x1 + side, yy - 14)], fill=(64, 44, 30, 255))

    # --- front wall: vertical planks of uneven width and colour
    x = x0
    woods = [(128, 94, 62), (116, 84, 56), (138, 104, 70), (104, 76, 50), (122, 96, 70)]
    while x < x1:
        pw = rng.randint(13, 22)
        c = rng.choice(woods)
        if rng.random() < 0.08:
            c = rng.choice([(96, 110, 118), (120, 90, 80), (110, 116, 90)])  # odd salvaged plank
        top = wall_top + rng.randint(-2, 3)
        d.rectangle([x, top, min(x + pw, x1), wall_bot], fill=c + (255,))
        d.line([(x + 2, top + 2), (x + 2, wall_bot - 2)], fill=_shade(c, 1.12))
        d.line([(x, top), (x, wall_bot)], fill=(52, 36, 24, 255), width=2)  # gap between boards
        for _ in range(rng.randint(0, 2)):                                   # knots
            ky = rng.randint(top + 10, wall_bot - 10)
            d.ellipse([x + pw / 2 - 2, ky, x + pw / 2 + 2, ky + 4], fill=_shade(c, 0.7))
        if rng.random() < 0.12:                                              # split board
            sx = x + rng.randint(4, max(5, pw - 4))
            d.line([(sx, wall_bot - rng.randint(20, 60)), (sx + 1, wall_bot)], fill=(46, 32, 22, 255))
        x += pw
    # Horizontal battens holding the boards.
    for by in (wall_top + 22, wall_bot - 26):
        d.rectangle([x0, by, x1, by + 6], fill=(98, 70, 46, 255), outline=(56, 40, 26, 255))
        for nx in range(x0 + 8, x1, rng.randint(20, 30)):
            d.point((nx, by + 3), fill=(40, 40, 44, 255))

    # --- door
    dw, dh = 54, int(1.78 * P)
    if door_side is None:
        door_side = rng.choice([0.28, 0.5, 0.7])
    dx = int(x0 + W * door_side - dw / 2)
    dy = wall_bot - dh
    d.rectangle([dx - 4, dy - 5, dx + dw + 4, wall_bot], fill=(72, 50, 32, 255))
    if curtain_door:
        cc = rng.choice([(150, 70, 60), (90, 110, 130), (170, 150, 110)])
        d.rectangle([dx, dy, dx + dw, wall_bot], fill=(26, 18, 14, 255))
        pts = [(dx, dy)] + [(dx + i * dw / 6, wall_bot - (4 if i % 2 else 0)) for i in range(7)] + [(dx + dw, dy)]
        d.polygon(pts, fill=cc + (255,))
        for i in range(1, 6):
            d.line([(dx + i * dw / 6, dy + 2), (dx + i * dw / 6, wall_bot - 4)], fill=_shade(cc, 0.75))
        d.rectangle([dx - 2, dy - 2, dx + dw + 2, dy + 2], fill=(60, 60, 64, 255))
    else:
        dc = rng.choice([(96, 68, 44), (86, 60, 40), (104, 80, 56)])
        for i in range(4):
            d.rectangle([dx + i * dw / 4, dy, dx + (i + 1) * dw / 4, wall_bot], fill=_shade(dc, 0.9 + 0.1 * (i % 2)),
                        outline=(48, 32, 22, 255))
        d.line([(dx + 4, dy + 12), (dx + dw - 4, wall_bot - 12)], fill=(70, 48, 30, 255), width=3)
        d.rectangle([dx + dw - 12, dy + dh / 2, dx + dw - 8, dy + dh / 2 + 5], fill=(50, 50, 54, 255))
    # Worn stone step.
    d.rectangle([dx - 6, wall_bot, dx + dw + 6, wall_bot + base_h + 2], fill=(132, 124, 110, 255),
                outline=(70, 64, 56, 255))

    # --- window (cloth curtain or boarded)
    if W > 200:
        wx = int(x0 + (W * 0.78 if door_side < 0.5 else W * 0.18)) - 20
        wy = wall_top + 34
        d.rectangle([wx - 3, wy - 3, wx + 43, wy + 35], fill=(70, 50, 32, 255))
        d.rectangle([wx, wy, wx + 40, wy + 32], fill=(30, 24, 22, 255))
        if rng.random() < 0.5:
            cc = rng.choice([(186, 168, 130), (150, 120, 110), (130, 140, 120)])
            d.polygon([(wx, wy), (wx + 22, wy), (wx + 14, wy + 32), (wx, wy + 32)], fill=cc + (255,))
            d.polygon([(wx + 40, wy), (wx + 26, wy), (wx + 32, wy + 32), (wx + 40, wy + 32)], fill=_shade(cc, 0.9))
        else:
            for i in range(3):
                yb = wy + 4 + i * 10
                d.polygon([(wx - 4, yb), (wx + 44, yb + rng.randint(-3, 3)), (wx + 44, yb + 7), (wx - 4, yb + 7)],
                          fill=(120, 90, 60, 255), outline=(56, 40, 26, 255))
        d.rectangle([wx - 5, wy + 34, wx + 45, wy + 38], fill=(96, 70, 46, 255))

    # --- stone base
    for sx in range(x0 - 2, x1 + 2, 12):
        c = rng.choice([(120, 112, 100), (104, 98, 90), (136, 126, 110)])
        d.rectangle([sx, wall_bot + 1, sx + 11, wall_bot + base_h], fill=c + (255,), outline=(66, 60, 52, 255))

    # --- roof: corrugated tin sheets seen from above, rusty and patched
    ov = 10
    rx0, rx1 = x0 - ov, x1 + side + 2
    ry0, ry1 = pad, wall_top + 6
    roof = Image.new("RGBA", img.size, (0, 0, 0, 0))
    rd = ImageDraw.Draw(roof)
    sheets_x = [rx0]
    while sheets_x[-1] < rx1:
        sheets_x.append(sheets_x[-1] + rng.randint(48, 76))
    for i in range(len(sheets_x) - 1):
        sx0, sx1 = sheets_x[i], min(sheets_x[i + 1], rx1)
        tint = rng.choice([(150, 150, 146), (136, 134, 128), (160, 150, 136), (128, 120, 110)])
        rows = [ry0, ry0 + (ry1 - ry0) // 2 + rng.randint(-10, 10), ry1]
        for r in range(2):
            ya, yb = rows[r] - (3 if r else 0), rows[r + 1]
            for cx in range(sx0, sx1, 8):  # ridges
                rd.rectangle([cx, ya, min(cx + 3, sx1), yb], fill=_shade(tint, 1.12))
                if cx + 4 <= sx1:
                    rd.rectangle([cx + 4, ya, min(cx + 7, sx1), yb], fill=_shade(tint, 0.86))
            rd.line([(sx0, yb), (sx1, yb)], fill=_shade(tint, 0.6), width=2)   # overlap seam
        rd.line([(sx0, ry0), (sx0, ry1)], fill=_shade(tint, 0.62), width=2)
    rarr = np.asarray(roof).astype(float)
    nrng = np.random.default_rng(seed)
    rust = smoothstep(0.56, 0.78, fbm(rarr.shape[0], rarr.shape[1], 12, nrng)) * 0.75
    rust_col = np.array([146, 84, 50])
    body = rarr[..., 3] > 0
    rarr[..., :3] = np.where(body[..., None], rarr[..., :3] * (1 - rust[..., None] * 0.8) +
                             rust_col * (0.6 + 0.4 * (rarr[..., :3].mean(-1, keepdims=True) / 160)) * rust[..., None] * 0.8,
                             rarr[..., :3])
    roof = Image.fromarray(np.clip(rarr, 0, 255).astype(np.uint8), "RGBA")
    rd = ImageDraw.Draw(roof)
    for _ in range(rng.randint(1, 3)):  # patches of odd material
        pw, ph = rng.randint(30, 60), rng.randint(20, 40)
        px, py = rng.randint(rx0 + 6, max(rx0 + 7, rx1 - pw - 6)), rng.randint(ry0 + 6, max(ry0 + 7, ry1 - ph - 6))
        pc = rng.choice([(110, 90, 70), (90, 96, 104), (140, 110, 80), (80, 70, 60)])
        rd.polygon([(px, py), (px + pw, py + rng.randint(-3, 3)), (px + pw, py + ph), (px + 2, py + ph)],
                   fill=pc + (255,), outline=_shade(pc, 0.55))
    for _ in range(rng.randint(3, 6)):  # stones and bricks holding the sheets down
        sx, sy = rng.randint(rx0 + 10, rx1 - 16), rng.randint(ry0 + 8, ry1 - 14)
        sc = rng.choice([(150, 144, 132), (120, 112, 104), (160, 100, 80)])
        rd.ellipse([sx, sy, sx + rng.randint(9, 15), sy + rng.randint(7, 11)], fill=sc + (255,), outline=(60, 54, 48, 255))
    # Eave: sheet edge and its shadow on the wall.
    rd.rectangle([rx0, ry1 - 4, rx1, ry1 + 2], fill=(92, 88, 84, 255))
    img = Image.alpha_composite(img, roof)
    d = ImageDraw.Draw(img)
    if stovepipe:
        px = int(rx0 + (rx1 - rx0) * rng.uniform(0.6, 0.8))
        d.rectangle([px, ry0 - 26, px + 10, ry0 + 30], fill=(58, 56, 58, 255), outline=(30, 28, 30, 255))
        d.rectangle([px - 4, ry0 - 30, px + 14, ry0 - 24], fill=(48, 46, 48, 255))
    arr = np.asarray(img).astype(float)
    yy = np.arange(arr.shape[0])[:, None]
    eave = np.exp(-np.clip(yy - ry1, 0, None) / 9) * (yy > ry1) * (yy < wall_bot)
    arr[..., :3] *= (1 - eave[..., None] * 0.45)
    # Mud splash at the foot of the wall.
    splash = smoothstep(wall_bot - 26, wall_bot, yy) * (yy <= wall_bot)
    arr[..., :3] *= (1 - splash[..., None] * 0.25)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    img = _texture_noise(img, seed, 0.07)
    img = _outline(img)
    if lean_to:  # crooked lean-to shelter with junk on the west side
        extra = Image.new("RGBA", (img.width + 70, img.height), (0, 0, 0, 0))
        extra.alpha_composite(img, (70, 0))
        e = ImageDraw.Draw(extra)
        e.polygon([(10, wall_top + 30), (80, wall_top + 10), (80, wall_bot), (14, wall_bot)], fill=(40, 30, 24, 255))
        e.polygon([(4, wall_top + 24), (84, wall_top + 2), (84, wall_top + 12), (6, wall_top + 36)],
                  fill=(128, 120, 108, 255), outline=OUTLINE)
        for px in (14, 74):
            e.rectangle([px, wall_top + 26, px + 5, wall_bot], fill=(104, 76, 50, 255), outline=OUTLINE)
        e.rectangle([24, wall_bot - 24, 50, wall_bot], fill=(120, 90, 60, 255), outline=OUTLINE)
        e.ellipse([52, wall_bot - 22, 68, wall_bot], fill=(90, 96, 100, 255), outline=OUTLINE)
        img = extra
    arr = np.asarray(img).astype(float)
    return arr, (wall_bot + base_h) / arr.shape[0]


# ----------------------------------------------------------------- abandoned
def abandoned(house, seed):
    """Collapse parts of a roof, board the door and kill the lamp."""
    rng = np.random.default_rng(seed)
    out = house.copy()
    h, w = out.shape[:2]
    rgb = out[..., :3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    yy = np.arange(h)[:, None]
    roof = (r > g * 1.15) & (yy < h * 0.5) & (out[..., 3] > 0)
    holes = (fbm(h, w, 26, rng) > 0.6) & roof
    holes = ndi.binary_opening(holes, iterations=2)
    edge = ndi.binary_dilation(holes, iterations=3) & ~holes & roof
    xx = np.arange(w)[None, :].repeat(h, 0)
    rafters = (xx % 16 < 4)  # bare rafters showing through the gaps
    out[holes, :3] = np.array([26, 19, 15])
    beam = holes & rafters
    out[beam, :3] = np.array([92, 66, 44]) * (0.8 + 0.2 * (xx[beam, None] % 16 == 0))
    out[edge, :3] = out[edge, :3] * 0.6 + np.array([90, 60, 40]) * 0.4
    lamp = (r > 180) & (g > 120) & (b < 110) & (r - b > 90)
    out[lamp, :3] = desaturate(out[lamp, :3][None], 0.8)[0] * 0.55
    out[..., :3] = desaturate(out[..., :3], 0.5) * 0.85
    return out


# -------------------------------------------------------------------- props
def _img(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def chicken_frames(body_col, seed):
    rng = random.Random(seed)
    frames = []
    for f in range(4):
        img = _img(26, 24)
        d = ImageDraw.Draw(img)
        d.ellipse([6, 20, 20, 23], fill=(10, 8, 6, 70))
        bob = 1 if f == 3 else 0
        d.ellipse([4, 8 + bob, 18, 19 + bob], fill=body_col + (255,), outline=_shade(body_col, 0.45))
        d.polygon([(4, 11 + bob), (1, 6 + bob), (6, 10 + bob)], fill=_shade(body_col, 0.85), outline=_shade(body_col, 0.45))
        d.ellipse([8, 11 + bob, 15, 16 + bob], fill=_shade(body_col, 0.88))  # wing
        if f == 1:  # pecking
            hx, hy = 20, 16
        else:
            hx, hy = 18, 6 + bob
        d.ellipse([hx - 3, hy - 3, hx + 3, hy + 3], fill=body_col + (255,), outline=_shade(body_col, 0.45))
        d.rectangle([hx - 1, hy - 5, hx + 1, hy - 3], fill=(200, 50, 40, 255))
        d.polygon([(hx + 3, hy), (hx + 6, hy + 1), (hx + 3, hy + 2)], fill=(230, 170, 60, 255))
        d.point((hx + 1, hy - 1), fill=(20, 20, 20, 255))
        legs = [(9, 12), (11, 10), (8, 13), (12, 9)][f]
        for lx in legs:
            d.line([(lx, 19 + bob), (lx + (1 if f == 2 else 0), 22)], fill=(220, 160, 60, 255))
        frames.append(np.asarray(img).astype(float))
    return frames


def woodpile(seed):
    rng = random.Random(seed)
    img = _img(112, 70)
    d = ImageDraw.Draw(img)
    d.ellipse([4, 60, 108, 69], fill=(14, 10, 8, 80))
    d.rectangle([6, 20, 106, 62], fill=(76, 52, 34, 255))
    for row in range(4):
        for i in range(7 - (row % 2)):
            cx = 14 + i * 14 + (7 if row % 2 else 0)
            cy = 56 - row * 11
            r = rng.randint(6, 7)
            d.ellipse([cx - r, cy - r, cx + r, cy + r], fill=(176, 138, 92, 255), outline=(82, 56, 36, 255))
            d.ellipse([cx - r + 3, cy - r + 3, cx + r - 3, cy + r - 3], outline=(140, 104, 66, 255))
    d.rectangle([4, 12, 108, 18], fill=(110, 110, 104, 255), outline=OUTLINE)  # tin cover
    return np.asarray(_outline(img)).astype(float)


def trash_heap(seed):
    rng = random.Random(seed)
    img = _img(130, 84)
    d = ImageDraw.Draw(img)
    d.ellipse([6, 66, 124, 82], fill=(16, 12, 8, 90))
    d.polygon([(10, 76), (30, 40), (62, 22), (96, 34), (122, 76)], fill=(84, 70, 54, 255))
    for _ in range(26):
        x, y = rng.randint(18, 110), rng.randint(30, 72)
        k = rng.random()
        if k < 0.3:  # broken plank
            c = rng.choice([(126, 94, 62), (100, 74, 50)])
            dx = rng.randint(-18, 18)
            d.line([(x, y), (x + dx, y + rng.randint(-6, 6))], fill=c + (255,), width=4)
        elif k < 0.55:  # rag / sack
            c = rng.choice([(150, 130, 100), (120, 110, 130), (140, 90, 80), (110, 120, 96)])
            d.polygon([(x, y), (x + 12, y - 3), (x + 15, y + 7), (x + 2, y + 9)], fill=c + (255,), outline=_shade(c, 0.6))
        elif k < 0.7:  # bottle
            d.rectangle([x, y, x + 4, y + 9], fill=(90, 120, 100, 255), outline=(40, 60, 50, 255))
        elif k < 0.85:  # tin can
            d.ellipse([x, y, x + 7, y + 6], fill=(150, 146, 140, 255), outline=(70, 66, 60, 255))
        else:  # broken pot
            d.pieslice([x, y, x + 14, y + 12], 0, 200, fill=(160, 96, 66, 255), outline=(80, 48, 34, 255))
    img = _texture_noise(img, seed, 0.08)
    return np.asarray(_outline(img)).astype(float)


def broken_cart(seed):
    img = _img(170, 100)
    d = ImageDraw.Draw(img)
    d.ellipse([8, 86, 162, 99], fill=(14, 10, 8, 80))
    # Tilted bed resting on the ground on one side (missing wheel).
    d.polygon([(20, 40), (140, 30), (146, 70), (26, 88)], fill=(118, 86, 56, 255), outline=OUTLINE)
    for i in range(1, 6):
        x = 20 + i * 20
        d.line([(x, 40 - i * 1.6), (x + 5, 88 - i * 3.4)], fill=(80, 56, 36, 255), width=2)
    d.polygon([(20, 40), (140, 30), (138, 22), (18, 32)], fill=(138, 104, 70, 255), outline=OUTLINE)
    # One wheel still on, one lying on the ground.
    d.ellipse([112, 50, 158, 96], outline=(70, 50, 32, 255), width=6)
    for a in range(0, 360, 45):
        d.line([(135, 73), (135 + 20 * math.cos(math.radians(a)), 73 + 20 * math.sin(math.radians(a)))],
               fill=(96, 70, 46, 255), width=3)
    d.ellipse([2, 80, 44, 96], outline=(80, 58, 36, 255), width=5)
    d.line([(40, 60), (4, 44)], fill=(110, 80, 52, 255), width=6)  # shaft
    return np.asarray(_outline(img)).astype(float)


def water_barrels(seed):
    rng = random.Random(seed)
    img = _img(80, 64)
    d = ImageDraw.Draw(img)
    d.ellipse([4, 54, 76, 63], fill=(14, 10, 8, 80))
    for bx in (6, 34):
        d.rectangle([bx, 14, bx + 26, 58], fill=(120, 86, 56, 255), outline=OUTLINE)
        for y in (20, 36, 52):
            d.rectangle([bx, y, bx + 26, y + 3], fill=(84, 84, 90, 255))
        d.ellipse([bx, 8, bx + 26, 20], fill=(64, 80, 84, 255), outline=OUTLINE)  # water surface
        d.ellipse([bx + 5, 11, bx + 12, 14], fill=(140, 160, 170, 255))
    d.polygon([(62, 44), (76, 44), (74, 60), (64, 60)], fill=(150, 148, 142, 255), outline=OUTLINE)  # bucket
    d.arc([62, 36, 76, 50], 180, 360, fill=(70, 70, 70, 255), width=2)
    return np.asarray(_texture_noise(img, seed, 0.06)).astype(float)


def chicken_coop(seed):
    rng = random.Random(seed)
    img = _img(150, 120)
    d = ImageDraw.Draw(img)
    d.ellipse([8, 106, 142, 119], fill=(14, 10, 8, 80))
    d.rectangle([14, 50, 136, 110], fill=(112, 82, 54, 255), outline=OUTLINE)
    for x in range(16, 136, 12):
        d.line([(x, 52), (x, 108)], fill=(80, 56, 36, 255), width=2)
    d.rectangle([56, 72, 88, 110], fill=(30, 22, 16, 255), outline=OUTLINE)  # opening
    d.polygon([(64, 110), (80, 110), (98, 118), (46, 118)], fill=(130, 100, 66, 255), outline=OUTLINE)  # ramp
    d.polygon([(4, 52), (146, 52), (136, 12), (14, 12)], fill=(126, 120, 108, 255), outline=OUTLINE)
    for x in range(16, 136, 9):
        d.line([(x, 14), (x - 2, 50)], fill=(104, 98, 90, 255), width=2)
    for _ in range(4):
        x, y = rng.randint(20, 120), rng.randint(18, 44)
        d.ellipse([x, y, x + 10, y + 7], fill=(146, 138, 126, 255), outline=(70, 64, 56, 255))
    for _ in range(6):  # straw at the door
        x = rng.randint(50, 96)
        d.line([(x, 112), (x + rng.randint(-8, 8), 116)], fill=(210, 180, 110, 255))
    return np.asarray(_texture_noise(img, seed, 0.06)).astype(float)
