# Yuuki Pixel
Projeto independente para um jogo 2D pixelado na Unity. Fase inicial: arte e validacao de animacoes.

## Estado real
**As duas folhas em Art/Experiments sao rascunhos, nao sprites finais aprovados.**
A identidade visual se aproxima da referencia, mas as asas ainda trocam de cor em alguns frames, existem residuos de cor e a continuidade precisa de retoque. Nao usar flipX: a asa esquerda anatomica e preta; a direita e branca.
Nao ha jogo executavel nem regras portadas ainda.

## Ver as animacoes
Abra preview/index.html no navegador, escolha a folha e o movimento. Pause e avance quadro a quadro para conferir o cajado, as asas e a continuidade.
As seis linhas propostas sao: andar esquerda, andar direita, correr esquerda, correr direita, pular esquerda, pular direita. Cada linha tem seis frames. A divisao regular e uma hipotese de trabalho, nao uma garantia de que a IA alinhou cada desenho.

## Testar na Unity
Crie um projeto 2D na versao de Unity que voce usa. Copie Assets/Editor/YuukiAtlasImporter.cs para Assets/Editor desse projeto e uma folha experimental para Assets/Art.
Selecione a textura e execute Yuuki > Criar clipes experimentais.
O importador preserva o arquivo original, define Point/sem compressao, fatia 36 sprites e cria seis AnimationClips em pasta nova. Ele nao corrige a arte. Use o mesmo PPU em todos os assets.
O importador ainda precisa de compilacao e validacao no Unity Editor; nenhum teste no editor foi executado nesta etapa.

## Escopo
Apenas classes, ataques e skills do RPG de mesa servirao como referencia para a logica futura. Sem dependencia de NestJS, banco, autenticacao ou servidor do RPG.
Veja docs/regras-origem.md e docs/arte.md.
