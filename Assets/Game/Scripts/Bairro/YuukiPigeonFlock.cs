using System.Collections.Generic;
using UnityEngine;

// A few pigeons pecking the street. They take off when Yuuki gets close and quietly come
// back some time later.
public sealed class YuukiPigeonFlock : MonoBehaviour
{
    public Sprite[] frames = new Sprite[0]; // idle, peck, wings up, wings down
    [Min(1)] public int count = 3;
    [Min(0f)] public float scareDistance = 2.2f;
    public Transform player;

    private sealed class Bird
    {
        public Transform transform;
        public SpriteRenderer renderer;
        public Vector2 home;
        public Vector2 velocity;
        public float nextPeck;
        public bool flying;
        public float flightTime;
    }

    private readonly List<Bird> birds = new List<Bird>();
    private float returnAt = -1f;

    private void Start()
    {
        for (int i = 0; i < count; i++)
        {
            var go = new GameObject("Pombo " + i);
            go.transform.SetParent(transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.spriteSortPoint = SpriteSortPoint.Pivot;
            var bird = new Bird { transform = go.transform, renderer = sr };
            bird.home = (Vector2)transform.position + Random.insideUnitCircle * new Vector2(0.9f, 0.45f);
            birds.Add(bird);
            Land(bird);
        }
    }

    private void Land(Bird bird)
    {
        bird.flying = false;
        bird.transform.position = bird.home;
        bird.renderer.sprite = frames.Length > 0 ? frames[0] : null;
        bird.renderer.flipX = Random.value < 0.5f;
        bird.renderer.color = Color.white;
        bird.renderer.sortingOrder = 0;
        bird.nextPeck = Time.time + Random.Range(0.3f, 2f);
    }

    private void Update()
    {
        if (frames.Length < 4) return;
        bool scared = player != null && Vector2.Distance(player.position, transform.position) < scareDistance;
        bool allAway = true;
        foreach (var bird in birds)
        {
            if (!bird.flying)
            {
                allAway = false;
                if (scared)
                {
                    bird.flying = true;
                    bird.flightTime = 0;
                    Vector2 away = ((Vector2)bird.transform.position - (Vector2)player.position).normalized;
                    bird.velocity = new Vector2(away.x * 3.2f + Random.Range(-0.6f, 0.6f), 2.6f + Random.Range(0f, 1.2f));
                    bird.renderer.flipX = bird.velocity.x < 0;
                    bird.renderer.sortingOrder = 120; // above roofs while in the air
                    continue;
                }
                if (Time.time > bird.nextPeck)
                {
                    bool peck = bird.renderer.sprite == frames[0];
                    bird.renderer.sprite = peck ? frames[1] : frames[0];
                    bird.nextPeck = Time.time + (peck ? Random.Range(0.15f, 0.35f) : Random.Range(0.6f, 2.4f));
                    if (!peck && Random.value < 0.3f)
                    {
                        // Small hop around the spot.
                        Vector2 hop = Random.insideUnitCircle * 0.25f;
                        Vector2 next = Vector2.ClampMagnitude((Vector2)bird.transform.position + hop - bird.home, 0.6f);
                        bird.transform.position = bird.home + next;
                        bird.renderer.flipX = hop.x < 0;
                    }
                }
            }
            else
            {
                bird.flightTime += Time.deltaTime;
                bird.transform.position += (Vector3)(bird.velocity * Time.deltaTime);
                bird.renderer.sprite = ((int)(bird.flightTime * 12f) % 2 == 0) ? frames[2] : frames[3];
                bird.renderer.color = new Color(1, 1, 1, Mathf.Clamp01(2.4f - bird.flightTime));
                if (bird.flightTime < 2.4f) allAway = false;
            }
        }
        if (allAway && returnAt < 0) returnAt = Time.time + Random.Range(10f, 18f);
        if (returnAt > 0 && Time.time > returnAt && !scared)
        {
            returnAt = -1f;
            foreach (var bird in birds) Land(bird);
        }
    }
}
