# Lector de cartas

La web reconoce las cartas de nuestra baraja Fournier comparando cada carta de la foto con 40 referencias.
Estas referencias salen de las 4 fotos de `fotos-baraja/` (una por palo, sobre la mesa blanca).

1. **Encontrar cartas:** píxeles más oscuros que su entorno (borde y marco impreso) → componentes conexas → rectángulo de área mínima girando de -20° a 20°.
2. **Firma:** la carta se muestrea en su propio giro en una rejilla de 18 × 27 colores, normalizada.
3. **Comparar:** parecido (coseno) con las 40 referencias, probando pequeños desplazamientos, escalas y la carta del revés.
4. **Una sola baraja:** cada referencia se asigna como mucho a una carta, empezando por el parecido más alto.

Para regenerar las referencias con otra baraja (requiere `numpy`, `scipy` y `Pillow`), cambia las fotos y el orden de las cartas en `build_refs.py` (`ORDER`) y ejecuta:

```bash
python build_refs.py        # comprueba la detección y dibuja las etiquetas en salida/
python build2.py            # firmas con giro → salida/refs2.npy
python eval2.py             # prueba con fotos giradas, más claras y más oscuras
python exportar_referencias.py   # → referencias.json
```

Después hay que pegar el contenido de `referencias.json` en `web/index.html`, en la línea `const DECK = {...}`.
`deckreader.js` es el mismo lector que va dentro de la web, por separado para leerlo con calma.
