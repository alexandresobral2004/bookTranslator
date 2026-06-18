import os
import csv
import logging
from typing import List, Dict
from app.config import settings
from core.rag.glossary_store import glossary_store

logger = logging.getLogger(__name__)

def load_glossary_csv(file_path: str) -> List[Dict[str, str]]:
    """Lê o glossário do arquivo CSV e retorna como lista de dicionários."""
    terms: List[Dict[str, str]] = []
    
    if not os.path.exists(file_path):
        logger.warning(f"Arquivo de glossário CSV não encontrado em: {file_path}")
        return terms
        
    try:
        with open(file_path, mode="r", encoding="utf-8") as f:
            reader = csv.DictReader(f)
            # Valida as colunas obrigatórias
            if not reader.fieldnames or "term_en" not in reader.fieldnames or "term_pt" not in reader.fieldnames:
                logger.error(f"Formato inválido de cabeçalhos no CSV de glossário. Esperado: term_en, term_pt")
                return terms
                
            for row in reader:
                term_en = row.get("term_en", "").strip()
                term_pt = row.get("term_pt", "").strip()
                domain = row.get("domain", "general").strip()
                
                if term_en and term_pt:
                    terms.append({
                        "term_en": term_en,
                        "term_pt": term_pt,
                        "domain": domain
                    })
        logger.info(f"Carregados {len(terms)} termos do CSV: {file_path}")
    except Exception as e:
        logger.error(f"Erro ao ler CSV de glossário: {str(e)}")
        
    return terms

def initialize_glossary() -> None:
    """
    Inicializa o glossário. Tenta carregar o índice FAISS pré-construído em disco.
    Se não existir, carrega do CSV, reconstrói o índice e o salva em disco.
    """
    glossary_dir = settings.GLOSSARY_DIR
    csv_path = os.path.join(glossary_dir, settings.GLOSSARY_FILE_NAME)
    index_dir = os.path.join(glossary_dir, settings.GLOSSARY_INDEX_DIR)
    
    # 1. Tenta carregar o índice salvo em disco
    if glossary_store.load_index(index_dir):
        logger.info("Glossário inicializado a partir do índice salvo em disco.")
        return
        
    # 2. Se falhar, reconstrói do CSV
    logger.info("Índice em disco indisponível. Reconstruindo a partir do CSV...")
    
    # Garante que a pasta exista
    os.makedirs(glossary_dir, exist_ok=True)
    
    # Se o CSV não existir, criamos um arquivo vazio
    if not os.path.exists(csv_path):
        with open(csv_path, "w", encoding="utf-8", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["term_en", "term_pt", "domain"])
        logger.info(f"Criado arquivo CSV de glossário vazio em: {csv_path}")
        
    terms = load_glossary_csv(csv_path)
    if terms:
        try:
            glossary_store.build_index(terms)
            glossary_store.save_index(index_dir)
            logger.info("Índice do glossário construído e persistido com sucesso.")
        except Exception as e:
            logger.error(f"Falha ao construir e salvar o índice do glossário: {str(e)}")
    else:
        logger.info("Glossário está vazio. Pronto para receber adições.")
