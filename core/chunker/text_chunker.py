import re
import logging
from typing import List, Dict, Any, Tuple
from transformers import AutoTokenizer
from app.config import settings
from core.extractor.page_model import Page, Block, TextSpan

logger = logging.getLogger(__name__)

class Chunker:
    def __init__(self):
        self.tokenizer = None

    def _load_tokenizer(self):
        if self.tokenizer is None:
            try:
                # Carrega o tokenizer correspondente ao modelo MarianMT do cache/HuggingFace
                logger.info(f"Carregando tokenizer: {settings.MARIAN_MODEL_NAME}")
                self.tokenizer = AutoTokenizer.from_pretrained(
                    settings.MARIAN_MODEL_NAME,
                    cache_dir=settings.MODEL_CACHE_DIR
                )
            except Exception as e:
                logger.warning(f"Erro ao carregar tokenizer do MarianMT ({str(e)}). Usando fallback por caracteres (1 token ≈ 4 caracteres).")
                self.tokenizer = None

    def get_token_count(self, text: str) -> int:
        """Retorna a contagem de tokens usando o tokenizer ou um fallback aproximado."""
        self._load_tokenizer()
        if self.tokenizer:
            try:
                return len(self.tokenizer.tokenize(text))
            except Exception:
                pass
        # Fallback: aproximadamente 4 caracteres por token
        return len(text) // 4 + 1

    def block_to_html_text(self, block: Block) -> str:
        """
        Converte o bloco de texto e seus spans em uma única string HTML contendo
        tags inline <b> (bold) e <i> (italic) para preservar os estilos na tradução.
        """
        parts = []
        for span in block.spans:
            text = span.text
            if not text:
                continue
            
            # Sanitiza caracteres que possam quebrar tags simples
            # Mas preservamos espaços em branco nas bordas para manter a formatação do texto
            formatted_text = text
            if span.bold:
                formatted_text = f"<b>{formatted_text}</b>"
            if span.italic:
                formatted_text = f"<i>{formatted_text}</i>"
            parts.append(formatted_text)
            
        return "".join(parts)

    def split_sentences(self, text: str) -> List[str]:
        """Divide uma string em sentenças simples respeitando pontuação de final de frase."""
        # Regex básico para separar por . ! ? mantendo a pontuação na sentença correspondente
        sentence_end = re.compile(r'(?<=[.!?])\s+')
        sentences = sentence_end.split(text)
        return [s.strip() for s in sentences if s.strip()]

    def chunk_pages(self, pages: List[Page]) -> List[Dict[str, Any]]:
        """
        Segmenta as páginas extraídas em chunks de tamanho controlado para tradução,
        mantendo o mapeamento de volta para o bloco/página de origem.
        
        Retorna uma lista de dicionários contendo:
        {
            "chunk_id": int,
            "page_num": int,
            "block_idx": int,
            "text": str,  # texto formatado em HTML com tags inline <b>/<i>
            "token_count": int
        }
        """
        chunks = []
        chunk_id = 0
        limit = settings.CHUNK_SIZE_TOKENS

        for page in pages:
            for block_idx, block in enumerate(page.blocks):
                if block.block_type != "text":
                    continue
                
                html_text = self.block_to_html_text(block)
                if not html_text.strip():
                    continue

                tokens = self.get_token_count(html_text)
                
                # Se couber em um único chunk, enviamos o bloco inteiro
                if tokens <= limit:
                    chunks.append({
                        "chunk_id": chunk_id,
                        "page_num": page.page_num,
                        "block_idx": block_idx,
                        "text": html_text,
                        "token_count": tokens
                    })
                    chunk_id += 1
                else:
                    # Se exceder o limite de tokens, dividimos o bloco por sentenças
                    logger.info(f"Bloco {block_idx} na pág {page.page_num} excede o limite ({tokens} tokens). Dividindo...")
                    sentences = self.split_sentences(html_text)
                    current_chunk_text = []
                    current_chunk_tokens = 0
                    
                    for sentence in sentences:
                        sent_tokens = self.get_token_count(sentence)
                        
                        # Se uma única sentença for maior que o limite, mandamos ela inteira de qualquer forma
                        if current_chunk_tokens + sent_tokens > limit and current_chunk_text:
                            # Salva o chunk acumulado anterior
                            chunks.append({
                                "chunk_id": chunk_id,
                                "page_num": page.page_num,
                                "block_idx": block_idx,
                                "text": " ".join(current_chunk_text),
                                "token_count": current_chunk_tokens
                            })
                            chunk_id += 1
                            current_chunk_text = [sentence]
                            current_chunk_tokens = sent_tokens
                        else:
                            current_chunk_text.append(sentence)
                            current_chunk_tokens += sent_tokens
                            
                    # Adiciona a última parte acumulada
                    if current_chunk_text:
                        chunks.append({
                            "chunk_id": chunk_id,
                            "page_num": page.page_num,
                            "block_idx": block_idx,
                            "text": " ".join(current_chunk_text),
                            "token_count": current_chunk_tokens
                        })
                        chunk_id += 1

        logger.info(f"Segmentação concluída. Total de chunks gerados: {len(chunks)}.")
        return chunks

# Singleton do segmentador
chunker = Chunker()
