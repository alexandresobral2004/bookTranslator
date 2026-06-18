#!/usr/bin/env python
import os
import sys
import logging

# Adiciona o diretório raiz ao PYTHONPATH para poder importar módulos do core/app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Inicializa logs
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("rebuild_index")

from core.rag.glossary_loader import load_glossary_csv
from core.rag.glossary_store import glossary_store
from app.config import settings

def main():
    logger.info("=== BookTranslator: Reconstruindo Índice do Glossário ===")
    
    csv_path = os.path.join(settings.GLOSSARY_DIR, settings.GLOSSARY_FILE_NAME)
    index_dir = os.path.join(settings.GLOSSARY_DIR, settings.GLOSSARY_INDEX_DIR)
    
    if not os.path.exists(csv_path):
        logger.error(f"Erro: O arquivo de glossário não existe em {csv_path}")
        sys.exit(1)
        
    logger.info(f"Lendo termos de {csv_path}...")
    terms = load_glossary_csv(csv_path)
    
    if not terms:
        logger.warning("O arquivo de glossário está vazio ou não possui registros válidos.")
        sys.exit(0)
        
    logger.info(f"Gerando embeddings e construindo índice FAISS com {len(terms)} termos...")
    try:
        # Reconstrói
        glossary_store.build_index(terms)
        # Salva em disco
        glossary_store.save_index(index_dir)
        logger.info(f"Sucesso! Índice atualizado e salvo em: {index_dir}")
    except Exception as e:
        logger.error(f"Erro crítico durante a compilação do índice: {str(e)}", exc_info=True)
        sys.exit(1)

if __name__ == "__main__":
    main()
