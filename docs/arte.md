# Direcao de arte e revisao

Yuuki: anja jovem, petite em proporcao chibi, cabelo branco, olhos vermelhos, vestido gotico branco com detalhes pretos, aureola e cajado preto com gema vermelha. Manter figurino e aderecos consistentes.

A asa esquerda anatomica e preta e a direita e branca. Vista para a esquerda: asa proxima preta, distante branca. Vista para a direita: asa proxima branca, distante preta. Cada direcao tem seus proprios sprites; nao usar flipX automatico.

## Atlas e fontes

Assets/Game/Art/Yuuki/Yuuki_Movement_6x6.png: 3072 x 3072 pixels, seis linhas e seis colunas de 512 x 512. Ordem: andar esquerda/direita, correr esquerda/direita, pular esquerda/direita. O JSON homonimo registra fonte, ritmo, pivo e limpeza. Yuuki_Idle_2x1.png possui duas celulas 512 x 512, esquerda e direita, com poses neutras e pes apoiados.

As fontes revisadas estao em Art/Yuuki/Left/walk-left-clean-v3.png, run-left-clean-v3.png e jump-left-clean-v3.png. Foram retocadas com ImageGen a partir dos quadros existentes, em grades 3 x 2 com espaco entre sprites. Os contornos do cabelo foram redesenhados sem as faixas embaçadas. As poses de repouso estao nos arquivos idle-left-v1.png e idle-right-v1.png das pastas Left e Right. As referencias de retoque estao em Art/Experiments/*-clean-reference.png.

scripts/build_yuuki_atlas.py empacota os quadros. Usa uma escala uniforme por movimento, nearest-neighbor e alinhamento pelo halo para os candidatos da esquerda. A caminhada tem apoio dos pes estabilizado; a corrida conserva a fase com os pes no ar. Ilhas de pixels desconectadas sao removidas, com dois pixels de margem para conservar o contorno. O RGB sob transparencia total tambem e limpo: os arquivos gerados podem ter cores invisiveis que confundem visualizadores de referencias. A corrida direita aprovada nao recebe nenhum desses filtros e continua identica pixel a pixel.

As fontes antigas e os atlas movement-atlas-v1.png e movement-atlas-v2.png ficam preservados em Art/Yuuki. Pulo duplo permanece excluido.

## Estado de aprovacao

- Caminhada esquerda: cabelo e alinhamento revisados; alguns quadros ainda repetem uma passada muito parecida. E um candidato, nao uma animacao final aprovada.
- Caminhada direita: candidato anterior mantido, com limpeza de transparencia.
- Corrida direita: preservada exatamente da fonte aprovada.
- Corrida esquerda: cabelo e silhueta retocados; os tres momentos da passada ainda sao semelhantes nas duas metades do ciclo. Avaliar a fluidez.
- Pulo esquerdo: contorno retocado, sem os fragmentos e as bordas cortadas da fonte anterior.
- Pulo direito: poses anteriores com o fragmento solto removido.
- Repouso: duas poses neutras novas, estaticas; ainda sem respiracao ou piscada. Conferir proporcoes e transicao para caminhada.

No navegador e no Unity o pulo acompanha subida e descida pela velocidade vertical. Os clipes Unity agora mantem o ultimo quadro por um intervalo completo antes de repetir. Os sprites sao importados sem compressao, mipmap ou filtragem bilinear.

O criterio de aprovacao e conferir os seis quadros em movimento e quadro a quadro: cores anatomicas das asas, rosto/roupa/cajado consistentes, contato dos pes, alternancia de pernas, contornos e transparencia. Limpeza tecnica e maior nitidez nao garantem por si so um ciclo de pernas natural.
