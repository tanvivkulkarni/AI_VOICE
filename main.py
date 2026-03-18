import asyncio
import base64
import json
import os

import websockets
from dotenv import load_dotenv
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.responses import Response

load_dotenv()

app = FastAPI()

DEEPGRAM_API_KEY = os.environ.get("DEEPGRAM_API_KEY")
NGROK_URL = (os.environ.get("NGROK_URL") or "").strip().rstrip("/")

# Agent prompt — replace the old LLM system prompt
AGENT_PROMPT = """You are a health assistant chatbot.

Rules:
- Give short, clear responses.
- Be helpful and supportive.
- Do not provide medical diagnosis.
- Focus only on general wellness advice.
- You can help with: calorie tracking, diet plans, step counting,
  distance tracking, calorie burn goals, and general health questions.
- Keep responses under 2 sentences."""

AGENT_GREETING = "Hello, this is your Health checker app. How may I help you?"


def _deepgram_agent_config() -> dict:
    """Build the Deepgram Voice Agent Settings message for Twilio (mulaw 8kHz)."""
    return {
        "type": "Settings",
        "audio": {
            "input": {
                "encoding": "mulaw",
                "sample_rate": 8000,
            },
            "output": {
                "encoding": "mulaw",
                "sample_rate": 8000,
                "container": "none",
            },
        },
        "agent": {
            "language": "en",
            "listen": {
                "provider": {
                    "type": "deepgram",
                    "model": "nova-3",
                }
            },
            "think": {
                "provider": {
                    "type": "open_ai",
                    "model": "gpt-4o-mini",
                    "temperature": 0.7,
                },
                "prompt": AGENT_PROMPT,
            },
            "speak": {
                "provider": {
                    "type": "deepgram",
                    "model": "aura-2-thalia-en",
                }
            },
            "greeting": AGENT_GREETING,
        },
    }


# ---------------------------------------------------------------------------
# Twilio webhook — returns TwiML that opens a Media Stream to our WS endpoint
# ---------------------------------------------------------------------------

@app.api_route("/twilio-voice", methods=["GET", "POST"])
async def twilio_voice(request: Request):
    """Return TwiML that connects the call to a bidirectional Media Stream."""
    print("[twilio-voice] Webhook called")

    # Build the WebSocket URL Twilio will connect to
    ws_url = NGROK_URL.replace("https://", "wss://").replace("http://", "ws://")
    stream_url = f"{ws_url}/twilio-media-stream"

    twiml = f"""<?xml version="1.0" encoding="UTF-8"?>
<Response>
    <Connect>
        <Stream url="{stream_url}" />
    </Connect>
</Response>"""

    print(f"[twilio-voice] Stream URL: {stream_url}")
    return Response(content=twiml, media_type="application/xml")


# ---------------------------------------------------------------------------
# WebSocket endpoint — bridges Twilio Media Stream ↔ Deepgram Voice Agent
# ---------------------------------------------------------------------------

@app.websocket("/twilio-media-stream")
async def twilio_media_stream(twilio_ws: WebSocket):
    """Bridge audio between Twilio and the Deepgram Voice Agent API."""
    await twilio_ws.accept()
    print("[ws] Twilio media stream connected")

    audio_queue: asyncio.Queue[bytes] = asyncio.Queue()
    streamsid_queue: asyncio.Queue[str] = asyncio.Queue()

    async with websockets.connect(
        "wss://agent.deepgram.com/v1/agent/converse",
        subprotocols=["token", DEEPGRAM_API_KEY],
    ) as dg_ws:
        # Send agent configuration
        await dg_ws.send(json.dumps(_deepgram_agent_config()))
        print("[ws] Sent Deepgram Agent config")

        # --- Task: forward buffered audio from queue → Deepgram ---
        async def send_audio_to_deepgram():
            while True:
                chunk = await audio_queue.get()
                await dg_ws.send(chunk)

        # --- Task: receive from Deepgram → forward to Twilio ---
        async def receive_from_deepgram():
            streamsid = await streamsid_queue.get()
            async for message in dg_ws:
                if isinstance(message, str):
                    # Text message (JSON event)
                    data = json.loads(message)
                    msg_type = data.get("type", "")
                    print(f"[dg] {msg_type}")

                    # Barge-in: clear queued audio when user starts speaking
                    if msg_type == "UserStartedSpeaking":
                        await twilio_ws.send_json({
                            "event": "clear",
                            "streamSid": streamsid,
                        })
                    continue

                # Binary message → agent TTS audio (raw mulaw)
                media_msg = {
                    "event": "media",
                    "streamSid": streamsid,
                    "media": {
                        "payload": base64.b64encode(message).decode("ascii"),
                    },
                }
                await twilio_ws.send_json(media_msg)

        # --- Task: receive from Twilio → buffer into queue ---
        async def receive_from_twilio():
            BUFFER_SIZE = 20 * 160  # 20 messages × 160 bytes (20ms each)
            inbuffer = bytearray()
            try:
                while True:
                    raw = await twilio_ws.receive_text()
                    data = json.loads(raw)
                    event = data.get("event")

                    if event == "start":
                        streamsid = data["start"]["streamSid"]
                        print(f"[tw] Stream started: {streamsid}")
                        streamsid_queue.put_nowait(streamsid)
                    elif event == "media":
                        chunk = base64.b64decode(data["media"]["payload"])
                        if data["media"].get("track") == "inbound":
                            inbuffer.extend(chunk)
                    elif event == "stop":
                        print("[tw] Stream stopped")
                        break
                    elif event == "connected":
                        print("[tw] Connected")
                        continue

                    # Flush buffer when large enough
                    while len(inbuffer) >= BUFFER_SIZE:
                        audio_queue.put_nowait(bytes(inbuffer[:BUFFER_SIZE]))
                        inbuffer = inbuffer[BUFFER_SIZE:]
            except WebSocketDisconnect:
                print("[tw] Twilio disconnected")

        # Run all three tasks concurrently
        tasks = [
            asyncio.create_task(send_audio_to_deepgram()),
            asyncio.create_task(receive_from_deepgram()),
            asyncio.create_task(receive_from_twilio()),
        ]

        # When any task finishes (e.g. Twilio hangs up), cancel the rest
        done, pending = await asyncio.wait(tasks, return_when=asyncio.FIRST_COMPLETED)
        for t in pending:
            t.cancel()

    print("[ws] Session ended")
