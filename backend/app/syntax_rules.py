"""Simple regex-driven syntax rules for language detection.

This module provides lightweight, human-readable syntax rules derived from `syntax.md`.
It scores candidate languages by counting weighted regex matches.
"""
from typing import Dict, List, Tuple
import re


RULES: Dict[str, List[Tuple[str, float]]] = {
    "Python": [
        (r"^\s*def\s+\w+\s*\(", 1.0),
        (r"^\s*class\s+\w+", 0.6),
        (r"\bimport\s+\w+", 0.5),
        (r"\bself\b", 0.4),
        (r":\s*$", 0.3),
        (r"#", 0.2),
    ],
    "JavaScript": [
        (r"console\.log\s*\(|\bconsole\.info\b", 1.0),
        (r"=>", 0.8),
        (r"\b(function|var|let|const)\s+\w+", 0.7),
        (r"\bmodule\.exports\b", 0.6),
    ],
    "TypeScript": [
        (r":\s*\w+(\[\])?\b", 0.9),
        (r"interface\s+\w+", 0.8),
        (r"<\w+>", 0.3),
    ],
    "C": [
        (r"#include\s*<\w+\.h>", 1.0),
        (r"\bprintf\s*\(", 0.8),
        (r"\bscanf\s*\(", 0.6),
    ],
    "C++": [
        (r"#include\s*<.*>", 1.0),
        (r"std::\w+", 0.8),
        (r"\bcout\s*<<", 0.7),
    ],
    "Java": [
        (r"public\s+class\s+\w+", 1.0),
        (r"System\.out\.println\s*\(", 0.9),
        (r"public\s+static\s+void\s+main", 0.8),
    ],
    "Go": [
        (r"package\s+main", 1.0),
        (r"fmt\.Println", 0.9),
        (r"func\s+main\s*\(|go\s+func\b", 0.6),
    ],
    "Ruby": [
        (r"\bputs\s+['\"]", 1.0),
        (r"def\s+\w+", 0.6),
        (r"end\b", 0.3),
        (r"\bclass\s+\w+", 0.4),
    ],
    "SQL": [
        (r"\bSELECT\b.*\bFROM\b", 1.0),
        (r"\bINSERT\b.*\bINTO\b", 0.8),
    ],
    "PowerShell": [
        (r"Write-Host\b", 1.0),
        (r"Get-\w+\b", 0.6),
    ],
    "Kotlin": [
        (r"fun\s+main\s*\(|val\s+\w+|var\s+\w+", 0.9),
        (r"println\(|data class\b|:\s*\w+", 0.6),
    ],
    "Groovy": [
        (r"println\s+['\"]|def\s+\w+|@Grab\(|script\s*:\s*true", 0.9),
    ],
    "PHP": [
        (r"<\?php\b|echo\s+\$|\$\w+\s*=", 1.0),
    ],
    "Swift": [
        (r"import\s+Foundation", 1.0),
        (r"let\s+\w+:\s*", 0.9),
        (r"func\s+main\s*\(|func\s+\w+\s*\(|print\(", 0.4),
    ],
    "Shell": [
        (r"^#!\/(bin|usr)\/|echo\s+\$|\bgrep\b|\bawk\b", 1.0),
        (r"\bif\s+\[|fi\b|/bin/bash", 0.5),
    ],
    "Perl": [
        (r"^\s*#!\/usr\/bin\/perl|use\s+strict|\$\w+->", 1.0),
    ],
    "Scala": [
        (r"object\s+\w+\s*\{|def\s+\w+\(|val\s+\w+:\s*\w+", 0.9),
    ],
    "PHP_HTML": [
        (r"<\?php|\?>", 1.0),
    ],
    # Additional languages provided by user (1-100).
    "HTML": [
        (r"<!DOCTYPE html>|<html|<body|<script|<link\s+rel=", 1.0),
        (r"<div\b|<span\b|<head\b|<meta\b", 0.6),
    ],
    "CSS": [
        (r"[.#][\w-]+\s*\{", 1.0),
        # reduce property matching weight to avoid false positives with TS/JS type annotations
        (r"[a-z-]{3,}\s*:\s*[^;]+;", 0.35),
        (r"@media\b|@import\b", 0.6),
    ],
    "JSON": [
        (r"^\s*\{\s*\"\w+\"\s*:\s*", 1.0),
        (r"^\s*\[\s*\{\s*\"\w+\"", 0.6),
    ],
    "YAML": [
        (r"^\s*\w+:\s+[^\n]", 1.0),
        (r"^---|\.\.\.", 0.6),
    ],
    "TOML": [
        (r"^\s*\[\w+\]|^\w+\s*=\s*\"", 1.0),
    ],
    "XML": [
        (r"^\s*<\?xml\b|<\w+:?\w+\b[^>]*>", 1.0),
    ],
    "JSX": [
        (r"<\w+\s+.*>.*<\/\w+>|return\s*\(|export\s+default\s+function", 0.9),
    ],
    "TSX": [
        (r"<\w+\s+.*:|<\w+\s+.*>.*<\/\w+>|:\s*React\.FC", 0.9),
    ],
    "SASS": [
        (r"\$\w+\s*:\s*[^;]+;|@mixin\b|@include\b", 1.0),
    ],
    "SCSS": [
        (r"\.\w+\s*\{|\$\w+\s*:\s|@extend\b", 0.95),
    ],
    "LESS": [
        (r"@[\w-]+\s*:\s*[^;]+;|\.mixin\b", 0.9),
    ],
    "CoffeeScript": [
        (r"->|\->|class\s+\w+|\bconsole\.log\b", 0.9),
    ],
    "GraphQL": [(r"query\s+\w+|mutation\s+\w+|type\s+\w+\{|schema\{", 1.0)],
    "Cypher": [(r"MATCH\s*\(|CREATE\s*\(|RETURN\s+", 0.95)],
    "SPARQL": [(r"PREFIX\s+\w+:|SELECT\s+\?|WHERE\s*\{", 1.0)],
    "GraphQL-Schema": [(r"type\s+\w+\s*\{|input\s+\w+\s*\{", 0.9)],
    "SQLDialect": [(r"\bSELECT\b|\bINSERT\b|\bUPDATE\b|\bDELETE\b", 1.0)],
    "PLSQL": [(r"CREATE\s+OR\s+REPLACE\s+PROCEDURE|EXECUTE\s+IMMEDIATE", 1.0)],
    "TSQL": [(r"\bEXEC\b|\bTOP\b\s+\d+|\bUSE\b\s+\w+", 0.9)],
    "pgSQL": [(r"\bFUNCTION\b|RETURN\s+TABLE|LANGUAGE\s+plpgsql", 0.9)],
    "MySQL": [(r"\bLIMIT\b|AUTO_INCREMENT|`\w+`\s+INT|ENGINE=", 0.85)],
    "MongoDB": [(r"db\.\w+\.(find|aggregate|insert)\(|\$match|\$project", 0.95)],
    "CQL": [(r"SELECT\s+\*\s+FROM\s+\w+|CREATE\s+TABLE\s+\w+|CONSISTENCY\s+LEVEL", 0.85)],
    "PLpgSQL": [(r"RETURN\s+TABLE|LANGUAGE\s+plpgsql|\bRAISE\b", 0.85)],
    "GraphQLQuery": [(r"\bquery\b|\bmutation\b|\bfragment\b", 0.8)],
    "JSONiq": [(r"\bfor\s+\$|\breturn\s+$|\{\$", 0.6)],
    "XSLT": [(r"<xsl:stylesheet|<xsl:template", 1.0)],
    "Hack": [(r"<\?hh|<<__EntryPoint|HHClient|namespace\s+", 0.9)],
    "ColdFusion": [(r"<cfoutput|cfset\b|cfif\b", 0.9)],
    "VB.NET": [(r"Imports\s+System|Public\s+Class|Sub\s+\w+\(|Console\.WriteLine\b", 0.9)],
    "Objective-C": [(r"#import\s+<|@interface\s+|\[\w+\s+\w+\]", 0.9)],
    "Solidity": [(r"pragma\s+solidity|contract\s+\w+|function\s+\w+\(|mapping\(|emit\b", 1.0)],
    "VHDL": [(r"entity\s+\w+\s+is|architecture\s+|signal\s+\w+\s*:\s*", 0.9)],
    "Verilog": [(r"module\s+\w+\(|always\s*@\(|initial\s+\{", 0.9)],
    "Apex": [(r"public\s+class\s+|@isTest|System\.debug\(|List<\w+>\s+\w+", 0.9)],
    "ABAP": [(r"REPORT\s+|WRITE:\s+|SELECT\s+\*\s+FROM\s+", 0.9)],
    "Tcl": [(r"^proc\s+\w+|set\s+\w+\s+|puts\s+\"|\$\w+", 0.8)],
    # AWK: prefer explicit AWK features (numeric fields, BEGIN block) and explicit 'awk' mention
    "AWK": [(r"\$\d+\b|\bBEGIN\s*\{|\bFS=|\bawk\b", 1.0)],
    "SED": [(r"s\/[^\/]+\/[^\/]+\/g|\/pattern\/[pg]*|^#\!\/bin\/(bash|sh)", 0.85)],
    "Rexx": [(r"parse\s+arg|say\s+|call\s+\w+|pull\b", 0.7)],
    "PostScript": [(r"%\!|def\s+\w+|showpage|moveto|lineto|stroke", 0.8)],
    "GLSL": [(r"void\s+main\s*\(|uniform\s+\w+|vec[234]\b|gl_FragColor", 0.9)],
    "WAT": [(r"\(module\b|\(func\b|memory\b|i32\.const|local\.get", 0.9)],
    "Zig": [(r"const\s+\w+\s*=|pub\s+fn\s+\w+\(|@import\(|comptime\b", 0.9)],
    "Nim": [(r"proc\s+\w+\(|let\s+\w+\s*=|import\s+\w+", 0.9)],
    "Mojo": [(r"def\s+\w+\(|fn\s+\w+|from\s+\w+\s+import\b", 0.8)],
    "Dart": [(r"import\s+\'|void\s+main\(|class\s+\w+\{|final\s+\w+\s*=" , 0.9)],
    "R": [(r"<-\s|library\(|print\(|#'|\bdata\.frame\b", 0.9)],
    "MATLAB": [(r"function\s+\[?\w*\]?=|end\b|%\s|disp\(|plot\(|\bmatrix\(|;\s*$", 0.9)],
    "D": [(r"import\s+std\.|void\s+main\(|mixin\(|alias\s+", 0.8)],
    "Crystal": [(r"class\s+\w+\n|def\s+\w+|@[a-z]\w+", 0.8)],
    "C#": [
        (r"using\s+System\b|namespace\s+\w+", 1.0),
        (r"Console\.WriteLine\s*\(", 0.9),
    ],
}


def detect_by_syntax(text: str) -> Dict[str, float]:
    """Score languages using the RULES regexes.

    Returns a mapping of language -> score (0..1). Scores are normalized by the
    maximum matched weight so the top language tends to have a value close to 1.0
    when strong patterns exist.
    """
    if not text:
        return {}

    scores: Dict[str, float] = {}
    up_text = text

    for lang, patterns in RULES.items():
        total = 0.0
        for pat, weight in patterns:
            try:
                if re.search(pat, up_text, flags=re.IGNORECASE | re.MULTILINE):
                    total += weight
            except re.error:
                # in case of a bad pattern, skip it
                continue

        if total > 0:
            scores[lang] = total

    if not scores:
        return {}

    # normalize by maximum seen
    max_score = max(scores.values())
    if max_score <= 0:
        return {lang: 0.0 for lang in scores}

    # normalize to 0..1 and apply mild boost to very strong signals so they stand out
    normalized = {}
    for lang, score in scores.items():
        norm = score / max_score
        if norm >= 0.95:
            norm = min(1.0, norm + 0.05)
        normalized[lang] = round(norm, 4)
    return normalized
