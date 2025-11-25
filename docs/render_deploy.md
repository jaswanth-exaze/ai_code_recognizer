# Deploying AI Code Recognizer (backend) to Render using Docker

This document explains how to deploy the backend (FastAPI + OCR + model) to Render using the existing `backend/Dockerfile`.

Why Render?

- Quick GitHub-connected deployments and HTTPS by default
- Support for Docker images so system libraries (Tesseract, OpenCV) work

Prerequisites

- A Render account and the Render CLI (optional)
- Your repository pushed to GitHub

Steps — GitHub → Render (Docker)

1. Ensure Dockerfile is present at `backend/Dockerfile` (this repo includes one that installs Tesseract and required system libs).

2. Sign into Render and create a new "Web Service":

   - Connect your GitHub account and choose the repository.
   - Under "Docker" choose path `backend/Dockerfile` (or leave it default if Render detects automatically).

3. Set the Start Command (Render sets a PORT env var at runtime):

   - Command: `uvicorn backend.app.main:app --host 0.0.0.0 --port $PORT`

4. Add environment variables (optional):

   - If you store model/key/config in env vars (e.g., `MODEL_S3_URL`), add them in the Render dashboard.

5. Deploy and wait — Render will build the Docker image and provide a public HTTPS URL.

Notes & tips

- Model artifacts: avoid storing large model files in the repo. Use object storage (S3/GCS) or store model in a volume and download on startup.
- Ensure your Docker image is kept small and avoid installing unneeded packages to reduce build time.
- For EasyOCR (torch) you may want a larger instance or GPU-backed render instance (if available/needed).

Troubleshooting

- Build fails with missing system libraries — confirm Dockerfile includes tesseract cli and OpenCV/Pillow dependencies (already included in `backend/Dockerfile`).
- If OCR misbehaves on Render, try running the container locally first to reproduce:

```powershell
docker build -t ai-code-recognizer-backend -f backend/Dockerfile backend/
docker run -p 8000:8000 -e PORT=8000 ai-code-recognizer-backend
```

After this the backend will be reachable at http://localhost:8000 and the demo UI will be available (if mounted) at `/`.
