import logging
from uuid import uuid4
from dependencies.settings import get_settings
from rag.rag_service import index_text, retrieve

settings = get_settings()

logging.basicConfig(
    level=settings.log,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("rag_dep")

def _rag_context(question: str, phone_number: int) -> str:
    """Genel bilgi tabanı ve yalnızca bu kullanıcıya ait hafızayı getirir.

    Kullanıcı hafızasını genel aramaya karıştırmıyoruz; aksi halde bir
    kullanıcının kişisel bilgisi başka bir kullanıcıya cevap olarak sızabilir.
    """
    try:
        general_results = retrieve(
            question,
            top_k=4,
            min_score=0.35,
            exclude_prefix="memory:user:",
        )
        personal_results = retrieve(
            question,
            top_k=4,
            min_score=0.35,
            source_prefix=f"memory:user:{phone_number}:",
        )
    except Exception:
        # RAG/Ollama geçici olarak kapalıysa normal sohbet akışı devam eder.
        logger.exception("RAG bağlamı alınamadı; mesaja RAG olmadan devam ediliyor.")
        return ""
    results = sorted(
        [*general_results, *personal_results],
        key=lambda item: item["score"],
        reverse=True,
    )
    if not results:
        return ""

    return "\n\n".join(
        f"[Kaynak: {item['source']} | benzerlik: {item['score']:.3f}]\n"
        f"{item['content']}"
        for item in results[:6]
    )


def _extract_long_term_memory(content: str) -> str | None:
    """Açıkça kişisel/kalıcı görünen mesajları hafızaya aday yapar.

    Her mesajı hafızaya yazmak yerine basit bir güvenlik filtresi kullanıyoruz.
    Daha gelişmiş bir sürümde bu fonksiyon ayrı bir LLM sınıflandırıcısıyla
    değiştirilebilir; fakat kaydetme kararı yine uygulama kodunda kalmalıdır.
    """
    normalized = content.strip()
    lower = normalized.lower()
    memory_markers = (
        "benim ", "adım ", "ismim ", "yaşım ", "şehirde yaşıyorum",
        "seviyorum", "tercih ederim", "istemiyorum", "hatırla", "unutma",
    )
    if len(normalized) > 600 or not any(marker in lower for marker in memory_markers):
        return None
    return normalized


def _save_long_term_memory(content: str, phone_number: int) -> None:
    """Kişisel hafızayı embedding'e çevirip kullanıcıya özel kaynakla saklar."""
    memory = _extract_long_term_memory(content)
    if memory is None:
        return

    # Her hafızaya ayrı kaynak id'si verilir; yeni bir bilgi eski anıları silmez.
    source = f"memory:user:{phone_number}:{uuid4()}"
    index_text(memory, source)
    logger.info("Uzun süreli hafızaya bilgi eklendi: phone=%i", phone_number)
