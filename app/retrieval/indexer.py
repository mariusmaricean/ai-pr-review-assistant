from pathlib import Path

import faiss
import numpy as np

from app.retrieval.embedder import embed_texts


INDEX_PATH = "repo_context.index"
METADATA_PATH = "repo_context_files.txt"

SUPPORTED_EXTENSIONS = {
    ".py",
    ".md",
    ".txt",
    ".yml",
    ".yaml",
    ".json",
    ".ts",
    ".js",
}

IGNORED_PARTS = {
    ".git",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    ".venv",
    "__pycache__",
}


def collect_repo_files(root: str = ".") -> list[Path]:
    files = []

    for path in Path(root).rglob("*"):
        if any(part in IGNORED_PARTS for part in path.parts):
            continue

        if path.name in {INDEX_PATH, METADATA_PATH}:
            continue

        if path.is_file() and path.suffix.lower() in SUPPORTED_EXTENSIONS:
            files.append(path)

    return files


def build_index(root: str = "."):
    files = collect_repo_files(root)

    texts = []
    metadata = []

    for file_path in files:
        try:
            text = file_path.read_text(errors="ignore")
        except Exception:
            continue

        if not text.strip():
            continue

        texts.append(text[:4000])
        metadata.append(str(file_path))

    if not texts:
        Path(METADATA_PATH).write_text("")
        return {
            "indexed_files": 0,
        }

    embeddings = embed_texts(texts)
    embeddings = np.array(embeddings).astype("float32")

    index = faiss.IndexFlatIP(embeddings.shape[1])
    index.add(embeddings)

    faiss.write_index(index, INDEX_PATH)

    Path(METADATA_PATH).write_text("\n".join(metadata))

    return {
        "indexed_files": len(metadata),
    }
