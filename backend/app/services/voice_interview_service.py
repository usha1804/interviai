"""
Voice Interview Service
TTS: edge-tts (free, no API key)
STT: faster-whisper (local, no API key)
Filler word detection, speaking speed analysis, transcript management.
"""
import asyncio
import io
import logging
import os
import re
import tempfile
import threading
import traceback
import uuid
from typing import Dict, List, Optional, Tuple

FILLER_WORDS = [
    "um", "uh", "like", "you know", "basically", "literally",
    "actually", "so", "right", "okay", "hmm", "er", "ah",
]

AUDIO_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "audio_cache")
os.makedirs(AUDIO_DIR, exist_ok=True)

_whisper_model = None
_whisper_init_lock = threading.Lock()
_whisper_transcribe_lock = threading.Lock()
MAX_AUDIO_BYTES = 8 * 1024 * 1024


def _get_whisper():
    global _whisper_model
    if _whisper_model is None:
        with _whisper_init_lock:
            if _whisper_model is None:
                from faster_whisper import WhisperModel
                cpu_threads = max(1, min(4, os.cpu_count() or 1))
                _whisper_model = WhisperModel(
                    "tiny.en",
                    device="cpu",
                    compute_type="int8",
                    cpu_threads=cpu_threads,
                )
    return _whisper_model


async def text_to_speech(text: str, session_id: int, index: int) -> Tuple[str, str]:
    """Convert text to speech using edge-tts. Returns path to audio file and MIME type."""
    filename = f"tts_{session_id}_{index}_{uuid.uuid4().hex}.mp3"
    path = os.path.join(AUDIO_DIR, filename)

    if not text or not text.strip():
        raise ValueError("Text-to-speech requires non-empty text.")

    # Prefer edge-tts, then gTTS. Never replace failed speech with silent audio.
    try:
        import edge_tts
    except Exception:
        try:
            from gtts import gTTS
        except Exception as exc:
            raise RuntimeError("No text-to-speech provider is available.") from exc

        # Use gTTS synchronously in a thread
        def _save_gtts(text, out_path):
            tts = gTTS(text=text, lang='en')
            tts.save(out_path)

        try:
            await asyncio.to_thread(_save_gtts, text, path)
            if os.path.isfile(path) and os.path.getsize(path) > 1024:
                return path, "audio/mpeg"
            raise RuntimeError("gTTS produced an empty audio file.")
        except Exception as e:
            raise RuntimeError(f"gTTS TTS processing failed: {e}")

    # edge-tts path
    try:
        communicate = edge_tts.Communicate(text, voice="en-US-AriaNeural")
        await communicate.save(path)
        if not os.path.isfile(path) or os.path.getsize(path) < 1024:
            raise RuntimeError("Edge TTS produced an empty audio file.")
        return path, "audio/mpeg"
    except Exception as exc:
        logging.error("edge-tts conversion failed: %s", traceback.format_exc())
        try:
            from gtts import gTTS
            def _save_gtts(text, out_path):
                tts = gTTS(text=text, lang='en')
                tts.save(out_path)
            await asyncio.to_thread(_save_gtts, text, path)
            if os.path.isfile(path) and os.path.getsize(path) > 1024:
                return path, "audio/mpeg"
            raise RuntimeError("gTTS produced an empty audio file.")
        except Exception as gtts_exc:
            logging.error("gTTS fallback failed: %s", traceback.format_exc())
            raise RuntimeError("All text-to-speech providers failed.") from gtts_exc


def _guess_audio_extension(audio_bytes: bytes) -> str:
    """Return a supported container extension based on its file signature."""
    if audio_bytes.startswith(b'RIFF'):
        return '.wav'
    if audio_bytes.startswith(b'OggS'):
        return '.ogg'
    if audio_bytes.startswith(b'ID3') or audio_bytes[0:2] == b'\xFF\xFB':
        return '.mp3'
    if len(audio_bytes) >= 12 and audio_bytes[4:8] == b'ftyp':
        return '.mp4'
    if audio_bytes.startswith(b'\x1A\x45\xDF\xA3'):
        return '.webm'
    raise ValueError("Unsupported audio format. Upload WebM, Ogg, MP4, WAV, or MP3 audio.")


def speech_to_text(audio_bytes: bytes) -> Dict:
    """Transcribe audio bytes using faster-whisper. Returns transcript + metadata."""
    if not audio_bytes:
        raise ValueError("Audio recording is empty.")
    if len(audio_bytes) > MAX_AUDIO_BYTES:
        raise ValueError("Audio recording exceeds the 8 MB upload limit.")
    ext = _guess_audio_extension(audio_bytes)
    with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as f:
        f.write(audio_bytes)
        tmp_path = f.name

    try:
        model = _get_whisper()
        with _whisper_transcribe_lock:
            segments, info = model.transcribe(
                tmp_path,
                beam_size=1,
                vad_filter=True,
                condition_on_previous_text=False,
            )
        transcript = " ".join(seg.text.strip() for seg in segments)
        if not transcript.strip():
            raise ValueError("No speech could be recognized in the audio recording.")
        duration = info.duration if hasattr(info, "duration") else 0
        return {
            "transcript": transcript,
            "duration_seconds": round(duration, 2),
            "language": info.language if hasattr(info, "language") else "en",
        }
    finally:
        try:
            os.unlink(tmp_path)
        except OSError:
            pass


def analyze_speech(transcript: str, duration_seconds: float) -> Dict:
    """Analyze transcript for filler words, speaking speed, communication quality."""
    words = transcript.split()
    word_count = len(words)
    text_lower = transcript.lower()

    # Filler word detection
    found_fillers: Dict[str, int] = {}
    for fw in FILLER_WORDS:
        count = len(re.findall(r'\b' + re.escape(fw) + r'\b', text_lower))
        if count > 0:
            found_fillers[fw] = count
    total_fillers = sum(found_fillers.values())

    # Speaking speed (words per minute)
    wpm = round((word_count / duration_seconds) * 60) if duration_seconds > 0 else 0
    if wpm < 100:
        speed_label = "Too Slow"
    elif wpm <= 160:
        speed_label = "Good"
    elif wpm <= 200:
        speed_label = "Fast"
    else:
        speed_label = "Too Fast"

    # Communication score (simple heuristic)
    filler_penalty = min(total_fillers * 3, 30)
    speed_penalty = 0 if speed_label == "Good" else 10
    comm_score = max(0, 100 - filler_penalty - speed_penalty)

    return {
        "word_count": word_count,
        "words_per_minute": wpm,
        "speaking_speed": speed_label,
        "filler_words": found_fillers,
        "filler_word_count": total_fillers,
        "communication_score": comm_score,
    }


def build_transcript_entry(role: str, text: str, timestamp: str = None) -> Dict:
    from datetime import datetime
    return {
        "role": role,
        "text": text,
        "timestamp": timestamp or datetime.utcnow().isoformat(),
    }
