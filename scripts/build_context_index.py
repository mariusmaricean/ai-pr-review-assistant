import sys
from pathlib import Path


def main():
    root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(root))

    from app.retrieval.indexer import build_index

    result = build_index(".")
    print(result)


if __name__ == "__main__":
    main()
