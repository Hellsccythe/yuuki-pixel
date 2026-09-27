"""Rebuild the whole bairro: shared sprites, then every modular map (ground, JSON, preview).

Run:  python3 scripts/bairro/build_bairro.py
Then in Unity: Yuuki > Bairro > Construir todo o bairro.
"""
import sys
import json
from pathlib import Path
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent))
import assets
import moradias
import rua_de_casa

MAPS = [rua_de_casa, moradias]


def main():
    if '--layouts-only' in sys.argv:
        # Reuse art and NPCs without recolouring or reimporting their pixels.
        variants_by_id = {}
        for path in assets.MAPS.glob('*.json'):
            data = json.loads(path.read_text(encoding='utf-8'))
            for s in data['sprites']:
                w,h = Image.open(assets.ROOT/s['path']).size
                assets.sprites[s['id']] = dict(s,w=w,h=h)
            variants_by_id.update({v['id']:v for v in data['npcVariants']})
        variants = list(variants_by_id.values())
    else:
        assets.build_sprites()
        variants = assets.build_npcs()
    for module in MAPS:
        m = module.build()
        data = m.export(variants)
        out = m.preview(data)
        print(f"{m.name}: {len(m.objects)} objects, {len(m.blockers)} blockers, {len(m.npcs)} NPCs, "
              f"{len(data['sprites'])} sprites -> {out.name}")


if __name__ == "__main__":
    main()
