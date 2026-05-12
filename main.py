import subprocess
import sys
import os
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
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
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

static_dir = Path(__file__).parent / "static"
brochure_dir = Path(__file__).parent / "brochure"

if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

if brochure_dir.exists():
    app.mount("/brochure", StaticFiles(directory=str(brochure_dir)), name="brochure")


@app.get("/")
def root():
    index_file = static_dir / "index.html"
    if index_file.exists():
        return FileResponse(index_file)
    return {
        "service": "ColePago API",
        "status": "ok",
        "docs": "/docs",
        "api_base": "/api",
        "ping": "/api/ping",
    }


@app.get("/app")
@app.get("/app/")
def app_portal():
    app_file = static_dir / "portal.html"
    if app_file.exists():
        return FileResponse(app_file)
    return {
        "service": "ColePago App",
        "status": "missing static/portal.html",
        "api_base": "/api",
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
    project_root = Path(__file__).parent
    reload_enabled = os.getenv("UVICORN_RELOAD", "false").lower() == "true"

    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8010,
        reload=reload_enabled,
        reload_dirs=[str(project_root / "colepago"), str(project_root)] if reload_enabled else None,
    )
