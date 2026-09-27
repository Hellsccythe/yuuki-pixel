using UnityEngine;

// Carries the arrival point across a scene load between two modular maps.
public static class YuukiMapTravel
{
    private static bool pending;
    private static Vector2 spawn;

    public static void Set(Vector2 arrival)
    {
        spawn = arrival;
        pending = true;
    }

    public static bool Consume(out Vector2 arrival)
    {
        arrival = spawn;
        bool had = pending;
        pending = false;
        return had;
    }
}
