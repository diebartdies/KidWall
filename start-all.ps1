# Kidwall Auto-Startup Script
# Starts all project components: Docker Compose services + Kubernetes ingress-nginx

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Kidwall Project - Auto Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Docker is running
Write-Host "[1/6] Checking Docker..." -ForegroundColor Yellow
try {
    docker ps > $null 2>&1
    Write-Host "[OK] Docker is running" -ForegroundColor Green
} catch {
    Write-Host "[ERROR] Docker is not running. Please start Docker Desktop." -ForegroundColor Red
    exit 1
}

# Pull latest changes
Write-Host "[2/6] Pulling latest changes from git..." -ForegroundColor Yellow
try {
    git pull
    Write-Host "[OK] Git pull complete" -ForegroundColor Green
} catch {
    Write-Host "[WARN] Git pull failed (continuing anyway)" -ForegroundColor Yellow
}

# Stop existing containers
Write-Host "[3/6] Stopping existing Docker Compose containers..." -ForegroundColor Yellow
docker-compose down --remove-orphans 2>&1 | Out-Null
Write-Host "[OK] Existing containers stopped" -ForegroundColor Green

# Build images
Write-Host "[4/6] Building Docker images..." -ForegroundColor Yellow
docker-compose build --pull
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Images built successfully" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Build failed" -ForegroundColor Red
    Write-Host "[INFO] Re-run for verbose output: docker-compose build --pull --progress=plain" -ForegroundColor Yellow
    exit 1
}

# Start Docker Compose services
Write-Host "[5/6] Starting Docker Compose services..." -ForegroundColor Yellow
docker-compose up -d
if ($LASTEXITCODE -eq 0) {
    Write-Host "[OK] Docker Compose services started" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Failed to start Docker Compose services" -ForegroundColor Red
    exit 1
}

# Restart Kubernetes ingress-nginx
Write-Host "[6/6] Restarting Kubernetes ingress-nginx..." -ForegroundColor Yellow
try {
    kubectl rollout restart deployment/ingress-nginx-controller -n ingress-nginx 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[OK] Ingress-nginx restarted" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Could not restart ingress-nginx (cluster may not be running)" -ForegroundColor Yellow
    }
} catch {
    Write-Host "[WARN] kubectl not available or ingress-nginx not found" -ForegroundColor Yellow
}

# Wait for services to be ready
Write-Host ""
Write-Host "Waiting for services to be ready..." -ForegroundColor Yellow
Start-Sleep -Seconds 5

# Check service health
Write-Host ""
Write-Host "Docker Compose Service Status:" -ForegroundColor Cyan
Write-Host "----------------------------------------"

# Check Database
$dbStatus = docker ps --filter "name=kidwall_db" --format "{{.Status}}"
if ($dbStatus -match "healthy") {
    Write-Host "[OK] Database (PostgreSQL):    HEALTHY" -ForegroundColor Green
} elseif ($dbStatus -match "Up") {
    Write-Host "[STARTING] Database (PostgreSQL):    STARTING" -ForegroundColor Yellow
} else {
    Write-Host "[ERROR] Database (PostgreSQL):    DOWN" -ForegroundColor Red
}

# Check Backend API
$apiStatus = docker ps --filter "name=kidwall_colepago" --format "{{.Status}}"
if ($apiStatus -match "Up") {
    Write-Host "[OK] Backend API (Port 8000):  RUNNING" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Backend API (Port 8000):  DOWN" -ForegroundColor Red
}

# Check Parents App
$parentStatus = docker ps --filter "name=kidwall_parents_app" --format "{{.Status}}"
if ($parentStatus -match "Up") {
    Write-Host "[OK] Parents App (Port 8080):  RUNNING" -ForegroundColor Green
} else {
    Write-Host "[ERROR] Parents App (Port 8080):  DOWN" -ForegroundColor Red
}

Write-Host "----------------------------------------"
Write-Host ""
Write-Host "Kubernetes Services:" -ForegroundColor Cyan
Write-Host "----------------------------------------"

try {
    $nginxStatus = kubectl get deployment ingress-nginx-controller -n ingress-nginx -o jsonpath='{.status.replicas}/{.status.updatedReplicas}/{.status.availableReplicas}' 2>$null
    if ($nginxStatus) {
        Write-Host "Ingress-nginx: $nginxStatus ready" -ForegroundColor White
    }
} catch {
    Write-Host "[INFO] Ingress-nginx status unavailable" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "Access your services:" -ForegroundColor Cyan
Write-Host "  * Backend API:    http://localhost:8000" -ForegroundColor White
Write-Host "  * API Docs:       http://localhost:8000/docs" -ForegroundColor White
Write-Host "  * Parents App:    http://localhost:8080" -ForegroundColor White
Write-Host "  * Database:       localhost:5433" -ForegroundColor White
Write-Host "  * Ingress Route:  http://your-ingress-domain" -ForegroundColor White
Write-Host ""
Write-Host "Useful commands:" -ForegroundColor Cyan
Write-Host "  * View Docker logs:        docker-compose logs -f colepago" -ForegroundColor White
Write-Host "  * Stop Docker services:    docker-compose down" -ForegroundColor White
Write-Host "  * Check K8s ingress:       kubectl get ingress" -ForegroundColor White
Write-Host "  * K8s ingress-nginx logs:  kubectl logs -n ingress-nginx -l app.kubernetes.io/name=ingress-nginx -f" -ForegroundColor White
Write-Host ""
Write-Host "[OK] Startup complete!" -ForegroundColor Green
