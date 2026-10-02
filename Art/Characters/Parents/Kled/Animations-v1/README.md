# Kled — animações v1

Modelo adulto aprovado: cabelo preto em camadas, olhos vermelhos, brincos, roupa preta e duas asas brancas. Esta primeira passagem das animações aguarda avaliação do usuário.

- Andar: quatro quadros por direção, 6 fps.
- Correr: quatro quadros por direção, 8 fps.
- Respiração: três desenhos por direção, ciclo 1 → 2 → 3 → 2, 2 fps.
- Frente e costas têm desenhos próprios. Esquerda espelha exatamente a direita em torno do pivô.
- Corpo RGBA 512 × 512, apoio (256, 400), 220 pixels por unidade, Point, sem mipmaps e sem compressão.
- Auréola do modelo aprovado preservada como camada independente: opacidade 0,6 aplicada ao renderizar, cor livre.

`Sources/`: seis originais do ImageGen integrado. `Atlases/`: uma folha por direção; linhas andar, correr e respiração. `production-prompts.json`: instruções completas e fontes. `packing-report.json` e `final-qa.json`: recortes, registro e verificações. `preview-proof.png`: captura da prévia testada.

Recursos: `Assets/Game/Resources/Parents/KledV2/Frames/`, com catálogo `animations.json`. Prévia: `preview/kled-animation.html` (WASD/setas, Shift para correr, soltar para respirar).

Sara e os desenhos já aprovados da infância e da Yuuki adulta continuam preservados. As animações ainda não foram inseridas nas cenas do jogo.
