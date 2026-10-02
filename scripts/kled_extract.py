"""Mechanical alpha segmentation. No drawing, interpolation, or anatomy changes."""
from PIL import Image, ImageOps, ImageFilter
import numpy as np

def components(mask):
    # Scanline union-find gives the same 8-neighbor connectivity as pixel BFS.
    parents=[]; runs=[]; prev=[]
    def find(i):
        while parents[i]!=i:
            parents[i]=parents[parents[i]]; i=parents[i]
        return i
    for y,row in enumerate(mask):
        edges=np.flatnonzero(np.diff(np.pad(row.astype('int8'),(1,1))))
        current=[]; p=0
        for x0,x1 in zip(edges[::2],edges[1::2]):
            x0=int(x0);x1=int(x1); label=len(parents);parents.append(label)
            while p<len(prev) and prev[p][1]<x0:p+=1
            j=p
            while j<len(prev) and prev[j][0]<=x1:
                a,b=find(label),find(prev[j][2]);parents[b]=a;j+=1
            current.append((x0,x1,label));runs.append((y,x0,x1,label))
        prev=current
    labels=np.zeros(mask.shape,dtype='int32');stats={}
    for y,x0,x1,label in runs:
        root=find(label)+1;labels[y,x0:x1]=root
        s=stats.setdefault(root,{'count':0,'box':[x0,y,x1,y+1]})
        s['count']+=x1-x0;s['box']=[min(s['box'][0],x0),min(s['box'][1],y),max(s['box'][2],x1),max(s['box'][3],y+1)]
    return labels,stats

def clean(im):
    a=np.array(im.convert('RGBA'));labels,stats=components(a[:,:,3]>100)
    keep=np.isin(labels,[k for k,s in stats.items() if s['count']>40])
    keep=np.array(Image.fromarray(keep.astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
    a[~keep | (a[:,:,3]<28)]=0;a[a[:,:,3]==0]=0
    return Image.fromarray(a)

def lateral_extract(path):
    im=Image.open(path).convert('RGBA');a=np.array(im)
    labels,stats=components(a[:,:,3]>100)
    large=sorted(((k,s) for k,s in stats.items() if s['count']>20000),key=lambda x:x[1]['box'][1])
    assert len(large)==8,[(s['count'],s['box']) for k,s in large]
    upper=sorted(large[:4],key=lambda x:x[1]['box'][0]);lower=sorted(large[4:],key=lambda x:x[1]['box'][0])
    groups=[];report=[]
    for row in (upper,lower):
        poses=[]
        for label,s in row:
            # Every main silhouette is connected. Retain one pixel of alpha edge.
            mask=np.array(Image.fromarray((labels==label).astype('uint8')*255).filter(ImageFilter.MaxFilter(3)))>0
            b=a.copy();b[~mask | (b[:,:,3]<28)]=0;b[b[:,:,3]==0]=0
            pose=Image.fromarray(b);box=pose.getchannel('A').getbbox()
            assert min(box[:2])>0 and box[2]<im.width and box[3]<im.height,(path,box,'source clipped')
            poses.append(ImageOps.expand(pose.crop(box),border=2,fill=(0,0,0,0)))
            report.append({'solidPixels':s['count'],'sourceBox':box})
        groups.append(poses)
    return groups,{'method':'connected silhouettes, preserving alpha contour; no straight cut through neighboring feet or wings','poses':report}
