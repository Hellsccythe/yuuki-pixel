"""Versioned Kled animation packing; preserves all previously approved assets."""
from pathlib import Path
from PIL import Image,ImageDraw
import numpy as np
import json,shutil,hashlib,importlib.util
import kled_extract

ROOT=Path('D:/yuuki-pixel');STAGE=Path(__file__).parent
ART=ROOT/'Art/Characters/Parents/Kled/Animations-v1'
OUT=ROOT/'Assets/Game/Resources/Parents/KledV2'
GEN=Path('C:/Users/Hellsccythe/.codex/generated_images/01a0de91-4e4f-79f2-9ff8-3bfa5d375ffa')
spec=importlib.util.spec_from_file_location('sara_helpers',ROOT/'scripts/pack_sara_animations.py')
sara=importlib.util.module_from_spec(spec);spec.loader.exec_module(sara)
sara.alice.clean=kled_extract.clean
save=sara.save;digest=sara.digest

def preservation():
    result={}
    for folder,stems in [('Art/Characters/Childhood',('adult-preservation','yuuki-child-approved-preservation','alice-child-approved-preservation','tenebris-child-approved-preservation')),('Art/Characters/Parents',('sara-design-approved-preservation','kled-design-approved-preservation','sara-animation-approved-preservation'))]:
        for stem in stems:
            data=json.loads((ROOT/folder/(stem+'.json')).read_text(encoding='utf-8-sig'))
            for f in data['files']:assert digest(ROOT/f['path'])==f['sha256'],f['path']
            result[stem]=len(data['files'])
    return result

def normalize(pose,scale,bob=0,idle=False):
    top,bottom,cx=sara.metric(pose);box=pose.getchannel('A').getbbox();crop=pose.crop(box)
    crop=crop.resize((round(crop.width*scale),round(crop.height*scale)),Image.Resampling.NEAREST)
    x=round(256-(cx-box[0])*scale)
    y=400-round((bottom-box[1])*scale) if idle else 96+bob-round((top-box[1])*scale)
    assert x>=12 and y>=12 and x+crop.width<=500 and y+crop.height<=500,(x,y,crop.size)
    out=Image.new('RGBA',(512,512));out.alpha_composite(crop,(x,y))
    return out,{'x':256,'y':round(y+(top-box[1])*scale-24)}

def main():
    protected=preservation()
    unchanged={str(p.relative_to(ROOT)):digest(p) for folder in ('Art/Characters/Childhood/Yuuki/Animations-v2','Assets/Game/Resources/Childhood/YuukiV2','Art/Characters/Parents/Kled/Design-v1','Assets/Game/Resources/Parents/Kled') for p in (ROOT/folder).rglob('*') if p.is_file()}
    assert not (OUT/'animations.json').exists(),'An existing animation revision must be preserved first'
    for folder in (ART/'Sources',ART/'Atlases',OUT/'Frames'):folder.mkdir(parents=True,exist_ok=True)
    cfgpath=STAGE/'kled-animation-production-prompts.json'
    if not cfgpath.exists():cfgpath=ART/'production-prompts.json'
    cfg=json.loads(cfgpath.read_text(encoding='utf-8'));save(ART/'production-prompts.json',cfg)
    for key,name in cfg['sources'].items():shutil.copy2(GEN/name,ART/'Sources'/(key+'.png'))
    clips=[];details=[]
    for direction in ('down','up','right'):
        source=ART/'Sources'/('motion_'+direction+'.png')
        motion,cuts=kled_extract.lateral_extract(source) if direction=='right' else sara.extract(source,2,4)
        idle,idlecuts=sara.extract(ART/'Sources'/('idle_'+direction+'.png'),1,3)
        for state,poses in zip(('walk','run','idle'),[motion[0],motion[1],idle[0]]):
            # One constant uniform scale per row, with no individual limb stretching.
            scale=304/float(np.median([sara.metric(p)[1]-sara.metric(p)[0] for p in poses]))
            ims=[];anchors=[];frames=[]
            for i,pose in enumerate(poses):
                frame,anchor=normalize(pose,scale,bob=(-1 if i%2 and state!='idle' else 0),idle=state=='idle')
                ims.append(frame);anchors.append(anchor)
                name=f'{state}_{direction}_v1_{i:02}';dest=OUT/'Frames'/(name+'.png')
                frame.save(dest);sara.meta(dest);frames.append('Parents/KledV2/Frames/'+name)
            clips.append({'name':state+'_'+direction,'frames':frames,'haloAnchors':anchors,'fps':6 if state=='walk' else 8 if state=='run' else 2,'loop':True,'sequence':[0,1,2,1] if state=='idle' else [0,1,2,3]})
            details.append({'clip':state+'_'+direction,'scale':scale,'bounds':[list(i.getchannel('A').getbbox()) for i in ims],'sourceOrder':list(range(len(ims))),'cuts':idlecuts if state=='idle' else cuts})
    for state in ('walk','run','idle'):
        src=next(c for c in clips if c['name']==state+'_right');paths=[]
        for i,path in enumerate(src['frames']):
            right=Image.open(ROOT/'Assets/Game/Resources'/(path+'.png')).convert('RGBA');left=sara.reflect(right)
            name=f'{state}_left_v1_{i:02}';dest=OUT/'Frames'/(name+'.png');left.save(dest);sara.meta(dest)
            assert np.array_equal(np.array(Image.open(dest)),np.array(left))
            paths.append('Parents/KledV2/Frames/'+name)
        clips.append({'name':state+'_left','frames':paths,'haloAnchors':[{'x':512-a['x'],'y':a['y']} for a in src['haloAnchors']],'fps':src['fps'],'loop':True,'sequence':src['sequence'][:],'mirroredFrom':state+'_right'})
    ordered=[next(c for c in clips if c['name']==st+'_'+d) for d in ('down','up','left','right') for st in ('walk','run','idle')]
    design=json.loads((ROOT/'Art/Characters/Parents/Kled/Design-v2/design.json').read_text(encoding='utf-8'))
    halo={k:v for k,v in design['halo'].items() if k!='anchor'};halo.update(status='approved design retained',alphaBaked=False)
    catalog={'character':'Kled','lifeStage':'adult','chapter':'childhood of Yuuki','status':'awaiting user motion review','designApproved':True,'weapons':False,'bodyFrame':design['bodyFrame'],'halo':halo,'wingAnatomy':design['wingAnatomy'],'playbackRevision':'kled-v1','clips':ordered}
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
    statepath=ROOT/'Art/Characters/Parents/design-state.json';state=json.loads(statepath.read_text(encoding='utf-8'))
    state.update(phase='Sara animations approved and archived; Kled animation pass ready for review',KledAnimations={'preview':'preview/kled-animation.html','catalog':'Assets/Game/Resources/Parents/KledV2/animations.json','clips':12,'drawings':44,'status':'awaiting user motion review'})
    save(statepath,state)
    assert preservation()==protected and all(digest(ROOT/p)==h for p,h in unchanged.items())
    save(ART/'packing-report.json',{'character':'Kled','drawings':44,'clips':12,'selectedGeneratedDrawings':33,'exactReflectedDrawings':11,'exactLateralMirror':True,'frontBackFaceAndFringeNotReflected':True,'protectedFilesVerified':protected,'otherFilesUnchanged':len(unchanged),'clipsDetail':details,'processing':'same 8-neighbor detached-speck cleanup as Alice; connected silhouette separation for lateral motion; transparent gutter splitting elsewhere; crop; one constant nearest-neighbor scale per row; integer registration; exact reflection; no anatomy painting'})
    save(OUT/'animations.json',catalog)
    (ART/'README.md').write_text('''# Kled — animações v1

Modelo adulto aprovado: cabelo preto em camadas, olhos vermelhos, brincos, roupa preta e duas asas brancas. Esta primeira passagem das animações aguarda avaliação do usuário.

- Andar: quatro quadros por direção, 6 fps.
- Correr: quatro quadros por direção, 8 fps.
- Respiração: três desenhos por direção, ciclo 1 → 2 → 3 → 2, 2 fps.
- Frente e costas têm desenhos próprios. Esquerda espelha exatamente a direita em torno do pivô.
- Corpo RGBA 512 × 512, apoio (256, 400), 220 pixels por unidade, Point, sem mipmaps e sem compressão.
- Auréola do modelo aprovado preservada como camada independente: opacidade 0,6 aplicada ao renderizar, cor livre.

`Sources/`: seis originais do ImageGen integrado. `Atlases/`: uma folha por direção; linhas andar, correr e respiração. `production-prompts.json`: instruções completas e fontes. `packing-report.json` e `final-qa.json`: recortes, registro e verificações. `preview-proof.png`: captura da prévia testada.

Recursos: `Assets/Game/Resources/Parents/KledV2/Frames/`, com catálogo `animations.json`. Prévia: `preview/kled-animation.html` (WASD/setas, Shift para correr, soltar para respirar).

Sara e os desenhos já aprovados da infância e da Yuuki adulta continuam preservados. As animações ainda não foram inseridas nas cenas do jogo.
''',encoding='utf-8')
    print(json.dumps({'drawings':44,'clips':12,'protected':protected,'unchangedOtherFiles':len(unchanged),'output':str(OUT)}))

if __name__=='__main__':main()
