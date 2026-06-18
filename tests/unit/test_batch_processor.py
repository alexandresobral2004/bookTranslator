import pytest
import asyncio
from unittest.mock import MagicMock, patch
from core.translator.batch_processor import translate_chunks_batched
from app.config import settings

@pytest.mark.asyncio
async def test_translate_chunks_batched_success():
    # Mock settings batch size and workers
    with patch.object(settings, 'BATCH_SIZE', 2), \
         patch.object(settings, 'TRANSLATION_WORKERS', 2):
        
        call_count = 0
        def mock_translate(batch):
            nonlocal call_count
            call_count += 1
            return [f"pt_{text}" for text in batch]
            
        with patch('core.translator.batch_processor.translator.translate', side_effect=mock_translate) as mock_t:
            chunks = ["one", "two", "three", "four", "five"]
            
            progress_calls = []
            async def progress_cb(processed, total):
                progress_calls.append((processed, total))
                
            results = await translate_chunks_batched(chunks, progress_callback=progress_cb)
            
            assert results == ["pt_one", "pt_two", "pt_three", "pt_four", "pt_five"]
            assert mock_t.call_count == 3
            assert len(progress_calls) == 3
            assert progress_calls[-1] == (5, 5)

@pytest.mark.asyncio
async def test_translate_chunks_batched_fallback():
    # Mock settings batch size and workers
    with patch.object(settings, 'BATCH_SIZE', 2), \
         patch.object(settings, 'TRANSLATION_WORKERS', 2):
        
        def mock_translate(batch):
            if "three" in batch or "four" in batch:
                raise RuntimeError("Mock batch error")
            return [f"pt_{text}" for text in batch]
            
        with patch('core.translator.batch_processor.translator.translate', side_effect=mock_translate):
            chunks = ["one", "two", "three", "four", "five"]
            
            progress_calls = []
            async def progress_cb(processed, total):
                progress_calls.append((processed, total))
                
            results = await translate_chunks_batched(chunks, progress_callback=progress_cb)
            
            assert results == ["pt_one", "pt_two", "three", "four", "pt_five"]
            assert progress_calls[-1] == (5, 5)
