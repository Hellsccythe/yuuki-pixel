using UnityEngine;

// One shared breeze for the whole map. Gusts travel from west to east, so trees, weeds,
// laundry, leaves and smoke all react to the same wave a moment after one another.
public static class YuukiWind
{
    public const float Direction = 1f; // +1 = blowing east

    // 0..1 strength at a given x position.
    public static float Strength(float x)
    {
        float t = Time.time;
        float wave = Mathf.Sin(t * 0.55f - x * 0.09f) * 0.5f + 0.5f;
        float envelope = Mathf.Sin(t * 0.11f + 1.3f) * 0.5f + 0.5f;
        float flutter = Mathf.PerlinNoise(t * 0.35f, x * 0.05f);
        return Mathf.Clamp01(0.18f + wave * envelope * 0.62f + flutter * 0.2f);
    }
}
