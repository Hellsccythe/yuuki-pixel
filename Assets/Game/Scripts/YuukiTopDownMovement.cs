using UnityEngine;

[RequireComponent(typeof(Rigidbody2D), typeof(Animator))]
public sealed class YuukiTopDownMovement : MonoBehaviour
{
    public bool InputBlocked { get; set; }
    private Rigidbody2D body;
    private Animator animator;
    private Vector2 direction;
    private bool running, facingLeft;
    private Vector2 previousPosition;
    private void Awake()
    {
        body = GetComponent<Rigidbody2D>();
        animator = GetComponent<Animator>();
        body.gravityScale = 0;
        body.freezeRotation = true;
        previousPosition = body.position;
    }
    private void Update()
    {
        direction = InputBlocked ? Vector2.zero : new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical")).normalized;
        running = !InputBlocked && (Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift));
        if (direction.x < 0) facingLeft = true;
        else if (direction.x > 0) facingLeft = false;
        // Front/back drawings are intentionally deferred; preserve anatomical wing colors.
        animator.SetBool("FacingLeft", facingLeft);
        animator.SetBool("Running", running && direction.sqrMagnitude > 0);
        animator.SetBool("Grounded", true);
        animator.SetFloat("HorizontalSpeed", direction.magnitude);
    }
    private void FixedUpdate()
    {
        bool moved = (body.position - previousPosition).sqrMagnitude > 0.000001f;
        animator.SetBool("Moving", !InputBlocked && direction.sqrMagnitude > 0 && moved);
        previousPosition = body.position;
        body.linearVelocity = direction * (running ? 2.65f : 1.55f);
    }
    public void Teleport(Vector2 position)
    {
        if (body == null) body = GetComponent<Rigidbody2D>();
        body.position = position;
        transform.position = position;
        body.linearVelocity = Vector2.zero;
        previousPosition = position;
    }
}
