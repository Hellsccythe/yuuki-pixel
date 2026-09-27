using System.Collections.Generic;
using UnityEngine;

// Outdoor atmosphere around the camera: drifting leaves, dust motes, the odd loose page
// and slow cloud shadows crossing the neighbourhood. Everything is built at runtime so the
// scene only stores sprite references.
public sealed class YuukiWindFx : MonoBehaviour
{
    public Camera followCamera;
    public Rect mapBounds = new Rect(0, 0, 48, 36);
    public Sprite[] leaves = new Sprite[0];
    public Sprite dust;
    public Sprite paper;
    public Sprite cloud;
    [Min(0)] public int cloudCount = 4;

    private readonly List<ParticleSystem> systems = new List<ParticleSystem>();
    private readonly List<Transform> clouds = new List<Transform>();
    private readonly List<float> cloudSpeed = new List<float>();

    private void Start()
    {
        if (followCamera == null) followCamera = Camera.main;
        foreach (var leaf in leaves)
            systems.Add(Create("Folhas", leaf, 1.2f, 7f, new Vector2(0.11f, 0.17f), 0.9f, true));
        if (dust != null) systems.Add(Create("Poeira", dust, 9f, 5f, new Vector2(0.04f, 0.07f), 0.55f, false));
        if (paper != null) systems.Add(Create("Paginas soltas", paper, 0.12f, 9f, new Vector2(0.2f, 0.24f), 1f, true));
        for (int i = 0; i < cloudCount && cloud != null; i++)
        {
            var go = new GameObject("Sombra de nuvem " + i);
            go.transform.SetParent(transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = cloud;
            sr.color = new Color(1, 1, 1, 0.13f + 0.05f * (i % 2));
            sr.sortingOrder = 90;
            go.transform.localScale = Vector3.one * Random.Range(0.8f, 1.3f);
            go.transform.position = new Vector3(Random.Range(mapBounds.xMin, mapBounds.xMax),
                Random.Range(mapBounds.yMin, mapBounds.yMax), 0);
            clouds.Add(go.transform);
            cloudSpeed.Add(Random.Range(0.35f, 0.6f));
        }
    }

    private ParticleSystem Create(string label, Sprite sprite, float rate, float lifetime, Vector2 size,
        float alpha, bool spin)
    {
        var go = new GameObject(label);
        go.transform.SetParent(transform, false);
        var ps = go.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);

        var main = ps.main;
        main.duration = 10f;
        main.loop = true;
        main.startLifetime = new ParticleSystem.MinMaxCurve(lifetime * 0.7f, lifetime);
        main.startSpeed = 0f;
        main.startSize = new ParticleSystem.MinMaxCurve(size.x, size.y);
        main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
        main.startColor = new Color(1, 1, 1, alpha);
        main.simulationSpace = ParticleSystemSimulationSpace.World;
        main.maxParticles = 200;
        main.gravityModifier = 0f;

        var emission = ps.emission;
        emission.rateOverTime = rate;

        // Spawn along the upwind (west) side and a bit everywhere across the view.
        var shape = ps.shape;
        shape.shapeType = ParticleSystemShapeType.Box;
        shape.scale = new Vector3(26f, 14f, 0.1f);

        var velocity = ps.velocityOverLifetime;
        velocity.enabled = true;
        velocity.space = ParticleSystemSimulationSpace.World;
        velocity.x = new ParticleSystem.MinMaxCurve(0.9f * YuukiWind.Direction, 2.6f * YuukiWind.Direction);
        velocity.y = new ParticleSystem.MinMaxCurve(-0.35f, 0.25f);
        velocity.z = new ParticleSystem.MinMaxCurve(0f, 0f);

        var noise = ps.noise;
        noise.enabled = true;
        noise.strength = spin ? 0.8f : 0.35f;
        noise.frequency = 0.35f;
        noise.scrollSpeed = 0.4f;

        if (spin)
        {
            var rotation = ps.rotationOverLifetime;
            rotation.enabled = true;
            rotation.z = new ParticleSystem.MinMaxCurve(-3f, 3f);
        }

        var color = ps.colorOverLifetime;
        color.enabled = true;
        var gradient = new Gradient();
        gradient.SetKeys(
            new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
            new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.12f), new GradientAlphaKey(1f, 0.8f),
                    new GradientAlphaKey(0f, 1f) });
        color.color = gradient;

        var renderer = go.GetComponent<ParticleSystemRenderer>();
        var material = new Material(Shader.Find("Sprites/Default"));
        material.mainTexture = sprite.texture;
        renderer.material = material;
        renderer.sortingOrder = 100;
        renderer.renderMode = ParticleSystemRenderMode.Billboard;

        ps.Play();
        return ps;
    }

    private void LateUpdate()
    {
        if (followCamera == null) return;
        Vector3 c = followCamera.transform.position;
        float strength = YuukiWind.Strength(c.x);
        foreach (var ps in systems)
        {
            // Emitter trails slightly upwind so particles cross the whole screen.
            ps.transform.position = new Vector3(c.x - 3f * YuukiWind.Direction, c.y, 0f);
            var emission = ps.emission;
            var main = ps.main;
            emission.rateOverTimeMultiplier = Mathf.Lerp(0.35f, 1.6f, strength) * BaseRate(ps);
            main.simulationSpeed = Mathf.Lerp(0.75f, 1.35f, strength);
        }
        for (int i = 0; i < clouds.Count; i++)
        {
            var t = clouds[i];
            Vector3 p = t.position + new Vector3(cloudSpeed[i] * YuukiWind.Direction, 0.05f, 0) * Time.deltaTime;
            if (p.x > mapBounds.xMax + 10f) p.x = mapBounds.xMin - 10f;
            if (p.y > mapBounds.yMax + 6f) p.y = mapBounds.yMin - 6f;
            t.position = p;
        }
    }

    private readonly Dictionary<ParticleSystem, float> baseRates = new Dictionary<ParticleSystem, float>();

    private float BaseRate(ParticleSystem ps)
    {
        if (!baseRates.TryGetValue(ps, out float rate))
        {
            rate = ps.emission.rateOverTimeMultiplier;
            baseRates[ps] = rate;
        }
        return rate;
    }
}
