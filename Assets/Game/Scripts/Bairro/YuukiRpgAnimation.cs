using System;
using System.Collections.Generic;
using UnityEngine;

// Four-direction sprite playback is separate from the legacy platform Animator.
public sealed class YuukiRpgAnimation : MonoBehaviour
{
    [Serializable] public sealed class Clip { public string name; public string[] frames; public float fps; public bool loop; }
    [Serializable] public sealed class Catalog { public Clip[] clips; }
    public SpriteRenderer art;
    public Sprite[] runLeft, runRight;
    public string Facing { get; private set; } = "down";
    public string State { get; private set; } = "idle";
    public int FrameIndex { get; private set; }
    public bool ScriptedMotion { get; set; }
    public Vector2 ScriptedDirection { get; set; }
    private readonly Dictionary<string, Sprite[]> frames = new Dictionary<string, Sprite[]>();
    private float elapsed, stopped;
    private bool wasMoving, stowed = true;
    private int transitionIndex;
    private float transitionElapsed;
    private bool drawing;

    private void Awake()
    {
        if (art == null) art = GetComponentInChildren<SpriteRenderer>();
        var legacy = GetComponentInChildren<Animator>();
        if (legacy != null) legacy.enabled = false;
        var catalog = JsonUtility.FromJson<Catalog>(Resources.Load<TextAsset>("RpgRevision/yuuki").text);
        foreach (var clip in catalog.clips)
        {
            var list = new Sprite[clip.frames.Length];
            for (int i=0;i<list.Length;i++) list[i]=Resources.Load<Sprite>(clip.frames[i]);
            frames.Add(clip.name,list);
        }
        SetSprite("idle",0);
    }

    public void Tick(Vector2 movement, bool running, float delta)
    {
        if (ScriptedMotion) { movement=ScriptedDirection; running=false; }
        bool moving=movement.sqrMagnitude>.001f;
        if (moving)
        {
            string facing = Mathf.Abs(movement.y)>Mathf.Abs(movement.x) ? (movement.y>0?"up":"down") : (movement.x>0?"right":"left");
            if (facing!=Facing) { Facing=facing; elapsed=0; }
            if (!wasMoving && stowed)
            {
                drawing=true; transitionIndex=2; transitionElapsed=0;
            }
            stopped=0; wasMoving=true;
            if (drawing)
            {
                transitionElapsed+=delta;
                transitionIndex=2-Mathf.FloorToInt(transitionElapsed/.07f);
                if (transitionIndex>=0) { SetSprite("stow",transitionIndex); State="draw"; return; }
                drawing=false;
            }
            stowed=false; elapsed+=delta*(running?12:8);
            var run = Facing=="left" ? runLeft : Facing=="right" ? runRight : null;
            if (running && run!=null && run.Length>0)
            {
                State="run"; FrameIndex=Mathf.FloorToInt(elapsed)%run.Length;
                art.sprite=run[FrameIndex]; art.flipX=false;
                return;
            }
            SetSprite("walk",Mathf.FloorToInt(elapsed)%frames["walk_"+Facing].Length);
            return;
        }
        if (wasMoving) { wasMoving=false; drawing=false; stopped=0; elapsed=0; }
        stopped+=delta;
        if (!stowed)
        {
            if (stopped<.18f) { SetSprite("stow",0); return; }
            int frame=Mathf.FloorToInt((stopped-.18f)/.13f);
            if (frame<3) { SetSprite("stow",frame); return; }
            stowed=true; elapsed=0;
        }
        // Three drawings only, breathing out through the middle pose avoids a snap.
        elapsed+=delta;
        int[] breathing={0,1,2,1};
        SetSprite("idle",breathing[Mathf.FloorToInt(elapsed/.48f)%4]);
    }

    private void SetSprite(string state,int index)
    {
        State=state; FrameIndex=index;
        var list=frames[state+"_"+Facing];
        art.sprite=list[Mathf.Clamp(index,0,list.Length-1)];
        art.flipX=false;
    }
}
