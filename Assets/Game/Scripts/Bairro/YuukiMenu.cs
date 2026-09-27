using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.SceneManagement;

// Title screen: start, controls, scenery gallery, quit. Keyboard (W/S + Enter) or mouse.
public sealed class YuukiMenu : MonoBehaviour
{
    public const string SceneName = "Bairro_Menu";
    public const string FirstMap = "Bairro_RuaDeCasa";
    public Sprite hero;
    public int GalleryCount => catalog.assets.Length;

    private enum Screen { Home, Controls, Gallery }

    private static readonly string[] Items = { "Começar", "Controles", "Galeria de cenários", "Sair" };

    private YuukiEnvironmentCatalog catalog;
    private readonly Dictionary<string, Texture2D> textures = new Dictionary<string, Texture2D>();
    private string[] categories;
    private Screen screen;
    private int index, category, page;
    private YuukiEnvironmentAsset selected;
    private Sprite[] breathing;
    private float fadeIn = 1f;

    private void Awake()
    {
        Time.timeScale = 1;
        Application.targetFrameRate = 60;
        catalog = YuukiEnvironmentCatalog.Load();
        categories = new[] { "Todos" }.Concat(catalog.assets.Select(a => a.category).Distinct()).ToArray();
        var clips = Resources.Load<TextAsset>("RpgRevision/yuuki");
        if (clips != null)
        {
            var data = JsonUtility.FromJson<YuukiRpgAnimation.Catalog>(clips.text);
            var idle = data.clips.FirstOrDefault(c => c.name == "idle_down");
            if (idle != null) breathing = idle.frames.Select(Resources.Load<Sprite>).Where(s => s != null).ToArray();
        }
    }

    private void Update()
    {
        fadeIn = Mathf.Max(0, fadeIn - Time.unscaledDeltaTime * 1.6f);
        switch (screen)
        {
            case Screen.Home:
                index = YuukiUI.Navigate(index, Items.Length);
                if (Input.GetKeyDown(KeyCode.Return) || Input.GetKeyDown(KeyCode.KeypadEnter) || Input.GetKeyDown(KeyCode.Space))
                    Choose(index);
                break;
            case Screen.Controls:
                if (YuukiUI.Back() || YuukiUI.Confirm()) screen = Screen.Home;
                break;
            case Screen.Gallery:
                if (YuukiUI.Back())
                {
                    if (selected != null) selected = null;
                    else screen = Screen.Home;
                }
                if (selected == null)
                {
                    if (Input.GetKeyDown(KeyCode.D) || Input.GetKeyDown(KeyCode.RightArrow)) page++;
                    if (Input.GetKeyDown(KeyCode.A) || Input.GetKeyDown(KeyCode.LeftArrow)) page--;
                }
                break;
        }
    }

    private void Choose(int item)
    {
        switch (item)
        {
            case 0: StartGame(); break;
            case 1: screen = Screen.Controls; break;
            case 2: ShowGallery(); break;
            case 3: Quit(); break;
        }
    }

    public void StartGame()
    {
        Time.timeScale = 1;
        YuukiMapTravel.Clear();
        YuukiClock.Reset();
        SceneManager.LoadScene(FirstMap);
    }

    public void ShowGallery() { screen = Screen.Gallery; page = 0; selected = null; }

    private Texture2D Texture(string resource)
    {
        if (!textures.TryGetValue(resource, out var tex))
        {
            tex = Resources.Load<Texture2D>(resource);
            textures.Add(resource, tex);
        }
        return tex;
    }

    private void Art(Rect rect, string id)
    {
        var tex = Texture("Environment/Art/" + id);
        if (tex != null) GUI.DrawTexture(rect, tex, ScaleMode.ScaleToFit, true);
    }

    private static void DrawSprite(Rect rect, Sprite sprite)
    {
        if (sprite == null) return;
        var r = sprite.textureRect;
        var t = sprite.texture;
        GUI.DrawTextureWithTexCoords(rect, t, new Rect(r.x / t.width, r.y / t.height, r.width / t.width, r.height / t.height));
    }

    private void OnGUI()
    {
        float w = YuukiUI.Begin();
        YuukiUI.Fill(new Rect(0, 0, w, YuukiUI.Height), new Color(0.055f, 0.06f, 0.07f));
        switch (screen)
        {
            case Screen.Home: DrawHome(w); break;
            case Screen.Controls: DrawControls(w); break;
            case Screen.Gallery: DrawGallery(w); break;
        }
        if (fadeIn > 0) YuukiUI.Fill(new Rect(0, 0, w, YuukiUI.Height), new Color(0, 0, 0, fadeIn));
        YuukiUI.End();
    }

    private void DrawHome(float w)
    {
        // Evening scene on the right: a street lamp's warm pool with Yuuki breathing in it.
        float cx = Mathf.Max(760, w * 0.7f);
        for (int i = 5; i >= 1; i--)
        {
            float r = 90 + i * 60;
            YuukiUI.Dot(new Rect(cx - r, 470 - r * 0.62f, r * 2, r * 1.24f), new Color(1f, 0.72f, 0.38f, 0.018f * (6 - i)));
        }
        YuukiUI.Dot(new Rect(cx - 170, 548, 340, 40), new Color(0, 0, 0, 0.35f));
        Art(new Rect(cx + 40, 250, 170, 320), "poste-luz");
        if (breathing != null && breathing.Length > 0)
        {
            int[] order = { 0, 1, 2, 1 };
            var frame = breathing[order[(int)(Time.unscaledTime / 0.48f) % 4] % breathing.Length];
            DrawSprite(new Rect(cx - 150, 250, 330, 330), frame);
        }
        else DrawSprite(new Rect(cx - 150, 250, 330, 330), hero);

        float x = 96;
        YuukiUI.Text(new Rect(x, 110, 560, 20), "CIDADE DOS ANJOS  ·  OS SUBÚRBIOS", YuukiUI.Size.Caption, YuukiUI.Accent);
        YuukiUI.Text(new Rect(x - 6, 128, 600, 110), "YUUKI", YuukiUI.Size.Huge, YuukiUI.Ink);
        YuukiUI.Text(new Rect(x, 236, 560, 30), "As ruas da nossa infância", YuukiUI.Size.Large, YuukiUI.Muted);
        YuukiUI.Fill(new Rect(x, 290, 56, 2), YuukiUI.Line);
        int clicked = YuukiUI.List(new Rect(x - 18, 320, 380, 240), Items, index, 54);
        if (clicked >= 0) { index = clicked; Choose(clicked); }
        float ky = 640;
        float kx = x;
        kx += YuukiUI.Key(kx, ky, "W") + 4;
        kx += YuukiUI.Key(kx, ky, "S") + 10;
        YuukiUI.Text(new Rect(kx, ky - 2, 90, 26), "escolher", YuukiUI.Size.Caption, YuukiUI.Muted, TextAnchor.MiddleLeft);
        kx += 80;
        kx += YuukiUI.Key(kx, ky, "Enter") + 10;
        YuukiUI.Text(new Rect(kx, ky - 2, 90, 26), "confirmar", YuukiUI.Size.Caption, YuukiUI.Muted, TextAnchor.MiddleLeft);
        YuukiUI.Text(new Rect(w - 360, 680, 340, 20), "Protótipo · visuais provisórios", YuukiUI.Size.Caption, YuukiUI.Faint,
            TextAnchor.MiddleRight);
    }

    private void DrawControls(float w)
    {
        DrawControlsCard(new Rect(w / 2 - 330, 120, 660, 460), Debug.isDebugBuild);
    }

    // Shared by the title screen and the pause menu.
    public static void DrawControlsCard(Rect rect, bool debug)
    {
        YuukiUI.Panel(rect);
        YuukiUI.Text(new Rect(rect.x + 36, rect.y + 26, 400, 20), "CONTROLES", YuukiUI.Size.Caption, YuukiUI.Accent);
        YuukiUI.Text(new Rect(rect.x + 36, rect.y + 44, 500, 40), "Explorar o bairro", YuukiUI.Size.Title, YuukiUI.Ink);
        var rows = new List<(string, string)>
        {
            ("WASD / setas", "andar"),
            ("Shift", "correr"),
            ("F", "ler placas, ver estantes, descer escadas"),
            ("Portas", "ande para cima para entrar e para baixo para sair"),
            ("Bordas do mapa", "continue andando para ir à próxima área"),
            ("Esc", "pausa · voltar"),
        };
        if (debug) rows.Add(("T", "teste: avançar 1 hora"));
        float y = rect.y + 106;
        foreach (var (key, what) in rows)
        {
            YuukiUI.Text(new Rect(rect.x + 36, y, 190, 30), key, YuukiUI.Size.Body, YuukiUI.Ink, TextAnchor.MiddleLeft);
            YuukiUI.Text(new Rect(rect.x + 236, y, rect.width - 272, 30), what, YuukiUI.Size.Body, YuukiUI.Muted, TextAnchor.MiddleLeft);
            y += 42;
        }
        float kx = rect.x + 36;
        kx += YuukiUI.Key(kx, rect.yMax - 46, "Esc") + 10;
        YuukiUI.Text(new Rect(kx, rect.yMax - 48, 100, 26), "voltar", YuukiUI.Size.Caption, YuukiUI.Muted, TextAnchor.MiddleLeft);
    }

    private void DrawGallery(float w)
    {
        float x0 = Mathf.Max(40, w / 2 - 600);
        YuukiUI.Text(new Rect(x0, 34, 400, 20), "GALERIA", YuukiUI.Size.Caption, YuukiUI.Accent);
        YuukiUI.Text(new Rect(x0, 52, 800, 40), "Cenários dos subúrbios", YuukiUI.Size.Title, YuukiUI.Ink);
        int clickedCategory = YuukiUI.List(new Rect(x0 - 18, 120, 250, 520), categories, category, 44);
        if (clickedCategory >= 0) { category = clickedCategory; page = 0; selected = null; }
        var list = catalog.assets.Where(a => category == 0 || a.category == categories[category]).ToArray();
        int pages = Mathf.Max(1, (list.Length + 5) / 6);
        page = (page % pages + pages) % pages;
        float gx = x0 + 260;
        for (int i = page * 6; i < Mathf.Min(list.Length, page * 6 + 6); i++)
        {
            var asset = list[i];
            int slot = i - page * 6;
            var rect = new Rect(gx + (slot % 3) * 300, 124 + (slot / 3) * 250, 284, 236);
            bool hover = rect.Contains(Event.current.mousePosition);
            YuukiUI.Fill(rect, new Color(1, 1, 1, hover ? 0.06f : 0.03f));
            Art(new Rect(rect.x + 12, rect.y + 10, rect.width - 24, 180), asset.id);
            YuukiUI.Text(new Rect(rect.x + 14, rect.y + 198, rect.width - 28, 30), asset.name, YuukiUI.Size.Small, YuukiUI.Ink);
            if (GUI.Button(rect, GUIContent.none, GUIStyle.none)) selected = asset;
        }
        YuukiUI.Text(new Rect(gx, 640, 600, 24), $"{list.Length} peças  ·  página {page + 1} de {pages}  ·  A/D mudam a página",
            YuukiUI.Size.Small, YuukiUI.Muted);
        float kx = w - x0 - 120;
        kx += YuukiUI.Key(kx, 642, "Esc") + 10;
        YuukiUI.Text(new Rect(kx, 640, 80, 26), "voltar", YuukiUI.Size.Caption, YuukiUI.Muted, TextAnchor.MiddleLeft);
        if (selected == null) return;
        YuukiUI.Fill(new Rect(0, 0, w, YuukiUI.Height), new Color(0.03f, 0.03f, 0.035f, 0.97f));
        Art(new Rect(w / 2 - 520, 70, 1040, 500), selected.id);
        YuukiUI.Text(new Rect(w / 2 - 520, 590, 900, 40), selected.name, YuukiUI.Size.Title, YuukiUI.Ink);
        YuukiUI.Text(new Rect(w / 2 - 520, 634, 900, 24), selected.category + (selected.floor ? " · textura de chão" : " · peça do cenário"),
            YuukiUI.Size.Small, YuukiUI.Muted);
        if (GUI.Button(new Rect(0, 0, w, YuukiUI.Height), GUIContent.none, GUIStyle.none)) selected = null;
    }

    public static void Quit()
    {
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;
#else
        Application.Quit();
#endif
    }
}
