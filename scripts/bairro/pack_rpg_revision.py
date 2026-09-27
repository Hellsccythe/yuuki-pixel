"""Technical packing of generated art. No repainting, warping or interpolated poses.
Keep the previous platform atlas untouched, including the approved right run.
"""
import json
from pathlib import Path
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage as ndi

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'Assets/Game/Resources/RpgRevision'
SOURCE = ROOT / 'Art/Yuuki/Rpg-v4'


def clean(im):
    a = np.array(im.convert('RGBA'))
    # Retain opaque islands including halo, then retain their immediate soft edge.
    labels, _ = ndi.label(a[:, :, 3] > 100)
    counts = np.bincount(labels.ravel()); counts[0] = 0
    keep = counts >= 20
    mask = ndi.binary_dilation(keep[labels], iterations=1)
    a[~mask | (a[:, :, 3] < 30)] = 0
    a[a[:, :, 3] == 0] = 0
    return Image.fromarray(a)


def frames(name):
    im = Image.open(SOURCE / (name+'.png')).convert('RGBA')
    return [clean(im.crop((c*im.width//3,r*im.height//2,(c+1)*im.width//3,(r+1)*im.height//2)))
            for r in range(2) for c in range(3)]


def measurements(im):
    a = np.array(im); alpha=a[:,:,3]
    solid = alpha>100
    ys,xs = np.where(solid)
    # White hair is above wings and dress. The staff/halo do not affect body scale.
    white = (a[:,:,:3].min(2)>155) & (a[:,:,:3].max(2)-a[:,:,:3].min(2)<55) & solid
    wy,wx = np.where(white)
    top = int(np.percentile(wy, 1))
    head = white & (np.indices(alpha.shape)[0] < top+85)
    hy,hx=np.where(head)
    anchor = float(np.median(hx))
    return alpha.shape, (xs.min(),ys.min(),xs.max()+1,ys.max()+1), top, anchor


def character():
    clips=[]
    for direction in ['left','right','up','down']:
        walk=frames('walk_'+direction)
        rest=frames('rest_up_v2' if direction=='up' else 'rest_'+direction)
        # This generated candidate faces left in its first cell; never play it facing right.
        if direction=='right': rest[0]=walk[1].copy()
        # Contact A -> pass A -> contact B -> pass B; don't replay repeated contact poses.
        selected = [0,1,3,4] if direction in ('up','down') else [0,1,2,3,4,5]
        for state, sequence, fps, loop in [('walk',[walk[i] for i in selected],8,True),
                                         ('stow',rest[:3],6,False),('idle',rest[3:],2,True)]:
            measure=[measurements(im) for im in sequence]
            # One scale for this clip, never independently stretch body parts or frames.
            scale=240 / float(np.median([box[3]-top for _,box,top,_ in measure]))
            names=[]
            for i,(im,(_,box,top,anchor)) in enumerate(zip(sequence,measure)):
                crop=im.crop(box)
                crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.NEAREST)
                x=round(256-(anchor-box[0])*scale); y=400-crop.height
                assert x>8 and y>8 and x+crop.width<504, (direction,state,i,box)
                frame=Image.new('RGBA',(512,512)); frame.alpha_composite(crop,(x,y))
                pixels=np.array(frame); pixels[pixels[:,:,3]==0]=0; frame=Image.fromarray(pixels)
                name=f'{state}_{direction}_{i:02}'
                frame.save(OUT/'Yuuki'/f'{name}.png'); names.append('RpgRevision/Yuuki/'+name)
            clips.append(dict(name=state+'_'+direction,frames=names,fps=fps,loop=loop))
    (OUT/'yuuki.json').write_text(json.dumps(dict(clips=clips),indent=2),encoding='utf-8')
    # Large, labelled inspection sheet; the actual game uses individual 512px cells.
    contact=Image.new('RGB',(12*180,4*210),'#343d36'); d=ImageDraw.Draw(contact)
    for row,direction in enumerate(['left','right','up','down']):
        names=[f for c in clips if c['name'].endswith('_'+direction) for f in c['frames']]
        for col,name in enumerate(names):
            im=Image.open(ROOT/'Assets/Game/Resources'/f'{name}.png')
            im.thumbnail((180,180),Image.Resampling.NEAREST)
            contact.paste(im,(col*180,row*210),im)
            d.text((col*180+4,row*210+184),name.split('/')[-1],fill='white')
    contact.save(ROOT/'docs/bairro/yuuki-rpg-v4.jpg',quality=94)


def environment():
    source=ROOT/'Art/World/Sources/Home-v3'
    im=Image.open(source/'props.png').convert('RGBA')
    specs=[('tapete',(0,0,512,565),3),('fogao',(512,0,1024,565),1.35),('livros',(1024,0,1536,565),.65),
           ('livro-aberto',(0,565,512,1024),.75),('meia-parede',(512,565,1024,1024),3),
           ('horta',(1024,565,1536,1024),2.2)]
    items=[]
    for name,box,width in specs:
        crop=clean(im.crop(box)); crop=crop.crop(crop.getchannel('A').getbbox())
        packed=Image.new('RGBA',(crop.width+16,crop.height+16)); packed.alpha_composite(crop,(8,8))
        packed.save(OUT/'Home'/f'{name}.png')
        items.append(dict(id=name,width=width,ppu=crop.width/width,pivotY=8/packed.height))
    room=clean(Image.open(source/'room.png')); room=room.crop(room.getchannel('A').getbbox())
    room.save(OUT/'Home/room.png')
    items.append(dict(id='room',width=6.4,ppu=room.width/6.4,pivotY=0))
    # The doors are exact pixel crops of each original facade, animated by Unity transforms.
    for name,box in [('casa-yuuki',(210,242,273,340)),('casa-tenebris',(196,380,249,468))]:
        src=Image.open(ROOT/f'Assets/Game/Bairro/Sprites/Buildings/{name}.png')
        src.crop(box).save(OUT/'Home'/f'porta-{name}.png')
        items.append(dict(id='porta-'+name,width=(box[2]-box[0])/60,ppu=60,pivotY=0))
    (OUT/'home.json').write_text(json.dumps(dict(assets=items),indent=2),encoding='utf-8')


if __name__=='__main__':
    for folder in ['Yuuki','Home']: (OUT/folder).mkdir(parents=True,exist_ok=True)
    character(); environment()
    print('Packed 44 movement/rest frames and 9 interior/door pieces; old atlas preserved.')
