"""Kontrollblatt der Jack Screw rendern: Dreiseitenansicht + Dreiviertel.

Baut Kopf und Schraube frisch aus create_jackscrew_step, exportiert sie als
getrennte STLs (zwei Materialien im Render), ruft Blender headless auf und
setzt aus den vier Ansichten ein Blatt mit den Sollmaßen der Zeichnung:

  .venv/bin/python screws/render_jackscrew_checks.py

Die Einzelansichten und das Blatt landen neben der STEP-Datei. Blender wird
über $BLENDER gefunden, sonst der macOS-Standardpfad.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import cadquery as cq
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))
from create_jackscrew_step import (BELOW_HEAD, COLLAR_D, COLLAR_L, HEAD_D,  # noqa: E402
                                    HEAD_H, NECK_D, NECK_L, SCREW_L, THREAD_L,
                                    UNC440_D, build_head, build_screw)

BLENDER = os.environ.get('BLENDER') or shutil.which('blender') \
    or '/Applications/Blender.app/Contents/MacOS/Blender'
HERE = Path(__file__).resolve().parent
OUT_DIR = HERE / 'D Sub Male Screw lock 4-40 UNC with plas'
STEM = '09670009971_jackscrew'
VIEW_TITLES = [('front', 'Vorderansicht'), ('side', 'Seitenansicht (90°)'),
               ('top', 'Draufsicht Kopf'), ('iso', 'Dreiviertel')]
FONTS = ('/System/Library/Fonts/Supplemental/Arial.ttf',
         '/System/Library/Fonts/Helvetica.ttc',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
FONTS_BOLD = ('/System/Library/Fonts/Supplemental/Arial Bold.ttf',
              '/System/Library/Fonts/Supplemental/Arial.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')

PAD, GAP, HEADER = 26, 18, 96
INK, MUTED, RULE = (25, 32, 45), (105, 115, 130), (208, 214, 222)


def font(size, bold=False):
    for path in (FONTS_BOLD if bold else FONTS):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def mm(x):
    return f'{x:g}'.replace('.', ',')


FACTS = [
    ('Kopf', f'Ø{mm(HEAD_D)} x {mm(HEAD_H)} mm, gerändelt, PH1-Kreuzschlitz '
             '(grauer 30% GF Thermoplast, umspritzt)'),
    ('Bund', f'Ø{mm(COLLAR_D)} x {mm(COLLAR_L)} mm ab Kopfunterkante'),
    ('Hals', f'Ø{mm(NECK_D)} x {mm(NECK_L)} mm'),
    ('Gewinde', f'UNC 4-40 (Ø{mm(UNC440_D)}), Zone {mm(THREAD_L)} mm, '
                f'Schraubenteil {mm(SCREW_L)} mm — im Modell glatter Zylinder'),
    ('Länge', f'{mm(HEAD_H + BELOW_HEAD)} mm gesamt, {mm(BELOW_HEAD)} mm '
              'unter dem Kopf'),
    ('Werkstoff', 'Stahlschraube vernickelt (Nickel über Kupfer)'),
    ('Quelle', 'Harting-Zeichnung 09670009971_BL01_R31392_100079036DRW002A'),
]


def render_views(out_dir):
    """STL-Paar exportieren, Blender rufen. Gibt die PNG-Pfade zurück."""
    with tempfile.TemporaryDirectory() as tmp:
        stls = []
        for name, solid in (('head', build_head()), ('screw', build_screw())):
            stl = Path(tmp) / f'{name}.stl'
            cq.exporters.export(cq.Workplane(obj=solid), str(stl),
                                tolerance=0.003, angularTolerance=0.05)
            stls.append(str(stl))
        cmd = [BLENDER, '--background', '--python',
               str(HERE / 'blender_jackscrew_views.py'),
               '--', *stls, str(out_dir), STEM]
        res = subprocess.run(cmd, capture_output=True, text=True)
    pngs = {v: Path(out_dir) / f'{STEM}_{v}.png' for v, _ in VIEW_TITLES}
    missing = [v for v, p in pngs.items() if not p.exists()]
    if missing:
        sys.stderr.write(res.stdout[-3000:] + res.stderr[-3000:])
        raise RuntimeError(f'Blender lieferte keine Ansicht {missing}')
    return pngs


def compose(pngs, out):
    """Vier Hochformat-Ansichten nebeneinander + Maßangaben darunter."""
    tiles = {}
    for v, p in pngs.items():
        src = Image.open(p).convert('RGBA')
        bg = Image.new('RGBA', src.size, (255, 255, 255, 255))
        tiles[v] = Image.alpha_composite(bg, src).convert('RGB')
    tw, th = next(iter(tiles.values())).size
    label_h = 34
    sheet_w = PAD * 2 + tw * 4 + GAP * 3
    facts_h = 30 + len(FACTS) * 26
    sheet_h = HEADER + th + label_h + GAP + facts_h + PAD

    im = Image.new('RGB', (sheet_w, sheet_h), 'white')
    d = ImageDraw.Draw(im)
    d.text((PAD, 24), 'Harting 09670009971 — Jack Screw UNC 4-40',
           font=font(34, bold=True), fill=INK)
    d.text((PAD, 64), 'D-Sub-Schraubverriegelung — Kontrollblatt, alle '
           'Ansichten orthografisch. Maße in mm.', font=font(18), fill=MUTED)
    d.line([(PAD, HEADER - 6), (sheet_w - PAD, HEADER - 6)], fill=RULE, width=1)

    for i, (view, caption) in enumerate(VIEW_TITLES):
        x = PAD + i * (tw + GAP)
        im.paste(tiles[view], (x, HEADER))
        d.rectangle([x, HEADER, x + tw - 1, HEADER + th - 1], outline=RULE)
        d.text((x + 4, HEADER + th + 8), caption, font=font(19, bold=True),
               fill=INK)

    y = HEADER + th + label_h + GAP
    d.line([(PAD, y - 10), (sheet_w - PAD, y - 10)], fill=RULE, width=1)
    for label, value in FACTS:
        d.text((PAD, y), label, font=font(18, bold=True), fill=MUTED)
        d.text((PAD + 130, y), value, font=font(18), fill=INK)
        y += 26
    im.convert('P', palette=Image.ADAPTIVE, colors=192).save(out, optimize=True)
    return out


def main():
    pngs = render_views(OUT_DIR)
    out = compose(pngs, OUT_DIR / f'{STEM}_check.png')
    print(f'Wrote {out}')


if __name__ == '__main__':
    main()
