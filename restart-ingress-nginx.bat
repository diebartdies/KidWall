@echo off
REM Kidwall - Restart Kubernetes Ingress-nginx Controller

echo.
echo ========================================
echo Kidwall - Restart Ingress-nginx
echo ========================================
echo.

kubectl rollout restart deployment/ingress-nginx-controller -n ingress-nginx

if %errorlevel% equ 0 (
    echo.
    echo [OK] Ingress-nginx restarted successfully
    echo.
    echo Waiting for rollout...
    timeout /t 5
    kubectl rollout status deployment/ingress-nginx-controller -n ingress-nginx
) else (
    echo.
    echo [ERROR] Failed to restart ingress-nginx
    echo Make sure kubectl is installed and your cluster is running
    echo.
)

pause
