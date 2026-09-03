"""Drei-Seiten-Ansicht aus dem Zeichnungs-PDF ausschneiden, wie Roberts bisherige Exporte.

  .venv/bin/python parts/16-003270E/crop_drawing.py <zeichnung.pdf> <out.png> [dpi]

Rendert das PDF, entfernt Blattrahmen und Schriftfeld (Rahmen = äußerste
lange Linien, Schriftfeld = Block unten rechts) und schneidet auf den
Inhalt zu; Weiß wird transparent (RGBA wie die anderen 3-Seitenansichten).
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
from PIL import Image

pdf, out = sys.argv[1], sys.argv[2]
dpi = int(sys.argv[3]) if len(sys.argv) > 3 else 400
with tempfile.TemporaryDirectory() as tmp:
    subprocess.run(['pdftoppm', '-r', str(dpi), '-png', '-singlefile', pdf, f'{tmp}/p'], check=True)
    im = Image.open(f'{tmp}/p.png').convert('L')
a = np.array(im)
h, w = a.shape
dark = a < 200
# Blattrahmen: Zeilen/Spalten, die zu > 60 % dunkel sind, sind Rahmenlinien
row_frac = dark.mean(axis=1); col_frac = dark.mean(axis=0)
frame_rows = np.where(row_frac > 0.6)[0]; frame_cols = np.where(col_frac > 0.6)[0]
top = frame_rows[frame_rows < h // 2].max() + 3 if (frame_rows < h // 2).any() else 0
bottom = frame_rows[frame_rows > h // 2].min() - 3 if (frame_rows > h // 2).any() else h
left = frame_cols[frame_cols < w // 2].max() + 3 if (frame_cols < w // 2).any() else 0
right = frame_cols[frame_cols > w // 2].min() - 3 if (frame_cols > w // 2).any() else w
inner = dark[top:bottom, left:right].copy()
# Schriftfeld unten rechts: Zeile im unteren Drittel, ab der rechts eine lange Linie liegt
ih, iw = inner.shape
tb_top = None
for y in range(ih * 2 // 3, ih):
    if inner[y, iw // 2:].mean() > 0.5:
        tb_top = y; break
if tb_top is not None:
    # Schriftfeld-Breite: die Oberkante ist ein durchgehender dunkler Lauf bis zum
    # rechten Rand; sein Anfang ist die linke Kante des Schriftfelds
    row = inner[tb_top]
    x = iw - 1
    while x > 0 and row[max(0, x - 3):x + 1].any():
        x -= 1
    tb_left = x
    inner[tb_top - 4:, tb_left - 4:] = False
ys, xs = np.where(inner)
pad = int(dpi * 0.15)
y0, y1 = max(0, ys.min() - pad), min(ih, ys.max() + pad)
x0, x1 = max(0, xs.min() - pad), min(iw, xs.max() + pad)
crop = a[top + y0:top + y1, left + x0:left + x1]
rgba = np.zeros((*crop.shape, 4), dtype=np.uint8)
rgba[..., :3] = crop[..., None]
rgba[..., 3] = (255 - crop).astype(np.uint8)          # Weiß → transparent, Schwarz → deckend
Image.fromarray(rgba, 'RGBA').save(out)
print(f'Wrote {out} {crop.shape[1]}x{crop.shape[0]} (Rahmen {left},{top}-{right},{bottom}; Schriftfeld ab Zeile {tb_top})')
