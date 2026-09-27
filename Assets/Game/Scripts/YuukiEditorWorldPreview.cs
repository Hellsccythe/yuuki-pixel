using UnityEngine;

// The scene stays visible before Play; the controller owns a fresh copy at runtime.
public sealed class YuukiEditorWorldPreview : MonoBehaviour
{
    private void Awake() { gameObject.SetActive(false); Destroy(gameObject); }
}
