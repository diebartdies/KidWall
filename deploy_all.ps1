# PowerShell script to automate build, sync, container, and deployment for KidWall

# Ensure we always run from the KidWall root regardless of where the script was invoked from
Set-Location -Path $PSScriptRoot

# 0. Backup .env locally
if (Test-Path ".env") {
    $envBackupDir = "$PSScriptRoot\backups"
    if (-not (Test-Path $envBackupDir)) { New-Item -ItemType Directory -Path $envBackupDir | Out-Null }
    Copy-Item ".env" "$envBackupDir\.env.backup" -Force
    Write-Host ".env backed up to $envBackupDir\.env.backup"
} else {
    Write-Warning ".env not found - skipping backup."
}

# 1. Verify Flutter/Android toolchain and build/recompile APKs.
# Do not run `flutter upgrade` here: deployment must be reproducible, and an
# automatic SDK upgrade can break Android plugin/Gradle compatibility.
$apkBuildSucceeded = $false
Write-Host "Checking Flutter version..."
flutter --version
if ($LASTEXITCODE -ne 0) {
    Write-Warning "Flutter is not available or failed to report its version - skipping APK build and continuing."
} else {
    Write-Host "Building APKs with pinned project Android toolchain..."
    Set-Location -Path "d:/kidwall/colepago-parents-app"
    try {
        & ".\build_both_apks.ps1"
        if ($LASTEXITCODE -ne 0) {
            Write-Warning "APK build failed - continuing with non-APK deployment steps."
        } else {
            $apkBuildSucceeded = $true
        }
    } catch {
        Write-Warning "APK build failed - continuing with non-APK deployment steps. $($_.Exception.Message)"
    } finally {
        Set-Location -Path "d:/kidwall"
    }
}

# 2. Sync all code to GitHub (force push all branches)
git add .
git commit -m "Automated sync and deployment"
git push -f origin main
git checkout colepago
git push -f origin colepago
git checkout colepago-parents-app
git push -f origin colepago-parents-app
git checkout colepagokidwall
git push -f origin colepagokidwall
git checkout main

# 3. Start local DB container, backup, and run migrations
Write-Host "Starting local Postgres container..."
Set-Location -Path "d:/kidwall"
docker-compose up -d db

Write-Host "Waiting for Postgres to be ready before backup..."
$retries = 10
while ($retries -gt 0) {
    $ready = docker exec kidwall_db pg_isready -U colepago 2>&1
    if ($ready -match "accepting connections") { break }
    Start-Sleep -Seconds 2
    $retries--
}

$backupDir = "D:\backups\colepago"
if (-not (Test-Path $backupDir)) { New-Item -ItemType Directory -Path $backupDir | Out-Null }
$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
$backupFile = "$backupDir/colepago_$timestamp.sql"
Write-Host "Backing up database to $backupFile ..."
docker exec kidwall_db pg_dump -U colepago colepago | Out-File -Encoding utf8 $backupFile
if ($LASTEXITCODE -eq 0) {
    Write-Host "Backup saved: $backupFile"
    # Keep only the 10 most recent backups
    Get-ChildItem $backupDir -Filter "colepago_*.sql" |
        Sort-Object LastWriteTime -Descending |
        Select-Object -Skip 10 |
        Remove-Item -Force
} else {
    Write-Warning "Backup failed - aborting deployment to protect data."
    exit 1
}

Write-Host "Waiting for Postgres to be ready..."
$retries = 10
while ($retries -gt 0) {
    $ready = docker exec kidwall_db pg_isready -U colepago 2>&1
    if ($ready -match "accepting connections") { break }
    Start-Sleep -Seconds 2
    $retries--
}

Write-Host "Running Alembic migrations..."
.venv\Scripts\alembic upgrade head

# 4. Restart backend (kill existing python main.py if running, then start fresh)
Write-Host "Restarting backend..."
$backendPort = 8010
$listener = Get-NetTCPConnection -LocalPort $backendPort -State Listen -ErrorAction SilentlyContinue |
    Select-Object -First 1
if ($listener) {
    Write-Host "Stopping process using port $backendPort (PID $($listener.OwningProcess))..."
    Stop-Process -Id $listener.OwningProcess -Force -ErrorAction SilentlyContinue
}
Start-Process -NoNewWindow -FilePath ".venv\Scripts\python.exe" -ArgumentList "main.py"
Write-Host "Backend started on http://0.0.0.0:8010"

# 5. Build Docker image for wallet backend
Write-Host "Building Docker image for colepago..."
Set-Location -Path "d:/kidwall/colepago"
docker build -t colepago:latest .
Set-Location -Path "d:/kidwall"

# 6. Apply Terraform to deploy/update container
Write-Host "Applying Terraform deployment..."
Set-Location -Path "d:/kidwall/terraform"
terraform init
terraform apply -auto-approve
Set-Location -Path "d:/kidwall"

# 7. Update EasyDNS dynamic DNS records (if configured)
$dyndnsScript = Join-Path $PSScriptRoot "update_easydns_dyndns.ps1"
if (Test-Path $dyndnsScript) {
    try {
        Write-Host "Updating EasyDNS dynamic DNS records..."
        & $dyndnsScript
    } catch {
        Write-Warning "EasyDNS update skipped/failed: $($_.Exception.Message)"
    }
}

if ($apkBuildSucceeded) {
    Write-Host "All steps completed."
} else {
    Write-Warning "Deployment completed, but APK build failed or was interrupted. APK-related actions remain pending."
}

# ============================================================
# DEPLOYMENT SUMMARY
# ============================================================
$sep = "=" * 62
$publicIp = try { (Invoke-RestMethod -Uri "https://api.ipify.org" -TimeoutSec 5) } catch { "unavailable" }
$dbRunning  = (docker inspect -f '{{.State.Running}}' kidwall_db 2>$null) -eq "true"
$backendPid = (Get-NetTCPConnection -LocalPort 8010 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess
$ingressIp  = "172.18.0.5"

Write-Host ""
Write-Host $sep -ForegroundColor Cyan
Write-Host "  COLEPAGO DEPLOYMENT SUMMARY  $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')" -ForegroundColor Cyan
Write-Host $sep -ForegroundColor Cyan

Write-Host ""
Write-Host "  PUBLIC IP" -ForegroundColor Yellow
Write-Host "    $publicIp"

Write-Host ""
Write-Host "  WEB / STATIC FRONTEND" -ForegroundColor Yellow
Write-Host "    HTTPS : https://colepago-web.drsrv.net.ar"
Write-Host "    HTTP  : http://colepago-web.drsrv.net.ar"
Write-Host "    Local : http://localhost:8010"

Write-Host ""
Write-Host "  API BACKEND (FastAPI)" -ForegroundColor Yellow
Write-Host "    HTTPS : https://api.drsrv.net.ar/api"
Write-Host "    HTTP  : http://api.drsrv.net.ar/api"
Write-Host "    Local : http://localhost:8010/api"
Write-Host "    Docs  : http://localhost:8010/docs"
if ($backendPid) {
    Write-Host "    Status: RUNNING (PID $backendPid)" -ForegroundColor Green
} else {
    Write-Host "    Status: NOT DETECTED on port 8010" -ForegroundColor Red
}

Write-Host ""
Write-Host "  DATABASE (PostgreSQL)" -ForegroundColor Yellow
Write-Host "    Container : kidwall_db"
Write-Host "    Host      : localhost:5432"
Write-Host "    DB name   : colepago"
Write-Host "    User      : colepago"
if ($dbRunning) {
    Write-Host "    Status    : RUNNING" -ForegroundColor Green
} else {
    Write-Host "    Status    : STOPPED" -ForegroundColor Red
}

Write-Host ""
Write-Host "  KUBERNETES / NGINX INGRESS" -ForegroundColor Yellow
Write-Host "    Ingress IP     : $ingressIp"
Write-Host "    TLS secret     : colepago-web-drsrv-tls  -> colepago-web.drsrv.net.ar"
Write-Host "    TLS secret     : api-tls-secret           -> api.drsrv.net.ar"
Write-Host "    Namespace      : default"
$ingressStatus = kubectl get ingress 2>$null | Select-String -Pattern "ingress"
if ($ingressStatus) { $ingressStatus | ForEach-Object { Write-Host "    $_" } }

Write-Host ""
Write-Host "  FLUTTER APKs" -ForegroundColor Yellow
$kidsApk    = "d:/kidwall/colepago-parents-app/build/app/outputs/flutter-apk/app-kids-release.apk"
$parentsApk = "d:/kidwall/colepago-parents-app/build/app/outputs/flutter-apk/app-parents-release.apk"
if (Test-Path $kidsApk) {
    $sz = [math]::Round((Get-Item $kidsApk).Length / 1MB, 1)
    Write-Host "    Kids    : $kidsApk  ($sz MB)" -ForegroundColor Green
} else {
    Write-Host "    Kids    : NOT FOUND (build failed?)" -ForegroundColor Red
}
if (Test-Path $parentsApk) {
    $sz = [math]::Round((Get-Item $parentsApk).Length / 1MB, 1)
    Write-Host "    Parents : $parentsApk  ($sz MB)" -ForegroundColor Green
} else {
    Write-Host "    Parents : NOT FOUND (build failed?)" -ForegroundColor Red
}

Write-Host ""
Write-Host "  DOCKER IMAGES" -ForegroundColor Yellow
docker images colepago --format "    {{.Repository}}:{{.Tag}}  built {{.CreatedSince}}  ({{.Size}})"

Write-Host ""
Write-Host "  VOICE / SPEECH SERVICES" -ForegroundColor Yellow

# Whisper server (port 8000)
$whisperPid = (Get-NetTCPConnection -LocalPort 8000 -State Listen -ErrorAction SilentlyContinue | Select-Object -First 1).OwningProcess
$whisperExe  = "D:\tools\whisper.cpp\Release\whisper-server.exe"
$whisperModel = "D:\tools\whisper.cpp\ggml-small.en.bin"
Write-Host "    Whisper server  : http://localhost:8000/inference"
Write-Host "    Start script    : D:\kidwall\start_whisper_server.ps1"
Write-Host "    Model file      : $whisperModel  (exists: $(Test-Path $whisperModel))"
Write-Host "    Executable      : $whisperExe  (exists: $(Test-Path $whisperExe))"
if ($whisperPid) {
    Write-Host "    Status          : RUNNING (PID $whisperPid)" -ForegroundColor Green
} else {
    Write-Host "    Status          : STOPPED  (run .\start_whisper_server.ps1 to start)" -ForegroundColor Red
}

# Speech listener (speak_to_text.py)
$listenerProc = Get-Process python -ErrorAction SilentlyContinue |
    Where-Object { $_.CommandLine -match "speak_to_text" } |
    Select-Object -First 1
Write-Host "    Speech listener : D:\kidwall\speak_to_text.py"
Write-Host "    Start script    : D:\kidwall\start_listener.bat"
Write-Host "    Backend (env)   : TRANSCRIBE_BACKEND in .env  (default: local)"
Write-Host "    Sox audio       : C:\Program Files (x86)\sox-14-4-2\sox.exe  (exists: $(Test-Path 'C:\Program Files (x86)\sox-14-4-2\sox.exe'))"
if ($listenerProc) {
    Write-Host "    Status          : RUNNING (PID $($listenerProc.Id))" -ForegroundColor Green
} else {
    Write-Host "    Status          : STOPPED  (run .\start_listener.bat to start)" -ForegroundColor Red
}

Write-Host ""
Write-Host $sep -ForegroundColor Cyan
Write-Host ""
