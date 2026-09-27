using UnityEngine;

// Stairs or a hidden passage to another map, used on purpose with F (the dungeon entrance
// and its way back up).
public sealed class YuukiStairs : YuukiInteractable
{
    public string destinationName;
    public string targetMap;
    public Vector2 target;

    private void Reset() { prompt = "Descer"; }

    public override bool Available => YuukiBairro.Instance != null && !YuukiBairro.Instance.TransitionBusy;

    public override void Interact()
    {
        var map = YuukiBairro.Instance;
        if (map == null) return;
        if (!string.IsNullOrEmpty(targetMap) && Application.CanStreamedLevelBeLoaded(targetMap))
            map.LoadMap(targetMap, target);
        else
            map.Toast(destinationName + " ainda não está disponível.");
    }
}
