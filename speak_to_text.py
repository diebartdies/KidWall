import os
import re
import shutil
import subprocess
import tempfile
import time

SOX = r"C:\Program Files (x86)\sox-14-4-2\sox.exe"
MODEL_NAME = "small"   # used only when TRANSCRIBE_BACKEND=local
COPY_TO_CLIPBOARD = True
STOP_WORD = "period"
SOX_INPUT_DEVICE = os.environ.get("SOX_INPUT_DEVICE", "default")
ACTIVE_SOX_INPUT_DEVICE = SOX_INPUT_DEVICE
# Only act on speech that starts with this word.
# Say "hey check the status" → outputs "check the status"
# Anything without "hey" at the start is silently ignored.
WAKE_WORD = "hey"

# ---------------------------------------------------------------------------
# Transcription backend
# Set TRANSCRIBE_BACKEND=local   → local openai-whisper model (default)
# Set TRANSCRIBE_BACKEND=openai  → OpenAI Whisper API (requires OPENAI_API_KEY)
# ---------------------------------------------------------------------------
TRANSCRIBE_BACKEND = os.environ.get("TRANSCRIBE_BACKEND", "local").lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")


def check_dependencies() -> None:
    if not os.path.exists(SOX):
        raise FileNotFoundError(f"SoX not found at: {SOX}")
    if TRANSCRIBE_BACKEND == "openai" and not OPENAI_API_KEY:
        raise EnvironmentError(
            "TRANSCRIBE_BACKEND=openai requires OPENAI_API_KEY to be set."
        )


def transcribe(wav_path: str) -> str:
    """Transcribe wav_path using the configured backend. Returns text string."""
    if TRANSCRIBE_BACKEND == "openai":
        import urllib.request
        import json
        with open(wav_path, "rb") as f:
            audio_bytes = f.read()
        boundary = "----WavBoundary"
        body = (
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="model"\r\n\r\n'
            f"whisper-1\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="language"\r\n\r\n'
            f"en\r\n"
            f"--{boundary}\r\n"
            f'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
            f"Content-Type: audio/wav\r\n\r\n"
        ).encode() + audio_bytes + f"\r\n--{boundary}--\r\n".encode()
        req = urllib.request.Request(
            "https://api.openai.com/v1/audio/transcriptions",
            data=body,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": f"multipart/form-data; boundary={boundary}",
            },
            method="POST",
        )
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode()).get("text", "").strip()
    else:
        import whisper as _whisper
        if not hasattr(transcribe, "_model"):
            transcribe._model = _whisper.load_model(MODEL_NAME)
        result = transcribe._model.transcribe(wav_path, language="en")
        return (result.get("text") or "").strip()


def copy_text_to_clipboard(text: str) -> None:
    if not text or not COPY_TO_CLIPBOARD:
        return
    clip = shutil.which("clip")
    if not clip:
        return
    subprocess.run(clip, input=text, text=True, check=False)


def record_one_phrase(output_wav: str) -> None:
    global ACTIVE_SOX_INPUT_DEVICE

    # Wait for voice input and stop after trailing silence.
    def _run_record(device_name: str) -> subprocess.CompletedProcess:
        cmd = [
            SOX,
            "-q",
            "-t",
            "waveaudio",
            device_name,
            "-r",
            "16000",
            "-c",
            "1",
            output_wav,
            "silence",
            "1",
            "0.1",
            "3%",
            "1",
            "1.5",
            "3%",
        ]
        return subprocess.run(cmd, capture_output=True, text=True, check=False)

    proc = _run_record(ACTIVE_SOX_INPUT_DEVICE)
    if proc.returncode == 0:
        return

    err = (proc.stderr or "").strip()
    err_lower = err.lower()

    # If a specific configured device disappeared, fall back to default mic.
    if (
        ACTIVE_SOX_INPUT_DEVICE != "default"
        and "device was not found" in err_lower
    ):
        print(
            f"Warning: SoX input device '{ACTIVE_SOX_INPUT_DEVICE}' not found. "
            "Falling back to default device."
        )
        ACTIVE_SOX_INPUT_DEVICE = "default"
        proc = _run_record(ACTIVE_SOX_INPUT_DEVICE)
        if proc.returncode == 0:
            print("Using SoX input device: default")
            return
        err = (proc.stderr or "").strip()
        err_lower = err.lower()

    if "no default audio device configured" in err_lower and ACTIVE_SOX_INPUT_DEVICE == "default":
        raise RuntimeError(
            "SoX could not find a default microphone. Set one in Windows Sound settings "
            "or launch with SOX_INPUT_DEVICE set to a specific waveaudio device name."
        )
    raise RuntimeError(f"SoX recording failed: {err or 'unknown error'}")


def should_stop_listener(text: str) -> bool:
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    words = normalized.split()
    return STOP_WORD in words


def main() -> None:
    check_dependencies()
    print("Always-on listener started. Speak a phrase and pause.")
    print("Say 'period' to stop, or press Ctrl+C.\n")
    print(f"SoX input device: {ACTIVE_SOX_INPUT_DEVICE}")
    print(f"Transcription backend: {TRANSCRIBE_BACKEND}")

    if TRANSCRIBE_BACKEND == "local":
        print(f"Loading Whisper model: {MODEL_NAME} ...")
        import whisper as _whisper
        transcribe._model = _whisper.load_model(MODEL_NAME)
    print("Ready. Listening...\n")

    with tempfile.TemporaryDirectory() as tmp:
        wav_path = os.path.join(tmp, "phrase.wav")
        try:
            while True:
                if os.path.exists(wav_path):
                    os.remove(wav_path)

                record_one_phrase(wav_path)

                if not os.path.exists(wav_path) or os.path.getsize(wav_path) < 1000:
                    time.sleep(0.15)
                    continue

                text = transcribe(wav_path)
                if text:
                    print(f"Heard: {text}")
                    if should_stop_listener(text):
                        print("Voice stop command received. Listener stopped.")
                        break
                    # Only act if the phrase starts with the wake word
                    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()
                    if not normalized.startswith(WAKE_WORD):
                        print("(ignored — no wake word)\n")
                        continue
                    # Strip the wake word and use the rest
                    command = text[text.lower().find(WAKE_WORD) + len(WAKE_WORD):].strip()
                    if command:
                        print(f"You said: {command}")
                        copy_text_to_clipboard(command)
                        if COPY_TO_CLIPBOARD:
                            print("Copied to clipboard.\n")
        except KeyboardInterrupt:
            print("\nListener stopped.")


if __name__ == "__main__":
    main()
