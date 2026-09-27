# Prompts de arte do bairro (NPCs, distrito comercial, escola)

Prompts no mesmo formato de `prompts.md` (usados pelo Codex no ImageGen), para gerar a arte que falta. Depois de gerar, salve os originais em `Art/World/Sources/` e me avise: o recorte, a limpeza da transparência e o encaixe no jogo ficam por conta dos scripts em `scripts/bairro/`.

## Regras comuns (valem para todos)

- **Perspectiva**: clássica de RPG vista de cima em 3/4, câmera ortográfica olhando para baixo a ~45° em direção ao norte. Nada de isométrico em losango nem de vista lateral de plataforma. Personagens seguem o mesmo 3/4 dos sprites da Yuuki.
- **Estilo**: pixel art 32-bit, detalhada, com clusters de pixels feitos à mão; sem pintura digital suave, sem antialias borrado, sem gradientes ou brilhos.
- **Paleta**: tarde quente e poeirenta, nogueira gasta, reboco creme sujo, terracota desbotada, ardósia, musgo. Periferia **pobre**: remendos, tinta descascada, rachaduras e manchas de chuva, mas com sinais de cuidado, gente vivendo ali.
- **Fundo**: transparente de verdade, sem sombra fora da silhueta, sem texto, sem UI, sem grade desenhada.
- **Mundo**: todos são anjos. As asas são brancas; **só a Yuuki tem uma asa preta**, e isso não pode se repetir em nenhum NPC. Todos têm auréola dourada fina.

## Personagens (NPCs)

Formato de cada folha: **6 colunas x 4 linhas, células de 512 x 512 px (3072 x 2048)**, fundo transparente, personagem centralizado com os pés sempre na mesma altura (~400 px a partir do topo da célula), altura do corpo ~280 px em proporção chibi igual à da Yuuki, 35 px de margem livre em cada célula.
Linhas, de cima para baixo: **andar para a esquerda (6 quadros), andar para a direita (6), andar para baixo/sul (6), andar para cima/norte (6)**. Quando o repouso for pedido, ele vai numa folha separada: 4 células (esquerda, direita, baixo, cima).
Cada direção é desenhada de verdade, sem espelhamento automático (as asas mudam de lado).

Texto base para colar antes da descrição do personagem:

> Production game character sprite sheet for a CLASSIC TOP-DOWN 3/4 pixel-art RPG, same chibi proportions and rendering as the provided reference character (petite, big head, detailed 32-bit pixel clusters, dark outline). Exactly 6 columns x 4 rows on a 3072x2048 transparent canvas, 512x512 cells. Row 1 walk cycle facing LEFT, row 2 walk cycle facing RIGHT, row 3 walk cycle facing DOWN toward the camera, row 4 walk cycle facing UP away from the camera. Feet on the same baseline in every cell, alternating legs, readable silhouette at small size. Angel with thin golden halo and two WHITE feathered wings. No text, no background, no shadow blob, no cell borders.

### Personagens da história

| Arquivo sugerido | Descrição para o prompt |
| --- | --- |
| `npc-tenebris.png` | Menino anjo de 9 anos, amigo de infância e vizinho da Yuuki. Cabelo branco curto e sempre desarrumado, olhos dourados intensos, expressão fechada de quem não leva desaforo. Roupa simples de periferia: camisa de linho cor de areia com remendo no cotovelo, bermuda marrom, suspensório gasto, botinas surradas. Asas brancas um pouco eriçadas. Postura firme, protetora. |
| `npc-alice.png` | Menina anja de 9 anos de família nobre. Cabelos pretos longos e muito bem cuidados, olhos azuis, vestido preto com detalhes azuis e renda, bem feito demais para a periferia; sapatos de verniz, laço azul. Asas brancas imaculadas. Curiosa, olhar atento. |
| `npc-sara.png` | Mãe da Yuuki, jovem mas cansada. Cabelo loiro-claro até a cintura, olhos azuis suaves, ~1,71 m. Camisa branca de manga longa, saia preta, meia-calça escura, sapatos azul-escuro. Asas brancas. Porte gentil. |
| `npc-kled.png` | Pai da Yuuki. Cabelo preto até os ombros, olhos vermelhos, ~1,78 m. Camisa preta, calça preta, cinto preto; roupas casuais e gastas de trabalhador. Asas brancas. Expressão jovem apesar do cansaço. |

### Moradores (substituem as silhuetas provisórias)

Os nomes batem com as pastas em `Assets/Game/Bairro/Sprites/NPC/`.

| Pasta | Descrição para o prompt |
| --- | --- |
| `morador` | Homem anjo adulto trabalhador, camisa de algodão cru com mangas arregaçadas, colete marrom remendado, calça de lona, botas gastas, barba por fazer. |
| `idosa` | Senhora anja idosa, costas levemente curvadas, xale de lã cinza, vestido longo desbotado, lenço na cabeça, bengala de madeira simples. |
| `idoso` | Senhor anjo idoso, boina, suspensórios sobre camisa amarelada, calça larga, andar lento, bengala. |
| `lavadeira` | Mulher anja com avental manchado, mangas arregaçadas, saia marrom, lenço prendendo o cabelo, cesto de roupa na cintura. |
| `vizinha` | Jovem mãe anja, vestido simples verde-oliva desbotado, avental, cabelo preso num coque bagunçado. |
| `artesao` | Carpinteiro/ferreiro anjo, avental de couro com marcas de queimado, luvas grossas, braços fortes, fuligem no rosto. |
| `andarilho` | Anjo andarilho magro, capa curta puída, chapéu de aba larga, trouxa no ombro, sandálias. |
| `crianca-a` / `crianca-b` / `crianca-c` | Crianças anjas de 6 a 8 anos, roupas grandes demais herdadas dos irmãos, joelhos ralados, descalças ou com sandálias; cores de roupa diferentes (verde, azul, vermelho desbotado). |

## Distrito comercial (mapa 4) — lojas

Formato: **folha de 3 colunas x 2 linhas, 1536 x 1024, uma fachada por célula de 512 x 512**, 20 px de margem, mesma vista 3/4 das casas atuais (`buildings-topdown.png`): telhado com profundidade visível, porta virada para o sul (para baixo), paredes laterais aparecendo um pouco. Todas as lojas **pequenas, velhas e modestas**.

> Adapt to a proper CLASSIC TOP-DOWN 3/4 RPG GAME BUILDING TILESET, viewed from high above at a fixed 45-degree downward orthographic camera, looking NORTH at southern facades. NOT isometric, NOT side view. Grid exactly 3 columns x 2 rows, 1536x1024, transparent background, six isolated small shop buildings of a POOR angel-city outskirts market street, fully inside cells with 20px margins, all doorways facing south. Crisp hand-placed pixel clusters, limited warm dusty palette, patched roofs, peeling paint, rain stains, cracked plaster, but lived-in and cared for. No characters, no readable text (signs use simple pictograms only), no background, no ground.

| Célula | Loja | Descrição |
| --- | --- | --- |
| 1 | **Padaria** | Casinha de tijolo e reboco rachado, forno de barro saindo pela lateral com chaminé fumegante, balcão de madeira na janela com pães redondos e cestos de vime, toldo listrado bege e vinho desbotado e remendado, placa com pictograma de pão. |
| 2 | **Loja de roupas / costureira** | Sobrado estreito de madeira, vitrine pequena com manequim de pano e rolos de tecido, varal de roupas à venda sob o beiral, toldo azul desbotado, placa com pictograma de agulha e linha. |
| 3 | **Mercearia / quitanda** | Térreo largo com portas duplas abertas, caixotes de legumes e frutas na calçada, sacos de grãos, balança de ferro, telhado de telha com remendos de zinco, placa com pictograma de maçã. |
| 4 | **Barraca de comida** | Barraca de rua de madeira com fogareiro, panela de sopa fumegante, bancos toscos, lona remendada por cima, lanterna de papel. |
| 5 | **Sapateiro / consertos** | Oficina mínima com meia-porta, sapatos pendurados, bancada com ferramentas, janela com vidro trincado, placa com pictograma de bota. |
| 6 | **Taverna simples** | Construção de pedra e madeira um pouco maior, porta de vaivém, barris empilhados na lateral, janelas com luz âmbar, placa com pictograma de caneca. |

Objetos extras do distrito (folha 3x3 no formato de `props-topdown.png`): carrinho de mão com verduras, bancada de feira com toldo, pilha de sacos de farinha, barril com peixes, caixotes de frutas, cesto de pães, lampião de rua torto, bebedouro de pedra, placa de madeira em branco.

## Escola do bairro (mapa 1, ao norte) — antiga e pobre

**Fachada principal**, célula única 1024 x 1024:

> CLASSIC TOP-DOWN 3/4 pixel-art RPG, orthographic 45-degree camera looking NORTH. One complete standalone OLD POOR NEIGHBOURHOOD SCHOOL building of an angel city outskirts: two storeys, cracked cream plaster over grey stone, faded tiny wing-shaped stone crest above a central arched double door (south), symmetrical tall windows with a few broken panes patched with boards, small bell tower with a green-stained bronze bell, patched terracotta roof with missing tiles and moss, rusty gutter, peeling blue paint on shutters, worn stone steps. Humble but dignified, clearly underfunded compared with the rich central academy. Transparent background, no characters, no text, crisp 32-bit pixel clusters, warm dusty afternoon palette.

**Anexos e pátio**, folha 3x3 no formato de `props-topdown.png`:
cerca de pátio de ferro enferrujado com portão, banco escolar comprido de madeira, bebedouro de pedra, amarelinha riscada no chão (decalque), árvore grande velha com balanço de corda, galpão de lenha, sino de mão num poste, carteira quebrada encostada, canteiro seco.

**Interior (sala de aula + biblioteca)**, folha 3x3 com fundo transparente, mesma perspectiva dos móveis atuais:
carteira dupla de madeira gasta, mesa do professor com pilha de livros e tinteiro, quadro-negro rachado na parede, estante alta de biblioteca abarrotada de livros velhos, estante baixa com livros tombados, mesa de leitura comprida com lamparina, escada de biblioteca de madeira, globo antigo desbotado, caixote de livros doados.

A **biblioteca** é o refúgio da Yuuki e do Tenebris na história: vale caprichar em livros velhos, poeira dourada na luz da janela e cantinhos de leitura.
