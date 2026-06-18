import os
import re
import threading
import torch
import logging
from typing import List
from transformers import MarianMTModel, MarianTokenizer
from app.config import settings

logger = logging.getLogger(__name__)

class MarianTranslator:
    def __init__(self):
        self.model_name = settings.MARIAN_MODEL_NAME
        self.cache_dir = settings.MODEL_CACHE_DIR
        self.model = None
        self.tokenizer = None
        self.device = "cpu"
        self._lock = threading.Lock()
        self._load_lock = threading.Lock()

    def load_model(self) -> None:
        """Carrega o modelo MarianMT e Tokenizer em memória (Lazy loading)."""
        if self.model is not None and self.tokenizer is not None:
            return

        with self._load_lock:
            # Double-checked locking
            if self.model is not None and self.tokenizer is not None:
                return

            logger.info(f"Iniciando carregamento do modelo de tradução: {self.model_name}")
            
            # Cria diretório de cache se não existir
            os.makedirs(self.cache_dir, exist_ok=True)
            
            try:
                # Detectar dispositivo ideal: CUDA -> MPS (Apple Silicon) -> CPU
                if torch.cuda.is_available():
                    self.device = "cuda"
                elif hasattr(torch.backends, "mps") and torch.backends.mps.is_available():
                    # Nota: Em alguns ambientes mais antigos, mps pode ter bugs com MarianMT. 
                    # Mas é o padrão recomendado para aceleração em Apple Silicon.
                    self.device = "mps"
                else:
                    self.device = "cpu"
                    
                logger.info(f"Dispositivo selecionado para tradução local: {self.device}")
                
                # Carrega tokenizer e modelo
                self.tokenizer = MarianTokenizer.from_pretrained(
                    self.model_name,
                    cache_dir=self.cache_dir
                )
                self.model = MarianMTModel.from_pretrained(
                    self.model_name,
                    cache_dir=self.cache_dir
                ).to(self.device)
                
                logger.info("Modelo de tradução local carregado com sucesso.")
            except Exception as e:
                logger.error(f"Falha crítica ao carregar o modelo MarianMT: {str(e)}", exc_info=True)
                raise RuntimeError(f"Não foi possível carregar o modelo de tradução local: {str(e)}")

    def translate(self, texts: List[str]) -> List[str]:
        """
        Traduz uma lista de textos do inglês para o português de forma síncrona.
        Toma cuidado com o carregamento do modelo.
        """
        if not texts:
            return []
            
        self.load_model()
        
        try:
            # Tokenização das entradas
            # padding=True garante que todas as sentenças tenham o mesmo comprimento no lote
            inputs = self.tokenizer(
                texts, 
                return_tensors="pt", 
                padding=True, 
                truncation=True, 
                max_length=512
            ).to(self.device)
            
            # Geração da tradução sem cálculo de gradientes com trava de segurança de thread
            with self._lock:
                with torch.no_grad():
                    translated_tokens = self.model.generate(**inputs)
                
            # Decodificação das saídas de tokens para strings legíveis
            decoded_translations = self.tokenizer.batch_decode(
                translated_tokens, 
                skip_special_tokens=True
            )
            
            # Sanitização simples para remover eventuais tags indesejadas introduzidas pelo modelo
            # (Helsinki-NLP às vezes pode repetir a tag de idioma na saída, removemos se necessário)
            cleaned_translations = []
            for t in decoded_translations:
                # Remove artefatos de saída como ">>pt_br<<"
                cleaned = re.sub(r'^>>[a-z_]+<<\s*', '', t)
                cleaned_translations.append(cleaned)
                
            return cleaned_translations
            
        except Exception as e:
            logger.error(f"Erro durante a tradução local: {str(e)}")
            raise e

# Singleton do tradutor
translator = MarianTranslator()
