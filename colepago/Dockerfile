# Python FastAPI backend Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/ping')" || exit 1

EXPOSE 8000

CMD ["uvicorn", "api.router:app", "--host", "0.0.0.0", "--port", "8000"]
