"""Train a small demo TF-IDF + Logistic Regression language detector.

This is intentionally small and lightweight for the MVP — replace with a larger dataset or CodeBERT
for production.
"""
import sys
from pathlib import Path

# When running this file directly (python backend/train.py) the python import path
# will point to backend/ as the current directory which makes ``import backend...`` fail.
# Ensure project root is added to sys.path so absolute imports work in both run modes.
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import json
from sklearn.model_selection import cross_val_predict, cross_val_score
from sklearn.calibration import CalibratedClassifierCV

from backend.app.model import save_detector
from sklearn.pipeline import Pipeline
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression


def build_sample_dataset():
    # Some short canonical examples, extended to cover many common languages
    samples = [
        ("def add(a, b):\n    return a + b", "Python"),
        ("class Foo:\n    def __init__(self):\n        pass", "Python"),
        ("import sys\nprint(sys.version)", "Python"),
        ("console.log('hello world')", "JavaScript"),
        ("function greet() { return 'hi' }", "JavaScript"),
        ("var x = 10; let y = x * 2;", "JavaScript"),
        ("public class App { public static void main(String[] args){} }", "Java"),
        ("System.out.println(\"hello\")", "Java"),
        ("#include <stdio.h>\nint main(){ printf(\"hello\"); }", "C"),
        ("using namespace std; int main() { cout << \"hi\"; }", "C++"),
        ("using System;\npublic class App { static void Main(){ Console.WriteLine(\"hi\"); } }", "C#"),
        ("console.log('hello world')", "JavaScript"),
        ("function greet() { return 'hi' }", "JavaScript"),
        ("var x = 10; let y = x * 2;", "JavaScript"),
        ("const add = (a: number, b: number): number => a + b;", "TypeScript"),
        ("package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"hi\") }", "Go"),
        ("puts 'hello'", "Ruby"),
        ("def greet\n  puts 'hi'\nend", "Ruby"),
        ("SELECT * FROM users WHERE id = 1;", "SQL"),
        ("# PowerShell sample\nWrite-Host 'hello'", "PowerShell"),
        ("<html><head></head><body>Hello</body></html>", "HTML"),
        ("body { display: flex; } .btn { color: #fff; }", "CSS"),
        ("{ \"name\": \"alice\", \"age\": 30 }", "JSON"),
        ("title: Sample\nowner: me", "YAML"),
        ("<?php echo \$name; ?>", "PHP"),
        ("fun main() { println(\"hello\") }", "Kotlin"),
        ("import Foundation\nprint(\"hi\")", "Swift"),
        ("@main struct App { static func main() { print(\"hello\") } }", "Swift"),
        ("let message: String = \"hello\"\nprint(message)", "Swift"),
        ("puts 'x'", "Ruby"),
        ("function test(){ return 1 }", "JavaScript"),
        ("console.log('typescript?')", "JavaScript"),
        ("echo $HOME", "Shell"),
        ("printf(\"hi\")", "C"),
        ("# R sample\nplot(x, y)", "R"),
        ("function myfunc()\n    disp('hello')\nend", "MATLAB"),
        ("import 'dart:core'; void main(){ print('hi'); }", "Dart"),
        ("class ScalaApp { def main(args: Array[String]) = println(\"hi\") }", "Scala"),
        ("object Main extends App { println(\"Hello Scala\") }", "Scala"),
        ("#!/usr/bin/perl\nprint \"hello\n\";", "Perl"),
        ("function love() end", "Lua"),
        ("local function hello() print('hi') end", "Lua"),
        ("package main\nimport \"fmt\"\nfunc main() { fmt.Println(\"hi\") }", "Go"),
        ("func (t *Thing) Do() {}", "Go"),
        ("puts 'hello'", "Ruby"),
        ("def greet\n  puts 'hi'\nend", "Ruby"),
        ("# PowerShell sample\nWrite-Host 'hello'", "PowerShell"),
        ("SELECT * FROM users WHERE id = 1;", "SQL"),
    ]

    # Multiply some samples to give the model a bit more to learn from
    X = [t for t, _ in samples for _ in range(6)]
    y = [l for _, l in samples for _ in range(6)]
    return X, y


def main():
    X, y = build_sample_dataset()

    base_pipeline = Pipeline([
        ("tfidf", TfidfVectorizer(ngram_range=(1, 3), max_features=10000)),
        ("clf", LogisticRegression(max_iter=800, solver="liblinear", multi_class="ovr")),
    ])

    # use a calibrated classifier to improve probability estimates
    calib = CalibratedClassifierCV(base_pipeline, cv=3, method="isotonic")
    calib.fit(X, y)

    # cross-validated accuracy and per-class scores for baseline
    acc = float(sum(cross_val_score(base_pipeline, X, y, cv=4, scoring="accuracy")) / 4.0)

    # Save pipeline and metrics
    save_detector(calib)

    metrics = {"accuracy_cv4": round(acc, 4)}
    metrics_path = Path(__file__).resolve().parents[1] / "models" / "metrics.json"
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(json.dumps(metrics, indent=2))

    print("Trained, calibrated and saved model at backend/models/lang_detector.joblib")
    print("Saved training metrics at", metrics_path)


if __name__ == "__main__":
    main()
