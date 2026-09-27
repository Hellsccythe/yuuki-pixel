"""Map 2 of the bairro: "Moradias", the cramped residential streets west of Yuuki's street.

Plank shacks with patched tin roofs along narrow dirt lanes, an open drainage ditch crossed by
plank bridges, a communal well square with shared clotheslines, a yard with a chicken coop,
an abandoned house with a collapsing roof, trash heaps and mud. East edge leads back to the
Rua de Casa.
"""
import random

from assets import CHICKENS
from mapkit import MapLayout

MAP_W, MAP_H = 48, 36
ENTRY = (46.0, 13.35)          # arriving from the Rua de Casa (east)
RUA_ENTRY = (2.0, 13.35)       # arriving at the Rua de Casa from here (west edge over there)


def layout(m):
    rng = random.Random(21)
    # ---------------------------------------------------------------- ground
    m.roads.extend([
        (24, 11.4, 24, 3.9),     # main lane coming from the Rua de Casa
        (3.2, 11.8, 19.5, 3.2),  # narrower west of the ditch
        (3.0, 3.8, 3.0, 26.5),   # north-south lane on the west side
        (3.0, 27.8, 45, 2.5),    # lower lane
        (7.2, 15.2, 13.8, 8.0),   # communal square (well and clotheslines)
        (9.2, 26.6, 1.3, 1.6), (16.0, 26.6, 1.3, 1.6),
        (13.6, 4.2, 1.7, 7.6),   # alleys between the shacks
        (33.3, 4.2, 1.7, 7.6),
        (26.2, 26.6, 1.3, 1.6), (32.6, 26.6, 1.3, 1.6), (39.4, 26.6, 1.3, 1.6),
    ])
    m.ruts = [(12.9, (11.4, 15.3)), (14.0, (11.4, 15.3)), (28.6, (27.8, 30.3)), (29.5, (27.8, 30.3))]
    m.yards.extend([(24.8, 16.2, 10.5, 6.2)])   # packed earth of the chicken yard
    m.mud.extend([(30.5, 21.2, 2.4, 1.1), (21.0, 13.4, 1.4, 1.2), (24.2, 29.2, 1.5, 0.7),
                  (12.4, 20.2, 1.3, 0.5), (8.6, 33.2, 1.8, 0.7)])
    m.puddles.extend([(9.2, 12.4, 0.7, 0.3), (40.8, 13.9, 0.9, 0.35), (15.8, 29.4, 0.8, 0.3),
                      (4.4, 7.6, 0.6, 0.28), (36.2, 29.0, 0.7, 0.3), (16.8, 16.2, 0.6, 0.25)])

    # --------------------------------------------------------------- borders
    m.block(0, 0, 48, 3.4)
    m.block(-0.6, 0, 3.6, 36)                     # west: fences and scrub
    m.block(47.9, 0, 0.7, 11.4)
    m.block(47.9, 15.3, 0.7, 21)
    m.wall_row("muro", 0, 48, 35.9)
    m.block(0, 34.9, 48, 1.1)
    for x in (1.0, 4.4, 8.2, 12.2, 20.0, 25.4, 31.0, 36.2, 42.0, 46.6):
        m.obj("arvore-seca" if rng.random() < 0.5 else "arvore", x + rng.uniform(-.3, .3), 3.1 + rng.uniform(-.2, .2),
              (0.9, 0.5, 0.0), sway=1.0 + rng.random() * .8, shadow=2.3)
    for y in (8.0, 14.2, 20.5, 26.8, 33.0):
        m.obj("cerca-torta", 1.4, y, None, shadow=2.4)
        m.obj("mato-%d" % rng.randrange(6), 2.3, y + 0.8, sway=6)

    # ----------------------------------------- the open ditch and its plank bridges
    m.ditch(21.6, 3.4, 1.4, 31.5, bridges=[(11.5, 15.2), (27.8, 30.3)])

    # --------------------------------------------- north row, fronting the main lane
    m.building("barraco-0", 9.6, 11.2, depth=0.62, smoke_at=None)
    m.building("barraco-3", 17.8, 11.2, depth=0.62)
    m.building("casa-abandonada", 28.2, 11.2, depth=0.55)
    m.building("barraco-2", 39.0, 11.2, depth=0.62)
    m.building("barraco-4", 44.9, 11.2, depth=0.62)
    # alley ends: junk
    m.obj("lixo", 14.4, 5.4, (1.6, 0.6, 0.0), shadow=1.8)
    m.obj("lenha", 34.1, 5.2, (1.6, 0.5, 0.0), shadow=1.7)
    m.obj("mato-3", 13.9, 7.6, sway=6)
    m.obj("mato-0", 34.6, 8.4, sway=6)
    m.obj("barris-agua", 7.0, 11.4, (1.1, 0.4, 0.0), shadow=1.2)
    m.obj("caixotes", 20.6, 11.0, (1.2, 0.5, 0.0), shadow=1.3)
    m.obj("entulho-1", 31.6, 11.6)
    m.obj("entulho-0", 25.0, 11.5)

    # ------------------------------------------------------------ main lane
    m.hole(36.5, 14.3, 0.6, 0.35)
    m.hole(10.6, 12.5, 0.45, 0.3)
    m.obj("placa", 46.6, 11.6, (0.4, 0.3, 0.0), shadow=0.8, flip=True)  # points to the Rua de Casa
    m.obj("mato-1", 24.5, 15.6, sway=6)
    m.obj("mato-4", 6.8, 15.6, sway=6)

    # ------------------------------------------------ communal square (west of ditch)
    m.obj("poco", 13.4, 18.0, (1.9, 0.9, 0.0), shadow=2.2)
    m.laundry_line(10.0, 21.4, "varal-a", first=0)
    m.laundry_line(17.6, 21.2, "varal-b", first=3)
    m.obj("barris-agua", 8.3, 16.6, (1.1, 0.4, 0.0), shadow=1.2)
    m.obj("banco", 19.6, 16.4, (1.8, 0.45, 0.0), shadow=1.9)
    m.obj("lixo-2", 20.2, 22.7, (1.6, 0.6, 0.0), shadow=1.8)
    m.weeds([(7.9, 20.0, 2), (20.4, 19.4, 0), (11.2, 15.8, 5), (15.4, 22.6, 3)])
    # two more shacks crammed along the lower lane
    m.building("barraco-1", 9.8, 27.4, depth=0.62, flip=True)
    m.building("barraco-0", 16.4, 27.4, depth=0.62)
    m.obj("caixotes", 19.6, 27.2, (1.2, 0.5, 0.0), shadow=1.3)
    m.obj("barris-agua", 12.9, 27.5, (1.1, 0.4, 0.0), shadow=1.2)

    # ----------------------------------------- east block: chicken yard and houses
    m.obj("cerca-esq", 26.1, 16.1, (2.0, 0.4, 0.0), shadow=2)
    m.obj("cerca-torta", 42.2, 16.2, (3.0, 0.45, 0.0), shadow=2.6)
    m.obj("galinheiro", 29.6, 19.4, (3.0, 1.0, 0.0), shadow=3.2)
    m.chickens.append(dict(x=29.4, y=21.8, radius=1.8, frames=CHICKENS["branca"]))
    m.chickens.append(dict(x=31.8, y=20.4, radius=1.6, frames=CHICKENS["ruiva"]))
    m.obj("carroca-quebrada", 38.6, 18.8, (2.4, 0.7, 0.0), shadow=2.6)
    m.obj("horta", 44.2, 19.2, (2.2, 1.0, 0.1))
    m.obj("lenha", 46.4, 21.4, (1.6, 0.5, 0.0), shadow=1.7)
    m.weeds([(35.2, 17.2, 1), (41.2, 21.8, 3), (25.4, 21.6, 5), (47.0, 17.0, 0)])
    # houses fronting the lower lane
    m.building("barraco-1", 26.8, 27.4, depth=0.62)
    m.building("barraco-5", 33.4, 27.4, depth=0.62)
    m.building("casa-velha", 40.2, 27.4, depth=0.5, flip=True, smoke_at=(96, 18))
    m.building("barraco-4", 45.6, 27.4, depth=0.62, flip=True)
    m.block(23.0, 15.3, 1.4, 12.4)     # east bank of the ditch

    # ------------------------------------------------ lower lane and back lots
    m.hole(26.6, 32.5, 1.1, 0.6)
    m.hole(13.0, 31.6, 0.7, 0.45)
    m.obj("lixo", 9.2, 32.4, (1.6, 0.6, 0.0), shadow=1.8)
    m.obj("lixo-2", 31.4, 33.4, (1.6, 0.6, 0.0), shadow=1.8)
    m.laundry_line(40.4, 32.8, "varal-c", first=5)
    m.chickens.append(dict(x=44.6, y=32.4, radius=1.3, frames=CHICKENS["carijo"]))
    m.obj("arvore-seca", 4.2, 33.4, (0.8, 0.45, 0.0), sway=1.8, shadow=2.2)
    m.obj("arvore", 18.0, 34.2, (0.9, 0.5, 0.0), sway=1.2, shadow=2.4)
    m.obj("caixotes", 35.4, 33.6, (1.4, 0.55, 0.0), shadow=1.5)
    m.obj("entulho-2", 16.2, 31.2)
    m.obj("entulho-0", 46.4, 31.0)
    m.weeds([(6.2, 31.0, 0), (11.0, 34.0, 3), (20.2, 31.6, 1), (28.8, 34.2, 5), (37.8, 31.2, 2),
             (47.0, 34.0, 0), (24.8, 34.4, 4), (33.2, 31.0, 3)])

    # ------------------------------------------------------------------ exits
    m.exits.append(dict(id="saida-rua-de-casa", x=47.6, y=13.35, w=0.8, h=3.9, label="Rua de Casa",
                        targetMap="Bairro_RuaDeCasa", targetX=RUA_ENTRY[0], targetY=RUA_ENTRY[1]))
    m.block(47.9, 11.4, 0.7, 3.9)

    # ------------------------------------------------------------------- life
    m.npcs.extend([
        dict(id="lavadeira", variant="lavadeira", scale=1.14, speed=0.8, mode="patrol",
             points=[(8.6, 22.3), (11.6, 22.3)], waitMin=3, waitMax=7),
        dict(id="vizinha", variant="vizinha", scale=1.12, speed=0.9, mode="wander",
             rect=(8.4, 17.1, 3.4, 2.7), waitMin=2, waitMax=5),
        dict(id="crianca-a", variant="crianca-a", scale=0.82, speed=2.4, mode="wander",
             rect=(15.0, 16.9, 4.4, 3.3), waitMin=0.3, waitMax=1.4),
        dict(id="crianca-b", variant="crianca-b", scale=0.8, speed=2.2, mode="wander",
             rect=(15.0, 16.9, 4.4, 3.3), waitMin=0.3, waitMax=1.6),
        dict(id="crianca-c", variant="crianca-c", scale=0.78, speed=2.0, mode="wander",
             rect=(26.0, 29.0, 16.0, 0.8), waitMin=0.5, waitMax=2.0),
        dict(id="idoso", variant="idoso", scale=1.1, speed=0.55, mode="patrol",
             points=[(7.0, 13.7), (19.6, 13.7)], waitMin=3, waitMax=8),
        dict(id="morador", variant="morador", scale=1.22, speed=1.3, mode="patrol",
             points=[(25.2, 13.1), (46.2, 13.1)], waitMin=1.5, waitMax=4),
        dict(id="andarilho", variant="andarilho", scale=1.15, speed=1.1, mode="patrol",
             points=[(4.6, 29.1), (22.3, 29.0), (46.4, 29.1)], waitMin=2, waitMax=5),
        dict(id="lavadeira-2", variant="lavadeira", scale=1.1, speed=0.7, mode="patrol",
             points=[(38.8, 33.7), (42.0, 33.7)], waitMin=4, waitMax=8),
    ])
    m.birds.extend([dict(x=11.0, y=15.9, count=3), dict(x=33.0, y=13.0, count=4), dict(x=29.4, y=31.4, count=3)])


def build():
    m = MapLayout("moradias", "Moradias", "Bairro_Moradias", MAP_W, MAP_H, seed=31)
    layout(m)
    m.spawn = ENTRY
    return m
