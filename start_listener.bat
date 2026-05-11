@echo off
cd /d D:\kidwall
call D:\kidwall\.venv\Scripts\activate.bat
for /f "usebackq tokens=1,* delims==" %%A in ("D:\kidwall\.env") do (
    if /i "%%A"=="OPENAI_API_KEY" set "OPENAI_API_KEY=%%B"
    if /i "%%A"=="TRANSCRIBE_BACKEND" set "TRANSCRIBE_BACKEND=%%B"
    if /i "%%A"=="TRANSCRIBE_URL" set "TRANSCRIBE_URL=%%B"
    if /i "%%A"=="SOX_INPUT_DEVICE" set "SOX_INPUT_DEVICE=%%B"
    if /i "%%A"=="WAKE_WORD" set "WAKE_WORD=%%B"
)
if not defined TRANSCRIBE_BACKEND set "TRANSCRIBE_BACKEND=custom"
if not defined TRANSCRIBE_URL set "TRANSCRIBE_URL=http://localhost:8000/inference"
python D:\kidwall\speak_to_text.py
