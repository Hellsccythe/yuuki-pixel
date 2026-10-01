"""Pack generated drawings without painting, mirroring or warping poses."""
import hashlib,json,re,shutil,sys,uuid
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'.venv/Lib/site-packages'))
from scipy import ndimage as ndi
STAGE=Path(__file__).resolve().parent
GEN=Path('C:/Users/Hellsccythe/.codex/generated_images/01a0de91-4e4f-79f2-9ff8-3bfa5d375ffa')
ART=ROOT/'Art/Characters/Childhood/Yuuki/Animations-v1'
OUT=ROOT/'Assets/Game/Resources/Childhood/Yuuki'
SOURCES={'down':'exec-be5a8da3-f1ba-4f7c-93a0-8635a796b243.png','up':'exec-d902bc01-25f6-47cc-9876-2b125058f762.png','left':'exec-96645c23-bf33-4feb-8576-53b9491dcbd3.png','right':'exec-a5061462-c2e3-4af3-a863-30a6a763b4e7.png'}
WALKS={'down':'exec-7d3dd9aa-1a18-4e4a-abfe-831c2a4504b5.png','up':'exec-e55ed079-645b-4754-b76b-5bf82558862b.png','left':'exec-a16afe6d-c608-4f3d-9754-e1bc3910e4b2.png','right':'exec-58641473-be2e-452e-9cf0-42657c30092b.png'}
def digest(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def check_adult():
 m=json.loads((ROOT/'Art/Characters/Childhood/adult-preservation.json').read_text(encoding='utf-8-sig'))
 changed=[f['path'] for f in m['files'] if digest(ROOT/f['path'])!=f['sha256']]
 assert not changed,changed
 return len(m['files'])
def clean(im):
 a=np.array(im.convert('RGBA'));labels,_=ndi.label(a[:,:,3]>110)
 counts=np.bincount(labels.ravel());counts[0]=0
 mask=ndi.binary_dilation(np.isin(labels,np.where(counts>35)[0]),iterations=1)
 a[~mask | (a[:,:,3]<28)]=0;a[a[:,:,3]==0]=0
 return Image.fromarray(a)
def gutter(a,expected):
 start=max(0,expected-38);end=min(a.shape[0],expected+65)
 scores=(a[start:end]>110).sum(1);zero=np.where(scores==0)[0]
 if len(zero):
  runs=np.split(zero,np.where(np.diff(zero)>1)[0]+1)
  return start+int(np.median(max(runs,key=len)))
 return start+int(scores.argmin())
def metrics(im):
 a=np.array(im);solid=a[:,:,3]>110;ys,xs=np.where(solid);top=int(ys.min());bottom=int(ys.max()+1)
 white=(a[:,:,:3].min(2)>145)&(np.ptp(a[:,:,:3].astype(int),axis=2)<80)&solid
 white &= np.indices(solid.shape)[0]<top+(bottom-top)*.23
 _,wx=np.where(white);anchor=float(np.median(wx)) if len(wx) else float(np.median(xs))
 return top,bottom,anchor
def metadata(path,ppu=220,pivot=(.5,.21875)):
 meta=Path(str(path)+'.meta')
 if meta.exists():return
 t=(ROOT/'Assets/Game/Resources/RpgRevision/Yuuki/idle_down_00.png.meta').read_text()
 t=re.sub(r'guid: [a-f0-9]+','guid: '+uuid.uuid4().hex,t,count=1)
 t=re.sub(r'spritePixelsToUnits: \d+',f'spritePixelsToUnits: {ppu}',t)
 t=re.sub(r'spritePivot: \{.*?\}',f'spritePivot: {{x: {pivot[0]}, y: {pivot[1]}}}',t)
 t=re.sub(r'textureCompression: \d+','textureCompression: 0',t)
 t=re.sub(r'spriteID: [a-f0-9]+','spriteID: '+uuid.uuid4().hex,t)
 meta.write_text(t,encoding='utf-8')
def main():
 preserved=check_adult()
 for p in [ART/'Sources',ART/'Atlases',OUT/'Frames']:p.mkdir(parents=True,exist_ok=True)
 prompts=json.loads((ART/'prompts.json').read_text())
 cp=STAGE/'child-animation-corrections.json'
 if cp.exists():prompts['corrections']=json.loads(cp.read_text())
 (ART/'prompts.json').write_text(json.dumps(prompts,ensure_ascii=False,indent=2),encoding='utf-8')
 approved=ROOT/'Art/Characters/Childhood/Yuuki/Design-v1/body.png';approved_hash=digest(approved)
 shutil.copy2(ROOT/'Art/Characters/Halos/Yuuki-v2/halo-neutral.png',OUT/'halo-neutral.png')
 metadata(OUT/'halo-neutral.png',pivot=(.5,.5))
 clips=[];report=[];overview=Image.new('RGB',(1140,2520),'#263139');draw=ImageDraw.Draw(overview)
 for di,(direction,srcname) in enumerate(SOURCES.items()):
  local_source=ART/'Sources'/f'{direction}.png'
  if not local_source.exists():shutil.copy2(GEN/srcname,local_source)
  source=Image.open(local_source).convert('RGBA');a=np.array(source)[:,:,3]
  ys=[0,gutter(a,341),gutter(a,683),source.height]
  raw=[[clean(source.crop((c*256,ys[r],(c+1)*256,ys[r+1]))) for c in range(n)] for r,n in enumerate([6,6,3])]
  scale=220/float(np.median([metrics(im)[1]-metrics(im)[0] for im in raw[2]]))
  walk_path=ART/'Sources'/f'walk-{direction}-refined.png'
  if not walk_path.exists():shutil.copy2(GEN/WALKS[direction],walk_path)
  walksource=Image.open(walk_path).convert('RGBA')
  wy=[0,gutter(np.array(walksource)[:,:,3],512),walksource.height]
  walk=[clean(walksource.crop((c*512,wy[r],(c+1)*512,wy[r+1]))) for r in range(2) for c in range(3)]
  # Front contact A -> feet passing -> contact B -> feet passing. Reject repeated contacts.
  if direction=='down':walk=[walk[i] for i in [0,1,3,4]]
  walkscale=224/float(np.median([metrics(im)[1]-metrics(im)[0] for im in walk]))
  raw[0]=walk
  atlas=Image.new('RGBA',(3072,1536))
  for row,(state,images) in enumerate(zip(['walk','run','idle'],raw)):
   frame_scale=walkscale if state=='walk' else scale
   names=[];anchors=[];bounds=[]
   for i,im in enumerate(images):
    top,bottom,anchor=metrics(im);box=im.getchannel('A').getbbox()
    crop=im.crop(box);crop=crop.resize((round(crop.width*frame_scale),round(crop.height*frame_scale)),Image.Resampling.NEAREST)
    bob=[0,-1,-4,0,-1,-4][i] if state=='run' else 0
    x=round(256-(anchor-box[0])*frame_scale);y=400+bob-round((bottom-box[1])*frame_scale)
    assert x>=12 and y>=12 and x+crop.width<=500 and y+crop.height<=500,(direction,state,i)
    frame=Image.new('RGBA',(512,512));frame.alpha_composite(crop,(x,y));name=f'{state}_{direction}_{i:02}'
    frame.save(OUT/'Frames'/f'{name}.png');metadata(OUT/'Frames'/f'{name}.png')
    names.append('Childhood/Yuuki/Frames/'+name)
    anchors.append(dict(x=256,y=round(y+(top-box[1])*frame_scale-24)));bounds.append(frame.getchannel('A').getbbox())
    atlas.alpha_composite(frame,(i*512,row*512))
    visible=frame.crop((96,104,416,424)).resize((190,190),Image.Resampling.NEAREST)
    overview.paste(visible,(i*190,(di*3+row)*210),visible);draw.text((i*190+5,(di*3+row)*210+190),name,fill='#ddd6c7')
   clips.append(dict(name=state+'_'+direction,frames=names,fps=(5 if direction=='down' else 7) if state=='walk' else 10 if state=='run' else 2,loop=True,sequence=[0,1,2,1] if state=='idle' else list(range(len(images))),haloAnchors=anchors))
   report.append(dict(clip=state+'_'+direction,frames=len(images),sourceRow=wy if state=='walk' else [ys[row],ys[row+1]],scale=frame_scale,bounds=bounds))
  atlas.save(ART/'Atlases'/f'{direction}.png')
 overview.save(ART/'contact-sheet.png')
 catalog=dict(character='Yuuki',age=9,status='first-animation-pass-for-motion-review',designApproved=True,bodyFrame=dict(width=512,height=512,pivot=[.5,.21875],pixelsPerUnit=220,feet=[256,400]),halo=dict(resource='Childhood/Yuuki/halo-neutral',width=96,height=28,alphaBaked=True,geometry='Yuuki-v2',tintable=True),weapons=False,wingAnatomy=dict(left='black',right='white'),clips=clips)
 (OUT/'animations.json').write_text(json.dumps(catalog,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 assert digest(approved)==approved_hash
 assert check_adult()==preserved
 (ART/'packing-report.json').write_text(json.dumps(dict(frames=58,clips=12,adultFilesVerified=preserved,approvedBodyUnchanged=True,clipsDetail=report),indent=2),encoding='utf-8')
 sf=ROOT/'Art/Characters/Childhood/validation-state.json';s=json.loads(sf.read_text(encoding='utf-8'))
 s['phase']='Yuuki animation preview ready for motion review; Alice and Tenebris queued'
 s['Yuuki']['animations']='v1 refined: 58 selected frames, walk/run/3-frame breathing idle in four directions; motion review pending'
 s['Yuuki']['animationPreview']='preview/childhood-animation.html'
 sf.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
 print(json.dumps(dict(frames=58,clips=12,adultFilesVerified=preserved,rows={r['clip']:r['sourceRow'] for r in report})))
if __name__=='__main__':
 main()
 # Persist the user's lateral revision when rebuilding from the original sheets.
 if (ART/'motion-four-frame-v3.json').exists():
  from revise_child_yuuki_motion import main as revise_motion
  revise_motion()
  if (ART/'left-from-right-v4.json').exists():
   revise_motion('left-from-right-v4.json')
   if (ART/'leg-copy-v5.json').exists():
    from copy_child_yuuki_run_legs import main as copy_run_legs
    copy_run_legs()
 elif (ART/'lateral-revision.json').exists():
  from revise_child_yuuki_lateral import main as revise_lateral
  revise_lateral()
