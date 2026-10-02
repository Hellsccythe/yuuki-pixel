# Sara e Kled — designs iniciais

Uma pose neutra de cada personagem para aprovação. Nenhuma animação foi produzida e os personagens ainda não foram adicionados às cenas.

## Referência da história

Fonte: `D:/RPG/Rpg Pathfinder/historias do rpg/yuuki, revisado.pdf`, páginas 1 e 13–14.

- **Sara**, mãe de Yuuki: 1,71 m; cabelos loiros claros até a cintura; olhos azuis; camisa branca de mangas longas; saia preta; meia-calça escura; sapatos azul-escuros.
- **Kled**, pai de Yuuki: 1,78 m; cabelos pretos até os ombros; olhos vermelhos; camisa, calça e cinto pretos.
- Ambos têm duas asas brancas, aparência jovem de adultos e um leve cansaço do trabalho. As roupas são simples e cuidadas.

Os sapatos pretos e o rosto sem barba de Kled, assim como os desenhos das auréolas, são propostas visuais para validação. Não foram atribuídas idades exatas nem profissões que a história não define.

## Arquivos

`{Sara,Kled}/Design-v1/` contém a arte original, o corpo em PNG RGBA de 512 × 512, a auréola separada e o perfil com posição da luz. `Assets/Game/Resources/Parents/` contém cópias prontas para importação no Unity, com filtro Point, sem mipmaps nem compressão, 220 pixels por unidade e pivô nos pés.

O processamento apenas recorta, redimensiona com nearest-neighbor e posiciona a arte. Não desenha nem altera a anatomia. A auréola é renderizada com opacidade 0,6 e pode ser recolorida sem mudar o corpo.

Prévia: `http://127.0.0.1:8765/preview/yuuki-parents-design.html`.

Geração: ferramenta ImageGen integrada. Os prompts, referências e escolhas estão em `production-prompts.json`; as verificações estão em `packing-report.json` e `design-qa.json`.

Yuuki adulta, Yuuki criança aprovada, Alice e Tenebris aprovados foram verificados pelos manifests de preservação. A revisão V2 da Yuuki também foi preservada; sua aprovação não foi presumida.

## Revisão do Kled

Sara aprovada em 2026-10-01, com backup e manifest de preservação. Kled `Design-v2` usa o rosto e o cabelo da referência enviada pelo usuário. Sua pose e as duas asas brancas foram mantidas. O primeiro Kled continua em `Design-v1`; a nova prévia usa `Parents/KledV2`. O prompt e a referência estão na pasta da revisão. O novo Kled ainda aguarda aprovação.

## Estado atual

Sara e Kled V2 aprovados. Sara tem uma primeira sequência de 44 quadros e 12 animações, em `Sara/Animations-v1`, pronta para avaliação na prévia `preview/sara-animation.html`. Kled ainda não tem animações.
