# Requirements: Sistema de Personas e Geração de Comentários com IA

## 1. Visão Geral

### 1.1 Objetivo
Implementar um sistema completo de gestão de personas e geração automática de comentários sugeridos para tweets coletados, permitindo que usuários criem múltiplas personas com diferentes tons de voz e as utilizem em campanhas de scraping do Twitter.

### 1.2 Problema Atual
- Sistema atual apenas coleta e filtra tweets
- Não há análise de qualidade dos tweets
- Não há geração de comentários sugeridos
- Usuário precisa manualmente criar respostas para engajamento
- Falta de padronização no tom de voz das respostas

### 1.3 Solução Proposta
Sistema que permite:
1. Criar e gerenciar múltiplas personas (CRUD completo)
2. Selecionar persona ao criar campanha
3. Analisar tweets coletados usando IA
4. Gerar comentários sugeridos baseados na persona
5. Pontuar tweets por qualidade
6. Exibir top 3 tweets com comentários no email
7. Mostrar todos os comentários no documento e na plataforma

---

## 2. Requisitos Funcionais

### 2.1 Gestão de Personas (CRUD)

#### RF-001: Criar Persona
**Prioridade:** Alta  
**Descrição:** Usuário deve poder criar uma nova persona com todos os campos necessários.

**Campos da Persona:**
- **Nome** (obrigatório): Nome identificador da persona (ex: "Strategic Partner")
- **Título** (obrigatório): Título/função da persona (ex: "Social Media Copywriter")
- **Descrição** (obrigatório): Descrição detalhada do papel e identidade
- **Tom de Voz** (obrigatório): Instruções sobre como a persona se comunica
- **Princípios** (obrigatório): Lista de princípios que a persona segue
- **Vocabulário Permitido** (opcional): Palavras/frases que a persona deve usar
- **Vocabulário Proibido** (opcional): Palavras/frases que a persona NÃO deve usar
- **Regras de Formatação** (opcional): Regras específicas (ex: "Sem emojis", "Máx 280 chars")
- **Idioma** (obrigatório): Idioma dos comentários (padrão: "en")
- **Prompt do Sistema** (obrigatório): Prompt completo para o LLM

**Critérios de Aceitação:**
- [ ] Formulário de criação com todos os campos
- [ ] Validação de campos obrigatórios
- [ ] Salvar persona no banco de dados
- [ ] Mensagem de sucesso após criação
- [ ] Redirecionamento para lista de personas

#### RF-002: Listar Personas
**Prioridade:** Alta  
**Descrição:** Usuário deve ver lista de todas as personas criadas.

**Critérios de Aceitação:**
- [ ] Exibir lista paginada de personas
- [ ] Mostrar nome, título e data de criação
- [ ] Botão para criar nova persona
- [ ] Botões de ação (editar, excluir, visualizar)
- [ ] Indicador de persona padrão (se houver)

#### RF-003: Visualizar Persona
**Prioridade:** Média  
**Descrição:** Usuário deve poder ver todos os detalhes de uma persona.

**Critérios de Aceitação:**
- [ ] Página de detalhes com todos os campos
- [ ] Formatação clara e legível
- [ ] Botões para editar e excluir
- [ ] Botão para voltar à lista

#### RF-004: Editar Persona
**Prioridade:** Alta  
**Descrição:** Usuário deve poder editar uma persona existente.

**Critérios de Aceitação:**
- [ ] Formulário pré-preenchido com dados atuais
- [ ] Validação de campos obrigatórios
- [ ] Atualizar persona no banco de dados
- [ ] Mensagem de sucesso após edição
- [ ] Campanhas existentes mantêm referência à persona

#### RF-005: Excluir Persona
**Prioridade:** Média  
**Descrição:** Usuário deve poder excluir uma persona.

**Critérios de Aceitação:**
- [ ] Confirmação antes de excluir
- [ ] Verificar se persona está em uso por campanhas
- [ ] Se em uso, avisar usuário e impedir exclusão OU permitir com aviso
- [ ] Remover persona do banco de dados
- [ ] Mensagem de sucesso após exclusão

#### RF-006: Persona Padrão
**Prioridade:** Baixa  
**Descrição:** Sistema deve ter uma persona padrão pré-configurada.

**Critérios de Aceitação:**
- [ ] Persona "Strategic Partner" criada automaticamente
- [ ] Baseada na persona do Cadu da squad
- [ ] Marcada como padrão
- [ ] Usada automaticamente se usuário não selecionar

---

### 2.2 Integração com Campanhas

#### RF-007: Selecionar Persona na Campanha
**Prioridade:** Alta  
**Descrição:** Ao criar campanha, usuário deve selecionar qual persona usar.

**Critérios de Aceitação:**
- [ ] Campo "Persona" no formulário de criação de campanha
- [ ] Dropdown com lista de personas disponíveis
- [ ] Persona padrão pré-selecionada
- [ ] Salvar persona_id na campanha
- [ ] Exibir persona selecionada nos detalhes da campanha

#### RF-008: Campanha sem Persona
**Prioridade:** Baixa  
**Descrição:** Se usuário não selecionar persona, usar padrão.

**Critérios de Aceitação:**
- [ ] Se campo vazio, usar persona padrão
- [ ] Se não houver padrão, usar primeira persona disponível
- [ ] Se não houver nenhuma persona, criar padrão automaticamente

---

### 2.3 Análise de Tweets

#### RF-009: Analisar Qualidade dos Tweets
**Prioridade:** Alta  
**Descrição:** Sistema deve analisar cada tweet coletado usando IA.

**Critérios de Pontuação:**
1. **Lead Relevance** (0-10): Autor é tomador de decisão relevante?
2. **Tone of Voice** (0-10): Tom profissional e consultivo?
3. **Insight Strength** (0-10): Tweet fornece insights valiosos?
4. **Engagement Potential** (0-10): Convida à conversa significativa?
5. **Brand Safety** (0-10): Seguro para engajamento da marca?

**Critérios de Aceitação:**
- [ ] Usar OpenAI para análise
- [ ] Calcular score médio (média dos 5 critérios)
- [ ] Gerar veredito: APPROVED (média >= 8) ou REJECTED (média < 8)
- [ ] Gerar notas explicativas sobre os scores
- [ ] Salvar análise no banco de dados

#### RF-010: Selecionar Top 3 Tweets
**Prioridade:** Alta  
**Descrição:** Sistema deve selecionar os 3 melhores tweets baseado nos scores.

**Critérios de Aceitação:**
- [ ] Ordenar tweets por score médio (maior para menor)
- [ ] Selecionar top 3
- [ ] Marcar como "featured" no banco de dados
- [ ] Usar no corpo do email

---

### 2.4 Geração de Comentários

#### RF-011: Gerar Comentário para Tweet
**Prioridade:** Alta  
**Descrição:** Sistema deve gerar comentário sugerido para cada tweet usando a persona selecionada.

**Formato do Comentário:**
```
@username [Hook inicial]

[Conteúdo do comentário seguindo princípios da persona]

[Conclusão orgânica - opinião, concordância ou pergunta]
```

**Critérios de Aceitação:**
- [ ] Usar OpenAI com prompt da persona
- [ ] Incluir @username do autor do tweet
- [ ] Respeitar limite de 280 caracteres
- [ ] Seguir tom de voz da persona
- [ ] Aplicar regras de formatação da persona
- [ ] Salvar comentário no banco de dados
- [ ] Vincular comentário ao tweet

#### RF-012: Validar Comentário Gerado
**Prioridade:** Média  
**Descrição:** Sistema deve validar se comentário segue regras da persona.

**Validações:**
- [ ] Máximo 280 caracteres
- [ ] Sem emojis (se regra da persona)
- [ ] Sem links externos no corpo
- [ ] Contém @username
- [ ] Idioma correto

**Critérios de Aceitação:**
- [ ] Se validação falhar, regenerar comentário
- [ ] Máximo 3 tentativas de regeneração
- [ ] Se falhar 3x, marcar como "failed" e continuar

---

### 2.5 Email e Documento

#### RF-013: Email com Top 3 + Comentários
**Prioridade:** Alta  
**Descrição:** Email deve incluir top 3 tweets com comentários sugeridos no corpo.

**Estrutura do Email:**
```
🐦 Twitter Scraping - Resultados da Campanha

Total de tweets coletados: X
Score médio: Y/10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Top 3 Tweets com Comentários Sugeridos:
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📌 Tweet #1 - @username (Score: 9.2/10)
🔗 [Link para o tweet]

Tweet Original:
"[Texto do tweet...]"

💬 Comentário Sugerido:
@username [Comentário gerado pela persona]

Análise:
• Lead Relevance: 9/10
• Tone of Voice: 9/10
• Insight Strength: 10/10
• Engagement: 9/10
• Brand Safety: 10/10

Notas: [Notas da análise]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Repetir para Tweet #2 e #3]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📎 Anexo: Documento completo com todos os X tweets e comentários

Próximos passos:
• Revise os comentários sugeridos
• Copie e use no Twitter para engajamento
• Acesse a plataforma para ver todos os resultados
```

**Critérios de Aceitação:**
- [ ] Email com formato acima
- [ ] Top 3 tweets no corpo
- [ ] Comentários formatados corretamente
- [ ] Scores e análise visíveis
- [ ] Link para cada tweet
- [ ] Documento anexado

#### RF-014: Documento com Todos os Tweets + Comentários
**Prioridade:** Alta  
**Descrição:** Documento Word deve incluir todos os tweets com comentários.

**Estrutura do Documento:**
```
Twitter Scraping - Resultados da Campanha
Data: [Data]
Campanha: [Nome]
Persona: [Nome da Persona]
Total de tweets: X
Score médio: Y/10

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Tweet #1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

Autor: @username
Link: [URL]
Engajamento: X likes, Y retweets, Z replies
Score: 9.2/10 | Veredito: APPROVED

Tweet Original:
"[Texto completo do tweet]"

💬 Comentário Sugerido:
@username [Comentário gerado]

📊 Análise Detalhada:
• Lead Relevance: 9/10 - [Justificativa]
• Tone of Voice: 9/10 - [Justificativa]
• Insight Strength: 10/10 - [Justificativa]
• Engagement Potential: 9/10 - [Justificativa]
• Brand Safety: 10/10 - [Justificativa]

Notas da Rita: [Notas explicativas]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[Repetir para todos os tweets]
```

**Critérios de Aceitação:**
- [ ] Documento .docx gerado
- [ ] Todos os tweets incluídos
- [ ] Comentários para cada tweet
- [ ] Análise completa visível
- [ ] Formatação clara e profissional
- [ ] Upload para Supabase Storage

---

### 2.6 Exibição na Plataforma

#### RF-015: Exibir Comentários na Página de Detalhes
**Prioridade:** Alta  
**Descrição:** Página de detalhes da campanha deve mostrar comentários sugeridos.

**Critérios de Aceitação:**
- [ ] Card de tweet expandido com comentário
- [ ] Botão "Copiar Comentário" para clipboard
- [ ] Badge de score (cor: verde >= 8, amarelo 6-8, vermelho < 6)
- [ ] Expandir/colapsar análise detalhada
- [ ] Indicador visual para top 3 tweets
- [ ] Filtro para mostrar apenas top 3

#### RF-016: Copiar Comentário
**Prioridade:** Média  
**Descrição:** Usuário deve poder copiar comentário facilmente.

**Critérios de Aceitação:**
- [ ] Botão "Copiar" em cada comentário
- [ ] Copiar para clipboard
- [ ] Feedback visual (toast/mensagem)
- [ ] Formato copiado pronto para colar no Twitter

---

## 3. Requisitos Não-Funcionais

### 3.1 Performance
- **RNF-001:** Análise de tweets deve processar até 100 tweets em menos de 5 minutos
- **RNF-002:** Geração de comentário deve levar menos de 10 segundos por tweet
- **RNF-003:** Interface de personas deve carregar em menos de 2 segundos

### 3.2 Segurança
- **RNF-004:** Prompts de personas devem ser armazenados de forma segura
- **RNF-005:** API keys do OpenAI devem estar em variáveis de ambiente
- **RNF-006:** Validar entrada de usuário para prevenir injection

### 3.3 Usabilidade
- **RNF-007:** Interface intuitiva para criar personas
- **RNF-008:** Feedback claro durante processamento
- **RNF-009:** Mensagens de erro compreensíveis

### 3.4 Escalabilidade
- **RNF-010:** Sistema deve suportar até 50 personas por usuário
- **RNF-011:** Processamento assíncrono via Celery
- **RNF-012:** Cache de análises para evitar reprocessamento

### 3.5 Manutenibilidade
- **RNF-013:** Código modular e testável
- **RNF-014:** Documentação de APIs
- **RNF-015:** Logs detalhados de processamento

---

## 4. Regras de Negócio

### RN-001: Limite de Personas
- Usuário pode criar até 50 personas
- Após limite, deve excluir personas antigas

### RN-002: Persona em Uso
- Persona em uso por campanhas ativas não pode ser excluída
- Deve mostrar aviso com lista de campanhas

### RN-003: Custo de Processamento
- Análise + geração de comentário = ~2 chamadas OpenAI por tweet
- Estimar custo antes de processar campanhas grandes

### RN-004: Idioma dos Comentários
- Comentários devem ser no idioma especificado na persona
- Padrão: inglês (en)

### RN-005: Validação de Comentários
- Comentários devem passar por validação automática
- Se falhar 3x, marcar como "failed" e continuar

### RN-006: Reprocessamento
- Usuário pode solicitar reprocessamento de comentários
- Usar mesma persona ou selecionar outra

---

## 5. Casos de Uso

### UC-001: Criar Primeira Persona
**Ator:** Usuário  
**Fluxo Principal:**
1. Usuário acessa "Personas" no menu
2. Sistema exibe lista vazia
3. Usuário clica em "Criar Persona"
4. Sistema exibe formulário
5. Usuário preenche campos obrigatórios
6. Usuário clica em "Salvar"
7. Sistema valida e salva persona
8. Sistema exibe mensagem de sucesso
9. Sistema redireciona para lista de personas

**Fluxo Alternativo:**
- 6a. Campos obrigatórios vazios → Sistema exibe erro

### UC-002: Criar Campanha com Persona
**Ator:** Usuário  
**Fluxo Principal:**
1. Usuário acessa "Nova Campanha"
2. Sistema exibe formulário
3. Usuário preenche dados da campanha
4. Usuário seleciona persona no dropdown
5. Usuário clica em "Criar Campanha"
6. Sistema cria campanha com persona selecionada
7. Sistema inicia processamento assíncrono

**Fluxo Alternativo:**
- 4a. Usuário não seleciona persona → Sistema usa padrão

### UC-003: Visualizar Resultados com Comentários
**Ator:** Usuário  
**Fluxo Principal:**
1. Usuário acessa detalhes de campanha concluída
2. Sistema exibe lista de tweets
3. Usuário vê comentários sugeridos em cada tweet
4. Usuário clica em "Copiar Comentário"
5. Sistema copia para clipboard
6. Sistema exibe mensagem de sucesso
7. Usuário cola no Twitter

---

## 6. Dependências

### 6.1 Externas
- **OpenAI API:** Para análise e geração de comentários
- **Supabase:** Armazenamento de personas e análises
- **Celery:** Processamento assíncrono

### 6.2 Internas
- Sistema de campanhas existente
- Sistema de scraping de tweets
- Sistema de geração de documentos
- Sistema de envio de emails

---

## 7. Riscos e Mitigações

### Risco 1: Custo Alto de API OpenAI
**Impacto:** Alto  
**Probabilidade:** Média  
**Mitigação:**
- Implementar cache de análises
- Limitar número de tweets por campanha
- Mostrar estimativa de custo antes de processar

### Risco 2: Qualidade dos Comentários
**Impacto:** Alto  
**Probabilidade:** Média  
**Mitigação:**
- Validação automática rigorosa
- Permitir regeneração manual
- Feedback do usuário para melhorar prompts

### Risco 3: Performance com Muitos Tweets
**Impacto:** Médio  
**Probabilidade:** Alta  
**Mitigação:**
- Processamento assíncrono
- Barra de progresso
- Notificação quando concluir

---

## 8. Critérios de Aceitação Globais

- [ ] Usuário pode criar, editar, visualizar e excluir personas
- [ ] Usuário pode selecionar persona ao criar campanha
- [ ] Sistema analisa tweets e gera scores
- [ ] Sistema gera comentários usando persona selecionada
- [ ] Email inclui top 3 tweets com comentários
- [ ] Documento inclui todos os tweets com comentários
- [ ] Plataforma exibe comentários com opção de copiar
- [ ] Sistema processa 100 tweets em menos de 5 minutos
- [ ] Interface intuitiva e responsiva
- [ ] Testes automatizados cobrindo funcionalidades principais

---

## 9. Fora do Escopo (Não Será Implementado)

- ❌ Postagem automática de comentários no Twitter
- ❌ Agendamento de postagens
- ❌ Análise de sentimento de respostas
- ❌ Integração com outras redes sociais
- ❌ Sistema de aprovação multi-usuário
- ❌ Versionamento de personas
- ❌ A/B testing de comentários
- ❌ Analytics de engajamento pós-comentário

---

## 10. Próximos Passos

1. ✅ Revisar e aprovar requisitos
2. ⏳ Criar documento de design técnico
3. ⏳ Criar lista de tarefas de implementação
4. ⏳ Implementar CRUD de personas
5. ⏳ Implementar análise de tweets
6. ⏳ Implementar geração de comentários
7. ⏳ Atualizar email e documento
8. ⏳ Atualizar frontend
9. ⏳ Testes e refinamento
10. ⏳ Deploy e monitoramento

---

**Versão:** 1.0  
**Data:** 21/04/2026  
**Status:** 📝 Aguardando Aprovação
