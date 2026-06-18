import asyncio
import logging
from weasyprint import HTML

logger = logging.getLogger(__name__)

async def export_html_to_pdf_async(html_content: str, output_path: str) -> None:
    """
    Converte o HTML compilado em um documento PDF usando WeasyPrint.
    Executa em uma thread separada (asyncio.to_thread) pois a compilação do WeasyPrint
    é uma tarefa pesada de CPU-bound.
    """
    logger.info(f"Iniciando compilação do PDF final via WeasyPrint: {output_path}")
    
    def compile_pdf():
        # Cria a instância HTML do WeasyPrint e gera o PDF
        html = HTML(string=html_content)
        html.write_pdf(output_path)
        
    try:
        await asyncio.to_thread(compile_pdf)
        logger.info(f"PDF gerado com sucesso em: {output_path}")
    except Exception as e:
        logger.error(f"Erro crítico ao gerar PDF com WeasyPrint: {str(e)}")
        raise RuntimeError(f"Falha na compilação do PDF: {str(e)}")
