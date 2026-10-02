from pathlib import Path
from PIL import Image,ImageOps
import numpy as np
import json,hashlib,re
root=Path('D:/yuuki-pixel');stage=Path(__file__).parent
catalog=json.loads((root/'Assets/Game/Resources/Parents/Sara/animations.json').read_text(encoding='utf-8'))
clips={c['name']:c for c in catalog['clips']};guids=[];details=[]
assert len(clips)==12
for name,c in clips.items():
    assert len(c['frames'])==(3 if name.startswith('idle') else 4)
    assert all(i<len(c['frames']) for i in c['sequence'])
    bounds=[]
    for path in c['frames']:
        file=root/'Assets/Game/Resources'/(path+'.png');im=Image.open(file)
        assert im.mode=='RGBA' and im.size==(512,512)
        box=im.getchannel('A').getbbox();assert min(box[:2])>=12 and box[2]<=500 and box[3]<=500
        assert not np.any(np.array(im)[[0,-1],:,3]) and not np.any(np.array(im)[:,[0,-1],3])
        bounds.append(list(box));meta=Path(str(file)+'.meta').read_text()
        assert all(t in meta for t in ('filterMode: 0','enableMipMap: 0','textureCompression: 0','spritePixelsToUnits: 220','spritePivot: {x: 0.5, y: 0.21875}'))
        guids.append(re.search(r'^guid: ([a-f0-9]+)',meta,re.M)[1])
    details.append({'clip':name,'frames':len(c['frames']),'bounds':bounds})
assert len(guids)==44 and len(set(guids))==44
for state in ('walk','run','idle'):
    for right,left in zip(clips[state+'_right']['frames'],clips[state+'_left']['frames']):
        r=np.array(Image.open(root/'Assets/Game/Resources'/(right+'.png')))
        l=np.array(Image.open(root/'Assets/Game/Resources'/(left+'.png')))
        assert np.array_equal(np.roll(np.fliplr(r),1,axis=1),l)
for d in ('down','up'):
    for state in ('walk','run'):
        paths=clips[state+'_'+d]['frames']
        for a,b in ((0,2),(1,3)):
            ia=np.array(Image.open(root/'Assets/Game/Resources'/(paths[a]+'.png')))
            ib=np.array(Image.open(root/'Assets/Game/Resources'/(paths[b]+'.png')))
            assert np.array_equal(np.roll(np.fliplr(ia),1,axis=1),ib)
shoe_spans={}
for state in ('walk','run'):
    spans=[]
    for path in clips[state+'_right']['frames']:
        a=np.array(Image.open(root/'Assets/Game/Resources'/(path+'.png')));y,x=np.indices(a.shape[:2])
        box=Image.fromarray(a[:,:,3]).getbbox()
        shoe=(a[:,:,3]>100)&(y>box[1]+(box[3]-box[1])*.82)&(a[:,:,2]>a[:,:,0]*1.12)&(a[:,:,2]>a[:,:,1]*1.08)
        _,xs=np.where(shoe);assert len(xs)>10
        spans.append(int(xs.max()-xs.min()+1))
    assert min(spans[0],spans[2])>max(spans[1],spans[3])+15,(state,spans)
    shoe_spans[state]=spans
preserved={}
for folder,stems in [('Art/Characters/Childhood',('adult-preservation','yuuki-child-approved-preservation','alice-child-approved-preservation','tenebris-child-approved-preservation')),('Art/Characters/Parents',('sara-design-approved-preservation','kled-design-approved-preservation'))]:
    for stem in stems:
        data=json.loads((root/folder/(stem+'.json')).read_text(encoding='utf-8-sig'))
        for f in data['files']:assert hashlib.sha256((root/f['path']).read_bytes()).hexdigest()==f['sha256']
        preserved[stem]=len(data['files'])
report={'frames':44,'clips':12,'mode':'RGBA','frameSize':[512,512],'uniqueUnityGuids':True,'allFramesContained':True,'exactLateralMirror':True,'frontBackOppositePhasesVerified':True,'rightShoeHorizontalSpans':shoe_spans,'contactWiderThanPassing':True,'approvedFilesPreserved':preserved,'details':details,'browserPreview':'pending visual check'}
(stage/'sara-final-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='details'},ensure_ascii=False))
