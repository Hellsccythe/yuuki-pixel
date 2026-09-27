# Bairro da Yuuki — mapas modulares

Jogo em vista de cima no estilo Stardew Valley: Yuuki anda livremente em X e Y (8 direções) e colide só pelos pés. Não há gravidade nem ground check. Buracos são bloqueios no chão; um pulo futuro vai ignorá-los por um instante em vez de lançar a personagem para cima.

![Prévia da Rua de Casa](rua-de-casa-preview.png)

## Os quatro mapas

| Mapa | Estado | Ligação |
| --- | --- | --- |
| **Rua de Casa** — casa da Yuuki, casa do Tenebris (vizinho), o beco da história, pracinha do poço | **pronto** (este) | centro |
| Escola do bairro — antiga e pobre, com a biblioteca | a fazer | saída norte |
| Moradias — casas simples de madeira | a fazer | saída oeste |
| Distrito comercial — lojinhas de roupa, comida, padaria | a fazer | saída leste |

As saídas já existem nas bordas da Rua de Casa: mostram "em breve" e bloqueiam a passagem até o mapa vizinho existir.

## O que a Rua de Casa tem

- Ruas de terra batida com marcas de roda, rachaduras, pedrinhas, lixo e manchas; trechos de calçamento velho com pedras faltando; mato seco e falhado.
- Casas envelhecidas a partir das artes do Codex: cor desbotada, escorrido de chuva, barro na base, rachaduras e janelas pregadas com tábuas. A casa da Yuuki é velha mas bem cuidada (portão antigo, varanda, vaso de flores, horta dos pais), como na história.
- O beco do capítulo "O beco": chão de terra, muros rachados, cerca de madeira torta e caixotes empilhados no fundo.
- Muros baixos rachados ao longo da rua, lote baldio, varal com roupas remendadas, poço, bancos, placas.
- Buracos (bloqueiam a passagem) e poças com reflexo do céu (dá para pisar).
- Vento: rajadas que atravessam o mapa de oeste para leste e balançam árvores, mato e roupas no varal; folhas, poeira e páginas soltas voando; sombras de nuvem passando; fumaça das chaminés dobrando com o vento.
- Vida: 7 moradores andando (patrulha ou passeio aleatório, param quando a Yuuki está no caminho e se viram para olhar para ela) e bandos de pombos que levantam voo quando ela se aproxima.
- Interior da casa da Yuuki: entra-se andando até a porta, com fade. Cama, duas estantes e pilhas de livros, fogão aceso, mesa com livro e caneca, tapete remendado, luz da janela.

## Como abrir no Unity

1. Abra o projeto e espere a compilação (o `Packages/manifest.json` agora inclui `jsonserialize`, `particlesystem` e `audio`; isso também corrige o erro `JsonUtility does not exist` do protótipo antigo).
2. Menu **Yuuki > Bairro > Construir Rua de Casa**. O construtor configura a importação dos sprites (PPU, pivô, Point, sem compressão) e cria `Assets/Game/Scenes/Bairro_RuaDeCasa.unity`.
3. Aperte **Play**. WASD ou setas para andar, Shift para correr.

Reconstruir recria a cena do zero. Para mudar o mapa, edite o layout em `scripts/bairro/build_rua_de_casa.py` e rode de novo; se preferir ajustar à mão na cena, pare de reconstruir.

## Regerar a arte e o layout

```bash
pip install pillow numpy scipy
python3 scripts/bairro/build_rua_de_casa.py   # sprites, chão pintado, JSON e esta prévia
python3 scripts/bairro/validate_map.py        # colisões, porta, saídas e rotas dos NPCs
```

O gerador é determinístico. Coordenadas de desenho em tiles (1 tile = 1 unidade Unity, x para a direita e y para baixo); o JSON sai em coordenadas Unity (y para cima). A escala segue o Stardew: Yuuki com ~1,6 tile de altura e portas com ~1,8 tile. `rua-de-casa-colisao.png` mostra em verde onde a Yuuki consegue andar a partir do spawn.

## NPCs provisórios

Não há sprites gratuitos de NPC com a qualidade da Yuuki (os pacotes livres são pixel art de 16–32 px, em outro estilo). Por isso os moradores são **silhuetas sépia** geradas a partir da animação da Yuuki: servem para testar movimento, rotas e densidade, mas não copiam as cores dela (a asa preta continua sendo só dela).

Para trocar por sprites de verdade, substitua os PNGs em `Assets/Game/Bairro/Sprites/NPC/<morador>/` mantendo os nomes (`walk_left_00..05`, `walk_right_00..05`, `idle_left_00`, `idle_right_00`), com o pé na mesma altura, ou aponte novos arquivos no JSON. Quando existirem animações para cima e para baixo, o `YuukiNpcWalker` e o `YuukiPlayerTopDown` só precisam receber os quadros extras.

## Scripts

| Arquivo | Função |
| --- | --- |
| `Assets/Game/Scripts/Bairro/YuukiPlayerTopDown.cs` | Movimento livre em X/Y, correr, animator (mantém o último lado ao andar para cima e para baixo) |
| `YuukiBairro.cs` | Áreas do mapa, viagem com fade, nome do lugar, avisos |
| `YuukiBairroCamera.cs` | Câmera suave presa aos limites da área; interiores pequenos ficam centralizados |
| `YuukiPortal.cs` / `YuukiMapExit.cs` | Porta de entrar andando / borda para o próximo mapa |
| `YuukiWind.cs`, `YuukiWindSway.cs`, `YuukiWindFx.cs`, `YuukiChimneySmoke.cs` | Vento compartilhado, balanço, partículas, nuvens, fumaça |
| `YuukiNpcWalker.cs`, `YuukiPigeonFlock.cs` | Moradores e pombos |
| `Assets/Editor/Bairro/YuukiBairroBuilder.cs` | Menu que monta a cena a partir do JSON |

A profundidade usa o eixo Y da câmera (Custom Axis 0,1,0) com o pivô de cada sprite nos pés: quem está mais abaixo na tela é desenhado na frente, e a Yuuki passa por trás dos telhados.
