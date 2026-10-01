# Yuuki criança — corrida esquerda v5

Revisão de 30/09/2026 solicitada pelo usuário: as pernas de cada quadro da corrida direita aprovada (v3) foram copiadas literalmente e refletidas para a corrida esquerda. Não houve geração de imagens, escala, deformação, interpolação, mudança de cor ou mistura de alpha. Pequenos deslocamentos inteiros encaixam os quadris sob a saia existente; as máscaras preservam o restante do corpo e as asas da esquerda v4.

Apenas run_left mudou: quatro quadros, mesma ordem 1 → 2 → 3 → 4, 8 FPS e mesmas âncoras da auréola. As outras onze animações, incluindo andar para a esquerda v4, estão aprovadas e foram preservadas. Os 155 arquivos da Yuuki adulta também passaram pela verificação de integridade.

- Aplicar a correção: python scripts/copy_child_yuuki_run_legs.py.
- leg-copy-v5.json: polígonos, deslocamentos e hashes das fontes aprovadas. Coordenadas em pixels, origem no canto superior esquerdo; máscaras da fonte já no espaço refletido.
- Revisions/run-left-v5/: catálogo anterior, máscaras, recortes exatos das pernas, comparação e verificações.
- Recursos atuais de corrida esquerda: run_left_v5_00 até 03. As versões anteriores continuam guardadas.
- A prévia abre diretamente em Correr / Esquerda / 1×. A avaliação de fluidez pelo usuário continua pendente.

## Histórico — esquerda v4

Revisão de 30/09/2026: somente andar e correr para a esquerda foram refeitos com ImageGen integrado, usando as poses aprovadas da direita como referência refletida. Asa próxima preta, asa distante branca; cabelo e roupa continuam nas cores originais. Quatro quadros por ciclo, 6 FPS ao andar e 8 FPS ao correr.

A direita, frente, costas e o idle foram aprovados pelo usuário e permaneceram idênticos, assim como os 155 arquivos preservados da Yuuki adulta. A nova esquerda aguarda avaliação visual na prévia.

- Configuração atual da esquerda: left-from-right-v4.json.
- Prompt e origem da arte: left-from-right-v4-prompt.json.
- Fonte final: Sources/left-from-approved-right-v4.png.
- Referência aprovada: Sources/right-approved-v3-reference.png.
- Recursos novos: Assets/Game/Resources/Childhood/Yuuki/Frames/walk_left_v4_00 até 03 e run_left_v4_00 até 03.
- Catálogo anterior e verificação: Revisions/left-v4/.
- Aplicar somente esta revisão: python scripts/revise_child_yuuki_motion.py left-from-right-v4.json.
- O empacotamento completo aplica v3 e depois v4. As fontes e os sprites antigos continuam preservados.

## Base preservada — v3

Modelo e auréola Yuuki-v2 aprovados em 29/09/2026. Sem armas.
Asa esquerda anatômica preta, direita anatômica branca. Nenhum playback usa espelhamento.

## Ciclos atuais

- Andar de frente: os quatro desenhos aprovados, sem alterações, 5 FPS.
- Andar de costas: os seis desenhos aprovados, sem alterações, 7 FPS.
- Andar para esquerda/direita: quatro desenhos novos em cada direção, 6 FPS.
- Correr: quatro desenhos novos em cada uma das quatro direções, 8 FPS.
- Respiração: os três desenhos existentes por direção, ciclo 0 → 1 → 2 → 1, 2 FPS.

São 46 desenhos usados em 12 animações. As caminhadas laterais e corridas usam passadas menores e registro fixo dos olhos/linha do cabelo. Uma escala constante por folha evita esticar os desenhos. Não há mistura de imagens nem interpolação de poses.
A revisão v3 está aprovada, exceto a esquerda: caminhada v4 aprovada e corrida v5 aguardando avaliação. Versões anteriores, desenhos aprovados e todos os arquivos da Yuuki adulta continuam preservados.

## Arte e configuração

- Sources/: folhas originais do ImageGen integrado, incluindo tentativas anteriores. As folhas *compact-v3* fornecem a revisão atual; *refined* corrige duas poses que repetiam o apoio da mesma perna.
- motion-four-frame-v3.json: fontes, cadência e registro dos ciclos atuais.
- motion-four-frame-v3-prompts.json: prompts iniciais e correções específicas.
- motion-v3-outputs.json: nomes dos resultados selecionados da ferramenta integrada.
- Revisions/motion-v3/catalog-before.json: catálogo anterior a esta revisão.
- Revisions/motion-v3/asset-checks.json: verificação dos arquivos preservados e amplitude vertical do registro.
- packing-report.json: limites, recursos e layout das folhas.
- Atlases/: uma folha por direção, células 512 × 512. Linha 1 andar, linha 2 correr, linha 3 idle. Células sem desenho são transparentes. O relatório registra o recurso de cada célula.
- contact-sheet.png: conferência dos 46 desenhos usados.
- Revisions/lateral-v2/, lateral-revision.json e fontes antigas: histórico preservado.

## Unity

PNGs e catálogo: Assets/Game/Resources/Childhood/Yuuki.
Corpo: célula 512 × 512, pivô (0.5, 0.21875), apoio dos pés (256,400), 220 pixels por unidade. Filtro Point, sem mipmaps ou compressão.
animations.json fornece frames, sequence, FPS e haloAnchors. Os índices de sequence se referem às listas de recursos e âncoras. Respeitar essa ordem, inclusive no idle.
Auréola neutra 96 × 28 num SpriteRenderer próprio; aplicar cor preservando o alpha. A âncora usa pixels com origem superior esquerda. Posição local Unity: ((anchor.x-256)/220, (400-anchor.y)/220).

## Prévia

http://127.0.0.1:8765/preview/childhood-animation.html
Escolher direção e animação, pausar e avançar quadros. Velocidade padrão 1×.
Clicar no canvas e usar WASD/setas; Shift corre. Soltar retorna ao idle.
Esta etapa revisa os assets; a integração nas cenas Unity continua pendente.

## Reprodução

scripts/revise_child_yuuki_motion.py aplica somente a revisão v3 a partir das folhas locais e verifica os arquivos protegidos.
scripts/pack_child_yuuki.py reempacota as fontes originais e aplica automaticamente v3, v4 e a cópia de pernas v5 ao final, quando as configurações estão presentes.
Requer Pillow, numpy e scipy. As etapas anteriores extraem e registram os desenhos gerados. A etapa v5 faz a cópia de pixels autorizada pelo usuário; não redesenha ou deforma partes do corpo. Para reaplicar apenas o ajuste atual, use copy_child_yuuki_run_legs.py.
