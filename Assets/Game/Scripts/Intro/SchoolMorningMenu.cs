using UnityEngine;
using UnityEngine.SceneManagement;
namespace YuukiIntro
{
    public sealed class SchoolMorningMenu : MonoBehaviour
    {
        GUIStyle title,text;Texture2D art;
        void Awake(){Time.timeScale=1;art=Resources.Load<Texture2D>("SchoolMorning/school");}
        void OnGUI()
        {
            if(title==null){title=new GUIStyle(GUI.skin.label){fontSize=40,fontStyle=FontStyle.Bold,wordWrap=true};text=new GUIStyle(GUI.skin.label){fontSize=19,wordWrap=true};}
            if(art)GUI.DrawTexture(new Rect(Screen.width*.52f,25,Screen.width*.46f,Screen.height-50),art,ScaleMode.ScaleToFit);
            float x=Screen.width*.08f,y=Screen.height*.21f,w=Screen.width*.42f;
            GUI.Label(new Rect(x,y,w,120),"YUUKI\nOs Subúrbios",title);
            GUI.Label(new Rect(x,y+135,w,105),"06:45 da manhã.\nUma caminhada com Tenebris até a Escola Anjos do Testamento.",text);
            if(GUI.Button(new Rect(x,y+265,300,55),"Iniciar caminhada"))SceneManager.LoadScene("Intro_Main");
            GUI.Label(new Rect(x,y+335,w,110),"WASD / setas · andar\nShift + direção · correr   F · ação\nEspaço / Enter · próxima fala   Esc · pausa",text);
            if(GUI.Button(new Rect(x,y+460,140,36),"Sair"))Application.Quit();
        }
    }
}
