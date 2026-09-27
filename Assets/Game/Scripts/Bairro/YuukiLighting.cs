using System.Collections.Generic;
using UnityEngine;

// Darkness overlay in front of the camera. Outdoors it follows the clock (day, dusk,
// night); in the dungeon it stays dark all the time. The nearest lights are sent to the
// Yuuki/Darkness shader every frame.
[RequireComponent(typeof(SpriteRenderer))]
public sealed class YuukiLighting : MonoBehaviour
{
    private const int MaxLights = 32;

    public Camera target;
    public bool followClock = true;
    public Color fixedAmbient = new Color(0.01f, 0.01f, 0.02f, 0.9f); // used when not following the clock
    [Range(0, 12)] public int steps = 8;
    [Range(0f, 1f)] public float glowStrength = 0.2f;

    private SpriteRenderer overlay;
    private Material material;
    private readonly Vector4[] lights = new Vector4[MaxLights];
    private readonly Vector4[] colors = new Vector4[MaxLights];
    private readonly List<YuukiLight> visible = new List<YuukiLight>();

    private static readonly int LightsId = Shader.PropertyToID("_Lights");
    private static readonly int ColorsId = Shader.PropertyToID("_LightColors");
    private static readonly int CountId = Shader.PropertyToID("_LightCount");
    private static readonly int AmbientId = Shader.PropertyToID("_Ambient");
    private static readonly int StepsId = Shader.PropertyToID("_Steps");
    private static readonly int GlowId = Shader.PropertyToID("_GlowStrength");

    public Color CurrentAmbient { get; private set; }

    private void Awake()
    {
        overlay = GetComponent<SpriteRenderer>();
        if (overlay.sharedMaterial == null || overlay.sharedMaterial.shader.name != "Yuuki/Darkness")
        {
            var shader = Shader.Find("Yuuki/Darkness");
            if (shader != null) overlay.sharedMaterial = new Material(shader);
        }
        // Work on an instance so the material asset in the project is never modified.
        material = overlay.material;
        overlay.sortingOrder = 1000;
        if (target == null) target = GetComponentInParent<Camera>() ?? Camera.main;
    }

    private void LateUpdate()
    {
        if (target == null || material == null) return;
        // Cover the whole view, whatever the zoom.
        float h = target.orthographicSize * 2f + 2f;
        float w = h * target.aspect + 2f;
        var size = overlay.sprite != null ? (Vector2)overlay.sprite.bounds.size : Vector2.one;
        transform.position = new Vector3(target.transform.position.x, target.transform.position.y, 0f);
        transform.localScale = new Vector3(w / size.x, h / size.y, 1f);

        CurrentAmbient = followClock ? YuukiClock.Ambient : fixedAmbient;
        overlay.enabled = CurrentAmbient.a > 0.004f;
        if (!overlay.enabled) return;

        Vector2 center = target.transform.position;
        float reach = Mathf.Max(w, h) * 0.75f;
        visible.Clear();
        foreach (var light in YuukiLight.Active)
        {
            if (light.CurrentIntensity <= 0.01f) continue;
            if (Vector2.Distance(light.Position, center) - light.CurrentRadius > reach) continue;
            visible.Add(light);
        }
        visible.Sort((a, b) => Vector2.SqrMagnitude(a.Position - center).CompareTo(Vector2.SqrMagnitude(b.Position - center)));
        int count = Mathf.Min(MaxLights, visible.Count);
        for (int i = 0; i < MaxLights; i++)
        {
            if (i < count)
            {
                var l = visible[i];
                lights[i] = new Vector4(l.Position.x, l.Position.y, l.CurrentRadius, l.CurrentIntensity);
                colors[i] = new Vector4(l.color.r, l.color.g, l.color.b, 1f);
            }
            else
            {
                lights[i] = Vector4.zero;
                colors[i] = Vector4.zero;
            }
        }
        material.SetVectorArray(LightsId, lights);
        material.SetVectorArray(ColorsId, colors);
        material.SetFloat(CountId, count);
        material.SetColor(AmbientId, CurrentAmbient);
        material.SetFloat(StepsId, steps);
        material.SetFloat(GlowId, glowStrength);
    }
}
