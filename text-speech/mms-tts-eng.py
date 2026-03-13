from transformers import pipeline
import soundfile as sf

tts = pipeline("text-to-speech", model="facebook/mms-tts-eng")

speech = tts("Oh! That's something I haven't heard before. Could you tell me a little more about it?")

sf.write("speech.wav", speech["audio"], speech["sampling_rate"])