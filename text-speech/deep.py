from deepgram import DeepgramClient
import os
from dotenv import load_dotenv

load_dotenv()

DEEPGRAM_API_KEY = os.environ["DEEPGRAM_API_KEY"]

TEXT = "Your lab results show elevated cholesterol levels of 240 mg/dL; I recommend starting Atorvastatin 10 mg daily and scheduling a follow-up in eight weeks to reassess."
FILENAME = "deepgram_out.mp3"


def main():
    try:
        deepgram = DeepgramClient(api_key=DEEPGRAM_API_KEY)

        response = deepgram.speak.v1.audio.generate(
            text=TEXT,
            model="aura-2-thalia-en",
            encoding="mp3",
        )

        with open(FILENAME, "wb") as f:
            for chunk in response:
                f.write(chunk)

        print(f"Audio saved to {FILENAME}")

    except Exception as e:
        print(f"Exception: {e}")


if __name__ == "__main__":
    main()