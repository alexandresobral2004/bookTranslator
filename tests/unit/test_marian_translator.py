import pytest
import threading
import time
from unittest.mock import MagicMock, patch
from core.translator.marian_translator import MarianTranslator

def test_marian_translator_concurrent_load():
    translator = MarianTranslator()
    
    # Counter to track how many times the real loading actually occurred
    load_count = 0
    
    def mock_from_pretrained(*args, **kwargs):
        nonlocal load_count
        # Simulate slight delay during model loading to expose potential race conditions
        time.sleep(0.1)
        load_count += 1
        return MagicMock()

    with patch('core.translator.marian_translator.MarianTokenizer.from_pretrained', side_effect=mock_from_pretrained), \
         patch('core.translator.marian_translator.MarianMTModel.from_pretrained', side_effect=mock_from_pretrained):
         
        threads = []
        # Create 5 concurrent threads attempting to load the model simultaneously
        for _ in range(5):
            t = threading.Thread(target=translator.load_model)
            threads.append(t)
            
        for t in threads:
            t.start()
            
        for t in threads:
            t.join()
            
        # tokenizer.from_pretrained and model.from_pretrained should each be called exactly once
        # because of the thread-safe double-checked lock pattern.
        assert load_count == 2
        assert translator.model is not None
        assert translator.tokenizer is not None
