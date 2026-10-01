"""Pack independently generated Yuuki directions without altering approved assets.

This script only crops, clears detached specks, registers and packs ImageGen art.
It never draws anatomy, stretches limbs or mirrors asymmetric wings.
"""
from pathlib import Path
import json, shutil, hashlib, re, uuid
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT/'Art/Characters/Childhood/Yuuki/Animations-v2'
OUT = ROOT/'Assets/Game/Resources/Childhood/YuukiV2'
GEN = Path('C:/Users/Hellsccythe/.codex/generated_images/01a0de91-4e4f-79f2-9ff8-3bfa5d375ffa')
DIRECTIONS = ('down', 'up', 'left', 'right')
STATES = ('walk', 'run', 'idle')

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def save(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')

def protected():
    counts = {}
    for name in ('yuuki-child-approved-preservation', 'alice-child-approved-preservation',
                 'tenebris-child-approved-preservation', 'adult-preservation'):
        manifest = json.loads((ROOT/'Art/Characters/Childhood'/(name+'.json')).read_text(encoding='utf-8-sig'))
        bad = [f['path'] for f in manifest['files'] if digest(ROOT/f['path']) != f['sha256']]
        assert not bad, ('Approved assets changed', bad)
        counts[name] = len(manifest['files'])
    return counts

def metadata(path, pivot=(.5, .21875)):
    meta = Path(str(path)+'.meta')
    if meta.exists():
        return
    template = (ROOT/'Assets/Game/Resources/RpgRevision/Yuuki/idle_down_00.png.meta').read_text()
    template = re.sub(r'guid: [a-f0-9]+', 'guid: '+uuid.uuid4().hex, template, count=1)
    template = re.sub(r'spritePixelsToUnits: \d+', 'spritePixelsToUnits: 220', template)
    template = re.sub(r'spritePivot: \{.*?\}', f'spritePivot: {{x: {pivot[0]}, y: {pivot[1]}}}', template)
    template = re.sub(r'textureCompression: \d+', 'textureCompression: 0', template)
    template = re.sub(r'spriteID: [a-f0-9]+', 'spriteID: '+uuid.uuid4().hex, template)
    meta.write_text(template, encoding='utf-8')

def clean(im):
    a = np.array(im.convert('RGBA'))
    solid = a[:, :, 3] > 100
    seen = np.zeros(solid.shape, dtype=bool)
    kept = np.zeros(solid.shape, dtype=bool)
    height, width = solid.shape
    for sy, sx in zip(*np.where(solid)):
        if seen[sy, sx]:
            continue
        seen[sy, sx] = True
        queue = deque([(int(sy), int(sx))])
        pixels = []
        while queue:
            y, x = queue.popleft()
            pixels.append((y, x))
            for yy in range(max(0, y-1), min(height, y+2)):
                for xx in range(max(0, x-1), min(width, x+2)):
                    if solid[yy, xx] and not seen[yy, xx]:
                        seen[yy, xx] = True
                        queue.append((yy, xx))
        if len(pixels) > 40:
            ys, xs = zip(*pixels)
            kept[ys, xs] = True
    kept = np.array(Image.fromarray(kept.astype('uint8')*255).filter(ImageFilter.MaxFilter(3))) > 0
    a[~kept | (a[:, :, 3] < 28)] = 0
    a[a[:, :, 3] == 0] = 0
    return Image.fromarray(a)

def metric(im):
    a = np.array(im)
    ys, xs = np.where(a[:, :, 3] > 110)
    assert len(xs), 'Empty sprite'
    top, bottom = int(ys.min()), int(ys.max()+1)
    y, x = np.indices(a.shape[:2])
    # White hair crown only, above the wings; avoids the black temple ribbon.
    crown = ((a[:, :, 3] > 110) & (a[:, :, :3].min(2) > 100)
             & (a[:, :, :3].max(2) > 140) & (y >= top)
             & (y < top+(bottom-top)*.22))
    _, hx = np.where(crown)
    assert len(hx), 'Cannot register white hair crown'
    crown_width = float(np.percentile(hx, 98)-np.percentile(hx, 2)+1)
    return top, bottom, float(np.median(hx)), crown_width

def cut_line(alpha, expected, axis=0):
    if axis:
        alpha = alpha.T
    radius = max(40, round(alpha.shape[0]/12))
    start, end = max(0, expected-radius), min(alpha.shape[0], expected+radius)
    scores = (alpha[start:end] > 110).sum(1)
    zero = np.where(scores == 0)[0]
    assert len(zero), 'No transparent gutter at expected cell boundary'
    runs = np.split(zero, np.where(np.diff(zero) > 1)[0]+1)
    run = min(runs, key=lambda r: abs(start+float(np.median(r))-expected))
    return start+round(float(np.median(run)))

def extract(path, rows=3, selected_rows=None):
    im = Image.open(path).convert('RGBA')
    a = np.array(im)[:, :, 3]
    yc = [0]+[cut_line(a, round(im.height*r/rows)) for r in range(1, rows)]+[im.height]
    groups, xc = [], []
    for r in range(rows):
        row = im.crop((0, yc[r], im.width, yc[r+1]))
        ra = np.array(row)[:, :, 3]
        cuts = [0]+[cut_line(ra, round(im.width*c/4), axis=1) for c in range(1, 4)]+[im.width]
        xc.append(cuts)
        count = 3 if rows == 3 and r == 2 else 4
        poses = []
        if selected_rows is None or r in selected_rows:
            for c in range(count):
                pose = clean(row.crop((cuts[c], 0, cuts[c+1], row.height)))
                pa = np.array(pose)[:, :, 3]
                assert not (pa[0].any() or pa[-1].any() or pa[:, 0].any() or pa[:, -1].any()), (str(path), r, c, 'clipped cell')
                poses.append(pose)
        groups.append(poses)
    return groups, {'rows': yc, 'columns': xc}

def normalize(pose, scale, bob=0, feet_fixed=False):
    top, bottom, hx, _ = metric(pose)
    box = pose.getchannel('A').getbbox()
    crop = pose.crop(box)
    crop = crop.resize((round(crop.width*scale), round(crop.height*scale)), Image.Resampling.NEAREST)
    x = round(256-(hx-box[0])*scale)
    y = 400-round((bottom-box[1])*scale) if feet_fixed else 180+bob-round((top-box[1])*scale)
    assert x >= 12 and y >= 12 and x+crop.width <= 500 and y+crop.height <= 500
    frame = Image.new('RGBA', (512, 512))
    frame.alpha_composite(crop, (x, y))
    return frame, {'x': 256, 'y': round(y+(top-box[1])*scale-24)}

def main():
    before = protected()
    for folder in (ART/'Sources', ART/'Atlases', OUT/'Frames'):
        folder.mkdir(parents=True, exist_ok=True)
    cfg = json.loads((ART/'production-prompts.json').read_text(encoding='utf-8'))
    for key, filename in cfg.get('earlierVariants', {}).items():
        dest = ART/'Sources/History'/(key+'.png')
        dest.parent.mkdir(exist_ok=True)
        if not dest.exists():
            shutil.copy2(GEN/filename, dest)
    for key, filename in cfg['sources'].items():
        shutil.copy2(GEN/filename, ART/'Sources'/(key+'.png'))
    original_halo = ROOT/'Assets/Game/Resources/Childhood/Yuuki/halo-neutral.png'
    halo_hash = digest(original_halo)
    shutil.copy2(original_halo, OUT/'halo-neutral.png')
    metadata(OUT/'halo-neutral.png', (.5, .5))
    halo = Image.open(OUT/'halo-neutral.png').convert('RGBA')
    clips, details = [], []
    for direction in DIRECTIONS:
        selections = cfg.get('rowSelections', {}).get(direction, {})
        selected_rows = [i for i, state in enumerate(STATES) if state not in selections]
        groups, cuts = extract(ART/'Sources'/(direction+'.png'), selected_rows=selected_rows)
        row_cuts = {}
        for state, selection in selections.items():
            selection = {'source': selection, 'rows': 1, 'row': 0} if isinstance(selection, str) else selection
            extra, extra_cuts = extract(ART/'Sources'/(selection['source']+'.png'),
                                        rows=selection['rows'], selected_rows=[selection['row']])
            groups[STATES.index(state)] = extra[selection['row']]
            row_cuts[state] = extra_cuts
        scale = 220/float(np.median([metric(p)[1]-metric(p)[0] for p in groups[2]]))
        idle_crown = float(np.median([metric(p)[3] for p in groups[2]]))
        for state, poses in zip(STATES, groups):
            row_scale = scale*idle_crown/float(np.median([metric(p)[3] for p in poses]))
            resources, anchors, bounds = [], [], []
            for i, pose in enumerate(poses):
                frame, anchor = normalize(pose, row_scale, (-1 if i % 2 else 0) if state != 'idle' else 0, feet_fixed=state == 'idle')
                name = f'{state}_{direction}_v2_{i:02}'
                path = OUT/'Frames'/(name+'.png')
                frame.save(path)
                metadata(path)
                resources.append('Childhood/YuukiV2/Frames/'+name)
                anchors.append(anchor)
                bounds.append(frame.getchannel('A').getbbox())
            clips.append({'name': state+'_'+direction, 'frames': resources, 'haloAnchors': anchors,
                          'fps': 6 if state == 'walk' else 8 if state == 'run' else 2,
                          'loop': True, 'sequence': [0, 1, 2, 1] if state == 'idle' else [0, 1, 2, 3]})
            details.append({'clip': state+'_'+direction, 'frames': len(poses), 'scale': row_scale,
                            'cuts': row_cuts.get(state, cuts), 'bounds': bounds,
                            'headTopRangePixels': max(b[1] for b in bounds)-min(b[1] for b in bounds),
                            'footBaselineRangePixels': max(b[3] for b in bounds)-min(b[3] for b in bounds)})
    catalog = {'character': 'Yuuki', 'age': 9, 'status': 'motion-revision-awaiting-review',
               'designApproved': True, 'weapons': False, 'playbackRevision': 'yuuki-v2-alice-tenebris-cadence',
               'bodyFrame': {'width': 512, 'height': 512, 'pivot': [.5, .21875], 'pixelsPerUnit': 220, 'feet': [256, 400]},
               'halo': {'resource': 'Childhood/YuukiV2/halo-neutral', 'width': halo.width, 'height': halo.height,
                        'alphaBaked': True, 'geometry': 'Yuuki-v2', 'tintable': True, 'status': 'approved', 'originalSha256': halo_hash},
               'wingAnatomy': {'left': 'black', 'right': 'white'}, 'independentDirections': True,
               'motionReference': ['Alice approved', 'Tenebris approved'], 'clips': clips}
    save(OUT/'animations.json', catalog)
    overview = Image.new('RGB', (760, 2520), '#263139')
    draw = ImageDraw.Draw(overview)
    layout = {}
    for di, direction in enumerate(DIRECTIONS):
        atlas = Image.new('RGBA', (2048, 1536))
        layout[direction] = {}
        for row, state in enumerate(STATES):
            clip = next(c for c in clips if c['name'] == state+'_'+direction)
            layout[direction][state] = clip['frames']
            for col, resource in enumerate(clip['frames']):
                im = Image.open(ROOT/'Assets/Game/Resources'/(resource+'.png')).convert('RGBA')
                atlas.alpha_composite(im, (col*512, row*512))
                thumb = im.crop((96, 104, 416, 424)).resize((190, 190), Image.Resampling.NEAREST)
                yy = (di*3+row)*210
                overview.paste(thumb, (col*190, yy), thumb)
                draw.text((col*190+5, yy+190), resource.rsplit('/', 1)[-1], fill='#ddd6c7')
        atlas.save(ART/'Atlases'/(direction+'.png'))
    overview.save(ART/'contact-sheet.png')
    assert protected() == before
    assert digest(OUT/'halo-neutral.png') == halo_hash
    assert len(clips) == 12 and sum(len(c['frames']) for c in clips) == 44
    report = {'character': 'Yuuki child', 'revision': 'v2', 'drawings': 44, 'clips': 12,
              'independentDirections': True, 'haloExactReuse': True, 'haloSha256': halo_hash,
              'protectedFilesVerified': before, 'approvedOldYuukiUnchanged': True,
              'haloMaximumAlpha': int(np.array(halo)[:, :, 3].max()), 'atlasLayout': layout, 'clipsDetail': details}
    save(ART/'packing-report.json', report)
    state_path = ROOT/'Art/Characters/Childhood/validation-state.json'
    state = json.loads(state_path.read_text(encoding='utf-8'))
    state['phase'] = 'Three original childhood sets approved; Yuuki motion revision v2 awaiting user review'
    state['Yuuki']['motionRevision'] = {'revision': 'v2', 'status': 'awaiting user review',
                                       'catalog': OUT.relative_to(ROOT).as_posix()+'/animations.json',
                                       'preview': 'preview/yuuki-animation-v2.html', 'previousApprovedSetPreserved': True}
    save(state_path, state)
    print(json.dumps({'drawings': 44, 'clips': 12, 'protected': before, 'haloExactReuse': True, 'details': details}))

if __name__ == '__main__':
    main()
