"""Empaqueta las 40 firmas de referencia (salida/refs2.npy) en referencias.json para la web."""
import numpy as np, json, base64
M = np.load('salida/refs2.npy'); K = json.load(open('salida/keys2.json'))
scales = np.abs(M).max(1) / 127
q = np.round(M / scales[:, None]).astype(np.int8)
data = {'gw': 18, 'gh': 27, 'keys': K, 'scales': [round(float(x), 8) for x in scales], 'b64': base64.b64encode(q.tobytes()).decode()}
open('referencias.json', 'w').write(json.dumps(data))
print('referencias.json listo:', len(K), 'cartas')
