# Sara — animações v1

Design da mãe aprovado pelo usuário. Esta sequência de movimentos foi aprovada pelo usuário em 2026-10-01.

- Andar: quatro quadros por direção, 6 fps.
- Correr: quatro quadros por direção, 8 fps.
- Respiração parada: três desenhos por direção, ordem 1 → 2 → 3 → 2, 2 fps.
- Quatro direções, 12 clips e 44 arquivos de quadros, em PNG RGBA de 512 × 512.
- A esquerda é a reflexão exata da direita. Frente e costas usam contato e passagem dos pés e suas reflexões para garantir as fases opostas.
- Auréola separada, translúcida (opacidade 0,6), com cores livres; o corpo não contém auréola.
- Pivô nos pés (256, 400), 220 pixels por unidade, Point, sem mipmaps e sem compressão.

`Sources/` guarda as seis folhas selecionadas; `Atlases/` tem uma folha 4 × 3 por direção (andar, correr, respirar). `contact-sheet.png` permite conferir os quadros. Os PNGs separados e o catálogo estão em `Assets/Game/Resources/Parents/Sara/`.

O empacotamento reutiliza a limpeza de fragmentos do pipeline aprovado da Alice, encontra espaços transparentes entre poses, mantém uma escala constante por linha, recorta e alinha com nearest-neighbor e reflete as poses. Não desenha membros nem aplica interpolação borrada. Os originais selecionados são preservados.

Geração: ImageGen integrada. Prompts e seleção em `production-prompts.json`; métricas em `packing-report.json` e `final-qa.json`.

Prévia interativa: `http://127.0.0.1:8765/preview/sara-animation.html`. WASD/setas movem, Shift corre; botões permitem pausar e avançar quadro por quadro. Os assets ainda não foram integrados às cenas do jogo.

Designs aprovados de Sara e Kled guardados com manifests e backups. Yuuki, Alice e Tenebris preservados. Aprovação de designs não implica aprovação destes novos movimentos.
