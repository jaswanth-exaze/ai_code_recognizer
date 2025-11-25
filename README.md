# AI Code Recognizer — MVP Backend

This repository is a small MVP backend for the AI Code Recognizer project described in `my requirement.md`.

It provides a FastAPI server with a `/detect-language` endpoint and a small TF-IDF + Logistic Regression model plus a simple rule-based enhancer for detecting programming language from text (or OCR'd images when tesseract is installed).

Quick start (Python 3.9+):

1. Create and activate a virtual environment.

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
```

2. Train the small demo model and start the server

```powershell
python backend/train.py
uvicorn backend.app.main:app --reload --port 8000 --host 0.0.0.0
```

3. Try sending a text or image to the `/detect-language` endpoint (see docs at http://127.0.0.1:8000/docs)

Notes:

- OCR prefers `EasyOCR` (if installed) and falls back to `pytesseract` (the Tesseract system binary). EasyOCR is recommended for code screenshots but may require extra libraries (e.g., torch).
- If no OCR binaries are available you can post text directly using the `text` form field.
- This is an MVP; next steps include expanding models, integrating CodeBERT, and building mobile clients.

Quick example using curl (text-only):

```powershell
curl -X POST "http://127.0.0.1:8000/detect-language" -F "text=def add(a,b):\n    return a + b"
```

Installing Tesseract on Windows:

- Use the Tesseract installer from https://github.com/UB-Mannheim/tesseract/wiki (Windows builds) and add it to your PATH.
- After installing the binary, `pytesseract` will be able to call it and OCR images.

## Demo UI

After you start the backend, the demo frontend is served from `/` (root). Open http://127.0.0.1:8000 to use the premium-style UI and try uploads directly.

## Expose to mobile over the local network

If your phone and development machine are on the same Wi‑Fi network you can open the app directly using your machine's LAN IP address.

1. Find your machine's local IP address (Windows PowerShell):

```powershell
ipconfig | Select-String "IPv4" -First 1
```

2. Start the server with host 0.0.0.0 (see above) and on your phone open:

```
http://<YOUR_LAN_IP>:8000
```

For example: http://192.168.1.55:8000

Note: you may need to allow incoming traffic in your OS firewall for port 8000.

## Quick public link for testing (ngrok)

To test from devices outside your network or share a temporary HTTPS link, use ngrok:

```powershell
ngrok http 8000
```

ngrok will show a public forwarding URL (for example https://abcd1234.ngrok.io). Open that URL on your mobile phone to use the demo UI and API.

## Run in Docker (quick local container)

You can build and run the container image that ships with the repo — it binds port 8000 so you can test locally or use a cloud container service.

```powershell
docker build -t ai-code-recognizer-backend -f backend/Dockerfile backend/
docker run -p 8000:8000 ai-code-recognizer-backend
```

## Deploy to a cloud provider

For a stable public endpoint use Render, Railway, Fly, or a container host. Most platforms can deploy directly from a GitHub repo or a Docker image. Use the command:

```
uvicorn backend.app.main:app --host 0.0.0.0 --port 8000
```

## Security / Production notes

- This project enables CORS="\*" for development to make mobile testing easy. Restrict origins before publishing to production.
- When deploying publicly enable HTTPS, add authentication and rate‑limiting, and do not expose internal endpoints without protection.

## Model deployment note

For production deployments you may want to keep trained model artifacts outside the repo. Instead:

1. Upload the trained model file `lang_detector.joblib` to a cloud storage location (S3, GCS) or object store.
2. In Render, add an environment variable named `MODEL_URL` pointing to the public or pre-signed download URL for that file.
3. On container start the backend will attempt to download `MODEL_URL` and save it to `backend/models/lang_detector.joblib`. If download fails the app falls back to the built-in default model.

Example Render setup step:

- In the Render dashboard for your service -> Environment -> Add `MODEL_URL` with the pre-signed S3 URL.

## Training & metrics

The training script now trains a calibrated classifier and writes a small metrics file to `backend/models/metrics.json` which contains cross-validation accuracy and basic training notes. See it after running `python backend/train.py`.

## Evaluation

After training, run the evaluation script to produce a more detailed JSON report and a calibration plot:

```powershell
python backend/evaluate.py
```

This will write `backend/models/metrics_detailed.json` and `backend/models/calibration.png` which help inspect the model's behavior.

## CI

I added a GitHub Actions workflow at `.github/workflows/ci.yaml`. It installs dependencies, runs tests, trains the toy model, and runs the evaluation script. This makes it easy to verify the pipeline in CI.

Running tests locally

```powershell
python -m venv .venv; .\.venv\Scripts\Activate.ps1
pip install -r backend/requirements.txt
python backend/train.py
pytest -q
```
