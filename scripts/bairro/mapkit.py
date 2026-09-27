"""Toolkit to lay out one modular map of the bairro and export it for Unity.

Design coordinates are tiles (1 tile = 1 Unity unit) with x to the right and y DOWN from the
map's top-left corner, like a drawing. Export converts to Unity coordinates (y up).
"""
import json
import math
import random

import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

from common import ROOT, fbm, value_noise, smoothstep, tile, desaturate, terrain_textures
from assets import G, MAPS, sprites, size_units, register_ground, FX


class MapLayout:
    def __init__(self, map_id, name, scene, w, h, seed):
        self.id, self.name, self.scene = map_id, name, scene
        self.w, self.h, self.seed = w, h, seed
        self.objects, self.blockers, self.portals, self.exits = [], [], [], []
        self.npcs, self.birds, self.smoke, self.chickens = [], [], [], []
        self.shadows = []
        self.roads, self.cobble, self.puddles, self.holes, self.yards = [], [], [], [], []
        self.ruts = []    # (line_y, (lane_y0, lane_y1))
        self.water = []   # open ditch rectangles (x, y, w, h)
        self.bridges = []  # plank bridges over the ditch (x, y, w, h)
        self.mud = []     # (x, y, rx, ry) wet dark earth, walkable
        self.extra_areas = []  # interiors: dict(id, name, x, y, w, h, ground, painter)
        self.spawn = (w / 2, h / 2)

    # ------------------------------------------------------------- placement
    def obj(self, sid, x, y, col=None, sway=0.0, swing=False, shadow=None, flip=False, group=""):
        """Sprite with its pivot (feet) at design (x, y). col = (w, h, lift) in tiles."""
        o = dict(sprite=sid, x=x, y=y, sway=sway, swing=swing, flipX=flip, sortBias=0.0, group=group,
                 colW=0.0, colH=0.0, colX=0.0, colY=0.0)
        if col:
            w, h, lift = col
            o.update(colW=w, colH=h, colX=0.0, colY=lift + h / 2)
        self.objects.append(o)
        if shadow:
            self.shadows.append((x, y, shadow))
        return o

    def building(self, sid, cx, feet_y, depth=0.52, door=None, smoke_at=None, flip=False, width_frac=0.9):
        w, h = size_units(sid)
        self.obj(sid, cx, feet_y, (w * width_frac, h * depth - 0.35, 0.35), shadow=w * 0.95, flip=flip)
        if smoke_at:
            sx, sy = smoke_at  # chimney top in sprite pixels (from the top-left)
            s = sprites[sid]
            if flip:
                sx = s["w"] - sx
            self.smoke.append(dict(x=cx + (sx - s["w"] * s["pivotX"]) / s["ppu"], y=feet_y - (s["h"] - sy) / s["ppu"]))
        if door is not None:
            return cx - w / 2 + (1 - door if flip else door) * w
        return None

    def block(self, x, y, w, h, kind="wall"):
        """Axis-aligned blocker given by its top-left corner."""
        self.blockers.append(dict(x=x + w / 2, y=y + h / 2, w=w, h=h, kind=kind))

    def hole(self, x, y, rx, ry):
        self.holes.append((x, y, rx, ry))
        self.block(x - rx * 0.85, y - ry * 0.75, rx * 1.7, ry * 1.5, "hole")

    def ditch(self, x, y, w, h, bridges=()):
        """Open drainage ditch, blocked except where plank bridges (ranges along it) cross it."""
        self.water.append((x, y, w, h))
        vertical = h > w
        pos, end = (y, y + h) if vertical else (x, x + w)

        def span(a, b, kind):
            if b - a <= 0.01:
                return
            if kind == "water":
                if vertical:
                    self.block(x, a, w, b - a, "water")
                else:
                    self.block(a, y, b - a, h, "water")
            elif vertical:
                self.bridges.append((x - 0.3, a, w + 0.6, b - a))
            else:
                self.bridges.append((a, y - 0.3, b - a, h + 0.6))

        for b0, b1 in sorted(bridges):
            span(pos, b0, "water")
            span(b0, b1, "bridge")
            pos = b1
        span(pos, end, "water")

    def wall_row(self, sid, x0, x1, feet_y, alt="muro-gasto"):
        w, _ = size_units(sid)
        x, i = x0 + w / 2, 0
        while x - w / 2 < x1 - 0.5:
            self.obj(sid if i % 3 != 2 else alt, min(x, x1 - w / 2), feet_y, (w * 0.96, 0.6, 0.0),
                     shadow=w * 0.9, flip=i % 2 == 1)
            x += w * 0.97
            i += 1

    def laundry_line(self, x, y, group, first=0, count=5):
        from props import rope_y
        self.obj("varal", x, y, None, group=group)
        s = sprites["varal"]
        for i, px in enumerate((34, 76, 118, 160, 200)[:count]):
            ox = x + (px - s["w"] / 2) / 64
            oy = y - (s["h"] - rope_y(px)) / 64
            self.obj(f"roupa-{(first + i) % 8}", ox, oy, swing=True, sway=10 + i, group=group)
        self.block(x - 1.9, y - 0.25, 0.25, 0.3)
        self.block(x + 1.65, y - 0.25, 0.25, 0.3)

    def weeds(self, spots):
        for (x, y, k) in spots:
            self.obj(f"mato-{k}", x, y, sway=6)

    # ---------------------------------------------------------------- ground
    def _rect_mask(self, rects, blur, noise_amt, rng, cell=40):
        h, w = self.h * G, self.w * G
        m = np.zeros((h, w))
        for (x, y, rw, rh) in rects:
            m[max(0, int(y * G)):int((y + rh) * G), max(0, int(x * G)):int((x + rw) * G)] = 1
        m = ndi.gaussian_filter(m, blur)
        n = fbm(h, w, cell, rng) - 0.5
        return smoothstep(0.42, 0.58, m + n * noise_amt)

    def _ellipse(self, cx, cy, rx, ry, rng, wobble=0.18):
        h, w = self.h * G, self.w * G
        yy, xx = np.mgrid[0:h, 0:w]
        d = ((xx - cx * G) / (rx * G)) ** 2 + ((yy - cy * G) / (ry * G)) ** 2
        return d + (value_noise(h, w, 10, rng) - 0.5) * wobble * 4

    def paint_ground(self, grass_dry=0.5, bald_level=0.55):
        rng = np.random.default_rng(self.seed)
        prng = random.Random(self.seed)
        tex = terrain_textures()
        h, w = self.h * G, self.w * G
        grass = tile(tex["grass"], h, w)
        dirt = tile(tex["dirt"], h, w, 37, 91)
        cobble = tile(tex["cobble"], h, w, 120, 12)
        dry = desaturate(grass, grass_dry) * np.array([1.12, 1.02, 0.74])
        grass = desaturate(grass, 0.25) * np.array([1.0, 0.97, 0.86])
        mix = fbm(h, w, 90, rng)
        ground = grass * (1 - mix[..., None]) + dry * mix[..., None]
        bald = smoothstep(bald_level, bald_level + 0.11, fbm(h, w, 60, rng))
        ground = ground * (1 - bald[..., None]) + (dirt * 0.92) * bald[..., None]

        road = self._rect_mask(self.roads, 14, 0.55, rng)
        tone = 0.84 + 0.26 * fbm(h, w, 70, rng)
        street = dirt * tone[..., None]
        yy, xx = np.mgrid[0:h, 0:w]
        ruts = np.zeros((h, w))
        lanes = np.zeros((h, w), bool)
        for base, (l0, l1) in self.ruts:
            wob = np.sin(xx / G * 0.45 + base) * 0.18 * G + (value_noise(h, w, 80, rng) - 0.5) * 0.4 * G
            dy = np.abs(yy - base * G - wob)
            ruts += np.exp(-(dy / 6) ** 2) * 0.9 - np.exp(-((dy - 9) / 4) ** 2) * 0.25
            lanes |= (yy > l0 * G) & (yy < l1 * G)
        ruts *= lanes * (0.6 + 0.4 * value_noise(h, w, 50, rng))
        street *= (1 - ruts[..., None] * 0.2)
        ground = ground * (1 - road[..., None]) + street * road[..., None]

        if self.cobble:
            cob = self._rect_mask(self.cobble, 10, 0.6, rng, 30)
            cob *= smoothstep(0.4, 0.55, fbm(h, w, 26, rng))
            ground = ground * (1 - cob[..., None]) + desaturate(cobble, 0.35) * 0.92 * cob[..., None]
        if self.yards:
            yard = self._rect_mask(self.yards, 6, 0.2, rng)
            ground = ground * (1 - yard[..., None] * 0.5) + (dirt * 1.08) * yard[..., None] * 0.5

        # Mud patches: dark, wet, a few footprints.
        for (cx, cy, rx, ry) in self.mud:
            f = self._ellipse(cx, cy, rx, ry, rng, 0.25)
            m = smoothstep(1.2, 0.7, f)
            ground = ground * (1 - m[..., None] * 0.55) + np.array([70, 54, 40]) * m[..., None] * 0.55

        img = Image.fromarray(np.clip(ground, 0, 255).astype(np.uint8))
        over = Image.new("RGBA", img.size, (0, 0, 0, 0))
        d = ImageDraw.Draw(over)
        road_pts = np.argwhere(road > 0.8)
        n_scale = len(road_pts) / 400000
        for _ in range(int(260 * n_scale)):
            y, x = road_pts[prng.randrange(len(road_pts))]
            pts, a = [(x, y)], prng.uniform(0, math.tau)
            for _ in range(prng.randint(4, 12)):
                a += prng.uniform(-0.8, 0.8)
                x += math.cos(a) * 4
                y += math.sin(a) * 4
                pts.append((x, y))
            d.line(pts, fill=(58, 42, 30, 120), width=1)
        for _ in range(int(1400 * n_scale)):
            y, x = road_pts[prng.randrange(len(road_pts))]
            c = prng.choice([(170, 156, 132), (140, 126, 106), (190, 178, 150)])
            d.rectangle([x, y, x + prng.choice([1, 2]), y + 1], fill=c + (220,))
            d.point((x, y + 2), fill=(50, 38, 28, 140))
        for _ in range(int(60 * n_scale)):
            y, x = road_pts[prng.randrange(len(road_pts))]
            if prng.random() < 0.5:
                d.polygon([(x, y), (x + 7, y - 1), (x + 8, y + 5), (x + 1, y + 6)], fill=(214, 204, 178, 230),
                          outline=(130, 120, 100, 200))
            else:
                for _ in range(4):
                    d.line([(x, y), (x + prng.randint(-6, 6), y + prng.randint(-2, 2))], fill=(196, 170, 100, 220))
        for _ in range(int(90 * n_scale)):
            y, x = road_pts[prng.randrange(len(road_pts))]
            r = prng.randint(6, 18)
            d.ellipse([x - r, y - r * .6, x + r, y + r * .6], fill=(40, 30, 22, 38))
        img = Image.alpha_composite(img.convert("RGBA"), over).convert("RGB")
        ground = np.asarray(img).astype(float)

        sh = np.zeros((h, w))
        for (x, y, sw) in self.shadows:
            e = ((xx - x * G) / (sw * G / 2)) ** 2 + ((yy - (y - 0.15) * G) / (0.42 * G)) ** 2
            sh = np.maximum(sh, np.clip(1 - e, 0, 1))
        ground *= (1 - ndi.gaussian_filter(sh, 5)[..., None] * 0.45)

        # Open ditch: murky water with scum, dark wet banks.
        if self.water:
            wm = self._rect_mask(self.water, 3, 0.25, rng, 12)
            bank = np.clip(ndi.gaussian_filter(wm, 9) * 1.6, 0, 1) * (1 - wm)
            ground = ground * (1 - bank[..., None] * 0.5) + np.array([60, 46, 34]) * bank[..., None] * 0.2
            murk = np.array([52, 56, 46]) * (0.78 + 0.35 * fbm(h, w, 14, rng))[..., None]
            flow = (np.sin(yy / 9.0 + np.sin(xx / 5.0) * 1.5) > 0.86) * 0.12  # slow ripples
            murk *= (1 + flow[..., None])
            scum = smoothstep(0.68, 0.78, fbm(h, w, 10, rng))
            murk = murk * (1 - scum[..., None] * 0.8) + np.array([96, 102, 56]) * scum[..., None] * 0.8
            ground = ground * (1 - wm[..., None]) + murk * wm[..., None]
            glint = wm * (np.abs(((xx * 0.7 + yy) % 31) - 3) < 1) * 0.35
            ground += glint[..., None] * 50
        # Plank bridges over the ditch.
        img = Image.fromarray(np.clip(ground, 0, 255).astype(np.uint8)).convert("RGBA")
        d = ImageDraw.Draw(img)
        for (bx, by, bw, bh) in self.bridges:
            x0, y0, x1, y1 = bx * G, by * G, (bx + bw) * G, (by + bh) * G
            d.rectangle([x0 - 2, y0 - 2, x1 + 2, y1 + 6], fill=(30, 22, 16, 150))
            vertical_boards = bw > bh  # boards span the ditch: across a N-S ditch they lie E-W
            step = 14
            if not vertical_boards:
                for y in range(int(y0), int(y1), step):
                    c = prng.choice([(128, 96, 64), (116, 86, 58), (140, 106, 72), (104, 78, 52)])
                    d.rectangle([x0 + prng.randint(-4, 2), y, x1 + prng.randint(-2, 4), y + step - 2], fill=c + (255,),
                                outline=(56, 40, 26, 255))
            else:
                for x in range(int(x0), int(x1), step):
                    c = prng.choice([(128, 96, 64), (116, 86, 58), (140, 106, 72), (104, 78, 52)])
                    d.rectangle([x, y0 + prng.randint(-4, 2), x + step - 2, y1 + prng.randint(-2, 4)], fill=c + (255,),
                                outline=(56, 40, 26, 255))
        ground = np.asarray(img.convert("RGB")).astype(float)

        for (cx, cy, rx, ry) in self.puddles:
            f = self._ellipse(cx, cy, rx, ry, rng, 0.12)
            wet, water = smoothstep(1.9, 1.0, f), smoothstep(1.05, 0.9, f)
            ground *= (1 - wet[..., None] * 0.28)
            refl = np.array([118, 132, 146]) * (0.75 + 0.35 * smoothstep(cy * G + ry * G, cy * G - ry * G, yy))[..., None]
            ground = ground * (1 - water[..., None] * 0.85) + refl * water[..., None] * 0.85
            ground += (water * (np.abs(((xx - yy * 0.6) % 23) - 3) < 1) * 0.5)[..., None] * 60
        for (cx, cy, rx, ry) in self.holes:
            f = self._ellipse(cx, cy, rx, ry, rng, 0.14)
            inside = smoothstep(1.02, 0.9, f)
            rim = smoothstep(1.7, 1.05, f) * (1 - inside)
            v = np.clip((yy - (cy - ry) * G) / (2 * ry * G), 0, 1)
            wall = np.array([104, 78, 56]) * (1 - v[..., None] * 0.9)
            deep = smoothstep(0.35, 0.7, v)[..., None]
            pit = wall * (1 - deep) + np.array([22, 16, 12]) * deep
            ground = ground * (1 - inside[..., None]) + pit * inside[..., None]
            top, bottom = rim * (yy < cy * G), rim * (yy >= cy * G)
            ground *= (1 - top[..., None] * 0.35)
            ground = ground * (1 - bottom[..., None] * 0.35) + np.array([176, 150, 116]) * bottom[..., None] * 0.35

        ground = desaturate(ground, 0.12) * np.array([1.03, 0.99, 0.92])
        return np.clip(ground, 0, 255)

    # ---------------------------------------------------------------- export
    def uy(self, y):
        return round(self.h - y, 4)

    def export(self, npc_variants):
        MAPS.mkdir(parents=True, exist_ok=True)
        gid = f"{self.id}_chao"
        Image.fromarray(self.paint_ground().astype(np.uint8)).save(MAPS / f"{gid}.png", optimize=True)
        register_ground(gid, MAPS / f"{gid}.png", self.w, self.h)
        areas = [dict(id=self.id, name=self.name, x=0, y=0, w=self.w, h=self.h, ground=gid, outdoor=True)]
        for a in self.extra_areas:
            agid = f"{a['id']}_chao"
            Image.fromarray(a["painter"]().astype(np.uint8)).save(MAPS / f"{agid}.png", optimize=True)
            register_ground(agid, MAPS / f"{agid}.png", a["w"], a["h"])
            areas.append(dict(id=a["id"], name=a["name"], x=a["x"], y=self.h - a["y"] - a["h"], w=a["w"], h=a["h"],
                              ground=agid, outdoor=False))
        used = {o["sprite"] for o in self.objects} | {a["ground"] for a in areas}
        used |= set(FX["leaves"]) | set(FX["pigeon"]) | {FX["dust"], FX["paper"], FX["cloud"], FX["smoke"]}
        variants = [v for v in npc_variants if any(n["variant"] == v["id"] for n in self.npcs)]
        for v in variants:
            used |= set(v["walkLeft"]) | set(v["walkRight"]) | {v["idleLeft"], v["idleRight"]}
        for c in self.chickens:
            used |= set(c["frames"])
        data = dict(
            version=1, map=self.id, name=self.name, scene=self.scene,
            sprites=[{k: v for k, v in sprites[s].items() if k not in ("w", "h")} for s in sorted(used)],
            areas=areas,
            objects=[dict(o, y=self.uy(o["y"])) for o in self.objects],
            blockers=[dict(b, y=self.uy(b["y"])) for b in self.blockers],
            portals=[dict(p, y=self.uy(p["y"]), targetY=self.uy(p["targetY"])) for p in self.portals],
            exits=[dict(e, y=self.uy(e["y"]), targetY=self.uy(e["targetY"]) if e.get("targetMap") else 0)
                   for e in self.exits],
            npcs=[dict(id=n["id"], variant=n["variant"], scale=n["scale"], speed=n["speed"], mode=n["mode"],
                       waitMin=n["waitMin"], waitMax=n["waitMax"],
                       points=[dict(x=p[0], y=self.uy(p[1])) for p in n.get("points", [])],
                       rect=dict(x=n["rect"][0], y=self.uy(n["rect"][1] + n["rect"][3]), w=n["rect"][2],
                                 h=n["rect"][3]) if "rect" in n else dict(x=0, y=0, w=0, h=0))
                  for n in self.npcs],
            npcVariants=variants,
            birds=[dict(b, y=self.uy(b["y"])) for b in self.birds],
            chickens=[dict(x=c["x"], y=self.uy(c["y"]), radius=c["radius"], frames=c["frames"]) for c in self.chickens],
            smoke=[dict(x=s["x"], y=self.uy(s["y"]), interior=s.get("interior", False)) for s in self.smoke],
            player=dict(x=self.spawn[0], y=self.uy(self.spawn[1]), area=self.id),
            fx=FX,
        )
        path = MAPS / f"{self.id}.json"
        path.write_text(json.dumps(data, ensure_ascii=False, indent=1), encoding="utf-8")
        return data

    def preview(self, data, scale=24):
        """Compose ground + sprites with Y sorting to check the map without Unity."""
        k = scale / G
        base = Image.open(ROOT / sprites[data["areas"][0]["ground"]]["path"]).convert("RGBA")
        canvas = base.resize((int(base.width * k), int(base.height * k)), Image.LANCZOS)
        rooms = []
        width = canvas.width
        for a in data["areas"][1:]:
            im = Image.open(ROOT / sprites[a["ground"]]["path"]).convert("RGBA")
            im = im.resize((int(im.width * k), int(im.height * k)), Image.LANCZOS)
            rooms.append((a, width + scale * 2, im))
            width += scale * 2 + im.width
        full = Image.new("RGBA", (width, canvas.height), (12, 12, 14, 255))
        full.alpha_composite(canvas)
        for a, ox, im in rooms:
            full.alpha_composite(im, (ox, int((self.h - a["y"] - a["h"]) * scale)))

        def to_px(ux, uy):
            for a, ox, _ in rooms:
                if a["x"] <= ux <= a["x"] + a["w"]:
                    return ox + (ux - a["x"]) * scale, (self.h - uy) * scale
            return ux * scale, (self.h - uy) * scale

        group_y = {o["group"]: o["y"] for o in data["objects"] if o["group"] and not o["swing"]}
        items = [((group_y[o["group"]] - 0.001) if o["swing"] else o["y"], o) for o in data["objects"]]
        for n in data["npcs"]:
            p = n["points"][0] if n["points"] else dict(x=n["rect"]["x"] + n["rect"]["w"] / 2,
                                                       y=n["rect"]["y"] + n["rect"]["h"] / 2)
            v = next(v for v in data["npcVariants"] if v["id"] == n["variant"])
            items.append((p["y"], dict(sprite=v["walkRight"][1], x=p["x"], y=p["y"], scale=n["scale"])))
        for c in data["chickens"]:
            for i in range(3):
                a = i * 2.1
                cx, cy = c["x"] + math.cos(a) * c["radius"] * .5, c["y"] + math.sin(a) * c["radius"] * .4
                items.append((cy, dict(sprite=c["frames"][i % 2], x=cx, y=cy, flipX=i % 2 == 1)))
        items.append((data["player"]["y"], dict(sprite="__yuuki", x=data["player"]["x"], y=data["player"]["y"])))
        yuuki = Image.open(ROOT / "Assets/Game/Art/Yuuki/Yuuki_Idle_2x1.png").convert("RGBA").crop((512, 0, 1024, 512))
        for _, o in sorted(items, key=lambda t: -t[0]):
            if o["sprite"] == "__yuuki":
                im, ppu, pv, sc = yuuki, 200, (0.5, 112 / 512), 1.15
            else:
                s = sprites[o["sprite"]]
                im = Image.open(ROOT / s["path"]).convert("RGBA")
                ppu, pv, sc = s["ppu"], (s["pivotX"], s["pivotY"]), o.get("scale", 1.0)
                if o.get("flipX"):
                    im = im.transpose(Image.FLIP_LEFT_RIGHT)
                    pv = (1 - pv[0], pv[1])
            f = scale / ppu * sc
            im = im.resize((max(1, int(im.width * f)), max(1, int(im.height * f))), Image.LANCZOS)
            px, py = to_px(o["x"], o["y"])
            full.alpha_composite(im, (int(px - pv[0] * im.width), int(py - (1 - pv[1]) * im.height)))
        out = ROOT / f"docs/bairro/{self.id}-preview.png"
        out.parent.mkdir(parents=True, exist_ok=True)
        full.convert("RGB").save(out, optimize=True)
        return out
