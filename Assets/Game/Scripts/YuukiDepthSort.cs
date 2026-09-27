using UnityEngine;

[ExecuteAlways]
public sealed class YuukiDepthSort : MonoBehaviour
{
    private SpriteRenderer sprite;
    private void LateUpdate()
    {
        if (sprite == null) sprite = GetComponentInChildren<SpriteRenderer>();
        if (sprite != null) sprite.sortingOrder = Mathf.RoundToInt(-transform.position.y * 100f);
    }
}
