import cadquery as cq
from pathlib import Path

# Sub-D (D-subminiature) connectors, standard density, as STEP solids for CAD
# import (e.g. Onshape, which converts STEP to native Parasolid solids).
# Units: millimetres.
# Frame: z = 0 at the mating face, +z toward the solder pins.
#        +y = wide side of the D (the row with the most contacts).
#
# The DC-37 (colloquially "DB37") geometry below was measured off the drawings
# db37/*/DB37-*.png and calibrated via the standard 63.5 mm mounting-hole
# spacing.  Every other shell size is derived from it: across the whole family
# the depth profile, wall thicknesses, taper and contact geometry are identical
# — only the shell WIDTH changes (and, for the DD shell, its HEIGHT, because it
# carries a third contact row).  So each size only needs two offsets, dw/dh,
# applied to the reference shell.
#
# Shell dimensions per MIL-DTL-24308 / DIN 41652, cross-checked against two
# independent vendor tables (Amphenol/FCI and Konmek), which agree to <0.1 mm:
#
#   shell  flange len A   mount holes C   shell width B   flange h E   shell h D
#   DE       30.81           24.99          16.92           12.55        8.36
#   DA       39.14           33.32          25.25           12.55        8.36
#   DB       53.04           47.04          38.96           12.55        8.36
#   DC       69.32           63.50          55.42           12.55        8.36
#   DD       66.93           61.11          52.81           15.37       11.07
#
# dw is the B-delta against DC, dh the D-delta — both taken from that table.

BASE = Path(__file__).resolve().parent
SLOPE = 0.174   # D-sub taper, ~10 deg per side
PITCH = 2.77    # contact pitch within a row (.109")
ROW_PITCH = 2.84  # row-to-row spacing (.112")

# High-density variants (HD / "DE15HD", "DA26HD", ...): SAME shells as the
# standard-density family, but three contact rows on a finer grid, and the
# contacts themselves are thinner (0.76 instead of 1.02 mm pin diameter).
# Grid per MIL-DTL-24308 high density:
HD_PITCH = 2.286      # .090" within a row
HD_ROW_PITCH = 1.981  # .078" row to row
HD_CONTACT = 0.745    # radius factor against the standard-density contact

# Reference geometry: DC-37 shell, measured from the drawings.
REF = {
    'female': dict(
        slabs=[                       # D-trapezoid stack: (H, Wc, r, z0, z1)
            (7.88, 53.83, 1.0, 0.0, 5.49),    # shell tube
            (8.98, 54.80, 1.0, 5.49, 5.98),   # flare
            (11.78, 56.93, 1.0, 7.02, 7.51),  # rear rolled rim
            (10.75, 55.88, 1.0, 7.51, 9.71),  # rear body steps
            (8.73, 53.92, 1.0, 9.71, 10.50),
            (6.78, 51.85, 1.0, 10.50, 11.48),
        ],
        flange=(5.98, 7.02),
        cavity=(6.90, 52.73, 0.8, -0.2, 0.4),  # recess to insulator face
        sockets=(0.52, 0.3, 5.4),              # r, z0, z1 (hole depth)
        front_pins=None,
        cups=(0.52, 11.48, 11.97),             # r, z0, z1
        tail=(0.29, 15.97),                    # solder pin r, rounded tip z
    ),
    'male': dict(
        slabs=[
            (9.29, 55.35, 1.2, 0.0, 5.50),    # shell skirt
            (10.26, 56.32, 1.0, 5.50, 5.99),  # flare
            (11.81, 56.81, 1.0, 6.97, 7.54),  # rear rolled rim
            (10.83, 55.84, 1.0, 7.54, 9.65),  # rear body steps
            (9.45, 54.53, 1.0, 9.65, 10.14),
            (8.80, 53.89, 1.0, 10.14, 10.47),
            (6.76, 51.77, 1.0, 10.47, 11.53),
        ],
        flange=(5.99, 6.97),
        cavity=(8.31, 54.29, 0.9, -0.2, 5.50),  # full shell cavity
        sockets=None,
        front_pins=(0.475, 0.6, 5.6),          # r, tip z, embedded end z
        cups=(0.50, 11.53, 11.98),
        tail=(0.31, 15.97),
    ),
}

# Zweite Bauform: Kabelstecker mit Loetkelch (MH Connectors MHDM-Serie,
# z.B. MHDM9SP — gedrehte Kontakte, 5A, Blechschale). Gegenueber REF oben ein
# anderer Aufbau, keine Parametervariante davon: duenne Blechschale statt
# gestuftem Kunststoffkoerper, dahinter ein Isolatorblock, und statt der langen
# Loetstifte kurze Kelche zum Anloeten der Litzen. Bautiefe darum nur 13,5 statt
# 15,97 mm. Masse aus dem Datenblatt MHDM SP Rev. 1.0, Bezugsgroesse DC-37:
#   A Schale 55.42 · B Loecher 63.50 · C Flansch 69.32 · D Koerper hinten 57.71
#   E Blech 1.0 · F Steckflaeche->Isolator hinten 10.8 · G Kelch 2.7
#   H Steckflaeche->Flansch 5.84
# Die Spalten A/B/C des Datenblatts decken sich exakt mit den Normmassen in
# SHELLS, deshalb tragen beide Bauformen dieselben dw/dh.
# Breiten hier als Bmax (breite Seite des Trapezes) wie im Datenblatt notiert,
# nicht als Wc — bmax_profile() rechnet um.
SOLDERCUP = dict(
    shell=(8.36, 55.42, 1.0, 0.0, 5.84),      # H, Bmax, r, z0, z1
    shell_bore=(7.56, 54.62, 0.8, -0.2, 5.84),  # Blechstaerke 0,40 ringsum
    flange=(5.84, 6.84),
    rear=(10.72, 57.71, 1.2, 6.84, 10.80),
    # Der Isolator fuellt nur den hinteren Teil des Blechrohrs; davor bleibt der
    # Steckbereich hohl, damit die Stifte frei stehen (hier 3,4 mm).
    insulator=(7.16, 54.22, 0.8, 4.40, 6.84),
    front_pins=(0.475, 0.55, 7.0),              # r, Spitze z, eingebettetes Ende
    cups=(0.70, 0.50, 10.80, 13.50),            # r aussen, r Bohrung, z0, z1
)

# Bauformen je Schalengroesse. Die MHDM-Loetkelchserie gibt es fuer 9/15/25/37/50;
# erzeugt wird, was gebraucht wurde.
DEFAULT_FORMS = ('female', 'male')
FORMS = {'de9': ('female', 'male', 'male_soldercup')}

# rows: contacts per row, wide side of the D first.
SHELLS = {
    'de9':  dict(name='DE9',  rows=(5, 4),      flange_len=30.81, holes=24.99,
                 flange_h=12.55, dw=-38.50, dh=0.0),
    'da15': dict(name='DA15', rows=(8, 7),      flange_len=39.14, holes=33.32,
                 flange_h=12.55, dw=-30.17, dh=0.0),
    'db25': dict(name='DB25', rows=(13, 12),    flange_len=53.04, holes=47.04,
                 flange_h=12.55, dw=-16.46, dh=0.0),
    'db37': dict(name='DB37', rows=(19, 18),    flange_len=69.32, holes=63.50,
                 flange_h=12.55, dw=0.0, dh=0.0),
    'dd50': dict(name='DD50', rows=(17, 16, 17), flange_len=66.93, holes=61.11,
                 flange_h=15.37, dw=-2.61, dh=2.71),
    # --- High density: same shells as DE/DA, three rows on the HD grid.
    # Row counts and numbering from the device manuals that use them
    # (AIR Avionics ACD-57: 1-5 / 6-10 / 11-15; AIR COM AC-1 connector 1:
    # 1-9 / 10-18 / 19-26). Adjacent rows sit half a pitch apart, so the
    # contacts nest — that is what makes the HD grid fit the same shell.
    'de15hd': dict(name='DE15HD', rows=(5, 5, 5), flange_len=30.81, holes=24.99,
                   flange_h=12.55, dw=-38.50, dh=0.0,
                   pitch=HD_PITCH, row_pitch=HD_ROW_PITCH,
                   row_off=(0.0, 0.5, 0.0), contact=HD_CONTACT),
    'da26hd': dict(name='DA26HD', rows=(9, 9, 8), flange_len=39.14, holes=33.32,
                   flange_h=12.55, dw=-30.17, dh=0.0,
                   pitch=HD_PITCH, row_pitch=HD_ROW_PITCH,
                   row_off=(0.0, 0.5, 0.0), contact=HD_CONTACT),
}


def contacts(shell):
    """Contact centres in mm, wide side of the D at +y.

    Standard density: every row centred on x = 0 — with counts like 13/12 that
    already staggers the rows. High density needs the offsets spelled out
    (`row_off`, in pitch units), because there two rows can carry the SAME
    number of contacts and would otherwise stack. The whole pattern is
    re-centred afterwards, so the connector stays symmetric.
    """
    if not isinstance(shell, dict):          # Altaufruf mit reiner rows-Liste
        shell = dict(rows=shell)
    rows = shell['rows']
    pitch = shell.get('pitch', PITCH)
    row_pitch = shell.get('row_pitch', ROW_PITCH)
    offs = shell.get('row_off') or (0.0,) * len(rows)
    top = (len(rows) - 1) / 2
    pts = [((i - (n - 1) / 2 + offs[k]) * pitch, (top - k) * row_pitch)
           for k, n in enumerate(rows)
           for i in range(n)]
    mid = (min(p[0] for p in pts) + max(p[0] for p in pts)) / 2
    return [(x - mid, y) for x, y in pts]


def scale_contacts(v, factor):
    """Kontaktmasse einer Bauform skalieren (HD-Kontakte sind duenner)."""
    if factor == 1.0:
        return v
    out = dict(v)
    for key, idx in (('sockets', (0,)), ('front_pins', (0,)),
                     ('cups', (0,)), ('tail', (0,))):
        val = v.get(key)
        if val:
            out[key] = tuple(x * factor if i in idx else x
                             for i, x in enumerate(val))
    return out


def resize(profile, dw, dh):
    """(H, Wc, ...) with the shell grown by dh in height and dw in width.

    Wc is the trapezoid width at mid-height, so growing H alone would also
    widen the wide side by SLOPE * dh; that is subtracted out, leaving the
    wide-side width shifted by exactly dw.
    """
    H, Wc, *rest = profile
    return (H + dh, Wc + dw - SLOPE * dh, *rest)


def bmax_profile(profile, dw, dh):
    """(H, Bmax, ...) aus dem Datenblatt in ein resize-tes (H, Wc, ...) wandeln.

    Bmax ist die Breite an der breiten Seite des Trapezes, Wc die auf halber
    Hoehe; sie unterscheiden sich um die Verjuengung SLOPE * H.
    """
    H, bmax, *rest = profile
    return resize((H, bmax - SLOPE * H, *rest), dw, dh)


def dtrap_prism(H, Wc, r, z0, z1):
    """Extruded D-trapezoid, corners filleted. Wide side at +y."""
    hw = lambda yy: Wc / 2 + SLOPE * yy
    pts = [(-hw(-H / 2), -H / 2), (hw(-H / 2), -H / 2),
           (hw(H / 2), H / 2), (-hw(H / 2), H / 2)]
    wp = (cq.Workplane("XY", origin=(0, 0, z0))
          .polyline(pts).close().extrude(z1 - z0))
    return wp.edges("|Z").fillet(r).val()


def cyl(cx, cy, r, z0, z1):
    return cq.Solid.makeCylinder(r, z1 - z0, cq.Vector(cx, cy, z0))


def ball(cx, cy, cz, r):
    return cq.Solid.makeSphere(r, cq.Vector(cx, cy, cz), angleDegrees1=-90)


def build(v, shell):
    dw, dh = shell['dw'], shell['dh']
    v = scale_contacts(v, shell.get('contact', 1.0))
    pins = contacts(shell)
    fl0, fl1 = v['flange']
    flange = (cq.Workplane("XY", origin=(0, 0, fl0))
              .rect(shell['flange_len'], shell['flange_h']).extrude(fl1 - fl0)
              .edges("|Z").fillet(0.9).val())
    adds = [dtrap_prism(*resize(s, dw, dh)) for s in v['slabs']] + [flange]
    cup_r, cup0, cup1 = v['cups']
    tail_r, tip = v['tail']
    for cx, cy in pins:                            # solder tails, rounded tip
        adds += [cyl(cx, cy, cup_r, cup0, cup1),
                 cyl(cx, cy, tail_r, cup1 - 0.1, tip - tail_r),
                 ball(cx, cy, tip - tail_r, tail_r)]

    # Cavity must be cut before any contact pins are fused in, or it would
    # remove them again (they live inside the cavity).
    body = adds[0].fuse(*adds[1:], glue=False).clean()
    body = body.cut(dtrap_prism(*resize(v['cavity'], dw, dh))).clean()

    if v['front_pins']:
        pr, ptip, pz1 = v['front_pins']
        pins_3d = [s for cx, cy in pins
                   for s in (cyl(cx, cy, pr, ptip + pr, pz1),
                             ball(cx, cy, ptip + pr, pr))]
        body = body.fuse(*pins_3d, glue=False).clean()

    hx = shell['holes'] / 2
    cuts = [cyl(cx, 0.0, 1.50, fl0 - 0.1, fl1 + 0.1)  # mounting holes, dia 3.0
            for cx in (-hx, hx)]
    if v['sockets']:
        sr, sz0, sz1 = v['sockets']
        cuts += [cyl(cx, cy, sr, sz0, sz1) for cx, cy in pins]
    return body.cut(*cuts).clean()


def build_soldercup(v, shell):
    """Kabelstecker mit Loetkelch (MHDM-Bauform), Aufbau von vorn nach hinten."""
    dw, dh = shell['dw'], shell['dh']
    v = scale_contacts(v, shell.get('contact', 1.0))
    pins = contacts(shell)
    fl0, fl1 = v['flange']
    flange = (cq.Workplane("XY", origin=(0, 0, fl0))
              .rect(shell['flange_len'], shell['flange_h']).extrude(fl1 - fl0)
              .edges("|Z").fillet(0.9).val())

    # Blechschale zuerst aushoehlen: der Isolator sitzt in diesem Hohlraum und
    # wuerde beim Schnitt sonst gleich wieder verschwinden.
    shell_solid = dtrap_prism(*bmax_profile(v['shell'], dw, dh))
    shell_solid = shell_solid.cut(
        dtrap_prism(*bmax_profile(v['shell_bore'], dw, dh))).clean()

    body = shell_solid.fuse(
        flange,
        dtrap_prism(*bmax_profile(v['rear'], dw, dh)),
        dtrap_prism(*bmax_profile(v['insulator'], dw, dh)),
        glue=False).clean()

    pr, ptip, pz1 = v['front_pins']
    cup_r, bore_r, cup0, cup1 = v['cups']
    adds = []
    for cx, cy in pins:
        adds += [cyl(cx, cy, pr, ptip + pr, pz1), ball(cx, cy, ptip + pr, pr),
                 cyl(cx, cy, cup_r, cup0, cup1)]
    body = body.fuse(*adds, glue=False).clean()

    hx = shell['holes'] / 2
    cuts = [cyl(cx, 0.0, 1.525, fl0 - 0.1, fl1 + 0.1)  # Schraubloecher, dia 3,05
            for cx in (-hx, hx)]
    cuts += [cyl(cx, cy, bore_r, cup0 + 0.1, cup1 + 0.1) for cx, cy in pins]
    return body.cut(*cuts).clean()


BUILDERS = {
    'female': (REF['female'], build),
    'male': (REF['male'], build),
    'male_soldercup': (SOLDERCUP, build_soldercup),
}


def step_path(key, form):
    return BASE / key / form / f"{SHELLS[key]['name']}_{form}_trapezoid.step"


def main():
    for key, shell in SHELLS.items():
        for form in FORMS.get(key, DEFAULT_FORMS):
            v, builder = BUILDERS[form]
            body = builder(v, shell)
            out = step_path(key, form)
            out.parent.mkdir(parents=True, exist_ok=True)
            body.exportStep(str(out))
            bb = body.BoundingBox()
            print(f'Wrote {out}')
            print(f'  valid={body.isValid()} solids={len(body.Solids())} '
                  f'volume={body.Volume():.0f} mm^3')
            print(f'  bbox x[{bb.xmin:.3f},{bb.xmax:.3f}] y[{bb.ymin:.3f},{bb.ymax:.3f}] '
                  f'z[{bb.zmin:.3f},{bb.zmax:.3f}]')


if __name__ == '__main__':
    main()
