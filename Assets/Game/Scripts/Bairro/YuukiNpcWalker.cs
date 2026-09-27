using UnityEngine;

// Ambient villager: patrols between points or wanders inside a rectangle, pausing now and
// then. Stops instead of pushing Yuuki and turns to look at her when she is close.
[RequireComponent(typeof(Rigidbody2D))]
public sealed class YuukiNpcWalker : MonoBehaviour
{
    public enum Mode { Patrol, Wander }

    public Mode mode = Mode.Patrol;
    public Vector2[] points = new Vector2[0];
    public Rect wanderArea;
    [Min(0f)] public float speed = 1.2f;
    [Min(0f)] public float waitMin = 1f, waitMax = 3f;
    public SpriteRenderer spriteRenderer;
    public Sprite[] walkLeft = new Sprite[0];
    public Sprite[] walkRight = new Sprite[0];
    public Sprite idleLeft, idleRight;
    [Min(1f)] public float framesPerSecond = 8f;
    public Transform player;

    private Rigidbody2D body;
    private Vector2 target;
    private int index;
    private int step = 1;
    private float waitUntil;
    private float stuckTime;
    private bool facingLeft;
    private float animTime;
    private bool moving;

    private void Awake()
    {
        body = GetComponent<Rigidbody2D>();
        body.bodyType = RigidbodyType2D.Kinematic;
        body.interpolation = RigidbodyInterpolation2D.Interpolate;
        if (spriteRenderer == null) spriteRenderer = GetComponentInChildren<SpriteRenderer>();
    }

    private void Start()
    {
        target = body.position;
        waitUntil = Time.time + Random.Range(0f, waitMax);
        facingLeft = Random.value < 0.5f;
    }

    private void FixedUpdate()
    {
        moving = false;
        if (Time.time < waitUntil) return;

        Vector2 pos = body.position;
        Vector2 to = target - pos;
        if (to.magnitude < 0.05f)
        {
            PickNext();
            waitUntil = Time.time + Random.Range(waitMin, waitMax);
            return;
        }
        Vector2 dir = to.normalized;
        // Wait politely if Yuuki stands in the way.
        if (player != null)
        {
            Vector2 toPlayer = (Vector2)player.position - pos;
            if (toPlayer.magnitude < 0.9f && Vector2.Dot(toPlayer.normalized, dir) > 0.3f)
            {
                stuckTime += Time.fixedDeltaTime;
                if (stuckTime > 2.5f) { PickNext(); stuckTime = 0; }
                return;
            }
        }
        stuckTime = 0;
        float stepLen = Mathf.Min(speed * Time.fixedDeltaTime, to.magnitude);
        body.MovePosition(pos + dir * stepLen);
        moving = true;
        if (Mathf.Abs(dir.x) > 0.15f) facingLeft = dir.x < 0;
    }

    private void PickNext()
    {
        if (mode == Mode.Wander || points.Length < 2)
        {
            target = new Vector2(Random.Range(wanderArea.xMin, wanderArea.xMax),
                Random.Range(wanderArea.yMin, wanderArea.yMax));
            return;
        }
        // Ping-pong along the patrol route.
        if (index + step >= points.Length || index + step < 0) step = -step;
        index += step;
        target = points[index];
    }

    private void Update()
    {
        if (spriteRenderer == null) return;
        if (!moving && player != null && Vector2.Distance(player.position, transform.position) < 2f)
            facingLeft = player.position.x < transform.position.x;
        Sprite[] frames = facingLeft ? walkLeft : walkRight;
        if (moving && frames.Length > 0)
        {
            animTime += Time.deltaTime * framesPerSecond * Mathf.Clamp(speed / 1.2f, 0.7f, 1.8f);
            spriteRenderer.sprite = frames[(int)animTime % frames.Length];
        }
        else
        {
            animTime = 0;
            spriteRenderer.sprite = facingLeft ? idleLeft : idleRight;
        }
    }

    private void OnDrawGizmosSelected()
    {
        Gizmos.color = new Color(1f, 0.8f, 0.2f, 0.8f);
        if (mode == Mode.Wander)
            Gizmos.DrawWireCube(wanderArea.center, wanderArea.size);
        for (int i = 0; i + 1 < points.Length; i++)
            Gizmos.DrawLine(points[i], points[i + 1]);
    }
}
