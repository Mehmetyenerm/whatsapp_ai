import os
import requests
import logging
from dependencies.settings import get_settings

settings = get_settings()

headers = {
    "accept": "application/json",
    "Content-Type": "application/json"
}

logging.basicConfig(
    level=settings.log,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("whatsapp_dep")

def send_wa_text(number: int, text: str):
    payload = {
        "to": number,
        "message": text,
    }
    try:
        response = requests.post(
            url=f"{settings.whatsapp_api_url}/message/text",
            json=payload,
            headers=headers,
            verify=os.path.expanduser(settings.whatsapp_ssl_path),  # true false degil ca sertifikanin yolunu ver
            timeout=30,
        )
        response.raise_for_status()
        logger.info("Whatsapp Text send to: %s, status: %s", number, response.status_code)
        return response.json()
    except requests.RequestException:
        return {"Error": "failed"}
        logger.exception("WhatsApp API'sine mesaj gonderilemedi (to=%s).", number)

def send_wa_audio(number: int, path: str):
    payload = {
        "to": number,
        "filePath": path,
    }
    try:
        response = requests.post(
            url=f"{settings.whatsapp_api_url}/message/audio",
            json=payload,
            headers=headers,
            verify=os.path.expanduser(settings.whatsapp_ssl_path),  # true false degil ca sertifikanin yolunu ver
            timeout=30,
        )
        response.raise_for_status()
        logger.info("Whatsapp Audio send to: %s, file: %s, status: %s", number, path, response.status_code)
        return response.json()
    except requests.RequestException:
        logger.exception("WhatsApp API'sine mesaj gonderilemedi (to=%s).", number)
        return {"error":"failed to send file"}