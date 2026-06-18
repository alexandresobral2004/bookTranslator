import os
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from app.config import settings
from core.jobs.job_store import job_store
from core.jobs.job_model import JobStatus

router = APIRouter(prefix="/api", tags=["download"])
logger = logging.getLogger(__name__)

@router.get("/download/{job_id}")
async def download_translated_pdf(job_id: str):
    """Permite o download do PDF final traduzido."""
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job de tradução não encontrado.")
    
    if job.status != JobStatus.COMPLETED:
        raise HTTPException(
            status_code=400, 
            detail=f"O PDF ainda não está pronto para download. Status atual: {job.status}"
        )
        
    if not job.output_filename:
        raise HTTPException(
            status_code=404, 
            detail="Arquivo de saída não registrado no Job."
        )

    file_path = os.path.join(settings.OUTPUT_DIR, job.output_filename)
    
    # Criamos um arquivo de simulação caso ele ainda não exista no disco (para podermos testar a API pura sem o backend de WeasyPrint pronto)
    if not os.path.exists(file_path):
        # Para testes do mock, se o arquivo físico ainda não existir, cria um dummy de 0 bytes
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        with open(file_path, "wb") as f:
            f.write(b"%PDF-1.4 Mock output PDF contents for testing backend structures.")
        logger.info(f"Criado arquivo dummy para download em {file_path}")

    # Define o nome do arquivo final de download como o nome original com sufixo _traduzido
    base_name, _ = os.path.splitext(job.filename)
    download_name = f"{base_name}_traduzido.pdf"

    return FileResponse(
        path=file_path,
        filename=download_name,
        media_type="application/pdf"
    )
