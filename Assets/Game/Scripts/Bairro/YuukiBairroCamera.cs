using UnityEngine;

// Smooth follow clamped to the current area. Small interiors are centred on screen.
[RequireComponent(typeof(Camera))]
public sealed class YuukiBairroCamera : MonoBehaviour
{
    public Transform target;
    [SerializeField, Min(0f)] private float smoothTime = 0.12f;
    [SerializeField] private float lookAhead = 0.35f;

    private Camera cam;
    private Rect bounds = new Rect(0, 0, 48, 36);
    private Vector3 velocity;

    private void Awake()
    {
        cam = GetComponent<Camera>();
    }

    public void SetBounds(Rect value, Color background)
    {
        bounds = value;
        if (cam == null) cam = GetComponent<Camera>();
        cam.backgroundColor = background;
    }

    public void Snap()
    {
        if (target == null) return;
        transform.position = Desired();
        velocity = Vector3.zero;
    }

    private void LateUpdate()
    {
        if (target == null) return;
        transform.position = Vector3.SmoothDamp(transform.position, Desired(), ref velocity, smoothTime);
    }

    private Vector3 Desired()
    {
        if (cam == null) cam = GetComponent<Camera>();
        float halfH = cam.orthographicSize, halfW = halfH * cam.aspect;
        // Aim at the upper body rather than the feet.
        Vector2 p = (Vector2)target.position + new Vector2(0, lookAhead);
        float x = bounds.width <= halfW * 2 ? bounds.center.x : Mathf.Clamp(p.x, bounds.xMin + halfW, bounds.xMax - halfW);
        float y = bounds.height <= halfH * 2 ? bounds.center.y : Mathf.Clamp(p.y, bounds.yMin + halfH, bounds.yMax - halfH);
        return new Vector3(x, y, -10f);
    }
}
