import requests
import json
import time
import logging
from uuid import UUID, uuid4
from sqlmodel import Session, select
from schemas.database_schema import Conversation, Message, MessageRole
from crud import create_conversation, create_message, get_last_messages
from schemas.main_schema import WhatsAppMessage
from database import create_session
from dependencies.whatsapp_dep import send_wa_text
from dependencies.rag_dep import _rag_context, _save_long_term_memory
from dependencies.tool_dep import generate_voice, get_time, search_internet, tools
from dependencies.settings import get_settings
from systemPromt import system_promt

settings = get_settings()

logging.basicConfig(
    level=settings.log,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("main_dep")

headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

TOOL_IMPLEMENTATIONS = {
    "search_internet": search_internet,
    "get_time": get_time,
    "generate_voice": generate_voice,
}

def _execute_tool_call(tool_call: dict, number: int):
    """Bir tool_call'ı guvenli sekilde calistirir; hatalari yutmak yerine
    modele okunabilir bir hata mesaji dondurur."""
    tool_name = tool_call.get("function", {}).get("name")
    raw_args = tool_call.get("function", {}).get("arguments", {})

    # Bazi modeller argumanlari JSON string olarak dondurebilir.
    if isinstance(raw_args, str):
        try:
            raw_args = json.loads(raw_args) if raw_args else {}
        except json.JSONDecodeError:
            logger.warning("Tool argumanlari parse edilemedi: %r", raw_args)
            return tool_name, {"error": "invalid_arguments"}

    implementation = TOOL_IMPLEMENTATIONS.get(tool_name)
    if implementation is None:
        return tool_name, {"error": f"Unknown tool: {tool_name}"}

    try:
        if implementation == generate_voice:
            return tool_name, implementation(**raw_args, number=number)
        return tool_name, implementation(**raw_args)
    except TypeError:
        logger.exception("Tool '%s' beklenmeyen argumanlarla cagrildi: %r", tool_name, raw_args)
        return tool_name, {"error": "invalid_arguments"}


def send_message(model: str, messages, number: int):
    for iteration in range(1,settings.max_tool_iterations + 1):
        logger.debug("Ollama istegi gonderiliyor (deneme %s/%s)", iteration, settings.max_tool_iterations)
        # Send a POST request to the model API
        response = requests.post(f"{settings.ollama_url}/api/chat", headers=headers, json={
            "model": model,  # Model name from the request
            "messages": messages,  # Prompt from the request
            "stream": False,  # Streaming flag from the request
            "tools": tools,
            "options": {
                "temperature": settings.temperature,
                "top_p": settings.top_p,
                "top_k": settings.top_k,
            },
        },timeout=250)
        if not response.ok:
            logger.error(
                "Ollama HTTP %s response: %s",
                response.status_code,
                response.text
            )
            response.raise_for_status()

        try:
            response.raise_for_status()
        except requests.HTTPError:
            raise

        result = response.json()
        message = result["message"]

        tool_calls = message.get("tool_calls") or []
        if not tool_calls:
            logger.debug("Model dogrudan cevap verdi, tool cagrisi yok.")
            return message.get("content") or ""

        # Assistant'ın tool çağrısını history'ye ekle
        messages.append(message)

        for tool_call in tool_calls:
            tool_name, tool_result = _execute_tool_call(tool_call, number)
            tool_call_id = tool_call.get("id", str(uuid4()))
            logger.debug("Tool calisti: %s -> %s", tool_name, tool_result)

            # Tool sonucunu modele geri ver
            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call_id,
                    "name": tool_name,
                    "content": json.dumps(tool_result, ensure_ascii=False)
                }
            )
        logger.debug(
            "Tool sonucu modele geri gonderiliyor.Sonraki iteration=%s",iteration + 1)
    logger.warning("Tool-call dongusu tamamlanamadi.")
    return "Uzgunum, su anda isteginizi tamamlayamiyorum. Lutfen tekrar deneyin."

def start_conversation(phone_number: int, session: Session):
    stmt = select(Conversation).where(Conversation.phone == phone_number)
    ph_nmr = session.exec(stmt).first()
    if ph_nmr is None:
        item = Conversation(
            id=uuid4(),
            phone=phone_number
        )
        return create_conversation(item, session)
    return ph_nmr

def generate_promt(
    conversation_id: UUID,
    session: Session,
    phone_number: int | None = None,
    question: str | None = None,
):
    history = get_last_messages(conversation_id, session, limit=10)

    messages = [
        {
            "role": MessageRole.SYSTEM,
            "content": system_promt,
        }
    ]

    # RAG sonuçları sistem mesajından hemen sonra eklenir; böylece model hem
    # statik bilgi tabanını hem de bu kullanıcıya ait uzun süreli hafızayı görür.
    if phone_number and question:
        context = _rag_context(question, phone_number)
        if context:
            messages.append(
                {
                    "role": MessageRole.SYSTEM,
                    "content": (
                        "Use the following RAG context only when it is relevant. "
                        "If it does not contain the answer, do not invent information.\n\n" + context
                    ),
                }
            )

    for item in history:
        messages.append(
            {
                "role": item.role,
                "content": item.content
            }
        )

    return messages

def handle_message(message: WhatsAppMessage):
    with create_session() as session:
        try:
            logger.info("Message is handling")
            phone_number = message.from_
            number, sys = phone_number.split("@")
            sender_number = int(number)
            item = start_conversation(sender_number, session)
            con_id = item.id

            # Metin olmayan bir WhatsApp olayında DB'ye NULL yazmamak için güvenli
            # bir içerik değeri kullanılır.
            content = message.filePath if message.filePath is not None else (message.text or "")

            msg = Message(
                id=message.id,
                conversation_id=con_id,
                role=MessageRole.USER,
                content=content,
                created_at=message.timestamp or int(time.time()),
            )
            create_message(msg, session)
            promt = generate_promt(
                msg.conversation_id,
                session,
                phone_number=sender_number,
                question=content,
            )
            try:
                generated_text = send_message(settings.model, promt, sender_number)
            except requests.RequestException:
                logger.exception("Ollama'ya istek gonderilirken hata olustu.")
                generated_text = "Uzgunum, su anda cevap veremiyorum. Lutfen birazdan tekrar deneyin."

            try:
                send_wa_text(sender_number, generated_text)
            except Exception:
                logger.exception("TTS de problem var")
            llmMsg = Message(
                conversation_id=con_id,
                role=MessageRole.ASSISTANT,
                content=generated_text,
                created_at=int(time.time()),
            )
            create_message(llmMsg, session)

            # Cevap gönderildikten sonra kullanıcı mesajındaki kalıcı bilgiyi
            # uzun süreli hafızaya ekleriz. RAG araması bir sonraki mesajdan
            # itibaren bu bilgiyi kullanabilir.
            try:
                _save_long_term_memory(content, sender_number)
            except Exception:
                # Hafıza yazılamaması WhatsApp cevabını başarısız kılmamalıdır.
                logger.exception("Uzun süreli hafızaya kayıt başarısız oldu.")
        except Exception:
            logger.exception("Mesaj islenirken beklenmeyen bir hata olustu.")