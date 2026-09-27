using System.Collections.Generic;
using System.Linq;
using UnityEngine;

public sealed class YuukiWorldController : MonoBehaviour
{
    public YuukiTopDownMovement player;
    public YuukiWorldCamera worldCamera;
    private YuukiWorldData world;
    private YuukiMapData map;
    private GameObject area;
    private YuukiWorldInteractable[] points;
    private YuukiWorldInteractable nearest;
    private readonly Dictionary<string, string> journal = new Dictionary<string, string>();
    private string panelTitle, panelText;
    private bool showPanel, showMap;

    private void Start()
    {
        world = JsonUtility.FromJson<YuukiWorldData>(Resources.Load<TextAsset>("World/angel-suburbs").text);
        var initial = world.maps.First(item => item.id == world.startMap);
        Enter(initial.id, initial.spawnX, initial.spawnY);
    }

    private void Enter(string id, float x, float y)
    {
        if (area != null) { area.SetActive(false); Destroy(area); }
        map = world.maps.First(item => item.id == id);
        area = Instantiate(Resources.Load<GameObject>("World/Areas/" + id));
        area.name = map.name;
        points = area.GetComponentsInChildren<YuukiWorldInteractable>();
        nearest = null;
        player.Teleport(new Vector2(x / 100f, -y / 100f));
        worldCamera.SetBounds(map.width / 100f, map.height / 100f);
        Physics2D.SyncTransforms();
    }

    private void Update()
    {
        if (map == null) return;
        if (Input.GetKeyDown(KeyCode.Escape)) { showPanel = false; showMap = false; }
        if (Input.GetKeyDown(KeyCode.J)) OpenJournal();
        if (Input.GetKeyDown(KeyCode.M)) { showMap = !showMap; showPanel = false; }
        player.InputBlocked = showPanel || showMap;
        if (player.InputBlocked)
        {
            if (Input.GetKeyDown(KeyCode.E)) { showPanel = false; showMap = false; player.InputBlocked = false; }
            return;
        }
        nearest = points.Where(p => Vector2.Distance(player.transform.position, p.transform.position) < .76f)
            .OrderBy(p => Vector2.Distance(player.transform.position, p.transform.position)).FirstOrDefault();
        if (nearest != null && Input.GetKeyDown(KeyCode.E))
        {
            var point = nearest.point;
            if (!string.IsNullOrEmpty(point.target)) Enter(point.target, point.targetX, point.targetY);
            else
            {
                if (point.journal) journal[point.id] = point.title;
                panelTitle = point.title; panelText = point.text; showPanel = true;
                player.InputBlocked = true;
            }
        }
    }

    private void OpenJournal()
    {
        showMap = false; showPanel = true;
        panelTitle = "Os caminhos de casa";
        panelText = "Conheça a casa, o beco, a escola e o limiar da cidade.\n\n" +
            (journal.Count == 0 ? "Aproxime-se de um ponto de interesse e pressione E." : string.Join("\n", journal.Values.Select(title => "• " + title)));
    }

    private void OnGUI()
    {
        if (map == null) return;
        // Scale the readable HUD independently of Game-view resolution.
        GUI.matrix = Matrix4x4.TRS(Vector3.zero, Quaternion.identity, Vector3.one * (Screen.height / 640f));
        float width = Screen.width * 640f / Screen.height;
        var box = new GUIStyle(GUI.skin.box) { fontSize = 17, alignment = TextAnchor.MiddleLeft, padding = new RectOffset(16,16,10,10) };
        var body = new GUIStyle(GUI.skin.label) { fontSize = 17, wordWrap = true, padding = new RectOffset(20,20,12,12) };
        var button = new GUIStyle(GUI.skin.button) { fontSize = 15 };
        var label = new GUIStyle(GUI.skin.label) { fontSize = 13 };
        var region = map.regions.FirstOrDefault(r => player.transform.position.x * 100 >= r.x && player.transform.position.x * 100 < r.x + r.w &&
            -player.transform.position.y * 100 >= r.y && -player.transform.position.y * 100 < r.y + r.h);
        GUI.Box(new Rect(16,16,335,60), "CIDADE DOS ANJOS\n" + (region != null ? region.name : map.name), box);
        if (GUI.Button(new Rect(width-200,16,88,36),"Diário · J",button)) OpenJournal();
        if (GUI.Button(new Rect(width-104,16,88,36),"Mapa · M",button)) { showMap = !showMap; showPanel = false; }
        GUI.Box(new Rect(0,612,width,28), GUIContent.none);
        GUI.Label(new Rect(16,615,width-250,25),"WASD / setas · mover    Shift · correr    E · interagir",label);
        GUI.Label(new Rect(width-245,615,230,25),"Lembranças do bairro · " + journal.Count + "/5",label);
        if (nearest != null && !showPanel && !showMap)
            GUI.Box(new Rect(width/2-190,559,380,37),"E   " + nearest.point.title,box);
        if (showPanel)
        {
            GUI.Box(new Rect(width/2-280,165,560,295),GUIContent.none);
            GUI.Label(new Rect(width/2-270,178,540,42),panelTitle,new GUIStyle(body){fontSize=23});
            GUI.Label(new Rect(width/2-270,224,540,174),panelText,body);
            if (GUI.Button(new Rect(width/2-75,408,150,34),"Continuar · E",button)) showPanel = false;
        }
        if (showMap)
        {
            GUI.Box(new Rect(width/2-330,92,660,468),GUIContent.none);
            GUI.Label(new Rect(width/2-310,104,600,36),"O bairro",new GUIStyle(body){fontSize=23});
            var texture = Resources.Load<Texture2D>("World/Floors/suburbs");
            var rect = new Rect(width/2-307,153,614,360);
            GUI.DrawTexture(rect,texture,ScaleMode.StretchToFill);
            foreach (var regionInfo in world.maps[0].regions)
                GUI.Label(new Rect(rect.x+regionInfo.x/3072*rect.width+12,rect.y+regionInfo.y/2048*rect.height+20,155,45),regionInfo.name,label);
            if (map.id == "suburbs") GUI.Label(new Rect(rect.x+player.transform.position.x/30.72f*rect.width-6,rect.y-player.transform.position.y/20.48f*rect.height-12,30,30),"◆",new GUIStyle(label){fontSize=22});
            GUI.Label(new Rect(width/2-305,521,600,25),"M ou Esc para voltar",label);
        }
        GUI.matrix = Matrix4x4.identity;
    }
}
