import logging
from typing import List, Dict, Any
from core.extractor.page_model import Page

logger = logging.getLogger(__name__)

class HTMLBuilder:
    def detect_block_tag(self, block: Any) -> str:
        """
        Heurística simples para detectar se o bloco original se comporta
        como cabeçalho (h1, h2, h3) ou parágrafo comum (p) com base no tamanho das fontes.
        """
        if not block.spans:
            return "p"
            
        # Pega o span principal (maior fonte ou primeiro)
        spans_sorted = sorted(block.spans, key=lambda s: s.size, reverse=True)
        main_span = spans_sorted[0]
        
        # Se a fonte for maior que 16px e for negrito/curta
        if main_span.size >= 16.0 and len(block.text) < 100:
            return "h1"
        elif main_span.size >= 13.0 and len(block.text) < 120:
            return "h2"
        elif main_span.size >= 11.0 and main_span.bold and len(block.text) < 150:
            return "h3"
            
        return "p"

    def build_translation_html(self, pages: List[Page], translated_chunks: List[Dict[str, Any]]) -> str:
        """
        Reconstrói o documento traduzido em formato HTML estruturado.
        Agrupa os chunks traduzidos de volta nos seus respectivos blocos e páginas,
        e aplica estilos baseados no documento original com CSS inline.
        """
        logger.info("Iniciando reconstrução do HTML traduzido.")
        
        # 1. Agrupar chunks traduzidos por (page_num, block_idx)
        # O chunk original contém o texto traduzido no campo "translated_text"
        translations_map: Dict[str, List[str]] = {}
        for chunk in translated_chunks:
            key = f"{chunk['page_num']}_{chunk['block_idx']}"
            if key not in translations_map:
                translations_map[key] = []
            translations_map[key].append(chunk.get("translated_text", chunk["text"]))
            
        # 2. Montar estrutura HTML do documento
        html_pages = []
        for page in pages:
            page_blocks_html = []
            
            # Ordena os blocos por posição vertical (y0) e horizontal (x0) para garantir leitura natural
            sorted_blocks = sorted(page.blocks, key=lambda b: (b.bbox[1], b.bbox[0]))
            
            for block_idx, block in enumerate(sorted_blocks):
                if block.block_type != "text":
                    continue
                
                # Busca a tradução do bloco (pode ser reconstruída de múltiplos chunks)
                key = f"{page.page_num}_{page.blocks.index(block)}"
                translated_texts_list = translations_map.get(key)
                
                if translated_texts_list:
                    translated_html_content = " ".join(translated_texts_list)
                else:
                    # Fallback para o original se não houver tradução
                    from core.chunker.text_chunker import chunker
                    translated_html_content = chunker.block_to_html_text(block)
                
                if not translated_html_content.strip():
                    continue
                    
                # Detecta tag semântica (h1, h2, p)
                tag = self.detect_block_tag(block)
                
                # Aplica estilos inline simples preservando o tamanho de fonte relativo
                size_style = ""
                if block.spans:
                    font_size = block.spans[0].size
                    size_style = f"font-size: {font_size:.1f}px;"
                
                block_html = f"<{tag} style='margin-bottom: 12px; line-height: 1.5; {size_style}'>{translated_html_content}</{tag}>"
                page_blocks_html.append(block_html)
                
            # Constrói a página com quebra de página do CSS para WeasyPrint
            page_content = "\n  ".join(page_blocks_html)
            page_html = f"""
<div class="page" style="page-break-after: always; padding: 50px 60px; box-sizing: border-box; min-height: 800px;">
  {page_content}
</div>
"""
            html_pages.append(page_html)

        # 3. Une todas as páginas em um template HTML completo
        full_html = f"""<!DOCTYPE html>
<html lang="pt-br">
<head>
    <meta charset="UTF-8">
    <title>Livro Traduzido</title>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Crimson+Pro:ital,wght@0,300;0,400;0,600;1,400&family=Inter:wght@400;500;600&display=swap');
        
        body {{
            font-family: 'Crimson Pro', Georgia, serif;
            color: #2c3e50;
            margin: 0;
            padding: 0;
            background-color: #f8f9fa;
        }}
        
        h1, h2, h3 {{
            font-family: 'Inter', sans-serif;
            color: #1a252f;
            margin-top: 24px;
            margin-bottom: 12px;
            font-weight: 600;
        }}
        
        h1 {{ border-bottom: 1px solid #eee; padding-bottom: 8px; }}
        
        p {{
            text-align: justify;
            text-indent: 20px;
            margin: 0 0 12px 0;
        }}
        
        b, strong {{
            font-weight: 600;
        }}
        
        i, em {{
            font-style: italic;
        }}
        
        /* Regras de impressão para o WeasyPrint */
        @page {{
            size: A4;
            margin: 0;
        }}
        
        .page {{
            background: white;
            max-width: 800px;
            margin: 0 auto;
        }}
    </style>
</head>
<body>
    {"".join(html_pages)}
</body>
</html>
"""
        logger.info("HTML traduzido construído com sucesso.")
        return full_html

# Singleton do construtor HTML
html_builder = HTMLBuilder()
