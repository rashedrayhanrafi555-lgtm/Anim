import bpy, math, random, os
from mathutils import Vector, Euler, Matrix

random.seed(11)
FPS = 30
DUR = 25.0
TOTAL = int(FPS * DUR) + 1

for o in list(bpy.data.objects):
    bpy.data.objects.remove(o, do_unlink=True)

def mat(name, rgb):
    m = bpy.data.materials.new(name)
    m.use_nodes = True
    nt = m.node_tree
    nt.nodes.clear()
    out = nt.nodes.new("ShaderNodeOutputMaterial")
    em = nt.nodes.new("ShaderNodeEmission")
    em.inputs["Color"].default_value = (rgb[0], rgb[1], rgb[2], 1.0)
    em.inputs["Strength"].default_value = 1.0
    nt.links.new(em.outputs[0], out.inputs[0])
    return m

M = {
    "sky": mat("sky", (0.36, 0.63, 0.94)),
    "ground": mat("ground", (0.36, 0.72, 0.28)),
    "grass2": mat("grass2", (0.30, 0.64, 0.24)),
    "stone": mat("stone", (0.62, 0.62, 0.65)),
    "wood": mat("wood", (0.72, 0.58, 0.36)),
    "lava": mat("lava", (0.95, 0.30, 0.08)),
    "brick": mat("brick", (0.85, 0.35, 0.25)),
    "yellow": mat("yellow", (0.98, 0.85, 0.24)),
    "blue": mat("blue", (0.18, 0.42, 0.85)),
    "greenp": mat("greenp", (0.22, 0.72, 0.30)),
    "dark": mat("dark", (0.05, 0.05, 0.05)),
    "gold": mat("gold", (0.98, 0.78, 0.16)),
    "white": mat("white", (0.96, 0.96, 0.96)),
    "red": mat("red", (0.92, 0.15, 0.12)),
}

def cube(name, size, loc, material, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_cube_add(size=1, location=loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.rotation_euler = rot
    o.data.materials.append(material)
    return o

cube("Sky", (600, 600, 600), (40, 0, 0), M["sky"])
cube("Baseplate", (220, 70, 2), (45, -5, -1), M["ground"])

TX = [-40, -26, -12, 100, 112, 126]
for i, x in enumerate(TX):
    h = 5 + (i % 3) * 1.4
    y = 16 + (i % 3) * 5
    cube(f"Trunk{i}", (1.2, 1.2, h), (x, y, h / 2), M["wood"])
    cube(f"Leaf{i}", (5, 5, 5), (x, y, h + 2), M["grass2"])
cube("HillL", (30, 20, 14), (-30, 25, 6), M["grass2"])
cube("HillR", (36, 22, 18), (150, 20, 8), M["grass2"])

cube("Lava", (95, 26, 0.4), (78, -22, 0.2), M["lava"])

def plat(x, z, sx=5, mtl="stone"):
    return cube(f"Plat{x}", (sx, 5, 1), (x, -22, z - 0.5), M[mtl])

plat(30, 6, mtl="wood")
plat(38, 7.5)
plat(46, 9, 4)
plat(54, 10.5, 3.5)
plat(62, 12, 3)
plat(70, 13.5, 3, "brick")
plat(78, 15, 6, "gold")
cube("SpawnPad", (7, 7, 1), (2, -22, 0.5), M["white"])
cube("TrophyBase", (3, 3, 0.5), (78, -22, 15.75), M["stone"])
cube("Trophy", (1.6, 1.6, 1.6), (78, -22, 16.8), M["gold"])

def limb(name, size, pivot_loc, material):
    bpy.ops.mesh.primitive_cube_add(size=1, location=pivot_loc)
    o = bpy.context.active_object
    o.name = name
    o.scale = (size[0] / 2, size[1] / 2, size[2] / 2)
    o.data.transform(Matrix.Translation((0, 0, -size[2] / 2)))
    o.data.materials.append(material)
    return o

torso = cube("Torso", (2, 2, 2), (2, -22, 3.0), M["blue"])
head = cube("Head", (1.4, 1.4, 1.4), (2, -22, 4.7), M["yellow"])
eyeL = cube("EyeL", (0.14, 0.3, 0.06), (2.73, -22.35, 4.95), M["dark"])
eyeR = cube("EyeR", (0.14, 0.3, 0.06), (2.73, -21.65, 4.95), M["dark"])
mouth = cube("Mouth", (0.06, 0.7, 0.2), (2.73, -22, 4.25), M["dark"])
armL = limb("ArmL", (1, 1, 2), (2, -23.0, 3.5), M["yellow"])
armR = limb("ArmR", (1, 1, 2), (2, -21.0, 3.5), M["yellow"])
legL = limb("LegL", (1, 1, 2), (2, -22.85, 2.0), M["greenp"])
legR = limb("LegR", (1, 1, 2), (2, -21.15, 2.0), M["greenp"])

char_root = bpy.data.objects.new("CharRoot", None)
char_root.location = (2, -22, 2.0)
bpy.context.collection.objects.link(char_root)
bpy.context.view_layer.update()
for k in (torso, legL, legR):
    k.parent = char_root
    k.matrix_parent_inverse = char_root.matrix_world.inverted()
bpy.context.view_layer.update()
for k in (head, armL, armR):
    k.parent = torso
    k.matrix_parent_inverse = torso.matrix_world.inverted()
bpy.context.view_layer.update()
for k in (eyeL, eyeR, mouth):
    k.parent = head
    k.matrix_parent_inverse = head.matrix_world.inverted()

def text3d(name, body, loc, size, material):
    bpy.ops.object.text_add(location=loc)
    t = bpy.context.active_object
    t.name = name
    t.data.body = body
    t.data.size = size
    t.data.extrude = 0.3
    t.data.align_x = "CENTER"
    t.data.align_y = "CENTER"
    t.data.materials.append(material)
    t.rotation_euler = (math.radians(90), 0, 0)
    t.scale = (0.001, 0.001, 0.001)
    return t

txt_title = text3d("Title", "THE OBBY!", (8, -14, 10), 3.0, M["gold"])
txt_oof = text3d("OofTxt", "OOF!", (74, -13, 14), 4.5, M["red"])
txt_respawn = text3d("RespTxt", "RESPAWN", (2, -14, 8), 2.4, M["white"])
txt_gg = text3d("GG", "GG!", (78, -13, 20), 3.6, M["gold"])
txt_sub = text3d("Sub", "SUBSCRIBE", (78, -13, 16), 2.0, M["white"])

def K(o, path, frame):
    o.keyframe_insert(data_path=path, frame=frame)

def set_pose(f, pos, phase, mode):
    char_root.location = pos
    K(char_root, "location", f)
    s = math.sin(phase * math.pi * 2)
    if mode == "run":
        legL.rotation_euler = (s * 0.95, 0, 0)
        legR.rotation_euler = (-s * 0.95, 0, 0)
        armL.rotation_euler = (-s * 0.8, 0, 0)
        armR.rotation_euler = (s * 0.8, 0, 0)
        torso.rotation_euler = (s * 0.07, 0, 0)
        head.rotation_euler = (-s * 0.05, 0, 0)
    elif mode == "jump":
        legL.rotation_euler = legR.rotation_euler = (-0.55, 0, 0)
        armL.rotation_euler = armR.rotation_euler = (-2.5, 0, 0)
        torso.rotation_euler = (0.12, 0, 0)
        head.rotation_euler = (0, 0, 0)
    elif mode == "fall":
        fl = math.sin(phase * math.pi * 2)
        legL.rotation_euler = (fl * 0.5, 0, 0)
        legR.rotation_euler = (-fl * 0.5, 0, 0)
        armL.rotation_euler = (2.6 + fl * 0.5, 0.5, 0)
        armR.rotation_euler = (2.6 - fl * 0.5, -0.5, 0)
        torso.rotation_euler = (-0.18, 0, fl * 0.22)
        head.rotation_euler = (0.4, 0, 0)
    elif mode == "idle":
        a = math.sin(phase * math.pi * 2) * 0.06
        legL.rotation_euler = legR.rotation_euler = (0, 0, 0)
        armL.rotation_euler = armR.rotation_euler = (a, 0, 0)
        torso.rotation_euler = (0, 0, 0)
        head.rotation_euler = (0, 0, 0)
    elif mode == "victory":
        w = math.sin(phase * math.pi * 4)
        legL.rotation_euler = legR.rotation_euler = (0, 0, 0)
        armL.rotation_euler = (-2.6 + w * 0.35, 0, 0)
        armR.rotation_euler = (-2.6 - w * 0.35, 0, 0)
        torso.rotation_euler = (0, 0, w * 0.12)
        head.rotation_euler = (0, 0, w * 0.2)
    for o in (legL, legR, armL, armR, torso, head):
        K(o, "rotation_euler", f)

P = 2.0
HIP = {
    "ground": 0 + P, "pad": 1.0 + P, "p30": 6.5 + P, "p38": 8 + P, "p46": 9.5 + P,
    "p54": 11 + P, "p62": 12.5 + P, "p70": 14 + P, "gold": 15.5 + P,
}
V = lambda x, z: Vector((x, -22, z))

segs = []
def seg(kind, t0, t1, a, b):
    segs.append((kind, int(round(t0 * FPS)), int(round(t1 * FPS)), a, b))

seg("run", 1.0, 4.6, V(6, HIP["ground"]), V(26, HIP["ground"]))
seg("idle", 4.6, 5.0, V(26, HIP["ground"]), V(26, HIP["ground"]))
seg("jump", 5.0, 5.9, V(26, HIP["ground"]), V(30, HIP["p30"]))
seg("idle", 5.9, 6.15, V(30, HIP["p30"]), V(30, HIP["p30"]))
seg("jump", 6.15, 7.0, V(30, HIP["p30"]), V(38, HIP["p38"]))
seg("idle", 7.0, 7.2, V(38, HIP["p38"]), V(38, HIP["p38"]))
seg("jump", 7.2, 8.05, V(38, HIP["p38"]), V(46, HIP["p46"]))
seg("idle", 8.05, 8.25, V(46, HIP["p46"]), V(46, HIP["p46"]))
seg("jump", 8.25, 9.1, V(46, HIP["p46"]), V(54, HIP["p54"]))
seg("idle", 9.1, 9.3, V(54, HIP["p54"]), V(54, HIP["p54"]))
seg("jump", 9.3, 10.15, V(54, HIP["p54"]), V(62, HIP["p62"]))
seg("idle", 10.15, 10.4, V(62, HIP["p62"]), V(62, HIP["p62"]))
seg("jump", 10.4, 11.3, V(62, HIP["p62"]), V(70, HIP["p70"]))
seg("idle", 11.3, 11.55, V(70, HIP["p70"]), V(70, HIP["p70"]))
seg("jump", 11.55, 12.8, V(70, HIP["p70"]), V(76.2, HIP["gold"]))
seg("fall", 12.8, 18.0, V(76.2, HIP["gold"]), V(78, -6.0))
seg("idle", 18.0, 18.9, V(2, HIP["pad"]), V(2, HIP["pad"]))
seg("run", 18.9, 20.0, V(2, HIP["pad"]), V(26, HIP["ground"]))
seg("jump", 20.0, 20.7, V(26, HIP["ground"]), V(30, HIP["p30"]))
seg("jump", 20.7, 21.2, V(30, HIP["p30"]), V(38, HIP["p38"]))
seg("jump", 21.2, 21.7, V(38, HIP["p38"]), V(46, HIP["p46"]))
seg("jump", 21.7, 22.2, V(46, HIP["p46"]), V(54, HIP["p54"]))
seg("jump", 22.2, 22.7, V(54, HIP["p54"]), V(62, HIP["p62"]))
seg("jump", 22.7, 23.2, V(62, HIP["p62"]), V(70, HIP["p70"]))
seg("jump", 23.2, 23.7, V(70, HIP["p70"]), V(78, HIP["gold"]))
seg("idle", 23.7, 24.1, V(78, HIP["gold"]), V(78, HIP["gold"]))
seg("victory", 24.1, 25.1, V(78, HIP["gold"]), V(78, HIP["gold"]))

def seg_pos(s, f):
    kind, f0, f1, a, b = s
    u = min(max((f - f0) / max(f1 - f0, 1), 0.0), 1.0)
    if kind in ("run", "idle"):
        return a.lerp(b, u), u * 1.15
    if kind == "jump":
        p = a.lerp(b, u)
        p.z = a.z + (b.z - a.z) * u + math.sin(u * math.pi) * 2.4
        return p, u
    p = a.lerp(b, u)
    p.z = a.z + (b.z - a.z) * u * u
    return p, u * 2.4

for f in range(1, TOTAL + 1):
    active = segs[0]
    for s in segs:
        if f >= s[1]:
            active = s
    pos, ph = seg_pos(active, f)
    set_pose(f, pos, ph, active[0])
    if active[0] == "fall" and f > 17.4 * FPS:
        k = (f - 17.4 * FPS) / (0.6 * FPS)
        sc_ = max(0.001, 1.0 - k * 0.999)
        char_root.scale = (sc_, sc_, sc_)
    else:
        char_root.scale = (1, 1, 1)
    K(char_root, "scale", f)

def pop(txt, tin, tout):
    for fr, sv in [(tin, 0.001), (tin + 6, 1.25), (tin + 10, 1.0), (tout - 5, 1.0), (tout, 0.001)]:
        txt.scale = (sv, sv, sv)
        K(txt, "scale", fr)

pop(txt_title, int(1.2 * FPS), int(4.2 * FPS))
pop(txt_oof, int(12.9 * FPS), int(17.6 * FPS))
pop(txt_respawn, int(18.1 * FPS), int(18.9 * FPS))
pop(txt_gg, int(24.4 * FPS), int(25.1 * FPS))
pop(txt_sub, int(24.7 * FPS), int(25.1 * FPS))

cam_data = bpy.data.cameras.new("Cam")
cam_data.lens = 22
cam = bpy.data.objects.new("Cam", cam_data)
bpy.context.collection.objects.link(cam)
bpy.context.scene.camera = cam

def look_at(o, target):
    d = target - o.location
    o.rotation_euler = d.to_track_quat("-Z", "Y").to_euler()

for f in range(1, TOTAL + 1):
    t = f / FPS
    seg_now = segs[0]
    for s in segs:
        if f >= s[1]:
            seg_now = s
    pos, _ = seg_pos(seg_now, f)
    if 1.0 <= t < 4.6:
        c = pos + Vector((-3.5 + t * 0.5, -13, 1.6))
    elif t < 11.5:
        c = pos + Vector((-4.2, -14, 3.0))
    elif t < 18.0:
        u = (t - 11.5) / 6.5
        c = pos + Vector((-5.0 + u * 2.0, -13 - u * 5, 4.0 - u * 1.0))
    elif t < 18.9:
        c = pos + Vector((2.0, -10, 2.8))
    elif t < 24.1:
        c = pos + Vector((-5.5, -11.5, 0.8 + (t - 18.9) * 0.35))
    else:
        c = pos + Vector((-3.0, -9.5, 2.4))
    cam.location = c
    look_at(cam, pos + Vector((1.2, 0, 1.6)))
    K(cam, "location", f)
    K(cam, "rotation_euler", f)

sc = bpy.context.scene
sc.render.engine = "CYCLES"
sc.cycles.device = "CPU"
sc.cycles.samples = 8
sc.cycles.max_bounces = 0
sc.cycles.use_denoising = False
sc.cycles.use_persistent_data = True
sc.render.resolution_x = 1080
sc.render.resolution_y = 1920
sc.render.fps = FPS
sc.frame_start = 1
sc.frame_end = TOTAL
sc.render.image_settings.file_format = "JPEG"
sc.render.image_settings.quality = 90

OUT = os.environ.get("RBX_OUT", "/tmp/rblox_frames")
os.makedirs(OUT, exist_ok=True)
sc.render.filepath = os.path.join(OUT, "f00000")
for f in range(1, TOTAL + 1):
    sc.frame_set(f)
    sc.render.filepath = os.path.join(OUT, "f%05d" % f)
    bpy.ops.render.render(write_still=True)
    if f % 150 == 0:
        print("rendered", f, "/", TOTAL, flush=True)
print("RENDER DONE", TOTAL, "frames")
