using System.Collections;
using System.Collections.Generic;
using System.Linq;
using UnityEngine;

// A preloaded room occupying the exterior's actual footprint. No teleport to a
// distant room, scene load, full-screen overlay or black fade is used here.
public sealed class YuukiCutawayHouse : MonoBehaviour
{
    public string houseName;
    public Rect roomBounds;
    public GameObject interior;
    public GameObject[] floors = new GameObject[0];
    public int CurrentFloor { get; private set; }
    public static YuukiCutawayHouse ActiveHouse { get; private set; }
    private readonly Dictionary<SpriteRenderer,bool> outsideVisibility = new Dictionary<SpriteRenderer,bool>();
    private readonly List<Collider2D> ignoredColliders = new List<Collider2D>();
    private readonly List<YuukiLight> hiddenLights = new List<YuukiLight>();
    private Collider2D playerCollider;
    public SpriteRenderer exterior;
    public Collider2D exteriorCollider;
    public Transform doorHinge;
    public SpriteRenderer door;
    public SpriteRenderer doorway;
    public Vector2 threshold;
    public bool Inside { get; private set; }
    public bool Transitioning { get; private set; }
    private SpriteRenderer[] contents;
    private YuukiBairro.Area outdoor;
    private float readyAt;
    private Color doorwayTint;

    private void Awake()
    {
        contents = interior.GetComponentsInChildren<SpriteRenderer>(true);
        doorwayTint=doorway.color;
        interior.SetActive(false);
        SetDoor(0);
        doorway.enabled=false;
        door.enabled=false;
    }

    private void Update()
    {
        var map=YuukiBairro.Instance;
        if (map==null || Transitioning || Time.time<readyAt || map.player.InputBlocked) return;
        var p=(Vector2)map.player.transform.position;
        // Intent matters: stopping at the doorstep must not immediately turn around.
        float inputY=Input.GetAxisRaw("Vertical");
        bool near=Mathf.Abs(p.x-threshold.x)<.7f;
        if (!Inside && map.Current.outdoor && near && p.y>threshold.y-.6f && p.y<threshold.y+.45f && inputY>0)
            TryEnter();
        else if (Inside && CurrentFloor==0 && near && p.y<threshold.y+.72f && inputY<0) TryExit();
    }

    public bool TryEnter()
    {
        var map=YuukiBairro.Instance;
        if (Inside || Transitioning || map==null || map.Current==null || !map.Current.outdoor ||
            Vector2.Distance(map.player.transform.position,threshold)>1.5f || !map.BeginHouseTransition()) return false;
        outdoor=map.Current;
        StartCoroutine(Enter(map));
        return true;
    }

    public bool TryExit()
    {
        var map=YuukiBairro.Instance;
        if (!Inside || CurrentFloor!=0 || Transitioning || map==null || !map.BeginHouseTransition()) return false;
        StartCoroutine(Exit(map));
        return true;
    }

    private IEnumerator Enter(YuukiBairro map)
    {
        Transitioning=true;
        doorway.enabled=true; door.enabled=true;
        for(float t=0;t<1;t+=Time.deltaTime/.28f) { SetDoor(t); yield return null; }
        SetDoor(1);
        exteriorCollider.enabled=false;
        CurrentFloor=0;
        for(int i=0;i<floors.Length;i++) floors[i].SetActive(i==0);
        interior.SetActive(true);
        ActiveHouse=this;
        IsolateInterior(map);
        SetContentsAlpha(0);
        var area=new YuukiBairro.Area { id=name, name=houseName, bounds=roomBounds, outdoor=false, background=outdoor.background };
        map.ShowHouseArea(area);
        var animation=map.player.GetComponent<YuukiRpgAnimation>();
        animation.ScriptedMotion=true; animation.ScriptedDirection=Vector2.up;
        Vector2 from=map.player.transform.position;
        Vector2 to=threshold+Vector2.up*.95f;
        for(float t=0;t<1;t+=Time.deltaTime/.55f)
        {
            float smooth=Mathf.SmoothStep(0,1,t);
            map.player.Teleport(Vector2.Lerp(from,to,smooth));
            exterior.color=new Color(1,1,1,1-smooth);
            SetDoorAlpha(1-smooth);
            SetContentsAlpha(smooth);
            yield return null;
        }
        map.player.Teleport(to);
        exterior.enabled=false; door.enabled=false; doorway.enabled=false;
        SetContentsAlpha(1);
        animation.ScriptedMotion=false;
        Inside=true; Transitioning=false; readyAt=Time.time+.35f;
        map.FinishHouseTransition();
    }

    private IEnumerator Exit(YuukiBairro map)
    {
        Transitioning=true;
        var animation=map.player.GetComponent<YuukiRpgAnimation>();
        animation.ScriptedMotion=true; animation.ScriptedDirection=Vector2.down;
        exterior.enabled=true; door.enabled=true; doorway.enabled=true;
        SetDoor(1);
        var from=(Vector2)map.player.transform.position;
        var to=threshold-Vector2.up*.68f;
        map.ShowHouseArea(outdoor);
        for(float t=0;t<1;t+=Time.deltaTime/.55f)
        {
            float smooth=Mathf.SmoothStep(0,1,t);
            map.player.Teleport(Vector2.Lerp(from,to,smooth));
            exterior.color=new Color(1,1,1,smooth);
            SetDoorAlpha(smooth);
            SetContentsAlpha(1-smooth);
            yield return null;
        }
        map.player.Teleport(to);
        interior.SetActive(false);
        RestoreExterior();
        ActiveHouse=null;
        exterior.color=Color.white;
        SetDoorAlpha(1);
        exteriorCollider.enabled=true;
        for(float t=1;t>0;t-=Time.deltaTime/.28f) { SetDoor(t); yield return null; }
        SetDoor(0); door.enabled=false; doorway.enabled=false;
        animation.ScriptedMotion=false;
        Inside=false; Transitioning=false; readyAt=Time.time+.5f;
        map.FinishHouseTransition();
    }

    public bool TryChangeFloor(int target,Vector2 landing)
    {
        var map=YuukiBairro.Instance;
        if(!Inside || Transitioning || target<0 || target>=floors.Length || target==CurrentFloor ||
            map==null || !map.BeginHouseTransition()) return false;
        StartCoroutine(ChangeFloor(map,target,landing));
        return true;
    }

    private IEnumerator ChangeFloor(YuukiBairro map,int target,Vector2 landing)
    {
        Transitioning=true;
        // Both floors are already in the same scene. Only room art fades, never the screen.
        var previous=floors[CurrentFloor];
        var previousArt=previous.GetComponentsInChildren<SpriteRenderer>();
        for(float t=0;t<1;t+=Time.deltaTime/.18f)
        {
            foreach(var sr in previousArt) sr.color=new Color(1,1,1,1-t);
            yield return null;
        }
        previous.SetActive(false); CurrentFloor=target;
        floors[target].SetActive(true);
        map.player.Teleport(landing);
        var nextArt=floors[target].GetComponentsInChildren<SpriteRenderer>();
        for(float t=0;t<1;t+=Time.deltaTime/.22f)
        {
            foreach(var sr in nextArt) sr.color=new Color(1,1,1,t);
            yield return null;
        }
        foreach(var sr in nextArt) sr.color=Color.white;
        Transitioning=false; readyAt=Time.time+.35f;
        map.ShowHouseArea(new YuukiBairro.Area { id=name, name=houseName+(target==0?" — térreo":" — primeiro andar"),
            bounds=roomBounds,outdoor=false,background=outdoor.background });
        map.FinishHouseTransition();
    }

    private bool BelongsToRoom(Transform t) => t.IsChildOf(transform);

    private void IsolateInterior(YuukiBairro map)
    {
        playerCollider=map.player.GetComponent<Collider2D>();
        // Suppress outdoor objects only while occupying the room; their enabled state
        // and existing collision exceptions are preserved individually.
        foreach(var sr in FindObjectsByType<SpriteRenderer>(FindObjectsSortMode.None))
        {
            if(BelongsToRoom(sr.transform) || sr==exterior || sr.transform.IsChildOf(map.player.transform) ||
                sr.sortingOrder < -50 || sr.sortingOrder >= 900) continue;
            outsideVisibility[sr]=sr.enabled;
        }
        foreach(var collider in FindObjectsByType<Collider2D>(FindObjectsSortMode.None))
        {
            if(collider==playerCollider || collider.isTrigger || BelongsToRoom(collider.transform) ||
                Physics2D.GetIgnoreCollision(playerCollider,collider)) continue;
            Physics2D.IgnoreCollision(playerCollider,collider,true); ignoredColliders.Add(collider);
        }
        foreach(var light in FindObjectsByType<YuukiLight>(FindObjectsSortMode.None))
            if(!BelongsToRoom(light.transform) && roomBounds.Contains(light.transform.position) && light.enabled)
            { hiddenLights.Add(light); light.enabled=false; }
        LateUpdate();
    }

    private void LateUpdate()
    {
        if(outsideVisibility.Count==0) return;
        foreach(var pair in outsideVisibility)
        {
            var sr=pair.Key; if(sr==null) continue;
            var b=sr.bounds;
            bool overlap=roomBounds.Overlaps(new Rect(b.min.x,b.min.y,b.size.x,b.size.y));
            sr.enabled=pair.Value && !overlap;
        }
    }

    private void RestoreExterior()
    {
        foreach(var pair in outsideVisibility) if(pair.Key!=null) pair.Key.enabled=pair.Value;
        outsideVisibility.Clear();
        foreach(var collider in ignoredColliders)
            if(collider!=null && playerCollider!=null) Physics2D.IgnoreCollision(playerCollider,collider,false);
        ignoredColliders.Clear();
        foreach(var light in hiddenLights) if(light!=null) light.enabled=true;
        hiddenLights.Clear();
    }

    private void OnDisable()
    {
        RestoreExterior();
        if(ActiveHouse==this) ActiveHouse=null;
    }

    private void SetContentsAlpha(float a)
    {
        foreach(var renderer in contents) renderer.color=new Color(1,1,1,a);
    }

    private void SetDoor(float open)
    {
        doorHinge.localScale=new Vector3(Mathf.Lerp(1,.10f,open),1,1);
    }

    private void SetDoorAlpha(float alpha)
    {
        door.color=new Color(1,1,1,alpha);
        doorway.color=new Color(doorwayTint.r,doorwayTint.g,doorwayTint.b,alpha);
    }
}
