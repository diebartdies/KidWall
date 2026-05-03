import os
import re
import shutil
import subprocess
import tempfile
import time

import whisper

SOX = r"C:\Program Files (x86)\sox-14-4-2\sox.exe"
MODEL_NAME = "small"   # better accuracy than "base", still fast
COPY_TO_CLIPBOARD = True
STOP_WORD = "period"
# Only act on speech that starts with this word.
# Say "hey check the status" → outputs "check the status"
# Anything without "hey" at the start is silently ignored.
WAKE_WORD = "hey"


def check_dependencies() -> None:
    if not os.path.exists(SOX):
        raise FileNotFoundError(f"SoX not found at: {SOX}")


def copy_text_to_clipboard(text: str) -> None:
    if not text or not COPY_TO_CLIPBOARD:
        return
    clip = shutil.which("clip")
    if not clip:
        return
    subprocess.run(clip, input=text, text=True, check=False)


def record_one_phrase(output_wav: str) -> None:
    # Wait for voice input and stop after trailing silence.
    cmd = [
        SOX,
        "-q",
        "-d",
        "-r",
        "16000",
        "-c",
        "1",
        output_wav,
        "silence",
        "1",
        "0.1",
        "1%",
        "1",
        "1.0",
        "1%",
    ]
    subprocess.run(cmd, check=False)


def should_stop_listener(text: str) -> bool:
    normalized = re.sub(r"[^a-z0-9\s]", " ", text.lower())
    words = normalized.split()
    return STOP_WORD in words


def main() -> None:
    check_dependencies()
    print("Always-on listener started. Speak a phrase and pause.")
    print("Say 'period' to stop, or press Ctrl+C.\n")

    print(f"Loading Whisper model: {MODEL_NAME} ...")
    model = whisper.load_model(MODEL_NAME)
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

                result = model.transcribe(wav_path, language="en")
                text = (result.get("text") or "").strip()
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
