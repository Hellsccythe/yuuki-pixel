using UnityEngine;

// Shared look for every screen of the prototype (menu, pause, HUD, signs, books).
// Everything is drawn with IMGUI on a virtual canvas 720 units tall, so it scales
// with the window without extra assets.
public static class YuukiUI
{
    public const float Height = 720f;

    public static readonly Color Ink = new Color(0.94f, 0.91f, 0.84f);
    public static readonly Color Muted = new Color(0.64f, 0.63f, 0.57f);
    public static readonly Color Faint = new Color(0.42f, 0.42f, 0.38f);
    public static readonly Color Accent = new Color(0.90f, 0.74f, 0.44f);
    public static readonly Color PanelColor = new Color(0.075f, 0.068f, 0.06f, 0.9f);
    public static readonly Color Line = new Color(0.58f, 0.47f, 0.32f, 0.85f);

    private static Texture2D pixel, circle;
    private static GUIStyle[] styles;
    private static int styleFrame = -1;

    public static float Width => Screen.width * Height / Mathf.Max(1, Screen.height);

    public static Texture2D Pixel
    {
        get
        {
            if (pixel == null)
            {
                pixel = new Texture2D(1, 1) { hideFlags = HideFlags.HideAndDontSave };
                pixel.SetPixel(0, 0, Color.white);
                pixel.Apply();
            }
            return pixel;
        }
    }

    public static Texture2D Circle
    {
        get
        {
            if (circle == null)
            {
                const int size = 32;
                circle = new Texture2D(size, size) { hideFlags = HideFlags.HideAndDontSave, filterMode = FilterMode.Point };
                for (int y = 0; y < size; y++)
                    for (int x = 0; x < size; x++)
                    {
                        float d = Vector2.Distance(new Vector2(x + .5f, y + .5f), new Vector2(size / 2f, size / 2f));
                        circle.SetPixel(x, y, d <= size / 2f - .5f ? Color.white : Color.clear);
                    }
                circle.Apply();
            }
            return circle;
        }
    }

    // Call at the top of OnGUI; returns the canvas width.
    public static float Begin()
    {
        float scale = Screen.height / Height;
        GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, Vector3.one * scale);
        return Width;
    }

    public static void End() { GUI.matrix = Matrix4x4.identity; }

    public static void Fill(Rect rect, Color color)
    {
        var previous = GUI.color;
        GUI.color = color;
        GUI.DrawTexture(rect, Pixel);
        GUI.color = previous;
    }

    public static void Dot(Rect rect, Color color)
    {
        var previous = GUI.color;
        GUI.color = color;
        GUI.DrawTexture(rect, Circle);
        GUI.color = previous;
    }

    // Flat dark card with a thin warm rule at the top.
    public static void Panel(Rect rect, float alpha = 1f)
    {
        Fill(rect, new Color(PanelColor.r, PanelColor.g, PanelColor.b, PanelColor.a * alpha));
        Fill(new Rect(rect.x, rect.y, rect.width, 1.5f), new Color(Line.r, Line.g, Line.b, Line.a * alpha));
    }

    public static void Dim(float alpha)
    {
        Fill(new Rect(0, 0, Width, Height), new Color(0.02f, 0.02f, 0.025f, alpha));
    }

    public enum Size { Caption = 0, Small = 1, Body = 2, Large = 3, Title = 4, Display = 5, Huge = 6 }

    public static GUIStyle Style(Size size, TextAnchor anchor = TextAnchor.UpperLeft, bool wrap = false)
    {
        if (styles == null || styleFrame < 0)
        {
            styles = new GUIStyle[7];
            int[] sizes = { 13, 15, 19, 24, 34, 54, 96 };
            for (int i = 0; i < sizes.Length; i++)
            {
                styles[i] = new GUIStyle(GUI.skin.label) { fontSize = sizes[i], richText = true, clipping = TextClipping.Overflow };
                styles[i].normal.textColor = Ink;
            }
            styles[(int)Size.Title].fontStyle = FontStyle.Bold;
            styles[(int)Size.Huge].fontStyle = FontStyle.Bold;
            styleFrame = 1;
        }
        var style = styles[(int)size];
        style.alignment = anchor;
        style.wordWrap = wrap;
        return style;
    }

    public static void Text(Rect rect, string text, Size size, Color color, TextAnchor anchor = TextAnchor.UpperLeft,
        bool wrap = false, float alpha = 1f)
    {
        var style = Style(size, anchor, wrap);
        var previous = GUI.color;
        GUI.color = new Color(color.r, color.g, color.b, color.a * alpha);
        GUI.Label(rect, text, style);
        GUI.color = previous;
    }

    // Small key cap, e.g. [F]
    public static float Key(float x, float y, string key, float alpha = 1f)
    {
        float w = Mathf.Max(22, key.Length * 9 + 12);
        Fill(new Rect(x, y, w, 22), new Color(Ink.r, Ink.g, Ink.b, 0.92f * alpha));
        Text(new Rect(x, y, w, 22), key, Size.Caption, new Color(0.08f, 0.07f, 0.06f), TextAnchor.MiddleCenter, false, alpha);
        return w;
    }

    // Vertical list of options with a marker on the selected one. Returns the index clicked
    // with the mouse (or -1). Keyboard handling stays in the caller's Update.
    public static int List(Rect area, string[] items, int selected, float rowHeight = 44f, bool[] disabled = null)
    {
        int clicked = -1;
        for (int i = 0; i < items.Length; i++)
        {
            var row = new Rect(area.x, area.y + i * rowHeight, area.width, rowHeight - 6);
            bool off = disabled != null && i < disabled.Length && disabled[i];
            bool hover = row.Contains(Event.current.mousePosition) && !off;
            bool active = i == selected;
            if (active)
            {
                Fill(new Rect(row.x, row.y, row.width, row.height), new Color(1, 1, 1, 0.045f));
                Fill(new Rect(row.x, row.y + 6, 3, row.height - 12), Accent);
            }
            Color color = off ? Faint : active ? Ink : hover ? Ink : Muted;
            Text(new Rect(row.x + 18, row.y, row.width - 18, row.height), items[i], Size.Large, color, TextAnchor.MiddleLeft);
            if (!off && GUI.Button(row, GUIContent.none, GUIStyle.none)) clicked = i;
        }
        return clicked;
    }

    // Shared keyboard navigation for lists (W/S, arrows).
    public static int Navigate(int index, int count)
    {
        if (count <= 0) return 0;
        if (Input.GetKeyDown(KeyCode.W) || Input.GetKeyDown(KeyCode.UpArrow)) index = (index + count - 1) % count;
        if (Input.GetKeyDown(KeyCode.S) || Input.GetKeyDown(KeyCode.DownArrow)) index = (index + 1) % count;
        return index;
    }

    public static bool Confirm() =>
        Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter) || Input.GetKeyDown(KeyCode.F) ||
        Input.GetKeyDown(KeyCode.Space);

    public static bool Back() => Input.GetKeyDown(KeyCode.Escape) || Input.GetKeyDown(KeyCode.Backspace);
}
