"""Generate text embeddings via Gemini gemini-embedding-001."""

from google import genai
from google.genai import types

from .config import GEMINI_API_KEY

EMBEDDING_MODEL = "gemini-embedding-001"
MAX_BATCH_SIZE = 100  # Gemini API limit per request
TASK_TYPES = (
    "SEMANTIC_SIMILARITY",
    "CLASSIFICATION",
    "CLUSTERING",
    "RETRIEVAL_DOCUMENT",
    "RETRIEVAL_QUERY",
    "CODE_RETRIEVAL_QUERY",
    "QUESTION_ANSWERING",
    "FACT_VERIFICATION",
)


def create_embeddings(
    texts: str | list[str],
    task_type: str = "RETRIEVAL_DOCUMENT",
    output_dimensionality: int = 3072,
    normalize: bool | None = None,
) -> dict:
    """Generate embeddings for text(s) using gemini-embedding-001."""
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY not set in .env")

    if task_type not in TASK_TYPES:
        raise ValueError(f"task_type must be one of {TASK_TYPES}")

    if isinstance(texts, str):
        texts = [texts]
    if not texts:
        raise ValueError("texts cannot be empty")

    if normalize is None:
        normalize = output_dimensionality < 3072

    client = genai.Client(api_key=GEMINI_API_KEY)
    config = types.EmbedContentConfig(
        task_type=task_type,
        output_dimensionality=output_dimensionality,
    )

    embeddings = []
    for i in range(0, len(texts), MAX_BATCH_SIZE):
        batch = texts[i : i + MAX_BATCH_SIZE]
        result = client.models.embed_content(
            model=EMBEDDING_MODEL,
            contents=batch,
            config=config,
        )
        for emb in result.embeddings:
            values = list(emb.values) if hasattr(emb, "values") else list(emb)
            if normalize and output_dimensionality < 3072:
                import numpy as np

                arr = np.array(values, dtype=float)
                norm = np.linalg.norm(arr)
                if norm > 0:
                    arr = arr / norm
                values = arr.tolist()
            embeddings.append(values)

    return {
        "embeddings": embeddings,
        "dimensions": len(embeddings[0]) if embeddings else 0,
        "count": len(embeddings),
    }
