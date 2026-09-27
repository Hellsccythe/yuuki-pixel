using UnityEngine;

// Edge of a modular map. Standing on it shows where it leads; walking on into the edge
// for a moment travels there (YuukiBairro handles the timing). Areas that don't exist yet
// only show their name as "em construção".
[RequireComponent(typeof(Collider2D))]
public sealed class YuukiMapExit : MonoBehaviour
{
    public string label;
    public string targetMap;   // scene name, e.g. "Bairro_Moradias"
    public Vector2 target;     // arrival point in the target map
    public Vector2 outward = Vector2.left; // direction that leaves the map

    public bool Ready => !string.IsNullOrEmpty(targetMap) && Application.CanStreamedLevelBeLoaded(targetMap);
    public Vector2 Outward => outward.sqrMagnitude > 0.01f ? outward.normalized : Vector2.left;

    private void OnTriggerEnter2D(Collider2D other)
    {
        if (YuukiBairro.Instance != null && other.GetComponentInParent<YuukiPlayerTopDown>() != null)
            YuukiBairro.Instance.EnterEdge(this);
    }

    private void OnTriggerExit2D(Collider2D other)
    {
        if (YuukiBairro.Instance != null && other.GetComponentInParent<YuukiPlayerTopDown>() != null)
            YuukiBairro.Instance.LeaveEdge(this);
    }
}
