# Yuuki criança — movimentos revisados para avaliação

A revisão usa a Alice e o Tenebris aprovados como referência de cadência: quatro quadros para andar, quatro para correr e três desenhos para respirar parada, nas quatro direções. Mantém a Yuuki de nove anos, cabelos brancos, olhos vermelhos, roupa preta e branca e mãos vazias.

## Anatomia e auréola

Asa anatômica esquerda preta, direita branca. De frente, a asa branca está à esquerda do observador; de costas, a preta está à esquerda. Na lateral direita a asa próxima é branca; na esquerda a próxima é preta. As quatro direções foram geradas separadamente; não há espelhamento integral da personagem.

A auréola aprovada foi reutilizada com os mesmos bytes, transparência e geometria `Yuuki-v2`, em uma camada independente e recolorível. As posições por quadro estão no catálogo.

## Arquivos e reprodução

- `Assets/Game/Resources/Childhood/YuukiV2/`: 44 PNGs RGBA de 512 × 512, catálogo e auréola. Importação Unity em Point, sem mipmaps ou compressão, 220 pixels por unidade e pivô (0,5; 0,21875).
- `Art/Characters/Childhood/Yuuki/Animations-v2/Atlases/`: quatro folhas de 2048 × 1536, linhas andar, correr e idle, células 512 × 512. A quarta célula do idle fica vazia.
- `Sources/`: seis fontes ImageGen, incluindo as primeiras versões e as correções selecionadas. Nenhuma anatomia foi pintada por script.
- `production-prompts.json`: prompts completos da ferramenta integrada ImageGen, referências, nomes dos arquivos gerados e seleção de cada linha.
- `packing-report.json` e `final-qa.json`: alinhamento, margens, transparência, importação e verificação dos arquivos preservados.
- `browser-qa.json` e `browser-preview.png`: conferência dos doze movimentos na prévia local.

Andar usa 6 fps, correr 8 fps, ambos em ciclo 1–2–3–4. Respiração usa 2 fps, ciclo 1–2–3–2, com apoio dos pés estável. O script só recorta, remove pequenos fragmentos desconectados, ajusta a escala por clipe, alinha e empacota, sem esticar pernas ou modificar as cores das asas. O cabelo é alinhado pela região branca da cabeça, com escala constante dentro de cada clipe. A corrida frontal e as passadas de costas usam folhas corretivas para alternar os pés.

Reconstrua com `scripts/pack_child_yuuki_v2.py` usando Python, Pillow e NumPy. O script verifica os quatro manifestos de preservação antes e depois. Não execute os antigos empacotadores sobre conjuntos aprovados para esta revisão.

## Prévia e preservação

Abra `http://127.0.0.1:8765/preview/yuuki-animation-v2.html`. Há seleção de movimento, direção, quadro, velocidade 1× e cor da auréola. WASD/setas movem a personagem; Shift corre. A prévia tem links para comparar com Alice, Tenebris e a Yuuki anterior.

Esta revisão aguarda avaliação visual do usuário e está separada do conjunto anterior aprovado. Não substitui as animações nas cenas Unity. A Yuuki criança anterior, a Yuuki adulta, Alice e Tenebris permanecem preservados; foram conferidos 565 arquivos dos respectivos manifestos. O Tenebris aprovado nesta etapa tem backup verificado em `Logs/Archives/tenebris-child-approved-20260930.zip`.
