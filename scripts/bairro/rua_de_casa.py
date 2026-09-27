"""Map 1 of the bairro: "Rua de Casa", Yuuki's street.

The main street is the spine of the map (west: Moradias, east: commercial district, north
road: school). Houses face the streets, yards are closed by fences, clutter stays against
walls. Yuuki's and Tenebris' houses (neighbours) sit on the lower lane; their interiors are
built in Unity by YuukiRpgRevisionBuilder inside the same footprint.
"""
import random

from mapkit import MapLayout
import moradias

MAP_W, MAP_H = 48, 36
ENTRY_FROM_MORADIAS = (2.2, 13.35)


def layout(m):
    rng = random.Random(7)
    # --------------------------------------------------------------- ground areas
    m.roads.extend([
        (0, 11.4, 48, 3.9),       # main street (west: Moradias, east: commercial district)
        (20, 0, 4, 11.6),         # road north to the school
        (2.8, 27.7, 43.6, 2.6),   # lower lane in front of the houses
        (7.3, 4.2, 3.2, 7.4),     # the alley (beco) of the story
        (2.8, 15, 3.2, 12.9),     # west path joining both streets
        (25, 15, 9.6, 12.8),      # small square with the well
        (44.4, 15, 1.8, 13.2),    # east footpath closing the loop
        (11.6, 24.6, 1.4, 3.2),   # Yuuki's gate path
        (20.2, 24.6, 1.4, 3.2),   # Tenebris' door path
        (39.6, 24.6, 1.4, 3.2),
    ])
    m.ruts = [(12.9, (11.4, 15.3)), (14.1, (11.4, 15.3)), (28.5, (27.7, 30.3)), (29.4, (27.7, 30.3))]
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

    # ------------------------------------------- north block, fronting the main street
    m.building("casa-pedra", 4.2, 11.2)
    m.obj("barris-agua", 1.4, 11.0, (1.1, 0.4, 0.0), shadow=1.2)
    m.building("oficina", 14.6, 11.2, smoke_at=(355, 20))
    m.obj("lenha", 18.4, 10.75, (1.6, 0.5, 0.0), shadow=1.7)           # firewood by the workshop
    m.obj("caixotes", 10.95, 10.9, (1.2, 0.5, 0.0), shadow=1.3, flip=True)
    m.building("casa-velha", 28.8, 11.2, smoke_at=(96, 18))
    m.building("casa-pedra-gasta", 44.0, 11.2)
    # The alley of the story: dirt floor, cracked walls, crooked fence and crates at the end.
    m.obj("muro-gasto", 8.9, 4.7, (4.2, 0.6, 0.0), shadow=4)
    m.obj("cerca-torta", 8.9, 5.6, (3.0, 0.45, 0.0), shadow=2.6)
    m.obj("caixotes", 7.95, 6.4, (1.4, 0.55, 0.0), shadow=1.5)
    m.obj("caixotes", 9.95, 6.1, (1.4, 0.55, 0.0), shadow=1.5, flip=True)
    m.inspect(8.9, 7.0, "O beco", "Caixotes empilhados e uma cerca torta fecham o fundo do beco. "
              "As paredes têm rachaduras fundas e a tinta já quase saiu.")
    m.weeds([(7.6, 9.6, 3), (10.1, 7.2, 0)])
    m.obj("entulho-0", 9.9, 9.4)
    # Vacant lot between the old houses.
    m.obj("arvore-seca", 36.2, 6.8, (0.8, 0.45, 0.0), sway=1.6, shadow=2.2)
    m.obj("muro-gasto", 34.4, 5.2, (4.2, 0.6, 0.0), shadow=4)
    m.obj("entulho-1", 38.9, 6.2)
    m.obj("caixotes", 39.6, 10.4, (1.4, 0.55, 0.0), shadow=1.5)
    m.hole(38.2, 8.6, 1.25, 0.75)
    m.weeds([(33.2, 7.2, 0), (35.3, 9.9, 3), (40.4, 7.6, 1), (32.8, 10.6, 4), (37.6, 5.6, 5)])

    # ------------------------------------------------------------- main street
    m.hole(6.2, 13.9, 0.55, 0.35)
    m.hole(33.2, 12.6, 0.75, 0.42)
    for (x, y) in ((11.9, 11.25), (24.7, 11.3), (35.2, 15.75), (6.6, 15.75), (46.6, 11.3)):
        m.lamp_post(x, y)
    m.sign("placa", 1.5, 11.15, "Moradias", "‹ Moradias\n\nAs vielas de tábua do outro lado da valeta.", flip=True)
    m.sign("placa", 19.5, 11.9, "Escola do bairro",
           "↑ Escola do bairro\n\nOs portões estão fechados para reforma.")
    m.sign("placa", 46.9, 15.95, "Distrito comercial",
           "Distrito comercial ›\n\nPadaria, mercearia e alfaiataria. A passagem está interditada por enquanto.")
    m.weeds([(24.6, 11.7, 1), (47.3, 15.3, 4), (2.2, 15.5, 0)])

    # --------------------------------- south block: low cracked walls along the street
    m.wall_row("muro", 7.4, 24.8, 16.3)
    m.wall_row("muro", 35.6, 43.4, 16.3)
    # Yuuki's home: old but carefully kept.
    door_x = m.building("casa-yuuki", 11.5, 24.8, depth=0.5, door=0.62, smoke_at=(95, 14))
    m.obj("cerca-esq", 8.75, 27.45, (2.0, 0.4, 0.0), shadow=2)
    m.obj("cerca-esq", 10.75, 27.45, (2.0, 0.4, 0.0), shadow=2)
    m.obj("cerca-dir", 14.05, 27.45, (2.2, 0.4, 0.0), shadow=2)
    m.obj("cerca-dir", 15.2, 27.4, (1.0, 0.4, 0.0), shadow=1)
    m.obj("horta", 8.9, 26.9, (2.2, 1.0, 0.1))
    m.obj("caixotes", 15.0, 26.5, (1.3, 0.5, 0.0), shadow=1.4)
    m.inspect(12.2, 27.9, "Portão antigo", "A madeira tem marcas do tempo, mas o portão continua firme. "
              "Sara e Kled cuidam de tudo o que podem.", radius=1.0)
    # Tenebris' family, next door.
    m.building("casa-tenebris", 20.8, 24.8, depth=0.5)
    m.obj("banco", 23.6, 26.5, (1.8, 0.45, 0.0), shadow=1.9)
    m.weeds([(17.6, 26.9, 2), (24.6, 25.0, 0)])
    # Small square with the old well: the heart of the street.
    m.obj("poco", 29.6, 21.4, (1.9, 0.9, 0.0), shadow=2.2)
    m.inspect(29.6, 22.2, "Poço da praça", "O poço mais antigo da rua. A corda é nova; alguém sempre troca "
              "antes que arrebente.")
    m.obj("banco", 32.6, 23.8, (1.8, 0.45, 0.0), shadow=1.9)
    m.obj("arvore", 33.4, 18.4, (0.9, 0.5, 0.0), sway=1.2, shadow=2.4)
    m.env("amarelinha", 27.4, 25.6)                  # hopscotch for the kids
    m.weeds([(25.6, 26.8, 4), (34.0, 26.6, 3)])
    # House east of the square and the dry corner by the footpath.
    m.building("casa-madeira-gasta", 39.5, 24.8, depth=0.5, smoke_at=(313, 16))
    m.obj("arvore-seca", 47.0, 21.2, (0.8, 0.45, 0.0), sway=1.8, shadow=2.2)
    m.obj("entulho-1", 43.6, 25.8)
    m.obj("caixotes", 42.9, 26.6, (1.4, 0.55, 0.0), shadow=1.5)
    m.weeds([(44.0, 18.6, 5), (47.2, 25.4, 1)])
    # West path.
    m.obj("arvore-seca", 1.4, 20.6, (0.8, 0.45, 0.0), sway=1.8, shadow=2.2)
    m.weeds([(6.6, 26.6, 1), (2.3, 24.0, 3)])
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
    m.obj("entulho-0", 13.6, 34.2)
    m.obj("entulho-1", 36.6, 34.0)
    m.obj("entulho-2", 45.8, 34.0)
    m.weeds([(5.6, 34.4, 0), (12.2, 34.4, 3), (15.4, 34.2, 1), (27.4, 34.4, 5), (34.2, 34.3, 2),
             (43.3, 34.3, 0), (47.2, 33.6, 3), (20.4, 34.5, 4)])

    # ------------------------------------------------------------------ exits
    m.exits.extend([
        dict(id="saida-escola", x=22.0, y=0.9, w=4.0, h=0.8, label="Escola do bairro",
             targetMap="", targetX=0, targetY=0),
        dict(id="saida-moradias", x=0.4, y=13.35, w=0.8, h=3.9, label="Moradias",
             targetMap="Bairro_Moradias", targetX=moradias.ENTRY[0], targetY=moradias.ENTRY[1]),
        dict(id="saida-comercio", x=47.6, y=13.35, w=0.8, h=3.9, label="Distrito comercial",
             targetMap="", targetX=0, targetY=0),
    ])
    m.block(20, -0.6, 4, 0.8)
    m.block(-0.6, 11.4, 0.7, 3.9)
    m.block(47.9, 11.4, 0.7, 3.9)

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
             points=[(12.8, 12.2), (16.6, 12.0)], waitMin=3, waitMax=8),
        dict(id="andarilho", variant="andarilho", scale=1.15, speed=1.1, mode="patrol",
             points=[(3.5, 29.0), (24, 28.8), (45.2, 29.1)], waitMin=2, waitMax=5),
    ])
    m.birds.extend([dict(x=31.2, y=25.8, count=3), dict(x=22.2, y=13.0, count=4), dict(x=35.4, y=10.4, count=3),
                    dict(x=12.0, y=30.8, count=2)])
    return door_x


def build():
    m = MapLayout("rua-de-casa", "Rua de Casa", "Bairro_RuaDeCasa", MAP_W, MAP_H, seed=3)
    door_x = layout(m)
    m.spawn = (door_x, 25.95)   # on Yuuki's porch
    return m
