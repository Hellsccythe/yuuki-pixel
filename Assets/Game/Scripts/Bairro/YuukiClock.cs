using UnityEngine;

// In-game time shared by every map (static, survives scene loads). One game minute lasts
// RealSecondsPerMinute real seconds, so a whole day takes about 17 minutes. The ambient
// light, street lamps and torches all read from here.
public static class YuukiClock
{
    public const float RealSecondsPerMinute = 0.7f;
    public const float StartHour = 7f;

    public static int Day { get; private set; } = 1;
    public static float Minutes { get; private set; } = StartHour * 60f; // 0..1440

    public static float Hour => Minutes / 60f;
    public static int HourInt => Mathf.FloorToInt(Minutes / 60f) % 24;
    public static int MinuteInt => Mathf.FloorToInt(Minutes) % 60;

    public static void Reset()
    {
        Day = 1;
        Minutes = StartHour * 60f;
    }

    public static void Tick(float realSeconds)
    {
        Minutes += realSeconds / RealSecondsPerMinute;
        while (Minutes >= 1440f) { Minutes -= 1440f; Day++; }
    }

    public static void Skip(float hours)
    {
        Minutes += hours * 60f;
        while (Minutes >= 1440f) { Minutes -= 1440f; Day++; }
        while (Minutes < 0f) { Minutes += 1440f; Day = Mathf.Max(1, Day - 1); }
    }

    public static string Period
    {
        get
        {
            float h = Hour;
            if (h < 5f) return "Madrugada";
            if (h < 12f) return "Manhã";
            if (h < 18f) return "Tarde";
            return "Noite";
        }
    }

    // Shown in the HUD, rounded to 10 minutes like Stardew Valley.
    public static string TimeText => $"{HourInt:00}:{(MinuteInt / 10) * 10:00}";

    // 0 = full day, 1 = deep night. Smooth dawn (5-7h) and dusk (17-20h).
    public static float Night
    {
        get
        {
            float h = Hour;
            if (h < 5f) return 1f;
            if (h < 7f) return 1f - Mathf.SmoothStep(0, 1, (h - 5f) / 2f);
            if (h < 17f) return 0f;
            if (h < 20f) return Mathf.SmoothStep(0, 1, (h - 17f) / 3f);
            return 1f;
        }
    }

    // Lamps and windows light up a bit before full dark and switch off after dawn.
    public static bool LampsOn
    {
        get
        {
            float h = Hour;
            return h >= 18.25f || h < 5.75f;
        }
    }

    // Ambient overlay: rgb = tint of the shadows, a = how much the scene is darkened.
    public static Color Ambient
    {
        get
        {
            float h = Hour;
            var night = new Color(0.03f, 0.05f, 0.14f, 0.66f);
            var dusk = new Color(0.36f, 0.16f, 0.07f, 0.24f);
            var dawn = new Color(0.22f, 0.14f, 0.24f, 0.28f);
            var day = new Color(0.36f, 0.16f, 0.07f, 0f);
            if (h < 5f) return night;
            if (h < 6.2f) return Color.Lerp(night, dawn, (h - 5f) / 1.2f);
            if (h < 7.5f) return Color.Lerp(dawn, day, (h - 6.2f) / 1.3f);
            if (h < 16.5f) return day;
            if (h < 18.2f) return Color.Lerp(day, dusk, (h - 16.5f) / 1.7f);
            if (h < 20f) return Color.Lerp(dusk, night, (h - 18.2f) / 1.8f);
            return night;
        }
    }
}
