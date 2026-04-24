import io
import os
import re
import wave

try:
    import winsound as _winsound  # Windows only — only needed for terminal mode
except ImportError:
    _winsound = None  # type: ignore[assignment]

import httpx
from dotenv import load_dotenv

load_dotenv()

_TTS_URL = "https://api.minimax.io/v1/t2a_v2"
_MODEL = "speech-2.8-hd"
_SAMPLE_RATE = 24000

_VOICE_BY_GENDER: dict[str, str] = {
    "feminino": "Calm_Woman",
    "masculino": "Patient_Man",
}

_EMOTION_KEYWORDS: list[tuple[str, list[str]]] = [
    ("fearful",   ["nervous", "hesitat", "fidget", "tense", "swallows", "tightens", "stiffens", "fearful"]),
    ("angry",     ["frustrated", "scoffs", "clenches", "bitterly", "sharply"]),
    ("surprised", ["surprised", "startled", "eyes widen", "raises eyebrows"]),
    ("disgusted", ["grimaces", "makes a face", "waves off"]),
    ("happy",     ["laughs", "smiles", "chuckl", "brightens", "grins", "perks up"]),
    ("sad",       ["sighs", "looks down", "tearful", "tears", "trails off", "voice breaks", "heavily", "softly", "sad"]),
]

_STAGE_RE = re.compile(r"\*([^*]+)\*")


def _clean_text(text: str) -> str:
    text = _STAGE_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def _detect_emotion(text: str, default: str = "neutral") -> str:
    directions = " ".join(_STAGE_RE.findall(text)).lower()
    if not directions:
        return default
    for emotion, keywords in _EMOTION_KEYWORDS:
        if any(k in directions for k in keywords):
            return emotion
    return default


def _pcm_to_wav(pcm: bytes) -> bytes:
    buf = io.BytesIO()
    with wave.open(buf, "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(_SAMPLE_RATE)
        wf.writeframes(pcm)
    return buf.getvalue()


class PatientVoice:
    """Synthesizes patient speech with emotion inferred from LLM stage directions."""

    def __init__(self, voice_id: str, speed: float = 0.85, default_emotion: str = "neutral") -> None:
        self.api_key = os.getenv("MINIMAX_API_KEY", "")
        self.voice_id = voice_id
        self.speed = speed
        self.default_emotion = default_emotion

    def synthesize(self, text: str) -> bytes | None:
        """Return WAV bytes — used by the web interface."""
        emotion = _detect_emotion(text, default=self.default_emotion)
        clean = _clean_text(text)
        if not clean:
            return None
        r = httpx.post(
            _TTS_URL,
            headers={"Authorization": f"Bearer {self.api_key}"},
            json={
                "model": _MODEL,
                "text": clean,
                "stream": False,
                "voice_setting": {"voice_id": self.voice_id, "speed": self.speed, "vol": 1.0, "pitch": 0, "emotion": emotion},
                "audio_setting": {"sample_rate": _SAMPLE_RATE, "format": "pcm", "channel": 1},
            },
            timeout=30.0,
        )
        r.raise_for_status()
        audio_hex: str = r.json()["data"]["audio"]
        if not audio_hex:
            return None
        return _pcm_to_wav(bytes.fromhex(audio_hex))

    def speak(self, text: str) -> None:
        """Synthesize and play locally — used by the terminal interface (Windows only)."""
        if _winsound is None:
            raise NotImplementedError("speak() requires Windows. Use synthesize() in the web interface.")
        wav = self.synthesize(text)
        if wav:
            _winsound.PlaySound(wav, _winsound.SND_MEMORY)


def voice_for_ficha(genero: str) -> PatientVoice:
    voice_id = os.getenv("MINIMAX_VOICE_ID") or _VOICE_BY_GENDER.get(genero.lower(), "Calm_Woman")
    return PatientVoice(voice_id=voice_id, default_emotion="sad")
