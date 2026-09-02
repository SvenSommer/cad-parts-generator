"""Kontrollblatt und Produktbilder eines Schraubteils erzeugen.

  .venv/bin/python screws/render_checks.py [bkl-10120256 ...]

Je Teil entstehen neben der STEP-Datei:
  <name>_dreiseitenansicht.png   Vorder-, Drauf- und Seitenansicht in erster
                                 Winkelprojektion, massstabsgleich, dazu eine
                                 Dreiviertelansicht und die Sollmasse
  <name>_render.png              Produktbild, vernickeltes Messing
  <name>_render_schnitt.png      dasselbe laengs halbiert, zeigt das Innengewinde

Blender laeuft headless (Pfad ueber $BLENDER, sonst macOS-Standard).
Zwischenschritt ist STL, weil Blender kein STEP liest.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import cadquery as cq
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, str(Path(__file__).resolve().parent))  # Aufruf vom Repo-Root
from create_screw_step import SCREWS, build, step_path  # noqa: E402

BLENDER = os.environ.get('BLENDER') or shutil.which('blender') \
    or '/Applications/Blender.app/Contents/MacOS/Blender'
HERE = Path(__file__).resolve().parent

# Bezugssystem der Teile: Achse = z, Kopf bei negativem z. Bild-rechts ist
# ueberall -z, damit der Kopf in jeder Tafel rechts liegt — wie auf der
# Herstellerzeichnung. Erste Winkelprojektion: die Draufsicht (Blick von +y)
# kommt unter die Vorderansicht, die Ansicht von rechts (Blick auf die
# Kopfstirn) links daneben.
TAFELN = [
    dict(name='front', dir=[-1, 0, 0], up=[0, 1, 0]),   # zeigt die Schluesselweite
    dict(name='top', dir=[0, -1, 0], up=[-1, 0, 0]),    # zeigt das Eckenmass
    dict(name='right', dir=[0, 0, 1], up=[0, 1, 0]),    # Kopfstirn
]
ISO = dict(name='iso', dir=[0.55, 0.62, 0.56], up=[0, 1, 0], pad=1.10)
# Laengsschnitt: Blick senkrecht IN die Schnittebene des halbierten Koerpers.
# Weg ist die Haelfte bei y > 0, die Kamera muss also von dort kommen
# (dir = -y); mit up = -x bleibt der Kopf wie in allen Tafeln rechts.
SCHNITT_TAFEL = dict(name='half', dir=[0, -1, 0], up=[-1, 0, 0])
# Dasselbe Halbmodell fuer das Produktbild, aber schraeg — im Metall zeigt
# erst die Perspektive, wie tief das Innengewinde sitzt.
SCHNITT = dict(name='half', dir=[0.30, -0.86, 0.42], up=[1, 0, 0], pad=1.10)

TAFEL_TITEL = {'right': 'Ansicht von rechts', 'front': 'Vorderansicht',
               'top': 'Draufsicht', 'iso': 'Dreiviertelansicht',
               'half': 'Längsschnitt'}
FONTS = ('/System/Library/Fonts/Supplemental/Arial.ttf',
         '/System/Library/Fonts/Helvetica.ttc',
         '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf')
FONTS_BOLD = ('/System/Library/Fonts/Supplemental/Arial Bold.ttf',
              '/System/Library/Fonts/Supplemental/Arial.ttf',
              '/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf')
PAD, GAP, HEADER = 26, 18, 100
INK, MUTED, RULE = (25, 32, 45), (105, 115, 130), (208, 214, 222)


def font(size, bold=False):
    for path in (FONTS_BOLD if bold else FONTS):
        if Path(path).exists():
            return ImageFont.truetype(path, size)
    return ImageFont.load_default(size)


def masse(v):
    """Sollmasse des Teils, wie sie unter dem Blatt stehen."""
    d, p = v['thread']['d'], v['thread']['p']
    h = 0.8660254 * p
    def mm(x):
        return f'{x:.2f}'.replace('.', ',')
    return [
        ('Gesamtlänge', f"{mm(v['shank'] + v['head_len'])} mm "
                        f"({mm(v['shank'])} Schaft + {mm(v['head_len'])} Kopf)"),
        ('Kopf', f"Sechskant SW {mm(v['head_af'])} mm, über Ecke "
                 f"{mm(v['head_af'] / 3 ** 0.5 * 2)} mm, "
                 f"beidseitig C {mm(v['head_chamfer'])}"),
        ('Außengewinde', f'4-40 UNC-2A, Ø {mm(d)} / Kern {mm(d - 17 * h / 12)} mm, '
                         f"Länge {mm(v['thread_len'])} mm"),
        ('Absatz', f"{mm(v['shank'] - v['thread_len'])} mm glatt unter dem Kopf, "
                   f'Ø {mm(d)} mm'),
        ('Innengewinde', f'4-40 UNC-2B, Ø {mm(d)} / Kern {mm(d - 5 * h / 4)} mm, '
                         f"{mm(v['tap_depth'])} mm tief ab Kopfstirn, "
                         f"C {mm(v['tap_chamfer'])} an der Mündung"),
        ('Steigung', f'{mm(p)} mm (40 Gänge je Zoll), rechtsgängig'),
        ('Bezugssystem', 'z = 0 an der Anlagefläche des Kopfes, +z zur '
                         'Gewindespitze'),
    ]


def render(stl, out_dir, stem, style, views, res):
    """Blender headless aufrufen; gibt die PNG-Pfade je Ansicht zurueck."""
    job = dict(stl=str(stl), out_dir=str(out_dir), stem=stem, style=style,
               res=res, views=views)
    job_file = Path(out_dir) / f'{stem}_{style}.json'
    job_file.write_text(json.dumps(job))
    res_run = subprocess.run(
        [BLENDER, '--background', '--python', str(HERE / 'blender_views.py'),
         '--', str(job_file)], capture_output=True, text=True)
    pngs = {v['name']: Path(out_dir) / f"{stem}_{v['name']}.png" for v in views}
    missing = [n for n, p in pngs.items() if not p.exists()]
    if missing:
        sys.stderr.write(res_run.stdout[-3000:] + res_run.stderr[-3000:])
        raise RuntimeError(f'Blender lieferte keine Ansicht {missing}')
    return pngs


def auf_weiss(path):
    """Transparentes Render auf weissen Grund setzen (Stil "cad")."""
    src = Image.open(path).convert('RGBA')
    bg = Image.new('RGBA', src.size, (255, 255, 255, 255))
    return Image.alpha_composite(bg, src).convert('RGB')


def umbrechen(text, f, breite, d):
    """Wert auf die Spaltenbreite umbrechen (Pillow bricht selbst nicht um)."""
    zeilen, zeile = [], ''
    for wort in text.split(' '):
        probe = f'{zeile} {wort}'.strip()
        if zeile and d.textlength(probe, font=f) > breite:
            zeilen.append(zeile)
            zeile = wort
        else:
            zeile = probe
    return zeilen + [zeile]


def blatt(pngs, titel, untertitel, rows, out):
    """Tafeln in Projektionsanordnung, Dreiviertelansicht, Schnitt, Massliste.

    Raster 3x2. Die Massliste sitzt in der letzten Zelle statt unter dem
    Blatt — sonst klafft dort, wo in der Projektion die Ansicht von links
    stuende, eine leere Flaeche ueber die halbe Blattbreite.
    """
    tiles = {k: auf_weiss(p) for k, p in pngs.items()}
    tw, th = next(iter(tiles.values())).size
    label_h = 32
    sheet_w = PAD * 2 + tw * 3 + GAP * 2
    sheet_h = HEADER + (th + label_h) * 2 + PAD

    im = Image.new('RGB', (sheet_w, sheet_h), 'white')
    d = ImageDraw.Draw(im)
    d.text((PAD, 24), titel, font=font(34, bold=True), fill=INK)
    d.text((PAD, 66), untertitel, font=font(18), fill=MUTED)
    d.line([(PAD, HEADER - 6), (sheet_w - PAD, HEADER - 6)], fill=RULE, width=1)

    def zelle(col, row):
        return PAD + col * (tw + GAP), HEADER + row * (th + label_h)

    for view, col, row in (('right', 0, 0), ('front', 1, 0), ('iso', 2, 0),
                           ('half', 0, 1), ('top', 1, 1)):
        x, y = zelle(col, row)
        im.paste(tiles[view], (x, y))
        d.rectangle([x, y, x + tw - 1, y + th - 1], outline=RULE)
        d.text((x + 4, y + th + 7), TAFEL_TITEL[view], font=font(19, bold=True),
               fill=INK)

    x, y = zelle(2, 1)
    y += 18                      # Abstand zur Bildunterschrift der Zelle darueber
    f_label, f_val = font(17, bold=True), font(19)
    for label, value in rows:
        d.text((x + 6, y), label.upper(), font=f_label, fill=MUTED)
        y += 24
        for zeile in umbrechen(value, f_val, tw - 24, d):
            d.text((x + 6, y), zeile, font=f_val, fill=INK)
            y += 25
        y += 10
    im.convert('P', palette=Image.ADAPTIVE, colors=200).save(out, optimize=True)
    return out


def main(keys):
    for key in keys:
        v = SCREWS[key]
        body = build(v)
        ziel = step_path(v).parent
        with tempfile.TemporaryDirectory() as tmp:
            stl = Path(tmp) / f"{v['name']}.stl"
            cq.exporters.export(cq.Workplane(obj=body), str(stl),
                                tolerance=0.004, angularTolerance=0.06)
            # Laengs halbiert fuer das Schnittbild: erst hier, nicht im
            # Bauteilskript — die STEP-Datei bleibt das ganze Teil.
            half_stl = Path(tmp) / f"{v['name']}_half.stl"
            cq.exporters.export(
                cq.Workplane(obj=body.cut(cq.Solid.makeBox(
                    9, 9, 20, cq.Vector(-9, 0, -8)))),
                str(half_stl), tolerance=0.004, angularTolerance=0.06)

            spann = (v['shank'] + v['head_len']) * 1.08   # Rahmen aller Tafeln
            cad_views = [dict(t, span_mm=spann) for t in TAFELN] + [ISO]
            cad = render(stl, tmp, v['name'], 'cad', cad_views, [900, 640])
            cad.update(render(half_stl, tmp, v['name'] + '_cut', 'cad',
                              [dict(SCHNITT_TAFEL, span_mm=spann)], [900, 640]))
            out = blatt(cad, v['title'], v['subtitle'], masse(v),
                        ziel / f"{v['name']}_dreiseitenansicht.png")
            print(f'Wrote {out}')

            for stl_src, view, suffix in ((stl, ISO, '_render.png'),
                                          (half_stl, SCHNITT, '_render_schnitt.png')):
                stem = v['name'] + ('_half' if 'half' in suffix else '')
                png = render(stl_src, tmp, stem, 'metal', [view], [1400, 1050])
                out = ziel / (v['name'] + suffix)
                shutil.copy(png[view['name']], out)
                print(f'Wrote {out}')


if __name__ == '__main__':
    args = sys.argv[1:] or list(SCREWS)
    unbekannt = [a for a in args if a not in SCREWS]
    if unbekannt:
        sys.exit(f'Unbekanntes Teil: {unbekannt}. Bekannt: {list(SCREWS)}')
    main(args)
