import re
import logging
from typing import List

logger = logging.getLogger(__name__)

class QualityScorer:
    def calculate_repetition_penalty(self, text: str) -> float:
        """
        Calcula uma penalidade se houver repetições excessivas de palavras ou caracteres.
        Loopings são um problema conhecido de modelos NMT (como MarianMT).
        """
        words = text.lower().split()
        if not words:
            return 0.0
            
        # Detecta repetições consecutivas de 3 ou mais palavras idênticas
        consecutive_repeats = 0
        for i in range(len(words) - 2):
            if words[i] == words[i+1] == words[i+2]:
                consecutive_repeats += 1
                
        # Detecta loopings longos (ex: "o que o que o que")
        phrase_repeats = 0
        text_clean = re.sub(r'[^\w\s]', '', text.lower())
        for length in range(3, 10):  # tamanho do padrão de 3 a 9 palavras
            patterns = re.findall(rf'(\b.+\b)(?:\s+\1){{2,}}', text_clean)
            phrase_repeats += len(patterns)
            
        penalty = (consecutive_repeats * 0.2) + (phrase_repeats * 0.3)
        return min(penalty, 0.8)  # Limita a penalidade máxima a 0.8

    def evaluate_quality(self, original_en: str, translated_pt: str) -> float:
        """
        Avalia a qualidade de um chunk traduzido e retorna um score de 0.0 a 1.0.
        Usa heurísticas baseadas em razão de comprimento, artefatos e repetições consecutivas.
        """
        # Limpa espaços e tags HTML básicas para comparação de comprimento
        orig_clean = re.sub(r'<[^>]+>', '', original_en).strip()
        trans_clean = re.sub(r'<[^>]+>', '', translated_pt).strip()
        
        if not orig_clean:
            return 1.0  # Se o original for vazio, está correto
            
        if not trans_clean:
            return 0.0  # Se a tradução for vazia mas o original não, score zero

        score = 1.0
        
        # 1. Razão de comprimento (Português é em média 15% a 30% mais longo que Inglês)
        len_orig = len(orig_clean)
        len_trans = len(trans_clean)
        ratio = len_trans / len_orig
        
        if ratio < 0.5:
            # Muito curta (pode ser perda de informação)
            score -= (0.5 - ratio) * 1.5
        elif ratio > 2.2:
            # Muito longa (pode ser alucinação ou looping)
            score -= (ratio - 2.2) * 0.5
            
        # 2. Presença de tokens desconhecidos (ex: <unk>)
        if "<unk>" in translated_pt.lower():
            score -= 0.4
            
        # 3. Penalidade de looping e repetição
        repetition_penalty = self.calculate_repetition_penalty(trans_clean)
        score -= repetition_penalty

        # Garante que o score fique entre 0.0 e 1.0
        final_score = max(min(score, 1.0), 0.0)
        
        logger.debug(
            f"Avaliação de qualidade - Ratio: {ratio:.2f}, "
            f"Repetitions penalty: {repetition_penalty:.2f}, Score final: {final_score:.2f}"
        )
        return final_score

# Singleton do avaliador
quality_scorer = QualityScorer()
