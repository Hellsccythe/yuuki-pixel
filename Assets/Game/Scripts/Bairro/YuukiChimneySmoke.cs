using UnityEngine;

// Thin smoke from a chimney, bent by the shared breeze.
public sealed class YuukiChimneySmoke : MonoBehaviour
{
    public Sprite puff;
    public Color tint = new Color(0.9f, 0.88f, 0.86f, 0.55f);

    private ParticleSystem ps;

    private void Start()
    {
        if (puff == null) return;
        ps = gameObject.AddComponent<ParticleSystem>();
        ps.Stop(true, ParticleSystemStopBehavior.StopEmittingAndClear);
        var main = ps.main;
        main.loop = true;
        main.startLifetime = new ParticleSystem.MinMaxCurve(2.6f, 3.8f);
        main.startSpeed = 0f;
        main.startSize = new ParticleSystem.MinMaxCurve(0.28f, 0.42f);
        main.startColor = tint;
        main.simulationSpace = ParticleSystemSimulationSpace.World;
        main.maxParticles = 60;

        var emission = ps.emission;
        emission.rateOverTime = 5f;

        var shape = ps.shape;
        shape.shapeType = ParticleSystemShapeType.Circle;
        shape.radius = 0.06f;

        var velocity = ps.velocityOverLifetime;
        velocity.enabled = true;
        velocity.space = ParticleSystemSimulationSpace.World;
        velocity.x = new ParticleSystem.MinMaxCurve(0.1f, 0.3f);
        velocity.y = new ParticleSystem.MinMaxCurve(0.45f, 0.7f);
        velocity.z = new ParticleSystem.MinMaxCurve(0f, 0f);

        var size = ps.sizeOverLifetime;
        size.enabled = true;
        size.size = new ParticleSystem.MinMaxCurve(1f, AnimationCurve.Linear(0, 0.6f, 1, 2.6f));

        var color = ps.colorOverLifetime;
        color.enabled = true;
        var gradient = new Gradient();
        gradient.SetKeys(
            new[] { new GradientColorKey(Color.white, 0f), new GradientColorKey(Color.white, 1f) },
            new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(1f, 0.15f), new GradientAlphaKey(0f, 1f) });
        color.color = gradient;

        var renderer = GetComponent<ParticleSystemRenderer>();
        var material = new Material(Shader.Find("Sprites/Default"));
        material.mainTexture = puff.texture;
        renderer.material = material;
        renderer.sortingOrder = 80;
        ps.Play();
    }

    private void Update()
    {
        if (ps == null) return;
        // Push the plume sideways with the gust passing over this roof.
        var force = ps.forceOverLifetime;
        force.enabled = true;
        force.space = ParticleSystemSimulationSpace.World;
        float s = YuukiWind.Strength(transform.position.x);
        force.x = new ParticleSystem.MinMaxCurve(s * 1.1f * YuukiWind.Direction);
        force.y = new ParticleSystem.MinMaxCurve(0f);
        force.z = new ParticleSystem.MinMaxCurve(0f);
    }
}
