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
        const string old="Assets/Game/Bairro/Sprites/Interior/";
        const string props="Assets/Game/Bairro/Sprites/Props/";
        float w=h.roomW, ht=h.roomH, left=h.x-w/2, baseY=h.y;
        var root=new GameObject("Interior "+h.name).transform;
        root.SetParent(shell.parent,false);
        var house=root.gameObject.AddComponent<YuukiCutawayHouse>();
        house.houseName=h.name;
        house.exterior=shell.GetComponentInChildren<SpriteRenderer>();
        house.exteriorCollider=shell.GetComponent<Collider2D>();
        house.threshold=new Vector2(h.doorX,baseY+.18f);
        house.roomBounds=new Rect(left,baseY,w,ht);
        var room=new GameObject("Cômodo").transform; room.SetParent(root,false); house.interior=room.gameObject;
        var floor=Art(room,Root+"Home/room.png",new Vector2(h.x,baseY),w,-50);
        floor.transform.localScale=new Vector3(w/floor.sprite.bounds.size.x,ht/floor.sprite.bounds.size.y,1);
        float back=Mathf.Min(2f,ht*.34f);
        Wall(room,new Vector2(left+.17f,baseY+ht/2),new Vector2(.34f,ht));
        Wall(room,new Vector2(left+w-.17f,baseY+ht/2),new Vector2(.34f,ht));
        Wall(room,new Vector2(left+w/2,baseY+ht-back/2),new Vector2(w,back));
        float gap=Mathf.Max(.6f,h.doorWidth/2+.1f);
        foreach(var section in new[]{new Vector2(left,h.doorX-gap),new Vector2(h.doorX+gap,left+w)})
        {
            float length=section.y-section.x;
            if(length<.2f) continue;
            var lowWall=Art(room,Root+"Home/meia-parede.png",new Vector2((section.x+section.y)/2,baseY),length);
            lowWall.transform.localScale=new Vector3(length/lowWall.sprite.bounds.size.x,.85f/lowWall.sprite.bounds.size.y,1);
            Wall(room,new Vector2((section.x+section.y)/2,baseY+.12f),new Vector2(length,.24f));
        }
        // Furniture goes to the side away from the door; the column in front of the door stays free.
        float doorLocal=h.doorX-left;
        bool doorRight=doorLocal>w/2;
        float Side(float fromWall)=>doorRight?fromWall:w-fromWall;
        float Other(float fromWall)=>doorRight?w-fromWall:fromWall;
        float backY=ht-back+.02f;
        SpriteRenderer Prop(string path,float x,float y,float width,float cw=0,float ch=0,int order=0)
        {
            // Keep a free corridor in front of the door (the arrival spot and the way out).
            float half=Mathf.Max(width,cw)/2, lane=.95f;
            if(order==0 && y<2.2f && Mathf.Abs(x-doorLocal)<lane+half)
            {
                float near=x<doorLocal ? doorLocal-lane-half : doorLocal+lane+half;
                float far=x<doorLocal ? doorLocal+lane+half : doorLocal-lane-half;
                bool Fits(float v)=>v>=.35f+half-.001f && v<=w-.35f-half+.001f;
                if(Fits(near)) x=near;
                else if(Fits(far)) x=far;
                else return null; // narrow shack: no room outside the corridor, leave it out
            }
            x=Mathf.Clamp(x,.35f+half,w-.35f-half);
            if(order==0 && y<2.2f && Mathf.Abs(x-doorLocal)<lane+half-.05f) return null;
            var r=Art(room,path,new Vector2(left+x,baseY+y),width,order);
            if(cw>0) Wall(room,new Vector2(left+x,baseY+y+ch/2),new Vector2(cw,ch));
            return r;
        }
        void Shelf(SpriteRenderer r,string shelfName,float reach)
        {
            if(r==null) return;
            var shelf=r.gameObject.AddComponent<YuukiBookshelf>();
            shelf.shelfName=shelfName; shelf.prompt="Ver livros"; shelf.point=new Vector2(0,-.45f); shelf.radius=reach;
        }
        void Fire(SpriteRenderer r,float radius,float intensity)
        {
            if(r==null) return;
            var fire=r.gameObject.AddComponent<YuukiLight>();
            fire.mode=YuukiLight.Mode.Always; fire.radius=radius; fire.intensity=intensity; fire.flicker=.35f;
            fire.color=new Color(1f,.62f,.3f); fire.offset=new Vector2(0,.35f);
        }
        bool odd=h.seed%2==1;
        switch(h.theme)
        {
            case "oficina":
                Prop(old+"mesa.png",Side(1.4f),backY,1.7f,1.5f,.6f);
                Fire(Prop(Root+"Home/fogao.png",Other(.8f),backY,1.0f,.8f,.5f),3.0f,1.0f);
                Prop(props+"caixotes.png",Side(.75f),1.0f,1.0f,.9f,.45f);
                Prop(props+"lenha.png",Other(1.0f),.9f,1.2f,1.0f,.4f);
                Prop(props+"barris-agua.png",Side(2.3f),.45f,.8f,.7f,.3f);
                Shelf(Prop(Root+"Home/livros.png",Other(1.9f),backY+.02f,.45f),"Cadernos de encomendas",.9f);
                break;
            case "barraco":
                Prop(old+"cama.png",Side(.7f),.35f,.9f,.72f,1.1f);
                if(odd) Fire(Prop(Root+"Home/fogao.png",Other(.7f),backY,.8f,.65f,.4f),2.2f,.8f);
                else
                {
                    var candle=Prop(props+"caixotes.png",Other(.7f),backY,.85f,.75f,.4f);
                    if(candle!=null)
                    {
                        var light=candle.gameObject.AddComponent<YuukiLight>();
                        light.mode=YuukiLight.Mode.Always; light.radius=1.8f; light.intensity=.7f; light.flicker=.45f;
                        light.color=new Color(1f,.75f,.45f); light.offset=new Vector2(0,.6f);
                    }
                }
                Prop(props+"barris-agua.png",Other(.6f),.4f,.7f,.6f,.3f);
                Prop(Root+"Home/tapete.png",w*.5f,.55f,Mathf.Min(1.6f,w*.38f),order:-40);
                if(h.seed%3==0) Shelf(Prop(Root+"Home/livros.png",Side(1.5f),backY+.02f,.42f),"Livros no chão",.9f);
                break;
            default: // familia
                Shelf(Prop(old+"estante.png",Other(.9f),backY,1.1f,.95f,.3f),"Estante — "+h.name,1.1f);
                Fire(Prop(Root+"Home/fogao.png",Side(.75f),backY,.95f,.75f,.45f),2.6f,.9f);
                Prop(old+"cama.png",Side(.8f),.4f,1.0f,.82f,1.3f);
                Prop(old+"mesa.png",Other(1.1f),.75f,1.35f,1.15f,.55f);
                Prop(Root+"Home/tapete.png",w*.5f,.5f,Mathf.Min(2.2f,w*.4f),order:-40);
                Shelf(Prop(Root+"Home/livros.png",Other(1.9f),backY+.02f,.45f),"Pilha de livros",.9f);
                break;
        }
        // Dark doorway and the door leaf that swings open (a crop of this very facade).
        string doorPath="Assets/Game/Bairro/Sprites/Doors/"+h.door+".png";
        var gapArt=Art(root,doorPath,new Vector2(h.doorX,h.doorY),h.doorWidth,8);
        gapArt.name="Vão da porta"; gapArt.color=new Color(.045f,.033f,.025f); gapArt.flipX=h.flip;
        house.doorway=gapArt;
        var hinge=new GameObject("Dobradiça").transform; hinge.SetParent(root,false);
        hinge.position=new Vector3(h.doorX-h.doorWidth/2,h.doorY,0);
        house.door=Art(hinge,doorPath,new Vector2(h.doorX,h.doorY),h.doorWidth,9);
        house.door.flipX=h.flip;
        house.doorHinge=hinge;
        room.gameObject.SetActive(false);
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
        float w=id=="casa-yuuki"?6.4f:6.8f;
        float h=6.2f;
        float baseY=shell.position.y;
        float left=shell.position.x-w/2;
        // Exact doorway pixel coordinates in each original facade.
        float dx=id=="casa-yuuki"?241.5f:222.5f;
        float dy=id=="casa-yuuki"?340:468;
        var sp=outside.sprite;
        float doorX=shell.position.x+(dx-sp.pivot.x)/sp.pixelsPerUnit;
        float doorY=baseY+(sp.rect.height-dy-sp.pivot.y)/sp.pixelsPerUnit;
        var root=new GameObject("Interior "+id).transform;
        root.SetParent(shell.parent,false);
        var house=root.gameObject.AddComponent<YuukiCutawayHouse>();
        house.houseName=id=="casa-yuuki"?"Casa da Yuuki":"Casa do Tenebris";
        house.exterior=outside; house.exteriorCollider=shell.GetComponent<Collider2D>();
        house.threshold=new Vector2(doorX,baseY+.18f);
        house.roomBounds=new Rect(left,baseY,w,h);
        var room=new GameObject("Cômodo").transform; room.SetParent(root,false); house.interior=room.gameObject;
        var floor=Art(room,Root+"Home/room.png",new Vector2(shell.position.x,baseY),w,-50);
        floor.transform.localScale=new Vector3(w/floor.sprite.bounds.size.x,h/floor.sprite.bounds.size.y,1);
        Wall(room,new Vector2(left+.17f,baseY+h/2),new Vector2(.34f,h));
        Wall(room,new Vector2(left+w-.17f,baseY+h/2),new Vector2(.34f,h));
        Wall(room,new Vector2(left+w/2,baseY+h-1),new Vector2(w,2));
        // Two visible low wall pieces leave an actual doorway gap.
        foreach(var section in new[]{new Vector2(left,doorX-.6f),new Vector2(doorX+.6f,left+w)})
        {
            float length=section.y-section.x;
            var lowWall=Art(room,Root+"Home/meia-parede.png",new Vector2((section.x+section.y)/2,baseY),length);
            lowWall.transform.localScale=new Vector3(length/lowWall.sprite.bounds.size.x,.85f/lowWall.sprite.bounds.size.y,1);
            Wall(room,new Vector2((section.x+section.y)/2,baseY+.12f),new Vector2(length,.24f));
        }
        SpriteRenderer Prop(string path,float x,float y,float width,float cw=0,float ch=0,int order=0)
        {
            var r=Art(room,path,new Vector2(left+x,baseY+y),width,order);
            if(cw>0) Wall(room,new Vector2(left+x,baseY+y+ch/2),new Vector2(cw,ch));
            return r;
        }
        // F on a bookshelf or a pile of books opens the book list ("Sem registro" until books exist).
        void Shelf(SpriteRenderer r,string shelfName,float reach)
        {
            var shelf=r.gameObject.AddComponent<YuukiBookshelf>();
            shelf.shelfName=shelfName; shelf.prompt="Ver livros"; shelf.point=new Vector2(0,-.45f); shelf.radius=reach;
        }
        const string old="Assets/Game/Bairro/Sprites/Interior/";
        Prop(Root+"Home/tapete.png",w*.51f,.9f,2.5f,order:-40);
        bool yuuki=id=="casa-yuuki";
        Prop(old+"cama.png",yuuki?1.05f:w-1.15f,yuuki?2.05f:1.7f,1.1f,.9f,1.45f);
        string family=yuuki?"da Yuuki":"do Tenebris";
        Shelf(Prop(old+"estante.png",2.65f,4.05f,1.25f,1.1f,.32f),"Estante "+family,1.1f);
        if(id=="casa-yuuki") Shelf(Prop(old+"estante.png",4.0f,4.05f,1.1f,.95f,.32f),"Estante dos pais da Yuuki",1.1f);
        Prop(old+"mesa.png",yuuki?w-1.3f:1.35f,1.8f,1.55f,1.3f,.65f);
        var stove=Prop(Root+"Home/fogao.png",yuuki?w-.85f:w-2.15f,3.35f,1.0f,.8f,.5f);
        var fire=stove.gameObject.AddComponent<YuukiLight>();
        fire.mode=YuukiLight.Mode.Always; fire.radius=2.6f; fire.intensity=.9f; fire.flicker=.35f;
        fire.color=new Color(1f,.62f,.3f); fire.offset=new Vector2(0,.35f);
        var pile=Prop(Root+"Home/livros.png",2.3f,3.9f,.5f);
        Shelf(pile,"Pilha de livros",.9f);
        var open=Prop(Root+"Home/livro-aberto.png",1.0f,.65f,.6f);
        Shelf(open,"Livro aberto no chão",.9f);
        // Dark aperture hides the painted closed door, then the original leaf swings.
        float dw=id=="casa-yuuki"?1.05f:.883f;
        var sr=Art(root,Root+"Home/porta-"+id+".png",new Vector2(doorX,doorY),dw,8);
        sr.name="Vão da porta"; sr.color=new Color(.045f,.033f,.025f);
        house.doorway=sr;
        var hinge=new GameObject("Dobradiça").transform; hinge.SetParent(root,false);
        hinge.position=new Vector3(doorX-dw/2,doorY,0);
        house.door=Art(hinge,Root+"Home/porta-"+id+".png",new Vector2(doorX,doorY),dw,9);
        house.doorHinge=hinge;
        room.gameObject.SetActive(false);
    }
}
#endif
