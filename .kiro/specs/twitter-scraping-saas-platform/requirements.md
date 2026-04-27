# Requirements Document

## Introduction

Esta especificação define os requisitos para transformar os agentes de scraping do Twitter existentes (twitter-monitoring-squad e twitter-outreach-squad) em uma plataforma web SaaS completa. A plataforma permitirá que usuários configurem credenciais, criem e executem campanhas de scraping do Twitter, visualizem resultados e acessem histórico de campanhas anteriores.

O sistema migrará a lógica existente em Node.js para Python no backend, utilizará React no frontend, Supabase como banco de dados, e manterá a integração com Apify para scraping e OpenAI para análise de conteúdo.

## Glossary

- **Platform**: O sistema web SaaS completo que engloba frontend, backend e banco de dados
- **User**: Pessoa que utiliza a plataforma (single-user no MVP, sem autenticação)
- **Campaign**: Uma configuração de scraping do Twitter com parâmetros específicos (keywords, perfis, filtros)
- **Scraping_Engine**: Componente backend responsável por executar o scraping via Apify
- **Analysis_Engine**: Componente backend responsável por processar resultados com OpenAI
- **Document_Generator**: Componente backend responsável por gerar arquivos .doc
- **Email_Service**: Componente backend responsável por enviar emails com arquivos anexados
- **Configuration_Manager**: Componente backend responsável por gerenciar credenciais do usuário
- **Campaign_Executor**: Componente backend responsável por orquestrar a execução completa de uma campanha
- **Storage_Service**: Supabase Storage para armazenamento de arquivos .doc
- **Database**: Supabase PostgreSQL para persistência de dados
- **Queue_System**: Sistema de fila para processamento assíncrono de campanhas
- **Frontend**: Aplicação React que fornece a interface do usuário
- **Backend**: Aplicação Python que processa requisições e executa lógica de negócio
- **API_Token**: Credencial de acesso para serviços externos (Apify, OpenAI)
- **Search_Type**: Tipo de busca no Twitter (Profile ou Keywords)
- **Profile_Search**: Busca por tweets de perfis específicos (formato @usuario)
- **Keyword_Search**: Busca por tweets contendo palavras-chave específicas
- **Engagement_Filter**: Filtro baseado em métricas de engajamento (likes, retweets, replies)
- **Campaign_Status**: Estado atual de uma campanha (pending, running, completed, failed)
- **Result_Set**: Conjunto de tweets coletados e processados de uma campanha
- **History_Record**: Registro histórico de uma campanha executada

## Requirements

### Requirement 1: Gerenciamento de Configurações do Usuário

**User Story:** Como um usuário, eu quero salvar minhas credenciais de API e email na plataforma, para que eu possa executar campanhas sem precisar inserir essas informações repetidamente.

#### Acceptance Criteria

1. THE Frontend SHALL exibir uma página de configurações com campos para email do usuário, token da API do Apify e token da API da OpenAI
2. WHEN o usuário submete o formulário de configurações, THE Backend SHALL validar que todos os campos obrigatórios estão preenchidos
3. WHEN a validação é bem-sucedida, THE Configuration_Manager SHALL armazenar as credenciais no Database de forma segura
4. THE Backend SHALL nunca expor tokens de API completos no Frontend (apenas indicadores de presença ou primeiros/últimos caracteres)
5. WHEN o usuário acessa a página de configurações novamente, THE Frontend SHALL exibir os valores salvos (com tokens parcialmente mascarados)
6. THE Frontend SHALL permitir edição de todas as configurações salvas
7. WHEN o usuário atualiza uma configuração, THE Configuration_Manager SHALL sobrescrever o valor anterior no Database
8. IF o usuário tenta criar uma campanha sem configurações salvas, THEN THE Backend SHALL retornar erro indicando configurações faltantes

### Requirement 2: Criação de Campanhas de Scraping

**User Story:** Como um usuário, eu quero criar campanhas de scraping do Twitter com parâmetros personalizados, para que eu possa coletar dados relevantes para minhas necessidades específicas.

#### Acceptance Criteria

1. THE Frontend SHALL exibir uma página de criação de campanha com formulário contendo todos os campos necessários
2. THE Frontend SHALL incluir campo obrigatório para nome da campanha
3. THE Frontend SHALL incluir campo de seleção de rede social com valor fixo "Twitter" (estrutura preparada para múltiplas redes)
4. THE Frontend SHALL incluir campo de seleção de tipo de busca com opções "Profile" e "Keywords"
5. WHEN o tipo de busca é "Profile", THE Frontend SHALL exibir campo de texto para entrada de perfis no formato @usuario (múltiplos perfis separados por vírgula ou linha)
6. WHEN o tipo de busca é "Keywords", THE Frontend SHALL exibir campo de texto para entrada de palavras-chave (múltiplas keywords separadas por vírgula ou linha)
7. THE Frontend SHALL incluir campo de seleção de idioma
8. THE Frontend SHALL incluir campos numéricos opcionais para filtros de engajamento: likes mínimos, retweets mínimos e replies mínimos
9. WHEN um filtro de engajamento não é preenchido, THE Backend SHALL usar valor padrão 0
10. THE Frontend SHALL incluir botões "Criar Campanha" e "Cancelar"
11. WHEN o usuário clica em "Cancelar", THE Frontend SHALL descartar dados do formulário e retornar à página anterior
12. WHEN o usuário clica em "Criar Campanha", THE Frontend SHALL validar campos obrigatórios antes de enviar ao Backend
13. WHEN a validação do Frontend falha, THE Frontend SHALL exibir mensagens de erro específicas para cada campo inválido

### Requirement 3: Validação e Transformação de Dados de Campanha

**User Story:** Como um desenvolvedor, eu quero que o backend valide e transforme os dados da campanha corretamente, para que o scraping seja executado com parâmetros adequados.

#### Acceptance Criteria

1. WHEN o Backend recebe uma requisição de criação de campanha, THE Backend SHALL validar que o nome da campanha não está vazio
2. WHEN o tipo de busca é "Profile", THE Backend SHALL validar que ao menos um perfil foi fornecido
3. WHEN o tipo de busca é "Keywords", THE Backend SHALL validar que ao menos uma keyword foi fornecida
4. WHEN perfis são fornecidos com símbolo @, THE Backend SHALL remover o símbolo @ antes de processar
5. THE Backend SHALL nunca modificar ou expandir automaticamente as keywords fornecidas pelo usuário
6. THE Backend SHALL validar que filtros de engajamento são números não-negativos
7. WHEN a validação falha, THE Backend SHALL retornar erro HTTP 400 com mensagem descritiva do problema
8. WHEN a validação é bem-sucedida, THE Backend SHALL transformar os dados de entrada em configuração de scraping compatível com Apify
9. THE Backend SHALL persistir a configuração da campanha no Database com status "pending"
10. THE Backend SHALL retornar resposta de sucesso com ID da campanha criada

### Requirement 4: Execução Automática de Campanhas

**User Story:** Como um usuário, eu quero que minhas campanhas sejam executadas automaticamente após a criação, para que eu não precise iniciar manualmente o processo de scraping.

#### Acceptance Criteria

1. WHEN uma campanha é criada com sucesso, THE Backend SHALL adicionar a campanha à Queue_System imediatamente
2. THE Campaign_Executor SHALL processar campanhas da Queue_System em ordem FIFO (First In, First Out)
3. WHEN o Campaign_Executor inicia processamento de uma campanha, THE Campaign_Executor SHALL atualizar o status da campanha para "running" no Database
4. THE Campaign_Executor SHALL recuperar as credenciais do usuário do Configuration_Manager
5. THE Campaign_Executor SHALL invocar o Scraping_Engine com a configuração da campanha e credenciais do Apify
6. THE Campaign_Executor SHALL aguardar conclusão do scraping antes de prosseguir para próxima etapa
7. IF o scraping falha, THEN THE Campaign_Executor SHALL atualizar status da campanha para "failed" e registrar mensagem de erro no Database
8. WHEN o scraping é bem-sucedido, THE Campaign_Executor SHALL invocar o Analysis_Engine com os resultados coletados e credenciais da OpenAI
9. WHEN a análise é concluída, THE Campaign_Executor SHALL invocar o Document_Generator para criar arquivo .doc
10. WHEN o arquivo é gerado, THE Campaign_Executor SHALL invocar o Email_Service para enviar o arquivo ao usuário
11. WHEN o email é enviado, THE Campaign_Executor SHALL salvar o arquivo no Storage_Service
12. WHEN todas as etapas são concluídas, THE Campaign_Executor SHALL atualizar status da campanha para "completed" no Database

### Requirement 5: Scraping do Twitter via Apify

**User Story:** Como um desenvolvedor, eu quero que o sistema execute scraping do Twitter usando a mesma lógica do código existente, para que os resultados sejam consistentes e confiáveis.

#### Acceptance Criteria

1. THE Scraping_Engine SHALL ser implementado em Python adaptando a lógica de search-twitter.js
2. WHEN o tipo de busca é "Profile", THE Scraping_Engine SHALL construir query usando operador "from:" para cada perfil
3. WHEN múltiplos perfis são fornecidos, THE Scraping_Engine SHALL combinar queries com operador "OR"
4. WHEN o tipo de busca é "Keywords", THE Scraping_Engine SHALL construir query usando as keywords fornecidas combinadas com operador "OR"
5. THE Scraping_Engine SHALL adicionar operador "lang:" à query com o idioma selecionado
6. WHEN filtro de likes mínimos é maior que 0, THE Scraping_Engine SHALL adicionar operador "min_faves:" à query
7. WHEN filtro de replies mínimos é maior que 0, THE Scraping_Engine SHALL adicionar operador "min_replies:" à query
8. THE Scraping_Engine SHALL adicionar operador "since:" à query baseado no intervalo de tempo configurado
9. THE Scraping_Engine SHALL invocar o actor "automation-lab/twitter-scraper" do Apify com a query construída
10. THE Scraping_Engine SHALL passar cookies de autenticação do Twitter (auth_token e ct0) na requisição ao Apify
11. WHEN o Apify retorna resultados, THE Scraping_Engine SHALL aplicar filtros localmente para garantir conformidade com critérios de engajamento
12. THE Scraping_Engine SHALL transformar resultados em formato padronizado contendo: id, url, author, text, likes, reposts, replies, timestamp
13. THE Scraping_Engine SHALL retornar lista de tweets qualificados ao Campaign_Executor

### Requirement 6: Análise de Conteúdo com OpenAI

**User Story:** Como um usuário, eu quero que os tweets coletados sejam analisados pela OpenAI, para que eu receba insights relevantes sobre o conteúdo.

#### Acceptance Criteria

1. THE Analysis_Engine SHALL receber lista de tweets do Scraping_Engine
2. THE Analysis_Engine SHALL usar credenciais da OpenAI armazenadas no Configuration_Manager
3. THE Analysis_Engine SHALL processar tweets usando a API da OpenAI
4. THE Analysis_Engine SHALL gerar análise estruturada do conteúdo coletado
5. THE Analysis_Engine SHALL retornar resultados da análise ao Campaign_Executor
6. IF a API da OpenAI retorna erro, THEN THE Analysis_Engine SHALL propagar erro ao Campaign_Executor

### Requirement 7: Geração de Documentos

**User Story:** Como um usuário, eu quero receber um arquivo .doc com os resultados da campanha, para que eu possa revisar e compartilhar os dados coletados.

#### Acceptance Criteria

1. THE Document_Generator SHALL receber tweets coletados e análise da OpenAI
2. THE Document_Generator SHALL criar arquivo no formato .doc (Microsoft Word)
3. THE Document_Generator SHALL incluir no documento: nome da campanha, data de execução, parâmetros utilizados, tweets coletados e análise gerada
4. THE Document_Generator SHALL formatar o documento de forma legível e profissional
5. THE Document_Generator SHALL retornar caminho do arquivo gerado ao Campaign_Executor

### Requirement 8: Envio de Email com Resultados

**User Story:** Como um usuário, eu quero receber um email com o arquivo de resultados anexado, para que eu seja notificado quando a campanha for concluída.

#### Acceptance Criteria

1. THE Email_Service SHALL ser implementado em Python adaptando a lógica de send-gmail.ts
2. THE Email_Service SHALL usar credenciais SMTP do Gmail armazenadas no Configuration_Manager
3. THE Email_Service SHALL usar o email do usuário armazenado como destinatário
4. THE Email_Service SHALL criar email com assunto descritivo incluindo nome da campanha
5. THE Email_Service SHALL incluir no corpo do email: resumo da campanha, quantidade de tweets coletados e link para visualização na plataforma
6. THE Email_Service SHALL anexar o arquivo .doc gerado ao email
7. THE Email_Service SHALL enviar o email usando SMTP do Gmail
8. WHEN o envio é bem-sucedido, THE Email_Service SHALL retornar confirmação ao Campaign_Executor
9. IF o envio falha, THEN THE Email_Service SHALL retornar erro ao Campaign_Executor

### Requirement 9: Armazenamento de Arquivos

**User Story:** Como um usuário, eu quero que os arquivos gerados sejam armazenados na plataforma, para que eu possa acessá-los posteriormente sem depender do email.

#### Acceptance Criteria

1. THE Storage_Service SHALL usar Supabase Storage para armazenar arquivos .doc
2. WHEN o Campaign_Executor recebe arquivo gerado, THE Storage_Service SHALL fazer upload do arquivo para Supabase Storage
3. THE Storage_Service SHALL organizar arquivos em estrutura de pastas por campanha
4. THE Storage_Service SHALL gerar URL de acesso ao arquivo armazenado
5. THE Storage_Service SHALL salvar URL do arquivo no registro da campanha no Database
6. THE Storage_Service SHALL retornar confirmação de sucesso ao Campaign_Executor
7. IF o upload falha, THEN THE Storage_Service SHALL retornar erro ao Campaign_Executor

### Requirement 10: Visualização de Histórico de Campanhas

**User Story:** Como um usuário, eu quero visualizar uma lista de todas as campanhas que executei, para que eu possa acompanhar meu histórico de scraping.

#### Acceptance Criteria

1. THE Frontend SHALL exibir uma página de histórico de campanhas
2. THE Frontend SHALL listar todas as campanhas ordenadas por data de criação (mais recentes primeiro)
3. THE Frontend SHALL exibir para cada campanha: nome, data de criação, status e quantidade de resultados
4. WHEN o status é "pending", THE Frontend SHALL exibir indicador visual de aguardando processamento
5. WHEN o status é "running", THE Frontend SHALL exibir indicador visual de em execução
6. WHEN o status é "completed", THE Frontend SHALL exibir indicador visual de concluída com sucesso
7. WHEN o status é "failed", THE Frontend SHALL exibir indicador visual de falha
8. THE Frontend SHALL permitir que o usuário clique em uma campanha para ver detalhes
9. THE Backend SHALL fornecer endpoint para listar campanhas com paginação
10. THE Backend SHALL retornar dados de campanhas do Database

### Requirement 11: Visualização de Detalhes de Campanha

**User Story:** Como um usuário, eu quero visualizar detalhes completos de uma campanha específica, para que eu possa revisar a configuração utilizada e os resultados obtidos.

#### Acceptance Criteria

1. WHEN o usuário clica em uma campanha no histórico, THE Frontend SHALL navegar para página de detalhes da campanha
2. THE Frontend SHALL exibir nome da campanha, data de criação e status
3. THE Frontend SHALL exibir seção "Configuração Utilizada" contendo: tipo de busca, perfis ou keywords, idioma e filtros de engajamento
4. WHEN o status é "completed", THE Frontend SHALL exibir seção "Resultados" contendo lista de tweets coletados
5. THE Frontend SHALL exibir para cada tweet: autor, texto, likes, retweets, replies e timestamp
6. THE Frontend SHALL exibir link para visualizar tweet original no Twitter
7. WHEN o status é "failed", THE Frontend SHALL exibir mensagem de erro detalhada
8. WHEN a campanha possui arquivo .doc associado, THE Frontend SHALL exibir botão "Visualizar Documento"
9. WHEN a campanha possui arquivo .doc associado, THE Frontend SHALL exibir botão "Baixar Documento"
10. THE Backend SHALL fornecer endpoint para recuperar detalhes completos de uma campanha específica
11. THE Backend SHALL retornar dados da campanha e resultados associados do Database

### Requirement 12: Download de Arquivos Gerados

**User Story:** Como um usuário, eu quero baixar os arquivos .doc gerados pelas campanhas, para que eu possa trabalhar com os dados offline.

#### Acceptance Criteria

1. WHEN o usuário clica em "Baixar Documento" na página de detalhes, THE Frontend SHALL iniciar download do arquivo .doc
2. THE Backend SHALL fornecer endpoint para download de arquivos
3. WHEN o Backend recebe requisição de download, THE Backend SHALL recuperar URL do arquivo do Database
4. THE Backend SHALL gerar URL assinada temporária do Supabase Storage
5. THE Backend SHALL retornar URL assinada ao Frontend
6. THE Frontend SHALL redirecionar navegador para URL assinada para iniciar download
7. THE Backend SHALL validar que o arquivo existe antes de gerar URL assinada
8. IF o arquivo não existe, THEN THE Backend SHALL retornar erro HTTP 404

### Requirement 13: Visualização de Arquivos Gerados

**User Story:** Como um usuário, eu quero visualizar os arquivos .doc diretamente na plataforma, para que eu possa revisar rapidamente os resultados sem precisar baixar.

#### Acceptance Criteria

1. WHEN o usuário clica em "Visualizar Documento" na página de detalhes, THE Frontend SHALL exibir preview do arquivo .doc
2. THE Frontend SHALL usar componente de visualização de documentos compatível com formato .doc
3. THE Frontend SHALL carregar conteúdo do arquivo do Supabase Storage
4. THE Frontend SHALL exibir documento em modo somente leitura
5. THE Frontend SHALL incluir opção para fechar visualização e retornar aos detalhes da campanha
6. IF o arquivo não pode ser visualizado, THEN THE Frontend SHALL exibir mensagem de erro e oferecer opção de download

### Requirement 14: Feedback Visual Durante Execução de Campanha

**User Story:** Como um usuário, eu quero receber feedback visual enquanto minha campanha está sendo executada, para que eu saiba que o processo está em andamento.

#### Acceptance Criteria

1. WHEN o usuário cria uma campanha, THE Frontend SHALL exibir mensagem de confirmação
2. THE Frontend SHALL exibir indicador de loading durante submissão do formulário
3. WHEN a campanha é criada com sucesso, THE Frontend SHALL exibir mensagem de sucesso informando que a execução foi iniciada
4. THE Frontend SHALL redirecionar automaticamente para página de histórico após 3 segundos
5. WHEN ocorre erro na criação, THE Frontend SHALL exibir mensagem de erro clara e específica
6. THE Frontend SHALL manter dados do formulário em caso de erro para permitir correção
7. WHEN o usuário está na página de histórico, THE Frontend SHALL atualizar status das campanhas automaticamente a cada 10 segundos
8. THE Frontend SHALL exibir indicador visual de atualização automática

### Requirement 15: Tratamento de Erros e Mensagens Claras

**User Story:** Como um usuário, eu quero receber mensagens de erro claras e específicas, para que eu possa entender e corrigir problemas rapidamente.

#### Acceptance Criteria

1. WHEN ocorre erro de validação, THE Frontend SHALL exibir mensagem específica para cada campo inválido
2. WHEN ocorre erro de comunicação com Backend, THE Frontend SHALL exibir mensagem indicando problema de conexão
3. WHEN o Backend retorna erro, THE Backend SHALL incluir mensagem descritiva e código de erro apropriado
4. WHEN credenciais de API são inválidas, THE Backend SHALL retornar mensagem indicando qual credencial está incorreta
5. WHEN o scraping falha, THE Backend SHALL registrar erro detalhado no Database incluindo stack trace
6. WHEN o usuário visualiza campanha com status "failed", THE Frontend SHALL exibir mensagem de erro em linguagem compreensível
7. THE Frontend SHALL evitar expor detalhes técnicos sensíveis ao usuário (tokens, stack traces completos)
8. THE Backend SHALL logar todos os erros para facilitar debugging

### Requirement 16: Segurança de Credenciais

**User Story:** Como um usuário, eu quero que minhas credenciais sejam armazenadas de forma segura, para que meus tokens de API não sejam expostos ou comprometidos.

#### Acceptance Criteria

1. THE Backend SHALL armazenar tokens de API criptografados no Database
2. THE Backend SHALL usar algoritmo de criptografia forte (AES-256 ou superior)
3. THE Backend SHALL nunca retornar tokens completos em respostas de API
4. WHEN o Frontend solicita configurações, THE Backend SHALL retornar apenas indicadores de presença de tokens (ex: "apify_api_XXX...XXX")
5. THE Backend SHALL validar tokens antes de armazenar (formato básico)
6. THE Backend SHALL usar variáveis de ambiente para chave de criptografia
7. THE Backend SHALL nunca logar tokens completos em logs de aplicação
8. THE Backend SHALL usar HTTPS para todas as comunicações entre Frontend e Backend

### Requirement 17: Estrutura Preparada para Múltiplas Redes Sociais

**User Story:** Como um desenvolvedor, eu quero que a arquitetura suporte múltiplas redes sociais no futuro, para que possamos expandir a plataforma facilmente.

#### Acceptance Criteria

1. THE Database SHALL incluir campo "social_network" na tabela de campanhas
2. THE Backend SHALL implementar interface abstrata para scraping engines
3. THE Scraping_Engine para Twitter SHALL implementar interface abstrata
4. THE Backend SHALL usar factory pattern para instanciar scraping engine apropriado baseado na rede social
5. THE Frontend SHALL estruturar formulário de criação de campanha para suportar campos dinâmicos por rede social
6. THE Database SHALL usar estrutura flexível (JSONB) para armazenar configurações específicas de cada rede social
7. THE Backend SHALL validar configurações baseado na rede social selecionada

### Requirement 18: Sistema de Fila para Processamento Assíncrono

**User Story:** Como um desenvolvedor, eu quero que campanhas sejam processadas de forma assíncrona usando fila, para que múltiplas campanhas possam ser gerenciadas eficientemente.

#### Acceptance Criteria

1. THE Backend SHALL implementar Queue_System para processamento assíncrono
2. THE Queue_System SHALL usar tecnologia apropriada para Python (Celery, RQ ou similar)
3. WHEN uma campanha é criada, THE Backend SHALL adicionar tarefa à fila imediatamente
4. THE Queue_System SHALL processar tarefas em ordem FIFO
5. THE Queue_System SHALL suportar retry automático em caso de falhas transientes
6. THE Queue_System SHALL limitar número de tentativas de retry (máximo 3)
7. WHEN todas as tentativas falham, THE Queue_System SHALL marcar campanha como "failed"
8. THE Queue_System SHALL permitir processamento paralelo de múltiplas campanhas
9. THE Backend SHALL fornecer configuração para número máximo de workers

### Requirement 19: Persistência de Dados no Supabase

**User Story:** Como um desenvolvedor, eu quero que todos os dados sejam persistidos no Supabase, para que tenhamos banco de dados gerenciado e confiável.

#### Acceptance Criteria

1. THE Database SHALL usar Supabase PostgreSQL
2. THE Database SHALL incluir tabela "configurations" para armazenar credenciais do usuário
3. THE Database SHALL incluir tabela "campaigns" para armazenar campanhas e seus status
4. THE Database SHALL incluir tabela "campaign_results" para armazenar tweets coletados
5. THE Database SHALL usar relacionamento one-to-many entre campaigns e campaign_results
6. THE Database SHALL incluir índices apropriados para queries de listagem e busca
7. THE Database SHALL usar timestamps automáticos (created_at, updated_at)
8. THE Backend SHALL usar biblioteca de cliente Supabase para Python
9. THE Backend SHALL implementar connection pooling para otimizar performance

### Requirement 20: Parser de Configuração de Campanha

**User Story:** Como um desenvolvedor, eu quero que o sistema parse corretamente entradas de perfis e keywords, para que usuários possam inserir dados em formatos flexíveis.

#### Acceptance Criteria

1. WHEN o usuário insere múltiplos perfis separados por vírgula, THE Backend SHALL parsear em lista de perfis individuais
2. WHEN o usuário insere múltiplos perfis separados por quebra de linha, THE Backend SHALL parsear em lista de perfis individuais
3. WHEN o usuário insere múltiplas keywords separadas por vírgula, THE Backend SHALL parsear em lista de keywords individuais
4. WHEN o usuário insere múltiplas keywords separadas por quebra de linha, THE Backend SHALL parsear em lista de keywords individuais
5. THE Backend SHALL remover espaços em branco extras no início e fim de cada item
6. THE Backend SHALL remover itens vazios da lista após parsing
7. WHEN perfis contêm símbolo @, THE Backend SHALL remover o símbolo antes de armazenar
8. THE Backend SHALL preservar texto exato das keywords sem modificações (exceto trim)
9. THE Backend SHALL validar que lista resultante não está vazia após parsing

### Requirement 21: Pretty Printer para Configuração de Campanha

**User Story:** Como um desenvolvedor, eu quero que configurações de campanha sejam formatadas de forma legível, para que usuários possam revisar facilmente os parâmetros utilizados.

#### Acceptance Criteria

1. THE Backend SHALL implementar função de formatação para configurações de campanha
2. WHEN a configuração é exibida no Frontend, THE Backend SHALL formatar perfis como lista com símbolo @ prefixado
3. WHEN a configuração é exibida no Frontend, THE Backend SHALL formatar keywords como lista legível
4. THE Backend SHALL formatar filtros de engajamento com labels descritivos (ex: "Mínimo de 10 likes")
5. WHEN um filtro tem valor 0, THE Backend SHALL exibir "Sem filtro" ou equivalente
6. THE Backend SHALL formatar idioma com nome completo (ex: "Inglês" ao invés de "en")
7. THE Backend SHALL formatar tipo de busca com label descritivo (ex: "Busca por Perfis" ao invés de "profile")

### Requirement 22: Round-Trip de Configuração de Campanha

**User Story:** Como um desenvolvedor, eu quero garantir que configurações de campanha sejam preservadas corretamente, para que dados não sejam perdidos ou corrompidos durante processamento.

#### Acceptance Criteria

1. FOR ALL configurações de campanha válidas, parsear a configuração, formatá-la e parsear novamente SHALL produzir configuração equivalente
2. THE Backend SHALL implementar testes automatizados para verificar propriedade de round-trip
3. THE Backend SHALL validar integridade de configuração antes de executar campanha
4. WHEN configuração armazenada está corrompida, THE Backend SHALL retornar erro ao tentar executar campanha
5. THE Backend SHALL logar warning quando detectar inconsistência em configuração armazenada
