from kittentts import KittenTTS
m = KittenTTS("KittenML/kitten-tts-mini-0.8")
audio = m.generate("Hello, this is a test of the Kitten TTS library. This model supports multiple languages and can generate high-quality speech. I hope you find it useful for your projects!", voice='Bruno' )
# available_voices : ['Bella', 'Jasper', 'Luna', 'Bruno', 'Rosie', 'Hugo', 'Kiki', 'Leo']
# Save the audio
import soundfile as sf
sf.write('kitten.wav', audio, 24000)
