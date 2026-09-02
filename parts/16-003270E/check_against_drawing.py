"""Modell des SnapLock-Clips über die CONEC-Zeichnung legen.

  .venv/bin/python parts/16-003270E/check_against_drawing.py

Rendert das Datenblatt (16-003270E_1 (1).pdf) mit 600 dpi, schneidet die
Bereiche aus, in denen der Clip zu sehen ist, und zeichnet das Modell
farbig darüber — links der Schnitt (Ansicht ohne Deckel, rechter Clip),
rechts die Seitenansicht (Clip von vorn). Deckt sich das Modell mit den
schwarzen Linien, stimmen die abgegriffenen Maße.

Bezug der Zeichnung (600 dpi, 25,0 px/mm): Raststift-Achse rechts bei
x = 4347, Lippenunterkante y = 4598 (= z_clip -3,30), Haubenmitte der
Seitenansicht x = 756.
"""
import subprocess
import sys
import tempfile
from pathlib import Path

import numpy as np
import trimesh
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_snaplock_clip_step import (FOOT_VARIANT, NAME, RAIL, RAIL_R, T,  # noqa: E402
                                       TONGUE, TONGUE_RAD, TONGUE_W, W,
                                       face_stencil, fork_slot, profile_solid,
                                       tongue_stencil)

HERE = Path(__file__).resolve().parent
PDF = HERE / '16-003270E_1 (1).pdf'
PX, ZOOM = 25.0, 6
X_PIN, Y_LIP, X_SIDE = 4347, 4598, 756
Z_OFF = 3.30                     # z_clip = v_zeichnung - Z_OFF


def mesh_of(solid):
    verts, tris = solid.tessellate(0.003, 0.05)
    return trimesh.Trimesh([(v.x, v.y, v.z) for v in verts], tris, process=False)


def section_lines(mesh, y):
    sec = mesh.section(plane_origin=[0, y, 0], plane_normal=[0, 1, 0])
    if sec is None:
        return []
    return [np.asarray(p)[:, [0, 2]] for p in sec.discrete]   # (x, z)


def outline_mask(mesh, size, to_px):
    """Umriss der Projektion auf yz als Randpixel-Maske."""
    im = Image.new('L', size, 0)
    d = ImageDraw.Draw(im)
    v = mesh.vertices
    for tri in mesh.faces:
        d.polygon([to_px(v[i][1], v[i][2]) for i in tri], fill=255)
    a = np.array(im) > 0
    er = a.copy()
    er[1:, :] &= a[:-1, :]; er[:-1, :] &= a[1:, :]
    er[:, 1:] &= a[:, :-1]; er[:, :-1] &= a[:, 1:]
    return a & ~er


def main():
    with tempfile.TemporaryDirectory() as tmp:
        subprocess.run(['pdftoppm', '-r', '600', '-png', str(PDF), f'{tmp}/p'], check=True)
        page = Image.open(next(Path(tmp).glob('p*.png'))).convert('RGB')

    rails = profile_solid(RAIL, RAIL_R, T, W).intersect(face_stencil())
    if FOOT_VARIANT == 'fork':
        rails = rails.cut(fork_slot())
    tongue = profile_solid(TONGUE, TONGUE_RAD, T, TONGUE_W).intersect(tongue_stencil())
    m_rails, m_tongue = mesh_of(rails), mesh_of(tongue)

    # --- Schnitt (Ansicht ohne Deckel, rechter Clip) ---
    x0, y0 = X_PIN - 80, Y_LIP - int(19 * PX)
    x1, y1 = X_PIN + 135, Y_LIP - int(2.5 * PX)
    sec = page.crop((x0, y0, x1, y1)).resize(((x1 - x0) * ZOOM, (y1 - y0) * ZOOM), Image.LANCZOS)
    d = ImageDraw.Draw(sec)

    def px_sec(x, z):
        return ((X_PIN + x * PX - x0) * ZOOM, (Y_LIP - (z + Z_OFF) * PX - y0) * ZOOM)

    # y = 1,9 trifft Lappen und Gabelarm; y = 0 liegt im Gabelschlitz und
    # zeigt vom Fuß nichts mehr, dafür den Steg oben.
    for mesh, y, col in ((m_rails, 4.30, (0, 90, 255)), (m_rails, 1.90, (255, 120, 0)),
                         (m_rails, 0.0, (255, 0, 0)), (m_tongue, 0.0, (0, 160, 0))):
        for poly in section_lines(mesh, y):
            pts = [px_sec(x, z) for x, z in poly]
            d.line(pts + pts[:1], fill=col, width=3)
    d.text((10, 10), 'blau: Schnitt y = 4,3 (Schenkel)   orange: y = 1,9 (Lappen, Gabelarm)   '
           'rot: y = 0 (Steg)   grün: Zunge y = 0', fill=(0, 0, 0))

    # --- Seitenansicht (Clip von vorn) ---
    x0s, y0s = X_SIDE - 165, Y_LIP - int(19 * PX)
    x1s, y1s = X_SIDE + 165, Y_LIP - int(2.5 * PX)
    side = page.crop((x0s, y0s, x1s, y1s)).resize(((x1s - x0s) * ZOOM, (y1s - y0s) * ZOOM), Image.LANCZOS)
    size = side.size

    def px_side(y, z):
        return ((X_SIDE + y * PX - x0s) * ZOOM, (Y_LIP - (z + Z_OFF) * PX - y0s) * ZOOM)

    arr = np.array(side)
    for mesh, col in ((m_rails, (0, 90, 255)), (m_tongue, (0, 160, 0))):
        edge = outline_mask(mesh, size, px_side)
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                arr[np.roll(np.roll(edge, dy, 0), dx, 1)] = col
    side = Image.fromarray(arr)
    ImageDraw.Draw(side).text((10, 10), 'blau: Schenkel/Fuß von vorn   grün: Zunge',
                              fill=(0, 0, 0))

    h = max(sec.height, side.height)
    out = Image.new('RGB', (sec.width + side.width + 30, h), 'white')
    out.paste(sec, (0, 0)); out.paste(side, (sec.width + 30, 0))
    out = out.resize((out.width // 2, out.height // 2), Image.LANCZOS)
    dest = HERE / f'{NAME}_zeichnungsabgleich.png'
    out.save(dest)
    print(f'Wrote {dest}  {out.size}')


if __name__ == '__main__':
    main()
