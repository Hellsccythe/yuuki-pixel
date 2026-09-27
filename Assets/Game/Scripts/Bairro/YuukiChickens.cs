using System.Collections.Generic;
using UnityEngine;

// A few chickens scratching around a spot. They wander, peck and scurry away from Yuuki,
// then drift back to their yard.
public sealed class YuukiChickens : MonoBehaviour
{
    public Sprite[] frames = new Sprite[0]; // idle, peck, walk A, walk B
    [Min(1)] public int count = 3;
    [Min(0.2f)] public float radius = 1.6f;
    [Min(0f)] public float fleeDistance = 1.6f;
    public Transform player;

    private sealed class Hen
    {
        public Transform transform;
        public SpriteRenderer renderer;
        public Vector2 target;
        public float speed;
        public float nextDecision;
        public float animTime;
        public bool pecking;
    }

    private readonly List<Hen> hens = new List<Hen>();

    private void Start()
    {
        for (int i = 0; i < count; i++)
        {
            var go = new GameObject("Galinha " + i);
            go.transform.SetParent(transform, false);
            go.transform.position = Home();
            var sr = go.AddComponent<SpriteRenderer>();
            sr.spriteSortPoint = SpriteSortPoint.Pivot;
            sr.sprite = frames.Length > 0 ? frames[0] : null;
            var hen = new Hen { transform = go.transform, renderer = sr, target = go.transform.position };
            hen.nextDecision = Time.time + Random.Range(0f, 2f);
            hens.Add(hen);
        }
    }

    private Vector2 Home()
    {
        return (Vector2)transform.position + Random.insideUnitCircle * new Vector2(radius, radius * 0.6f);
    }

    private void Update()
    {
        if (frames.Length < 4) return;
        foreach (var hen in hens)
        {
            Vector2 pos = hen.transform.position;
            if (player != null)
            {
                Vector2 away = pos - (Vector2)player.position;
                if (away.magnitude < fleeDistance)
                {
                    // Scurry off, but never too far from the yard.
                    Vector2 flee = pos + away.normalized * 1.4f;
                    Vector2 fromHome = flee - (Vector2)transform.position;
                    hen.target = (Vector2)transform.position + Vector2.ClampMagnitude(fromHome, radius * 1.6f);
                    hen.speed = 2.6f;
                    hen.pecking = false;
                    hen.nextDecision = Time.time + 1.2f;
                }
            }
            if (Time.time > hen.nextDecision)
            {
                float roll = Random.value;
                if (roll < 0.45f)
                {
                    hen.pecking = true;
                    hen.target = pos;
                    hen.nextDecision = Time.time + Random.Range(0.8f, 2.4f);
                }
                else
                {
                    hen.pecking = false;
                    hen.target = Home();
                    hen.speed = Random.Range(0.5f, 0.9f);
                    hen.nextDecision = Time.time + Random.Range(1.5f, 3.5f);
                }
            }
            Vector2 to = hen.target - pos;
            bool walking = to.magnitude > 0.03f;
            if (walking)
            {
                hen.transform.position = pos + Vector2.ClampMagnitude(to, hen.speed * Time.deltaTime);
                if (Mathf.Abs(to.x) > 0.01f) hen.renderer.flipX = to.x < 0;
                hen.animTime += Time.deltaTime * 9f * Mathf.Max(1f, hen.speed);
                hen.renderer.sprite = frames[2 + ((int)hen.animTime % 2)];
            }
            else if (hen.pecking)
            {
                hen.animTime += Time.deltaTime * 4f;
                hen.renderer.sprite = frames[((int)hen.animTime % 3 == 0) ? 1 : 0];
            }
            else
            {
                hen.renderer.sprite = frames[0];
            }
        }
    }
}
