FROM python:3.11-slim

WORKDIR /app

# System deps for unstructured.pdf (if needed)
RUN apt-get update \
 && apt-get install -y build-essential libxml2-dev libxslt1-dev libjpeg-dev zlib1g-dev \
 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ ./src

CMD ["python", "-u", "src/worker.py"]

