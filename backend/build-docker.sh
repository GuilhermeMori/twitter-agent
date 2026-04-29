#!/bin/bash

# Script para construir a imagem Docker do backend
# Uso: ./build-docker.sh [tag]

# Define o nome da imagem
IMAGE_NAME="twitter-scraping-backend"

# Usa a tag fornecida ou 'latest' como padrão
TAG="${1:-latest}"

# Nome completo da imagem
FULL_IMAGE_NAME="${IMAGE_NAME}:${TAG}"

echo "🐳 Construindo imagem Docker: ${FULL_IMAGE_NAME}"
echo "================================================"

# Constrói a imagem
docker build -t "${FULL_IMAGE_NAME}" .

# Verifica se o build foi bem-sucedido
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ Imagem construída com sucesso!"
    echo "================================================"
    echo "Nome da imagem: ${FULL_IMAGE_NAME}"
    echo ""
    echo "Para executar o container:"
    echo "  docker run -p 8000:8000 --env-file .env ${FULL_IMAGE_NAME}"
    echo ""
    echo "Para executar com docker-compose:"
    echo "  docker-compose up"
else
    echo ""
    echo "❌ Erro ao construir a imagem!"
    exit 1
fi
