from fastapi import APIRouter, HTTPException

from app.db.session import get_connection
from app.schemas.training import GenerateTrainingAudioRequest, GenerateTrainingAudioResponse
from app.services.generation_service import generate_audio_for_phrase

router = APIRouter(prefix="/api/training", tags=["training"])


@router.post("/generate", response_model=GenerateTrainingAudioResponse)
def generate_training_audio(request: GenerateTrainingAudioRequest):
    try:
        with get_connection() as conn:
            data = generate_audio_for_phrase(
                conn,
                phrase_id=request.phrase_id,
                accent_id=request.accent_id,
                noise_profile_id=request.noise_profile_id,
                speed=request.speed,
            )
            return data
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
