"""
Genre Embedding Model

Builds low-dimensional genre vectors from album co-occurrence data + a hand-curated
taxonomy seed. Replaces exact-match Jaccard similarity with cosine similarity on
averaged album genre vectors, capturing semantic relationships like hip-hop ≈ rap.

Pipeline: co-occurrence matrix → taxonomy injection → PPMI → TruncatedSVD → L2-normalize
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD

logger = logging.getLogger(__name__)

# Hand-curated genre groups. Each group's genres are injected as synthetic
# co-occurrences so the model knows "hip-hop" and "rap" are near-synonyms
# even if they never appear on the same album in our catalog.
GENRE_TAXONOMY_SEED: list[list[str]] = [
    ["hip-hop", "rap", "trap", "hip hop"],
    ["rock", "indie rock", "alternative rock", "alt-rock", "garage rock"],
    ["r&b", "soul", "neo-soul", "rhythm and blues", "rnb"],
    ["electronic", "electronica", "edm", "house", "techno", "synth"],
    ["pop", "synth-pop", "synthpop", "electropop", "art pop", "indie pop"],
    ["jazz", "bebop", "free jazz", "jazz fusion", "smooth jazz"],
    ["metal", "heavy metal", "death metal", "black metal", "thrash metal", "doom metal"],
    ["punk", "punk rock", "post-punk", "hardcore", "hardcore punk"],
    ["folk", "indie folk", "folk rock", "acoustic", "singer-songwriter"],
    ["country", "alt-country", "americana", "country rock"],
    ["classical", "orchestral", "chamber music", "contemporary classical"],
    ["ambient", "drone", "shoegaze", "dream pop", "post-rock"],
    ["reggae", "dub", "dancehall", "ska"],
    ["blues", "delta blues", "electric blues", "blues rock"],
    ["latin", "bossa nova", "salsa", "reggaeton", "latin pop"],
    ["funk", "disco", "boogie"],
    ["experimental", "avant-garde", "noise", "art rock", "progressive rock"],
    ["gospel", "christian", "worship"],
]

TAXONOMY_INJECTION_WEIGHT = 3.0


def _parse_genre_list(genres_csv: str | None) -> list[str]:
    """Parse comma-separated genre string into list of lowercase genres."""
    if not genres_csv:
        return []
    return [g.strip().lower() for g in genres_csv.split(",") if g.strip()]


def build_genre_embeddings(
    album_genre_lists: list[list[str]],
    n_dims: int = 16,
) -> GenreEmbeddingModel:
    """
    Build genre embedding vectors from album genre co-occurrence data.

    Args:
        album_genre_lists: List of genre lists, one per album.
        n_dims: Embedding dimensionality.

    Returns:
        A GenreEmbeddingModel with L2-normalized vectors for each genre.
    """
    # 1. Build vocab from data + taxonomy
    vocab: dict[str, int] = {}
    for genres in album_genre_lists:
        for g in genres:
            if g not in vocab:
                vocab[g] = len(vocab)
    for group in GENRE_TAXONOMY_SEED:
        for g in group:
            if g not in vocab:
                vocab[g] = len(vocab)

    n = len(vocab)
    if n == 0:
        logger.warning("No genres found, returning empty embedding model")
        return GenreEmbeddingModel(vectors={}, vocab=[], n_dims=n_dims)

    # 2. Co-occurrence matrix from album genre lists
    cooc = np.zeros((n, n), dtype=np.float64)
    for genres in album_genre_lists:
        idxs = [vocab[g] for g in genres if g in vocab]
        for i, a in enumerate(idxs):
            for b in idxs[i + 1 :]:
                cooc[a, b] += 1.0
                cooc[b, a] += 1.0

    # 3. Inject taxonomy pairs
    for group in GENRE_TAXONOMY_SEED:
        group_idxs = [vocab[g] for g in group if g in vocab]
        for i, a in enumerate(group_idxs):
            for b in group_idxs[i + 1 :]:
                cooc[a, b] += TAXONOMY_INJECTION_WEIGHT
                cooc[b, a] += TAXONOMY_INJECTION_WEIGHT

    # 4. PPMI transform
    total = cooc.sum()
    if total == 0:
        logger.warning("Zero co-occurrence total, returning empty model")
        return GenreEmbeddingModel(vectors={}, vocab=[], n_dims=n_dims)

    row_sums = cooc.sum(axis=1, keepdims=True)
    col_sums = cooc.sum(axis=0, keepdims=True)

    # Avoid division by zero
    with np.errstate(divide="ignore", invalid="ignore"):
        pmi = np.log2((cooc * total) / (row_sums * col_sums))
    pmi = np.nan_to_num(pmi, nan=0.0, posinf=0.0, neginf=0.0)
    ppmi = np.maximum(pmi, 0.0)

    # 5. TruncatedSVD
    actual_dims = min(n_dims, n - 1) if n > 1 else 1
    if actual_dims < 1:
        logger.warning("Too few genres for SVD, returning empty model")
        return GenreEmbeddingModel(vectors={}, vocab=[], n_dims=n_dims)

    svd = TruncatedSVD(n_components=actual_dims, random_state=42)
    embeddings = svd.fit_transform(csr_matrix(ppmi))

    # 6. L2-normalize
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    embeddings = embeddings / norms

    # Build index
    idx_to_genre = {idx: genre for genre, idx in vocab.items()}
    vectors = {idx_to_genre[i]: embeddings[i].tolist() for i in range(n)}

    logger.info(
        f"Built genre embeddings: {n} genres, {actual_dims} dims, "
        f"explained variance: {svd.explained_variance_ratio_.sum():.2%}"
    )

    return GenreEmbeddingModel(vectors=vectors, vocab=list(vocab.keys()), n_dims=actual_dims)


@dataclass
class GenreEmbeddingModel:
    """Trained genre embedding model with lookup and similarity methods."""

    vectors: dict[str, list[float]] = field(default_factory=dict)
    vocab: list[str] = field(default_factory=list)
    n_dims: int = 16

    def get_vector(self, genre: str) -> np.ndarray | None:
        """
        Get embedding vector for a genre.

        Falls back to token-average for unseen genres (e.g., "indie hip-hop"
        averages "indie" and "hip-hop" vectors if both exist).
        """
        genre = genre.strip().lower()

        # Exact match
        if genre in self.vectors:
            return np.array(self.vectors[genre])

        # Token-average fallback
        tokens = genre.replace("-", " ").split()
        vecs = [np.array(self.vectors[t]) for t in tokens if t in self.vectors]
        if vecs:
            avg = np.mean(vecs, axis=0)
            norm = np.linalg.norm(avg)
            return avg / norm if norm > 0 else avg

        return None

    def album_vector(self, genres_csv: str | None) -> np.ndarray | None:
        """Compute mean embedding vector for an album's genres."""
        genres = _parse_genre_list(genres_csv)
        if not genres:
            return None

        vecs = [self.get_vector(g) for g in genres]
        vecs = [v for v in vecs if v is not None]
        if not vecs:
            return None

        avg = np.mean(vecs, axis=0)
        norm = np.linalg.norm(avg)
        return avg / norm if norm > 0 else avg

    def similarity(self, vec_a: np.ndarray, vec_b: np.ndarray) -> float:
        """Cosine similarity between two vectors (already L2-normalized)."""
        return float(np.dot(vec_a, vec_b))

    def to_dict(self) -> dict:
        """Serialize for Redis/JSON storage."""
        return {
            "vectors": self.vectors,
            "vocab": self.vocab,
            "n_dims": self.n_dims,
        }

    @classmethod
    def from_dict(cls, data: dict) -> GenreEmbeddingModel:
        """Deserialize from Redis/JSON storage."""
        return cls(
            vectors=data.get("vectors", {}),
            vocab=data.get("vocab", []),
            n_dims=data.get("n_dims", 16),
        )
