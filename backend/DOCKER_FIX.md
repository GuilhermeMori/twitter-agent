# Correção do Problema de Build Docker

## Problema Identificado

Ao tentar construir a imagem Docker do último commit, dois problemas foram encontrados:

### 1. ❌ HEALTHCHECK com dependência faltante

**Erro**: O Dockerfile usava `import requests` no HEALTHCHECK, mas a biblioteca `requests` não estava no `requirements.txt`.

```dockerfile
# ❌ ANTES (ERRADO)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8000/health', timeout=5)" || exit 1
```

**Solução**: Substituído por `urllib.request`, que faz parte da biblioteca padrão do Python:

```dockerfile
# ✅ DEPOIS (CORRETO)
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health', timeout=5)" || exit 1
```

### 2. ⚠️ Imagem sem nome/tag

**Problema**: Ao executar `docker build backend/` sem especificar `-t nome:tag`, a imagem é criada mas aparece como `<none>` no `docker images`.

**Solução**: Sempre usar a flag `-t` para nomear a imagem:

```bash
# ✅ Correto
docker build -t twitter-scraping-backend:latest backend/

# ❌ Evitar (cria imagem sem nome)
docker build backend/
```

## Arquivos Modificados

1. **backend/Dockerfile**
   - Corrigido o HEALTHCHECK para usar `urllib.request`

2. **backend/build-docker.sh** (NOVO)
   - Script helper para facilitar o build com nome correto
   - Uso: `./build-docker.sh [tag]`

3. **backend/README.md**
   - Adicionadas instruções de build Docker
   - Documentado o problema e solução

## Como Usar Agora

### Opção 1: Script Helper (Recomendado)

```bash
cd backend
./build-docker.sh          # Cria twitter-scraping-backend:latest
./build-docker.sh v1.0     # Cria twitter-scraping-backend:v1.0
```

### Opção 2: Docker Build Manual

```bash
cd backend
docker build -t twitter-scraping-backend:latest .
```

### Opção 3: Docker Compose

```bash
docker-compose build
docker-compose up
```

## Verificação

Para verificar se a imagem foi criada corretamente:

```bash
# Listar imagens
docker images | grep twitter-scraping

# Deve aparecer algo como:
# twitter-scraping-backend   latest   abc123def456   2 minutes ago   328MB
```

## Testando a Imagem

```bash
# Executar o container
docker run -p 8000:8000 --env-file .env twitter-scraping-backend:latest

# Testar o healthcheck
curl http://localhost:8000/health

# Deve retornar:
# {"status":"healthy","version":"1.0.0","environment":"production"}
```

## Dependências do Projeto

O `requirements.txt` atual contém:

- fastapi==0.104.1
- uvicorn[standard]==0.24.0
- pydantic==2.5.0
- supabase==2.9.1
- celery==5.3.4
- redis==5.0.1
- apify-client>=1.6.3
- openai>=1.3.7
- python-docx==1.1.0
- email-validator==2.1.0
- cryptography==41.0.7
- httpx==0.27.0

**Nota**: `requests` NÃO está na lista, por isso o healthcheck original falhava.

## Resumo

✅ **Problema resolvido**: HEALTHCHECK agora usa biblioteca padrão do Python  
✅ **Script criado**: `build-docker.sh` para facilitar builds  
✅ **Documentação atualizada**: README.md com instruções claras  
✅ **Build testado**: Imagem constrói com sucesso (ID: c3caaa3fcc0c)

## Próximos Passos

1. Commitar as mudanças:
   ```bash
   git add backend/Dockerfile backend/build-docker.sh backend/README.md backend/DOCKER_FIX.md
   git commit -m "fix: corrige HEALTHCHECK do Dockerfile e adiciona script de build"
   git push
   ```

2. Reconstruir a imagem com o nome correto:
   ```bash
   cd backend
   ./build-docker.sh
   ```

3. Testar o container:
   ```bash
   docker-compose up
   ```
