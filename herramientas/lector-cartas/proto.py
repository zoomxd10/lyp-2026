"""Prototipo del lector: mismas operaciones que luego irán en JavaScript."""
import numpy as np
from PIL import Image, ImageDraw
from scipy import ndimage

WORK = 1400         # lado mayor de trabajo
GW, GH = 18, 27     # rejilla de la firma (retrato)


def load(path, rot=0, bright=1.0):
    im = Image.open(path).convert('RGB')
    if rot:
        im = im.rotate(rot, resample=Image.BILINEAR, expand=True, fillcolor=(235, 235, 235))
    s = WORK / max(im.size)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.BILINEAR)
    a = np.asarray(im).astype(np.float32) * bright
    return np.clip(a, 0, 255)


def ink_mask(a):
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    gray = 0.299 * r + 0.587 * g + 0.114 * b
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    bg = np.median(gray)
    return ((gray < bg - 70) | ((sat > 0.35) & (mx > 60))), bg


def box_dilate(m, r):
    # máximo en ventana (2r+1) separable, igual que en JS
    m = ndimage.maximum_filter1d(m.astype(np.uint8), 2 * r + 1, axis=1)
    return ndimage.maximum_filter1d(m, 2 * r + 1, axis=0).astype(bool)


def detect(a):
    H, W = a.shape[:2]
    ink, bg = ink_mask(a)
    r = max(2, round(max(W, H) * 0.003))
    d = box_dilate(ink, r)
    lab, n = ndimage.label(d, structure=np.ones((3, 3)))
    objs = ndimage.find_objects(lab)
    boxes = []
    for sl in objs:
        y0, y1 = sl[0].start, sl[0].stop
        x0, x1 = sl[1].start, sl[1].stop
        boxes.append([x0 + r, y0 + r, x1 - r, y1 - r])
    # fusionar cajas que se solapan (marcos con huecos)
    changed = True
    while changed:
        changed = False
        out = []
        for b in boxes:
            for o in out:
                if b[0] < o[2] and o[0] < b[2] and b[1] < o[3] and o[1] < b[3]:
                    o[:] = [min(o[0], b[0]), min(o[1], b[1]), max(o[2], b[2]), max(o[3], b[3])]
                    changed = True
                    break
            else:
                out.append(list(b))
        boxes = out
    cards = []
    for x0, y0, x1, y1 in boxes:
        w, h = x1 - x0, y1 - y0
        if w * h < W * H * 0.008:
            continue
        ar = min(w, h) / max(w, h)
        if not 0.5 < ar < 0.85:
            continue
        cards.append((x0, y0, x1, y1))
    return cards


def signature(a, box, turn):
    """turn: 0, 1, 2, 3 cuartos de vuelta para dejar la carta en retrato."""
    x0, y0, x1, y1 = box
    crop = Image.fromarray(a[y0:y1, x0:x1].astype(np.uint8))
    crop = crop.rotate(90 * turn, expand=True)
    crop = crop.resize((GW, GH), Image.BOX)
    v = np.asarray(crop).astype(np.float32).reshape(-1)
    v = v - v.mean()
    return v / (np.linalg.norm(v) + 1e-6)


def reading_order(cards):
    cards = sorted(cards, key=lambda c: (c[1] + c[3]) / 2)
    hs = np.mean([c[3] - c[1] for c in cards]) if cards else 1
    rows = []
    for c in cards:
        cy = (c[1] + c[3]) / 2
        for row in rows:
            if abs(row[0] - cy) < hs * 0.5:
                row[1].append(c)
                break
        else:
            rows.append([cy, [c]])
    return [c for _, row in rows for c in sorted(row, key=lambda c: c[0])]


def draw(a, cards, path, labels=None):
    im = Image.fromarray(a.astype(np.uint8))
    dr = ImageDraw.Draw(im)
    for i, c in enumerate(cards):
        dr.rectangle(c, outline=(255, 0, 0), width=3)
        dr.text((c[0] + 4, c[1] + 4), labels[i] if labels else str(i + 1), fill=(255, 0, 0))
    im.save(path)


def detect_paper(a, delta=10, erode_frac=0.004):
    """Cartas = zonas más claras que la mesa, rellenando los dibujos de dentro."""
    H, W = a.shape[:2]
    gray = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    mx, mn = a.max(-1), a.min(-1)
    sat = np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)
    bg = np.median(gray)
    paper = (gray > bg + delta) & (sat < 0.25)
    filled = ndimage.binary_fill_holes(paper)
    r = max(1, round(max(W, H) * erode_frac))
    er = ~box_dilate(~filled, r)          # erosión = dilatar el complemento
    lab, n = ndimage.label(er)
    cards = []
    for sl in ndimage.find_objects(lab):
        x0, x1, y0, y1 = sl[1].start - r, sl[1].stop + r, sl[0].start - r, sl[0].stop + r
        w, h = x1 - x0, y1 - y0
        if w * h < W * H * 0.01: continue
        ar = min(w, h) / max(w, h)
        if not 0.5 < ar < 0.85: continue
        cards.append((max(0, x0), max(0, y0), min(W, x1), min(H, y1)))
    return cards, bg


def adaptive_ink(a, block=25, C=15):
    """Igual que cv2.adaptiveThreshold MEAN_C INV: más oscuro que la media local - C."""
    gray = np.round(0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2])
    mean = ndimage.uniform_filter(gray, size=block, mode='nearest')
    return gray < mean - C


def detect_lines(a, block=25, C=15):
    H, W = a.shape[:2]
    th = adaptive_ink(a, block, C)
    lab, n = ndimage.label(th, structure=np.ones((3, 3)))
    boxes = []
    for sl in ndimage.find_objects(lab):
        x0, x1, y0, y1 = sl[1].start, sl[1].stop, sl[0].start, sl[0].stop
        w, h = x1 - x0, y1 - y0
        if w * h < 0.012 * W * H or w * h > 0.2 * W * H: continue
        if not 0.5 < min(w, h) / max(w, h) < 0.85: continue
        boxes.append((x0, y0, x1, y1))
    keep = []
    for b in sorted(boxes, key=lambda b: -(b[2] - b[0]) * (b[3] - b[1])):
        cx, cy = (b[0] + b[2]) / 2, (b[1] + b[3]) / 2
        if any(k[0] < cx < k[2] and k[1] < cy < k[3] for k in keep): continue
        keep.append(b)
    return keep


def detect_cards(a, block_frac=0.018, rel=0.04):
    """Devuelve cartas como rectángulos girados: centro, eje largo (hacia abajo), largo y ancho."""
    H, W = a.shape[:2]
    gray = 0.299 * a[..., 0] + 0.587 * a[..., 1] + 0.114 * a[..., 2]
    block = max(9, int(max(W, H) * block_frac) | 1)
    mean = ndimage.uniform_filter(gray, size=block, mode='nearest')
    th = gray < mean - np.maximum(8, rel * mean)
    lab, n = ndimage.label(th, structure=np.ones((3, 3)))
    objs = ndimage.find_objects(lab)
    cards = []
    for idx, sl in enumerate(objs, start=1):
        w, h = sl[1].stop - sl[1].start, sl[0].stop - sl[0].start
        if w * h < 0.010 * W * H or w * h > 0.25 * W * H: continue
        ys, xs = np.nonzero(lab[sl] == idx)
        xs = xs + sl[1].start; ys = ys + sl[0].start
        if not 0.4 < min(w, h) / max(w, h) < 0.95: continue
        # rectángulo de área mínima probando giros de -20° a 20° (cartas casi rectas, de pie o tumbadas)
        best = None
        for deg in np.arange(-20, 20.5, 1.0):
            t = np.deg2rad(deg); ca, sa = np.cos(t), np.sin(t)
            px = xs * ca + ys * sa; py = -xs * sa + ys * ca
            area = (px.max() - px.min()) * (py.max() - py.min())
            if best is None or area < best[0]: best = (area, t, px, py)
        _, t, px, py = best
        ex = np.array([np.cos(t), np.sin(t)]); ey = np.array([-np.sin(t), np.cos(t)])
        wx, wy = px.max() - px.min(), py.max() - py.min()
        mx, my = (px.max() + px.min()) / 2, (py.max() + py.min()) / 2
        ccx, ccy = mx * ex[0] + my * ey[0], mx * ex[1] + my * ey[1]
        if wy >= wx: down, right, L, S = ey, ex, wy, wx
        else:
            down = ex if ex[1] >= 0 else -ex
            right = np.array([down[1], -down[0]]); L, S = wx, wy
        if not 0.55 < S / L < 0.8: continue
        cards.append(dict(c=(ccx, ccy), down=down, right=right, L=L, S=S,
                          box=(xs.min(), ys.min(), xs.max(), ys.max())))
    keep = []
    for cd in sorted(cards, key=lambda d: -d['L'] * d['S']):
        cx, cy = cd['c']
        if any(k['box'][0] < cx < k['box'][2] and k['box'][1] < cy < k['box'][3] for k in keep): continue
        keep.append(cd)
    return keep


def sig_rot(a, cd, flip):
    """Firma muestreando la carta en su propio giro. flip=True: carta del revés."""
    H, W = a.shape[:2]
    down = -cd['down'] if flip else cd['down']
    right = np.array([down[1], -down[0]])
    cx, cy = cd['c']
    u = (np.arange(GW * 3) + 0.5) / (GW * 3) - 0.5
    v = (np.arange(GH * 3) + 0.5) / (GH * 3) - 0.5
    U, V = np.meshgrid(u * cd['S'] * 0.96, v * cd['L'] * 0.96)
    X = np.clip(np.round(cx + U * right[0] + V * down[0]).astype(int), 0, W - 1)
    Y = np.clip(np.round(cy + U * right[1] + V * down[1]).astype(int), 0, H - 1)
    s = a[Y, X].reshape(GH, 3, GW, 3, 3).mean(axis=(1, 3)).reshape(-1)
    s = s - s.mean()
    return s / (np.linalg.norm(s) + 1e-6)


def order_cards(cards):
    boxes = [tuple(cd['box']) for cd in cards]
    ordered = reading_order(boxes)
    return [cards[boxes.index(b)] for b in ordered]


def classify_j(a, cd, M, K, jit=0.025):
    """Prueba pequeños desplazamientos y escalas del recorte y se queda con el mejor parecido."""
    best = (-2.0, None)
    for flip in (False, True):
        for dx in (-jit, 0, jit):
            for dy in (-jit, 0, jit):
                for sc in (0.97, 1.0, 1.03):
                    c2 = dict(cd)
                    c2['c'] = (cd['c'][0] + dx * cd['S'] * cd['right'][0] + dy * cd['L'] * cd['down'][0],
                               cd['c'][1] + dx * cd['S'] * cd['right'][1] + dy * cd['L'] * cd['down'][1])
                    c2['S'] = cd['S'] * sc; c2['L'] = cd['L'] * sc
                    s = M @ sig_rot(a, c2, flip); i = int(s.argmax())
                    if s[i] > best[0]: best = (float(s[i]), K[i])
    return best


def scores_j(a, cd, M, jit=0.025):
    """Parecido con cada una de las 40 referencias (el mejor entre giros y pequeños desplazamientos)."""
    best = np.full(M.shape[0], -2.0)
    for flip in (False, True):
        for dx in (-jit, 0, jit):
            for dy in (-jit, 0, jit):
                for sc in (0.97, 1.0, 1.03):
                    c2 = dict(cd)
                    c2['c'] = (cd['c'][0] + dx * cd['S'] * cd['right'][0] + dy * cd['L'] * cd['down'][0],
                               cd['c'][1] + dx * cd['S'] * cd['right'][1] + dy * cd['L'] * cd['down'][1])
                    c2['S'] = cd['S'] * sc; c2['L'] = cd['L'] * sc
                    best = np.maximum(best, M @ sig_rot(a, c2, flip))
    return best


def assign_unique(S, K, minimo=0.45):
    """Una sola baraja: cada referencia se asigna a una carta como mucho, empezando por los parecidos más altos."""
    S = S.copy(); res = [None] * S.shape[0]
    while True:
        i, j = np.unravel_index(np.argmax(S), S.shape)
        if S[i, j] < minimo: break
        res[i] = (K[j], float(S[i, j])); S[i, :] = -9; S[:, j] = -9
    return res
