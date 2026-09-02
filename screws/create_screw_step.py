"""Schraubteile als STEP-Solids für den CAD-Import (Onshape u. a.).

Einheiten: Millimeter. Bezugssystem je Teil: z = 0 an der Anlagefläche des
Kopfes, +z entlang des Schafts — der Kopf liegt also bei negativem z, das
Außengewinde bei positivem. So sitzt die Schraube beim Einbau mit z = 0 auf
dem Flansch des Steckverbinders.

  .venv/bin/python screws/create_screw_step.py

Die Gewinde sind echt geschnitten: das UN-Profil wird entlang einer Helix
gesweept, nicht als glatter Zylinder vereinfacht.
"""
from pathlib import Path

import cadquery as cq

BASE = Path(__file__).resolve().parent

# UN-Grundprofil (ASME B1.1), abgeleitet aus Nenndurchmesser D und Steigung P:
#   H      = Höhe des Grunddreiecks = sqrt(3)/2 * P
#   außen  Kamm auf D/2 mit Abflachung P/8, Grund auf D/2 - 17H/24, Nutbreite
#          dort P/6 — das ergibt den Kerndurchmesser der Tabellen (4-40: 2,066)
#   innen  Kamm auf D/2 - 5H/8 (Kerndurchmesser 2,157) mit Abflachung P/4,
#          Grund auf dem Nenndurchmesser
# Zahnbreite über dem Radius: w(r) = P * (D/2 + H/8 - r) / H.
UNC_4_40 = dict(d=2.845, p=0.635)      # No. 4-40 UNC, 0.112" / 40 TPI

# BKL 10120256: Befestigungsschrauben-Set für D-Sub-Steckverbinder, UNC 4/40
# (2 Schrauben, 2 Muttern, 2 Flach-, 2 Federscheiben). Modelliert ist der
# Schraubverbinder selbst — Außengewinde am Schaft, Innengewinde im
# Sechskantkopf, in das die Schraube des Gegensteckers greift.
# Maße aus der Zeichnung "BKL 10120256.pdf":
#   Schaft 7,92 · Kopf 4,80 lang, SW 4,80 · C 0,5 an den Kopfkanten
#   C 0,3 an der Gewindemündung · NO. 4-40UNC-2A außen / -2B innen
# Unbemaßtes aus der Schnittdarstellung abgegriffen (Kopflänge als Maßstab):
# Gewindelänge am Schaft 6,70, Rest glatter Absatz; Sacklochtiefe 3,50 ab
# Kopfstirn, darunter der Kegel des Bohrergrunds.
SCREWS = {
    'bkl-10120256': dict(
        name='BKL_10120256_jackscrew',
        folder='BKL 10120256',
        title='BKL 10120256 — Schraubverbinder',
        subtitle='Befestigungsschraube für D-Sub-Steckverbinder, UNC 4/40. '
                 'Alle Ansichten orthografisch und maßstabsgleich, erste '
                 'Winkelprojektion. Maße in mm.',
        thread=UNC_4_40,
        shank=7.92,          # Gesamtlänge des Schafts ab Kopf-Anlagefläche
        thread_len=6.70,     # davon Gewinde, am freien Ende beginnend
        lead_in=0.30,        # Anschnittfase am freien Schaftende, 45 Grad
        head_len=4.80,
        head_af=4.80,        # Schlüsselweite
        head_chamfer=0.50,   # C 0,5, an beiden Kopfkanten
        tap_depth=3.50,      # Innengewinde ab Kopfstirn
        tap_chamfer=0.30,    # C 0,3 an der Mündung
    ),
}

# Übermaß, mit dem das Innengewindeprofil in die Kernbohrung hineinragt. Das
# Außenprofil bekommt bewusst keines: Am Kernzylinder darf es nur tangieren,
# dann verschmilzt OCC die berührenden Flächen sauber, während es an einer
# helikalen Durchdringung scheitert und zwei lose Körper zurückgibt. Beim
# Innengewinde ist es umgekehrt — dort werden Bohrung und Nut zu einem
# Werkzeug verschmolzen, und das braucht die Überlappung.
BORE_OVERLAP = 0.05


def thread_profile(d, p, internal=False):
    """Achsschnitt eines Gewindegangs als Punktliste (Radius, Höhe).

    Außen der Zahn des Bolzens, innen die Nut der Mutter — beide aus demselben
    Grunddreieck, deshalb passen sie spielfrei ineinander. Beide enden radial
    exakt auf dem Nenndurchmesser; eine Zugabe nach außen würde beim
    Innengewinde den Gewindegrund vertiefen.
    """
    h = 0.8660254 * p
    if not internal:
        r_root, r_crest = d / 2 - 17 * h / 24, d / 2
        return [(r_root, -p * 5 / 12), (r_crest, -p / 16),
                (r_crest, p / 16), (r_root, p * 5 / 12)]
    r_crest = d / 2 - 5 * h / 8 - BORE_OVERLAP
    return [(r_crest, -p / 8), (d / 2, -p * 7 / 16),
            (d / 2, p * 7 / 16), (r_crest, p / 8)]


def thread_solid(d, p, z0, z1, internal=False):
    """Gewindegänge zwischen z0 und z1, plan auf diese Länge geschnitten.

    Der Sweep läuft eine Steigung länger und wird zurückgeschnitten, sonst
    endet der letzte Gang mit einer schrägen Stirnfläche in der Luft. Der
    Schnitt muss hier passieren und nicht erst am fertigen Körper: Ein
    ungetrimmter Gang, der eine Nachbarfläche streift, macht jede folgende
    boolesche Operation unbrauchbar.

    Der Wendel läuft rechtsgängig wie jedes UNC-Gewinde. Nachgemessen wurde am
    fertigen Körper gegen eine Kurve bekannter Steigungsrichtung — makeHelix
    und positionAt() legen für sich genommen die Gegenrichtung nahe.
    """
    pts = thread_profile(d, p, internal)
    spine = cq.Workplane("XY").add(
        cq.Wire.makeHelix(p, z1 - z0 + 2 * p, pts[0][0]).moved(
            cq.Location(cq.Vector(0, 0, z0 - p))))
    prof = cq.Workplane("XZ", origin=(0, 0, z0 - p)).polyline(pts).close()
    return prof.sweep(spine, isFrenet=True).val().intersect(cyl(d, z0, z1))


def cyl(r, z0, z1):
    return cq.Solid.makeCylinder(r, z1 - z0, cq.Vector(0, 0, z0))


def cone(r0, r1, z0, z1):
    return cq.Solid.makeCone(r0, r1, z1 - z0, cq.Vector(0, 0, z0))


def build(v):
    """Schraubverbinder: Sechskantkopf mit Innengewinde, Schaft mit Außengewinde."""
    d, p = v['thread']['d'], v['thread']['p']
    h = 0.8660254 * p
    r_core = d / 2 - 17 * h / 24          # Kern des Außengewindes
    r_tap = d / 2 - 5 * h / 8             # Kern des Innengewindes
    shank, head = v['shank'], v['head_len']
    thr0 = shank - v['thread_len']        # Gewindeanfang am Schaft

    # Kopf: Sechskantprisma, an beiden Stirnkanten kegelig gefast. Die Fase
    # nimmt an den Ecken head_chamfer weg und läuft in den Flächen aus — die
    # abgedrehte Fase eines Sechskants, keine umlaufende Kantenfase.
    r_corner = v['head_af'] / 3 ** 0.5
    r_end = r_corner - v['head_chamfer']
    body = (cq.Workplane("XY", origin=(0, 0, -head))
            .polygon(6, 2 * r_corner).extrude(head).val()
            .intersect(cone(r_end, r_end + head, -head, 0.0))
            .intersect(cone(r_end + head, r_end, -head, 0.0)))

    # Schaft: glatter Absatz unter dem Kopf, dahinter Kern samt Gewindegängen.
    # Der Hüllkörper aus Zylinder und Kegel bringt am freien Ende die
    # Anschnittfase an und kappt die Gewindekämme mit; sein Zylinder liegt
    # außerhalb des Nenndurchmessers und rührt das Gewinde deshalb nicht an.
    lead = v['lead_in']
    shaft = (cyl(r_core, thr0, shank)
             .fuse(cyl(d / 2, 0.0, thr0))
             .fuse(thread_solid(d, p, thr0, shank))
             .intersect(cyl(d / 2 + BORE_OVERLAP, 0.0, shank - lead).fuse(
                 cone(d / 2 + BORE_OVERLAP, d / 2 - lead, shank - lead, shank))))
    body = body.fuse(shaft)

    # Innengewinde: Sackloch ab Kopfstirn mit 118-Grad-Kegel am Grund, gefaste
    # Mündung, Gewindenut. Alles zu einem Werkzeug verschmolzen und in einem
    # Zug abgezogen — nacheinander abgezogen greift der Nutschnitt nicht mehr,
    # weil er dann auf der blanken Bohrungswand aufsetzt.
    zb = -head + v['tap_depth']                   # Bohrungsgrund
    tool = (cyl(r_tap, -head - 0.1, zb)
            .fuse(cone(r_tap, 0.001, zb, zb + r_tap / 1.66428))
            .fuse(thread_solid(d, p, -head - p, zb, internal=True))
            .fuse(cone(r_tap + v['tap_chamfer'], r_tap,
                       -head, -head + v['tap_chamfer'])))
    return body.cut(tool)


def step_path(v):
    return BASE / v['folder'] / f"{v['name']}.step"


def main():
    for v in SCREWS.values():
        body = build(v)
        out = step_path(v)
        out.parent.mkdir(parents=True, exist_ok=True)
        body.exportStep(str(out))
        bb = body.BoundingBox()
        print(f'Wrote {out}')
        print(f'  valid={body.isValid()} solids={len(body.Solids())} '
              f'faces={len(body.Faces())} volume={body.Volume():.1f} mm^3')
        print(f'  bbox x[{bb.xmin:.3f},{bb.xmax:.3f}] y[{bb.ymin:.3f},{bb.ymax:.3f}] '
              f'z[{bb.zmin:.3f},{bb.zmax:.3f}]')


if __name__ == '__main__':
    main()
