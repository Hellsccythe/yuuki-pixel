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
        YuukiBairroBuilder.BuildAll();
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
        void Prop(string path,float x,float y,float width,float cw=0,float ch=0,int order=0)
        {
            var r=Art(room,path,new Vector2(left+x,baseY+y),width,order);
            if(cw>0) Wall(room,new Vector2(left+x,baseY+y+ch/2),new Vector2(cw,ch));
        }
        const string old="Assets/Game/Bairro/Sprites/Interior/";
        Prop(Root+"Home/tapete.png",w*.51f,.9f,2.5f,order:-40);
        bool yuuki=id=="casa-yuuki";
        Prop(old+"cama.png",yuuki?1.05f:w-1.15f,yuuki?2.05f:1.7f,1.1f,.9f,1.45f);
        Prop(old+"estante.png",2.65f,4.05f,1.25f,1.1f,.32f);
        if(id=="casa-yuuki") Prop(old+"estante.png",4.0f,4.05f,1.1f,.95f,.32f);
        Prop(old+"mesa.png",yuuki?w-1.3f:1.35f,1.8f,1.55f,1.3f,.65f);
        Prop(Root+"Home/fogao.png",yuuki?w-.85f:w-2.15f,3.35f,1.0f,.8f,.5f);
        Prop(Root+"Home/livros.png",2.3f,3.9f,.5f);
        Prop(Root+"Home/livro-aberto.png",1.0f,.65f,.6f);
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
