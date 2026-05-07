@echo off
cd /d D:\kidwall
call D:\kidwall\.venv\Scripts\activate.bat
set "TRANSCRIBE_BACKEND=openai"
for /f "usebackq tokens=1,* delims==" %%A in ("D:\kidwall\.env") do (
    if /i "%%A"=="OPENAI_API_KEY" set "OPENAI_API_KEY=%%B"
    if /i "%%A"=="SOX_INPUT_DEVICE" set "SOX_INPUT_DEVICE=%%B"
)
set "SOX_INPUT_DEVICE=Microphone (High Definition Audio Device)"
python D:\kidwall\speak_to_text.py
