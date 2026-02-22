FROM python:3.11-slim

WORKDIR /app

# Install system dependencies
# ffmpeg might be needed for some audio libraries, though basic websocket streaming might not strictly need it 
# unless we do transcoding.
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ENV PORT=8080
EXPOSE 8080

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
