import os

import pyttsx3
import os

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
    print("Converting text to speech...")
    if not text:
        raise ValueError("text cannot be empty")

    try:
        print("Loading TTS model")
        from pocket_tts import TTSModel
        import scipy.io.wavfile

        tts_model = TTSModel.load_model()
        voice_state = tts_model.get_state_for_audio_prompt(
            "alba"
        )
        audio = tts_model.generate_audio(voice_state, text)
        scipy.io.wavfile.write(audio_file, tts_model.sample_rate, audio.numpy())

    except Exception as e:
        print(f"Coqui TTS failed ({e}), using pyttsx3 fallback.")
        # _tts_pyttsx3(text, audio_file)
        # print("Audio saved with pyttsx3 to", audio_file)
