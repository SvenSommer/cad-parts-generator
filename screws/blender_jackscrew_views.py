"""Vier Kontrollansichten der Jack Screw rendern (Blender, headless).

Aufruf:
  blender --background --python blender_jackscrew_views.py -- \
      <kopf.stl> <schraube.stl> <out_dir> <stem>

Erzeugt <out_dir>/<stem>_{front,side,top,iso}.png, orthografisch. Gegenüber
sub_d_connectors/blender_views.py zwei Meshes mit eigenen Materialien
(grauer GF-Kunststoffkopf, vernickelter Stahl) und eine Orientierung wie auf
der Harting-Zeichnung: Kopf oben, Gewindespitze unten.
"""
import os
import sys

import bpy
from mathutils import Euler, Matrix, Vector

argv = sys.argv[sys.argv.index("--") + 1:]
HEAD_STL, SCREW_STL, OUT_DIR, STEM = argv[0], argv[1], argv[2], argv[3]
os.makedirs(OUT_DIR, exist_ok=True)

# CAD-Frame des Modells: z = 0 an der Kopfunterkante, +z zur Gewindespitze.
# Bild-Vertikale deshalb -z, dann steht die Schraube wie auf der Zeichnung.
# (Name, Blickrichtung Kamera -> Objekt, Bild-Vertikale in Weltkoordinaten)
VIEWS = [
    ("front", (0.0, 1.0, 0.0), (0.0, 0.0, -1.0)),
    ("side", (1.0, 0.0, 0.0), (0.0, 0.0, -1.0)),
    ("top", (0.0, 0.0, 1.0), (0.0, 1.0, 0.0)),
    ("iso", (0.66, 0.66, 0.48), (0.0, 0.0, -1.0)),
]

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"
sc.unit_settings.length_unit = "MILLIMETERS"


def load(stl):
    before = set(sc.objects)
    bpy.ops.wm.stl_import(filepath=stl, global_scale=0.001)
    obj = next(o for o in set(sc.objects) - before if o.type == "MESH")
    obj.data.transform(obj.matrix_world)
    obj.matrix_world.identity()
    # STL kommt flat-shaded an — auf den fein tesselierten Loft-Flächen des
    # Kreuzschlitzes gibt das körnige Facetten. Winkelbasiert glätten,
    # Rillen- und Schlitzkanten bleiben scharf.
    with bpy.context.temp_override(object=obj, active_object=obj,
                                   selected_editable_objects=[obj]):
        bpy.ops.object.shade_auto_smooth(angle=0.6)
    return obj


head, screw = load(HEAD_STL), load(SCREW_STL)

# Bounding-Box beider Teile aus den Vertices (siehe blender_views.py: der
# bound_box-Cache hängt nach dem Einbrennen am ungeskalierten Mesh).
co = [v.co for o in (head, screw) for v in o.data.vertices]
lo = Vector(min(c[i] for c in co) for i in range(3))
hi = Vector(max(c[i] for c in co) for i in range(3))
center, size = (lo + hi) / 2, hi - lo
print(f"BBOX_MM {[round(size[i] * 1000, 2) for i in range(3)]}")

world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
bg = world.node_tree.nodes["Background"]
bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
bg.inputs[1].default_value = 0.45  # Aufhellung; Grund kommt beim Komponieren
sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 48
sc.render.resolution_x = 560
sc.render.resolution_y = 1080
sc.render.film_transparent = True
sc.view_settings.view_transform = "Standard"

sc.render.use_freestyle = True
vl = sc.view_layers[0]
vl.use_freestyle = True
# Rändel und Kreuzschlitz sind fein tesseliert; ein größerer crease_angle als
# beim Sub-D, sonst werden die Rillenränder zum flächigen Linienraster.
vl.freestyle_settings.crease_angle = 1.75
lineset = vl.freestyle_settings.linesets.new("contours")
lineset.select_silhouette = True
lineset.select_crease = True
lineset.select_border = True
if lineset.linestyle is None:
    lineset.linestyle = bpy.data.linestyles.new("contour")
lineset.linestyle.color = (0.04, 0.09, 0.20)
lineset.linestyle.thickness = 1.0


def material(name, color, rough, metal):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes["Principled BSDF"]
    bsdf.inputs["Base Color"].default_value = color
    bsdf.inputs["Roughness"].default_value = rough
    bsdf.inputs["Metallic"].default_value = metal
    return mat


# Grauer 30%-GF-Thermoplast, matt und deutlich dunkler als der Stahl —
# vor der gleichmaessig weissen Welt bekommt reines Metall kaum
# Reflexionszeichnung, die Werkstofftrennung muss ueber den Helligkeits-
# und Glanzkontrast kommen.
head.data.materials.clear()
head.data.materials.append(material("gf_grey", (0.16, 0.165, 0.175, 1.0), 0.68, 0.0))
screw.data.materials.clear()
screw.data.materials.append(material("nickel", (0.82, 0.81, 0.78, 1.0), 0.24, 0.85))

sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.0
sc.collection.objects.link(sun)

cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
cam_data.clip_start = 0.0001
cam_data.clip_end = 10.0
cam = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam

for name, direction, up in VIEWS:
    d = Vector(direction).normalized()
    right = d.cross(Vector(up)).normalized()
    upv = right.cross(d).normalized()
    quat = Matrix((right, upv, -d)).transposed().to_quaternion()
    cam.location = center - d * size.length * 3.0
    cam.rotation_euler = quat.to_euler()
    # Licht im BILD von oben links, sonst kippt die Wahrnehmung des
    # Kreuzschlitzes in der Draufsicht ins Erhabene (Konkav/Konvex-
    # Taeuschung): mit dem Vorbild-Offset (+0.55 um X) faellt das Licht
    # von Bild-unten ein.
    sun.rotation_euler = (quat @ Euler((-0.55, -0.45, 0.0)).to_quaternion()).to_euler()
    w = sum(abs(right[i]) * size[i] for i in range(3))
    h = sum(abs(upv[i]) * size[i] for i in range(3))
    # ortho_scale wirkt auf die GROESSERE Aufloesungsdimension (sensor fit
    # AUTO) — hier Hochformat, also auf die Bildhoehe. Sichtbar sind
    # scale*min(1, aspect) in der Breite und scale*min(1, 1/aspect) in der
    # Hoehe; beide Anforderungen einrechnen (die Vorbildformel in
    # sub_d_connectors/blender_views.py deckt nur Querformat ab).
    aspect = sc.render.resolution_x / sc.render.resolution_y
    cam_data.ortho_scale = max(w / min(1.0, aspect),
                               h / min(1.0, 1.0 / aspect)) * 1.12
    sc.render.filepath = os.path.join(OUT_DIR, f"{STEM}_{name}.png")
    bpy.ops.render.render(write_still=True)
    print(f"VIEW_DONE {name} {sc.render.filepath}")
