from pathlib import Path
import json,hashlib
from PIL import Image
from pack_intro_assets import preservation,kled_extract,R,O,A,h

protected=preservation();count=0;names=[]
for catalog in ('actions','npcs'):
 data=json.loads((O/(catalog+'.json')).read_text())
 for clip in data['clips']:
  assert 0<len(clip['frames'])<=4,clip['name']
  hashes=[]
  for path in clip['frames']:
   p=R/'Assets/Game/Resources'/(path+'.png');im=Image.open(p).convert('RGBA');box=im.getchannel('A').getbbox()
   assert im.size==(512,512) and box and min(box[:2])>=10 and max(box[2:])<=502,(path,box)
   hashes.append(hashlib.sha256(p.read_bytes()).hexdigest());count+=1
  assert len(set(hashes))==len(hashes),('Duplicate animation drawing',clip['name'])
  names.append(clip['name'])
report={'newFrames':count,'cycles':names,'maximumDrawingsPerAnimation':4,'allFramesInsideTransparentMargins':True,'allDrawingsDistinct':True,'protectedFiles':protected,'protectedFileCount':sum(protected.values()),'tool':'built-in image generation','mechanicalProcessingOnly':True}
h.save(A/'asset-qa.json',report)
print(json.dumps(report))
