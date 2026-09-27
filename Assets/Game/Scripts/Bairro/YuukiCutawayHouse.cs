using System.Collections;
using UnityEngine;

// A preloaded room occupying the exterior's actual footprint. No teleport to a
// distant room, scene load, full-screen overlay or black fade is used here.
public sealed class YuukiCutawayHouse : MonoBehaviour
{
    public string houseName;
    public Rect roomBounds;
    public GameObject interior;
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
        else if (Inside && near && p.y<threshold.y+.72f && inputY<0) TryExit();
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
        if (!Inside || Transitioning || map==null || !map.BeginHouseTransition()) return false;
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
        interior.SetActive(true);
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
        exterior.color=Color.white;
        SetDoorAlpha(1);
        exteriorCollider.enabled=true;
        for(float t=1;t>0;t-=Time.deltaTime/.28f) { SetDoor(t); yield return null; }
        SetDoor(0); door.enabled=false; doorway.enabled=false;
        animation.ScriptedMotion=false;
        Inside=false; Transitioning=false; readyAt=Time.time+.5f;
        map.FinishHouseTransition();
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
