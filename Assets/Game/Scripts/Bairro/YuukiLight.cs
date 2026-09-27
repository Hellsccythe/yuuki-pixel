using System.Collections.Generic;
using UnityEngine;

// A point of light read by YuukiLighting. Torches flicker; street lamps and windows only
// shine at night and can swap their sprite between "off" and "on".
public sealed class YuukiLight : MonoBehaviour
{
    public enum Mode { Always, NightOnly }

    public Mode mode = Mode.Always;
    [Min(0.1f)] public float radius = 3f;
    [Range(0f, 2f)] public float intensity = 1f;
    public Color color = new Color(1f, 0.72f, 0.38f);
    [Range(0f, 1f)] public float flicker = 0f;
    public Vector2 offset;                 // light origin relative to the object
    public SpriteRenderer lampRenderer;    // optional sprite swap
    public Sprite onSprite, offSprite;

    public static readonly List<YuukiLight> Active = new List<YuukiLight>();

    public Vector2 Position => (Vector2)transform.position + offset;
    public float CurrentIntensity { get; private set; }
    public float CurrentRadius { get; private set; }

    private float seed;
    private bool lastOn;

    private void OnEnable()
    {
        Active.Add(this);
        seed = Random.value * 100f;
        lastOn = !IsOn();
        Refresh();
    }

    private void OnDisable() { Active.Remove(this); }

    private bool IsOn() => mode == Mode.Always || YuukiClock.LampsOn;

    private void Update() { Refresh(); }

    private void Refresh()
    {
        bool on = IsOn();
        float target = on ? intensity : 0f;
        if (mode == Mode.NightOnly)
            target *= Mathf.Lerp(0.55f, 1f, YuukiClock.Night);
        float wobble = flicker > 0f
            ? 1f + (Mathf.PerlinNoise(seed, Time.time * 7f) - 0.5f) * flicker * 0.9f
                 + Mathf.Sin(Time.time * 23f + seed) * flicker * 0.05f
            : 1f;
        CurrentIntensity = Mathf.Max(0f, target * wobble);
        CurrentRadius = radius * (flicker > 0f ? 1f + (wobble - 1f) * 0.35f : 1f);
        if (on != lastOn && lampRenderer != null)
        {
            var sprite = on ? onSprite : offSprite;
            if (sprite != null) lampRenderer.sprite = sprite;
        }
        lastOn = on;
    }

    private void OnDrawGizmosSelected()
    {
        Gizmos.color = new Color(color.r, color.g, color.b, 0.6f);
        Gizmos.DrawWireSphere((Vector2)transform.position + offset, radius);
    }
}
