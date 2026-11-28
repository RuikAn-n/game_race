"""
《入谱》第三幕 · 文档预览图（读已生成的 .blend，不改资产）
  Blender -b --factory-startup -P Tools/blender/rupu_a3_shots.py -- --out Docs/images/act3 [--only 名字前缀,...]

- 动作：每个片段按关键帧渲 4～6 格（右前 3/4 侧视，Workbench），持枪片段把 PROP_A3_Spear 零变换挂到右手插槽位置，
  拼成一张图 anim_<组>.jpg。
- 资产：一组资产并排渲一张 props_<组>.jpg / env_<名>.jpg / chars_<组>.jpg。
"""
import math
import os
import sys

import bpy
from mathutils import Matrix, Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.path.join(REPO, "ArtSource")
TMP = os.path.join(REPO, "Builds", "tmp", "a3_shots")

SPEAR = {"A3_CombatIdleLoop", "A3_CombatWalk", "A3_CombatRun", "A3_SpearThrust1", "A3_SpearThrust2", "A3_SpearSweep",
         "A3_SpearHeavy", "A3_BlockLoop", "A3_Parry", "A3_Dodge", "A3_Hit", "A3_Death", "A3_Execute", "A3_AllyFight",
         "A3_AguiSpear", "A3_AguiFear", "A3_RaiseFlag", "A3_PlantFlag"}

ANIM_GROUPS = {
    "player_spear": ["A3_CombatIdleLoop", "A3_SpearThrust1", "A3_SpearThrust2", "A3_SpearSweep", "A3_SpearHeavy", "A3_Execute"],
    "player_defense": ["A3_BlockLoop", "A3_Parry", "A3_Dodge", "A3_Hit", "A3_Death", "A3_CombatWalk", "A3_CombatRun"],
    "player_tasks": ["A3_CannonFire", "A3_WinchLoop", "A3_RaiseFlag", "A3_PullLever", "A3_BeatDrum", "A3_CarryBucket",
                     "A3_ThrowWater", "A3_LightFuse", "A3_PlantFlag", "A3_CloseGate", "A3_HelpUp", "A3_Lookout", "A3_Kneel"],
    "ally": ["A3_AllyIdle", "A3_AllyFight", "A3_AllyShoot", "A3_AllyShield", "A3_AllyDeath", "A3_AllyCarry", "A3_AllyFlee",
             "A3_AllyCheer"],
    "civ": ["A3_CivPanic", "A3_CivRun", "A3_CivHide", "A3_CivCarry", "A3_CivKneel", "A3_CivGrieve", "A3_CivReceive",
            "A3_CivChildCry"],
    "story": ["A3_AguiSpear", "A3_AguiKneel", "A3_AguiFear", "A3_AguiRun", "A3_ShugaoReport", "A3_ShugaoKey", "A3_ElderBook",
              "A3_ElderAccuse", "A3_WoundedSit", "A3_WoundedLie", "A3_CorpseSide", "A3_CorpseProne", "A3_BoundLoop"],
}


def _setup(scene, res=(360, 460), tex=False):
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "TEXTURE" if tex else "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.render.resolution_x, scene.render.resolution_y = res
    scene.render.film_transparent = False
    scene.view_settings.view_transform = "Standard"
    if scene.world is None:
        scene.world = bpy.data.worlds.new("ShotWorld")
    scene.world.color = (0.8, 0.78, 0.74)


def _cam(scene, target, size, d=(0.9, -1.4, 0.55)):
    cd = bpy.data.cameras.new("ShotCam")
    cd.type = "ORTHO"
    cd.ortho_scale = size
    cam = bpy.data.objects.new("ShotCam", cd)
    scene.collection.objects.link(cam)
    d = Vector(d).normalized()
    cam.location = Vector(target) + d * 20
    cam.rotation_euler = (Vector(target) - cam.location).to_track_quat("-Z", "Y").to_euler()
    cd.clip_end = 100
    scene.camera = cam
    return cam


def _ground(scene, r=3.0):
    me = bpy.data.meshes.new("ShotGround")
    me.from_pydata([(-r, -r, 0), (r, -r, 0), (r, r, 0), (-r, r, 0)], [], [[0, 1, 2, 3]])
    m = bpy.data.materials.new("ShotGroundM")
    m.diffuse_color = (0.55, 0.52, 0.47, 1)
    me.materials.append(m)
    ob = bpy.data.objects.new("ShotGround", me)
    scene.collection.objects.link(ob)


def _attach_spear(rig):
    import rupu_kit as K
    import rupu_char as C
    import rupu_enemy as E
    import rupu_a3_cast as A3
    before = set(bpy.context.scene.objects)
    A3.build_spear()
    new = [o for o in bpy.context.scene.objects if o not in before]
    J = C.joints(1.75)
    pos, R = E.socket_rest(J, 1.75, "R")
    rig.data.pose_position = "REST"
    bpy.context.view_layer.update()
    for o in new:
        if o.type != "MESH":
            bpy.data.objects.remove(o, do_unlink=True)
            continue
        o.matrix_world = Matrix.Translation(pos) @ R.to_4x4()
        mw = o.matrix_world.copy()
        o.parent = rig
        o.parent_type = "BONE"
        o.parent_bone = "RightHand"
        bpy.context.view_layer.update()
        o.matrix_world = mw
    rig.data.pose_position = "POSE"
    bpy.context.view_layer.update()


def _keyframes(rig):
    fs = set()
    act = rig.animation_data.action if rig.animation_data else None
    if act is None:
        return [0]
    try:
        curves = act.fcurves
    except AttributeError:                                  # Blender 5：分层动作
        curves = [fc for l in act.layers for s in l.strips for cb in s.channelbags for fc in cb.fcurves]
    for fc in curves:
        for k in fc.keyframe_points:
            fs.add(int(round(k.co.x)))
    return sorted(fs)


def shoot_anim(clip, out_png):
    path = os.path.join(SRC, "Characters", f"CH_WangYan_1941@{clip}.blend")
    if not os.path.exists(path):
        print("[shots] 缺", path)
        return None
    bpy.ops.wm.open_mainfile(filepath=path)
    sc = bpy.context.scene
    ref = bpy.data.collections.get("_REF")
    if ref:
        for o in ref.all_objects:
            o.hide_render = True
    rig = next(o for o in sc.objects if o.type == "ARMATURE")
    if clip in SPEAR:
        _attach_spear(rig)
    _setup(sc)
    _ground(sc)
    _cam(sc, (0, 0, 0.95), 2.9)
    frames = _keyframes(rig)
    if len(frames) > 6:
        idx = [round(i * (len(frames) - 1) / 5) for i in range(6)]
        frames = [frames[i] for i in idx]
    tiles = []
    os.makedirs(TMP, exist_ok=True)
    for f in frames:
        sc.frame_set(f)
        p = os.path.join(TMP, f"{clip}_{f}.png")
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        tiles.append((f, p))
    return tiles


def sheet(rows, out, label=True):
    """rows = [(标题, [(帧, png), ...]), ...] → 拼一张 jpg（PIL 不在 Blender 里，用 bpy 图像 + numpy）。"""
    import numpy as np
    loaded = []
    tw = th = 0
    for title, tiles in rows:
        r = []
        for f, p in tiles:
            img = bpy.data.images.load(p)
            w, h = img.size
            a = np.array(img.pixels[:], dtype=np.float32).reshape(h, w, 4)
            bpy.data.images.remove(img)
            r.append(a)
            tw, th = max(tw, w), max(th, h)
        loaded.append(r)
    ncol = max(len(r) for r in loaded)
    H, Wd = th * len(loaded), tw * ncol
    canvas = np.ones((H, Wd, 4), dtype=np.float32)
    for i, r in enumerate(loaded):
        for j, a in enumerate(r):
            y0 = H - (i + 1) * th
            canvas[y0:y0 + a.shape[0], j * tw:j * tw + a.shape[1]] = a
    img = bpy.data.images.new("sheet", Wd, H)
    img.pixels = canvas.ravel()
    img.filepath_raw = out
    img.file_format = "JPEG"
    os.makedirs(os.path.dirname(out), exist_ok=True)
    img.save()
    print("[shots]", out)


def shoot_assets(names, out, cat_of, d=(0.9, -1.4, 0.8), res=(700, 560), top=False):
    """每个资产一格（各自取景），拼成一行或多行。"""
    tiles = []
    for n in names:
        path = os.path.join(SRC, cat_of(n), n + ".blend")
        if not os.path.exists(path):
            print("[shots] 缺", path)
            continue
        bpy.ops.wm.open_mainfile(filepath=path)
        sc = bpy.context.scene
        ref = bpy.data.collections.get("_REF")
        if ref:
            for o in ref.all_objects:
                o.hide_render = not n.startswith(("PROP_", "NPC_", "CH_"))
        objs = [o for o in sc.objects if o.type == "MESH" and not o.name.startswith(("REF_", "COL_"))
                and not (ref and o.name in ref.all_objects)]
        for o in sc.objects:
            if o.name.startswith(("COL_", "TRIG_")):
                o.hide_render = True
        mn = Vector((1e9,) * 3)
        mx = Vector((-1e9,) * 3)
        for o in objs:
            if o.hide_render:
                continue
            for v in o.bound_box:
                w = o.matrix_world @ Vector(v)
                mn = Vector([min(a, b) for a, b in zip(mn, w)])
                mx = Vector([max(a, b) for a, b in zip(mx, w)])
        c = (mn + mx) / 2
        size = (mx - mn).length * (0.85 if not top else 0.75)
        _setup(sc, res, tex=True)
        _cam(sc, c, max(0.3, size), (0.0, -0.001, 1.0) if top else d)
        p = os.path.join(TMP, f"{n}.png")
        os.makedirs(TMP, exist_ok=True)
        sc.render.filepath = p
        bpy.ops.render.render(write_still=True)
        tiles.append((0, p))
    per = 4
    rows = [("", tiles[i:i + per]) for i in range(0, len(tiles), per)]
    if rows:
        sheet(rows, out)


def main(argv):
    out = argv[argv.index("--out") + 1] if "--out" in argv else os.path.join(REPO, "Docs", "images", "act3")
    only = argv[argv.index("--only") + 1].split(",") if "--only" in argv else None
    groups = argv[argv.index("--groups") + 1].split(",") if "--groups" in argv else None
    if "--anims" in argv:
        for g, clips in ANIM_GROUPS.items():
            if groups and g not in groups:
                continue
            rows = []
            for c in clips:
                t = shoot_anim(c, None)
                if t:
                    rows.append((c, t))
            sheet(rows, os.path.join(out, f"anim_{g}.jpg"))
    if "--assets" in argv:
        import json
        spec = json.loads(argv[argv.index("--assets") + 1])
        cats = {"PROP": "Props", "ENV": "Environments", "NPC": "Characters", "CH": "Characters", "BLD": "Buildings"}
        for fname, names in spec.items():
            if only and fname not in only:
                continue
            top = fname.endswith("_top")
            shoot_assets(names, os.path.join(out, fname + ".jpg"), lambda n: cats[n.split("_")[0]], top=top)


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
