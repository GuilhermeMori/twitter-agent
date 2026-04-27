# Twitter Scraping SaaS Platform

Plataforma para criação e execução de campanhas de scraping do Twitter/X, com geração automática de comentários via OpenAI e envio de relatórios por e-mail.

---

## Índice

- [Visão Geral](#visão-geral)
- [Pré-requisitos](#pré-requisitos)
- [Serviços Externos](#serviços-externos)
- [Instalação](#instalação)
- [Configuração](#configuração)
- [Rodando o Projeto](#rodando-o-projeto)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Variáveis de Ambiente](#variáveis-de-ambiente)
- [Scripts Utilitários](#scripts-utilitários)
- [Migrations](#migrations)

---

## Visão Geral

A plataforma é composta por três processos que precisam rodar simultaneamente:

| Processo | Tecnologia | Porta | Descrição |
|---|---|---|---|
| **Backend API** | FastAPI + Python | `8000` | REST API principal |
| **Worker** | Celery + Redis | — | Execução assíncrona de campanhas |
| **Frontend** | React + Vite | `5173` | Interface web |

---

## Pré-requisitos

Instale as seguintes ferramentas antes de começar:

### Python 3.11+
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

### Node.js 18+
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

### Redis
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

### Gmail (envio de relatórios por e-mail)
1. Ative a verificação em duas etapas na sua conta Google
2. Vá em **Conta Google → Segurança → Senhas de app**
3. Gere uma senha de app para "E-mail"
4. Configure na interface da plataforma após subir o projeto

---

## Instalação

### 1. Clone o repositório
```bash
git clone <url-do-repositorio>
cd <nome-do-projeto>
```

### 2. Configure as variáveis de ambiente
```bash
# Copie o arquivo de exemplo
cp .env.example .env

# Edite com suas credenciais
nano .env  # ou use seu editor preferido
```

### 3. Instale as dependências do backend
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

### 4. Instale as dependências do frontend
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
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Cole o resultado no `.env` como valor de `ENCRYPTION_KEY`.

### Arquivo `.env` mínimo para rodar
```env
DEBUG=True
SUPABASE_URL=https://seu-projeto.supabase.co
SUPABASE_KEY=sua-chave-anon
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
ENCRYPTION_KEY=sua-chave-gerada-acima
CORS_ORIGINS=["http://localhost:5173"]
```

---

## Rodando o Projeto

Você precisa de **3 terminais abertos** simultaneamente.

### Terminal 1 — Backend API
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

### Terminal 2 — Celery Worker
```bash
cd backend
source venv/bin/activate  # Linux/macOS
# ou: venv\Scripts\activate  # Windows

celery -A src.workers.celery_app worker --loglevel=info
```

### Terminal 3 — Frontend
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
│   │   ├── utils/             # Utilitários (criptografia, OpenAI)
│   │   ├── workers/           # Celery tasks
│   │   └── main.py            # Entry point FastAPI
│   ├── migrations/            # SQL migrations para o Supabase
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/                   # React + Vite + TypeScript
│   ├── src/
│   │   ├── components/        # Componentes reutilizáveis
│   │   ├── contexts/          # React contexts (notificações)
│   │   ├── pages/             # Páginas da aplicação
│   │   ├── services/          # Cliente HTTP (axios)
│   │   ├── types/             # Tipos TypeScript
│   │   └── App.tsx            # Rotas principais
│   ├── package.json
│   └── vite.config.ts
│
├── create_bucket.py            # Script para criar bucket no Supabase Storage
├── .env.example                # Variáveis de ambiente de exemplo
└── README.md
```

---

## Variáveis de Ambiente

| Variável | Obrigatória | Descrição |
|---|---|---|
| `DEBUG` | Não | `True` para desenvolvimento (default: `False`) |
| `SUPABASE_URL` | **Sim** | URL do projeto Supabase |
| `SUPABASE_KEY` | **Sim** | Chave anon do Supabase |
| `REDIS_URL` | **Sim** | URL do Redis (default: `redis://localhost:6379/0`) |
| `CELERY_BROKER_URL` | **Sim** | URL do broker Celery (mesmo que `REDIS_URL`) |
| `CELERY_RESULT_BACKEND` | **Sim** | URL do backend de resultados Celery |
| `ENCRYPTION_KEY` | **Sim** | Chave Fernet para criptografar tokens |
| `CORS_ORIGINS` | Não | Lista JSON de origens permitidas |
| `VITE_API_BASE_URL` | Não | URL do backend (deixe vazio em dev) |

> As credenciais de Apify, OpenAI e Gmail são configuradas pela interface da plataforma em **Configurações**, não via `.env`.

---

## Scripts Utilitários

### Criar bucket no Supabase Storage
Necessário na primeira vez para armazenar os documentos gerados pelas campanhas:

```bash
# Na raiz do projeto, com o .env configurado
pip install supabase python-dotenv  # se não tiver o venv do backend ativo
python create_bucket.py
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

1. **Configure as credenciais** — acesse `/configuration` e insira os tokens de Apify, OpenAI e Gmail
2. **Crie um estilo de comunicação** — acesse `/communication-styles` para definir o tom dos comentários gerados
3. **Crie uma campanha** — acesse `/campaigns/new`, escolha busca por perfis ou keywords
4. **Acompanhe a execução** — o Celery worker processa a campanha em background
5. **Veja os resultados** — acesse o detalhe da campanha para ver tweets coletados, análises e comentários gerados
