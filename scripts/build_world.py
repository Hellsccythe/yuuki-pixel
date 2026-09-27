"""Pack generated environment pieces and assemble the shared modular RPG district."""
from pathlib import Path
import json
import random
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "Art/World/Sources"
DEST = ROOT / "Assets/Game/Resources/World"
ART = DEST / "Art"


def save_piece(image, name, box=None):
    image = image.convert("RGBA")
    if box:
        image = image.crop(box)
    alpha = image.getchannel("A")
    image.putalpha(alpha.point(lambda a: 0 if a < 12 else a))
    bounds = image.getchannel("A").getbbox()
    if not bounds:
        raise ValueError(name)
    image = image.crop(bounds)
    clean = Image.new("RGBA", (image.width + 8, image.height + 8))
    clean.alpha_composite(image, (4, 4))
    clean.save(ART / (name + ".png"), optimize=True)


def pack_art():
    ART.mkdir(parents=True, exist_ok=True)
    buildings = Image.open(SOURCE / "buildings-topdown.png")
    # Reviewed boundaries: the upper buildings extend below the nominal 512px line.
    for name, box in zip(["home", "timber-house", "stone-house", "school", "workshop", "wall"],
                         [(0, 0, 530, 532), (530, 0, 1050, 532), (1050, 0, 1536, 532),
                          (0, 532, 530, 1024), (530, 532, 1050, 1024), (1050, 532, 1536, 1024)]):
        save_piece(buildings, name, box)
    props = Image.open(SOURCE / "props-topdown.png")
    boxes = [(0, 0, 480, 389), (480, 145, 1110, 334), (1120, 70, 1500, 355),
             (75, 398, 399, 681), (592, 430, 957, 665), (1160, 370, 1470, 681),
             (91, 683, 370, 1015), (598, 670, 964, 1003), (1130, 716, 1480, 1000)]
    for name, box in zip(["tree", "fence", "crates", "well", "bench", "sign", "bed", "bookshelf", "table"], boxes):
        save_piece(props, name, box)
    save_piece(Image.open(SOURCE / "city-gate.png"), "city-gate")
    terrain = Image.open(SOURCE / "terrain.png").convert("RGB")
    half = terrain.width // 2
    for index, name in enumerate(["grass", "dirt", "stone", "wood"]):
        col, row = index % 2, index // 2
        tile = terrain.crop((col * half, row * half, (col + 1) * half, (row + 1) * half))
        tile.resize((128, 128), Image.Resampling.NEAREST).save(ART / (name + ".png"))


def obj(asset, x, y, w, h, solid=True, **extra):
    # Position = bottom center. Footprints describe the occupied floor, not the roof.
    depth = 0.43 if asset in ("home", "timber-house", "stone-house", "school", "workshop", "city-gate") else 0.30
    if asset == "tree":
        footprint = [-w * .12, -h * .12, w * .24, h * .12]
    else:
        footprint = [-w * .41, -h * depth, w * .82, h * depth]
    return dict(asset=asset, x=x, y=y, width=w, height=h, solid=solid,
                footprint=footprint, **extra)


def point(id, x, y, title, text="", target="", tx=0, ty=0, journal=False):
    return dict(id=id, x=x, y=y, title=title, text=text, target=target,
                targetX=tx, targetY=ty, journal=journal)


def build_definition():
    modules = [
        dict(id="home-yard", objects=[
            obj("home", 400, 450, 450, 410), obj("fence", 155, 550, 240, 75),
            obj("fence", 650, 550, 240, 75), obj("tree", 30, 380, 270, 275),
            obj("crates", 730, 440, 105, 95)],
            points=[point("home-door", 461, 476, "Entrar em casa", target="home", tx=560, ty=590),
                    point("family-gate", 392, 558, "O portão antigo", "A madeira tem marcas do tempo, mas o portão continua firme. Sara e Kled cuidam de tudo o que podem.", journal=True)]),
        dict(id="neighbor-lot", objects=[obj("timber-house", 250, 450, 385, 440),
             obj("bench", 420, 496, 110, 66), obj("crates", 70, 492, 85, 80)],
             points=[point("neighbor", 260, 476, "A casa dos vizinhos", "Tenebris mora perto. O caminho até a escola é curto quando os dois vão juntos.")]),
        dict(id="old-alley", objects=[obj("workshop", 0, 355, 375, 315),
             obj("stone-house", 570, 350, 335, 420), obj("wall", 280, 110, 250, 130),
             obj("fence", 300, 275, 235, 80), obj("crates", 233, 260, 93, 93),
             obj("crates", 385, 320, 85, 87)],
             points=[point("alley-memory", 300, 408, "O beco da cerca", "Terra batida, tinta descascada e uma cerca torta. Este beco guarda o começo de uma amizade que mudaria tudo.", journal=True)]),
        dict(id="school-court", objects=[obj("school", 320, 450, 515, 455),
             obj("well", -80, 565, 155, 160), obj("bench", 590, 540, 140, 78),
             obj("tree", 680, 360, 255, 285), obj("sign", 17, 605, 74, 112)],
             points=[point("school-door", 320, 478, "Biblioteca da escola", target="library", tx=576, ty=630),
                     point("school-sign", 17, 630, "Pátio da escola", "Entre o treino e a volta para casa, há sempre tempo para um livro.")]),
        dict(id="city-threshold", objects=[obj("city-gate", 300, 470, 630, 403),
             obj("wall", -145, 440, 240, 122), obj("sign", 630, 547, 75, 110)],
             points=[point("city-gate", 300, 510, "O caminho para o centro", "Depois da terra, a pedra bem assentada. Além do portão estão os jardins e as grandes casas da Cidade dos Anjos. Este caminho será aberto na próxima área.", journal=True)])
    ]
    exterior = dict(id="suburbs", name="Subúrbios da Cidade dos Anjos", width=3072, height=2048,
        floor="grass", spawnX=615, spawnY=662,
        paths=[dict(x=0,y=640,w=3072,h=192,tile="dirt"), dict(x=512,y=400,w=160,h=1140,tile="dirt"),
               dict(x=1100,y=735,w=180,h=770,tile="dirt"), dict(x=400,y=1320,w=2100,h=192,tile="dirt"),
               dict(x=2050,y=740,w=192,h=690,tile="dirt"), dict(x=2400,y=535,w=672,h=375,tile="stone"),
               dict(x=1780,y=1190,w=820,h=345,tile="stone"), dict(x=720,y=1090,w=795,h=380,tile="dirt")],
        instances=[dict(module="home-yard",x=128,y=96), dict(module="neighbor-lot",x=935,y=85),
                   dict(module="neighbor-lot",x=1570,y=45), dict(module="old-alley",x=900,y=920),
                   dict(module="school-court",x=1800,y=850), dict(module="city-threshold",x=2420,y=170)],
        objects=[], points=[point("road-sign",1430,735,"As ruas do bairro","O caminho de terra liga as casas ao pátio da escola. Ao sul, o beco; a leste, o portão do centro.")],
        regions=[dict(name="Rua de casa",x=0,y=0,w=950,h=950), dict(name="Rua dos vizinhos",x=950,y=0,w=1400,h=900),
                 dict(name="Beco da cerca",x=620,y=900,w=1130,h=750), dict(name="Pátio da escola",x=1750,y=950,w=1000,h=700),
                 dict(name="Limiar do centro",x=2380,y=0,w=692,h=950)])
    exterior['objects'] += [obj('sign',1430,712,67,104),obj('well',820,905,145,143),
                            obj('bench',690,945,120,65),obj('wall',290,1180,340,151),obj('workshop',385,1780,390,321),
                            obj('timber-house',1660,1850,365,419),obj('stone-house',2540,1840,340,437)]
    rng=random.Random(24)
    for x,y in [(70,180),(825,240),(1410,240),(2130,210),(120,890),(190,1460),(90,1800),
                (2750,1160),(2920,1480),(2800,1790),(770,1730),(1090,1870),(2250,1810),(2050,1950)]:
        size=rng.randint(210,280)
        exterior['objects'].append(obj('tree',x,y,size,size*1.1))
    home = dict(id="home",name="Casa de Yuuki",width=1024,height=768,floor="wood",spawnX=560,spawnY=590,
        paths=[dict(x=352,y=360,w=340,h=280,tile="stone")],instances=[],regions=[],
        objects=[obj('bed',225,390,155,220),obj('bookshelf',795,300,162,213),
                 obj('table',535,460,234,184),obj('crates',831,560,92,84),obj('bench',219,620,165,90)],
        points=[point('home-exit',560,699,'Sair de casa',target='suburbs',tx=590,ty=610),
                point('home-book',536,507,'O livro sobre a mesa','As páginas estão gastas de tanto serem relidas. Para Yuuki, perguntas nunca faltam.',journal=True),
                point('home-family',224,437,'Um lar cuidado','A casa é pequena, de madeira e bem cuidada. Os pais trabalham até tarde; o carinho está nas pequenas coisas.')])
    library = dict(id="library",name="Biblioteca da escola",width=1152,height=832,floor="wood",spawnX=576,spawnY=630,
        paths=[dict(x=385,y=240,w=385,h=490,tile="stone")],instances=[],regions=[],
        objects=[obj('bookshelf',185,305,200,250),obj('bookshelf',480,305,200,250),
                 obj('bookshelf',775,305,200,250),obj('bookshelf',1000,310,170,220),
                 obj('table',230,562,215,167),obj('table',840,562,215,167),obj('bench',1030,680,135,85)],
        points=[point('library-exit',576,764,'Voltar ao pátio',target='suburbs',tx=2120,ty=1375),
                point('library-shelf',480,344,'O refúgio de Yuuki','Entre estas estantes, Yuuki e Tenebris dividem tardes de leitura e perguntas. Aqui, a curiosidade tem espaço.',journal=True)])
    return dict(version=1,tileSize=32,startMap="suburbs",modules=modules,maps=[exterior,home,library])


def tiled(name, size):
    tile = Image.open(ART / (name + ".png")).convert('RGB')
    result = Image.new('RGB',size)
    for y in range(0,size[1],128):
        for x in range(0,size[0],128):result.paste(tile,(x,y))
    return result


def assemble_floors(world):
    (DEST/'Floors').mkdir(exist_ok=True)
    for level in world['maps']:
        size=(level['width'],level['height'])
        floor=tiled(level['floor'],size)
        for index,path in enumerate(level['paths']):
            # A coarse reusable terrain brush avoids perfectly rectangular dirt edges.
            mask=Image.new('L',size);draw=ImageDraw.Draw(mask)
            x,y,w,h=[path[key] for key in ['x','y','w','h']]
            draw.rounded_rectangle((x,y,x+w,y+h),radius=24,fill=255)
            if path['tile']=='dirt':
                rng=random.Random(index+38)
                for px in range(x+24,x+w-24,16):
                    draw.rectangle((px,y-rng.randint(0,8),px+16,y+8),fill=255)
                    draw.rectangle((px,y+h-8,px+16,y+h+rng.randint(0,8)),fill=255)
            floor.paste(tiled(path['tile'],size),(0,0),mask)
        floor.save(DEST/'Floors'/f"{level['id']}.png",optimize=True)


if __name__ == '__main__':
    pack_art()
    world=build_definition()
    (DEST/'angel-suburbs.json').write_text(json.dumps(world,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
    assemble_floors(world)
    print(f"Built {len(world['modules'])} reusable modules, {len(world['maps'])} maps and {len(list(ART.glob('*.png')))} art assets.")
