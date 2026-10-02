from pathlib import Path
from PIL import Image,ImageOps,ImageDraw
import numpy as np,json,shutil,importlib.util
import sys
sys.path.insert(0,str(Path('D:/yuuki-pixel/scripts')))
import kled_extract
from pack_kled_animations import preservation
R=Path('D:/yuuki-pixel');S=Path(__file__).parent
A=R/'Art/Story/SchoolMorning-v1';O=R/'Assets/Game/Resources/SchoolMorning'
G=Path('C:/Users/Hellsccythe/.codex/generated_images/01a0de91-4e4f-79f2-9ff8-3bfa5d375ffa')
spec=importlib.util.spec_from_file_location('sara',R/'scripts/pack_sara_animations.py');h=importlib.util.module_from_spec(spec);spec.loader.exec_module(h)
h.alice.clean=kled_extract.clean
def extract(path,rows,cols):
    try:return h.extract(path,rows,cols)
    except AssertionError as err:
        if 'gutter' not in str(err):raise
        a=np.array(Image.open(path).convert('RGBA'));labels,stats=kled_extract.components(a[:,:,3]>100)
        large=sorted(((k,v) for k,v in stats.items() if v['count']>10000),key=lambda kv:(kv[1]['box'][1]+kv[1]['box'][3])/2)
        assert len(large)==rows*cols,[(v['count'],v['box']) for k,v in large]
        groups=[]
        for r in range(rows):
            row=[]
            for k,v in sorted(large[r*cols:(r+1)*cols],key=lambda kv:kv[1]['box'][0]):
                mask=np.array(Image.fromarray((labels==k).astype('uint8')*255).filter(kled_extract.ImageFilter.MaxFilter(3)))>0
                b=a.copy();b[~mask | (b[:,:,3]<28)]=0;b[b[:,:,3]==0]=0
                im=Image.fromarray(b);box=im.getchannel('A').getbbox()
                assert min(box[:2])>0 and box[2]<im.width and box[3]<im.height
                row.append(ImageOps.expand(im.crop(box),border=4,fill=(0,0,0,0)))
            groups.append(row)
        return groups,{'method':'complete connected silhouettes; no straight cuts through neighbors'}
def main():
    preserved=preservation()
    for p in (A/'Sources',O/'Actions',O/'Props',O/'Residents',O/'Ground'):p.mkdir(parents=True,exist_ok=True)
    cfg=json.loads((S/'intro-image-prompts.json').read_text(encoding='utf-8'));cfg['sources']=json.loads((S/'intro-selected-sources.json').read_text(encoding='utf-8'))
    h.save(A/'production-prompts.json',cfg)
    for key,name in cfg['sources'].items():
        target=A/'Sources'/(key+'.png')
        if not target.exists():shutil.copy2(G/name,target)
    clips=[];report=[]
    for action in ('exhaust','grasp','pickup','kick','tenebris_grasp'):
        groups,cuts=extract(A/'Sources'/(action+'.png'),1,4);poses=groups[0]
        # The first pose is upright. Scale the whole row from it: crouching never stretches legs.
        t,b,c=h.metric(poses[0]);scale=220/(b-t)
        paths=[];anchors=[]
        for i,p in enumerate(poses):
            top,bottom,cx=h.metric(p);box=p.getchannel('A').getbbox();im=p.crop(box)
            im=im.resize((round(im.width*scale),round(im.height*scale)),Image.Resampling.NEAREST)
            x=round(256-(cx-box[0])*scale);y=400-round((bottom-box[1])*scale)
            assert x>=12 and y>=12 and x+im.width<=500 and y+im.height<=500
            frame=Image.new('RGBA',(512,512));frame.alpha_composite(im,(x,y))
            name=f'{action}_{i:02}';pout=O/'Actions'/(name+'.png');frame.save(pout);h.meta(pout)
            paths.append('SchoolMorning/Actions/'+name);anchors.append({'x':256,'y':round(y+(top-box[1])*scale-24)})
        clips.append({'name':action,'frames':paths,'haloAnchors':anchors,'fps':4 if action=='exhaust' else 4,'loop':action=='exhaust','sequence':[1,2,3,2] if action=='exhaust' else [0,1,2,3]})
        report.append({'action':action,'constantScale':scale,'sourceCuts':cuts,'registration':'feet fixed; first upright frame controls row scale'})
    props,_=extract(A/'Sources/props.png',2,2)
    residents,_=extract(A/'Sources/residents.png',2,3)
    defs=[]
    for folder,groups,names in [('Props',props,['gate','backpack','ball','flower']),('Residents',residents,['lady','boy-blue','boy-red','dog','teacher-man','teacher-woman'])]:
        for pose,name in zip([p for row in groups for p in row],names):
            box=pose.getchannel('A').getbbox();im=ImageOps.expand(pose.crop(box),border=4,fill=(0,0,0,0))
            im.save(O/folder/(name+'.png'));h.meta(O/folder/(name+'.png'))
            defs.append({'id':name,'resource':'SchoolMorning/'+folder+'/'+name,'width':im.width,'height':im.height})
    school=kled_extract.clean(Image.open(A/'Sources/school.png'));school=ImageOps.expand(school.crop(school.getchannel('A').getbbox()),border=4,fill=(0,0,0,0));school.save(O/'school.png');h.meta(O/'school.png')
    atlas=Image.open(R/'Art/World/Sources/terrain.png').convert('RGBA');half=atlas.width//2
    for i,name in enumerate(('grass','dirt','cobble')):
        q=atlas.crop(((i%2)*half+6,(i//2)*half+6,(i%2+1)*half-6,(i//2+1)*half-6));q=q.resize((256,256),Image.Resampling.NEAREST);q.save(O/'Ground'/(name+'.png'));h.meta(O/'Ground'/(name+'.png'))
    h.save(O/'actions.json',{'clips':clips,'frameSize':[512,512],'feet':[256,400],'pixelsPerUnit':220,'bodyScale':'220px standing height; one uniform scale per source row','halo':'reuse the protagonist separate recolorable halo','assets':defs})
    h.save(A/'packing-report.json',{'actions':report,'frames':20,'maximumDrawingsPerAnimation':4,'approvedFilesPreserved':preserved,'processing':'alpha cleanup, transparent gutters, crop, uniform nearest-neighbor scaling; no painting or limb deformation'})
    assert preservation()==preserved
    overview=Image.new('RGB',(1024,5*250),'#28322b');draw=ImageDraw.Draw(overview)
    for row,c in enumerate(clips):
        for col,path in enumerate(c['frames']):
            im=Image.open(R/'Assets/Game/Resources'/(path+'.png'));thumb=im.crop((64,128,448,416)).resize((240,180),Image.Resampling.NEAREST);overview.paste(thumb,(col*256,row*250+25),thumb);draw.text((col*256+10,row*250+212),c['name']+' '+str(col+1),fill='#ede2cb')
    overview.save(A/'actions-contact-sheet.png')
    shutil.copy2(R/'Art/Characters/Parents/sara-animation-approved-preservation.json',A/'sara-preservation-reference.json')
    storySource=Path('C:/Users/Hellsccythe/.codex/attachments/0d508082-153c-4af7-a6bf-5da98fbd412b/Texto colado.txt')
    if storySource.exists():shutil.copy2(storySource,A/'scenario-source.txt')
    print(json.dumps({'actions':5,'actionFrames':20,'assets':10,'school':str(O/'school.png'),'preserved':preserved}))
if __name__=='__main__':main()
