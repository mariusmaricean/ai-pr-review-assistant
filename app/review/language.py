from pathlib import Path


def detect_language(filename: str) -> str:
    suffix = Path(filename).suffix.lower()

    mapping = {
        ".py": "python",
        ".js": "javascript",
        ".ts": "typescript",
        ".tsx": "typescript-react",
        ".jsx": "javascript-react",
        ".sql": "sql",
        ".yml": "yaml",
        ".yaml": "yaml",
        ".json": "json",
        ".tf": "terraform",
        ".dockerfile": "docker",
    }

    if filename.lower().endswith("dockerfile"):
        return "docker"

    return mapping.get(suffix, "generic")
