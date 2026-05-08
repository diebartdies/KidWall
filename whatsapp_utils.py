"""
Twilio WhatsApp helper.

Set in .env:
  TWILIO_ACCOUNT_SID=ACxxxx
  TWILIO_AUTH_TOKEN=xxxx
  TWILIO_WHATSAPP_FROM=whatsapp:+14155238886   (sandbox) or your approved number
  TWILIO_CALL_FROM=+15005550006                (Twilio voice number)
  TWILIO_TWIML_SAY_VOICE=Polly.Joanna         (optional, any Twilio/Polly voice)
"""
import os
from dotenv import load_dotenv

load_dotenv()

_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID", "")
_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN", "")
_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")
_CALL_FROM = os.getenv("TWILIO_CALL_FROM", "")
_CALL_VOICE = os.getenv("TWILIO_TWIML_SAY_VOICE", "Polly.Joanna")


def _get_client():
    if not _ACCOUNT_SID or not _AUTH_TOKEN:
        raise RuntimeError(
            "Twilio credentials not configured. "
            "Set TWILIO_ACCOUNT_SID and TWILIO_AUTH_TOKEN in .env"
        )
    from twilio.rest import Client
    return Client(_ACCOUNT_SID, _AUTH_TOKEN)


def _normalize_number(to_number: str, country_code: str) -> str:
    cc = country_code.strip()
    if not cc.startswith("+"):
        cc = f"+{cc}"
    digits = "".join(c for c in to_number if c.isdigit())
    return f"{cc}{digits}"


def send_whatsapp(to_number: str, country_code: str, body: str) -> str:
    """
    Send a WhatsApp message via Twilio.
    Returns the Twilio message SID on success.
    """
    client = _get_client()
    full_number = f"whatsapp:{_normalize_number(to_number, country_code)}"
    message = client.messages.create(
        from_=_FROM,
        to=full_number,
        body=body,
    )
    return message.sid


def make_voice_call(to_number: str, country_code: str, spoken_message: str) -> str:
    """
    Place an automated voice call via Twilio that reads `spoken_message` aloud.
    Requires TWILIO_CALL_FROM in .env.
    Returns the Twilio call SID on success.
    """
    if not _CALL_FROM:
        raise RuntimeError(
            "TWILIO_CALL_FROM not set in .env. "
            "Add your Twilio voice number (e.g. +15005550006)."
        )
    client = _get_client()
    full_number = _normalize_number(to_number, country_code)

    # TwiML: say the message twice so the recipient doesn't miss it
    twiml = (
        f"<Response>"
        f"<Say voice='{_CALL_VOICE}' loop='2'>{spoken_message}</Say>"
        f"</Response>"
    )

    call = client.calls.create(
        twiml=twiml,
        to=full_number,
        from_=_CALL_FROM,
    )
    return call.sid
