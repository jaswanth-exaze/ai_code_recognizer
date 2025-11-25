import json
from typing import List, Dict, Any
from dataclasses import dataclass
import os
from pathlib import Path

import joblib
from backend.app.syntax_rules import detect_by_syntax
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression

MODEL_PATH = Path(__file__).resolve().parents[1] / "models" / "lang_detector.joblib"
MODEL_PATH.parent.mkdir(parents=True, exist_ok=True)


@dataclass
class PredictResult:
    language: str
    confidence: float
    indicators: List[str]
    raw_text: str


class LanguageDetector:
    def __init__(self, pipeline: Pipeline):
        self.pipeline = pipeline

    def predict_text(self, text: str) -> Dict[str, Any]:
        # pipeline.predict_proba returns array; index of maximum probability
        if not text or text.strip() == "":
            return {
                "language": "unknown",
                "confidence": 0.0,
                "indicators": [],
                "raw_text": text,
            }

        probs = self.pipeline.predict_proba([text])[0]
        # Safely obtain class labels from the pipeline (works for calibrated wrappers too)
        labels = None
        if hasattr(self.pipeline, "classes_"):
            labels = self.pipeline.classes_
        else:
            base = getattr(self.pipeline, "base_estimator", None)
            if base is not None and hasattr(base, "classes_"):
                labels = base.classes_

        # Fallback: if labels are still not available, infer by predicting a label
        if labels is None:
            preds = self.pipeline.predict([text])
            labels = [preds[0]]
        best_idx = int(probs.argmax())
        language = labels[best_idx]
        confidence = float(probs[best_idx])

        # syntax-based scores (regex rules from syntax.md)
        syntax_scores = detect_by_syntax(text)

        # rule-based indicators (simple heuristics)
        indicators = []
        lowered = text.lower()
        if "def " in lowered or ("import " in lowered and "def" in lowered):
            indicators.append("def / indentation -> likely Python")
        if "console.log" in lowered or "=>" in lowered or "function(" in lowered:
            indicators.append("JS specific constructs -> likely JavaScript/TypeScript")
        if "#include" in lowered or "printf(" in lowered:
            indicators.append("C/C++ preprocessor / printf -> likely C/C++")
        if "package main" in lowered or "func main(" in lowered:
            indicators.append("Go-like main() / package main -> likely Go")
        if "using " in lowered and "namespace" in lowered:
            indicators.append("C# / using + namespace patterns")
        if "class " in lowered and "public static void main" in lowered:
            indicators.append("Java style main -> likely Java")


        # Add syntax indicators from the syntax detector
        syntax_indicator = None
        top_syntax_lang = None
        top_syntax_score = 0.0
        if syntax_scores:
            top_syntax_lang, top_syntax_score = max(syntax_scores.items(), key=lambda kv: kv[1])
            syntax_indicator = f"syntax pattern -> {top_syntax_lang} (score={round(top_syntax_score,3)})"
            indicators.insert(0, syntax_indicator)

        # compute a combined probability that fuses calibrated ML proba and syntax strength
        # Ensure labels and probs line up
        try:
            ml_sorted = sorted(list(zip(labels, probs)), key=lambda kv: kv[1], reverse=True)
        except Exception:
            # final defensive fallback: predict label only
            ml_label = self.pipeline.predict([text])[0]
            ml_sorted = [(ml_label, 1.0)]
        ml_top_lang, ml_top_prob = ml_sorted[0]

        # default: keep ML prediction
        combined_lang = ml_top_lang
        ml_score_for_syntax_lang = 0.0
        if top_syntax_lang:
            for l, p in ml_sorted:
                if l.lower() == top_syntax_lang.lower() or l.startswith(top_syntax_lang):
                    ml_score_for_syntax_lang = p
                    break

        # choose weights depending on syntax signal strength
        if top_syntax_score >= 0.95:
            beta = 0.85
            alpha = 0.15
        elif top_syntax_score >= 0.7:
            beta = 0.6
            alpha = 0.4
        elif top_syntax_score >= 0.4:
            beta = 0.35
            alpha = 0.65
        else:
            beta = 0.15
            alpha = 0.85

        # compute fused scores for ML top and syntax top
        fused_ml_top = alpha * ml_top_prob + beta * (syntax_scores.get(ml_top_lang, 0) if syntax_scores else 0)
        fused_syntax_top = alpha * ml_score_for_syntax_lang + beta * (top_syntax_score if top_syntax_lang else 0)

        # pick the winner
        if top_syntax_lang and fused_syntax_top > fused_ml_top + 0.03:
            combined_lang = top_syntax_lang
            combined_conf = round(min(0.999, fused_syntax_top), 4)
        else:
            combined_lang = ml_top_lang
            combined_conf = round(min(0.999, fused_ml_top), 4)

        # Add ML top indicators for debug / transparency
        indicators.append(f"ml_top={ml_top_lang}({round(ml_top_prob,3)})")

        # return the fused language decision and combined confidence
        return {
            "language": combined_lang,
            "confidence": round(combined_conf, 4),
            "indicators": indicators,
            "raw_text": text,
        }


def save_detector(pipeline: Pipeline, filepath: Path = MODEL_PATH) -> None:
    filepath.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipeline, filepath)


def load_detector(filepath: Path = MODEL_PATH) -> LanguageDetector:
    # If MODEL_URL is set in the environment, try to download and overwrite the model file
    model_url = os.environ.get("MODEL_URL")
    if model_url and not filepath.exists():
        try:
            import requests

            resp = requests.get(model_url, timeout=30)
            resp.raise_for_status()
            filepath.parent.mkdir(parents=True, exist_ok=True)
            filepath.write_bytes(resp.content)
            print(f"Downloaded model from {model_url} to {filepath}")
        except Exception as e:
            # log the error and continue — fallback to default model
            print(f"Warning: failed to download model from MODEL_URL={model_url}: {e}")

    if filepath.exists():
        pipeline = joblib.load(filepath)
        return LanguageDetector(pipeline)

    # if not present, create a small default pipeline with naive labels
    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), max_features=5000)),
            (
                "clf",
                LogisticRegression(max_iter=200, solver="liblinear", multi_class="ovr"),
            ),
        ]
    )

    # Create a tiny default training set so that app still works offline
    default_texts = [
        ("def add(a, b):\n    return a + b", "Python"),
        ("console.log('hello')", "JavaScript"),
        ("#include <stdio.h>\nint main(){ printf(\"hi\"); }", "C"),
        ("public static void main(String[] args)", "Java"),
        ("package main\nfunc main() { fmt.Println(\"hi\") }", "Go"),
        ("puts 'hello'", "Ruby"),
    ]

    X = [t for t, _ in default_texts]
    y = [l for _, l in default_texts]

    pipeline.fit(X, y)
    save_detector(pipeline)

    return LanguageDetector(pipeline)
