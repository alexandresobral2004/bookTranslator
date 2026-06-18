import asyncio
import logging
from core.jobs.job_store import job_store
from core.jobs.job_model import JobStatus
from app.schemas.translation import TranslationOptions

logger = logging.getLogger(__name__)

async def start_translation_pipeline(job_id: str, file_path: str, options: TranslationOptions):
    """
    Função do pipeline de tradução rodando em background.
    No MVP, simulamos o progresso com esperas para que a API possa ser testada.
    """
    try:
        # 1. Extração
        job_store.update_job(job_id, status=JobStatus.EXTRACTING, progress=10.0, message="Extraindo texto do PDF...")
        await asyncio.sleep(2.0)

        # 2. Chunking
        job_store.update_job(job_id, status=JobStatus.CHUNKING, progress=20.0, message="Segmentando blocos de texto...")
        await asyncio.sleep(1.0)

        # 3. RAG/Glossário
        if options.use_glossary:
            job_store.update_job(job_id, status=JobStatus.TRANSLATING, progress=25.0, message="Carregando e aplicando glossário técnico...")
            await asyncio.sleep(1.0)

        # 4. Tradução (simulada por páginas/blocos)
        for i in range(1, 6):
            pct = 25.0 + (i * 10.0)  # vai de 35% a 75%
            job_store.update_job(job_id, status=JobStatus.TRANSLATING, progress=pct, message=f"Traduzindo blocos (Lote {i}/5)...")
            await asyncio.sleep(2.0)

        # 5. Pós-edição OpenAI
        if options.use_openai_postedit:
            job_store.update_job(job_id, status=JobStatus.POSTEDITING, progress=85.0, message="Revisando trechos de baixa qualidade via OpenAI...")
            await asyncio.sleep(2.0)

        # 6. Reconstrução
        job_store.update_job(job_id, status=JobStatus.BUILDING, progress=95.0, message="Reconstruindo layout e gerando PDF final...")
        await asyncio.sleep(2.0)

        # Concluído
        # Para o mock, apenas simula um nome de arquivo de saída
        output_filename = f"{job_id}_translated.pdf"
        job_store.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            progress=100.0,
            message="Tradução concluída com sucesso!",
            output_filename=output_filename
        )
        logger.info(f"Job {job_id} concluído com sucesso (mock).")

    except Exception as e:
        logger.error(f"Erro no pipeline do job {job_id}: {str(e)}", exc_info=True)
        job_store.update_job(
            job_id,
            status=JobStatus.FAILED,
            progress=100.0,
            message="Falha durante o processamento da tradução.",
            error_message=str(e)
        )
