from faster_whisper import WhisperModel
from deepgram import DeepgramClient
from dotenv import load_dotenv

import os

load_dotenv()

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")


def _deepgram_stt(audio_file: str) -> str:
    deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)

    with open(audio_file, "rb") as f:
        audio_data = f.read()

    response = deepgram.listen.v1.media.transcribe_file(
        request=audio_data,
        model="nova-3",
        smart_format=True,
        language="en",
    )

    transcript = response.results.channels[0].alternatives[0].transcript
    return transcript if transcript else "[No speech detected]"


def _whisper_stt(audio_file: str) -> str:
    model = WhisperModel("base", device="cpu", compute_type="int8")
    segments, info = model.transcribe(audio_file)
    text = "".join([segment.text.strip() + " " for segment in segments]).strip()
    return text if text else "[No speech detected]"


def speech_to_text(audio_file: str) -> str:
    print("Converting speech to text...")

    if not os.path.isfile(audio_file):
        raise FileNotFoundError(f"audio file not found: {audio_file}")

    try:
        print("Using Deepgram STT...")
        return _deepgram_stt(audio_file)
    except Exception as e:
        print(f"Deepgram failed: {e}, falling back to Whisper...")
        return _whisper_stt(audio_file)
