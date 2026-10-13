FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8000 \
    CHROMA_PERSIST_DIR=/tmp/koivu/chroma_db \
    DATABASE_PATH=/tmp/koivu/koivu.sqlite3

WORKDIR /app

COPY backend/requirements.txt /tmp/requirements.txt
RUN python -m pip install --no-cache-dir --disable-pip-version-check -r /tmp/requirements.txt \
    && groupadd --system koivu \
    && useradd --system --gid koivu --home-dir /app --no-create-home koivu \
    && mkdir -p /tmp/koivu/chroma_db \
    && chown -R koivu:koivu /tmp/koivu

COPY backend/main.py ./main.py
COPY backend/agent ./agent
COPY backend/core ./core
COPY backend/data/products.txt ./data/products.txt
COPY frontend ./frontend

USER koivu
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=15s --retries=3 \
  CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health', timeout=2)"

CMD ["sh", "-c", "exec python -m uvicorn main:app --host 0.0.0.0 --port ${PORT:-8000} --no-proxy-headers"]

