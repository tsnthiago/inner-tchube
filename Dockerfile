FROM python:3.13-slim

WORKDIR /app

# Install only runtime deps
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy app code
COPY src/ src/
COPY monitored_channels.json .

ENV PYTHONUNBUFFERED=1
EXPOSE 8000

CMD ["uvicorn", "src.api:app", "--host", "0.0.0.0", "--port", "8000"]
