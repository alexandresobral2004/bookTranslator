#!/bin/bash
# ==============================================================================
# Script de Configuração para Execução Local Sem Docker (macOS)
# ==============================================================================

set -e

# Cores para output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Iniciando configuração do ambiente local para BookTranslator ===${NC}\n"

# 1. Verificar dependências de sistema (macOS com Homebrew)
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo -e "${BLUE}[1/5] Verificando dependências do sistema via Homebrew...${NC}"
    if ! command -v brew &> /dev/null; then
        echo -e "${YELLOW}Aviso: Homebrew não encontrado. Certifique-se de instalar as dependências manualmente se WeasyPrint falhar.${NC}"
    else
        echo -e "${GREEN}Homebrew detectado. Instalando pango, cairo, libffi (necessários para WeasyPrint)...${NC}"
        brew install pango cairo libffi || echo -e "${YELLOW}Aviso: Falha ou pango/cairo já instalados. Continuando...${NC}"
    fi
else
    echo -e "${YELLOW}Ambiente não-macOS detectado. Certifique-se de instalar as dependências equivalentes a pango e cairo.${NC}"
fi

# 2. Criar ambiente virtual
echo -e "\n${BLUE}[2/5] Criando ambiente virtual Python (.venv)...${NC}"
if [ ! -d ".venv" ]; then
    python3 -m venv .venv
    echo -e "${GREEN}Ambiente virtual criado em .venv.${NC}"
else
    echo -e "${GREEN}Ambiente virtual .venv já existe.${NC}"
fi

# Ativar virtualenv
source .venv/bin/activate

# 3. Atualizar pip e instalar dependências
echo -e "\n${BLUE}[3/5] Instalando dependências do Python...${NC}"
pip install --upgrade pip
pip install -r requirements.txt
echo -e "${GREEN}Dependências do Python instaladas com sucesso.${NC}"

# 4. Criar estrutura de diretórios de dados
echo -e "\n${BLUE}[4/5] Criando estrutura de pastas para os volumes de dados...${NC}"
mkdir -p data/models data/uploads data/outputs data/glossary frontend
echo -e "${GREEN}Pastas de dados preparadas.${NC}"

# 5. Configurar arquivo .env
echo -e "\n${BLUE}[5/5] Configurando variáveis de ambiente (.env)...${NC}"
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        cp .env.example .env
        echo -e "${GREEN}Arquivo .env criado a partir do .env.example.${NC}"
    else
        cat <<EOT > .env
MODEL_CACHE_DIR=./data/models
CHUNK_SIZE_TOKENS=400
BATCH_SIZE=8
QUALITY_THRESHOLD=0.6
USE_OPENAI_POSTEDIT=false
OPENAI_API_KEY=
MAX_FILE_MB=100
JOB_RETENTION_HOURS=24
EOT
        echo -e "${GREEN}Arquivo .env gerado com valores padrão.${NC}"
    fi
else
    echo -e "${GREEN}Arquivo .env existente detectado. Nenhuma alteração feita.${NC}"
fi

echo -e "\n${GREEN}=== Configuração concluída com sucesso! ===${NC}"
echo -e "Para iniciar o projeto:"
echo -e "  1. Ative o ambiente virtual: ${YELLOW}source .venv/bin/activate${NC}"
echo -e "  2. Execute a suíte de testes: ${YELLOW}pytest tests/${NC}"
echo -e "  3. Inicie o servidor FastAPI: ${YELLOW}uvicorn app.main:app --reload${NC}"
echo -e "  4. Acesse o frontend no navegador: ${YELLOW}http://localhost:8000${NC}\n"
