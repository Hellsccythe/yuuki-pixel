using System.Collections.Generic;
using System.Linq;
using UnityEngine;
using UnityEngine.SceneManagement;

// Lightweight menu and art review gallery; the game scenes stay independent.
public sealed class YuukiMenu : MonoBehaviour
{
    public const string SceneName = "Bairro_Menu";
    public Sprite hero;
    public int GalleryCount => catalog.assets.Length;
    private YuukiEnvironmentCatalog catalog;
    private readonly Dictionary<string, Texture2D> textures = new Dictionary<string, Texture2D>();
    private string[] categories;
    private int screen, category, page;
    private YuukiEnvironmentAsset selected;
    private GUIStyle title, heading, text, small, button;
    private readonly Color ink = new Color(.89f, .86f, .76f);
    private readonly Color muted = new Color(.60f, .62f, .53f);

    private void Awake()
    {
        Time.timeScale = 1;
        Application.targetFrameRate = 60;
        catalog = YuukiEnvironmentCatalog.Load();
        categories = new[] { "Todos" }.Concat(catalog.assets.Select(a => a.category).Distinct()).ToArray();
    }

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Escape))
        {
            if (selected != null) selected = null;
            else screen = 0;
        }
        if (screen == 0 && Input.GetKeyDown(KeyCode.Return)) StartGame();
    }

    public void StartGame()
    {
        Time.timeScale = 1;
        YuukiMapTravel.Clear();
        SceneManager.LoadScene("Bairro_RuaDeCasa");
    }

    public void ShowGallery() { screen = 1; page = 0; }

    private Texture2D Texture(string resource)
    {
        if (!textures.TryGetValue(resource, out var tex))
        {
            tex = Resources.Load<Texture2D>(resource);
            textures.Add(resource, tex);
        }
        return tex;
    }

    private void Styles()
    {
        if (title != null) return;
        title = new GUIStyle(GUI.skin.label) { fontSize = 80, fontStyle = FontStyle.Bold };
        heading = new GUIStyle(GUI.skin.label) { fontSize = 30 };
        text = new GUIStyle(GUI.skin.label) { fontSize = 20, wordWrap = true };
        small = new GUIStyle(text) { fontSize = 15 };
        button = new GUIStyle(text) { alignment = TextAnchor.MiddleCenter };
        foreach (var style in new[] { title, heading, text, small, button }) style.normal.textColor = ink;
    }

    private static void Panel(Rect rect, Color color)
    {
        GUI.color = color; GUI.DrawTexture(rect, Texture2D.whiteTexture); GUI.color = Color.white;
    }

    private bool Button(Rect rect, string label, bool accent = false)
    {
        bool hover = rect.Contains(Event.current.mousePosition);
        Panel(rect, accent ? new Color(.40f, .37f, .24f) : new Color(.16f, .18f, .15f));
        Panel(new Rect(rect.x, rect.yMax-2, rect.width, 2), hover ? ink : muted * .7f);
        return GUI.Button(rect, label, button);
    }

    private void Art(Rect rect, string id)
    {
        var tex = Texture("Environment/Art/" + id);
        if (tex != null) GUI.DrawTexture(rect, tex, ScaleMode.ScaleToFit, true);
    }

    private void OnGUI()
    {
        Styles();
        float scale = Mathf.Min(Screen.width / 1280f, Screen.height / 720f);
        GUI.matrix = Matrix4x4.TRS(new Vector3((Screen.width-1280*scale)/2, (Screen.height-720*scale)/2),
            Quaternion.identity, Vector3.one * scale);
        Panel(new Rect(0, 0, 1280, 720), new Color(.065f, .083f, .077f));
        if (screen == 0) DrawHome();
        else if (screen == 1) DrawGallery();
        else DrawControls();
        GUI.matrix = Matrix4x4.identity;
    }

    private void DrawHome()
    {
        Panel(new Rect(652, 0, 628, 720), new Color(.11f, .13f, .115f));
        Panel(new Rect(652, 554, 628, 166), new Color(.14f, .15f, .115f));
        Art(new Rect(735, 72, 465, 480), "casa-abandonada-a");
        Art(new Rect(682, 467, 120, 125), "horta-morta");
        Art(new Rect(1095, 438, 155, 155), "portao-ferrugem");
        if (hero != null)
        {
            var r = hero.textureRect;
            GUI.DrawTextureWithTexCoords(new Rect(910, 449, 145, 145), hero.texture,
                new Rect(r.x/hero.texture.width, r.y/hero.texture.height, r.width/hero.texture.width, r.height/hero.texture.height));
        }
        GUI.color = muted; GUI.Label(new Rect(62, 56, 540, 28), "CIDADE DOS ANJOS  /  OS SUBÚRBIOS", small); GUI.color = Color.white;
        GUI.Label(new Rect(56, 96, 560, 105), "YUUKI", title);
        GUI.Label(new Rect(62, 195, 550, 52), "As ruas de onde viemos", heading);
        GUI.Label(new Rect(62, 258, 500, 74), "Casas gastas, histórias esquecidas.\nUm bairro à sombra da cidade dos anjos.", text);
        if (Button(new Rect(62, 368, 455, 56), "Entrar no bairro", true)) StartGame();
        if (Button(new Rect(62, 440, 455, 48), "Galeria de cenários")) ShowGallery();
        if (Button(new Rect(62, 504, 218, 48), "Controles")) screen = 2;
        if (Button(new Rect(298, 504, 219, 48), "Sair")) Quit();
        GUI.color = muted;
        GUI.Label(new Rect(62, 649, 550, 36), "Protótipo de exploração · Rua de Casa + Moradias", small);
        GUI.Label(new Rect(740, 631, 470, 50), "O começo de um mundo em construção.", small);
        GUI.color = Color.white;
    }

    private void DrawGallery()
    {
        GUI.Label(new Rect(32, 22, 800, 44), "Cenários da infância de Yuuki", heading);
        if (Button(new Rect(1098, 24, 150, 42), "Voltar")) { screen = 0; selected = null; }
        for (int i = 0; i < categories.Length; i++)
            if (Button(new Rect(26, 90+i*52, 208, 44), categories[i], category == i)) { category = i; page = 0; selected = null; }
        var list = catalog.assets.Where(a => category == 0 || a.category == categories[category]).ToArray();
        int pages = Mathf.Max(1, (list.Length+5)/6);
        page = Mathf.Clamp(page, 0, pages-1);
        for (int i = page*6; i < Mathf.Min(list.Length, page*6+6); i++)
        {
            var asset = list[i]; int slot = i-page*6;
            var rect = new Rect(260+(slot%3)*330, 90+(slot/3)*258, 310, 242);
            Panel(rect, new Color(.13f, .15f, .13f));
            Art(new Rect(rect.x+12, rect.y+8, 286, 186), asset.id);
            GUI.Label(new Rect(rect.x+12, rect.y+199, 286, 39), asset.name, small);
            if (GUI.Button(rect, GUIContent.none, GUIStyle.none)) selected = asset;
        }
        if (Button(new Rect(260, 628, 135, 44), "Anterior")) page = (page+pages-1)%pages;
        GUI.Label(new Rect(435, 637, 570, 36), $"{list.Length} peças  ·  Página {page+1}/{pages}  ·  Clique para ampliar", small);
        if (Button(new Rect(1110, 628, 140, 44), "Próxima")) page = (page+1)%pages;
        if (selected == null) return;
        Panel(new Rect(0, 0, 1280, 720), new Color(.015f, .025f, .02f, .97f));
        Art(new Rect(120, 72, 1040, 500), selected.id);
        GUI.Label(new Rect(120, 584, 850, 45), selected.name, heading);
        GUI.Label(new Rect(120, 635, 820, 42), selected.category + (selected.floor ? " · textura de chão" : " · peça estática"), small);
        if (Button(new Rect(990, 625, 170, 48), "Fechar")) selected = null;
    }

    private void DrawControls()
    {
        GUI.Label(new Rect(170, 90, 940, 60), "Explorar o bairro", heading);
        GUI.Label(new Rect(170, 195, 950, 270), "WASD ou setas — andar em qualquer direção\n\nShift — correr\n\nPortas — aproxime-se para entrar ou sair\n\nBordas do mapa — confirme a viagem com Enter ou clique\n\nEsc — cancelar uma viagem, pausar ou voltar", text);
        if (Button(new Rect(170, 550, 300, 54), "Voltar")) screen = 0;
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
