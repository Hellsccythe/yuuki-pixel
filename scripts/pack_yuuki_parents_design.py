"""Prepare two initial parent designs; crop/scale only, no painted anatomy."""
from pathlib import Path
import hashlib, json, re, shutil, uuid
import numpy as np
from PIL import Image

ROOT=Path('D:/yuuki-pixel')
ART=ROOT/'Art/Characters/Parents'
OUT=ROOT/'Assets/Game/Resources/Parents'
GEN=Path('C:/Users/Hellsccythe/.codex/generated_images/01a0de91-4e4f-79f2-9ff8-3bfa5d375ffa')
STAGE=Path(__file__).parent

def save(path,data):
    path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def preservation():
    result={}
    for name in ('adult-preservation','yuuki-child-approved-preservation',
                 'alice-child-approved-preservation','tenebris-child-approved-preservation'):
        data=json.loads((ROOT/'Art/Characters/Childhood'/(name+'.json')).read_text(encoding='utf-8-sig'))
        assert all(hashlib.sha256((ROOT/e['path']).read_bytes()).hexdigest()==e['sha256'] for e in data['files']),name
        result[name]=len(data['files'])
    # Also preserve Yuuki's new candidate revision, even though not approved yet.
    result['yuukiV2']={str(p.relative_to(ROOT)):hashlib.sha256(p.read_bytes()).hexdigest()
                       for folder in ('Art/Characters/Childhood/Yuuki/Animations-v2','Assets/Game/Resources/Childhood/YuukiV2')
                       for p in (ROOT/folder).rglob('*') if p.is_file()}
    return result

def meta(path,pivot):
    out=Path(str(path)+'.meta')
    assert not out.exists(),('Do not replace initial design without versioning',str(out))
    s=(ROOT/'Assets/Game/Resources/RpgRevision/Yuuki/idle_down_00.png.meta').read_text()
    s=re.sub(r'guid: [a-f0-9]+','guid: '+uuid.uuid4().hex,s,count=1)
    s=re.sub(r'spriteID: [a-f0-9]+','spriteID: '+uuid.uuid4().hex,s)
    s=re.sub(r'spritePixelsToUnits: \d+','spritePixelsToUnits: 220',s)
    s=re.sub(r'spritePivot: \{.*?\}',f'spritePivot: {{x: {pivot[0]}, y: {pivot[1]}}}',s)
    s=re.sub(r'textureCompression: \d+','textureCompression: 0',s)
    out.write_text(s,encoding='utf-8')

def bounds(im,threshold=12):
    alpha=np.array(im)[:,:,3]
    box=Image.fromarray((alpha>threshold).astype('uint8')*255).getbbox()
    assert box,'Empty generated asset'
    # Include the complete generated alpha; no transparency repainting.
    return im.getchannel('A').getbbox(),box

def body_sprite(source,height):
    im=Image.open(source).convert('RGBA');box,solid=bounds(im)
    assert min(solid[:2])>0 and solid[2]<im.width and solid[3]<im.height,'Source clipped'
    crop=im.crop(box);scale=height/(solid[3]-solid[1])
    crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.NEAREST)
    a=np.array(im);yy,xx=np.indices(a.shape[:2])
    foot=(a[:,:,3]>110)&(yy>=solid[3]-(solid[3]-solid[1])*.1)
    _,fx=np.where(foot)
    cx=float(np.median(fx))
    x=round(256-(cx-box[0])*scale)
    y=round(400-(solid[3]-box[1])*scale)
    assert x>=12 and y>=12 and x+crop.width<=500 and y+crop.height<=500
    canvas=Image.new('RGBA',(512,512));canvas.alpha_composite(crop,(x,y))
    alpha=canvas.getchannel('A');b=alpha.getbbox()
    return canvas,{'x':256,'y':b[1]-22},b

def main():
    before=preservation()
    cfgpath=STAGE/'yuuki-parents-prompts.json'
    if not cfgpath.exists():cfgpath=ART/'production-prompts.json'
    cfg=json.loads(cfgpath.read_text(encoding='utf-8'))
    ART.mkdir(parents=True,exist_ok=True)
    save(ART/'production-prompts.json',cfg)
    profiles=[];report=[]
    for name,target_height in [('Sara',292),('Kled',304)]:
        folder=ART/name/'Design-v1';resource=OUT/name
        folder.mkdir(parents=True,exist_ok=True);resource.mkdir(parents=True,exist_ok=True)
        raw=folder/'body-source.png';assert not raw.exists(),str(raw)
        shutil.copy2(GEN/cfg['sources'][name],raw)
        body,anchor,box=body_sprite(raw,target_height)
        body.save(folder/'body.png');body.save(resource/'stand_down_00.png')
        meta(resource/'stand_down_00.png',(.5,.21875))
        halo_source=folder/'halo-source.png'
        shutil.copy2(GEN/cfg['sources'][name+'Halo'],halo_source)
        hi=Image.open(halo_source).convert('RGBA');hb=Image.fromarray((np.array(hi)[:,:,3]>8).astype('uint8')*255).getbbox()
        hi=hi.crop(hb);hi=hi.resize((110,round(hi.height*110/hi.width)),Image.Resampling.NEAREST)
        hi.save(folder/'halo-neutral.png');hi.save(resource/'halo-neutral.png')
        meta(resource/'halo-neutral.png',(.5,.5))
        canon=cfg['canon'][name]
        profile={'name':name,'relation':'mother' if name=='Sara' else 'father',
                 'status':'initial design awaiting user approval','story':cfg['story'],
                 'canon':canon,'proposal':cfg['designProposals'][name],
                 'body':f'Parents/{name}/stand_down_00','bodyFrame':{'width':512,'height':512,'feet':[256,400],'pivot':[.5,.21875],'pixelsPerUnit':220},
                 'halo':{'resource':f'Parents/{name}/halo-neutral','width':110,'height':hi.height,'anchor':anchor,
                         'opacity':.6,'tintable':True,'separateLayer':True,'status':'geometry proposal'},
                 'weapons':False,'wingAnatomy':{'left':'white','right':'white'},'animationFrames':0}
        save(folder/'design.json',profile);save(resource/'design.json',profile);profiles.append(profile)
        report.append({'character':name,'frameSize':[512,512],'bodyBounds':box,
                       'bodyTargetHeight':target_height,'sourceAlphaPreserved':True,'noAnatomyPainted':True,
                       'haloSize':list(hi.size),'separateHalo':True})
    save(ART/'design-state.json',{'date':cfg['date'],'phase':'two neutral designs for visual approval; no animations yet','characters':profiles,
                                'preview':'preview/yuuki-parents-design.html','storySource':cfg['story']})
    assert preservation()==before
    save(ART/'packing-report.json',{'characters':report,'approvedFilesVerified':{k:v for k,v in before.items() if k!='yuukiV2'},
                                  'yuukiV2CandidateFilesVerified':len(before['yuukiV2']),'unchangedCharacters':True})
    print(json.dumps({'characters':report,'preserved':{k:(len(v) if k=='yuukiV2' else v) for k,v in before.items()}}))

if __name__=='__main__':main()
