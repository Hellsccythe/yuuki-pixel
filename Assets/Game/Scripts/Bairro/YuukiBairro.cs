using System;
using System.Collections;
using UnityEngine;
using UnityEngine.SceneManagement;

// Runtime owner of one modular map: knows its areas (street, interiors), moves the player
// between them with a short fade and shows small location / exit messages.
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

    public YuukiPlayerTopDown player;
    public YuukiBairroCamera cameraFollow;
    public Area[] areas = new Area[0];
    public GameObject[] outdoorOnly = new GameObject[0];

    public static YuukiBairro Instance { get; private set; }
    public Area Current { get; private set; }

    private float fade;
    private bool busy;
    private string toast;
    private float toastUntil;
    private float titleUntil;
    private Texture2D pixel;
    private string pendingScene, pendingLabel;
    private Vector2 pendingArrival;
    public bool AwaitingTravel => !string.IsNullOrEmpty(pendingScene);
    public bool Paused { get; private set; }

    private void Update()
    {
        if (busy) return;
        if (AwaitingTravel)
        {
            if (Input.GetKeyDown(KeyCode.Escape)) CancelMapChange();
            else if (Input.GetKeyDown(KeyCode.Return)) ConfirmMapChange();
        }
        else if (Input.GetKeyDown(KeyCode.Escape)) SetPaused(!Paused);
    }

    public bool RequestMapChange(string destination, string scene, Vector2 arrival)
    {
        if (busy || Paused || AwaitingTravel) return false;
        if (string.IsNullOrEmpty(scene) || !Application.CanStreamedLevelBeLoaded(scene)) return false;
        pendingScene = scene;
        pendingLabel = destination;
        pendingArrival = arrival;
        player.InputBlocked = true;
        Time.timeScale = 0;
        return true;
    }

    public void CancelMapChange()
    {
        if (!AwaitingTravel) return;
        pendingScene = null;
        Time.timeScale = 1;
        player.InputBlocked = false;
        Toast("Você continua em " + Current.name + ".");
    }

    public void ConfirmMapChange()
    {
        if (!AwaitingTravel) return;
        string scene = pendingScene;
        pendingScene = null;
        Time.timeScale = 1;
        LoadMap(scene, pendingArrival);
    }

    public void SetPaused(bool value)
    {
        if (busy || AwaitingTravel) return;
        Paused = value;
        player.InputBlocked = value;
        Time.timeScale = value ? 0 : 1;
    }

    public void ReturnToMenu()
    {
        Time.timeScale = 1;
        YuukiMapTravel.Clear();
        SceneManager.LoadScene(YuukiMenu.SceneName);
    }

    private void OnDestroy()
    {
        if (Instance == this) Instance = null;
        if (pixel != null) Destroy(pixel);
        Time.timeScale = 1;
    }

    private void Awake()
    {
        Instance = this;
        pixel = new Texture2D(1, 1);
        pixel.SetPixel(0, 0, Color.white);
        pixel.Apply();
    }

    private void Start()
    {
        bool arriving = YuukiMapTravel.Consume(out Vector2 arrival);
        if (arriving) player.Teleport(arrival);
        EnterArea(FindArea(player.transform.position), true);
        if (arriving) StartCoroutine(FadeIn());
    }

    private IEnumerator FadeIn()
    {
        busy = true;
        fade = 1;
        player.InputBlocked = true;
        yield return null;
        for (float t = 1; t > 0; t -= Time.deltaTime / 0.35f) { fade = t; yield return null; }
        fade = 0;
        player.InputBlocked = false;
        busy = false;
    }

    // Walks out to another modular map (another scene) and arrives at `arrival` there.
    public void LoadMap(string sceneName, Vector2 arrival)
    {
        if (!busy && !Paused && !AwaitingTravel) StartCoroutine(LoadMapRoutine(sceneName, arrival));
    }

    private IEnumerator LoadMapRoutine(string sceneName, Vector2 arrival)
    {
        busy = true;
        player.InputBlocked = true;
        for (float t = 0; t < 1; t += Time.deltaTime / 0.3f) { fade = t; yield return null; }
        fade = 1;
        YuukiMapTravel.Set(arrival);
        SceneManager.LoadScene(sceneName);
    }

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

    public void Travel(Vector2 target, string areaId)
    {
        if (!busy && !Paused && !AwaitingTravel) StartCoroutine(TravelRoutine(target, GetArea(areaId) ?? FindArea(target)));
    }

    private IEnumerator TravelRoutine(Vector2 target, Area area)
    {
        busy = true;
        player.InputBlocked = true;
        for (float t = 0; t < 1; t += Time.deltaTime / 0.22f) { fade = t; yield return null; }
        fade = 1;
        player.Teleport(target);
        EnterArea(area, true);
        yield return new WaitForSeconds(0.08f);
        for (float t = 1; t > 0; t -= Time.deltaTime / 0.28f) { fade = t; yield return null; }
        fade = 0;
        player.InputBlocked = false;
        busy = false;
    }

    private void EnterArea(Area area, bool announce)
    {
        if (area == null) return;
        Current = area;
        cameraFollow.SetBounds(area.bounds, area.background);
        cameraFollow.Snap();
        foreach (var item in outdoorOnly)
            if (item != null) item.SetActive(area.outdoor);
        titleUntil = Time.time + (announce ? 2.5f : 3.5f);
    }

    public void Toast(string message)
    {
        toast = message;
        toastUntil = Time.time + 2.6f;
    }

    private void OnGUI()
    {
        float scale = Screen.height / 640f;
        GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, Vector3.one * scale);
        float width = Screen.width / scale;
        var label = new GUIStyle(GUI.skin.label) { fontSize = 15, alignment = TextAnchor.MiddleCenter };
        label.normal.textColor = new Color(0.96f, 0.92f, 0.84f);

        if (Current != null && Time.time < titleUntil)
        {
            float a = Mathf.Clamp01((titleUntil - Time.time) / 0.6f);
            DrawPanel(new Rect(16, 16, 220, 34), a);
            GUI.color = new Color(1, 1, 1, a);
            GUI.Label(new Rect(16, 16, 220, 34), Current.name, label);
            GUI.color = Color.white;
        }
        if (!string.IsNullOrEmpty(toast) && Time.time < toastUntil)
        {
            float a = Mathf.Clamp01((toastUntil - Time.time) / 0.5f);
            DrawPanel(new Rect(width / 2 - 170, 548, 340, 34), a);
            GUI.color = new Color(1, 1, 1, a);
            GUI.Label(new Rect(width / 2 - 170, 548, 340, 34), toast, label);
            GUI.color = Color.white;
        }
        var hint = new GUIStyle(label) { fontSize = 12, alignment = TextAnchor.MiddleLeft };
        hint.normal.textColor = new Color(1, 1, 1, 0.55f);
        GUI.Label(new Rect(14, 612, 580, 22), "WASD / setas · andar      Shift · correr      Esc · pausa", hint);

        if (AwaitingTravel || Paused)
        {
            GUI.color = new Color(0.02f, 0.03f, 0.025f, .8f);
            GUI.DrawTexture(new Rect(0, 0, width, 640), pixel);
            GUI.color = Color.white;
            float left = width / 2 - 220;
            DrawPanel(new Rect(left, 194, 440, 236), 1);
            var wrap = new GUIStyle(label) { wordWrap = true, fontSize = 19 };
            var btn = new GUIStyle(GUI.skin.button) { fontSize = 16 };
            if (AwaitingTravel)
            {
                GUI.Label(new Rect(left+24, 218, 392, 75), "Ir para " + pendingLabel + "?", wrap);
                GUI.Label(new Rect(left+24, 285, 392, 32), "Enter confirma · Esc cancela", label);
                if (GUI.Button(new Rect(left+24, 340, 188, 46), "Continuar aqui", btn)) CancelMapChange();
                if (GUI.Button(new Rect(left+228, 340, 188, 46), "Mudar de área", btn)) ConfirmMapChange();
            }
            else
            {
                GUI.Label(new Rect(left+24, 214, 392, 50), "Pausa", wrap);
                if (GUI.Button(new Rect(left+24, 279, 392, 48), "Retomar", btn)) SetPaused(false);
                if (GUI.Button(new Rect(left+24, 345, 392, 48), "Menu inicial", btn)) ReturnToMenu();
            }
        }

        if (fade > 0)
        {
            GUI.color = new Color(0, 0, 0, fade);
            GUI.DrawTexture(new Rect(0, 0, width, 640), pixel);
            GUI.color = Color.white;
        }
        GUI.matrix = Matrix4x4.identity;
    }

    private void DrawPanel(Rect rect, float alpha)
    {
        GUI.color = new Color(0.12f, 0.09f, 0.07f, 0.72f * alpha);
        GUI.DrawTexture(rect, pixel);
        GUI.color = new Color(0.55f, 0.42f, 0.28f, 0.9f * alpha);
        GUI.DrawTexture(new Rect(rect.x, rect.yMax - 2, rect.width, 2), pixel);
        GUI.color = Color.white;
    }
}
