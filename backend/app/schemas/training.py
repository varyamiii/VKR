from pydantic import BaseModel, Field


class GenerateTrainingAudioRequest(BaseModel):
    phrase_id: int = Field(gt=0)
    accent_id: int = Field(gt=0)
    noise_profile_id: int = Field(gt=0)
    speed: float = Field(default=1.0, gt=0.2, le=2.0)


class GenerateTrainingAudioResponse(BaseModel):
    audio_generation_id: int
    audio_url: str
    phrase_text: str
    accent_name: str
    noise_name: str
    duration_ms: int | None = None
