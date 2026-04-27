# Requirements Document

## Introduction

Este documento especifica os requisitos para refatorar o sistema atual de "Personas" em dois conceitos distintos e bem definidos:

1. **Assistentes (Assistants)**: Agentes especializados que executam tarefas específicas no pipeline (busca, comentário, revisão)
2. **Estilos de Comunicação (Communication Styles)**: Configurações de tom de voz e estilo para geração de comentários

Atualmente, a tabela `personas` mistura esses dois conceitos, causando confusão conceitual. Esta refatoração visa separar claramente as responsabilidades e permitir que usuários leigos possam editar assistentes e criar estilos de comunicação de forma intuitiva.

## Glossary

- **System**: O sistema completo de monitoramento e engajamento no Twitter
- **Assistant**: Agente especializado que executa uma tarefa específica (busca, comentário ou revisão)
- **Communication_Style**: Configuração de tom de voz, princípios e regras de formatação para geração de comentários
- **Campaign**: Campanha de monitoramento e engajamento configurada pelo usuário
- **Frontend**: Interface web para usuários leigos gerenciarem assistentes e estilos
- **Backend**: API e banco de dados que armazenam e servem dados
- **Database**: Banco de dados PostgreSQL/Supabase
- **User**: Usuário leigo que configura campanhas e edita assistentes

## Requirements

### Requirement 1: Criar Tabela de Assistentes

**User Story:** Como desenvolvedor, eu quero uma tabela `assistants` no banco de dados, para que os três assistentes fixos (Beto, Cadu, Rita) possam ser armazenados e editados.

#### Acceptance Criteria

1. THE Database SHALL criar uma tabela `assistants` com os campos: id (UUID), name (VARCHAR), title (VARCHAR), role (VARCHAR), description (TEXT), instructions (TEXT), principles (JSONB), quality_criteria (JSONB), skills (JSONB), is_editable (BOOLEAN), created_at (TIMESTAMP), updated_at (TIMESTAMP)
2. THE Database SHALL criar exatamente 3 registros fixos na tabela `assistants` correspondentes a Beto Busca, Cadu Comentário e Rita Revisão
3. THE Database SHALL definir is_editable como TRUE para todos os assistentes
4. THE Database SHALL criar índices em name e role para otimizar consultas
5. WHEN a tabela `assistants` é criada, THE Database SHALL popular os dados iniciais baseados nos arquivos de agentes existentes em `squads/twitter-monitoring-squad/agents/`

### Requirement 2: Renomear Tabela Personas para Communication Styles

**User Story:** Como desenvolvedor, eu quero renomear a tabela `personas` para `communication_styles`, para que o nome reflita claramente seu propósito de armazenar estilos de comunicação.

#### Acceptance Criteria

1. THE Database SHALL renomear a tabela `personas` para `communication_styles`
2. THE Database SHALL manter todos os campos existentes: id, name, title, description, tone_of_voice, principles, vocabulary_allowed, vocabulary_prohibited, formatting_rules, language, system_prompt, is_default, created_at, updated_at
3. THE Database SHALL manter todos os índices existentes com nomes atualizados
4. THE Database SHALL manter a constraint única para is_default
5. THE Database SHALL migrar todos os dados existentes da tabela `personas` para `communication_styles` sem perda de dados

### Requirement 3: Atualizar Referências em Campaigns

**User Story:** Como desenvolvedor, eu quero atualizar a tabela `campaigns` para referenciar `communication_styles` ao invés de `personas`, para que as campanhas usem o conceito correto.

#### Acceptance Criteria

1. THE Database SHALL renomear a coluna `persona_id` para `communication_style_id` na tabela `campaigns`
2. THE Database SHALL manter a foreign key constraint apontando para `communication_styles(id)`
3. THE Database SHALL manter todos os valores existentes de IDs sem alteração
4. THE Database SHALL atualizar o índice `idx_campaigns_persona_id` para `idx_campaigns_communication_style_id`

### Requirement 4: Criar API de Assistentes

**User Story:** Como desenvolvedor frontend, eu quero endpoints REST para gerenciar assistentes, para que a interface possa listar e editar os três assistentes fixos.

#### Acceptance Criteria

1. THE Backend SHALL criar endpoint GET /api/assistants que retorna os 3 assistentes fixos
2. THE Backend SHALL criar endpoint GET /api/assistants/{id} que retorna detalhes de um assistente específico
3. THE Backend SHALL criar endpoint PUT /api/assistants/{id} que atualiza um assistente existente
4. THE Backend SHALL rejeitar requisições DELETE para assistentes (não podem ser excluídos)
5. THE Backend SHALL rejeitar requisições POST para criar novos assistentes (sempre 3 fixos)
6. WHEN um assistente é atualizado, THE Backend SHALL validar que todos os campos obrigatórios estão presentes
7. THE Backend SHALL retornar HTTP 200 para atualizações bem-sucedidas
8. THE Backend SHALL retornar HTTP 404 para assistentes inexistentes
9. THE Backend SHALL retornar HTTP 400 para tentativas de criar ou excluir assistentes

### Requirement 5: Renomear API de Personas para Communication Styles

**User Story:** Como desenvolvedor frontend, eu quero que os endpoints de personas sejam renomeados para communication-styles, para que a API reflita a nova nomenclatura.

#### Acceptance Criteria

1. THE Backend SHALL renomear todos os endpoints de /api/personas para /api/communication-styles
2. THE Backend SHALL manter a mesma funcionalidade de CRUD completo (GET, POST, PUT, DELETE)
3. THE Backend SHALL atualizar todos os modelos Pydantic de Persona* para CommunicationStyle*
4. THE Backend SHALL atualizar todos os serviços e repositórios para usar a nova nomenclatura
5. THE Backend SHALL manter compatibilidade com os dados migrados da tabela personas

### Requirement 6: Criar Interface de Listagem de Assistentes

**User Story:** Como usuário leigo, eu quero ver uma lista dos 3 assistentes (Beto, Cadu, Rita), para que eu possa entender quem faz o quê no sistema.

#### Acceptance Criteria

1. THE Frontend SHALL exibir uma página "Assistentes" acessível via menu de navegação
2. THE Frontend SHALL listar exatamente 3 cards de assistentes com nome, título e descrição resumida
3. THE Frontend SHALL exibir um ícone visual indicando a função de cada assistente (🔍 para Beto, ✍️ para Cadu, 🛡️ para Rita)
4. THE Frontend SHALL exibir um botão "Editar" em cada card de assistente
5. THE Frontend SHALL NÃO exibir botões de "Excluir" ou "Criar Novo" (assistentes são fixos)
6. WHEN o usuário clica em "Editar", THE Frontend SHALL navegar para a página de edição do assistente

### Requirement 7: Criar Interface de Edição de Assistentes

**User Story:** Como usuário leigo, eu quero editar as instruções e princípios de cada assistente, para que eu possa personalizar o comportamento do sistema.

#### Acceptance Criteria

1. THE Frontend SHALL exibir um formulário de edição com campos: nome, título, descrição, instruções, princípios (lista editável), critérios de qualidade (lista editável)
2. THE Frontend SHALL exibir os campos de forma clara com labels descritivos para usuários leigos
3. THE Frontend SHALL permitir adicionar/remover itens nas listas de princípios e critérios de qualidade
4. THE Frontend SHALL exibir um botão "Salvar" que envia as alterações para a API
5. THE Frontend SHALL exibir um botão "Cancelar" que descarta as alterações
6. WHEN o usuário clica em "Salvar", THE Frontend SHALL validar que todos os campos obrigatórios estão preenchidos
7. WHEN a validação falha, THE Frontend SHALL exibir mensagens de erro claras
8. WHEN o salvamento é bem-sucedido, THE Frontend SHALL exibir uma mensagem de sucesso e retornar à lista de assistentes
9. THE Frontend SHALL exibir indicadores de loading durante o salvamento

### Requirement 8: Criar Interface de Listagem de Estilos de Comunicação

**User Story:** Como usuário leigo, eu quero ver uma lista de estilos de comunicação disponíveis, para que eu possa escolher qual usar em minhas campanhas.

#### Acceptance Criteria

1. THE Frontend SHALL exibir uma página "Estilos de Comunicação" acessível via menu de navegação
2. THE Frontend SHALL listar todos os estilos de comunicação em cards com nome, título e indicador de estilo padrão
3. THE Frontend SHALL exibir um badge "Padrão" nos estilos marcados como is_default
4. THE Frontend SHALL exibir botões "Editar" e "Excluir" em cada card
5. THE Frontend SHALL exibir um botão "Criar Novo Estilo" no topo da página
6. WHEN o usuário clica em "Criar Novo Estilo", THE Frontend SHALL navegar para o formulário de criação
7. WHEN o usuário clica em "Editar", THE Frontend SHALL navegar para o formulário de edição
8. WHEN o usuário clica em "Excluir", THE Frontend SHALL exibir um modal de confirmação

### Requirement 9: Criar Interface de Criação/Edição de Estilos de Comunicação

**User Story:** Como usuário leigo, eu quero criar e editar estilos de comunicação, para que eu possa personalizar o tom de voz dos comentários gerados.

#### Acceptance Criteria

1. THE Frontend SHALL exibir um formulário com campos: nome, título, descrição, tom de voz (textarea), princípios (lista editável), vocabulário permitido (lista editável), vocabulário proibido (lista editável), regras de formatação (lista editável), idioma (dropdown), marcar como padrão (checkbox)
2. THE Frontend SHALL exibir tooltips explicativos para cada campo ajudando usuários leigos
3. THE Frontend SHALL permitir adicionar/remover itens nas listas editáveis
4. THE Frontend SHALL exibir um botão "Salvar" que envia os dados para a API
5. THE Frontend SHALL exibir um botão "Cancelar" que descarta as alterações
6. WHEN o usuário clica em "Salvar", THE Frontend SHALL validar que todos os campos obrigatórios estão preenchidos
7. WHEN a validação falha, THE Frontend SHALL exibir mensagens de erro claras
8. WHEN o salvamento é bem-sucedido, THE Frontend SHALL exibir uma mensagem de sucesso e retornar à lista de estilos
9. WHEN o usuário marca um estilo como padrão, THE Frontend SHALL avisar que o estilo padrão anterior será desmarcado

### Requirement 10: Atualizar Interface de Criação de Campanhas

**User Story:** Como usuário leigo, eu quero selecionar um estilo de comunicação ao criar uma campanha, para que os comentários sejam gerados com o tom de voz desejado.

#### Acceptance Criteria

1. THE Frontend SHALL exibir um dropdown "Estilo de Comunicação" no formulário de criação de campanha
2. THE Frontend SHALL popular o dropdown com todos os estilos de comunicação disponíveis
3. THE Frontend SHALL pré-selecionar o estilo marcado como padrão
4. THE Frontend SHALL exibir o nome e título de cada estilo no dropdown
5. THE Frontend SHALL NÃO exibir seleção de assistentes (sempre os 3 fixos)
6. WHEN o usuário submete o formulário, THE Frontend SHALL enviar o communication_style_id selecionado para a API

### Requirement 11: Migrar Dados Existentes

**User Story:** Como desenvolvedor, eu quero migrar os dados existentes de personas para o novo modelo, para que nenhum dado seja perdido na refatoração.

#### Acceptance Criteria

1. THE Migration_Script SHALL criar a tabela `assistants` e popular com os 3 assistentes fixos
2. THE Migration_Script SHALL renomear a tabela `personas` para `communication_styles`
3. THE Migration_Script SHALL atualizar a coluna `persona_id` para `communication_style_id` na tabela `campaigns`
4. THE Migration_Script SHALL executar todas as alterações em uma transação única
5. WHEN a migração falha, THE Migration_Script SHALL fazer rollback de todas as alterações
6. THE Migration_Script SHALL criar um backup dos dados antes da migração
7. THE Migration_Script SHALL validar a integridade dos dados após a migração

### Requirement 12: Atualizar Serviço de Geração de Comentários

**User Story:** Como desenvolvedor, eu quero que o serviço de geração de comentários use o assistente Cadu e o estilo de comunicação selecionado, para que os comentários sejam gerados corretamente.

#### Acceptance Criteria

1. THE Comment_Generation_Service SHALL buscar o assistente Cadu (role='comment') da tabela `assistants`
2. THE Comment_Generation_Service SHALL buscar o estilo de comunicação da campanha usando communication_style_id
3. THE Comment_Generation_Service SHALL combinar as instruções do assistente Cadu com o system_prompt do estilo de comunicação
4. THE Comment_Generation_Service SHALL usar os princípios do estilo de comunicação na geração
5. THE Comment_Generation_Service SHALL aplicar as regras de formatação do estilo de comunicação
6. WHEN o communication_style_id não é fornecido, THE Comment_Generation_Service SHALL usar o estilo padrão

### Requirement 13: Atualizar Serviço de Revisão de Comentários

**User Story:** Como desenvolvedor, eu quero que o serviço de revisão use o assistente Rita, para que os comentários sejam revisados com os critérios corretos.

#### Acceptance Criteria

1. THE Comment_Review_Service SHALL buscar o assistente Rita (role='review') da tabela `assistants`
2. THE Comment_Review_Service SHALL usar as instruções e princípios de Rita para revisar comentários
3. THE Comment_Review_Service SHALL aplicar os quality_criteria de Rita na avaliação
4. THE Comment_Review_Service SHALL retornar veredito APPROVED ou REJECTED baseado nos critérios de Rita

### Requirement 14: Atualizar Serviço de Busca de Posts

**User Story:** Como desenvolvedor, eu quero que o serviço de busca use o assistente Beto, para que os posts sejam encontrados com os critérios corretos.

#### Acceptance Criteria

1. THE Search_Service SHALL buscar o assistente Beto (role='search') da tabela `assistants`
2. THE Search_Service SHALL usar as instruções e princípios de Beto para buscar posts
3. THE Search_Service SHALL aplicar os critérios de qualidade de Beto na filtragem de posts
4. THE Search_Service SHALL usar as skills de Beto (Apify) para executar a busca

### Requirement 15: Criar Documentação para Usuários

**User Story:** Como usuário leigo, eu quero documentação clara sobre assistentes e estilos de comunicação, para que eu possa entender e usar o sistema corretamente.

#### Acceptance Criteria

1. THE Documentation SHALL explicar a diferença entre assistentes e estilos de comunicação
2. THE Documentation SHALL descrever a função de cada assistente (Beto, Cadu, Rita)
3. THE Documentation SHALL fornecer exemplos de como editar assistentes
4. THE Documentation SHALL fornecer exemplos de como criar estilos de comunicação
5. THE Documentation SHALL incluir screenshots da interface
6. THE Documentation SHALL estar disponível em português

### Requirement 16: Validar Integridade Referencial

**User Story:** Como desenvolvedor, eu quero garantir a integridade referencial entre campanhas e estilos de comunicação, para que não existam referências quebradas.

#### Acceptance Criteria

1. THE Database SHALL manter foreign key constraint entre campaigns.communication_style_id e communication_styles.id
2. THE Database SHALL configurar ON DELETE RESTRICT para impedir exclusão de estilos em uso
3. WHEN um usuário tenta excluir um estilo em uso, THE Backend SHALL retornar HTTP 400 com mensagem clara
4. THE Backend SHALL listar quais campanhas usam um estilo antes de permitir exclusão

### Requirement 17: Criar Testes de Integração

**User Story:** Como desenvolvedor, eu quero testes de integração para os novos endpoints, para que a refatoração seja confiável.

#### Acceptance Criteria

1. THE Test_Suite SHALL incluir testes para todos os endpoints de assistants
2. THE Test_Suite SHALL incluir testes para todos os endpoints de communication-styles
3. THE Test_Suite SHALL incluir testes para a migração de dados
4. THE Test_Suite SHALL incluir testes para a integração com serviços de comentário e revisão
5. THE Test_Suite SHALL validar que assistentes não podem ser criados ou excluídos
6. THE Test_Suite SHALL validar que estilos de comunicação podem ser criados e excluídos (se não em uso)

### Requirement 18: Criar Script de Rollback

**User Story:** Como desenvolvedor, eu quero um script de rollback da migração, para que possamos reverter em caso de problemas.

#### Acceptance Criteria

1. THE Rollback_Script SHALL reverter a renomeação de `communication_styles` para `personas`
2. THE Rollback_Script SHALL reverter a renomeação de `communication_style_id` para `persona_id`
3. THE Rollback_Script SHALL excluir a tabela `assistants`
4. THE Rollback_Script SHALL restaurar todos os índices e constraints originais
5. THE Rollback_Script SHALL executar todas as alterações em uma transação única
6. WHEN o rollback falha, THE Rollback_Script SHALL fazer rollback da transação e reportar erro

### Requirement 19: Atualizar Modelos Pydantic

**User Story:** Como desenvolvedor, eu quero modelos Pydantic atualizados para assistentes e estilos de comunicação, para que a validação de dados seja correta.

#### Acceptance Criteria

1. THE Backend SHALL criar modelos Assistant, AssistantSummary, AssistantUpdateDTO
2. THE Backend SHALL renomear modelos Persona* para CommunicationStyle*
3. THE Backend SHALL validar que name, title, description, instructions não podem ser vazios
4. THE Backend SHALL validar que principles e quality_criteria são listas não vazias
5. THE Backend SHALL validar que role é um dos valores: 'search', 'comment', 'review'
6. THE Backend SHALL validar que skills é uma lista de strings válidas

### Requirement 20: Atualizar Repositórios

**User Story:** Como desenvolvedor, eu quero repositórios atualizados para assistentes e estilos de comunicação, para que o acesso ao banco de dados seja correto.

#### Acceptance Criteria

1. THE Backend SHALL criar AssistantRepository com métodos: list_all(), get_by_id(), get_by_role(), update()
2. THE Backend SHALL renomear PersonaRepository para CommunicationStyleRepository
3. THE Backend SHALL atualizar todos os métodos para usar a tabela `communication_styles`
4. THE Backend SHALL manter os mesmos métodos de CRUD existentes
5. THE Backend SHALL adicionar método get_by_role() no AssistantRepository para buscar por função
