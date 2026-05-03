# Kidwall Quick-Start Script
# Starts all project components: DB, Backend API, Parents App
# Note: Ingress-nginx-controller runs separately in Kubernetes

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kidwall Project - Quick Start" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker is running
Write-Host "[1/3] Checking Docker..." -ForegroundColor Yellow
try {
    docker ps > $null 2>&1
    Write-Host "[OK] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Start services
Write-Host "[2/3] Starting Docker Compose services..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Services started" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to start services" -ForegroundColor Red
    exit 1
}

# Wait and check status
Write-Host "[3/3] Checking service status..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

Write-Host ""
Write-Host "Docker Compose Services:" -ForegroundColor Cyan
Write-Host "----------------------------------------"

docker-compose ps

Write-Host ""
Write-Host "Kubernetes Ingress-nginx Status:" -ForegroundColor Cyan
Write-Host "----------------------------------------"

try {
    $nginxPods = kubectl get pods -n ingress-nginx --no-headers 2>$null | Select-Object -First 3
    if ($nginxPods) {
        Write-Host $nginxPods -ForegroundColor White
    } else {
        Write-Host "[INFO] Ingress-nginx not found in cluster" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] kubectl not available or cluster not running" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Access your services:" -ForegroundColor Cyan
Write-Host "  * Backend API:    http://localhost:8000" -ForegroundColor White
Write-Host "  * API Docs:       http://localhost:8000/docs" -ForegroundColor White
Write-Host "  * Parents App:    http://localhost:8080" -ForegroundColor White
Write-Host "  * Database:       localhost:5433" -ForegroundColor White
Write-Host "  * Ingress Route:  http://your-ingress-domain" -ForegroundColor White
Write-Host ""
Write-Host "[OK] All services ready!" -ForegroundColor Green
