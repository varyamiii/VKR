from pathlib import Path

import psycopg

from app.core.config import get_settings
from app.services.audio_service import (
    make_audio_filename,
    overlay_noise,
    public_audio_url,
    resolve_noise_path,
)
from app.services.catalog_service import get_accent, get_noise_profile, get_phrase
from app.services.tts_client import generate_speech


def _insert_audio_generation(
    conn: psycopg.Connection,
    *,
    phrase_id: int,
    accent_id: int,
    noise_profile_id: int,
    generated_text: str,
) -> int:
    with conn.cursor() as cur:
        cur.execute(
            """
            INSERT INTO app.audio_generations (
                phrase_id,
                accent_id,
                noise_profile_id,
                generated_text,
                status
            )
            VALUES (%s, %s, %s, %s, 'processing')
            RETURNING id;
            """,
            (phrase_id, accent_id, noise_profile_id, generated_text),
        )
        return int(cur.fetchone()["id"])


def _mark_audio_success(
    conn: psycopg.Connection,
    *,
    audio_generation_id: int,
    audio_file_path: str,
    duration_ms: int,
    snr_db: float | None,
) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE app.audio_generations
            SET status = 'success',
                audio_file_path = %s,
                duration_ms = %s,
                snr_db = %s,
                error_message = NULL
            WHERE id = %s;
            """,
            (audio_file_path, duration_ms, snr_db, audio_generation_id),
        )


def _mark_audio_failed(
    conn: psycopg.Connection, *, audio_generation_id: int, error_message: str) -> None:
    with conn.cursor() as cur:
        cur.execute(
            """
            UPDATE app.audio_generations
            SET status = 'failed', error_message = %s
            WHERE id = %s;
            """,
            (error_message[:4000], audio_generation_id),
        )


def generate_audio_for_phrase(
    conn: psycopg.Connection,
    *,
    phrase_id: int,
    accent_id: int,
    noise_profile_id: int,
    speed: float = 1.0,
) -> dict:
    settings = get_settings()
    phrase = get_phrase(conn, phrase_id)
    accent = get_accent(conn, accent_id)
    noise_profile = get_noise_profile(conn, noise_profile_id)

    generated_text = phrase.get("example_text") or phrase["phrase_text"]
    audio_generation_id = _insert_audio_generation(
        conn,
        phrase_id=phrase_id,
        accent_id=accent_id,
        noise_profile_id=noise_profile_id,
        generated_text=generated_text,
    )

    clean_filename = make_audio_filename(f"clean_{audio_generation_id}")
    final_filename = make_audio_filename(f"audio_{audio_generation_id}")
    clean_path = settings.generated_audio_dir / clean_filename
    final_path = settings.generated_audio_dir / final_filename

    try:
        speaker_key = accent["tts_speaker_code"]
        if not speaker_key:
            raise ValueError("Для выбранного акцента не задан tts_speaker_code")

        generate_speech(
            text=generated_text,
            speaker_key=speaker_key,
            output_filename=clean_filename,
            speed=speed,
        )

        noise_type = str(noise_profile["noise_type"])
        noise_path: Path | None = None
        snr_db = None
        if noise_type != "none":
            noise_path = resolve_noise_path(noise_profile.get("file_path"))
            snr_db = float(noise_profile["default_snr_db"]) if noise_profile.get("default_snr_db") else None

        duration_ms = overlay_noise(
            speech_path=clean_path,
            noise_path=noise_path,
            output_path=final_path,
            snr_db=snr_db,
        )

        # Чистый промежуточный файл не нужен пользователю.
        clean_path.unlink(missing_ok=True)

        audio_url = public_audio_url(final_filename)
        _mark_audio_success(
            conn,
            audio_generation_id=audio_generation_id,
            audio_file_path=audio_url,
            duration_ms=duration_ms,
            snr_db=snr_db,
        )
        return {
            "audio_generation_id": audio_generation_id,
            "audio_url": audio_url,
            "phrase_text": phrase["phrase_text"],
            "accent_name": accent["name_ru"],
            "noise_name": noise_profile["name_ru"],
            "duration_ms": duration_ms,
        }
    except Exception as exc:
        _mark_audio_failed(conn, audio_generation_id=audio_generation_id, error_message=str(exc))
        raise
