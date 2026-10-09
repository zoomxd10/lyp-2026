# Cuarenta

Lenguaje de programación esotérico que se juega con la baraja española de 40 cartas.
El código es una fila de cartas: el palo dice qué hace cada carta, el número dice cuánto,
y el Rey decide si el resultado se lee como números, texto, dibujo o música.

Práctica de **Lenguajes y Paradigmas** · Álvaro Lorenzo, Inés Téllez y Antonio Galván · octubre de 2026

## Qué hay en este repositorio

| Carpeta | Contenido |
|---|---|
| `web/` | El juego: intérprete visual en una sola página (`index.html`). Mesa, mazo, código escrito, ejecución paso a paso, 8 ejemplos, 8 retos y lectura de fotos de nuestra baraja. |
| `python/` | Intérprete de línea de órdenes (`cuarenta.py`, sin librerías externas) y los 8 ejemplos comentados (`ejemplos/*.cuarenta`). |
| `docs/` | Manual del lenguaje: concepto, sintaxis, gramática EBNF, semántica, ejemplos y decisiones de diseño. |
| `herramientas/lector-cartas/` | Fotos de nuestra baraja Fournier y los scripts que generan las 40 referencias que usa la web para reconocer cartas. |

## Probarlo

**Web:** abre `web/index.html` en el navegador. También se puede publicar con GitHub Pages
(Settings → Pages → rama `main`, carpeta `/web` o la raíz) y abrirlo desde el móvil para usar la cámara.

**Python** (3.10 o superior):

```bash
cd python
python cuarenta.py ejemplos/01_cuenta_atras.cuarenta
python cuarenta.py ejemplos/02_hola.cuarenta
python cuarenta.py ejemplos/06_cifrado_cesar.cuarenta --entradas "H"
python cuarenta.py ejemplos/05_escala.cuarenta --wav escala.wav
python cuarenta.py -e "5O SO 1E 2B RE" --traza
```

## Reglas en una tabla

| Carta | Qué hace |
|---|---|
| Oros 1–7 (`5O`) | suma n al marcador |
| Espadas 1–7 (`3E`) | resta n |
| Copas 1–7 (`2C`) | multiplica por n |
| Bastos 1–7 (`2B`) | repite las n cartas anteriores tantas veces como valga el marcador al llegar (máx. 12) |
| Sota (`SO`…) | saca el marcador por la salida |
| Caballo (`CO`…) | lee la siguiente entrada (número o letra) y la suma |
| Rey (`RO`…) | fin. Su palo decide la salida: Oros números, Copas texto, Espadas dibujo, Bastos música |

El marcador empieza en 0, cada carta solo puede aparecer una vez (una sola baraja) y todo programa termina.

## Cómo se hizo

Lo construimos con **Claude Pro** (Anthropic). Nosotros decidimos la idea y cada cambio, lo probamos,
encontramos los fallos y fotografiamos nuestra baraja; Claude programó la web y el intérprete de Python,
preparó las referencias de las cartas, redactó el manual y montó la presentación.
