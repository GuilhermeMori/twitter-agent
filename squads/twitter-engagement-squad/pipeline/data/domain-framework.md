# Domain Framework: Twitter Strategic Engagement (Gbm Tecnologia)

Este framework define o processo completo de monitoramento, curadoria e resposta automatizada com supervisão humana.

## 1. Monitoramento (Agente de Pesquisa)
- **Frequência:** 1 hora (agendado) ou sob demanda.
- **Fontes:** Perfis específicos e palavras-chave de IA/Automação.
- **Filtros:** Mínimo de likes e reposts (configurável).
- **Meta:** Coletar os top 20 posts mais engajados no intervalo.

## 2. Redação (Agente de Criação)
- **Input:** Post original + contexto da Gbm Tecnologia.
- **Prompt:** Gerar comentário descontraído, curto e gerador de engajamento (pergunta ao final).
- **Regra:** Nunca postar diretamente.

## 3. Revisão (Agente de Revisão)
- **Checklist:** Relevância do post + Qualidade do comentário + Segurança de marca.
- **Veredito:** APROVADO | REPROVADO (com motivo).

## 4. Aprovação Humana (Gmail)
- **Email:** Enviar corpo do post + comentário sugerido + link original.
- **Gatilho:** Receber confirmação Sim/Não do usuário.
- **Retry:** Se "Não", o comentário volta para a etapa 2 com o feedback do usuário.
