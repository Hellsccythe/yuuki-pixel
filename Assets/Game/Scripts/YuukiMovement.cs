using UnityEngine;

[RequireComponent(typeof(Rigidbody2D), typeof(Animator), typeof(SpriteRenderer))]
public sealed class YuukiMovement : MonoBehaviour
{
    [Header("Movement")]
    [SerializeField, Min(0f)] private float walkSpeed = 3f;
    [SerializeField, Min(0f)] private float runSpeed = 5f;
    [SerializeField, Min(0f)] private float jumpVelocity = 8f;

    [Header("Ground check")]
    [SerializeField] private Transform groundCheck;
    [SerializeField, Min(0.01f)] private float groundCheckRadius = 0.12f;
    [SerializeField] private LayerMask groundLayers;

    private Rigidbody2D body;
    private Animator animator;
    private float horizontal;
    private bool running;
    private bool grounded;
    private bool facingLeft;

    private void Awake()
    {
        body = GetComponent<Rigidbody2D>();
        animator = GetComponent<Animator>();
        body.freezeRotation = true;
    }

    private void Update()
    {
        horizontal = Input.GetAxisRaw("Horizontal");
        running = Mathf.Abs(horizontal) > 0.01f &&
                  (Input.GetKey(KeyCode.LeftShift) || Input.GetKey(KeyCode.RightShift));

        Vector2 checkPosition = groundCheck != null
            ? (Vector2)groundCheck.position
            : (Vector2)transform.position + Vector2.down * 0.5f;
        grounded = body.linearVelocity.y <= 0.1f &&
                   Physics2D.OverlapCircle(checkPosition, groundCheckRadius, groundLayers) != null;

        if (horizontal < -0.01f)
            facingLeft = true;
        else if (horizontal > 0.01f)
            facingLeft = false;

        animator.SetFloat("HorizontalSpeed", Mathf.Abs(horizontal));
        animator.SetBool("Moving", Mathf.Abs(horizontal) > 0.01f);
        animator.SetBool("Running", running);
        animator.SetBool("FacingLeft", facingLeft);

        if (grounded && Input.GetButtonDown("Jump"))
        {
            body.linearVelocity = new Vector2(body.linearVelocity.x, jumpVelocity);
            grounded = false;
            animator.SetTrigger("Jump");
        }
        animator.SetBool("Grounded", grounded);
        animator.SetFloat("JumpProgress", Mathf.Clamp01(
            (jumpVelocity - body.linearVelocity.y) / (2f * Mathf.Max(jumpVelocity, 0.01f))));
    }

    private void FixedUpdate()
    {
        float speed = running ? runSpeed : walkSpeed;
        body.linearVelocity = new Vector2(horizontal * speed, body.linearVelocity.y);
    }

    private void OnDrawGizmosSelected()
    {
        Vector3 position = groundCheck != null
            ? groundCheck.position
            : transform.position + Vector3.down * 0.5f;
        Gizmos.color = Color.yellow;
        Gizmos.DrawWireSphere(position, groundCheckRadius);
    }
}
