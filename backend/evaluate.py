"""Evaluate the trained model and produce calibration / metrics.

Produces:
- backend/models/metrics_detailed.json (classification report + accuracy)
- backend/models/calibration.png (reliability diagram showing predicted vs true probabilities)

This script generates a synthetic validation set (similar distribution to the train script)
so you can quickly inspect calibration and per-class behavior.
"""
from pathlib import Path
import json
import numpy as np
from sklearn.metrics import classification_report, accuracy_score, confusion_matrix
from sklearn.calibration import calibration_curve
import matplotlib.pyplot as plt

import sys
from pathlib import Path

# ensure project root is in sys.path when script is run directly
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.model import load_detector


def build_eval_dataset():
    # slightly more diverse set for evaluation
    samples = [
        ("def foo(a,b):\n    return a+b", "Python"),
        ("class Foo:\n    def __init__(self): pass", "Python"),
        ("import os\nprint(os.name)", "Python"),
        ("console.log('hello')", "JavaScript"),
        ("function test(){ return 1 }", "JavaScript"),
        ("var x = 1; let y = x + 1;", "JavaScript"),
        ("System.out.println(\"hi\")", "Java"),
        ("public static void main(String[] args)", "Java"),
        ("#include <stdio.h>\nint main(){ printf(\"hi\"); }", "C"),
        ("using namespace std;\nint main(){ cout << \"hi\"; }", "C++"),
        ("package main\nfunc main() { fmt.Println(\"hi\") }", "Go"),
        ("puts \"hello\"", "Ruby"),
        ("SELECT name FROM users WHERE id = 1;", "SQL"),
        ("<?php echo $name; ?>", "PHP"),
        ("fun main(){ println(\"hi\") }", "Kotlin"),
        ("#!/bin/bash\necho $HOME", "Shell"),
        ("import Foundation\nfunc main(){}", "Swift"),
    ]

    # Expand and slightly shuffle
    X = [t for t, _ in samples for _ in range(30)]
    y = [l for _, l in samples for _ in range(30)]

    rng = np.random.default_rng(1234)
    idx = rng.permutation(len(X))
    X = [X[i] for i in idx]
    y = [y[i] for i in idx]

    # split
    split = int(len(X) * 0.8)
    return X[split:], y[split:]


def evaluate_and_plot():
    mdl = load_detector()
    X_test, y_test = build_eval_dataset()

    # predict
    probs = mdl.pipeline.predict_proba(X_test)
    preds = mdl.pipeline.predict(X_test)

    acc = accuracy_score(y_test, preds)
    report = classification_report(y_test, preds, output_dict=True)
    cm = confusion_matrix(y_test, preds, labels=mdl.pipeline.classes_)

    out = {
        "accuracy": round(float(acc), 4),
        "report": report,
        "classes": list(mdl.pipeline.classes_),
    }

    models_dir = Path(__file__).resolve().parents[1] / 'models'
    models_dir.mkdir(parents=True, exist_ok=True)

    metrics_path = models_dir / 'metrics_detailed.json'
    metrics_path.write_text(json.dumps(out, indent=2))
    print("Saved metrics ->", metrics_path)

    # reliability diagram: use the prob assigned to the true class per sample
    clf = mdl.pipeline
    labels = clf.classes_

    # compute per-sample probability for true class
    label_to_idx = {lab: i for i, lab in enumerate(labels)}
    true_probs = [probs[i][label_to_idx[y_test[i]]] if y_test[i] in label_to_idx else 0.0 for i in range(len(y_test))]

    prob_true, prob_pred = calibration_curve([1]*len(true_probs), true_probs, n_bins=10, strategy='uniform')

    # Plot
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.plot(prob_pred, prob_true, marker='o', label='Model')
    ax.plot([0, 1], [0, 1], linestyle='--', color='gray', label='Perfect')
    ax.set_xlabel('Mean predicted probability')
    ax.set_ylabel('Observed fraction of positives')
    ax.set_title('Reliability diagram (true-class predicted probability)')
    ax.legend()

    out_img = models_dir / 'calibration.png'
    fig.savefig(out_img, dpi=150, bbox_inches='tight')
    print('Saved calibration plot ->', out_img)


if __name__ == '__main__':
    evaluate_and_plot()
