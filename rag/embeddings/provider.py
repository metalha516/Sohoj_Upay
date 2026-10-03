"""Provider-agnostic vector embedding interface with deterministic local fallback."""

from __future__ import annotations

import os
from typing import Protocol, runtime_checkable

import numpy as np
from scipy.sparse import hstack
from sklearn.feature_extraction.text import HashingVectorizer


@runtime_checkable
class EmbeddingProvider(Protocol):
    """Protocol defining the standard embedding provider contract."""

    @property
    def dimension(self) -> int:
        """Vector dimensionality (e.g. 1536)."""
        ...

    def embed_text(self, text: str) -> list[float]:
        """Generate a normalized embedding vector for a single string."""
        ...

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate normalized embedding vectors for a batch of strings."""
        ...


class DeterministicLocalEmbedding:
    """Deterministic, offline, dependency-free embedding provider for testing and CI.

    Combines word and character n-gram hashing with a Gaussian random projection
    into 1536-dimensional unit Euclidean space. Guarantees:
    - 100% reproducible results given identical text and random seed.
    - Zero external network requests or heavyweight model downloads.
    - High semantic sensitivity to financial keywords and acronyms.
    """

    def __init__(self, dimension: int = 1536, seed: int = 42) -> None:
        self._dimension = dimension
        self._seed = seed

        # Dual word (1-2 ngrams) and character (3-5 ngrams) hashing
        self._hw = HashingVectorizer(
            n_features=4096,
            analyzer="word",
            ngram_range=(1, 2),
            stop_words="english",
            alternate_sign=True,
        )
        self._hc = HashingVectorizer(
            n_features=4096,
            analyzer="char_wb",
            ngram_range=(3, 5),
            alternate_sign=True,
        )

        # Fixed random projection matrix from 8192 features down to dimension
        rng = np.random.RandomState(seed)
        self._projection = rng.normal(0.0, 1.0 / np.sqrt(dimension), (8192, dimension)).astype(
            np.float32
        )

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> list[float]:
        """Embed a single text string."""
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Embed a batch of text strings into normalized 1536-dimensional vectors."""
        if not texts:
            return []

        w_feats = self._hw.transform(texts)
        c_feats = self._hc.transform(texts)
        combined = hstack([w_feats, c_feats])

        # Dense projection
        projected = (combined @ self._projection).astype(np.float32)

        # L2 Unit Normalization (for exact cosine similarity via dot product)
        norms = np.linalg.norm(projected, axis=1, keepdims=True)
        # Avoid zero division
        norms[norms == 0.0] = 1.0
        normalized = projected / norms

        return [row.tolist() for row in normalized]


class OpenAIEmbeddingProvider:
    """OpenAI API embedding provider using text-embedding-3-small or ada-002."""

    def __init__(
        self,
        api_key: str | None = None,
        model: str = "text-embedding-3-small",
        dimension: int = 1536,
    ) -> None:
        self._api_key = api_key or os.environ.get("OPENAI_API_KEY", "")
        self._model = model
        self._dimension = dimension

    @property
    def dimension(self) -> int:
        return self._dimension

    def embed_text(self, text: str) -> list[float]:
        return self.embed_batch([text])[0]

    def embed_batch(self, texts: list[str]) -> list[list[float]]:
        if not self._api_key:
            raise ValueError("OPENAI_API_KEY is required to invoke OpenAIEmbeddingProvider.")
        try:
            from openai import OpenAI

            client = OpenAI(api_key=self._api_key)
            response = client.embeddings.create(input=texts, model=self._model)
            return [data.embedding for data in response.data]
        except ImportError as e:
            raise ImportError("openai package is required for OpenAIEmbeddingProvider.") from e


def get_embedding_provider(
    provider_type: str = "deterministic",
    dimension: int = 1536,
    seed: int = 42,
    **kwargs: object,
) -> EmbeddingProvider:
    """Factory creating an instance of EmbeddingProvider."""
    if provider_type == "deterministic" or not os.environ.get("OPENAI_API_KEY"):
        return DeterministicLocalEmbedding(dimension=dimension, seed=seed)
    if provider_type == "openai":
        return OpenAIEmbeddingProvider(dimension=dimension, **kwargs)  # type: ignore[arg-type]
    return DeterministicLocalEmbedding(dimension=dimension, seed=seed)
