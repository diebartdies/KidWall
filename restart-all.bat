@echo off
REM Kidwall - Restart Everything (Docker Compose + Kubernetes Ingress-nginx)

echo.
echo ========================================
echo Kidwall - Restart All Components
echo ========================================
echo.

echo [1/2] Restarting Docker Compose services...
docker-compose down --remove-orphans
docker-compose up -d

echo.
echo [2/2] Restarting Kubernetes ingress-nginx...
kubectl rollout restart deployment/ingress-nginx-controller -n ingress-nginx

echo.
echo Waiting for services to stabilize...
timeout /t 5

echo.
echo Docker Compose Status:
docker-compose ps

echo.
echo Kubernetes Ingress-nginx Status:
kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx

echo.
echo [OK] All components restarted!
echo.
pause
