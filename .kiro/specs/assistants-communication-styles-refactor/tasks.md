# Implementation Plan: Assistants + Communication Styles Refactor

## Overview

Esta refatoração separa o conceito de "Personas" em dois conceitos distintos:
- **Assistentes (Assistants)**: 3 agentes fixos (Beto, Cadu, Rita) que executam tarefas específicas
- **Estilos de Comunicação (Communication Styles)**: Configurações de tom de voz editáveis pelo usuário

A implementação seguirá uma abordagem incremental, começando pelo banco de dados, depois backend, e finalmente frontend, com checkpoints para validação.

## Tasks

- [x] 1. Database: Criar tabela de assistentes e popular com dados iniciais
  - Criar migration SQL para tabela `assistants` com todos os campos necessários
  - Criar índices em `role` e `name` para otimização
  - Criar constraint única em `role` (apenas 1 assistente por role)
  - Popular tabela com os 3 assistentes fixos: Beto Busca (search), Cadu Comentário (comment), Rita Revisão (review)
  - Usar dados dos arquivos em `squads/twitter-monitoring-squad/agents/` como referência
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5_

- [x] 2. Database: Renomear tabela personas para communication_styles
  - Criar migration SQL para renomear tabela `personas` → `communication_styles`
  - Renomear todos os índices relacionados
  - Atualizar comentários da tabela
  - Manter todos os dados existentes sem perda
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [x] 3. Database: Atualizar referências em campaigns
  - Renomear coluna `persona_id` → `communication_style_id` na tabela `campaigns`
  - Atualizar foreign key constraint para apontar para `communication_styles(id)`
  - Configurar ON DELETE RESTRICT para impedir exclusão de estilos em uso
  - Renomear índice `idx_campaigns_persona_id` → `idx_campaigns_communication_style_id`
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 16.1, 16.2_

- [x] 4. Database: Criar script de rollback
  - Criar script SQL que reverte todas as alterações de migração
  - Reverter renomeação de `communication_styles` → `personas`
  - Reverter renomeação de `communication_style_id` → `persona_id`
  - Excluir tabela `assistants`
  - Restaurar índices e constraints originais
  - Executar todas as alterações em transação única
  - _Requirements: 18.1, 18.2, 18.3, 18.4, 18.5, 18.6_

- [ ]* 5. Database: Testar migrações
  - Executar migrations em ambiente de teste
  - Validar integridade dos dados após migração
  - Testar script de rollback
  - Verificar que foreign keys funcionam corretamente
  - _Requirements: 11.4, 11.5, 11.6, 11.7_

- [x] 6. Checkpoint - Validar estrutura do banco de dados
  - Ensure all tests pass, ask the user if questions arise.

- [x] 7. Backend: Criar modelos Pydantic para Assistants
  - Criar arquivo `backend/src/models/assistant.py`
  - Implementar modelo `Assistant` com todos os campos (id, name, title, role, description, instructions, principles, quality_criteria, skills, is_editable, created_at, updated_at)
  - Implementar modelo `AssistantSummary` para listagens
  - Implementar modelo `AssistantUpdateDTO` para atualizações
  - Adicionar validadores: name não vazio, principles lista não vazia, role enum ('search', 'comment', 'review')
  - _Requirements: 19.1, 19.3, 19.4, 19.5, 19.6_

- [x] 8. Backend: Renomear modelos Persona para CommunicationStyle
  - Renomear arquivo `backend/src/models/persona.py` → `backend/src/models/communication_style.py`
  - Renomear classe `Persona` → `CommunicationStyle`
  - Renomear classe `PersonaSummary` → `CommunicationStyleSummary`
  - Renomear classe `PersonaCreateDTO` → `CommunicationStyleCreateDTO`
  - Renomear classe `PersonaUpdateDTO` → `CommunicationStyleUpdateDTO`
  - Manter todos os validadores existentes
  - _Requirements: 5.3, 19.2_

- [x] 9. Backend: Criar AssistantRepository
  - Criar arquivo `backend/src/repositories/assistant_repository.py`
  - Implementar método `list_all()` que retorna os 3 assistentes ordenados por role
  - Implementar método `get_by_id(assistant_id)` que busca por UUID
  - Implementar método `get_by_role(role)` que busca por função (search, comment, review)
  - Implementar método `update(assistant_id, update_data)` que atualiza campos permitidos
  - Adicionar tratamento de erros e logging
  - _Requirements: 20.1, 20.5_

- [x] 10. Backend: Renomear PersonaRepository para CommunicationStyleRepository
  - Renomear arquivo `backend/src/repositories/persona_repository.py` → `backend/src/repositories/communication_style_repository.py`
  - Renomear classe `PersonaRepository` → `CommunicationStyleRepository`
  - Atualizar todas as referências de tabela de `personas` → `communication_styles`
  - Atualizar referências de coluna `persona_id` → `communication_style_id`
  - Implementar método `check_usage_in_campaigns(style_id)` para validar uso antes de deletar
  - _Requirements: 5.4, 20.2, 20.3, 20.4, 16.3_

- [x] 11. Backend: Criar AssistantService
  - Criar arquivo `backend/src/services/assistant_service.py`
  - Implementar método `list_assistants()` que retorna os 3 assistentes
  - Implementar método `get_assistant(assistant_id)` com tratamento de erro 404
  - Implementar método `get_assistant_by_role(role)` para buscar por função
  - Implementar método `update_assistant(assistant_id, data)` com validação
  - Validar que todos os campos obrigatórios estão presentes
  - Adicionar logging de operações
  - _Requirements: 4.6, 4.7_

- [x] 12. Backend: Renomear PersonaService para CommunicationStyleService
  - Renomear arquivo `backend/src/services/persona_service.py` → `backend/src/services/communication_style_service.py`
  - Renomear classe `PersonaService` → `CommunicationStyleService`
  - Renomear métodos: `create_persona` → `create_communication_style`, `get_persona` → `get_communication_style`, etc.
  - Atualizar cache keys de `persona:` → `communication_style:`
  - Manter toda a lógica de negócio existente
  - _Requirements: 5.4_

- [x] 13. Backend: Atualizar CommentGenerationService
  - Modificar `backend/src/services/comment_generation_service.py`
  - Adicionar dependência de `AssistantService` no construtor
  - Renomear dependência `PersonaService` → `CommunicationStyleService`
  - Atualizar método `generate_comment()` para buscar Assistant Cadu (role='comment')
  - Combinar `assistant.instructions` + `style.system_prompt` no prompt do OpenAI
  - Atualizar referências de `persona_id` → `communication_style_id`
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5, 12.6_

- [x] 14. Backend: Atualizar CommentReviewService
  - Modificar `backend/src/services/comment_review_service.py` (ou arquivo equivalente)
  - Adicionar dependência de `AssistantService`
  - Buscar Assistant Rita (role='review') no início da revisão
  - Usar `rita.instructions` e `rita.principles` para revisar comentários
  - Aplicar `rita.quality_criteria` na avaliação
  - Retornar veredito APPROVED/REJECTED baseado nos critérios de Rita
  - _Requirements: 13.1, 13.2, 13.3, 13.4_

- [x] 15. Backend: Atualizar SearchService
  - Modificar `backend/src/services/scraping_engine.py` ou arquivo de busca equivalente
  - Adicionar dependência de `AssistantService`
  - Buscar Assistant Beto (role='search') no início da busca
  - Usar `beto.instructions` e `beto.principles` para buscar posts
  - Aplicar `beto.quality_criteria` na filtragem de posts
  - Usar `beto.skills` (Apify) para executar a busca
  - _Requirements: 14.1, 14.2, 14.3, 14.4_

- [x] 16. Checkpoint - Validar serviços do backend
  - Ensure all tests pass, ask the user if questions arise.

- [x] 17. Backend: Criar rotas /api/assistants
  - Criar arquivo `backend/src/api/routes/assistants.py`
  - Implementar `GET /api/assistants` que retorna lista dos 3 assistentes
  - Implementar `GET /api/assistants/{id}` que retorna detalhes de um assistente
  - Implementar `PUT /api/assistants/{id}` que atualiza um assistente
  - Implementar `POST /api/assistants` que retorna HTTP 405 (Method Not Allowed)
  - Implementar `DELETE /api/assistants/{id}` que retorna HTTP 405 (Method Not Allowed)
  - Adicionar validações e tratamento de erros (404, 400, 500)
  - Registrar rotas no `backend/src/main.py`
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5, 4.7, 4.8, 4.9_

- [x] 18. Backend: Renomear rotas /api/personas para /api/communication-styles
  - Renomear arquivo `backend/src/api/routes/personas.py` → `backend/src/api/routes/communication_styles.py`
  - Atualizar base path de `/api/personas` → `/api/communication-styles`
  - Atualizar todas as referências de `PersonaService` → `CommunicationStyleService`
  - Atualizar modelos de request/response para usar `CommunicationStyle*`
  - Manter funcionalidade CRUD completa (GET, POST, PUT, DELETE)
  - Atualizar registro de rotas no `backend/src/main.py`
  - _Requirements: 5.1, 5.2, 5.5_

- [ ]* 19. Backend: Criar testes unitários para AssistantService
  - Criar arquivo `backend/tests/services/test_assistant_service.py`
  - Testar `list_assistants()` retorna exatamente 3 assistentes
  - Testar `get_assistant_by_role()` para cada role (search, comment, review)
  - Testar `update_assistant()` com dados válidos
  - Testar `update_assistant()` com dados inválidos (deve falhar)
  - Testar `get_assistant()` com ID inexistente (deve retornar 404)
  - _Requirements: 17.1_

- [ ]* 20. Backend: Criar testes unitários para CommunicationStyleService
  - Criar arquivo `backend/tests/services/test_communication_style_service.py`
  - Testar operações CRUD completas
  - Testar gerenciamento de estilo padrão (apenas 1 pode ser padrão)
  - Testar validação de uso antes de deletar
  - Testar que não pode deletar estilo em uso por campanhas
  - _Requirements: 17.2_

- [ ]* 21. Backend: Criar testes de integração para APIs
  - Criar arquivo `backend/tests/api/test_assistants_api.py`
  - Testar todos os endpoints de assistants (GET list, GET by id, PUT, POST blocked, DELETE blocked)
  - Criar arquivo `backend/tests/api/test_communication_styles_api.py`
  - Testar todos os endpoints de communication-styles (CRUD completo)
  - Validar códigos de resposta HTTP corretos (200, 201, 404, 405, 400)
  - _Requirements: 17.2, 17.5, 17.6_

- [x] 22. Checkpoint - Validar APIs do backend
  - Ensure all tests pass, ask the user if questions arise.

- [x] 23. Frontend: Criar tipos TypeScript para Assistants
  - Criar ou atualizar arquivo `frontend/src/types/index.ts` (ou equivalente)
  - Definir interface `Assistant` com todos os campos
  - Definir interface `AssistantSummary` para listagens
  - Definir interface `AssistantUpdateDTO` para atualizações
  - Definir type literal para `role`: 'search' | 'comment' | 'review'
  - _Requirements: 5.3_

- [x] 24. Frontend: Renomear tipos Persona para CommunicationStyle
  - Atualizar arquivo de tipos TypeScript
  - Renomear interface `Persona` → `CommunicationStyle`
  - Renomear interface `PersonaSummary` → `CommunicationStyleSummary`
  - Renomear interface `PersonaCreateDTO` → `CommunicationStyleCreateDTO`
  - Renomear interface `PersonaUpdateDTO` → `CommunicationStyleUpdateDTO`
  - _Requirements: 5.3_

- [x] 25. Frontend: Criar AssistantService.ts
  - Criar arquivo `frontend/src/services/assistantService.ts` (ou caminho equivalente)
  - Implementar método `listAssistants()` que chama GET /api/assistants
  - Implementar método `getAssistant(id)` que chama GET /api/assistants/{id}
  - Implementar método `updateAssistant(id, data)` que chama PUT /api/assistants/{id}
  - Adicionar tratamento de erros com mensagens em português
  - _Requirements: 5.1_

- [x] 26. Frontend: Renomear PersonaService para CommunicationStyleService
  - Renomear arquivo `frontend/src/services/personaService.ts` → `frontend/src/services/communicationStyleService.ts`
  - Renomear classe/objeto `PersonaService` → `CommunicationStyleService`
  - Atualizar base path de `/api/personas` → `/api/communication-styles`
  - Atualizar tipos de retorno para usar `CommunicationStyle*`
  - Manter todos os métodos CRUD existentes
  - _Requirements: 5.1, 5.2_

- [x] 27. Frontend: Criar AssistantListPage
  - Criar arquivo `frontend/src/pages/AssistantListPage.tsx` (ou caminho equivalente)
  - Exibir 3 cards de assistentes com nome, título, descrição resumida
  - Adicionar ícones visuais: 🔍 para Beto, ✍️ para Cadu, 🛡️ para Rita
  - Exibir badge com a função (Busca, Comentário, Revisão)
  - Adicionar botão "Editar" em cada card
  - NÃO adicionar botões "Criar Novo" ou "Excluir"
  - Adicionar nota explicativa que assistentes são fixos
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5, 6.6_

- [x] 28. Frontend: Criar AssistantEditPage
  - Criar arquivo `frontend/src/pages/AssistantEditPage.tsx` (ou caminho equivalente)
  - Criar formulário com campos: nome, título, descrição, instruções (textarea grande)
  - Adicionar seção editável para princípios (lista com add/remove)
  - Adicionar seção editável para critérios de qualidade (lista com add/remove)
  - Adicionar botões "Salvar" e "Cancelar"
  - Implementar validação de campos obrigatórios
  - Exibir mensagens de erro claras em português
  - Exibir mensagem de sucesso após salvar
  - Adicionar indicadores de loading durante salvamento
  - _Requirements: 7.1, 7.2, 7.3, 7.4, 7.5, 7.6, 7.7, 7.8, 7.9_

- [x] 29. Frontend: Renomear PersonaListPage para CommunicationStyleListPage
  - Renomear arquivo `frontend/src/pages/PersonaListPage.tsx` → `frontend/src/pages/CommunicationStyleListPage.tsx`
  - Atualizar título da página para "Estilos de Comunicação"
  - Atualizar textos e labels para usar "Estilo de Comunicação"
  - Atualizar chamadas de serviço para usar `CommunicationStyleService`
  - Manter funcionalidade de listagem, edição e exclusão
  - Exibir badge "Padrão" para estilos marcados como is_default
  - _Requirements: 8.1, 8.2, 8.3, 8.4, 8.5, 8.6, 8.7, 8.8_

- [x] 30. Frontend: Renomear PersonaCreatePage para CommunicationStyleCreatePage
  - Renomear arquivo `frontend/src/pages/PersonaCreatePage.tsx` → `frontend/src/pages/CommunicationStyleCreatePage.tsx`
  - Atualizar título da página para "Criar Estilo de Comunicação"
  - Atualizar textos e labels para usar "Estilo de Comunicação"
  - Atualizar chamadas de serviço para usar `CommunicationStyleService`
  - Manter todos os campos do formulário
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8_

- [x] 31. Frontend: Renomear PersonaEditPage para CommunicationStyleEditPage
  - Renomear arquivo `frontend/src/pages/PersonaEditPage.tsx` → `frontend/src/pages/CommunicationStyleEditPage.tsx`
  - Atualizar título da página para "Editar Estilo de Comunicação"
  - Atualizar textos e labels para usar "Estilo de Comunicação"
  - Atualizar chamadas de serviço para usar `CommunicationStyleService`
  - Adicionar aviso quando usuário marca estilo como padrão (desmarca o anterior)
  - _Requirements: 9.1, 9.2, 9.3, 9.4, 9.5, 9.6, 9.7, 9.8, 9.9_

- [x] 32. Frontend: Renomear PersonaForm para CommunicationStyleForm (se existir)
  - Renomear componente `PersonaForm` → `CommunicationStyleForm`
  - Atualizar props e tipos para usar `CommunicationStyle*`
  - Atualizar labels e textos para "Estilo de Comunicação"
  - Adicionar tooltips explicativos para cada campo
  - _Requirements: 9.2_

- [x] 33. Frontend: Atualizar navegação e rotas
  - Atualizar arquivo de rotas (ex: `frontend/src/App.tsx` ou `routes.tsx`)
  - Adicionar rota `/assistants` → `AssistantListPage`
  - Adicionar rota `/assistants/:id/edit` → `AssistantEditPage`
  - Renomear rotas de `/personas` → `/communication-styles`
  - Atualizar menu de navegação para incluir "Assistentes" e "Estilos de Comunicação"
  - Remover ou atualizar links antigos de "Personas"
  - _Requirements: 6.1, 8.1_

- [x] 34. Frontend: Atualizar CampaignForm
  - Modificar formulário de criação de campanha
  - Renomear campo "Persona" → "Estilo de Comunicação"
  - Atualizar dropdown para buscar de `CommunicationStyleService.listCommunicationStyles()`
  - Pré-selecionar estilo marcado como padrão (is_default)
  - Exibir nome e título de cada estilo no dropdown
  - Enviar `communication_style_id` ao invés de `persona_id` no submit
  - NÃO exibir seleção de assistentes (sempre os 3 fixos)
  - _Requirements: 10.1, 10.2, 10.3, 10.4, 10.5, 10.6_

- [ ]* 35. Frontend: Criar testes E2E para workflows de usuário
  - Criar testes para workflow de edição de assistente
  - Criar testes para workflow de criação de estilo de comunicação
  - Criar testes para workflow de edição de estilo de comunicação
  - Criar testes para workflow de exclusão de estilo não usado
  - Criar testes para validação de exclusão de estilo em uso (deve falhar)
  - Criar testes para criação de campanha com estilo de comunicação
  - _Requirements: 17.4_

- [x] 36. Checkpoint - Validar interface do usuário
  - Ensure all tests pass, ask the user if questions arise.

- [ ] 37. Documentation: Criar guia de usuário
  - Criar arquivo `docs/assistants-communication-styles-guide.md` (ou caminho equivalente)
  - Explicar diferença entre assistentes e estilos de comunicação
  - Descrever função de cada assistente (Beto, Cadu, Rita)
  - Fornecer exemplos de como editar assistentes
  - Fornecer exemplos de como criar estilos de comunicação
  - Incluir screenshots da interface (ou placeholders para screenshots)
  - Escrever em português
  - _Requirements: 15.1, 15.2, 15.3, 15.4, 15.5, 15.6_

- [ ] 38. Documentation: Atualizar README e documentação técnica
  - Atualizar `backend/README.md` com informações sobre assistentes
  - Atualizar `frontend/README.md` com informações sobre novas páginas
  - Atualizar diagramas de arquitetura se existirem
  - Documentar endpoints da API de assistentes
  - Documentar mudanças de nomenclatura (personas → communication_styles)

- [ ] 39. Final Checkpoint - Validação completa do sistema
  - Executar todas as migrações em ambiente de staging
  - Executar suite completa de testes (unitários, integração, E2E)
  - Validar que campanhas existentes continuam funcionando
  - Validar que comentários são gerados corretamente com novos assistentes
  - Validar que revisão funciona com Assistant Rita
  - Validar que busca funciona com Assistant Beto
  - Ensure all tests pass, ask the user if questions arise.

## Notes

- Tasks marcadas com `*` são opcionais (testes) e podem ser puladas para MVP mais rápido
- Cada task referencia requisitos específicos para rastreabilidade
- Checkpoints garantem validação incremental
- A implementação segue ordem lógica: Database → Backend → Frontend
- Migrações devem ser executadas em transação única para garantir atomicidade
- Assistentes são sempre 3 e fixos (não podem ser criados ou excluídos)
- Estilos de comunicação são totalmente editáveis pelo usuário (CRUD completo)
- Foreign key constraints garantem integridade referencial
- Script de rollback permite reverter mudanças em caso de problemas
