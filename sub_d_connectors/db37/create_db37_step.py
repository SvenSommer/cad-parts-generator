import cadquery as cq
from pathlib import Path

# DB37 sub-D connectors (printable approximation) as STEP solids for CAD
# import (e.g. Onshape, which converts STEP to native Parasolid solids).
# All dimensions were taken from the drawings DB37-female.png / DB37-male.png,
# calibrated via the standard 63.5 mm mounting-hole spacing.
# Units: millimetres.
# Frame: z = 0 at the mating face, +z toward the solder pins.
#        +y = wide side of the D (the 19-contact row).

BASE = Path(__file__).resolve().parent
SLOPE = 0.174  # D-sub taper, ~10 deg per side
PITCH = 2.77
ROW_Y = 1.42
CONTACTS = ([((i - 9) * PITCH, ROW_Y) for i in range(19)]        # wide side
            + [((i - 8.5) * PITCH, -ROW_Y) for i in range(18)])

VARIANTS = {
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

def build(v):
    fl0, fl1 = v['flange']
    flange = (cq.Workplane("XY", origin=(0, 0, fl0))
              .rect(69.32, 12.55).extrude(fl1 - fl0)
              .edges("|Z").fillet(0.9).val())
    adds = [dtrap_prism(*s) for s in v['slabs']] + [flange]
    cup_r, cup0, cup1 = v['cups']
    tail_r, tip = v['tail']
    for cx, cy in CONTACTS:                        # solder tails, rounded tip
        adds += [cyl(cx, cy, cup_r, cup0, cup1),
                 cyl(cx, cy, tail_r, cup1 - 0.1, tip - tail_r),
                 ball(cx, cy, tip - tail_r, tail_r)]

    # Cavity must be cut before any contact pins are fused in, or it would
    # remove them again (they live inside the cavity).
    body = adds[0].fuse(*adds[1:], glue=False).clean()
    body = body.cut(dtrap_prism(*v['cavity'])).clean()

    if v['front_pins']:
        pr, ptip, pz1 = v['front_pins']
        pins = [s for cx, cy in CONTACTS
                for s in (cyl(cx, cy, pr, ptip + pr, pz1), ball(cx, cy, ptip + pr, pr))]
        body = body.fuse(*pins, glue=False).clean()

    cuts = [cyl(cx, 0.0, 1.50, fl0 - 0.1, fl1 + 0.1)  # mounting holes, dia 3.0
            for cx in (-31.75, 31.75)]
    if v['sockets']:
        sr, sz0, sz1 = v['sockets']
        cuts += [cyl(cx, cy, sr, sz0, sz1) for cx, cy in CONTACTS]
    return body.cut(*cuts).clean()

for name, v in VARIANTS.items():
    body = build(v)
    out = BASE / name / f'DB37_{name}_trapezoid.step'
    body.exportStep(str(out))
    bb = body.BoundingBox()
    print(f'Wrote {out}')
    print(f'  valid={body.isValid()} solids={len(body.Solids())} '
          f'volume={body.Volume():.0f} mm^3')
    print(f'  bbox x[{bb.xmin:.3f},{bb.xmax:.3f}] y[{bb.ymin:.3f},{bb.ymax:.3f}] '
          f'z[{bb.zmin:.3f},{bb.zmax:.3f}]')
