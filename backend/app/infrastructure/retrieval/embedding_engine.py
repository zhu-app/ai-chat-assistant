import math
import re
from collections import Counter

from app.core.config import settings as app_settings

if app_settings.openai_api_key:
    from langchain_openai import OpenAIEmbeddings


class EmbeddingEngine:
    def __init__(self) -> None:
        self.has_remote_embedding = bool(app_settings.openai_api_key)
        self.embedding_dimensions = app_settings.rag_embedding_dimensions
        self.client = None
        if self.has_remote_embedding:
            self.client = OpenAIEmbeddings(
                api_key=app_settings.openai_api_key,
                base_url=app_settings.openai_base_url,
                model=app_settings.rag_embedding_model,
            )

    @staticmethod
    def _normalize(text: str) -> str:
        return re.sub(r'\s+', ' ', text).strip().lower()

    @classmethod
    def _tokenize(cls, text: str) -> list[str]:
        normalized = cls._normalize(text)
        english_terms = re.findall(r'[a-z0-9_\-]{2,}', normalized)
        cjk_chars = re.findall(r'[\u4e00-\u9fff]', normalized)
        compact_cjk = ''.join(cjk_chars)
        cjk_terms = [compact_cjk] if compact_cjk else []
        cjk_terms.extend(compact_cjk[index : index + 2] for index in range(max(len(compact_cjk) - 1, 0)))
        return [token for token in [*english_terms, *cjk_terms] if token]

    def _hash_embed(self, text: str) -> list[float]:
        vector = [0.0] * self.embedding_dimensions
        counts = Counter(self._tokenize(text))
        if not counts:
            return vector

        for token, count in counts.items():
            slot = sum(ord(char) for char in token) % self.embedding_dimensions
            vector[slot] += float(count)

        norm = math.sqrt(sum(value * value for value in vector)) or 1.0
        return [value / norm for value in vector]

    def embed_documents(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        if self.client:
            try:
                return [list(map(float, vector)) for vector in self.client.embed_documents(texts)]
            except Exception:
                pass
        return [self._hash_embed(text) for text in texts]

    def embed_query(self, text: str) -> list[float]:
        if self.client:
            try:
                return list(map(float, self.client.embed_query(text)))
            except Exception:
                pass
        return self._hash_embed(text)

    @staticmethod
    def cosine_similarity(left: list[float], right: list[float]) -> float:
        if not left or not right or len(left) != len(right):
            return 0.0
        numerator = sum(a * b for a, b in zip(left, right))
        left_norm = math.sqrt(sum(value * value for value in left)) or 1.0
        right_norm = math.sqrt(sum(value * value for value in right)) or 1.0
        return numerator / (left_norm * right_norm)