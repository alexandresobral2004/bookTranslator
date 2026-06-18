import pytest
from unittest.mock import MagicMock, patch
from core.extractor.page_model import Page, Block, TextSpan
from core.chunker.text_chunker import Chunker
from core.translator.quality_scorer import QualityScorer
from core.rag.term_replacer import TermReplacer

# ==============================================================================
# 1. Testes do Segmentador (Chunker)
# ==============================================================================
def test_block_to_html_text():
    chunker_inst = Chunker()
    block = Block(
        block_type="text",
        bbox=(0, 0, 100, 100),
        spans=[
            TextSpan(text="Hello ", font_name="Arial", size=12, bold=False, italic=False, color=0),
            TextSpan(text="world", font_name="Arial", size=12, bold=True, italic=False, color=0),
            TextSpan(text=" in ", font_name="Arial", size=12, bold=False, italic=False, color=0),
            TextSpan(text="italics", font_name="Arial", size=12, bold=False, italic=True, color=0),
        ]
    )
    
    html = chunker_inst.block_to_html_text(block)
    assert html == "Hello <b>world</b> in <i>italics</i>"

def test_split_sentences():
    chunker_inst = Chunker()
    text = "This is sentence one. And sentence two! Is this three?"
    sentences = chunker_inst.split_sentences(text)
    assert len(sentences) == 3
    assert sentences[0] == "This is sentence one."
    assert sentences[1] == "And sentence two!"
    assert sentences[2] == "Is this three?"

# ==============================================================================
# 2. Testes de Avaliação de Qualidade
# ==============================================================================
def test_evaluate_quality_perfect():
    scorer = QualityScorer()
    # Tradução correta deve ter score alto
    score = scorer.evaluate_quality(
        original_en="The cat is on the table.",
        translated_pt="O gato está em cima da mesa."
    )
    assert score > 0.8

def test_evaluate_quality_repetition():
    scorer = QualityScorer()
    # Tradução com loopings bizarros deve ser penalizada
    score = scorer.evaluate_quality(
        original_en="Deep learning is a subset of machine learning.",
        translated_pt="Aprendizado profundo é um o que o que o que o que"
    )
    assert score < 0.5

def test_evaluate_quality_empty():
    scorer = QualityScorer()
    assert scorer.evaluate_quality("Original", "") == 0.0
    assert scorer.evaluate_quality("", "") == 1.0

# ==============================================================================
# 3. Testes do Substituidor de Termos (TermReplacer)
# ==============================================================================
@patch('core.rag.term_replacer.glossary_store')
def test_term_replacer_preprocess(mock_store):
    # Mock de busca no FAISS retornando um termo candidato
    mock_store.search.return_value = [
        ({"term_en": "neural network", "term_pt": "rede neural", "domain": "ml"}, 0.9)
    ]
    
    replacer = TermReplacer()
    text = "We built a deep neural network from scratch."
    
    processed_text, mapping = replacer.preprocess_chunk(text)
    
    # Deve substituir "neural network" pelo placeholder
    assert "{{TERM_0}}" in processed_text
    assert len(mapping) == 1
    assert mapping[0]["term_en"] == "neural network"
    assert mapping[0]["term_pt"] == "rede neural"

def test_term_replacer_postprocess():
    replacer = TermReplacer()
    translated_with_placeholders = "Nós criamos uma {{ TERM_0 }} profunda."
    mapping = [{
        "placeholder": "{{TERM_0}}",
        "term_en": "neural network",
        "term_pt": "rede neural"
    }]
    
    restored = replacer.postprocess_chunk(translated_with_placeholders, mapping)
    assert "rede neural" in restored
    assert "{{ TERM_0 }}" not in restored
