"""Produktbild der SD-AC1-DS-Assembly aus Onshape (GLB), Cover oben, LED hervorgehoben.

  blender --background --python parts/16-003270E/render_assembly.py -- <glb> <out.png> [samples]

Nutzt das Studio-Setup aus ../sdlink-videos/blender/sdlib.py. Das GLB kommt
von prodflux/scripts/fetch_onshape_cases.py --gltf … assembly. Nach dem
glTF-Import liegt die Cover-Normale auf ±Y; das Modell wird so gedreht, dass
das Cover nach +Z zeigt. Zwei Kameras: Gesamtansicht schräg von oben und
eine Nahaufnahme der LED, die als Einsatz unten rechts eingesetzt wird.
"""
import os
import sys

import bpy
from mathutils import Vector

sys.path.insert(0, os.path.expanduser('~/dev/sdlink-videos/blender'))
import sdlib  # noqa: E402

argv = sys.argv[sys.argv.index('--') + 1:]
GLB, OUT = argv[0], argv[1]
SAMPLES = int(argv[2]) if len(argv) > 2 else 96

bpy.ops.wm.read_factory_settings(use_empty=True)
sc = bpy.context.scene
bpy.ops.import_scene.gltf(filepath=GLB)
meshes = [o for o in bpy.data.objects if o.type == 'MESH']


def center_of(objs):
    lo = Vector((1e9,) * 3); hi = Vector((-1e9,) * 3)
    for o in objs:
        for c in o.bound_box:
            w = o.matrix_world @ Vector(c)
            lo = Vector(map(min, lo, w)); hi = Vector(map(max, hi, w))
    return (lo + hi) / 2, hi - lo


cover = [o for o in meshes if o.name.startswith('Cover')]
body = [o for o in meshes if o.name.startswith('Body')]
c_cover, _ = center_of(cover); c_body, _ = center_of(body)
up_y = (c_cover - c_body).y
# Cover-Normale (±Y) nach +Z drehen: Rotation um X
import math  # noqa: E402
angle = math.pi / 2 if up_y > 0 else -math.pi / 2   # +90 Grad um X bildet +Y auf +Z ab
pivot = bpy.data.objects.new('pivot', None); sc.collection.objects.link(pivot)
for o in bpy.data.objects:
    if o.parent is None and o is not pivot:
        o.parent = pivot
pivot.rotation_euler = (angle, 0, 0)
bpy.context.view_layer.update()
center, size = center_of(meshes)
pivot.location = -center
bpy.context.view_layer.update()
center, size = center_of(meshes)
print(f'BBOX size=({size.x*1000:.1f}, {size.y*1000:.1f}, {size.z*1000:.1f}) mm')

# LED gruen leuchtend
led = [o for o in meshes if o.name.startswith('LED')]
mat = bpy.data.materials.new('LED gruen'); mat.use_nodes = True
bsdf = mat.node_tree.nodes['Principled BSDF']
bsdf.inputs['Base Color'].default_value = (0.45, 0.85, 0.15, 1)
bsdf.inputs['Emission Color'].default_value = (0.45, 0.9, 0.15, 1)
bsdf.inputs['Emission Strength'].default_value = 0.6
bsdf.inputs['Roughness'].default_value = 0.2
for o in led:
    o.data.materials.clear(); o.data.materials.append(mat)
    for poly in o.data.polygons:
        poly.use_smooth = True
c_led, _ = center_of(led)
print(f'LED bei ({c_led.x*1000:.1f}, {c_led.y*1000:.1f}, {c_led.z*1000:.1f}) mm')

sdlib.build_studio(sc)
sdlib.setup_cycles(sc, res=(1800, 1300), samples=SAMPLES)
reach = max(size) * 3.6
cam, _ = sdlib.build_camera(sc, (reach * 0.62, -reach * 0.62, reach * 0.5), (0.0, 0.0, -size.z * 0.1),
                            focal=80, name='Cam gesamt')
sdlib.render_still(sc, OUT)

# Nahaufnahme LED
sc.render.resolution_x, sc.render.resolution_y = 900, 700
d = max(size) * 0.4
top = (c_led.x, c_led.y, c_led.z + 0.0011)     # Kuppe der Linse
cam2, _ = sdlib.build_camera(sc, (top[0] + d * 0.45, top[1] - d * 0.55, top[2] + d * 0.6), top,
                             focal=135, name='Cam LED')
sdlib.render_still(sc, OUT.replace('.png', '_led.png'))
