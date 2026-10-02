# Prólogo: a caminho da escola

Abra `Builds/SchoolMorning/Yuuki.exe` no Windows, ou `http://127.0.0.1:8765/preview/school-morning.html` com o servidor local servindo a raiz do projeto. O menu inicia a caminhada jogável às 06:45.

- WASD/setas: andar; Shift + direção: correr.
- F: ação contextual (flor, portão, bola de pano e pedrinha).
- Espaço/Enter: próxima fala; Esc: pausa e menu.
- No navegador há controles de toque e tela cheia.

Yuuki é controlada pelo jogador. Tenebris guia o caminho, espera quando ela se afasta e retoma quando ela o alcança. Os balões acompanham os personagens. O tutorial pausa a simulação, inclusive animações e relógio, até haver movimento real de corrida. Depois da corrida curta, Yuuki recupera o fôlego e os dois seguem mais devagar.

O portão desliza completamente para abrir; a colisão acompanha a passagem. O quintal tem cerca frontal, lateral e dos fundos sem saídas alternativas. A poça é um detalhe do chão, abaixo dos personagens. A bola fica visível à frente dos pés e é devolvida aos meninos. Tenebris para ao lado de Yuuki, evitando cobrir seu corpo nas conversas.

Os quatro módulos `quintal`, `rua`, `ladeira` e `escola` em `Assets/Game/Resources/SchoolMorning/Maps` são ligados continuamente. Casas da família Arcadia e de Tenebris permanecem separadas. Esta introdução termina na chegada à Escola Anjos do Testamento; a sala de aula e o capítulo seguinte ainda não fazem parte deste percurso.

O texto novo enviado pelo usuário situa Yuuki aos oito anos. Os arquivos infantis aprovados são reutilizados sem modificar seus metadados anteriores. A narrativa está em `Art/Story/SchoolMorning-v1/scenario-source.txt`; a adaptação em `Assets/Game/Resources/SchoolMorning/story.json` preserva 93 falas em 24 etapas.

## Arte

As novas ações ficam em `Assets/Game/Resources/SchoolMorning/Actions`: exausta, pegar um objeto, mexer no portão, chutar a pedrinha, Tenebris ajudando no portão e Yuuki apertando sutilmente as alças da mochila. Cada ciclo tem quatro desenhos. As alças e a mochila são acessórios separados nos movimentos comuns; no gesto, as mãos e as alças fazem parte do desenho. A auréola é uma camada separada, como nos conjuntos aprovados.

Os moradores têm seis ciclos de quatro quadros: senhora varrendo, dois meninos, cachorro andando e dois professores respirando/piscando. Os originais e prompts de geração estão em `Art/Story/SchoolMorning-v1/Sources` e `Revision2/Sources`. A arte foi gerada com a ferramenta integrada de imagens; o empacotamento usa apenas recorte, limpeza de transparência, registro dos pés e escala uniforme por sequência, sem deformar pernas.

Os sprites anteriores da Yuuki adulta/infantil, Alice, Tenebris, Sara e Kled continuam preservados. Os manifestos de aprovação são verificados por SHA-256; o relatório registra 700 arquivos protegidos.

## Reprodução e verificação

No Unity, abra `Assets/Game/Scenes/Intro/Intro_Menu.unity`. O método de editor `YuukiSchoolIntroBuilder.BuildAndExport` valida o percurso e exporta apenas `Intro_Menu` e `Intro_Main` para `Builds/SchoolMorning`. Os protótipos anteriores permanecem disponíveis em suas pastas.

`node scripts/Intro/test-school-morning.mjs D:/yuuki-pixel` verifica a rota inteira, o uso obrigatório de F, a espera do guia, a pausa, o tutorial, o perímetro fechado, o deslizamento completo, os balões dispensáveis, a bola visível e o gesto da mochila. As animações são limitadas a quatro quadros.

`Yuuki.exe -batchmode --yuuki-intro-smoke --smoke-output D:/yuuki-pixel/Art/Story/SchoolMorning-v1/NativeSmoke` executa uma verificação opcional com entradas de movimento no modelo real, sem teletransportar os personagens. O resultado e as capturas são salvos nessa pasta. O jogador normal nunca é dirigido por esse verificador.

A prévia tem uma verificação visual separada, acionada apenas por `?verificar=1`, com checkpoints e um botão para continuar. A URL normal usa os comandos do jogador. Os resultados ficam em `Art/Story/SchoolMorning-v1/browser-model-qa.json`, `unity-model-qa.json` e `NativeSmoke/result.json`.
