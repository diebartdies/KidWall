import subprocess
import sys
from pathlib import Path

def _ensure_requirements():
    req_file = Path(__file__).parent / "requirements.txt"
    if not req_file.exists():
        return
    result = subprocess.run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_file)],
        capture_output=True, text=True
    )
    if result.returncode != 0:
        print("WARNING: Failed to install some requirements:\n", result.stderr, flush=True)
    else:
        newly_installed = [
            line for line in result.stdout.splitlines()
            if line.startswith("Successfully installed")
        ]
        if newly_installed:
            print("\n".join(newly_installed), flush=True)

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import Response
from colepago.api.router import router as api_router

app = FastAPI(title="ColePago API", description="KidWall - Kids' Wallet System", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "service": "ColePago API",
        "status": "ok",
        "docs": "/docs",
        "api_base": "/api",
        "ping": "/api/ping",
    }


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/favicon.ico", include_in_schema=False)
def favicon():
    return Response(status_code=204)

if __name__ == "__main__":
    import uvicorn
    _ensure_requirements()
    uvicorn.run("main:app", host="0.0.0.0", port=8010, reload=True)
