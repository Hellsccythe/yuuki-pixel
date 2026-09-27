using System;
using System.Collections.Generic;
using UnityEngine;

// Readable books of the game, registered in Assets/Game/Resources/Livros/biblioteca.json.
// Each bookshelf lists the ids it holds; unknown or missing books show as "Sem registro".
//
// Format:
// { "livros": [ { "id": "diario-sara", "titulo": "...", "autor": "...",
//                 "resumo": "...", "paginas": ["texto da página 1", "texto da página 2"] } ] }
[Serializable] public sealed class YuukiBook
{
    public string id, titulo, autor, resumo;
    public string[] paginas = new string[0];
}

[Serializable] public sealed class YuukiBookCollection
{
    public YuukiBook[] livros = new YuukiBook[0];
}

public static class YuukiBookLibrary
{
    private static Dictionary<string, YuukiBook> books;

    public static int Count { get { Load(); return books.Count; } }

    private static void Load()
    {
        if (books != null) return;
        books = new Dictionary<string, YuukiBook>();
        var asset = Resources.Load<TextAsset>("Livros/biblioteca");
        if (asset == null) return;
        var data = JsonUtility.FromJson<YuukiBookCollection>(asset.text);
        if (data?.livros == null) return;
        foreach (var book in data.livros)
            if (book != null && !string.IsNullOrEmpty(book.id)) books[book.id] = book;
    }

    public static YuukiBook Find(string id)
    {
        Load();
        return id != null && books.TryGetValue(id, out var book) ? book : null;
    }

    // Books a shelf actually has registered. An empty result means "Sem registro".
    public static List<YuukiBook> Resolve(string[] ids)
    {
        Load();
        var list = new List<YuukiBook>();
        if (ids == null) return list;
        foreach (var id in ids)
        {
            var book = Find(id);
            if (book != null) list.Add(book);
        }
        return list;
    }
}
