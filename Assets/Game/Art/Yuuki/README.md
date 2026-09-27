# Sprites da Yuuki

Yuuki_Movement_6x6.png: 3072 x 3072, seis linhas de seis celulas 512 x 512. Ordem: andar esquerda/direita, correr esquerda/direita, pular esquerda/direita. Yuuki_Idle_2x1.png: 1024 x 512, repouso esquerda/direita. Os JSONs registram fontes, pivos e estado da revisao.

Os tres movimentos para a esquerda receberam retoque do cabelo e contornos. Fragmentos soltos foram removidos; a corrida para a direita aprovada permanece identica pixel a pixel. As poses de repouso tem os pes apoiados, mas ainda sao estaticas. A fluidez das passadas continua em avaliacao. Fontes e atlas anteriores preservados em Art/Yuuki. Nao ha pulo duplo.

Asa anatomica esquerda preta e direita branca: olhando para a esquerda, asa proxima preta; olhando para a direita, asa proxima branca. Nao usar espelhamento automatico. Consulte docs/arte.md e reproduza os atlas com scripts/build_yuuki_atlas.py. No Unity use Yuuki > Importar atlas de movimento; a importacao preserva GUIDs existentes.
