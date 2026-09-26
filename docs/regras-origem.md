# Origem das regras (futura adaptacao)
Repositorio de referencia: Hellsccythe/rpg-mesa
Commit consultado: 185f630a6d6c6080abcd60076bfec014bd6e11cd

Arquivos consultados:
- server/src/modules/classes/models/classe.model.ts: requisitos, nivel maximo, bonus, skills iniciais/passivas/assinatura, pericia e atributo de ataque.
- server/src/modules/combate/combate.service.ts: resolucao de ataques e integracao com atributos, inventario e efeitos.
- server/src/modules/combate/skills-de-combate.service.ts: skills Ativa/Assinatura, custo, recarga, dados, atributos e efeitos.

A implementacao futura deve separar definicoes de classes/skills de estado de personagem e resolucao de combate, em C# independente de infraestrutura.
Nao foram copiados catalogos do banco, dados de jogadores, credenciais, uploads ou codigo do backend.
Decisao pendente: como adaptar turnos, dados e recargas a um jogo de acao em tempo real. Nao assumir que segundos equivalem a turnos.
