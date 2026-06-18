import asyncio
import logging
import threading
from weasyprint import HTML

logger = logging.getLogger(__name__)

# Timeout em segundos para compilação do PDF (protege contra travamentos em documentos grandes)
WEASYPRINT_TIMEOUT_SECONDS = 600  # 10 minutos

async def export_html_to_pdf_async(html_content: str, output_path: str) -> None:
    """
    Converte o HTML compilado em um documento PDF usando WeasyPrint.
    Executa em uma thread separada (asyncio.to_thread) pois a compilação do WeasyPrint
    é uma tarefa pesada de CPU-bound. Inclui um timeout para proteger contra travamentos.
    """
    logger.info(f"Iniciando compilação do PDF final via WeasyPrint: {output_path}")

    result_container = {"error": None}

    def compile_pdf():
        try:
            # base_url=None evita que WeasyPrint tente resolver caminhos relativos de arquivo
            html = HTML(string=html_content, base_url=None)
            html.write_pdf(output_path)
        except Exception as e:
            result_container["error"] = e

    thread = threading.Thread(target=compile_pdf, daemon=True)
    thread.start()

    # Aguarda a thread de compilação em asyncio sem bloquear o event loop
    loop = asyncio.get_event_loop()
    await loop.run_in_executor(None, thread.join, WEASYPRINT_TIMEOUT_SECONDS)

    if thread.is_alive():
        # Timeout — a thread ainda está rodando (WeasyPrint travou)
        error_msg = f"Timeout de {WEASYPRINT_TIMEOUT_SECONDS}s atingido na compilação do PDF com WeasyPrint."
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    if result_container["error"]:
        logger.error(f"Erro crítico ao gerar PDF com WeasyPrint: {result_container['error']}")
        raise RuntimeError(f"Falha na compilação do PDF: {result_container['error']}")

    logger.info(f"PDF gerado com sucesso em: {output_path}")

