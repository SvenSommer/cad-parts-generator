"""Kontrollblatt der Everlight 42-21SYGC: drei Ansichten, Dreiviertelansicht, Maße.

  .venv/bin/python "leds/EVL 42-21SYGC/render_checks_led.py"
"""
import sys
import tempfile
from pathlib import Path

import cadquery as cq
from PIL import Image, ImageDraw

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
sys.path.insert(0, str(ROOT / 'screws'))
sys.path.append(str(HERE))
from create_led_step import (BODY_L, L, LENS_CYL, LENS_D, LENS_R, NAME, T_BASE,  # noqa: E402
                             T_BODY, W, build)
from render_checks import INK, MUTED, RULE, auf_weiss, font, render, umbrechen  # noqa: E402

PAD, GAP, HEADER, LABEL = 26, 18, 100, 32
VIEWS = [dict(name='front', dir=[0, 1, 0], up=[0, 0, 1]),     # längs, Lötfahnen links/rechts
         dict(name='top', dir=[0, 0, -1], up=[0, 1, 0]),
         dict(name='side', dir=[-1, 0, 0], up=[0, 0, 1])]
ISO = dict(name='iso', dir=[-0.55, 0.62, -0.56], up=[0, 0, 1], pad=1.12)
TITEL = {'front': 'Vorderansicht (längs)', 'top': 'Draufsicht', 'side': 'Seitenansicht', 'iso': 'Dreiviertelansicht'}


def mm(x):
    return f'{x:.2f}'.rstrip('0').rstrip('.').replace('.', ',')


def masse():
    return [
        ('Grundplatte', f'{mm(L)} × {mm(W)} × {mm(T_BASE)}, Lötfahnen an den Stirnseiten'),
        ('Gehäusekörper', f'{mm(BODY_L)} × {mm(W)} × {mm(T_BODY)}, Kathodenmarke als Eckfase'),
        ('Linse', f'Ø {mm(LENS_D)}, Zylinder {mm(LENS_CYL)} + Kuppe R {mm(LENS_R)}; Gesamthöhe '
                  f'{mm(T_BASE + T_BODY + LENS_CYL + LENS_R)}'),
        ('Bezugssystem', 'Ursprung in der Linsenachse auf der Lötebene, +z zur Linsenspitze, x längs'),
        ('Quelle', 'Everlight-Datenblatt 42-21SYGC/S530-E2/TR8, Package Outline Dimensions, ±0,1 mm'),
    ]


def blatt(pngs, out):
    tiles = {k: auf_weiss(p) for k, p in pngs.items()}
    tw, th = next(iter(tiles.values())).size
    im = Image.new('RGB', (PAD * 2 + tw * 3 + GAP * 2, HEADER + (th + LABEL) * 2 + PAD), 'white')
    d = ImageDraw.Draw(im)
    d.text((PAD, 24), 'Everlight 42-21SYGC — 1,8-mm-Rund-SMD-LED', font=font(34, bold=True), fill=INK)
    d.text((PAD, 66), 'Funktions-LED des SD-AC1-DS. Alle Ansichten orthografisch und maßstabsgleich. Maße in mm.',
           font=font(18), fill=MUTED)
    d.line([(PAD, HEADER - 6), (im.width - PAD, HEADER - 6)], fill=RULE, width=1)

    def zelle(col, row):
        return PAD + col * (tw + GAP), HEADER + row * (th + LABEL)
    for view, col, row in (('side', 0, 0), ('front', 1, 0), ('iso', 2, 0), ('top', 1, 1)):
        x, y = zelle(col, row)
        im.paste(tiles[view], (x, y))
        d.rectangle([x, y, x + tw - 1, y + th - 1], outline=RULE)
        d.text((x + 4, y + th + 7), TITEL[view], font=font(19, bold=True), fill=INK)
    x, y = zelle(2, 1); y += 18
    for label, value in masse():
        d.text((x + 6, y), label.upper(), font=font(17, bold=True), fill=MUTED); y += 24
        for zeile in umbrechen(value, font(19), tw - 24, d):
            d.text((x + 6, y), zeile, font=font(19), fill=INK); y += 25
        y += 8
    im.convert('P', palette=Image.ADAPTIVE, colors=200).save(out, optimize=True)
    return out


def main():
    body = build()
    with tempfile.TemporaryDirectory() as tmp:
        stl = Path(tmp) / f'{NAME}.stl'
        cq.exporters.export(cq.Workplane(obj=body), str(stl), tolerance=0.002, angularTolerance=0.05)
        views = [dict(v, span_mm=L * 1.25) for v in VIEWS] + [ISO]
        pngs = render(stl, tmp, NAME, 'cad', views, [900, 640])
        print('Wrote', blatt(pngs, HERE / f'{NAME}_dreiseitenansicht.png'))


if __name__ == '__main__':
    main()
