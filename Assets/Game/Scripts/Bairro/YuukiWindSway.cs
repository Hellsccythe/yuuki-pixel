using UnityEngine;

// Rotates the sprite around its pivot: bottom pivot (trees, weeds) bends with the wind,
// top pivot (laundry on the clothesline) swings.
public sealed class YuukiWindSway : MonoBehaviour
{
    public float amplitude = 1.2f;   // degrees at full strength
    public bool hanging;             // pivot on top (laundry)

    private float phase;
    private float baseAngle;

    private void Start()
    {
        phase = transform.position.x * 1.7f + transform.position.y * 0.9f;
        baseAngle = transform.localEulerAngles.z;
    }

    private void Update()
    {
        float s = YuukiWind.Strength(transform.position.x);
        float flutter = Mathf.Sin(Time.time * (hanging ? 3.1f : 2.2f) + phase) * (0.25f + s * 0.35f);
        float angle = amplitude * (s * 0.85f + flutter * 0.4f);
        // A bottom-pivoted plant leans east with a negative (clockwise) rotation,
        // a hanging cloth swings its lower edge east with a positive one.
        transform.localRotation = Quaternion.Euler(0, 0, baseAngle + (hanging ? angle : -angle) * YuukiWind.Direction);
    }
}
