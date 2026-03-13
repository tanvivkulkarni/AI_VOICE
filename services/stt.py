from faster_whisper import WhisperModel
import os


def speech_to_text(audio_file: str) -> str:
    print("Converting speech to text...")
    """
    Convert speech to text using OpenAI's Whisper model (offline).
    Supports WAV, MP3, FLAC, OGG, and other common formats.
    """
    # ensure the file exists
    if not os.path.isfile(audio_file):
        raise FileNotFoundError(f"audio file not found: {audio_file}")

    # load a lightweight Whisper model (base = ~140MB)
    # options: tiny, base, small, medium, large
    # larger = better accuracy, slower; tiny = fastest, lower accuracy
    try:
        model = WhisperModel("base", device="cpu", compute_type="int8")
    except Exception as e:
        raise RuntimeError(f"failed to load Whisper model: {e}")

    try:
        # transcribe the audio file
        segments, info = model.transcribe(audio_file)
        # combine all segments into a single text
        text = "".join([segment.text.strip() + " " for segment in segments]).strip()
        return text if text else "[No speech detected]"
    except Exception as e:
        raise RuntimeError(f"speech recognition failed for {audio_file}: {e}")
