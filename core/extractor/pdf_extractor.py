import fitz  # PyMuPDF
import logging
from typing import List
from core.extractor.page_model import Page, Block, TextSpan

logger = logging.getLogger(__name__)

def extract_pdf_structure(file_path: str) -> List[Page]:
    """
    Abre o PDF usando PyMuPDF (fitz) e extrai todo o texto estruturado em páginas,
    blocos e spans de texto, preservando estilos (negrito, itálico, tamanho) e coordenadas.
    """
    logger.info(f"Iniciando extração do PDF: {file_path}")
    pages: List[Page] = []
    
    try:
        doc = fitz.open(file_path)
    except Exception as e:
        logger.error(f"Erro ao abrir arquivo PDF {file_path}: {str(e)}")
        raise ValueError(f"Não foi possível ler o PDF: {str(e)}")

    try:
        for page_idx, page_fitz in enumerate(doc):
            page_data = page_fitz.get_text("dict")
            width = page_data["width"]
            height = page_data["height"]
            
            page = Page(
                page_num=page_idx + 1,
                width=width,
                height=height,
                blocks=[]
            )
            
            for block_dict in page_data.get("blocks", []):
                block_type = "image" if block_dict.get("type") == 1 else "text"
                bbox = block_dict.get("bbox")  # (x0, y0, x1, y1)
                
                block = Block(
                    block_type=block_type,
                    bbox=bbox,
                    spans=[]
                )
                
                # Para blocos de texto, iteramos pelas linhas e pelos spans
                if block_type == "text":
                    for line in block_dict.get("lines", []):
                        for span_dict in line.get("spans", []):
                            flags = span_dict.get("flags", 0)
                            
                            # Bitwise check do PyMuPDF para estilos:
                            # italic = flags & 2
                            # bold = flags & 16
                            is_italic = bool(flags & 2)
                            is_bold = bool(flags & 16)
                            
                            span = TextSpan(
                                text=span_dict.get("text", ""),
                                font_name=span_dict.get("font", "Helvetica"),
                                size=span_dict.get("size", 10.0),
                                bold=is_bold,
                                italic=is_italic,
                                color=span_dict.get("color", 0)
                            )
                            block.spans.append(span)
                
                # Apenas adicionamos blocos que contêm algum texto útil
                if block_type == "text" and block.text.strip():
                    page.blocks.append(block)
                elif block_type == "image":
                    # Mapeia bloco de imagem (útil para preservação de layout no futuro se necessário)
                    page.blocks.append(block)
                    
            pages.append(page)
            
        logger.info(f"Extração concluída com sucesso. {len(pages)} página(s) processada(s).")
        return pages
    finally:
        doc.close()
