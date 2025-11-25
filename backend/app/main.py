from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict, Any, List
import io
from PIL import Image, ImageFilter, ImageOps, ImageEnhance

from backend.app.model import LanguageDetector, load_detector
from fastapi.staticfiles import StaticFiles
from pathlib import Path

app = FastAPI(title="AI Code Recognizer (MVP)")

detector: LanguageDetector = load_detector()

# Development CORS: allow mobile & local UI to access the API while testing.
# NOTE: In production, restrict origins appropriately!
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve the lightweight demo frontend under the project frontend/ folder
FRONTEND_DIR = Path(__file__).resolve().parents[1].parents[0] / 'frontend'
if FRONTEND_DIR.exists():
    # Mount frontend static assets at /static to avoid intercepting API POST routes
    app.mount('/static', StaticFiles(directory=str(FRONTEND_DIR), html=True), name='frontend-static')


@app.get('/', include_in_schema=False)
def serve_index():
    """Return the demo frontend index page."""
    index_path = FRONTEND_DIR / 'index.html'
    if index_path.exists():
        from fastapi.responses import FileResponse

        return FileResponse(str(index_path))
    raise HTTPException(status_code=404, detail="Demo frontend not found")


class DetectResponse(BaseModel):
    language: str
    confidence: float
    indicators: List[str]
    raw_text: str


def _preprocess_image(pil_image: Image.Image) -> Image.Image:
    try:
        # convert to RGB then grayscale if necessary
        img = pil_image.convert('L')
        # Resize to reasonable width while maintaining aspect ratio
        max_w = 1024
        if img.width > max_w:
            ratio = max_w / float(img.width)
            new_h = int(img.height * ratio)
            img = img.resize((max_w, new_h), Image.LANCZOS)

        # Increase contrast + sharpen
        img = ImageOps.autocontrast(img)
        img = img.filter(ImageFilter.SHARPEN)
        img = ImageEnhance.Contrast(img).enhance(1.2)
        return img
    except Exception:
        return pil_image


_easyocr_reader = None


def _image_to_text(file_bytes: bytes) -> str:
    # Try EasyOCR if available, then fall back to pytesseract. If no OCR available
    # user can still supply `text` form field.
    global _easyocr_reader

    try:
        pil_image = Image.open(io.BytesIO(file_bytes))
    except Exception:
        return ""

    # preprocessing
    pil_image = _preprocess_image(pil_image)

    # try EasyOCR first
    try:
        import easyocr
        if _easyocr_reader is None:
            # only init once (may be heavy)
            _easyocr_reader = easyocr.Reader(['en'], gpu=False)
        # easyocr works on numpy arrays
        import numpy as np
        arr = np.array(pil_image)
        res = _easyocr_reader.readtext(arr, detail=0)
        if res:
            return "\n".join(res).strip()
    except Exception:
        # fallthrough to pytesseract
        _easyocr_reader = None

    try:
        import pytesseract
        text = pytesseract.image_to_string(pil_image)
        return text.strip()
    except Exception:
        return ""


@app.post("/detect-language", response_model=DetectResponse)
async def detect_language(file: Optional[UploadFile] = File(None), text: Optional[str] = Form(None)):
    if not file and not text:
        raise HTTPException(status_code=400, detail="Either 'file' (image) or 'text' form-field is required")

    ocr_text = ""
    if file:
        contents = await file.read()
        ocr_text = _image_to_text(contents)

    final_text = (text or "") + "\n" + (ocr_text or "")
    final_text = final_text.strip()

    if len(final_text) == 0:
        raise HTTPException(status_code=400, detail="No text could be extracted from the input. If using images, ensure Tesseract OCR is installed or pass 'text' field.")

    result = detector.predict_text(final_text)

    return JSONResponse(content=result)


@app.get("/health")
def health() -> Dict[str, Any]:
    return {"status": "ok"}
