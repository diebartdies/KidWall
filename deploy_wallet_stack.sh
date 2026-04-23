#!/bin/bash
# Deployment/startup script for Colepago Wallet App Stack (Flutter APK + Backend)
# This script launches the backend API and Flutter app (APK) in a production-like environment.
# - Backend runs 24/7
# - Flutter app (kids) only available during parent-defined hours
# - Merchants only available during business hours

# --- CONFIGURABLE PARAMETERS ---
BACKEND_DIR="/opt/colepago/backend"   # Path to backend code
BACKEND_VENV="$BACKEND_DIR/.venv"
BACKEND_START_CMD="python main.py"    # Adjust as needed

APK_PATH="/opt/colepago/colepago-parents-app/build/app/outputs/flutter-apk/app-release.apk"
KID_START_HOUR=8      # Example: 8 AM
KID_END_HOUR=20       # Example: 8 PM
MERCHANT_START_HOUR=9 # Example: 9 AM
MERCHANT_END_HOUR=18  # Example: 6 PM

# --- FUNCTIONS ---
start_backend() {
  echo "[INFO] Starting backend API..."
  cd "$BACKEND_DIR" || exit 1
  source "$BACKEND_VENV/bin/activate"
  nohup $BACKEND_START_CMD > backend.log 2>&1 &
  echo $! > backend.pid
  echo "[INFO] Backend started with PID $(cat backend.pid)"
}

stop_backend() {
  if [ -f backend.pid ]; then
    kill $(cat backend.pid)
    rm backend.pid
    echo "[INFO] Backend stopped."
  fi
}

start_flutter_apk() {
  echo "[INFO] Launching Flutter APK (emulator/device required)..."
  # Example: Use adb to install and launch APK on connected device
  adb install -r "$APK_PATH"
  adb shell monkey -p com.example.colepago_parents_app -c android.intent.category.LAUNCHER 1
}

is_within_hours() {
  local start_hour=$1
  local end_hour=$2
  local now_hour=$(date +%H)
  if [ $now_hour -ge $start_hour ] && [ $now_hour -lt $end_hour ]; then
    return 0
  else
    return 1
  fi
}

# --- MAIN LOOP ---
echo "[INFO] Starting Colepago Wallet Stack..."
start_backend

while true; do
  # Kids app availability
  if is_within_hours $KID_START_HOUR $KID_END_HOUR; then
    echo "[INFO] Kids app: AVAILABLE"
    # Optionally, send push notification or unlock app
  else
    echo "[INFO] Kids app: UNAVAILABLE (outside allowed hours)"
    # Optionally, lock app or show message
  fi

  # Merchants availability
  if is_within_hours $MERCHANT_START_HOUR $MERCHANT_END_HOUR; then
    echo "[INFO] Merchants: AVAILABLE"
    # Optionally, enable merchant endpoints
  else
    echo "[INFO] Merchants: UNAVAILABLE (outside business hours)"
    # Optionally, disable merchant endpoints
  fi

  sleep 300 # Check every 5 minutes

done

# On script exit, stop backend
trap stop_backend EXIT
