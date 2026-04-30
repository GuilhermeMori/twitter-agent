# Twitter Scraping SaaS Platform

Plataforma para criação e execução de campanhas de scraping do Twitter/X, com análise automática de tweets (Rita), geração de comentários via OpenAI (Cadu) e envio de relatórios por e-mail.

---

## Índice

- [Visão Geral](#visão-geral)
- [Arquitetura](#arquitetura)
- [Pré-requisitos](#pré-requisitos)
- [Serviços Externos](#serviços-externos)
- [Instalação](#instalação)
  - [Opção 1: Docker (Recomendado)](#opção-1-docker-recomendado)
  - [Opção 2: Desenvolvimento Local](#opção-2-desenvolvimento-local)
- [Configuração](#configuração)
- [Migrations](#migrations)
- [Rodando o Projeto](#rodando-o-projeto)
  - [Com Docker](#com-docker)
  - [Sem Docker (Desenvolvimento)](#sem-docker-desenvolvimento)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Scripts Utilitários](#scripts-utilitários)
- [Fluxo de Uso](#fluxo-de-uso)
- [Troubleshooting](#troubleshooting)

---

## Visão Geral

A plataforma automatiza o processo de encontrar e engajar com tweets relevantes no Twitter/X:

1. **Beto Busca** 🔍 — Scraping de tweets via Apify (busca por perfis ou keywords)
2. **Rita Revisão** 📊 — Análise automática de tweets com 5 critérios de pontuação via OpenAI
3. **Cadu Comentário** 💬 — Geração de comentários personalizados seguindo um estilo de comunicação
4. **Relatório** 📧 — Documento .docx + e-mail com os top 3 tweets e comentários

### Fluxo Completo

```
Campanha Criada
    ↓
Beto: Scraping (Apify) → 39 tweets encontrados
    ↓
Rita: Análise (OpenAI) → 15 aprovados, 24 rejeitados
    ↓
Cadu: Comentários (OpenAI) → Apenas para os 15 aprovados
    ↓
Documento .docx → Download disponível na plataforma
```

---

## Arquitetura

A plataforma é composta por **4 serviços** que rodam simultaneamente:

| Serviço | Tecnologia | Porta | Descrição |
|---|---|---|---|
| **Redis** | Redis 7 | `6379` | Message broker para Celery |
| **Backend API** | FastAPI + Python 3.11 | `8000` | REST API principal |
| **Worker** | Celery + Redis | — | Execução assíncrona de campanhas |
| **Frontend** | React + Vite + Nginx | `80` | Interface web |

### Banco de Dados

- **Supabase** (PostgreSQL) — Armazena campanhas, tweets, análises, comentários
- **Supabase Storage** — Armazena documentos .docx gerados

---

## Pré-requisitos

### Opção 1: Docker (Recomendado para Produção)

Instale apenas:

- **Docker** 20.10+ ([Instalar Docker](https://docs.docker.com/get-docker/))
- **Docker Compose** 2.0+ (já incluído no Docker Desktop)

```bash
# Verifique as versões
docker --version
docker-compose --version
```

### Opção 2: Desenvolvimento Local

Instale as seguintes ferramentas:

#### Python 3.11+
```bash
# Verifique a versão
python --version  # deve ser 3.11 ou superior

# Ubuntu/Debian
sudo apt install python3.11 python3.11-venv python3-pip

# macOS (Homebrew)
brew install python@3.11

# Windows
# Baixe em https://www.python.org/downloads/
```

#### Node.js 18+
```bash
# Verifique a versão
node --version  # deve ser 18 ou superior

# Ubuntu/Debian (via NodeSource)
curl -fsSL https://deb.nodesource.com/setup_18.x | sudo -E bash -
sudo apt install -y nodejs

# macOS (Homebrew)
brew install node@18

# Windows
# Baixe em https://nodejs.org/
```

#### Redis
O Redis é o broker de mensagens do Celery. Precisa estar rodando localmente.

```bash
# Ubuntu/Debian
sudo apt install redis-server
sudo systemctl start redis-server
sudo systemctl enable redis-server  # iniciar automaticamente no boot

# macOS (Homebrew)
brew install redis
brew services start redis

# Windows
# Use o WSL2 com Ubuntu, ou baixe em https://github.com/microsoftarchive/redis/releases
# Ou via Chocolatey: choco install redis-64

# Verifique se está rodando
redis-cli ping  # deve retornar PONG
```

---

## Serviços Externos

Você precisará de contas nos seguintes serviços:

### Supabase (banco de dados + storage)
1. Crie uma conta em [supabase.com](https://supabase.com)
2. Crie um novo projeto
3. Vá em **Settings → API** e copie:
   - `Project URL` → `SUPABASE_URL`
   - `anon public` key → `SUPABASE_KEY`
4. Execute as migrations (veja a seção [Migrations](#migrations))
5. Crie o bucket de storage (veja [Scripts Utilitários](#scripts-utilitários))

### Apify (scraping do Twitter)
1. Crie uma conta em [apify.com](https://apify.com)
2. Vá em **Settings → Integrations** e copie o API token
3. Configure na interface da plataforma após subir o projeto

### OpenAI (geração de comentários)
1. Crie uma conta em [platform.openai.com](https://platform.openai.com)
2. Vá em **API Keys** e crie uma nova chave
3. Configure na interface da plataforma após subir o projeto

---

## Instalação

### Opção 1: Docker (Recomendado)

#### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd <nome-do-projeto>
```

#### 2. Configure as variáveis de ambiente
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite com suas credenciais
nano .env  # ou use seu editor preferido
```

#### 3. Gere a chave de criptografia
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Cole o resultado no `.env` como valor de `ENCRYPTION_KEY`.

#### 4. Configure o .env mínimo
```env
DEBUG=True
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon
ENCRYPTION_KEY=sua-chave-gerada-acima
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0
CORS_ORIGINS=["http://localhost"]
```

#### 5. Execute as migrations no Supabase
Veja a seção [Migrations](#migrations) abaixo.

#### 6. Suba os containers
```bash
docker-compose up -d
```

Pronto! A aplicação estará rodando em:
- Frontend: `http://localhost`
- Backend API: `http://localhost:8000`
- API Docs: `http://localhost:8000/api/docs`

### Opção 2: Desenvolvimento Local

#### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd <nome-do-projeto>
```

#### 2. Configure as variáveis de ambiente
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite com suas credenciais
nano .env  # ou use seu editor preferido
```

#### 3. Instale as dependências do backend
```bash
cd backend

# Crie e ative um ambiente virtual (recomendado)
python -m venv venv

# Linux/macOS
source venv/bin/activate

# Windows
venv\Scripts\activate

# Instale as dependências
pip install -r requirements.txt

# Volte para a raiz
cd ..
```

#### 4. Instale as dependências do frontend
```bash
cd frontend
npm install
cd ..
```

---

## Configuração

### Gerar a chave de criptografia
A `ENCRYPTION_KEY` é usada para criptografar tokens de API no banco de dados. Gere uma:

```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Cole o resultado no `.env` como valor de `ENCRYPTION_KEY`.

### Arquivo `.env` completo

```env
# ─── Aplicação ───────────────────────────────
DEBUG=True

# ─── Supabase (obrigatório) ──────────────────
# Obtenha em: https://app.supabase.com/project/_/settings/api
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon

# ─── Redis (obrigatório para Celery) ─────────
# Docker: redis://redis:6379/0
# Local: redis://localhost:6379/0
REDIS_URL=redis://redis:6379/0
CELERY_BROKER_URL=redis://redis:6379/0
CELERY_RESULT_BACKEND=redis://redis:6379/0

# ─── Criptografia (obrigatório) ──────────────
# Gere com o comando acima
ENCRYPTION_KEY=sua-chave-gerada-acima

# ─── CORS ────────────────────────────────────
# Docker: ["http://localhost"]
# Local: ["http://localhost:5173","http://localhost:3000"]
CORS_ORIGINS=["http://localhost"]

# ─── Frontend (Vite) ─────────────────────────
# Deixe vazio (não é necessário)
VITE_API_BASE_URL=
```

---

## Migrations

As migrations criam as tabelas no Supabase. Execute-as **antes** de rodar a aplicação:

### 1. Acesse o SQL Editor do Supabase
Vá em [app.supabase.com](https://app.supabase.com) → Seu Projeto → **SQL Editor**

### 2. Execute a migration principal
Copie e execute o conteúdo de:

```
backend/migrations/000_full_migration_assistants_communication_styles.sql
```

Este arquivo cria:
- Tabela `campaigns` — Campanhas de scraping
- Tabela `assistants` — Beto, Rita e Cadu (3 assistentes)
- Tabela `communication_styles` — Estilos de comunicação (ex: Growth Collective)
- Tabela `tweet_analysis` — Análises da Rita
- Tabela `tweet_comments` — Comentários do Cadu

### 3. Crie o bucket de storage
Execute o script para criar o bucket onde os documentos .docx serão armazenados:

```bash
# Na raiz do projeto
python3 create_bucket.py
```

> **Nota:** Os 3 assistentes (Beto, Rita, Cadu) e 1 estilo de comunicação padrão (Growth Collective) são criados automaticamente pela migration.

---

## Rodando o Projeto

### Com Docker

#### Iniciar todos os serviços
```bash
docker-compose up -d
```

#### Ver logs em tempo real
```bash
# Todos os serviços
docker-compose logs -f

# Apenas o worker (para ver execução de campanhas)
docker-compose logs -f worker

# Apenas o backend
docker-compose logs -f backend
```

#### Parar todos os serviços
```bash
docker-compose down
```

#### Reconstruir após mudanças no código
```bash
# Reconstruir tudo
docker-compose build --no-cache

# Reconstruir apenas um serviço
docker-compose build --no-cache worker

# Reiniciar após rebuild
docker-compose up -d
```

#### Acessar a aplicação
- **Frontend:** `http://localhost`
- **Backend API:** `http://localhost:8000`
- **API Docs (Swagger):** `http://localhost:8000/api/docs`
- **ReDoc:** `http://localhost:8000/api/redoc`

### Sem Docker (Desenvolvimento)

Você precisa de **3 terminais abertos** simultaneamente.

#### Terminal 1 — Backend API
```bash
cd backend
source venv/bin/activate  # Linux/macOS
# ou: venv\Scripts\activate  # Windows

uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

A API estará disponível em:
- `http://localhost:8000` — API
- `http://localhost:8000/api/docs` — Swagger UI
- `http://localhost:8000/api/redoc` — ReDoc

#### Terminal 2 — Celery Worker
```bash
cd backend
source venv/bin/activate  # Linux/macOS
# ou: venv\Scripts\activate  # Windows

celery -A src.workers.celery_app worker --loglevel=info
```

#### Terminal 3 — Frontend
```bash
cd frontend
npm run dev
```

O frontend estará disponível em `http://localhost:5173`.

> **Dica:** O Vite já está configurado para fazer proxy das chamadas `/api` para `http://localhost:8000`, então não é necessário configurar `VITE_API_BASE_URL` em desenvolvimento.

---

## Estrutura do Projeto

```
.
├── backend/                    # API FastAPI + Celery Worker
│   ├── src/
│   │   ├── api/
│   │   │   ├── middleware/     # Logging e tratamento de erros
│   │   │   └── routes/        # Endpoints REST
│   │   ├── core/              # Config, database, logging
│   │   ├── models/            # Modelos Pydantic
│   │   ├── repositories/      # Acesso ao Supabase
│   │   ├── services/          # Lógica de negócio
│   │   │   ├── analysis_engine.py          # Rita (análise)
│   │   │   ├── comment_generation_service.py # Cadu (comentários)
│   │   │   ├── comment_validator.py        # Validação de comentários
│   │   │   ├── scraping_engine.py          # Beto (scraping)
│   │   │   └── ...
│   │   ├── utils/             # Utilitários (criptografia, OpenAI)
│   │   ├── workers/           # Celery tasks
│   │   │   └── campaign_executor.py  # Orquestrador principal
│   │   └── main.py            # Entry point FastAPI
│   ├── migrations/            # SQL migrations para o Supabase
│   │   └── 000_full_migration_assistants_communication_styles.sql
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/        # Componentes reutilizáveis
│   │   ├── contexts/          # React contexts (notificações)
│   │   ├── pages/             # Páginas da aplicação
│   │   │   ├── CampaignCreationPage.tsx
│   │   │   ├── CampaignDetailPage.tsx
│   │   │   └── ...
│   │   ├── services/          # Cliente HTTP (axios)
│   │   ├── types/             # Tipos TypeScript
│   │   └── App.tsx            # Rotas principais
│   ├── Dockerfile
│   ├── nginx.conf             # Configuração Nginx (proxy /api)
│   ├── package.json
│   └── vite.config.ts
│
├── docker-compose.yml          # Orquestração de todos os serviços
├── create_bucket.py            # Script para criar bucket no Supabase Storage
├── .env.example                # Variáveis de ambiente de exemplo
├── .gitignore                  # Arquivos ignorados pelo Git
└── README.md                   # Este arquivo
```

---

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição | Valor Docker | Valor Local |
|---|---|---|---|---|
| `DEBUG` | Não | Modo debug (default: `False`) | `True` | `True` |
| `SUPABASE_URL` | **Sim** | URL do projeto Supabase | `https://xxx.supabase.co` | `https://xxx.supabase.co` |
| `SUPABASE_KEY` | **Sim** | Chave anon do Supabase | `eyJxxx...` | `eyJxxx...` |
| `REDIS_URL` | **Sim** | URL do Redis | `redis://redis:6379/0` | `redis://localhost:6379/0` |
| `CELERY_BROKER_URL` | **Sim** | URL do broker Celery | `redis://redis:6379/0` | `redis://localhost:6379/0` |
| `CELERY_RESULT_BACKEND` | **Sim** | URL do backend de resultados | `redis://redis:6379/0` | `redis://localhost:6379/0` |
| `ENCRYPTION_KEY` | **Sim** | Chave Fernet para criptografar tokens | Gerar com comando | Gerar com comando |
| `CORS_ORIGINS` | Não | Lista JSON de origens permitidas | `["http://localhost"]` | `["http://localhost:5173"]` |
| `VITE_API_BASE_URL` | Não | URL do backend (deixe vazio) | `` | `` |

> **Nota:** As credenciais de Apify e OpenAI são configuradas pela interface da plataforma em **Configurações**, não via `.env`.

---

## Scripts Utilitários

### Criar bucket no Supabase Storage
Necessário na primeira vez para armazenar os documentos gerados pelas campanhas:

```bash
# Na raiz do projeto, com o .env configurado
pip install supabase python-dotenv  # se não tiver o venv do backend ativo
python3 create_bucket.py
```

### Verificar status dos containers (Docker)
```bash
docker-compose ps
```

### Ver logs de um serviço específico
```bash
docker-compose logs -f worker
```

### Acessar o shell de um container
```bash
# Backend
docker exec -it twitter-scraping-backend bash

# Worker
docker exec -it twitter-scraping-worker bash
```

### Limpar tudo e recomeçar (Docker)
```bash
# Parar e remover containers, volumes e redes
docker-compose down -v

# Reconstruir tudo do zero
docker-compose build --no-cache

# Subir novamente
docker-compose up -d
```

---

## Migrations

As migrations ficam em `backend/migrations/`. Execute-as no Supabase em ordem:

1. Acesse o **SQL Editor** do seu projeto em [app.supabase.com](https://app.supabase.com)
2. Execute o arquivo principal que cria todas as tabelas:

```
backend/migrations/000_full_migration_assistants_communication_styles.sql
```

Este arquivo cria todas as tabelas necessárias de uma vez. Os demais arquivos em `migrations/` são incrementais e já estão incluídos nele.

---

## Fluxo de Uso

1. **Configure as credenciais** — Acesse `/configuration` e insira os tokens de:
   - **Apify** (scraping)
   - **OpenAI** (análise + comentários)

2. **Verifique os assistentes** — Acesse `/assistants` para ver:
   - **Beto Busca** 🔍 — Scraping de tweets
   - **Rita Revisão** 📊 — Análise de tweets (5 critérios)
   - **Cadu Comentário** 💬 — Geração de comentários

3. **Crie um estilo de comunicação** — Acesse `/communication-styles`:
   - Define o tom, princípios e vocabulário dos comentários
   - Exemplo: "Growth Collective" (já vem criado por padrão)

4. **Crie uma campanha** — Acesse `/campaigns/new`:
   - Escolha busca por **perfis** ou **keywords**
   - Selecione o **estilo de comunicação** (obrigatório para Rita + Cadu)
   - Configure filtros (likes, retweets, replies, dias)

5. **Acompanhe a execução** — O Celery worker processa em background:
   - **Beto:** Scraping via Apify (pode demorar 1-2 min)
   - **Rita:** Análise de cada tweet (5-10 seg por tweet)
   - **Cadu:** Comentários apenas para tweets APROVADOS (3-5 seg por tweet)
   - **Documento:** Geração do .docx e upload para Supabase Storage

6. **Veja os resultados** — Acesse o detalhe da campanha:
   - Lista de tweets encontrados
   - Análises da Rita (score, veredito, justificativa)
   - Comentários do Cadu (apenas para aprovados)
   - **Download do documento .docx** (botão na interface)

### Regras Importantes

- **Sem estilo de comunicação:** Apenas Beto executa (somente scraping)
- **Com estilo de comunicação:** Beto → Rita → Cadu (fluxo completo)
- **Limite de comentários:** Máximo 350 caracteres (antes era 280)
- **Comentários apenas para aprovados:** Cadu não gera para tweets rejeitados

---

## Troubleshooting

### Docker: Porta 6379 já está em uso
```bash
# Parar Redis local
sudo systemctl stop redis-server  # Linux
brew services stop redis          # macOS

# Ou mudar a porta no docker-compose.yml
```

### Docker: Erro ao construir imagem
```bash
# Limpar cache do Docker
docker system prune -a

# Reconstruir sem cache
docker-compose build --no-cache
```

### Worker não está processando campanhas
```bash
# Verificar logs do worker
docker-compose logs -f worker

# Verificar se Redis está rodando
docker-compose ps redis

# Reiniciar worker
docker-compose restart worker
```

### Frontend não consegue acessar o backend
```bash
# Verificar se o backend está rodando
curl http://localhost:8000/api/health

# Verificar logs do backend
docker-compose logs -f backend

# Verificar configuração do nginx.conf
cat frontend/nginx.conf
```

### Campanha fica travada em "running"
```bash
# Ver logs do worker para identificar o erro
docker-compose logs -f worker

# Causas comuns:
# - Token Apify inválido ou sem créditos
# - Token OpenAI inválido ou sem créditos
# - Erro de rede (proxy Apify retornando 502/590)
```

### Comentários muito longos (>350 chars)
O Cadu tenta até 3 vezes gerar um comentário válido. Se falhar, o comentário é marcado como `invalid` no banco de dados.

```bash
# Ver quantos comentários falharam
# No Supabase SQL Editor:
SELECT validation_status, COUNT(*) 
FROM tweet_comments 
WHERE campaign_id = 'seu-campaign-id'
GROUP BY validation_status;
```

### Apify retorna 0 tweets
Causas comuns:
- **Proxy error 590/502:** Erro temporário da Apify, tente novamente
- **Keywords muito específicas:** Tente keywords mais genéricas
- **Perfil privado ou inexistente:** Verifique se o perfil existe e é público
- **Sem créditos Apify:** Verifique seu saldo em apify.com

---

## Arquivos Importantes

### Versionados no Git ✅
- `backend/src/**` — Todo o código backend
- `frontend/src/**` — Todo o código frontend
- `backend/migrations/**` — Migrations SQL
- `backend/Dockerfile` — Imagem Docker do backend/worker
- `frontend/Dockerfile` — Imagem Docker do frontend
- `frontend/nginx.conf` — Configuração Nginx (proxy /api)
- `docker-compose.yml` — Orquestração de serviços
- `.env.example` — Exemplo de variáveis de ambiente
- `backend/.env.example` — Exemplo de variáveis do backend
- `create_bucket.py` — Script para criar bucket no Supabase
- `README.md` — Documentação completa

### NÃO versionados (.gitignore) ❌
- `.env` — Credenciais reais (NUNCA commitar)
- `backend/.env` — Credenciais do backend
- `node_modules/` — Dependências Node.js
- `backend/venv/` — Ambiente virtual Python
- `backend/__pycache__/` — Cache Python
- `frontend/dist/` — Build do frontend
- `*.log` — Logs de execução
- `documents/` — Documentos .docx gerados

---

## Suporte

Para dúvidas ou problemas:

1. Verifique a seção [Troubleshooting](#troubleshooting)
2. Veja os logs: `docker-compose logs -f`
3. Verifique o Swagger: `http://localhost:8000/api/docs`
4. Abra uma issue no repositório

---

## Licença

[Adicione sua licença aqui]
