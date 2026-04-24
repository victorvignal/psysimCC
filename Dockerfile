FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 7860

ENV PYTHONPATH=/app \
    CHAINLIT_NO_TELEMETRY=1

CMD ["chainlit", "run", "src/app.py", "--host", "0.0.0.0", "--port", "7860"]
