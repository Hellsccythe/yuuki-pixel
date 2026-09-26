# Direcao de arte e revisao
Yuuki: anja jovem (16-18), petite em proporcao chibi, cabelo branco, olhos vermelhos, vestido gotico branco com detalhes pretos, aureola, cajado preto com gema vermelha.
Manter figurino e aderecos fixos entre movimentos; nao alternar capuz espontaneamente.
Asa esquerda anatomica preta, direita branca. Na vista esquerda a asa proxima e preta; na direita a proxima e branca. Nao espelhar a folha.
Folha proposta: 6 linhas x 6 colunas, andar E/D, correr E/D, pular E/D. Andar e correr em loop; pulo: antecipacao, impulso, subida, apice, descida, aterrissagem.
Margem deve acomodar toda a arma/asas em cada frame. Tamanho constante do corpo, pivô fixo; nao normalizar bbox individualmente (isso altera a escala e apaga o movimento).
Gerado com a ferramenta integrada image_gen, usando a imagem do usuario como referencia de identidade. V1 e V2 sao tentativas, nao resultados aprovados.
Prompt resumido: "Production pixel-art 6x6 animation atlas, six chronological frames per movement and direction; fixed Yuuki identity, white hair/red eyes, same dress/staff/halo; anatomical left wing black, right wing white; genuine transparent alpha; complete silhouette with margin; no labels, no checkerboard."
Revisao V2: "Recolor entire near wing white in ALL right-facing cells, far wing black; retain opposite arrangement in left-facing cells; remove stray red/magenta pixels; preserve poses."
Falhas visuais ainda presentes: cores das asas inconsistentes entre alguns quadros; residuos vermelhos/magenta; grade e escala nao validadas; ciclos nao aprovados.
Criterio de aceite: revisar os seis clipes em movimento e quadro a quadro, checar cores anatomicas, estabilidade do rosto/roupa/cajado, contato dos pes, cortes e alpha em fundos claro/escuro. Testar transicoes na Unity antes de chamar de pronto.
