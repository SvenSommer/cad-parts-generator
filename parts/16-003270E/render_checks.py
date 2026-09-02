"""Kontrollblatt des SnapLock-Clips: drei Ansichten, Dreiviertelansicht, Maße.

  .venv/bin/python parts/16-003270E/render_checks.py

Nutzt den Blender-Renderer der Schraubteile (screws/blender_views.py, Stil
"cad"). Alle Tafeln orthografisch und maßstabsgleich.
"""
import sys
import tempfile
from pathlib import Path

import cadquery as cq
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / 'screws'))
from create_snaplock_clip_step import (NAME, SLOT_R, SLOT_W, SLOT_Z0, SLOT_Z1,  # noqa: E402
                                       T, TONGUE, TONGUE_W, W, W_TAB, Z_TAB,
                                       Z_TOP, build)
from render_checks import INK, MUTED, RULE, auf_weiss, font, render, umbrechen  # noqa: E402

PAD, GAP, HEADER, LABEL = 26, 18, 100, 32
# Bezugssystem: +x nach außen (Haubenwand), +z Steckrichtung, y quer.
# "front" blickt von außen auf den Clip (wie die Seitenansicht der Haube),
# "side" zeigt das Profil mit dem Außenschenkel rechts (wie der Schnitt in
# der Haubenzeichnung), "top" von oben (+z), also aus dem Haubeninneren.
VIEWS = [dict(name='side', dir=[0, 1, 0], up=[0, 0, 1]),
         dict(name='front', dir=[-1, 0, 0], up=[0, 0, 1]),
         dict(name='top', dir=[0, 0, -1], up=[-1, 0, 0])]
ISO = dict(name='iso', dir=[-0.62, 0.50, -0.60], up=[0, 0, 1], pad=1.12)
TITEL = {'side': 'Profil (Blick quer, außen rechts)', 'front': 'Ansicht von außen',
         'top': 'Draufsicht (aus der Haube)', 'iso': 'Dreiviertelansicht'}


def mm(x):
    return f'{x:.2f}'.rstrip('0').rstrip('.').replace('.', ',')


def masse():
    return [
        ('Blech', f'{mm(T)} mm Edelstahl, Biegeradius innen 0,2'),
        ('Größe', f'{mm(W)} breit, {mm(Z_TOP)} hoch (z), 6,15 tief (x, Gabelende bis Außenfläche)'),
        ('Außenschenkel', f'Unterkante z = {mm(Z_TAB)}, Ecken R 0,9, um 1,8° geneigt; '
                          f'darunter Lappen {mm(W_TAB)} breit'),
        ('Gabelfuß', 'waagerecht bis x = −1,3 (über die Stiftachse hinaus), Schlitz 2,5 breit, '
                     'nach innen offen, geschlossen bei x = 3,4; sitzt im Hals des Raststifts (Ø 2,6)'),
        ('Fenster', f'{mm(SLOT_W)} breit, z = {mm(SLOT_Z0)} … {mm(SLOT_Z1)}, Ecken R {mm(SLOT_R)}'),
        ('Zunge', f'{mm(TONGUE_W)} breit, Spitze z = {mm(TONGUE[-1][1])}, ab z = {mm(TONGUE[1][1])} '
                  f'um 4,8° nach innen, Spitzenecken R 0,3'),
        ('Kröpfung', '1,56 nach innen unter 45°, z = 10,3 … 11,8; Oberteil bei x = 2,47 … 2,97'),
        ('Bezugssystem', 'Ursprung auf der Raststift-Achse, z = 0 Fußunterseite, '
                         '+z Steckrichtung, +x nach außen; Stifthals bei z ≈ 0 … 0,4, Kuppe darüber'),
        ('Quelle', 'Abgegriffen aus CONEC-Zeichnung 16K1A4424 (25 px/mm), ±0,1 mm; '
                   'Fensteroberkante und Schlitzbreite angenommen'),
    ]


def blatt(pngs, out):
    tiles = {k: auf_weiss(p) for k, p in pngs.items()}
    tw, th = next(iter(tiles.values())).size
    sheet_w = PAD * 2 + tw * 3 + GAP * 2
    sheet_h = HEADER + (th + LABEL) * 2 + PAD
    im = Image.new('RGB', (sheet_w, sheet_h), 'white')
    d = ImageDraw.Draw(im)
    d.text((PAD, 24), 'CONEC 16-003270E — SnapLock-Clip', font=font(34, bold=True), fill=INK)
    d.text((PAD, 66), 'Federclip aus dem Haubensatz, nachmodelliert aus der Haubenzeichnung. '
                      'Alle Ansichten orthografisch und maßstabsgleich. Maße in mm.',
           font=font(18), fill=MUTED)
    d.line([(PAD, HEADER - 6), (sheet_w - PAD, HEADER - 6)], fill=RULE, width=1)

    def zelle(col, row):
        return PAD + col * (tw + GAP), HEADER + row * (th + LABEL)

    for view, col, row in (('side', 0, 0), ('front', 1, 0), ('iso', 2, 0), ('top', 1, 1)):
        x, y = zelle(col, row)
        im.paste(tiles[view], (x, y))
        d.rectangle([x, y, x + tw - 1, y + th - 1], outline=RULE)
        d.text((x + 4, y + th + 7), TITEL[view], font=font(19, bold=True), fill=INK)

    x, y = zelle(2, 1)
    y += 18
    f_label, f_val = font(17, bold=True), font(19)
    for label, value in masse():
        d.text((x + 6, y), label.upper(), font=f_label, fill=MUTED)
        y += 24
        for zeile in umbrechen(value, f_val, tw - 24, d):
            d.text((x + 6, y), zeile, font=f_val, fill=INK)
            y += 25
        y += 8
    im.convert('P', palette=Image.ADAPTIVE, colors=200).save(out, optimize=True)
    return out


def main():
    body = build()
    with tempfile.TemporaryDirectory() as tmp:
        stl = Path(tmp) / f'{NAME}.stl'
        cq.exporters.export(cq.Workplane(obj=body), str(stl), tolerance=0.003,
                            angularTolerance=0.05)
        span = Z_TOP * 1.12
        views = [dict(v, span_mm=span) for v in VIEWS] + [ISO]
        pngs = render(stl, tmp, NAME, 'cad', views, [900, 640])
        out = blatt(pngs, HERE / f'{NAME}_dreiseitenansicht.png')
        print(f'Wrote {out}')


if __name__ == '__main__':
    main()
