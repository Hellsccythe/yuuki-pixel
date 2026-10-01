"""Crop generated replacements, retaining their alpha and original art (no painting)."""
import json
from pathlib import Path
import numpy as np
from PIL import Image
from scipy import ndimage as ndi

ROOT=Path(__file__).resolve().parents[2]
SRC=ROOT/'Art/World/Sources/Neighborhood-v6'
OUT=ROOT/'Assets/Game/Resources/NeighborhoodV6'
items=[]

def clean(im):
    a=np.array(im.convert('RGBA'))
    labels,_=ndi.label(a[:,:,3]>110)
    sizes=np.bincount(labels.ravel()); sizes[0]=0
    keep=ndi.binary_dilation(sizes[labels]>=28,iterations=1)
    a[~keep | (a[:,:,3]<35)]=0
    a[a[:,:,3]==0]=0
    return Image.fromarray(a)

def save(sid,source,box,width,door=None,pivot=None):
    cell=clean(source.crop(box)); bb=cell.getchannel('A').getbbox()
    im=cell.crop(bb); result=Image.new('RGBA',(im.width+16,im.height+16)); result.alpha_composite(im,(8,8))
    path=OUT/(sid+'.png'); result.save(path)
    item=dict(id=sid,path=path.relative_to(ROOT).as_posix(),ppu=im.width/width,
              pivotX=.5,pivotY=8/result.height,w=result.width,h=result.height)
    if pivot is not None: item['pivotY']=pivot
    if door:
        x0,y0,x1,y1=door
        item['door']=[x0-box[0]-bb[0]+8,y0-box[1]-bb[1]+8,x1-box[0]-bb[0]+8,y1-box[1]-bb[1]+8]
    items.append(item)

def grid(source,cols,rows,col,row):
    return (col*source.width//cols,row*source.height//rows,(col+1)*source.width//cols,(row+1)*source.height//rows)

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    source=Image.open(SRC/'shacks.png')
    cuts=[(0,0,510,512),(511,0,968,512),(969,0,1536,512),(0,512,510,1024),(510,512,968,1024),(969,512,1536,1024)]
    doors=[(126,282,204,430),(612,276,696,427),(1182,305,1275,432),(117,772,204,924),(605,794,678,919),(1170,780,1255,927)]
    for i,(box,door,width) in enumerate(zip(cuts,doors,[4.4,3.6,5.0,4.0,3.8,4.6])):
        save('barraco-'+str(i),source,box,width,door)
    source=Image.open(SRC/'cottages.png')
    for i,(door,width) in enumerate(zip([(151,575,232,754),(713,582,798,755),(1290,585,1364,755)],[4.5,4.5,4.3])):
        save('casa-simples-'+str(i),source,grid(source,3,1,i,0),width,door)
    source=Image.open(SRC/'props.png')
    specs=[('ponte-v6',2.0),('galinheiro',3.6),('barris-agua',1.25),('carroca-quebrada',2.6),('lenha',1.9),
           ('varal-v6',3.6),('lixo',1.7),('poca-v6',1.4),('buraco-v6',1.4)]
    # The bridge extends slightly below a mathematical third of the generated sheet.
    # The empty band at y=468 separates it cleanly from the cart underneath.
    rows=[0,468,853,source.height]
    for i,(sid,width) in enumerate(specs):
        col,row=i%3,i//3
        save(sid,source,(col*source.width//3,rows[row],(col+1)*source.width//3,rows[row+1]),width)
    source=Image.open(SRC/'interiors.png')
    for i,(sid,width) in enumerate([('room-familia',6),('room-barraco',6),('room-oficina',6),('escada-subir',1.25),('escada-descer',1.25),('divisoria',.26)]):
        save(sid,source,grid(source,3,2,i%3,i//3),width,pivot=0 if i<3 else None)
    source=Image.open(SRC/'chickens.png')
    for row,color in enumerate(['branca','ruiva','carijo']):
        cells=[clean(source.crop(grid(source,4,3,col,row))) for col in range(4)]
        boxes=[im.getchannel('A').getbbox() for im in cells]
        scale=94/max(bb[2]-bb[0] for bb in boxes)
        for col,(cell,bb) in enumerate(zip(cells,boxes)):
            crop=cell.crop(bb); crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.NEAREST)
            packed=Image.new('RGBA',(128,128)); packed.alpha_composite(crop,((128-crop.width)//2,112-crop.height))
            sid=f'galinha-{color}-{col}';path=OUT/(sid+'.png');packed.save(path)
            items.append(dict(id=sid,path=path.relative_to(ROOT).as_posix(),ppu=155,pivotX=.5,pivotY=16/128,w=128,h=128))
    (OUT/'catalog.json').write_text(json.dumps(dict(sprites=items),indent=2),encoding='utf-8')
    print(f'Packed {len(items)} sprites with doors, pivots and matching scale.')

if __name__=='__main__': main()
