"""Pack the approved generated sheets, without redrawing or resampling the art.

Explicit rectangles handle the nonuniform sheets. School/tree/fence masks select
their disconnected silhouettes where their bounding rectangles overlap. Originals
and exact prompts remain in Art/World/Sources/Bairro-v2.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'Art/World/Sources/Bairro-v2'
OUT = ROOT / 'Assets/Game/Resources/Environment'
PAD = 8

# id, display name, visual width in Unity tiles (1 unit = 1 tile).
SETS = {
    'shops': ('Comércio', [
        ('padaria', 'Pão do Dia · padaria', 5), ('alfaiataria', 'Roupas e Remendos', 4.4),
        ('mercearia', 'Mercearia do Bairro', 5), ('ferreiro', 'Forja improvisada', 5),
        ('usados', 'Loja de segunda mão', 4.6), ('objetos-sagrados', 'Objetos sagrados baratos', 4.6)]),
    'school': ('Escola · exterior', [
        ('escola', 'Escola do bairro', 8), ('arvore-balanco', 'Árvore e balanço', 6),
        ('grade-escola', 'Grade e portão escolar', 7), ('banco-escola', 'Banco deteriorado', 2.4),
        ('gangorra', 'Gangorra quebrada', 3), ('abrigo-lenha', 'Abrigo de lenha', 2.8)]),
    'interior': ('Escola · interior', [
        ('carteira', 'Carteira e dois bancos', 2), ('mesa-professor', 'Mesa do professor', 2.4),
        ('quadro-negro', 'Quadro negro', 3), ('estante-alta', 'Estante alta', 2),
        ('estante-baixa', 'Estante baixa', 2), ('mesa-leitura', 'Mesa de leitura', 2.5),
        ('escada-biblioteca', 'Escada da biblioteca', 1), ('globo', 'Globo antigo', .8),
        ('caixa-livros', 'Livros doados', 1)]),
    'market': ('Comércio · objetos', [
        ('carroca-verduras', 'Carroça de verduras', 2.5), ('barraca-feira', 'Barraca remendada', 3),
        ('sacos-farinha', 'Sacos de farinha', 1.3), ('barril-peixes', 'Barril de peixes', 1),
        ('caixa-frutas', 'Caixa de frutas', 1), ('cesto-paes', 'Cesto de pães', .9),
        ('poste-luz', 'Poste torto', 1), ('fonte', 'Fonte rachada', 1.5),
        ('placas-lojas', 'Placas sem inscrição', 1.7)]),
    'dungeon': ('Dungeon', [
        ('entrada-dungeon', 'Escada escondida', 3), ('parede-dungeon', 'Parede horizontal', 3),
        ('canto-dungeon', 'Canto de ruína', 3), ('tocha', 'Tocha enferrujada', .7),
        ('correntes', 'Correntes e algemas', 1.6), ('ossos', 'Ossos antigos', 1.4),
        ('asa-carbonizada', 'Relíquia de asa carbonizada', 1.6), ('altar', 'Altar quebrado', 2.4),
        ('velas', 'Círculo de velas', 1.5)]),
    'abandoned': ('Bairro abandonado', [
        ('casa-abandonada-a', 'Casa abandonada A', 4.5), ('casa-abandonada-b', 'Casa abandonada B', 4.5),
        ('muro-sagrado', 'Muro de símbolo apagado', 3), ('portao-ferrugem', 'Portão enferrujado', 3),
        ('cerca-podre', 'Cerca apodrecida', 3), ('varal-vazio', 'Varal vazio', 3.4),
        ('horta-morta', 'Horta morta', 2), ('lixo', 'Entulho e lixo', 1.4),
        ('brinquedo', 'Brinquedo e pena esquecidos', .8)]),
    'details': ('Detalhes', [
        ('teia', 'Teia e gancho', 1), ('parede-vertical', 'Parede vertical', 1.2),
        ('grade-dungeon', 'Grade da dungeon', 2.4), ('poca', 'Poça escura', 1.5),
        ('simbolo-apagado', 'Símbolo de asas apagado', 1.5), ('penas', 'Penas caídas', .8),
        ('sino-escola', 'Sino da escola', .8), ('carteira-quebrada', 'Carteira quebrada', 1.6),
        ('amarelinha', 'Amarelinha desbotada', 1.2)]),
    'terrain': ('Pisos', [
        ('terra-dungeon', 'Terra úmida da dungeon', 4), ('lajes-dungeon', 'Lajes da dungeon', 4),
        ('lama-suburbio', 'Lama dos subúrbios', 4), ('calcamento', 'Calçamento deteriorado', 4)])
}
DECALS = {'poca', 'simbolo-apagado', 'penas', 'amarelinha', 'ossos', 'brinquedo', 'velas', 'asa-carbonizada', 'teia', 'correntes', 'tocha'}


def rectangles(key, size):
    w, h = size
    if key == 'school':
        return [(0, 0, 557, 650), (549, 0, 1070, 650), (960, 390, 1536, 650),
                (0, 690, 510, h), (510, 670, 1050, h), (1060, 655, w, h)]
    if key == 'shops':
        return [(0, 0, 500, 487), (500, 0, 1010, 487), (1010, 0, w, 487),
                (0, 487, 513, h), (513, 487, 1018, h), (1018, 487, w, h)]
    rows = {'interior': [0, 418, 824, h], 'market': [0, 419, 740, h],
            'abandoned': [0, 470, 835, h]}.get(key, [0, h//3, 2*h//3, h])
    cols = [0, w//3, 2*w//3, w]
    if key == 'interior':
        cols = [0, 418, 816, w]
    if key == 'abandoned':
        cols = [0, 435, 836, w]
    if key == 'dungeon':
        return [(a, c, b, d) for row, (c, d) in enumerate(zip(rows, rows[1:]))
                for a, b in zip([0, 418, 810 if row == 1 else 836],
                                [418, 810 if row == 1 else 836, w])]
    if key == 'terrain':
        rows, cols = [0, h//2, h], [0, w//2, w]
    return [(a, c, b, d) for c, d in zip(rows, rows[1:]) for a, b in zip(cols, cols[1:])]


def isolate_school(source, index):
    """Keep the selected whole silhouette; preserve antialiased edges, not neighbours."""
    rgba = np.array(source)
    labels, _ = ndi.label(rgba[:, :, 3] > 30)
    counts = np.bincount(labels.ravel()); counts[0] = 0
    order = np.argsort(counts)[::-1]
    # Area rank: building, tree, wood shed, fence, seesaw, bench.
    selected = order[{0: 0, 1: 1, 2: 3}[index]]
    mask = ndi.binary_dilation(labels == selected, iterations=2)
    rgba[~mask] = 0
    return Image.fromarray(rgba)


def pack():
    (OUT / 'Art').mkdir(parents=True, exist_ok=True)
    assets, images = [], []
    for key, (category, items) in SETS.items():
        source = Image.open(SOURCE / (key + '.png')).convert('RGBA')
        for index, ((sid, name, tiles), box) in enumerate(zip(items, rectangles(key, source.size))):
            im = isolate_school(source, index) if key == 'school' and index < 3 else source
            im = im.crop(box)
            if key != 'terrain':
                bbox = im.getchannel('A').getbbox()
                if bbox is None:
                    raise ValueError('Empty sprite: ' + sid)
                im = im.crop(bbox)
                packed = Image.new('RGBA', (im.width + 2*PAD, im.height + 2*PAD))
                packed.alpha_composite(im, (PAD, PAD))
                im = packed
            # Some generated PNGs have arbitrary RGB under fully transparent pixels.
            data = np.array(im); data[data[:, :, 3] == 0] = 0
            im = Image.fromarray(data)
            path = OUT / 'Art' / (sid + '.png'); im.save(path)
            visible_width = im.width - (0 if key == 'terrain' else 2*PAD)
            ppu = round(visible_width / tiles, 4)
            floor = key == 'terrain'
            decal = floor or sid in DECALS
            assets.append(dict(id=sid, name=name, category=category,
                resource='Environment/Art/' + sid, path=path.relative_to(ROOT).as_posix(),
                source='Art/World/Sources/Bairro-v2/' + key + '.png', crop=list(box),
                width=im.width, height=im.height, ppu=ppu, tileWidth=tiles,
                pivotX=.5, pivotY=.5 if decal else PAD/im.height,
                colliderWidth=0 if decal else round(tiles * .8, 3),
                colliderHeight=0 if decal else round(min(1.2, im.height/ppu*.22), 3),
                floor=floor, decal=decal,
                note='Textura de preenchimento; junções e bordas devem ser compostas no mapa.' if floor
                     else 'Peça estática. Colisão de base ajustável no prefab; portas são colocadas no mapa.'))
            images.append(im)
    catalog = dict(version=1, title='Cenários da infância de Yuuki', assets=assets)
    (OUT / 'catalog.json').write_text(json.dumps(catalog, ensure_ascii=False, indent=2), encoding='utf-8')
    # Contact sheets are inspection artifacts, never a replacement for source art.
    font = ImageFont.truetype('C:/Windows/Fonts/segoeui.ttf', 15)
    for key, (category, _) in SETS.items():
        selected = [(a, im) for a, im in zip(assets, images) if a['category'] == category]
        sheet = Image.new('RGB', (960, ((len(selected)+2)//3)*288), '#24252b')
        draw = ImageDraw.Draw(sheet)
        for i, (asset, im) in enumerate(selected):
            thumb = im.copy(); thumb.thumbnail((294, 241), Image.Resampling.NEAREST)
            x, y = (i%3)*320, (i//3)*288
            sheet.paste(thumb, (x+(320-thumb.width)//2, y+8+(241-thumb.height)//2), thumb)
            draw.text((x+10, y+254), asset['name'], font=font, fill='#e2d7be')
        sheet.save(ROOT / 'docs/bairro' / ('catalogo-' + key + '.jpg'), quality=94)
    print(f'{len(assets)} assets packed into {OUT}')


if __name__ == '__main__':
    pack()
