/* ---------- lector con vuestra baraja: compara cada carta con las 40 referencias ---------- */
const DECK = __DECK__;
let DECK_REFS = null;
function deckRefs(){
  if(DECK_REFS) return DECK_REFS;
  const bin = atob(DECK.b64), n = DECK.keys.length, d = DECK.gw * DECK.gh * 3, M = new Float32Array(n * d);
  for(let i = 0; i < n; i++){
    let norm = 0;
    for(let k = 0; k < d; k++){ let v = bin.charCodeAt(i*d + k); if(v > 127) v -= 256; v *= DECK.scales[i]; M[i*d + k] = v; norm += v*v; }
    norm = Math.sqrt(norm) || 1; for(let k = 0; k < d; k++) M[i*d + k] /= norm;
  }
  return DECK_REFS = {M, n, d};
}
// 1) Encontrar las cartas: líneas más oscuras que su entorno (borde de la carta y su marco impreso)
function deckDetect(img){
  const s = 1400 / Math.max(img.naturalWidth, img.naturalHeight);
  const W = Math.max(1, Math.round(img.naturalWidth * s)), H = Math.max(1, Math.round(img.naturalHeight * s)), N = W * H;
  const cv = document.createElement('canvas'); cv.width = W; cv.height = H;
  const ctx = cv.getContext('2d', {willReadFrequently: true}); ctx.drawImage(img, 0, 0, W, H);
  const data = ctx.getImageData(0, 0, W, H).data;
  const gray = new Float32Array(N);
  for(let i = 0, j = 0; i < N; i++, j += 4) gray[i] = 0.299*data[j] + 0.587*data[j+1] + 0.114*data[j+2];
  // media local con imagen integral
  const I = new Float64Array((W+1) * (H+1));
  for(let y = 0; y < H; y++){ let row = 0; for(let x = 0; x < W; x++){ row += gray[y*W + x]; I[(y+1)*(W+1) + x+1] = I[y*(W+1) + x+1] + row; } }
  const half = Math.max(9, Math.floor(Math.max(W, H) * 0.018) | 1) >> 1;
  const th = new Uint8Array(N);
  for(let y = 0; y < H; y++){
    const y0 = Math.max(0, y-half), y1 = Math.min(H, y+half+1);
    for(let x = 0; x < W; x++){
      const x0 = Math.max(0, x-half), x1 = Math.min(W, x+half+1);
      const mean = (I[y1*(W+1)+x1] - I[y0*(W+1)+x1] - I[y1*(W+1)+x0] + I[y0*(W+1)+x0]) / ((y1-y0)*(x1-x0));
      if(gray[y*W + x] < mean - Math.max(8, 0.04*mean)) th[y*W + x] = 1;
    }
  }
  // componentes conexas (8 vecinos)
  const lab = new Int32Array(N), stack = new Int32Array(N), comps = [];
  for(let p = 0; p < N; p++){
    if(!th[p] || lab[p]) continue;
    const id = comps.length + 1, c = {id, minx:W, maxx:0, miny:H, maxy:0, n:0};
    let sp = 0; stack[sp++] = p; lab[p] = id;
    while(sp){
      const q = stack[--sp], qx = q % W, qy = (q - qx) / W; c.n++;
      if(qx<c.minx)c.minx=qx; if(qx>c.maxx)c.maxx=qx; if(qy<c.miny)c.miny=qy; if(qy>c.maxy)c.maxy=qy;
      for(let dy = -1; dy <= 1; dy++) for(let dx = -1; dx <= 1; dx++){
        const nx = qx+dx, ny = qy+dy; if(nx<0||ny<0||nx>=W||ny>=H) continue;
        const r = ny*W + nx; if(th[r] && !lab[r]){ lab[r] = id; stack[sp++] = r; }
      }
    }
    comps.push(c);
  }
  let cards = [];
  for(const c of comps){
    const w = c.maxx-c.minx+1, h = c.maxy-c.miny+1;
    if(w*h < 0.010*N || w*h > 0.25*N) continue;
    if(Math.min(w,h)/Math.max(w,h) < 0.4 || Math.min(w,h)/Math.max(w,h) > 0.95) continue;
    // puntos de la componente (como mucho unos 6000)
    const step = Math.max(1, Math.round(Math.sqrt(c.n / 6000)));
    const xs = [], ys = [];
    for(let y = c.miny; y <= c.maxy; y += step) for(let x = c.minx; x <= c.maxx; x += step) if(lab[y*W + x] === c.id){ xs.push(x); ys.push(y); }
    // rectángulo de área mínima girando de -20° a 20°
    let best = null;
    for(let deg = -20; deg <= 20; deg += 1){
      const t = deg*Math.PI/180, ca = Math.cos(t), sa = Math.sin(t);
      let a0 = Infinity, a1 = -Infinity, b0 = Infinity, b1 = -Infinity;
      for(let k = 0; k < xs.length; k++){ const px = xs[k]*ca + ys[k]*sa, py = -xs[k]*sa + ys[k]*ca; if(px<a0)a0=px; if(px>a1)a1=px; if(py<b0)b0=py; if(py>b1)b1=py; }
      const area = (a1-a0)*(b1-b0); if(!best || area < best.area) best = {area, t, a0, a1, b0, b1};
    }
    const {t, a0, a1, b0, b1} = best, ex = [Math.cos(t), Math.sin(t)], ey = [-Math.sin(t), Math.cos(t)];
    const wx = a1-a0, wy = b1-b0, mx = (a0+a1)/2, my = (b0+b1)/2;
    const cx = mx*ex[0] + my*ey[0], cy = mx*ex[1] + my*ey[1];
    let down, right, L, S;
    if(wy >= wx){ down = ey; right = ex; L = wy; S = wx; }
    else { down = ex[1] >= 0 ? ex : [-ex[0], -ex[1]]; right = [down[1], -down[0]]; L = wx; S = wy; }
    if(S/L < 0.55 || S/L > 0.8) continue;
    cards.push({cx, cy, down, right, L, S, box:[c.minx, c.miny, c.maxx, c.maxy]});
  }
  const keep = [];
  cards.sort((p, q) => q.L*q.S - p.L*p.S).forEach(cd => {
    if(!keep.some(k => k.box[0] < cd.cx && cd.cx < k.box[2] && k.box[1] < cd.cy && cd.cy < k.box[3])) keep.push(cd);
  });
  return {cards: keep, data, W, H, scale: s};
}
// 2) Firma de una carta: rejilla de colores medida en su propio giro
function deckSig(data, W, H, cd, flip, out){
  const gw = DECK.gw, gh = DECK.gh;
  const down = flip ? [-cd.down[0], -cd.down[1]] : cd.down, right = [down[1], -down[0]];
  out.fill(0);
  for(let gy = 0; gy < gh*3; gy++){
    const v = ((gy + 0.5)/(gh*3) - 0.5) * cd.L * 0.96;
    for(let gx = 0; gx < gw*3; gx++){
      const u = ((gx + 0.5)/(gw*3) - 0.5) * cd.S * 0.96;
      const X = Math.min(W-1, Math.max(0, Math.round(cd.cx + u*right[0] + v*down[0])));
      const Y = Math.min(H-1, Math.max(0, Math.round(cd.cy + u*right[1] + v*down[1])));
      const p = (Y*W + X) * 4, o = ((gy/3|0)*gw + (gx/3|0)) * 3;
      out[o] += data[p]; out[o+1] += data[p+1]; out[o+2] += data[p+2];
    }
  }
  let mean = 0; for(let k = 0; k < out.length; k++) mean += out[k]; mean /= out.length;
  let norm = 0; for(let k = 0; k < out.length; k++){ out[k] -= mean; norm += out[k]*out[k]; }
  norm = Math.sqrt(norm) || 1; for(let k = 0; k < out.length; k++) out[k] /= norm;
  return out;
}
// 3) Parecido con las 40 referencias, probando pequeños desplazamientos y la carta del revés
function deckScores(det, cd){
  const {M, n, d} = deckRefs(), best = new Float32Array(n).fill(-2), sig = new Float32Array(d), J = 0.025;
  for(const flip of [false, true]) for(const dx of [-J, 0, J]) for(const dy of [-J, 0, J]) for(const sc of [0.97, 1, 1.03]){
    const c2 = {cx: cd.cx + dx*cd.S*cd.right[0] + dy*cd.L*cd.down[0], cy: cd.cy + dx*cd.S*cd.right[1] + dy*cd.L*cd.down[1],
                down: cd.down, right: cd.right, L: cd.L*sc, S: cd.S*sc};
    deckSig(det.data, det.W, det.H, c2, flip, sig);
    for(let i = 0; i < n; i++){ let dot = 0; const o = i*d; for(let k = 0; k < d; k++) dot += M[o+k]*sig[k]; if(dot > best[i]) best[i] = dot; }
  }
  return best;
}
// 4) Una sola baraja: cada carta de referencia se asigna como mucho una vez, empezando por el parecido más alto
function deckAssign(rows, minimo){
  const n = DECK.keys.length, res = rows.map(() => null), usedR = new Set(), usedK = new Set();
  const pairs = [];
  rows.forEach((r, i) => { for(let k = 0; k < n; k++) if(r[k] >= minimo) pairs.push([r[k], i, k]); });
  pairs.sort((a, b) => b[0] - a[0]);
  for(const [sc, i, k] of pairs){ if(usedR.has(i) || usedK.has(k)) continue; res[i] = {key: DECK.keys[k], score: sc}; usedR.add(i); usedK.add(k); }
  return res;
}
function deckRead(img){
  const det = deckDetect(img);
  const rows = det.cards.map(cd => deckScores(det, cd));
  const asg = deckAssign(rows, 0.55);
  let cards = det.cards.map((cd, i) => ({cd, a: asg[i]})).filter(x => x.a);
  // orden de lectura: filas de arriba abajo, cada fila de izquierda a derecha
  const hs = cards.reduce((m, x) => m + (x.cd.box[3]-x.cd.box[1]), 0) / (cards.length || 1);
  cards.sort((p, q) => p.cd.cy - q.cd.cy);
  const filas = [];
  cards.forEach(x => { const f = filas.find(r => Math.abs(r.cy - x.cd.cy) < hs*0.5); if(f) f.items.push(x); else filas.push({cy: x.cd.cy, items: [x]}); });
  cards = filas.flatMap(f => f.items.sort((p, q) => p.cd.cx - q.cd.cx));
  return cards.map(x => ({key: x.a.key, score: x.a.score, box: x.cd.box.map(v => v / det.scale)}));
}
