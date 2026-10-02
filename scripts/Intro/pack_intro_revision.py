from pathlib import Path
from PIL import Image, ImageOps, ImageDraw
import numpy as np, json, shutil
from pack_intro_assets import extract, h, R, O, A, G
from pack_kled_animations import preservation
import kled_extract

S=Path(__file__).parent
SOURCES={
 'boundary':'exec-8a276e21-48cf-4032-8962-d32f0392a327.png',
 'lady':'exec-1efe415b-6304-4c5f-9cf0-3111782fedf4.png',
 'boy-blue':'exec-6f54b8e2-b695-402f-9edd-fb8e1fce6727.png',
 'boy-red':'exec-7986b1da-100d-4b1f-9b82-07bc4e3ebbad.png',
 'dog':'exec-d4e10521-3122-46e0-af0d-bc24940f6e71.png',
 'teacher-man':'exec-164a6f2f-551f-4301-b4d6-bad2782a286f.png',
 'teacher-woman':'exec-4147a14f-a0c7-4f06-a73e-7afde7f869eb.png',
 'strap_grip':'exec-440751ff-dfbb-4ecd-8042-6643ca277503.png',
 'straps':'exec-a4edf09a-a64c-4c4c-b6a0-00b954181f0a.png',
 'side-fence':'exec-25187204-b4ae-4682-ab43-d147e4b315fb.png'}

def main():
 before=preservation(); source=A/'Revision2/Sources'; source.mkdir(parents=True,exist_ok=True)
 for k,f in SOURCES.items():
  target=source/(k+'.png')
  if not target.exists():shutil.copy2(G/f,target)
 shutil.copy2(S/'production-prompts-revision3.json',A/'Revision2/production-prompts.json')
 clips=[]; report=[]
 for name in ('lady','boy-blue','boy-red','dog','teacher-man','teacher-woman','strap_grip'):
  grid,cuts=extract(source/(name+'.png'),1 if name=='strap_grip' else 2,4 if name=='strap_grip' else 2);poses=[p for row in grid for p in row]
  top,bottom,cx=h.metric(poses[0]); height=130 if name=='dog' else 248 if name in ('lady','teacher-man','teacher-woman') else 220
  scale=height/(bottom-top); folder='Actions' if name=='strap_grip' else 'NpcAnimations';(O/folder).mkdir(exist_ok=True)
  paths=[]; anchors=[]
  for i,p in enumerate(poses):
   t,b,c=h.metric(p); box=p.getchannel('A').getbbox(); im=p.crop(box)
   im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
   x=round(256-(c-box[0])*scale); y=400-round((b-box[1])*scale)
   assert min(x,y)>=10 and x+im.width<=502 and y+im.height<=502,(name,i,x,y,im.size)
   frame=Image.new('RGBA',(512,512));frame.alpha_composite(im,(x,y))
   path=O/folder/(f'{name}_{i:02}.png');frame.save(path);h.meta(path)
   paths.append('SchoolMorning/'+folder+'/'+path.stem);anchors.append({'x':256,'y':round(y+(t-box[1])*scale-24)})
  clip={'name':name,'frames':paths,'haloAnchors':anchors,'fps':5 if name=='dog' else 3 if name=='strap_grip' else 4,'sequence':[0,1,2,3],'loop':True}
  if name=='strap_grip':
   action_path=O/'actions.json'; actions=json.loads(action_path.read_text()); actions['clips']=[c for c in actions['clips'] if c['name']!=name]+[clip];h.save(action_path,actions)
  else:clips.append(clip)
  report.append({'name':name,'sourceCuts':cuts,'uniformRowScale':scale,'standingHeight':height})
 h.save(O/'npcs.json',{'clips':clips,'halo':{'resource':'Childhood/Tenebris/halo-neutral','opacity':.7,'alphaBaked':True},'frameSize':[512,512]})
 boundary,cuts=extract(source/'boundary.png',2,2)
 for name,p in zip(('fence-front','fence-oblique','fence-corner-left','fence-corner-right'),[p for row in boundary for p in row]):
  p=ImageOps.expand(p.crop(p.getchannel('A').getbbox()),border=4,fill=(0,0,0,0));path=O/'Props'/(name+'.png');p.save(path);h.meta(path)
 for name in ('straps','side-fence'):
  p=kled_extract.clean(Image.open(source/(name+'.png')));p=ImageOps.expand(p.crop(p.getchannel('A').getbbox()),border=4,fill=(0,0,0,0));path=O/'Props'/(name+'.png');p.save(path);h.meta(path)
 sheet=Image.new('RGB',(1000,7*250),'#35443d');d=ImageDraw.Draw(sheet)
 for row,name in enumerate(('lady','boy-blue','boy-red','dog','teacher-man','teacher-woman','strap_grip')):
  folder='Actions' if name=='strap_grip' else 'NpcAnimations'
  for i in range(4):
   im=Image.open(O/folder/(f'{name}_{i:02}.png'));im=im.crop((96,96,416,416));im.thumbnail((225,225),Image.Resampling.NEAREST);sheet.paste(im,(i*250+12,row*250+5),im);d.text((i*250+15,row*250+232),name+' '+str(i+1),fill='#faf1d9')
 sheet.save(A/'Revision2/contact-sheet.png')
 h.save(A/'Revision2/packing-report.json',{'rows':report,'npcFrames':24,'gestureFrames':4,'maximumDrawingsPerAnimation':4,'preserved':before,'processing':'Alpha cleanup, crop, common nearest-neighbor scale per row, feet registration. No limb deformation or repainting.'})
 assert preservation()==before
 print(json.dumps({'npcFrames':24,'gestureFrames':4,'preserved':before,'contactSheet':str(A/'Revision2/contact-sheet.png')}))

if __name__=='__main__':main()
