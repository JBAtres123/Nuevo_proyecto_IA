FROM python:3.11-slim

WORKDIR /app

# System deps for Pillow and MySQL
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc libmariadb-dev pkg-config libffi-dev libjpeg-dev \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create data dirs
RUN mkdir -p /app/data/examenes /app/data/reportes /app/data/materiales /app/chroma_db

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
