#!/usr/bin/env python3
"""Helper to inspect the handcrafted NL parser with trace + derivation tree."""

from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable, List
import re
import unicodedata

try:
    import matplotlib.pyplot as plt  # type: ignore
except ImportError:  # pragma: no cover - optional dependency
    plt = None

from nl_parser import Parser, ParseTree, LABELS, format_tree

DEFAULT_SENTENCES = [
    "La niña mira el perro.",
    "Juan ama Maria.",
    "Ana duerme.",
    "El perro corre.",
]


def load_sentences(files: Iterable[str]) -> list[str]:
    sentences: list[str] = []
    for file in files:
        path = Path(file)
        if not path.exists():
            print(f"[WARN] File not found: {file}")
            continue
        text = path.read_text(encoding="utf-8").strip()
        if text:
            sentences.append(" ".join(line.strip() for line in text.splitlines() if line.strip()))
    return sentences


def clip(text: str, width: int) -> str:
    if len(text) <= width:
        return text.ljust(width)
    if width <= 1:
        return text[:width]
    return text[: width - 1] + "…"


def print_trace(trace: List[dict], tokens: List[str]) -> None:
    if not trace:
        print("(sin traza disponible)\n")
        return

    widths = (40, 8, 50)
    header = clip("Buffer restante", widths[0]) + "  " + clip("Pos", widths[1]) + "  " + clip("Acción", widths[2])
    separator = clip("-" * 16, widths[0]) + "  " + clip("-" * 3, widths[1]) + "  " + clip("-" * 6, widths[2])
    print(header)
    print(separator)

    for evt in trace:
        idx = evt.get("index", 0)
        remaining = " ".join(tokens[idx:]) if idx < len(tokens) else "<eof>"
        action = describe_event(evt)
        row = clip(remaining or "<eof>", widths[0])
        row += "  " + clip(str(idx), widths[1])
        row += "  " + clip(action, widths[2])
        print(row)
    print()


def describe_event(evt: dict) -> str:
    kind = evt.get("event", "?")
    if kind == "start":
        return "Inicio"
    if kind in {"enter", "exit", "fail"}:
        rule = evt.get("rule", "?")
        return f"{kind.upper()} {rule}"
    if kind == "consume":
        token = evt.get("token", "")
        k = evt.get("kind", "tok")
        return f"match {k}='{token}'"
    if kind == "end":
        ok = evt.get("accepted")
        consumed = evt.get("consumed")
        total = evt.get("total")
        status = "OK" if ok else "FAIL"
        return f"Fin ({status}) consumidos={consumed}/{total}"
    return kind


@dataclass
class TreeNode:
    label: str
    children: List["TreeNode"] = field(default_factory=list)


def tuple_to_tree(node: ParseTree) -> TreeNode:
    label = node[0]
    display = LABELS.get(label, label)
    children: List[TreeNode] = []
    for child in node[1:]:
        if isinstance(child, tuple):
            if len(child) == 2 and isinstance(child[1], str):
                friendly = LABELS.get(child[0])
                prefix = f"{child[0]} ({friendly})" if friendly else child[0]
                children.append(TreeNode(f"{prefix}: {child[1]}"))
            else:
                children.append(tuple_to_tree(child))
    title = f"{label} ({display})" if display != label else label
    return TreeNode(title, children)


def print_ascii_tree(tree: ParseTree) -> None:
    root = tuple_to_tree(tree)

    def walk(node: TreeNode, prefix: str, is_last: bool) -> None:
        connector = "└─ " if is_last else "├─ "
        print(prefix + connector + node.label)
        new_prefix = prefix + ("   " if is_last else "│  ")
        for idx, child in enumerate(node.children):
            walk(child, new_prefix, idx == len(node.children) - 1)

    print(root.label)
    for idx, child in enumerate(root.children):
        walk(child, "", idx == len(root.children) - 1)


def main() -> None:
    ap = argparse.ArgumentParser(description="Trace and tree visualizer for the NL parser.")
    ap.add_argument("sentences", nargs="*", help="Sentences to parse (quotes recommended).")
    ap.add_argument("-f", "--file", action="append", default=[], help="Text file with a sentence (one per file).")
    ap.add_argument("--no-trace", action="store_true", help="Hide the step-by-step trace table.")
    ap.add_argument("--ascii-tree", action="store_true", help="Draw the derivation tree with box-drawing characters.")
    ap.add_argument("--png-dir", help="Save each derivation tree as PNG in the given directory (requires matplotlib).")
    args = ap.parse_args()

    sentences = list(args.sentences)
    sentences.extend(load_sentences(args.file))
    if not sentences:
        sentences = DEFAULT_SENTENCES

    rd_parser = Parser()
    png_dir = Path(args.png_dir) if args.png_dir else None
    warned_png = False

    for idx, sentence in enumerate(sentences, start=1):
        print("=" * 72)
        print(f"Sentence: {sentence}")
        print("=" * 72)
        ok, tree, trace = rd_parser.parse_with_trace(sentence)
        tokens = trace[0].get("tokens", rd_parser.tokens) if trace else rd_parser.tokens
        if not args.no_trace:
            print_trace(trace, tokens)
        print("Resultado:", "OK" if ok else "FALLO")
        if tree is not None:
            print()
            if args.ascii_tree:
                print("Árbol de derivación (ASCII):")
                print_ascii_tree(tree)
            else:
                print(format_tree(tree).rstrip())
            if png_dir:
                if plt is None:
                    if not warned_png:
                        print("[WARN] matplotlib no está instalado; no se generan PNG.")
                        warned_png = True
                else:
                    png_dir.mkdir(parents=True, exist_ok=True)
                    slug = slugify(sentence) or f"tree_{idx}"
                    path = png_dir / f"{slug}.png"
                    save_png_tree(tree, path, sentence)
                    print(f"PNG -> {path}")
        print()


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFD", text)
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower()
    text = re.sub(r"[^a-z0-9]+", "-", text).strip("-")
    return text


def save_png_tree(tree: ParseTree, path: Path, title: str) -> None:
    if plt is None:  # pragma: no cover - safeguarded by caller
        raise RuntimeError("matplotlib is not available")
    root = tuple_to_tree(tree)
    positions: dict[int, tuple[float, int]] = {}
    compute_positions(root, 0, {"x": 0}, positions)
    xs = [pos[0] for pos in positions.values()]
    depths = [pos[1] for pos in positions.values()]
    min_x = min(xs)
    max_x = max(xs)
    width = max(max_x - min_x, 1)
    max_depth = max(depths)

    coords: dict[int, tuple[float, float]] = {}
    for node in iter_nodes(root):
        raw_x, depth = positions[id(node)]
        x = 0.05 + 0.9 * ((raw_x - min_x) / width if width else 0.5)
        y = 0.9 - 0.8 * (depth / max_depth if max_depth else 0)
        coords[id(node)] = (x, y)

    fig, ax = plt.subplots(figsize=(8, 4 + max_depth * 0.6))
    ax.axis("off")
    ax.set_title(title, fontsize=12)

    def draw(node: TreeNode) -> None:
        x, y = coords[id(node)]
        ax.text(
            x,
            y,
            node.label,
            ha="center",
            va="center",
            fontsize=10,
            bbox=dict(boxstyle="round,pad=0.3", fc="#F3FAFF", ec="#4A6FA5"),
        )
        for child in node.children:
            cx, cy = coords[id(child)]
            ax.plot([x, cx], [y - 0.02, cy + 0.02], color="#4A6FA5")
            draw(child)

    draw(root)
    fig.tight_layout()
    fig.savefig(path, dpi=200)
    plt.close(fig)


def compute_positions(
    node: TreeNode, depth: int, counter: dict[str, int], positions: dict[int, tuple[float, int]]
) -> None:
    child_xs: List[float] = []
    for child in node.children:
        compute_positions(child, depth + 1, counter, positions)
        child_xs.append(positions[id(child)][0])
    if not child_xs:
        x = float(counter["x"])
        counter["x"] += 1
    else:
        x = sum(child_xs) / len(child_xs)
    positions[id(node)] = (x, depth)


def iter_nodes(node: TreeNode):
    yield node
    for child in node.children:
        yield from iter_nodes(child)


if __name__ == "__main__":
    main()