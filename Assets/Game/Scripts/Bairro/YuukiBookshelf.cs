using UnityEngine;

// A bookshelf or a pile of books. F opens the list of the books it holds.
public sealed class YuukiBookshelf : YuukiInteractable
{
    public string shelfName = "Estante";
    public string[] bookIds = new string[0];  // ids from Resources/Livros/biblioteca.json

    private void Reset() { prompt = "Ver livros"; }

    public override void Interact()
    {
        if (YuukiBairro.Instance != null)
            YuukiBairro.Instance.ShowBooks(shelfName, YuukiBookLibrary.Resolve(bookIds));
    }
}
