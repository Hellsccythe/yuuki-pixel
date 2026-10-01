using UnityEngine;

// Lives on Yuuki: picks the closest interactable in front of her and uses it with F.
[RequireComponent(typeof(YuukiPlayerTopDown))]
public sealed class YuukiInteractor : MonoBehaviour
{
    public static readonly KeyCode Key = KeyCode.F;

    public YuukiInteractable Current { get; private set; }

    private YuukiPlayerTopDown player;
    private YuukiRpgAnimation rpgAnimation;
    private Vector2 lastDirection = Vector2.down;

    private void Awake()
    {
        player = GetComponent<YuukiPlayerTopDown>();
        rpgAnimation = GetComponent<YuukiRpgAnimation>();
    }

    private void Update()
    {
        var map = YuukiBairro.Instance;
        bool free = map != null && !map.Blocking && !player.InputBlocked;
        Current = free ? FindBest() : null;
        if (Current != null && Input.GetKeyDown(Key))
            Current.Interact();
    }

    private Vector2 Facing()
    {
        if (player.Velocity.sqrMagnitude > 0.01f) lastDirection = player.Velocity.normalized;
        else if (rpgAnimation != null)
        {
            switch (rpgAnimation.Facing)
            {
                case "up": lastDirection = Vector2.up; break;
                case "down": lastDirection = Vector2.down; break;
                case "left": lastDirection = Vector2.left; break;
                case "right": lastDirection = Vector2.right; break;
            }
        }
        return lastDirection;
    }

    private YuukiInteractable FindBest()
    {
        Vector2 feet = transform.position;
        Vector2 facing = Facing();
        YuukiInteractable best = null;
        float bestScore = float.MaxValue;
        foreach (var item in YuukiInteractable.Active)
        {
            if (item == null || !item.Available) continue;
            var house=YuukiCutawayHouse.ActiveHouse;
            if(house!=null && !item.transform.IsChildOf(house.interior.transform)) continue;
            Vector2 to = item.Point - feet;
            float distance = to.magnitude;
            if (distance > item.radius) continue;
            // Prefer what she is looking at, but allow standing right on top of it.
            float facingPenalty = distance < 0.35f ? 0f : (1f - Vector2.Dot(to / distance, facing)) * 0.6f;
            float score = distance + facingPenalty;
            if (score < bestScore) { bestScore = score; best = item; }
        }
        return best;
    }
}
