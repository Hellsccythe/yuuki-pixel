"""Pack Alice's generated drawings; lateral left is an exact pivot-aware mirror."""
from pathlib import Path
import json, shutil, sys, hashlib, re, uuid
from collections import deque
import numpy as np
from PIL import Image, ImageDraw, ImageOps, ImageFilter

ROOT=Path(__file__).resolve().parents[1]
ART=ROOT/'Art/Characters/Childhood/Alice/Animations-v1'
DESIGN=ROOT/'Art/Characters/Childhood/Alice/Design-v2'
HALO=ROOT/'Art/Characters/Halos/Alice-v1'
OUT=ROOT/'Assets/Game/Resources/Childhood/Alice'
GEN=Path(r'C:\Users\Hellsccythe\.codex\generated_images\01a0de91-4e4f-79f2-9ff8-3bfa5d375ffa')

class yuuki:
 @staticmethod
 def digest(path):return hashlib.sha256(path.read_bytes()).hexdigest()
 @staticmethod
 def check_adult():
  m=json.loads((ROOT/'Art/Characters/Childhood/adult-preservation.json').read_text(encoding='utf-8-sig'))
  bad=[f['path'] for f in m['files'] if yuuki.digest(ROOT/f['path'])!=f['sha256']]
  assert not bad,bad
  return len(m['files'])
 @staticmethod
 def metadata(path,pivot=(.5,.21875)):
  meta=Path(str(path)+'.meta')
  if meta.exists():return
  t=(ROOT/'Assets/Game/Resources/RpgRevision/Yuuki/idle_down_00.png.meta').read_text()
  t=re.sub(r'guid: [a-f0-9]+','guid: '+uuid.uuid4().hex,t,count=1)
  t=re.sub(r'spritePixelsToUnits: \d+','spritePixelsToUnits: 220',t)
  t=re.sub(r'spritePivot: \{.*?\}',f'spritePivot: {{x: {pivot[0]}, y: {pivot[1]}}}',t)
  t=re.sub(r'textureCompression: \d+','textureCompression: 0',t)
  t=re.sub(r'spriteID: [a-f0-9]+','spriteID: '+uuid.uuid4().hex,t)
  meta.write_text(t,encoding='utf-8')

def save(path,value):
 path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')

def protected():
 manifest=json.loads((ROOT/'Art/Characters/Childhood/yuuki-child-approved-preservation.json').read_text(encoding='utf-8'))
 bad=[f['path'] for f in manifest['files'] if yuuki.digest(ROOT/f['path'])!=f['sha256']]
 assert not bad,bad
 return len(manifest['files'])

def clean(im):
 a=np.array(im.convert('RGBA'))
 solid=a[:,:,3]>100
 seen=np.zeros(solid.shape,dtype=bool);kept=np.zeros(solid.shape,dtype=bool)
 height,width=solid.shape
 for sy,sx in zip(*np.where(solid)):
  if seen[sy,sx]:continue
  seen[sy,sx]=True;queue=deque([(int(sy),int(sx))]);pixels=[]
  while queue:
   y,x=queue.popleft();pixels.append((y,x))
   for yy in range(max(0,y-1),min(height,y+2)):
    for xx in range(max(0,x-1),min(width,x+2)):
     if solid[yy,xx] and not seen[yy,xx]:
      seen[yy,xx]=True;queue.append((yy,xx))
  if len(pixels)>40:
   ys,xs=zip(*pixels);kept[ys,xs]=True
 kept=np.array(Image.fromarray(kept.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
 a[~kept | (a[:,:,3]<28)]=0
 a[a[:,:,3]==0]=0
 return Image.fromarray(a)

def metric(im):
 a=np.array(im);ys,xs=np.where(a[:,:,3]>110)
 top,bottom=int(ys.min()),int(ys.max()+1)
 y,x=np.indices(a.shape[:2])
 # Median of the dark crown keeps registration stable even in back view.
 crown=(a[:,:,3]>110)&(a[:,:,:3].max(2)<135)&(y>=top)&(y<top+(bottom-top)*.22)
 _,hx=np.where(crown)
 return top,bottom,float(np.median(hx))

def cut_line(alpha,expected,axis=0):
 if axis:alpha=alpha.T
 radius=max(40,round(alpha.shape[0]/12))
 start=max(0,expected-radius);end=min(alpha.shape[0],expected+radius)
 scores=(alpha[start:end]>110).sum(1)
 zero=np.where(scores==0)[0]
 assert len(zero),'No transparent gutter at expected cell boundary'
 # Prefer the zero run nearest the intended grid division.
 runs=np.split(zero,np.where(np.diff(zero)>1)[0]+1)
 run=min(runs,key=lambda r:abs(start+float(np.median(r))-expected))
 return start+round(float(np.median(run)))

def extract(path,rows=3):
 im=Image.open(path).convert('RGBA');a=np.array(im)[:,:,3]
 yc=[0]+[cut_line(a,round(im.height*r/rows)) for r in range(1,rows)]+[im.height]
 groups=[];xc=[]
 for r in range(rows):
  row=im.crop((0,yc[r],im.width,yc[r+1]));ra=np.array(row)[:,:,3]
  cuts=[0]+[cut_line(ra,round(im.width*c/4),axis=1) for c in range(1,4)]+[im.width]
  xc.append(cuts)
  count=3 if rows==3 and r==2 else 4
  poses=[]
  for c in range(count):
   pose=clean(row.crop((cuts[c],0,cuts[c+1],row.height)))
   pa=np.array(pose)[:,:,3]
   assert not (pa[0].any() or pa[-1].any() or pa[:,0].any() or pa[:,-1].any()),(path,r,c,'clipped cell')
   poses.append(pose)
  groups.append(poses)
 return groups,{'rows':yc,'columns':xc}

def normalize(pose,scale,bob=0,feet_fixed=False):
 top,bottom,hx=metric(pose);box=pose.getchannel('A').getbbox()
 crop=pose.crop(box)
 crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.NEAREST)
 x=round(256-(hx-box[0])*scale)
 y=400-round((bottom-box[1])*scale) if feet_fixed else 180+bob-round((top-box[1])*scale)
 assert x>=12 and y>=12 and x+crop.width<=500 and y+crop.height<=500
 frame=Image.new('RGBA',(512,512));frame.alpha_composite(crop,(x,y))
 return frame,dict(x=256,y=round(y+(top-box[1])*scale-24))

def main():
 nprotected=protected();adult=yuuki.check_adult()
 original=ROOT/'Art/Characters/Design-v1/alice.png'
 original_hash=yuuki.digest(original)
 for d in (ART/'Sources',ART/'Atlases',DESIGN,HALO,OUT/'Frames'):d.mkdir(parents=True,exist_ok=True)
 cfg=json.loads((ART/'production-prompts.json').read_text(encoding='utf-8'))
 for key,name in cfg['sources'].items():
  dest=(DESIGN/'body-source.png' if key=='body' else HALO/'halo-source.png' if key=='halo' else ART/'Sources'/(key+'.png'))
  if not dest.exists():shutil.copy2(GEN/name,dest)
 body=clean(Image.open(DESIGN/'body-source.png'))
 top,bottom,_=metric(body)
 body,body_halo_anchor=normalize(body,220/(bottom-top),feet_fixed=True)
 body.save(DESIGN/'body.png')
 hi=Image.open(HALO/'halo-source.png').convert('RGBA')
 ha=np.array(hi);box=Image.fromarray((ha[:,:,3]>8).astype('uint8')*255).getbbox()
 hi=hi.crop(box);hi=hi.resize((96,round(hi.height*96/hi.width)),Image.Resampling.LANCZOS)
 h=np.array(hi);luma=np.array(hi.convert('L'))
 h[:,:,:3]=luma[:,:,None]
 h[:,:,3]=np.minimum(156,np.rint(h[:,:,3].astype(float)*.65)).astype('uint8')
 h[h[:,:,3]==0]=0
 halo=Image.fromarray(h)
 halo.save(HALO/'halo-neutral.png');halo.save(OUT/'halo-neutral.png')
 yuuki.metadata(OUT/'halo-neutral.png',pivot=(.5,.5))
 preview=body.copy();color=np.array(halo);color[:,:,:3]=np.rint(color[:,:,:3]*np.array([.412,.714,1])).astype('uint8')
 preview.alpha_composite(Image.fromarray(color),(body_halo_anchor['x']-48,body_halo_anchor['y']-halo.height//2))
 preview.save(DESIGN/'preview.png')
 save(DESIGN/'design.json',dict(character='Alice',age=9,appearance='approved Design-v1; two matching hair bows added at user request',
  body='body.png',halo='../../../Halos/Alice-v1/halo-neutral.png',haloStatus='proposal for user review',
  haloAnchor=body_halo_anchor,weapons=False,wingAnatomy={'left':'white','right':'white'},symmetricHairBows=True,
  frame={'width':512,'height':512,'feet':[256,400],'pixelsPerUnit':220}))
 clips=[];details=[]
 for direction in ('down','up','right'):
  groups,cuts=extract(ART/'Sources'/(direction+'.png'))
  scale=220/float(np.median([metric(p)[1]-metric(p)[0] for p in groups[2]]))
  if direction=='down' and 'down-walk' in cfg['sources']:
   groups[0],wc=extract(ART/'Sources/down-walk.png',rows=1)
   groups[0]=groups[0][0]
  else:wc=None
  for state,poses in zip(('walk','run','idle'),groups):
   # Each row uses one constant scale: no per-frame stretching.
   row_scale=220/float(np.median([metric(p)[1]-metric(p)[0] for p in poses])) if state=='walk' and wc else scale
   resources=[];anchors=[];bounds=[]
   for i,pose in enumerate(poses):
    if direction=='down' and state=='walk' and i>=2 and cfg.get('frontWalkReflectedPair'):
     source_frame=Image.open(OUT/'Frames'/f'walk_down_v1_{i-2:02}.png').convert('RGBA')
     frame=Image.fromarray(np.roll(np.array(ImageOps.mirror(source_frame)),1,axis=1))
     anchor={'x':512-anchors[i-2]['x'],'y':anchors[i-2]['y']}
    else:
     frame,anchor=normalize(pose,row_scale,(-1 if i%2 else 0) if state!='idle' else 0,feet_fixed=state=='idle')
    name=f'{state}_{direction}_v1_{i:02}'
    path=OUT/'Frames'/(name+'.png');frame.save(path);yuuki.metadata(path)
    resources.append('Childhood/Alice/Frames/'+name);anchors.append(anchor);bounds.append(frame.getchannel('A').getbbox())
   clips.append(dict(name=state+'_'+direction,frames=resources,haloAnchors=anchors,
    fps=6 if state=='walk' else 8 if state=='run' else 2,loop=True,
    sequence=[0,1,2,1] if state=='idle' else [0,1,2,3]))
   details.append(dict(clip=state+'_'+direction,frames=len(poses),scale=row_scale,cuts=wc if wc and state=='walk' else cuts,
    bounds=bounds,headTopRangePixels=max(b[1] for b in bounds)-min(b[1] for b in bounds),
    footBaselineRangePixels=max(b[3] for b in bounds)-min(b[3] for b in bounds)))
 clipmap={c['name']:c for c in clips}
 for state in ('walk','run','idle'):
  src=clipmap[state+'_right']
  frames=[]
  for i,f in enumerate(src['frames']):
   right=Image.open(ROOT/'Assets/Game/Resources'/(f+'.png')).convert('RGBA')
   # Reflection around frame pivot x=256, with a 1px integer compensation.
   arr=np.roll(np.array(ImageOps.mirror(right)),1,axis=1)
   assert not arr[:,0,3].any()
   im=Image.fromarray(arr);name=f'{state}_left_v1_{i:02}';path=OUT/'Frames'/(name+'.png')
   im.save(path);yuuki.metadata(path)
   assert np.array_equal(np.array(Image.open(path)),arr)
   frames.append('Childhood/Alice/Frames/'+name)
  clips.append(dict(name=state+'_left',frames=frames,haloAnchors=[{'x':512-a['x'],'y':a['y']} for a in src['haloAnchors']],
   fps=src['fps'],sequence=src['sequence'][:],loop=True,mirroredFrom=state+'_right'))
 ordered=[next(c for c in clips if c['name']==st+'_'+d) for d in ('down','up','left','right') for st in ('walk','run','idle')]
 catalog=dict(character='Alice',age=9,status='first-animation-pass-for-motion-review',designApproved=True,
  symmetricHairBows=True,weapons=False,bodyFrame={'width':512,'height':512,'pivot':[.5,.21875],'pixelsPerUnit':220,'feet':[256,400]},
  halo={'resource':'Childhood/Alice/halo-neutral','width':96,'height':halo.height,'alphaBaked':True,'geometry':'Alice-v1','tintable':True,'status':'proposal'},
  wingAnatomy={'left':'white','right':'white'},playbackRevision='alice-v1',clips=ordered)
 save(OUT/'animations.json',catalog)
 overview=Image.new('RGB',(760,2520),'#263139');draw=ImageDraw.Draw(overview);layout={}
 for di,direction in enumerate(('down','up','left','right')):
  atlas=Image.new('RGBA',(2048,1536));layout[direction]={}
  for row,state in enumerate(('walk','run','idle')):
   clip=next(c for c in ordered if c['name']==state+'_'+direction)
   layout[direction][state]=clip['frames']
   for col,f in enumerate(clip['frames']):
    im=Image.open(ROOT/'Assets/Game/Resources'/(f+'.png')).convert('RGBA')
    atlas.alpha_composite(im,(col*512,row*512))
    thumb=im.crop((96,104,416,424)).resize((190,190),Image.Resampling.NEAREST)
    yy=(di*3+row)*210;overview.paste(thumb,(col*190,yy),thumb)
    draw.text((col*190+5,yy+190),f.rsplit('/',1)[-1],fill='#ddd6c7')
  atlas.save(ART/'Atlases'/(direction+'.png'))
 overview.save(ART/'contact-sheet.png')
 assert protected()==nprotected;assert yuuki.check_adult()==adult;assert yuuki.digest(original)==original_hash
 assert len(ordered)==12 and sum(len(c['frames']) for c in ordered)==44
 save(ART/'packing-report.json',dict(character='Alice',drawings=44,generatedDrawings=31,exactMirroredDrawings=13,
  yuukiChildFilesVerified=nprotected,yuukiAdultFilesVerified=adult,originalAliceUnchanged=True,
  exactLateralMirror=True,frontWalkReflectedPair=bool(cfg.get('frontWalkReflectedPair')),haloMaximumAlpha=int(h[:,:,3].max()),atlasLayout=layout,clipsDetail=details))
 sp=ROOT/'Art/Characters/Childhood/validation-state.json';state=json.loads(sp.read_text(encoding='utf-8'))
 state['phase']='Yuuki approved and archived; Alice animations and halo awaiting visual review'
 state['Alice'].update(appearance='Design-v1 retained; two matching hair bows requested by user 2026-09-30',
  halo='Alice-v1: separate translucent double ring with four lozenges, neutral recolorable; proposed',
  animations='44 drawings: walk/run 4 frames, breathing idle 3 frames in 4 directions; left exactly mirrors right; awaiting user motion review',
  animationPreview='preview/alice-animation.html')
 save(sp,state)
 print(json.dumps(dict(drawings=44,clips=12,exactMirroredDrawings=13,yuukiFilesVerified=nprotected,adultFilesVerified=adult,detail=details)))

if __name__=='__main__':main()
