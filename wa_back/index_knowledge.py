from pathlib import Path

from database import create_db_and_tables
from rag.rag_service import index_file


def main() -> None:
    create_db_and_tables()
    knowledge_dir = Path("knowledge")
    files = [
        path
        for path in knowledge_dir.glob("**/*")
        if path.is_file() and path.suffix.lower() in {".txt", ".md"}
    ]

    if not files:
        raise SystemExit("knowledge/ klasöründe .txt veya .md belge bulunamadı.")

    for path in files:
        print(f"{path}: {index_file(path)} parça indekslendi")


if __name__ == "__main__":
    main()
