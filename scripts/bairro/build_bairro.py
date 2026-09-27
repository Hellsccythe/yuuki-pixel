"""Rebuild the whole bairro: shared sprites, then every modular map (ground, JSON, preview).

Run:  python3 scripts/bairro/build_bairro.py
Then in Unity: Yuuki > Bairro > Construir todo o bairro.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import assets
import moradias
import rua_de_casa

MAPS = [rua_de_casa, moradias]


def main():
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
