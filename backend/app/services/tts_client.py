import requests

from app.core.config import get_settings


class TTSServiceError(RuntimeError):
    pass


def generate_speech(
    *,
    text: str,
    speaker_key: str,
    output_filename: str,
    speed: float = 1.0,
) -> str:
    settings = get_settings()
    url = f"{settings.tts_service_url.rstrip('/')}/generate"
    payload = {
        "text": text,
        "speaker_key": speaker_key,
        "output_filename": output_filename,
        "speed": speed,
    }

    try:
        response = requests.post(url, json=payload, timeout=300)
    except requests.RequestException as exc:
        raise TTSServiceError(f"Не удалось обратиться к MeloTTS service: {exc}") from exc

    if response.status_code >= 400:
        raise TTSServiceError(f"MeloTTS service вернул ошибку: {response.text}")

    data = response.json()
    return data["output_filename"]
