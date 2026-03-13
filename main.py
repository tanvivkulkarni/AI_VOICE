import os
import tempfile
from pathlib import Path

import httpx
from dotenv import load_dotenv

load_dotenv()
from fastapi import FastAPI, Request
from fastapi.responses import Response, FileResponse
from pydantic import BaseModel
from twilio.twiml.voice_response import VoiceResponse

from state import SessionState
from services.stt import speech_to_text
from services.tts import text_to_speech
from services.llm import detect_intent, generate_response
from flow import handle_intent

app = FastAPI()

GREETING_TEXT = "Hello, this is your AI tutor. How can I help you today? you can ask me anything about the course or any other question you have."
AUDIO_CACHE_DIR = Path("audio_cache")
GREETING_WAV = AUDIO_CACHE_DIR / "greeting.wav"

call_states: dict[str, SessionState] = {}


def _get_state(call_sid: str) -> SessionState:
    if call_sid not in call_states:
        call_states[call_sid] = SessionState(str(call_sid), str(call_sid))
    return call_states[call_sid]


def _ensure_greeting_audio() -> None:
    print("Ensuring greeting audio...")
    """Send greeting text to text_to_speech(); cache WAV so it can be played."""
    AUDIO_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    if not GREETING_WAV.exists():
        print("[twilio-voice] Generating greeting with text_to_speech...")
        text_to_speech(GREETING_TEXT, str(GREETING_WAV))
        print("[twilio-voice] Greeting saved to", GREETING_WAV)

@app.get("/audio/greeting")
def serve_greeting_audio():
    print("Serving greeting audio...")
    """Serve the greeting WAV so Twilio can play it (caller hears TTS response)."""
    _ensure_greeting_audio()
    return FileResponse(GREETING_WAV, media_type="audio/wav")


@app.api_route("/twilio-voice", methods=["GET", "POST"])
async def twilio_voice(request: Request):
    print("Twilio voice API route called...")
    """TwiML for when a call connects. Greeting is from text_to_speech(), so caller hears it."""
    print("[twilio-voice] Webhook called by Twilio")
    _ensure_greeting_audio()

    base_url = (os.environ.get("NGROK_URL") or "").strip().rstrip("/")
    response = VoiceResponse()
    if base_url:
        # Play TTS-generated greeting so the response is heard
        print(f"{base_url}/audio/greeting")
        response.play(f"{base_url}/audio/greeting")
    else:
        response.say(GREETING_TEXT, voice="alice", language="en-US")
      

    response.record(
        action="/process-speech",
        method="POST",
        max_length=10
    )
    twiml = str(response)
    print("[twilio-voice] Returning TwiML length:", len(twiml))
    return Response(content=twiml, media_type="application/xml")


@app.post("/process-speech")
async def process_speech(request: Request):
    print("Processing speech...")
    """Twilio calls this after recording. Run same pipeline as /voice and return TwiML to play response."""
    body = await request.form()
    recording_url = body.get("RecordingUrl")
    call_sid = body.get("CallSid", "unknown")

    if not recording_url:
        response = VoiceResponse()
        response.say("Sorry, I didn't receive any recording.")
        return Response(content=str(response), media_type="application/xml")

    # Twilio serves WAV when you append .wav; download requires Basic auth
    account_sid = os.environ.get("TWILIO_ACCOUNT_SID")
    auth_token = os.environ.get("TWILIO_AUTH_TOKEN")
    if not account_sid or not auth_token:
        response = VoiceResponse()
        response.say("Server is not configured for Twilio.")
        return Response(content=str(response), media_type="application/xml")

    download_url = f"{recording_url}.wav" if not recording_url.lower().endswith(".wav") else recording_url
    state = _get_state(call_sid)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
        tmp_path = tmp.name
    try:
        async with httpx.AsyncClient() as client:
            r = await client.get(
                download_url,
                auth=(account_sid, auth_token),
                timeout=30.0
            )
            r.raise_for_status()
            Path(tmp_path).write_bytes(r.content)
    except Exception as e:
        print(f"Download recording failed: {e}")
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        response = VoiceResponse()
        response.say("Sorry, I couldn't process the recording.")
        return Response(content=str(response), media_type="application/xml")

    # Same pipeline as /voice: STT -> intent -> flow/LLM -> TTS
    try:
        user_text = speech_to_text(tmp_path)
    except Exception as e:
        print(f"STT failed: {e}")
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)
        response = VoiceResponse()
        response.say("Sorry, I couldn't understand that.")
        response.record(action="/process-speech", method="POST", max_length=10)
        return Response(content=str(response), media_type="application/xml")
    finally:
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)

    print(f"User said: {user_text}")
    intent = detect_intent(user_text)
    # print(f"Detected intent: {intent}")

    import random
    import asyncio

    WAIT_PHRASES = [
        "Just a moment while I check that.",
        "Let me look that up for you.",
        "Give me a second."
    ]

    wait_phrase = random.choice(WAIT_PHRASES)

    # ------------------------
    # Generate Response
    # ------------------------

    if intent in ["Other", "Requesting Information"]:

        task = asyncio.create_task(generate_response(intent, user_text))

        try:
            bot_response = await asyncio.wait_for(task, timeout=4)

        except asyncio.TimeoutError:
            print("LLM taking too long → sending wait phrase")

            response.say(wait_phrase)

            response.record(
                action="/process-speech",
                method="POST",
                max_length=10
            )

            return Response(content=str(response), media_type="application/xml")

    else:
        bot_response = handle_intent(intent, user_text, state)

    print(f"Bot response: {bot_response}")

    response = VoiceResponse()
    # response.say(bot_response)
    base_url = (os.environ.get("NGROK_URL") or "").strip().rstrip("/")
    text_to_speech(bot_response, "audio_cache/response.wav")
    response.record(action="/process-speech", method="POST", max_length=10)

    if base_url:
        # Play TTS-generated greeting so the response is heard
        print(f"{base_url}/audio/response.wav")
        response.play(f"{base_url}/audio/response.wav")
    else:
        response.say(GREETING_TEXT, voice="alice", language="en-US")

    return Response(content=str(response), media_type="application/xml")
