"""Small procedural pixel props drawn at 64 px per tile (weeds, rubble, laundry, birds, FX)."""
import math
import random

import numpy as np
from scipy import ndimage as ndi
from PIL import Image, ImageDraw, ImageFilter

from common import save_rgba, load_rgba, desaturate, value_noise, smoothstep, crop_alpha, WORLD_ART


def _img(w, h):
    return Image.new("RGBA", (w, h), (0, 0, 0, 0))


def _arr(img):
    return np.asarray(img).astype(float)


# ------------------------------------------------------------------------- plants
def weeds(seed, kind="dry"):
    rng = random.Random(seed)
    w, h = 56, 46
    img = _img(w, h)
    d = ImageDraw.Draw(img)
    palettes = {
        "dry": [(122, 128, 70), (146, 140, 78), (170, 158, 96), (98, 104, 58)],
        "green": [(86, 112, 58), (104, 128, 66), (72, 94, 50), (126, 138, 76)],
        "straw": [(176, 156, 98), (196, 176, 116), (150, 128, 80), (128, 112, 70)],
    }
    pal = palettes[kind]
    base_x, base_y = w / 2, h - 3
    # Soft contact shadow.
    d.ellipse([base_x - 15, base_y - 3, base_x + 15, base_y + 2], fill=(20, 18, 12, 70))
    for _ in range(rng.randint(14, 22)):
        x = base_x + rng.uniform(-12, 12)
        ln = rng.uniform(14, 36)
        ang = -math.pi / 2 + rng.uniform(-0.75, 0.75)
        bend = rng.uniform(-0.03, 0.03)
        pts = [(x, base_y)]
        px, py, a = x, base_y, ang
        for _ in range(int(ln / 3)):
            a += bend * 3
            px += math.cos(a) * 3
            py += math.sin(a) * 3
            pts.append((px, py))
        col = rng.choice(pal)
        d.line(pts, fill=col + (255,), width=rng.choice([1, 2, 2]))
        d.point(pts[-1], fill=tuple(min(255, c + 30) for c in col) + (255,))
    if kind == "green" and rng.random() < 0.8:
        for _ in range(rng.randint(2, 5)):  # tiny pale flowers
            fx, fy = base_x + rng.uniform(-12, 12), base_y - rng.uniform(16, 30)
            d.rectangle([fx, fy, fx + 1, fy + 1], fill=(232, 228, 206, 255))
    return _arr(img)


def rubble(seed):
    rng = random.Random(seed)
    w, h = 72, 40
    img = _img(w, h)
    d = ImageDraw.Draw(img)
    d.ellipse([6, h - 12, w - 6, h - 2], fill=(22, 18, 14, 80))
    stones = []
    for _ in range(rng.randint(7, 11)):
        sw, sh = rng.randint(8, 20), rng.randint(6, 13)
        sx, sy = rng.randint(6, w - 6 - sw), rng.randint(h - 12 - sh - rng.randint(0, 12), h - 4 - sh)
        stones.append((sy + sh, sx, sy, sw, sh))
    for _, sx, sy, sw, sh in sorted(stones):
        base = rng.choice([(150, 144, 130), (170, 160, 140), (128, 122, 112), (184, 170, 146), (140, 110, 90)])
        d.polygon([(sx + 2, sy), (sx + sw - 2, sy + 1), (sx + sw, sy + sh - 3), (sx + sw - 3, sy + sh),
                   (sx + 2, sy + sh), (sx, sy + 3)], fill=base + (255,), outline=(60, 54, 48, 255))
        d.line([(sx + 2, sy + 1), (sx + sw - 3, sy + 2)], fill=tuple(min(255, c + 35) for c in base) + (255,))
        d.line([(sx + 2, sy + sh - 1), (sx + sw - 3, sy + sh - 1)], fill=tuple(int(c * 0.7) for c in base) + (255,))
    return _arr(img)


def dry_tree(tree, seed):
    """Sparse, faded version of the Codex tree: fewer leaves, dusty olive tone."""
    rng = np.random.default_rng(seed)
    out = tree.copy()
    rgb = out[..., :3]
    r, g, b = rgb[..., 0], rgb[..., 1], rgb[..., 2]
    leaf = (g > r * 1.02) & (g > b * 1.1) & (out[..., 3] > 0)
    h, w = leaf.shape
    holes = value_noise(h, w, 7, rng) > 0.47
    out[leaf & holes, 3] = 0
    rgb2 = desaturate(rgb, 0.6)
    rgb2 = rgb2 * np.array([1.16, 1.02, 0.7])
    out[..., :3] = np.where(leaf[..., None], rgb2, desaturate(rgb, 0.25))
    return out


def garden_bed(seed):
    """Small tilled vegetable bed with sprouts, cared for (Yuuki's parents)."""
    rng = random.Random(seed)
    w, h = 150, 84
    img = _img(w, h)
    d = ImageDraw.Draw(img)
    d.rectangle([2, 8, w - 3, h - 3], fill=(96, 70, 48, 255), outline=(62, 44, 30, 255))
    d.rectangle([2, 8, w - 3, 13], fill=(122, 92, 62, 255))  # wooden border top
    for row in range(4):
        y = 22 + row * 15
        d.rectangle([8, y - 4, w - 9, y + 4], fill=(78, 56, 40, 255))
        d.line([(8, y - 4), (w - 9, y - 4)], fill=(110, 82, 58, 255))
        for x in range(14, w - 12, 13):
            x2 = x + rng.randint(-2, 2)
            if rng.random() < 0.15:
                continue
            c = rng.choice([(96, 130, 64), (112, 142, 70), (84, 116, 58)])
            d.line([(x2, y), (x2 - 3, y - 6)], fill=c + (255,), width=2)
            d.line([(x2, y), (x2 + 3, y - 7)], fill=c + (255,), width=2)
    return _arr(img)


# ---------------------------------------------------------------------- clothesline
def clothesline():
    w, h = 236, 112
    img = _img(w, h)
    d = ImageDraw.Draw(img)
    for x in (8, w - 10):
        d.ellipse([x - 8, h - 7, x + 10, h - 1], fill=(20, 16, 12, 80))
        d.rectangle([x - 2, 12, x + 3, h - 4], fill=(104, 76, 50, 255), outline=(54, 38, 24, 255))
        d.line([(x - 1, 14), (x - 1, h - 6)], fill=(138, 104, 70, 255))
        d.rectangle([x - 9, 10, x + 10, 14], fill=(96, 70, 46, 255), outline=(54, 38, 24, 255))
    pts = []
    for i in range(41):
        t = i / 40
        x = 10 + t * (w - 22)
        y = 13 + math.sin(t * math.pi) * 9
        pts.append((x, y))
    d.line(pts, fill=(200, 190, 160, 255), width=1)
    return _arr(img)


def rope_y(x_px, w=236):
    t = (x_px - 10) / (w - 22)
    return 13 + math.sin(t * math.pi) * 9


def laundry(kind, seed):
    rng = random.Random(seed)
    faded = [(168, 150, 124), (132, 146, 150), (170, 128, 110), (190, 184, 160), (120, 132, 104)]
    col = rng.choice(faded)
    dark = tuple(int(c * 0.72) for c in col)
    if kind == "shirt":
        w, h = 34, 34
        img = _img(w, h)
        d = ImageDraw.Draw(img)
        d.polygon([(4, 2), (30, 2), (33, 12), (27, 13), (27, 32), (7, 32), (7, 13), (1, 12)],
                  fill=col + (255,), outline=dark + (255,))
        d.line([(17, 3), (17, 31)], fill=dark + (255,))
    elif kind == "sheet":
        w, h = 48, 44
        img = _img(w, h)
        d = ImageDraw.Draw(img)
        d.polygon([(1, 1), (46, 1), (45, 42), (24, 40), (2, 43)], fill=col + (255,), outline=dark + (255,))
        for _ in range(2):  # patches
            px, py = rng.randint(6, 30), rng.randint(8, 28)
            pc = rng.choice(faded)
            d.rectangle([px, py, px + 9, py + 8], fill=pc + (255,), outline=tuple(int(c * .6) for c in pc) + (255,))
        d.line([(10, 3), (12, 40)], fill=dark + (255,))
    elif kind == "pants":
        w, h = 24, 38
        img = _img(w, h)
        d = ImageDraw.Draw(img)
        d.polygon([(2, 1), (22, 1), (22, 36), (14, 36), (12, 12), (10, 36), (2, 36)],
                  fill=col + (255,), outline=dark + (255,))
        d.rectangle([2, 1, 22, 4], fill=dark + (255,))
    else:  # towel
        w, h = 22, 30
        img = _img(w, h)
        d = ImageDraw.Draw(img)
        d.rectangle([1, 1, 20, 28], fill=col + (255,), outline=dark + (255,))
        for y in (7, 22):
            d.line([(2, y), (19, y)], fill=dark + (255,))
    # Clothes pegs.
    d.rectangle([4, 0, 6, 3], fill=(140, 110, 80, 255))
    d.rectangle([w - 7, 0, w - 5, 3], fill=(140, 110, 80, 255))
    return _arr(img)


# -------------------------------------------------------------------------- interior
def book_pile(seed):
    rng = random.Random(seed)
    w, h = 34, 34
    img = _img(w, h)
    d = ImageDraw.Draw(img)
    d.ellipse([3, h - 6, w - 3, h - 1], fill=(18, 12, 8, 80))
    y = h - 4
    for _ in range(rng.randint(3, 6)):
        bw, bh = rng.randint(20, 28), rng.randint(4, 6)
        x = (w - bw) // 2 + rng.randint(-3, 3)
        c = rng.choice([(120, 60, 48), (70, 90, 110), (96, 110, 70), (150, 120, 70), (90, 60, 90)])
        d.rectangle([x, y - bh, x + bw, y], fill=c + (255,), outline=tuple(int(v * .55) for v in c) + (255,))
        d.line([(x + 1, y - 1), (x + bw - 1, y - 1)], fill=(226, 214, 186, 255))
        y -= bh + 1
    return _arr(img)


def stove():
    w, h = 64, 110
    img = _img(w, h)
    d = ImageDraw.Draw(img)
    d.ellipse([4, h - 9, w - 4, h - 1], fill=(14, 10, 8, 90))
    d.rectangle([28, 0, 36, 50], fill=(58, 56, 60, 255), outline=(26, 24, 28, 255))  # pipe
    d.rectangle([6, 46, w - 7, h - 8], fill=(66, 62, 64, 255), outline=(26, 24, 28, 255))
    d.rectangle([6, 46, w - 7, 54], fill=(92, 88, 90, 255), outline=(26, 24, 28, 255))
    d.rectangle([16, 64, w - 17, 86], fill=(34, 30, 32, 255), outline=(20, 18, 20, 255))
    d.rectangle([19, 74, w - 20, 84], fill=(206, 110, 48, 255))  # embers
    d.rectangle([22, 78, w - 23, 83], fill=(250, 180, 80, 255))
    for x in (8, w - 12):
        d.rectangle([x, h - 10, x + 4, h - 4], fill=(40, 38, 40, 255))
    return _arr(img)


# ------------------------------------------------------------------------------ fx
def pigeon_frames():
    """Four tiny frames: idle, peck, flap up, flap down (24x18 px)."""
    frames = []
    body, wing, head, belly = (150, 150, 158), (118, 118, 128), (96, 104, 118), (180, 178, 184)
    for f in range(4):
        img = _img(24, 18)
        d = ImageDraw.Draw(img)
        if f < 2:
            d.ellipse([5, 16, 19, 18], fill=(10, 10, 10, 70))
            d.ellipse([5, 7, 18, 15], fill=body + (255,), outline=(60, 60, 68, 255))
            d.ellipse([8, 9, 16, 14], fill=wing + (255,))
            d.line([(4, 10), (1, 9)], fill=(84, 84, 92, 255), width=2)  # tail
            hx, hy = (17, 5) if f == 0 else (19, 10)
            d.ellipse([hx - 3, hy - 2, hx + 3, hy + 3], fill=head + (255,), outline=(50, 54, 64, 255))
            d.point((hx + 1, hy), fill=(230, 120, 60, 255))
            d.point((hx + 4, hy + 1), fill=(210, 190, 150, 255))
            d.line([(10, 15), (10, 17)], fill=(200, 110, 90, 255))
            d.line([(13, 15), (13, 17)], fill=(200, 110, 90, 255))
        else:
            d.ellipse([7, 7, 17, 13], fill=body + (255,), outline=(60, 60, 68, 255))
            if f == 2:
                d.polygon([(9, 8), (2, 0), (14, 7)], fill=wing + (255,), outline=(60, 60, 68, 255))
                d.polygon([(12, 8), (20, 1), (15, 8)], fill=belly + (255,), outline=(60, 60, 68, 255))
            else:
                d.polygon([(9, 10), (2, 16), (14, 11)], fill=wing + (255,), outline=(60, 60, 68, 255))
                d.polygon([(12, 10), (20, 16), (15, 11)], fill=belly + (255,), outline=(60, 60, 68, 255))
            d.ellipse([16, 6, 21, 11], fill=head + (255,))
        frames.append(_arr(img))
    return frames


def leaf(seed):
    rng = random.Random(seed)
    img = _img(9, 7)
    d = ImageDraw.Draw(img)
    c = rng.choice([(150, 140, 70), (176, 130, 60), (120, 130, 64), (190, 160, 90)])
    d.polygon([(0, 3), (4, 0), (8, 3), (4, 6)], fill=c + (255,), outline=tuple(int(v * .6) for v in c) + (255,))
    d.line([(1, 3), (7, 3)], fill=tuple(int(v * .7) for v in c) + (255,))
    return _arr(img)


def dust():
    img = _img(4, 4)
    d = ImageDraw.Draw(img)
    d.rectangle([1, 1, 2, 2], fill=(226, 206, 160, 200))
    d.point((0, 1), fill=(226, 206, 160, 90))
    return _arr(img)


def paper():
    img = _img(12, 14)
    d = ImageDraw.Draw(img)
    d.polygon([(1, 1), (10, 0), (11, 12), (2, 13)], fill=(232, 222, 196, 255), outline=(150, 136, 110, 255))
    for y in (4, 7, 10):
        d.line([(3, y), (9, y - 1)], fill=(140, 130, 120, 255))
    return _arr(img)


def soft_blob(w, h, color, alpha, blur):
    img = _img(w, h)
    d = ImageDraw.Draw(img)
    rng = random.Random(w * 7 + h)
    for _ in range(9):  # lumpy cloud outline from overlapping ellipses
        cx, cy = rng.uniform(w * .25, w * .75), rng.uniform(h * .3, h * .7)
        rx, ry = rng.uniform(w * .15, w * .28), rng.uniform(h * .18, h * .3)
        d.ellipse([cx - rx, cy - ry, cx + rx, cy + ry], fill=color + (alpha,))
    return _arr(img.filter(ImageFilter.GaussianBlur(blur)))


def smoke_puff():
    img = _img(32, 32)
    d = ImageDraw.Draw(img)
    d.ellipse([4, 4, 28, 28], fill=(236, 232, 226, 255))
    return _arr(img.filter(ImageFilter.GaussianBlur(4)))


# ----------------------------------------------------------------------------- NPCs
def npc_silhouettes(atlas, idle, tint, name, out_dir):
    """Placeholder villagers: monochrome, low-contrast versions of the chibi base.

    They keep the shared animation rhythm without copying Yuuki's colours, so her black
    wing stays unique. Replace the PNGs in the variant folder with real sprites later.
    """
    cells = []
    for row, label in ((0, "walk_left"), (1, "walk_right")):
        for c in range(6):
            cells.append((label, c, atlas[row * 512:(row + 1) * 512, c * 512:(c + 1) * 512]))
    cells.append(("idle_left", 0, idle[:, 0:512]))
    cells.append(("idle_right", 0, idle[:, 512:1024]))
    # Shared crop so every frame keeps the same pivot (x=256, feet at y=400).
    x0, x1, y0, y1 = 64, 448, 60, 440
    names = []
    for label, c, cell in cells:
        a = cell.copy()
        l = (a[..., 0] * .299 + a[..., 1] * .587 + a[..., 2] * .114) / 255
        shade = 0.36 + 0.8 * l
        rgb = np.clip(np.array(tint)[None, None, :] * shade[..., None], 0, 255)
        body = a[..., 3] > 40
        a[..., :3] = np.where(body[..., None], rgb, 0)
        a[..., 3] = np.where(body, 255, 0)
        # Dark 2px outline so the placeholder reads clearly on any ground.
        ring = ndi.binary_dilation(body, iterations=2) & ~body
        a[ring, :3] = np.array(tint) * 0.3
        a[ring, 3] = 255
        crop = a[y0:y1, x0:x1]
        fname = f"{label}_{c:02d}.png"
        save_rgba(crop, out_dir / name / fname)
        names.append((label, c, fname))
    pivot = ((256 - x0) / (x1 - x0), (y1 - 400) / (y1 - y0))
    return names, pivot
