from TTS.api import TTS


print("Loading model...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", gpu=False)

print("Generating audio...")

tts.tts_to_file(
    text="Hello, this is a test of the Coqui TTS library. This model supports multiple languages and can generate high-quality speech. I hope you find it useful for your projects!",
    file_path="output2.wav",
    speaker_wav="sample2.wav",
    language="en"
)

print("Audio saved as output.wav")