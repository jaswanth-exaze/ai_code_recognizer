from pathlib import Path
import sys
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from backend.app.model import load_detector

mdl = load_detector()

tests = [
    'import Foundation\nfunc main(){ print("x") }',
    'fun main() { println("hi") }',
    'const x: number = 1; console.log(x);',
]

for t in tests:
    print('\n===> INPUT:', t)
    print(mdl.predict_text(t))
