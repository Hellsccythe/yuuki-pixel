# Yuuki para a esquerda
Trabalho solicitado: reaproveitar caminhada aprovada e corrida/pulo da imagem anexada, espelhar cada quadro sem reverter a ordem temporal e trocar as cores das asas.
Somente esquerda nesta etapa; pulo duplo fora da selecao ativa.

## Fontes e resultado
- Caminhada direita aprovada: terceira linha de ../Right/walk-approved-source.png, preservada sem alteracao.
- Caminhada esquerda: primeira linha de walk-left-source-v1.png.
- Corrida esquerda: primeira linha de run-jump-left-v2.png.
- Pulo esquerda: segunda linha de run-jump-left-v2.png.
As demais linhas da primeira tentativa nao estao selecionadas.

## Metodo e prompt
Ferramenta integrada image_gen, edicao com referencias, nao espelhamento deterministico.
Prompt da primeira tentativa: usar somente linha 3 da fonte de caminhada e linhas 1/2 da fonte de corrida/pulo. Espelhar individualmente cada celula, manter ordem dos seis frames. Recolorir somente penas: asa grande proxima preta/carvao e pequena distante branca/cinza claro. Preservar rosto, cabelo, vestido, cajado, escala, poses e transparencia; nunca incluir pulo duplo. Grade 6x3.
Correcao da segunda tentativa: usar somente corrida e pulo da imagem anexada, grade 6x2. Copiar exatamente as poses das pernas e alturas originais refletidas, contato/compressao/passagem/contato oposto na corrida; agachar/impulso/subida/apice/descida/aterrissagem no pulo. Mesma troca de cores apenas nas asas.

## Revisao
A disposicao das cores das asas ficou correta visualmente, mas a ferramenta alterou poses/pixels e o espacamento. Nao afirmar equivalencia pixel a pixel.
Algumas figuras ficaram muito proximas das bordas externas; verificar cortes e componentes antes de exportar para Unity. Existem residuos coloridos no contorno.
preview/directions.html mostra as duas direcoes com o mesmo indice de quadro para comparacao. Fatiamento regular no preview e provisório, nao prova de corte correto. Nao aplicar o importador antigo 6x6.
