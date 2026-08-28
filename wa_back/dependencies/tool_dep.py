import logging
from datetime import datetime
from ddgs import DDGS
from pathlib import Path
import torchaudio as ta
from dependencies.settings import get_settings
from dependencies.whatsapp_dep import send_wa_audio

from wa_back.dependencies.settings import Settings

_tts_model = None
settings = get_settings()
ROOT_DIR = Path("./").resolve().parent
AUDIO_DIR = Path(ROOT_DIR, "./audio").resolve()

logging.basicConfig(
    level=settings.log,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("tool_dep")

tools = [
    {
        "type": "function",
        "function": {
            "name": "search_internet",
            "description": (
            "Search the live internet and return current news, facts and webpages. "
            "Always use this function before answering questions about current events, "
            "news, weather, prices, sports or any information that may have changed."
        ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string"
                    }
                },
                "required": ["query"]
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_time",
            "description": (
            "Get current time and date."
            )
        }
    },
{
        "type": "function",
        "function": {
            "name": "generate_voice",
            "description": (
            "This is used when the user requests a voice response or when the response needs to be sent as an audio message."
        ),
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "The exact text to convert to speech."
                    }
                },
                "required": ["text"]
            },
        },
    }
]

def get_tts_model():
    global _tts_model
    if _tts_model is None:
        import torch
        from chatterbox.mtl_tts import ChatterboxMultilingualTTS
        logger.info("CUDA available: %s", torch.cuda.is_available())
        logger.info("Selected TTS device: %s", settings.device)
        _tts_model = ChatterboxMultilingualTTS.from_pretrained(device=settings.device)
    return _tts_model

def search_internet(query: str):
    """DuckDuckGo uzerinden arama yapar. Hata durumunda bos liste doner
    (model bos sonuc alip yoluna devam edebilsin diye None yerine [])."""
    query = str(query)
    logger.info("Searching the internet query: %s", query)
    try:
        with DDGS() as ddgs:
            results = list(ddgs.text(query, max_results=10,region="us-en", safesearch="off", timelimit="y", backend="google, brave, duckduckgo"))
        return [
            {
                "title": r.get("title"),
                "body": r.get("body"),
                "href": r.get("href"),
            }
            for r in results
        ]
    except Exception:
        logger.exception("Internet aramasi basarisiz oldu: query=%r", query)
        return []

def get_time():
    return [{"time":str(datetime.now())}]

def generate_voice(text: str, number: int):
    try:
        AUDIO_DIR.mkdir(parents=True, exist_ok=True)
        output_path = str(AUDIO_DIR / f"{number}.wav")
        multilingual_model = get_tts_model()
        logger.info("Selenilecek metin: %s", text)
        wav = multilingual_model.generate(
            text,
            language_id=settings.voice_lang,
            audio_prompt_path=str(AUDIO_DIR / settings.voice_file),
        )
        ta.save(output_path, wav, multilingual_model.sr)
        logger.info("Text transform to the audio: %s, sending to WhatsApp", wav)
        res = send_wa_audio(number=number, path=output_path)
        logger.info("WhatsApp response: %s", res)
        return {"message": "ok", "whatsapp_response": res}
    except Exception as e:
        logger.exception("TTS ses üretilemedi: %s",e)
        return {"message": "fail"}
