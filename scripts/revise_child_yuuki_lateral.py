"""Install the reviewed lateral playback without changing accepted directions.

The only image operations are transparent cell extraction, alpha cleanup,
nearest-neighbor scaling and packing. Drawings come from built-in ImageGen.
"""
import json
import shutil
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import pack_child_yuuki as pack

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'Art/Characters/Childhood/Yuuki/Animations-v1'
OUT = ROOT / 'Assets/Game/Resources/Childhood/Yuuki'
CATALOG = OUT / 'animations.json'


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def main():
    config = json.loads((ART / 'lateral-revision.json').read_text(encoding='utf-8'))
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    clips = {clip['name']: clip for clip in catalog['clips']}
    old_clips = json.loads(json.dumps(catalog['clips']))
    preserved = pack.check_adult()
    protected = {OUT / 'halo-neutral.png', ROOT / 'Art/Characters/Childhood/Yuuki/Design-v1/body.png'}
    for clip in catalog['clips']:
        if clip['name'] not in ('walk_left', 'run_left'):
            protected.update(ROOT / 'Assets/Game/Resources' / (name + '.png') for name in clip['frames'])
    protected.update(ART / 'Atlases' / (direction + '.png') for direction in ('up', 'down'))
    hashes_before = {path: pack.digest(path) for path in protected}
    revision = ART / 'Revisions/lateral-v2'
    revision.mkdir(parents=True, exist_ok=True)
    if not (revision / 'catalog-before.json').exists():
        shutil.copy2(CATALOG, revision / 'catalog-before.json')

    sheet = Image.open(ART / 'Sources' / config['leftSource']).convert('RGBA')
    middle = pack.gutter(np.array(sheet)[:, :, 3], sheet.height // 2)
    row_cuts = [0, middle, sheet.height]
    drawings = []
    column_cuts = []
    for row in range(2):
        row_image = sheet.crop((0, row_cuts[row], sheet.width, row_cuts[row + 1]))
        alpha = np.array(row_image)[:, :, 3]
        cuts = [0] + [pack.gutter(alpha.T, round(sheet.width * c / 4)) for c in range(1, 4)] + [sheet.width]
        column_cuts.append(cuts)
        poses = [pack.clean(row_image.crop((cuts[c], 0, cuts[c + 1], row_image.height))) for c in range(4)]
        for pose in poses:
            # A transparent gutter must surround every complete drawing.
            a = np.array(pose)[:, :, 3]
            assert not (a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any()), 'Sheet cell clips a drawing'
        drawings.append(poses)

    scale = 224 / float(np.median([pack.metrics(im)[1] - pack.metrics(im)[0] for im in drawings[0]]))
    # Use the same scale for airborne poses; resizing each pose to equal height
    # would stretch the body and erase the lifting of the feet.
    contact_height = float(np.median([pack.metrics(drawings[1][i])[1] - pack.metrics(drawings[1][i])[0] for i in (0, 2)]))
    run_top = round(400 - contact_height * scale)
    detail = []
    for row, state in enumerate(('walk', 'run')):
        names, anchors, bounds = [], [], []
        for i, pose in enumerate(drawings[row]):
            top, bottom, anchor = pack.metrics(pose)
            box = pose.getchannel('A').getbbox()
            crop = pose.crop(box)
            crop = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.Resampling.NEAREST)
            x = round(256 - (anchor - box[0]) * scale)
            if state == 'walk':
                y = 400 - round((bottom - box[1]) * scale)
            else:
                target_top = run_top - (5 if i in (1, 3) else 0)
                y = target_top - round((top - box[1]) * scale)
            assert x >= 12 and y >= 12 and x + crop.width <= 500 and y + crop.height <= 500
            frame = Image.new('RGBA', (512, 512))
            frame.alpha_composite(crop, (x, y))
            name = f'{state}_left_v2_{i:02}'
            path = OUT / 'Frames' / (name + '.png')
            frame.save(path)
            pack.metadata(path)
            names.append('Childhood/Yuuki/Frames/' + name)
            anchors.append(dict(x=256, y=round(y + (top - box[1]) * scale - 24)))
            bounds.append(frame.getchannel('A').getbbox())
        clip = clips[state + '_left']
        clip.update(frames=names, haloAnchors=anchors, fps=config['leftFps'][state], sequence=[0, 1, 2, 3])
        detail.append(dict(clip=clip['name'], frames=4, source=config['leftSource'], sourceRow=row_cuts[row:row + 2], sourceColumns=column_cuts[row], scale=scale, bounds=bounds))

    for state in ('walk', 'run'):
        clips[state + '_right']['sequence'] = config['rightSequence']
    catalog['status'] = 'lateral-v2-for-motion-review'
    catalog['playbackRevision'] = 'lateral-v2'
    save_json(CATALOG, catalog)

    overview = Image.new('RGB', (1140, 2520), '#263139')
    draw = ImageDraw.Draw(overview)
    atlas_layout = {}
    for di, direction in enumerate(('down', 'up', 'left', 'right')):
        atlas = Image.new('RGBA', (3072, 1536))
        atlas_layout[direction] = {}
        for row, state in enumerate(('walk', 'run', 'idle')):
            clip = clips[state + '_' + direction]
            order = list(dict.fromkeys(clip['sequence']))
            atlas_layout[direction][state] = [clip['frames'][i] for i in order]
            for col, index in enumerate(order):
                name = clip['frames'][index]
                frame = Image.open(ROOT / 'Assets/Game/Resources' / (name + '.png')).convert('RGBA')
                atlas.alpha_composite(frame, (col * 512, row * 512))
                thumb = frame.crop((96, 104, 416, 424)).resize((190, 190), Image.Resampling.NEAREST)
                yy = (di * 3 + row) * 210
                overview.paste(thumb, (col * 190, yy), thumb)
                draw.text((col * 190 + 5, yy + 190), name.rsplit('/', 1)[-1], fill='#ddd6c7')
        if direction in ('left', 'right'):
            atlas.save(ART / 'Atlases' / (direction + '.png'))
    overview.save(ART / 'contact-sheet.png')

    frame_count = sum(len(clip['frames']) for clip in catalog['clips'])
    report_path = ART / 'packing-report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    report['clipsDetail'] = [next((r for r in detail if r['clip'] == item['clip']), item) for item in report['clipsDetail']]
    report.update(frames=frame_count, playbackRevision='lateral-v2', atlasLayout=atlas_layout, adultFilesVerified=preserved)
    save_json(report_path, report)
    # The user accepted front/back; this lateral-only operation must not change
    # those catalog entries, any existing right drawings, the idle or halo.
    unchanged_clips = [c for c in old_clips if c['name'] not in ('walk_left', 'run_left', 'walk_right', 'run_right')]
    assert all(clips[c['name']] == c for c in unchanged_clips)
    assert all(pack.digest(path) == digest for path, digest in hashes_before.items())
    assert pack.check_adult() == preserved
    save_json(revision / 'asset-checks.json', dict(frames=frame_count, clips=12, protectedFilesVerified=len(protected), acceptedDirectionsUnchanged=True, adultFilesVerified=preserved, rightSequence=config['rightSequence'], leftFrameCounts={state: len(clips[state + '_left']['frames']) for state in ('walk', 'run')}, leftFps=config['leftFps']))

    state_path = ROOT / 'Art/Characters/Childhood/validation-state.json'
    validation = json.loads(state_path.read_text(encoding='utf-8'))
    validation['Yuuki']['animations'] = f'lateral-v2: {frame_count} selected drawings; front/back accepted; right reordered as requested; left walk/run four-frame loops awaiting review'
    validation['Yuuki']['acceptedDirections'] = ['down', 'up']
    validation['Yuuki']['animationPreview'] = 'preview/childhood-animation.html'
    save_json(state_path, validation)
    print(json.dumps(dict(frames=frame_count, rightSequence=[i + 1 for i in config['rightSequence']], leftFrameCounts={state: len(clips[state + '_left']['frames']) for state in ('walk', 'run')}, protectedFilesVerified=len(protected), adultFilesVerified=preserved)))


if __name__ == '__main__':
    main()
