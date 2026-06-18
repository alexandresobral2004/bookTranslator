import os
import asyncio
import logging
from core.jobs.job_store import job_store
from core.jobs.job_model import JobStatus
from app.config import settings
from app.schemas.translation import TranslationOptions

# Importações dos módulos da Fase 2
from core.extractor.pdf_extractor import extract_pdf_structure
from core.chunker.text_chunker import chunker
from core.translator.batch_processor import translate_chunks_batched
from core.builder.html_builder import html_builder
from core.builder.pdf_exporter import export_html_to_pdf_async

logger = logging.getLogger(__name__)

async def start_translation_pipeline(job_id: str, file_path: str, options: TranslationOptions):
    """
    Função principal que orquestra todo o pipeline de tradução do PDF de forma assíncrona.
    Consome os serviços das camadas independentes e reporta o progresso em tempo real no JobStore.
    """
    try:
        # 1. Extração de texto estruturado
        logger.info(f"Iniciando extração do job {job_id}.")
        job_store.update_job(
            job_id, 
            status=JobStatus.EXTRACTING, 
            progress=5.0, 
            message="Iniciando leitura e extração do PDF..."
        )
        
        # Executa a extração em thread pool (CPU-bound)
        pages = await asyncio.to_thread(extract_pdf_structure, file_path)
        
        if not pages:
            raise ValueError("O PDF está vazio ou não possui texto extraível.")
            
        job_store.update_job(
            job_id, 
            status=JobStatus.CHUNKING, 
            progress=15.0, 
            message="Texto extraído com sucesso. Iniciando segmentação..."
        )

        # 2. Chunking (segmentação por tokens)
        # Executa em thread pool
        chunks = await asyncio.to_thread(chunker.chunk_pages, pages)
        
        if not chunks:
            raise ValueError("Não foi possível segmentar o documento em chunks válidos.")

        # 3. Camada RAG & Glossário (Fase 3 - a ser implementada)
        # Placeholder para as próximas fases:
        if options.use_glossary:
            job_store.update_job(
                job_id, 
                status=JobStatus.TRANSLATING, 
                progress=20.0, 
                message="Carregando dicionário e aplicando termos do glossário..."
            )
            # RAG HOOK: Aqui aplicaremos a substituição de termos
            await asyncio.sleep(1.0) # Simulação de carregamento do index
            
        # 4. Tradução via MarianMT
        job_store.update_job(
            job_id, 
            status=JobStatus.TRANSLATING, 
            progress=25.0, 
            message="Iniciando tradução local via MarianMT..."
        )
        
        # Callback assíncrono de progresso para a tradução
        async def translation_progress(processed: int, total: int):
            # Mapeia o progresso de 25% a 80% do pipeline total
            pct = 25.0 + (processed / total) * 55.0
            job_store.update_job(
                job_id,
                progress=pct,
                message=f"Traduzindo blocos de texto ({processed}/{total})..."
            )

        # Extrai apenas as strings de texto para tradução
        texts_to_translate = [c["text"] for c in chunks]
        
        # Traduz os blocos
        translated_texts = await translate_chunks_batched(
            texts_to_translate, 
            progress_callback=translation_progress
        )
        
        # Vincula os textos traduzidos de volta nos respectivos chunks
        for idx, trans_text in enumerate(translated_texts):
            chunks[idx]["translated_text"] = trans_text

        # 5. Pós-edição OpenAI (Fase 4 - a ser implementada)
        if options.use_openai_postedit:
            job_store.update_job(
                job_id, 
                status=JobStatus.POSTEDITING, 
                progress=85.0, 
                message="Avaliando e revisando trechos com OpenAI..."
            )
            # POST-EDIT HOOK: Aqui executaremos a verificação de qualidade
            await asyncio.sleep(1.0)

        # 6. Reconstrução do layout (HTML + PDF final)
        job_store.update_job(
            job_id, 
            status=JobStatus.BUILDING, 
            progress=90.0, 
            message="Reconstruindo layout e gerando HTML..."
        )
        
        # Cria HTML
        html_content = await asyncio.to_thread(
            html_builder.build_translation_html, 
            pages, 
            chunks
        )
        
        # Define caminho de saída
        output_filename = f"{job_id}_translated.pdf"
        output_path = os.path.join(settings.OUTPUT_DIR, output_filename)
        
        job_store.update_job(
            job_id, 
            status=JobStatus.BUILDING, 
            progress=95.0, 
            message="Compilando PDF final com WeasyPrint..."
        )
        
        # Compila para PDF usando WeasyPrint (CPU-bound)
        await export_html_to_pdf_async(html_content, output_path)

        # Conclusão bem-sucedida do Job
        job_store.update_job(
            job_id,
            status=JobStatus.COMPLETED,
            progress=100.0,
            message="Tradução concluída com sucesso! Download pronto.",
            output_filename=output_filename
        )
        logger.info(f"Job {job_id} concluído com sucesso. Arquivo: {output_filename}")

    except Exception as e:
        logger.error(f"Erro crítico no pipeline do job {job_id}: {str(e)}", exc_info=True)
        job_store.update_job(
            job_id,
            status=JobStatus.FAILED,
            progress=100.0,
            message="Falha durante o processamento da tradução.",
            error_message=str(e)
        )
        
        # Remove arquivo temporário de upload se falhar
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass
