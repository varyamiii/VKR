import os
from pathlib import Path

from fastapi import FastAPI, HTTPException

from app.schemas import GenerateSpeechRequest, GenerateSpeechResponse
from app.tts_engine import create_engine

app = FastAPI(title="MeloTTS Service")
engine = create_engine()
OUTPUT_DIR = Path(os.getenv("TTS_OUTPUT_DIR", "/shared/generated_audio"))


@app.get("/health")
def health():
    return {"status": "ok", "speakers": sorted(engine.speaker_ids.keys())}


@app.post("/generate", response_model=GenerateSpeechResponse)
def generate(request: GenerateSpeechRequest):
    try:
        safe_filename = Path(request.output_filename).name
        output_path = OUTPUT_DIR / safe_filename
        engine.generate(
            text=request.text,
            speaker_key=request.speaker_key,
            output_path=output_path,
            speed=request.speed,
        )
        return GenerateSpeechResponse(output_filename=safe_filename)
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
