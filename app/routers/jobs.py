import json
import asyncio
import logging
from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from core.jobs.job_store import job_store
from core.jobs.job_model import JobStatus
from app.schemas.job import JobStatusResponse

router = APIRouter(prefix="/api", tags=["jobs"])
logger = logging.getLogger(__name__)

# Intervalo entre atualizações de progresso (ms)
SSE_POLL_INTERVAL = 0.5
# Intervalo do heartbeat para manter a conexão viva em proxies (s)
SSE_HEARTBEAT_INTERVAL = 15.0


@router.get("/status/{job_id}", response_model=JobStatusResponse)
async def get_job_status(job_id: str):
    """Consulta o status atual de um job específico."""
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job de tradução não encontrado.")
    return job


@router.get("/status/{job_id}/events")
async def get_job_status_events(job_id: str):
    """Retorna um stream SSE (Server-Sent Events) de atualizações de progresso em tempo real."""
    job = job_store.get_job(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Job de tradução não encontrado.")

    async def event_generator():
        last_heartbeat = asyncio.get_event_loop().time()
        try:
            while True:
                current_job = job_store.get_job(job_id)
                if not current_job:
                    yield "event: error\ndata: Job não encontrado\n\n"
                    break

                # Envia estado atual do job
                job_json = current_job.model_dump_json()
                yield f"data: {job_json}\n\n"

                # Para de enviar se o job estiver finalizado ou falhado
                if current_job.status in [JobStatus.COMPLETED, JobStatus.FAILED]:
                    break

                await asyncio.sleep(SSE_POLL_INTERVAL)

                # Heartbeat: comentário SSE para manter conexão viva em proxies
                now = asyncio.get_event_loop().time()
                if now - last_heartbeat >= SSE_HEARTBEAT_INTERVAL:
                    yield ": keepalive\n\n"
                    last_heartbeat = now

        except asyncio.CancelledError:
            logger.info(f"Conexão SSE cancelada para o job {job_id}.")
        except Exception as e:
            logger.error(f"Erro no stream SSE para o job {job_id}: {str(e)}")
            yield f"event: error\ndata: Erro interno no stream: {str(e)}\n\n"

    # Headers essenciais para evitar buffering em proxies (Nginx, Railway, Cloudflare)
    headers = {
        "Cache-Control": "no-cache",
        "X-Accel-Buffering": "no",
        "Connection": "keep-alive",
    }

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers=headers,
    )
