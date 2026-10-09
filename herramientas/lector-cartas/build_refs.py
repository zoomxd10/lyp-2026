from proto import *
import json
ORDER = {
 'oros':   ['1','2','3','4','5','6','7','10','11','12'],
 'copas':  ['1','2','3','4','5','6','7','10','11','12'],
 'bastos': ['5','1','12','6','2','11','7','3','10','4'],
 'espadas':['5','1','11','6','2','12','7','3','10','4'],
}
TURN = {'oros':0,'copas':0,'bastos':1,'espadas':1}
SUIT = {'oros':'O','copas':'C','bastos':'B','espadas':'E'}
refs = {}
for s, labels in ORDER.items():
    a = load(f'fotos-baraja/{s}.png'); cs = reading_order(detect_lines(a))
    assert len(cs) == 10, s
    draw(a, cs, f'salida/lab_{s}.png', [l+SUIT[s] for l in labels])
    for lab, box in zip(labels, cs):
        refs[lab+SUIT[s]] = signature(a, box, TURN[s])
np.save('salida/refs.npy', np.stack([refs[k] for k in sorted(refs)])); json.dump(sorted(refs), open('salida/keys.json','w'))
# separación entre cartas: parecido con la segunda más parecida
K = sorted(refs); M = np.stack([refs[k] for k in K]); S = M @ M.T; np.fill_diagonal(S, -1)
worst = sorted(((S[i].max(), K[i], K[S[i].argmax()]) for i in range(len(K))), reverse=True)[:6]
print('pares más parecidos:', [(round(a,3),b,c) for a,b,c in worst])
