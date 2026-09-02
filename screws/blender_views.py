"""Ansichten eines Schraubteils rendern (Blender, headless).

Aufruf:
  blender --background --python screws/blender_views.py -- <auftrag.json>

Der Auftrag beschreibt STL, Zielordner, Stil und Ansichten:
  {"stl": ..., "out_dir": ..., "stem": ..., "style": "cad"|"metal",
   "res": [w, h], "views": [{"name": ..., "dir": [...], "up": [...]}]}

Erzeugt <out_dir>/<stem>_<name>.png je Ansicht.

Zwei Stile: "cad" wie bei den Sub-D-Teilen (Onshape-Blau, orthografisch,
Freestyle-Konturen, transparenter Grund — der weisse Grund kommt erst beim
Zusammensetzen des Blattes) und "metal" fuer Produktbilder (vernickeltes
Messing wie in der Zeichnung, Studio-Licht, Verlaufsgrund).
"""
import json
import os
import sys

import bpy
from mathutils import Euler, Matrix, Vector

JOB = json.load(open(sys.argv[sys.argv.index("--") + 1:][0]))
STYLE = JOB.get("style", "cad")
os.makedirs(JOB["out_dir"], exist_ok=True)

ONSHAPE_BLUE = (0.086275, 0.317647, 0.690196, 1.0)
NICKEL = (0.807, 0.796, 0.769, 1.0)      # vernickeltes Messing, leicht warm

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
sc.unit_settings.system = "METRIC"
sc.unit_settings.length_unit = "MILLIMETERS"

# Szene in Millimetern statt Metern (scale_length stellt die Einheit richtig).
# Freestyle braucht das: bei einem 13-mm-Teil in Metern fallen alle Kanten
# unter seine internen Schwellen und es rendert "strokes set empty" — also
# gar keine Konturen. Alles Weitere haengt an der Bounding Box, nicht an der
# absoluten Groesse, und beleuchtet wird nur mit Welt und Sonnen, die
# entfernungsunabhaengig sind.
sc.unit_settings.scale_length = 0.001
bpy.ops.wm.stl_import(filepath=JOB["stl"], global_scale=1.0)
obj = [o for o in sc.objects if o.type == "MESH"][0]
obj.data.transform(obj.matrix_world)
obj.matrix_world.identity()
# Zylinder und Gewinde kommen tesselliert an: glatt schattieren, aber nur bis
# 35 Grad, sonst verschleifen Zahnflanken und Kopffasen zu Wuelsten.
bpy.context.view_layer.objects.active = obj
try:
    bpy.ops.object.shade_auto_smooth(angle=0.61)
except (AttributeError, RuntimeError):
    bpy.ops.object.shade_smooth()

# Direkt aus den Vertices, nicht aus obj.bound_box: der Cache haengt nach dem
# Einbrennen noch am ungeskalierten Mesh und ist um den Faktor 1000 daneben.
co = [v.co for v in obj.data.vertices]
lo = Vector(min(c[i] for c in co) for i in range(3))
hi = Vector(max(c[i] for c in co) for i in range(3))
center, size = (lo + hi) / 2, hi - lo
print(f"BBOX_MM {[round(size[i] * 1000, 2) for i in range(3)]}")

world = bpy.data.worlds.new("W")
sc.world = world
world.use_nodes = True
nt = world.node_tree
bg = nt.nodes["Background"]

sc.render.engine = "BLENDER_EEVEE"
sc.eevee.taa_render_samples = 96
sc.render.resolution_x, sc.render.resolution_y = JOB.get("res", [1000, 780])
sc.view_settings.view_transform = "Standard"

if STYLE == "cad":
    bg.inputs[0].default_value = (1.0, 1.0, 1.0, 1.0)
    # Hellt die Schattenseiten auf; faerbt auch den Grund, deshalb transparent
    # rendern und das Weiss erst im Blatt unterlegen.
    bg.inputs[1].default_value = 0.6
    sc.render.film_transparent = True
    sc.render.use_freestyle = True
    vl = sc.view_layers[0]
    vl.use_freestyle = True
    # Kleiner als der Default (134 Grad): sonst fehlen der Absatz unter dem
    # Kopf und die Kopffasen. Viel kleiner, und die Tesselierung der
    # Gewindeflanken schlaegt als Linienraster durch.
    vl.freestyle_settings.crease_angle = 1.2
    ls = vl.freestyle_settings.linesets.new("contours")
    ls.select_silhouette = ls.select_crease = ls.select_border = True
    if ls.linestyle is None:
        ls.linestyle = bpy.data.linestyles.new("contour")
    ls.linestyle.color = (0.04, 0.09, 0.20)
    # 2,2 px, nicht 1: auf transparentem Grund bleibt eine 1-px-Linie so
    # schwach antialiast, dass sie beim Unterlegen des weissen Grundes zu
    # hellem Blaugrau verwaschen wird — im Blatt sieht man dann keine Kontur.
    ls.linestyle.thickness = 2.2
else:
    # Studio-Verlauf als Umgebung: EEVEE spiegelt die Welt im Metall, vor einem
    # flachen Weiss sieht die Schraube aus wie aus Plastik. Der Verlauf laeuft
    # ueber die Welt-Z-Richtung (im World-Shader liefert "Generated" den
    # Blickvektor, -1..1, deshalb die Map Range davor).
    coord = nt.nodes.new("ShaderNodeTexCoord")
    sep = nt.nodes.new("ShaderNodeSeparateXYZ")
    remap = nt.nodes.new("ShaderNodeMapRange")
    remap.inputs["From Min"].default_value = -0.6
    remap.inputs["From Max"].default_value = 0.6
    ramp = nt.nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.elements[0].color = (0.055, 0.06, 0.075, 1.0)
    ramp.color_ramp.elements[1].color = (0.93, 0.94, 0.96, 1.0)
    nt.links.new(coord.outputs["Generated"], sep.inputs["Vector"])
    nt.links.new(sep.outputs["Z"], remap.inputs["Value"])
    nt.links.new(remap.outputs["Result"], ramp.inputs["Fac"])
    nt.links.new(ramp.outputs["Color"], bg.inputs[0])
    bg.inputs[1].default_value = 1.1
    sc.render.film_transparent = False
    if hasattr(sc.eevee, "use_raytracing"):
        sc.eevee.use_raytracing = True

mat = bpy.data.materials.new("part")
mat.use_nodes = True
bsdf = mat.node_tree.nodes["Principled BSDF"]
if STYLE == "cad":
    bsdf.inputs["Base Color"].default_value = ONSHAPE_BLUE
    bsdf.inputs["Roughness"].default_value = 0.55
    bsdf.inputs["Metallic"].default_value = 0.0
else:
    bsdf.inputs["Base Color"].default_value = NICKEL
    bsdf.inputs["Roughness"].default_value = 0.24
    bsdf.inputs["Metallic"].default_value = 1.0
obj.data.materials.clear()
obj.data.materials.append(mat)

# Nur Sonnen: ihre Helligkeit haengt nicht vom Abstand ab, das Bild bleibt
# also gleich belichtet, egal wie gross das Teil ist. Flaechenlichter waren
# hier zuerst drin und haben ein 13-mm-Teil komplett ausgebrannt.
sun = bpy.data.objects.new("Sun", bpy.data.lights.new("Sun", "SUN"))
sun.data.energy = 3.2 if STYLE == "cad" else 2.6
if STYLE == "metal":
    sun.data.angle = 0.20      # weiche, aber sichtbare Glanzkante
sc.collection.objects.link(sun)
# (Name, Richtung im Kamerasystem, Energie) — wandern mit der Kamera mit.
FILL = [("fill", (-0.9, 0.35, 0.3), 1.1), ("rim", (0.7, -0.2, -0.8), 1.8)] \
    if STYLE == "metal" else []
fills = []
for name, direction, energy in FILL:
    data = bpy.data.lights.new(name, "SUN")
    data.energy, data.angle = energy, 0.35
    lamp = bpy.data.objects.new(name, data)
    sc.collection.objects.link(lamp)
    fills.append((lamp, Vector(direction)))

cam_data = bpy.data.cameras.new("Cam")
cam_data.type = "ORTHO"
# Clip-Ebenen aus der Teilegroesse: der Default (0,1 bis 100) schneidet in
# Millimeter-Szenen mitten durchs Mesh oder kappt die Kamerastandpunkte.
cam_data.clip_start = size.length * 0.01
cam_data.clip_end = size.length * 20.0
cam = bpy.data.objects.new("Cam", cam_data)
sc.collection.objects.link(cam)
sc.camera = cam

for view in JOB["views"]:
    d = Vector(view["dir"]).normalized()
    # Kamerabasis explizit aufbauen (lokal -Z = Blickrichtung, +Y = oben):
    # to_track_quat richtet die Up-Achse an der Welt-Z aus und legt das Teil
    # je nach Ansicht auf die falsche Seite.
    right = d.cross(Vector(view["up"])).normalized()
    upv = right.cross(d).normalized()
    quat = Matrix((right, upv, -d)).transposed().to_quaternion()
    cam.location = center - d * size.length * 3.0
    cam.rotation_euler = quat.to_euler()
    # Licht wandert mit der Kamera, sonst steht eine Ansicht im Gegenlicht.
    # Vorzeichen der X-Drehung beachten: Die Sonne leuchtet entlang ihrer
    # lokalen -Z, +0.55 dreht die Lichtrichtung auf (0, +0.52, -0.85) — das
    # Licht scheint dann nach oben, kommt also von UNTEN. So steht es im
    # Sub-D-Vorbild, dessen Kommentar "von schraeg oben links" das Gegenteil
    # behauptet. Mit Licht von unten liest sich jede Vertiefung als Erhebung
    # (Sackloch, Senkung, Kreuzschlitz), weil das Auge Licht von oben annimmt.
    sun.rotation_euler = (quat @ Euler((-0.55, -0.45, 0.0)).to_quaternion()).to_euler()
    for lamp, direction in fills:
        # Sonnen leuchten entlang ihrer lokalen -Z: Richtung im Kamerasystem
        # aufbauen und mitdrehen, dann bleibt die Lichtfuehrung je Ansicht gleich.
        d_world = (quat @ direction).normalized()
        lamp.rotation_euler = d_world.to_track_quat("-Z", "Y").to_euler()
    # Ortho-Rahmen aus der Ausdehnung senkrecht zur Blickrichtung; die drei
    # Tafeln der Dreiseitenansicht bekommen stattdessen "span_mm", sonst waere
    # jede fuer sich formatfuellend und der Massstab zwischen ihnen dahin.
    w = sum(abs(right[i]) * size[i] for i in range(3))
    h = sum(abs(upv[i]) * size[i] for i in range(3))
    aspect = sc.render.resolution_x / sc.render.resolution_y
    span = view.get("span_mm") or max(w, h * aspect)   # Szene rechnet in mm
    cam_data.ortho_scale = span * view.get("pad", 1.12)
    sc.render.filepath = os.path.join(JOB["out_dir"], f'{JOB["stem"]}_{view["name"]}.png')
    bpy.ops.render.render(write_still=True)
    print(f'VIEW_DONE {view["name"]} {sc.render.filepath}')
