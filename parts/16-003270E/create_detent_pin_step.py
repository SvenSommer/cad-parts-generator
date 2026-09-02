"""Raststift 4-40 UNC und Federscheibe aus dem CONEC-Haubensatz 16-003270E.

Der Satz enthält je zwei Raststifte („Detent pin with 4-40 UNC") und
Federscheiben; sie werden in die 4-40-Buchsen des Steckverbinders geschraubt,
auf den die SnapLock-Haube (bzw. beim SD-AC1-DS das Gehäuse mit den
eingesetzten Clips) aufgesteckt wird. Der Clip-Fuß schnappt beim Aufstecken
über die Kuppe und sitzt dann im Hals des Stifts.

  .venv/bin/python parts/16-003270E/create_detent_pin_step.py

Maße: Zeichnung 16K1A4424 bemaßt den Stift nicht. Sechskant und Gewinde
sind Normteile (D-Sub-Befestigung: 4-40 UNC, SW 4,8 wie BKL 10120256).
Bund, Hals und Kuppe sind aus der 3D-Ansicht des Datenblatts abgegriffen
(Verhältnis zum Gewinde-Außendurchmesser 2,845 bzw. zur Sechskanthöhe) und
am Foto des SD-AC1-DS-Prototyps (sd-ac1-ds_2.png) gegengeprüft; Unsicherheit
etwa ±0,2 mm, Gewindelänge ±0,5 mm.

Bezugssystem wie bei den Schraubteilen: z = 0 an der Anlagefläche des
Sechskants (liegt auf der Federscheibe), +z entlang des Gewindes, Kopf
(Sechskant, Bund, Hals, Kuppe) bei negativem z. Die Federscheibe hat
ihren eigenen Ursprung so, dass sie im Stift-System direkt an z = 0
anliegt (Unterseite bei z = 0,64 … in entspanntem Zustand darunter).

Aufbau des Stifts, von der Spitze zum Kopf:
  Gewinde     4-40 UNC-2A, 4,5 lang, Anschnitt C 0,3
  Sechskant   SW 4,8, 4,8 hoch, Fase C 0,2 unten / C 0,4 oben (abgedreht)
  Bund        Ø 3,1 × 1,8
  Hals        Ø 2,6 × 0,4          ← hier sitzt die Gabel des Clips
  Kuppe       Ø 3,0, 2,3 hoch, oben Fläche Ø 1,0 mit Körnermarke
Federscheibe: Sprengring Nr. 4 (ASME B18.21.1 regular), Innen-Ø 2,95,
Außen-Ø 5,3, Dicke 0,64, aufgebogen (Enden axial versetzt).
"""
import math
import sys
from pathlib import Path

import cadquery as cq

BASE = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE.parent.parent / 'screws'))
from create_screw_step import BORE_OVERLAP, UNC_4_40, cone, cyl, thread_solid  # noqa: E402

PIN_NAME = 'CONEC_16-003270E_Raststift_4-40'
WASHER_NAME = 'CONEC_16-003270E_Federscheibe'

THREAD_L, LEAD_IN = 4.50, 0.30
HEX_AF, HEX_H = 4.80, 4.80
HEX_CH_BOT, HEX_CH_TOP = 0.20, 0.40
COLLAR_D, COLLAR_L = 3.10, 1.80
NECK_D, NECK_L = 2.60, 0.40
DOME_D, DOME_H, DOME_STRAIGHT = 3.00, 2.30, 0.50
DOME_TOP_D = 1.00
DIMPLE_D, DIMPLE_DEPTH = 0.50, 0.12

WASHER_ID, WASHER_OD, WASHER_T = 2.95, 5.30, 0.64
WASHER_GAP_DEG, WASHER_RISE = 25.0, 0.55     # Lücke; axialer Versatz der Enden


def build_pin():
    d, p = UNC_4_40['d'], UNC_4_40['p']
    h = 0.8660254 * p
    r_core = d / 2 - 17 * h / 24

    # Sechskant z = -HEX_H … 0, an beiden Stirnen kegelig abgedreht
    r_corner = HEX_AF / 3 ** 0.5
    hexagon = (cq.Workplane('XY', origin=(0, 0, -HEX_H))
               .polygon(6, 2 * r_corner).extrude(HEX_H).val()
               .intersect(cone(r_corner - HEX_CH_TOP, r_corner - HEX_CH_TOP + HEX_H,
                               -HEX_H, 0.0))
               .intersect(cone(r_corner - HEX_CH_BOT + HEX_H, r_corner - HEX_CH_BOT,
                               -HEX_H, 0.0)))

    # Gewinde z = 0 … THREAD_L mit Anschnittfase an der Spitze. Der Kern
    # beginnt 0,3 tiefer im Sechskant: Enden Kern und Gewindegang in derselben
    # Ebene z = 0, lässt OCC beide als lose Körper stehen (2 Solids, invalid).
    shaft = (cyl(r_core, -0.3, THREAD_L)
             .fuse(thread_solid(d, p, 0.0, THREAD_L))
             .intersect(cyl(d / 2 + BORE_OVERLAP, -0.35, THREAD_L - LEAD_IN).fuse(
                 cone(d / 2 + BORE_OVERLAP, d / 2 - LEAD_IN, THREAD_L - LEAD_IN, THREAD_L))))

    # Kopf: Bund, Hals, Kuppe (Rotationskörper), leicht in den Sechskant hinein
    z_collar = -HEX_H - COLLAR_L
    z_neck = z_collar - NECK_L
    z_top = z_neck - DOME_H
    r_d, r_t = DOME_D / 2, DOME_TOP_D / 2
    z_arc0 = z_neck - DOME_STRAIGHT
    # Kreisbogen von (r_d, z_arc0) tangential senkrecht startend nach (r_t, z_top)
    dz = z_top - z_arc0
    R = ((r_d - r_t) ** 2 + dz ** 2) / (2 * (r_d - r_t))
    cx = r_d - R
    a0, a1 = 0.0, math.atan2(dz, r_t - cx)
    am = (a0 + a1) / 2
    mid = (cx + R * math.cos(am), z_arc0 + R * math.sin(am))
    head = (cq.Workplane('XZ')
            .moveTo(0, -HEX_H + 0.05).lineTo(COLLAR_D / 2, -HEX_H + 0.05)
            .lineTo(COLLAR_D / 2, z_collar).lineTo(NECK_D / 2, z_collar)
            .lineTo(NECK_D / 2, z_neck).lineTo(r_d, z_neck).lineTo(r_d, z_arc0)
            .threePointArc(mid, (r_t, z_top)).lineTo(0, z_top).close()
            .revolve(360, (0, 0, 0), (0, 1, 0)).val())
    dimple = cq.Solid.makeSphere(DIMPLE_D / 2,
                                 cq.Vector(0, 0, z_top - DIMPLE_D / 2 + DIMPLE_DEPTH))
    return hexagon.fuse(shaft).fuse(head).cut(dimple)


def build_washer():
    """Sprengring als Rechteckprofil, entlang einer Schraubenlinie gesweept.

    Höhe der Helix = axialer Versatz der Enden; die Lücke bleibt am Umfang
    offen. Unterster Punkt bei z = 0, +z wie beim Stift (zur Gewindespitze).
    """
    r_in, r_out = WASHER_ID / 2, WASHER_OD / 2
    r_m = (r_in + r_out) / 2
    turn = (360 - WASHER_GAP_DEG) / 360
    pitch = WASHER_RISE / turn
    spine = cq.Workplane('XY').add(cq.Wire.makeHelix(pitch, WASHER_RISE, r_m))
    prof = cq.Workplane('XZ').center(r_m, 0).rect(r_out - r_in, WASHER_T)
    ring = prof.sweep(spine, isFrenet=True).val()
    return ring.translate(cq.Vector(0, 0, WASHER_T / 2))


def report(body, out):
    body.exportStep(str(out))
    bb = body.BoundingBox()
    print(f'Wrote {out}')
    print(f'  valid={body.isValid()} solids={len(body.Solids())} faces={len(body.Faces())} '
          f'volume={body.Volume():.2f} mm^3')
    print(f'  bbox x[{bb.xmin:.3f},{bb.xmax:.3f}] y[{bb.ymin:.3f},{bb.ymax:.3f}] '
          f'z[{bb.zmin:.3f},{bb.zmax:.3f}]')


def main():
    report(build_pin(), BASE / f'{PIN_NAME}.step')
    report(build_washer(), BASE / f'{WASHER_NAME}.step')


if __name__ == '__main__':
    main()
