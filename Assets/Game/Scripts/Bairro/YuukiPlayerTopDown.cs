using UnityEngine;

// Stardew-style free movement on X and Y. There is no gravity or ground check: holes are
// blockers on the floor, and a future jump will temporarily ignore them instead of
// launching the character upwards.
[RequireComponent(typeof(Rigidbody2D))]
public sealed class YuukiPlayerTopDown : MonoBehaviour
{
    [SerializeField, Min(0f)] private float walkSpeed = 2.8f;
    [SerializeField, Min(0f)] private float runSpeed = 4.6f;
    [SerializeField] private Animator animator;

    private bool inputBlocked;
    public bool InputBlocked
    {
        get => inputBlocked;
        set
        {
            inputBlocked = value;
            if (!value) return;
            direction = Vector2.zero;
            Velocity = Vector2.zero;
            if (body != null) body.linearVelocity = Vector2.zero;
            if (animator != null) { animator.SetBool("Moving", false); animator.SetBool("Running", false); }
        }
    }
    public bool FacingLeft { get; private set; }
    public Vector2 Velocity { get; private set; }

    private Rigidbody2D body;
    private Vector2 direction;
    private bool running;
    private YuukiRpgAnimation rpgAnimation;

    private void Awake()
    {
        body = GetComponent<Rigidbody2D>();
        body.gravityScale = 0f;
        body.freezeRotation = true;
        if (animator == null) animator = GetComponentInChildren<Animator>();
        rpgAnimation = GetComponent<YuukiRpgAnimation>();
    }

    private void Update()
    {
        Vector2 input = InputBlocked
            ? Vector2.zero
            : new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
        // Same speed in every direction, diagonals included.
        direction = input.sqrMagnitude > 1f ? input.normalized : input;
        running = !InputBlocked && (Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift));

        // Retained for legacy side-view consumers; the RPG animation also faces up/down.
        if (direction.x < -0.01f) FacingLeft = true;
        else if (direction.x > 0.01f) FacingLeft = false;

        if (rpgAnimation != null)
        {
            rpgAnimation.Tick(direction, running, Time.deltaTime);
            return;
        }

        if (animator == null) return;
        bool moving = direction.sqrMagnitude > 0.0001f;
        animator.SetBool("FacingLeft", FacingLeft);
        animator.SetBool("Moving", moving);
        animator.SetBool("Running", running && moving);
        animator.SetBool("Grounded", true);
        animator.SetFloat("HorizontalSpeed", direction.magnitude);
    }

    private void FixedUpdate()
    {
        Velocity = InputBlocked ? Vector2.zero : direction * (running ? runSpeed : walkSpeed);
#if UNITY_6000_0_OR_NEWER
        body.linearVelocity = Velocity;
#else
        body.velocity = Velocity;
#endif
    }

    public void Teleport(Vector2 position)
    {
        if (body == null) body = GetComponent<Rigidbody2D>();
        body.position = position;
        transform.position = new Vector3(position.x, position.y, transform.position.z);
#if UNITY_6000_0_OR_NEWER
        body.linearVelocity = Vector2.zero;
#else
        body.velocity = Vector2.zero;
#endif
    }
}
