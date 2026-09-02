import math
from pathlib import Path

import cadquery as cq

# Harting 09670009971 — D-Sub Jack Screw UNC 4-40 mit Kunststoff-Rändelkopf,
# als STEP für CAD-Import (z.B. Onshape). Maße aus der Harting-Zeichnung
# 09670009971_BL01_R31392_100079036DRW002A.pdf. Einheiten: Millimeter.
#
# Aufbau laut Zeichnung, von oben nach unten:
#   Rändelkopf Ø6,5 x 8 (grauer 30% GF Thermoplast, umspritzt), oben
#   PH1-Kreuzschlitz nach ISO 4757 — darunter die Stahlschraube (vernickelt):
#   Bund Ø3 (8 mm ab Kopfunterkante), Hals Ø1,8, Schraubenteil 8,8 mm mit
#   UNC-4-40-Gewinde auf den unteren 4,5 mm. Gesamt unter dem Kopf: 21,9.
#   Die gestrichelte Nut unter dem Kopf kennzeichnet nur die M3-Version
#   (09670029971) und fehlt hier deshalb.
#
# Koordinaten: z = 0 an der Kopfunterkante (Auflagefläche), +z zur
# Gewindespitze. Der Kopf liegt bei z in [-8, 0].
#
# Zwei Solids im Compound — Kunststoffkopf und Stahlschraube getrennt, damit
# sie im CAD einzeln einfärbbar sind. Gewinde vereinfacht als Zylinder auf
# dem Außendurchmesser (UNC 4-40: Ø2,845, Steigung 0,635). Echte
# Helix-Gewinde kann inzwischen create_screw_step.py (thread_solid); beim
# Zusammenführen der beiden screws-Pipelines kann dieses Teil darauf wechseln.

BASE = Path(__file__).resolve().parent

HEAD_D, HEAD_H = 6.5, 8.0        # Rändelkopf
COLLAR_D, COLLAR_L = 3.0, 8.0    # Bund unter dem Kopf
NECK_D = 1.8                     # Hals
SCREW_L = 8.8                    # Schraubenteil gesamt (Kegel + Gewindezone)
THREAD_L = 4.5                   # davon Gewinde
BELOW_HEAD = 21.9                # Kopfunterkante -> Spitze
NECK_L = BELOW_HEAD - COLLAR_L - SCREW_L   # 5,1
UNC440_D = 2.845                 # UNC 4-40 Außendurchmesser (0.112")

KNURLS = 24                      # Längsrillen am Kopf (kosmetisch)
KNURL_R = 0.18
RECESS_DEPTH = 2.1               # PH1-Kegelgrund im Kopf
CORE_TOP = -HEAD_H + RECESS_DEPTH + 0.3  # Stahlkern endet unter dem Schlitz


def cyl(r, z0, z1, cx=0.0, cy=0.0):
    return cq.Solid.makeCylinder(r, z1 - z0, cq.Vector(cx, cy, z0))


def cone(r_bottom, r_top, z0, z1):
    return cq.Solid.makeCone(r_bottom, r_top, z1 - z0, cq.Vector(0, 0, z0))


def build_head():
    """Kunststoffkopf: gerändeltes Rohr um den Ø3-Kern der Stahlschraube."""
    head = cyl(HEAD_D / 2, -HEAD_H, 0.0)
    head = cq.Workplane(obj=head).edges("<Z").chamfer(0.4).val()

    # Geradrändel: Rillen als Zylinderschnitte am Umfang. Die Zeichnung
    # rändelt die volle Kopfhöhe; nur die Kopffase oben bleibt frei, damit
    # die Rillen nicht in die Fasenkante schneiden.
    cuts = []
    for i in range(KNURLS):
        a = 2 * math.pi * i / KNURLS
        cx = math.cos(a) * (HEAD_D / 2 + KNURL_R * 0.45)
        cy = math.sin(a) * (HEAD_D / 2 + KNURL_R * 0.45)
        cuts.append(cyl(KNURL_R, -HEAD_H + 0.45, -0.15, cx, cy))

    # PH1-Kreuzschlitz (ISO 4757), vereinfacht: zwei gekreuzte Flügel mit
    # Bodenschräge plus zentraler Kegelgrund.
    wing = (cq.Workplane("XY", origin=(0, 0, -HEAD_H))
            .rect(4.2, 1.0).workplane(offset=1.4)
            .rect(1.2, 1.0).loft(combine=False).val())
    cuts += [wing, wing.rotate(cq.Vector(0, 0, 0), cq.Vector(0, 0, 1), 90),
             cone(1.15, 0.0, -HEAD_H, -HEAD_H + RECESS_DEPTH)]

    # Sackbohrung für den Stahlkern — nur bis unter den Kreuzschlitz, damit
    # der Schlitz in vollem Kunststoff liegt und seine Tiefe behält.
    cuts.append(cyl(COLLAR_D / 2, CORE_TOP, 0.1))
    return head.cut(*cuts).clean()


def build_screw():
    """Stahlschraube: Ø3-Kern im Kopf, Bund, Hals, Kegel, Gewindezylinder."""
    z_neck0 = COLLAR_L                       # Bundende
    z_screw0 = COLLAR_L + NECK_L             # Beginn Schraubenteil
    z_taper1 = z_screw0 + (SCREW_L - THREAD_L)  # Kegel bis Gewindebeginn
    z_tip = BELOW_HEAD
    tip_ch = 0.4                             # Fase an der Spitze

    parts = [
        cyl(COLLAR_D / 2, CORE_TOP, z_neck0),        # Kern im Kopf + Bund
        cyl(NECK_D / 2, z_neck0 - 0.1, z_screw0 + 0.1),
        cone(NECK_D / 2, UNC440_D / 2, z_screw0, z_taper1),
        # Gewindezylinder exakt am Kegelende ansetzen — ein Überlapp würde
        # radial über den Kegel hinausstehen und die 4,5er Zone verlängern.
        cyl(UNC440_D / 2, z_taper1, z_tip - tip_ch),
        cone(UNC440_D / 2, UNC440_D / 2 - tip_ch, z_tip - tip_ch, z_tip),
    ]
    return parts[0].fuse(*parts[1:], glue=False).clean()


def main():
    head, screw = build_head(), build_screw()
    body = cq.Compound.makeCompound([head, screw])
    out = (BASE / 'D Sub Male Screw lock 4-40 UNC with plas'
           / '09670009971_jackscrew_unc4-40.step')
    body.exportStep(str(out))
    bb = body.BoundingBox()
    print(f'Wrote {out}')
    for name, s in (('Kopf', head), ('Schraube', screw)):
        print(f'  {name}: valid={s.isValid()} volume={s.Volume():.1f} mm^3')
    print(f'  bbox x[{bb.xmin:.3f},{bb.xmax:.3f}] y[{bb.ymin:.3f},{bb.ymax:.3f}] '
          f'z[{bb.zmin:.3f},{bb.zmax:.3f}]  Gesamtlänge={bb.zlen:.3f}')


if __name__ == '__main__':
    main()
