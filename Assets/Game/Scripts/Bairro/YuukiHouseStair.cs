using UnityEngine;

// House floors share one footprint and are preloaded; these stairs never load a scene.
public sealed class YuukiHouseStair : YuukiInteractable
{
    public YuukiCutawayHouse house;
    public int targetFloor;
    public Vector2 landing;
    public override bool Available => house != null && house.Inside && !house.Transitioning;
    public override void Interact()
    {
        if(Available) house.TryChangeFloor(targetFloor,landing);
    }
}
