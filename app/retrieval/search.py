import logging
from pathlib import Path

import faiss
import numpy as np

from app.retrieval.embedder import embed_texts
from app.retrieval.indexer import INDEX_PATH, METADATA_PATH


logger = logging.getLogger(__name__)


def search_related_context(query: str, top_k: int = 5) -> str:
    if not Path(INDEX_PATH).exists() or not Path(METADATA_PATH).exists():
        return ""

    index = faiss.read_index(INDEX_PATH)
    metadata = Path(METADATA_PATH).read_text().splitlines()

    if not metadata:
        return ""

    try:
        query_embedding = embed_texts([query])
    except Exception as error:
        logger.warning("Failed to embed retrieval query: %s", error)
        return ""

    query_embedding = np.array(query_embedding).astype("float32")

    _, indices = index.search(query_embedding, min(top_k, len(metadata)))

    sections = []

    for index_id in indices[0]:
        if index_id < 0 or index_id >= len(metadata):
            continue

        file_path = Path(metadata[index_id])

        if not file_path.exists():
            continue

        content = file_path.read_text(errors="ignore")[:3000]

        sections.append(
            f"""
Related File: {file_path}

{content}
"""
        )

    return "\n---\n".join(sections)
