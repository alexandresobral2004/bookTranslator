import asyncio
import logging
from typing import List, Callable, Awaitable, Any, Optional
from app.config import settings
from core.translator.marian_translator import translator

logger = logging.getLogger(__name__)

async def translate_chunks_batched(
    chunks: List[str], 
    progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None
) -> List[str]:
    """
    Traduz uma lista de textos em lotes (batches) de forma assíncrona, 
    utilizando asyncio.to_thread e limitando com um asyncio.Semaphore
    para paralelizar as traduções sem causar sobrecarga de memória/processamento.
    
    A cada lote processado, opcionalmente chama a função progress_callback(processed_count, total_count).
    """
    if not chunks:
        return []

    batch_size = settings.BATCH_SIZE
    total_count = len(chunks)
    
    # Criamos o semáforo de concorrência com o número configurado de workers
    workers = settings.TRANSLATION_WORKERS
    sem = asyncio.Semaphore(workers)
    
    logger.info(
        f"Iniciando tradução de {total_count} chunks em lotes de tamanho {batch_size} "
        f"com {workers} workers paralelos."
    )
    
    # Controladores de progresso seguros
    processed_count = 0
    progress_lock = asyncio.Lock()
    
    async def update_progress(count: int):
        nonlocal processed_count
        async with progress_lock:
            processed_count += count
            if progress_callback:
                try:
                    await progress_callback(processed_count, total_count)
                except Exception as cb_err:
                    logger.warning(f"Erro ao chamar callback de progresso: {str(cb_err)}")

    async def translate_batch(batch_idx: int, batch: List[str]) -> List[str]:
        # Tenta traduzir o lote inteiro utilizando o semáforo
        async with sem:
            try:
                # Roda a inferência do modelo em uma thread separada para não bloquear a API
                batch_translated = await asyncio.to_thread(translator.translate, batch)
                await update_progress(len(batch))
                return batch_translated
            except Exception as e:
                logger.error(f"Erro ao traduzir lote {batch_idx + 1}: {str(e)}")
                logger.info("Tentando traduzir itens do lote individualmente como fallback...")
        
        # Fallback em caso de falha do lote: tenta individualmente para não perder todo o lote.
        # Note que liberamos o semáforo do lote principal e cada tentativa individual adquirirá o semáforo.
        batch_translated = []
        for text in batch:
            async with sem:
                try:
                    single_translated = await asyncio.to_thread(translator.translate, [text])
                    batch_translated.extend(single_translated)
                except Exception as single_err:
                    logger.error(f"Falha de tradução individual: {str(single_err)}")
                    # Se falhar totalmente, mantém o texto original para não parar o pipeline
                    batch_translated.append(text)
            # Atualiza o progresso para cada chunk processado
            await update_progress(1)
            
        return batch_translated

    # Divide a lista em batches e cria as tarefas concorrentes
    batches = [chunks[i:i + batch_size] for i in range(0, total_count, batch_size)]
    tasks = [translate_batch(idx, batch) for idx, batch in enumerate(batches)]
    
    # Executa de forma concorrente. A ordem dos resultados é preservada pelo asyncio.gather
    results = await asyncio.gather(*tasks)
    
    # Achatando a lista de listas em uma única lista ordenada de resultados
    flat_results = []
    for res in results:
        flat_results.extend(res)
        
    return flat_results

