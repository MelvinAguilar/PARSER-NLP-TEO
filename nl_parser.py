"""Recursive-descent parser for a tiny SVO subset (Spanish only)."""

from __future__ import annotations

import argparse
import re
import unicodedata
from typing import List, Tuple, Optional, Iterable, Dict, Any

ParseTree = Tuple[str, ...]
LABELS = {
    "S": "Oración",
    "NP": "Sintagma nominal",
    "VP": "Sintagma verbal",
    "Det": "Determinante",
    "Adj": "Adjetivo",
    "N": "Sustantivo",
    "V": "Verbo",
    "Name": "Nombre propio",
    "Pron": "Pronombre",
    "Conj": "Conjunción",
}


class Parser:
    """Deterministic parser for a handcrafted SVO grammar."""

    def __init__(self, tokens: Optional[List[str]] = None):
        spanish = {
            "det": {
                "el",
                "la",
                "los",
                "las",
                "un",
                "una",
                "unos",
                "unas",
                "este",
                "esta",
                "estos",
                "estas",
                "ese",
                "esa",
                "esos",
                "esas",
                "aquel",
                "aquella",
                "aquellos",
                "aquellas",
                "mi",
                "mis",
                "tu",
                "tus",
                "su",
                "sus",
                "nuestro",
                "nuestra",
                "nuestros",
                "nuestras",
            },
            "adj": {
                "grande",
                "roja",
                "rojo",
                "feliz",
                "pequena",
                "pequeno",
                "rapida",
                "rapido",
                "alta",
                "alto",
                "baja",
                "bajo",
                "lenta",
                "lento",
                "nueva",
                "nuevo",
                "vieja",
                "viejo",
                "triste",
                "contenta",
                "contento",
                "hermosa",
                "hermoso",
                "inteligente",
                "fuerte",
            },
            "noun": {
                "nina",
                "nino",
                "ninas",
                "ninos",
                "perro",
                "perros",
                "perra",
                "perras",
                "gata",
                "gato",
                "gatas",
                "gatos",
                "carne",
                "coche",
                "coches",
                "carro",
                "carros",
                "auto",
                "autos",
                "libro",
                "libros",
                "casa",
                "casas",
                "ciudad",
                "ciudades",
                "amigo",
                "amiga",
                "amigos",
                "amigas",
                "familia",
                "familias",
                "maestro",
                "maestra",
                "profesor",
                "profesora",
                "estudiante",
                "estudiantes",
                "padre",
                "madre",
                "hijo",
                "hija",
                "hermano",
                "hermana",
            },
            "verb": {
                "come",
                "comen",
                "como",
                "comes",
                "comemos",
                "mira",
                "miran",
                "miro",
                "miras",
                "miramos",
                "ama",
                "aman",
                "amo",
                "amas",
                "amamos",
                "ve",
                "ven",
                "veo",
                "ves",
                "vemos",
                "corre",
                "corren",
                "corro",
                "corres",
                "corremos",
                "duerme",
                "duermen",
                "duermo",
                "duermes",
                "dormimos",
                "habla",
                "hablan",
                "hablo",
                "hablas",
                "hablamos",
                "escribe",
                "escriben",
                "escribo",
                "escribes",
                "escribimos",
                "tiene",
                "tienen",
                "tengo",
                "tienes",
                "tenemos",
                "camina",
                "caminan",
                "camino",
                "caminas",
                "caminamos",
                "salta",
                "saltan",
                "salto",
                "saltas",
                "saltamos",
                "juega",
                "juegan",
                "juego",
                "juegas",
                "jugamos",
            },
            "name": {
                "juan",
                "maria",
                "ana",
                "luis",
                "melvin",
                "henry",
                "mario",
                "fabio",
                "carlos",
                "rodolfo",
                "andrea",
                "sofia",
                "laura",
                "pedro",
                "jose",
                "carmen",
                "paula",
                "diego",
                "ricardo",
                "hugo",
            },
            "pron": {
                "ella",
                "el",
                "ellos",
                "ellas",
                "yo",
                "tu",
                "usted",
                "ustedes",
                "nosotros",
                "nosotras",
            },
            "conj": {"y", "e", "ni", "o", "u"},
        }

        self.dets = set(spanish["det"])
        self.adjs = set(spanish["adj"])
        self.nouns = set(spanish["noun"])
        self.verbs = set(spanish["verb"])
        self.names = set(spanish["name"])
        self.prons = set(spanish["pron"])
        self.conjs = set(spanish["conj"])

        self.lang_vocab = {"es": self._flatten_vocab(spanish.values())}

        self.tokens = tokens or []
        self.i = 0
        self._trace_enabled = False
        self.trace: List[Dict[str, Any]] = []

    @staticmethod
    def _flatten_vocab(groups: Iterable[Iterable[str]]) -> set[str]:
        vocab: set[str] = set()
        for subset in groups:
            vocab.update(subset)
        return vocab

    @staticmethod
    def _normalize_token(token: str) -> str:
        normalized = unicodedata.normalize("NFD", token)
        stripped = "".join(ch for ch in normalized if not unicodedata.combining(ch))
        return stripped

    def detect_language(self, sentence: str) -> str:
        # Solo soportamos español, se mantiene el método para compatibilidad
        return "es"

    def tokenize(self, s: str) -> List[str]:
        s = s.strip().lower()
        s = re.sub(r"[\.? ,!;:]+$", "", s)
        parts = [self._normalize_token(tok) for tok in re.findall(r"\w+", s)]
        return parts

    def parse(self, s: str, with_trace: bool = False) -> Tuple[bool, Optional[ParseTree]]:
        self.tokens = self.tokenize(s)
        self.i = 0
        self._trace_enabled = with_trace
        self.trace = []
        self._log("start", tokens=list(self.tokens))
        tree = self.S()
        accepted = tree is not None and self.i == len(self.tokens)
        self._log("end", accepted=accepted, consumed=self.i, total=len(self.tokens))
        return accepted, tree

    def parse_with_trace(self, s: str) -> Tuple[bool, Optional[ParseTree], List[Dict[str, Any]]]:
        accepted, tree = self.parse(s, with_trace=True)
        return accepted, tree, list(self.trace)

    # Tracing helpers
    def _log(self, event: str, **data: Any) -> None:
        if not self._trace_enabled:
            return
        payload: Dict[str, Any] = {"event": event, "index": self.i}
        payload.update(data)
        self.trace.append(payload)

    def _log_rule(self, rule: str, action: str, **extra: Any) -> None:
        self._log(action, rule=rule, **extra)

    def _log_match(self, kind: str, value: str) -> None:
        self._log("consume", kind=kind, token=value)

    # Helper: peek and consume
    def peek(self) -> Optional[str]:
        if self.i < len(self.tokens):
            return self.tokens[self.i]
        return None

    def eat(self, tok: str) -> bool:
        if self.peek() == tok:
            self.i += 1
            return True
        return False

    # Grammar implementation
    def S(self):
        # S -> NP VP
        pos = self.i
        self._log_rule("S", "enter")
        np = self.NP()
        if np is None:
            self.i = pos
            self._log_rule("S", "fail", expected="NP (sujeto)", token=self.peek())
            return None
        vp = self.VP()
        if vp is None:
            self.i = pos
            self._log_rule("S", "fail", expected="VP (verbo + opcional objeto)", token=self.peek())
            return None
        self._log_rule("S", "exit")
        return ("S", np, vp)

    def NP(self):
        # NP -> NP_atom (Conj NP_atom)*
        pos = self.i
        self._log_rule("NP", "enter")
        first = self._np_atom()
        if first is None:
            self.i = pos
            self._log_rule(
                "NP", "fail", expected="Det/Adj/N, Nombre o Pron", token=self.peek()
            )
            return None

        parts: List[ParseTree] = [first]
        while True:
            w = self.peek()
            if w in self.conjs:
                conj = w
                self._log_match("Conj", conj)
                self.i += 1
                nxt = self._np_atom()
                if nxt is None:
                    self.i = pos
                    self._log_rule(
                        "NP",
                        "fail",
                        expected="Sintagma nominal tras conjunción",
                        token=self.peek(),
                    )
                    return None
                parts.append(("Conj", conj))
                parts.append(nxt)
            else:
                break

        self._log_rule("NP", "exit")
        if len(parts) == 1:
            return parts[0]
        return ("NP", *parts)

    def _np_atom(self) -> Optional[ParseTree]:
        start = self.i
        w = self.peek()
        if w in self.names:
            self._log_match("Name", w)
            self.i += 1
            return ("NP", ("Name", w))

        det = None
        if w in self.dets:
            det = w
            self._log_match("Det", w)
            self.i += 1

        adjs = []
        while True:
            w = self.peek()
            if w in self.adjs:
                self._log_match("Adj", w)
                adjs.append(w)
                self.i += 1
            else:
                break

        w = self.peek()
        if w in self.nouns:
            noun = w
            self._log_match("N", noun)
            self.i += 1
            parts: List[ParseTree] = []
            if det:
                parts.append(("Det", det))
            for adj in adjs:
                parts.append(("Adj", adj))
            parts.append(("N", noun))
            return ("NP", *parts)

        self.i = start
        w = self.peek()
        if w in self.prons:
            self._log_match("Pron", w)
            self.i += 1
            return ("NP", ("Pron", w))

        self.i = start
        return None

    def VP(self):
        # VP -> V NP | V
        pos = self.i
        self._log_rule("VP", "enter")
        w = self.peek()
        if w in self.verbs:
            self._log_match("V", w)
            v = w
            self.i += 1
            # try NP
            np = self.NP()
            if np is not None:
                self._log_rule("VP", "exit")
                return ("VP", ("V", v), np)
            self._log_rule("VP", "exit")
            return ("VP", ("V", v))
        self.i = pos
        self._log_rule("VP", "fail", expected="Verbo", token=w)
        return None


def _display(label: str) -> str:
    friendly = LABELS.get(label)
    return f"{label} ({friendly})" if friendly else label


def format_tree(node: Optional[ParseTree], indent: int = 0) -> str:
    if node is None:
        return ""
    label = node[0]
    pad = "  " * indent
    title = _display(label)
    if len(node) == 2 and isinstance(node[1], tuple):
        # Wrap single child (Name/Pron)
        child = node[1]
        return f"{pad}{title}\n" + format_tree(child, indent + 1)
    if len(node) == 2 and isinstance(node[1], str):
        return f"{pad}{title}: {node[1]}\n"
    lines = [f"{pad}{title}\n"]
    for child in node[1:]:
        if isinstance(child, tuple):
            lines.append(format_tree(child, indent + 1))
        else:
            lines.append(f"{pad}  {child}\n")
    return "".join(lines)


if __name__ == "__main__":
    def render_trace(trace: List[Dict[str, Any]], tokens: List[str]) -> None:
        if not trace:
            print("(sin traza disponible)")
            return
        widths = (34, 6, 20, 50)

        def clip(text: str, width: int) -> str:
            if len(text) <= width:
                return text.ljust(width)
            if width <= 1:
                return text[:width]
            return text[: width - 1] + "…"

        def describe(evt: Dict[str, Any]) -> tuple[str, str]:
            event = evt.get("event", "?")
            rule = evt.get("rule")
            token = evt.get("token")
            expected = evt.get("expected")
            if event == "start":
                return "START", f"Tokens normalizados: {tokens}"
            if event == "enter":
                return f"ENTER {rule}", f"Entrando a la regla {rule}"
            if event == "exit":
                return f"EXIT {rule}", f"Regla {rule} completada"
            if event == "fail":
                details = []
                if expected:
                    details.append(f"esperaba {expected}")
                if token is not None:
                    details.append(f"encontró '{token}'")
                msg = "; ".join(details) if details else "sin coincidencias"
                return f"FAIL {rule}", msg
            if event == "consume":
                kind = evt.get("kind")
                tok = evt.get("token")
                return f"match {kind}", f"Consumido {kind} '{tok}'"
            if event == "end":
                status = "OK" if evt.get("accepted") else "FAIL"
                consumed = evt.get("consumed")
                total = evt.get("total")
                return f"END {status}", f"Consumidos {consumed}/{total} tokens"
            return event.upper(), ""

        header = (
            clip("Buffer restante", widths[0])
            + "  "
            + clip("Pos", widths[1])
            + "  "
            + clip("Acción", widths[2])
            + "  "
            + clip("Descripción", widths[3])
        )
        separator = (
            clip("-" * 16, widths[0])
            + "  "
            + clip("-" * 3, widths[1])
            + "  "
            + clip("-" * 6, widths[2])
            + "  "
            + clip("-" * 10, widths[3])
        )
        print(header)
        print(separator)
        for evt in trace:
            idx = evt.get("index", 0)
            remaining = " ".join(tokens[idx:]) if idx < len(tokens) else "<eof>"
            action, desc = describe(evt)
            row = clip(remaining or "<eof>", widths[0])
            row += "  " + clip(str(idx), widths[1])
            row += "  " + clip(action, widths[2])
            row += "  " + clip(desc, widths[3])
            print(row)

    ap = argparse.ArgumentParser(description="Parser recursivo SVO (español).")
    ap.add_argument("sentence", nargs="*", help="Oración a evaluar (entre comillas si contiene espacios).")
    ap.add_argument("--trace", action="store_true", help="Muestra la traza paso a paso, incluso si falla.")
    args = ap.parse_args()

    sentence = " ".join(args.sentence) if args.sentence else input("Oración: ")
    parser = Parser()
    if args.trace:
        ok, tree, trace = parser.parse_with_trace(sentence)
    else:
        ok, tree = parser.parse(sentence)
        trace = []

    print("ACCEPTED" if ok else "REJECTED")
    if args.trace:
        render_trace(trace or parser.trace, parser.tokens)

    if tree is not None:
        print(format_tree(tree))
    elif not ok:
        print("No se pudo construir el árbol; revisa la traza para ver en qué regla falló.")
