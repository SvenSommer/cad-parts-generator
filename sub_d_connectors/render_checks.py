"""Kontrollblatt je Sub-D-Variante rendern.

Fuer jede Groesse/Bauform entsteht neben der STEP-Datei ein PNG mit vier
orthografischen Ansichten (Steckseite, Dreiviertel, Loetseite, Profil) und den
Sollmassen — damit laesst sich ein Modell pruefen, ohne es in CAD zu laden.

  .venv/bin/python sub_d_connectors/render_checks.py [de9 db25 ...]

Ohne Argumente werden alle Varianten gerendert. Blender wird headless
aufgerufen; der Pfad laesst sich ueber $BLENDER setzen.
Zwischenschritt ist STL, weil Blender kein STEP liest.
"""
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import cadquery as cq
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))  # Aufruf vom Repo-Root
from create_subd_step import (DEFAULT_FORMS, FORMS, PITCH, ROW_PITCH, SHELLS,  # noqa: E402
                               step_path)

BLENDER = os.environ.get('BLENDER') or shutil.which('blender') \
    or '/Applications/Blender.app/Contents/MacOS/Blender'
HERE = Path(__file__).resolve().parent
VIEW_TITLES = [('front', 'Steckseite'), ('iso', 'Dreiviertel vorn'),
               ('rear', 'Loetseite'), ('side', 'Profil')]
FORM_LABEL = {
    'female': 'Buchse (female)',
    'male': 'Stecker (male)',
    'male_soldercup': 'Stecker (male), Kabelmontage',
}
TERMINATION = {
    'female': 'Loetstifte, gerade — fuer Leiterplatte',
    'male': 'Loetstifte, gerade — fuer Leiterplatte',
    'male_soldercup': 'Loetkelch — fuer Litze, gedrehte Kontakte',
}
TITLE_FORM = {'female': 'female', 'male': 'male', 'male_soldercup': 'male, Loetkelch'}
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


def facts(key, form, depth):
    """Sollmasse der Variante, wie sie im Kontrollblatt stehen."""
    s = SHELLS[key]
    rows = '+'.join(str(n) for n in s['rows'])
    hole_d = 3.05 if form == 'male_soldercup' else 3.0
    rows_out = [
        ('Kontakte', f"{rows} = {sum(s['rows'])}, {len(s['rows'])}-reihig"),
        ('Raster', f'{PITCH} mm in der Reihe / {ROW_PITCH} mm Reihenabstand'),
        ('Flansch', f"{s['flange_len']} x {s['flange_h']} mm"),
        ('Schraubloecher', f"{s['holes']} mm Abstand, {hole_d:g} mm Durchmesser"
                           .replace('.', ',')),
        ('Bautiefe', f'{depth:.2f} mm ab Steckflaeche'.replace('.', ',')),
        ('Bauform', FORM_LABEL[form]),
        ('Anschluss', TERMINATION[form]),
    ]
    if form == 'male_soldercup':
        rows_out.append(('Vorbild', f"MH Connectors MHDM{sum(s['rows'])}SP"))
    return rows_out


def render_views(step, out_dir, stem):
    """STEP -> STL -> vier Blender-Ansichten. Gibt PNG-Pfade und Bautiefe zurueck."""
    shape = cq.importers.importStep(str(step))
    depth = shape.val().BoundingBox().zlen
    stl = Path(out_dir) / f'{stem}.stl'
    cq.exporters.export(shape, str(stl), tolerance=0.005, angularTolerance=0.08)
    cmd = [BLENDER, '--background', '--python', str(HERE / 'blender_views.py'),
           '--', str(stl), str(out_dir), stem]
    res = subprocess.run(cmd, capture_output=True, text=True)
    pngs = {v: Path(out_dir) / f'{stem}_{v}.png' for v, _ in VIEW_TITLES}
    missing = [v for v, p in pngs.items() if not p.exists()]
    if missing:
        sys.stderr.write(res.stdout[-3000:] + res.stderr[-3000:])
        raise RuntimeError(f'Blender lieferte keine Ansicht {missing} fuer {stem}')
    return pngs, depth


def compose(pngs, title, subtitle, rows, out):
    """Vier Ansichten + Massangaben zu einem Kontrollblatt setzen."""
    # Blender rendert mit Alpha (siehe blender_views.py), Grund kommt hier dazu.
    tiles = {}
    for v, p in pngs.items():
        src = Image.open(p).convert('RGBA')
        bg = Image.new('RGBA', src.size, (255, 255, 255, 255))
        tiles[v] = Image.alpha_composite(bg, src).convert('RGB')
    tw, th = next(iter(tiles.values())).size
    label_h = 34
    sheet_w = PAD * 2 + tw * 2 + GAP
    facts_h = 30 + len(rows) * 26
    sheet_h = HEADER + (th + label_h) * 2 + GAP + facts_h + PAD

    im = Image.new('RGB', (sheet_w, sheet_h), 'white')
    d = ImageDraw.Draw(im)
    d.text((PAD, 24), title, font=font(34, bold=True), fill=INK)
    d.text((PAD, 64), subtitle, font=font(18), fill=MUTED)
    d.line([(PAD, HEADER - 6), (sheet_w - PAD, HEADER - 6)], fill=RULE, width=1)

    for i, (view, caption) in enumerate(VIEW_TITLES):
        x = PAD + (i % 2) * (tw + GAP)
        y = HEADER + (i // 2) * (th + label_h)
        im.paste(tiles[view], (x, y))
        d.rectangle([x, y, x + tw - 1, y + th - 1], outline=RULE)
        d.text((x + 4, y + th + 8), caption, font=font(19, bold=True), fill=INK)

    y = HEADER + (th + label_h) * 2 + GAP
    d.line([(PAD, y - 10), (sheet_w - PAD, y - 10)], fill=RULE, width=1)
    for label, value in rows:
        d.text((PAD, y), f'{label}', font=font(18, bold=True), fill=MUTED)
        d.text((PAD + 190, y), value, font=font(18), fill=INK)
        y += 26
    # Flaechiges Bild mit wenigen Blautoenen: als Palettenbild ein Bruchteil der
    # Groesse, ohne sichtbaren Unterschied — die Blaetter liegen im Repo.
    im.convert('P', palette=Image.ADAPTIVE, colors=192).save(out, optimize=True)
    return out


def main(keys):
    for key in keys:
        for form in FORMS.get(key, DEFAULT_FORMS):
            step = step_path(key, form)
            stem = f"{SHELLS[key]['name']}_{form}"
            with tempfile.TemporaryDirectory() as tmp:
                pngs, depth = render_views(step, tmp, stem)
                out = step.parent / f'{stem}_check.png'
                compose(pngs, f"{SHELLS[key]['name']} {TITLE_FORM[form]}",
                        'Sub-D standard density — Kontrollblatt, alle Ansichten '
                        'orthografisch. Masse in mm.',
                        facts(key, form, depth), out)
            print(f'Wrote {out}')


if __name__ == '__main__':
    args = sys.argv[1:] or list(SHELLS)
    unknown = [a for a in args if a not in SHELLS]
    if unknown:
        sys.exit(f'Unbekannte Groesse: {unknown}. Bekannt: {list(SHELLS)}')
    main(args)
