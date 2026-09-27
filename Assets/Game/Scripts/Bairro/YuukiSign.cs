using UnityEngine;

// A sign (or anything worth a closer look) that shows a short text when read with F.
public sealed class YuukiSign : YuukiInteractable
{
    public string title;
    [TextArea(2, 6)] public string text;

    private void Reset() { prompt = "Ler"; }

    public override void Interact()
    {
        if (YuukiBairro.Instance != null) YuukiBairro.Instance.ShowMessage(title, text);
    }
}
