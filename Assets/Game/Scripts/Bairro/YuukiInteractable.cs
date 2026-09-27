using System.Collections.Generic;
using UnityEngine;

// Something Yuuki can use with F when standing next to it (signs, bookshelves, stairs...).
public abstract class YuukiInteractable : MonoBehaviour
{
    public string prompt = "Examinar";
    public Vector2 point;            // interaction spot relative to the object (feet level)
    [Min(0.2f)] public float radius = 1.1f;

    public static readonly List<YuukiInteractable> Active = new List<YuukiInteractable>();

    public Vector2 Point => (Vector2)transform.position + point;

    protected virtual void OnEnable() { Active.Add(this); }
    protected virtual void OnDisable() { Active.Remove(this); }

    public virtual bool Available => true;
    public abstract void Interact();

    private void OnDrawGizmosSelected()
    {
        Gizmos.color = new Color(0.4f, 0.9f, 1f, 0.7f);
        Gizmos.DrawWireSphere(Point, radius);
    }
}
