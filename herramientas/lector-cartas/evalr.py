from proto import *
from build_refs import ORDER, SUIT
from PIL import ImageFilter
import json, itertools
M = np.load('salida/refs.npy'); K = json.load(open('salida/keys.json'))
def classify(a, box):
    w, h = box[2]-box[0], box[3]-box[1]
    turns = (0, 2) if h >= w else (1, 3)
    best = (-2, None, 0)
    for t in turns:
        s = M @ signature(a, box, t)
        i = int(s.argmax()); srt = np.sort(s)
        if s[i] > best[0]: best = (float(s[i]), K[i], float(s[i]-srt[-2]))
    return best
def load_t(path, rot, bright, scale, blur):
    im = Image.open(path).convert('RGB')
    if scale != 1: im = im.resize((int(im.width*scale), int(im.height*scale)), Image.BILINEAR)
    if blur: im = im.filter(ImageFilter.GaussianBlur(blur))
    if rot: im = im.rotate(rot, resample=Image.BILINEAR, expand=True, fillcolor=tuple(int(v) for v in np.median(np.asarray(im).reshape(-1,3),0)))
    s = WORK / max(im.size); im = im.resize((round(im.width*s), round(im.height*s)), Image.BILINEAR)
    return np.clip(np.asarray(im).astype(np.float32)*bright, 0, 255)
tot = ok = found = 0; margins = []; errs = []
for rot, bright, scale, blur in itertools.product([-4, 0, 4], [0.8, 1.0, 1.2], [1.0, 0.4], [0, 1.5]):
    for s, labels in ORDER.items():
        a = load_t(f'fotos-baraja/{s}.png', rot, bright, scale, blur)
        cs = reading_order(detect_lines(a)); tot += 10; found += min(len(cs), 10)
        if len(cs) != 10: errs.append((s, rot, bright, scale, blur, 'detectadas', len(cs))); continue
        for lab, box in zip(labels, cs):
            sc, k, mg = classify(a, box); margins.append(mg)
            if k == lab+SUIT[s]: ok += 1
            else: errs.append((s, rot, bright, scale, blur, lab+SUIT[s], k, round(sc,3)))
print(f'detectadas {found}/{tot}  acertadas {ok}/{tot}  margen mínimo {min(margins):.3f}')
for e in errs[:15]: print(e)
