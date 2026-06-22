import re

from src.providers.base import ProviderResult


class ConfidenceService:
    def evaluate(self, result: ProviderResult) -> float:
        text = result.text.strip()
        if not text:
            return 0.0
        characters = [character for character in text if not character.isspace()]
        readable = sum(
            character.isalnum() or character in ".,:;!?@%/()-_" for character in characters
        )
        readability = readable / max(1, len(characters))
        tokens = re.findall(r"\w+", text, flags=re.UNICODE)
        token_score = min(1.0, len(tokens) / 20)
        score = 0.7 * result.confidence + 0.2 * readability + 0.1 * token_score
        return round(max(0.0, min(1.0, score)), 4)
