import asyncio
import logging
from typing import List, Callable, Awaitable, Any, Optional
from app.config import settings
from core.translator.marian_translator import MarianTranslator

logger = logging.getLogger(__name__)

# Instância singleton do tradutor
translator = MarianTranslator()

async def translate_chunks_batched(
    chunks: List[str], 
    progress_callback: Optional[Callable[[int, int], Awaitable[None]]] = None
) -> List[str]:
    """
    Traduz uma lista de textos em lotes (batches) de forma assíncrona, 
    utilizando asyncio.to_thread para não travar o event loop do FastAPI.
    
    A cada lote processado, opcionalmente chama a função progress_callback(processed_count, total_count).
    """
    if not chunks:
        return []

    batch_size = settings.BATCH_SIZE
    total_count = len(chunks)
    translated_texts = []
    
    logger.info(f"Iniciando tradução de {total_count} chunks em lotes de tamanho {batch_size}.")
    
    # Executa em lotes
    for i in range(0, total_count, batch_size):
        batch = chunks[i:i + batch_size]
        
        try:
            # Roda a inferência do modelo em uma thread separada para não bloquear a API
            batch_translated = await asyncio.to_thread(translator.translate, batch)
            translated_texts.extend(batch_translated)
        except Exception as e:
            logger.error(f"Erro ao traduzir lote {i // batch_size + 1}: {str(e)}")
            # Fallback em caso de falha do lote: tenta individualmente para não perder todo o lote
            logger.info("Tentando traduzir itens do lote individualmente como fallback...")
            for text in batch:
                try:
                    single_translated = await asyncio.to_thread(translator.translate, [text])
                    translated_texts.extend(single_translated)
                except Exception as single_err:
                    logger.error(f"Falha de tradução individual: {str(single_err)}")
                    # Se falhar totalmente, mantém o texto original para não parar o pipeline
                    translated_texts.append(text)
                    
        # Aciona o callback de progresso se fornecido
        processed = min(i + batch_size, total_count)
        if progress_callback:
            try:
                await progress_callback(processed, total_count)
            except Exception as cb_err:
                logger.warning(f"Erro ao chamar callback de progresso: {str(cb_err)}")

    return translated_texts

