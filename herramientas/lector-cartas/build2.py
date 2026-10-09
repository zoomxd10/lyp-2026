from proto import *
import json
from build_refs import ORDER, SUIT
FLIP = {'oros': False, 'copas': False, 'bastos': None, 'espadas': None}
refs = {}
for s, labels in ORDER.items():
    a = load(f'fotos-baraja/{s}.png'); cs = order_cards(detect_cards(a))
    assert len(cs) == 10, (s, len(cs))
    for lab, cd in zip(labels, cs):
        # tarjetas apaisadas: el eje "down" queda horizontal; la parte de arriba de la carta está a la derecha
        if FLIP[s] is None:
            flip = cd['down'][0] > 0       # down apunta a la derecha → del revés
        else:
            flip = False
        refs[lab + SUIT[s]] = sig_rot(a, cd, flip)
K = sorted(refs); M = np.stack([refs[k] for k in K])
np.save('salida/refs2.npy', M); json.dump(K, open('salida/keys2.json', 'w'))
S = M @ M.T; np.fill_diagonal(S, -1)
print('máximo parecido entre cartas distintas:', round(float(S.max()), 3), K[S.max(1).argmax()])
