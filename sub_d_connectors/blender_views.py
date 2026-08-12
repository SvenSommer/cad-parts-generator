"""Vier Kontrollansichten eines Bauteils rendern (Blender, headless).

Aufruf:
  blender --background --python blender_views.py -- <stl> <out_dir> <stem>

Erzeugt <out_dir>/<stem>_{front,rear,side,iso}.png, orthografisch (keine
perspektivische Verzerrung, Kanten bleiben vergleichbar). Jede Ansicht fuellt
ihr eigenes Bild — die Massangaben stehen im Kontrollblatt daneben.

Weisser Grund und Onshape-Blau wie die Materialbilder in
../sdlink-videos/blender/part_volume_still.py, aber mit Freestyle-Konturen
statt Workbench-Cavity: zur Kontrolle muss die Trapezkontur auch in der
frontalen Ansicht lesbar sein, und dort liegen Schale und Flansch in derselben
Ebene zur Kamera — Cavity zeichnet sie nur als kaum sichtbaren Schemen.
"""
import bpy
import os
import sys
from mathutils import Euler, Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
STL, OUT_DIR, STEM = argv[0], argv[1], argv[2]
os.makedirs(OUT_DIR, exist_ok=True)

ONSHAPE_BLUE = (0.086275, 0.317647, 0.690196, 1.0)

# (Name, Blickrichtung Kamera -> Objekt, Bild-Vertikale in Weltkoordinaten)
# CAD-Frame: +z zeigt von der Steckflaeche zu den Loetstiften, +y = breite
# Seite des D. Die Steckseite sieht man also von -z aus.
# Ueberall +y nach oben, damit die breite Seite des Trapezes in jeder Ansicht
# oben liegt und sich die Bilder untereinander vergleichen lassen.
VIEWS = [
    ("front", (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    ("iso", (0.75, -0.55, 1.0), (0.0, 1.0, 0.0)),
    ("rear", (-0.75, -0.55, -1.0), (0.0, 1.0, 0.0)),
    ("side", (1.0, 0.0, 0.0), (0.0, 1.0, 0.0)),
]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"
sc.unit_settings.length_unit = "MILLIMETERS"

# STL liegt in mm vor, die Szene rechnet in m: Skalierung ins Mesh einbrennen.
bpy.ops.wm.stl_import(filepath=STL, global_scale=0.001)
obj = [o for o in sc.objects if o.type == "MESH"][0]
obj.data.transform(obj.matrix_world)
obj.matrix_world.identity()

# Direkt aus den Vertices, nicht aus obj.bound_box: der Cache haengt nach dem
# Einbrennen noch am ungeskalierten Mesh und ist um den Faktor 1000 daneben —
# die Kamera stuende dann weit ausserhalb und das Bild bliebe leer.
co = [v.co for v in obj.data.vertices]
lo = Vector(min(c[i] for c in co) for i in range(3))
hi = Vector(max(c[i] for c in co) for i in range(3))
center, size = (lo + hi) / 2, hi - lo
print(f"BBOX_MM {[round(size[i] * 1000, 2) for i in range(3)]}")

world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
# Hellt die Schattenseiten auf. Der Wert faerbt auch den sichtbaren
# Hintergrund, deshalb wird transparent gerendert und der weisse Grund erst
# beim Zusammensetzen des Kontrollblatts untergelegt.
bg.inputs[1].default_value = 0.6

sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 48
sc.render.resolution_x = 1000
sc.render.resolution_y = 780
sc.render.film_transparent = True
sc.view_settings.view_transform = "Standard"

sc.render.use_freestyle = True
vl = sc.view_layers[0]
vl.use_freestyle = True
# Kleiner als der Default (134 Grad), sonst fehlen die flachen Absaetze am
# Steckergehaeuse; deutlich kleiner wuerde die Tesselierung der Rundungen als
# Linienraster durchschlagen.
vl.freestyle_settings.crease_angle = 1.4
lineset = vl.freestyle_settings.linesets.new("contours")
lineset.select_silhouette = True
lineset.select_crease = True
lineset.select_border = True
if lineset.linestyle is None:
    lineset.linestyle = bpy.data.linestyles.new("contour")
lineset.linestyle.color = (0.04, 0.09, 0.20)
lineset.linestyle.thickness = 1.2

mat = bpy.data.materials.new("part_blue")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
bsdf.inputs["Base Color"].default_value = ONSHAPE_BLUE
bsdf.inputs["Roughness"].default_value = 0.55
bsdf.inputs["Metallic"].default_value = 0.0
obj.data.materials.clear()
obj.data.materials.append(mat)

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.2
sc.collection.objects.link(sun)

cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
# Default clip_start (0,1 m) schneidet bei kleinen Teilen mitten durchs Mesh.
cam_data.clip_start = 0.0001
cam_data.clip_end = 10.0
cam = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam

for name, direction, up in VIEWS:
    d = Vector(direction).normalized()
    # Kamerabasis explizit aufbauen (lokal -Z = Blickrichtung, +Y = oben):
    # to_track_quat richtet die Up-Achse an der Welt-Z aus und wuerde das
    # Trapez je nach Ansicht auf den Kopf stellen.
    right = d.cross(Vector(up)).normalized()
    upv = right.cross(d).normalized()
    quat = Matrix((right, upv, -d)).transposed().to_quaternion()
    cam.location = center - d * size.length * 3.0
    cam.rotation_euler = quat.to_euler()
    # Licht wandert mit der Kamera (von schraeg oben links dahinter), sonst
    # bliebe die frontale Ansicht flach und die Rueckansicht im Gegenlicht.
    sun.rotation_euler = (quat @ Euler((0.55, -0.45, 0.0)).to_quaternion()).to_euler()
    # Ortho-Rahmen aus der Ausdehnung senkrecht zur Blickrichtung: jede Ansicht
    # nutzt das Bild aus, sonst waere die Seitenansicht eines DB37 (16 mm tief,
    # 69 mm breit) nur ein Strich.
    w = sum(abs(right[i]) * size[i] for i in range(3))
    h = sum(abs(upv[i]) * size[i] for i in range(3))
    aspect = sc.render.resolution_x / sc.render.resolution_y
    cam_data.ortho_scale = max(w, h * aspect) * 1.12
    sc.render.filepath = os.path.join(OUT_DIR, f"{STEM}_{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"VIEW_DONE {name} {sc.render.filepath}")
