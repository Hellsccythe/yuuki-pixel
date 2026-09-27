using UnityEngine;

// Edge of a modular map. Confirmation freezes movement until the player chooses.
[RequireComponent(typeof(Collider2D))]
public sealed class YuukiMapExit : MonoBehaviour
{
    public string label;
    public string targetMap;   // scene name, e.g. "Bairro_Moradias"
    public Vector2 target;     // arrival point in the target map

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (YuukiBairro.Instance == null || other.GetComponentInParent<YuukiPlayerTopDown>() == null) return;
        if (!string.IsNullOrEmpty(targetMap) && Application.CanStreamedLevelBeLoaded(targetMap))
            YuukiBairro.Instance.RequestMapChange(label, targetMap, target);
        else
            YuukiBairro.Instance.Toast(label);
    }
}
