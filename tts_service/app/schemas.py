from pydantic import BaseModel, Field


class GenerateSpeechRequest(BaseModel):
    text: str = Field(min_length=1)
    speaker_key: str = Field(min_length=1)
    output_filename: str = Field(min_length=5)
    speed: float = Field(default=1.0, gt=0.2, le=2.0)


class GenerateSpeechResponse(BaseModel):
    output_filename: str
