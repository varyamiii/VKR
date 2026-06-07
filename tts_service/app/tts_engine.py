import os
from pathlib import Path

from melo.api import TTS


class MeloTTSEngine:
    def __init__(self, language: str = "EN", device: str = "cpu") -> None:
        self.model = TTS(language=language, device=device)
        self.speaker_ids = self.model.hps.data.spk2id

    def generate(self, *, text: str, speaker_key: str, output_path: Path, speed: float = 1.0) -> Path:
        if speaker_key not in self.speaker_ids:
            available = ", ".join(sorted(self.speaker_ids.keys()))
            raise ValueError(f"Unknown speaker_key '{speaker_key}'. Available: {available}")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        self.model.tts_to_file(text, self.speaker_ids[speaker_key], str(output_path), speed=speed)
        return output_path


def create_engine() -> MeloTTSEngine:
    language = os.getenv("MELO_LANGUAGE", "EN")
    device = os.getenv("MELO_DEVICE", "cpu")
    return MeloTTSEngine(language=language, device=device)
