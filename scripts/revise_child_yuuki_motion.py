"""Pack compact four-frame gait drawings with a fixed head registration.

Existing front/back walking drawings and all idle clips are protected. No
interpolation, pose painting, mirroring or body warping is performed here.
"""
import json
import shutil
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

import pack_child_yuuki as pack

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / 'Art/Characters/Childhood/Yuuki/Animations-v1'
OUT = ROOT / 'Assets/Game/Resources/Childhood/Yuuki'
CATALOG = OUT / 'animations.json'
CHANGED = {'walk_left', 'walk_right', 'run_left', 'run_right', 'run_down', 'run_up'}


def save_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')


def landmark(im):
    """A translation-only registration on the eye, or rear hairline."""
    a = np.array(im)
    top, bottom, hair_x = pack.metrics(im)
    rgb = a[:, :, :3].astype(float)
    red = (a[:, :, 3] > 150) & (rgb[:, :, 0] > 110) & (rgb[:, :, 0] > rgb[:, :, 1] * 1.65) & (rgb[:, :, 0] > rgb[:, :, 2] * 1.25)
    red &= np.indices(red.shape)[0] < top + (bottom - top) * .5
    ys, xs = np.where(red)
    if len(xs) > 3:
        return float(np.median(xs)), float(np.median(ys)), 'eye'
    return hair_x, top, 'hairline'


def extract(sheet, cols, rows):
    alpha = np.array(sheet)[:, :, 3]
    y_cuts = [0] + [pack.gutter(alpha, round(sheet.height * r / rows)) for r in range(1, rows)] + [sheet.height]
    poses = []
    x_rows = []
    for row in range(rows):
        row_image = sheet.crop((0, y_cuts[row], sheet.width, y_cuts[row + 1]))
        row_alpha = np.array(row_image)[:, :, 3]
        x_cuts = [0] + [pack.gutter(row_alpha.T, round(sheet.width * c / cols)) for c in range(1, cols)] + [sheet.width]
        x_rows.append(x_cuts)
        row_poses = []
        for col in range(cols):
            pose = pack.clean(row_image.crop((x_cuts[col], 0, x_cuts[col + 1], row_image.height)))
            a = np.array(pose)[:, :, 3]
            assert not (a[0].any() or a[-1].any() or a[:, 0].any() or a[:, -1].any()), 'Drawing touches cell boundary'
            row_poses.append(pose)
        poses.append(row_poses)
    return poses, dict(rows=y_cuts, columns=x_rows)


def main(config_name='motion-four-frame-v3.json'):
    config = json.loads((ART / config_name).read_text(encoding='utf-8'))
    revision_id = config.get('revision', 'motion-v3')
    asset_suffix = config.get('assetSuffix', 'v3')
    changed = set(config.get('changedClips', CHANGED))
    catalog = json.loads(CATALOG.read_text(encoding='utf-8'))
    before_clips = json.loads(json.dumps(catalog['clips']))
    clips = {c['name']: c for c in catalog['clips']}
    preserved = pack.check_adult()
    protected = {OUT / 'halo-neutral.png', ROOT / 'Art/Characters/Childhood/Yuuki/Design-v1/body.png'}
    for clip in before_clips:
        if clip['name'] not in changed:
            protected.update(ROOT / 'Assets/Game/Resources' / (name + '.png') for name in clip['frames'])
    hashes_before = {p: pack.digest(p) for p in protected}
    protected_atlases = {ART / 'Atlases' / (direction + '.png') for direction in config.get('protectedAtlases', [])}
    hashes_before.update({p: pack.digest(p) for p in protected_atlases})
    revision = ART / 'Revisions' / revision_id
    revision.mkdir(parents=True, exist_ok=True)
    if not (revision / 'catalog-before.json').exists():
        shutil.copy2(CATALOG, revision / 'catalog-before.json')

    detail = []
    for direction, source in config['sources'].items():
        sheet = Image.open(ART / 'Sources' / source['file']).convert('RGBA')
        rows, cuts = extract(sheet, source['columns'], source['rows'])
        groups = {'walk': rows[0], 'run': rows[1]} if direction in ('left', 'right') else {'run': [p for row in rows for p in row]}
        scale_poses = groups['walk'] if 'walk' in groups else groups['run']
        reference = Image.open(ROOT / source['reference']).convert('RGBA')
        target_height = 220
        if source.get('matchReferenceHeight'):
            ref_top, ref_bottom, _ = pack.metrics(reference)
            target_height = ref_bottom - ref_top
        scale = target_height / float(np.median([pack.metrics(p)[1] - pack.metrics(p)[0] for p in scale_poses]))
        for state, poses in groups.items():
            assert state + '_' + direction in changed
            state_reference = Image.open(ROOT / source.get('referenceByState', {}).get(state, source['reference'])).convert('RGBA')
            target_x, target_y, mode = landmark(state_reference)
            if source.get('mirrorReference'):
                target_x = state_reference.width - 1 - target_x
            assert len(poses) == 4
            names, anchors, bounds, registrations = [], [], [], []
            for i, pose in enumerate(poses):
                top, bottom, _ = pack.metrics(pose)
                eye_x, eye_y, _ = landmark(pose)
                box = pose.getchannel('A').getbbox()
                crop = pose.crop(box)
                crop = crop.resize((round(crop.width * scale), round(crop.height * scale)), Image.Resampling.NEAREST)
                x = round(target_x - (eye_x - box[0]) * scale)
                y = round(target_y - (eye_y - box[1]) * scale)
                assert x >= 12 and y >= 12 and x + crop.width <= 500 and y + crop.height <= 500
                frame = Image.new('RGBA', (512, 512))
                frame.alpha_composite(crop, (x, y))
                name = f'{state}_{direction}_{asset_suffix}_{i:02}'
                path = OUT / 'Frames' / (name + '.png')
                frame.save(path)
                pack.metadata(path)
                names.append('Childhood/Yuuki/Frames/' + name)
                anchors.append(dict(x=256, y=round(y + (top - box[1]) * scale - 24)))
                bounds.append(frame.getchannel('A').getbbox())
                fx, fy, _ = landmark(frame)
                registrations.append([round(fx, 2), round(fy, 2)])
            clip = clips[state + '_' + direction]
            clip.update(frames=names, haloAnchors=anchors, sequence=[0, 1, 2, 3], fps=config['fps'][state])
            top_range = max(b[1] for b in bounds) - min(b[1] for b in bounds)
            foot_range = max(b[3] for b in bounds) - min(b[3] for b in bounds)
            detail.append(dict(clip=clip['name'], frames=4, source=source['file'], sourceCuts=cuts, scale=scale, bounds=bounds, registration=mode, landmarks=registrations, headTopRangePixels=top_range, footBaselineRangePixels=foot_range))

    catalog.update(status=revision_id + '-for-motion-review', playbackRevision=revision_id)
    save_json(CATALOG, catalog)
    overview = Image.new('RGB', (1140, 2520), '#263139')
    draw = ImageDraw.Draw(overview)
    layout = {}
    for di, direction in enumerate(('down', 'up', 'left', 'right')):
        atlas = Image.new('RGBA', (3072, 1536))
        layout[direction] = {}
        for row, state in enumerate(('walk', 'run', 'idle')):
            clip = clips[state + '_' + direction]
            order = list(dict.fromkeys(clip['sequence']))
            layout[direction][state] = [clip['frames'][i] for i in order]
            for col, index in enumerate(order):
                name = clip['frames'][index]
                frame = Image.open(ROOT / 'Assets/Game/Resources' / (name + '.png')).convert('RGBA')
                atlas.alpha_composite(frame, (col * 512, row * 512))
                thumb = frame.crop((96, 104, 416, 424)).resize((190, 190), Image.Resampling.NEAREST)
                yy = (di * 3 + row) * 210
                overview.paste(thumb, (col * 190, yy), thumb)
                draw.text((col * 190 + 5, yy + 190), name.rsplit('/', 1)[-1], fill='#ddd6c7')
        atlas.save(ART / 'Atlases' / (direction + '.png'))
    overview.save(ART / 'contact-sheet.png')

    for clip in before_clips:
        if clip['name'] not in changed:
            assert clips[clip['name']] == clip
    assert all(pack.digest(p) == digest for p, digest in hashes_before.items())
    assert pack.check_adult() == preserved
    count = sum(len(c['frames']) for c in catalog['clips'])
    report_path = ART / 'packing-report.json'
    report = json.loads(report_path.read_text(encoding='utf-8'))
    report['clipsDetail'] = [next((d for d in detail if d['clip'] == old['clip']), old) for old in report['clipsDetail']]
    report.update(frames=count, playbackRevision=revision_id, atlasLayout=layout, adultFilesVerified=preserved)
    save_json(report_path, report)
    save_json(revision / 'asset-checks.json', dict(frames=count, clips=12, protectedFilesVerified=len(protected), acceptedWalkingDirectionsUnchanged=True, idleUnchanged=True, adultFilesVerified=preserved, newClips=detail, fps=config['fps']))
    validation_path = ROOT / 'Art/Characters/Childhood/validation-state.json'
    validation = json.loads(validation_path.read_text(encoding='utf-8'))
    validation['Yuuki']['animations'] = config.get('validationText', f'motion-v3: {count} drawings; front/back walking accepted; lateral walking and all running use four compact phases awaiting motion review')
    validation['Yuuki'].pop('acceptedDirections', None)
    validation['Yuuki']['acceptedClips'] = config.get('acceptedClips', ['walk_down', 'walk_up'])
    save_json(validation_path, validation)
    print(json.dumps(dict(frames=count, protectedFilesVerified=len(protected), adultFilesVerified=preserved, newClips=[{k: d[k] for k in ('clip', 'frames', 'headTopRangePixels', 'footBaselineRangePixels')} for d in detail])))


if __name__ == '__main__':
    main(sys.argv[1] if len(sys.argv) > 1 else 'motion-four-frame-v3.json')
