#!/usr/bin/env python3
"""Contrast the handcrafted parser with spaCy for a few sample sentences."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable, List, Optional

from nl_parser import Parser, format_tree

try:
    import spacy  # type: ignore
except ImportError:  # pragma: no cover - spaCy is optional at runtime
    spacy = None

DEFAULT_SENTENCES = [
    "La niña mira el perro.",
    "Juan ama Maria.",
    "Ana duerme.",
    "El perro corre.",
    "Corre la niña el perro.",
]

SPACY_MODELS = {
    "es": "es_core_news_sm",
}


def load_sentences(files: Iterable[str]) -> List[str]:
    sentences: List[str] = []
    for file in files:
        path = Path(file)
        if not path.exists():
            print(f"[WARN] File not found: {file}")
            continue
        text = path.read_text(encoding="utf-8").strip()
        if text:
            sentences.append(" ".join(line.strip() for line in text.splitlines() if line.strip()))
    return sentences


def load_spacy_model(lang: str):
    if spacy is None:
        return None
    model_name = SPACY_MODELS.get(lang)
    if model_name is None:
        return None
    try:
        return spacy.load(model_name)
    except OSError:
        print(f"[WARN] spaCy model '{model_name}' not found. Install it with: python -m spacy download {model_name}")
        return None


def analyze_spacy(doc) -> dict:
    verbs = [tok.text for tok in doc if tok.pos_ in {"VERB", "AUX"}]
    subjects = [tok.text for tok in doc if tok.dep_ in {"nsubj", "nsubjpass"}]
    objects = [tok.text for tok in doc if tok.dep_ in {"dobj", "obj", "iobj", "attr"}]
    root = next((tok for tok in doc if tok.dep_ == "ROOT"), None)
    root_is_verb = root is not None and root.pos_ in {"VERB", "AUX"}
    ok = bool(verbs) and bool(subjects) and (bool(objects) or root_is_verb)
    missing = []
    if not verbs:
        missing.append("verbo")
    if not subjects:
        missing.append("sujeto")
    if not objects and not root_is_verb:
        missing.append("objeto o verbo raíz")
    return {
        "ok": ok,
        "verbs": verbs,
        "subjects": subjects,
        "objects": objects,
        "root": root.text if root else None,
        "missing": missing,
    }


def compare_sentence(sentence: str, rd_parser: Parser, nlp_models) -> tuple[bool, Optional[dict], str, Optional[str]]:
    accepted, tree = rd_parser.parse(sentence)
    lang = "es"
    nlp_info: Optional[dict] = None
    if nlp_models.get(lang) is not None:
        doc = nlp_models[lang](sentence)
        nlp_info = analyze_spacy(doc)
    tree_str = format_tree(tree).rstrip() if tree else None
    return accepted, nlp_info, lang, tree_str


def main() -> None:
    parser = argparse.ArgumentParser(description="Compare handcrafted parser against spaCy.")
    parser.add_argument("files", nargs="*", help="Optional text files with sentences to evaluate (one per file).")
    parser.add_argument("--show-tree", action="store_true", help="Pretty-print the handcrafted parse tree when available.")
    args = parser.parse_args()

    sentences = load_sentences(args.files) if args.files else []
    if not sentences:
        sentences = DEFAULT_SENTENCES

    rd_parser = Parser()
    models = {lang: load_spacy_model(lang) for lang in {"es"}}
    if spacy is None:
        print("spaCy is not installed. Install requirements.txt to enable comparisons.")

    print(f"Evaluating {len(sentences)} sentence(s)...")
    print("-" * 60)
    for sentence in sentences:
        accepted, nlp_info, lang, tree_str = compare_sentence(sentence, rd_parser, models)
        print(f"Sentence: {sentence}")
        print(f"  Parser: {'OK' if accepted else 'FAIL'}")
        if nlp_info is None:
            print("  spaCy: skipped (model not available)")
        else:
            status = "OK" if nlp_info["ok"] else "FAIL"
            if nlp_info["ok"]:
                detail = (
                    f"sujetos={nlp_info['subjects'] or '-'}, verbos={nlp_info['verbs'] or '-'}, objetos={nlp_info['objects'] or '-'}"
                )
            else:
                detail = "faltó " + ", ".join(nlp_info["missing"]) if nlp_info["missing"] else "estructura incompleta"
            print(f"  spaCy: {status} ({detail})")
        if args.show_tree and tree_str:
            for line in tree_str.splitlines():
                print(f"    {line}")
        print("-" * 60)


if __name__ == "__main__":
    main()
