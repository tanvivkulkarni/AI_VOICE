from twilio.rest import Client
import os
from dotenv import load_dotenv


load_dotenv()
def outbound_call():
    account_sid = os.getenv("TWILIO_ACCOUNT_SID")
    auth_token = os.getenv("TWILIO_AUTH_TOKEN")


    client=Client(account_sid, auth_token)
    ngrok_url = os.getenv("NGROK_URL")
    call = client.calls.create(
        to="+919537062674",
        from_="+13158093649",
        url=f"{ngrok_url}/twilio-voice"
    )

    print("Call SID:", call.sid)
    return call.sid


if __name__ == "__main__":
    outbound_call()