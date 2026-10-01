# Alice criança — primeira sequência para revisão

O visual aprovado foi mantido, com dois laços azuis iguais conforme a escolha do usuário. Alice não carrega armas e tem duas asas brancas. A Yuuki aprovada permanece independente, com cópia em `Logs/Archives/yuuki-child-approved-20260930.zip` e manifesto SHA-256 em `Art/Characters/Childhood/yuuki-child-approved-preservation.json`.

## Animações

- Quatro direções: frente, costas, esquerda e direita.
- Andar: quatro desenhos, 6 fps, sequência 1–2–3–4.
- Correr: quatro desenhos, 8 fps, sequência 1–2–3–4.
- Idle com respiração: três desenhos, 2 fps, sequência 1–2–3–2.
- 44 PNGs transparentes de 512 × 512, com importação Unity em Point, sem mipmaps nem compressão; 220 pixels por unidade e pivô (0,5; 0,21875).

A esquerda é um espelhamento horizontal exato da direita em torno do pivô do corpo. Na caminhada de frente, os dois primeiros quadros e seus reflexos formam as quatro fases, garantindo alternância dos pés sem alongar as pernas. As fontes geradas foram mantidas em `Sources/`; nenhum quadro original foi sobrescrito.

## Auréola independente

`Assets/Game/Resources/Childhood/Alice/halo-neutral.png` é uma camada neutra de 96 × 32, com transparência preservada e cor aplicada separadamente. O desenho é uma proposta para revisão, com dois anéis finos e quatro pequenos losangos; ainda depende da aprovação do usuário. As posições por quadro estão em `animations.json`.

## Revisão e reprodução

A página `http://127.0.0.1:8765/preview/alice-animation.html` permite escolher direção, movimento, velocidade, quadro e cor da auréola. Andar e correr começam em 1×; WASD/setas movem, Shift corre. `alice-design.html` mostra o visual estático. As animações aguardam avaliação visual do usuário antes da integração nas cenas Unity e antes de avançar para Tenebris.

As artes foram produzidas com ImageGen. `production-prompts.json` registra os prompts e arquivos gerados; `packing-report.json` registra alinhamento, fontes selecionadas e verificações de preservação. As folhas consolidadas estão em `Atlases/`, e `contact-sheet.png` permite conferir todos os quadros.

Para reconstruir os assets da Alice a partir das fontes registradas: execute `scripts/pack_child_alice.py` com Python, Pillow e NumPy. O script verifica a integridade da Yuuki criança, da Yuuki adulta e da referência original da Alice antes de empacotar.
