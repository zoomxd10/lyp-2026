#!/usr/bin/env python3
"""
Cuarenta — intérprete de un lenguaje de programación esotérico hecho con la baraja española.

Un programa es una fila de cartas que se lee de izquierda a derecha (y, si hay varias
filas, de arriba abajo). Hay una única memoria, el MARCADOR, que empieza en 0.

    Oros 1-7     suma n al marcador                      (5O)
    Espadas 1-7  resta n                                 (3E)
    Copas 1-7    multiplica por n                        (2C)
    Bastos 1-7   repite las n cartas anteriores tantas veces como valga el
                 marcador al llegar (máximo 12)          (2B)
    Sota         saca el marcador por la salida          (SO, SC, SE, SB)
    Caballo      lee la siguiente entrada y la suma      (CO, CC, CE, CB)
    Rey          termina; su palo dice cómo se lee la salida:
                 RO números · RC texto · RE dibujo · RB música

Solo hay una baraja: cada carta puede aparecer una vez como mucho.
Todo programa termina, porque cada bucle fija su número de vueltas antes de empezar.

Uso:
    python cuarenta.py programa.cuarenta
    python cuarenta.py programa.cuarenta --entradas "3, 4"
    python cuarenta.py programa.cuarenta --traza            (muestra cada jugada)
    python cuarenta.py programa.cuarenta --wav escala.wav   (guarda la música en un .wav)
    python cuarenta.py -e "5O SO 1E 2B RO"                  (código directo)
"""

import argparse
import math
import re
import struct
import sys
import unicodedata
import wave
from dataclasses import dataclass, field

# --------------------------------------------------------------------------------------
# Constantes del lenguaje
# --------------------------------------------------------------------------------------

PALOS = {"O": "Oros", "C": "Copas", "E": "Espadas", "B": "Bastos"}
FIGURAS = {10: "Sota", 11: "Caballo", 12: "Rey"}
MODOS = {"O": "números", "C": "texto", "E": "dibujo", "B": "música"}
ALFABETO = "ABCDEFGHIJKLMNÑOPQRSTUVWXYZ"          # A=1 … Ñ=15 … Z=27, 0 = espacio
NOTAS = ["Do", "Re", "Mi", "Fa", "Sol", "La", "Si"]
SEMITONOS = [0, 2, 4, 5, 7, 9, 11]
SIMBOLOS = {"O": "🪙", "C": "🍷", "E": "🗡️", "B": "🪵"}
SIMBOLOS_ASCII = {"O": "o", "C": "u", "E": "|", "B": "!"}
MAX_VUELTAS = 12
MAX_JUGADAS = 100_000

# Una carta en texto: valor (1-7, S, C, R o 10-12) seguido del palo (O, C, E, B)
TOKEN = re.compile(r"^(1[0-2]|[1-7]|[SCR])([OCEB])$", re.IGNORECASE)


class Renuncio(Exception):
    """Error de Cuarenta. En las cartas, 'renuncio' es saltarse una regla del juego."""


@dataclass(frozen=True)
class Carta:
    valor: int      # 1-7, 10 (Sota), 11 (Caballo) o 12 (Rey)
    palo: str       # O, C, E, B
    linea: int = 0  # línea del código fuente, para los mensajes de error

    @property
    def nombre(self) -> str:
        return f"{FIGURAS.get(self.valor, self.valor)} de {PALOS[self.palo]}"

    @property
    def clave(self) -> str:
        return f"{self.valor}{self.palo}"


# --------------------------------------------------------------------------------------
# Análisis léxico y sintáctico
# --------------------------------------------------------------------------------------

def analizar(codigo: str) -> list[Carta]:
    """Convierte el código escrito en una lista de cartas.

    Gramática (EBNF):
        programa   = { linea } ;
        linea      = { carta } [ comentario ] "\\n" ;
        carta      = valor palo ;
        valor      = "1" | "2" | "3" | "4" | "5" | "6" | "7"
                   | "S" | "C" | "R" | "10" | "11" | "12" ;
        palo       = "O" | "C" | "E" | "B" ;
        comentario = "#" { cualquier carácter } ;
    Las cartas se separan con espacios, comas o "·".
    Regla semántica: ninguna carta puede repetirse (solo hay una baraja).
    """
    cartas, vistas = [], {}
    for n, linea in enumerate(codigo.splitlines(), start=1):
        sin_comentario = linea.split("#", 1)[0]
        for tok in filter(None, re.split(r"[\s,·;]+", sin_comentario)):
            m = TOKEN.match(tok)
            if not m:
                raise Renuncio(f"línea {n}: «{tok}» no es una carta (ejemplos válidos: 5O, SC, RB)")
            valor = {"S": 10, "C": 11, "R": 12}.get(m.group(1).upper()) or int(m.group(1))
            carta = Carta(valor, m.group(2).upper(), n)
            if carta.clave in vistas:
                raise Renuncio(f"línea {n}: el {carta.nombre} ya está en la línea {vistas[carta.clave]}; "
                               "con una sola baraja solo hay uno")
            vistas[carta.clave] = n
            cartas.append(carta)
    return cartas


def modo_de(programa: list[Carta]) -> str | None:
    """El primer Rey del programa es el que lo termina (no hay saltos hacia delante),
    así que su palo decide cómo se lee la salida."""
    return next((c.palo for c in programa if c.valor == 12), None)


def leer_entradas(texto: str) -> list[int]:
    """'3, 4' -> [3, 4];  'H' -> [8];  'HOLA' -> [8, 16, 12, 1]."""
    valores = []
    for tok in filter(None, (t.strip() for t in re.split(r"[,;]", texto or ""))):
        if re.fullmatch(r"-?\d+", tok):
            valores.append(int(tok))
        else:
            valores.extend(v for v in (valor_letra(ch) for ch in tok) if v is not None)
    return valores


def valor_letra(ch: str) -> int | None:
    if ch in " _":
        return 0
    ch = ch.upper()
    if ch != "Ñ":
        ch = unicodedata.normalize("NFD", ch).encode("ascii", "ignore").decode() or ch
    i = ALFABETO.find(ch)
    return i + 1 if i >= 0 else None


# --------------------------------------------------------------------------------------
# Intérprete
# --------------------------------------------------------------------------------------

@dataclass
class Bucle:
    posicion: int   # dónde está el Basto
    total: int      # vueltas decididas al llegar
    quedan: int     # vueltas que faltan


@dataclass
class Partida:
    programa: list[Carta]
    entradas: list[int]
    marcador: int = 0
    pc: int = 0                       # carta que toca
    salida: list[int] = field(default_factory=list)
    bucles: list[Bucle] = field(default_factory=list)
    jugadas: int = 0
    terminada: bool = False
    traza: list[str] = field(default_factory=list)

    def paso(self) -> None:
        """Ejecuta una carta."""
        if self.pc >= len(self.programa):
            self.terminada = True
            self.traza.append("Se acabaron las cartas sin un Rey: la salida se lee como números.")
            return
        self.jugadas += 1
        if self.jugadas > MAX_JUGADAS:
            raise Renuncio(f"la partida pasa de {MAX_JUGADAS} jugadas")

        c = self.programa[self.pc]
        antes = self.marcador

        if c.valor <= 7 and c.palo == "O":
            self.marcador += c.valor
            self._anota(c, f"{antes} + {c.valor} = {self.marcador}")
            self.pc += 1
        elif c.valor <= 7 and c.palo == "E":
            self.marcador -= c.valor
            self._anota(c, f"{antes} − {c.valor} = {self.marcador}")
            self.pc += 1
        elif c.valor <= 7 and c.palo == "C":
            self.marcador *= c.valor
            self._anota(c, f"{antes} × {c.valor} = {self.marcador}")
            self.pc += 1
        elif c.valor <= 7 and c.palo == "B":
            self._basto(c)
        elif c.valor == 10:                                   # Sota
            self.salida.append(self.marcador)
            self._anota(c, f"saca {self.marcador}")
            self.pc += 1
        elif c.valor == 11:                                   # Caballo
            if not self.entradas:
                raise Renuncio(f"el {c.nombre} pide una entrada, pero no quedan (usa --entradas)")
            v = self.entradas.pop(0)
            self.marcador += v
            self._anota(c, f"entra {v} → {antes} + {v} = {self.marcador}")
            self.pc += 1
        else:                                                 # Rey
            self.terminada = True
            self._anota(c, f"fin; la salida se lee como {MODOS[c.palo]}")

    def _basto(self, c: Carta) -> None:
        """Bucle de vueltas fijas. Si el Basto ya tiene un bucle abierto, cuenta una vuelta;
        si no, abre uno con tantas vueltas como valga el marcador (entre 0 y 12)."""
        def saltar():
            self.pc = max(0, self.pc - c.valor)

        abierto = self.bucles[-1] if self.bucles else None
        if abierto and abierto.posicion == self.pc:
            if abierto.quedan > 0:
                abierto.quedan -= 1
                self._anota(c, f"vuelta {abierto.total - abierto.quedan} de {abierto.total}")
                saltar()
            else:
                self.bucles.pop()
                self._anota(c, f"bucle terminado tras {abierto.total} {'vuelta' if abierto.total == 1 else 'vueltas'}")
                self.pc += 1
            return
        vueltas = max(0, min(MAX_VUELTAS, self.marcador))
        if vueltas == 0:
            self._anota(c, f"el marcador vale {self.marcador} → no repite nada")
            self.pc += 1
            return
        self.bucles.append(Bucle(self.pc, vueltas, vueltas - 1))
        self._anota(c, f"el marcador vale {self.marcador} → repite {vueltas} {'vez' if vueltas == 1 else 'veces'} "
                          f"{'la carta anterior' if c.valor == 1 else f'las {c.valor} cartas anteriores'}")
        saltar()

    def _anota(self, c: Carta, texto: str) -> None:
        self.traza.append(f"{c.nombre}: {texto}")

    def jugar(self) -> list[int]:
        while not self.terminada:
            self.paso()
        return self.salida


# --------------------------------------------------------------------------------------
# Las cuatro formas de leer la salida
# --------------------------------------------------------------------------------------

def letra(n: int) -> str:
    m = n % 28
    return " " if m == 0 else ALFABETO[m - 1]


def nombre_nota(n: int) -> str:
    if n <= 0:
        return "silencio"
    i, octava = (n - 1) % 7, min(2, (n - 1) // 7)
    return NOTAS[i] + "'" * octava


def frecuencia(n: int) -> float:
    i, octava = (n - 1) % 7, min(2, (n - 1) // 7)
    return 261.63 * 2 ** ((SEMITONOS[i] + 12 * octava) / 12)


def palo_fila(n: int) -> str:
    return "BOCE"[abs(n) % 4]           # 1 oros, 2 copas, 3 espadas, 0 bastos


def mostrar(salida: list[int], modo: str | None, ascii_only: bool = False) -> str:
    if modo == "C":
        return "".join(letra(n) for n in salida)
    if modo == "E":
        simbolos = SIMBOLOS_ASCII if ascii_only else SIMBOLOS
        # se centra contando símbolos (no caracteres): cada símbolo ocupa 3 columnas
        anchos = [min(abs(n), MAX_VUELTAS) for n in salida]
        mayor = max(anchos, default=0)
        paso = 2 if ascii_only else 3
        return "\n".join(" " * ((mayor - k) * paso // 2) + " ".join([simbolos[palo_fila(n)]] * k)
                         for n, k in zip(salida, anchos))
    if modo == "B":
        return " ".join(nombre_nota(n) for n in salida)
    return " ".join(str(n) for n in salida)


def guardar_wav(salida: list[int], ruta: str, duracion: float = 0.4, muestreo: int = 22050) -> None:
    """Sintetiza la melodía (onda triangular con ataque y caída suaves) en un .wav."""
    marcos = bytearray()
    por_nota = int(duracion * muestreo)
    for n in salida:
        f = frecuencia(n) if n > 0 else 0.0
        for i in range(por_nota):
            t = i / muestreo
            envolvente = min(1.0, i / (0.02 * muestreo)) * math.exp(-4 * t)
            onda = (2 / math.pi) * math.asin(math.sin(2 * math.pi * f * t)) if f else 0.0
            marcos += struct.pack("<h", int(12000 * envolvente * onda))
    with wave.open(ruta, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)
        w.setframerate(muestreo)
        w.writeframes(bytes(marcos))


# --------------------------------------------------------------------------------------
# Línea de órdenes
# --------------------------------------------------------------------------------------

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description="Intérprete de Cuarenta, el lenguaje de la baraja española.")
    ap.add_argument("fichero", nargs="?", help="programa .cuarenta")
    ap.add_argument("-e", "--codigo", help="código directo, por ejemplo \"5O SO 1E 2B RO\"")
    ap.add_argument("--entradas", default="", help="entradas para los Caballos: \"3, 4\" o \"HOLA\"")
    ap.add_argument("--traza", action="store_true", help="muestra cada jugada")
    ap.add_argument("--wav", help="con el Rey de Bastos, guarda la música en este fichero .wav")
    ap.add_argument("--ascii", action="store_true", help="dibuja con letras en vez de emojis")
    args = ap.parse_args(argv)

    if args.codigo is None and args.fichero is None:
        ap.error("indica un fichero .cuarenta o usa -e \"código\"")
    codigo = args.codigo if args.codigo is not None else open(args.fichero, encoding="utf-8").read()

    try:
        programa = analizar(codigo)
        modo = modo_de(programa)
        partida = Partida(programa, leer_entradas(args.entradas))
        try:
            partida.jugar()
        finally:
            if args.traza:
                print("\n".join(partida.traza), end="\n\n")
    except Renuncio as e:
        print(f"¡Renuncio! {e}", file=sys.stderr)
        return 1

    print(f"Salida ({MODOS.get(modo, 'números')}):")
    print(mostrar(partida.salida, modo, args.ascii))
    if args.wav:
        if modo != "B":
            print("Aviso: --wav solo tiene sentido con el Rey de Bastos (música).", file=sys.stderr)
        guardar_wav(partida.salida, args.wav)
        print(f"Música guardada en {args.wav}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
