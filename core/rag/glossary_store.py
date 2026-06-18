import os
import faiss
import numpy as np
import logging
from typing import List, Dict, Tuple, Optional
from sentence_transformers import SentenceTransformer
from app.config import settings

logger = logging.getLogger(__name__)

class GlossaryStore:
    def __init__(self):
        self.model_name = settings.EMBEDDING_MODEL_NAME
        self.cache_dir = settings.MODEL_CACHE_DIR
        self.model = None
        self.index = None
        # Lista contendo os dicionários de termos carregados correspondentes às linhas do FAISS
        # Cada item: {"term_en": "...", "term_pt": "...", "domain": "..."}
        self.terms: List[Dict[str, str]] = []

    def _load_model(self):
        """Lazy loader para o modelo sentence-transformers."""
        if self.model is None:
            logger.info(f"Carregando modelo de embeddings: {self.model_name}")
            try:
                self.model = SentenceTransformer(
                    self.model_name,
                    cache_folder=self.cache_dir
                )
                logger.info("Modelo de embeddings carregado com sucesso.")
            except Exception as e:
                logger.error(f"Erro ao carregar modelo de embeddings: {str(e)}")
                raise e

    def build_index(self, terms: List[Dict[str, str]]) -> None:
        """
        Recebe uma lista de dicionários de termos e reconstrói o índice FAISS na memória.
        """
        if not terms:
            logger.warning("Nenhum termo fornecido para construir o índice do glossário.")
            self.terms = []
            self.index = None
            return

        self._load_model()
        logger.info(f"Construindo índice FAISS com {len(terms)} termos.")
        
        # Extrai os textos em inglês para gerar embeddings
        texts = [t["term_en"].lower().strip() for t in terms]
        
        # Gera embeddings em float32
        embeddings = self.model.encode(texts, convert_to_numpy=True).astype('float32')
        
        # Normalização L2 para busca por produto interno (equivalente à similaridade de cosseno)
        faiss.normalize_L2(embeddings)
        
        dimension = embeddings.shape[1]
        
        # Cria o índice FAISS
        index = faiss.IndexFlatIP(dimension)
        index.add(embeddings)
        
        self.index = index
        self.terms = terms
        logger.info("Índice FAISS reconstruído com sucesso na memória.")

    def save_index(self, directory_path: str) -> None:
        """Salva o índice FAISS e a lista de termos estruturada em disco."""
        if self.index is None:
            logger.warning("Nenhum índice ativo para ser salvo.")
            return

        os.makedirs(directory_path, exist_ok=True)
        index_file = os.path.join(directory_path, "faiss.index")
        terms_file = os.path.join(directory_path, "terms.json")
        
        # Grava o índice FAISS
        faiss.write_index(self.index, index_file)
        
        # Grava a lista de termos mapeada
        import json
        with open(terms_file, "w", encoding="utf-8") as f:
            json.dump(self.terms, f, ensure_ascii=False, indent=2)
            
        logger.info(f"Índice do glossário persistido em: {directory_path}")

    def load_index(self, directory_path: str) -> bool:
        """Carrega o índice FAISS e termos salvos em disco."""
        index_file = os.path.join(directory_path, "faiss.index")
        terms_file = os.path.join(directory_path, "terms.json")
        
        if not os.path.exists(index_file) or not os.path.exists(terms_file):
            logger.info("Índice do glossário não encontrado em disco.")
            return False
            
        try:
            self.index = faiss.read_index(index_file)
            
            import json
            with open(terms_file, "r", encoding="utf-8") as f:
                self.terms = json.load(f)
                
            logger.info(f"Índice do glossário carregado do disco com {len(self.terms)} termos.")
            return True
        except Exception as e:
            logger.error(f"Erro ao carregar o índice do glossário: {str(e)}")
            return False

    def search(self, query: str, k: int = 3, threshold: float = 0.5) -> List[Tuple[Dict[str, str], float]]:
        """
        Busca termos semelhantes no glossário.
        Retorna uma lista de tuplas contendo (termo, score_similaridade).
        """
        if self.index is None or not self.terms:
            return []

        self._load_model()
        
        # Prepara a query
        query_vector = self.model.encode([query.lower().strip()], convert_to_numpy=True).astype('float32')
        faiss.normalize_L2(query_vector)
        
        # Busca os k mais próximos
        scores, indices = self.index.search(query_vector, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            # FAISS retorna -1 para resultados não encontrados
            if idx != -1 and score >= threshold:
                results.append((self.terms[idx], float(score)))
                
        return results

# Singleton de GlossaryStore
glossary_store = GlossaryStore()
