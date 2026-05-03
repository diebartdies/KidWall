$ErrorActionPreference = "Stop"
$root = "D:\kidwall"
Set-Location $root

$python = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) {
    Write-Error "Python venv not found at $python"
}

& $python "D:\kidwall\speak_to_text.py"
