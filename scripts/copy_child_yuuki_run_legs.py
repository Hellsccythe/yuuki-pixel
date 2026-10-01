"""Copy the approved right-run legs exactly into the existing left-run body.

Only horizontal reflection, integer translation and binary masks are used.
No generation, scaling, interpolation, color changes or alpha blending.
"""
import copy
import hashlib
import json
from pathlib import Path
import shutil

import numpy as np
from PIL import Image, ImageDraw, ImageOps
import pack_child_yuuki as pack

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'Art/Characters/Childhood/Yuuki/Animations-v1'
OUT = ROOT / 'Assets/Game/Resources/Childhood/Yuuki'
REVISION = 'run-left-v5'


def read(path):
    return json.loads(path.read_text(encoding='utf-8'))


def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def polygon(points):
    im = Image.new('1', (512, 512))
    ImageDraw.Draw(im).polygon([tuple(p) for p in points], fill=1)
    return np.array(im)


def compose(left, right, config):
    erase = polygon(config['erase'])
    # Remove skin-colored remnants under the hem that become exposed between legs.
    # This narrow area contains legs only; the neutral skirt border stays intact.
    yy, xx = np.indices((512, 512))
    rgb = left[:, :, :3].astype(float)
    erase |= ((yy >= 337) & (yy <= 350) & (xx >= 210) & (xx < 300)
              & (rgb[:, :, 0] > 105) & (rgb[:, :, 0] > rgb[:, :, 2] * 1.2)
              & (left[:, :, 3] > 0))
    source_mask = polygon(config['source'])
    for x0, y0, x1, y1 in config.get('eraseExtraRects', []):
        erase[y0:y1, x0:x1] = True
    for x0, y0, x1, y1 in config.get('sourceExcludeRects', []):
        source_mask[y0:y1, x0:x1] = False
    layer = np.zeros_like(right)
    layer[source_mask] = right[source_mask]
    dx, dy = config['offset']
    ys, xs = np.where(layer[:, :, 3] > 0)
    assert min(xs) + dx >= 0 and max(xs) + dx < 512
    assert min(ys) + dy >= 0 and max(ys) + dy < 512
    layer = np.roll(layer, (dy, dx), (0, 1))
    body = left.copy()
    body[erase] = 0
    # Existing skirt and wing foreground retain their original bytes.
    visible = (body[:, :, 3] == 0) & (layer[:, :, 3] > 0)
    result = body.copy()
    result[visible] = layer[visible]
    affected = erase | visible
    assert np.array_equal(result[~affected], left[~affected])
    assert np.array_equal(result[:337], left[:337])
    assert np.array_equal(result[visible], layer[visible])
    assert int(visible.sum()) > .8 * int((layer[:, :, 3] > 0).sum())
    return result, layer, erase, visible


def main():
    config = read(ART / 'leg-copy-v5.json')
    catalog_path = OUT / 'animations.json'
    catalog = read(catalog_path)
    before = copy.deepcopy(catalog)
    clips = {c['name']: c for c in catalog['clips']}
    protected = {OUT / 'halo-neutral.png', ROOT / 'Art/Characters/Childhood/Yuuki/Design-v1/body.png'}
    for c in catalog['clips']:
        if c['name'] != 'run_left':
            protected.update(ROOT / 'Assets/Game/Resources' / (f + '.png') for f in c['frames'])
    protected.update(ART / 'Atlases' / (d + '.png') for d in ('up', 'down', 'right'))
    # Keep both approved sources and previous left frames for recovery.
    for i in range(4):
        protected.add(OUT / 'Frames' / f'run_left_v4_{i:02}.png')
        protected.add(OUT / 'Frames' / f'run_right_v3_{i:02}.png')
    hashes = {p: pack.digest(p) for p in protected}
    adult_count = pack.check_adult()
    revision = ART / 'Revisions' / REVISION
    revision.mkdir(parents=True, exist_ok=True)
    if not (revision / 'catalog-before.json').exists():
        shutil.copy2(catalog_path, revision / 'catalog-before.json')
    old_atlas = np.array(Image.open(ART / 'Atlases/left.png').convert('RGBA'))
    outputs, details = [], []
    comparison = Image.new('RGB', (1280, 600), '#263139')
    draw = ImageDraw.Draw(comparison)
    for i, frame_config in enumerate(config['frames']):
        src_path = OUT / 'Frames' / f'run_right_v3_{i:02}.png'
        old_path = OUT / 'Frames' / f'run_left_v4_{i:02}.png'
        assert pack.digest(src_path) == frame_config['sourceSha256'], 'Approved right frame changed'
        assert pack.digest(old_path) == frame_config['bodySha256'], 'Left body reference changed'
        source = np.array(ImageOps.mirror(Image.open(src_path).convert('RGBA')))
        left = np.array(Image.open(old_path).convert('RGBA'))
        result, legs, erase, visible = compose(left, source, frame_config)
        im = Image.fromarray(result)
        assert not (result[0, :, 3].any() or result[-1, :, 3].any()
                    or result[:, 0, 3].any() or result[:, -1, 3].any())
        filename = f'run_left_v5_{i:02}'
        path = OUT / 'Frames' / (filename + '.png')
        im.save(path)
        pack.metadata(path)
        outputs.append('Childhood/Yuuki/Frames/' + filename)
        # Store masks and the exact transferred layer for auditing/reproduction.
        Image.fromarray(erase.astype('uint8') * 255).save(revision / f'erase-{i:02}.png')
        Image.fromarray(visible.astype('uint8') * 255).save(revision / f'visible-legs-{i:02}.png')
        Image.fromarray(legs).save(revision / f'mirrored-legs-{i:02}.png')
        details.append(dict(frame=i, source=src_path.relative_to(ROOT).as_posix(),
                            body=old_path.relative_to(ROOT).as_posix(),
                            integerOffset=frame_config['offset'],
                            visibleLegPixels=int(visible.sum()), exactLegBytes=True,
                            unchangedOutsideMasks=True, unchangedAboveY=337,
                            bounds=im.getchannel('A').getbbox(),
                            sourceSha256=pack.digest(src_path), bodySha256=pack.digest(old_path),
                            outputSha256=pack.digest(path)))
        for row, pic in enumerate((Image.fromarray(source), im)):
            thumb = pic.crop((96, 104, 416, 424))
            comparison.paste(thumb, (i * 320, row * 300 - 30), thumb)
            draw.text((i * 320 + 8, row * 300 + 278),
                      f'{i + 1} | ' + ('DIREITA ESPELHADA (referencia)' if row == 0 else 'ESQUERDA (pernas copiadas)'),
                      fill='#ddd6c7')

    clips['run_left']['frames'] = outputs
    catalog.update(playbackRevision=REVISION, status=REVISION + '-for-motion-review')
    for old_clip in before['clips']:
        if old_clip['name'] != 'run_left':
            assert clips[old_clip['name']] == old_clip
        else:
            assert {k: v for k, v in clips['run_left'].items() if k != 'frames'} == {
                k: v for k, v in old_clip.items() if k != 'frames'}
    assert {k: v for k, v in catalog.items() if k not in ('clips', 'status', 'playbackRevision')} == {
        k: v for k, v in before.items() if k not in ('clips', 'status', 'playbackRevision')}
    atlas = old_atlas.copy()
    atlas[512:1024] = 0
    for i, f in enumerate(outputs):
        atlas[512:1024, i * 512:(i + 1) * 512] = np.array(
            Image.open(ROOT / 'Assets/Game/Resources' / (f + '.png')).convert('RGBA'))
    assert np.array_equal(old_atlas[:512], atlas[:512])
    assert np.array_equal(old_atlas[1024:], atlas[1024:])
    Image.fromarray(atlas).save(ART / 'Atlases/left.png')
    save(catalog_path, catalog)
    comparison.save(revision / 'comparison.png')
    overview = Image.new('RGB', (1140, 2520), '#263139')
    draw = ImageDraw.Draw(overview)
    for di, direction in enumerate(('down', 'up', 'left', 'right')):
        for row, state in enumerate(('walk', 'run', 'idle')):
            clip = clips[state + '_' + direction]
            for col, index in enumerate(dict.fromkeys(clip['sequence'])):
                name = clip['frames'][index]
                im = Image.open(ROOT / 'Assets/Game/Resources' / (name + '.png')).convert('RGBA')
                thumb = im.crop((96, 104, 416, 424)).resize((190, 190), Image.Resampling.NEAREST)
                y = (di * 3 + row) * 210
                overview.paste(thumb, (col * 190, y), thumb)
                draw.text((col * 190 + 5, y + 190), name.rsplit('/', 1)[-1], fill='#ddd6c7')
    overview.save(ART / 'contact-sheet.png')
    assert all(pack.digest(p) == value for p, value in hashes.items()), 'Protected file changed'
    assert pack.check_adult() == adult_count
    report = read(ART / 'packing-report.json')
    report.update(playbackRevision=REVISION)
    report['atlasLayout']['left']['run'] = outputs
    report['clipsDetail'] = [
        dict(clip='run_left', frames=4, method='exact mirrored leg pixels, integer offsets, binary masks',
             configuration='leg-copy-v5.json', bounds=[d['bounds'] for d in details],
             details=details) if c['clip'] == 'run_left' else c for c in report['clipsDetail']]
    save(ART / 'packing-report.json', report)
    checks = dict(revision=REVISION, changedClips=['run_left'], acceptedClipsUnchanged=11,
                  protectedFilesVerified=len(protected), adultFilesVerified=adult_count,
                  frames=46, clips=12, fps=clips['run_left']['fps'],
                  sequence=clips['run_left']['sequence'], frameChecks=details,
                  leftAtlasWalkAndIdleUnchanged=True,
                  method='pixel copy; no generation, scaling, warping, recoloring or alpha blending')
    save(revision / 'asset-checks.json', checks)
    save(ART / 'preview-checks.json', checks)
    state_path = ROOT / 'Art/Characters/Childhood/validation-state.json'
    state = read(state_path)
    state['updated'] = '2026-09-30'
    state['Yuuki']['acceptedClips'] = [c['name'] for c in catalog['clips'] if c['name'] != 'run_left']
    state['Yuuki']['animations'] = (
        'run-left-v5: only left running legs replaced by exact mirrored right-run pixels. '
        'Four frames, 8 FPS. Other 11 clips approved and unchanged; left run awaiting user review.')
    save(state_path, state)
    print(json.dumps(checks))


if __name__ == '__main__':
    main()
