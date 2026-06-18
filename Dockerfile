# ==============================================================================
# Stage 1: Builder (Instalação e compilação de pacotes)
# ==============================================================================
FROM python:3.11-slim AS builder

WORKDIR /build

# Instala dependências de compilação do sistema
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    gcc \
    libffi-dev \
    && rm -rf /var/lib/apt/lists/*

# Instala pacotes Python
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# ==============================================================================
# Stage 2: Runtime (Imagem final otimizada)
# ==============================================================================
FROM python:3.11-slim AS runner

WORKDIR /app

# Instala dependências de execução do WeasyPrint (Cairo, Pango, GdkPixbuf e Fontes)
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpango-1.0-0 \
    libpangocairo-1.0-0 \
    libcairo2 \
    libgdk-pixbuf-2.0-0 \
    shared-mime-info \
    fonts-dejavu-core \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# Copia dependências instaladas no Builder
COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

# Configura variáveis de ambiente do Python e cache de modelos
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    HF_HOME=/app/data/models \
    MODEL_CACHE_DIR=/app/data/models

# Cria estrutura de diretórios para volumes
RUN mkdir -p data/models data/uploads data/outputs data/glossary frontend

# Copia a aplicação
COPY app/ ./app/
COPY core/ ./core/
COPY frontend/ ./frontend/
COPY start.py .
COPY requirements.txt .

EXPOSE 8000

# Usa start.py para iniciar o Uvicorn programaticamente com log_config
# que redireciona TODOS os logs (incluindo internos do Uvicorn) para stdout
CMD ["python", "start.py"]
