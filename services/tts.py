import os
import time

import pyttsx3

from dotenv import load_dotenv

load_dotenv()

def _tts_pyttsx3(text: str, audio_file: str) -> None:
    """Generate speech with pyttsx3 (no torch/torchaudio). Saves WAV to audio_file."""
    print("Generating speech with pyttsx3...")
    output_dir = os.path.dirname(audio_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    engine = pyttsx3.init()
    engine.save_to_file(text, audio_file)
    engine.runAndWait()


def text_to_speech(text: str, audio_file: str) -> None:
    """
    Convert text to speech. Tries Coqui TTS first; if that fails (e.g. torchaudio
    on Windows), falls back to pyttsx3 so the app still works.
    Saves the audio to the given WAV file.
    """
    start = time.perf_counter()
    print("Converting text to speech...")
    if not text:
        raise ValueError("text cannot be empty")

    try:
    #     print("Loading TTS model")
    #     from pocket_tts import TTSModel
    #     import scipy.io.wavfile

    #     tts_model = TTSModel.load_model()
    #     voice_state = tts_model.get_state_for_audio_prompt(
    #         "alba"
    #     )
    #     audio = tts_model.generate_audio(voice_state, text)
    #     scipy.io.wavfile.write(audio_file, tts_model.sample_rate, audio.numpy())
    #     elapsed = time.perf_counter() - start
    #     print(f"TTS completed in {elapsed:.2f}s")
        from deepgram import DeepgramClient
        DEEPGRAM_API_KEY = os.environ["DEEPGRAM_API_KEY"]
        deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)
        response = deepgram.speak.v1.audio.generate(
            text=text,
            model="aura-2-thalia-en",
            encoding="linear16",
            container="wav",
        )
        with open(audio_file, "wb") as f:
            for chunk in response:
                f.write(chunk)
        elapsed = time.perf_counter() - start
        print(f"TTS completed in {elapsed:.2f}s, audio saved to {audio_file}")

    except Exception as e:
        elapsed = time.perf_counter() - start
        print(f"TTS failed after {elapsed:.2f}s ({e})")
        _tts_pyttsx3(text, audio_file)
        print("Audio saved with pyttsx3 to", audio_file)

    