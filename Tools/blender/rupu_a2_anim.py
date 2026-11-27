"""
《入谱》第二幕补缺口 · 动作 + 手持道具
（Blender bpy，程序化；由 build_yongchang.py 统一生成/导出，recipes() 返回 {资产名: (分类, 生成函数)}）

对应 Docs/第二幕_策划对照与建模缺口.md §1/§4/§7（开工、王宅拆梁、殉难三选一、护民）；说明文档 Docs/act2_anim.md。

约定：
  - 动作资产 CH_WangYan_1941@A2_<动作>（Humanoid 共用），写法同 rupu_act2 的 A2_GESTURES：
    _pose(L/R=(前抬, 外张), LF/RF=屈肘, 骨骼=矩阵)、_legs(P, 大腿前抬, 小腿后屈, 脚)，第三项髋高偏移（m，按 1.75 m 人）。
    注册走 rupu_char.GESTURE_HOOKS，并套 rupu_act2._grounded 自动落地（逐关键帧量网格最低点，脚/膝/背刚好贴地）。
    每个关键帧都补全 Hips / 两手 / 两肩骨，避免某根骨只在部分帧有关键帧而「拖」到别的帧。
  - 手持道具沿用 rupu_enemy 的武器约定：原点 = 握点，本地 +Z = 虎口方向（杆/刃朝向），-Y = 指节方向；
    挂到人物手骨插槽 SOCKET_Hand_R / _L（或 A 自建的同朝向空物体）下，局部位置/旋转清零即可。
    放在地上的道具（饭篮）仍是原点在底面中心，另给 ANCHOR_Grip 握点。
  - 动画事件 FBX 带不进去（管线不支持），命中/点火等帧号写在 Docs/act2_anim.md，A 在 clip 导入设置里加。
  - 材质前缀 M_A2AN_*。
"""
import math

import bmesh
import bpy
from mathutils import Matrix, Vector

import rupu_kit as K
import rupu_char as C
import rupu_act2 as A2

K.PALETTE.update({
    "M_A2AN_Iron": "#4a4d4f", "M_A2AN_IronEdge": "#6a6d6e", "M_A2AN_Wood": "#6b5039", "M_A2AN_WoodDark": "#3e2f24",
    "M_A2AN_Match": "#a08a5a", "M_A2AN_Ember": "#C4552E", "M_A2AN_Bamboo": "#a8925e", "M_A2AN_BambooDark": "#7a6640",
    "M_A2AN_Cloth": "#4f5f5c", "M_A2AN_Bowl": "#d8d2c2", "M_A2AN_BowlBlue": "#4a5a6a", "M_A2AN_Rice": "#e8e2d2",
    "M_A2AN_Veg": "#6f7a52", "M_A2AN_Lantern": "#E8DCC8", "M_A2AN_LanternFace": "#E8DCC8", "M_A2AN_LanternRib": "#6b5039",
    "M_A2AN_LanternCap": "#3e2f24", "M_A2AN_Tassel": "#8a3a30", "M_A2AN_Cord": "#5a4636",
})

# ====================================================================== 动作
_X = lambda a: C._rot("X", a)
_Y = lambda a: C._rot("Y", a)
_Z = lambda a: C._rot("Z", a)
P_ = C._pose
LG = C._legs
I3 = Matrix.Identity(3)
FILL = ("Hips", "LeftHand", "RightHand", "LeftShoulder", "RightShoulder")

# ---------------------------------------------------------------- 正向运动学 + 手臂求解（只用 mathutils，不碰场景）
# 姿势里每根骨的矩阵 R 是骨架空间、相对父骨的旋转（rupu_char.set_rot 的约定），所以累计旋转 D = D_父 @ R。
_H = 1.75
_J = C.joints(_H)
_BL = C.bone_list(_J)
_HEAD = {n: _J[a] for n, a, b, p in _BL}
_PAR = {n: p for n, a, b, p in _BL}
_LT = (_J["hipL"] - _J["kneeL"]).length
_LS = (_J["kneeL"] - _J["ankleL"]).length


def fk(P, up=0.0):
    out = {}
    for n, a, b, p in _BL:
        R = P.get(n, I3)
        if p is None:
            out[n] = (_HEAD[n] + Vector((0, 0, up)), R.copy())
        else:
            pp, Dp = out[p]
            out[n] = (pp + Dp @ (_HEAD[n] - _HEAD[p]), Dp @ R)
    return out


def _grip_rest(s):
    sg = 1 if s == "L" else -1
    return _J["wrist" + s] + Vector((sg * 0.05 * _H, -0.004 * _H, -0.02 * _H))


def grip(P, s, F=None):
    """手部握点（= rupu_enemy 的 SOCKET_Hand_* 位置）与虎口方向（道具 +Z）。"""
    F = F or fk(P)
    hand = ("Left" if s == "L" else "Right") + "Hand"
    pos, D = F[hand]
    return pos + D @ (_grip_rest(s) - _HEAD[hand]), D @ Vector((0, -1, 0))


def at_bone(P, bone, off):
    pos, D = fk(P)[bone]
    return pos + D @ Vector(off)


REACH_LOG = []          # (手, 握点误差 m, 虎口与目标方向的余弦) 调试用
_LO = (-70, -70, 0, -90, -45)
_HI = (185, 110, 150, 90, 45)


def _arm_rots(sg, q):
    fwd, side, bend, tw, dev = q
    return C._arm(sg, fwd, side), C._fore(sg, bend) @ _X(tw), _Z(-sg * dev)


def reach(P, s, target, thumb=None, q0=(40, 10, 40, 0, 0), w=0.06):
    """把 s 手（'L'/'R'）的握点送到 target，虎口尽量朝 thumb；多起点坐标下降解 (前抬, 外张, 屈肘, 前臂旋, 腕偏)。原地改 P。"""
    side, sg = ("Left", 1) if s == "L" else ("Right", -1)
    t = Vector(target)
    d = Vector(thumb).normalized() if thumb is not None else None
    F = fk(P)
    sh = side + "Shoulder"
    p_sh, D_sh = F[sh]
    ua, la, hd = side + "UpperArm", side + "LowerArm", side + "Hand"
    o_ua = _HEAD[ua] - _HEAD[sh]
    o_la = _HEAD[la] - _HEAD[ua]
    o_hd = _HEAD[hd] - _HEAD[la]
    o_g = _grip_rest(s) - _HEAD[hd]
    ym = Vector((0, -1, 0))

    def cost(q):
        Ra, Rf, Rh = _arm_rots(sg, q)
        D1 = D_sh @ Ra
        D2 = D1 @ Rf
        D3 = D2 @ Rh
        g = p_sh + D_sh @ o_ua + D1 @ o_la + D2 @ o_hd + D3 @ o_g
        c = (g - t).length_squared
        if d is not None:
            c += w * (1 - (D3 @ ym).dot(d))
        return c + 2e-8 * (q[3] ** 2 + q[4] ** 2)

    def descend(q, steps=(24, 12, 6, 3, 1.5, 0.75, 0.3)):
        q = list(q)
        best = cost(q)
        for step in steps:
            better = True
            while better:
                better = False
                for i in range(5):
                    for sgn in (1, -1):
                        qq = q[:]
                        qq[i] = min(_HI[i], max(_LO[i], qq[i] + sgn * step))
                        c = cost(qq)
                        if c < best - 1e-12:
                            best, q, better = c, qq, True
        return best, q
    # 多起点（坐标下降会卡在局部极小）：给定初值 + 一组典型臂位，粗搜后取最好的几个细化
    starts = [list(q0)] + [[f, sd, b, tw, 0] for f in (10, 60, 110, 160) for sd in (-30, 20, 70) for b in (30, 100)
                           for tw in (-50, 0, 50)]
    rough = sorted((descend(q, (24, 12)) for q in starts), key=lambda x: x[0])[:4]
    best, q = min((descend(q) for _, q in rough), key=lambda x: x[0])
    for n, R in zip((ua, la, hd), _arm_rots(sg, q)):
        P[n] = R
    g, th = grip(P, s)
    REACH_LOG.append((s, round((g - t).length, 3), round(th.dot(d), 2) if d is not None else None))
    return P


def wield(P, g, d, sep, q0r=(30, 10, 40, 0, 0), q0l=(60, -10, 40, 0, 0), front="L"):
    """双手持杆：后手（默认右手）握点 g，杆朝 d，前手在杆上 sep 米处；两手虎口都朝杆头。"""
    g, d = Vector(g), Vector(d).normalized()
    back = "R" if front == "L" else "L"
    reach(P, back, g, d, q0r if back == "R" else q0l)
    reach(P, front, g + d * sep, d, q0l if front == "L" else q0r)
    return P


def lunge(P, ft=26, fs=34, bt=-16, front="Left", toe=0.0):
    """弓步：前腿大腿前抬 ft、小腿后屈 fs；后腿大腿后摆 bt，小腿屈度自动求出让两踝同高；两脚放平（后脚可 toe 度踮起）。"""
    hf = _LT * math.cos(math.radians(ft)) + _LS * math.cos(math.radians(ft - fs))
    c = max(-1.0, min(1.0, (hf - _LT * math.cos(math.radians(bt))) / _LS))
    s = -math.degrees(math.acos(c))
    bs = max(0.0, bt - s)
    back = "Right" if front == "Left" else "Left"
    LG(P, ft, fs, ft - fs, front)
    LG(P, bt, bs, bt - bs + toe, back)
    return P


def crouch(P, t=20, s=36):
    """双脚平放下蹲。"""
    return LG(P, t, s, t - s)


# ---------------------------------------------------------------- 王叔杲拆梁
def g_pry_beam():
    """拆梁：双手举撬杠，爪头插进头顶前方的梁缝 → 往下猛压两下（第 24、38 帧发力）→ 第 44 帧梁落、撬杠一空 →
    后退半步仰头看 → 双手把撬杠斜握在身前站定。"""
    D0 = (0, -0.8, 0.6)

    def lever(f, hz, hy, sp, kn, ch=-6, hd=-18):
        P = P_(Spine=_X(sp), Chest=_X(ch), Head=_X(hd))
        lunge(P, kn, kn * 1.6, -10)
        wield(P, (-0.1, hy, hz), D0, 0.32, q0r=(90, 0, 70, 0, 0), q0l=(110, 0, 60, 0, 0))
        return (f, P, 0.0)
    P = P_(Head=_X(-4))
    wield(P, (-0.18, -0.14, 0.95), (0.3, -0.42, 0.86), 0.34)
    keys = [(0, P, 0.0)]                                           # 起止都是双手斜握撬杠
    P = P_(Spine=_X(-2), Head=_X(-8))
    wield(P, (-0.1, -0.22, 1.3), (0.05, -0.5, 0.86), 0.32, q0r=(90, 0, 60, 0, 0), q0l=(110, 0, 50, 0, 0))
    keys.append((8, P, 0.0))
    keys += [lever(16, 1.42, -0.32, 0, 6),
             lever(24, 1.32, -0.4, 10, 20, ch=2, hd=-12),          # 第一下
             lever(31, 1.4, -0.33, 0, 8),
             lever(38, 1.22, -0.42, 16, 28, ch=4, hd=-10),         # 第二下
             lever(44, 1.1, -0.42, 22, 32, ch=6, hd=-6)]           # 梁落（撬杠一空）
    P = P_(Spine=_X(-10), Chest=_X(-4), Head=_X(-22))
    LG(LG(P, 6, 8, -2, "Left"), -22, 4, -18, "Right")
    wield(P, (-0.16, -0.12, 1.08), (0.15, -0.6, 0.78), 0.34)
    keys.append((52, P, 0.0))                                      # 退半步，仰头看
    P = P_(Spine=_X(-4), Head=_X(-10))
    LG(LG(P, 3, 4, -1, "Left"), -12, 2, -10, "Right")
    wield(P, (-0.18, -0.14, 0.98), (0.3, -0.42, 0.86), 0.34)
    keys.append((60, P, 0.0))
    P = P_(Head=_X(-4))
    wield(P, (-0.18, -0.14, 0.95), (0.3, -0.42, 0.86), 0.34)
    keys.append((72, P, 0.0))
    return 72, keys


# ---------------------------------------------------------------- 王沛
def g_look_out_loop():
    """北门看船：右手搭凉棚遮在眉上远眺，左手扶住身侧立着的枪；重心左右慢慢换，头微微扫（循环 96 帧）。"""
    def k(f, side, neck, sway):
        P = P_(Head=_X(-6), Neck=_Z(neck), Spine=_Z(sway), Chest=_X(-2))
        o = "Right" if side == "Left" else "Left"
        LG(P, 6, 12, -6, side)
        LG(P, -1, 0, 1, o)
        brow = at_bone(P, "Head", (-0.03, -0.13, 0.11))
        reach(P, "R", brow, at_bone(P, "Head", (0, 1, 0)) - at_bone(P, "Head", (0, 0, 0)), q0=(110, 50, 120, 0, 0), w=0.02)
        reach(P, "L", (0.3, -0.1, 1.0), (0, 0, 1), q0=(20, 14, 70, 0, 0))
        return (f, P, 0.0)
    return 96, [k(0, "Left", 6, 2), k(24, "Left", 0, 1), k(48, "Right", -6, -2), k(72, "Right", 0, -1), k(96, "Left", 6, 2)]


def g_fire_cannon():
    """试炮：右手火绳杆探向左前方炮尾火门（第 16 帧点火）→ 侧身扭开、左手捂耳缩肩 → 第 30 帧炮响、人一震 →
    回头看炮，站直（停在立杆站姿）。站位：炮尾火门在人物脚底原点的左 0.5 m、前 1.0 m、高 0.87 m（PROP_Cannon_Ming 的 FX_Fuse 高度）。"""
    HOLE = Vector((0.5, -1.0, 0.87))
    L_TIP = 1.085

    def hold(P, g=(-0.26, -0.1, 0.95)):
        return reach(P, "R", g, (0.0, -0.15, 1.0), q0=(20, 12, 60, 0, 0))

    def touch(P, g):
        g = Vector(g)
        return reach(P, "R", g, HOLE - g, q0=(50, 0, 30, 0, 0), w=0.08)

    def duck(sp, hd):
        P = P_(Spine=_X(sp) @ _Z(-24), Chest=_X(6) @ _Z(-14), Neck=_Z(-26), Head=_X(hd), LeftShoulder=_Y(-10),
               RightShoulder=_Y(10))
        crouch(P, 16, 28)
        reach(P, "L", at_bone(P, "Head", (0.11, 0.0, 0.06)), None, q0=(40, 70, 140, 0, 0))
        reach(P, "R", (-0.36, 0.06, 1.0), (-0.2, 0.3, 1.0), q0=(10, 20, 50, 0, 0))
        return P
    keys = [(0, hold(P_(Head=_X(-2))), 0.0)]
    P = lunge(P_(L=(20, 20), LF=30, Spine=_X(12) @ _Z(10), Chest=_Z(6), Head=_X(16), Neck=_Z(10)), 22, 34, -14)
    g10 = HOLE - Vector((0.62, -0.75, -0.12)).normalized() * (L_TIP + 0.08)
    keys.append((10, touch(P, g10), 0.0))
    P = lunge(P_(L=(20, 20), LF=30, Spine=_X(18) @ _Z(12), Chest=_Z(6), Head=_X(20), Neck=_Z(10)), 24, 38, -16)
    g16 = HOLE - Vector((0.62, -0.75, -0.22)).normalized() * L_TIP
    keys.append((16, touch(P, g16), 0.0))                     # 点火
    keys.append((24, duck(14, 14), 0.0))
    keys.append((30, duck(20, 20), 0.0))                      # 炮响
    P = P_(Spine=_X(2) @ _Z(-20), Chest=_X(-6) @ _Z(-12), Neck=_Z(-24), Head=_X(-12), LeftShoulder=_Y(-12),
           RightShoulder=_Y(12))
    crouch(P, 8, 14)
    reach(P, "L", at_bone(P, "Head", (0.11, 0.0, 0.06)), None, q0=(40, 70, 140, 0, 0))
    reach(P, "R", (-0.38, 0.1, 1.04), (-0.25, 0.35, 1.0), q0=(10, 20, 50, 0, 0))
    keys.append((33, P, 0.0))                                 # 震一下（后仰）
    keys.append((40, duck(16, 16), 0.0))
    P = P_(L=(10, 8), LF=20, Neck=_Z(16), Head=_X(-2), Spine=_Z(6))
    keys.append((52, hold(P), 0.0))                           # 回头看炮
    keys.append((64, hold(P_(Chest=_X(-3), Head=_X(-2))), 0.0))
    return 64, keys


# 王沛枪术：左脚在前、身体右转 30°（左肩朝前），右手在后（右胯）、左手在前，两手虎口朝枪头；枪尖朝前、略高过腰。
SPEAR_D = (0.12, -1.0, 0.2)


def _guard(g=(-0.22, 0.04, 0.9), d=SPEAR_D, sep=0.58, st=(24, 36, -16), **kw):
    a = dict(Hips=_Z(-30), Neck=_Z(14), Head=_X(-2) @ _Z(10), Chest=_X(-2))
    a.update(kw)
    P = P_(**a)
    lunge(P, *st)
    return wield(P, g, d, sep, q0r=(10, 10, 40, 0, 0), q0l=(60, -10, 40, 0, 0))


def g_spear_idle_loop():
    """持枪戒备：弓步、枪平端，胸口一起一伏，枪尖轻晃（循环 48 帧）。"""
    return 48, [(0, _guard(), 0.0),
                (12, _guard(g=(-0.22, 0.04, 0.91), d=(0.13, -1, 0.22), Chest=_X(-3)), 0.0),
                (24, _guard(g=(-0.22, 0.05, 0.89), d=(0.1, -1, 0.18), Chest=_X(-1)), 0.0),
                (36, _guard(g=(-0.22, 0.04, 0.91), d=(0.11, -1, 0.21), Chest=_X(-3)), 0.0),
                (48, _guard(), 0.0)]


def g_spear_thrust():
    """直刺：回抽蓄力（第 6 帧）→ 弓步送出，后手推到前手边（第 12 帧命中）→ 收回戒备。"""
    return 30, [(0, _guard(), 0.0),
                (6, _guard(g=(-0.27, 0.14, 0.9), d=(0.14, -1, 0.18), sep=0.62, Spine=_X(-4), st=(20, 32, -14)), 0.0),
                (12, _guard(g=(-0.13, -0.36, 1.0), d=(0.06, -1, 0.06), sep=0.3, Spine=_X(14), Hips=_Z(-38),
                            Head=_X(-8) @ _Z(12), st=(40, 58, -30)), 0.0),
                (16, _guard(g=(-0.14, -0.33, 1.0), d=(0.06, -1, 0.06), sep=0.3, Spine=_X(12), Hips=_Z(-36),
                            Head=_X(-6) @ _Z(12), st=(38, 56, -28)), 0.0),
                (30, _guard(), 0.0)]


def g_spear_sweep():
    """横扫：身子右拧、枪头甩到右前（第 8 帧）→ 向左横扫一大圈（第 15 帧命中）→ 收势戒备。"""
    return 36, [(0, _guard(), 0.0),
                (8, _guard(g=(-0.26, 0.0, 1.0), d=(-0.6, -0.8, 0.12), sep=0.36, Spine=_Z(-28), Chest=_Z(-14),
                           Head=_Z(26)), 0.0),
                (15, _guard(g=(-0.02, -0.22, 1.02), d=(0.8, -0.6, 0.04), sep=0.5, Spine=_X(8) @ _Z(26), Chest=_Z(12),
                            Head=_Z(-4), st=(32, 48, -22)), 0.0),
                (20, _guard(g=(0.04, -0.2, 1.02), d=(0.95, -0.3, 0.04), sep=0.4, Spine=_X(8) @ _Z(32), Chest=_Z(14),
                            Head=_Z(-10), st=(32, 48, -22)), 0.0),
                (36, _guard(), 0.0)]


def g_spear_parry():
    """格挡：双手把枪杆横举到额前上方（第 5 帧架住）→ 顶一下 → 落回戒备。"""
    blk = dict(d=(1, 0.05, 0.08), sep=0.6, Spine=_X(-4), Head=_X(2) @ _Z(8), st=(22, 40, -18))
    return 24, [(0, _guard(), 0.0),
                (5, _guard(g=(-0.32, -0.3, 1.62), **blk), 0.0),
                (10, _guard(g=(-0.32, -0.32, 1.68), **blk), 0.0),
                (24, _guard(), 0.0)]


def g_spear_hit():
    """受击：胸口挨一下，上身后仰、枪尖挑起，前脚收半步（第 3 帧）→ 回戒备。"""
    return 20, [(0, _guard(), 0.0),
                (3, _guard(g=(-0.24, 0.12, 0.95), d=(0.1, -0.8, 0.6), sep=0.5, Spine=_X(-14), Chest=_X(-8),
                           Head=_X(-12) @ _Z(10), st=(12, 20, -10)), 0.0),
                (8, _guard(g=(-0.23, 0.08, 0.93), d=(0.1, -0.9, 0.4), sep=0.55, Spine=_X(-8), Chest=_X(-6),
                           Head=_X(-6) @ _Z(10), st=(16, 26, -12)), 0.0),
                (20, _guard(), 0.0)]


# ---------------------------------------------------------------- 王德 / 义师短刀（右手，刃朝虎口方向）
def _knife(P, g, d, q0=(60, 10, 60, 0, 0)):
    return reach(P, "R", g, d, q0=q0, w=0.08)


def g_militia_charge():
    """举刀冲锋起手：右手短刀高举、左手前指，压低身子，前脚一蹬（第 16 帧，接 Run）。"""
    def k(f, g, d, lf, sp, hd, st):
        P = P_(L=lf[0], LF=lf[1], Spine=_X(sp), Head=_X(hd))
        lunge(P, *st)
        return (f, _knife(P, g, d, q0=(150, 30, 40, 0, 0)), 0.0)
    return 28, [(0, C._base(), 0.0),
                k(8, (-0.32, -0.02, 1.86), (-0.1, 0.35, 1), ((76, 14), 24), 6, -12, (18, 28, -10)),
                k(16, (-0.3, -0.12, 1.84), (-0.05, 0.1, 1), ((84, 10), 14), 20, -22, (40, 54, -28)),
                k(28, (-0.3, -0.1, 1.84), (-0.05, 0.15, 1), ((80, 12), 18), 18, -20, (36, 50, -24))]


def g_militia_slash():
    """短刀劈砍：刀举到右肩上方（第 7 帧）→ 斜劈到左胯前（第 11 帧命中）→ 收回胸前。"""
    def k(f, g, d, l, sp, hd, st, q0):
        P = P_(L=l[0], LF=l[1], Spine=sp, Head=hd)
        lunge(P, *st)
        return (f, _knife(P, g, d, q0), 0.0)
    G = ((-0.14, -0.36, 1.22), (0.05, -0.7, 0.7))
    guard = lambda f: k(f, *G, ((40, 18), 40), _X(6), _X(-4), (18, 28, -10), (60, 10, 70, 0, 0))
    return 26, [guard(0),
                k(7, (-0.3, 0.0, 1.72), (0.1, 0.65, 0.75), ((54, 4), 36), _X(-2) @ _Z(-18), _X(-6) @ _Z(10),
                  (18, 28, -10), (140, 40, 100, 0, 0)),
                k(11, (0.1, -0.46, 0.98), (0.55, -0.55, -0.62), ((26, 30), 30), _X(18) @ _Z(20), _X(-10) @ _Z(-10),
                  (34, 50, -22), (55, -30, 15, 0, 0)),
                k(15, (0.18, -0.36, 0.86), (0.6, -0.3, -0.74), ((24, 30), 30), _X(20) @ _Z(24), _X(-8) @ _Z(-12),
                  (34, 50, -22), (40, -35, 20, 0, 0)),
                guard(26)]


# ---------------------------------------------------------------- 护民撤祠堂
def g_guide_crowd_loop():
    """引路：右手指向前方（祠堂），身子半侧、回头看后面的人群，左手一下一下往前招（循环 32 帧）。"""
    def k(f, l, lf, bob):
        P = P_(R=(84, 22), RF=10, L=l, LF=lf, Spine=_Z(26), Chest=_Z(12), Neck=_Z(26), Head=_X(-4))
        LG(P, 6 + bob, 12 + bob * 2, -6 - bob, "Left")
        LG(P, -6, 4, -10, "Right")
        return (f, P, 0.0)
    return 32, [k(0, (34, 76), 40, 0), k(10, (104, 44), 92, 3), k(16, (66, -4), 70, 2), k(26, (64, 58), 48, 0),
                k(32, (34, 76), 40, 0)]


def _reverse(T, keys):
    return T, sorted([(T - f, P, u) for f, P, u in keys], key=lambda x: x[0])


def g_shield_civilian_loop():
    """护民：面朝来敌、两臂向后张开把人挡在身后，一边原地倒退（循环 32 帧；团结里根节点按每循环约 0.7 m 后移）。"""
    up = lambda t: dict(L=(-14, 66), LF=24, R=(-14, 66), RF=24, Spine=_X(6), Chest=_X(-2), Head=_X(-6))
    return _reverse(*A2._step_cycle(32, up, -0.04, 20))


def g_flee_loop():
    """平民护头小跑：弯腰缩脖、双臂抱头，原地小跑（循环 16 帧）。"""
    up = lambda t: dict(L=(120, 40), LF=130, R=(120, 40), RF=130, Spine=_X(24), Chest=_X(8), Head=_X(16), Neck=_X(6))
    T, keys = A2._step_cycle(16, up, -0.06, 30)
    for f, P, u in keys:                                       # 两手捂住后脑两侧
        for s, x in (("L", 0.07), ("R", -0.07)):
            reach(P, s, at_bone(P, "Head", (x, 0.04, 0.13)), None, q0=(120, 40, 130, 0, 0))
    return T, keys


def g_carry_child_run_loop():
    """抱孩子小跑：双臂把孩子搂在胸前、身子前倾护着，原地小跑（循环 16 帧；孩子另摆，贴胸口）。"""
    up = lambda t: dict(L=(44, -26), LF=104, R=(36, -20), RF=96, Spine=_X(16), Chest=_X(-4), Head=_X(6))
    return A2._step_cycle(16, up, -0.05, 28)


# ---------------------------------------------------------------- 殉难遗体 / 族老
def g_corpse_lie():
    """王沛遗体：仰卧，头偏向右侧，两臂摊开，右膝微屈（静态，4 帧同一姿势）。枪另放在右手边地上。"""
    P = P_(Hips=_X(-86), Spine=_X(4), Chest=_X(2), Neck=_Z(-26), Head=_X(-8), L=(-4, 48), LF=14, R=(-4, 30), RF=26)
    LG(P, 0, 4, 10, "Left")
    LG(P, 18, 30, 6, "Right")
    return 4, [(0, P, 0.0), (4, P, 0.0)]


def g_elder_object():
    """族老反对：右手收到胸前一拂袖甩开（第 14 帧）→ 下巴一抬、向右后转约 175° → 双手背到身后站定（停在末帧）。"""
    behind = dict(L=(-24, -16), LF=72, R=(-24, -16), RF=72)
    return 48, [(0, C._base(), 0.0),
                (8, P_(R=(62, -36), RF=84, Spine=_Z(10), Neck=_Z(-8), Head=_X(4)), 0.0),
                (14, P_(R=(46, 66), RF=10, L=(10, 10), LF=20, Spine=_Z(-14), Chest=_X(-4), Head=_X(-10)), 0.0),
                (22, LG(P_(Hips=_Z(-90), R=(22, 34), RF=18, L=(14, 12), LF=24, Chest=_X(-3), Head=_X(-8)), 24, 46, -22, "Right"),
                 0.0),
                (32, P_(Hips=_Z(-175), R=(4, 6), RF=30, L=(4, 6), LF=30, Chest=_X(-4), Head=_X(-8)), 0.0),
                (48, P_(Hips=_Z(-175), **behind, Chest=_X(-5), Head=_X(-8)), 0.0)]


A2_ANIM = {
    "A2_PryBeam": g_pry_beam,
    "A2_LookOutLoop": g_look_out_loop,
    "A2_FireCannon": g_fire_cannon,
    "A2_SpearIdleLoop": g_spear_idle_loop, "A2_SpearThrust": g_spear_thrust, "A2_SpearSweep": g_spear_sweep,
    "A2_SpearParry": g_spear_parry, "A2_SpearHit": g_spear_hit,
    "A2_MilitiaCharge": g_militia_charge, "A2_MilitiaSlash": g_militia_slash,
    "A2_GuideCrowdLoop": g_guide_crowd_loop, "A2_ShieldCivilianLoop": g_shield_civilian_loop,
    "A2_FleeLoop": g_flee_loop, "A2_CarryChildRunLoop": g_carry_child_run_loop,
    "A2_CorpseLie": g_corpse_lie, "A2_ElderObject": g_elder_object,
}

# 事件帧（24 fps 原帧号；管线写不进 FBX，A 在团结 clip 导入设置里加。AttackHit/Stagger/Footstep 是 CLAUDE.md 约定名，其余是建议名）
A2_EVENTS = {
    "A2_PryBeam": [("PryEffort", 24), ("PryEffort", 38), ("BeamFall", 44)],
    "A2_FireCannon": [("Ignite", 16), ("AttackHit", 30)],
    "A2_SpearThrust": [("AttackHit", 12)], "A2_SpearSweep": [("AttackHit", 15)],
    "A2_SpearParry": [("Parry", 5)], "A2_SpearHit": [("Stagger", 3)],
    "A2_MilitiaCharge": [("Footstep", 16)], "A2_MilitiaSlash": [("AttackHit", 11)],
    "A2_ElderObject": [("Sleeve", 14)],
}


def _filled(fn):
    def wrapped():
        total, keys = fn()
        out = []
        for f, P, up in keys:
            P = dict(P)
            for b in FILL:
                P.setdefault(b, I3)
            out.append((f, P, up))
        return total, out
    return wrapped


C.GESTURE_HOOKS.update({k: A2._grounded(_filled(v)) for k, v in A2_ANIM.items()})

# ====================================================================== 道具
obj = A2.obj
tb, el, bx, anchor = A2.tb, A2.el, A2.bx, A2.anchor


def build_pry_bar():
    """撬杠：1.25 m 八棱铁杆，上端扁头弯成羊角起钉爪（朝 -Y），下端扁錾口。原点 = 后手握点（离尾端 0.15 m），+Z 朝爪。"""
    mb = K.MB()
    mb.cyl(0, 0, -0.15, 1.0, 0.015, "M_A2AN_Iron", seg=8)
    mb.cyl(0, 0, -0.06, 0.12, 0.018, "M_A2AN_WoodDark", seg=8)               # 缠麻握把
    mb.prism([(-0.015, -0.15), (0.015, -0.15), (0.004, -0.21), (-0.004, -0.21)], "y", -0.012, 0.012, "M_A2AN_IronEdge")
    with mb.at(0, 0, 1.0, rx=-35):                                           # 弯头
        mb.cyl(0, 0, 0, 0.1, 0.015, "M_A2AN_Iron", seg=8, r_top=0.013)
        with mb.at(0, 0, 0.1, rx=-40):
            for sx in (-1, 1):                                               # 分叉爪
                mb.prism([(sx * 0.003, 0.0), (sx * 0.018, 0.0), (sx * 0.012, 0.09), (sx * 0.006, 0.09)], "y",
                         -0.008, 0.008, "M_A2AN_IronEdge")
    obj(mb, "PryBar", uv=0.3)
    anchor("FX_Tip", (0, -0.13, 1.16), 0.04, kind="SPHERE")


def build_linstock():
    """火绳杆：1.2 m 木杆，杆头铁叉夹着点着的火绳，余绳在杆上缠几圈。原点 = 握点，+Z 朝杆头；FX_Match 是火绳头（火星/烟）。"""
    mb = K.MB()
    mb.cyl(0, 0, -0.35, 0.85, 0.016, "M_A2AN_Wood", seg=8, r_top=0.014)
    mb.cyl(0, 0, -0.38, -0.35, 0.02, "M_A2AN_Iron", seg=8)                    # 杆尾铁箍
    mb.cyl(0, 0, 0.83, 0.9, 0.02, "M_A2AN_Iron", seg=8)                      # 銎
    for sx in (-1, 1):                                                       # 双股叉，弯向前
        A2.tb(mb, (sx * 0.012, 0, 0.9), (sx * 0.03, -0.02, 0.98), 0.006, "M_A2AN_Iron", seg=4)
        A2.tb(mb, (sx * 0.03, -0.02, 0.98), (sx * 0.02, -0.05, 1.03), 0.006, "M_A2AN_Iron", seg=4)
    pts = []
    for i in range(25):                                                      # 缠在杆上的火绳（螺旋）
        a = i * 0.9
        pts.append((0.022 * math.cos(a), 0.022 * math.sin(a), 0.45 + i * 0.014))
    pts += [(0.03, -0.02, 0.86), (0.028, -0.025, 0.96), (0.0, -0.05, 1.02), (-0.01, -0.07, 1.06)]
    for a, b in zip(pts, pts[1:]):
        A2.tb(mb, a, b, 0.006, "M_A2AN_Match", seg=4)
    A2.tb(mb, (-0.01, -0.07, 1.06), (-0.013, -0.08, 1.085), 0.008, "M_A2AN_Ember", seg=4)
    obj(mb, "Linstock", uv=0.3)
    anchor("FX_Match", (-0.013, -0.08, 1.085), 0.04, kind="SPHERE")


def _ring(mb, r, z, t, mat, seg=12, h=0.012):
    mb.cyl(0, 0, z, z + h, r + t, mat, seg=seg)


def build_food_basket():
    """送饭竹提篮：圆篮身（竹篾编纹两色）、提梁、半掀的蓝灰盖布，露出一碗饭；布下还压一碗菜和一双筷子。
    原点 = 篮底中心；ANCHOR_Grip = 提梁顶握点（挂手：握点对齐 SOCKET_Hand_*，篮子自然垂下）。"""
    mb = K.MB()
    R0, R1, Hh = 0.15, 0.18, 0.17
    n = 6
    for i in range(n):                                                       # 篮身：一圈圈篾片，交替深浅
        z0, z1 = Hh * i / n, Hh * (i + 1) / n
        r0, r1 = R0 + (R1 - R0) * i / n, R0 + (R1 - R0) * (i + 1) / n
        mb.cyl(0, 0, z0, z1, r0, "M_A2AN_Bamboo" if i % 2 else "M_A2AN_BambooDark", seg=14, r_top=r1)
    mb.cyl(0, 0, Hh, Hh + 0.012, R1 + 0.012, "M_A2AN_BambooDark", seg=14)    # 口沿（顶面当篮里的垫布/饭菜底）
    mb.cyl(0, 0, -0.0, 0.015, R0 + 0.01, "M_A2AN_BambooDark", seg=14)        # 底圈
    pts = []
    for i in range(11):                                                      # 提梁：沿 X 的拱
        a = math.pi * i / 10
        pts.append((R1 * math.cos(a), 0, Hh + 0.01 + 0.2 * math.sin(a)))
    for a, b in zip(pts, pts[1:]):
        tb(mb, a, b, 0.011, "M_A2AN_BambooDark", seg=5)
    obj(mb, "Basket", uv=0.2)

    bw = K.MB()                                                              # 露出来的一碗饭（青花碗）
    bw.cyl(0, 0, 0, 0.01, 0.03, "M_A2AN_Bowl", seg=10, r_top=0.03)
    bw.cyl(0, 0, 0.01, 0.055, 0.035, "M_A2AN_BowlBlue", seg=10, r_top=0.06)
    el(bw, (0, 0, 0.05), 0.055, 0.055, 0.03, "M_A2AN_Rice", seg=10, rings=3, zmin=0.0)
    obj(bw, "Bowl_1", (0.06, -0.07, Hh + 0.012), uv=0.2)
    b2 = K.MB()                                                              # 布下一碗菜
    b2.cyl(0, 0, 0, 0.01, 0.03, "M_A2AN_Bowl", seg=10)
    b2.cyl(0, 0, 0.01, 0.05, 0.035, "M_A2AN_Bowl", seg=10, r_top=0.058)
    el(b2, (0, 0, 0.045), 0.05, 0.05, 0.018, "M_A2AN_Veg", seg=10, rings=3, zmin=0.0)
    tb(b2, (-0.06, 0.03, 0.05), (0.07, -0.02, 0.05), 0.004, "M_A2AN_WoodDark", seg=4)
    tb(b2, (-0.06, 0.04, 0.052), (0.07, -0.01, 0.052), 0.004, "M_A2AN_WoodDark", seg=4)
    obj(b2, "Bowl_2", (-0.04, 0.07, Hh + 0.012), uv=0.2)

    cl = K.MB()                                                              # 盖布：盖住后半个篮口，前缘直边，四边搭出口沿下垂
    N = 6
    grid = []
    for j in range(N + 1):
        row = []
        for i in range(N + 1):
            x = -0.25 + 0.5 * i / N
            y = -0.03 + 0.28 * j / N
            r = math.hypot(x, y)
            if r <= R1:
                z = Hh + 0.1 - 0.06 * (r / R1) ** 2
            else:
                z = max(Hh * 0.55, Hh + 0.025 - (r - R1) * 1.4)
                k = (R1 + 0.012) / r                                         # 垂下的部分贴着篮外壁
                x, y = x * k, y * k
            row.append(cl.addv([(x, y, z)]))
        grid.append(row)
    for j in range(N):
        for i in range(N):
            q = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
            cl.face(q, "M_A2AN_Cloth")
            cl.face(list(reversed(q)), "M_A2AN_Cloth")
    obj(cl, "Cloth", uv=0.3)
    anchor("ANCHOR_Grip", (0, 0, Hh + 0.21), 0.06)


def build_ming_lantern():
    """明代提灯：竹竿（原点 = 握点，+Z 朝竿头，竿头向前弯出一个挂钩）挂一盏竹骨纸灯笼。
    子物体：Lantern（枢轴 = 挂钩，团结里每帧把它的世界旋转扶正即可自然下垂）；
            Lantern/Lantern_Face（前面 -Y 一块贴字面片，UV 0–1 占满，用来贴「王」字等）；Lantern/FX_Glow（灯光）。"""
    mb = K.MB()
    mb.cyl(0, 0, -0.25, 0.62, 0.012, "M_A2AN_Bamboo", seg=6, r_top=0.01)
    for z in (-0.05, 0.22, 0.48):                                            # 竹节
        mb.cyl(0, 0, z, z + 0.012, 0.0135, "M_A2AN_BambooDark", seg=6)
    tb(mb, (0, 0, 0.62), (0, -0.12, 0.76), 0.01, "M_A2AN_Bamboo", seg=6)
    tb(mb, (0, -0.12, 0.76), (0, -0.2, 0.78), 0.009, "M_A2AN_Bamboo", seg=6)
    tb(mb, (0, -0.2, 0.78), (0, -0.21, 0.75), 0.004, "M_A2AN_Iron", seg=4)  # 铁钩
    pole = obj(mb, "Pole", uv=0.3)

    hook = Vector((0, -0.21, 0.75))
    lm = K.MB()                                                              # 灯笼（局部坐标，原点在挂钩）
    tb(lm, (0, 0, 0), (0, 0, -0.07), 0.003, "M_A2AN_Cord", seg=4)
    top, bot, Rm = -0.09, -0.41, 0.125
    lm.cyl(0, 0, top - 0.025, top, 0.06, "M_A2AN_LanternCap", seg=10)         # 上盖
    lm.cyl(0, 0, bot, bot + 0.025, 0.065, "M_A2AN_LanternCap", seg=10)        # 底托
    rings = []
    S = 12
    for k in range(7):                                                       # 纸面：鼓形
        t = k / 6
        z = top - (top - bot) * t
        r = 0.06 + (Rm - 0.06) * math.sin(math.pi * t) ** 0.6
        rings.append([(r * math.cos(2 * math.pi * i / S), r * math.sin(2 * math.pi * i / S), z) for i in range(S)])
    idx = [lm.addv(rg) for rg in rings]
    for a, b in zip(idx, idx[1:]):
        for i in range(S):
            j = (i + 1) % S
            lm.face([a + i, a + j, b + j, b + i], "M_A2AN_Lantern")
    for i in range(0, S, 2):                                                 # 竹骨（竖条）
        for a, b in zip(rings, rings[1:]):
            pa, pb = Vector(a[i]) * 1.03, Vector(b[i]) * 1.03
            pa.z, pb.z = a[i][2], b[i][2]
            tb(lm, pa, pb, 0.0028, "M_A2AN_LanternRib", seg=3)
    tb(lm, (0, 0, bot), (0, 0, bot - 0.12), 0.012, "M_A2AN_Tassel", seg=5, r1=0.022)   # 红穗
    lan = obj(lm, "Lantern", hook, uv=0.2)
    lan.parent = pole

    fm = bpy.data.meshes.new("Lantern_Face")                                 # 贴字面片：前面 ±50° 弧、上下 3 段
    bm = bmesh.new()
    uvl = bm.loops.layers.uv.new()
    NA, NZ = 6, 4
    vs = []
    for kz in range(NZ + 1):
        t = 0.15 + 0.7 * kz / NZ
        z = top - (top - bot) * t
        r = (0.06 + (Rm - 0.06) * math.sin(math.pi * t) ** 0.6) * 1.012
        row = []
        for ka in range(NA + 1):
            a = math.radians(-90 - 50 + 100 * ka / NA)                       # 以 -Y 为中心
            row.append(bm.verts.new((r * math.cos(a), r * math.sin(a), z)))
        vs.append(row)
    for kz in range(NZ):
        for ka in range(NA):
            f = bm.faces.new([vs[kz][ka], vs[kz + 1][ka], vs[kz + 1][ka + 1], vs[kz][ka + 1]])
            for l, (u, v) in zip(f.loops, [(ka, kz), (ka, kz + 1), (ka + 1, kz + 1), (ka + 1, kz)]):
                l[uvl].uv = (1 - u / NA, 1 - v / NZ)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    for f in bm.faces:                                                       # 法线朝外（-Y）
        c = f.calc_center_median()
        if f.normal.dot(Vector((c.x, c.y, 0))) < 0:
            f.normal_flip()
    bm.to_mesh(fm)
    bm.free()
    fm.materials.append(K.get_mat("M_A2AN_LanternFace"))
    face = bpy.data.objects.new("Lantern_Face", fm)
    bpy.context.scene.collection.objects.link(face)
    face.parent = lan
    g = anchor("FX_Glow", (0, 0, (top + bot) / 2), 0.05, kind="SPHERE")
    g.parent = lan


# ====================================================================== 注册
def recipes():
    R = {
        "PROP_PryBar": ("Props", build_pry_bar),
        "PROP_Linstock": ("Props", build_linstock),
        "PROP_FoodBasket": ("Props", build_food_basket),
        "PROP_MingLantern": ("Props", build_ming_lantern),
    }
    for k in A2_ANIM:
        R[f"CH_WangYan_1941@{k}"] = ("Characters", (lambda kk=k: C.build_gesture(kk)))
    return R
