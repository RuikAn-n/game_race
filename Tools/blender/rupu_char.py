"""
《入谱》主要人物：程序化低模 + Humanoid 骨架 + 基础动画（Blender bpy）
=====================================================================

由 build_yongchang.py 的驱动统一生成/导出（RECIPES 里以 CH_ / NPC_ / PROP_ 开头的条目）。

约定：
  - 正面朝 Blender -Y，脚底 z=0，T 姿势；人物左侧 = +X。
  - 骨骼名用团结 Humanoid 标准名（Hips/Spine/Chest/Neck/Head/LeftUpperArm/...），导入后自动映射 Avatar。
  - 低模分段身体，每段刚性绑定到一根骨骼；长衫下摆按左右腿混合权重，走路时会跟腿摆。
  - 不做写实脸：五官只是几块小几何体，后续换表情贴图。
  - 动画：CH_WangYan_1941@Idle / @Walk / @Run，所有人共用（Humanoid 重定向）。

人物与清单 ID 对应：CH_WangYan_1941=CHR_WangYan_1941、CH_WangYan_1560=CHR_WangYan_1560、
NPC_WangPei=CHR_WangPei、NPC_WangShugao=CHR_WangShugao、NPC_WangDe=CHR_WangDe、NPC_WangBingzhi=CHR_WangBingzhi。
1941 族亲：NPC_ClanElder=CHR_Elder、NPC_ClanJiao=CHR_Jiao、NPC_ClanShao=CHR_Shao、NPC_ClanCang=CHR_Cang；
NPC_ClanUncle / NPC_ClanGranny / NPC_ClanBoy / NPC_ClanGirl = CHR_Townsperson 的男/老/少/女变体（族中冷遇、亲善、孩童、少女）。
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import rupu_kit as K

# ---------------------------------------------------------------- 颜色
CHAR_PALETTE = {
    "M_CH_Skin": "#c9a585", "M_CH_Skin_Dark": "#a37b5a", "M_CH_Skin_Old": "#b8977a",
    "M_CH_Eye": "#1a1614", "M_CH_Hair": "#1c1a18", "M_CH_Hair_Grey": "#8a8680", "M_CH_Hair_White": "#e2ddd2",
    # 王砚 1941
    "M_CH_WY41_Robe": "#5f6f7a", "M_CH_WY41_Pants": "#3a3f44", "M_CH_WY41_Shoe": "#262626", "M_CH_WY41_Bag": "#6a4a32",
    # 王砚 1560
    "M_CH_WY60_Coat": "#7a6a52", "M_CH_WY60_Pants": "#5a5244", "M_CH_WY60_Sash": "#3d3a33",
    "M_CH_Wrap": "#b8ad94", "M_CH_Straw": "#a08a5a", "M_CH_Pouch": "#8A5A3B", "M_CH_Headband": "#3a3a3a",
    # 王沛
    "M_CH_WP_Under": "#6e3b32", "M_CH_WP_Leather": "#4e3a2a", "M_CH_WP_Plate": "#5c574c", "M_CH_WP_Pants": "#3f3a33",
    "M_CH_WP_Boot": "#2e2620", "M_CH_Tag": "#9a7a52",
    # 王叔杲
    "M_CH_WS_Robe": "#56636e", "M_CH_WS_Sash": "#2e3236", "M_CH_WS_Cap": "#1e2226", "M_CH_WS_Shoe": "#222222",
    "M_CH_Scroll": "#d8cdb5",
    # 王德
    "M_CH_WD_Coat": "#3e4a57", "M_CH_WD_Pants": "#4a4438", "M_CH_WD_Sash": "#8A5A3B", "M_CH_Scabbard": "#3a2a1c",
    # 王秉之
    "M_CH_WB_Robe": "#4e3b2c", "M_CH_WB_Cap": "#1a1a1a", "M_CH_WB_Shoe": "#222222",
    # 1941 族亲（第一幕祠堂）
    "M_CH_EL_Robe": "#3a2f27", "M_CH_EL_Magua": "#1f1d1b", "M_CH_EL_Shoe": "#1a1a1a", "M_CH_Beads": "#5a2a22",
    "M_CH_JP_Robe": "#4a5560", "M_CH_JP_Sash": "#2a2c2e", "M_CH_Ledger": "#7a6a4a", "M_CH_Glasses": "#1a1614",
    "M_CH_SP_Coat": "#2f3236", "M_CH_SP_Pants": "#3d3b36", "M_CH_SP_Sash": "#6e3b32", "M_CH_Torch": "#9a5238",
    "M_CH_CP_Ao": "#34423d", "M_CH_CP_Skirt": "#262629", "M_CH_CP_Bundle": "#5e6b5a", "M_CH_ClothShoe": "#2a2724",
    "M_CH_UC_Coat": "#5a5a50", "M_CH_UC_Pants": "#33312d", "M_CH_UC_Hat": "#3a332b",
    "M_CH_GM_Ao": "#3e4a57", "M_CH_GM_Skirt": "#2b2a28", "M_CH_GM_Band": "#1e1e1e",
    "M_CH_BY_Coat": "#8a7a5a", "M_CH_BY_Pants": "#4a4438",
    "M_CH_GL_Ao": "#7a4a40", "M_CH_GL_Pants": "#3a3f44", "M_CH_GL_Ribbon": "#8a3a30",
    # 1941 日军（土黄军服，低饱和；JA = Japanese Army，与交谱派 JP 区分）
    "M_CH_JA_Khaki": "#6b6446", "M_CH_JA_KhakiDark": "#57513a", "M_CH_JA_Leather": "#4a3524", "M_CH_JA_Boot": "#1f1b17",
    "M_CH_JA_Glove": "#d9d4c6", "M_CH_JA_Red": "#8a2e26", "M_CH_JA_Helmet": "#545a42", "M_CH_JA_Gold": "#8f7a44",
    "M_CH_JA_Wrap": "#7a7256", "M_CH_JA_Steel": "#4a4d4f",
    # 1941 小贩 / 街坊
    "M_CH_VD_Coat": "#6e6a5c", "M_CH_VD_Pants": "#3e3b34", "M_CH_VD_Apron": "#4a5560", "M_CH_StrawHat": "#a08a5a",
    "M_CH_VG_Coat": "#3d4650", "M_CH_TW_Ao": "#5a4e5c", "M_CH_TW_Scarf": "#6e6a5c", "M_CH_TO_Robe": "#5a5248",
    "M_CH_TI_Coat": "#585c56", "M_CH_Bandage": "#d6d0c0", "M_CH_Blood": "#5e1f1a", "M_CH_TR_Coat": "#6a5a44",
    "M_CH_Bedroll": "#7a6a52",
    # 道具
    "M_PR_Wood": "#6b5039", "M_PR_WoodDark": "#3e2f24", "M_PR_Iron": "#5a5d5e", "M_PR_Tassel": "#9a4a3a",
    "M_PR_Bead": "#2b211a",
}
K.PALETTE.update(CHAR_PALETTE)


# ---------------------------------------------------------------- 蒙皮网格累加器
class Skin:
    def __init__(self):
        self.v, self.w, self.f, self.fm, self.mats = [], [], [], [], []

    def mi(self, m):
        if m not in self.mats:
            self.mats.append(m)
        return self.mats.index(m)

    def add(self, verts, faces, mat, weights):
        base = len(self.v)
        for p in verts:
            p = Vector(p)
            self.v.append(p)
            self.w.append(weights(p) if callable(weights) else weights)
        for fc in faces:
            self.f.append([base + i for i in fc])
            self.fm.append(self.mi(mat))

    def to_object(self, name, rig):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        vs = [bm.verts.new(p) for p in self.v]
        for fc, mi in zip(self.f, self.fm):
            try:
                f = bm.faces.new([vs[i] for i in fc])
                f.material_index = mi
            except ValueError:
                pass
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        K.box_uv(bm, 0.5)
        bm.to_mesh(me)
        bm.free()
        for m in self.mats:
            me.materials.append(K.get_mat(m))
        for p in me.polygons:
            p.use_smooth = False
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        groups = {}
        for i, wd in enumerate(self.w):
            for b, wt in wd.items():
                if wt <= 0:
                    continue
                g = groups.get(b) or ob.vertex_groups.new(name=b)
                groups[b] = g
                g.add([i], wt, "REPLACE")
        ob.parent = rig
        mod = ob.modifiers.new("Armature", "ARMATURE")
        mod.object = rig
        return ob


# ---------------------------------------------------------------- 几何原语（返回 verts, faces）
def _frame(d):
    d = d.normalized()
    ref = Vector((1, 0, 0)) if abs(d.x) < 0.9 else Vector((0, 1, 0))
    u = (ref - d * ref.dot(d)).normalized()
    v = d.cross(u)
    return u, v


def rings_mesh(rings, seg=8, cap0=True, cap1=True):
    """rings: [(center Vector, rx(沿 X), ry(沿 Y))]，水平截面（适合躯干/下摆）。"""
    verts, faces = [], []
    for c, rx, ry in rings:
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((c.x + rx * math.cos(a), c.y + ry * math.sin(a), c.z))
    n = len(rings)
    for r in range(n - 1):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((r * seg + i, r * seg + j, (r + 1) * seg + j, (r + 1) * seg + i))
    if cap0:
        faces.append(tuple(reversed(range(seg))))
    if cap1:
        faces.append(tuple((n - 1) * seg + i for i in range(seg)))
    return verts, faces


def tube(p0, p1, r0, r1, seg=8, sx=1.0, sy=1.0):
    p0, p1 = Vector(p0), Vector(p1)
    u, v = _frame(p1 - p0)
    verts = []
    for p, r in ((p0, r0), (p1, r1)):
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append(tuple(p + u * (r * sx * math.cos(a)) + v * (r * sy * math.sin(a))))
    faces = [(i, (i + 1) % seg, seg + (i + 1) % seg, seg + i) for i in range(seg)]
    faces.append(tuple(reversed(range(seg))))
    faces.append(tuple(seg + i for i in range(seg)))
    return verts, faces


def ellipsoid(c, rx, ry, rz, seg=10, rings=6, zmin=-1.0):
    """椭球（zmin>-1 时截掉下半部分，用于帽子/头发）。"""
    c = Vector(c)
    verts, faces = [], []
    zmin = max(zmin, -0.97)
    lats = [math.asin(zmin) + (math.pi / 2 - math.asin(zmin)) * k / rings for k in range(rings + 1)]
    for la in lats[:-1]:
        for i in range(seg):
            a = 2 * math.pi * i / seg
            verts.append((c.x + rx * math.cos(la) * math.cos(a), c.y + ry * math.cos(la) * math.sin(a), c.z + rz * math.sin(la)))
    top = len(verts)
    verts.append((c.x, c.y, c.z + rz))
    nr = rings
    for r in range(nr - 1):
        for i in range(seg):
            j = (i + 1) % seg
            faces.append((r * seg + i, r * seg + j, (r + 1) * seg + j, (r + 1) * seg + i))
    for i in range(seg):
        faces.append(((nr - 1) * seg + i, (nr - 1) * seg + (i + 1) % seg, top))
    faces.append(tuple(reversed(range(seg))))
    return verts, faces


def box(c, s, rot=None):
    c = Vector(c)
    hx, hy, hz = s[0] / 2, s[1] / 2, s[2] / 2
    pts = [(-hx, -hy, -hz), (hx, -hy, -hz), (hx, hy, -hz), (-hx, hy, -hz),
           (-hx, -hy, hz), (hx, -hy, hz), (hx, hy, hz), (-hx, hy, hz)]
    R = rot.to_matrix() if rot is not None else Matrix.Identity(3)
    verts = [tuple(c + R @ Vector(p)) for p in pts]
    faces = [(0, 3, 2, 1), (4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
    return verts, faces


def wedge(c, w, d_top, d_bot, h):
    """胡子用：上宽下窄的楔形，c 为上沿中心。"""
    c = Vector(c)
    pts = [(-w / 2, -d_top / 2, 0), (w / 2, -d_top / 2, 0), (w / 2, d_top / 2, 0), (-w / 2, d_top / 2, 0),
           (-w * 0.25, -d_bot / 2, -h), (w * 0.25, -d_bot / 2, -h), (w * 0.25, d_bot / 2, -h), (-w * 0.25, d_bot / 2, -h)]
    verts = [tuple(c + Vector(p)) for p in pts]
    faces = [(0, 1, 2, 3), (4, 7, 6, 5), (0, 4, 5, 1), (1, 5, 6, 2), (2, 6, 7, 3), (3, 7, 4, 0)]
    return verts, faces


# ---------------------------------------------------------------- 骨架
def joints(H, hunch=0.0, bw=1.0):
    h = H
    J = {
        "hips": Vector((0, 0, 0.53 * h)), "spine": Vector((0, 0, 0.60 * h)), "chest": Vector((0, 0, 0.685 * h)),
        "chest_t": Vector((0, 0, 0.815 * h)), "neck": Vector((0, 0, 0.835 * h)), "head": Vector((0, 0, 0.872 * h)),
        "top": Vector((0, 0, 1.0 * h)),
    }
    # 驼背：胸以上前移下沉
    off = {"chest": (0, -0.012, -0.004), "chest_t": (0, -0.04, -0.012), "neck": (0, -0.055, -0.018),
           "head": (0, -0.07, -0.024), "top": (0, -0.085, -0.03)}
    for k, (x, y, z) in off.items():
        J[k] = J[k] + Vector((x, y, z)) * h * hunch
    sh_z = J["chest_t"].z
    sh_y = J["chest_t"].y
    for s, sg in (("L", 1), ("R", -1)):
        J["shoulder" + s] = Vector((sg * 0.025 * h, sh_y, sh_z))
        J["arm" + s] = Vector((sg * 0.105 * h * bw, sh_y, sh_z))
        J["elbow" + s] = J["arm" + s] + Vector((sg * 0.165 * h, 0, 0))
        J["wrist" + s] = J["elbow" + s] + Vector((sg * 0.15 * h, 0, 0))
        J["hand" + s] = J["wrist" + s] + Vector((sg * 0.095 * h, 0, 0))
        J["hip" + s] = Vector((sg * 0.055 * h, 0, 0.52 * h))
        J["knee" + s] = Vector((sg * 0.055 * h, -0.005 * h, 0.285 * h))
        J["ankle" + s] = Vector((sg * 0.055 * h, 0.0, 0.048 * h))
        J["toe" + s] = Vector((sg * 0.055 * h, -0.085 * h, 0.018 * h))
        J["toeEnd" + s] = Vector((sg * 0.055 * h, -0.135 * h, 0.018 * h))
    return J


def bone_list(J):
    B = [("Hips", "hips", "spine", None), ("Spine", "spine", "chest", "Hips"), ("Chest", "chest", "chest_t", "Spine"),
         ("Neck", "neck", "head", "Chest"), ("Head", "head", "top", "Neck")]
    for s, side in (("L", "Left"), ("R", "Right")):
        B += [(side + "Shoulder", "shoulder" + s, "arm" + s, "Chest"),
              (side + "UpperArm", "arm" + s, "elbow" + s, side + "Shoulder"),
              (side + "LowerArm", "elbow" + s, "wrist" + s, side + "UpperArm"),
              (side + "Hand", "wrist" + s, "hand" + s, side + "LowerArm"),
              (side + "UpperLeg", "hip" + s, "knee" + s, "Hips"),
              (side + "LowerLeg", "knee" + s, "ankle" + s, side + "UpperLeg"),
              (side + "Foot", "ankle" + s, "toe" + s, side + "LowerLeg"),
              (side + "Toes", "toe" + s, "toeEnd" + s, side + "Foot")]
    return B


def make_rig(J):
    arm = bpy.data.armatures.new("Rig")
    rig = bpy.data.objects.new("Rig", arm)
    bpy.context.scene.collection.objects.link(rig)
    bpy.context.view_layer.objects.active = rig
    rig.select_set(True)
    bpy.ops.object.mode_set(mode="EDIT")
    ebs = {}
    for name, a, b, parent in bone_list(J):
        eb = arm.edit_bones.new(name)
        eb.head, eb.tail = J[a], J[b]
        eb.roll = 0.0
        if parent:
            eb.parent = ebs[parent]
        ebs[name] = eb
    bpy.ops.object.mode_set(mode="OBJECT")
    arm.display_type = "STICK"
    return rig


# ---------------------------------------------------------------- 权重工具
def W(b):
    return {b: 1.0}


def torso_weight(J):
    zs, zc = J["spine"].z, J["chest"].z
    band = 0.025 * (J["top"].z)

    def f(p):
        z = p.z
        if z < zs - band:
            return W("Hips")
        if z < zs + band:
            t = (z - (zs - band)) / (2 * band)
            return {"Hips": 1 - t, "Spine": t}
        if z < zc - band:
            return W("Spine")
        if z < zc + band:
            t = (z - (zc - band)) / (2 * band)
            return {"Spine": 1 - t, "Chest": t}
        return W("Chest")
    return f


def skirt_weight(J, z_hip):
    def f(p):
        if p.z >= z_hip - 0.01:
            return W("Hips")
        k = min(1.0, (z_hip - p.z) / (z_hip - 0.1) * 0.9 + 0.1)   # 越往下越跟腿
        x = p.x
        side = max(-1.0, min(1.0, x / 0.04))
        wl = k * (0.5 + 0.5 * side)
        wr = k * (0.5 - 0.5 * side)
        return {"Hips": 1 - k, "LeftUpperLeg": wl, "RightUpperLeg": wr}
    return f


def spine_y(J, z):
    """躯干中心线随高度的 Y 偏移（驼背）。"""
    pts = [(J["hips"].z, J["hips"].y), (J["chest"].z, J["chest"].y), (J["chest_t"].z, J["chest_t"].y), (J["neck"].z, J["neck"].y)]
    if z <= pts[0][0]:
        return pts[0][1]
    for (z0, y0), (z1, y1) in zip(pts, pts[1:]):
        if z <= z1:
            t = (z - z0) / max(1e-6, z1 - z0)
            return y0 + (y1 - y0) * t
    return pts[-1][1]


# ---------------------------------------------------------------- 人物生成
def build_body(S, J, H, c):
    """c: 配置 dict。"""
    h = H
    skin = c.get("skin", "M_CH_Skin")
    top, pants, shoe = c["top"], c["pants"], c["shoe"]
    outfit = c["outfit"]
    bulk = c.get("bulk", 1.0)

    # 头（head>1：孩童的大头比例）
    hs = c.get("head", 1.0)
    hc = J["head"] + Vector((0, -0.004 * h, 0.064 * h * hs))
    rx, ry, rz = 0.05 * h * hs, 0.058 * h * hs, 0.066 * h * hs
    S.add(*ellipsoid(hc, rx, ry, rz, seg=10, rings=6), skin, W("Head"))
    fy = hc.y - ry * 0.93
    fh = h * hs     # 五官按头的大小缩放
    tilt = c.get("brow_tilt", 0.0)     # >0 皱眉（内端压低），<0 眉梢下垂（和善）
    for sx in (-1, 1):
        S.add(*box((hc.x + sx * 0.019 * fh, fy, hc.z + 0.006 * fh), (0.012 * fh, 0.006 * fh, 0.006 * fh)), "M_CH_Eye", W("Head"))
        S.add(*box((hc.x + sx * 0.019 * fh, fy + 0.002 * fh, hc.z + 0.018 * fh), (0.017 * fh, 0.006 * fh, 0.003 * fh),
                   rot=_eu(0, -sx * tilt, 0)), c.get("brow", "M_CH_Hair"), W("Head"))
        S.add(*box((hc.x + sx * rx * 0.98, hc.y + 0.004 * fh, hc.z), (0.008 * fh, 0.018 * fh, 0.022 * fh)), skin, W("Head"))
    S.add(*box((hc.x, fy - 0.004 * fh, hc.z - 0.008 * fh), (0.010 * fh, 0.012 * fh, 0.018 * fh)), skin, W("Head"))
    S.add(*box((hc.x, fy + 0.003 * fh, hc.z - 0.03 * fh), (0.018 * fh, 0.004 * fh, 0.003 * fh)), "M_CH_Eye", W("Head"))
    # 脖子
    S.add(*tube(J["neck"] + Vector((0, 0, -0.01 * h)), J["head"] + Vector((0, 0, 0.02 * h)), 0.024 * h, 0.022 * h), skin, W("Neck"))

    # 躯干（上衣）
    zb = 0.47 * h if outfit != "robe" else 0.50 * h
    rings = []
    for z, rxx, ryy in ((zb, 0.092, 0.064), (0.56 * h, 0.085, 0.060), (0.64 * h, 0.093, 0.064), (0.72 * h, 0.105, 0.066),
                        (J["chest_t"].z - 0.004 * h, 0.112, 0.060), (J["chest_t"].z + 0.016 * h, 0.06, 0.042)):
        rings.append((Vector((0, spine_y(J, z), z)), rxx * h * bulk, ryy * h * bulk))
    S.add(*rings_mesh(rings, seg=10), top, torso_weight(J))
    # 领口
    S.add(*tube(J["neck"] + Vector((0, 0, -0.012 * h)), J["neck"] + Vector((0, 0, 0.012 * h)), 0.03 * h, 0.028 * h, seg=8),
          c.get("collar", top), W("Neck"))

    # 手臂
    for s, side in (("L", "Left"), ("R", "Right")):
        sg = 1 if s == "L" else -1
        S.add(*ellipsoid(J["arm" + s], 0.036 * h * bulk, 0.035 * h * bulk, 0.035 * h * bulk, seg=8, rings=4),
              top, {side + "UpperArm": 0.7, side + "Shoulder": 0.3})
        S.add(*tube(J["arm" + s], J["elbow" + s] + Vector((sg * 0.01 * h, 0, 0)), 0.033 * h * bulk, 0.028 * h * bulk),
              top, W(side + "UpperArm"))
        cuff = c.get("cuff", 1.0)
        S.add(*tube(J["elbow" + s], J["wrist" + s] + Vector((sg * 0.005 * h, 0, 0)), 0.028 * h * bulk, 0.023 * h * cuff),
              c.get("sleeve", top), W(side + "LowerArm"))
        # 手：掌 + 拇指（glove：军官白手套）
        hand = c.get("glove", skin)
        wc = J["wrist" + s] + Vector((sg * 0.045 * h, 0, 0))
        S.add(*box(wc, (0.085 * h, 0.042 * h, 0.022 * h)), hand, W(side + "Hand"))
        S.add(*box(J["wrist" + s] + Vector((sg * 0.03 * h, -0.026 * h, -0.004 * h)), (0.035 * h, 0.015 * h, 0.014 * h)),
              hand, W(side + "Hand"))

        # 腿
        S.add(*tube(J["hip" + s] + Vector((0, 0, 0.02 * h)), J["knee" + s], 0.05 * h * bulk, 0.035 * h), pants, W(side + "UpperLeg"))
        S.add(*tube(J["knee" + s] + Vector((0, 0, 0.012 * h)), J["ankle" + s], 0.034 * h, 0.025 * h), pants, W(side + "LowerLeg"))
        if c.get("wrap"):
            S.add(*tube(J["knee" + s] + Vector((0, 0, -0.02 * h)), J["ankle" + s] + Vector((0, 0, 0.02 * h)), 0.037 * h, 0.029 * h),
                  c["wrap"], W(side + "LowerLeg"))
        # 鞋
        ax = J["ankle" + s]
        boot = c.get("boot", False)
        S.add(*box((ax.x, 0.0, (0.06 if boot else 0.028) * h), (0.056 * h, 0.12 * h, (0.12 if boot else 0.056) * h)),
              shoe, W(side + "Foot"))
        S.add(*box((ax.x, -0.105 * h, 0.018 * h), (0.054 * h, 0.06 * h, 0.036 * h)), shoe, W(side + "Toes"))

    # 下摆
    if outfit == "robe":
        zr = 0.505 * h
        fl = c.get("flare", 1.0)       # 裙摆外张
        rr = [(Vector((0, 0, zr)), 0.095 * h * bulk, 0.066 * h * bulk), (Vector((0, 0.002 * h, 0.40 * h)), 0.108 * h * fl, 0.075 * h * fl),
              (Vector((0, 0.004 * h, 0.24 * h)), 0.12 * h * fl, 0.083 * h * fl),
              (Vector((0, 0.006 * h, c.get("hem", 0.075) * h)), 0.128 * h * fl, 0.088 * h * fl)]
        S.add(*rings_mesh(rr, seg=12, cap0=False, cap1=False), c.get("skirt", top), skirt_weight(J, zr))
        # 长衫右衽开襟线
        S.add(*box((0.035 * h, spine_y(J, 0.66 * h) - 0.066 * h * bulk, 0.66 * h), (0.006 * h, 0.004 * h, 0.2 * h), rot=_rz(0.0)),
              c.get("trim", "M_CH_Eye"), torso_weight(J))
    else:
        zr = zb + 0.01 * h
        rr = [(Vector((0, 0, zr)), 0.094 * h * bulk, 0.066 * h * bulk), (Vector((0, 0, 0.42 * h)), 0.105 * h * bulk, 0.074 * h * bulk)]
        S.add(*rings_mesh(rr, seg=10, cap0=False, cap1=False), top, skirt_weight(J, zr))
    # 腰带
    if c.get("sash"):
        zs = 0.505 * h
        S.add(*rings_mesh([(Vector((0, 0, zs - 0.018 * h)), 0.099 * h * bulk, 0.07 * h * bulk),
                           (Vector((0, 0, zs + 0.018 * h)), 0.097 * h * bulk, 0.068 * h * bulk)], seg=10), c["sash"], W("Hips"))
    return hc, (rx, ry, rz)


def _rz(deg):
    from mathutils import Euler
    return Euler((0, 0, math.radians(deg)))


def _eu(x=0, y=0, z=0):
    from mathutils import Euler
    return Euler((math.radians(x), math.radians(y), math.radians(z)))


def hair_short(S, hc, r, mat, h):
    rx, ry, rz = r
    S.add(*ellipsoid(hc + Vector((0, 0.006 * h, 0.012 * h)), rx * 1.07, ry * 1.05, rz * 0.98, seg=10, rings=4, zmin=0.0),
          mat, W("Head"))
    S.add(*box(hc + Vector((0, ry * 0.55, -0.01 * h)), (rx * 1.7, ry * 0.7, rz * 0.9)), mat, W("Head"))


def hair_bun(S, hc, r, mat, h, band=None):
    hair_short(S, hc, r, mat, h)
    rx, ry, rz = r
    S.add(*ellipsoid(hc + Vector((0, 0.004 * h, rz + 0.012 * h)), 0.02 * h, 0.02 * h, 0.018 * h, seg=8, rings=4), mat, W("Head"))
    if band:
        S.add(*rings_mesh([(hc + Vector((0, 0, 0.018 * h)), rx * 1.1, ry * 1.08), (hc + Vector((0, 0, 0.032 * h)), rx * 1.09, ry * 1.07)],
                          seg=10), band, W("Head"))


def hair_back_bun(S, hc, r, mat, h, band=None):
    """妇人：脑后低髻（可加抹额）。"""
    hair_short(S, hc, r, mat, h)
    rx, ry, rz = r
    S.add(*ellipsoid(hc + Vector((0, ry * 0.95, -rz * 0.15)), 0.034 * h, 0.026 * h, 0.03 * h, seg=8, rings=4), mat, W("Head"))
    if band:
        S.add(*rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.32)), rx * 1.1, ry * 1.08),
                           (hc + Vector((0, 0.004 * h, rz * 0.5)), rx * 1.08, ry * 1.06)], seg=10), band, W("Head"))


def hair_braid(S, J, hc, r, mat, h, ribbon=None):
    """少女：短发 + 脑后一根长辫（辫梢跟胸）。"""
    hair_short(S, hc, r, mat, h)
    rx, ry, rz = r
    top = hc + Vector((0, ry * 0.9, -rz * 0.4))
    bot = Vector((0, J["chest"].y + 0.075 * h, J["chest"].z - 0.02 * h))
    S.add(*tube(top, bot, 0.018 * h, 0.012 * h, seg=6), mat,
          lambda p: {"Head": 0.6, "Chest": 0.4} if p.z > J["neck"].z else W("Chest"))
    if ribbon:
        S.add(*box(bot + Vector((0, 0.002 * h, 0.01 * h)), (0.03 * h, 0.012 * h, 0.022 * h)), ribbon, W("Chest"))


def brim_hat(S, hc, r, mat, h):
    """毡帽：圆顶 + 一圈帽檐。"""
    rx, ry, rz = r
    S.add(*ellipsoid(hc + Vector((0, 0.004 * h, rz * 0.35)), rx * 1.05, ry * 1.03, rz * 0.8, seg=10, rings=4, zmin=0.0),
          mat, W("Head"))
    S.add(*rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.33)), rx * 1.75, ry * 1.6),
                       (hc + Vector((0, 0.004 * h, rz * 0.37)), rx * 1.75, ry * 1.6)], seg=12), mat, W("Head"))


def helmet(S, hc, r, mat, h):
    """九〇式钢盔：圆顶 + 窄檐 + 顶上一点星徽。"""
    rx, ry, rz = r
    S.add(*ellipsoid(hc + Vector((0, 0.004 * h, rz * 0.12)), rx * 1.22, ry * 1.18, rz * 1.05, seg=10, rings=4, zmin=0.0),
          mat, W("Head"))
    S.add(*rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.08)), rx * 1.32, ry * 1.28),
                       (hc + Vector((0, 0.004 * h, rz * 0.14)), rx * 1.3, ry * 1.26)], seg=12), mat, W("Head"))
    S.add(*box(hc + Vector((0, -ry * 1.1, rz * 0.6)), (0.012 * h, 0.004 * h, 0.012 * h)), "M_CH_JA_Gold", W("Head"))


def field_cap(S, hc, r, mat, h, neck_flaps=False):
    """战斗帽（略帽）：低平帽身 + 短帽舌 + 星徽，可带护颈布。"""
    rx, ry, rz = r
    S.add(*ellipsoid(hc + Vector((0, 0.006 * h, rz * 0.3)), rx * 1.08, ry * 1.06, rz * 0.78, seg=10, rings=3, zmin=0.0),
          mat, W("Head"))
    S.add(*box(hc + Vector((0, -ry * 1.12, rz * 0.32)), (rx * 1.3, ry * 0.45, 0.006 * h), rot=_eu(-12, 0, 0)), mat, W("Head"))
    S.add(*box(hc + Vector((0, -ry * 1.05, rz * 0.62)), (0.012 * h, 0.004 * h, 0.012 * h)), "M_CH_JA_Gold", W("Head"))
    if neck_flaps:
        for sx in (-1, 0, 1):
            S.add(*box(hc + Vector((sx * rx * 0.75, ry * (0.75 if sx else 1.05), -rz * 0.25)),
                       (0.004 * h if sx else rx * 1.3, ry * 0.9 if sx else 0.004 * h, rz * 0.9)), mat,
                  lambda p: {"Head": 0.7, "Neck": 0.3})


def peaked_cap(S, hc, r, mat, h):
    """军官大檐帽：帽墙 + 红帽箍 + 顶 + 黑漆帽檐。"""
    rx, ry, rz = r
    S.add(*rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.3)), rx * 1.06, ry * 1.04),
                       (hc + Vector((0, 0.004 * h, rz * 0.55)), rx * 1.07, ry * 1.05)], seg=12), "M_CH_JA_Red", W("Head"))
    S.add(*rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.55)), rx * 1.07, ry * 1.05),
                       (hc + Vector((0, 0.01 * h, rz * 0.98)), rx * 1.18, ry * 1.2)], seg=12, cap1=False), mat, W("Head"))
    S.add(*ellipsoid(hc + Vector((0, 0.01 * h, rz * 0.97)), rx * 1.18, ry * 1.2, 0.012 * h, seg=12, rings=2, zmin=0.0),
          mat, W("Head"))
    S.add(*box(hc + Vector((0, -ry * 1.14, rz * 0.3)), (rx * 1.4, ry * 0.55, 0.006 * h), rot=_eu(-18, 0, 0)), "M_CH_JA_Boot", W("Head"))
    S.add(*box(hc + Vector((0, -ry * 1.07, rz * 0.43)), (0.014 * h, 0.004 * h, 0.014 * h)), "M_CH_JA_Gold", W("Head"))


def straw_hat(S, hc, r, mat, h):
    """斗笠：压低的宽圆锥。"""
    rx, ry, rz = r
    S.add(*rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.35)), rx * 3.0, ry * 2.7),
                       (hc + Vector((0, 0.004 * h, rz * 1.25)), rx * 0.2, ry * 0.2)], seg=12), mat, W("Head"))


def headscarf(S, hc, r, mat, h):
    """包头巾：裹住头顶到耳后，脑后打一个结。"""
    rx, ry, rz = r
    S.add(*ellipsoid(hc + Vector((0, 0.008 * h, 0.006 * h)), rx * 1.12, ry * 1.1, rz * 1.02, seg=10, rings=4, zmin=-0.15),
          mat, W("Head"))
    S.add(*ellipsoid(hc + Vector((0, ry * 1.1, -rz * 0.2)), 0.024 * h, 0.018 * h, 0.022 * h, seg=6, rings=3), mat, W("Head"))


# ---------------------------------------------------------------- 角色配置
# ---------------------------------------------------------------- 扩展钩子（其他模块注册，不必改本文件）
# HAIR_HOOKS[name](S, J, hc, r, hair_mat, h, cfg)      —— cfg["hair"] == name 时调用
# EXTRA_HOOKS[name](S, J, h, cfg, torso_w, hips_w)     —— cfg["extras"] 含 name 时调用
# GESTURE_HOOKS[kind]() -> (总帧数, [(帧, 姿势, 髋高)])   —— build_gesture(kind) 优先查这里
HAIR_HOOKS = {}
EXTRA_HOOKS = {}
GESTURE_HOOKS = {}

CAST = {
    "CH_WangYan_1941": dict(H=1.75, outfit="robe", top="M_CH_WY41_Robe", pants="M_CH_WY41_Pants", shoe="M_CH_WY41_Shoe",
                            hair="short", extras=["camera_bag"], desc="王砚 1941：照相馆学徒，灰蓝长衫、布鞋、斜挎相机包、短发"),
    "CH_WangYan_1560": dict(H=1.75, outfit="jacket", top="M_CH_WY60_Coat", pants="M_CH_WY60_Pants", shoe="M_CH_Straw",
                            sash="M_CH_WY60_Sash", wrap="M_CH_Wrap", hair="bun", band="M_CH_Headband", extras=["pouch"],
                            desc="王砚 1560：同脸；明制短褐、布带、绑腿、草鞋、腰间谱袋"),
    "NPC_WangPei": dict(H=1.78, outfit="jacket", top="M_CH_WP_Under", pants="M_CH_WP_Pants", shoe="M_CH_WP_Boot", boot=True,
                        skin="M_CH_Skin_Dark", sash="M_CH_WP_Leather", hair="bun", hair_mat="M_CH_Hair_Grey", band="M_CH_WP_Under",
                        brow="M_CH_Hair_Grey", beard="short_grey", extras=["armor", "tag"], bulk=1.02,
                        desc="王沛 62 岁老将：瘦硬深肤短须，旧皮札甲、褪红衬袍、木腰牌「沛」（长枪另为道具）"),
    "NPC_WangShugao": dict(H=1.72, outfit="robe", top="M_CH_WS_Robe", pants="M_CH_WS_Robe", shoe="M_CH_WS_Shoe",
                           sash="M_CH_WS_Sash", hair="scholar_cap", beard="goatee", extras=["scroll"], bulk=0.95, cuff=1.35,
                           desc="王叔杲 41 岁建堡者：清瘦书吏气，蓝灰长衫、方巾、腰插建堡图卷"),
    "NPC_WangDe": dict(H=1.72, outfit="jacket", top="M_CH_WD_Coat", pants="M_CH_WD_Pants", shoe="M_CH_Straw",
                       sash="M_CH_WD_Sash", wrap="M_CH_Wrap", hair="bun", band="M_CH_Headband", extras=["knife", "tag"],
                       desc="王德 20 岁义师：短打、绑腿、短刀、木腰牌「德」"),
    "NPC_WangBingzhi": dict(H=1.70, outfit="robe", top="M_CH_WB_Robe", pants="M_CH_WB_Robe", shoe="M_CH_WB_Shoe",
                            skin="M_CH_Skin_Old", hair="melon_cap", brow="M_CH_Hair_White", beard="long_white", hunch=1.0,
                            bulk=0.92, desc="王秉之 1941：60+，瘦、背微驼，深褐长袍、瓜皮帽、白须（木拐另为道具）"),
    # ---- 1941 族亲（第一幕祠堂：族老、三派、族亲冷遇/亲善、老少群众） ----
    "NPC_ClanElder": dict(H=1.68, outfit="robe", top="M_CH_EL_Robe", pants="M_CH_EL_Robe", shoe="M_CH_EL_Shoe",
                          skin="M_CH_Skin_Old", hair="short", hair_mat="M_CH_Hair_Grey", brow="M_CH_Hair_Grey",
                          beard="short_grey", hunch=0.35, bulk=0.95, extras=["magua", "beads"],
                          desc="族老 1941：65 岁，黑褐长衫外罩黑马褂、念珠、灰短发短须；不戴帽、背只微弯，与王秉之区分（手杖另为道具）"),
    "NPC_ClanJiao": dict(H=1.70, outfit="robe", top="M_CH_JP_Robe", pants="M_CH_JP_Robe", shoe="M_CH_EL_Shoe",
                         sash="M_CH_JP_Sash", hair="short", hair_mat="M_CH_Hair_Grey", beard="goatee", bulk=1.1,
                         extras=["glasses", "ledger"],
                         desc="交谱派族老 1941：55 岁，微胖圆滑，石青长衫、圆眼镜、山羊须，腰间夹账本"),
    "NPC_ClanShao": dict(H=1.76, outfit="jacket", top="M_CH_SP_Coat", pants="M_CH_SP_Pants", shoe="M_CH_ClothShoe",
                         sash="M_CH_SP_Sash", wrap="M_CH_Wrap", hair="short", brow_tilt=16, bulk=1.02, cuff=1.2,
                         extras=["torch"],
                         desc="烧谱派青年 1941：22 岁，黑短打、褪红腰带、绑腿，皱眉，背后腰带斜插一支未点的火把"),
    "NPC_ClanCang": dict(H=1.58, outfit="robe", top="M_CH_CP_Ao", skirt="M_CH_CP_Skirt", pants="M_CH_CP_Skirt",
                         shoe="M_CH_ClothShoe", hair="back_bun", hem=0.03, flare=1.05, bulk=0.9, trim="M_CH_CP_Skirt",
                         extras=["ao_hem", "bundle"],
                         desc="藏谱派妇人 1941：42 岁，深青灰袄 + 黑长裙、脑后低髻，斜背灰绿包袱（藏谱用）"),
    "NPC_ClanUncle": dict(H=1.72, outfit="jacket", top="M_CH_UC_Coat", pants="M_CH_UC_Pants", shoe="M_CH_ClothShoe",
                          sash="M_CH_UC_Pants", hair="brim_hat", hair_mat="M_CH_UC_Hat", brow_tilt=14, bulk=1.04,
                          desc="族叔（族中冷遇）1941：45 岁，灰短褂黑裤、旧毡帽、皱眉——「你爹投了日本人，你还有脸回来？」"),
    "NPC_ClanGranny": dict(H=1.55, outfit="robe", top="M_CH_GM_Ao", skirt="M_CH_GM_Skirt", pants="M_CH_GM_Skirt",
                           shoe="M_CH_ClothShoe", skin="M_CH_Skin_Old", hair="back_bun", hair_mat="M_CH_Hair_White",
                           band="M_CH_GM_Band", brow="M_CH_Hair_White", brow_tilt=-12, hunch=0.7, bulk=0.9, hem=0.03,
                           trim="M_CH_GM_Skirt", extras=["ao_hem"],
                           desc="族婶婆（族中亲善）1941：68 岁，靛蓝袄黑裙、白发低髻、黑抹额、背驼——「孩子刚回来，先让他给他爹上炷香」"),
    "NPC_ClanBoy": dict(H=1.18, head=1.3, outfit="jacket", top="M_CH_BY_Coat", pants="M_CH_BY_Pants", shoe="M_CH_ClothShoe",
                        hair="short", bulk=0.95, cuff=1.15,
                        desc="族中孩童 1941：8 岁男孩，褪黄短褂、短发、大头比例；跟在族婶婆身边"),
    "NPC_ClanGirl": dict(H=1.50, head=1.12, outfit="jacket", top="M_CH_GL_Ao", pants="M_CH_GL_Pants", shoe="M_CH_ClothShoe",
                         hair="braid", ribbon="M_CH_GL_Ribbon", bulk=0.88, brow_tilt=-6,
                         desc="族中少女 1941：14 岁，旧红袄蓝裤、一根长辫系红头绳；跟着藏谱派妇人（母女）"),
    # ---- 1941 日军（第一幕祠堂/街市） ----
    "NPC_JpOfficer": dict(H=1.72, outfit="jacket", top="M_CH_JA_Khaki", pants="M_CH_JA_Khaki", shoe="M_CH_JA_Boot", boot=True,
                          wrap="M_CH_JA_Boot", sash="M_CH_JA_Leather", glove="M_CH_JA_Glove", hair="peaked_cap",
                          hair_mat="M_CH_JA_Khaki", brow_tilt=6, extras=["glasses", "boards", "gunto"],
                          desc="日本军官 1941：40 岁，黄呢军服、大檐帽红帽箍、白手套、圆眼镜、马靴、左胯军刀；克制而危险（祠堂/街市共用）"),
    "NPC_JpSoldier_A": dict(H=1.66, outfit="jacket", top="M_CH_JA_Khaki", pants="M_CH_JA_Khaki", shoe="M_CH_JA_Boot",
                            wrap="M_CH_JA_Wrap", sash="M_CH_JA_Leather", hair="helmet", hair_mat="M_CH_JA_Helmet", brow_tilt=10,
                            extras=["boards", "pouches", "bayonet", "rifle_back"],
                            desc="日本兵·步枪兵 1941：钢盔、绑腿、子弹盒、刺刀鞘、三八式斜背（随军官进祠堂）"),
    "NPC_JpSoldier_B": dict(H=1.68, outfit="jacket", top="M_CH_JA_Khaki", pants="M_CH_JA_Khaki", shoe="M_CH_JA_Boot",
                            wrap="M_CH_JA_Wrap", sash="M_CH_JA_Leather", hair="field_cap_flaps", hair_mat="M_CH_JA_Khaki",
                            brow_tilt=14, bulk=1.05, extras=["boards", "pouches", "bayonet", "canteen"],
                            desc="日本兵·搜捕兵 1941：战斗帽带护颈布、徒手（步枪另为道具握持），踹门抢箱/推搡小贩"),
    "NPC_JpSoldier_C": dict(H=1.64, outfit="jacket", top="M_CH_JA_KhakiDark", pants="M_CH_JA_KhakiDark", shoe="M_CH_JA_Boot",
                            wrap="M_CH_JA_Wrap", sash="M_CH_JA_Leather", hair="helmet", hair_mat="M_CH_JA_Helmet", brow_tilt=8,
                            extras=["boards", "pouches", "backpack", "canteen", "rifle_back"],
                            desc="日本兵·巡逻兵 1941：钢盔、背囊毛毯卷、水壶、三八式斜背（街市巡逻）"),
    # ---- 1941 小贩 ----
    "NPC_VendorVeg": dict(H=1.68, outfit="jacket", top="M_CH_VD_Coat", pants="M_CH_VD_Pants", shoe="M_CH_Straw",
                          sash="M_CH_VD_Pants", hair="straw_hat", hair_mat="M_CH_StrawHat", skin="M_CH_Skin_Dark",
                          brow_tilt=-8, cuff=1.25, bulk=0.96, extras=["apron"],
                          desc="小贩·菜贩 1941：50 岁，灰褐短褂卷袖、斗笠、蓝围裙、草鞋（扁担菜筐另为道具）"),
    "NPC_VendorGoods": dict(H=1.64, outfit="robe", top="M_CH_VG_Coat", pants="M_CH_VG_Coat", shoe="M_CH_ClothShoe",
                            hem=0.18, skin="M_CH_Skin_Old", hair="melon_cap", brow="M_CH_Hair_Grey", beard="short_grey",
                            brow_tilt=-10, hunch=0.3, extras=["apron"], apron="M_CH_Bedroll",
                            desc="小贩·杂货摊主 1941：60 岁，青灰短衫、旧瓜皮帽、灰短须、土黄围裙"),
    # ---- 1941 街坊（与族亲 4 人合计 8 个变体：老/少/男/女/伤/逃难） ----
    "NPC_TownOldMan": dict(H=1.64, outfit="robe", top="M_CH_TO_Robe", pants="M_CH_TO_Robe", shoe="M_CH_ClothShoe",
                           skin="M_CH_Skin_Old", hair="short", hair_mat="M_CH_Hair_White", brow="M_CH_Hair_White",
                           beard="long_white", hunch=0.8, bulk=0.9,
                           desc="街坊·老汉 1941：70 岁，旧褐长衫、白发长须、驼背"),
    "NPC_TownWoman": dict(H=1.57, outfit="robe", top="M_CH_TW_Ao", skirt="M_CH_GM_Skirt", pants="M_CH_GM_Skirt",
                          shoe="M_CH_ClothShoe", hair="headscarf", hair_mat="M_CH_TW_Scarf", hem=0.03, bulk=0.92,
                          trim="M_CH_GM_Skirt", brow_tilt=-10, extras=["ao_hem"],
                          desc="街坊·妇女 1941：35 岁，灰紫袄黑裙、灰包头巾，眉头发愁"),
    "NPC_TownInjured": dict(H=1.70, outfit="jacket", top="M_CH_TI_Coat", pants="M_CH_VD_Pants", shoe="M_CH_ClothShoe",
                            sash="M_CH_VD_Pants", hair="bandaged", brow_tilt=-6, extras=["sling"],
                            desc="街坊·伤者 1941：28 岁，头缠渗血绷带、右臂吊带（轰炸后）"),
    "NPC_TownRefugee": dict(H=1.70, outfit="jacket", top="M_CH_TR_Coat", pants="M_CH_VD_Pants", shoe="M_CH_Straw",
                            sash="M_CH_VD_Pants", wrap="M_CH_Wrap", hair="straw_hat", hair_mat="M_CH_StrawHat",
                            skin="M_CH_Skin_Dark", extras=["bedroll"],
                            desc="街坊·逃难者 1941：35 岁，土黄短褂绑腿、斗笠、背铺盖卷和包袱"),
}


def build_character(name, cfg=None):
    """cfg 不为空时用它代替 CAST[name]（例如只用来渲染照片、不单独出资产的人物）。"""
    c = cfg if cfg is not None else CAST[name]
    H = c["H"]
    h = H
    J = joints(H, c.get("hunch", 0.0), c.get("bulk", 1.0))
    rig = make_rig(J)
    S = Skin()
    hc, r = build_body(S, J, H, c)
    hm = c.get("hair_mat", "M_CH_Hair")
    hair = c.get("hair")
    if hair == "short":
        hair_short(S, hc, r, hm, h)
    elif hair == "bun":
        hair_bun(S, hc, r, hm, h, c.get("band"))
    elif hair == "scholar_cap":     # 方巾
        hair_short(S, hc, r, hm, h)
        S.add(*box(hc + Vector((0, 0.004 * h, r[2] * 0.75)), (r[0] * 2.05, r[1] * 2.0, 0.05 * h)), "M_CH_WS_Cap", W("Head"))
        S.add(*box(hc + Vector((0, 0.01 * h, r[2] * 0.75 + 0.035 * h)), (r[0] * 2.2, r[1] * 1.8, 0.03 * h)), "M_CH_WS_Cap", W("Head"))
        S.add(*box(hc + Vector((0, r[1] * 1.05, r[2] * 0.3)), (0.04 * h, 0.006 * h, 0.07 * h)), "M_CH_WS_Cap", W("Head"))
    elif hair == "back_bun":
        hair_back_bun(S, hc, r, hm, h, c.get("band"))
    elif hair == "braid":
        hair_braid(S, J, hc, r, hm, h, c.get("ribbon"))
    elif hair == "brim_hat":
        hair_short(S, hc, r, "M_CH_Hair", h)
        brim_hat(S, hc, r, hm, h)
    elif hair == "helmet":
        hair_short(S, hc, r, "M_CH_Hair", h)
        helmet(S, hc, r, hm, h)
    elif hair in ("field_cap", "field_cap_flaps"):
        hair_short(S, hc, r, "M_CH_Hair", h)
        field_cap(S, hc, r, hm, h, neck_flaps=hair.endswith("flaps"))
    elif hair == "peaked_cap":
        hair_short(S, hc, r, "M_CH_Hair", h)
        peaked_cap(S, hc, r, hm, h)
    elif hair == "straw_hat":
        hair_short(S, hc, r, "M_CH_Hair", h)
        straw_hat(S, hc, r, hm, h)
    elif hair == "headscarf":
        hair_short(S, hc, r, "M_CH_Hair", h)
        headscarf(S, hc, r, hm, h)
    elif hair == "bandaged":     # 伤者：头缠绷带，额前一片血迹
        hair_short(S, hc, r, hm, h)
        S.add(*rings_mesh([(hc + Vector((0, 0.004 * h, r[2] * 0.15)), r[0] * 1.1, r[1] * 1.08),
                           (hc + Vector((0, 0.004 * h, r[2] * 0.62)), r[0] * 1.06, r[1] * 1.04)], seg=10), "M_CH_Bandage", W("Head"))
        S.add(*box(hc + Vector((0.018 * h, -r[1] * 1.07, r[2] * 0.4)), (0.03 * h, 0.004 * h, 0.022 * h)), "M_CH_Blood", W("Head"))
    elif hair in HAIR_HOOKS:
        HAIR_HOOKS[hair](S, J, hc, r, hm, h, c)
    elif hair == "melon_cap":       # 瓜皮帽
        S.add(*ellipsoid(hc + Vector((0, 0.004 * h, 0.014 * h)), r[0] * 1.08, r[1] * 1.06, r[2] * 0.95, seg=10, rings=4, zmin=0.05),
              "M_CH_WB_Cap", W("Head"))
        S.add(*ellipsoid(hc + Vector((0, 0.004 * h, r[2] + 0.012 * h)), 0.008 * h, 0.008 * h, 0.008 * h, seg=6, rings=3),
              "M_PR_Tassel", W("Head"))
    beard = c.get("beard")
    chin = hc + Vector((0, -r[1] * 0.72, -r[2] * 0.62))
    if beard == "short_grey":
        S.add(*wedge(chin + Vector((0, 0, 0.012 * h)), 0.06 * h, 0.03 * h, 0.022 * h, 0.035 * h), "M_CH_Hair_Grey", W("Head"))
        S.add(*box(hc + Vector((0, -r[1] * 0.95, -0.022 * h)), (0.04 * h, 0.01 * h, 0.008 * h)), "M_CH_Hair_Grey", W("Head"))
    elif beard == "goatee":
        S.add(*wedge(chin + Vector((0, -0.004 * h, 0.004 * h)), 0.02 * h, 0.014 * h, 0.01 * h, 0.03 * h), "M_CH_Hair", W("Head"))
        S.add(*box(hc + Vector((0, -r[1] * 0.95, -0.022 * h)), (0.034 * h, 0.008 * h, 0.005 * h)), "M_CH_Hair", W("Head"))
    elif beard == "long_white":
        S.add(*wedge(chin + Vector((0, 0, 0.016 * h)), 0.055 * h, 0.03 * h, 0.012 * h, 0.12 * h), "M_CH_Hair_White",
              lambda p: {"Head": 0.7, "Neck": 0.3})
        S.add(*box(hc + Vector((0, -r[1] * 0.95, -0.022 * h)), (0.046 * h, 0.012 * h, 0.009 * h)), "M_CH_Hair_White", W("Head"))
    hipsW = W("Hips")
    tw = torso_weight(J)
    for e in c.get("extras", []):
        if e in EXTRA_HOOKS:
            EXTRA_HOOKS[e](S, J, h, c, tw, hipsW)
        elif e == "camera_bag":   # 右肩斜挎到左胯
            a = J["chest_t"] + Vector((-0.07 * h, 0, 0))
            b = Vector((0.1 * h, 0, 0.5 * h))
            for yy in (-0.068 * h, 0.066 * h):
                d = b - a
                mid = (a + b) / 2 + Vector((0, yy, 0))
                ang = math.degrees(math.atan2(d.x, d.z))
                S.add(*box(mid, (0.022 * h, 0.006 * h, d.length), rot=_eu(0, ang, 0)), "M_CH_WY41_Bag", tw)
            S.add(*box((0.11 * h, -0.03 * h, 0.47 * h), (0.04 * h, 0.09 * h, 0.07 * h)), "M_CH_WY41_Bag", hipsW)
        elif e == "pouch":
            S.add(*box((-0.085 * h, -0.05 * h, 0.47 * h), (0.035 * h, 0.03 * h, 0.05 * h)), "M_CH_Pouch", hipsW)
        elif e == "scroll":
            S.add(*tube((0.07 * h, -0.075 * h, 0.44 * h), (0.035 * h, -0.07 * h, 0.6 * h), 0.012 * h, 0.012 * h, seg=6),
                  "M_CH_Scroll", hipsW)
        elif e == "knife":
            S.add(*box((0.1 * h, 0.0, 0.43 * h), (0.02 * h, 0.03 * h, 0.17 * h), rot=_eu(18, 0, 0)),
                  "M_CH_Scabbard", hipsW)
            S.add(*box((0.1 * h, -0.02 * h, 0.53 * h), (0.016 * h, 0.016 * h, 0.05 * h)), "M_PR_WoodDark", hipsW)
        elif e == "tag":
            S.add(*box((-0.075 * h, -0.07 * h, 0.455 * h), (0.025 * h, 0.006 * h, 0.04 * h)), "M_CH_Tag", hipsW)
        elif e == "magua":      # 马褂：罩在长衫外的短褂，到胯，袖到肘
            bk = c.get("bulk", 1.0) * 1.07
            rings = []
            for z, rxx, ryy in ((0.45 * h, 0.104, 0.074), (0.56 * h, 0.092, 0.066), (0.64 * h, 0.098, 0.068),
                                (0.72 * h, 0.11, 0.07), (J["chest_t"].z - 0.002 * h, 0.117, 0.064)):
                rings.append((Vector((0, spine_y(J, z), z)), rxx * h * bk, ryy * h * bk))
            S.add(*rings_mesh(rings, seg=10, cap0=False), "M_CH_EL_Magua", tw)
            for s_, side in (("L", "Left"), ("R", "Right")):
                sg = 1 if s_ == "L" else -1
                S.add(*tube(J["arm" + s_] + Vector((sg * 0.01 * h, 0, 0)), J["elbow" + s_], 0.039 * h * bk, 0.034 * h * bk),
                      "M_CH_EL_Magua", W(side + "UpperArm"))
            for k in range(4):      # 对襟盘扣
                z = 0.5 * h + k * 0.07 * h
                S.add(*box((0, spine_y(J, z) - 0.073 * h * bk, z), (0.016 * h, 0.006 * h, 0.008 * h)), "M_CH_Tag", tw)
        elif e == "beads":      # 念珠：挂在胸前的一圈珠子
            nc = J["chest_t"]
            for k in range(14):
                a = math.pi * (0.15 + 0.7 * k / 13)
                p = Vector((0.07 * h * math.cos(a), nc.y - 0.06 * h * math.sin(a) - 0.012 * h, nc.z - 0.11 * h * math.sin(a)))
                S.add(*box(p, (0.013 * h, 0.013 * h, 0.013 * h)), "M_CH_Beads", W("Chest"))
        elif e == "glasses":    # 圆眼镜：两圈镜框 + 鼻梁
            fyy = hc.y - r[1] * 0.98
            for sx in (-1, 1):
                ring = [Vector((sx * 0.019 * h + 0.011 * h * math.cos(2 * math.pi * k / 8), fyy,
                                hc.z + 0.006 * h + 0.011 * h * math.sin(2 * math.pi * k / 8))) for k in range(8)]
                for k in range(8):
                    S.add(*tube(ring[k], ring[(k + 1) % 8], 0.0018 * h, 0.0018 * h, seg=4), "M_CH_Glasses", W("Head"))
            S.add(*box((0, fyy, hc.z + 0.008 * h), (0.016 * h, 0.003 * h, 0.003 * h)), "M_CH_Glasses", W("Head"))
        elif e == "ledger":     # 账本：夹在腰带左前
            S.add(*box((-0.07 * h, -0.085 * h, 0.47 * h), (0.07 * h, 0.018 * h, 0.1 * h), rot=_eu(0, 8, 0)), "M_CH_Ledger", hipsW)
            S.add(*box((-0.07 * h, -0.095 * h, 0.47 * h), (0.072 * h, 0.004 * h, 0.012 * h), rot=_eu(0, 8, 0)), "M_CH_Scroll", hipsW)
        elif e == "torch":      # 火把：斜插在背后腰带，缠布头朝上
            a = Vector((-0.06 * h, 0.08 * h, 0.4 * h))
            b = Vector((0.1 * h, 0.1 * h, 0.78 * h))
            S.add(*tube(a, b, 0.012 * h, 0.012 * h, seg=6), "M_PR_Wood", lambda p: W("Hips") if p.z < 0.56 * h else W("Chest"))
            d = (b - a).normalized()
            S.add(*tube(b - d * 0.07 * h, b + d * 0.03 * h, 0.022 * h, 0.018 * h, seg=6), "M_CH_Torch", W("Chest"))
        elif e == "ao_hem":     # 袄的下摆：盖在裙子外的一圈短摆
            bk = c.get("bulk", 1.0)
            S.add(*rings_mesh([(Vector((0, 0, 0.53 * h)), 0.1 * h * bk, 0.071 * h * bk),
                               (Vector((0, 0.002 * h, 0.43 * h)), 0.118 * h * bk, 0.083 * h * bk)], seg=12, cap0=False, cap1=False),
                  c["top"], skirt_weight(J, 0.53 * h))
        elif e == "bundle":     # 包袱：右肩斜挎到左后腰，一个方包袱 + 打结
            a = J["chest_t"] + Vector((-0.07 * h, 0, 0))
            b = Vector((0.09 * h, 0.06 * h, 0.5 * h))
            for yy in (-0.066 * h, 0.064 * h):
                d = b - a
                mid = (a + b) / 2 + Vector((0, yy, 0))
                ang = math.degrees(math.atan2(d.x, d.z))
                S.add(*box(mid, (0.03 * h, 0.006 * h, d.length), rot=_eu(0, ang, 0)), "M_CH_CP_Bundle", tw)
            S.add(*box((0.06 * h, 0.115 * h, 0.55 * h), (0.15 * h, 0.07 * h, 0.13 * h), rot=_eu(0, -10, 0)), "M_CH_CP_Bundle", tw)
            S.add(*ellipsoid((0.0, 0.08 * h, 0.64 * h), 0.022 * h, 0.018 * h, 0.018 * h, seg=6, rings=3), "M_CH_CP_Bundle", tw)
        elif e == "boards":     # 军装：肩章 + 红领章 + 前襟纽扣
            for s_, side in (("L", "Left"), ("R", "Right")):
                sg = 1 if s_ == "L" else -1
                S.add(*box(J["arm" + s_] + Vector((-sg * 0.03 * h, 0, 0.035 * h)), (0.07 * h, 0.03 * h, 0.006 * h)),
                      "M_CH_JA_Red", {side + "Shoulder": 0.5, "Chest": 0.5})
                S.add(*box(J["neck"] + Vector((sg * 0.022 * h, -0.024 * h, -0.004 * h)), (0.016 * h, 0.006 * h, 0.012 * h)),
                      "M_CH_JA_Red", W("Neck"))
            for k in range(4):
                z = 0.5 * h + k * 0.075 * h
                S.add(*box((0, spine_y(J, z) - 0.068 * h * c.get("bulk", 1.0), z), (0.01 * h, 0.006 * h, 0.01 * h)),
                      "M_CH_JA_Gold", tw)
        elif e == "gunto":      # 军刀：左胯挂鞘，刀柄朝前上
            S.add(*box((0.1 * h, 0.03 * h, 0.36 * h), (0.018 * h, 0.03 * h, 0.42 * h), rot=_eu(22, 0, 0)), "M_CH_JA_Steel", hipsW)
            S.add(*box((0.1 * h, -0.07 * h, 0.6 * h), (0.016 * h, 0.022 * h, 0.12 * h), rot=_eu(22, 0, 0)), "M_CH_JA_Leather", hipsW)
            S.add(*box((0.1 * h, -0.05 * h, 0.55 * h), (0.03 * h, 0.035 * h, 0.006 * h), rot=_eu(22, 0, 0)), "M_CH_JA_Gold", hipsW)
        elif e == "pouches":    # 子弹盒：腰带前两只、后一只
            for x in (-0.055, 0.055):
                S.add(*box((x * h, -0.08 * h, 0.5 * h), (0.05 * h, 0.03 * h, 0.035 * h)), "M_CH_JA_Leather", hipsW)
            S.add(*box((0, 0.08 * h, 0.5 * h), (0.07 * h, 0.03 * h, 0.04 * h)), "M_CH_JA_Leather", hipsW)
        elif e == "bayonet":    # 刺刀鞘：左胯
            S.add(*box((0.1 * h, 0.01 * h, 0.43 * h), (0.014 * h, 0.022 * h, 0.2 * h), rot=_eu(10, 0, 0)), "M_CH_JA_Boot", hipsW)
        elif e == "rifle_back":  # 三八式斜背：右肩到左腰后，枪口朝上
            a = Vector((0.11 * h, 0.085 * h, 0.3 * h))
            b = Vector((-0.12 * h, 0.09 * h, 0.95 * h))
            d = (b - a).normalized()
            S.add(*tube(a, a + d * 0.45 * (b - a).length, 0.02 * h, 0.018 * h, seg=6), "M_PR_Wood",
                  lambda p: W("Hips") if p.z < 0.56 * h else W("Chest"))
            S.add(*tube(a + d * 0.45 * (b - a).length, b, 0.01 * h, 0.009 * h, seg=6), "M_CH_JA_Steel", W("Chest"))
            S.add(*box((0, 0.068 * h, 0.66 * h), (0.012 * h, 0.006 * h, 0.4 * h), rot=_eu(0, 35, 0)), "M_CH_JA_Leather", tw)
        elif e == "backpack":   # 背囊 + 卷起的毛毯
            S.add(*box((0, 0.1 * h, 0.68 * h), (0.15 * h, 0.06 * h, 0.14 * h)), "M_CH_JA_KhakiDark", tw)
            S.add(*tube((-0.09 * h, 0.1 * h, 0.77 * h), (0.09 * h, 0.1 * h, 0.77 * h), 0.022 * h, 0.022 * h, seg=6),
                  "M_CH_JA_Wrap", W("Chest"))
        elif e == "canteen":    # 水壶：右胯
            S.add(*ellipsoid((-0.1 * h, 0.02 * h, 0.45 * h), 0.02 * h, 0.014 * h, 0.032 * h, seg=6, rings=3), "M_CH_JA_Helmet", hipsW)
        elif e == "apron":      # 围裙：前片到膝
            S.add(*box((0, -0.078 * h * c.get("bulk", 1.0), 0.4 * h), (0.16 * h, 0.006 * h, 0.22 * h)), c.get("apron", "M_CH_VD_Apron"),
                  {"Hips": 0.6, "LeftUpperLeg": 0.2, "RightUpperLeg": 0.2})
            S.add(*box((0, -0.075 * h, 0.66 * h), (0.11 * h, 0.006 * h, 0.12 * h)), c.get("apron", "M_CH_VD_Apron"), tw)
        elif e == "sling":      # 伤者：右前臂吊带 + 绷带
            S.add(*tube(J["elbowR"], J["wristR"], 0.032 * h, 0.028 * h, seg=6), "M_CH_Bandage", W("RightLowerArm"))
            S.add(*box((0, -0.06 * h, 0.7 * h), (0.012 * h, 0.006 * h, 0.28 * h), rot=_eu(0, -40, 0)), "M_CH_Bandage", tw)
            S.add(*box((-0.035 * h, -0.072 * h, 0.66 * h), (0.02 * h, 0.004 * h, 0.03 * h)), "M_CH_Blood", tw)
        elif e == "bedroll":    # 逃难：背上铺盖卷 + 包袱
            S.add(*tube((-0.11 * h, 0.1 * h, 0.72 * h), (0.11 * h, 0.1 * h, 0.72 * h), 0.04 * h, 0.04 * h, seg=8), "M_CH_Bedroll", W("Chest"))
            S.add(*box((0, 0.1 * h, 0.58 * h), (0.14 * h, 0.07 * h, 0.12 * h)), "M_CH_CP_Bundle", tw)
            for sx in (-1, 1):
                S.add(*box((sx * 0.06 * h, -0.07 * h, 0.66 * h), (0.012 * h, 0.006 * h, 0.22 * h)), "M_CH_Bedroll", tw)
        elif e == "armor":
            # 皮札甲：胸背甲 + 甲片横条 + 披膊 + 前后甲裙
            rings = []
            for z, rxx, ryy in ((0.49 * h, 0.1, 0.072), (0.6 * h, 0.095, 0.068), (0.7 * h, 0.108, 0.072), (0.79 * h, 0.114, 0.066)):
                rings.append((Vector((0, spine_y(J, z), z)), rxx * h, ryy * h))
            S.add(*rings_mesh(rings, seg=10), "M_CH_WP_Leather", tw)
            for k in range(6):
                z = 0.52 * h + k * 0.045 * h
                S.add(*box((0, -0.073 * h, z), (0.17 * h, 0.012 * h, 0.012 * h)), "M_CH_WP_Plate", tw)
                S.add(*box((0, 0.071 * h, z), (0.17 * h, 0.012 * h, 0.012 * h)), "M_CH_WP_Plate", tw)
            for s, side in (("L", "Left"), ("R", "Right")):
                sg = 1 if s == "L" else -1
                S.add(*box(J["arm" + s] + Vector((sg * 0.03 * h, 0, 0.022 * h)), (0.09 * h, 0.1 * h, 0.03 * h), rot=_eu(0, -sg * 15, 0)),
                      "M_CH_WP_Leather", W(side + "UpperArm"))
                S.add(*box(J["arm" + s] + Vector((sg * 0.05 * h, 0, 0.0)), (0.07 * h, 0.105 * h, 0.04 * h), rot=_eu(0, -sg * 25, 0)),
                      "M_CH_WP_Plate", W(side + "UpperArm"))
                # 甲裙（左右各一，前后两片）
                for yy in (-0.07 * h, 0.07 * h):
                    S.add(*box((sg * 0.05 * h, yy, 0.40 * h), (0.09 * h, 0.014 * h, 0.15 * h)), "M_CH_WP_Leather",
                          {"Hips": 0.4, side + "UpperLeg": 0.6})
                    for k in range(3):
                        S.add(*box((sg * 0.05 * h, yy * 1.08, 0.35 * h + k * 0.045 * h), (0.092 * h, 0.006 * h, 0.01 * h)),
                              "M_CH_WP_Plate", {"Hips": 0.4, side + "UpperLeg": 0.6})
    S.to_object(name, rig)
    return rig


# ---------------------------------------------------------------- 道具
def build_spear():
    mb = K.MB()
    mb.cyl(0, 0, 0, 2.3, 0.017, "M_PR_Wood", seg=8)
    mb.cyl(0, 0, 0, 0.06, 0.022, "M_PR_Iron", seg=8)                 # 鐏
    mb.cyl(0, 0, 2.28, 2.36, 0.022, "M_PR_Iron", seg=8)              # 銎
    mb.cyl(0, 0, 2.18, 2.3, 0.065, "M_PR_Tassel", seg=10, r_top=0.02)  # 褪红枪缨
    mb.prism([(-0.035, 2.36), (0.035, 2.36), (0.0, 2.6)], "y", -0.006, 0.006, "M_PR_Iron")
    mb.prism([(-0.006, 2.36), (0.006, 2.36), (0.0, 2.6)], "x", -0.014, 0.014, "M_PR_Iron")
    mb.to_object("PROP_Spear_Pei")


def build_cane():
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.88, 0.014, "M_PR_WoodDark", seg=6, r_top=0.016)
    mb.prism([(0, 0.86), (0.012, 0.88), (0.12, 0.92), (0.11, 0.95)], "y", -0.016, 0.016, "M_PR_WoodDark")
    mb.to_object("PROP_Cane_Bingzhi")


def build_staff():
    """族老的手杖：直杆、杖头圆疙瘩、缠一道红绳（比王秉之的拐长、直）。"""
    mb = K.MB()
    mb.cyl(0, 0, 0, 1.22, 0.014, "M_PR_WoodDark", seg=6, r_top=0.017)
    mb.cyl(0, 0, 1.2, 1.28, 0.03, "M_PR_WoodDark", seg=8, r_top=0.022)
    mb.cyl(0, 0, 0.95, 0.99, 0.02, "M_CH_Beads", seg=6)
    mb.to_object("PROP_Staff_Elder")


def build_abacus():
    """王叔杲的十三档算盘（平放，底在 z=0）。"""
    mb = K.MB()
    L, Wd, T = 0.32, 0.13, 0.025
    for y in (-Wd / 2, Wd / 2 - 0.012):
        mb.box(-L / 2, y, 0, L / 2, y + 0.012, T, "M_PR_WoodDark")
    for x in (-L / 2, L / 2 - 0.012):
        mb.box(x, -Wd / 2, 0, x + 0.012, Wd / 2, T, "M_PR_WoodDark")
    beam = Wd / 2 - 0.045
    mb.box(-L / 2, beam - 0.004, 0, L / 2, beam + 0.004, T, "M_PR_WoodDark")
    for i in range(13):
        x = -L / 2 + 0.02 + i * (L - 0.04) / 12
        mb.box(x - 0.0015, -Wd / 2, T / 2 - 0.0015, x + 0.0015, Wd / 2, T / 2 + 0.0015, "M_PR_Iron")
        for k in range(5):
            y = -Wd / 2 + 0.018 + k * 0.012 + (0.012 if k == 0 and i % 3 == 0 else 0)
            mb.box(x - 0.008, y, T / 2 - 0.006, x + 0.008, y + 0.01, T / 2 + 0.006, "M_PR_Bead")
        for k in range(2):
            y = beam + 0.008 + k * 0.012
            mb.box(x - 0.008, y, T / 2 - 0.006, x + 0.008, y + 0.01, T / 2 + 0.006, "M_PR_Bead")
    mb.to_object("PROP_Abacus")


# ---------------------------------------------------------------- 动画
def _rot(axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis)


def set_rot(rig, bname, R):
    pb = rig.pose.bones[bname]
    M = pb.bone.matrix_local.to_3x3()
    pb.rotation_mode = "QUATERNION"
    pb.rotation_quaternion = (M.inverted() @ R @ M).to_quaternion()


def key_pose(rig, frame, pose, hips_up=0.0):
    for b, R in pose.items():
        set_rot(rig, b, R)
        rig.pose.bones[b].keyframe_insert("rotation_quaternion", frame=frame)
    hb = rig.pose.bones["Hips"]
    hb.location = (0, hips_up, 0)
    hb.keyframe_insert("location", frame=frame)


def pose_at(t, kind):
    """t ∈ [0,1) 一个循环内的相位。返回 {骨骼: 旋转矩阵(骨架静止空间)}。"""
    I = Matrix.Identity(3)
    s = math.sin(2 * math.pi * t)
    c2 = math.cos(4 * math.pi * t)
    if kind == "idle":
        breath = math.sin(2 * math.pi * t)
        P = {"Chest": _rot("X", 1.2 * breath), "Spine": I, "Head": _rot("X", -0.8 * breath), "Neck": I}
        for side, sg in (("Left", 1), ("Right", -1)):
            P[side + "UpperArm"] = _rot("X", -4) @ _rot("Y", sg * 76)
            P[side + "LowerArm"] = _rot("Z", -sg * 12)
            P[side + "UpperLeg"] = I
            P[side + "LowerLeg"] = I
            P[side + "Foot"] = I
        return P, 0.0
    if kind == "walk":
        th, kn, arm, fa, lean, bob = 24, 38, 18, 18, 3, 0.022
    else:   # run
        th, kn, arm, fa, lean, bob = 40, 85, 32, 80, 11, 0.05
    P = {"Spine": _rot("X", lean * 0.5) @ _rot("Z", 4 * s), "Chest": _rot("X", lean * 0.5) @ _rot("Z", 3 * s),
         "Neck": I, "Head": _rot("X", -lean * 0.8)}
    for side, sg, ph in (("Left", 1, 0.0), ("Right", -1, 0.5)):
        ss = math.sin(2 * math.pi * (t + ph))
        cc = math.cos(2 * math.pi * (t + ph))
        swing = -th * ss                                  # 负 = 向前(-Y)
        knee = kn * max(0.0, cc) * (1.0 if kind == "run" else 1.0) + 6
        P[side + "UpperLeg"] = _rot("X", swing)
        P[side + "LowerLeg"] = _rot("X", knee)
        P[side + "Foot"] = _rot("X", -(swing + knee) * 0.45)
        P[side + "UpperArm"] = _rot("X", arm * ss) @ _rot("Y", sg * 74)
        P[side + "LowerArm"] = _rot("Z", -sg * (fa + 10 * max(0.0, -ss)))
    return P, bob * (0.5 + 0.5 * c2)


def build_anim(kind):
    rig = build_character("CH_WangYan_1941")
    scene = bpy.context.scene
    scene.render.fps = 24
    period = {"idle": 48, "walk": 24, "run": 16}[kind]
    scene.frame_start, scene.frame_end = 0, period
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    act = bpy.data.actions.new(kind.capitalize())
    rig.animation_data_create()
    rig.animation_data.action = act
    steps = period // (4 if kind == "idle" else 2)
    for i in range(steps + 1):
        f = round(i * period / steps)
        P, up = pose_at((f / period) % 1.0, kind)
        key_pose(rig, f, P, up)
    bpy.ops.object.mode_set(mode="OBJECT")


# ---------------------------------------------------------------- 第一幕动作（关键帧手摆，Humanoid 共用）
# 手臂参数 (fwd, side)：都从「自然下垂」量起——fwd 向前抬的角度（90 = 平举向前，140 = 举过头），
# side 向外侧张开的角度（90 = T 姿势；负值 = 向身体内侧收，手到对侧胯/胸前）。
# 前臂 _fore(sg, a) 向前屈肘 a 度；脊柱/头 _rot("X", +a) 前倾/低头；大腿 _rot("X", -a) 前抬，小腿 _rot("X", +a) 后屈。
def _arm(sg, fwd=0.0, side=0.0):
    return _rot("X", -fwd) @ _rot("Y", sg * (88.0 - side))


def _fore(sg, bend):
    return _rot("Z", -sg * bend)


def _base():
    P, _ = pose_at(0.0, "idle")
    return dict(P)


def _pose(**kw):
    """从待机姿势出发，按关键字覆盖骨骼：L/R 臂 = (fwd, side)，LF/RF 前臂 = 屈肘度数，其余为骨骼名 → 矩阵。"""
    P = _base()
    for k, v in kw.items():
        if k in ("L", "R"):
            sg = 1 if k == "L" else -1
            P[("Left" if k == "L" else "Right") + "UpperArm"] = _arm(sg, *v)
        elif k in ("LF", "RF"):
            sg = 1 if k == "LF" else -1
            P[("Left" if k == "LF" else "Right") + "LowerArm"] = _fore(sg, v)
        else:
            P[k] = v
    return P


def _legs(P, thigh=0.0, shin=0.0, foot=0.0, side=None):
    for s in (("Left", "Right") if side is None else (side,)):
        P[s + "UpperLeg"] = _rot("X", -thigh)
        P[s + "LowerLeg"] = _rot("X", shin)
        P[s + "Foot"] = _rot("X", foot)
    return P


def gesture_keys(kind):
    """返回 (总帧数, [(帧, 姿势, 髋高偏移 m)])。24 fps；髋高按 1.75 m 基准人物，Humanoid 会按身高缩放。"""
    X = lambda a: _rot("X", a)
    Z = lambda a: _rot("Z", a)
    if kind in GESTURE_HOOKS:
        return GESTURE_HOOKS[kind]()
    if kind == "TalkLoop":          # 说话：右手在胸前比划，轻点头（族老、三派、军官共用）
        return 48, [(0, _pose(R=(50, 10), RF=60, Head=X(2)), 0),
                    (12, _pose(R=(62, 22), RF=40, Head=X(-3), Neck=Z(4)), 0),
                    (24, _pose(R=(45, 8), RF=72, Head=X(4)), 0),
                    (36, _pose(R=(66, 16), RF=30, Head=X(-2), Neck=Z(-4)), 0),
                    (48, _pose(R=(50, 10), RF=60, Head=X(2)), 0)]
    if kind == "ArgueLoop":         # 争吵：前倾、双手挥动、头往前戳（春祭争执）
        return 36, [(0, _pose(Spine=X(8), Chest=X(6), R=(70, 15), RF=50, L=(30, 10), LF=40, Head=X(-6)), 0),
                    (9, _pose(Spine=X(12), Chest=X(8), R=(100, 5), RF=20, L=(45, 15), LF=70, Head=X(4)), 0),
                    (18, _pose(Spine=X(6), Chest=X(4), R=(60, 30), RF=80, L=(80, 10), LF=20, Head=X(-8)), 0),
                    (27, _pose(Spine=X(12), Chest=X(9), R=(95, 0), RF=30, L=(40, 10), LF=60, Head=X(6)), 0),
                    (36, _pose(Spine=X(8), Chest=X(6), R=(70, 15), RF=50, L=(30, 10), LF=40, Head=X(-6)), 0)]
    if kind == "CowerLoop":         # 躲闪：缩身半蹲、双臂护头、发抖（街坊、小贩）
        def k(f, d):
            P = _pose(Spine=X(18 + d), Chest=X(12), Head=X(20), L=(130, 25), LF=115, R=(130, 25), RF=115)
            return (f, _legs(P, 35, 60, -25), -0.14)
        return 12, [k(0, 0), k(3, 2), k(6, -1), k(9, 2), k(12, 0)]
    if kind == "WatchLoop":         # 围观：双手攥在身前、头随事件慢慢转
        return 72, [(0, _pose(L=(28, -12), LF=70, R=(28, -12), RF=70, Head=X(6), Neck=Z(10)), 0),
                    (36, _pose(L=(28, -12), LF=76, R=(28, -12), RF=76, Head=X(3), Neck=Z(-12)), 0),
                    (72, _pose(L=(28, -12), LF=70, R=(28, -12), RF=70, Head=X(6), Neck=Z(10)), 0)]
    if kind == "AttentionLoop":     # 军官站定：挺胸收腹、两臂贴身、下巴微抬（进祠堂站定后才开口）
        return 72, [(0, _pose(Chest=X(-4), Head=X(-4), L=(0, 3), LF=4, R=(0, 3), RF=4), 0),
                    (36, _pose(Chest=X(-5), Head=X(-3), L=(0, 3), LF=5, R=(0, 3), RF=5), 0),
                    (72, _pose(Chest=X(-4), Head=X(-4), L=(0, 3), LF=4, R=(0, 3), RF=4), 0)]
    if kind == "Beckon":            # 族老「跟我来」：右手抬到身侧往回招两下
        return 40, [(0, _base(), 0),
                    (10, _pose(R=(70, 30), RF=80, Head=Z(-15)), 0),
                    (18, _pose(R=(75, 35), RF=20, Head=Z(-15)), 0),
                    (26, _pose(R=(70, 30), RF=85, Head=Z(-15)), 0),
                    (34, _pose(R=(75, 35), RF=20, Head=Z(-10)), 0),
                    (40, _base(), 0)]
    if kind == "IncenseBow":        # 王砚上香：双手捧香举到额前，三拜（结束回站姿）
        hold = dict(L=(75, -15), LF=100, R=(75, -15), RF=100)
        keys = [(0, _base(), 0), (12, _pose(**hold, Head=X(4)), 0)]
        for i in range(3):
            f = 18 + i * 22
            keys += [(f + 8, _pose(**hold, Spine=X(30), Chest=X(10), Head=X(10)), 0), (f + 20, _pose(**hold, Head=X(4)), 0)]
        keys += [(96, _base(), 0)]
        return 96, keys
    if kind == "KneelPray":         # 跪拜：双膝跪地、合手胸前、俯身，停在最后一帧
        hands = dict(L=(55, -22), LF=95, R=(55, -22), RF=95)
        return 48, [(0, _base(), 0),
                    (16, _legs(_pose(Spine=X(6), **hands), 50, 90, -20), -0.25),
                    (30, _legs(_pose(Spine=X(10), Chest=X(6), Head=X(8), **hands), 0, 90, 60), -0.43),
                    (48, _legs(_pose(Spine=X(32), Chest=X(16), Head=X(14), **hands), 0, 90, 60), -0.45)]
    if kind == "TouchFlag":         # 指尖触旗：半蹲、右手向前下方伸出，停住
        return 40, [(0, _base(), 0),
                    (18, _legs(_pose(Spine=X(25), Chest=X(10), Head=X(15), R=(60, 5), RF=25), 40, 70, -30), -0.18),
                    (40, _legs(_pose(Spine=X(32), Chest=X(14), Head=X(20), R=(78, 5), RF=8), 45, 80, -35), -0.22)]
    if kind == "DrawSword":         # 军官拔刀：右手横过身前到左胯握柄 → 拔出向前斜指，停住
        return 36, [(0, _base(), 0),
                    (12, _pose(Spine=Z(-10), R=(30, -38), RF=55, L=(10, 8), LF=30), 0),
                    (22, _pose(Spine=Z(6), R=(100, 18), RF=25, L=(0, 3), LF=15), 0),
                    (36, _pose(Spine=Z(4), Chest=X(-3), R=(85, 8), RF=5, L=(0, 3), LF=10), 0)]
    if kind == "Push":              # 日本兵推搡：收手蓄力 → 前冲双手猛推 → 回收
        return 30, [(0, _base(), 0),
                    (8, _pose(Spine=X(-4), L=(40, 5), LF=100, R=(40, 5), RF=100), 0),
                    (14, _legs(_legs(_pose(Spine=X(18), Chest=X(8), L=(90, -5), LF=5, R=(90, -5), RF=5), 35, 30, -10, "Left"),
                               -20, 5, 10, "Right"), -0.04),
                    (30, _pose(Spine=X(6), L=(30, 5), LF=40, R=(30, 5), RF=40), 0)]
    if kind == "Fall":              # 小贩被推倒：后仰踉跄、双臂乱抓 → 坐倒在地、手撑身后，停住
        return 36, [(0, _base(), 0),
                    (8, _legs(_pose(Spine=X(-15), Head=X(-10), L=(60, 50), LF=30, R=(60, 50), RF=30), -15, 10, 0), 0),
                    (20, _legs(_pose(Spine=X(-25), Chest=X(-10), Head=X(5), L=(-30, 25), LF=10, R=(-30, 25), RF=10), 60, 40, -10), -0.5),
                    (36, _legs(_pose(Spine=X(-20), Chest=X(-6), Head=X(10), L=(-40, 20), LF=5, R=(-40, 20), RF=5), 85, 30, -20), -0.8)]
    raise ValueError(kind)


GESTURES = ("TalkLoop", "ArgueLoop", "CowerLoop", "WatchLoop", "AttentionLoop", "Beckon", "IncenseBow", "KneelPray",
            "TouchFlag", "DrawSword", "Push", "Fall")


def build_gesture(kind):
    rig = build_character("CH_WangYan_1941")
    scene = bpy.context.scene
    scene.render.fps = 24
    total, keys = gesture_keys(kind)
    scene.frame_start, scene.frame_end = 0, total
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    act = bpy.data.actions.new(kind)
    rig.animation_data_create()
    rig.animation_data.action = act
    for f, P, up in keys:
        key_pose(rig, f, P, up)
    bpy.ops.object.mode_set(mode="OBJECT")


# ---------------------------------------------------------------- 注册
def recipes():
    R = {}
    for n in CAST:
        cat = "Characters"
        R[n] = (cat, (lambda nm=n: build_character(nm)))
    R["PROP_Spear_Pei"] = ("Props", build_spear)
    R["PROP_Cane_Bingzhi"] = ("Props", build_cane)
    R["PROP_Abacus"] = ("Props", build_abacus)
    R["PROP_Staff_Elder"] = ("Props", build_staff)
    for k in ("Idle", "Walk", "Run"):
        R[f"CH_WangYan_1941@{k}"] = ("Characters", (lambda kk=k.lower(): build_anim(kk)))
    for g in GESTURES:
        R[f"CH_WangYan_1941@{g}"] = ("Characters", (lambda gg=g: build_gesture(gg)))
    return R
