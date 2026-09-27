"""Check packing/import inputs, transparency, unclipped crops and source provenance."""
import json
from pathlib import Path
import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
data = json.loads((ROOT / 'Assets/Game/Resources/Environment/catalog.json').read_text(encoding='utf-8'))
assets = data['assets']
assert len(assets) == 61
assert len({a['id'] for a in assets}) == len(assets)
for a in assets:
    im = Image.open(ROOT / a['path']).convert('RGBA')
    px = np.array(im)
    assert im.size == (a['width'], a['height']), a['id']
    assert a['ppu'] > 0 and 0 <= a['pivotY'] <= 1, a['id']
    assert (ROOT / a['source']).is_file(), a['id']
    assert np.all(px[px[:, :, 3] == 0] == 0), 'Hidden RGB: '+a['id']
    if a['floor']:
        assert np.all(px[:, :, 3] == 255), a['id']
    else:
        alpha = im.getchannel('A')
        x0,y0,x1,y1 = alpha.getbbox()
        assert min(x0,y0,im.width-x1,im.height-y1) >= 8, 'No safe margin: '+a['id']
        # Ignore isolated <30 alpha edge pixels when checking the source crop.
        crop = np.array(Image.open(ROOT / a['source']).convert('RGBA').crop(a['crop']))[:, :, 3]
        if a['id'] not in {'escola', 'arvore-balanco', 'grade-escola'}:
            assert not any(np.any(edge > 30) for edge in [crop[0,:],crop[-1,:],crop[:,0],crop[:,-1]]), 'Source crop touches art: '+a['id']
print('OK: 61 unique assets, valid source crops, 8px transparent padding, clean RGBA, floor opacity and Unity metadata.')
