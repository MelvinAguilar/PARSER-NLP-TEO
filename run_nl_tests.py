#!/usr/bin/env python3
"""Simple runner for the handcrafted NL parser test suites."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Iterable

from nl_parser import Parser, format_tree


def iter_files(folder: Path) -> Iterable[Path]:
    if not folder.exists():
        return []
    return sorted(path for path in folder.glob("*.txt") if path.is_file())


def load_sentence(path: Path) -> str:
    text = path.read_text(encoding="utf-8").strip()
    return " ".join(line.strip() for line in text.splitlines() if line.strip())


def run_suite(paths: Iterable[Path], expect_ok: bool, show_tree: bool, parser: Parser) -> tuple[int, int]:
    total = 0
    passed = 0
    for path in paths:
        sentence = load_sentence(path)
        accepted, tree = parser.parse(sentence)
        success = accepted if expect_ok else not accepted
        status = "PASS" if success else "FAIL"
        expectation = "OK" if expect_ok else "FAIL"
        print(f"[{status}] expect={expectation:4} actual={'OK' if accepted else 'FAIL'} :: {path.name}")
        if show_tree and tree is not None:
            print(format_tree(tree, indent=1))
        total += 1
        if success:
            passed += 1
    return passed, total


def main() -> None:
    parser = argparse.ArgumentParser(description="Run NL parser regression tests.")
    parser.add_argument("--ok-dir", default="tests/nl_ok", help="Directory with positive cases (default: tests/nl_ok)")
    parser.add_argument("--fail-dir", default="tests/nl_fail", help="Directory with negative cases (default: tests/nl_fail)")
    parser.add_argument("--show-tree", action="store_true", help="Pretty-print parse trees for accepted inputs")
    args = parser.parse_args()

    rd_parser = Parser()

    ok_passed, ok_total = run_suite(iter_files(Path(args.ok_dir)), True, args.show_tree, rd_parser)
    fail_passed, fail_total = run_suite(iter_files(Path(args.fail_dir)), False, args.show_tree, rd_parser)

    total = ok_total + fail_total
    passed = ok_passed + fail_passed
    print("-" * 50)
    if total:
        print(f"Summary: {passed}/{total} cases passed ({passed / total:.0%}).")
    else:
        print("No test cases were executed (check directories).")


if __name__ == "__main__":
    main()
