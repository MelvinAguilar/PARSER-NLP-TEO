Gramática libre de contexto limitada para oraciones SVO (español)

Producciones principales (forma EBNF compacta):

- `S -> NP VP`
- `NP -> NP_atom (Conj NP_atom)*`
- `NP_atom -> (Det) Adj* N | Name | Pron`
- `VP -> V (NP)` (los verbos intransitivos se modelan con la alternativa sin objeto)
- `Conj ->` {`y`, `e`, `ni`, `o`, `u`}

Lexicón de terminales (normalizados en minúsculas y sin tildes):

- `Det ->` el, la, los, las, un, una, unos, unas, este, esta, estos, estas, ese, esa, esos, esas, aquel, aquella, aquellos, aquellas, mi, mis, tu, tus, su, sus, nuestro, nuestra, nuestros, nuestras.
- `Adj ->` grande, roja, rojo, feliz, pequena, pequeno, rapida, rapido, alta, alto, baja, bajo, lenta, lento, nueva, nuevo, vieja, viejo, triste, contenta, contento, hermosa, hermoso, inteligente, fuerte.
- `N ->` nina, nino, ninas, ninos, perro, perros, perra, perras, gata, gato, gatas, gatos, carne, coche, coches, carro, carros, auto, autos, libro, libros, casa, casas, ciudad, ciudades, amigo, amiga, amigos, amigas, familia, familias, maestro, maestra, profesor, profesora, estudiante, estudiantes, padre, madre, hijo, hija, hermano, hermana.
- `V ->` come, comen, como, comes, comemos, mira, miran, miro, miras, miramos, ama, aman, amo, amas, amamos, ve, ven, veo, ves, vemos, corre, corren, corro, corres, corremos, duerme, duermen, duermo, duermes, dormimos, habla, hablan, hablo, hablas, hablamos, escribe, escriben, escribo, escribes, escribimos, tiene, tienen, tengo, tienes, tenemos, camina, caminan, camino, caminas, caminamos, salta, saltan, salto, saltas, saltamos, juega, juegan, juego, juegas, jugamos.
- `Name ->` juan, maria, ana, luis, melvin, henry, mario, fabio, carlos, rodolfo, andrea, sofia, laura, pedro, jose, carmen, paula, diego, ricardo, hugo.
- `Pron ->` ella, el, ellos, ellas, yo, tu, usted, ustedes, nosotros, nosotras.

Convenciones y restricciones:

- Todo se trabaja en minúsculas; el tokenizer elimina puntuación final y normaliza tildes (`niña` → `nina`).
- El vocabulario es reducido y estático; frases fuera de él deben rechazarse.
- La gramática es determinista y está pensada para implementarse con un parser descendente recursivo.
- El árbol sintáctico expone las no terminales `S`, `NP`, `VP`, `Det`, `Adj`, `N`, `V`, `Name`, `Pron` para su inspección en las pruebas.

La sencillez permite contrastar fácilmente con modelos estadísticos (spaCy) en términos de cobertura léxica y manejo de ambigüedad dentro de este micro subconjunto del español.
