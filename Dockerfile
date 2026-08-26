FROM ghcr.io/astral-sh/uv:0.11.8 AS uv

FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PORT=8080 \
    GOOGLE_GENAI_USE_VERTEXAI=TRUE \
    GOOGLE_CLOUD_LOCATION=global \
    CLOUD_RESEARCH_MODEL=gemini-3.7-flash \
    CLOUD_RESEARCH_LIVE_MODEL=gemini-live-2.5-flash-native-audio

WORKDIR /workspace

COPY --from=uv /uv /uvx /bin/
COPY pyproject.toml uv.lock README.md ./
RUN uv sync --frozen --no-dev --no-install-project

COPY app ./app

EXPOSE 8080

CMD ["sh", "-c", "uv run --no-sync uvicorn app.fast_api_app:app --host 0.0.0.0 --port ${PORT}"]
