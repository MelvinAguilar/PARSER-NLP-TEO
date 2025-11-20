# parser-LL1-TEO2025

Repositorio didáctico para experimentar con un mini-parser descendente recursivo que acepta oraciones SVO en español. El foco actual es exclusivamente el módulo de lenguaje natural (`nl_parser.py`) y sus herramientas auxiliares para traza, visualización de árboles, comparación con spaCy y ejecución automatizada de pruebas.

## Requisitos

- Python 3.10+
- `pip install -r requirements.txt`
- (Opcional) `python -m spacy download es_core_news_sm` para habilitar `compare_nlp.py`

## Estructura relevante

- `nl_parser.py`: parser principal y CLI (`--trace`, `--file`, etc.).
- `nl_parser_tree.py`: imprime la traza paso a paso y el árbol (ASCII o PNG via `matplotlib`).
- `compare_nlp.py`: compara el parser artesanal contra spaCy para la misma oración.
- `run_nl_tests.py`: ejecuta todos los casos de `tests/nl_ok` (esperado OK) y `tests/nl_fail` (esperado error).
- `nl_grammar.md`: gramática, vocabulario permitido y notas de diseño.
- `tests/nl_ok`, `tests/nl_fail`: corpus base en texto plano (UTF-8, una oración por archivo).
- `tree_pngs/`: ejemplos exportados con `nl_parser_tree.py --png-dir`.

## Uso rápido

```bash
python nl_parser.py "La niña mira el perro"
```

### Trazas detalladas

```bash
python nl_parser.py --trace "Corre la niña el perro"
```

La salida `--trace` muestra columnas Buffer/Pos/Acción/Descripción para entender qué regla se aplica, qué token se consume o qué símbolo se esperaba cuando ocurre un error.

### Coordinación básica

```bash
python nl_parser.py "Melvin y Mario miran los autos"
```

El parser admite sujetos u objetos coordinados mediante las conjunciones `y`, `e`, `ni`, `o`, `u`, reutilizando la gramática determinista documentada en `nl_grammar.md`.

### Árboles ASCII y PNG

```bash
python nl_parser_tree.py --ascii-tree "La niña mira el perro"
python nl_parser_tree.py --png-dir out/trees "La niña mira el perro."
```

`--ascii-tree` imprime el árbol en consola y `--png-dir` genera imágenes en la carpeta indicada (se crea automáticamente).

### Batería de pruebas

```bash
python run_nl_tests.py --show-tree
```

`run_nl_tests.py` recorre las carpetas `tests/nl_ok` y `tests/nl_fail`, ejecuta cada archivo y, opcionalmente, imprime el árbol para las frases aceptadas.

### Comparación con spaCy

```bash
python compare_nlp.py --show-tree tests/nl_ok/003_la_nina_mira_el_perro.txt
```

El comparador indica si la oración fue aceptada por el parser artesanal, qué roles (sujeto, verbo, objeto) detectó spaCy y muestra los árboles producidos. Si el modelo de spaCy no está instalado, el script continúa sin ese análisis adicional.

## Glosario de etiquetas

- `S`: oración completa.
- `NP`: sintagma nominal (sujeto u objeto).
- `VP`: sintagma verbal.
- `Det`, `Adj`, `N`, `V`: terminales básicos.
- `Name`, `Pron`: nombres propios y pronombres manejados como terminales.
- `Conj`: conjunciones coordinantes (`y`, `e`, `ni`, `o`, `u`).

## Limitaciones actuales

- Vocabulario cerrado: cualquier palabra fuera de `nl_grammar.md` causa error inmediato.
- Orden rígido SVO: no hay inversión sujeto/verbo ni cláusulas subordinadas.
- Sin acuerdo morfológico: el parser solo valida la secuencia, no la concordancia.
- No se manejan ambigüedades ni varias derivaciones para una misma oración.

## Próximos pasos sugeridos

- Ampliar el vocabulario y las reglas de `nl_grammar.md`.
- Integrar más diagnósticos en `compare_nlp.py` (por ejemplo, dependencias adicionales de spaCy).
- Añadir más casos en `tests/nl_fail` que cubran errores de orden y vocabulario.
