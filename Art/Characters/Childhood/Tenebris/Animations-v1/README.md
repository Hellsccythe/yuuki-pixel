# Tenebris criança — primeira sequência para revisão

Mantém a aparência infantil aprovada, inspirada no penteado e postura de Kiryu: cabelo preto, olhos dourados, jaqueta clara remendada sobre camisa vinho, bermuda escura, meias escuras, botas marrons e duas asas brancas. Não carrega armas. A cor do cabelo foi alterada conforme pedido; a referência anterior permanece em `Approved-reference/`.

## Quadros e importação

- Quatro direções: frente, costas, esquerda e direita.
- Andar: quatro desenhos por direção, 6 fps, ciclo 1–2–3–4.
- Correr: quatro desenhos por direção, 8 fps, ciclo 1–2–3–4.
- Idle com respiração: três desenhos por direção, 2 fps, ciclo 1–2–3–2.
- 44 PNGs transparentes de 512 × 512, com importação Unity em Point, sem mipmaps nem compressão; 220 pixels por unidade e pivô (0,5; 0,21875).

A esquerda espelha exatamente os quadros da direita em torno do pivô do corpo. A escala é constante dentro de cada clipe e usa a largura do cabelo para evitar mudanças de tamanho da cabeça entre estados. Não há esticamento separado das pernas. A referência de movimento e acabamento foi a Alice aprovada.

Os quadros de caminhada de frente e costas foram corrigidos com ImageGen para alternar os pés. A corrida frontal tem uma folha própria de quatro quadros. O idle frontal usa os desenhos completos da primeira fonte, porque a folha corretiva veio com pontas das botas cortadas nessa linha. As fontes selecionadas e anteriores estão preservadas em `Sources/`.

## Auréola independente

`Assets/Game/Resources/Childhood/Tenebris/halo-neutral.png` é uma camada neutra recolorível com transparência. A proposta tem dois anéis, um pequeno losango frontal e dois traços discretos. As posições por quadro estão em `animations.json`. O desenho aguarda aprovação e deverá ser mantido na versão adulta depois de aprovado.

## Testar e reproduzir

Abra `http://127.0.0.1:8765/preview/tenebris-animation.html`: movimento, direção, velocidade 1×, seleção de quadros e cor da auréola. Clique na prévia e use WASD/setas para mover, Shift para correr. `tenebris-design.html` mostra a pose de referência. A integração nas cenas Unity fica após a avaliação visual dos movimentos.

Artes feitas com a ferramenta integrada ImageGen. `production-prompts.json` registra os prompts, fontes e seleção final. `packing-report.json` registra margens, alinhamento e verificações de preservação. `Atlases/` tem as folhas consolidadas, com linhas andar/correr/idle e células 512 × 512; `contact-sheet.png` mostra todos os quadros.

Reconstrua com `scripts/pack_child_tenebris.py`, usando Python, Pillow e NumPy. O script verifica os manifestos da Yuuki criança, Yuuki adulta e Alice aprovada antes e depois do empacotamento. As três versões são independentes. A Alice aprovada foi arquivada em `Logs/Archives/alice-child-approved-20260930.zip`; a Yuuki continua em seu arquivo aprovado anterior.
