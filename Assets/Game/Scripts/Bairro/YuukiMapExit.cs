using UnityEngine;

// Edge of a modular map. Walking into it loads the neighbouring map when that scene is in the
// Build Settings; otherwise it only says the place is not ready yet ("em breve").
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
            YuukiBairro.Instance.LoadMap(targetMap, target);
        else
            YuukiBairro.Instance.Toast(label);
    }
}
