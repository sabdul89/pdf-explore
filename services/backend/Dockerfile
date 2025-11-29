FROM python:3.11-slim

# system deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgl1 \
    libglib2.0-0 \
    tesseract-ocr \
    poppler-utils \
    pkg-config \
    libsm6 \
    libxrender1 \
    libxext6 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir -r requirements.txt

# download spaCy model
RUN python -m spacy download en_core_web_sm || true

EXPOSE 10000
CMD ["uvicorn","app.main:app","--host","0.0.0.0","--port","10000"] 
