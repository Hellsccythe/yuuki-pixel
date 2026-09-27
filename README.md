# Yuuki Pixel

Prototipo 2D independente do RPG de mesa. Este diretorio ja e um projeto Unity 6000.0.82f1; nao e necessario criar outro projeto ou copiar a pasta Assets.

## Testar

Abra D:\yuuki-pixel no Unity Hub e execute a cena Assets/Game/Scenes/YuukiPrototype.unity. Mova com A/D ou setas, segure Shift para correr e use Espaco para pular. O importador de sprites, os clipes, o Animator Controller, a camera e os colisores foram criados e validados pelo Editor em modo batch.

Para testar rapidamente no navegador, sirva a raiz do repositorio com python -m http.server 8765 e abra http://127.0.0.1:8765/preview/game.html. Nessa previa ha um pequeno cenario com plataformas, paginas para recolher e uma biblioteca. preview/directions.html permite pausar e conferir os quadros individualmente. O jogo Unity e a previa usam o mesmo atlas de sprites; o cenario do navegador serve para testar o movimento enquanto a fase Unity e construida.

## Arte e movimento

Assets/Game/Art/Yuuki/Yuuki_Movement_6x6.png tem seis linhas de seis quadros, com celulas transparentes de 512 x 512 pixels: andar esquerda/direita, correr esquerda/direita e pular esquerda/direita. scripts/build_yuuki_atlas.py reproduz a composicao. A caminhada, a corrida e o pulo para a esquerda usam candidatos retocados para limpar o cabelo e os contornos. O repouso tem poses proprias com os dois pes apoiados em Yuuki_Idle_2x1.png. A corrida para a direita aprovada pelo usuario foi mantida sem alteracao pixel a pixel. As fontes anteriores e uma copia do atlas anterior permanecem em Art/Yuuki para comparacao.

As passadas ainda precisam de avaliacao visual: alguns quadros de pernas permanecem muito parecidos. Os fragmentos isolados foram removidos do movimento revisado; nenhuma silhueta atinge a borda da sua celula. O idle e uma pose neutra estatica, ainda sem ciclo de respiracao ou piscada. O pulo duplo fica para a proxima etapa. Veja docs/arte.md para os criterios de revisao e a regra das asas.

## Estrutura

O controle Unity esta em Assets/Game/Scripts/YuukiMovement.cs. O menu Yuuki > Importar atlas de movimento atualiza os dois atlas e os clipes preservando os GUIDs e as referencias do Animator Controller; Yuuki > Criar cena jogavel recria a cena basica. docs/ambientacao.md resume a direcao narrativa e docs/regras-origem.md delimita o que pode ser adaptado da logica de classes, ataques e skills do RPG de mesa.

## Verificacao da revisao v3

O importador compilou e importou 36 sprites de movimento e 2 de repouso no Unity 6000.0.82f1 em uma copia temporaria, sem fechar o editor aberto. Os arquivos importados foram sincronizados de volta preservando os GUIDs existentes. Os clipes sustentam o ultimo quadro pelo intervalo completo e o pulo usa a velocidade vertical para escolher a fase. No navegador, scripts/verify_preview.cjs verifica repouso, caminhada, corrida e os seis quadros de pulo nas duas direcoes, sem erros de carregamento ou JavaScript. O script requer Node, Playwright, Edge e o servidor local na porta 8765.
