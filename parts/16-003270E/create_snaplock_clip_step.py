"""SnapLock-Clip aus dem CONEC/Amphenol-Haubensatz 16-003270E als STEP-Solid.

Der Satz (Kunststoffhaube 25-pol. mit Schnellverriegelung, Zeichnung
16K1A4424) enthält zwei Federclips aus Edelstahl, die für den SD-AC1-DS in
das gedruckte Adaptergehäuse eingesetzt werden. CONEC liefert für den Clip
keine CAD-Daten; die Geometrie ist aus der Haubenzeichnung abgegriffen
(Datenblatt im selben Ordner):

  Ansicht ohne Deckel   Schnitt durch die Raststift-Achse — Profil des
                        Clips samt Zunge, dazu der Raststift im Eingriff
  Seitenansicht         Clip von vorn — Fenster, Zunge, Lappen
  Vorderansicht         Überstand über die Seitenwand, Unterkante Schenkel

Maßstab der Zeichnung 1,5:1 auf A3, als A4-PDF gedruckt, also 25,0 px/mm
bei 600 dpi (geeicht an 55,4 / 41,5 / 15,4). Ablesegenauigkeit etwa 0,1 mm.
Abgleich Modell gegen Zeichnung: check_against_drawing.py.

  .venv/bin/python parts/16-003270E/create_snaplock_clip_step.py

Bezugssystem (mm): Ursprung auf der Achse des Raststifts, z = 0 an der
Unterseite des Fußes (tiefster Punkt des Clips), +z zum Haubeninneren
(= Steckrichtung, der Stift zeigt nach +z), +x nach außen durch die
Haubenwand, y quer. Der Clip ist zu y = 0 symmetrisch. In der CONEC-Haube
liegt die 54,4-mm-Seitenwand bei x = 3,7; der Clip steht mit dem
Außenschenkel etwa 1,1 mm darüber hinaus.

Aufbau des Blechteils (t = 0,5):
  Fuß            waagerecht, läuft 1,3 mm über die Stiftachse hinaus und trägt
                 einen 2,5 mm breiten Gabelschlitz (nach innen offen): die
                 beiden Gabelarme schnappen beim Aufstecken über die Kuppe
                 des Raststifts (Ø 3,0) und sitzen dann in seinem Hals
                 (Ø 2,6) — das ist die SnapLock-Verriegelung. FOOT_VARIANT
                 'short' baut stattdessen den kurzen Fuß bis x = 2,85 ohne
                 Schlitz (frühere Lesart; siehe README)
  Bogen          90 Grad, Innenradius 0,2
  Außenschenkel  leicht geneigt (1,8 Grad, unten weiter außen); unten als
                 Lappen 5,1 breit, ab z = 1,75 volle Breite 11,6
  Fenster        5,6 breit, Ecken R 1,45, z = 2,95 … 13,0
  Zunge          3,5 breit, hängt vom Steg herab, ab z = 9,4 um 4,8 Grad
                 nach innen geneigt, Spitze z = 3,65; sie berührt den Stift
                 nicht (zwischen Zungenschlitz und Stiftbohrung liegt in der
                 Haube eine geschlossene Wand), sondern federt den Clip im
                 Wandschlitz vor
  Kröpfung       45 Grad, 1,56 nach innen, z = 10,3 … 11,8
  Oberteil       senkrecht im Wandschlitz, Oberkante z = 14,6

Durch die Wand verdeckt und deshalb angenommen: das obere Fensterende
(z = 13,0) und damit die Steghöhe (1,6), außerdem Breite und geschlossenes
Ende des Gabelschlitzes (Schlitz 2,5 = Halsdurchmesser minus Vorspannung,
Ende bei x = 3,4 direkt vor dem Bogen, damit die Arme lang und weich
sind). Die Zungenspitze ist glatt modelliert; die Zeichnung deutet dort
eine kleine Nase nach innen an.
"""
import math
from pathlib import Path

import cadquery as cq

BASE = Path(__file__).resolve().parent
NAME = 'CONEC_16-003270E_SnapLock_Clip'
PART_NAME = 'SnapLock-Clip 16-003270E'     # Bauteilname in Onshape
STAINLESS = (0.75, 0.76, 0.78)


def export_named(body, out, name, rgb):
    """STEP mit Bauteilname und Farbe schreiben.

    Shape.exportStep() schreibt kein PRODUCT mit Namen — Onshape nennt das
    Teil dann „Part 1". Der Umweg über eine einteilige Assembly legt Name
    und Farbe im STEP ab (Onshape übernimmt beides).
    """
    assy = cq.Assembly(body, name=name, color=cq.Color(*rgb))
    if hasattr(assy, 'export'):
        assy.export(str(out))
    else:
        assy.save(str(out), exportType='STEP')

T = 0.50            # Blechdicke
W = 11.60           # Breite Schenkel/Oberteil
W_TAB = 5.10        # Breite Lappen und Fuß
Z_TAB = 1.75        # Unterkante des breiten Schenkels
R_LEG = 0.90        # Ecken Unterkante Schenkel
R_TAB = 0.30        # Hohlkehle Lappen/Schenkel
SLOT_W, SLOT_Z0, SLOT_Z1, SLOT_R = 5.60, 2.95, 13.00, 1.45
TONGUE_W, TONGUE_R = 3.50, 0.30
Z_TOP = 14.60
FOOT_VARIANT = 'fork'            # 'fork' (Gabelfuß über die Stiftachse) | 'short'
FOOT_END = {'fork': -1.30, 'short': 2.85}[FOOT_VARIANT]
FORK_W, FORK_X_END = 2.50, 3.40  # Schlitzbreite; geschlossenes Ende (x der Stirn)

# Mittellinie der Schenkel (x, z) mit Biegeradius je Ecke (Mittellinie).
# Der Schenkel ist um 1,8 Grad geneigt; sein Fußpunkt P1 ist der Schnitt der
# Schenkelgeraden mit der Fußmittellinie z = 0,25.
LEG_TOP, LEG_BOT = (4.30, 10.30), (4.60, 0.70)
_k = (LEG_BOT[0] - LEG_TOP[0]) / (LEG_BOT[1] - LEG_TOP[1])
RAIL = [(FOOT_END, 0.25),
        (LEG_BOT[0] + (0.25 - LEG_BOT[1]) * _k, 0.25),   # Fuß → Schenkel
        LEG_TOP,                                          # Schenkel → Kröpfung
        (2.72, 11.80),                                    # Kröpfung → Oberteil
        (2.72, Z_TOP)]
RAIL_R = [0.45, 0.45, 0.45]
TONGUE = [(2.72, 13.90), (2.72, 9.40), (2.32, 3.65)]
TONGUE_RAD = [3.0]


def _unit(a, b):
    dx, dy = b[0] - a[0], b[1] - a[1]
    n = math.hypot(dx, dy)
    return dx / n, dy / n


def sheet_profile(pts, radii, t):
    """Geschlossene Kontur eines Blechs der Dicke t entlang einer
    Mittellinie aus Geraden mit Biegeradien an den Innenecken.

    Liefert eine Liste von ('line', p) / ('arc', mid, end)-Schritten, die
    mit moveTo(start) beginnt. Beide Seiten werden um t/2 versetzt; an den
    Bögen bleibt der Mittelpunkt, der Radius wird je Seite größer oder
    kleiner — so entstehen echte konzentrische Zylinderflächen.
    """
    n = len(pts)
    corners = []                                   # (A, B, C, r, s) je Ecke
    for i in range(1, n - 1):
        d_in, d_out = _unit(pts[i - 1], pts[i]), _unit(pts[i], pts[i + 1])
        cross = d_in[0] * d_out[1] - d_in[1] * d_out[0]
        s = 1.0 if cross > 0 else -1.0             # +1: Linkskurve
        theta = math.acos(max(-1.0, min(1.0, d_in[0] * d_out[0] + d_in[1] * d_out[1])))
        r = radii[i - 1]
        L = r * math.tan(theta / 2)
        A = (pts[i][0] - d_in[0] * L, pts[i][1] - d_in[1] * L)
        B = (pts[i][0] + d_out[0] * L, pts[i][1] + d_out[1] * L)
        n_in = (-d_in[1], d_in[0])                 # linke Normale
        C = (A[0] + n_in[0] * r * s, A[1] + n_in[1] * r * s)
        corners.append((A, B, C, r, s, d_in, d_out))

    def side(sign):
        """Versetzte Kontur einer Seite: sign=+1 links der Laufrichtung."""
        d0 = _unit(pts[0], pts[1])
        n0 = (-d0[1], d0[0])
        steps = [('start', (pts[0][0] + n0[0] * sign * t / 2,
                            pts[0][1] + n0[1] * sign * t / 2))]
        for A, B, C, r, s, d_in, d_out in corners:
            n_in, n_out = (-d_in[1], d_in[0]), (-d_out[1], d_out[0])
            ra = r - s * sign * t / 2              # Radius dieser Seite
            a = (A[0] + n_in[0] * sign * t / 2, A[1] + n_in[1] * sign * t / 2)
            b = (B[0] + n_out[0] * sign * t / 2, B[1] + n_out[1] * sign * t / 2)
            # Bogenmitte auf der Winkelhalbierenden, gleicher Mittelpunkt
            bis = _unit(C, ((A[0] + B[0]) / 2, (A[1] + B[1]) / 2))
            m = (C[0] + bis[0] * ra, C[1] + bis[1] * ra)
            steps.append(('line', a))
            steps.append(('arc', m, b))
        dl = _unit(pts[-2], pts[-1])
        nl = (-dl[1], dl[0])
        steps.append(('line', (pts[-1][0] + nl[0] * sign * t / 2,
                               pts[-1][1] + nl[1] * sign * t / 2)))
        return steps

    left, right = side(+1), side(-1)
    # links vorwärts, Endkappe, rechts rückwärts, Startkappe
    out = [left[0]] + left[1:]
    rev = []
    r_pts = right
    # rechte Seite rückwärts ablaufen: Schritte umkehren
    pos = [st[-1] for st in r_pts]                 # Endpunkte je Schritt
    out.append(('line', pos[-1]))
    for i in range(len(r_pts) - 1, 0, -1):
        st = r_pts[i]
        prev_end = pos[i - 1]
        if st[0] == 'line':
            rev.append(('line', prev_end))
        else:
            rev.append(('arc', st[1], prev_end))
    out += rev
    out.append(('close', None))
    return out


def profile_solid(pts, radii, t, width):
    """Blechkontur in der xz-Ebene, symmetrisch um y = 0 auf width extrudiert."""
    steps = sheet_profile(pts, radii, t)
    wp = cq.Workplane('XZ').moveTo(*steps[0][1])
    for kind, *args in steps[1:]:
        if kind == 'line':
            wp = wp.lineTo(*args[0])
        elif kind == 'arc':
            wp = wp.threePointArc(args[0], args[1])
        else:
            wp = wp.close()
    return wp.extrude(width / 2, both=True).val()


def face_stencil():
    """Umriss des Clips von vorn (yz), als Körper durch x hindurch.

    Lappen 5,1 breit bis z = 1,75, darüber voller Schenkel 11,6 breit mit
    R 0,9 an den unteren Ecken und R 0,3 in der Hohlkehle zum Lappen. Oben
    offen (das Oberteil endet über das Profil bei z = 14,6).
    """
    hw, ht = W / 2, W_TAB / 2
    z0, z1 = -0.5, Z_TOP + 1.0
    c = 0.70710678
    wp = (cq.Workplane('YZ').moveTo(-ht, z0)
          .lineTo(-ht, Z_TAB - R_TAB)
          .threePointArc((-ht - R_TAB + R_TAB * c, Z_TAB - R_TAB + R_TAB * c),
                         (-ht - R_TAB, Z_TAB))
          .lineTo(-hw + R_LEG, Z_TAB)
          .threePointArc((-hw + R_LEG - R_LEG * c, Z_TAB + R_LEG - R_LEG * c),
                         (-hw, Z_TAB + R_LEG))
          .lineTo(-hw, z1).lineTo(hw, z1).lineTo(hw, Z_TAB + R_LEG)
          .threePointArc((hw - R_LEG + R_LEG * c, Z_TAB + R_LEG - R_LEG * c),
                         (hw - R_LEG, Z_TAB))
          .lineTo(ht + R_TAB, Z_TAB)
          .threePointArc((ht + R_TAB - R_TAB * c, Z_TAB - R_TAB + R_TAB * c),
                         (ht, Z_TAB - R_TAB))
          .lineTo(ht, z0).close())
    body = wp.extrude(12).translate((-2, 0, 0)).val()
    slot = (cq.Workplane('YZ', origin=(-2, 0, 0))
            .center(0, (SLOT_Z0 + SLOT_Z1) / 2)
            .rect(SLOT_W, SLOT_Z1 - SLOT_Z0).extrude(12)
            .edges('|X').fillet(SLOT_R).val())
    return body.cut(slot)


def tongue_stencil():
    hw = TONGUE_W / 2
    z0 = TONGUE[-1][1]
    body = (cq.Workplane('YZ', origin=(-2, 0, 0))
            .center(0, (z0 + Z_TOP) / 2).rect(TONGUE_W, Z_TOP - z0).extrude(12))
    tip_edges = body.edges('|X').edges(
        cq.selectors.BoxSelector((-3, -hw - 0.1, z0 - 0.1), (11, hw + 0.1, z0 + 0.1)))
    return tip_edges.fillet(TONGUE_R).val()


def fork_slot():
    """Gabelschlitz im Fuß: nach innen offen, halbrund geschlossen bei x = FORK_X_END."""
    r = FORK_W / 2
    length = FORK_X_END - r - (FOOT_END - 1.0)
    return (cq.Workplane('XY', origin=(0, 0, -0.5))
            .center(FORK_X_END - r - length / 2, 0)
            .slot2D(length + FORK_W, FORK_W).extrude(1.0)
            .cut(cq.Workplane('XY', origin=(0, 0, -0.6)).center(FOOT_END - 3.0, 0)
                 .rect(4.0, 6.0).extrude(1.2))      # offenes Ende nicht abrunden
            .val())


def build():
    rails = profile_solid(RAIL, RAIL_R, T, W).intersect(face_stencil())
    if FOOT_VARIANT == 'fork':
        rails = rails.cut(fork_slot())
    tongue = profile_solid(TONGUE, TONGUE_RAD, T, TONGUE_W).intersect(tongue_stencil())
    return rails.fuse(tongue).clean()


def step_path():
    return BASE / f'{NAME}.step'


def main():
    body = build()
    out = step_path()
    export_named(body, out, PART_NAME, STAINLESS)
    bb = body.BoundingBox()
    print(f'Wrote {out}')
    print(f'  valid={body.isValid()} solids={len(body.Solids())} '
          f'faces={len(body.Faces())} volume={body.Volume():.2f} mm^3 '
          f'(~{body.Volume() * 7.9e-3:.2f} g Edelstahl)')
    print(f'  bbox x[{bb.xmin:.3f},{bb.xmax:.3f}] y[{bb.ymin:.3f},{bb.ymax:.3f}] '
          f'z[{bb.zmin:.3f},{bb.zmax:.3f}]')


if __name__ == '__main__':
    main()
