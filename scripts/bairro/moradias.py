"""Map 2 of the bairro: "Moradias", the cramped residential streets west of Yuuki's street.

One main lane crosses the map from the Rua de Casa (east) and narrows as it goes west. Plank
shacks face it, each with a scrap of yard; an open ditch crossed by two plank bridges splits
the neighbourhood; the communal well square is the social hub. In the south-east corner an
abandoned yard hides the entrance to the small dungeon behind a rotten fence.
"""
import random

from assets import CHICKENS
from mapkit import MapLayout

MAP_W, MAP_H = 48, 36
ENTRY = (46.0, 13.35)          # arriving from the Rua de Casa (east)
RUA_ENTRY = (2.2, 13.35)       # arriving at the Rua de Casa from here (its west edge)
DUNGEON_DOOR = (45.7, 25.45)   # where Yuuki stands to go down (and comes back up)


def layout(m, dungeon_entry):
    rng = random.Random(21)
    # ---------------------------------------------------------------- ground
    m.roads.extend([
        (30, 11.4, 18, 3.9),       # main lane coming from the Rua de Casa
        (18, 11.8, 12.5, 3.3),     # ... narrower past the ditch
        (3.2, 12.3, 15.5, 3.0),    # ... and narrower still in the west
        (3.2, 5.0, 3.0, 25.3),     # north-south lane on the west side
        (3.2, 27.7, 35.5, 2.6),    # lower lane, ending at the abandoned yard
        (7.6, 15.6, 12.8, 8.0),    # communal square
        (11.0, 5.6, 1.8, 6.8),     # alleys between the north shacks
        (31.2, 5.6, 1.6, 6.2),
        (9.2, 26.6, 1.3, 1.6), (16.0, 26.6, 1.3, 1.6), (25.8, 26.6, 1.3, 1.6), (32.0, 26.6, 1.3, 1.6),
    ])
    m.ruts = [(13.0, (11.4, 15.3)), (14.1, (11.4, 15.3)), (28.6, (27.7, 30.3)), (29.5, (27.7, 30.3))]
    m.yards.extend([(23.8, 15.8, 12.0, 5.4)])      # packed earth of the chicken yard
    m.mud.extend([(29.6, 20.6, 2.4, 1.0), (21.0, 13.6, 1.4, 1.1), (24.2, 29.2, 1.5, 0.7),
                  (8.6, 33.2, 1.8, 0.7), (40.6, 30.6, 2.6, 1.2), (44.8, 25.9, 1.6, 0.6), (38.2, 24.4, 1.4, 0.7)])
    m.puddles.extend([(9.2, 13.0, 0.7, 0.3), (40.8, 13.9, 0.9, 0.35), (15.8, 29.4, 0.8, 0.3),
                      (4.4, 7.6, 0.6, 0.28), (34.2, 29.0, 0.7, 0.3), (12.2, 16.2, 0.6, 0.25), (42.6, 32.8, 0.9, 0.35)])

    # --------------------------------------------------------------- borders
    m.block(0, 0, 48, 3.4)
    m.block(-0.6, 0, 3.8, 36)                      # west: fences and scrub
    m.block(47.9, 0, 0.7, 11.4)
    m.block(47.9, 15.3, 0.7, 21)
    m.wall_row("muro", 0, 48, 35.9)
    m.block(0, 34.9, 48, 1.1)
    for x in (1.0, 4.4, 8.2, 12.2, 20.0, 25.4, 31.0, 36.2, 42.0, 46.6):
        m.obj("arvore-seca" if rng.random() < 0.5 else "arvore", x + rng.uniform(-.3, .3), 3.1 + rng.uniform(-.2, .2),
              (0.9, 0.5, 0.0), sway=1.0 + rng.random() * .8, shadow=2.3)
    for y in (8.0, 14.2, 20.5, 26.8, 33.0):
        m.obj("cerca-torta", 1.4, y, None, shadow=2.4)
        m.obj("mato-%d" % rng.randrange(6), 2.4, y + 0.8, sway=6)

    # ------------------------------------------ the open ditch and its plank bridges
    m.ditch(22.0, 3.4, 1.4, 31.5, bridges=[(11.8, 15.1), (27.7, 30.3)])
    m.inspect(21.2, 11.2, "A valeta", "Água parada e escura escorre pela valeta. As pontes de tábua rangem, "
              "mas ninguém lembra de uma ter caído.", radius=1.1)

    # --------------------------------------------- north row, fronting the main lane
    m.building("barraco-0", 8.3, 12.0, depth=0.62)
    m.building("barraco-3", 15.0, 12.0, depth=0.62)
    m.building("barraco-4", 19.4, 12.0, depth=0.62)
    m.building("barraco-2", 27.0, 11.6, depth=0.62)
    m.building("barraco-1", 35.0, 11.4, depth=0.62)
    m.building("casa-pedra-gasta", 41.0, 11.4)
    m.building("barraco-3", 46.1, 11.4, depth=0.62, flip=True)
    for (x, y) in ((8.3, 11.0), (15.0, 11.0), (35.0, 10.4)):   # candle light by the doors at night
        m.light(x, y, radius=1.6, intensity=0.55, flicker=0.35)
    m.obj("barris-agua", 5.6, 12.1, (1.1, 0.4, 0.0), shadow=1.2)
    m.obj("caixotes", 21.1, 11.6, (1.1, 0.5, 0.0), shadow=1.3)
    m.obj("lixo", 11.9, 6.4, (1.6, 0.6, 0.0), shadow=1.8)      # junk at the end of the alley
    m.obj("lenha", 32.0, 6.3, (1.6, 0.5, 0.0), shadow=1.7)
    m.weeds([(11.4, 8.6, 3), (32.4, 8.8, 0), (24.0, 11.9, 1), (30.0, 11.5, 4)])

    # ------------------------------------------------------------ main lane
    m.hole(36.5, 14.3, 0.6, 0.35)
    for (x, y) in ((6.8, 15.9), (20.8, 11.7), (37.6, 15.7)):
        m.lamp_post(x, y)
    m.sign("placa", 46.4, 15.95, "Rua de Casa", "Rua de Casa ›\n\nA rua da praça do poço, onde moram a Yuuki e o Tenebris.")

    # ------------------------------------------------ communal square (west of the ditch)
    m.obj("poco", 13.4, 18.0, (1.9, 0.9, 0.0), shadow=2.2)
    m.inspect(13.4, 18.8, "Poço comunitário", "Todo o quarteirão tira água daqui. Há marcas de baldes "
              "na borda de pedra, gastas de tanto uso.")
    m.laundry_line(10.0, 21.4, "varal-a", first=0)
    m.laundry_line(17.6, 21.2, "varal-b", first=3)
    m.obj("barris-agua", 8.4, 16.4, (1.1, 0.4, 0.0), shadow=1.2)
    m.obj("banco", 19.6, 16.4, (1.8, 0.45, 0.0), shadow=1.9)
    m.obj("lixo-2", 20.6, 23.6, (1.6, 0.6, 0.0), shadow=1.8)
    m.weeds([(7.9, 19.4, 2), (20.8, 19.0, 0), (12.0, 23.8, 3), (7.8, 23.4, 5)])
    # Two shacks crammed along the lower lane.
    m.building("barraco-1", 9.8, 27.4, depth=0.62, flip=True)
    m.building("barraco-5", 16.4, 27.4, depth=0.62)
    m.light(16.4, 26.3, radius=1.5, intensity=0.5, flicker=0.35)
    m.obj("caixotes", 19.9, 27.2, (1.2, 0.5, 0.0), shadow=1.3)
    m.obj("barris-agua", 12.6, 27.5, (1.1, 0.4, 0.0), shadow=1.2)

    # ----------------------------------------------------- chicken yard (east of the ditch)
    m.obj("cerca-esq", 25.0, 16.0, (2.0, 0.4, 0.0), shadow=2)
    m.obj("galinheiro", 27.0, 19.0, (3.0, 1.0, 0.0), shadow=3.2)
    m.chickens.append(dict(x=27.6, y=20.8, radius=1.7, frames=CHICKENS["branca"]))
    m.chickens.append(dict(x=31.6, y=19.6, radius=1.3, frames=CHICKENS["ruiva"]))
    m.obj("horta", 32.8, 17.6, (2.2, 1.0, 0.1))
    m.obj("carroca-quebrada", 34.4, 20.4, (2.4, 0.7, 0.0), shadow=2.6)
    m.weeds([(24.2, 20.4, 5), (35.6, 17.0, 1)])
    # Houses fronting the lower lane.
    m.building("barraco-0", 26.4, 27.4, depth=0.62, flip=True)
    m.building("casa-velha", 32.6, 27.4, depth=0.5, flip=True, smoke_at=(96, 18))

    # ---------------------------------------- the abandoned corner and the hidden stairs
    for (x0, x1) in ((36.6, 39.6), (42.6, 48.0)):
        m.wall_row("muro-gasto", x0, x1, 21.2, alt="muro-gasto")
    m.env("portao-ferrugem", 41.1, 21.3)                    # old gate, rusted shut
    m.inspect(41.1, 21.8, "Portão enferrujado", "O cadeado se fundiu com a ferrugem. Do outro lado só há o "
              "muro do galinheiro.", radius=1.1)
    m.env("casa-abandonada-b", 41.4, 28.0, shadow=4.4)
    m.inspect(41.4, 28.5, "Casa abandonada", "Tábuas pregadas às pressas na porta. Alguém escreveu com "
              "carvão: \"não entre\".", radius=1.1)
    m.env("muro-sagrado", 38.0, 26.4, shadow=2.8)
    m.inspect(38.0, 26.8, "Muro riscado", "Um símbolo de asas e auréola, raspado da pedra de propósito.",
              radius=1.1)
    m.env("entrada-dungeon", DUNGEON_DOOR[0], 24.8)
    m.env("cerca-podre", 45.9, 26.9, shadow=2.8)             # hides the lower steps from the yard
    m.env("penas", 44.8, 25.9)
    m.env("brinquedo", 43.2, 29.8)
    m.inspect(43.2, 29.9, "Brinquedo esquecido", "Um anjinho de madeira com a asa quebrada, jogado na lama.",
              radius=0.9)
    m.env("varal-vazio", 38.6, 31.8)
    m.env("horta-morta", 45.4, 31.2)
    m.env("lixo", 37.4, 34.0)
    m.obj("arvore-seca", 37.9, 23.4, (0.8, 0.45, 0.0), sway=1.8, shadow=2.2)
    m.obj("arvore-seca", 47.4, 22.4, (0.8, 0.45, 0.0), sway=1.8, shadow=2.2)
    m.weeds([(36.9, 29.0, 3), (44.0, 22.4, 0), (47.2, 27.8, 5), (39.8, 33.8, 1), (43.6, 34.0, 3)])
    m.stairs(DUNGEON_DOOR[0], DUNGEON_DOOR[1], "Descer a escada", "Passagem subterrânea", "Bairro_Dungeon",
             dungeon_entry, radius=1.1)

    # ------------------------------------------------ lower lane and back lots
    m.hole(26.6, 32.5, 1.1, 0.6)
    m.obj("lixo", 9.2, 32.4, (1.6, 0.6, 0.0), shadow=1.8)
    m.obj("lixo-2", 30.4, 33.4, (1.6, 0.6, 0.0), shadow=1.8)
    m.laundry_line(16.0, 32.8, "varal-c", first=5)
    m.chickens.append(dict(x=6.8, y=32.4, radius=1.2, frames=CHICKENS["carijo"]))
    m.obj("arvore-seca", 4.4, 34.2, (0.8, 0.45, 0.0), sway=1.8, shadow=2.2)
    m.obj("arvore", 19.8, 34.3, (0.9, 0.5, 0.0), sway=1.2, shadow=2.4)
    m.obj("caixotes", 34.6, 33.6, (1.4, 0.55, 0.0), shadow=1.5)
    m.obj("entulho-2", 12.8, 34.2)
    m.weeds([(6.2, 34.4, 0), (11.0, 34.4, 3), (24.8, 34.4, 4), (28.8, 34.2, 5), (33.2, 34.4, 3), (21.0, 31.0, 1)])

    # ------------------------------------------------------------------ exits
    m.exits.append(dict(id="saida-rua-de-casa", x=47.6, y=13.35, w=0.8, h=3.9, label="Rua de Casa",
                        targetMap="Bairro_RuaDeCasa", targetX=RUA_ENTRY[0], targetY=RUA_ENTRY[1]))
    m.block(47.9, 11.4, 0.7, 3.9)

    # ------------------------------------------------------------------- life
    m.npcs.extend([
        dict(id="lavadeira", variant="lavadeira", scale=1.14, speed=0.8, mode="patrol",
             points=[(8.6, 22.3), (11.6, 22.3)], waitMin=3, waitMax=7),
        dict(id="vizinha", variant="vizinha", scale=1.12, speed=0.9, mode="wander",
             rect=(8.6, 17.0, 3.0, 2.6), waitMin=2, waitMax=5),
        dict(id="crianca-a", variant="crianca-a", scale=0.82, speed=2.4, mode="wander",
             rect=(15.2, 17.0, 3.0, 3.2), waitMin=0.3, waitMax=1.4),
        dict(id="crianca-b", variant="crianca-b", scale=0.8, speed=2.2, mode="wander",
             rect=(15.2, 17.0, 3.0, 3.2), waitMin=0.3, waitMax=1.6),
        dict(id="crianca-c", variant="crianca-c", scale=0.78, speed=2.0, mode="wander",
             rect=(24.0, 28.8, 11.5, 0.9), waitMin=0.5, waitMax=2.0),
        dict(id="idoso", variant="idoso", scale=1.1, speed=0.55, mode="patrol",
             points=[(7.0, 13.9), (19.6, 13.9)], waitMin=3, waitMax=8),
        dict(id="morador", variant="morador", scale=1.22, speed=1.3, mode="patrol",
             points=[(24.6, 13.3), (46.2, 13.3)], waitMin=1.5, waitMax=4),
        dict(id="andarilho", variant="andarilho", scale=1.15, speed=1.1, mode="patrol",
             points=[(4.6, 29.1), (22.7, 29.0), (35.8, 29.1)], waitMin=2, waitMax=5),
        dict(id="lavadeira-2", variant="lavadeira", scale=1.1, speed=0.7, mode="patrol",
             points=[(14.6, 33.7), (17.4, 33.7)], waitMin=4, waitMax=8),
    ])
    m.birds.extend([dict(x=11.2, y=15.9, count=3), dict(x=33.0, y=13.0, count=4), dict(x=28.6, y=31.2, count=3)])


def build():
    import dungeon
    m = MapLayout("moradias", "Moradias", "Bairro_Moradias", MAP_W, MAP_H, seed=31)
    layout(m, dungeon.ENTRY)
    m.spawn = ENTRY
    return m
