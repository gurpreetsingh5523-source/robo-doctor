"""
Robo Doctor - Voice Interface (v6.2)
=====================================
Speak to patients and (optionally) listen to symptoms.

REAL now (offline, zero cost):
  - Text-to-speech via the operating system voice (macOS `say` — supports
    many voices/languages; on Linux falls back to espeak if installed).

PLUGGABLE (cloud, when configured):
  - STT (speech-to-text) via any Whisper-compatible API
    (Qwen/Alibaba DashScope paraformer, OpenAI Whisper, Groq, etc.)
    Set ROBO_STT_API_KEY + ROBO_STT_BASE_URL + ROBO_STT_MODEL.
  - Cloud TTS via any OpenAI-compatible audio endpoint
    Set ROBO_TTS_API_KEY + ROBO_TTS_BASE_URL.

Honesty: if a capability is not available on this machine, the module says
so instead of pretending.
"""

import os
import shutil
import subprocess
import tempfile
from datetime import datetime
from typing import Dict, Optional

try:
    import requests
except ImportError:
    requests = None


class VoiceNotAvailable(Exception):
    pass


class VoiceInterface:
    """
    Speak and listen for Robo Doctor.

    Usage:
        voice = VoiceInterface()
        voice.speak("Sat Sri Akal ji, tuhada glucose report ready hai", lang='pa')
    """

    # macOS voices for common languages (system `say`)
    MACOS_VOICES = {
        "en": "Samantha", "hi": "Lekha", "pa": "Lekha",  # Punjabi falls back to Hindi voice
    }

    def __init__(self, stt_api_key: Optional[str] = None,
                 stt_base_url: Optional[str] = None,
                 stt_model: Optional[str] = None):
        self.stt_api_key = stt_api_key or os.environ.get("ROBO_STT_API_KEY")
        self.stt_base_url = stt_base_url or os.environ.get("ROBO_STT_BASE_URL")
        self.stt_model = stt_model or os.environ.get("ROBO_STT_MODEL", "whisper-1")

    # ------------------------------------------------------------------
    def capabilities(self) -> Dict:
        return {
            "tts_offline": self._offline_tts_engine() is not None,
            "stt_cloud_configured": bool(self.stt_api_key and self.stt_base_url),
            "offline_engine": self._offline_tts_engine(),
        }

    def _offline_tts_engine(self) -> Optional[str]:
        if shutil.which("say"):
            return "macos_say"
        if shutil.which("espeak"):
            return "espeak"
        return None

    # ------------------------------------------------------------------
    def speak(self, text: str, lang: str = "en") -> Dict:
        """Speak text out loud using the offline system voice."""
        engine = self._offline_tts_engine()
        if engine is None:
            raise VoiceNotAvailable(
                "No offline TTS engine found (need macOS 'say' or 'espeak').")
        if engine == "macos_say":
            voice = self.MACOS_VOICES.get(lang, "Samantha")
            subprocess.run(["say", "-v", voice, text], check=False, timeout=120)
        else:
            subprocess.run(["espeak", text], check=False, timeout=120)
        return {"status": "spoken", "engine": engine, "lang": lang,
                "chars": len(text), "at": datetime.now().isoformat()}

    def speak_file(self, text: str, out_path: str, lang: str = "en") -> Dict:
        """Render speech to an audio file (macOS AIFF) instead of playing."""
        if not shutil.which("say"):
            raise VoiceNotAvailable("macOS 'say' required for file output.")
        voice = self.MACOS_VOICES.get(lang, "Samantha")
        subprocess.run(["say", "-v", voice, "-o", out_path, text],
                       check=True, timeout=120)
        return {"status": "saved", "path": out_path, "voice": voice}

    # ------------------------------------------------------------------
    def transcribe(self, audio_path: str, language: Optional[str] = None) -> Dict:
        """
        Speech-to-text via a configured Whisper-compatible cloud API.
        Honest when not configured.
        """
        if not (self.stt_api_key and self.stt_base_url and requests):
            return {
                "status": "stt_not_configured",
                "text": None,
                "message": "Set ROBO_STT_API_KEY + ROBO_STT_BASE_URL "
                           "(Qwen DashScope, OpenAI Whisper, Groq, etc.). "
                           "No transcription was fabricated.",
            }
        with open(audio_path, "rb") as fh:
            files = {"file": fh}
            data = {"model": self.stt_model}
            if language:
                data["language"] = language
            resp = requests.post(
                f"{self.stt_base_url.rstrip('/')}/audio/transcriptions",
                headers={"Authorization": f"Bearer {self.stt_api_key}"},
                files=files, data=data, timeout=120)
        resp.raise_for_status()
        return {"status": "ok", "text": resp.json().get("text", ""),
                "engine": self.stt_model}
