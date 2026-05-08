# Starts whisper.cpp server for local transcription (no API charges)
# Listens on http://localhost:8000/v1/audio/transcriptions

$WhisperDir  = "D:\tools\whisper.cpp\Release"
$ModelFile   = "D:\tools\whisper.cpp\ggml-small.en.bin"
$ServerExe   = "$WhisperDir\whisper-server.exe"
$Port        = 8000

# --- Sanity checks ---
if (-not (Test-Path $ServerExe)) {
    Write-Error "whisper-server.exe not found at $ServerExe`nDownload from: https://github.com/ggml-org/whisper.cpp/releases/latest"
    exit 1
}

if (-not (Test-Path $ModelFile)) {
    Write-Host "Model not found. Downloading ggml-base.en.bin (~150 MB)..."
    New-Item -ItemType Directory -Force -Path $WhisperDir | Out-Null
    Invoke-WebRequest `
        -Uri "https://huggingface.co/ggerganov/whisper.cpp/resolve/main/ggml-base.en.bin" `
        -OutFile $ModelFile `
        -UseBasicParsing
    Write-Host "Download complete."
}

Write-Host "Starting whisper.cpp server on port $Port ..."
Write-Host "Press Ctrl+C to stop.`n"

& $ServerExe -m $ModelFile --port $Port --host 0.0.0.0
