import json
import math
from pathlib import Path
import requests
from sqlmodel import select
from database import create_session
from dependencies.settings import get_settings
from schemas.rag_schema import RagChunk

settings = get_settings()

def embed(texts: list[str]) -> list[list[float]]:
    """Ollama'nın güncel ``/api/embed`` endpoint'inden embedding alır."""
    response = requests.post(
        f"{settings.ollama_url}/api/embed",
        json={"model": settings.embed_model, "input": texts},
        timeout=(5, 60),
    )
    response.raise_for_status()
    return response.json()["embeddings"]


def chunk_text(text: str, chunk_size: int = 900, overlap: int = 150) -> list[str]:
    """Metni örtüşen karakter parçalarına böler."""
    if chunk_size <= overlap:
        raise ValueError("chunk_size, overlap değerinden büyük olmalıdır.")

    text = " ".join(text.split())
    if not text:
        return []

    step = chunk_size - overlap
    return [text[index:index + chunk_size] for index in range(0, len(text), step)]


def index_text(text: str, source: str) -> int:
    """Metni RAG'e yazar.

    ``source`` aynı kaldığında önceki parçalar silinir. Bu özellik, hem belge
    güncellemelerinde hem de bir kullanıcının değiştirdiği hafıza bilgisinde
    eski embedding'lerin kalmasını engeller.
    """
    chunks = chunk_text(text)
    if not chunks:
        return 0

    vectors = embed(chunks)
    if len(chunks) != len(vectors):
        raise RuntimeError("Ollama dönen embedding sayısı parça sayısıyla uyuşmuyor.")

    with create_session() as session:
        old_chunks = session.exec(
            select(RagChunk).where(RagChunk.source == source)
        ).all()
        for old_chunk in old_chunks:
            session.delete(old_chunk)

        session.add_all(
            [
                RagChunk(
                    source=source,
                    chunk_index=index,
                    content=chunk,
                    embedding=json.dumps(vector),
                )
                for index, (chunk, vector) in enumerate(zip(chunks, vectors))
            ]
        )
        session.commit()

    return len(chunks)


def index_file(path: Path) -> int:
    """Dosyayı yeniden indeksler; bilgi tabanı belgeleri için kolaylık sarmalayıcısı."""
    return index_text(path.read_text(encoding="utf-8"), str(path))


def cosine_similarity(a: list[float], b: list[float]) -> float:
    dot = sum(left * right for left, right in zip(a, b))
    norm = math.sqrt(sum(value * value for value in a)) * math.sqrt(
        sum(value * value for value in b)
    )
    return dot / norm if norm else 0.0


def retrieve(
    query: str,
    top_k: int = 4,
    min_score: float = 0.35,
    source_prefix: str | None = None,
    exclude_prefix: str | None = None,
) -> list[dict]:
    """Sorguya en yakın parçaları kaynak ve skorlarıyla döndürür.

    ``source_prefix`` kullanıcıya özel hafızayı seçmek, ``exclude_prefix`` ise
    genel bilgi aramasından kullanıcı hafızasını çıkarmak için kullanılır.
    """
    if top_k < 1:
        return []

    query_vector = embed([query])[0]
    with create_session() as session:
        chunks = session.exec(select(RagChunk)).all()

    ranked = [
        {
            "source": chunk.source,
            "chunk_index": chunk.chunk_index,
            "content": chunk.content,
            "score": cosine_similarity(query_vector, json.loads(chunk.embedding)),
        }
        for chunk in chunks
        if (source_prefix is None or chunk.source.startswith(source_prefix))
        and (exclude_prefix is None or not chunk.source.startswith(exclude_prefix))
    ]
    ranked.sort(key=lambda item: item["score"], reverse=True)
    return [item for item in ranked[:top_k] if item["score"] >= min_score]
