"""Everlight 42-21SYGC/S530-E2/TR8 — 1,8-mm-Rund-SMD-LED (gelbgrün) als STEP.

Maße aus dem Datenblatt (Package Outline Dimensions, Toleranz ±0,1):
  Grundplatte mit Lötflächen  3,2 × 2,4 × 0,5 (Lötfahnen an den Stirnseiten,
                              innen 2,0 frei)
  Gehäusekörper               2,2 × 2,4 × 0,5 darüber
  Linse                       Ø 1,8, Zylinder 0,6 + Kuppe R 0,9 → Gesamthöhe 2,5
  Kathodenmarke               Ecke des Gehäusekörpers angefast (im Datenblatt
                              der Punkt oben links)

  .venv/bin/python "leds/EVL 42-21SYGC/create_led_step.py"

Bezugssystem: Ursprung in der Linsenachse auf der Unterseite (Lötebene),
+z zur Linsenspitze, x längs (Lötfahnen bei ±1,6), y quer. Ein Solid
(Gehäuse und Linse zusammen); Farbe hell, die Linse ist wasserklar.
"""
import sys
from pathlib import Path

import cadquery as cq

BASE = Path(__file__).resolve().parent
sys.path.append(str(BASE.parent.parent / 'parts' / '16-003270E'))
from create_snaplock_clip_step import export_named  # noqa: E402

NAME = 'Everlight_42-21SYGC'
PART_NAME = 'LED 42-21SYGC Everlight'
COLOR = (0.93, 0.93, 0.88)

L, W = 3.2, 2.4          # Grundplatte
T_BASE = 0.5
BODY_L, T_BODY = 2.2, 0.5
LENS_D, LENS_CYL, LENS_R = 1.8, 0.6, 0.9
LEAD_GAP = 2.0           # freier Bereich zwischen den Lötfahnen unten
LEAD_RECESS = 0.15       # Rücksprung der Unterseite zwischen den Fahnen
CATHODE_CHAMFER = 0.3


def build():
    base = cq.Workplane('XY').box(L, W, T_BASE, centered=(True, True, False))
    recess = (cq.Workplane('XY').box(LEAD_GAP, W + 0.2, LEAD_RECESS, centered=(True, True, False)))
    base = base.cut(recess)
    body = (cq.Workplane('XY', origin=(0, 0, T_BASE))
            .box(BODY_L, W, T_BODY, centered=(True, True, False)))
    # Kathodenmarke: eine senkrechte Kante des Gehäusekörpers anfasen (-x, +y)
    body = body.edges('|Z').edges(cq.selectors.NearestToPointSelector((-BODY_L / 2, W / 2, T_BASE + T_BODY / 2))).chamfer(CATHODE_CHAMFER)
    z_lens = T_BASE + T_BODY
    lens = cq.Workplane('XY', origin=(0, 0, z_lens)).circle(LENS_D / 2).extrude(LENS_CYL)
    cap = cq.Workplane('XY').sphere(LENS_R).translate((0, 0, z_lens + LENS_CYL))
    cap = cap.intersect(cq.Workplane('XY', origin=(0, 0, z_lens + LENS_CYL)).box(4, 4, 2, centered=(True, True, False)))
    return base.union(body).union(lens).union(cap).val()


def main():
    body = build()
    out = BASE / f'{NAME}.step'
    export_named(body, out, PART_NAME, COLOR)
    bb = body.BoundingBox()
    print(f'Wrote {out}')
    print(f'  valid={body.isValid()} solids={len(body.Solids())} faces={len(body.Faces())} volume={body.Volume():.2f} mm^3')
    print(f'  bbox x[{bb.xmin:.2f},{bb.xmax:.2f}] y[{bb.ymin:.2f},{bb.ymax:.2f}] z[{bb.zmin:.2f},{bb.zmax:.2f}]')


if __name__ == '__main__':
    main()
