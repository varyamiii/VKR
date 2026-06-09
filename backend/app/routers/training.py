from fastapi import APIRouter, HTTPException, Request

from app.db.session import get_connection
from app.schemas.training import GenerateTrainingAudioRequest, GenerateTrainingAudioResponse
from app.services.auth_service import require_student
from app.services.generation_service import generate_audio_for_phrase

router = APIRouter(prefix="/api/training", tags=["training"])


@router.post("/generate", response_model=GenerateTrainingAudioResponse)
def generate_training_audio(payload: GenerateTrainingAudioRequest, request: Request):
    require_student(request)
    try:
        with get_connection() as conn:
            data = generate_audio_for_phrase(
                conn,
                phrase_id=payload.phrase_id,
                accent_id=payload.accent_id,
                noise_profile_id=payload.noise_profile_id,
                speed=payload.speed,
            )
            return data
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
