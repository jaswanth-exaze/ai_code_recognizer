import json
import sys
from pathlib import Path

# Ensure project root is in sys.path when running tests
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json().get("status") == "ok"


def test_detect_language_text_python():
    text = "def add(a, b):\n    return a + b"
    r = client.post("/detect-language", data={"text": text})
    assert r.status_code == 200
    body = r.json()
    assert "language" in body
    assert body["language"].lower() == "python"


def test_detect_language_text_js():
    text = "console.log('hello')"
    r = client.post("/detect-language", data={"text": text})
    assert r.status_code == 200
    body = r.json()
    assert "language" in body
    assert body["language"].lower() in ("javascript", "typescript") or body["confidence"] > 0.2


def test_detect_language_text_c():
    text = "#include <stdio.h>\nint main(){ printf(\"hi\"); }"
    r = client.post("/detect-language", data={"text": text})
    assert r.status_code == 200
    body = r.json()
    assert body["language"].lower().startswith("c") or body["confidence"] > 0.2


def test_detect_language_text_java():
    text = "public class App { public static void main(String[] args){} }"
    r = client.post("/detect-language", data={"text": text})
    assert r.status_code == 200
    body = r.json()
    assert "java" in body["language"].lower()


def test_detect_language_text_go():
    text = "package main\nfunc main() { fmt.Println(\"hi\") }"
    r = client.post("/detect-language", data={"text": text})
    assert r.status_code == 200
    body = r.json()
    assert body["language"].lower() == "go"


def test_detect_language_text_sql_and_ruby():
    sql_text = "SELECT name FROM users WHERE id = 1;"
    r_sql = client.post("/detect-language", data={"text": sql_text})
    assert r_sql.status_code == 200
    assert r_sql.json()["language"].lower() == "sql"

    ruby_text = "puts 'hello world'"
    r_rb = client.post("/detect-language", data={"text": ruby_text})
    assert r_rb.status_code == 200
    assert r_rb.json()["language"].lower() == "ruby"


def test_detect_language_kotlin_php_swift_shell():
    samples = [
        ("fun main() { println(\"hi\") }", "Kotlin"),
        ("<?php echo $name; ?>", "PHP"),
        ("import Foundation\nfunc main(){ print(\"x\") }", "Swift"),
        ("#!/bin/bash\necho $HOME", "Shell"),
    ]

    for text, expected in samples:
        r = client.post("/detect-language", data={"text": text})
        assert r.status_code == 200
        body = r.json()
        assert expected.lower() in body["language"].lower()


def test_indicators_include_syntax_or_ml():
    text = "def add(a,b):\n    return a + b"
    r = client.post('/detect-language', data={'text': text})
    assert r.status_code == 200
    b = r.json()
    assert any('syntax pattern' in ind.lower() or ind.startswith('ml_top') for ind in b.get('indicators', []))


def test_detect_language_html_css_json_yaml():
    samples = [
        ("<html><body>Hello</body></html>", "HTML"),
        ("body { display: flex; } .btn { color: #fff; }", "CSS"),
        ("{ \"name\": \"alice\" }", "JSON"),
        ("title: Example\nowner: you", "YAML"),
    ]

    for text, expected in samples:
        r = client.post("/detect-language", data={"text": text})
        assert r.status_code == 200
        body = r.json()
        assert expected.lower() in body["language"].lower()
