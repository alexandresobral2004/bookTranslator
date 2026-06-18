import os
import uuid
import shutil
import logging
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, BackgroundTasks, HTTPException, Depends
from app.config import settings
from app.schemas.job import UploadResponse
from app.schemas.translation import TranslationOptions
from core.jobs.job_store import job_store
from core.pipeline import start_translation_pipeline

router = APIRouter(prefix="/api", tags=["upload"])
logger = logging.getLogger(__name__)

@router.post("/upload", response_model=UploadResponse)
async def upload_pdf(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    use_glossary: bool = Form(default=True),
    use_openai_postedit: bool = Form(default=False),
    openai_api_key: Optional[str] = Form(default=None)
):
    # 1. Validação de extensão
    if not file.filename or not file.filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=400, detail="Apenas arquivos PDF são suportados.")

    # 2. Geração do UUID e caminhos
    job_id = str(uuid.uuid4())
    temp_filename = f"{job_id}.pdf"
    temp_path = os.path.join(settings.UPLOAD_DIR, temp_filename)

    # 3. Escrita assíncrona do arquivo (com limitação de tamanho)
    try:
        total_size = 0
        with open(temp_path, "wb") as buffer:
            while chunk := await file.read(8192):
                total_size += len(chunk)
                if total_size > settings.max_content_length:
                    # Remove arquivo parcial
                    buffer.close()
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                    raise HTTPException(
                        status_code=413, 
                        detail=f"Arquivo excede o limite máximo permitido de {settings.MAX_FILE_MB}MB."
                    )
                buffer.write(chunk)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Erro ao salvar arquivo de upload: {str(e)}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail="Erro interno ao salvar o arquivo enviado.")

    # 4. Criar registro do Job
    job_store.create_job(job_id=job_id, filename=file.filename)

    # 5. Configurar opções de tradução
    options = TranslationOptions(
        use_glossary=use_glossary,
        use_openai_postedit=use_openai_postedit,
        openai_api_key=openai_api_key
    )

    # 6. Agendar pipeline em background
    background_tasks.add_task(
        start_translation_pipeline,
        job_id=job_id,
        file_path=temp_path,
        options=options
    )

    logger.info(f"Upload concluído. Job {job_id} iniciado para o arquivo {file.filename}.")
    
    return UploadResponse(
        job_id=job_id,
        filename=file.filename,
        message="Upload concluído. Processamento iniciado em background."
    )
