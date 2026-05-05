# PyesowerShell script to automate build, sync, container, and deployment for KidWall

# Ensure we always run from the KidWall root regardless of where the script was invoked from
Set-Location -Path $PSScriptRoot

# 1. Upgrade Flutter if needed and build/recompile APKs
Write-Host "Checking for new Flutter version..."
flutter upgrade

Write-Host "Building APKs..."
Set-Location -Path "d:/kidwall/colepago-parents-app"
./build_both_apks.ps1
Set-Location -Path "d:/kidwall"

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
    Write-Warning "Backup failed — aborting deployment to protect data."
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

Write-Host "All steps completed."
