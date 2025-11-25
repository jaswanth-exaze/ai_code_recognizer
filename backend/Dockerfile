FROM python:3.11-slim

# Install system packages required by Tesseract, Pillow/OpenCV and for building some wheels
RUN apt-get update \
	&& apt-get install -y --no-install-recommends \
	   build-essential \
	   tesseract-ocr \
	   libtiff5 \
	   libjpeg62-turbo \
	   libfreetype6 \
	   liblcms2-2 \
	   libwebp6 \
	   tcl8.6 \
	   tk8.6 \
	   libsm6 \
	   libxrender1 \
	   libxext6 \
	   libgl1 \
	&& apt-get clean \
	&& rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy just requirements first for Docker layer caching
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

# Copy source files
COPY . /app

# Use PORT env if provided by the platform (e.g. Render sets PORT); fallback to 8000
ENV PORT=8000

# Launch using shell array so the PORT env var is respected on container start
CMD ["sh", "-c", "uvicorn backend.app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
