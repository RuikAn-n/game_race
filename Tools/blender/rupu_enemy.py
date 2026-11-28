"""
《入谱》第三幕 1560 守城 · 倭寇四兵种、两个 Boss、攻城与守城道具、战斗动作
（Blender bpy，程序化白模；由 build_yongchang.py 统一生成/导出，recipes() 返回 {资产名: (分类, 生成函数)}）
=====================================================================================================

对应 Docs/入谱_当前建模缺口清单.md 第四节；说明文档 Docs/act3_enemies.md。

约定：
  - 敌人/Boss 用 rupu_char 的 22 骨 Humanoid 骨架（build_character + 本模块的 HAIR/EXTRA 钩子，钩子名带 en_/bs_ 前缀）。
  - 武器是独立 Props，原点在握把。挂法：武器作为人物 `SOCKET_Hand_R` / `SOCKET_Hand_L`（挂在手骨上的空物体）的子物体，
    局部位置/旋转全 0。武器局部轴：+Z = 刃/弓臂方向（虎口方向），-Y = 刃口/正面（指节方向）。
  - Boss 阶段 = 同一骨架上的多个蒙皮子物体（Phase1_* / Phase12_* / Phase3_*），团结里按阶段显隐；
    FX_* 特效挂点、WEAK_* 弱点、SOCKET_* 挂点都是挂在骨骼上的空物体。
  - 动作：<模型>@<动作>，动作名带 EN_/BS_ 前缀；姿势用本模块的 Poser（FK + 两骨 IK，武器握持按插槽求解）。
  - 道具会动/切状态的部件是固定名字的子物体（Door_L/R、Bar、Broken、Wheel、Barrel、Ram、Wheel_FL…），
    物体旋转恒为 0，枢轴 = 物体原点。
"""
import math
import random

import bpy
from mathutils import Matrix, Vector

import rupu_kit as K
import rupu_char as C
from rupu_char import W, box, ellipsoid, rings_mesh, tube, wedge, _eu

# ================================================================ 颜色（低饱和；M_EN_ 敌人 / M_BS_ Boss / M_SG_ 攻守城）
ENEMY_PALETTE = {
    "M_EN_Skin": "#b99a7a", "M_EN_SkinDark": "#9c7656", "M_EN_Hair": "#1c1a18",
    "M_EN_SW_Kosode": "#3e4652", "M_EN_SW_Hakama": "#4a4438", "M_EN_SW_CoatB": "#6a6252", "M_EN_SW_PantsB": "#4a463c",
    "M_EN_AR_Kosode": "#7d6c4a", "M_EN_AR_Hakama": "#4f4a3c", "M_EN_AR_CoatB": "#6e6650", "M_EN_AR_PantsB": "#57524a",
    "M_EN_FP_Coat": "#6e3e2e", "M_EN_FP_Pants": "#3e3632", "M_EN_FP_CoatB": "#5e4a3c", "M_EN_FP_PantsB": "#45403a",
    "M_EN_SH_Kosode": "#3a3a38", "M_EN_SH_Hakama": "#45413a", "M_EN_SH_CoatB": "#5a5448", "M_EN_SH_PantsB": "#4a4640",
    "M_EN_Band": "#d0c6ae", "M_EN_BandRed": "#8a3a2e", "M_EN_Straw": "#a08a5a", "M_EN_Jingasa": "#3a3632",
    "M_EN_Leather": "#4a3626", "M_EN_Lacquer": "#2e2a26", "M_EN_Lace": "#6e3a30", "M_EN_Cord": "#7a3a30",
    "M_EN_Wrap": "#b8ad94", "M_EN_Padded": "#6e6450", "M_EN_Stud": "#8f7a44", "M_EN_Hood": "#4a4640",
    "M_EN_Steel": "#8a8e8e", "M_EN_Iron": "#3e4042", "M_EN_HiltWrap": "#26221e", "M_EN_Wood": "#6b5039",
    "M_EN_WoodDark": "#3e2f24", "M_EN_Rattan": "#7a5a3a", "M_EN_Bamboo": "#9a8a5a", "M_EN_String": "#d8d0bc",
    "M_EN_Fletch": "#d6d0c0", "M_EN_Clay": "#7a5a40", "M_EN_ClayDark": "#4a3a2e", "M_EN_Fuse": "#c8b890",
    "M_EN_Rope": "#a89670", "M_EN_Basket": "#8a7448", "M_EN_ShieldFace": "#6a5a44", "M_EN_ShieldMark": "#7a2e24",
    "M_EN_Sheath": "#2a2420",
}
BOSS_PALETTE = {
    "M_BS_CY_Skin": "#a87a5a", "M_BS_CY_Hair": "#5a2a20", "M_BS_CY_Vest": "#7a3a2c", "M_BS_CY_Pants": "#3a3430",
    "M_BS_CY_Armor": "#3a3330", "M_BS_CY_Plate": "#5a4a3e", "M_BS_CY_Mino": "#8a7a50", "M_BS_CY_Burn": "#1e1a17",
    "M_BS_CY_Pot": "#6a4632", "M_BS_CY_Ember": "#C4552E", "M_BS_CY_Wrap": "#a89a80", "M_BS_CY_Band": "#8a3a2e",
    "M_BS_CY_Chain": "#4a4a48",
    "M_BS_GW_Skin": "#b0906e", "M_BS_GW_Armor": "#2a2a2e", "M_BS_GW_Lace": "#6e2a26", "M_BS_GW_Gold": "#8f7a44",
    "M_BS_GW_Mask": "#6a2620", "M_BS_GW_MaskDark": "#1e1a18", "M_BS_GW_Robe": "#3a3e48", "M_BS_GW_Hakama": "#2e2c2a",
    "M_BS_GW_Flag": "#c9c2b0", "M_BS_GW_FlagMark": "#2a2624", "M_BS_GW_Crack": "#141210", "M_BS_GW_Fur": "#d8d0c0",
    "M_BS_Steel": "#8a8e90", "M_BS_Wood": "#4a3626", "M_BS_Handle": "#2a2220", "M_BS_Iron": "#3a3c3e",
}
SIEGE_PALETTE = {
    "M_SG_Bamboo": "#9a8a5a", "M_SG_Wood": "#6b5039", "M_SG_WoodDark": "#3e2f24", "M_SG_WoodWet": "#4e4034",
    "M_SG_Iron": "#3e4042", "M_SG_Bronze": "#5a4a32", "M_SG_Rope": "#a89670", "M_SG_Hide": "#6e5a44",
    "M_SG_HideDark": "#4e4032", "M_SG_Straw": "#9a8658", "M_SG_Char": "#1e1a17", "M_SG_Ember": "#C4552E",
    "M_SG_Sail": "#a49a80", "M_SG_Water": "#4F6B6A", "M_SG_Sand": "#9b8f6e", "M_SG_Cloth": "#b8ad94",
    "M_SG_Oil": "#2a2420", "M_SG_Clay": "#7a5a40", "M_SG_ClayDark": "#4a3a2e", "M_SG_Rubble": "#6e6e66",
    "M_SG_Scorch": "#2a2622", "M_SG_Earth": "#6a5e48", "M_SG_Blood": "#4a1a16", "M_SG_Brick": "#6e6a62",
    "M_SG_Powder": "#3a3632", "M_SG_Ball": "#2e3032", "M_SG_Bandage": "#d6d0c0",
}
K.PALETTE.update(ENEMY_PALETTE)
K.PALETTE.update(BOSS_PALETTE)
K.PALETTE.update(SIEGE_PALETTE)


# ================================================================ 小工具
def _R(axis, deg):
    return Matrix.Rotation(math.radians(deg), 3, axis)


def _ypr(t):
    """(前倾 pitch, 左转 yaw, 左倾 roll) 度 → 矩阵；与 rupu_char 一致：+X 前倾、+Z 向左转、+Y 向左侧倾。"""
    t = tuple(t) + (0, 0, 0)
    return _R("Z", t[1]) @ _R("X", t[0]) @ _R("Y", t[2])


def mb_add(mb, vf, mat):
    """把 rupu_char 几何原语（verts, faces）加进 K.MB（受 mb.at 变换影响）。"""
    verts, faces = vf
    b = mb.addv(verts)
    for fc in faces:
        mb.face([b + i for i in fc], mat)


def obj(mb, name, loc=(0.0, 0.0, 0.0), uv=0.5):
    ob = mb.to_object(name, uv_scale=uv)
    ob.location = loc
    return ob


def empty(name, loc, parent=None, kind="SPHERE", size=0.1):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind
    e.empty_display_size = size
    bpy.context.scene.collection.objects.link(e)
    if parent is not None:
        e.parent = parent
    e.location = loc
    return e


def bone_empty(rig, name, bone, loc, rot=None, kind="PLAIN_AXES", size=0.08):
    """挂在骨骼上的空物体（插槽/特效点/弱点），loc/rot 为静止姿势下的世界坐标/朝向。"""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind
    e.empty_display_size = size
    bpy.context.scene.collection.objects.link(e)
    e.parent = rig
    e.parent_type = "BONE"
    e.parent_bone = bone
    bpy.context.view_layer.update()
    M = Matrix.Translation(Vector(loc)) @ ((rot.to_4x4()) if rot is not None else Matrix.Identity(4))
    e.matrix_world = M
    return e


def loft_poly(mb, sections, mat, cap0=True, cap1=True):
    """沿 Y 放样：sections=[(y, [(x,z), ...])]，各截面点数相同、逆时针（从 -Y 看）。"""
    rings = []
    for y, pts in sections:
        rings.append(mb.addv([(x, y, z) for x, z in pts]))
    n = len(sections[0][1])
    for a, b in zip(rings, rings[1:]):
        for i in range(n):
            j = (i + 1) % n
            mb.face([a + i, a + j, b + j, b + i], mat)
    if cap0:
        mb.face([rings[0] + i for i in reversed(range(n))], mat)
    if cap1:
        mb.face([rings[-1] + i for i in range(n)], mat)


def rod(mb, p0, p1, r, mat, seg=6, r1=None):
    mb_add(mb, tube(p0, p1, r, r if r1 is None else r1, seg=seg), mat)


def blade(mb, z0, L, w0, w1, sori, t, mat, seg=8, tip=0.06):
    """弯刀身：在 YZ 平面，刃口朝 -Y、刀背朝 +Y，从 z0 起长 L，向刀背方向弯 sori（米）。"""
    def yc(s):
        return sori * s * s
    prev = None
    for i in range(seg + 1):
        s = i / seg * (1 - tip / L)
        z = z0 + L * s
        w = w0 + (w1 - w0) * s
        cur = (yc(s) - w / 2, yc(s) + w / 2, z)
        if prev:
            mb.prism([(prev[0], prev[2]), (cur[0], cur[2]), (cur[1], cur[2]), (prev[1], prev[2])], "x", -t / 2, t / 2, mat)
        prev = cur
    zt = z0 + L
    mb.prism([(prev[0], prev[2]), (yc(1.0) + w1 * 0.1, zt), (prev[1], prev[2])], "x", -t / 2, t / 2, mat)


# ================================================================ 姿势求解（FK + 两骨 IK）
def _frame_map(u0, v0, u1, v1):
    def basis(u, v):
        u = u.normalized()
        v = (v - u * v.dot(u)).normalized()
        return Matrix((u, v, u.cross(v))).transposed()
    return basis(u1, v1) @ basis(u0, v0).transposed()


def _ik(a, t, L1, L2, pole):
    d = t - a
    dist = d.length
    dn = d / dist if dist > 1e-6 else Vector((0, 0, -1))
    dist = max(abs(L1 - L2) + 1e-4, min(L1 + L2 - 1e-4, dist))
    ca = max(-1.0, min(1.0, (L1 * L1 + dist * dist - L2 * L2) / (2 * L1 * dist)))
    sa = math.sqrt(1 - ca * ca)
    pp = pole - dn * pole.dot(dn)
    if pp.length < 1e-6:
        pp = dn.orthogonal()
    pp.normalize()
    m = a + dn * (ca * L1) + pp * (sa * L1)
    tt = a + dn * dist
    return (m - a).normalized(), (tt - m).normalized()


def socket_rest(J, h, s):
    """手部插槽的静止位置与朝向：+Z = 虎口方向（T 姿势时朝前 -Y），-Y = 指节方向（手骨方向）。"""
    sg = 1 if s == "L" else -1
    pos = J["wrist" + s] + Vector((sg * 0.05 * h, -0.004 * h, -0.02 * h))
    if s == "R":
        R = Matrix(((0, 1, 0), (0, 0, -1), (-1, 0, 0)))     # 列：X=(0,0,-1) Y=(1,0,0) Z=(0,-1,0)
    else:
        R = Matrix(((0, -1, 0), (0, 0, -1), (1, 0, 0)))     # 列：X=(0,0,1) Y=(-1,0,0) Z=(0,-1,0)
    return pos, R


class Poser:
    """把「姿势描述」解成每根骨骼的绝对旋转 D（静止→姿势，骨架空间），再转成局部旋转打关键帧。

    描述字段：hips/spine/chest/neck/head = (前倾, 左转, 左倾) 度（逐级相对）；off = (左右, 向前, 向上) 米（髋位移）；
    feet[L/R] = ("ik", (x,y,z) 踝目标, 脚朝向 yaw, 脚 pitch) 或 ("fk", 抬腿, 屈膝, 脚, 外展, yaw)，默认踩在静止位置；
    arms[L/R] = ("fk", 前抬, 外张, 屈肘[, 手腕(p,y,r)]) 或 ("grip", 基准, 位置, 刃向, 刃口向, 肘尖方向)。
    grip 基准："C" 胸口坐标系（随胸转）、"Cw" 胸口点 + 世界偏移、"S" 本侧肩 + 世界偏移、"W" 世界、"GL"/"GR" 另一只手的握点 + 世界偏移。
    """

    def __init__(self, J, h):
        self.J, self.h = J, h
        self.B, self.order = {}, []
        for name, a, b, par in C.bone_list(J):
            self.B[name] = (J[a].copy(), J[b].copy(), par)
            self.order.append(name)
        self.dir = {n: (t - hd).normalized() for n, (hd, t, p) in self.B.items()}
        self.L = {n: (t - hd).length for n, (hd, t, p) in self.B.items()}
        self.sock = {s: socket_rest(J, h, s) for s in ("L", "R")}

    def hpos(self, D, offw, bone):
        hd, tl, par = self.B[bone]
        if par is None:
            return hd + offw
        return self.hpos(D, offw, par) + D[par] @ (hd - self.B[par][0])

    def pose(self, sp):
        J, h = self.J, self.h
        o = tuple(sp.get("off", (0, 0, 0)))
        offw = Vector((o[0], -o[1], o[2]))
        D = {"Hips": _ypr(sp.get("hips", (0, 0, 0)))}
        D["Spine"] = D["Hips"] @ _ypr(sp.get("spine", (0, 0, 0)))
        D["Chest"] = D["Spine"] @ _ypr(sp.get("chest", (0, 0, 0)))
        D["Neck"] = D["Chest"] @ _ypr(sp.get("neck", (0, 0, 0)))
        D["Head"] = D["Neck"] @ _ypr(sp.get("head", (0, 0, 0)))
        D["LeftShoulder"] = D["Chest"]
        D["RightShoulder"] = D["Chest"]
        feet = sp.get("feet", {})
        for s, side, sg in (("L", "Left", 1), ("R", "Right", -1)):
            f = feet.get(s) or ("ik", tuple(J["ankle" + s]), 0, 0)
            UL, LL, FT = side + "UpperLeg", side + "LowerLeg", side + "Foot"
            if f[0] == "fk":
                _, th, sh, ft, spr, yw = (list(f) + [0] * 6)[:6]
                D[UL] = D["Hips"] @ _R("Z", yw) @ _R("Y", -sg * spr) @ _R("X", -th)
                D[LL] = D[UL] @ _R("X", sh)
                D[FT] = D[LL] @ _R("X", ft)
            else:
                _, tgt, yw, pt = (list(f) + [0, 0])[:4]
                hip = self.hpos(D, offw, UL)
                pole = (_R("Z", yw) @ Vector((sg * 0.12, -1, 0))).normalized()
                d1, d2 = _ik(hip, Vector(tgt), self.L[UL], self.L[LL], pole)
                bend = d2 - d1 * d1.dot(d2)
                if bend.length < 1e-4:
                    bend = -(pole - d1 * pole.dot(d1))
                a1 = d1.cross(bend.normalized()).normalized()
                a0 = Vector((1, 0, 0))
                D[UL] = _frame_map(self.dir[UL], a0, d1, a1)
                D[LL] = _frame_map(self.dir[LL], a0, d2, a1)
                D[FT] = _R("Z", yw) @ _R("X", pt)
            D[side + "Toes"] = D[FT]
        grip = {}
        cpos = self.hpos(D, offw, "Chest") + D["Chest"] @ (J["chest_t"] - J["chest"])
        arms = sp.get("arms", {})
        la = arms.get("L")
        for s in (("R", "L") if la and la[0] == "grip" and la[1] == "GR" else ("L", "R")):
            side, sg = ("Left", 1) if s == "L" else ("Right", -1)
            UA, LA, HD = side + "UpperArm", side + "LowerArm", side + "Hand"
            a = arms.get(s) or ("fk", 0, 12, 12)
            spos, srot = self.sock[s]
            if a[0] == "fk":
                fwd, sd, bd = a[1], a[2], a[3]
                wr = a[4] if len(a) > 4 else (0, 0, 0)
                D[UA] = D["Chest"] @ C._arm(sg, fwd, sd)
                D[LA] = D[UA] @ C._fore(sg, bd)
                D[HD] = D[LA] @ _ypr(wr)
            else:
                _, base, g, b, e, pole = a
                Rb = D["Chest"] if base == "C" else Matrix.Identity(3)
                org = {"C": cpos, "Cw": cpos, "W": Vector((0, 0, 0)), "S": self.hpos(D, offw, UA)}.get(base)
                if org is None:
                    org = grip[base[1]]
                G = org + Rb @ Vector(g)
                bz = (Rb @ Vector(b)).normalized()
                ey = -(Rb @ Vector(e))
                Y = (ey - bz * ey.dot(bz)).normalized()
                F = Matrix((Y.cross(bz), Y, bz)).transposed()
                Dh = F @ srot.transposed()
                wrist = G - Dh @ (spos - J["wrist" + s])
                sh = self.hpos(D, offw, UA)
                pw = (Rb @ Vector(pole)).normalized()
                d1, d2 = _ik(sh, wrist, self.L[UA], self.L[LA], pw)
                bend = d2 - d1 * d1.dot(d2)
                if bend.length < 1e-4:
                    bend = -(pw - d1 * pw.dot(d1))
                a1 = bend.normalized().cross(d1).normalized()
                a0 = Vector((0, 0, sg))
                D[UA] = _frame_map(self.dir[UA], a0, d1, a1)
                D[LA] = _frame_map(self.dir[LA], a0, d2, a1)
                D[HD] = Dh
            grip[s] = self.hpos(D, offw, HD) + D[HD] @ (spos - J["wrist" + s])
        return D, o


def key_D(rig, poser, frame, D, off, prevq):
    for n in poser.order:
        par = poser.B[n][2]
        R = D[n] if par is None else D[par].transposed() @ D[n]
        pb = rig.pose.bones[n]
        M = pb.bone.matrix_local.to_3x3()
        q = (M.inverted() @ R @ M).to_quaternion()
        if n in prevq and prevq[n].dot(q) < 0:
            q.negate()
        prevq[n] = q
        pb.rotation_mode = "QUATERNION"
        pb.rotation_quaternion = q
        pb.keyframe_insert("rotation_quaternion", frame=frame)
    hb = rig.pose.bones["Hips"]
    hb.location = (off[0], off[2], off[1])       # Hips 局部：x=左右、y=上、z=前
    hb.keyframe_insert("location", frame=frame)


# ================================================================ 敌人：头饰 / 配件钩子
def _hc(J, h, c):
    hs = c.get("head", 1.0)
    return J["head"] + Vector((0, -0.004 * h, 0.064 * h * hs)), (0.05 * h * hs, 0.058 * h * hs, 0.066 * h * hs)


def en_topknot(S, J, hc, r, mat, h, c):
    """月代头（剃顶）+ 发髻 + 头巾（钵卷）：真倭。"""
    rx, ry, rz = r
    S.add(*box(hc + Vector((0, ry * 0.55, -rz * 0.12)), (rx * 1.9, ry * 0.85, rz * 1.15)), mat, W("Head"))
    for sx in (-1, 1):
        S.add(*box(hc + Vector((sx * rx * 0.86, ry * 0.12, -rz * 0.2)), (rx * 0.32, ry * 1.0, rz * 0.8)), mat, W("Head"))
    S.add(*tube(hc + Vector((0, ry * 0.55, rz * 0.82)), hc + Vector((0, -ry * 0.3, rz * 1.04)), 0.011 * h, 0.009 * h, seg=6),
          mat, W("Head"))
    band = c.get("band")
    if band:
        S.add(*rings_mesh([(hc + Vector((0, 0.003 * h, rz * 0.38)), rx * 1.08, ry * 1.07),
                           (hc + Vector((0, 0.003 * h, rz * 0.6)), rx * 1.04, ry * 1.04)], seg=10), band, W("Head"))
        S.add(*box(hc + Vector((0, ry * 1.08, rz * 0.48)), (0.03 * h, 0.02 * h, 0.022 * h)), band, W("Head"))
        for sx in (-1, 1):
            S.add(*box(hc + Vector((sx * 0.012 * h, ry * 1.15, rz * 0.0)), (0.014 * h, 0.004 * h, 0.08 * h),
                       rot=_eu(-15, sx * 10, 0)), band, lambda p: {"Head": 0.6, "Neck": 0.4})


def en_jingasa(S, J, hc, r, mat, h, c):
    """阵笠：宽平的漆斗笠（俯视是一个大圆盘），弓兵标志。"""
    rx, ry, rz = r
    C.hair_short(S, hc, r, "M_EN_Hair", h)
    R0 = 0.15 * h
    S.add(*rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.58)), R0, R0), (hc + Vector((0, 0.004 * h, rz * 0.66)), R0 * 1.0, R0),
                       (hc + Vector((0, 0.004 * h, rz * 1.42)), 0.012 * h, 0.012 * h)], seg=14), mat, W("Head"))
    S.add(*box(hc + Vector((0, -ry * 0.2, -rz * 0.55)), (rx * 1.6, 0.004 * h, 0.006 * h)), "M_EN_Cord", W("Head"))


def en_hood(S, J, hc, r, mat, h, c):
    """头巾兜（头裹布）：脸露在外，后脑垂一片护颈布；火罐兵。"""
    rx, ry, rz = r
    S.add(*ellipsoid(hc + Vector((0, ry * 0.22, rz * 0.05)), rx * 1.14, ry * 1.0, rz * 1.08, seg=10, rings=5, zmin=-0.45),
          mat, W("Head"))
    S.add(*box(hc + Vector((0, ry * 0.95, -rz * 0.85)), (rx * 1.7, 0.008 * h, rz * 1.0)), mat, lambda p: {"Head": 0.5, "Neck": 0.5})
    band = c.get("band")
    if band:
        S.add(*rings_mesh([(hc + Vector((0, ry * 0.18, rz * 0.45)), rx * 1.17, ry * 1.04),
                           (hc + Vector((0, ry * 0.18, rz * 0.6)), rx * 1.15, ry * 1.02)], seg=10), band, W("Head"))
    if c.get("mouthcloth"):
        S.add(*box(hc + Vector((0, -ry * 0.92, -rz * 0.45)), (rx * 1.6, 0.012 * h, rz * 0.7)), c["mouthcloth"], W("Head"))


def en_kabuto(S, J, hc, r, mat, h, c):
    """简易铁钵盔 + 后垂錣（护颈）+ 眉庇：盾兵。"""
    rx, ry, rz = r
    S.add(*ellipsoid(hc + Vector((0, 0.004 * h, rz * 0.12)), rx * 1.2, ry * 1.16, rz * 1.04, seg=10, rings=4, zmin=0.0),
          mat, W("Head"))
    S.add(*box(hc + Vector((0, -ry * 1.12, rz * 0.2)), (rx * 1.6, ry * 0.4, 0.008 * h), rot=_eu(-15, 0, 0)), mat, W("Head"))
    for k in range(5):
        a = math.radians(-10 + k * 50)
        p = hc + Vector((rx * 1.3 * math.cos(a), ry * 1.25 * math.sin(a) + 0.01 * h, -rz * 0.25))
        S.add(*box(p, (0.05 * h, 0.01 * h, rz * 0.8), rot=_eu(-25 * math.sin(a), 25 * math.cos(a), math.degrees(a) - 90)),
              c.get("lace", mat), lambda q: {"Head": 0.7, "Neck": 0.3})
    S.add(*box(hc + Vector((0, 0.004 * h, rz * 1.15)), (0.012 * h, 0.03 * h, 0.012 * h)), "M_EN_Stud", W("Head"))


def en_kerchief(S, J, hc, r, mat, h, c):
    """明人包头（胁从）：网巾式头巾 + 顶上小髻。"""
    rx, ry, rz = r
    C.headscarf(S, hc, r, mat, h)
    S.add(*ellipsoid(hc + Vector((0, 0.006 * h, rz + 0.012 * h)), 0.02 * h, 0.02 * h, 0.018 * h, seg=8, rings=3), mat, W("Head"))


for _k, _f in (("en_topknot", en_topknot), ("en_jingasa", en_jingasa), ("en_hood", en_hood),
               ("en_kabuto", en_kabuto), ("en_kerchief", en_kerchief)):
    C.HAIR_HOOKS[_k] = _f


def ex_tasuki(S, J, h, c, tw, hw):
    """襷（束袖带）：背后交叉 X。"""
    for sx in (-1, 1):
        S.add(*box((0, J["chest"].y + 0.07 * h, 0.67 * h), (0.016 * h, 0.006 * h, 0.3 * h), rot=_eu(0, sx * 38, 0)),
              c.get("cord", "M_EN_Cord"), tw)
        S.add(*box((sx * 0.07 * h, -0.064 * h, 0.78 * h), (0.016 * h, 0.006 * h, 0.07 * h)), c.get("cord", "M_EN_Cord"), tw)


def ex_sheath(S, J, h, c, tw, hw):
    """左胯刀鞘（刀在手上，鞘空着；刀口朝上、鞘尾斜向后下）。"""
    S.add(*box((0.105 * h, 0.04 * h, 0.43 * h), (0.02 * h, 0.03 * h, 0.44 * h), rot=_eu(66, 0, 0)), "M_EN_Sheath", hw)
    S.add(*box((0.105 * h, -0.155 * h, 0.52 * h), (0.026 * h, 0.036 * h, 0.03 * h), rot=_eu(66, 0, 0)), "M_EN_Iron", hw)


def ex_wakizashi(S, J, h, c, tw, hw):
    """腰插短刀（胁差），带柄。"""
    S.add(*box((0.085 * h, -0.02 * h, 0.47 * h), (0.016 * h, 0.024 * h, 0.26 * h), rot=_eu(70, 0, 10)), "M_EN_Sheath", hw)
    S.add(*box((0.07 * h, -0.13 * h, 0.52 * h), (0.016 * h, 0.018 * h, 0.08 * h), rot=_eu(70, 0, 10)), "M_EN_HiltWrap", hw)


def ex_obi(S, J, h, c, tw, hw):
    """腰带结 + 垂端。"""
    S.add(*box((-0.03 * h, -0.075 * h, 0.495 * h), (0.04 * h, 0.02 * h, 0.03 * h)), c.get("sash", "M_EN_Lacquer"), hw)
    S.add(*box((-0.035 * h, -0.08 * h, 0.45 * h), (0.02 * h, 0.006 * h, 0.07 * h), rot=_eu(0, 12, 0)), c.get("sash", "M_EN_Lacquer"),
          {"Hips": 0.7, "RightUpperLeg": 0.3})


def ex_quiver_hip(S, J, h, c, tw, hw):
    """箙（腰箭袋）：右后胯，箭羽朝上露出（俯视像一簇刺）。"""
    base = Vector((-0.1 * h, 0.08 * h, 0.5 * h))
    S.add(*box(base, (0.07 * h, 0.05 * h, 0.2 * h), rot=_eu(-12, 0, -10)), "M_EN_Lacquer", hw)
    S.add(*box(base + Vector((0, 0.002 * h, -0.11 * h)), (0.075 * h, 0.055 * h, 0.03 * h), rot=_eu(-12, 0, -10)), "M_EN_Rattan", hw)
    for k in range(6):
        x = -0.12 * h + (k % 3) * 0.018 * h
        y = 0.08 * h + (k // 3) * 0.018 * h
        top = Vector((x - 0.01 * h, y + 0.035 * h, 0.8 * h))
        S.add(*tube((x, y, 0.55 * h), top, 0.004 * h, 0.004 * h, seg=4), "M_EN_Bamboo", hw)
        S.add(*box(top + Vector((0, 0, -0.03 * h)), (0.004 * h, 0.022 * h, 0.06 * h)), "M_EN_Fletch", hw)


def ex_quiver_back(S, J, h, c, tw, hw):
    """背箭壶（胁从）：右胯斜到左肩，箭羽在左肩后露出。"""
    a = Vector((-0.08 * h, 0.09 * h, 0.5 * h))
    b = Vector((0.07 * h, 0.1 * h, 0.82 * h))
    S.add(*tube(a, b, 0.032 * h, 0.036 * h, seg=8), "M_EN_Rattan", tw)
    d = (b - a).normalized()
    for k in range(5):
        off = Vector(((k - 2) * 0.012 * h, 0.006 * h * (k % 2), 0))
        p0 = b + off - d * 0.02 * h
        p1 = b + off + d * 0.11 * h
        S.add(*tube(p0, p1, 0.004 * h, 0.004 * h, seg=4), "M_EN_Bamboo", W("Chest"))
        S.add(*box(p1, (0.004 * h, 0.02 * h, 0.05 * h)), "M_EN_Fletch", W("Chest"))
    S.add(*box((0, 0.065 * h, 0.66 * h), (0.012 * h, 0.006 * h, 0.36 * h), rot=_eu(0, -30, 0)), "M_EN_Leather", tw)


def _pot(S, p, rr, h, wt, mat="M_EN_Clay"):
    S.add(*ellipsoid(p, rr, rr, rr * 1.05, seg=8, rings=4), mat, wt)
    S.add(*tube(p + Vector((0, 0, rr * 0.85)), p + Vector((0, 0, rr * 1.3)), rr * 0.42, rr * 0.38, seg=6), "M_EN_ClayDark", wt)
    S.add(*tube(p + Vector((0, 0, rr * 1.3)), p + Vector((rr * 0.3, 0, rr * 1.75)), 0.003 * h, 0.003 * h, seg=4), "M_EN_Fuse", wt)


def ex_pot_basket(S, J, h, c, tw, hw):
    """背罐筐：竹筐背在背上，四个火罐冒头（俯视一个方块 + 圆罐）。"""
    y0, y1 = 0.08 * h, 0.21 * h
    z0, z1 = 0.6 * h, 0.82 * h
    xw = 0.14 * h
    wt = W("Chest")
    S.add(*box((0, (y0 + y1) / 2, z0 + 0.01 * h), (2 * xw, y1 - y0, 0.02 * h)), "M_EN_Basket", wt)
    for x0, x1, ya, yb in ((-xw, xw, y0, y0 + 0.012 * h), (-xw, xw, y1 - 0.012 * h, y1),
                           (-xw, -xw + 0.012 * h, y0, y1), (xw - 0.012 * h, xw, y0, y1)):
        S.add(*box(((x0 + x1) / 2, (ya + yb) / 2, (z0 + z1) / 2), (x1 - x0, yb - ya, z1 - z0)), "M_EN_Basket", wt)
    for k in range(3):
        S.add(*box((0, (y0 + y1) / 2, z0 + (k + 1) * 0.055 * h), (2 * xw + 0.006 * h, y1 - y0 + 0.006 * h, 0.008 * h)), "M_EN_Rattan", wt)
    for i, (x, y) in enumerate(((-0.07, 0.115), (0.07, 0.115), (-0.06, 0.175), (0.065, 0.175))):
        _pot(S, Vector((x * h, y * h, z1 - 0.02 * h + (i % 2) * 0.01 * h)), 0.042 * h, h, wt)
    for sx in (-1, 1):
        S.add(*box((sx * 0.06 * h, -0.066 * h, 0.7 * h), (0.016 * h, 0.006 * h, 0.22 * h)), "M_EN_Rope", tw)


def ex_pot_belt(S, J, h, c, tw, hw):
    """腰挂火罐：三个小罐 + 一盘引火绳。"""
    for x, y in ((0.07, -0.07), (0.1, 0.01), (-0.1, 0.0)):
        _pot(S, Vector((x * h, y * h, 0.42 * h)), 0.03 * h, h, hw)
        S.add(*tube((x * h, y * h, 0.47 * h), (x * h * 0.9, y * h * 0.9, 0.5 * h), 0.003 * h, 0.003 * h, seg=4), "M_EN_Rope", hw)
    S.add(*rings_mesh([(Vector((-0.06 * h, -0.075 * h, 0.44 * h)), 0.025 * h, 0.008 * h),
                       (Vector((-0.06 * h, -0.075 * h, 0.455 * h)), 0.025 * h, 0.008 * h)], seg=8), "M_EN_Fuse", hw)


def ex_armor(S, J, h, c, tw, hw):
    """简易具足：漆胴 + 绳缀横条 + 大袖 + 草摺（盾兵 A）。"""
    mat, lace = c.get("armor", "M_EN_Lacquer"), c.get("lace", "M_EN_Lace")
    rings = []
    for z, rxx, ryy in ((0.48 * h, 0.104, 0.075), (0.6 * h, 0.1, 0.072), (0.7 * h, 0.112, 0.074), (0.79 * h, 0.118, 0.068)):
        rings.append((Vector((0, C.spine_y(J, z), z)), rxx * h * c.get("bulk", 1.0), ryy * h * c.get("bulk", 1.0)))
    S.add(*rings_mesh(rings, seg=10), mat, tw)
    bk = c.get("bulk", 1.0)
    for k in range(5):
        z = 0.5 * h + k * 0.055 * h
        for yy in (-0.077, 0.075):
            S.add(*box((0, yy * h * bk, z), (0.18 * h * bk, 0.008 * h, 0.01 * h)), lace, tw)
    for s, side in (("L", "Left"), ("R", "Right")):
        sg = 1 if s == "L" else -1
        S.add(*box(J["arm" + s] + Vector((sg * 0.045 * h, 0, -0.04 * h)), (0.03 * h, 0.11 * h, 0.13 * h), rot=_eu(0, -sg * 12, 0)),
              mat, W(side + "UpperArm"))
        for k in range(3):
            S.add(*box(J["arm" + s] + Vector((sg * 0.062 * h, 0, -0.08 * h + k * 0.04 * h)), (0.006 * h, 0.112 * h, 0.008 * h),
                       rot=_eu(0, -sg * 12, 0)), lace, W(side + "UpperArm"))
        for yy in (-0.072, 0.072):
            wt = {"Hips": 0.45, side + "UpperLeg": 0.55}
            S.add(*box((sg * 0.055 * h, yy * h * bk, 0.4 * h), (0.09 * h, 0.014 * h, 0.15 * h)), mat, wt)
            for k in range(3):
                S.add(*box((sg * 0.055 * h, yy * h * bk * 1.1, 0.35 * h + k * 0.045 * h), (0.092 * h, 0.006 * h, 0.008 * h)), lace, wt)


def ex_padded(S, J, h, c, tw, hw):
    """棉甲背心（胁从盾兵）：鼓的布面甲 + 铜钉。"""
    bk = c.get("bulk", 1.0) * 1.08
    rings = []
    for z, rxx, ryy in ((0.44 * h, 0.108, 0.078), (0.56 * h, 0.1, 0.072), (0.68 * h, 0.11, 0.074), (0.79 * h, 0.116, 0.066)):
        rings.append((Vector((0, C.spine_y(J, z), z)), rxx * h * bk, ryy * h * bk))
    S.add(*rings_mesh(rings, seg=10, cap0=False), "M_EN_Padded", tw)
    for k in range(4):
        for i in range(4):
            x = (-0.06 + i * 0.04) * h
            z = 0.5 * h + k * 0.07 * h
            S.add(*box((x, -0.082 * h * bk, z), (0.01 * h, 0.006 * h, 0.01 * h)), "M_EN_Stud", tw)


for _k, _f in (("en_tasuki", ex_tasuki), ("en_sheath", ex_sheath), ("en_wakizashi", ex_wakizashi), ("en_obi", ex_obi),
               ("en_quiver_hip", ex_quiver_hip), ("en_quiver_back", ex_quiver_back), ("en_pot_basket", ex_pot_basket),
               ("en_pot_belt", ex_pot_belt), ("en_armor", ex_armor), ("en_padded", ex_padded)):
    C.EXTRA_HOOKS[_k] = _f


# ================================================================ 敌人配置
_JP = dict(outfit="robe", flare=1.18, hem=0.27, wrap="M_EN_Wrap", shoe="M_EN_Straw", skin="M_EN_Skin", cuff=1.25)
_CN = dict(outfit="jacket", wrap="M_EN_Wrap", shoe="M_EN_Straw", skin="M_EN_SkinDark", cuff=1.15)
EN_CAST = {
    "EN_Wokou_Sword_A": dict(_JP, H=1.64, top="M_EN_SW_Kosode", skirt="M_EN_SW_Hakama", pants="M_EN_Wrap", sash="M_EN_Lacquer",
                             hair="en_topknot", band="M_EN_Band", brow_tilt=16, trim="M_EN_SW_Hakama",
                             extras=["en_tasuki", "en_sheath", "en_obi"],
                             desc="刀兵 A（真倭）：月代头发髻 + 白钵卷、靛色小袖束襷、短袴绑腿草鞋、左胯空刀鞘；双手倭刀"),
    "EN_Wokou_Sword_B": dict(_CN, H=1.68, top="M_EN_SW_CoatB", pants="M_EN_SW_PantsB", sash="M_EN_Cord", hair="en_kerchief",
                             hair_mat="M_EN_Hood", brow_tilt=8, bulk=0.96, extras=["en_sheath"],
                             desc="刀兵 B（胁从）：明人包头小髻、土褐短褂、红布腰带、绑腿；同样双手倭刀"),
    "EN_Wokou_Archer_A": dict(_JP, H=1.66, top="M_EN_AR_Kosode", skirt="M_EN_AR_Hakama", pants="M_EN_Wrap", sash="M_EN_Lacquer",
                              hair="en_jingasa", hair_mat="M_EN_Jingasa", brow_tilt=8, bulk=0.95, trim="M_EN_AR_Hakama",
                              extras=["en_quiver_hip", "en_wakizashi", "en_tasuki"],
                              desc="弓兵 A（真倭）：黑漆阵笠（俯视大圆盘）、赭黄小袖、右后胯箙露箭羽、胁差；长弓"),
    "EN_Wokou_Archer_B": dict(_CN, H=1.64, top="M_EN_AR_CoatB", pants="M_EN_AR_PantsB", sash="M_EN_Leather", hair="straw_hat",
                              hair_mat="M_EN_Straw", brow_tilt=4, bulk=0.93, extras=["en_quiver_back"],
                              desc="弓兵 B（胁从）：斗笠、灰黄短褂、斜背箭壶（左肩后露箭羽）；长弓"),
    "EN_Wokou_FirePot_A": dict(_CN, H=1.68, skin="M_EN_Skin", top="M_EN_FP_Coat", pants="M_EN_FP_Pants", sash="M_EN_Rope",
                               hair="en_hood", hair_mat="M_EN_Hood", band="M_EN_BandRed", brow_tilt=12,
                               extras=["en_pot_basket", "en_pot_belt"],
                               desc="火罐兵 A（真倭）：裹头巾兜 + 红额带、铁锈红短褂、背竹罐筐四罐、腰挂三罐和引火绳"),
    "EN_Wokou_FirePot_B": dict(_CN, H=1.66, top="M_EN_FP_CoatB", pants="M_EN_FP_PantsB", sash="M_EN_Rope", hair="en_hood",
                               hair_mat="M_EN_Wrap", mouthcloth="M_EN_Hood", brow_tilt=6, bulk=0.97,
                               extras=["en_pot_basket", "en_pot_belt"],
                               desc="火罐兵 B（胁从）：浅色头兜 + 蒙口布（防烟）、褐短褂、背罐筐、腰挂火罐"),
    "EN_Wokou_Shield_A": dict(_JP, H=1.70, top="M_EN_SH_Kosode", skirt="M_EN_SH_Hakama", pants="M_EN_Wrap", sash="M_EN_Lacquer",
                              hair="en_kabuto", hair_mat="M_EN_Iron", lace="M_EN_Lace", bulk=1.12, brow_tilt=14,
                              trim="M_EN_SH_Hakama", extras=["en_armor", "en_sheath"],
                              desc="盾兵 A（真倭）：铁钵盔垂錣、黑漆具足（胴/大袖/草摺）、体格最壮；大木盾"),
    "EN_Wokou_Shield_B": dict(_CN, H=1.70, top="M_EN_SH_CoatB", pants="M_EN_SH_PantsB", sash="M_EN_Leather", hair="en_kerchief",
                              hair_mat="M_EN_Lacquer", bulk=1.1, brow_tilt=10, extras=["en_padded", "en_wakizashi"],
                              desc="盾兵 B（胁从）：黑包头、鼓胀的棉甲背心钉铜钉、壮；大木盾"),
}


def add_sockets(rig, J, h, extra=()):
    for s, bone in (("R", "RightHand"), ("L", "LeftHand")):
        pos, R = socket_rest(J, h, s)
        bone_empty(rig, "SOCKET_Hand_" + s, bone, pos, R, kind="ARROWS", size=0.1)
    bone_empty(rig, "SOCKET_Back", "Chest", (0, J["chest"].y + 0.12 * h, 0.7 * h), _R("Y", -35),
               kind="ARROWS", size=0.1)
    bone_empty(rig, "FX_Hit", "Chest", (0, J["chest"].y - 0.1 * h, 0.7 * h), size=0.06)
    bone_empty(rig, "FX_HitHead", "Head", (0, -0.05 * h, 0.93 * h), size=0.05)
    for name, bone, loc in extra:
        bone_empty(rig, name, bone, loc, size=0.07)


def build_enemy(name):
    c = EN_CAST[name]
    rig = C.build_character(name, c)
    h = c["H"]
    J = C.joints(h, c.get("hunch", 0.0), c.get("bulk", 1.0))
    extra = []
    if "Archer" in name:
        extra.append(("SOCKET_Quiver", "Hips" if name.endswith("A") else "Chest",
                      (-0.11 * h, 0.1 * h, 0.8 * h) if name.endswith("A") else (0.08 * h, 0.12 * h, 0.9 * h)))
    if "FirePot" in name:
        extra.append(("SOCKET_PotBasket", "Chest", (-0.05 * h, 0.15 * h, 0.84 * h)))
    add_sockets(rig, J, h, extra)
    return rig, J, h


# ================================================================ 敌人武器（Props，原点在握把）
def build_katana(name="PROP_EN_Katana", L=0.68, handle=0.25, w=0.03, sori=0.022, guard="M_EN_Iron", steel="M_EN_Steel",
                 wrap="M_EN_HiltWrap", gold=None):
    mb = K.MB()
    mb.box(-0.013, -0.016, -handle, 0.013, 0.016, 0.0, wrap)                         # 柄
    for k in range(4):                                                                 # 柄卷菱纹
        z = -handle + 0.03 + k * (handle - 0.06) / 3
        mb.box(-0.0145, -0.0175, z, 0.0145, 0.0175, z + 0.012, gold or "M_EN_Steel")
    mb.box(-0.015, -0.018, -handle - 0.012, 0.015, 0.018, -handle, gold or guard)      # 柄头
    mb.cyl(0, 0, 0.0, 0.008, 0.042, guard, seg=10)                                     # 镡
    mb.box(-0.006, -0.017, 0.008, 0.006, 0.017, 0.035, gold or "M_EN_Stud")            # 鎺
    blade(mb, 0.035, L, w, w * 0.82, sori, 0.007, steel)
    obj(mb, name, uv=0.25)
    empty("FX_Trail_Base", (0, 0, 0.12))
    empty("FX_Trail_Tip", (0, sori, 0.035 + L))


def build_bow():
    """和弓：上长下短、握把在下 1/3（原点），弓臂向射手一侧（+Y）弯；弦 String（松）/ String_Drawn（满弓）两态。"""
    mb = K.MB()
    top, bot = 1.33, -0.77

    def p(z):
        t = z / (top if z > 0 else -bot)
        y = 0.16 * t * t - (0.05 * max(0.0, abs(t) - 0.85) / 0.15 if abs(t) > 0.85 else 0.0)
        return Vector((0, y, z))
    zs = [bot + (top - bot) * i / 18 for i in range(19)]
    for za, zb in zip(zs, zs[1:]):
        th = 0.012 if abs(za) > 0.6 else 0.015
        rod(mb, p(za), p(zb), th, "M_EN_Lacquer", seg=4)
    for z in (-0.6, -0.3, 0.35, 0.7, 1.05):
        rod(mb, p(z - 0.02), p(z + 0.02), 0.017, "M_EN_Rattan", seg=4)
    rod(mb, p(-0.07), p(0.08), 0.02, "M_EN_Leather", seg=6)                            # 握把
    obj(mb, "PROP_EN_Bow", uv=0.25)
    tp, bp = p(top), p(bot)
    mb = K.MB()
    rod(mb, bp, tp, 0.0025, "M_EN_String", seg=3)
    obj(mb, "String", uv=0.25)
    mb = K.MB()
    nock = Vector((0, 0.70, 0.05))
    rod(mb, bp, nock, 0.0025, "M_EN_String", seg=3)
    rod(mb, nock, tp, 0.0025, "M_EN_String", seg=3)
    obj(mb, "String_Drawn", uv=0.25)
    empty("ANCHOR_Nock", tuple(nock), size=0.04)
    empty("ANCHOR_ArrowRest", (0, -0.01, 0.09), size=0.03)


def build_arrow():
    """箭：原点在箭尾（扣弦处），箭头朝 -Y；飞行时局部 -Y 朝前。"""
    mb = K.MB()
    rod(mb, (0, 0, 0), (0, -0.86, 0), 0.005, "M_EN_Bamboo", seg=5)
    with mb.at(0, -0.86, 0, rx=90):
        mb.cyl(0, 0, 0, 0.07, 0.01, "M_EN_Iron", seg=4, r_top=0.0005)
    for k in range(3):
        a = math.radians(90 + k * 120)
        with mb.at(0, 0, 0, ry=math.degrees(a)):
            mb.box(-0.0008, -0.17, 0.004, 0.0008, -0.03, 0.016, "M_EN_Fletch")
    rod(mb, (0, 0.005, 0), (0, -0.01, 0), 0.0065, "M_EN_Lacquer", seg=5)
    obj(mb, "PROP_EN_Arrow", uv=0.1)
    empty("FX_Trail", (0, 0, 0), size=0.03)


def build_firepot():
    """火罐（手雷式陶罐）：原点在掌心握点，罐身在下；FX_Fuse 引信点火处。"""
    mb = K.MB()
    mb_add(mb, ellipsoid((0, 0, -0.045), 0.075, 0.075, 0.07, seg=10, rings=5), "M_EN_Clay")
    mb.cyl(0, 0, 0.015, 0.045, 0.032, "M_EN_ClayDark", seg=8, r_top=0.028)
    mb_add(mb, ellipsoid((0, 0, 0.045), 0.04, 0.04, 0.02, seg=8, rings=3, zmin=-0.2), "M_EN_Wrap")
    for z in (-0.02, -0.07):
        mb_add(mb, rings_mesh([(Vector((0, 0, z - 0.003)), 0.077 - abs(z + 0.045) * 0.3, 0.077 - abs(z + 0.045) * 0.3),
                               (Vector((0, 0, z + 0.003)), 0.077 - abs(z + 0.045) * 0.3, 0.077 - abs(z + 0.045) * 0.3)], seg=10),
               "M_EN_Rope")
    rod(mb, (0, 0, 0.055), (0.02, -0.01, 0.1), 0.0035, "M_EN_Fuse", seg=4)
    obj(mb, "PROP_EN_FirePot", uv=0.1)
    empty("FX_Fuse", (0.02, -0.01, 0.1), size=0.03)


def build_shield():
    """大木盾（手牌）：中央竖握把在原点，盾板在握把前方（-Y），俯视是一道粗横线。"""
    mb = K.MB()
    x0, x1, z0, z1 = -0.3, 0.3, -0.64, 0.52
    for i in range(4):
        xa = x0 + i * 0.15
        dy = 0.004 * (i % 2)
        mb.box(xa + 0.003, -0.135 - dy, z0, xa + 0.147, -0.085, z1 - 0.02 * (i % 2), "M_EN_ShieldFace")
    for z in (-0.48, 0.36):
        mb.box(x0 - 0.005, -0.142, z - 0.03, x1 + 0.005, -0.13, z + 0.03, "M_EN_Iron")
    with mb.at(0, -0.14, -0.04, rx=90):
        mb.cyl(0, 0, 0, 0.012, 0.15, "M_EN_ShieldMark", seg=12)
        mb.cyl(0, 0, 0.012, 0.02, 0.07, "M_EN_ShieldFace", seg=10)
    for z in (-0.1, 0.1):
        mb.box(-0.12, -0.085, z - 0.025, 0.12, -0.06, z + 0.025, "M_EN_WoodDark")              # 背撑
        mb.box(-0.02, -0.06, z - 0.02, 0.02, -0.012, z + 0.02, "M_EN_WoodDark")
    mb.box(-0.016, -0.016, -0.12, 0.016, 0.016, 0.12, "M_EN_Leather")                           # 握把
    mb.box(x0 + 0.02, -0.085, -0.3, x1 - 0.02, -0.075, -0.25, "M_EN_WoodDark")
    obj(mb, "PROP_EN_Shield", uv=0.5)
    empty("FX_Block", (0, -0.16, 0.0), size=0.08)


# ================================================================ Boss 武器
def build_chiyan_axe():
    """赤焰的登船大斧：右手握点在原点，左手在 -0.5 m；斧刃朝 -Y，背刺朝 +Y。"""
    mb = K.MB()
    mb.box(-0.022, -0.026, -0.66, 0.022, 0.026, 0.66, "M_BS_Wood")
    for z in (-0.62, -0.5, -0.05, 0.05):
        mb.box(-0.025, -0.029, z, 0.025, 0.029, z + 0.03, "M_BS_CY_Chain")
    with mb.at(0, 0, 0):
        mb.prism([(-0.02, 0.6), (-0.02, 0.36), (-0.26, 0.24), (-0.36, 0.42), (-0.3, 0.7)], "x", -0.012, 0.012, "M_BS_Iron")
        mb.prism([(-0.26, 0.24), (-0.36, 0.42), (-0.39, 0.42), (-0.29, 0.21)], "x", -0.006, 0.006, "M_BS_Steel")
        mb.prism([(-0.36, 0.42), (-0.3, 0.7), (-0.32, 0.73), (-0.39, 0.42)], "x", -0.006, 0.006, "M_BS_Steel")
        mb.prism([(0.02, 0.56), (0.02, 0.44), (0.2, 0.5)], "x", -0.01, 0.01, "M_BS_Iron")
    mb.box(-0.03, -0.035, 0.34, 0.03, 0.035, 0.64, "M_BS_Iron")
    mb.cyl(0, 0, 0.64, 0.74, 0.02, "M_BS_Iron", seg=6, r_top=0.002)
    obj(mb, "PROP_BS_Chiyan_Axe", uv=0.25)
    empty("FX_AxeFire", (0, -0.22, 0.48), size=0.1)
    empty("FX_Trail_Base", (0, -0.1, 0.3))
    empty("FX_Trail_Tip", (0, -0.36, 0.72))


def build_guiwo_naginata():
    """鬼倭的薙刀（二阶段）：右手握点在原点、左手在 -0.45 m；杆长 1.75、弯刃 0.58。"""
    mb = K.MB()
    mb.cyl(0, 0, -1.05, 0.7, 0.019, "M_BS_GW_Armor", seg=8)
    for z in (-1.05, -0.2, 0.25, 0.62):
        mb.cyl(0, 0, z, z + 0.04, 0.022, "M_BS_GW_Gold", seg=8)
    mb.cyl(0, 0, 0.66, 0.68, 0.04, "M_BS_Iron", seg=10)
    mb.box(-0.007, -0.022, 0.68, 0.007, 0.022, 0.73, "M_BS_GW_Gold")
    blade(mb, 0.73, 0.58, 0.05, 0.042, 0.07, 0.008, "M_BS_Steel", seg=8, tip=0.08)
    obj(mb, "PROP_BS_Guiwo_Naginata", uv=0.25)
    empty("FX_Trail_Base", (0, 0, 0.75))
    empty("FX_Trail_Tip", (0, 0.07, 1.31))


# ================================================================ Boss：赤焰（火船头目）/ 鬼倭（倭酋）
def bs_chiyan_hair(S, J, hc, r, mat, h, c):
    """赤焰：染成锈红的乱发（一圈尖刺）+ 红额带 + 络腮胡。"""
    rx, ry, rz = r
    C.hair_short(S, hc, r, mat, h)
    for k in range(9):
        a = math.radians(200 + k * 17.5)
        base = hc + Vector((rx * 0.8 * math.cos(a), ry * 0.8 * math.sin(a) + 0.01 * h, rz * 0.55))
        tip = base + Vector((0.05 * h * math.cos(a), 0.05 * h * math.sin(a) + 0.02 * h, 0.05 * h + 0.012 * h * (k % 2)))
        S.add(*tube(base, tip, 0.016 * h, 0.002 * h, seg=4), mat, W("Head"))
    S.add(*rings_mesh([(hc + Vector((0, 0.003 * h, rz * 0.35)), rx * 1.1, ry * 1.09),
                       (hc + Vector((0, 0.003 * h, rz * 0.55)), rx * 1.08, ry * 1.07)], seg=10), c["band"], W("Head"))
    for sx in (-1, 1):
        S.add(*box(hc + Vector((sx * 0.01 * h, ry * 1.12, rz * 0.2)), (0.016 * h, 0.004 * h, 0.12 * h), rot=_eu(-10, sx * 14, 0)),
              c["band"], lambda p: {"Head": 0.5, "Neck": 0.5})
    chin = hc + Vector((0, -r[1] * 0.7, -r[2] * 0.55))
    S.add(*wedge(chin + Vector((0, 0.004 * h, 0.02 * h)), 0.085 * h, 0.05 * h, 0.03 * h, 0.06 * h), mat, W("Head"))
    for sx in (-1, 1):
        S.add(*box(hc + Vector((sx * rx * 0.85, -ry * 0.35, -rz * 0.45)), (0.014 * h, 0.04 * h, 0.06 * h)), mat, W("Head"))


C.HAIR_HOOKS["bs_chiyan_hair"] = bs_chiyan_hair

BS_CAST = {
    "BOSS_Chiyan": dict(H=1.92, outfit="jacket", top="M_BS_CY_Vest", sleeve="M_BS_CY_Wrap", pants="M_BS_CY_Pants",
                        shoe="M_EN_Straw", wrap="M_BS_CY_Wrap", skin="M_BS_CY_Skin", sash="M_BS_CY_Band", bulk=1.25, cuff=1.3,
                        hair="bs_chiyan_hair", hair_mat="M_BS_CY_Hair", band="M_BS_CY_Band", brow="M_BS_CY_Hair", brow_tilt=22,
                        extras=["en_pot_belt"],
                        desc="赤焰（火船头目，第 4 波 · 东水门）：1.92 m 壮汉，锈红乱发络腮胡、褪红无袖短褂、前臂缠布；背火罐架"),
    "BOSS_Guiwo": dict(H=1.86, outfit="robe", top="M_BS_GW_Robe", skirt="M_BS_GW_Hakama", pants="M_BS_GW_Hakama", flare=1.22,
                       hem=0.07, skirt_knee=True, shoe="M_BS_GW_Armor", boot=True, wrap="M_BS_GW_Armor", glove="M_BS_GW_Armor",
                       skin="M_BS_GW_Skin", sash="M_BS_GW_Lace", bulk=1.15, hair="en_topknot", hair_mat="M_EN_Hair",
                       band="M_BS_GW_Lace", brow_tilt=22, trim="M_BS_GW_Lace", extras=["en_sheath"],
                       desc="鬼倭（倭酋，第 8 波 · 环海楼/瓮城）：1.86 m，黑漆大铠红绳缀、金锹形盔、赤鬼面具、背指物旗"),
}


def _dou(S, J, h, bk, mat, lace, tw, front_only=False, crack=None):
    rings = []
    for z, rxx, ryy in ((0.47 * h, 0.108, 0.078), (0.6 * h, 0.103, 0.075), (0.7 * h, 0.115, 0.077), (0.8 * h, 0.12, 0.07)):
        rings.append((Vector((0, C.spine_y(J, z), z)), rxx * h * bk, ryy * h * bk))
    if not front_only:
        S.add(*rings_mesh(rings, seg=12), mat, tw)
        for k in range(6):
            z = 0.49 * h + k * 0.055 * h
            for yy in (-0.08, 0.078):
                S.add(*box((0, yy * h * bk, z), (0.2 * h * bk, 0.009 * h, 0.011 * h)), lace, tw)
    else:
        # 只剩左前半片胴，挂在一根肩带上
        S.add(*box((0.04 * h, -0.08 * h * bk, 0.62 * h), (0.13 * h * bk, 0.02 * h, 0.26 * h), rot=_eu(0, -8, 6)), mat, tw)
        for k in range(4):
            S.add(*box((0.04 * h, -0.092 * h * bk, 0.53 * h + k * 0.055 * h), (0.13 * h * bk, 0.008 * h, 0.01 * h), rot=_eu(0, -8, 6)),
                  lace, tw)
        S.add(*box((0.07 * h, -0.075 * h, 0.79 * h), (0.02 * h, 0.01 * h, 0.12 * h), rot=_eu(0, 25, 0)), lace, tw)
        if crack:
            for k in range(3):
                S.add(*box((0.0 + k * 0.03 * h, -0.093 * h * bk, 0.6 * h + k * 0.04 * h), (0.006 * h, 0.006 * h, 0.08 * h),
                           rot=_eu(0, 30 - k * 25, 0)), crack, tw)


def _sode(S, J, h, s, mat, lace, big=1.0):
    sg = 1 if s == "L" else -1
    side = "Left" if s == "L" else "Right"
    S.add(*box(J["arm" + s] + Vector((sg * 0.05 * h, 0, -0.045 * h)), (0.03 * h, 0.13 * h * big, 0.15 * h * big), rot=_eu(0, -sg * 12, 0)),
          mat, W(side + "UpperArm"))
    for k in range(4):
        S.add(*box(J["arm" + s] + Vector((sg * 0.067 * h, 0, -0.1 * h * big + k * 0.04 * h)), (0.006 * h, 0.132 * h * big, 0.008 * h),
                   rot=_eu(0, -sg * 12, 0)), lace, W(side + "UpperArm"))


def _kusazuri(S, J, h, bk, mat, lace, parts=("FL", "FR", "BL", "BR")):
    for p in parts:
        sg = 1 if "L" in p else -1
        yy = -0.08 if "F" in p else 0.08
        side = "Left" if sg > 0 else "Right"
        wt = {"Hips": 0.45, side + "UpperLeg": 0.55}
        S.add(*box((sg * 0.055 * h, yy * h * bk, 0.39 * h), (0.1 * h, 0.016 * h, 0.17 * h)), mat, wt)
        for k in range(3):
            S.add(*box((sg * 0.055 * h, yy * h * bk * 1.12, 0.33 * h + k * 0.05 * h), (0.102 * h, 0.006 * h, 0.009 * h)), lace, wt)


# ---- 赤焰阶段件
def ph_chiyan_mino(S, J, h, c, hc, r):
    """一阶段：蓑衣披肩 + 宽斗笠（火船上，俯视最宽）。"""
    tw = C.torso_weight(J)
    bk = c["bulk"]
    for k in range(3):
        z0 = J["chest_t"].z + 0.01 * h - k * 0.1 * h
        rr = [(Vector((0, C.spine_y(J, z0), z0)), (0.13 + k * 0.03) * h * bk, (0.085 + k * 0.025) * h * bk),
              (Vector((0, C.spine_y(J, z0) + 0.02 * h, z0 - 0.16 * h)), (0.17 + k * 0.03) * h * bk, (0.12 + k * 0.025) * h * bk)]
        S.add(*rings_mesh(rr, seg=12, cap0=False, cap1=False), "M_BS_CY_Mino", tw)
    rx, ry, rz = r
    S.add(*rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.45)), rx * 3.8, ry * 3.4), (hc + Vector((0, 0.004 * h, rz * 0.52)), rx * 3.8, ry * 3.4),
                       (hc + Vector((0, 0.004 * h, rz * 1.55)), rx * 0.15, ry * 0.15)], seg=14), "M_EN_Straw", W("Head"))


def ph_chiyan_armor(S, J, h, c, hc, r):
    """一、二阶段：焦黑胴甲 + 左大袖。"""
    _dou(S, J, h, c["bulk"], "M_BS_CY_Armor", "M_BS_CY_Plate", C.torso_weight(J))
    _sode(S, J, h, "L", "M_BS_CY_Armor", "M_BS_CY_Plate", 1.1)


def ph_chiyan_armor_broken(S, J, h, c, hc, r):
    """三阶段：胴甲只剩左前半片吊着、大袖烧没，焦痕。"""
    _dou(S, J, h, c["bulk"], "M_BS_CY_Armor", "M_BS_CY_Burn", C.torso_weight(J), front_only=True, crack="M_BS_CY_Ember")
    for k in range(4):
        S.add(*box((-0.06 * h + k * 0.04 * h, 0.1 * h, 0.6 * h + (k % 2) * 0.08 * h), (0.035 * h, 0.006 * h, 0.05 * h)),
              "M_BS_CY_Burn", C.torso_weight(J))


def _rack(S, h, wt, broken=False):
    y0 = 0.12 * h
    for sx in (-1, 1):
        S.add(*box((sx * 0.13 * h, y0 + 0.05 * h, 0.72 * h), (0.02 * h, 0.02 * h, 0.4 * h if not broken else 0.26 * h)), "M_BS_Wood", wt)
        S.add(*box((sx * 0.07 * h, -0.075 * h, 0.75 * h), (0.022 * h, 0.006 * h, 0.25 * h)), "M_EN_Rope", wt)
    for z in ((0.56, 0.74, 0.9) if not broken else (0.56,)):
        S.add(*box((0, y0 + 0.06 * h, z * h), (0.28 * h, 0.02 * h, 0.02 * h)), "M_BS_Wood", wt)


def ph_chiyan_pack(S, J, h, c, hc, r):
    """一、二阶段：背上火罐架，四个大火罐 + 引信（弱点所在）。"""
    wt = W("Chest")
    _rack(S, h, wt)
    for i, (x, z) in enumerate(((-0.065, 0.66), (0.065, 0.66), (-0.065, 0.83), (0.065, 0.83))):
        _pot(S, Vector((x * h, 0.2 * h, z * h)), 0.055 * h, h, wt, "M_BS_CY_Pot")


def ph_chiyan_pack_open(S, J, h, c, hc, r):
    """三阶段：火罐架破了，碎罐 + 露出发红的火芯（弱点外露）。"""
    wt = W("Chest")
    _rack(S, h, wt, broken=True)
    _pot(S, Vector((-0.065 * h, 0.2 * h, 0.66 * h)), 0.055 * h, h, wt, "M_BS_CY_Pot")
    for k in range(5):
        a = k * 72
        S.add(*box((0.065 * h + 0.03 * h * math.cos(math.radians(a)), 0.2 * h + 0.02 * h * math.sin(math.radians(a)), 0.66 * h),
                   (0.03 * h, 0.008 * h, 0.05 * h), rot=_eu(20, 0, a)), "M_BS_CY_Pot", wt)
    S.add(*ellipsoid((0.065 * h, 0.2 * h, 0.67 * h), 0.03 * h, 0.03 * h, 0.03 * h, seg=8, rings=4), "M_BS_CY_Ember", wt)
    S.add(*box((0, 0.17 * h, 0.78 * h), (0.16 * h, 0.06 * h, 0.06 * h), rot=_eu(0, 15, 0)), "M_BS_CY_Burn", wt)


# ---- 鬼倭阶段件
def ph_guiwo_sashimono(S, J, h, c, hc, r):
    """一阶段：背指物旗（俯视一根长杆 + 旗面，最远就认得出）。"""
    wt = W("Chest")
    S.add(*tube((0, 0.11 * h, 0.58 * h), (0, 0.13 * h, 1.38 * h), 0.008 * h, 0.007 * h, seg=6), "M_BS_Wood", wt)
    S.add(*box((0.0, 0.1 * h, 0.66 * h), (0.05 * h, 0.03 * h, 0.03 * h)), "M_BS_GW_Gold", wt)
    S.add(*box((0.085 * h, 0.13 * h, 1.15 * h), (0.16 * h, 0.006 * h, 0.4 * h)), "M_BS_GW_Flag", wt)
    S.add(*box((0.085 * h, 0.126 * h, 1.2 * h), (0.07 * h, 0.006 * h, 0.07 * h)), "M_BS_GW_FlagMark", wt)
    S.add(*box((0.085 * h, 0.13 * h, 1.355 * h), (0.17 * h, 0.012 * h, 0.01 * h)), "M_BS_Wood", wt)


def ph_guiwo_armor(S, J, h, c, hc, r):
    """一、二阶段：黑漆大铠（胴、两大袖、四片草摺）红绳缀。"""
    bk = c["bulk"]
    _dou(S, J, h, bk, "M_BS_GW_Armor", "M_BS_GW_Lace", C.torso_weight(J))
    for s in ("L", "R"):
        _sode(S, J, h, s, "M_BS_GW_Armor", "M_BS_GW_Lace", 1.25)
    _kusazuri(S, J, h, bk, "M_BS_GW_Armor", "M_BS_GW_Lace")
    S.add(*box((0, -0.086 * h * bk, 0.74 * h), (0.06 * h, 0.006 * h, 0.04 * h)), "M_BS_GW_Gold", C.torso_weight(J))


def ph_guiwo_armor_broken(S, J, h, c, hc, r):
    """三阶段：被炮打碎——胴只剩前半片带裂口、只剩右大袖、两片草摺。"""
    bk = c["bulk"]
    _dou(S, J, h, bk, "M_BS_GW_Armor", "M_BS_GW_Lace", C.torso_weight(J), front_only=True, crack="M_BS_GW_Crack")
    _sode(S, J, h, "R", "M_BS_GW_Armor", "M_BS_GW_Lace", 1.25)
    _kusazuri(S, J, h, bk, "M_BS_GW_Armor", "M_BS_GW_Lace", parts=("FR", "BL"))


def ph_guiwo_kabuto(S, J, h, c, hc, r):
    """一、二阶段：星兜 + 金色大锹形（俯视两只角）+ 吹返 + 外张錣。"""
    rx, ry, rz = r
    wt = W("Head")
    S.add(*ellipsoid(hc + Vector((0, 0.004 * h, rz * 0.15)), rx * 1.25, ry * 1.2, rz * 1.08, seg=12, rings=4, zmin=0.0),
          "M_BS_GW_Armor", wt)
    for k in range(4):
        z0 = rz * (0.1 - k * 0.28)
        rr = [(hc + Vector((0, 0.02 * h, z0)), rx * (1.35 + k * 0.18), ry * (1.25 + k * 0.15)),
              (hc + Vector((0, 0.02 * h, z0 - rz * 0.26)), rx * (1.45 + k * 0.18), ry * (1.35 + k * 0.15))]
        vs, fs = rings_mesh(rr, seg=12, cap0=False, cap1=False)
        fs = [f for f in fs if all(vs[i][1] > hc.y - ry * 0.2 for i in f)]         # 只留后半圈，脸前不挡
        S.add(vs, fs, "M_BS_GW_Lace" if k % 2 else "M_BS_GW_Armor", lambda p: {"Head": 0.7, "Neck": 0.3})
    for sx in (-1, 1):
        S.add(*box(hc + Vector((sx * rx * 1.35, -ry * 0.55, rz * 0.05)), (0.012 * h, 0.05 * h, 0.06 * h), rot=_eu(0, 0, sx * 35)),
              "M_BS_GW_Armor", wt)
        pts = [hc + Vector((sx * 0.015 * h, -ry * 1.15, rz * 0.55)), hc + Vector((sx * 0.05 * h, -ry * 1.3, rz * 1.2)),
               hc + Vector((sx * 0.1 * h, -ry * 1.3, rz * 1.9)), hc + Vector((sx * 0.12 * h, -ry * 1.15, rz * 2.5))]
        for i, (a, b) in enumerate(zip(pts, pts[1:])):
            S.add(*tube(a, b, (0.012 - i * 0.003) * h, (0.009 - i * 0.003) * h + 0.001 * h, seg=4), "M_BS_GW_Gold", wt)
    S.add(*box(hc + Vector((0, -ry * 1.18, rz * 0.6)), (0.04 * h, 0.006 * h, 0.03 * h)), "M_BS_GW_Gold", wt)
    S.add(*box(hc + Vector((0, -ry * 1.15, rz * 0.32)), (rx * 1.9, ry * 0.35, 0.008 * h), rot=_eu(-12, 0, 0)), "M_BS_GW_Armor", wt)


def ph_guiwo_mask(S, J, h, c, hc, r, half=False):
    """赤鬼面具（面頬）：红面、黑眼洞、獠牙、白须；half=True 只剩左半张 + 裂口。"""
    rx, ry, rz = r
    wt = W("Head")
    xs = (1,) if half else (-1, 1)
    for sx in xs:
        S.add(*box(hc + Vector((sx * rx * 0.48, -ry * 0.95, -rz * 0.25)), (rx * 0.95, 0.03 * h, rz * 1.15), rot=_eu(0, 0, -sx * 18)),
              "M_BS_GW_Mask", wt)
        S.add(*box(hc + Vector((sx * rx * 0.42, -ry * 1.03, rz * 0.08)), (rx * 0.42, 0.01 * h, 0.014 * h)), "M_BS_GW_MaskDark", wt)
        S.add(*box(hc + Vector((sx * rx * 0.55, -ry * 1.02, rz * 0.3)), (rx * 0.6, 0.016 * h, 0.012 * h), rot=_eu(0, sx * 20, 0)),
              "M_BS_GW_MaskDark", wt)
        S.add(*wedge(hc + Vector((sx * rx * 0.22, -ry * 1.04, -rz * 0.48)), 0.012 * h, 0.01 * h, 0.004 * h, 0.03 * h), "M_BS_GW_Fur", wt)
        S.add(*box(hc + Vector((sx * rx * 0.5, -ry * 0.98, -rz * 0.85)), (rx * 0.5, 0.02 * h, rz * 0.35)), "M_BS_GW_Fur", wt)
    if half:
        for k in range(3):
            S.add(*box(hc + Vector((0.004 * h, -ry * 1.04, -rz * (0.6 - k * 0.35))), (0.006 * h, 0.006 * h, rz * 0.4),
                       rot=_eu(0, 25 - k * 20, 0)), "M_BS_GW_Crack", wt)
    else:
        S.add(*box(hc + Vector((0, -ry * 1.08, -rz * 0.1)), (0.022 * h, 0.03 * h, 0.03 * h)), "M_BS_GW_Mask", wt)
        S.add(*box(hc + Vector((0, -ry * 1.02, -rz * 0.5)), (rx * 0.7, 0.012 * h, 0.012 * h)), "M_BS_GW_MaskDark", wt)


PHASES = {
    "BOSS_Chiyan": [("Phase1_Mino", ph_chiyan_mino), ("Phase12_Armor", ph_chiyan_armor), ("Phase3_ArmorBroken", ph_chiyan_armor_broken),
                    ("Phase12_Pack", ph_chiyan_pack), ("Phase3_PackOpen", ph_chiyan_pack_open)],
    "BOSS_Guiwo": [("Phase1_Sashimono", ph_guiwo_sashimono), ("Phase12_Armor", ph_guiwo_armor),
                   ("Phase3_ArmorBroken", ph_guiwo_armor_broken), ("Phase12_Kabuto", ph_guiwo_kabuto),
                   ("Phase12_Mask", ph_guiwo_mask), ("Phase3_MaskBroken", lambda *a: ph_guiwo_mask(*a, half=True))],
}


def build_boss(name):
    c = BS_CAST[name]
    rig = C.build_character(name, c)
    h = c["H"]
    J = C.joints(h, c.get("hunch", 0.0), c.get("bulk", 1.0))
    hc, r = _hc(J, h, c)
    for pname, fn in PHASES[name]:
        S = C.Skin()
        fn(S, J, h, c, hc, r)
        S.to_object(pname, rig)
    if name == "BOSS_Chiyan":
        extra = [("FX_Chiyan_Fuse_1", "Chest", (-0.065 * h, 0.2 * h, 0.75 * h)), ("FX_Chiyan_Fuse_2", "Chest", (0.065 * h, 0.2 * h, 0.75 * h)),
                 ("FX_Chiyan_Fuse_3", "Chest", (0.0, 0.2 * h, 0.92 * h)), ("FX_Chiyan_PackFire", "Chest", (0.065 * h, 0.22 * h, 0.67 * h)),
                 ("FX_Chiyan_Steam", "Chest", (0, 0.0, 0.78 * h)), ("WEAK_Chiyan_Pack", "Chest", (0.0, 0.21 * h, 0.72 * h))]
    else:
        extra = [("FX_Guiwo_MaskEyes", "Head", (0, hc.y - r[1] * 1.05, hc.z + r[2] * 0.1)),
                 ("FX_Guiwo_ArmorBreak", "Chest", (0, -0.1 * h, 0.66 * h)), ("FX_Guiwo_Banner", "Chest", (0.085 * h, 0.13 * h, 1.15 * h)),
                 ("WEAK_Guiwo_ArmorJoint", "Chest", (-0.11 * h, -0.02 * h, 0.74 * h)), ("WEAK_Guiwo_Chest", "Chest", (0.02 * h, -0.1 * h, 0.64 * h))]
    add_sockets(rig, J, h, extra)
    return rig, J, h


# ================================================================ 战斗动作（24 fps；<模型>@<动作>，动作名带 EN_/BS_ 前缀）
def _pad(t):
    return tuple(t) + (0, 0, 0)[len(t):]


def adj(sp, **kw):
    """在姿势描述上叠加：角度/位移字段相加，其余字段（arms/feet）替换。"""
    s = dict(sp)
    for k, v in kw.items():
        if k in ("hips", "spine", "chest", "neck", "head", "off"):
            s[k] = tuple(a + b for a, b in zip(_pad(s.get(k, (0, 0, 0))), _pad(v)))
        else:
            s[k] = v
    return s


def _two(g, b, e, off, base="C", pr=(-0.5, 0.4, -1), pl=(0.5, 0.4, -1)):
    """双手握持：右手在 g，左手沿刃向往后 off 米，两只手插槽同朝向。"""
    gl = Vector(g) - Vector(b).normalized() * off
    return {"R": ("grip", base, tuple(g), b, e, pr), "L": ("grip", base, tuple(gl), b, e, pl)}


def _f(J, x, y, yaw, z=None, pitch=0):
    return ("ik", (x, y, J["ankleL"].z if z is None else z), yaw, pitch)


def react_hit(st, h):
    return 20, [(0, st), (3, adj(st, spine=(-14, 0, 0), chest=(-8, 0, 0), head=(-12, 0, 0), off=(0, -0.05 * h, 0))),
                (9, adj(st, spine=(-6, 0, 0), head=(-4, 0, 0), off=(0, -0.02 * h, 0))), (20, st)]


def react_death(st, h, J):
    yaw = _pad(st.get("hips", (0, 0, 0)))[1]
    hang = {"L": ("fk", 25, 15, 25), "R": ("fk", 25, 15, 25)}
    kneel = dict(st, spine=(25, 0, 0), chest=(8, 0, 0), head=(10, 0, 0), arms=hang)
    kneel["off"] = (0, 0.02 * h, -0.27 * h)
    lie = {"hips": (80, yaw, 0), "spine": (8, 0, 0), "chest": (0, 0, 0), "neck": (0, 30, 0), "head": (-25, 30, 0),
           "off": (0, 0.25 * h, -0.41 * h), "feet": {"L": ("fk", -2, 12, 30, 6), "R": ("fk", 4, 25, 30, 4)},
           "arms": {"L": ("fk", 150, 35, 25), "R": ("fk", 120, 45, 30)}}
    return 36, [(0, st), (5, adj(st, spine=(-18, 0, 0), chest=(-6, 0, 0), head=(-15, 0, 0), off=(0, -0.04 * h, 0))),
                (14, kneel), (24, lie), (36, adj(lie, hips=(8, 0, 0), off=(0, 0, -0.02 * h)))]


def kneel_spec(st, h, J, arms, lean=20):
    s = dict(st, spine=(lean, 0, 0), chest=(6, 0, 0), head=(8, 0, 0), arms=arms)
    s["hips"] = (0, _pad(st.get("hips", (0, 0, 0)))[1] * 0.5, 0)
    s["off"] = (0, 0.0, -0.23 * h)
    s["feet"] = {"L": _f(J, 0.11 * h, -0.14 * h, 15), "R": _f(J, -0.1 * h, 0.24 * h, 0, z=0.11 * h, pitch=60)}
    return s


def react_stagger_loop(st, h, J, arms):
    k = kneel_spec(st, h, J, arms)
    return 48, [(0, k), (24, adj(k, spine=(5, 0, 0), chest=(4, 0, 0), head=(6, 0, 0), off=(0, 0, -0.01 * h))), (48, k)]


def react_executed(st, h, J, arms):
    k = kneel_spec(st, h, J, arms)
    yaw = _pad(k["hips"])[1]
    hang = {"L": ("fk", 30, 20, 25), "R": ("fk", 30, 20, 25)}
    side = dict(k, hips=(20, yaw, -40), spine=(10, 0, -10), head=(0, 0, -20), arms=hang)
    side["off"] = (0.1 * h, 0, -0.32 * h)
    lie = {"hips": (82, yaw, 0), "spine": (6, 0, 0), "neck": (0, 30, 0), "head": (-20, 30, 0), "off": (0, 0.2 * h, -0.41 * h),
           "feet": {"L": ("fk", -4, 30, 30, 8), "R": ("fk", 10, 60, 30, 4)}, "arms": {"L": ("fk", 150, 40, 25), "R": ("fk", 110, 50, 30)}}
    return 48, [(0, k), (6, adj(k, spine=(-18, 0, 0), chest=(-8, 0, 0), head=(-25, 0, 0))), (18, side), (30, lie),
                (48, adj(lie, hips=(6, 0, 0), off=(0, 0, -0.02 * h)))]


# ---------------------------------------------------------------- 刀兵（倭刀双手，左手在柄后 0.17 m）
def clips_sword(h, J):
    KAT = 0.17

    def st(g=None, lean=0, yaw=0, fwd=0, down=0, step=0, b=None, e=None):
        g = g or (-0.02 * h, -0.21 * h, -0.24 * h)
        return {"hips": (0, 12, 0), "spine": (5 + lean, -6 + yaw, 0), "chest": (3, -6 + yaw * 0.5, 0), "head": (-6 - lean * 0.6, -yaw * 0.4, 0),
                "off": (0, fwd, -0.045 * h - down),
                "feet": {"L": _f(J, 0.1 * h, 0.1 * h, 25), "R": _f(J, -0.06 * h, -0.14 * h - step, 5)},
                "arms": _two(g, b or (0, -0.75, 0.66), e or (0, -0.66, -0.75), KAT)}
    S0 = st()
    hasso = dict(g=(-0.1 * h, -0.05 * h, 0.04 * h), b=(0.1, 0.3, 1), e=(0, -1, 0.3))
    hit1 = dict(g=(0.0, -0.3 * h, -0.12 * h), b=(0.5, -0.85, -0.1), e=(0.5, 0.2, -0.85))
    fol1 = dict(g=(0.08 * h, -0.2 * h, -0.36 * h), b=(0.6, -0.35, -0.7), e=(0.3, 0.6, -0.4))
    coil2 = dict(g=(0.12 * h, -0.12 * h, -0.3 * h), b=(0.5, -0.3, -0.8), e=(-0.6, 0.0, -0.4))
    hit2 = dict(g=(-0.04 * h, -0.3 * h, -0.06 * h), b=(-0.6, -0.75, 0.2), e=(-0.75, 0.4, 0.4))
    fol2 = dict(g=(-0.14 * h, -0.14 * h, 0.08 * h), b=(-0.45, 0.25, 0.85), e=(-0.6, -0.7, 0.1))
    A1end = st(lean=20, yaw=20, fwd=0.1 * h, down=0.03 * h, step=0.1 * h, **fol1)
    return {
        "EN_SwordIdleLoop": (48, [(0, S0), (24, st(down=0.012 * h, b=(0, -0.7, 0.72))), (48, S0)]),
        "EN_SwordAttack1": (32, [(0, S0), (11, st(lean=-4, yaw=-10, **hasso)),
                                 (14, st(lean=14, yaw=15, fwd=0.08 * h, step=0.1 * h, **hit1)), (18, A1end), (32, S0)]),
        "EN_SwordAttack2": (28, [(0, A1end), (5, st(lean=15, yaw=25, fwd=0.08 * h, step=0.1 * h, **coil2)),
                                 (9, st(lean=10, yaw=-20, fwd=0.1 * h, step=0.1 * h, **hit2)),
                                 (13, st(lean=4, yaw=-30, fwd=0.08 * h, step=0.1 * h, **fol2)), (28, S0)]),
        "EN_SwordHit": react_hit(S0, h),
        "EN_SwordDeath": react_death(S0, h, J),
    }


# ---------------------------------------------------------------- 弓兵（左手持弓，右手拉弦/扣箭）
def clips_archer(h, J):
    def st(L=None, R=None, down=0):
        return {"hips": (0, -60, 0), "spine": (3, 0, 0), "chest": (0, -5, 0), "neck": (0, 25, 0), "head": (0, 30, 0),
                "off": (0, 0, -0.02 * h - down),
                "feet": {"L": _f(J, 0.05 * h, -0.1 * h, -55), "R": _f(J, -0.07 * h, 0.1 * h, -75)},
                "arms": {"L": L or ("grip", "Cw", (0.12 * h, -0.12 * h, -0.28 * h), (0.15, -0.4, 0.9), (0, -1, 0), (0.3, 0.5, -1)),
                         "R": R or ("fk", 15, 10, 25)}}
    S0 = st()
    nockL = ("grip", "Cw", (0.04 * h, -0.26 * h, -0.06 * h), (0, -0.1, 1), (0, -1, 0), (0.5, 0.3, -1))
    nockR = ("grip", "GL", (-0.02 * h, 0.08 * h, 0.02 * h), (0, 0, 1), (0, -1, 0), (-0.3, 1, -0.5))
    drawL = ("grip", "S", (0.0, -0.34 * h, 0.01 * h), (0, 0, 1), (0, -1, 0), (0.2, 0.2, -1))
    drawR = ("grip", "GL", (-0.01 * h, 0.42 * h, 0.035 * h), (0, 0, 1), (0, -1, 0), (-0.4, 1, 0.3))
    relR = ("grip", "GL", (-0.07 * h, 0.5 * h, 0.06 * h), (0, 0, 1), (0, -1, 0), (-0.4, 1, 0.3))
    return {
        "EN_BowIdleLoop": (48, [(0, S0), (24, adj(st(down=0.01 * h), chest=(1.5, 0, 0))), (48, S0)]),
        "EN_BowShoot": (40, [(0, S0), (8, st(nockL, nockR)), (18, st(drawL, drawR)), (26, adj(st(drawL, drawR), chest=(-1, 0, 0))),
                             (28, st(drawL, relR)), (32, st(drawL, relR)), (40, S0)]),
        "EN_BowHit": react_hit(S0, h),
        "EN_BowDeath": react_death(S0, h, J),
    }


# ---------------------------------------------------------------- 火罐兵（右手持罐投掷，左手点引信）
def clips_firepot(h, J, hand="R"):
    sgn = 1 if hand == "R" else -1          # 镜像：赤焰用左手扔

    def M(v):
        return (v[0] * sgn, v[1], v[2])

    o = "L" if hand == "R" else "R"

    def st(spine=(8, 0, 0), chest=(0, 0, 0), T=None, O=None, fwd=0, stepL=0):
        return {"hips": (0, 0, 0), "spine": (spine[0], spine[1] * sgn, 0), "chest": (chest[0], chest[1] * sgn, 0), "head": (-6, 0, 0),
                "off": (0, fwd, -0.035 * h),
                "feet": {"L": _f(J, 0.09 * h, -0.05 * h - stepL, 10), "R": _f(J, -0.09 * h, 0.06 * h, -15)},
                "arms": {hand: T or ("grip", "C", M((-0.08 * h, -0.16 * h, -0.28 * h)), (0, 0, 1), (0, -1, 0), M((-1, 0.3, -0.5))),
                         o: O or ("fk", 30, -10, 60)}}
    S0 = st()
    light = st(T=("grip", "C", M((-0.04 * h, -0.2 * h, -0.18 * h)), (0, 0, 1), (0, -1, 0), M((-1, 0.3, -0.5))),
               O=("grip", "G" + hand, M((0.03 * h, -0.02 * h, 0.05 * h)), (0, 0, 1), M((1, 0, 0)), M((1, 0.3, -1))))
    wind = st(spine=(-10, -30, 0), chest=(-4, -15, 0), stepL=0.09 * h,
              T=("grip", "C", M((-0.16 * h, 0.1 * h, 0.12 * h)), (0, 0, 1), (0, -1, 0.2), M((-1, 0.5, -0.3))), O=("fk", 75, 25, 15))
    rel = st(spine=(18, 20, 0), chest=(6, 10, 0), fwd=0.06 * h, stepL=0.09 * h,
             T=("grip", "C", M((-0.04 * h, -0.32 * h, 0.06 * h)), (0, -0.5, 0.8), (0, -1, -0.3), M((-1, 0.3, -0.4))), O=("fk", 20, 10, 40))
    fol = st(spine=(25, 25, 0), chest=(6, 10, 0), fwd=0.06 * h, stepL=0.09 * h,
             T=("grip", "C", M((0.07 * h, -0.26 * h, -0.3 * h)), (0, -1, 0), (0, 0, -1), M((-1, 0.3, -0.5))), O=("fk", 10, 15, 20))
    return S0, light, wind, rel, fol


def clips_pot(h, J):
    S0, light, wind, rel, fol = clips_firepot(h, J)
    return {
        "EN_PotIdleLoop": (48, [(0, S0), (24, adj(S0, spine=(3, 0, 0), off=(0, 0, -0.01 * h))), (48, S0)]),
        "EN_PotThrow": (34, [(0, S0), (6, light), (13, wind), (17, rel), (23, fol), (34, S0)]),
        "EN_PotHit": react_hit(S0, h),
        "EN_PotDeath": react_death(S0, h, J),
    }


# ---------------------------------------------------------------- 盾兵（左手中握大盾）
def clips_shield(h, J):
    def st(g=(0.05 * h, -0.23 * h, -0.14 * h), b=(0, 0, 1), lean=0, fwd=0, down=0, lstep=0, R=("fk", 40, -15, 80), feet=None):
        return {"hips": (0, -15, 0), "spine": (8 + lean, 8, 0), "chest": (2, 5, 0), "head": (-8 - lean * 0.6, 0, 0),
                "off": (0, fwd, -0.06 * h - down),
                "feet": feet or {"L": _f(J, 0.08 * h, -0.13 * h - lstep, -10), "R": _f(J, -0.09 * h, 0.12 * h, -25)},
                "arms": {"L": ("grip", "C", g, b, (0, -1, 0), (1, 0.5, -0.6)), "R": R}}
    S0 = st()
    coil = st(g=(0.03 * h, -0.15 * h, -0.1 * h), lean=8, fwd=-0.06 * h, down=0.03 * h)
    lunge = st(g=(0.04 * h, -0.34 * h, -0.08 * h), lean=12, fwd=0.22 * h, down=0.0, lstep=0.19 * h)
    block = st(g=(0.03 * h, -0.2 * h, 0.02 * h), b=(0, 0.3, 1), lean=6, down=0.04 * h, R=("fk", 70, -25, 95))
    s, base_l, base_r = 0.11 * h, -0.13 * h, 0.04 * h
    walk = []
    for f in range(0, 33, 4):
        def foot(ph, y0):
            ph %= 32
            if ph < 24:
                return y0 + s * ph / 24, 0.0
            t = (ph - 24) / 8
            return y0 + s * (1 - t), 0.04 * h * math.sin(math.pi * t)
        yl, zl = foot(f, base_l)
        yr, zr = foot(f + 16, base_r)
        az = J["ankleL"].z
        fe = {"L": _f(J, 0.08 * h, yl, -10, z=az + zl), "R": _f(J, -0.09 * h, yr, -25, z=az + zr)}
        walk.append((f, st(feet=fe, down=0.01 * h * math.cos(2 * math.pi * f / 16))))
    return {
        "EN_ShieldIdleLoop": (48, [(0, S0), (24, adj(S0, chest=(2, 0, 0), off=(0, 0, -0.01 * h))), (48, S0)]),
        "EN_ShieldBash": (36, [(0, S0), (10, coil), (17, adj(coil, spine=(2, 0, 0))), (21, lunge), (27, lunge), (36, S0)]),
        "EN_ShieldBlockLoop": (24, [(0, block), (12, adj(block, chest=(2, 0, 0), off=(0, -0.005 * h, -0.005 * h))), (24, block)]),
        "EN_ShieldWalk": (32, walk),
        "EN_ShieldHit": react_hit(S0, h),
        "EN_ShieldDeath": react_death(S0, h, J),
    }


# ---------------------------------------------------------------- 赤焰（双手大斧，左手在柄后 0.45 m；P1 左手扔火罐）
def clips_chiyan(h, J):
    AX = 0.45

    def st(g=(-0.12 * h, -0.22 * h, -0.08 * h), b=(-0.5, -0.25, 0.85), e=(-0.3, -1, 0), lean=0, yaw=0, fwd=0, down=0, rstep=0,
           arms=None, hy=10, feet=None):
        return {"hips": (0, hy, 0), "spine": (6 + lean, -5 + yaw, 0), "chest": (4, -5 + yaw * 0.5, 0), "head": (-8 - lean * 0.5, -yaw * 0.4, 0),
                "off": (0, fwd, -0.06 * h - down),
                "feet": feet or {"L": _f(J, 0.11 * h, 0.02 * h, 20), "R": _f(J, -0.11 * h, -0.06 * h - rstep, -15)},
                "arms": arms or _two(g, b, e, AX)}
    S0 = st()
    over = dict(g=(-0.02 * h, 0.02 * h, 0.2 * h), b=(0, 0.55, 0.83), e=(0, -0.83, 0.55))
    impact = dict(g=(0.0, -0.36 * h, -0.3 * h), b=(0, -0.6, -0.8), e=(0, 0.8, -0.6))
    chop_hit = st(lean=26, fwd=0.1 * h, down=0.12 * h, rstep=0.12 * h, **impact)
    raise_r = dict(g=(-0.16 * h, -0.02 * h, 0.02 * h), b=(-0.3, 0.2, 0.93), e=(0, -1, 0))
    h1 = dict(g=(0.02 * h, -0.32 * h, -0.1 * h), b=(0.6, -0.8, 0.0), e=(0.8, 0.6, 0))
    f1 = dict(g=(0.14 * h, -0.2 * h, -0.12 * h), b=(0.95, 0.1, 0.1), e=(0.1, 1, 0))
    h2 = dict(g=(-0.04 * h, -0.32 * h, -0.08 * h), b=(-0.6, -0.8, 0), e=(-0.8, 0.6, 0))
    spinpose = dict(g=(-0.2 * h, -0.16 * h, -0.12 * h), b=(-0.9, -0.4, 0), e=(0.4, -0.9, 0))
    spin = [(0, S0), (8, st(yaw=-30, **spinpose))]
    for i, (f, y) in enumerate(((12, 30), (16, 120), (20, 210), (24, 300), (28, 390), (32, 440))):
        spin.append((f, st(hy=10 + y, yaw=-30, down=0.04 * h, **spinpose)))
    spin += [(40, st(hy=370, down=0.02 * h)), (48, st(hy=370))]
    # P1 火罐：右手斧垂在身侧，左手扔
    S0p, light, wind, rel, fol = clips_firepot(h, J, hand="L")
    axe_low = ("fk", 12, 18, 15)

    def pot(sp):
        s2 = dict(sp)
        s2["arms"] = dict(sp["arms"], R=axe_low)
        return s2
    crouch = st(lean=25, down=0.2 * h, **raise_r)
    air = st(lean=-6, down=-0.35 * h, feet={"L": ("fk", 50, 90, 0), "R": ("fk", 35, 80, 0)}, **over)
    land = st(lean=34, down=0.22 * h, feet={"L": _f(J, 0.14 * h, 0.02 * h, 25), "R": _f(J, -0.14 * h, -0.08 * h, -20)}, **impact)
    roar = st(lean=-15, arms={"L": ("fk", 85, 80, 10), "R": ("fk", 145, 45, 15)})
    roar["head"] = (-22, 0, 0)
    plant = _two((-0.06 * h, -0.3 * h, -0.36 * h), (0, -0.15, -1), (0, -1, 0.15), AX)
    return {
        "BS_ChiyanIdleLoop": (48, [(0, S0), (24, adj(S0, chest=(4, 0, 0), off=(0, 0, -0.015 * h))), (48, S0)]),
        "BS_ChiyanAxeChop": (44, [(0, S0), (14, st(lean=-10, **over)), (18, chop_hit), (28, adj(chop_hit, spine=(-3, 0, 0))), (44, S0)]),
        "BS_ChiyanAxeCombo3": (60, [(0, S0), (12, st(yaw=-15, **raise_r)), (15, st(lean=10, yaw=25, fwd=0.06 * h, **h1)),
                                    (18, st(lean=8, yaw=35, fwd=0.06 * h, **f1)), (25, st(lean=10, yaw=-25, fwd=0.08 * h, **h2)),
                                    (40, st(lean=-10, fwd=0.04 * h, **over)), (44, chop_hit), (50, chop_hit), (60, S0)]),
        "BS_ChiyanAxeSpin": (48, spin),
        "BS_ChiyanPotThrow": (34, [(0, pot(S0p)), (6, pot(light)), (13, pot(wind)), (17, pot(rel)), (23, pot(fol)), (34, pot(S0p))]),
        "BS_ChiyanLeap": (44, [(0, S0), (10, crouch), (16, air), (22, adj(air, off=(0, 0, 0.05 * h))), (28, land), (34, land), (44, S0)]),
        "BS_ChiyanPhaseChange": (48, [(0, S0), (8, adj(S0, spine=(-10, 0, 0), off=(0, -0.05 * h, 0))), (20, roar), (36, roar), (48, S0)]),
        "BS_ChiyanWeakHit": (30, [(0, S0), (3, adj(S0, spine=(28, 0, 0), chest=(12, 0, 0), head=(15, 0, 0), off=(0, 0.08 * h, -0.04 * h))),
                                  (12, adj(S0, spine=(14, 0, 0), off=(0, 0.04 * h, -0.02 * h))), (30, S0)]),
        "BS_ChiyanStaggerLoop": react_stagger_loop(S0, h, J, plant),
        "BS_ChiyanExecuted": react_executed(S0, h, J, plant),
    }


# ---------------------------------------------------------------- 鬼倭（太刀 0.21 / 薙刀 0.45 / 野太刀 0.30）
def clips_guiwo(h, J):
    TA, NG, ND = 0.21, 0.45, 0.30

    def st(g=(-0.1 * h, -0.04 * h, 0.05 * h), b=(0.1, 0.25, 1), e=(0, -1, 0.25), off=TA, lean=0, yaw=0, fwd=0, down=0, step=0,
           arms=None, feet=None, hy=12):
        return {"hips": (0, hy, 0), "spine": (4 + lean, -6 + yaw, 0), "chest": (2, -6 + yaw * 0.5, 0), "head": (-6 - lean * 0.6, -yaw * 0.4, 0),
                "off": (0, fwd, -0.05 * h - down),
                "feet": feet or {"L": _f(J, 0.1 * h, 0.1 * h, 25), "R": _f(J, -0.06 * h, -0.15 * h - step, 5)},
                "arms": arms or _two(g, b, e, off)}
    S0 = st()
    over = dict(g=(-0.03 * h, 0.0, 0.17 * h), b=(0, 0.4, 0.9), e=(0, -0.9, 0.4))
    v1 = dict(g=(0.0, -0.32 * h, -0.18 * h), b=(0, -0.85, -0.5), e=(0, 0.5, -0.85))
    k1 = dict(g=(0.0, -0.3 * h, -0.12 * h), b=(0.5, -0.85, -0.1), e=(0.5, 0.2, -0.85))
    waki = dict(g=(-0.14 * h, 0.04 * h, -0.24 * h), b=(-0.3, 0.9, -0.3), e=(0, 0.3, -1))
    sweep = dict(g=(0.06 * h, -0.3 * h, -0.1 * h), b=(0.6, -0.8, 0), e=(0.8, 0.6, 0))
    sweepf = dict(g=(0.18 * h, -0.12 * h, -0.08 * h), b=(0.9, 0.4, 0.1), e=(0.4, -0.9, 0))
    dash = st(lean=22, yaw=20, fwd=0.45 * h, down=0.08 * h, feet={"L": _f(J, 0.1 * h, -0.1 * h, 20), "R": _f(J, -0.06 * h, -0.55 * h, 5)},
              g=(0.1 * h, -0.3 * h, -0.1 * h), b=(0.85, -0.5, 0), e=(0.5, 0.85, 0))
    dashf = adj(dash, spine=(0, 15, 0))
    dashf["arms"] = _two((0.18 * h, -0.1 * h, -0.05 * h), (0.9, 0.4, 0.1), (0.4, -0.9, 0), TA)
    # 薙刀
    ngr = dict(g=(-0.06 * h, -0.18 * h, -0.15 * h), b=(0.1, -0.8, 0.55), e=(0, -0.55, -0.8), off=NG)
    N0 = st(**ngr)
    nwind = st(yaw=-50, g=(-0.18 * h, 0.0, -0.18 * h), b=(-0.8, 0.3, -0.2), e=(0.3, 0.9, 0), off=NG)
    nhit = st(hy=52, yaw=10, lean=12, down=0.08 * h, g=(0.05 * h, -0.28 * h, -0.25 * h), b=(0.5, -0.8, -0.3), e=(0.85, 0.5, 0), off=NG)
    nfol = st(hy=82, yaw=10, lean=10, down=0.06 * h, g=(0.18 * h, -0.1 * h, -0.22 * h), b=(0.95, 0.2, -0.2), e=(0.2, -1, 0), off=NG)
    nback = st(fwd=-0.05 * h, g=(-0.1 * h, 0.02 * h, -0.12 * h), b=(0.05, -1, 0.1), e=(0, 0.1, 1), off=NG)
    nthr = st(fwd=0.25 * h, lean=15, step=0.2 * h, g=(-0.04 * h, -0.42 * h, -0.06 * h), b=(0, -1, 0.05), e=(0, 0.05, 1), off=NG)
    # 野太刀
    D0 = st(off=ND)
    dover = st(lean=-10, g=(0.0, 0.08 * h, 0.2 * h), b=(0, 0.8, 0.55), e=(0, -0.55, 0.8), off=ND)
    dhit = st(lean=35, fwd=0.12 * h, down=0.15 * h, step=0.12 * h, g=(0.0, -0.38 * h, -0.2 * h), b=(0, -0.8, -0.6),
              e=(0, 0.6, -0.8), off=ND)
    roar = st(lean=-15, arms={"L": ("fk", 80, 85, 10), "R": ("fk", 150, 35, 10)})
    roar["head"] = (-22, 0, 0)
    plant = _two((-0.08 * h, -0.26 * h, -0.3 * h), (0, -0.15, -1), (0, -1, 0.15), TA)
    return {
        "BS_GuiwoIdleLoop": (48, [(0, S0), (24, adj(S0, chest=(2, 0, 0), off=(0, 0, -0.012 * h))), (48, S0)]),
        "BS_GuiwoCombo3": (64, [(0, S0), (12, st(**over)), (15, st(lean=15, fwd=0.08 * h, step=0.06 * h, **v1)), (19, S0),
                                (23, st(lean=14, yaw=15, fwd=0.08 * h, step=0.1 * h, **k1)), (28, st(yaw=-25, **waki)),
                                (40, st(yaw=-30, down=0.03 * h, **waki)), (46, st(hy=42, lean=12, yaw=0, fwd=0.1 * h, step=0.12 * h, **sweep)),
                                (52, st(hy=62, lean=10, fwd=0.1 * h, step=0.12 * h, **sweepf)), (64, S0)]),
        "BS_GuiwoIaiDash": (44, [(0, S0), (8, st(lean=25, yaw=-20, down=0.12 * h, **waki)), (14, dash), (18, dashf), (30, dashf), (44, S0)]),
        "BS_GuiwoNaginataSweep": (48, [(0, N0), (10, nwind), (18, nhit), (24, nfol), (48, N0)]),
        "BS_GuiwoNaginataThrust": (40, [(0, N0), (10, nback), (16, nthr), (22, nthr), (40, N0)]),
        "BS_GuiwoNodachiCleave": (56, [(0, D0), (20, dover), (26, dhit), (38, adj(dhit, spine=(-3, 0, 0))), (56, D0)]),
        "BS_GuiwoPhaseChange": (48, [(0, S0), (8, adj(S0, spine=(-10, 0, 0), off=(0, -0.05 * h, 0))), (20, roar), (36, roar), (48, S0)]),
        "BS_GuiwoWeakHit": (30, [(0, S0), (3, adj(S0, spine=(-20, 0, 0), chest=(-10, 0, 0), head=(-15, 0, 0), off=(0, -0.08 * h, -0.02 * h))),
                                 (12, adj(S0, spine=(-8, 0, 0), off=(0, -0.04 * h, 0))), (30, S0)]),
        "BS_GuiwoStaggerLoop": react_stagger_loop(S0, h, J, plant),
        "BS_GuiwoExecuted": react_executed(S0, h, J, plant),
    }


# 动作 → (出动作的模型, 生成函数)。同一兵种的 A/B 变体共用（Humanoid 重定向）。
CLIP_SETS = [("EN_Wokou_Sword_A", clips_sword), ("EN_Wokou_Archer_A", clips_archer), ("EN_Wokou_FirePot_A", clips_pot),
             ("EN_Wokou_Shield_A", clips_shield), ("BOSS_Chiyan", clips_chiyan), ("BOSS_Guiwo", clips_guiwo)]


def _model(name):
    return build_enemy(name) if name in EN_CAST else build_boss(name)


def build_clip(model, fn, clip):
    rig, J, h = _model(model)
    total, keys = fn(h, J)[clip]
    poser = Poser(J, h)
    scene = bpy.context.scene
    scene.render.fps = 24
    scene.frame_start, scene.frame_end = 0, total
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    rig.animation_data_create()
    rig.animation_data.action = bpy.data.actions.new(clip)
    prevq = {}
    for f, sp in keys:
        D, off = poser.pose(sp)
        key_D(rig, poser, f, D, off, prevq)
    bpy.ops.object.mode_set(mode="OBJECT")
    kf = [f for f, _ in keys]
    ground_keys(rig, sorted(set(kf) | set(range(0, total + 1, 3))))
    scene.frame_set(0)


def ground_keys(rig, frames, tol=0.02):
    """落地修正（第三幕清单 §2.1）：逐关键帧量全部网格最低点，低于地面 tol 以上的把髋抬到刚好贴地（只抬不压）。
    跪地 / 倒地 / 被处决片段里身体不再沉进地面；站姿片段不受影响。"""
    scene = bpy.context.scene
    meshes = [o for o in scene.objects if o.type == "MESH" and not o.name.startswith("REF_")]
    hb = rig.pose.bones["Hips"]
    for f in frames:
        scene.frame_set(f)
        dg = bpy.context.evaluated_depsgraph_get()
        mz = 1e9
        for o in meshes:
            ev = o.evaluated_get(dg)
            me = ev.to_mesh()
            if len(me.vertices):
                mz = min(mz, min((ev.matrix_world @ v.co).z for v in me.vertices))
            ev.to_mesh_clear()
        if mz < -tol:
            loc = hb.location.copy()
            loc.y -= mz
            hb.location = loc
            hb.keyframe_insert("location", frame=f)


def _recipes_anim():
    R = {}
    for model, fn in CLIP_SETS:
        cat = "Enemies" if model in EN_CAST else "Bosses"
        names = list(fn(1.7, C.joints(1.7)).keys())
        for clip in names:
            R[f"{model}@{clip}"] = (cat, (lambda m=model, f=fn, c=clip: build_clip(m, f, c)))
    return R


# ================================================================ 攻守城道具（Props ≤3k；ENV_WallBreach 为 Environments）
def build_siege_ladder():
    """竹云梯：靠在 BLD_Wall_Seg 上（梯脚在墙段局部 (x, -5.25, 0)，同朝向），梯顶铁钩挂垛口。
    Ladder 枢轴在梯脚，绕 X 转即可做「推梯」。"""
    mb = K.MB()
    lean = math.degrees(math.atan2(3.0, 8.05))
    L = 8.9
    with mb.at(0, 0, 0, rx=-lean):
        for sx in (-1, 1):
            mb.cyl(sx * 0.25, 0, 0, L, 0.045, "M_SG_Bamboo", seg=6, r_top=0.035)
            for z in (1.5, 3.5, 5.5, 7.5):
                mb.cyl(sx * 0.25, 0, z, z + 0.06, 0.05, "M_SG_Rope", seg=6)
        n = int((L - 0.4) / 0.36)
        for k in range(n):
            z = 0.35 + k * 0.36
            with mb.at(0, 0, z, ry=90):
                mb.cyl(0, 0, -0.27, 0.27, 0.025, "M_SG_Bamboo", seg=5)
        for sx in (-1, 1):                                           # 顶端铁钩（朝墙 +Y 弯下）
            mb.box(sx * 0.25 - 0.02, -0.02, L - 0.05, sx * 0.25 + 0.02, 0.3, L + 0.02, "M_SG_Iron")
            mb.box(sx * 0.25 - 0.02, 0.26, L - 0.35, sx * 0.25 + 0.02, 0.3, L, "M_SG_Iron")
            mb.cyl(sx * 0.25, 0, 0.0, 0.12, 0.05, "M_SG_Iron", seg=4)     # 梯脚铁箍
    obj(mb, "Ladder", uv=1.0)
    tz = L * math.cos(math.radians(lean))
    ty = L * math.sin(math.radians(lean))
    empty("ANCHOR_Bottom", (0, -0.5, 0))
    empty("ANCHOR_Top", (0, ty + 0.4, 7.08))
    empty("FX_Hook_L", (0.25, ty, tz))
    empty("FX_Hook_R", (-0.25, ty, tz))


def build_battering_ram():
    """冲车：四轮木架 + 生牛皮人字顶（俯视一块深色长方顶），撞木吊在脊下。
    Ram 枢轴在吊点（绕 X 摆）；Wheel_FL/FR/BL/BR 枢轴在轮轴（绕 X 转）。"""
    mb = K.MB()
    for sx in (-1, 1):
        mb.box(sx * 0.9 - 0.12, -2.3, 0.55, sx * 0.9 + 0.12, 2.3, 0.8, "M_SG_WoodDark")
        for y in (-2.1, 0.0, 2.1):
            mb.box(sx * 0.9 - 0.08, y - 0.08, 0.8, sx * 0.9 + 0.08, y + 0.08, 2.05, "M_SG_Wood")
        mb.box(sx * 0.9 - 0.1, -2.3, 1.95, sx * 0.9 + 0.1, 2.3, 2.1, "M_SG_WoodDark")
    for y in (-2.1, 2.1):
        mb.box(-0.9, y - 0.1, 0.6, 0.9, y + 0.1, 0.75, "M_SG_WoodDark")
    mb.box(-0.08, -2.4, 2.85, 0.08, 2.4, 3.0, "M_SG_WoodDark")                  # 脊梁
    for y in (-2.1, 0.0, 2.1):                                                   # 人字撑
        mb.prism([(-0.95, 2.0), (-0.8, 2.0), (0.05, 2.9), (-0.08, 2.95)], "y", y - 0.07, y + 0.07, "M_SG_Wood")
        mb.prism([(0.8, 2.0), (0.95, 2.0), (0.08, 2.95), (-0.05, 2.9)], "y", y - 0.07, y + 0.07, "M_SG_Wood")
    for sx in (-1, 1):                                                           # 生牛皮顶，两坡
        mb.prism([(sx * 1.2, 1.88), (sx * 1.2, 1.98), (0, 3.08), (0, 2.98)] if sx < 0 else
                 [(sx * 1.2, 1.98), (sx * 1.2, 1.88), (0, 2.98), (0, 3.08)], "y", -2.6, 2.5, "M_SG_Hide")
        for y in (-1.8, -0.4, 1.0):                                              # 皮块补丁
            with mb.at(sx * 0.62, y, 2.5, ry=sx * 42.5):
                mb.box(-0.35, -0.3, 0.0, 0.35, 0.3, 0.03, "M_SG_HideDark")
    obj(mb, "Frame", uv=1.0)
    mb = K.MB()
    mb.cyl(0, 0, 0, 0, 0.01, "M_SG_Rope", seg=3)
    with mb.at(0, 0, -1.6, rx=90):
        mb.cyl(0, 0, -2.0, 2.6, 0.18, "M_SG_WoodWet", seg=8)
        mb.cyl(0, 0, 2.6, 2.95, 0.2, "M_SG_Iron", seg=8, r_top=0.08)
        for z in (-1.6, 0.0, 1.6):
            mb.cyl(0, 0, z, z + 0.08, 0.2, "M_SG_Iron", seg=8)
    for y in (-0.8, 0.8):
        mb.box(-0.03, y - 0.03, -1.45, 0.03, y + 0.03, 0.0, "M_SG_Rope")
    obj(mb, "Ram", (0, 0, 2.85), uv=1.0)
    for nm, x, y in (("Wheel_FL", 1.12, -1.6), ("Wheel_FR", -1.12, -1.6), ("Wheel_BL", 1.12, 1.6), ("Wheel_BR", -1.12, 1.6)):
        mb = K.MB()
        with mb.at(0, 0, 0, ry=90):
            mb.cyl(0, 0, -0.09, 0.09, 0.45, "M_SG_WoodDark", seg=12)
            mb.cyl(0, 0, -0.12, 0.12, 0.1, "M_SG_Iron", seg=6)
        obj(mb, nm, (x, y, 0.45), uv=1.0)
    empty("FX_RamHit", (0, -3.0, 1.25))
    for i, (x, y) in enumerate(((0.6, 2.7), (-0.6, 2.7), (0.6, 1.0), (-0.6, 1.0))):
        empty(f"ANCHOR_Push_{i + 1}", (x, y, 0))
    obj_col = K.MB()
    obj_col.box(-1.3, -2.6, 0, 1.3, 2.6, 3.1, "M_SG_Wood")
    obj(obj_col, "COL_Ram", uv=1.0)


def build_fire_ship():
    """火船：8 m 小船堆满柴草、火油罐，破帆桅杆，船头铁钩（撞水门用）。
    原点在船底中心；吃水线 ANCHOR_Waterline（z=0.45，团结里把船下沉到这里）。FX_Fire_1..4 / FX_Smoke 火点。
    子物体：Hull（船体）/ Cargo（柴草火油，可烧）/ Cargo_Burnt（烧剩的焦堆）/ Mast（桅杆，枢轴在桅脚，可倒）。"""
    def sec(w, top, bot=0.0):
        return [(-w / 2, top), (-w * 0.47, top - 0.35), (-w * 0.22, bot), (w * 0.22, bot), (w * 0.47, top - 0.35), (w / 2, top)]
    mb = K.MB()
    loft_poly(mb, [(-4.0, sec(0.12, 1.55, 0.9)), (-3.3, sec(1.2, 1.3, 0.25)), (-2.0, sec(2.0, 1.12)), (0.0, sec(2.2, 1.05)),
                   (2.5, sec(2.1, 1.12)), (3.7, sec(1.8, 1.3, 0.2))], "M_SG_WoodDark")
    for y0, y1 in ((-3.0, -1.0), (-0.9, 1.1), (1.2, 3.3)):
        mb.box(-0.95, y0, 1.06, 0.95, y1, 1.12, "M_SG_Wood")
    for sx in (-1, 1):
        mb.box(sx * 1.05 - 0.04, -3.0, 1.05, sx * 1.05 + 0.04, 3.5, 1.4, "M_SG_Wood")
    mb.box(-0.06, -4.6, 1.2, 0.06, -3.8, 1.32, "M_SG_Iron")                      # 船头钩
    for sx in (-1, 1):
        mb.box(-0.04 + sx * 0.12, -4.75, 1.0, 0.04 + sx * 0.12, -4.55, 1.32, "M_SG_Iron")
    mb.box(-0.6, 3.3, 1.1, 0.6, 3.75, 1.5, "M_SG_WoodDark")                       # 船尾舵台
    with mb.at(0, 4.0, 0.7, rx=-30):
        mb.box(-0.05, -0.1, -0.7, 0.05, 0.1, 0.6, "M_SG_WoodDark")
    obj(mb, "Hull", uv=1.0)
    rnd = random.Random(41)
    mb = K.MB()
    for k in range(14):                                                          # 柴捆（横放）
        y = -2.6 + (k % 7) * 0.75
        z = 1.25 + (k // 7) * 0.32
        with mb.at(rnd.uniform(-0.2, 0.2), y, z, rz=rnd.uniform(-15, 15), ry=90):
            mb.cyl(0, 0, -0.75, 0.75, 0.16, "M_SG_Straw", seg=6)
            mb.cyl(0, 0, -0.2, -0.1, 0.17, "M_SG_Rope", seg=6)
    for k, (x, y) in enumerate(((-0.6, -1.0), (0.6, -0.4), (-0.55, 1.4), (0.55, 2.1), (0.0, 0.6))):
        mb_add(mb, ellipsoid((x, y, 1.42), 0.22, 0.22, 0.28, seg=8, rings=4), "M_SG_Clay")
        mb.cyl(x, y, 1.65, 1.75, 0.1, "M_SG_ClayDark", seg=6)
    obj(mb, "Cargo", uv=1.0)
    mb = K.MB()
    for k in range(8):
        with mb.at(rnd.uniform(-0.5, 0.5), -2.4 + k * 0.7, 1.15, rz=rnd.uniform(-60, 60), ry=90):
            mb.cyl(0, 0, -0.6, 0.6, 0.08, "M_SG_Char", seg=5)
    obj(mb, "Cargo_Burnt", uv=1.0)
    mb = K.MB()
    mb.cyl(0, 0, 0, 5.2, 0.09, "M_SG_WoodDark", seg=6, r_top=0.06)
    mb.box(-1.3, -0.05, 4.7, 1.3, 0.05, 4.82, "M_SG_WoodDark")
    mb.prism([(-1.2, 4.7), (1.2, 4.7), (0.9, 2.6), (-1.0, 2.2)], "y", 0.03, 0.06, "M_SG_Sail")
    mb.prism([(0.2, 2.6), (0.9, 2.6), (0.7, 3.4)], "y", 0.06, 0.07, "M_SG_Char")
    obj(mb, "Mast", (0, -0.6, 1.1), uv=1.0)
    for i, (x, y, z) in enumerate(((0.0, -2.2, 1.8), (0.3, -0.3, 1.9), (-0.3, 1.4, 1.9), (0.2, 2.8, 1.7))):
        empty(f"FX_Fire_{i + 1}", (x, y, z), size=0.3)
    empty("FX_Smoke", (0, 0.2, 2.6), size=0.4)
    empty("ANCHOR_Waterline", (0, 0, 0.45), size=0.5)
    empty("ANCHOR_Boss", (0, 3.1, 1.12))


def build_cannon():
    """明制铁将军炮 + 木炮架。Barrel 枢轴在炮耳（绕 X 俯仰）；FX_Muzzle / FX_Fuse 挂在 Barrel 下。"""
    mb = K.MB()
    for sx in (-1, 1):
        mb.prism([(-0.75, 0.0), (0.75, 0.0), (0.75, 0.3), (-0.2, 0.68), (-0.55, 0.6)], "x", sx * 0.28 - 0.06, sx * 0.28 + 0.06,
                 "M_SG_Wood")
    for y in (-0.55, 0.5):
        mb.box(-0.34, y - 0.08, 0.05, 0.34, y + 0.08, 0.22, "M_SG_WoodDark")
    mb.box(-0.2, 0.3, 0.3, 0.2, 0.62, 0.45, "M_SG_WoodDark")                       # 俯仰楔
    for sx in (-1, 1):
        mb.box(sx * 0.28 - 0.07, -0.22, 0.55, sx * 0.28 + 0.07, -0.1, 0.72, "M_SG_Iron")
    obj(mb, "Carriage", uv=0.5)
    mb = K.MB()
    A1L = __import__("rupu_act1")
    A1L.loft_y(mb, [(-1.0, 0, 0, 0.11, 0.11), (-0.92, 0, 0, 0.13, 0.13), (-0.85, 0, 0, 0.1, 0.1), (-0.2, 0, 0, 0.12, 0.12),
                    (0.35, 0, 0, 0.16, 0.16), (0.62, 0, 0, 0.17, 0.17), (0.7, 0, 0, 0.1, 0.1), (0.8, 0, 0, 0.05, 0.05)],
                "M_SG_Iron", seg=10)
    for y in (-0.6, -0.25, 0.1, 0.45):
        A1L.loft_y(mb, [(y, 0, 0, 0.14 + (y + 0.6) * 0.04, 0.14 + (y + 0.6) * 0.04), (y + 0.06, 0, 0, 0.14 + (y + 0.6) * 0.04,
                                                                                        0.14 + (y + 0.6) * 0.04)], "M_SG_Bronze", seg=10)
    with mb.at(0, 0, 0, ry=90):
        mb.cyl(0, 0, -0.26, 0.26, 0.045, "M_SG_Iron", seg=6)
    mb.cyl(0, 0.52, 0.15, 0.2, 0.02, "M_SG_Bronze", seg=6)
    obj(mb, "Barrel", (0, -0.16, 0.66), uv=0.5)
    bar = bpy.data.objects["Barrel"]
    empty("FX_Muzzle", (0, -1.02, 0), parent=bar)
    empty("FX_Fuse", (0, 0.52, 0.21), parent=bar, size=0.05)
    empty("ANCHOR_Gunner", (-0.7, 0.9, 0))
    empty("ANCHOR_Loader", (0.7, -1.1, 0))


def build_cannon_emplacement():
    """炮位：木平台 + 前沿沙袋矮墙 + 火药桶 + 实弹/散弹两堆 + 推杆架，放在敌台炮位垫石上（ANCHOR_Cannon 放炮）。
    Ammo_Solid（实弹）/ Ammo_Scatter（散弹）/ Powder（火药桶，盖子 Powder_Lid）可单独显隐。"""
    mb = K.MB()
    mb.box(-1.4, -1.3, 0, 1.4, 1.3, 0.12, "M_SG_Wood")
    for x in (-1.2, -0.6, 0.0, 0.6, 1.2):
        mb.box(x - 0.01, -1.3, 0.12, x + 0.01, 1.3, 0.125, "M_SG_WoodDark")
    rnd = random.Random(7)
    for k in range(7):                                                             # 前沿沙袋（不挡垛口）
        for lay in range(2):
            x = -1.35 + k * 0.4 + lay * 0.2
            if x > 1.25:
                continue
            with mb.at(x, -1.45, 0.12 + lay * 0.18, rz=rnd.uniform(-6, 6)):
                mb.box(-0.2, -0.13, 0, 0.2, 0.13, 0.17, "M_SG_Sand")
    mb.box(1.5, -0.6, 0, 1.6, 0.9, 1.1, "M_SG_WoodDark")                           # 推杆架
    for z in (0.4, 0.9):
        mb.box(1.45, -0.6, z, 1.65, 0.9, z + 0.05, "M_SG_WoodDark")
    rod(mb, (1.55, -0.3, 0.05), (1.55, -0.2, 2.0), 0.02, "M_SG_Wood")
    rod(mb, (1.55, 0.5, 0.05), (1.55, 0.6, 1.9), 0.02, "M_SG_Wood")
    mb_add(mb, ellipsoid((1.55, 0.6, 1.9), 0.05, 0.05, 0.08, seg=6, rings=3), "M_SG_Cloth")
    with mb.at(-1.2, 0.95, 0.12):                                                  # 水桶（洗炮）
        mb.cyl(0, 0, 0, 0.35, 0.17, "M_SG_Wood", seg=8, r_top=0.19)
        mb.cyl(0, 0, 0.3, 0.31, 0.18, "M_SG_Water", seg=8)
    obj(mb, "Platform", uv=1.0)
    mb = K.MB()
    for lay, n in ((0, 3), (1, 2), (2, 1)):
        for i in range(n):
            for j in range(n):
                x = (i - (n - 1) / 2) * 0.14
                y = (j - (n - 1) / 2) * 0.14
                mb_add(mb, ellipsoid((x, y, 0.07 + lay * 0.11), 0.07, 0.07, 0.07, seg=6, rings=3), "M_SG_Ball")
    obj(mb, "Ammo_Solid", (-0.9, 0.3, 0.12), uv=0.5)
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.3, 0.22, "M_SG_Rope", seg=8, r_top=0.25)
    for i in range(4):
        mb_add(mb, ellipsoid(((i % 2 - 0.5) * 0.18, (i // 2 - 0.5) * 0.18, 0.34), 0.09, 0.09, 0.07, seg=6, rings=3), "M_SG_Cloth")
        mb.cyl((i % 2 - 0.5) * 0.18, (i // 2 - 0.5) * 0.18, 0.38, 0.42, 0.03, "M_SG_Rope", seg=5)
    obj(mb, "Ammo_Scatter", (-0.9, -0.4, 0.12), uv=0.5)
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.5, 0.2, "M_SG_WoodDark", seg=10)
    for z in (0.06, 0.25, 0.44):
        mb.cyl(0, 0, z, z + 0.03, 0.21, "M_SG_Iron", seg=10)
    obj(mb, "Powder", (1.0, 0.95, 0.12), uv=0.5)
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.04, 0.2, "M_SG_Wood", seg=10)
    obj(mb, "Powder_Lid", (1.0, 0.95, 0.62), uv=0.5)
    empty("ANCHOR_Cannon", (0, 0.0, 0.12), kind="ARROWS", size=0.5)
    empty("ANCHOR_Gunner", (-0.7, 0.9, 0.12))
    empty("ANCHOR_Powder", (1.0, 0.6, 0.12))
    empty("ANCHOR_Solid", (-0.9, 0.7, 0.12))
    empty("ANCHOR_Scatter", (-0.9, -0.8, 0.12))


def build_water_wheel():
    """筒车式水轮：A 字木架 + 轮（12 叶板 + 竹筒）+ 手摇绞把。Wheel 枢轴在轮轴（绕 X 转，绞把随轮转）；
    ANCHOR_Turn 玩家站位；Trough（水槽）出水口 FX_Water。原点在架底中心，轮底比原点低 0.2 m（放进渠里）。"""
    mb = K.MB()
    for sx in (-1, 1):
        x = sx * 0.55
        for sy in (-1, 1):
            rod(mb, (x, sy * 1.2, 0), (x, sy * 0.05, 2.15), 0.07, "M_SG_Wood", seg=6)
        mb.box(x - 0.08, -1.3, 0.0, x + 0.08, 1.3, 0.15, "M_SG_WoodDark")
        mb.box(x - 0.1, -0.12, 2.05, x + 0.1, 0.12, 2.3, "M_SG_WoodDark")
    mb.box(-0.65, -1.3, 0.0, 0.65, -1.15, 0.15, "M_SG_WoodDark")
    mb.box(-0.65, 1.15, 0.0, 0.65, 1.3, 0.15, "M_SG_WoodDark")
    obj(mb, "Frame", uv=1.0)
    mb = K.MB()
    R = 2.2
    with mb.at(0, 0, 0, ry=90):
        mb.cyl(0, 0, -0.95, 0.95, 0.09, "M_SG_WoodDark", seg=8)
        for sx in (-0.4, 0.4):
            mb.cyl(0, 0, sx - 0.05, sx + 0.05, 0.25, "M_SG_WoodDark", seg=8)
    for k in range(12):
        a = 2 * math.pi * k / 12
        for sx in (-0.4, 0.4):
            rod(mb, (sx, 0, 0), (sx, R * math.cos(a), R * math.sin(a)), 0.035, "M_SG_Wood", seg=4)
        c, s = math.cos(a), math.sin(a)
        with mb.at(0, R * c, R * s, rx=math.degrees(a)):
            mb.box(-0.48, -0.03, -0.22, 0.48, 0.03, 0.05, "M_SG_WoodWet")
            with mb.at(0.3, 0, 0.12, rx=90):
                mb.cyl(0, 0, -0.15, 0.15, 0.06, "M_SG_Bamboo", seg=5)
    for k in range(24):
        a0, a1 = 2 * math.pi * k / 24, 2 * math.pi * (k + 1) / 24
        for sx in (-0.45, 0.45):
            rod(mb, (sx, R * 0.92 * math.cos(a0), R * 0.92 * math.sin(a0)), (sx, R * 0.92 * math.cos(a1), R * 0.92 * math.sin(a1)),
                0.04, "M_SG_WoodDark", seg=4)
    for k in range(4):                                                             # 绞把（轴端 +X）
        a = math.pi / 2 * k + math.pi / 4
        rod(mb, (1.0, 0, 0), (1.0, 0.65 * math.cos(a), 0.65 * math.sin(a)), 0.04, "M_SG_Wood", seg=5)
        rod(mb, (1.0, 0.65 * math.cos(a), 0.65 * math.sin(a)), (1.25, 0.65 * math.cos(a), 0.65 * math.sin(a)), 0.035, "M_SG_WoodDark", seg=5)
    obj(mb, "Wheel", (0, 0, 2.0), uv=1.0)
    mb = K.MB()
    mb.box(-0.95, 0.4, 3.9, -0.55, 2.4, 3.95, "M_SG_Wood")
    for sx in (-0.95, -0.6):
        mb.box(sx, 0.4, 3.95, sx + 0.05, 2.4, 4.1, "M_SG_Wood")
    for y in (1.0, 2.2):
        mb.box(-0.8, y - 0.05, 0.0, -0.7, y + 0.05, 3.9, "M_SG_WoodDark")
    obj(mb, "Trough", uv=1.0)
    empty("FX_Water", (-0.75, 2.4, 3.95), size=0.2)
    empty("ANCHOR_Turn", (1.7, 0.0, 0))


def build_gate_bar():
    """城门门扇 + 门闩（配 BLD_Wall_GateBase 门洞宽 4.4）。原点在门洞地面中心，外侧 = -Y。
    Door_L（+X 侧）/ Door_R（-X 侧）枢轴在门轴，绕 Z 开；Bar 门闩（向上抬起）；Bar_Sockets 门洞两侧的闩槽；
    Broken = 撞破状态（替换 Door_L/R + Bar）。FX_RamHit 冲车撞点。"""
    W2, H = 2.2, 4.2
    for nm, sx in (("Door_L", 1), ("Door_R", -1)):
        mb = K.MB()
        for i in range(5):
            xa = -sx * (0.02 + i * 0.436)
            xb = -sx * (0.02 + (i + 1) * 0.436 - 0.01)
            mb.box(min(xa, xb), -0.08, 0.02, max(xa, xb), 0.06, H, "M_SG_WoodDark")
        for z in (0.5, 2.1, 3.7):
            mb.box(-sx * 0.05 if sx < 0 else -W2 + 0.05, 0.06, z - 0.12, W2 - 0.05 if sx < 0 else -0.05, 0.14, z + 0.12, "M_SG_Wood")
        for r_ in range(6):
            for c_ in range(4):
                x = -sx * (0.3 + c_ * 0.5)
                mb.box(x - 0.03, -0.11, 0.4 + r_ * 0.65, x + 0.03, -0.08, 0.46 + r_ * 0.65, "M_SG_Iron")
        for z in (1.4, 1.95):                                                    # 闩扣
            x = -sx * (W2 - 0.35)
            mb.box(x - 0.08, 0.14, z - 0.04, x + 0.08, 0.36, z + 0.04, "M_SG_Iron")
        obj(mb, nm, (sx * W2, 0, 0), uv=1.0)
    mb = K.MB()
    mb.box(-2.6, -0.13, -0.13, 2.6, 0.13, 0.13, "M_SG_Wood")
    for x in (-2.0, 2.0):
        mb.box(x - 0.05, -0.14, -0.14, x + 0.05, 0.14, 0.14, "M_SG_Iron")
    obj(mb, "Bar", (0, 0.27, 1.68), uv=1.0)
    mb = K.MB()
    for sx in (-1, 1):
        mb.box(sx * 2.2 - 0.2 * (1 - sx) / 2 - 0.0, 0.1, 1.5, sx * 2.2 + 0.2 * (1 + sx) / 2, 0.45, 1.56, "M_SG_Iron")
        mb.box(min(sx * 2.2, sx * 2.5), 0.1, 1.5, max(sx * 2.2, sx * 2.5), 0.45, 1.56, "M_SG_Iron")
        mb.box(min(sx * 2.2, sx * 2.5), 0.1, 1.8, max(sx * 2.2, sx * 2.5), 0.45, 1.86, "M_SG_Iron")
    obj(mb, "Bar_Sockets", uv=1.0)
    rnd = random.Random(3)
    mb = K.MB()
    for sx in (-1, 1):                                                            # 两扇残门：参差的板
        for i in range(5):
            xa = sx * (W2 - 0.02 - i * 0.436)
            top = rnd.uniform(0.8, 3.6) if i > 1 else rnd.uniform(3.0, 4.1)
            mb.box(min(xa, xa - sx * 0.42), -0.08, 0.02, max(xa, xa - sx * 0.42), 0.06, top, "M_SG_WoodDark")
            mb.prism([(min(xa, xa - sx * 0.42), top), (max(xa, xa - sx * 0.42), top), (xa - sx * 0.21, top + 0.35)], "y", -0.08, 0.06,
                     "M_SG_Char")
    for k in range(9):                                                            # 地上碎板
        with mb.at(rnd.uniform(-1.6, 1.6), rnd.uniform(0.4, 2.5), 0.03, rz=rnd.uniform(0, 180)):
            mb.box(-0.6, -0.1, 0, 0.6, 0.1, 0.06, "M_SG_WoodDark")
    with mb.at(0.7, 1.4, 0.13, rz=20):
        mb.box(-1.2, -0.13, -0.13, 0.2, 0.13, 0.13, "M_SG_Wood")
        mb.box(0.25, -0.13, -0.13, 1.1, 0.13, 0.13, "M_SG_Wood")
    obj(mb, "Broken", uv=1.0)
    empty("FX_RamHit", (0, -0.2, 1.6), size=0.3)
    empty("FX_Splinters", (0, 0.2, 1.8), size=0.3)


def build_chevaux():
    """拒马枪（Juma，原点）+ 鹿角（Lujiao，在 +X 3.6 m 处）：两件可分别显隐/摆放。COL_Juma / COL_Lujiao 碰撞。"""
    mb = K.MB()
    with mb.at(0, 0, 0.72, ry=90):
        mb.cyl(0, 0, -1.5, 1.5, 0.11, "M_SG_WoodDark", seg=8)
    for x in (-1.2, -0.6, 0.0, 0.6, 1.2):
        for sgn in (-1, 1):
            with mb.at(x + sgn * 0.05, 0, 0.72, rx=sgn * 48):
                mb.cyl(0, 0, -0.9, 0.55, 0.045, "M_SG_Wood", seg=6)
                mb.cyl(0, 0, 0.55, 0.85, 0.045, "M_SG_Iron", seg=6, r_top=0.003)
                mb.cyl(0, 0, -1.05, -0.9, 0.003, "M_SG_Wood", seg=6, r_top=0.045)
    obj(mb, "Juma", uv=1.0)
    rnd = random.Random(11)
    mb = K.MB()
    rod(mb, (-1.5, 0, 0.15), (1.5, 0.1, 0.2), 0.14, "M_SG_Wood", seg=6)
    for k in range(14):
        x = -1.4 + k * 0.21
        a = rnd.uniform(-35, 35)
        tip = (x + rnd.uniform(-0.2, 0.2), -1.2 + rnd.uniform(-0.2, 0.2), 0.7 + rnd.uniform(-0.2, 0.3))
        rod(mb, (x, 0.3, 0.1), tip, 0.04, "M_SG_Wood", seg=4, r1=0.006)
        if k % 2:
            mid = ((x + tip[0]) / 2, (0.3 + tip[1]) / 2, (0.1 + tip[2]) / 2)
            rod(mb, mid, (mid[0] + 0.3 * math.sin(math.radians(a)), mid[1] - 0.3, mid[2] + 0.3), 0.02, "M_SG_Wood", seg=4, r1=0.004)
    obj(mb, "Lujiao", (3.6, 0, 0), uv=1.0)
    c = K.MB()
    c.box(-1.55, -0.6, 0, 1.55, 0.6, 1.0, "M_SG_Wood")
    obj(c, "COL_Juma", uv=1.0)
    c = K.MB()
    c.box(-1.5, -1.3, 0, 1.5, 0.45, 0.8, "M_SG_Wood")
    obj(c, "COL_Lujiao", (3.6, 0, 0), uv=1.0)


def build_fire_oil():
    """熬火油：砖灶 + 铁锅（Cauldron，枢轴在倾倒轴，绕 X 转向 -Y 倒油）+ 倒油架 + 三个封口油坛 + 一筐小火罐。
    摆在城墙走道上，-Y 朝城外。FX_Fire（灶火）/ FX_Pour（锅嘴）/ FX_Smoke。"""
    mb = K.MB()
    mb.box(-0.55, -0.45, 0, 0.55, 0.45, 0.5, "M_SG_Brick")
    mb.box(-0.25, -0.46, 0.05, 0.25, -0.44, 0.35, "M_SG_Char")
    for sx in (-1, 1):
        mb.box(sx * 0.62 - 0.05, -0.05, 0, sx * 0.62 + 0.05, 0.05, 1.05, "M_SG_WoodDark")
    for k, (x, y) in enumerate(((1.0, 0.3), (1.35, 0.0), (1.0, -0.3))):
        with mb.at(x, y, 0):
            mb_add(mb, ellipsoid((0, 0, 0.28), 0.18, 0.18, 0.28, seg=8, rings=4), "M_SG_Clay")
            mb.cyl(0, 0, 0.5, 0.6, 0.08, "M_SG_ClayDark", seg=6)
            mb_add(mb, ellipsoid((0, 0, 0.6), 0.1, 0.1, 0.04, seg=6, rings=2), "M_SG_Cloth")
    with mb.at(-1.05, 0.1, 0):
        mb.cyl(0, 0, 0, 0.3, 0.25, "M_SG_Straw", seg=8, r_top=0.3)
        for i in range(5):
            a = i * 72
            mb_add(mb, ellipsoid((0.15 * math.cos(math.radians(a)), 0.15 * math.sin(math.radians(a)), 0.34), 0.07, 0.07, 0.07, seg=6,
                                 rings=3), "M_SG_Clay")
    rod(mb, (0.4, 0.6, 0.0), (0.2, 0.3, 1.2), 0.02, "M_SG_Wood")
    obj(mb, "Stove", uv=1.0)
    mb = K.MB()
    mb.cyl(0, 0, -0.3, 0.05, 0.3, "M_SG_Iron", seg=12, r_top=0.45)
    mb.cyl(0, 0, -0.0, 0.01, 0.43, "M_SG_Oil", seg=12)
    mb.box(-0.06, -0.52, -0.02, 0.06, -0.4, 0.05, "M_SG_Iron")
    with mb.at(0, 0, 0, ry=90):
        mb.cyl(0, 0, -0.62, 0.62, 0.025, "M_SG_Iron", seg=5)
    obj(mb, "Cauldron", (0, 0, 0.85), uv=1.0)
    cau = bpy.data.objects["Cauldron"]
    empty("FX_Pour", (0, -0.5, 0.05), parent=cau)
    empty("FX_Fire", (0, -0.2, 0.25), size=0.2)
    empty("FX_Smoke", (0, 0, 1.3), size=0.3)
    empty("ANCHOR_Tip", (0.9, 0.0, 0))


def build_bucket_sand():
    """水桶 / 沙袋：Bucket（单只，可拿，ANCHOR_Handle 手握点）、Bucket_Row（三桶一排）、Sandbags（两层沙袋矮墙）、
    Sandbag（单袋，可扛）、SandBasket（沙筐 + 铁锹）。"""
    def bucket(mb, x, y, water=True):
        with mb.at(x, y, 0):
            mb.cyl(0, 0, 0, 0.38, 0.15, "M_SG_Wood", seg=10, r_top=0.18)
            for z in (0.06, 0.3):
                mb.cyl(0, 0, z, z + 0.03, 0.155 + z * 0.08, "M_SG_Iron", seg=10)
            if water:
                mb.cyl(0, 0, 0.32, 0.33, 0.17, "M_SG_Water", seg=10)
            for sx in (-1, 1):
                rod(mb, (sx * 0.18, 0, 0.36), (sx * 0.1, 0, 0.55), 0.012, "M_SG_Rope", seg=4)
            rod(mb, (-0.1, 0, 0.55), (0.1, 0, 0.55), 0.015, "M_SG_Wood", seg=4)
    mb = K.MB()
    bucket(mb, 0, 0)
    obj(mb, "Bucket", uv=0.5)
    empty("ANCHOR_Handle", (0, 0, 0.55), parent=bpy.data.objects["Bucket"], size=0.05)
    mb = K.MB()
    for i in range(3):
        bucket(mb, 0.7 + i * 0.42, 0)
    obj(mb, "Bucket_Row", uv=0.5)
    rnd = random.Random(5)
    mb = K.MB()
    for lay in range(3):
        for k in range(5 - lay):
            with mb.at(-0.9 + k * 0.42 + lay * 0.21, 0.0, lay * 0.18, rz=rnd.uniform(-5, 5)):
                mb.box(-0.21, -0.14, 0, 0.21, 0.14, 0.18, "M_SG_Sand")
                mb.box(0.18, -0.06, 0.04, 0.24, 0.06, 0.14, "M_SG_Rope")
    obj(mb, "Sandbags", (0, 0.9, 0), uv=0.5)
    mb = K.MB()
    mb.box(-0.21, -0.14, 0, 0.21, 0.14, 0.18, "M_SG_Sand")
    mb.box(0.18, -0.06, 0.04, 0.24, 0.06, 0.14, "M_SG_Rope")
    obj(mb, "Sandbag", (-0.7, 0.0, 0), uv=0.5)
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.3, 0.25, "M_SG_Straw", seg=10, r_top=0.32)
    mb_add(mb, ellipsoid((0, 0, 0.28), 0.3, 0.3, 0.1, seg=10, rings=3, zmin=0.0), "M_SG_Sand")
    rod(mb, (0.1, 0.05, 0.3), (0.35, 0.1, 1.1), 0.02, "M_SG_Wood")
    with mb.at(0.08, 0.05, 0.3, ry=-18):
        mb.box(-0.1, -0.01, -0.2, 0.1, 0.01, 0.05, "M_SG_Iron")
    obj(mb, "SandBasket", (-1.4, 0.2, 0), uv=0.5)


def build_stretcher():
    """伤兵担架：两根竹杠 + 布兜 + 横撑，上面躺着一个包扎的伤兵（Wounded，静态网格，可隐藏单用担架）。
    ANCHOR_Bearer_Front/Back 抬担架的人站位（-Y 为头前）。"""
    mb = K.MB()
    for sx in (-1, 1):
        rod(mb, (sx * 0.3, -1.25, 0.12), (sx * 0.3, 1.25, 0.12), 0.03, "M_SG_Bamboo", seg=6)
    for y in (-0.85, 0.85):
        mb.box(-0.32, y - 0.03, 0.08, 0.32, y + 0.03, 0.12, "M_SG_Wood")
        for sx in (-1, 1):
            mb.box(sx * 0.3 - 0.03, y - 0.03, 0.0, sx * 0.3 + 0.03, y + 0.03, 0.1, "M_SG_Wood")
    mb.prism([(-0.29, 0.13), (0.29, 0.13), (0.24, 0.07), (-0.24, 0.07)], "y", -0.9, 0.9, "M_SG_Cloth")
    obj(mb, "Stretcher", uv=0.5)
    # 伤兵：用人物生成器造一个明人义兵，摆成平躺，再把骨架变形烘成静态网格
    cfg = dict(H=1.68, outfit="jacket", top="M_EN_SW_CoatB", pants="M_EN_FP_PantsB", shoe="M_EN_Straw", wrap="M_EN_Wrap",
               sash="M_EN_Cord", hair="bun", band="M_SG_Bandage", skin="M_EN_SkinDark", extras=[])
    rig = C.build_character("Wounded", cfg)
    h = cfg["H"]
    J = C.joints(h)
    P = Poser(J, h)
    D, off = P.pose({"hips": (-90, 0, 0), "head": (8, 15, 0), "off": (0, 0, 0),
                     "feet": {"L": ("fk", 2, 8, 0, 3), "R": ("fk", 10, 25, 0, 2)},
                     "arms": {"L": ("fk", 10, 15, 30), "R": ("fk", 5, 20, 15)}})
    bpy.context.view_layer.objects.active = rig
    bpy.ops.object.mode_set(mode="POSE")
    key_D(rig, P, 0, D, off, {})
    bpy.ops.object.mode_set(mode="OBJECT")
    ob = bpy.data.objects["Wounded"]
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(ob.evaluated_get(dg))
    mw = ob.matrix_world.copy()
    bpy.data.objects.remove(ob, do_unlink=True)
    bpy.data.objects.remove(rig, do_unlink=True)
    for a in list(bpy.data.actions):
        bpy.data.actions.remove(a)
    me.transform(mw)
    # 平躺后：髋在原点高度 0.53h，身体沿 -Y（头在 -Y）；落到担架布面上
    zmin = min(v.co.z for v in me.vertices)
    ymid = (min(v.co.y for v in me.vertices) + max(v.co.y for v in me.vertices)) / 2
    me.transform(Matrix.Translation((0, -ymid, 0.13 - zmin)))
    w = bpy.data.objects.new("Wounded", me)
    bpy.context.scene.collection.objects.link(w)
    w.vertex_groups.clear()
    mb = K.MB()                                                                      # 胸口包扎 + 血迹
    mb.box(-0.15, -0.35, 0.3, 0.15, -0.15, 0.33, "M_SG_Bandage")
    mb.box(-0.05, -0.3, 0.33, 0.06, -0.2, 0.335, "M_SG_Blood")
    obj(mb, "Bandage", uv=0.5)
    empty("ANCHOR_Bearer_Front", (0, -1.55, 0))
    empty("ANCHOR_Bearer_Back", (0, 1.55, 0))


def build_wall_breach():
    """城墙破口 / 火起状态（Environments，配 BLD_Wall_Seg 8 m 墙段，原点同墙段：地面中心，外侧 -Y）。
    Breach_Wall：替换整段墙的破口墙体（两端完好，中段塌到约 3.2 m，破口顶是夯土芯）；
    Rubble（墙外瓦砾坡，敌兵从这里爬进来）+ COL_Rubble（坡道碰撞）；
    Scorch：焦痕贴片（贴合原墙外立面/走道/垛墙，也可以单独叠在完好的 BLD_Wall_Seg 上表示「火起」）；
    Burning_Debris：焦黑木梁。FX_Fire_1..3 / FX_Smoke / FX_Dust，ANCHOR_BreachTop / ANCHOR_RubbleFoot。"""
    WALK = 7.08
    mb = K.MB()

    def body(x0, x1, parapet=True):
        mb.prism([(-2.5, -0.5), (2.5, -0.5), (2.5, 7.0), (-2.1, 7.0)], "x", x0, x1, "M_Wall_Stone")
        mb.box(x0, -1.5, 7.0, x1, 2.5, WALK, "M_Wall_Top")
        mb.box(x0, 2.35, 6.75, x1, 2.6, 7.0, "M_Stone_Base")
        if parapet:
            mb.box(x0, -2.1, 7.0, x1, -1.5, 7.95, "M_Wall_Stone")
            mb.box(x0, -2.2, 7.95, x1, -1.4, 8.05, "M_Wall_Top")
    body(-4.0, -2.3)
    body(2.5, 4.0)
    mb.crenels(-4.0, -2.3, -2.1, -1.5, 8.05, 8.75, "M_Wall_Stone")
    mb.crenels(2.5, 4.0, -2.1, -1.5, 8.05, 8.75, "M_Wall_Stone")
    mb.box(-4.0, -2.75, -0.5, 4.0, -2.35, 0.45, "M_Stone_Base")
    rnd = random.Random(21)
    cols = 8
    for i in range(cols):
        xa = -2.3 + 4.8 * i / cols
        xb = -2.3 + 4.8 * (i + 1) / cols
        t = abs((xa + xb) / 2 - 0.1) / 2.4
        ho = 3.0 + 4.0 * t * t + rnd.uniform(-0.25, 0.25)
        hi = min(7.0, ho + 1.2 + rnd.uniform(0, 0.6))
        yo = -2.5 + 0.4 * (ho + 0.5) / 7.5
        mb.prism([(-2.5, -0.5), (0.0, -0.5), (0.0, ho), (yo, ho)], "x", xa, xb, "M_Wall_Stone")
        mb.prism([(0.0, -0.5), (2.5, -0.5), (2.5, hi), (0.0, hi)], "x", xa, xb, "M_Wall_Stone")
        mb.box(xa + 0.02, yo + 0.05, ho, xb - 0.02, 0.0, ho + 0.06, "M_SG_Earth")
        mb.box(xa + 0.02, 0.02, hi, xb - 0.02, 2.45, hi + 0.06, "M_SG_Earth")
    for x, h_ in ((-2.3, 1.0), (2.5, 0.8)):                                        # 断垛口残块
        mb.box(x - 0.35, -2.1, 7.0, x + 0.35, -1.5, 7.0 + h_, "M_Wall_Stone")
    obj(mb, "Breach_Wall", uv=2.0)
    mb = K.MB()
    mb.prism([(-2.4, 0.0), (-8.0, 0.0), (-2.55, 3.1)], "x", -2.4, 2.6, "M_SG_Rubble")
    mb.prism([(2.4, 0.0), (6.0, 0.0), (2.5, 3.6)], "x", -2.0, 2.2, "M_SG_Rubble")
    for k in range(40):
        y = rnd.uniform(-7.5, -2.6)
        z = max(0.0, 3.1 * (y + 8.0) / 5.45 - 0.2) + rnd.uniform(0, 0.15)
        with mb.at(rnd.uniform(-2.6, 2.8), y, z, rz=rnd.uniform(0, 90), rx=rnd.uniform(-20, 20)):
            s_ = rnd.uniform(0.25, 0.6)
            mb.box(-s_, -s_ * 0.6, 0, s_, s_ * 0.6, s_ * 0.7, "M_Wall_Stone" if k % 3 else "M_Stone_Base")
    for k in range(12):
        y = rnd.uniform(2.7, 5.6)
        z = max(0.0, 3.6 * (6.0 - y) / 3.5 - 0.2)
        with mb.at(rnd.uniform(-2.0, 2.2), y, z, rz=rnd.uniform(0, 90)):
            s_ = rnd.uniform(0.25, 0.5)
            mb.box(-s_, -s_ * 0.6, 0, s_, s_ * 0.6, s_ * 0.7, "M_Wall_Stone")
    obj(mb, "Rubble", uv=2.0)
    c = K.MB()
    c.prism([(-2.4, 0.0), (-8.0, 0.0), (-2.5, 3.2)], "x", -2.3, 2.5, "M_SG_Rubble")
    c.prism([(2.4, 0.0), (6.0, 0.0), (2.4, 3.6)], "x", -2.0, 2.2, "M_SG_Rubble")
    obj(c, "COL_Rubble", uv=2.0)
    mb = K.MB()

    def face_y(zv):                                                               # 外立面收分：z → y
        return -2.5 + 0.4 * (zv + 0.5) / 7.5 - 0.02
    for k in range(9):
        x = rnd.uniform(-3.8, 3.4)
        z0 = rnd.uniform(1.0, 5.6)
        w_ = rnd.uniform(0.6, 1.4)
        h_ = rnd.uniform(0.8, 1.8)
        pts = [(x, z0), (x + w_, z0 + 0.1), (x + w_ * 0.8, z0 + h_), (x + w_ * 0.2, z0 + h_ * 0.8)]
        b = mb.addv([(px, face_y(pz), pz) for px, pz in pts] + [(px, face_y(pz) - 0.01, pz) for px, pz in pts])
        mb.face([b + 3, b + 2, b + 1, b + 0], "M_SG_Scorch")
        mb.face([b + 4, b + 5, b + 6, b + 7], "M_SG_Scorch")
    for k in range(6):                                                            # 走道 + 垛墙内侧焦痕
        x = rnd.uniform(-3.6, 3.0)
        y = rnd.uniform(-1.4, 2.0)
        mb.prism([(x, y), (x + 0.9, y + 0.1), (x + 0.7, y + 0.8), (x - 0.1, y + 0.6)], "z", WALK + 0.005, WALK + 0.015, "M_SG_Scorch")
    for k in range(3):
        x = rnd.uniform(-3.6, 3.0)
        mb.box(x, -1.51, 7.2, x + 0.9, -1.49, 7.85, "M_SG_Scorch")
    obj(mb, "Scorch", uv=2.0)
    mb = K.MB()
    for k in range(6):
        with mb.at(rnd.uniform(-3.5, 3.5), rnd.uniform(-0.8, 2.0), WALK + 0.12, rz=rnd.uniform(0, 180), ry=rnd.uniform(-8, 8)):
            mb.box(-1.2, -0.1, -0.1, 1.2, 0.1, 0.1, "M_SG_Char")
            mb.box(0.6, -0.11, -0.11, 1.0, 0.11, 0.11, "M_SG_Ember")
    obj(mb, "Burning_Debris", uv=1.0)
    for i, p in enumerate(((-3.0, 0.5, WALK + 0.2), (2.8, 1.2, WALK + 0.2), (0.3, -2.0, 3.4))):
        empty(f"FX_Fire_{i + 1}", p, size=0.4)
    empty("FX_Smoke", (0, 0.5, 8.5), size=0.6)
    empty("FX_Dust", (0.1, -3.0, 2.0), size=0.6)
    empty("ANCHOR_BreachTop", (0.1, -1.0, 3.3))
    empty("ANCHOR_RubbleFoot", (0.1, -7.5, 0))


def _recipes_siege():
    return {
        "PROP_SiegeLadder": ("Props", build_siege_ladder),
        "PROP_BatteringRam": ("Props", build_battering_ram),
        "PROP_FireShip": ("Props", build_fire_ship),
        "PROP_Cannon_Ming": ("Props", build_cannon),
        "PROP_CannonEmplacement": ("Props", build_cannon_emplacement),
        "PROP_WaterWheel": ("Props", build_water_wheel),
        "PROP_GateBar": ("Props", build_gate_bar),
        "PROP_Chevaux": ("Props", build_chevaux),
        "PROP_FireOil": ("Props", build_fire_oil),
        "PROP_BucketSand": ("Props", build_bucket_sand),
        "PROP_Stretcher": ("Props", build_stretcher),
        "ENV_WallBreach": ("Environments", build_wall_breach),
    }


# ================================================================ 第一批注册（敌人 + 武器）
def _recipes_enemy():
    R = {}
    for n in EN_CAST:
        R[n] = ("Enemies", (lambda nm=n: build_enemy(nm)))
    R["PROP_EN_Katana"] = ("Props", build_katana)
    R["PROP_EN_Bow"] = ("Props", build_bow)
    R["PROP_EN_Arrow"] = ("Props", build_arrow)
    R["PROP_EN_FirePot"] = ("Props", build_firepot)
    R["PROP_EN_Shield"] = ("Props", build_shield)
    R["PROP_BS_Chiyan_Axe"] = ("Props", build_chiyan_axe)
    R["PROP_BS_Guiwo_Tachi"] = ("Props", lambda: build_katana("PROP_BS_Guiwo_Tachi", L=0.8, handle=0.28, w=0.032, sori=0.035,
                                                              guard="M_BS_GW_Gold", steel="M_BS_Steel", wrap="M_BS_GW_Lace",
                                                              gold="M_BS_GW_Gold"))
    R["PROP_BS_Guiwo_Nodachi"] = ("Props", lambda: build_katana("PROP_BS_Guiwo_Nodachi", L=1.25, handle=0.42, w=0.042,
                                                                sori=0.05, guard="M_BS_Iron", steel="M_BS_Steel",
                                                                wrap="M_BS_GW_Lace"))
    R["PROP_BS_Guiwo_Naginata"] = ("Props", build_guiwo_naginata)
    return R


def recipes():
    R = {}
    R.update(_recipes_enemy())
    for n in BS_CAST:
        R[n] = ("Bosses", (lambda nm=n: build_boss(nm)))
    R.update(_recipes_anim())
    R.update(_recipes_siege())
    return R

