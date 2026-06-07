import shutil
import uuid
from pathlib import Path

from pydub import AudioSegment

from app.core.config import get_settings


def make_audio_filename(prefix: str, suffix: str = ".wav") -> str:
    return f"{prefix}_{uuid.uuid4().hex}{suffix}"


def resolve_noise_path(file_path: str | None) -> Path | None:
    if not file_path:
        return None

    settings = get_settings()
    raw_path = Path(file_path)
    if raw_path.is_absolute():
        return raw_path

    normalized = file_path.replace("\\", "/")
    if normalized.startswith("backend/static/noises/"):
        return settings.noises_dir / normalized.split("backend/static/noises/", 1)[1]
    if normalized.startswith("static/noises/"):
        return settings.noises_dir / normalized.split("static/noises/", 1)[1]
    if normalized.startswith("noises/"):
        return settings.noises_dir / normalized.split("noises/", 1)[1]
    return settings.noises_dir / raw_path.name


def overlay_noise(
    *,
    speech_path: Path,
    noise_path: Path | None,
    output_path: Path,
    snr_db: float | None,
) -> int:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    speech = AudioSegment.from_wav(speech_path)
    if noise_path is None:
        shutil.copyfile(speech_path, output_path)
        return len(speech)

    if not noise_path.exists():
        raise FileNotFoundError(
            f"Файл шума не найден: {noise_path}. "
            "Положите готовый WAV-файл шума в backend/app/static/noises "
            "или исправьте file_path в app.noise_profiles."
        )

    noise = AudioSegment.from_wav(noise_path)

    # Шум должен быть ровно такой же длины, как сгенерированная речь.
    # Если шум длиннее — обрезаем. Если вдруг короче — повторяем и затем обрезаем.
    if len(noise) < len(speech):
        repeats = (len(speech) // len(noise)) + 1
        noise = noise * repeats
    noise = noise[: len(speech)]

    # snr_db: насколько речь должна быть громче шума.
    # Например, 12 dB означает, что шум будет заметным, но речь останется основной.
    if snr_db is not None and speech.dBFS != float("-inf") and noise.dBFS != float("-inf"):
        target_noise_dbfs = speech.dBFS - float(snr_db)
        noise = noise.apply_gain(target_noise_dbfs - noise.dBFS)
    else:
        noise = noise.apply_gain(-18)

    mixed = speech.overlay(noise)
    mixed.export(output_path, format="wav")
    return len(mixed)


def public_audio_url(filename: str) -> str:
    return f"/static/generated_audio/{filename}"
