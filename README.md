# 🐦 Twitter Engagement Squad

> Sistema automatizado de monitoramento e engajamento estratégico no Twitter/X usando agentes de IA

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Node.js](https://img.shields.io/badge/Node.js-18+-green.svg)](https://nodejs.org/)
[![OpenSquad](https://img.shields.io/badge/OpenSquad-Compatible-blue.svg)](https://github.com/opensquad)

## 📋 Sobre o Projeto

O Twitter Engagement Squad é um sistema completo de automação para monitoramento e engajamento no Twitter/X. Ele utiliza três agentes de IA especializados que trabalham em conjunto para:

1. **🔍 Beto Busca** - Monitora o Twitter/X em busca de posts relevantes
2. **✍️ Cadu Comentário** - Cria comentários autênticos e engajadores em inglês
3. **🛡️ Rita Revisão** - Revisa e aprova comentários garantindo qualidade e brand safety

## ✨ Funcionalidades

- ✅ **Busca Inteligente** - Monitora posts por palavras-chave e filtros de engajamento
- ✅ **Comentários em Inglês** - Geração automática de respostas autênticas
- ✅ **Revisão de Qualidade** - Sistema de scoring e aprovação automática
- ✅ **Histórico Completo** - Versionamento de todas as execuções
- ✅ **E-mail com Anexos** - Notificações com 3 melhores posts + arquivo Word
- ✅ **Dashboard Visual** - Interface 2D para monitorar agentes em tempo real
- ✅ **Brand Safety** - Garantia de alinhamento com a marca

## 🚀 Início Rápido

### Pré-requisitos

- Node.js 18+ instalado
- Conta no [Apify](https://apify.com) (para scraping do Twitter)
- Conta Gmail com senha de app configurada
- Cookies de autenticação do Twitter/X

### Instalação

1. **Clone o repositório**
```bash
git clone https://github.com/seu-usuario/twitter-engagement-squad.git
cd twitter-engagement-squad
```

2. **Instale as dependências**
```bash
npm install
cd dashboard && npm install && cd ..
```

3. **Configure as variáveis de ambiente**
```bash
cp .env.example .env
# Edite o arquivo .env com suas credenciais
```

4. **Configure sua empresa**
```bash
cp _opensquad/_memory/company.example.md _opensquad/_memory/company.md
cp _opensquad/_memory/preferences.example.md _opensquad/_memory/preferences.md
# Edite os arquivos com suas informações
```

### Configuração das Credenciais

#### Gmail (para envio de e-mails)
1. Acesse [Google Account Security](https://myaccount.google.com/security)
2. Ative "Verificação em duas etapas"
3. Vá em "Senhas de app"
4. Gere uma senha para "Mail"
5. Use a senha gerada no `.env`

#### Apify (para scraping)
1. Crie uma conta em [Apify](https://apify.com)
2. Vá em Settings > Integrations > API tokens
3. Crie um novo token
4. Cole no `.env`

#### Twitter/X (cookies)
1. Faça login no Twitter/X no navegador
2. Abra DevTools (F12) > Application > Cookies > https://x.com
3. Copie os valores:
   - `auth_token` → `TWITTER_AUTH_TOKEN`
   - `ct0` → `TWITTER_CT0`

## 📖 Como Usar

### 1. Configurar Busca

Edite `squads/twitter-engagement-squad/output/research-focus.md`:

```markdown
## Palavras-chave
- Creative strategy
- dtc brands

## Filtros de Engajamento
- Mínimo de Likes: 10
- Mínimo de Reposts: 5
```

### 2. Executar o Squad

```bash
# Via OpenSquad (recomendado)
/opensquad run twitter-engagement-squad

# Ou via scripts diretos
node squads/twitter-engagement-squad/scripts/search-twitter.js
```

### 3. Visualizar Resultados

- **E-mail**: Receba os 3 melhores comentários + arquivo Word com todos
- **Dashboard**: `cd dashboard && npm run dev` → http://localhost:5173
- **Histórico**: `node squads/twitter-engagement-squad/scripts/list-history.js`

## 📁 Estrutura do Projeto

```
twitter-engagement-squad/
├── squads/
│   └── twitter-engagement-squad/
│       ├── agents/                    # Definição dos agentes
│       │   ├── beto-busca.agent.md
│       │   ├── cadu-comentario.agent.md
│       │   └── rita-revisao.agent.md
│       ├── pipeline/                  # Pipeline de execução
│       │   ├── steps/                 # Steps do pipeline
│       │   └── data/                  # Dados de referência
│       ├── scripts/                   # Scripts de automação
│       │   ├── search-twitter.js      # Busca de tweets
│       │   ├── send-comments.js       # Envio de e-mail
│       │   └── list-history.js        # Listagem de histórico
│       └── output/
│           ├── history/               # Histórico de execuções
│           │   └── YYYY-MM-DDTHH-MM-SS/
│           │       ├── raw-posts.md
│           │       ├── draft-comments.md
│           │       ├── reviewed-comments.md
│           │       └── comentarios-aprovados.doc
│           └── research-focus.md      # Configuração de busca
├── dashboard/                         # Dashboard visual
│   ├── src/
│   └── public/
├── _opensquad/                        # Sistema OpenSquad
│   ├── core/                          # Núcleo do sistema
│   └── _memory/                       # Memória e preferências
└── .env                               # Variáveis de ambiente (não commitado)
```

## 🎯 Fluxo de Trabalho

```
1. Usuário configura palavras-chave
   ↓
2. Beto Busca encontra tweets relevantes (via Apify)
   ↓
3. Cadu Comentário cria respostas em inglês
   ↓
4. Rita Revisão avalia e aprova (scoring 8+/10)
   ↓
5. E-mail enviado com:
   - 3 melhores comentários no corpo
   - Arquivo Word com todos os comentários
   ↓
6. Histórico salvo em pasta timestampada
```

## 📊 Sistema de Histórico

Cada execução é salva em uma pasta única:

```bash
# Listar todas as execuções
node squads/twitter-engagement-squad/scripts/list-history.js

# Saída:
# 1. 2026-04-01T17-28-42-257Z
#    🔍 Palavras-chave: Creative strategy, dtc brands
#    📊 Posts encontrados: 40
#    ✅ Comentários aprovados: 5
#    ⭐ Score médio: 8.7/10
```

## 🎨 Dashboard Visual

O dashboard oferece uma interface 2D com:
- Visualização dos agentes trabalhando em tempo real
- Painel de configuração do Twitter Engagement Squad
- Histórico de execuções
- Métricas de performance

```bash
cd dashboard
npm run dev
# Acesse http://localhost:5173
```

## 🔒 Segurança

- ✅ Todas as credenciais em `.env` (não commitado)
- ✅ Histórico de execuções ignorado pelo Git
- ✅ Dados da empresa em arquivos `.example`
- ✅ `.gitignore` robusto para proteção de dados sensíveis

## 📝 Documentação Adicional

- [HISTORICO.md](squads/twitter-engagement-squad/HISTORICO.md) - Sistema de histórico
- [ESTRUTURA-OTIMIZADA.md](squads/twitter-engagement-squad/ESTRUTURA-OTIMIZADA.md) - Arquitetura sem duplicação
- [CONFIGURACAO-EMAIL.md](squads/twitter-engagement-squad/CONFIGURACAO-EMAIL.md) - Configuração de e-mail

## 🤖 Sobre o OpenSquad

Este projeto é construído sobre o framework OpenSquad, que permite criar squads de agentes de IA que trabalham juntos direto do seu IDE.

### Comandos OpenSquad

```bash
# Abrir menu principal
/opensquad

# Criar um novo squad
/opensquad crie um squad para [o que você precisa]

# Executar um squad
/opensquad execute o squad <nome-do-squad>

# Gerar dashboard
/opensquad dashboard
```

Para mais informações sobre o OpenSquad, visite a [documentação oficial](https://github.com/opensquad).

## 🤝 Contribuindo

Contribuições são bem-vindas! Por favor:

1. Fork o projeto
2. Crie uma branch para sua feature (`git checkout -b feature/AmazingFeature`)
3. Commit suas mudanças (`git commit -m 'Add some AmazingFeature'`)
4. Push para a branch (`git push origin feature/AmazingFeature`)
5. Abra um Pull Request

## 📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo [LICENSE](LICENSE) para mais detalhes.

## 👤 Autor

**Guilherme Morii**
- GitHub: [@guilhermebmorii](https://github.com/guilhermebmorii)
- Email: guilhermebmorii@gmail.com

## 🙏 Agradecimentos

- [OpenSquad](https://github.com/opensquad) - Framework de agentes de IA
- [Apify](https://apify.com) - Plataforma de scraping
- Comunidade open source

---

⭐ Se este projeto foi útil para você, considere dar uma estrela!
