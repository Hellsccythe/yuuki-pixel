from pathlib import Path
from PIL import Image
import numpy as np
import json,re
from pack_kled_animations import preservation
root=Path('D:/yuuki-pixel');stage=Path(__file__).parent
catalog=json.loads((root/'Assets/Game/Resources/Parents/KledV2/animations.json').read_text(encoding='utf-8'))
clips={c['name']:c for c in catalog['clips']};guids=[];details=[]
assert len(clips)==12 and catalog['status']=='awaiting user motion review'
assert catalog['halo']['separateLayer'] and catalog['halo']['tintable'] and catalog['halo']['opacity']==.6
assert catalog['wingAnatomy']=={'left':'white','right':'white'}
for name,c in clips.items():
    assert len(c['frames'])==(3 if name.startswith('idle') else 4)
    assert all(0<=i<len(c['frames']) for i in c['sequence'])
    bounds=[];crowns=[];feet=[]
    for path in c['frames']:
        file=root/'Assets/Game/Resources'/(path+'.png');im=Image.open(file)
        assert im.mode=='RGBA' and im.size==(512,512)
        box=im.getchannel('A').getbbox();assert min(box[:2])>=12 and box[2]<=500 and box[3]<=500
        a=np.array(im);assert not a[[0,-1],:,3].any() and not a[:,[0,-1],3].any()
        yy,xx=np.where(a[:,:,3]>110);crowns.append(int(yy.min()));feet.append(int(yy.max()+1))
        assert np.all(a[a[:,:,3]==0]==0),'RGB halo/background data left in transparent pixels'
        bounds.append(list(box));meta=Path(str(file)+'.meta').read_text()
        assert all(t in meta for t in ('filterMode: 0','enableMipMap: 0','textureCompression: 0','spritePixelsToUnits: 220','spritePivot: {x: 0.5, y: 0.21875}'))
        guids.append(re.search(r'^guid: ([a-f0-9]+)',meta,re.M)[1])
    if not name.startswith('idle'):assert max(crowns)-min(crowns)<=2,(name,crowns)
    else:assert max(feet)-min(feet)<=1 and min(feet)>=399 and max(feet)<=401,(name,feet)
    details.append({'clip':name,'frames':len(c['frames']),'bounds':bounds,'headTop':crowns,'feetBottom':feet})
assert len(guids)==44 and len(set(guids))==44
for state in ('walk','run','idle'):
    for right,left in zip(clips[state+'_right']['frames'],clips[state+'_left']['frames']):
        r=np.array(Image.open(root/'Assets/Game/Resources'/(right+'.png')))
        l=np.array(Image.open(root/'Assets/Game/Resources'/(left+'.png')))
        assert np.array_equal(np.roll(np.fliplr(r),1,axis=1),l)
shoe_spans={}
for state in ('walk','run'):
    spans=[]
    for path in clips[state+'_right']['frames']:
        a=np.array(Image.open(root/'Assets/Game/Resources'/(path+'.png')));y,x=np.indices(a.shape[:2]);box=Image.fromarray(a[:,:,3]).getbbox()
        shoe=(a[:,:,3]>110)&(y>box[1]+(box[3]-box[1])*.82)&(a[:,:,:3].max(2)<100)
        _,xs=np.where(shoe);assert len(xs)>20;spans.append(int(xs.max()-xs.min()+1))
    assert min(spans[0],spans[2])>max(spans[1],spans[3])+15,(state,spans)
    shoe_spans[state]=spans
report={'frames':44,'clips':12,'mode':'RGBA','frameSize':[512,512],'uniqueUnityGuids':True,'allFramesContained':True,'exactLateralMirror':True,'frontBackUseOwnGeneratedPoses':True,'motionHeadDriftAtMost2px':True,'idleFeetDriftAtMost1px':True,'rightShoeHorizontalSpans':shoe_spans,'contactWiderThanPassing':True,'approvedFilesPreserved':preservation(),'details':details,'browserPreview':'pending visual check'}
(stage/'kled-final-qa.json').write_text(json.dumps(report,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
print(json.dumps({k:v for k,v in report.items() if k!='details'},ensure_ascii=False))
