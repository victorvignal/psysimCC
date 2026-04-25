FROM python:3.12-slim

WORKDIR /app

COPY pyproject.toml .
RUN pip install --no-cache-dir uv && uv pip install --system -r pyproject.toml 2>/dev/null || \
    pip install --no-cache-dir \
    "openai>=1.0.0" "httpx>=0.27" "pyyaml>=6.0" "python-dotenv>=1.0" \
    "pydantic>=2.0" "supabase>=2.25.1" "fastapi>=0.115" \
    "uvicorn[standard]>=0.30" "sse-starlette>=2.1"

COPY . .

EXPOSE 8000

ENV PYTHONPATH=/app

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
