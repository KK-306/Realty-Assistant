import os
import asyncio
import logging
import subprocess
import time
from pathlib import Path
from typing import Optional, Dict

from app.config import settings, AUDIO_DIR

logger = logging.getLogger(__name__)

# Curated high-fidelity real estate narrator voices
VOICE_MAP: Dict[str, str] = {
    # Presets
    "us_male": "en-US-BrianNeural",
    "us_female": "en-US-AriaNeural",
    "indian_male": "en-IN-PrabhatNeural",
    "indian_female": "en-IN-NeerjaNeural",
    "uk_male": "en-GB-RyanNeural",
    "uk_female": "en-GB-SoniaNeural",
    # Direct IDs
    "en-US-BrianNeural": "en-US-BrianNeural",
    "en-US-AriaNeural": "en-US-AriaNeural",
    "en-IN-PrabhatNeural": "en-IN-PrabhatNeural",
    "en-IN-NeerjaNeural": "en-IN-NeerjaNeural",
    "en-GB-RyanNeural": "en-GB-RyanNeural",
    "en-GB-SoniaNeural": "en-GB-SoniaNeural",
    "en-US-ChristopherNeural": "en-US-ChristopherNeural",
    "en-US-JennyNeural": "en-US-JennyNeural"
}

VOICE_PROFILES = {
    "en-US-BrianNeural": {"locale": "en-us", "gender": "male"},
    "en-US-AriaNeural": {"locale": "en-us", "gender": "female"},
    "en-IN-PrabhatNeural": {"locale": "en-in", "gender": "male"},
    "en-IN-NeerjaNeural": {"locale": "en-in", "gender": "female"},
    "en-GB-RyanNeural": {"locale": "en-gb", "gender": "male"},
    "en-GB-SoniaNeural": {"locale": "en-gb", "gender": "female"},
    "en-US-ChristopherNeural": {"locale": "en-us", "gender": "male"},
    "en-US-JennyNeural": {"locale": "en-us", "gender": "female"},
}


class AudioService:
    """
    Multi-engine Neural TTS voiceover service with automatic fallback chain:
      1. edge-tts  (Microsoft Neural TTS with custom speech rate & pitch)
      2. pyttsx3   (Offline Windows SAPI → WAV → MP3 via FFmpeg)
      3. gTTS      (Google Cloud TTS with region-specific accents)
      4. Silent    (Returns None — video renders without narration)
    """

    @classmethod
    async def generate_voiceover(
        cls, text: str, output_path: Path, voice: Optional[str] = None
    ) -> Optional[Path]:
        """
        Synthesises spoken voiceover with natural pacing, clear articulation,
        and professional commercial tone. Saves output to *output_path* (MP3).
        """
        if not text or not text.strip():
            return None
        if settings.TTS_PROVIDER == "none":
            return None

        clean_text = text.strip()
        selected_voice = cls._resolve_voice_id(voice)

        # --- Engine 1: edge-tts (Microsoft Neural Studio Voices) ---
        result = await cls._try_edge_tts(clean_text, output_path, selected_voice)
        if result:
            return result

        # --- Engine 2: pyttsx3 (Offline Windows SAPI → WAV → MP3 via FFmpeg) ---
        result = await asyncio.get_event_loop().run_in_executor(
            None, cls._try_pyttsx3, clean_text, output_path, selected_voice
        )
        if result:
            return result

        logger.error("Neural TTS and local system TTS both failed for voice %s.", selected_voice)
        return None

    @classmethod
    def get_background_music_path(cls) -> Optional[Path]:
        """Returns the path to the royalty-free ambient music track."""
        wav_path = AUDIO_DIR / "ambient_lounge.wav"
        if wav_path.is_file():
            return wav_path
        return None

    # ---------------------------------------------------------------------------
    # Helpers & Resolvers
    # ---------------------------------------------------------------------------

    @classmethod
    def _resolve_voice_id(cls, voice_key: Optional[str]) -> str:
        """Maps user preset/ID to the corresponding Edge TTS neural voice model."""
        if not voice_key:
            return settings.TTS_VOICE_EN
        key = voice_key.strip()
        if key in VOICE_MAP:
            return VOICE_MAP[key]
        normalized = key.casefold()
        return next(
            (voice_id for alias, voice_id in VOICE_MAP.items() if alias.casefold() == normalized),
            settings.TTS_VOICE_EN,
        )

    # ---------------------------------------------------------------------------
    # Engine Implementations
    # ---------------------------------------------------------------------------

    @classmethod
    async def _try_edge_tts(
        cls, text: str, output_path: Path, voice_id: str
    ) -> Optional[Path]:
        """
        Synthesizes using Microsoft's state-of-the-art Neural Voice models.
        Pacing is tuned to -3% for an authoritative, relaxed commercial narration cadence.
        """
        try:
            import edge_tts  # noqa: PLC0415

            # Professional real-estate pacing: slightly measured (-3% rate) with natural pitch
            communicate = edge_tts.Communicate(
                text,
                voice_id,
                rate="-3%",
                pitch="+0Hz",
                volume="+0%"
            )
            await communicate.save(str(output_path))

            if output_path.is_file() and output_path.stat().st_size > 500:
                logger.info(f"[TTS] Neural voice synthesis success ({voice_id}) → {output_path.stat().st_size} bytes")
                return output_path

            _safe_remove(output_path)
        except Exception as exc:
            logger.warning(f"[TTS] edge-tts error ({exc.__class__.__name__}: {exc}). Falling back to secondary engine.")
            _safe_remove(output_path)
        return None

    @classmethod
    def _try_pyttsx3(cls, text: str, output_path: Path, voice_id: str) -> Optional[Path]:
        """
        Offline synthesis via pyttsx3 (Windows SAPI5) with FFmpeg audio transcoding.
        """
        try:
            import pyttsx3  # noqa: PLC0415

            engine = pyttsx3.init()
            engine.setProperty("rate", 150)  # Calm commercial pace
            engine.setProperty("volume", 1.0)

            voices = engine.getProperty("voices")
            wav_path = output_path.with_suffix(".wav")
            _safe_remove(wav_path)
            local_voice = cls._select_local_voice(voices or [], voice_id)
            if not local_voice:
                engine.stop()
                logger.warning("[TTS] No suitable local speech voice is installed for %s.", voice_id)
                return None

            engine.setProperty("voice", local_voice.id)
            engine.save_to_file(text, str(wav_path))
            engine.runAndWait()
            engine.stop()

            if not wav_path.is_file() or wav_path.stat().st_size < 500:
                _safe_remove(wav_path)
                return None

            logger.info("[TTS] Local speech synthesis success for %s using %s", voice_id, local_voice.name)
            return wav_path

        except Exception as exc:
            logger.warning(f"[TTS] pyttsx3 fallback failed ({exc})")
            _safe_remove(output_path)
            _safe_remove(output_path.with_suffix(".wav"))
        return None

    @classmethod
    def _select_local_voice(cls, voices, voice_id: str):
        """Select an installed English SAPI voice matching the selected profile."""
        profile = VOICE_PROFILES.get(voice_id)
        if not profile:
            return None

        expected_locale = profile["locale"].replace("-", "")
        expected_gender = profile["gender"]
        candidates = []

        for voice in voices:
            raw_languages = getattr(voice, "languages", []) or []
            languages = " ".join(
                item.decode("utf-8", errors="ignore") if isinstance(item, bytes) else str(item)
                for item in raw_languages
            )
            descriptor = " ".join((str(getattr(voice, "id", "")), str(getattr(voice, "name", "")), languages)).casefold()
            compact = "".join(character for character in descriptor if character.isalnum())
            if "en" not in compact and "english" not in descriptor:
                continue

            gender_value = str(getattr(voice, "gender", "") or "").casefold()
            if gender_value in {"m", "male", "man"}:
                gender = "male"
            elif gender_value in {"f", "female", "woman"}:
                gender = "female"
            else:
                gender = ""
            if not gender:
                if any(marker in compact for marker in ("david", "mark", "ryan", "george", "james", "male")):
                    gender = "male"
                elif any(marker in compact for marker in ("zira", "jenny", "aria", "sonia", "hazel", "female")):
                    gender = "female"
            if gender and gender != expected_gender:
                continue

            score = 1 if gender == expected_gender else 0
            if expected_locale in compact:
                score += 4
            candidates.append((score, voice))

        if not candidates:
            return None
        return max(candidates, key=lambda candidate: candidate[0])[1]

    @classmethod
    def _try_gtts(cls, text: str, output_path: Path, voice_id: str) -> Optional[Path]:
        """
        Google Cloud TTS REST with region-matched accent TLDs.
        """
        try:
            from gtts import gTTS  # noqa: PLC0415

            # Match Google TTS top-level domain to target accent
            tld = "com"
            if "IN" in voice_id or "indian" in voice_id.lower():
                tld = "co.in"
            elif "GB" in voice_id or "uk" in voice_id.lower():
                tld = "co.uk"

            tts = gTTS(text=text, lang="en", tld=tld, slow=False)
            tts.save(str(output_path))

            if output_path.is_file() and output_path.stat().st_size > 500:
                logger.info(f"[TTS] gTTS fallback success (tld={tld}) → {output_path}")
                return output_path
            _safe_remove(output_path)
        except Exception as exc:
            logger.warning(f"[TTS] gTTS fallback failed ({exc})")
            _safe_remove(output_path)
        return None

    # ---------------------------------------------------------------------------
    # FFmpeg Audio Optimization
    # ---------------------------------------------------------------------------

    @staticmethod
    def _wav_to_mp3(wav_path: Path, mp3_path: Path) -> bool:
        """Transcode WAV to clean broadcast-standard MP3 (44.1kHz, 192k stereo)."""
        try:
            ffmpeg_bin = settings.get_ffmpeg_path()

            cmd = [
                ffmpeg_bin,
                "-hide_banner",
                "-loglevel", "warning",
                "-y",
                "-i", str(wav_path),
                "-vn",
                "-ar", "44100",
                "-ac", "2",
                "-b:a", "192k",
                "-threads", "1",
                str(mp3_path),
            ]
            logger.info("FFmpeg narration audio conversion started: %s", wav_path.name)
            started_at = time.monotonic()
            result = subprocess.run(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=60,
            )
            elapsed = time.monotonic() - started_at
            if result.returncode != 0:
                logger.error(
                    "FFmpeg narration audio conversion failed (exit=%s, %.1fs): %s",
                    result.returncode, elapsed, (result.stderr or "")[-3000:],
                )
                return False
            logger.info("FFmpeg narration audio conversion completed in %.1fs", elapsed)
            return True
        except subprocess.TimeoutExpired:
            logger.exception("FFmpeg narration audio conversion timed out for %s", wav_path)
            return False
        except Exception:
            logger.exception("FFmpeg narration audio conversion failed for %s", wav_path)
            return False


def _safe_remove(path: Optional[Path]) -> None:
    try:
        if path and path.is_file():
            path.unlink()
    except Exception:
        pass
