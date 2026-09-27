# Cenários e protótipo de exploração

Esta etapa mantém Rua de Casa e Moradias, os mapas feitos com Claude. A Yuuki atual e os moradores provisórios continuam em uso. A prioridade acordada é terminar o conjunto de cenários antes de organizar as próximas áreas e criar personagens definitivos.

## Testar agora

Abra `D:\yuuki-pixel\Builds\Bairro\Yuuki.exe`. O executável inicia no menu, com **Entrar no bairro**, **Galeria de cenários**, **Controles** e **Sair**. A galeria permite ampliar cada peça. O jogo usa WASD/setas, Shift para correr e Esc para pausar/voltar ao menu. Entrar de novo pelo menu reinicia a exploração; ainda não há salvamento de progresso.

Ao alcançar a saída oeste de Rua de Casa, o jogo pergunta se deseja ir para Moradias. Enter confirma, Esc cancela; também há botões. O mundo e o movimento ficam suspensos durante a pergunta. Ao cancelar, permanecemos no mesmo mapa; os limites físicos impedem sair do chão. A saída leste de Moradias volta para Rua de Casa. As portas dos interiores mantêm a entrada automática. Escola e comércio ainda mostram o aviso de área em preparação.

O executável é local e a pasta Builds é ignorada pelo Git. Não mova o `.exe` sozinho: ele precisa das pastas e DLLs que o acompanham.

No Unity 6000.0.82f1, abra `Assets/Game/Scenes/Bairro_Menu.unity` e aperte Play. **Yuuki > Protótipo > Preparar menu e assets** importa as peças e cria somente mapas que ainda não têm cena. **Exportar jogo para Windows** recompila o executável. Os comandos **Yuuki > Bairro > Construir…** continuam sendo os comandos explícitos que substituem as cenas dos mapas pelo JSON.

## 61 peças novas

| Conjunto | Peças | Conteúdo |
| --- | ---: | --- |
| Comércio | 6 | Padaria, alfaiataria, mercearia, forja, usados, objetos sagrados |
| Escola exterior | 6 | Prédio, árvore/balanço, grade, banco, gangorra, lenheiro |
| Escola interior | 9 | Carteira, mesa de professor, quadro, duas estantes, mesa de leitura, escada, globo, livros |
| Comércio objetos | 9 | Carroça, barraca, farinha, peixes, frutas, pão, poste, fonte, placas |
| Dungeon | 9 | Entrada, parede, canto, tocha, correntes, ossos, asa carbonizada, altar, velas |
| Bairro abandonado | 9 | Duas casas, muro, portão, cerca, varal, horta, lixo, brinquedo/pena |
| Detalhes | 9 | Teia, parede vertical, grade, poça, símbolo, penas, sino, carteira quebrada, amarelinha |
| Pisos | 4 | Terra e lajes da dungeon, lama e calçamento dos subúrbios |

- PNGs individuais e catálogo: `Assets/Game/Resources/Environment/`.
- Prefabs: `Assets/Game/Environment/Prefabs/`. Importação Point, sem mipmaps/compressão, escala definida em tiles e pivô na base. Objetos sólidos têm um colisor de base editável; adereços planos não bloqueiam a passagem.
- Folhas originais e prompts: `Art/World/Sources/Bairro-v2/`.
- Brief do usuário: `docs/bairro/brief-ambientes.txt`.
- Contatos para revisão: `docs/bairro/catalogo-*.jpg`.
- Galeria no navegador: `http://127.0.0.1:8765/preview/assets.html`, com a raiz do projeto servida por HTTP.

O novo conjunto está fora de `Assets/Game/Bairro/Sprites`: o gerador antigo apaga e recria essa pasta. Assim, regenerar os mapas antigos não apaga estas artes.

## Limites e próxima montagem

As peças são estáticas e completas, com 8 pixels de margem transparente. As imagens não foram borradas nem redimensionadas durante a extração. Retângulos individuais e máscaras de componentes separam as silhuetas cujos limites se sobrepõem na folha. RGB de pixels totalmente transparentes foi zerado para evitar resíduos na importação.

Os pisos são texturas de preenchimento, **não um autotile com todas as transições**. A parede em L é uma ruína decorativa; o encaixe final com paredes retas/verticais deve ser ajustado na montagem. Portas, entradas, placas com texto e colisões de cada construção precisam de posicionamento no mapa. Os nomes das lojas estão no catálogo; as placas desenhadas usam pictogramas para evitar texto deformado.

Ainda faltam a montagem jogável de escola, comércio, trecho abandonado e dungeon; luz dinâmica/fumaça das novas tochas, animações de objetos e áudio ambiente. As duas casas abandonadas são variantes para essa área futura e não substituem automaticamente as casas habitadas atuais. Os moradores e as animações para cima/baixo continuam provisórios; Yuuki criança, Tenebris, Alice, Sara e Kled definitivos ficam para uma etapa posterior.

## Reprodução e verificações

```text
python scripts/bairro/pack_environment.py
python scripts/bairro/validate_environment.py
python scripts/bairro/validate_map.py
```

Dependências: Pillow, NumPy e SciPy. O empacotador não desenha conteúdo: extrai as artes de origem e registra os recortes, tamanhos, escala e pivôs. O validador confere IDs, arquivos, recortes sem cortes, margem, transparência e metadados. O validador dos mapas verifica acesso às portas/saídas e rotas de moradores.

`scripts/verify_assets.cjs` testa a galeria web com Playwright/Edge, incluindo carregamento dos 61 PNGs, categorias, busca sem acentos, ampliação, Escape e largura de celular.

O build de desenvolvimento inclui uma verificação opcional que só roda com `--yuuki-smoke-test --smoke-output D:\yuuki-pixel\Logs\smoke`. Ela usa as cenas e gatilhos físicos reais para verificar menu, texturas, pausa, cancelamento, ida/volta, interiores e reentrada. O resultado fica em `result.txt`; execução normal não roda o teste. Capturas de tela feitas com a janela oculta podem sair pretas; isso não valida visualmente a interface nativa. O teste funcional e a revisão visual dos PNGs são verificações distintas.
