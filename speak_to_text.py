import os
import re
import shutil
import subprocess
import tempfile
import time
from dotenv import load_dotenv

load_dotenv()

SOX = r"C:\Program Files (x86)\sox-14-4-2\sox.exe"
MODEL_NAME = "small"   # used only when TRANSCRIBE_BACKEND=local
COPY_TO_CLIPBOARD = True
STOP_WORD = "period"
SOX_INPUT_DEVICE = os.environ.get("SOX_INPUT_DEVICE", "default")
ACTIVE_SOX_INPUT_DEVICE = SOX_INPUT_DEVICE
# Only act on speech that starts with this word.
# Say "hey check the status" → outputs "check the status"
# Anything without "hey" at the start is silently ignored.
WAKE_WORD = os.environ.get("WAKE_WORD", "")  # empty = respond to all speech

# ---------------------------------------------------------------------------
# Transcription backend
# Set TRANSCRIBE_BACKEND=local   → local openai-whisper model (default)
# Set TRANSCRIBE_BACKEND=openai  → OpenAI Whisper API (requires OPENAI_API_KEY)
# Set TRANSCRIBE_BACKEND=custom  → Local OpenAI-compatible server (TRANSCRIBE_URL)
# ---------------------------------------------------------------------------
TRANSCRIBE_BACKEND = os.environ.get("TRANSCRIBE_BACKEND", "local").lower()
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
TRANSCRIBE_URL = os.environ.get("TRANSCRIBE_URL", "http://localhost:8000/inference")


def check_dependencies() -> None:
    if not os.path.exists(SOX):
        raise FileNotFoundError(f"SoX not found at: {SOX}")
    if TRANSCRIBE_BACKEND == "openai" and not OPENAI_API_KEY:
        raise EnvironmentError(
            "TRANSCRIBE_BACKEND=openai requires OPENAI_API_KEY to be set."
        )


def _post_audio_multipart(url: str, wav_path: str, extra_headers: dict | None = None) -> str:
    """POST wav_path as multipart/form-data to url. Returns transcribed text."""
    import urllib.request
    import json
    with open(wav_path, "rb") as f:
        audio_bytes = f.read()
    boundary = "----WavBoundary"
    whisper_prompt = os.environ.get("WHISPER_PROMPT", "")
    prompt_part = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="prompt"\r\n\r\n'
        f"{whisper_prompt}\r\n"
    ) if whisper_prompt else ""
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="model"\r\n\r\n'
        f"whisper-1\r\n"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="language"\r\n\r\n'
        f"en\r\n"
        f"{prompt_part}"
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="file"; filename="audio.wav"\r\n'
        f"Content-Type: audio/wav\r\n\r\n"
    ).encode() + audio_bytes + f"\r\n--{boundary}--\r\n".encode()
    headers = {"Content-Type": f"multipart/form-data; boundary={boundary}"}
    if extra_headers:
        headers.update(extra_headers)
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    with urllib.request.urlopen(req, timeout=60) as resp:
        data = json.loads(resp.read().decode())
        # whisper.cpp returns {"text": ...}, OpenAI also returns {"text": ...}
        return (data.get("text") or data.get("results", [{}])[0].get("transcript", "")).strip()


def transcribe(wav_path: str) -> str:
    """Transcribe wav_path using the configured backend. Returns text string."""
    if TRANSCRIBE_BACKEND == "openai":
        return _post_audio_multipart(
            "https://api.openai.com/v1/audio/transcriptions",
            wav_path,
            extra_headers={"Authorization": f"Bearer {OPENAI_API_KEY}"},
        )
    elif TRANSCRIBE_BACKEND == "custom":
        return _post_audio_multipart(TRANSCRIBE_URL, wav_path)
    else:
        import whisper as _whisper
        if not hasattr(transcribe, "_model"):
            transcribe._model = _whisper.load_model(MODEL_NAME)
        result = transcribe._model.transcribe(wav_path, language="en")
        return (result.get("text") or "").strip()


def copy_text_to_clipboard(text: str) -> None:
    if not text or not COPY_TO_CLIPBOARD:
        return
    subprocess.run("clip", input=text, text=True, check=False, shell=True)


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
            "highpass", "100",   # strip low-frequency rumble (bus/AC noise)
            "silence",
            "1",
            "0.1",
            "10%",
            "1",
            "1.0",
            "10%",
        ]
        # Use Popen so we can hard-kill SoX if it never detects trailing silence
        # (happens when ambient noise stays above threshold continuously).
        MAX_RECORD_SECS = 8
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        try:
            stdout, stderr = proc.communicate(timeout=MAX_RECORD_SECS)
            return subprocess.CompletedProcess(cmd, proc.returncode, stdout.decode(errors="replace"), stderr.decode(errors="replace"))
        except subprocess.TimeoutExpired:
            proc.kill()
            proc.wait()
            # WAV file may have been partially written — that's fine, whisper handles it
            return subprocess.CompletedProcess(cmd, 0, "", "")


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
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()
    return normalized == STOP_WORD


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
                    # Skip whisper ambient sound labels like (engine revving), [BLANK_AUDIO]
                    stripped = text.strip()
                    if stripped.startswith(("[", "(")) and stripped.endswith(("]", ")")):
                        continue
                    print(f"Heard: {text}")
                    if should_stop_listener(text):
                        print("Voice stop command received. Listener stopped.")
                        break
                    # Only act if the phrase starts with the wake word
                    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower()).strip()
                    if WAKE_WORD and not normalized.startswith(WAKE_WORD):
                        print("(ignored — no wake word)\n")
                        continue
                    # Strip the wake word and use the rest
                    command = text[text.lower().find(WAKE_WORD) + len(WAKE_WORD):].strip() if WAKE_WORD else text
                    if command:
                        print(f"You said: {command}")
                        copy_text_to_clipboard(command)
                        if COPY_TO_CLIPBOARD:
                            print("Copied to clipboard.\n")
        except KeyboardInterrupt:
            print("\nListener stopped.")


if __name__ == "__main__":
    main()
