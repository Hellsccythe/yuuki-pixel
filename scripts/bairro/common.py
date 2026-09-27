"""Shared helpers for the procedural neighbourhood art (noise, textures, weathering).

Everything is deterministic: the same seed always rebuilds the same pixels, so the
generated PNGs can be regenerated at any time with scripts/bairro/build_rua_de_casa.py.
"""
from pathlib import Path
import math
import random

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
WORLD_ART = ROOT / "Assets/Game/Resources/World/Art"
SOURCES = ROOT / "Art/World/Sources"
OUT = ROOT / "Assets/Game/Bairro"


# --------------------------------------------------------------------------- noise
def value_noise(h, w, cell, rng):
    """Smooth value noise in [0, 1] with features roughly `cell` pixels wide."""
    gh, gw = h // cell + 4, w // cell + 4
    grid = rng.random((gh, gw))
    big = ndi.zoom(grid, cell, order=3, mode="grid-wrap")
    return np.clip(big[:h, :w], 0, 1)


def fbm(h, w, cell, rng, octaves=4):
    total = np.zeros((h, w))
    amp, norm = 1.0, 0.0
    for _ in range(octaves):
        total += value_noise(h, w, max(2, int(cell)), rng) * amp
        norm += amp
        amp *= 0.5
        cell /= 2
    return total / norm


def smoothstep(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1)
    return t * t * (3 - 2 * t)


def tile(tex, h, w, ox=0, oy=0):
    th, tw = tex.shape[:2]
    reps = (h // th + 2, w // tw + 2) + ((1,) if tex.ndim == 3 else ())
    big = np.tile(tex, reps)
    return big[oy:oy + h, ox:ox + w]


def lum(rgb):
    return rgb[..., 0] * 0.299 + rgb[..., 1] * 0.587 + rgb[..., 2] * 0.114


def desaturate(rgb, amount):
    l = lum(rgb)[..., None]
    return rgb * (1 - amount) + l * amount


# ------------------------------------------------------------------------- terrain
def terrain_textures():
    """Quadrants of the Codex terrain atlas: grass, dirt, cobble, wood (float RGB 0-255)."""
    img = np.asarray(Image.open(SOURCES / "terrain.png").convert("RGB")).astype(float)
    half = img.shape[0] // 2
    quads = {}
    for i, name in enumerate(["grass", "dirt", "cobble", "wood"]):
        c, r = i % 2, i // 2
        q = img[r * half:(r + 1) * half, c * half:(c + 1) * half]
        # Trim 6px so the atlas seams never repeat inside the tiled ground.
        quads[name] = q[6:-6, 6:-6]
    return quads


# ----------------------------------------------------------------------- sprites io
def load_rgba(path):
    return np.asarray(Image.open(path).convert("RGBA")).astype(float)


def save_rgba(arr, path):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    a = np.clip(arr, 0, 255).astype(np.uint8)
    # Clear RGB under full transparency so no hidden colour bleeds with filtering.
    a[a[..., 3] == 0, :3] = 0
    Image.fromarray(a, "RGBA").save(path, optimize=True)


def crop_alpha(arr, pad=2):
    ys, xs = np.nonzero(arr[..., 3] > 8)
    y0, y1, x0, x1 = ys.min(), ys.max() + 1, xs.min(), xs.max() + 1
    out = np.zeros((y1 - y0 + pad * 2, x1 - x0 + pad * 2, 4))
    out[pad:-pad, pad:-pad] = arr[y0:y1, x0:x1]
    return out


# ----------------------------------------------------------------------- weathering
def _walk_crack(draw, x, y, length, rng, width=1, color=(40, 30, 25, 210), hi=(235, 220, 190, 90)):
    angle = rng.uniform(math.pi * 0.3, math.pi * 0.7)  # mostly downward
    pts = [(x, y)]
    for _ in range(length):
        angle += rng.uniform(-0.6, 0.6)
        x += math.cos(angle) * 2.2
        y += math.sin(angle) * 2.2
        pts.append((x, y))
        if rng.random() < 0.06:  # small branch
            bx, by, ba = x, y, angle + rng.choice([-1, 1]) * rng.uniform(0.6, 1.2)
            bp = [(bx, by)]
            for _ in range(rng.randint(3, 8)):
                bx += math.cos(ba) * 2
                by += math.sin(ba) * 2
                bp.append((bx, by))
            draw.line(bp, fill=color, width=1)
    draw.line([(p[0] + 1, p[1]) for p in pts], fill=hi, width=1)
    draw.line(pts, fill=color, width=width)


def weather(arr, seed, desat=0.2, darken=0.05, grime=0.3, cracks=6, crack_zone=(0.35, 0.95),
            dust=(1.0, 0.95, 0.86)):
    """Age an RGBA sprite: fade colours, add rain streaks, ground splash and wall cracks."""
    rng = random.Random(seed)
    nrng = np.random.default_rng(seed)
    out = arr.copy()
    rgb = out[..., :3]
    alpha = out[..., 3]
    h, w = alpha.shape
    rgb[:] = desaturate(rgb, desat)
    rgb *= (1 - darken)
    rgb *= np.array(dust)[None, None, :] * 0.5 + 0.5
    if grime > 0:
        # Vertical rain streaks under eaves and window sills.
        streak = np.zeros((h, w))
        for _ in range(int(w / 9)):
            x = rng.randrange(w)
            y0 = rng.randrange(int(h * 0.2), int(h * 0.8))
            ln = rng.randrange(int(h * 0.05), int(h * 0.25))
            streak[y0:y0 + ln, x:x + rng.choice([1, 1, 2])] += np.linspace(0.8, 0, len(streak[y0:y0 + ln]))[:, None]
        streak = ndi.gaussian_filter(streak, (1.5, 0.4))
        # Mud splash along the base.
        ys = np.linspace(0, 1, h)[:, None]
        splash = smoothstep(0.82, 1.0, ys) * (0.6 + 0.4 * value_noise(h, w, 6, nrng))
        blot = smoothstep(0.55, 0.8, fbm(h, w, 24, nrng))
        g = np.clip(streak * 0.5 + splash * 0.7 + blot * 0.35, 0, 1) * grime
        rgb *= (1 - g[..., None] * np.array([0.42, 0.45, 0.5]))
    out[..., :3] = rgb
    if cracks:
        img = Image.fromarray(np.clip(out, 0, 255).astype(np.uint8), "RGBA")
        over = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        l = lum(out[..., :3])
        # Cracks only on light plaster / stone pixels inside the requested band.
        cand = np.argwhere((alpha > 200) & (l > 120) &
                           (np.arange(h)[:, None] > h * crack_zone[0]) &
                           (np.arange(h)[:, None] < h * crack_zone[1]))
        if len(cand):
            for _ in range(cracks):
                y, x = cand[rng.randrange(len(cand))]
                _walk_crack(d, x, y, rng.randint(6, 16), rng)
        over_arr = np.asarray(over).astype(float)
        oa = over_arr[..., 3:4] / 255 * (alpha[..., None] > 0)
        out[..., :3] = out[..., :3] * (1 - oa) + over_arr[..., :3] * oa
    return out


def board_window(arr, box, seed):
    """Nail old planks across a window area (x0, y0, x1, y1) in sprite pixels."""
    rng = random.Random(seed)
    img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8), "RGBA")
    d = ImageDraw.Draw(img)
    x0, y0, x1, y1 = box
    n = 3
    for i in range(n):
        yc = y0 + (i + 0.5) * (y1 - y0) / n + rng.uniform(-3, 3)
        tilt = rng.uniform(-6, 6)
        hgt = rng.randint(9, 12)
        base = (118 + rng.randint(-15, 10), 88 + rng.randint(-10, 8), 60 + rng.randint(-8, 8), 255)
        poly = [(x0 - 5, yc - hgt / 2 - tilt), (x1 + 5, yc - hgt / 2 + tilt),
                (x1 + 5, yc + hgt / 2 + tilt), (x0 - 5, yc + hgt / 2 - tilt)]
        d.polygon(poly, fill=base, outline=(52, 36, 24, 255))
        d.line([(x0 - 3, yc - tilt + 1), (x1 + 3, yc + tilt + 1)], fill=(92, 66, 44, 255))
        for nx in (x0 - 1, x1 + 1):
            d.point((nx, yc - tilt if nx < x1 else yc + tilt), fill=(40, 40, 44, 255))
    return np.asarray(img).astype(float)
