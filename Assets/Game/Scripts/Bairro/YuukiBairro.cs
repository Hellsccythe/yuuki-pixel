using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.SceneManagement;

// Runtime owner of one modular map: its areas (street, house interiors), travel between
// maps, the clock and the whole HUD (time, area titles, edge hints, sign texts, the book
// menu and the pause menu).
public sealed class YuukiBairro : MonoBehaviour
{
    [Serializable] public sealed class Area
    {
        public string id;
        public string name;
        public Rect bounds;
        public bool outdoor = true;
        public Color background = Color.black;
    }

    private enum Overlay { None, Pause, Controls, Message, Books, Reading }

    public YuukiPlayerTopDown player;
    public YuukiBairroCamera cameraFollow;
    public Area[] areas = new Area[0];
    public GameObject[] outdoorOnly = new GameObject[0];
    public string regionName = "Os Subúrbios";
    public bool clockRuns = true;

    public static YuukiBairro Instance { get; private set; }
    public Area Current { get; private set; }

    public bool Paused => overlay == Overlay.Pause || overlay == Overlay.Controls;
    public bool TransitionBusy => busy;
    public bool OverlayOpen => overlay != Overlay.None;
    // True while a menu, a text or a transition owns the input (also one frame after
    // closing, so the same key press doesn't reopen what was just closed).
    public bool Blocking => busy || overlay != Overlay.None || Time.frameCount <= closedFrame + 1;
    public YuukiMapExit Edge => edge;

    private Overlay overlay;
    private int openedFrame = -10, closedFrame = -10;
    private float fade;
    private bool busy;
    private string toast;
    private float toastUntil;
    private string cardTitle, cardSubtitle;
    private float cardStart = -10f, cardLength;
    private float sceneStart;
    private int menuIndex;

    private string messageTitle, messageBody;
    private string shelfName;
    private List<YuukiBook> shelfBooks = new List<YuukiBook>();
    private int bookIndex, pageIndex;

    private YuukiMapExit edge;
    private float edgeHold;
    public const float EdgeHoldTime = 0.45f;
    private YuukiInteractor interactor;

    private static readonly string[] PauseItems = { "Retomar", "Controles", "Menu inicial" };

    // ------------------------------------------------------------------ lifecycle
    private void Awake()
    {
        Instance = this;
        sceneStart = Time.time;
        Time.timeScale = 1;
    }

    private void Start()
    {
        interactor = player != null ? player.GetComponent<YuukiInteractor>() : null;
        bool arriving = YuukiMapTravel.Consume(out Vector2 arrival);
        if (arriving) player.Teleport(arrival);
        EnterArea(FindArea(player.transform.position));
        ShowCard(Current != null ? Current.name : "", regionName, 3.2f);
        if (arriving) StartCoroutine(FadeIn());
    }

    private void OnDestroy()
    {
        if (Instance == this) Instance = null;
        Time.timeScale = 1;
    }

    private void Update()
    {
        if (clockRuns && overlay == Overlay.None && !busy) YuukiClock.Tick(Time.deltaTime);
        if (Debug.isDebugBuild && overlay == Overlay.None && Input.GetKeyDown(KeyCode.T))
        {
            YuukiClock.Skip(1f);
            Toast("Teste: +1 hora · " + YuukiClock.TimeText);
        }
        if (busy) return;
        switch (overlay)
        {
            case Overlay.None:
                if (Input.GetKeyDown(KeyCode.Escape)) OpenPause();
                else UpdateEdge();
                break;
            case Overlay.Pause: UpdatePause(); break;
            case Overlay.Controls:
                if (Time.frameCount > openedFrame && (YuukiUI.Back() || YuukiUI.Confirm()))
                {
                    overlay = Overlay.Pause;
                    openedFrame = Time.frameCount;
                }
                break;
            case Overlay.Message:
                if (Time.frameCount > openedFrame && (YuukiUI.Confirm() || YuukiUI.Back())) CloseOverlay();
                break;
            case Overlay.Books: UpdateBooks(); break;
            case Overlay.Reading: UpdateReading(); break;
        }
    }

    // ------------------------------------------------------------------ overlays
    private void Open(Overlay value)
    {
        overlay = value;
        openedFrame = Time.frameCount;
        player.InputBlocked = true;
        Time.timeScale = 0;
    }

    private void CloseOverlay()
    {
        overlay = Overlay.None;
        closedFrame = Time.frameCount;
        Time.timeScale = 1;
        player.InputBlocked = false;
    }

    public void ShowMessage(string title, string body)
    {
        if (Blocking) return;
        messageTitle = title;
        messageBody = body;
        Open(Overlay.Message);
    }

    public void ShowBooks(string shelf, List<YuukiBook> books)
    {
        if (Blocking) return;
        shelfName = shelf;
        shelfBooks = books ?? new List<YuukiBook>();
        bookIndex = 0;
        Open(Overlay.Books);
    }

    public void CloseMessage() { if (overlay == Overlay.Message || overlay == Overlay.Books || overlay == Overlay.Reading) CloseOverlay(); }

    private void UpdateBooks()
    {
        if (Time.frameCount <= openedFrame) return;
        if (YuukiUI.Back()) { CloseOverlay(); return; }
        if (shelfBooks.Count == 0)
        {
            if (YuukiUI.Confirm()) CloseOverlay();
            return;
        }
        bookIndex = YuukiUI.Navigate(bookIndex, shelfBooks.Count);
        if (YuukiUI.Confirm()) OpenBook(bookIndex);
    }

    private void OpenBook(int index)
    {
        bookIndex = index;
        pageIndex = 0;
        overlay = Overlay.Reading;
        openedFrame = Time.frameCount;
    }

    private void UpdateReading()
    {
        if (Time.frameCount <= openedFrame) return;
        var book = shelfBooks[bookIndex];
        int pages = Mathf.Max(1, book.paginas != null ? book.paginas.Length : 0);
        if (YuukiUI.Back()) { overlay = Overlay.Books; openedFrame = Time.frameCount; return; }
        bool next = Input.GetKeyDown(KeyCode.D) || Input.GetKeyDown(KeyCode.RightArrow);
        if (next || YuukiUI.Confirm())
        {
            if (pageIndex < pages - 1) pageIndex++;
            else if (!next) { overlay = Overlay.Books; openedFrame = Time.frameCount; }
        }
        if (Input.GetKeyDown(KeyCode.A) || Input.GetKeyDown(KeyCode.LeftArrow)) pageIndex = Mathf.Max(0, pageIndex - 1);
    }

    private void OpenPause()
    {
        menuIndex = 0;
        Open(Overlay.Pause);
    }

    public void SetPaused(bool value)
    {
        if (busy) return;
        if (value && overlay == Overlay.None) OpenPause();
        else if (!value && Paused) CloseOverlay();
    }

    private void UpdatePause()
    {
        if (Time.frameCount <= openedFrame) return;
        if (YuukiUI.Back()) { CloseOverlay(); return; }
        menuIndex = YuukiUI.Navigate(menuIndex, PauseItems.Length);
        if (YuukiUI.Confirm()) ChoosePause(menuIndex);
    }

    private void ChoosePause(int index)
    {
        switch (index)
        {
            case 0: CloseOverlay(); break;
            case 1: overlay = Overlay.Controls; openedFrame = Time.frameCount; break;
            case 2: ReturnToMenu(); break;
        }
    }

    public void ReturnToMenu()
    {
        Time.timeScale = 1;
        YuukiMapTravel.Clear();
        SceneManager.LoadScene(YuukiMenu.SceneName);
    }

    // ------------------------------------------------------------------ houses (cutaway)
    public bool BeginHouseTransition()
    {
        if (Blocking) return false;
        busy = true;
        player.InputBlocked = true;
        return true;
    }

    public void ShowHouseArea(Area area)
    {
        Current = area;
        cameraFollow.SetBounds(area.bounds, area.background);
        cameraFollow.SetZoom(area.outdoor ? 5.4f : 3.75f);
        foreach (var item in outdoorOnly) if (item != null) item.SetActive(area.outdoor);
        if (!area.outdoor) ShowCard(area.name, null, 2.2f);
    }

    public void FinishHouseTransition()
    {
        player.InputBlocked = false;
        busy = false;
    }

    // ------------------------------------------------------------------ map edges
    public void EnterEdge(YuukiMapExit exit)
    {
        edge = exit;
        edgeHold = 0f;
    }

    public void LeaveEdge(YuukiMapExit exit)
    {
        if (edge == exit) { edge = null; edgeHold = 0f; }
    }

    // Keep walking into the edge for a moment to travel: no pop-up, and walking away
    // cancels on its own.
    private void UpdateEdge()
    {
        if (edge == null || !edge.Ready) { edgeHold = 0f; return; }
        Vector2 v = player.Velocity;
        bool pushing = v.sqrMagnitude > 0.25f && Vector2.Dot(v.normalized, edge.Outward) > 0.55f;
        edgeHold = pushing ? edgeHold + Time.deltaTime : Mathf.Max(0f, edgeHold - Time.deltaTime * 2f);
        if (edgeHold >= EdgeHoldTime)
        {
            var target = edge;
            edge = null;
            edgeHold = 0f;
            LoadMap(target.targetMap, target.target);
        }
    }

    // Travel through the edge Yuuki is standing on right away (used by the integration test).
    public bool TravelThroughEdge()
    {
        if (edge == null || !edge.Ready || Blocking) return false;
        var target = edge;
        edge = null;
        LoadMap(target.targetMap, target.target);
        return true;
    }

    // Walks out to another modular map (another scene) and arrives at `arrival` there.
    public void LoadMap(string sceneName, Vector2 arrival)
    {
        if (!busy && overlay == Overlay.None) StartCoroutine(LoadMapRoutine(sceneName, arrival));
    }

    private IEnumerator LoadMapRoutine(string sceneName, Vector2 arrival)
    {
        busy = true;
        player.InputBlocked = true;
        for (float t = 0; t < 1; t += Time.unscaledDeltaTime / 0.35f) { fade = t; yield return null; }
        fade = 1;
        YuukiMapTravel.Set(arrival);
        SceneManager.LoadScene(sceneName);
    }

    private IEnumerator FadeIn()
    {
        busy = true;
        fade = 1;
        player.InputBlocked = true;
        yield return null;
        for (float t = 1; t > 0; t -= Time.unscaledDeltaTime / 0.4f) { fade = t; yield return null; }
        fade = 0;
        player.InputBlocked = false;
        busy = false;
    }

    // ------------------------------------------------------------------ areas
    public Area FindArea(Vector2 position)
    {
        foreach (var area in areas)
            if (area.bounds.Contains(position)) return area;
        return areas.Length > 0 ? areas[0] : null;
    }

    public Area GetArea(string id)
    {
        foreach (var area in areas)
            if (area.id == id) return area;
        return null;
    }

    // Same-map travel with a short fade (kept for portals inside a map).
    public void Travel(Vector2 target, string areaId)
    {
        if (!busy && overlay == Overlay.None) StartCoroutine(TravelRoutine(target, GetArea(areaId) ?? FindArea(target)));
    }

    private IEnumerator TravelRoutine(Vector2 target, Area area)
    {
        busy = true;
        player.InputBlocked = true;
        for (float t = 0; t < 1; t += Time.unscaledDeltaTime / 0.22f) { fade = t; yield return null; }
        fade = 1;
        player.Teleport(target);
        EnterArea(area);
        if (area != null) ShowCard(area.name, null, 2.2f);
        yield return new WaitForSecondsRealtime(0.08f);
        for (float t = 1; t > 0; t -= Time.unscaledDeltaTime / 0.28f) { fade = t; yield return null; }
        fade = 0;
        player.InputBlocked = false;
        busy = false;
    }

    private void EnterArea(Area area)
    {
        if (area == null) return;
        Current = area;
        cameraFollow.SetBounds(area.bounds, area.background);
        cameraFollow.Snap();
        foreach (var item in outdoorOnly)
            if (item != null) item.SetActive(area.outdoor);
    }

    // ------------------------------------------------------------------ HUD
    public void Toast(string message)
    {
        toast = message;
        toastUntil = Time.unscaledTime + 2.8f;
    }

    private void ShowCard(string title, string subtitle, float seconds)
    {
        cardTitle = title;
        cardSubtitle = subtitle;
        cardStart = Time.unscaledTime;
        cardLength = seconds;
    }

    private void OnGUI()
    {
        float w = YuukiUI.Begin();
        DrawClock(w);
        DrawCard(w);
        if (overlay == Overlay.None && !busy)
        {
            DrawEdgeHint(w);
            DrawPrompt(w);
        }
        DrawToast(w);
        DrawHints();
        switch (overlay)
        {
            case Overlay.Pause: DrawPause(); break;
            case Overlay.Controls: DrawControls(w); break;
            case Overlay.Message: DrawMessage(w); break;
            case Overlay.Books: DrawBooks(w); break;
            case Overlay.Reading: DrawReading(w); break;
        }
        if (fade > 0) YuukiUI.Fill(new Rect(0, 0, w, YuukiUI.Height), new Color(0, 0, 0, fade));
        YuukiUI.End();
    }

    private void DrawClock(float w)
    {
        var rect = new Rect(w - 214, 18, 196, 62);
        YuukiUI.Panel(rect, 0.92f);
        var icon = new Rect(rect.x + 16, rect.y + 17, 28, 28);
        if (YuukiClock.Night < 0.5f)
        {
            YuukiUI.Dot(new Rect(icon.x - 4, icon.y - 4, 36, 36), new Color(1f, 0.82f, 0.4f, 0.22f));
            YuukiUI.Dot(icon, new Color(1f, 0.82f, 0.42f));
        }
        else
        {
            YuukiUI.Dot(icon, new Color(0.86f, 0.88f, 0.95f));
            YuukiUI.Dot(new Rect(icon.x + 9, icon.y - 4, 26, 26), new Color(0.075f, 0.068f, 0.06f));
        }
        YuukiUI.Text(new Rect(rect.x + 58, rect.y + 6, 130, 32), YuukiClock.TimeText, YuukiUI.Size.Title, YuukiUI.Ink);
        YuukiUI.Text(new Rect(rect.x + 60, rect.y + 38, 130, 20), $"Dia {YuukiClock.Day} · {YuukiClock.Period}",
            YuukiUI.Size.Caption, YuukiUI.Muted);
    }

    private void DrawCard(float w)
    {
        if (string.IsNullOrEmpty(cardTitle)) return;
        float t = Time.unscaledTime - cardStart;
        if (t > cardLength) return;
        float a = Mathf.Clamp01(t / 0.45f) * Mathf.Clamp01((cardLength - t) / 0.7f);
        float y = 64 - (1 - Mathf.Clamp01(t / 0.45f)) * 8;
        YuukiUI.Text(new Rect(0, y, w, 44), cardTitle.ToUpperInvariant(), YuukiUI.Size.Title, YuukiUI.Ink, TextAnchor.MiddleCenter, false, a);
        float line = Mathf.Min(220, w * 0.16f);
        var rule = new Color(YuukiUI.Line.r, YuukiUI.Line.g, YuukiUI.Line.b, a * 0.8f);
        YuukiUI.Fill(new Rect(w / 2 - line - 170, y + 22, line, 1), rule);
        YuukiUI.Fill(new Rect(w / 2 + 170, y + 22, line, 1), rule);
        if (!string.IsNullOrEmpty(cardSubtitle))
            YuukiUI.Text(new Rect(0, y + 44, w, 22), cardSubtitle, YuukiUI.Size.Small, YuukiUI.Muted, TextAnchor.MiddleCenter, false, a);
    }

    private void DrawEdgeHint(float w)
    {
        if (edge == null) return;
        bool ready = edge.Ready;
        Vector2 o = edge.Outward;
        string before = o.x < -0.5f ? "‹  " : "";
        string after = o.x > 0.5f ? "  ›" : o.y > 0.5f ? "  ↑" : o.y < -0.5f ? "  ↓" : "";
        var rect = new Rect(w / 2 - 170, 574, 340, 58);
        YuukiUI.Panel(rect, 0.9f);
        YuukiUI.Text(new Rect(rect.x, rect.y + 6, rect.width, 26), before + edge.label + after, YuukiUI.Size.Body, YuukiUI.Ink,
            TextAnchor.MiddleCenter);
        YuukiUI.Text(new Rect(rect.x, rect.y + 32, rect.width, 18), ready ? "continue andando para seguir" : "ainda em construção",
            YuukiUI.Size.Caption, YuukiUI.Muted, TextAnchor.MiddleCenter);
        if (ready && edgeHold > 0)
            YuukiUI.Fill(new Rect(rect.x, rect.yMax - 3, rect.width * Mathf.Clamp01(edgeHold / EdgeHoldTime), 3), YuukiUI.Accent);
    }

    private void DrawPrompt(float w)
    {
        var target = interactor != null ? interactor.Current : null;
        if (target == null || edge != null) return;
        string label = target.prompt;
        float textW = Mathf.Max(60, label.Length * 9.5f);
        float total = 14 + 22 + 12 + textW + 16;
        var rect = new Rect(w / 2 - total / 2, 592, total, 36);
        YuukiUI.Panel(rect, 0.9f);
        YuukiUI.Key(rect.x + 14, rect.y + 7, "F");
        YuukiUI.Text(new Rect(rect.x + 48, rect.y, textW, rect.height), label, YuukiUI.Size.Small, YuukiUI.Ink, TextAnchor.MiddleLeft);
    }

    private void DrawToast(float w)
    {
        if (string.IsNullOrEmpty(toast) || Time.unscaledTime > toastUntil) return;
        float a = Mathf.Clamp01((toastUntil - Time.unscaledTime) / 0.5f);
        var rect = new Rect(w / 2 - 200, 520, 400, 34);
        YuukiUI.Panel(rect, a * 0.9f);
        YuukiUI.Text(rect, toast, YuukiUI.Size.Small, YuukiUI.Ink, TextAnchor.MiddleCenter, false, a);
    }

    private void DrawHints()
    {
        float t = Time.time - sceneStart;
        float a = overlay == Overlay.None ? Mathf.Clamp01((14f - t) / 2f) * 0.6f : 0f;
        if (a <= 0) return;
        YuukiUI.Text(new Rect(18, 690, 640, 20), "WASD  andar      Shift  correr      F  interagir      Esc  pausa",
            YuukiUI.Size.Caption, YuukiUI.Ink, TextAnchor.MiddleLeft, false, a);
    }

    private void DrawMessage(float w)
    {
        var rect = new Rect(w / 2 - 390, 506, 780, 180);
        YuukiUI.Panel(rect);
        float y = rect.y + 18;
        if (!string.IsNullOrEmpty(messageTitle))
        {
            YuukiUI.Text(new Rect(rect.x + 28, y, rect.width - 56, 24), messageTitle.ToUpperInvariant(), YuukiUI.Size.Small, YuukiUI.Accent);
            y += 30;
        }
        YuukiUI.Text(new Rect(rect.x + 28, y, rect.width - 56, rect.yMax - y - 34), messageBody, YuukiUI.Size.Body, YuukiUI.Ink,
            TextAnchor.UpperLeft, true);
        float kx = rect.xMax - 110;
        YuukiUI.Key(kx, rect.yMax - 34, "F");
        YuukiUI.Text(new Rect(kx + 30, rect.yMax - 36, 80, 26), "fechar", YuukiUI.Size.Caption, YuukiUI.Muted, TextAnchor.MiddleLeft);
    }

    private void DrawBooks(float w)
    {
        YuukiUI.Dim(0.55f);
        var rect = new Rect(w / 2 - 440, 120, 880, 480);
        YuukiUI.Panel(rect);
        YuukiUI.Text(new Rect(rect.x + 32, rect.y + 22, 600, 22), "ESTANTE", YuukiUI.Size.Caption, YuukiUI.Accent);
        YuukiUI.Text(new Rect(rect.x + 32, rect.y + 40, 600, 40), shelfName, YuukiUI.Size.Title, YuukiUI.Ink);
        YuukiUI.Fill(new Rect(rect.x + 32, rect.y + 92, rect.width - 64, 1), new Color(1, 1, 1, 0.08f));
        var listArea = new Rect(rect.x + 24, rect.y + 108, 380, rect.height - 170);
        if (shelfBooks.Count == 0)
        {
            YuukiUI.List(listArea, new[] { "Sem registro" }, 0, 44, new[] { true });
            YuukiUI.Text(new Rect(rect.x + 440, rect.y + 116, rect.width - 480, 200),
                "Nenhum livro desta estante foi registrado ainda.\n\nQuando os livros forem cadastrados, eles aparecem aqui para leitura.",
                YuukiUI.Size.Body, YuukiUI.Muted, TextAnchor.UpperLeft, true);
        }
        else
        {
            var titles = new string[shelfBooks.Count];
            for (int i = 0; i < titles.Length; i++) titles[i] = shelfBooks[i].titulo;
            int clicked = YuukiUI.List(listArea, titles, bookIndex, 44);
            if (clicked >= 0) { if (clicked == bookIndex) OpenBook(clicked); else bookIndex = clicked; }
            var book = shelfBooks[Mathf.Clamp(bookIndex, 0, shelfBooks.Count - 1)];
            YuukiUI.Text(new Rect(rect.x + 440, rect.y + 112, rect.width - 480, 34), book.titulo, YuukiUI.Size.Large, YuukiUI.Ink,
                TextAnchor.UpperLeft, true);
            if (!string.IsNullOrEmpty(book.autor))
                YuukiUI.Text(new Rect(rect.x + 440, rect.y + 150, rect.width - 480, 22), book.autor, YuukiUI.Size.Small, YuukiUI.Muted);
            YuukiUI.Text(new Rect(rect.x + 440, rect.y + 186, rect.width - 480, 200), book.resumo ?? "", YuukiUI.Size.Body,
                YuukiUI.Muted, TextAnchor.UpperLeft, true);
        }
        float kx = rect.x + 32, ky = rect.yMax - 44;
        if (shelfBooks.Count > 0)
        {
            kx += YuukiUI.Key(kx, ky, "F") + 8;
            YuukiUI.Text(new Rect(kx, ky - 2, 60, 26), "ler", YuukiUI.Size.Caption, YuukiUI.Muted, TextAnchor.MiddleLeft);
            kx += 50;
        }
        kx += YuukiUI.Key(kx, ky, "Esc") + 8;
        YuukiUI.Text(new Rect(kx, ky - 2, 80, 26), "fechar", YuukiUI.Size.Caption, YuukiUI.Muted, TextAnchor.MiddleLeft);
    }

    private void DrawReading(float w)
    {
        YuukiUI.Dim(0.7f);
        var book = shelfBooks[bookIndex];
        int pages = book.paginas != null ? book.paginas.Length : 0;
        var rect = new Rect(w / 2 - 360, 70, 720, 580);
        YuukiUI.Fill(rect, new Color(0.86f, 0.81f, 0.7f, 0.98f));
        YuukiUI.Fill(new Rect(rect.x, rect.y, rect.width, 2), YuukiUI.Line);
        var dark = new Color(0.2f, 0.15f, 0.11f);
        YuukiUI.Text(new Rect(rect.x + 48, rect.y + 34, rect.width - 96, 40), book.titulo, YuukiUI.Size.Title, dark, TextAnchor.UpperLeft, true);
        string page = pages > 0 ? book.paginas[Mathf.Clamp(pageIndex, 0, pages - 1)] : "(página em branco)";
        YuukiUI.Text(new Rect(rect.x + 48, rect.y + 104, rect.width - 96, rect.height - 170), page, YuukiUI.Size.Body, dark,
            TextAnchor.UpperLeft, true);
        if (pages > 0)
            YuukiUI.Text(new Rect(rect.x, rect.yMax - 44, rect.width, 22), $"‹  {pageIndex + 1} / {pages}  ›", YuukiUI.Size.Small,
                new Color(0.35f, 0.28f, 0.2f), TextAnchor.MiddleCenter);
    }

    private void DrawPause()
    {
        YuukiUI.Dim(0.62f);
        var rect = new Rect(64, 170, 360, 300);
        YuukiUI.Panel(rect);
        YuukiUI.Text(new Rect(rect.x + 30, rect.y + 24, 300, 22), "PAUSA", YuukiUI.Size.Caption, YuukiUI.Accent);
        YuukiUI.Text(new Rect(rect.x + 30, rect.y + 42, 300, 40), Current != null ? Current.name : "", YuukiUI.Size.Title, YuukiUI.Ink);
        YuukiUI.Text(new Rect(rect.x + 30, rect.y + 84, 300, 22), $"Dia {YuukiClock.Day} · {YuukiClock.TimeText} · {YuukiClock.Period}",
            YuukiUI.Size.Small, YuukiUI.Muted);
        int clicked = YuukiUI.List(new Rect(rect.x + 16, rect.y + 128, rect.width - 32, 156), PauseItems, menuIndex, 50);
        if (clicked >= 0) { menuIndex = clicked; ChoosePause(clicked); }
    }

    private void DrawControls(float w)
    {
        YuukiUI.Dim(0.72f);
        YuukiMenu.DrawControlsCard(new Rect(w / 2 - 330, 120, 660, 460), Debug.isDebugBuild);
    }
}
