using UnityEngine;

[RequireComponent(typeof(Camera))]
public sealed class YuukiWorldCamera : MonoBehaviour
{
    public Transform target;
    private float mapWidth = 30.72f, mapHeight = 20.48f;
    public void SetBounds(float width, float height) { mapWidth = width; mapHeight = height; Snap(); }
    public void Snap()
    {
        if (target == null) return;
        Camera camera = GetComponent<Camera>();
        float halfHeight = camera.orthographicSize, halfWidth = halfHeight * camera.aspect;
        float x = mapWidth <= halfWidth * 2 ? mapWidth / 2 : Mathf.Clamp(target.position.x, halfWidth, mapWidth - halfWidth);
        float y = mapHeight <= halfHeight * 2 ? -mapHeight / 2 : Mathf.Clamp(target.position.y + 0.45f, -mapHeight + halfHeight, -halfHeight);
        transform.position = new Vector3(x, y, -10);
    }
    private void LateUpdate() { Snap(); }
}
