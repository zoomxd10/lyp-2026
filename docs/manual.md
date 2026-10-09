# Cuarenta: manual del lenguaje

Álvaro Lorenzo · Inés Téllez · Antonio Galván — Lenguajes y Paradigmas, octubre de 2026

## Concepto

Cuarenta es un lenguaje de programación esotérico en el que el código es una fila de cartas de la baraja española de 40 cartas. Se puede programar con cartas de verdad sobre una mesa, sin escribir nada, y ejecutarlo a mano, en el intérprete web o en el intérprete de Python.

La idea sale de los juegos de cartas españoles. Cada carta ya tiene dos datos que todo el mundo conoce, el palo y el número, y en Cuarenta el palo dice **qué** hace la carta y el número dice **cuánto**. Las figuras son las órdenes especiales y el Rey, como en el juego, es el que manda: decide cómo se lee el resultado.

El nombre viene de las 40 cartas de la baraja y de «cantar las cuarenta» del tute.

Tres restricciones le dan carácter:

- **Una sola baraja.** Cada carta puede usarse una vez como mucho, así que no se puede repetir una instrucción: hay que pensar con bucles.
- **Una sola memoria.** Todo el programa trabaja sobre un único número, el marcador, como el tanteo de una partida.
- **Todo programa termina.** Los bucles deciden sus vueltas antes de empezar, así que no existe el bucle infinito.

El resultado no es solo un número: según el Rey que cierre el programa, la salida es texto, un dibujo hecho con símbolos de la baraja o una melodía.

## Sintaxis

Un programa de Cuarenta tiene dos formas equivalentes: la física, con cartas sobre la mesa, y la escrita, con texto. El intérprete web pasa de una a otra.

**Forma física.** Las cartas se colocan boca arriba y se leen como un libro: filas de arriba abajo y, dentro de cada fila, de izquierda a derecha. Los comentarios no existen; los explica en voz alta quien juega.

**Forma escrita.** Cada carta es su valor seguido de su palo. Las cartas se separan con espacios, comas o el punto medio, y todo lo que hay detrás de `#` es un comentario.

| Parte | Se escribe | Ejemplo |
| --- | --- | --- |
| Números del 1 al 7 | la cifra | `5O` = 5 de Oros |
| Sota | `S` (o `10`) | `SC` = Sota de Copas |
| Caballo | `C` (o `11`) | `CB` = Caballo de Bastos |
| Rey | `R` (o `12`) | `RE` = Rey de Espadas |
| Palos | `O` Oros, `C` Copas, `E` Espadas, `B` Bastos | |
| Comentario | `#` hasta el final de la línea | `2B  # repite` |

No hay ambigüedad entre la C de Caballo y la C de Copas porque el valor va siempre primero: `CC` es el Caballo de Copas y `1C` es el 1 de Copas.

**Gramática (EBNF)**

```
programa   = { linea } ;
linea      = { carta } [ comentario ] salto ;
carta      = valor palo ;
valor      = "1" | "2" | "3" | "4" | "5" | "6" | "7"
           | "S" | "C" | "R" | "10" | "11" | "12" ;
palo       = "O" | "C" | "E" | "B" ;
comentario = "#" { cualquier carácter } ;
```

La gramática tiene una regla semántica añadida: **ninguna carta puede aparecer dos veces**, porque solo hay una baraja. Repetir una carta es un error, que en Cuarenta se llama «¡Renuncio!», como cuando alguien se salta una regla en una partida.

## Semántica

La máquina de Cuarenta tiene un marcador (un entero que empieza en 0), una cola de entradas, una lista de salida y una pila de bucles abiertos. Las cartas se ejecutan de una en una, de izquierda a derecha.

| Carta | Qué hace | Ejemplo |
| --- | --- | --- |
| Oros 1–7 | suma n al marcador | `5O`: 0 → 5 |
| Espadas 1–7 | resta n | `2E`: 5 → 3 |
| Copas 1–7 | multiplica por n | `4C`: 3 → 12 |
| Bastos 1–7 | repite las n cartas anteriores tantas veces como valga el marcador al llegar (máximo 12) | `2B` |
| Sota (cualquier palo) | añade el marcador a la salida | `SO` |
| Caballo (cualquier palo) | lee la siguiente entrada y la suma | `CO` |
| Rey | termina el programa; su palo decide cómo se lee la salida | `RC` |

**Los bucles (Bastos).** Cuando la ejecución llega a un Basto por primera vez, mira el marcador y fija cuántas vueltas dará: entre 0 y 12. Si es 0 o negativo, no repite nada. Si no, vuelve atrás n cartas y repite ese tramo las vueltas fijadas, aunque el marcador cambie por el camino. Como el número de vueltas no puede crecer una vez empezado, todo programa termina, también con bucles dentro de bucles. Es un bucle `for`, no un `while`.

**Las entradas (Caballos).** Las entradas pueden ser números o letras. Una letra vale su posición en el alfabeto español: `H` vale 8 y `HOLA` son cuatro entradas, 8, 16, 12 y 1. Si un Caballo pide una entrada y no quedan, es un error.

**El final (Reyes).** El programa termina con el primer Rey. Como en Cuarenta no se puede saltar hacia delante, el primer Rey de la fila es siempre el que se ejecuta, y su palo se conoce antes de empezar. Si se acaban las cartas sin ningún Rey, el programa termina igual y la salida se lee como números.

| Rey | La salida se lee como | Cada número n es… | Ejemplo |
| --- | --- | --- | --- |
| Rey de Oros | números | el propio número | 5 4 3 |
| Rey de Copas | texto | una letra: 1 = A … 15 = Ñ … 27 = Z, 0 = espacio (se cuenta en círculo cada 28) | 8 16 12 1 → HOLA |
| Rey de Espadas | dibujo | una fila con n símbolos (máximo 12); el palo de la fila es el resto de n entre 4: 1 oros, 2 copas, 3 espadas, 0 bastos | 3 → tres espadas |
| Rey de Bastos | música | una nota de la escala de Do mayor: 1 Do, 2 Re … 7 Si, 8 Do agudo; 0 o menos = silencio | 5 → Sol |

**Errores («¡Renuncio!»).** Hay tres: una carta repetida o mal escrita en el código, un Caballo sin entradas y, como límite de seguridad del intérprete web, una partida de más de 5.000 jugadas.

## Ejemplos comentados

Los ocho ejemplos están en el intérprete web y en la carpeta `python/ejemplos/`, y dan la misma salida en los dos.

**1. Cuenta atrás (números).** Salida: `5 4 3 2 1`.

```
5O   # marcador = 5
SO   # muestra el marcador
1E   # le resta 1
2B   # repite las 2 cartas anteriores tantas veces como marque el marcador (4)
RO   # fin. Rey de Oros: la salida se lee como números
```

Así se ejecuta, jugada a jugada:

| Jugada | Carta | Marcador | Salida | Qué pasa |
| --- | --- | --- | --- | --- |
| 1 | 5O | 5 | | suma 5 |
| 2 | SO | 5 | 5 | muestra |
| 3 | 1E | 4 | 5 | resta 1 |
| 4 | 2B | 4 | 5 | el marcador vale 4: fija 4 vueltas y vuelve a SO |
| 5–12 | SO, 1E, 2B … | 3, 2, 1, 0 | 5 4 3 2 1 | vueltas 2, 3 y 4 |
| 13 | 2B | 0 | 5 4 3 2 1 | bucle terminado, sigue |
| 14 | RO | 0 | 5 4 3 2 1 | fin, salida como números |

**2. Hola (texto).** Salida: `HOLA`. Cada letra necesita su propia Sota, y como hay justo cuatro Sotas, cuatro letras es lo máximo que se escribe sin bucles.

```
7O 1O   # 7 + 1 = 8 → H
SO      # escribe H
2C      # 8 × 2 = 16 → O
SC      # escribe O
4E      # 16 − 4 = 12 → L
SE      # escribe L
6E 5E   # 12 − 6 − 5 = 1 → A
SB      # escribe A
RC      # fin. Rey de Copas: la salida se lee como texto
```

**3. Pirámide (dibujo).** El mismo programa que la cuenta atrás, cambiando solo el Rey: ahora cada número es una fila de símbolos.

```
5O   # marcador = 5
SO   # dibuja una fila de 5
1E   # una menos
2B   # repite 4 veces → filas de 4, 3, 2 y 1
RE   # fin. Rey de Espadas: la salida se lee como dibujo
```

**4. Rombo (dibujo, dos bucles seguidos).** Salida: filas de 1, 2, 3, 4, 3, 2 y 1 símbolos. El primer bucle cuenta hacia arriba porque las vueltas se fijan al llegar: aunque el marcador crezca, el bucle no se alarga.

```
3O 2E      # marcador = 1
SO 1O      # dibuja una fila y suma 1
2B         # el marcador vale 2 → repite 2 veces: filas 1, 2, 3 (acaba en 4)
SC 1E 1C   # dibuja, resta 1 y multiplica por 1 (no cambia nada: es relleno)
3B         # el marcador vale 3 → repite 3 veces: filas 4, 3, 2, 1
RE         # fin. Salida como dibujo
```

**5. Escala (música).** Salida: Do' Si La Sol Fa Mi Re Do, la escala de Do hacia abajo. En la web suena mientras se ejecuta; en Python se guarda con `--wav`.

```
7O 1O   # marcador = 8 (Do agudo)
SO      # toca la nota
1E      # baja una nota
2B      # repite 7 veces: Si, La, Sol, Fa, Mi, Re, Do
RB      # fin. Rey de Bastos: la salida se lee como música
```

**6. Cifrado César (texto con entrada).** Con la entrada `H` escribe `K`: la letra avanza tres posiciones.

```
CO   # lee la entrada; una letra vale su posición (H = 8)
3O   # suma 3
SO   # escribe la letra
RC   # fin. Salida como texto
```

Los otros dos ejemplos son **Sumar entradas** (`CO CC SO RO`, con entradas 3 y 4 da 7) y **Potencias de dos** (`1O SO 2C 2B RO`, da 1 2 4).

## Implementación

Cuarenta se ejecuta de tres maneras, y las tres siguen las mismas reglas: a mano sobre la mesa, en un intérprete web y en un intérprete de Python. Da igual cómo se escriba el programa: el intérprete siempre trabaja con la misma lista de cartas, y solo al final mira el Rey para decidir cómo enseñar el resultado.

**A mano.** Se colocan las cartas, se pone una moneda como puntero sobre la primera y se apunta el marcador en un papel. Para los bucles basta con dejar al lado del Basto tantas fichas como vueltas queden.

**Intérprete web (JavaScript).** Una página con un tapete donde se colocan las cartas tocando el mazo, se escribe el código o se hace una foto a cartas reales. Ejecuta carta a carta con una ficha dorada que marca la carta actual, muestra el marcador y una traza en español, y pinta la salida como números, texto, dibujo o música (con Web Audio). Incluye 8 ejemplos y 8 retos con comprobación automática.

**Lectura de fotos.** La página reconoce las cartas de nuestra propia baraja Fournier comparándolas con 40 fotos de referencia, en el propio dispositivo y sin conexión. Primero busca cada carta por las líneas más oscuras que su entorno (el borde y el marco impreso), así que funciona sobre una mesa blanca. Después mide su giro, la convierte en una rejilla de 18 × 27 colores y la compara con las 40 referencias, probando pequeños desplazamientos y la carta del revés. Si dos cartas se parecen a la misma referencia, aplica la regla del lenguaje: con una sola baraja, cada carta solo puede estar una vez. En las pruebas con nuestras fotos giradas y con distinta luz reconoció 158 de 160 cartas sin confundir ninguna. Cualquier carta se puede corregir antes de ejecutar.

**Intérprete de Python.** El fichero `cuarenta.py` no necesita librerías externas y tiene tres partes: el analizador (`analizar`), que aplica la gramática y la regla de la baraja única; la máquina (`Partida`), que ejecuta carta a carta con su pila de bucles; y la salida (`mostrar`), que traduce los números a texto, a un dibujo con emojis o a notas, y puede guardar la melodía en un `.wav`.

```
python cuarenta.py ejemplos/05_escala.cuarenta --wav escala.wav
python cuarenta.py ejemplos/06_cifrado_cesar.cuarenta --entradas "H"
python cuarenta.py -e "5O SO 1E 2B RE" --traza
```

## Decisiones de diseño y desafíos

La decisión que más ha marcado el lenguaje es que se pueda jugar con una sola baraja física y nada más; casi todas las demás salen de ahí.

| Decisión | Alternativa descartada | Por qué |
| --- | --- | --- |
| El palo dice qué hace la carta y el número dice cuánto | Una tabla con un significado distinto para cada una de las 40 cartas | Se aprende en un minuto y cabe en una chuleta de 7 reglas |
| Una sola memoria (el marcador) | Variables con nombre o una pila | Con cartas físicas no hay dónde escribir nombres; un solo número se lleva de cabeza |
| Una sola baraja: cada carta una vez | Permitir varias barajas | Es la restricción que obliga a usar bucles y hace interesante el lenguaje |
| Bucles con las vueltas fijadas al llegar | Bucle «mientras el marcador no sea 0» | La primera versión permitía bucles infinitos; con vueltas fijas todo programa termina |
| El Rey decide cómo se lee la salida | Una carta distinta para cada tipo de salida | Las 4 Sotas sirven en cualquier modo y un mismo programa da números, texto, dibujo o música cambiando una carta |
| Notación escrita valor + palo | Solo la forma física | Permite comentar los ejemplos, compartir programas y escribir el intérprete de Python |

**Desafíos que encontramos:**

- **Bucles infinitos.** Con la regla original del Basto («vuelve atrás si el marcador no es 0»), programas como `1O SB 1B RB` no terminaban nunca. Fijar las vueltas al llegar lo resolvió sin quitar potencia para lo que el lenguaje hace.
- **Pocas cartas de salida.** Solo hay 4 Sotas. Al principio cada palo de Sota iba a ser un tipo de salida distinto, pero entonces solo se podría escribir una letra. Pasar esa decisión al Rey dejó las cuatro Sotas libres.
- **Leer cartas reales con la cámara.** La app del móvil no deja enviar imágenes a Claude, así que hubo que escribir un lector propio. Contar símbolos fallaba con las espadas y los bastos, que en la baraja real se cruzan, y con las figuras. Lo resolvimos fotografiando nuestra baraja y comparando cada carta con esas 40 referencias.
- **El alfabeto.** Usar el alfabeto español de 27 letras (con Ñ) obliga a contar en círculo cada 28 para incluir el espacio.

**Lo que no es Cuarenta:** no es Turing completo (una sola memoria y bucles acotados), y es a propósito: a cambio, cualquier programa se puede ejecutar a mano en una mesa y siempre termina.
