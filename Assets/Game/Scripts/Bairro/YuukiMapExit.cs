using UnityEngine;

// Edge of the modular map leading to a neighbouring map that does not exist yet.
// A blocker stands right behind the trigger; later this will load the next map.
[RequireComponent(typeof(Collider2D))]
public sealed class YuukiMapExit : MonoBehaviour
{
    public string label;
    public string targetMap;

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (YuukiBairro.Instance == null || other.GetComponentInParent<YuukiPlayerTopDown>() == null) return;
        YuukiBairro.Instance.Toast(label);
    }
}
