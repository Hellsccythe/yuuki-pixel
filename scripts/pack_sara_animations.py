"""Sara animation packing: gutter splitting, alignment, nearest-neighbor and reflection only."""
from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import numpy as np
import hashlib,json,shutil,re,uuid,zipfile,importlib.util

ROOT=Path('D:/yuuki-pixel');STAGE=Path(__file__).parent
ART=ROOT/'Art/Characters/Parents/Sara/Animations-v1'
OUT=ROOT/'Assets/Game/Resources/Parents/Sara'
GEN=Path('C:/Users/Hellsccythe/.codex/generated_images/01a0de91-4e4f-79f2-9ff8-3bfa5d375ffa')
spec=importlib.util.spec_from_file_location('alice_packing',ROOT/'scripts/pack_child_alice.py')
alice=importlib.util.module_from_spec(spec);spec.loader.exec_module(alice)
def save(path,data):path.write_text(json.dumps(data,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def preservation():
    result={}
    for folder,stems in [('Art/Characters/Childhood',('adult-preservation','yuuki-child-approved-preservation','alice-child-approved-preservation','tenebris-child-approved-preservation')),('Art/Characters/Parents',('sara-design-approved-preservation',))]:
        for stem in stems:
            m=json.loads((ROOT/folder/(stem+'.json')).read_text(encoding='utf-8-sig'))
            for f in m['files']:assert digest(ROOT/f['path'])==f['sha256'],f['path']
            result[stem]=len(m['files'])
    return result
def meta(path):
    dest=Path(str(path)+'.meta')
    if dest.exists():return
    text=(ROOT/'Assets/Game/Resources/RpgRevision/Yuuki/idle_down_00.png.meta').read_text()
    text=re.sub(r'^guid: [a-f0-9]+','guid: '+uuid.uuid4().hex,text,count=1,flags=re.M)
    text=re.sub(r'spriteID: [a-f0-9]+','spriteID: '+uuid.uuid4().hex,text)
    text=re.sub(r'spritePixelsToUnits: \d+','spritePixelsToUnits: 220',text)
    text=re.sub(r'spritePivot: \{.*?\}','spritePivot: {x: 0.5, y: 0.21875}',text)
    text=re.sub(r'textureCompression: \d+','textureCompression: 0',text)
    dest.write_text(text,encoding='utf-8')
def extract(path,rows,cols):
    im=alice.clean(Image.open(path).convert('RGBA'));alpha=np.array(im)[:,:,3]
    yc=[0]+[alice.cut_line((alpha>0).astype('uint8')*255,round(im.height*r/rows)) for r in range(1,rows)]+[im.height]
    groups=[];xc=[]
    for r in range(rows):
        row=im.crop((0,yc[r],im.width,yc[r+1]));ra=np.array(row)[:,:,3]
        cuts=[0]+[alice.cut_line((ra>0).astype('uint8')*255,round(im.width*c/cols),axis=1) for c in range(1,cols)]+[im.width]
        xc.append(cuts);poses=[]
        for c in range(cols):
            # Reuse the same detached-speck filtering as the approved Alice pipeline.
            pose=alice.clean(row.crop((cuts[c],0,cuts[c+1],row.height)))
            pa=np.array(pose)[:,:,3]
            assert not ((pa[0]>110).any() or (pa[-1]>110).any() or (pa[:,0]>110).any() or (pa[:,-1]>110).any()),(path,r,c,'clipped source')
            # A one-pixel gutter can place a complete soft edge at the cell end.
            # Retain that edge and add transparent padding before normalization.
            poses.append(ImageOps.expand(pose,border=2,fill=(0,0,0,0)))
        groups.append(poses)
    return groups,{'rows':yc,'columns':xc}
def metric(pose):
    a=np.array(pose);yy,xx=np.indices(a.shape[:2]);ys,xs=np.where(a[:,:,3]>110)
    top,bottom=int(ys.min()),int(ys.max()+1)
    crown=(a[:,:,3]>110)&(yy<top+(bottom-top)*.15)
    _,hx=np.where(crown)
    return top,bottom,float(np.median(hx))
def normalize(pose,scale,bob=0,idle=False):
    top,bottom,cx=metric(pose);box=pose.getchannel('A').getbbox();crop=pose.crop(box)
    crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.NEAREST)
    x=round(256-(cx-box[0])*scale)
    y=400-round((bottom-box[1])*scale) if idle else 108+bob-round((top-box[1])*scale)
    assert x>=12 and y>=12 and x+crop.width<=500 and y+crop.height<=500,(x,y,crop.size)
    out=Image.new('RGBA',(512,512));out.alpha_composite(crop,(x,y))
    return out,{'x':256,'y':round(y+(top-box[1])*scale-24)}
def reflect(im):
    a=np.roll(np.array(ImageOps.mirror(im)),1,axis=1)
    assert not a[:,0,3].any()
    return Image.fromarray(a)
def approve_kled():
    folder=ROOT/'Art/Characters/Parents/Kled/Design-v2';resource=ROOT/'Assets/Game/Resources/Parents/KledV2'
    profile=json.loads((folder/'design.json').read_text(encoding='utf-8'))
    profile.update(status='initial design approved by user',approvedDate='2026-10-01')
    for p in (folder/'design.json',resource/'design.json'):save(p,profile)
    manifest=ROOT/'Art/Characters/Parents/kled-design-approved-preservation.json'
    if not manifest.exists():
        files=[p for base in (folder,resource) for p in base.rglob('*') if p.is_file()]
        archive=ROOT/'Logs/Archives/kled-parent-design-v2-approved-20261001.zip';assert not archive.exists()
        with zipfile.ZipFile(archive,'w',zipfile.ZIP_DEFLATED) as z:
            for p in files:z.write(p,str(p.relative_to(ROOT)))
        save(manifest,{'character':'Kled','revision':2,'status':'design approved; no animation approval implied','archive':str(archive.relative_to(ROOT)).replace('\\','/'),'files':[{'path':str(p.relative_to(ROOT)).replace('\\','/'),'sha256':digest(p)} for p in files]})
    return profile
def main():
    protected=preservation()
    unchanged={str(p.relative_to(ROOT)):digest(p) for folder in ('Art/Characters/Childhood/Yuuki/Animations-v2','Assets/Game/Resources/Childhood/YuukiV2','Art/Characters/Parents/Kled/Design-v1','Assets/Game/Resources/Parents/Kled') for p in (ROOT/folder).rglob('*') if p.is_file()}
    assert not (OUT/'animations.json').exists(),'Preserve existing catalog before creating another revision'
    for folder in (ART/'Sources',ART/'Atlases',OUT/'Frames'):folder.mkdir(parents=True,exist_ok=True)
    cfgpath=STAGE/'sara-animation-production-prompts.json'
    if not cfgpath.exists():cfgpath=ART/'production-prompts.json'
    cfg=json.loads(cfgpath.read_text(encoding='utf-8'));save(ART/'production-prompts.json',cfg)
    for key,name in cfg['sources'].items():shutil.copy2(GEN/name,ART/'Sources'/(key+'.png'))
    clips=[];details=[]
    for direction in ('down','up','right'):
        motion,cuts=extract(ART/'Sources'/('motion_'+direction+'.png'),2,4 if direction=='right' else 2)
        idle,idlecuts=extract(ART/'Sources'/('idle_'+direction+'.png'),1,3)
        for state,poses in zip(('walk','run','idle'),[motion[0],motion[1],idle[0]]):
            # One uniform scale per generated row; never stretch individual limbs.
            scale=292/float(np.median([metric(p)[1]-metric(p)[0] for p in poses]))
            frames=[];anchors=[];ims=[]
            for i,pose in enumerate(poses):
                frame,anchor=normalize(pose,scale,bob=(-1 if i%2 and state!='idle' else 0),idle=state=='idle')
                ims.append(frame);anchors.append(anchor)
            if direction in ('down','up') and state!='idle':
                ims+= [reflect(p) for p in ims[:2]]
                anchors += [{'x':512-a['x'],'y':a['y']} for a in anchors[:2]]
            for i,im in enumerate(ims):
                name=f'{state}_{direction}_v1_{i:02}';dest=OUT/'Frames'/(name+'.png');im.save(dest);meta(dest)
                frames.append('Parents/Sara/Frames/'+name)
            clips.append({'name':state+'_'+direction,'frames':frames,'haloAnchors':anchors,'fps':6 if state=='walk' else 8 if state=='run' else 2,'loop':True,'sequence':[0,1,2,1] if state=='idle' else [0,1,2,3]})
            bounds=[list(i.getchannel('A').getbbox()) for i in ims]
            details.append({'clip':state+'_'+direction,'scale':scale,'bounds':bounds,'cuts':idlecuts if state=='idle' else cuts,'oppositePhaseReflected':direction!='right' and state!='idle'})
    for state in ('walk','run','idle'):
        src=next(c for c in clips if c['name']==state+'_right');paths=[]
        for i,path in enumerate(src['frames']):
            body=Image.open(ROOT/'Assets/Game/Resources'/(path+'.png')).convert('RGBA');left=reflect(body)
            name=f'{state}_left_v1_{i:02}';dest=OUT/'Frames'/(name+'.png');left.save(dest);meta(dest)
            assert np.array_equal(np.array(Image.open(dest)),np.array(left))
            paths.append('Parents/Sara/Frames/'+name)
        clips.append({'name':state+'_left','frames':paths,'haloAnchors':[{'x':512-a['x'],'y':a['y']} for a in src['haloAnchors']],'fps':src['fps'],'loop':True,'sequence':src['sequence'][:],'mirroredFrom':state+'_right'})
    ordered=[next(c for c in clips if c['name']==st+'_'+d) for d in ('down','up','left','right') for st in ('walk','run','idle')]
    design=json.loads((ROOT/'Art/Characters/Parents/Sara/Design-v1/design.json').read_text(encoding='utf-8'))
    halo={k:v for k,v in design['halo'].items() if k!='anchor'};halo.update(status='approved design retained',alphaBaked=False)
    catalog={'character':'Sara','lifeStage':'adult','chapter':'childhood of Yuuki','status':'first animation pass awaiting user motion review','designApproved':True,'weapons':False,'bodyFrame':design['bodyFrame'],'halo':halo,'wingAnatomy':design['wingAnatomy'],'playbackRevision':'sara-v1','clips':ordered}
    assert len(ordered)==12 and sum(len(c['frames']) for c in ordered)==44
    overview=Image.new('RGB',(1024,2880),'#253239');draw=ImageDraw.Draw(overview)
    for di,direction in enumerate(('down','up','left','right')):
        atlas=Image.new('RGBA',(2048,1536))
        for row,state in enumerate(('walk','run','idle')):
            clip=next(c for c in ordered if c['name']==state+'_'+direction)
            for col,path in enumerate(clip['frames']):
                im=Image.open(ROOT/'Assets/Game/Resources'/(path+'.png')).convert('RGBA')
                atlas.alpha_composite(im,(col*512,row*512))
                thumb=im.crop((64,64,448,416)).resize((240,220),Image.Resampling.NEAREST)
                yy=(di*3+row)*240;overview.paste(thumb,(col*256+8,yy),thumb)
                draw.text((col*256+8,yy+222),state+' '+direction+' '+str(col+1),fill='#e3ded4')
        atlas.save(ART/'Atlases'/(direction+'.png'))
    overview.save(ART/'contact-sheet.png')
    kled=approve_kled()
    statepath=ROOT/'Art/Characters/Parents/design-state.json';state=json.loads(statepath.read_text(encoding='utf-8'))
    state.update(phase='Sara and Kled designs approved; Sara animation pass ready for review; Kled has no animations yet',characters=[design,kled],SaraAnimations={'preview':'preview/sara-animation.html','catalog':'Assets/Game/Resources/Parents/Sara/animations.json','clips':12,'drawings':44,'status':'awaiting motion review'})
    save(statepath,state)
    assert preservation()==protected and all(digest(ROOT/p)==h for p,h in unchanged.items())
    save(ART/'packing-report.json',{'character':'Sara','drawings':44,'clips':12,'selectedGeneratedDrawings':25,'exactReflectedDrawings':19,'exactLateralMirror':True,'frontBackOppositePhasesReflected':True,'protectedFilesVerified':protected,'otherFilesUnchanged':len(unchanged),'clipsDetail':details,'processing':'reuse approved Alice detached-speck cleanup; crop; one constant nearest-neighbor scale per row; integer registration; exact reflection; no anatomy painting'})
    save(OUT/'animations.json',catalog)
    print(json.dumps({'drawings':44,'clips':12,'protected':protected,'unchangedOtherFiles':len(unchanged),'output':str(OUT)}))

if __name__=='__main__':main()
