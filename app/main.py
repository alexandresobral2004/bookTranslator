import os
import sys
import asyncio
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from app.config import settings
from app.routers import upload, jobs, download
from core.jobs.job_store import job_store

# Configuração de Logs (redirecionados para stdout para evitar [err] em logs informativos no Railway)
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)]
)
logger = logging.getLogger("app.main")

async def periodic_job_cleanup():
    """Tarefa em segundo plano para limpar jobs expirados periodicamente."""
    try:
        while True:
            # Limpa jobs mais antigos que o tempo definido nas configurações (ex: 24h)
            removed = job_store.clean_old_jobs(settings.JOB_RETENTION_HOURS)
            if removed > 0:
                logger.info(f"Limpeza periódica executada: {removed} job(s) expirado(s) removido(s).")
            # Executa a limpeza a cada 1 hora
            await asyncio.sleep(3600)
    except asyncio.CancelledError:
        logger.info("Tarefa de limpeza periódica cancelada.")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Garante que os diretórios necessários existam
    settings.create_directories()
    
    # Inicializa o glossário FAISS se disponível
    try:
        from core.rag.glossary_loader import initialize_glossary
        initialize_glossary()
    except Exception as e:
        logger.error(f"Erro ao inicializar glossário no startup: {str(e)}")
        
    # Pré-carrega o modelo de tradução local para evitar race conditions em threads
    try:
        from core.translator.marian_translator import translator
        logger.info("Pré-carregando modelo de tradução no startup...")
        await asyncio.to_thread(translator.load_model)
    except Exception as e:
        logger.error(f"Erro ao pré-carregar modelo de tradução no startup: {str(e)}")
        
    # Cria a pasta frontend se não existir para evitar erro de montagem do StaticFiles
    os.makedirs("frontend", exist_ok=True)
    os.makedirs(os.path.join("frontend", "css"), exist_ok=True)
    os.makedirs(os.path.join("frontend", "js"), exist_ok=True)
    
    # Cria arquivo index.html mínimo se não existir
    index_path = "frontend/index.html"
    if not os.path.exists(index_path):
        with open(index_path, "w", encoding="utf-8") as f:
            f.write("<!DOCTYPE html><html><body><h1>BookTranslator Backend is running</h1></body></html>")
            
    # Inicia a tarefa em background para limpeza de jobs antigos
    cleanup_task = asyncio.create_task(periodic_job_cleanup())
    
    logger.info("BookTranslator iniciado com sucesso. Pastas prontas.")
    yield
    
    # Cancelamento das tarefas em background ao encerrar
    cleanup_task.cancel()
    try:
        await cleanup_task
    except asyncio.CancelledError:
        pass
    logger.info("BookTranslator encerrado.")

app = FastAPI(
    title="BookTranslator API",
    description="Backend FastAPI para tradução de livros em PDF de inglês para português.",
    version="1.0.0",
    lifespan=lifespan
)

# Configuração de CORS (liberando tudo para desenvolvimento local)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registro de Rotas da API
app.include_router(upload.router)
app.include_router(jobs.router)
app.include_router(download.router)

# Rota principal para documentação e status da API
@app.get("/health", tags=["health"])
async def health_check():
    return {
        "status": "healthy",
        "app": "BookTranslator",
        "max_upload_size_mb": settings.MAX_FILE_MB,
        "active_jobs": len(job_store.list_jobs())
    }

# Montagem dos arquivos estáticos para o frontend
app.mount("/", StaticFiles(directory="frontend", html=True), name="frontend")
