import re
import logging
from typing import List, Dict, Tuple, Any
from core.rag.glossary_store import glossary_store
from app.config import settings

logger = logging.getLogger(__name__)

class TermReplacer:
    def preprocess_chunk(self, text: str) -> Tuple[str, List[Dict[str, str]]]:
        """
        Analisa o texto do chunk original em inglês, localiza termos técnicos
        usando busca semântica no FAISS (filtrando candidatos) + casamento de padrão,
        e os substitui por placeholders imutáveis para garantir consistência.
        
        Retorna: (texto_com_placeholders, mapeamento_de_termos)
        """
        mapeamento: List[Dict[str, str]] = []
        
        # 1. Busca termos candidatos no FAISS usando o próprio texto do chunk
        # Recuperamos k candidatos (ajustável pelas configurações)
        k_candidates = settings.RAG_K_NEIGHBORS * 3
        candidates_with_scores = glossary_store.search(text, k=k_candidates, threshold=0.3)
        
        if not candidates_with_scores:
            return text, mapeamento

        # Ordena candidatos por tamanho do termo em inglês decrescente
        # para evitar que substrings menores sejam casadas antes de termos compostos
        # Ex: "neural network" deve ser casada antes de "network"
        candidates = [item[0] for item in candidates_with_scores]
        candidates.sort(key=lambda x: len(x["term_en"]), reverse=True)
        
        processed_text = text
        placeholder_idx = 0
        
        # 2. Varre os termos candidatos no texto usando expressões regulares
        for candidate in candidates:
            term_en = candidate["term_en"].strip()
            term_pt = candidate["term_pt"].strip()
            
            # Escapa caracteres especiais do termo para evitar quebra de regex
            escaped_term = re.escape(term_en)
            
            # Regex case-insensitive com limite de palavra (\b) para casar apenas palavras completas
            pattern = re.compile(rf'\b{escaped_term}\b', re.IGNORECASE)
            
            # Se encontrar o termo no texto processado
            if pattern.search(processed_text):
                placeholder = f"{{{{TERM_{placeholder_idx}}}}}"
                
                # Substitui a palavra mantendo a posição das tags HTML se houver
                # Ex: se o termo estiver dentro de tags <b>, o pattern casa e substitui
                processed_text = pattern.sub(placeholder, processed_text)
                
                mapeamento.append({
                    "placeholder": placeholder,
                    "term_en": term_en,
                    "term_pt": term_pt
                })
                
                placeholder_idx += 1
                
        return processed_text, mapeamento

    def postprocess_chunk(self, translated_text: str, mapeamento: List[Dict[str, str]]) -> str:
        """
        Restaura os termos corretos em português nos respectivos placeholders
        após a tradução do chunk pelo MarianMT.
        """
        if not mapeamento:
            return translated_text
            
        restored_text = translated_text
        
        for item in mapeamento:
            placeholder = item["placeholder"]
            term_pt = item["term_pt"]
            
            # MarianMT pode alterar levemente a formatação do placeholder (ex: acrescentar espaços)
            # como "{{ TERM_0 }}" ou "{ { TERM_0 } }". Usamos uma regex robusta para encontrar variações.
            # Extrai o index numérico do placeholder (ex: TERM_0 -> 0)
            match = re.search(r'\d+', placeholder)
            if not match:
                continue
                
            idx = match.group()
            # Regex flexível para capturar variações do placeholder com ou sem espaços
            flexible_pattern_str = r'\{\{\s*TERM_' + str(idx) + r'\s*\}\}'
            flexible_pattern = re.compile(flexible_pattern_str, re.IGNORECASE)
            
            if flexible_pattern.search(restored_text):
                restored_text = flexible_pattern.sub(term_pt, restored_text)
            else:
                # Caso extremo: se o modelo removeu uma das chaves
                backup_pattern_str = r'\{\s*TERM_' + str(idx) + r'\s*\}'
                backup_pattern = re.compile(backup_pattern_str, re.IGNORECASE)
                if backup_pattern.search(restored_text):
                    restored_text = backup_pattern.sub(term_pt, restored_text)
                else:
                    # Se mesmo assim o placeholder sumiu (caso raro onde o modelo omitiu o token),
                    # apenas adicionamos um log e não podemos restaurar diretamente no lugar correto,
                    # mas deixamos o fluxo seguir.
                    logger.warning(f"Placeholder {placeholder} ({item['term_en']} -> {term_pt}) foi perdido ou corrompido pelo tradutor.")

        return restored_text

# Singleton do substituidor de termos
term_replacer = TermReplacer()
