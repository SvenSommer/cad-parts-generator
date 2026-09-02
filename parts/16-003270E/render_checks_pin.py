"""Kontrollblatt und Produktbild für Raststift und Federscheibe.

  .venv/bin/python parts/16-003270E/render_checks_pin.py

Erzeugt neben den STEP-Dateien:
  CONEC_16-003270E_Raststift_4-40_dreiseitenansicht.png   Tafeln + Sollmaße
  CONEC_16-003270E_Raststift_4-40_render.png              Stift und Federscheibe,
                                                          vernickelt, wie im Datenblatt
Nutzt den Blender-Renderer der Schraubteile (screws/blender_views.py).
"""
import shutil
import sys
import tempfile
from pathlib import Path

import cadquery as cq
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(HERE.parent.parent / 'screws'))
from create_detent_pin_step import (COLLAR_D, COLLAR_L, DOME_D, DOME_H, DOME_TOP_D,  # noqa: E402
                                    HEX_AF, HEX_CH_BOT, HEX_CH_TOP, HEX_H, NECK_D,
                                    NECK_L, PIN_NAME, THREAD_L, WASHER_ID,
                                    WASHER_OD, WASHER_RISE, WASHER_T, build_pin,
                                    build_washer)
from render_checks import INK, MUTED, RULE, auf_weiss, font, render, umbrechen  # noqa: E402

PAD, GAP, HEADER, LABEL = 26, 18, 100, 32
# Achse = z, Kopf bei negativem z; Bild-rechts ist -z, der Kopf liegt also
# rechts wie in der Datenblatt-Zeichnung der Schraubteile.
VIEWS = [dict(name='front', dir=[-1, 0, 0], up=[0, 1, 0]),
         dict(name='top', dir=[0, -1, 0], up=[-1, 0, 0]),
         dict(name='right', dir=[0, 0, 1], up=[0, 1, 0])]
ISO = dict(name='iso', dir=[0.55, 0.62, 0.56], up=[0, 1, 0], pad=1.10)
# Kamera auf der Kopfseite (−z), Kopf oben im Bild, Federscheibe unten
PRODUKT = dict(name='produkt', dir=[0.45, 0.55, 0.70], up=[0, 0, -1], pad=1.10)
TITEL = {'front': 'Vorderansicht', 'top': 'Draufsicht', 'right': 'Ansicht auf die Kuppe',
         'iso': 'Dreiviertelansicht'}


def mm(x):
    return f'{x:.2f}'.rstrip('0').rstrip('.').replace('.', ',')


def masse():
    return [
        ('Gesamtlänge', f'{mm(HEX_H + COLLAR_L + NECK_L + DOME_H + THREAD_L)} mm '
                        f'({mm(THREAD_L)} Gewinde + {mm(HEX_H)} Sechskant + '
                        f'{mm(COLLAR_L + NECK_L + DOME_H)} Kopf)'),
        ('Gewinde', f'4-40 UNC-2A, Ø 2,85, {mm(THREAD_L)} lang, Anschnitt C 0,3'),
        ('Sechskant', f'SW {mm(HEX_AF)}, {mm(HEX_H)} hoch, abgedrehte Fase C {mm(HEX_CH_BOT)} '
                      f'unten / C {mm(HEX_CH_TOP)} oben'),
        ('Bund', f'Ø {mm(COLLAR_D)} × {mm(COLLAR_L)}'),
        ('Hals', f'Ø {mm(NECK_D)} × {mm(NECK_L)} — hier sitzt die Gabel des Clips'),
        ('Kuppe', f'Ø {mm(DOME_D)}, {mm(DOME_H)} hoch, oben Fläche Ø {mm(DOME_TOP_D)} mit Körnermarke'),
        ('Federscheibe', f'Sprengring Nr. 4: Ø {mm(WASHER_ID)} / {mm(WASHER_OD)}, Dicke {mm(WASHER_T)}, '
                         f'Enden um {mm(WASHER_RISE)} versetzt'),
        ('Bezugssystem', 'z = 0 an der Anlagefläche des Sechskants, +z zur Gewindespitze; '
                         'Federscheibe im selben System bei z = 0 … 1,2'),
        ('Quelle', 'Sechskant/Gewinde Normmaße; Bund, Hals, Kuppe aus der 3D-Ansicht des '
                   'CONEC-Datenblatts und dem Prototypfoto, ±0,2 mm'),
    ]


def blatt(pngs, out):
    tiles = {k: auf_weiss(p) for k, p in pngs.items()}
    tw, th = next(iter(tiles.values())).size
    sheet_w = PAD * 2 + tw * 3 + GAP * 2
    sheet_h = HEADER + (th + LABEL) * 2 + PAD
    im = Image.new('RGB', (sheet_w, sheet_h), 'white')
    d = ImageDraw.Draw(im)
    d.text((PAD, 24), 'CONEC 16-003270E — Raststift 4-40 UNC', font=font(34, bold=True), fill=INK)
    d.text((PAD, 66), 'SnapLock-Raststift aus dem Haubensatz. Alle Ansichten orthografisch und '
                      'maßstabsgleich, erste Winkelprojektion. Maße in mm.', font=font(18), fill=MUTED)
    d.line([(PAD, HEADER - 6), (sheet_w - PAD, HEADER - 6)], fill=RULE, width=1)

    def zelle(col, row):
        return PAD + col * (tw + GAP), HEADER + row * (th + LABEL)

    for view, col, row in (('right', 0, 0), ('front', 1, 0), ('iso', 2, 0), ('top', 1, 1)):
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
    pin, washer = build_pin(), build_washer()
    with tempfile.TemporaryDirectory() as tmp:
        stl = Path(tmp) / f'{PIN_NAME}.stl'
        cq.exporters.export(cq.Workplane(obj=pin), str(stl), tolerance=0.003, angularTolerance=0.05)
        span = (HEX_H + COLLAR_L + NECK_L + DOME_H + THREAD_L) * 1.08
        views = [dict(v, span_mm=span) for v in VIEWS] + [ISO]
        pngs = render(stl, tmp, PIN_NAME, 'cad', views, [900, 640])
        print('Wrote', blatt(pngs, HERE / f'{PIN_NAME}_dreiseitenansicht.png'))

        # Produktbild: Stift mit Federscheibe unter der Gewindespitze, wie im Datenblatt
        expl = cq.Compound.makeCompound([pin, washer.translate(cq.Vector(0, 0, THREAD_L + 2.0))])
        stl2 = Path(tmp) / f'{PIN_NAME}_set.stl'
        cq.exporters.export(cq.Workplane(obj=expl), str(stl2), tolerance=0.003, angularTolerance=0.05)
        png = render(stl2, tmp, PIN_NAME + '_set', 'metal', [PRODUKT], [1400, 1050])
        out = HERE / f'{PIN_NAME}_render.png'
        shutil.copy(png['produkt'], out)
        print('Wrote', out)


if __name__ == '__main__':
    main()
