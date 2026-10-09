from proto import *
from build_refs import ORDER, SUIT
from evalr import load_t
import json, itertools, collections
M = np.load('salida/refs2.npy'); K = json.load(open('salida/keys2.json'))
def classify(a, cd):
    best = (-2, None, 0)
    for flip in (False, True):
        s = M @ sig_rot(a, cd, flip); i = int(s.argmax()); srt = np.sort(s)
        if s[i] > best[0]: best = (float(s[i]), K[i], float(s[i] - srt[-2]))
    return best
if __name__ == '__main__':
    tot = ok = det = 0; errs = collections.Counter(); margins = []
    for rot, bright, scale, blur in itertools.product([-5, 0, 5, 180], [0.75, 1.0, 1.2], [1.0, 0.35], [0, 1.5]):
        for s, labels in ORDER.items():
            a = load_t(f'fotos-baraja/{s}.png', rot, bright, scale, blur)
            cs = detect_cards(a); tot += 10; det += min(10, len(cs))
            want = collections.Counter(l + SUIT[s] for l in labels)
            got = collections.Counter()
            for cd in cs:
                sc, k, mg = classify(a, cd); got[k] += 1; margins.append(mg)
            ok += sum((want & got).values())
            for k, v in (got - want).items(): errs[(s, k)] += v
    print(f'detectadas {det}/{tot}  bien reconocidas {ok}/{tot}')
    print('confusiones:', errs.most_common(10))
