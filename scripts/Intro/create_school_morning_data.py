from pathlib import Path
import json,shutil
R=Path('D:/yuuki-pixel');S=Path(__file__).parent;O=R/'Assets/Game/Resources/SchoolMorning'
def save(p,v):p.parent.mkdir(parents=True,exist_ok=True);p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
def lines(s):
    return [{'speaker':a,'text':b} for a,b in (line.split('|',1) for line in s.strip().splitlines())]
steps=[]
def step(id,kind,title,x,y,dialog='',**kw):
    steps.append(dict(id=id,kind=kind,title=title,x=x,y=y,range=kw.pop('range',70),speed=kw.pop('speed',138),lines=lines(dialog) if dialog else [],**kw))
step('flower','action','Ajeite a flor no jardim de Sara',560,755,'Yuuki|Você vai ter que colaborar também...',action='pickup',seconds=1.15,prompt='Ajeitar a flor',guide=False)
step('gate-first','action','Abra o portão do quintal',660,855,'Yuuki|Ngh...',action='grasp',seconds=1.15,prompt='Tentar abrir o portão',guide=False)
step('gate-again','action','O portão emperrou. Tente outra vez',660,855,'Yuuki|De novo...',action='grasp',seconds=1.15,prompt='Tentar outra vez',guide=False)
step('gate-help','script','Tenebris veio ajudar',660,855,'Tenebris|Yuuki, deixa que eu ajudo.\nYuuki|A-ah!\nTenebris|Um, dois...',action='tenebris_grasp',seconds=1.5,guide=False)
step('gate-talk','talk','Atravesse o portão com Tenebris',660,855,'''Tenebris|Viu?
Yuuki|Eu conseguiria.
Tenebris|Eu sei.
Yuuki|Então por que ajudou?
Tenebris|Porque eu cheguei.
Yuuki|O-obrigada, Tenebris.
Tenebris|Não precisa agradecer por tudo.''',guide=False)
step('leave-yard','move','Saia do quintal',760,970)
step('close-gate','action','Confira se o portão ficou fechado',680,949,action='grasp',seconds=1.6,prompt='Fechar e conferir o portão',guide=False,minY=925,range=80)
step('bread-walk','move','Siga Tenebris pelo bairro',1320,950)
step('bread-talk','talk','O cheiro de pão',1320,950,'''Tenebris|Tá com fome?
Yuuki|Não.
Yuuki|...um pouco.
Tenebris|Você tomou café?
Yuuki|Tomei.
Tenebris|Então?
Yuuki|Uma pessoa pode ter tomado café e ainda achar pão cheiroso.
Tenebris|Faz sentido.''')
step('greeting-walk','move','Continue pela rua',1780,930)
step('greeting','talk','Um bairro despertando',1780,930,'Senhora|Bom dia, crianças!\nYuuki|Bom dia!')
step('ball-walk','move','A bola escapou para a rua',2160,930)
step('ball-pick','action','Devolva a bola às crianças',2160,930,action='pickup',seconds=1.15,prompt='Pegar a bola',guide=False)
step('ball-talk','talk','Uma pequena gentileza',2160,930,'''Menino|Ei!
Yuuki|Cuidado perto da estrada maior, tá?
Menino|Tá!
Yuuki|O quê?
Tenebris|Nada.
Yuuki|Você está olhando.
Tenebris|Você também olha pra mim.
Yuuki|Porque você está olhando pra mim!
Tenebris|Então estamos empatados.''')
step('worry-walk','move','Suba a rua com Tenebris',2690,850,'''Tenebris|Aconteceu alguma coisa ontem?
Yuuki|Não.
Tenebris|Tá.
Yuuki|O que foi?
Tenebris|Nada.
Yuuki|Tenebris.
Tenebris|Você falou que não aconteceu nada.
Yuuki|Então por que perguntou?
Tenebris|Porque você faz isso quando tá preocupada.
Tenebris|Isso.
Yuuki|Eu só estava ajeitando.
Tenebris|Faz dez minutos?
Yuuki|Não fazem dez minutos.
Tenebris|Sete?
Yuuki|Nem sete.
Tenebris|Cinco?
Tenebris|Sabia.
Yuuki|Você é irritante.
Tenebris|Você fala isso bastante.
Yuuki|Porque você é.''')
step('wings-talk','talk','Uma branca. Outra negra.',2690,850,'''Tenebris|Foi alguém da escola?
Yuuki|Não.
Tenebris|Eu nem falei nada.
Yuuki|Mas pensou.
Tenebris|Você não sabe o que eu pensei.
Yuuki|Sei sim.
Tenebris|Então fala.
Yuuki|Você está pensando em bater em alguém.
Yuuki|Acertei.
Tenebris|Talvez.
Yuuki|Tenebris...
Tenebris|Se fizeram alguma coisa com você...
Yuuki|Não fizeram nada.
Yuuki|Nada importante.
Tenebris|Isso não é a mesma coisa.
Yuuki|Eles só falaram das minhas asas de novo.
Tenebris|Idiotas.
Yuuki|Não chama eles assim.
Tenebris|Mas são.
Yuuki|Talvez eles só não entendam.
Tenebris|Dá na mesma.
Yuuki|Não dá.
Tenebris|Você sempre faz isso.
Yuuki|Isso o quê?
Tenebris|Arruma desculpa pra todo mundo.
Yuuki|Talvez.
Tenebris|Até pra quem é ruim com você.
Yuuki|Se eu ficar brava com todo mundo que faz alguma coisa ruim comigo... vou acabar ficando brava com muita gente.''')
step('stone-walk','move','Uma pedra no caminho',3000,820)
step('stone-kick','action','Tente tocar a pedrinha',3000,820,action='kick',seconds=.95,prompt='Tocar a pedra',guide=False)
step('tease','talk','A risada do Tenebris',3000,820,'''Tenebris|Você errou!
Yuuki|Eu sei!
Tenebris|Ela nem se mexeu!
Yuuki|Cala a boca!
Yuuki|Ei!
Tenebris|Você que falou pra eu calar a boca!
Yuuki|Volta aqui!''')
step('run-tip','tutorial','Corra atrás de Tenebris',3000,820,guide=False)
step('race','race','Alcance Tenebris',3650,800,speed=232,seconds=3,range=75)
step('exhaust','script','Recupere o fôlego',3650,800,'''Yuuki|Espera... espera...
Tenebris|Yuuki?
Yuuki|Eu tô bem...
Tenebris|Você correu nem um minuto.
Yuuki|Eu sei...
Yuuki|Vamos. A gente vai se atrasar.''',action='exhaust',seconds=5.5,guide=False)
step('school-walk','move','Anjos do Testamento',4170,755,speed=106,range=65)
step('arrival','finish','Vocês chegaram à escola',4170,755,guide=False)
objects=[];blockers=[]
def obj(id,resource,x,y,w,group='props',**kw):objects.append(dict(id=id,resource=resource,x=x,y=y,w=w,group=group,**kw))
def block(x,y,w,h,id):blockers.append(dict(x=x,y=y,w=w,h=h,id=id))
def house(id,res,x,y,w):
    obj(id,res,x,y,w,'houses');block(x-w*.42,y-75,w*.84,70,id)
house('Casa dos Arcadia','NeighborhoodV6/casa-simples-0',450,690,440)
house('Casa de Tenebris','NeighborhoodV6/casa-simples-1',1000,670,410)
house('Padaria','Environment/Art/padaria',1420,745,400)
house('Casa com varal','NeighborhoodV6/casa-simples-2',1900,690,390)
house('Casa de madeira','NeighborhoodV6/barraco-3',2340,680,345)
house('Moradia de pedra','NeighborhoodV6/casa-simples-0',2900,610,350)
house('Casa da ladeira','NeighborhoodV6/casa-simples-1',3340,600,340)
house('Anjos do Testamento','SchoolMorning/school',4230,665,660)
for x,y in [(540,755),(600,762),(525,735)]:obj('Jardim de Sara','SchoolMorning/Props/flower',x,y,40)
for x,y in [(1100,790),(1650,790),(2300,1100),(2600,1100),(3350,1080)]:obj('Caixotes','NeighborhoodV6/barris-agua',x,y,72)
for x,y in [(200,1030),(1160,1080),(1700,1080),(2580,680),(3150,1070),(3940,1040),(4520,900)]:
    obj('Árvore','World/Art/tree',x,y,235) if (R/'Assets/Game/Resources/World/Art/tree.png').exists() else obj('Árvore','Environment/Art/arvore-balanco',x,y,235)
obj('Varal','NeighborhoodV6/varal-v6',2050,760,160)
obj('Senhora','SchoolMorning/Residents/lady',1780,870,100,'residents')
obj('Menino','SchoolMorning/Residents/boy-blue',2230,970,77,'residents')
obj('Menino menor','SchoolMorning/Residents/boy-red',2360,1040,76,'residents')
obj('Cachorro','SchoolMorning/Residents/dog',2320,1050,54,'residents')
obj('Professor','SchoolMorning/Residents/teacher-man',4050,740,102,'residents')
obj('Professora','SchoolMorning/Residents/teacher-woman',4370,735,103,'residents')
obj('Banco','Environment/Art/banco-escola',3910,870,140)
obj('Poça','NeighborhoodV6/poca-v6',1610,1000,86,'ground')
obj('Poça','NeighborhoodV6/poca-v6',2510,953,74,'ground')
obj('Carroça','NeighborhoodV6/carroca-quebrada',3760,1050,175)
# Continuous perimeter with one real gate opening; never duplicate the moving gate.
for left,right in [(200,552),(788,840)]:
    for start in range(left,right,176):
        span=min(176,right-start)
        obj('Cerca frontal','SchoolMorning/Props/fence-front',start+span/2,914,span,'fence',h=130)
    block(left,889,right-left,18,'garden-front')
for x in (200,840):
    for y in (535,724,914):obj('Cerca lateral','SchoolMorning/Props/side-fence',x,y,30,'fence',h=320)
    block(x-8,346,16,561,'garden-side')
for x in (288,464,640,808):obj('Cerca dos fundos','SchoolMorning/Props/fence-front',x,350,176,'fence',h=130)
block(192,340,656,18,'garden-back')
maps=[]
for id,name,start,end in [('quintal','O jardim de Sara',0,1150),('rua','A rua acorda',1150,2250),('ladeira','Uma branca. Outra negra.',2250,3500),('escola','Anjos do Testamento',3500,4700)]:
    m=dict(id=id,name=name,start=start,end=end,objects=[o for o in objects if start<=o['x']<end])
    resource='SchoolMorning/Maps/'+id;save(O/'Maps'/(id+'.json'),m);maps.append(resource)
data=dict(version=2,title='A caminho da Escola Anjos do Testamento',chapter='Prólogo · Os Subúrbios',startHour='06:45',storyAge=8,width=4700,height=1400,start={'x':460,'y':777},companionStart={'x':747,'y':969},gate={'x':670,'y':914,'collider':{'x':552,'y':889,'w':236,'h':18}},maps=maps,objects=objects,blockers=blockers,steps=steps,actors={'yuuki':'Childhood/YuukiV2/animations','tenebris':'Childhood/Tenebris/animations'},controls={'action':'F','run':'Shift','move':'WASD / setas','dialogue':'Espaço / Enter'},introActions='SchoolMorning/actions',notes='Age follows the new scene text. Existing child visuals reused; approved archives untouched. Residents use four-frame cycles; Yuuki has separate backpack straps and a subtle four-frame nervous gesture. Four modular map files connect continuously.')
save(O/'story.json',data)
save(S/'school-story.json',data)
print(json.dumps({'steps':len(steps),'dialogueLines':sum(len(s['lines']) for s in steps),'objects':len(objects),'modules':len(maps)}))
