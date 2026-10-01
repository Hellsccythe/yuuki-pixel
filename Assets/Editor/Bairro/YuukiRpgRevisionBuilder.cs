#if UNITY_EDITOR
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

public static class YuukiRpgRevisionBuilder
{
    private const string Root="Assets/Game/Resources/RpgRevision/";
    [Serializable] private sealed class HomeAsset { public string id; public float width,ppu,pivotY; }
    [Serializable] private sealed class HomeCatalog { public HomeAsset[] assets; }
    [Serializable] private sealed class NeighborhoodCatalog { public YuukiSpriteInfo[] sprites; }
    private const string Neighborhood="Assets/Game/Resources/NeighborhoodV6/";

    [MenuItem("Yuuki/Protótipo/Reconstruir interiores e exportar")]
    public static void BuildAndExport()
    {
        // The export rebuilds every map scene (interiors included) before building the player.
        YuukiBairroReleaseBuilder.BuildAndExport();
    }

    public static void Import()
    {
        AssetDatabase.Refresh();
        foreach(var path in Directory.GetFiles(Root+"Yuuki","*.png"))
            Texture(path.Replace('\\','/'),200,new Vector2(.5f,112f/512));
        var catalog=JsonUtility.FromJson<HomeCatalog>(File.ReadAllText(Root+"home.json"));
        foreach(var a in catalog.assets) Texture(Root+"Home/"+a.id+".png",a.ppu,new Vector2(.5f,a.pivotY));
        var neighborhood=JsonUtility.FromJson<NeighborhoodCatalog>(File.ReadAllText(Neighborhood+"catalog.json"));
        foreach(var a in neighborhood.sprites) Texture(a.path,a.ppu,new Vector2(a.pivotX,a.pivotY));
    }

    private static void Texture(string path,float ppu,Vector2 pivot)
    {
        var t=(TextureImporter)AssetImporter.GetAtPath(path);
        t.textureType=TextureImporterType.Sprite; t.spriteImportMode=SpriteImportMode.Single;
        t.spritePixelsPerUnit=ppu; t.filterMode=FilterMode.Point; t.mipmapEnabled=false;
        t.textureCompression=TextureImporterCompression.Uncompressed; t.alphaIsTransparency=true;
        t.npotScale=TextureImporterNPOTScale.None; t.maxTextureSize=2048;
        var settings=new TextureImporterSettings(); t.ReadTextureSettings(settings);
        settings.spriteAlignment=(int)SpriteAlignment.Custom; settings.spritePivot=pivot;
        settings.spriteMeshType=SpriteMeshType.FullRect; t.SetTextureSettings(settings); t.SaveAndReimport();
    }

    public static void AddHouses(Transform map)
    {
        foreach(string id in new[]{"casa-yuuki","casa-tenebris"})
        {
            var shell=map.GetComponentsInChildren<Transform>().FirstOrDefault(t=>t.name==id);
            if(shell==null) continue;
            BuildHouse(shell,id);
        }
        // Replace the flat vegetable patch while retaining its existing footprint.
        foreach(var t in map.GetComponentsInChildren<Transform>().Where(t=>t.name=="horta"))
        {
            var r=t.GetComponentInChildren<SpriteRenderer>();
            if(r!=null) r.sprite=AssetDatabase.LoadAssetAtPath<Sprite>(Root+"Home/horta.png");
        }
    }

    // Every other enterable building of the map: same cutaway behaviour as the two family
    // houses, with a room sized to the footprint and furniture chosen by theme.
    public static void AddGenericHouses(Transform map,YuukiBairroData data)
    {
        if(data.houses==null) return;
        foreach(var h in data.houses)
        {
            var shell=map.GetComponentsInChildren<Transform>(true).FirstOrDefault(t=>t.name==h.sprite &&
                Vector2.Distance(t.position,new Vector2(h.x,h.y))<.05f);
            if(shell==null){ Debug.LogWarning("Casa não encontrada no mapa: "+h.name); continue; }
            BuildGenericHouse(shell,h);
        }
    }

    private static void BuildGenericHouse(Transform shell,YuukiHouseInfo h)
    {
        float w=h.roomW, ht=h.roomH, left=h.x-w/2;
        var root=new GameObject("Interior "+h.name).transform;
        root.SetParent(shell.parent,false);
        var house=root.gameObject.AddComponent<YuukiCutawayHouse>();
        house.houseName=h.name;
        house.exterior=shell.GetComponentInChildren<SpriteRenderer>();
        house.exteriorCollider=shell.GetComponent<Collider2D>();
        house.threshold=new Vector2(h.doorX,h.y+.18f);
        house.roomBounds=new Rect(left,h.y,w,ht);
        var rooms=new GameObject("Cômodos").transform; rooms.SetParent(root,false);
        house.interior=rooms.gameObject;
        house.floors=new GameObject[Mathf.Clamp(h.floors,1,2)];
        // Use the side furthest from the exterior door for the private room / stairs.
        bool serviceLeft=h.doorX>=h.x;
        for(int level=0;level<house.floors.Length;level++)
        {
            var room=new GameObject(level==0?"Térreo":"Primeiro andar").transform;
            room.SetParent(rooms,false); house.floors[level]=room.gameObject;
            BuildFloor(room,house,h,level,serviceLeft);
            room.gameObject.SetActive(level==0);
        }
        string doorPath=h.sprite=="casa-yuuki" || h.sprite=="casa-tenebris"
            ?Root+"Home/porta-"+h.sprite+".png":"Assets/Game/Bairro/Sprites/Doors/"+h.door+".png";
        var gapArt=Art(root,doorPath,new Vector2(h.doorX,h.doorY),h.doorWidth,8);
        gapArt.name="Vão da porta"; gapArt.color=new Color(.045f,.033f,.025f); gapArt.flipX=h.flip;
        house.doorway=gapArt;
        var hinge=new GameObject("Dobradiça").transform; hinge.SetParent(root,false);
        hinge.position=new Vector3(h.doorX-h.doorWidth/2,h.doorY,0);
        house.door=Art(hinge,doorPath,new Vector2(h.doorX,h.doorY),h.doorWidth,9);
        house.door.flipX=h.flip; house.doorHinge=hinge;
        rooms.gameObject.SetActive(false);
    }

    private static void BuildFloor(Transform room,YuukiCutawayHouse house,YuukiHouseInfo h,int level,bool serviceLeft)
    {
        const string old="Assets/Game/Bairro/Sprites/Interior/";
        float w=h.roomW, ht=h.roomH, left=h.x-w/2, by=h.y;
        bool upstairs=level>0, two=house.floors.Length>1, small=w<4.6f || ht<4.5f;
        string skin=upstairs?"familia":h.theme;
        if(skin!="oficina" && skin!="barraco") skin="familia";
        var floor=Art(room,Neighborhood+"room-"+skin+".png",new Vector2(h.x,by),w,-50);
        floor.transform.localScale=new Vector3(w/floor.sprite.bounds.size.x,ht/floor.sprite.bounds.size.y,1);
        // The back third is a visible wall, never usable floor or furniture space.
        float top=ht*.65f, margin=.3f;
        Wall(room,new Vector2(left+.14f,by+ht/2),new Vector2(.28f,ht));
        Wall(room,new Vector2(left+w-.14f,by+ht/2),new Vector2(.28f,ht));
        Wall(room,new Vector2(h.x,by+(ht+top)/2),new Vector2(w,ht-top));
        float gap=Mathf.Max(.58f,h.doorWidth/2+.08f);
        void CrossWall(float a,float b,float y)
        {
            float length=b-a; if(length<.16f) return;
            var sr=Art(room,Root+"Home/meia-parede.png",new Vector2(left+(a+b)/2,by+y),length);
            sr.name="Parede baixa";
            sr.transform.localScale=new Vector3(length/sr.sprite.bounds.size.x,.55f/sr.sprite.bounds.size.y,1);
            Wall(room,new Vector2(left+(a+b)/2,by+y+.1f),new Vector2(length,.2f));
        }
        if(upstairs) CrossWall(0,w,0);
        else { CrossWall(0,h.doorX-left-gap,0); CrossWall(h.doorX-left+gap,w,0); }
        // A bedroom/service room on one side; a full-width southern passage connects it
        // to the living area. Furnishings never occupy the passage or the door landing.
        float split=serviceLeft?w*.40f:w*.60f;
        float doorwayY=Mathf.Min(1.5f,top*.56f);
        float partitionBase=doorwayY+.5f;
        float partitionLength=top-partitionBase;
        if(partitionLength>.35f)
        {
            var partition=Art(room,Neighborhood+"divisoria.png",new Vector2(left+split,by+partitionBase),.23f);
            partition.name="Divisória quarto / sala";
            partition.transform.localScale=new Vector3(.23f/partition.sprite.bounds.size.x,(partitionLength+.15f)/partition.sprite.bounds.size.y,1);
            Wall(room,new Vector2(left+split,by+partitionBase+partitionLength/2),new Vector2(.2f,partitionLength));
        }
        float sideCenter=serviceLeft?split/2:(split+w)/2;
        float livingCenter=serviceLeft?(split+w)/2:split/2;
        float sideWidth=serviceLeft?split:w-split;
        float livingWidth=w-sideWidth;
        Vector2 World(float x,float y)=>new Vector2(left+x,by+y);
        SpriteRenderer Place(string path,string label,float x,float bottom,float width,float colliderDepth=0,int order=0)
        {
            var sprite=AssetDatabase.LoadAssetAtPath<Sprite>(path);
            float height=width*sprite.bounds.size.y/sprite.bounds.size.x;
            // Keep the complete drawing below the rear wall; use a smaller piece if needed.
            float maxHeight=top-.45f;
            if(height>maxHeight) { width*=maxHeight/height; height=maxHeight; }
            float y=Mathf.Clamp(bottom,margin,Mathf.Max(margin,top-height-.08f));
            x=Mathf.Clamp(x,margin+width/2,w-margin-width/2);
            var r=Art(room,path,World(x,y),width,order);
            r.name="Mobília — "+label;
            // Align the actual bounds, not a varying pivot from the source sprite.
            r.transform.position+=Vector3.up*(by+y-r.bounds.min.y);
            if(colliderDepth>0) Wall(room,World(x,y+colliderDepth/2),new Vector2(width*.80f,colliderDepth));
            return r;
        }
        float furniture=Mathf.Min(1.02f,sideWidth-.55f);
        if(two)
        {
            float stairWidth=Mathf.Min(1.0f,sideWidth-.5f);
            var stair=Place(Neighborhood+(upstairs?"escada-descer":"escada-subir")+".png",
                upstairs?"Escada para o térreo":"Escada para o quarto",sideCenter,Mathf.Max(1.65f,top-2.2f),stairWidth,.45f);
            var link=stair.gameObject.AddComponent<YuukiHouseStair>();
            link.house=house; link.targetFloor=upstairs?0:1;
            link.prompt=upstairs?"Descer ao térreo":"Subir ao primeiro andar";
            link.point=new Vector2(0,-.35f); link.radius=.95f;
            link.landing=World(sideCenter,.95f);
        }
        else
        {
            Place(old+"cama.png","Quarto",sideCenter,top-2.0f,furniture,.7f);
        }
        if(upstairs)
        {
            Place(old+"cama.png","Quarto da família",livingCenter,top-2.05f,Mathf.Min(1.2f,livingWidth-.65f),.8f);
            if(w>5.2f) Place(old+"cama.png","Cama infantil",livingCenter+livingWidth*.26f,.55f,.76f,.65f);
        }
        else
        {
            float stoveWidth=small?.58f:.77f;
            float stoveX=serviceLeft?w-.65f:.65f;
            var stove=Place(Root+"Home/fogao.png","Cozinha",stoveX,top-1.7f,stoveWidth,.36f);
            var fire=stove.gameObject.AddComponent<YuukiLight>(); fire.mode=YuukiLight.Mode.Always;
            fire.radius=2.6f; fire.intensity=.85f; fire.flicker=.25f; fire.color=new Color(1f,.65f,.35f);
            fire.offset=new Vector2(0,.3f);
            float tableX=serviceLeft?split+(small?.55f:.8f):split-(small?.55f:.8f);
            // Shallow shelters need the full passage; larger homes can fit a dining table.
            if(ht>=4.2f) Place(old+"mesa.png",h.theme=="oficina"?"Bancada de trabalho":"Mesa da família",
                tableX,Mathf.Min(1.85f,top*.48f),small?.70f:1.05f,.36f);
            if(!small)
            {
                var cabinet=Place(old+"estante.png",h.theme=="oficina"?"Prateleira de encomendas":"Estante da sala",
                    tableX,top-.7f,.72f,.23f);
                var library=cabinet.gameObject.AddComponent<YuukiBookshelf>();
                library.shelfName="Estante — "+h.name; library.prompt="Ver livros";
                library.point=new Vector2(0,-.25f); library.radius=1.05f;
            }
            if(h.sprite=="casa-yuuki")
                Place(old+"cama.png","Cama infantil da Yuuki",sideCenter+.62f,.5f,.68f,.66f);
        }
        // A small book pile is kept in the private room / stair alcove, never floating on the wall.
        float bookX=serviceLeft?.55f:w-.55f;
        var books=Place(Root+"Home/livros.png","Livros",bookX,.48f,.36f);
        var shelf=books.gameObject.AddComponent<YuukiBookshelf>();
        shelf.shelfName=(upstairs?"Livros do quarto — ":"Livros da família — ")+h.name;
        shelf.prompt="Ver livros"; shelf.point=Vector2.zero; shelf.radius=1.05f;
        float rugX=two?livingCenter:(h.doorX-left);
        Place(Root+"Home/tapete.png","Tapete",rugX,.35f,Mathf.Min(small?1.1f:1.65f,livingWidth-.35f),0,-40);
        // The partition divides private and shared space; the stove, dining table
        // and shelves define the kitchen/living area without blocking its doorway.
        if(h.theme=="oficina" && !upstairs && !small)
            Place(Neighborhood+"lenha.png","Materiais",sideCenter,.4f,.82f,.35f);
    }

    private static SpriteRenderer Art(Transform parent,string path,Vector2 at,float width,int order=0)
    {
        var sprite=AssetDatabase.LoadAssetAtPath<Sprite>(path);
        if(sprite==null) throw new InvalidOperationException(path);
        var go=new GameObject(Path.GetFileNameWithoutExtension(path));
        go.transform.SetParent(parent,false); go.transform.position=at;
        var sr=go.AddComponent<SpriteRenderer>(); sr.sprite=sprite; sr.spriteSortPoint=SpriteSortPoint.Pivot;
        sr.sortingOrder=order;
        go.transform.localScale=Vector3.one*(width/sprite.bounds.size.x);
        return sr;
    }

    private static void Wall(Transform parent,Vector2 center,Vector2 size)
    {
        var go=new GameObject("Colisão da parede visível"); go.transform.SetParent(parent,false);
        go.transform.position=center; go.AddComponent<BoxCollider2D>().size=size;
    }

    private static void BuildHouse(Transform shell,string id)
    {
        var outside=shell.GetComponentInChildren<SpriteRenderer>();
        var sp=outside.sprite;
        bool yuuki=id=="casa-yuuki";
        float dx=yuuki?241.5f:222.5f,dy=yuuki?340:468;
        BuildGenericHouse(shell,new YuukiHouseInfo {
            sprite=id,name=yuuki?"Casa da Yuuki":"Casa do Tenebris",theme="familia",seed=yuuki?1:2,
            x=shell.position.x,y=shell.position.y,roomW=yuuki?6.4f:6.8f,roomH=6.2f,floors=yuuki?1:2,
            doorX=shell.position.x+(dx-sp.pivot.x)/sp.pixelsPerUnit,
            doorY=shell.position.y+(sp.rect.height-dy-sp.pivot.y)/sp.pixelsPerUnit,
            doorWidth=yuuki?1.05f:.883f
        });
    }
}
#endif
