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

        # 3. Camada RAG & Glossário
        # Estrutura para armazenar os mapeamentos de placeholders por chunk
        placeholders_mappings = [None] * len(chunks)
        
        if options.use_glossary:
            job_store.update_job(
                job_id, 
                status=JobStatus.TRANSLATING, 
                progress=20.0, 
                message="Carregando dicionário e aplicando termos do glossário..."
            )
            from core.rag.term_replacer import term_replacer
            
            def preprocess_all_chunks():
                for idx, chunk_item in enumerate(chunks):
                    processed_text, mapping = term_replacer.preprocess_chunk(chunk_item["text"])
                    chunk_item["text"] = processed_text
                    placeholders_mappings[idx] = mapping
                    
            await asyncio.to_thread(preprocess_all_chunks)
            
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
        
        # Pós-processamento do glossário: Restaura os termos corretos em português
        if options.use_glossary:
            from core.rag.term_replacer import term_replacer
            
            def postprocess_all_chunks():
                for idx, trans_text in enumerate(translated_texts):
                    mapping = placeholders_mappings[idx]
                    if mapping:
                        translated_texts[idx] = term_replacer.postprocess_chunk(trans_text, mapping)
                        
            await asyncio.to_thread(postprocess_all_chunks)
            
        # Vincula os textos traduzidos de volta nos respectivos chunks
        for idx, trans_text in enumerate(translated_texts):
            chunks[idx]["translated_text"] = trans_text

        # 5. Pós-edição OpenAI
        if options.use_openai_postedit:
            job_store.update_job(
                job_id, 
                status=JobStatus.POSTEDITING, 
                progress=82.0, 
                message="Avaliando a qualidade da tradução local..."
            )
            from core.translator.quality_scorer import quality_scorer
            from core.posteditor.openai_editor import openai_editor
            
            low_quality_count = 0
            for idx, chunk_item in enumerate(chunks):
                original_en = chunk_item["text"]
                translated_pt = chunk_item["translated_text"]
                
                # Calcula o score de qualidade do chunk
                score = quality_scorer.evaluate_quality(original_en, translated_pt)
                
                # Se estiver abaixo do threshold, corrige com OpenAI
                if score < settings.QUALITY_THRESHOLD:
                    low_quality_count += 1
                    job_store.update_job(
                        job_id,
                        progress=82.0 + (idx / len(chunks)) * 7.0,
                        message=f"Corrigindo trecho {low_quality_count} com OpenAI..."
                    )
                    corrected_text = await openai_editor.postedit_translation_async(
                        original_en=original_en,
                        current_pt=translated_pt,
                        user_api_key=options.openai_api_key
                    )
                    chunk_item["translated_text"] = corrected_text
                    
            logger.info(f"Pós-edição OpenAI concluída. {low_quality_count}/{len(chunks)} chunks corrigidos.")

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

        # Limpa o arquivo de upload temporário após a conclusão bem-sucedida
        if os.path.exists(file_path):
            try:
                os.remove(file_path)
            except Exception:
                pass

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
