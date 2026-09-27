using UnityEngine;

// Walk-in doorway: stepping on the trigger moves the player to another area of the map.
[RequireComponent(typeof(Collider2D))]
public sealed class YuukiPortal : MonoBehaviour
{
    public Vector2 target;
    public string areaId;

    private static float cooldownUntil;

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (Time.time < cooldownUntil || YuukiBairro.Instance == null) return;
        if (other.GetComponentInParent<YuukiPlayerTopDown>() == null) return;
        cooldownUntil = Time.time + 0.8f;
        YuukiBairro.Instance.Travel(target, areaId);
    }
}
