"""
《入谱》第二幕 1560 筑堡 · 人物（族老、匠人、民夫、义师、妇人、孩童）、沙盘与筑堡道具、第二幕动作
（Blender bpy，程序化白模；由 build_yongchang.py 统一生成/导出，recipes() 返回 {资产名: (分类, 生成函数)}）

对应 Docs/入谱_当前建模缺口清单.md 3.3（人物）、3.4（核心道具）、3.6（动画部分）；文档见 Docs/act2_assets.md。

约定：
  - 人物用 rupu_char.build_character(name, cfg) + 本模块注册的钩子（前缀 a2_），22 骨 Humanoid，共用动画。
  - 道具正面朝 Blender -Y，原点在底面中心；会动/会切换的部件是固定名字的子物体；
    FX_* 空物体是特效挂点，ANCHOR_* 空物体是站位/镜头/插签点，COL_* 只做碰撞（沙盘热区）。
  - 动作资产 CH_WangYan_1941@A2<动作>（GESTURE_HOOKS），循环动作名带 Loop。
  - 材质前缀：人物 M_A2C_*，道具 M_A2_*。
"""
import math

import bpy
from mathutils import Vector

import rupu_kit as K
import rupu_char as C
import rupu_act1 as A1

# ====================================================================== 颜色
A2_PALETTE = {
    # ---- 人物（M_A2C_）
    "M_A2C_Collar": "#d8cdb5", "M_A2C_Black": "#1e1c1a", "M_A2C_NetCap": "#2a2826",
    # 族老
    "M_A2C_EA_Robe": "#6a5040", "M_A2C_EA_Sash": "#3a2e24",
    "M_A2C_EB_Robe": "#545440", "M_A2C_EB_Over": "#33322a", "M_A2C_EB_Cap": "#2b2a26",
    # 匠人
    "M_A2C_MS_Coat": "#7a7466", "M_A2C_MS_Pants": "#4a463e", "M_A2C_LeatherApron": "#5a4636", "M_A2C_Canvas": "#8a8270",
    "M_A2C_CP_Coat": "#6a5a44", "M_A2C_CP_Apron": "#a49a80", "M_A2C_Ink": "#141210",
    "M_A2C_RM_Coat": "#8a7a5a", "M_A2C_Towel": "#d6d0c0",
    "M_A2C_SM_Coat": "#3a3632", "M_A2C_SM_Apron": "#3e2a1e", "M_A2C_Iron": "#45484a",
    # 民夫
    "M_A2C_LB_Coat1": "#7a6a52", "M_A2C_LB_Coat2": "#5e5a4c", "M_A2C_LB_Coat3": "#6e6252", "M_A2C_LB_Coat4": "#4f5a56",
    "M_A2C_LB_Coat5": "#857560", "M_A2C_LB_Coat6": "#5a4e44",
    "M_A2C_LB_Pants1": "#4a4438", "M_A2C_LB_Pants2": "#3e3b34", "M_A2C_LB_Pants3": "#585044",
    "M_A2C_Patch": "#9a8e74", "M_A2C_Rope": "#a08a5a", "M_A2C_Cape": "#7a6a48", "M_A2C_Vest": "#4a4236",
    "M_A2C_Cloth_Grey": "#6e6a5c", "M_A2C_Cloth_Blue": "#46525c", "M_A2C_Cloth_Brown": "#5a4636",
    # 义师
    "M_A2C_ML_Coat": "#3e4a57", "M_A2C_ML_Coat2": "#4a4a42", "M_A2C_ML_Pants": "#3f3a33",
    "M_A2C_ML_Bujia_Red": "#6e3b32", "M_A2C_ML_Bujia_Blue": "#2e3a48", "M_A2C_ML_Paper": "#b8ad94",
    "M_A2C_ML_Paper2": "#9a9282", "M_A2C_ML_Lace": "#4a3a2a", "M_A2C_Stud": "#8f7a44", "M_A2C_Tassel": "#8a3a30",
    "M_A2C_Shield": "#8a7448", "M_A2C_Quiver": "#4e3a2a",
    # 妇人 / 孩童
    "M_A2C_WA_Ao": "#6a5a4e", "M_A2C_WA_Skirt": "#3a3a36", "M_A2C_WA_Bijia": "#4f5f5c", "M_A2C_WA_Scarf": "#8a8270",
    "M_A2C_WB_Ao": "#7a6a62", "M_A2C_WB_Skirt": "#2e2b2a", "M_A2C_WB_Bijia": "#5a3a34", "M_A2C_Pin": "#8f7a44",
    "M_A2C_CH_Coat": "#7a5a48", "M_A2C_CH_Pants": "#4a4438", "M_A2C_Silver": "#a8a49a",
    # ---- 道具（M_A2_）
    "M_A2_Sand": "#c8b58e", "M_A2_SandDark": "#9e8a66", "M_A2_SandRidge": "#b8a47c", "M_A2_Moss": "#6f7a52",
    "M_A2_Field": "#8a8a5c", "M_A2_MiniWater": "#4F6B6A", "M_A2_MiniWaterFlow": "#5f7f7c", "M_A2_MiniWaterLine": "#a9c0b8", "M_A2_HillMini": "#7a7a58",
    "M_A2_TableWood": "#6b4a32", "M_A2_TableDark": "#3e2c20", "M_A2_MiniWood": "#a08060", "M_A2_MiniWall": "#7c7466",
    "M_A2_MiniRoof": "#4a4a46", "M_A2_MiniIron": "#2e3030", "M_A2_Twine": "#b8a882", "M_A2_Rice": "#e8e2d2",
    "M_A2_FlagRed": "#9a3a2c", "M_A2_FlagBlue": "#3e5260", "M_A2_FlagYellow": "#b0924a", "M_A2_Grave": "#8a8678",
    "M_A2_Salt": "#dcd8cc", "M_A2_Paper": "#E8DCC8", "M_A2_PaperOld": "#cbbd9e", "M_A2_Ink": "#141210",
    "M_A2_SealRed": "#a8402e", "M_A2_Stone": "#8a877e", "M_A2_StoneDark": "#6a675f", "M_A2_StoneLight": "#a6a296",
    "M_A2_Carved": "#3a3833", "M_A2_Wood": "#6b5039", "M_A2_WoodDark": "#3e2f24", "M_A2_WoodLight": "#8a6e50",
    "M_A2_Fir": "#8a7454", "M_A2_Lashing": "#a08a5a", "M_A2_Rope": "#a8946a", "M_A2_Iron": "#4a4d4f",
    "M_A2_Bronze": "#6a5a3a", "M_A2_Mortar": "#c9c4b6", "M_A2_Lacquer": "#5a2a22", "M_A2_Silk": "#4a5560",
    "M_A2_Brass": "#8f7a44", "M_A2_Board": "#9a7a56",
}
K.PALETTE.update(A2_PALETTE)

V = Vector
W = C.W
box, tube, ellipsoid, rings_mesh, _eu = C.box, C.tube, C.ellipsoid, C.rings_mesh, C._eu


# ====================================================================== 人物：身体轮廓与小工具
# build_body 的躯干截面（z/h, rx, ry），叠穿（比甲、布甲、褙子）沿它外扩
_TORSO = [(0.42, 0.105, 0.074), (0.47, 0.094, 0.066), (0.56, 0.085, 0.060), (0.64, 0.093, 0.064), (0.72, 0.105, 0.066),
          (0.81, 0.112, 0.060)]


def _prof(zr, robe=False):
    """高度 z/h 处的身体（衣服外表面）半径 (rx, ry)，单位 h。"""
    pts = list(_TORSO)
    if robe:
        pts = [(0.075, 0.128, 0.088), (0.24, 0.12, 0.083), (0.40, 0.108, 0.075)] + pts[1:]
    else:
        pts = [(0.30, 0.112, 0.08)] + pts
    if zr <= pts[0][0]:
        return pts[0][1], pts[0][2]
    for (z0, a0, b0), (z1, a1, b1) in zip(pts, pts[1:]):
        if zr <= z1:
            t = (zr - z0) / (z1 - z0)
            return a0 + (a1 - a0) * t, b0 + (b1 - b0) * t
    return pts[-1][1], pts[-1][2]


def _wt(J, h):
    """叠穿用权重：腰以上跟躯干，腰以下跟腿（下摆）。"""
    tw = C.torso_weight(J)
    sw = C.skirt_weight(J, 0.53 * h)
    return lambda p: tw(p) if p.z > 0.53 * h else sw(p)


def _front(J, h, c, x, zr, out=0.004):
    """躯干前表面上 (x, z) 处的点（略浮出 out*h）。"""
    rx, ry = _prof(zr, c.get("outfit") == "robe")
    b = c.get("bulk", 1.0) * c.get("_shell", 1.0)
    rx, ry = rx * h * b, ry * h * b
    k = max(0.0, 1.0 - (x / rx) ** 2) if abs(x) < rx else 0.0
    return V((x, C.spine_y(J, zr * h) - ry * math.sqrt(k) - out * h, zr * h))


def _band(S, J, h, c, a, b, wd, mat, n=4, weights=None):
    """沿躯干前表面从 a=(x, z/h) 到 b 贴一条布带（交领、甲绦、斜挎带）。"""
    wts = weights or _wt(J, h)
    for i in range(n):
        t0, t1 = i / n, (i + 1) / n
        p0 = _front(J, h, c, a[0] + (b[0] - a[0]) * t0, a[1] + (b[1] - a[1]) * t0)
        p1 = _front(J, h, c, a[0] + (b[0] - a[0]) * t1, a[1] + (b[1] - a[1]) * t1)
        d = p1 - p0
        ang = math.degrees(math.atan2(d.x, d.z))
        S.add(*box((p0 + p1) / 2, (wd * h, 0.005 * h, d.length * 1.04), rot=_eu(0, ang, 0)), mat, wts)


def _shell(S, J, h, c, mat, z_top, z_bot, grow=1.07, flare=1.0, open_front=False):
    """叠穿外壳：从 z_top 到 z_bot（单位 h）的一圈，沿身体外扩 grow；flare 让下摆再张开。"""
    robe = c.get("outfit") == "robe"
    b = c.get("bulk", 1.0)
    zs = [z_top, 0.72, 0.64, 0.56, 0.47, 0.42, 0.34, 0.26, 0.16]
    zs = [z for z in zs if z_bot <= z <= z_top]
    if zs[-1] > z_bot + 1e-3:
        zs.append(z_bot)
    rings = []
    for z in zs:
        rx, ry = _prof(z, robe)
        f = grow * (1.0 + (flare - 1.0) * max(0.0, (0.53 - z) / 0.4))
        bb = c.get("flare", 1.0) if (robe and z < 0.5) else b     # 长袍下摆不随 bulk 缩放（同 build_body）
        rings.append((V((0, C.spine_y(J, z * h), z * h)), rx * h * bb * f, ry * h * bb * f))
    S.add(*rings_mesh(rings, seg=12, cap0=False, cap1=False), mat, _wt(J, h))
    if open_front:   # 对襟：前中一道深色缝
        S.add(*box((0, C.spine_y(J, (z_top + z_bot) / 2 * h) - _prof((z_top + z_bot) / 2, robe)[1] * h * b * grow - 0.003 * h,
                    (z_top + z_bot) / 2 * h), (0.008 * h, 0.004 * h, (z_top - z_bot) * h)), "M_A2C_Black", _wt(J, h))


def _belt_item(S, h, x, y, z, size, mat, rot=None):
    S.add(*box((x * h, y * h, z * h), tuple(s * h for s in size), rot=rot), mat, W("Hips"))


# ====================================================================== 人物：头饰钩子（HAIR_HOOKS）
def hair_fangjin(S, J, hc, r, mat, h, c):
    """四方平定巾：高而方、顶略外张的黑纱巾（族老）。"""
    rx, ry, rz = r
    C.hair_short(S, hc, r, mat, h)
    cap = c.get("cap", "M_A2C_Black")
    S.add(*rings_mesh([(hc + V((0, 0.006 * h, rz * 0.35)), rx * 1.1, ry * 1.08),
                       (hc + V((0, 0.008 * h, rz * 1.0)), rx * 1.14, ry * 1.1),
                       (hc + V((0, 0.012 * h, rz * 1.0 + 0.07 * h)), rx * 1.28, ry * 1.22)], seg=4), cap, W("Head"))


def hair_dongpo(S, J, hc, r, mat, h, c):
    """东坡巾：方筒高巾，前面一片斜折的护檐（族老 B）。"""
    rx, ry, rz = r
    C.hair_short(S, hc, r, mat, h)
    cap = c.get("cap", "M_A2C_EB_Cap")
    S.add(*box(hc + V((0, 0.006 * h, rz * 0.95)), (rx * 2.15, ry * 2.1, 0.11 * h)), cap, W("Head"))
    S.add(*box(hc + V((0, -ry * 1.04, rz * 0.85)), (rx * 2.0, 0.008 * h, 0.07 * h), rot=_eu(-14, 0, 0)), cap, W("Head"))
    S.add(*box(hc + V((0, 0.006 * h, rz * 0.95 + 0.06 * h)), (rx * 1.6, ry * 1.5, 0.012 * h)), cap, W("Head"))


def hair_wangjin(S, J, hc, r, mat, h, c):
    """网巾 + 发髻：明代男子日常，额上一道宽黑网巾，头顶一髻。"""
    rx, ry, rz = r
    C.hair_bun(S, hc, r, mat, h)
    S.add(*rings_mesh([(hc + V((0, 0.004 * h, rz * 0.2)), rx * 1.1, ry * 1.09),
                       (hc + V((0, 0.004 * h, rz * 0.62)), rx * 1.09, ry * 1.07)], seg=10), "M_A2C_NetCap", W("Head"))


def hair_toujin(S, J, hc, r, mat, h, c):
    """裹头巾：包住发髻，脑后两根巾脚垂下（义师、匠人、民夫）。"""
    rx, ry, rz = r
    cl = c.get("cloth", "M_A2C_Cloth_Grey")
    C.hair_short(S, hc, r, mat, h)
    S.add(*ellipsoid(hc + V((0, 0.008 * h, 0.012 * h)), rx * 1.13, ry * 1.11, rz * 1.02, seg=10, rings=4, zmin=-0.05),
          cl, W("Head"))
    S.add(*ellipsoid(hc + V((0, 0.006 * h, rz + 0.01 * h)), 0.024 * h, 0.022 * h, 0.02 * h, seg=8, rings=3), cl, W("Head"))
    for sx in (-1, 1):
        S.add(*box(hc + V((sx * 0.014 * h, ry * 1.08, -rz * 0.55)), (0.016 * h, 0.004 * h, 0.07 * h), rot=_eu(-8, sx * 6, 0)),
              cl, lambda p: {"Head": 0.6, "Neck": 0.4})


def hair_douli(S, J, hc, r, mat, h, c):
    """斗笠（可加顶缨：义师红缨笠）。"""
    C.hair_bun(S, hc, r, mat, h, c.get("band"))
    C.straw_hat(S, hc, r, c.get("hat", "M_CH_StrawHat"), h)
    if c.get("tassel"):
        S.add(*ellipsoid(hc + V((0, 0.004 * h, r[2] * 1.3)), 0.022 * h, 0.022 * h, 0.03 * h, seg=8, rings=3),
              c["tassel"], W("Head"))


def hair_woman_pin(S, J, hc, r, mat, h, c):
    """妇人：头顶偏后的高髻 + 横插发簪 + 抹额。"""
    rx, ry, rz = r
    C.hair_short(S, hc, r, mat, h)
    S.add(*ellipsoid(hc + V((0, ry * 0.55, rz * 0.85)), 0.036 * h, 0.03 * h, 0.03 * h, seg=8, rings=4), mat, W("Head"))
    S.add(*box(hc + V((0, ry * 0.55, rz * 0.9)), (0.11 * h, 0.006 * h, 0.006 * h), rot=_eu(0, 12, 0)), "M_A2C_Pin", W("Head"))
    S.add(*rings_mesh([(hc + V((0, 0.004 * h, rz * 0.3)), rx * 1.1, ry * 1.08),
                       (hc + V((0, 0.004 * h, rz * 0.44)), rx * 1.09, ry * 1.07)], seg=10), c.get("band", "M_A2C_Black"), W("Head"))


def hair_zongjiao(S, J, hc, r, mat, h, c):
    """孩童总角：头两侧各扎一个小髻，额前一撮刘海。"""
    rx, ry, rz = r
    C.hair_short(S, hc, r, mat, h)
    for sx in (-1, 1):
        S.add(*ellipsoid(hc + V((sx * rx * 0.85, 0.004 * h, rz * 0.8)), 0.022 * h, 0.02 * h, 0.022 * h, seg=8, rings=4),
              mat, W("Head"))
        S.add(*rings_mesh([(hc + V((sx * rx * 0.85, 0.004 * h, rz * 0.6)), 0.014 * h, 0.013 * h),
                           (hc + V((sx * rx * 0.85, 0.004 * h, rz * 0.66)), 0.014 * h, 0.013 * h)], seg=6),
              c.get("band", "M_A2C_Tassel"), W("Head"))
    S.add(*box(hc + V((0, -ry * 0.9, rz * 0.62)), (0.04 * h, 0.012 * h, 0.018 * h)), mat, W("Head"))


C.HAIR_HOOKS.update({"a2_fangjin": hair_fangjin, "a2_dongpo": hair_dongpo, "a2_wangjin": hair_wangjin,
                     "a2_toujin": hair_toujin, "a2_douli": hair_douli, "a2_woman_pin": hair_woman_pin,
                     "a2_zongjiao": hair_zongjiao})


# ====================================================================== 人物：服饰配件钩子（EXTRA_HOOKS）
def ex_jiaoling(S, J, h, c, tw, hipsW):
    """交领右衽：一道浅色领缘从左颈斜到右腋下，另一道短的从右颈到胸口（明制标志）。"""
    m = c.get("collar_mat", "M_A2C_Collar")
    zt = (J["chest_t"].z / h) + 0.005
    _band(S, J, h, c, (0.03 * h, zt), (-0.07 * h, 0.66), 0.018, m, n=5)
    _band(S, J, h, c, (-0.03 * h, zt), (0.0, 0.75), 0.016, m, n=3)


def ex_robe_sash(S, J, h, c, tw, hipsW):
    """长袍束带 + 前垂两条带头。"""
    m = c.get("robe_sash", "M_A2C_EA_Sash")
    p = _front(J, h, c, 0.02 * h, 0.5)
    for dx in (0.0, 0.025):
        S.add(*box(p + V((dx * h, -0.004 * h, -0.08 * h)), (0.014 * h, 0.004 * h, 0.14 * h)), m,
              {"Hips": 0.6, "LeftUpperLeg": 0.4})


def ex_beizi(S, J, h, c, tw, hipsW):
    """褙子：罩在袍外的对襟长衣，到膝下（族老 B）。"""
    _shell(S, J, h, c, c.get("over", "M_A2C_EB_Over"), 0.8, 0.22, grow=1.06, flare=1.05, open_front=True)


def ex_bijia(S, J, h, c, tw, hipsW):
    """比甲：无袖对襟长背心（妇人）。"""
    _shell(S, J, h, c, c["bijia"], 0.8, c.get("bijia_bot", 0.3), grow=1.07, flare=1.06, open_front=True)


def ex_sleeves(S, J, h, c, tw, hipsW):
    """袖套：前臂套一截粗布/皮。"""
    m = c.get("sleeve_mat", "M_A2C_Canvas")
    for s, side in (("L", "Left"), ("R", "Right")):
        sg = 1 if s == "L" else -1
        a = J["elbow" + s] + V((sg * 0.02 * h, 0, 0))
        b = J["wrist" + s] - V((sg * 0.005 * h, 0, 0))
        S.add(*tube(a, b, 0.031 * h, 0.027 * h, seg=8), m, W(side + "LowerArm"))


def ex_long_apron(S, J, h, c, tw, hipsW):
    """长围裙：胸前到小腿，挂脖带（铁匠/石匠）。"""
    m = c.get("apron", "M_A2C_LeatherApron")
    bk = c.get("bulk", 1.0)
    S.add(*box((0, -0.08 * h * bk, 0.34 * h), (0.19 * h, 0.006 * h, c.get("apron_len", 0.34) * h)), m,
          {"Hips": 0.5, "LeftUpperLeg": 0.25, "RightUpperLeg": 0.25})
    S.add(*box((0, -0.072 * h * bk, 0.64 * h), (0.15 * h, 0.006 * h, 0.2 * h)), m, tw)
    _band(S, J, h, c, (0.06 * h, 0.74), (0.035 * h, 0.81), 0.01, m, n=1)
    _band(S, J, h, c, (-0.06 * h, 0.74), (-0.035 * h, 0.81), 0.01, m, n=1)


def ex_mason_tools(S, J, h, c, tw, hipsW):
    """石匠：右胯插錾子、左胯挂手锤。"""
    _belt_item(S, h, -0.105, -0.02, 0.45, (0.012, 0.012, 0.14), "M_A2C_Iron", rot=_eu(10, 0, 0))
    _belt_item(S, h, 0.105, 0.0, 0.43, (0.014, 0.014, 0.12), "M_PR_Wood", rot=_eu(-8, 0, 0))
    _belt_item(S, h, 0.105, 0.0, 0.37, (0.03, 0.05, 0.03), "M_A2C_Iron")


def ex_carpenter(S, J, h, c, tw, hipsW):
    """木匠：背后斜插曲尺、右胯墨斗、耳后夹一支笔。"""
    S.add(*box((0.0, 0.085 * h, 0.66 * h), (0.012 * h, 0.006 * h, 0.26 * h), rot=_eu(0, 30, 0)), "M_A2_Fir", tw)
    S.add(*box((-0.065 * h, 0.085 * h, 0.55 * h), (0.14 * h, 0.006 * h, 0.012 * h), rot=_eu(0, 30, 0)), "M_A2_Fir", tw)
    _belt_item(S, h, -0.105, -0.03, 0.45, (0.03, 0.06, 0.035), "M_PR_WoodDark")
    _belt_item(S, h, -0.105, -0.065, 0.45, (0.02, 0.012, 0.02), "M_A2C_Ink")
    S.add(*box((0.055 * h, 0.01 * h, 0.9 * h), (0.006 * h, 0.05 * h, 0.006 * h), rot=_eu(20, 0, 0)), "M_PR_Wood", W("Head"))


def ex_towel(S, J, h, c, tw, hipsW):
    """汗巾：搭在脖子上，两头垂到胸前。"""
    m = c.get("towel", "M_A2C_Towel")
    S.add(*rings_mesh([(J["neck"] + V((0, 0.002 * h, -0.016 * h)), 0.045 * h, 0.038 * h),
                       (J["neck"] + V((0, 0.002 * h, 0.004 * h)), 0.042 * h, 0.036 * h)], seg=8), m, W("Chest"))
    for sx in (-1, 1):
        _band(S, J, h, c, (sx * 0.035 * h, 0.81), (sx * 0.045 * h, 0.7), 0.026, m, n=2)


def ex_smith(S, J, h, c, tw, hipsW):
    """铁匠：左胯挂火钳、皮护臂（用袖套）。"""
    for dx in (-0.006, 0.006):
        _belt_item(S, h, 0.105 + dx, 0.0, 0.38, (0.006, 0.008, 0.26), "M_A2C_Iron", rot=_eu(0, dx * 300, 0))


def ex_rope_shoulder(S, J, h, c, tw, hipsW):
    """一盘绳斜挎在左肩到右腰。"""
    m = "M_A2C_Rope"
    for k in range(3):
        _band(S, J, h, c, (0.07 * h, 0.81), (-0.08 * h, 0.5 + k * 0.012), 0.012, m, n=4)
    S.add(*box((0.0, 0.08 * h, 0.66 * h), (0.012 * h, 0.012 * h, 0.32 * h), rot=_eu(0, -35, 0)), m, tw)


def ex_patches(S, J, h, c, tw, hipsW):
    """补丁：衣服上几块颜色不同的方补。"""
    for x, z, s in ((0.04, 0.6, 0.05), (-0.05, 0.7, 0.04)):
        S.add(*box(_front(J, h, c, x * h, z, 0.002) - V((0, 0.001 * h, 0)), (s * h, 0.004 * h, s * h)), "M_A2C_Patch", tw)
    S.add(*box(V((0.085 * h, -0.02 * h, 0.2 * h)), (0.008 * h, 0.05 * h, 0.05 * h)), "M_A2C_Patch",
          W("LeftLowerLeg"))


def ex_shoulder_pad(S, J, h, c, tw, hipsW):
    """垫肩：右肩一块厚布垫（扛木杠用）。"""
    S.add(*box(J["armR"] + V((0.03 * h, 0, 0.03 * h)), (0.08 * h, 0.09 * h, 0.025 * h)), "M_A2C_Patch",
          {"RightShoulder": 0.5, "Chest": 0.5})


def ex_suoyi(S, J, h, c, tw, hipsW):
    """短蓑衣：披在肩背上的一圈草片。"""
    hz = J["chest_t"].z
    S.add(*rings_mesh([(V((0, J["chest_t"].y + 0.02 * h, hz + 0.02 * h)), 0.07 * h, 0.05 * h),
                       (V((0, J["chest_t"].y + 0.04 * h, hz - 0.03 * h)), 0.15 * h, 0.09 * h),
                       (V((0, J["chest"].y + 0.06 * h, 0.58 * h)), 0.16 * h, 0.09 * h)], seg=10, cap0=False, cap1=False),
          "M_A2C_Cape", tw)


def ex_kanjian(S, J, h, c, tw, hipsW):
    """坎肩：短背心罩在短褐外。"""
    _shell(S, J, h, c, c.get("vest", "M_A2C_Vest"), 0.8, 0.47, grow=1.06, open_front=True)


def ex_armor(S, J, h, c, tw, hipsW):
    """布面甲/纸甲：胸背甲 + 下摆甲裙 + 披膊；布甲钉铜泡，纸甲压横绦。"""
    m = c["armor_mat"]
    kind = c.get("armor_kind", "bu")
    _shell(S, J, h, c, m, 0.8, 0.36, grow=1.09, flare=1.08)
    cc = dict(c)
    cc["_shell"] = 1.09
    if kind == "bu":
        for z in (0.5, 0.58, 0.66, 0.74):
            for x in (-0.06, -0.02, 0.02, 0.06):
                p = _front(J, h, cc, x * h, z, 0.003)
                S.add(*box(p, (0.009 * h, 0.006 * h, 0.009 * h)), "M_A2C_Stud", tw)
        for z in (0.41,):
            for x in (-0.07, -0.025, 0.025, 0.07):
                p = _front(J, h, cc, x * h, z, 0.003)
                S.add(*box(p, (0.009 * h, 0.006 * h, 0.009 * h)), "M_A2C_Stud", _wt(J, h))
    else:
        b = c.get("bulk", 1.0)
        for z in (0.44, 0.52, 0.6, 0.68, 0.76):     # 横绦：绕甲身一圈的细带
            rx, ry = _prof(z)
            f = 1.1 * (1.0 + 0.08 * max(0.0, (0.53 - z) / 0.4)) * b * h
            rr = [(V((0, C.spine_y(J, (z + d) * h), (z + d) * h)), rx * f, ry * f) for d in (-0.005, 0.005)]
            S.add(*rings_mesh(rr, seg=12, cap0=False, cap1=False), "M_A2C_ML_Lace", _wt(J, h))
    # 前襟中缝
    _band(S, J, h, cc, (0.0, 0.8), (0.0, 0.38), 0.008, "M_A2C_ML_Lace", n=4)
    for s, side in (("L", "Left"), ("R", "Right")):
        sg = 1 if s == "L" else -1
        S.add(*box(J["arm" + s] + V((sg * 0.035 * h, 0, 0.0)), (0.08 * h, 0.095 * h, 0.06 * h), rot=_eu(0, -sg * 22, 0)), m,
              W(side + "UpperArm"))


def ex_quiver(S, J, h, c, tw, hipsW):
    """背后箭囊：右肩探出几支箭羽。"""
    a, b = V((0.06 * h, 0.1 * h, 0.5 * h)), V((-0.07 * h, 0.1 * h, 0.8 * h))
    S.add(*tube(a, b, 0.03 * h, 0.034 * h, seg=8), "M_A2C_Quiver", tw)
    d = (b - a).normalized()
    for k in range(3):
        o = V(((k - 1) * 0.012 * h, 0, 0))
        S.add(*tube(b + o, b + o + d * 0.08 * h, 0.006 * h, 0.006 * h, seg=4), "M_A2C_Towel", W("Chest"))
    _band(S, J, h, c, (-0.07 * h, 0.8), (0.07 * h, 0.5), 0.012, "M_A2C_Quiver", n=4)


def ex_shield_back(S, J, h, c, tw, hipsW):
    """背上藤牌：圆盾，中间一个凸。"""
    cy = J["chest"].y + 0.1 * h
    # 竖立在背后的圆盘：XZ 平面的扁圆柱
    seg = 12
    vs, fs = [], []
    for yy in (cy, cy + 0.025 * h):
        for i in range(seg):
            a = 2 * math.pi * i / seg
            vs.append((0.16 * h * math.cos(a), yy, 0.66 * h + 0.16 * h * math.sin(a)))
    fs.append(list(range(seg)))
    fs.append([seg + i for i in reversed(range(seg))])
    for i in range(seg):
        j = (i + 1) % seg
        fs.append([i, j, seg + j, seg + i])
    S.add(vs, fs, "M_A2C_Shield", tw)
    S.add(*ellipsoid((0, cy + 0.03 * h, 0.66 * h), 0.04 * h, 0.02 * h, 0.04 * h, seg=8, rings=3), "M_A2C_Stud", tw)


def ex_lock(S, J, h, c, tw, hipsW):
    """孩童长命锁：颈圈 + 胸前一块银锁。"""
    S.add(*rings_mesh([(J["neck"] + V((0, -0.002 * h, -0.02 * h)), 0.04 * h, 0.035 * h),
                       (J["neck"] + V((0, -0.002 * h, -0.012 * h)), 0.04 * h, 0.035 * h)], seg=8), "M_A2C_Silver", W("Chest"))
    S.add(*box(_front(J, h, c, 0.0, 0.76, 0.006), (0.05 * h, 0.008 * h, 0.035 * h)), "M_A2C_Silver", W("Chest"))


def ex_waist_apron(S, J, h, c, tw, hipsW):
    """妇人腰间短围裙。"""
    p = _front(J, h, c, 0.0, 0.44, 0.012)
    S.add(*box(p, (0.17 * h, 0.006 * h, 0.16 * h)), c.get("apron", "M_A2C_Towel"), {"Hips": 0.6, "LeftUpperLeg": 0.2, "RightUpperLeg": 0.2})


C.EXTRA_HOOKS.update({"a2_jiaoling": ex_jiaoling, "a2_robe_sash": ex_robe_sash, "a2_beizi": ex_beizi, "a2_bijia": ex_bijia,
                      "a2_sleeves": ex_sleeves, "a2_long_apron": ex_long_apron, "a2_mason_tools": ex_mason_tools,
                      "a2_carpenter": ex_carpenter, "a2_towel": ex_towel, "a2_smith": ex_smith,
                      "a2_rope_shoulder": ex_rope_shoulder, "a2_patches": ex_patches, "a2_shoulder_pad": ex_shoulder_pad,
                      "a2_suoyi": ex_suoyi, "a2_kanjian": ex_kanjian, "a2_armor": ex_armor, "a2_quiver": ex_quiver,
                      "a2_shield_back": ex_shield_back, "a2_lock": ex_lock, "a2_waist_apron": ex_waist_apron})


# ====================================================================== 人物配置
_MING = dict(outfit="jacket", shoe="M_CH_Straw", wrap="M_CH_Wrap")   # 短褐 + 绑腿 + 草鞋


def _ming(**kw):
    d = dict(_MING)
    d.update(kw)
    d["extras"] = ["a2_jiaoling"] + kw.get("extras", [])
    return d


A2_CAST = {
    # ---- 明代族老（祠堂议事，反对筑堡的「墙是死的，人是活的」）
    "NPC_MingElder_A": dict(H=1.66, outfit="robe", top="M_A2C_EA_Robe", pants="M_A2C_EA_Robe", shoe="M_CH_ClothShoe",
                            skin="M_CH_Skin_Old", hair="a2_fangjin", hair_mat="M_CH_Hair_White", brow="M_CH_Hair_White",
                            beard="long_white", hunch=0.45, bulk=1.06, cuff=1.4, brow_tilt=10, robe_sash="M_A2C_EA_Sash",
                            extras=["a2_jiaoling", "a2_robe_sash"],
                            desc="明代族老 A：70 岁，赭褐道袍、高方的四方平定巾、白长须、微驼、宽袖；算账反对筑堡的主声音"),
    "NPC_MingElder_B": dict(H=1.73, outfit="robe", top="M_A2C_EB_Robe", pants="M_A2C_EB_Robe", shoe="M_CH_ClothShoe",
                            skin="M_CH_Skin_Old", hair="a2_dongpo", hair_mat="M_CH_Hair_Grey", brow="M_CH_Hair_Grey",
                            beard="short_grey", hunch=0.15, bulk=0.9, cuff=1.35, brow_tilt=-4, over="M_A2C_EB_Over",
                            extras=["a2_jiaoling", "a2_beizi"],
                            desc="明代族老 B：62 岁，高瘦，暗橄榄直裰外罩黑褐褙子、东坡巾、灰短须；中间派"),
    # ---- 匠人 4 型
    "NPC_Artisan_Mason": _ming(H=1.70, top="M_A2C_MS_Coat", pants="M_A2C_MS_Pants", sash="M_A2C_MS_Pants", hair="a2_toujin",
                               cloth="M_A2C_Cloth_Grey", skin="M_CH_Skin_Dark", bulk=1.1, cuff=1.2, apron="M_A2C_LeatherApron",
                               apron_len=0.3, sleeve_mat="M_A2C_Canvas", brow_tilt=6,
                               extras=["a2_long_apron", "a2_sleeves", "a2_mason_tools"],
                               desc="石匠：40 岁，灰白短褐、灰头巾、皮围裙到膝、帆布袖套，腰挂錾子和手锤"),
    "NPC_Artisan_Carpenter": _ming(H=1.72, top="M_A2C_CP_Coat", pants="M_A2C_LB_Pants1", sash="M_A2C_LB_Pants1",
                                   hair="a2_wangjin", bulk=0.98, apron="M_A2C_CP_Apron",
                                   extras=["apron", "a2_carpenter"],
                                   desc="木匠：45 岁，褐短褐、网巾发髻、浅帆布围裙，背插曲尺、腰挂墨斗、耳夹木笔"),
    "NPC_Artisan_Rammer": _ming(H=1.69, top="M_A2C_RM_Coat", pants="M_A2C_LB_Pants3", sash="M_A2C_LB_Pants2", hair="a2_douli",
                                skin="M_CH_Skin_Dark", bulk=1.15, cuff=1.3, towel="M_A2C_Towel",
                                extras=["a2_towel"],
                                desc="夯土匠：35 岁，粗壮，土黄短褐卷袖、斗笠、脖搭白汗巾（喊号子的领夯）"),
    "NPC_Artisan_Smith": _ming(H=1.74, top="M_A2C_SM_Coat", pants="M_A2C_LB_Pants2", sash="M_A2C_LB_Pants2", hair="a2_toujin",
                               cloth="M_A2C_Cloth_Brown", skin="M_CH_Skin_Dark", bulk=1.12, apron="M_A2C_SM_Apron",
                               apron_len=0.4, sleeve_mat="M_A2C_SM_Apron", brow_tilt=8,
                               extras=["a2_long_apron", "a2_sleeves", "a2_smith"],
                               desc="铁匠：50 岁，黑短褐、褐头巾、长皮围裙到小腿、皮护臂，左胯挂火钳"),
    # ---- 民夫 6 变体（换头/换色/换配件 + 身高胖瘦）
    "NPC_Laborer_A": _ming(H=1.70, top="M_A2C_LB_Coat1", pants="M_A2C_LB_Pants1", sash="M_A2C_LB_Pants2", hair="a2_douli",
                           bulk=1.0, cuff=1.25, extras=["a2_towel"], desc="民夫 A：斗笠、汗巾、褐短褐（标准体）"),
    "NPC_Laborer_B": _ming(H=1.76, top="M_A2C_LB_Coat2", pants="M_A2C_LB_Pants2", sash="M_A2C_LB_Pants1", hair="a2_toujin",
                           cloth="M_A2C_Cloth_Blue", bulk=0.9, extras=["a2_rope_shoulder"],
                           desc="民夫 B：高瘦，蓝灰头巾、斜挎一盘麻绳"),
    "NPC_Laborer_C": _ming(H=1.62, top="M_A2C_LB_Coat3", pants="M_A2C_LB_Pants3", sash="M_A2C_LB_Pants2", hair="bun",
                           band="M_CH_Headband", skin="M_CH_Skin_Old", hunch=0.4, bulk=0.95, brow_tilt=-6,
                           hair_mat="M_CH_Hair_Grey", beard="short_grey", extras=["a2_patches"],
                           desc="民夫 C：矮、上年纪、灰发髻、背微驼，衣裤打补丁"),
    "NPC_Laborer_D": _ming(H=1.73, top="M_A2C_LB_Coat4", pants="M_A2C_LB_Pants1", sash="M_A2C_LB_Pants3", hair="a2_wangjin",
                           skin="M_CH_Skin_Dark", bulk=1.14, cuff=1.3, towel="M_A2C_Patch",
                           extras=["a2_shoulder_pad", "a2_towel"], desc="民夫 D：壮，网巾发髻、右肩垫肩（抬杠）、灰汗巾"),
    "NPC_Laborer_E": _ming(H=1.67, top="M_A2C_LB_Coat5", pants="M_A2C_LB_Pants2", sash="M_A2C_LB_Pants1", hair="headscarf",
                           hair_mat="M_A2C_Cloth_Brown", bulk=1.02, extras=["a2_suoyi"],
                           desc="民夫 E：包褐头巾、肩披短蓑衣（雨天上工）"),
    "NPC_Laborer_F": _ming(H=1.64, top="M_A2C_LB_Coat6", pants="M_A2C_LB_Pants3", sash="M_A2C_LB_Pants2", hair="a2_toujin",
                           cloth="M_A2C_Towel", head=1.06, bulk=0.88, vest="M_A2C_Vest", brow_tilt=-8,
                           extras=["a2_kanjian"], desc="民夫 F：半大后生（17 岁），白头巾、短褐外罩坎肩"),
    # ---- 义师 4 变体（与王德同系：靛蓝短打/头巾/绑腿/腰牌，加布甲或纸甲区分）
    "NPC_Militia_A": _ming(H=1.74, top="M_A2C_ML_Coat", pants="M_A2C_ML_Pants", sash="M_CH_WD_Sash", hair="a2_toujin",
                           cloth="M_A2C_ML_Bujia_Red", armor_mat="M_A2C_ML_Bujia_Red", armor_kind="bu", brow_tilt=8,
                           extras=["a2_armor", "knife", "tag"], desc="义师 A：红褐布面甲钉铜泡、红头巾、短刀、腰牌"),
    "NPC_Militia_B": _ming(H=1.70, top="M_A2C_ML_Coat2", pants="M_A2C_ML_Pants", sash="M_A2C_ML_Lace", hair="a2_toujin",
                           cloth="M_A2C_Cloth_Grey", armor_mat="M_A2C_ML_Paper", armor_kind="zhi", bulk=0.94,
                           extras=["a2_armor", "a2_quiver", "tag"], desc="义师 B：米黄纸甲压横绦、灰头巾、背箭囊（弓手）"),
    "NPC_Militia_C": _ming(H=1.77, top="M_A2C_ML_Coat", pants="M_A2C_ML_Pants", sash="M_A2C_ML_Lace", hair="a2_douli",
                           hat="M_CH_StrawHat", tassel="M_A2C_Tassel", armor_mat="M_A2C_ML_Bujia_Blue", armor_kind="bu",
                           bulk=1.08, extras=["a2_armor", "a2_shield_back", "tag"],
                           desc="义师 C：靛青布面甲、红缨斗笠、背藤牌（牌手）"),
    "NPC_Militia_D": _ming(H=1.68, top="M_A2C_ML_Coat2", pants="M_A2C_ML_Pants", sash="M_CH_WD_Sash", hair="a2_toujin",
                           cloth="M_A2C_ML_Coat", armor_mat="M_A2C_ML_Paper2", armor_kind="zhi", sleeve_mat="M_A2C_ML_Lace",
                           brow_tilt=4, extras=["a2_armor", "a2_sleeves", "knife", "tag"],
                           desc="义师 D：灰纸甲、靛头巾、皮护臂、短刀（长枪另为道具）"),
    # ---- 妇人 / 孩童
    "NPC_MingWoman_A": dict(H=1.56, outfit="robe", top="M_A2C_WA_Ao", skirt="M_A2C_WA_Skirt", pants="M_A2C_WA_Skirt",
                            shoe="M_CH_ClothShoe", hair="headscarf", hair_mat="M_A2C_WA_Scarf", hem=0.03, flare=1.04,
                            bulk=0.95, trim="M_A2C_WA_Skirt", bijia="M_A2C_WA_Bijia", bijia_bot=0.34, apron="M_A2C_Towel",
                            brow_tilt=-6, extras=["a2_jiaoling", "ao_hem", "a2_bijia", "a2_waist_apron"],
                            desc="妇人 A（送饭）：35 岁，褐袄长裙、青灰比甲、包头巾、白腰围（饭篮另为道具）"),
    "NPC_MingWoman_B": dict(H=1.58, outfit="robe", top="M_A2C_WB_Ao", skirt="M_A2C_WB_Skirt", pants="M_A2C_WB_Skirt",
                            shoe="M_CH_ClothShoe", hair="a2_woman_pin", hem=0.03, flare=1.02, bulk=0.88,
                            trim="M_A2C_WB_Skirt", bijia="M_A2C_WB_Bijia", bijia_bot=0.3, brow_tilt=-10,
                            extras=["a2_jiaoling", "ao_hem", "a2_bijia"],
                            desc="妇人 B（提灯）：20 岁，浅褐袄黑裙、暗红比甲、高髻横簪、黑抹额（灯笼另为道具）"),
    "NPC_MingChild": dict(H=1.15, head=1.3, outfit="jacket", top="M_A2C_CH_Coat", pants="M_A2C_CH_Pants", shoe="M_CH_ClothShoe",
                          hair="a2_zongjiao", band="M_A2C_Tassel", bulk=0.95, cuff=1.15, brow_tilt=-8,
                          extras=["a2_jiaoling", "a2_lock"],
                          desc="孩童：7 岁，赭红短袄、头两侧总角扎红绳、长命锁（春祭/巡游）"),
}


# ====================================================================== 道具：小工具
obj, fx, slab = A1.obj, A1.fx, A1.slab


def tb(mb, p0, p1, r, mat, seg=6, r1=None):
    """任意方向的圆杆（脚手架、绳、轴）。"""
    v, f = tube(V(p0), V(p1), r, r if r1 is None else r1, seg)
    b = mb.addv(v)
    for fc in f:
        mb.face([b + i for i in fc], mat)


def el(mb, c, rx, ry, rz, mat, seg=8, rings=4, zmin=-1.0):
    v, f = ellipsoid(V(c), rx, ry, rz, seg, rings, zmin)
    b = mb.addv(v)
    for fc in f:
        mb.face([b + i for i in fc], mat)


def bx(mb, c, s, mat, rot=None):
    """以中心 + 尺寸放盒子，可带旋转（度，Euler XYZ）。"""
    v, f = box(V(c), s, rot=_eu(*rot) if rot else None)
    b = mb.addv(v)
    for fc in f:
        mb.face([b + i for i in fc], mat)


def anchor(name, loc, size=0.1, parent=None, kind="ARROWS"):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind
    e.empty_display_size = size
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    if parent is not None:
        e.parent = parent
    return e


def group(name, loc=(0, 0, 0)):
    """分组空物体（团结里整组 SetActive）。"""
    return anchor(name, loc, 0.05, kind="PLAIN_AXES")


def child(ob, parent):
    """挂到父物体下且保持世界位置不变（父物体只有平移）。"""
    ob.parent = parent
    ob.location = ob.location - parent.location
    return ob


def col_box(name, c, s):
    """COL_* 碰撞/热区盒（团结里去掉渲染器，Raycast 用）。"""
    mb = K.MB()
    mb.boxc(0, 0, -s[2] / 2, s[0], s[1], s[2] / 2, "M_A2_SandDark")
    return obj(mb, name, c, uv=1.0)


def wheel(mb, r, w, mat, rim_mat=None, spokes=8, seg=12):
    """竖立的车轮，轴沿 X，中心在原点。"""
    rim_mat = rim_mat or mat
    with mb.at(0, 0, 0, ry=90):
        for k in range(seg):     # 轮辋：一圈小方块
            a0, a1 = 2 * math.pi * k / seg, 2 * math.pi * (k + 1) / seg
            p = [(r * math.cos(a0), r * math.sin(a0)), (r * math.cos(a1), r * math.sin(a1)),
                 ((r - 0.05) * math.cos(a1), (r - 0.05) * math.sin(a1)), ((r - 0.05) * math.cos(a0), (r - 0.05) * math.sin(a0))]
            mb.prism([(x, y) for x, y in p], "z", -w / 2, w / 2, rim_mat)
        mb.cyl(0, 0, -w * 0.9, w * 0.9, 0.06, mat, seg=8)
        for k in range(spokes):
            a = 2 * math.pi * k / spokes
            tb(mb, (0, 0, 0), ((r - 0.04) * math.cos(a), (r - 0.04) * math.sin(a), 0), 0.018, mat, seg=4)


# ====================================================================== 沙盘：底盘与地形
# 比例 1:500（布局平面坐标，已含 0.5 压缩）；永昌堡南北长轴沿沙盘长边（Blender X），北 = +X，东 = -Y（朝玩家）。
SAND_S = 1.0 / 500.0
TABLE_W, TABLE_D = 1.2, 0.8         # 策划案 4.2：1.2 × 0.8 m
TABLE_TOP = 0.80                    # 桌面板面
SAND_Z = 0.86                       # 沙面（ANCHOR_SandOrigin 的高度；沙盘套件都以它为原点）
RIM = 0.035


def m2t(x, z):
    """布局坐标（x=东, z=北）→ 沙盘局部 (X, Y)。"""
    return (z * SAND_S, -x * SAND_S)


def mrect(x0, z0, x1, z1, minw=0.0):
    """布局矩形 → 沙盘矩形 (X0, Y0, X1, Y1)，窄的拉宽到 minw。"""
    a = m2t(x0, z0)
    b = m2t(x1, z1)
    X0, X1 = sorted((a[0], b[0]))
    Y0, Y1 = sorted((a[1], b[1]))
    if X1 - X0 < minw:
        c = (X0 + X1) / 2
        X0, X1 = c - minw / 2, c + minw / 2
    if Y1 - Y0 < minw:
        c = (Y0 + Y1) / 2
        Y0, Y1 = c - minw / 2, c + minw / 2
    return X0, Y0, X1, Y1


def _layout():
    import json
    import os
    here = os.path.dirname(os.path.abspath(__file__))
    with open(os.path.join(here, "..", "..", "Data", "map", "yongchang_layout.json"), encoding="utf-8") as f:
        return json.load(f)


HX, HY = TABLE_W / 2 - RIM, TABLE_D / 2 - RIM      # 沙面可用半宽
SEA_Y = -0.345                                     # 东侧海岸线（压缩：海离城比实际近）
HILL_Y = 0.32                                      # 西侧山脚（压缩）：起坡在 Y=0.29，靠山 B 案西墙（x=-140 → Y=0.28）正好压在山脚

# 墙线三组（演绎，靠山 B 案：西墙 x=-140、南墙 z=-185）：
#   固定 = 北墙 + 东墙全段（两案共用）；贴河 = 南墙 + 西墙 x=-113（布局实际墙线）；靠山 = 南墙西延到 -140 + 西墙 x=-140 + 北墙西端补段。
#   两案的南墙同在 z=-185（各组各有一份，整组开关时只显示一份），区别只在西侧：贴河贴着护城河内岸，靠山把墙推到山脚、圈进护城河和河岸。
#   折线都按俯视顺时针走（城外在行进方向左手），沙埂 Ridge_<案>_NN 也按这个顺序编号。
WALL_FIXED = [[(-113, 185), (113, 185), (113, -185)]]
WALL_RIVER = [[(113, -185), (-113, -185), (-113, 185)]]
WALL_HILL = [[(113, -185), (-140, -185), (-140, 185), (-113, 185)]]
# 各组的转角台位置（固定组接缝处不出转角）
CORNERS = {"Wall_Fixed": [(113, 185), (113, -185)], "Wall_River": [(-113, -185), (-113, 185)],
           "Wall_Hill": [(-140, -185), (-140, 185)]}
# 两根木签（墙线首尾）= 两案分岔的西南角、西北角
STAKES = {"River": [(-113, -185), (-113, 185)], "Hill": [(-140, -185), (-140, 185)]}
GATES = {"GateTower_N": (4, 185, 0), "GateTower_E": (113, 40, 90), "GateTower_S": (-12, -185, 180),
         "GateTower_W": (-113, 12, 270), "GateTower_S_Hill": (-12, -185, 180), "GateTower_W_Hill": (-140, 12, 270)}
WATERGATES = {"WaterGate_E": (113, -56, 90), "WaterGate_N1": (-40, 185, 0), "WaterGate_N2": (48, 185, 0),
              "WaterGate_S1": (-40, -185, 180), "WaterGate_S2": (48, -185, 180),
              "WaterGate_S1_Hill": (-40, -185, 180), "WaterGate_S2_Hill": (48, -185, 180),
              # 靠山案的墙把西护城河圈进来：南墙西段、北墙西补段各跨一次护城河，各开一道涵洞水门
              "WaterGate_SW_Hill": (-127.5, -185, 180), "WaterGate_NW_Hill": (-127.5, 185, 0)}
TOWERS = {"Tower_East": (113, 112, 90), "Tower_North": (-72, 185, 0)}
HOUSE20_OUT = (60, 222)        # 王叔杲宅：北墙外（布局坐标）
HOUSE20_IN = (66, 168)         # 「圈进墙内」落位：北墙内、下河东岸，避开环城路以北的民居片和东北水田
SAND_CARDS = ("Wall", "Tower", "Water", "House")   # 纸卡议题（纸卡托上从左到右：墙线 / 敌台 / 水门 / 王宅）


def _water_rects(L):
    """沙盘上的水面矩形（X0,Y0,X1,Y1, 深度）。"""
    R = []
    for w in L["water"]:
        k = w["kind"]
        if k == "sea":
            continue
        minw = 0.009 if k in ("canal", "jia") else 0.012
        X0, Y0, X1, Y1 = mrect(w["x0"], w["z0"], w["x1"], w["z1"], minw)
        X0, X1 = max(X0, -HX), min(X1, HX)
        Y0, Y1 = max(Y0, SEA_Y), min(Y1, HY)
        if k == "jia" and w["id"] == "WT_JE_Banqiao":
            Y0 = max(Y0, -0.3)
        R.append((X0, Y0, X1, Y1, 0.006 if k in ("river", "moat", "pond") else 0.004))
    R.append((-HX, -HY, HX, SEA_Y, 0.008))                 # 海
    return R


def _hill(X, Y):
    """西侧山：沿后沿的几座土包。"""
    hgt = 0.0
    for cx, cy, a, r in ((-0.42, 0.37, 0.045, 0.09), (-0.22, 0.36, 0.06, 0.11), (0.02, 0.38, 0.05, 0.1),
                         (0.25, 0.36, 0.065, 0.12), (0.47, 0.37, 0.04, 0.09), (0.12, 0.33, 0.02, 0.06)):
        d2 = ((X - cx) ** 2 + (Y - cy) ** 2) / (r * r)
        hgt += a * math.exp(-d2 * 2.0)
    return hgt * max(0.0, min(1.0, (Y - HILL_Y + 0.03) / 0.07)) ** 1.5


def build_sand_surface(L):
    """沙面高度场：网格线落在所有水面/田块边界上，水面下凹成槽，后沿起山；平坦处合并成大面。"""
    waters = _water_rects(L)
    fields = []
    for f in L["fields"]:
        X0, Y0, X1, Y1 = mrect(f["x0"], f["z0"], f["x1"], f["z1"])
        fields.append((X0, Y0, X1, Y1, f["kind"]))
    bed = []
    for pts in WALL_FIXED + WALL_RIVER + WALL_HILL:
        for a, b in zip(pts, pts[1:]):
            A, B = m2t(*a), m2t(*b)
            bed.append((min(A[0], B[0]) - 0.008, min(A[1], B[1]) - 0.008, max(A[0], B[0]) + 0.008, max(A[1], B[1]) + 0.008))
    eps = 0.0018
    xs, ys = {-HX, HX}, {-HY, HY}
    for X0, Y0, X1, Y1, _ in waters:
        xs.update((X0, X1, X0 + eps, X1 - eps))
        ys.update((Y0, Y1, Y0 + eps, Y1 - eps))
    for X0, Y0, X1, Y1, _ in fields:
        xs.update((X0, X1))
        ys.update((Y0, Y1))
    for X0, Y0, X1, Y1 in bed:
        xs.update((X0, X1))
        ys.update((Y0, Y1))
    n = 40
    xs.update(-HX + 2 * HX * i / n for i in range(n + 1))
    ys.update(HILL_Y - 0.03 + (HY - HILL_Y + 0.03) * i / 8 for i in range(9))
    xs = sorted(x for x in xs if -HX <= x <= HX)
    ys = sorted(y for y in ys if -HY <= y <= HY)
    xs = [x for i, x in enumerate(xs) if i == 0 or x - xs[i - 1] > 4e-4]
    ys = [y for i, y in enumerate(ys) if i == 0 or y - ys[i - 1] > 4e-4]

    def inside(X, Y, r, shrink=0.0):
        return r[0] + shrink - 1e-6 <= X <= r[2] - shrink + 1e-6 and r[1] + shrink - 1e-6 <= Y <= r[3] - shrink + 1e-6

    def H(X, Y):
        d = 0.0
        for r in waters:
            if inside(X, Y, r, eps):
                d = max(d, r[4])
        return -d + _hill(X, Y)

    def M(X, Y):
        for r in waters:
            if inside(X, Y, r):
                return "M_A2_MiniWater"
        if _hill(X, Y) > 0.006:
            return "M_A2_HillMini"
        for r in fields:
            if inside(X, Y, r):
                return "M_A2_Moss" if r[4] == "paddy" else "M_A2_Field"
        for r in bed:
            if inside(X, Y, r):
                return "M_A2_SandDark"
        return "M_A2_Sand"

    mb = K.MB()
    nx, ny = len(xs), len(ys)
    base = mb.addv([(x, y, H(x, y)) for y in ys for x in xs])
    for j in range(ny - 1):
        for i in range(nx - 1):
            cx, cy = (xs[i] + xs[i + 1]) / 2, (ys[j] + ys[j + 1]) / 2
            a = base + j * nx + i
            mb.face([a, a + 1, a + nx + 1, a + nx], M(cx, cy))
    ob = obj(mb, "Sand", (0, 0, SAND_Z), uv=0.25)
    _simplify(ob)
    return ob


def _simplify(ob):
    """合并共面同材质的面再三角化（沙面平坦处只留大面）。"""
    import bmesh
    bm = bmesh.new()
    bm.from_mesh(ob.data)
    bmesh.ops.dissolve_limit(bm, angle_limit=math.radians(0.5), use_dissolve_boundaries=False,
                             verts=bm.verts, edges=bm.edges, delimit={"MATERIAL"})
    bmesh.ops.triangulate(bm, faces=bm.faces, quad_method="BEAUTY", ngon_method="BEAUTY")
    K.box_uv(bm, 0.25)
    bm.to_mesh(ob.data)
    bm.free()


def _poly_strips(mb, pts, wd, z0, z1, mat, ext=0.0):
    """沿折线（沙盘坐标）放一段段长条盒。"""
    for a, b in zip(pts, pts[1:]):
        (x0, y0), (x1, y1) = a, b
        if abs(x1 - x0) > abs(y1 - y0):
            mb.box(min(x0, x1) - ext, y0 - wd / 2, z0, max(x0, x1) + ext, y0 + wd / 2, z1, mat)
        else:
            mb.box(x0 - wd / 2, min(y0, y1) - ext, z0, x0 + wd / 2, max(y0, y1) + ext, z1, mat)


RIDGE_SEG = 0.05      # 沙埂分段长（约 5 cm = 布局 25 m，与墙条一致）


def build_ridge_segments(key, pts):
    """沙埂分段：Ridge_<key> 组空物体在沙面中心，子物体 Ridge_<key>_NN 沿折线顺序排；每段梯形截面（底宽 2.6 cm、高 5 mm），
    原点在段底中心、本地 +X 沿墙线前进方向。两端各多伸 2 mm 与相邻段搭接，折角处多伸半个底宽补满转角。
    同时生成 Twine_<key> 组：沿同一折线平铺在沙面的麻线段（Twine_<key>_NN，与沙埂一一对应）。"""
    g = group("Ridge_" + key, (0, 0, SAND_Z))
    tg = group("Twine_" + key, (0, 0, SAND_Z))
    wd, top, hgt = 0.026, 0.012, 0.005
    k = 0
    for ei, (a, b) in enumerate(zip(pts, pts[1:])):
        A, B = V((a[0], a[1], 0)), V((b[0], b[1], 0))
        d = B - A
        Ltot = d.length
        u = d / Ltot
        ang = math.degrees(math.atan2(u.y, u.x))
        n = max(1, round(Ltot / RIDGE_SEG))
        for i in range(n):
            t0, t1 = Ltot * i / n, Ltot * (i + 1) / n
            e0 = wd / 2 if (i == 0 and ei > 0) else 0.002
            e1 = wd / 2 if (i == n - 1 and ei < len(pts) - 2) else 0.002
            if i == 0 and ei == 0:
                e0 = wd / 2
            if i == n - 1 and ei == len(pts) - 2:
                e1 = wd / 2
            half = (t1 - t0) / 2
            c = A + u * ((t0 + t1) / 2)
            k += 1
            mb = K.MB()
            mb.prism([(-wd / 2, 0), (wd / 2, 0), (top / 2, hgt), (-top / 2, hgt)], "x", -half - e0, half + e1, "M_A2_SandRidge")
            ob = obj(mb, f"Ridge_{key}_{k:02d}", (c.x, c.y, SAND_Z), uv=0.25)
            ob.rotation_euler = (0, 0, math.radians(ang))
            child(ob, g)
            mb = K.MB()
            mb.box(-half - 0.001, -0.0005, 0, half + 0.001, 0.0005, 0.0009, "M_A2_Twine")
            ob = obj(mb, f"Twine_{key}_{k:02d}", (c.x, c.y, SAND_Z), uv=0.1)
            ob.rotation_euler = (0, 0, math.radians(ang))
            child(ob, tg)
    return g


def _stake_mesh(mb):
    """木签（与 PROP_Sand_Flags 的 Stake_NN 同形）：原点在插入点（沙面），签尖没入沙里 6 mm。"""
    mb.cyl(0, 0, 0.0, 0.084, 0.0022, "M_A2_MiniWood", seg=5)
    mb.cyl(0, 0, -0.006, 0.0, 0.0002, "M_A2_MiniWood", seg=5, r_top=0.0022)
    mb.cyl(0, 0, 0.069, 0.074, 0.0028, "M_A2_Twine", seg=5)


def build_stake_merlon(name, loc):
    """「木签变墙垛」成对件：组 <name>（原点 = 插签点，沙面）下 <name>_Stake（木签）与 <name>_Merlon（墙角垛台，比墙角台大一圈、带四角垛口），
    墙线固定时 Stake 缩下去/隐藏、Merlon 从本地 Z 0→1 长出来。"""
    g = group(name, loc)
    mb = K.MB()
    _stake_mesh(mb)
    child(obj(mb, name + "_Stake", loc, uv=0.1), g)
    mb = K.MB()
    s = 0.014
    mb.box(-s, -s, 0, s, s, MH + 0.006, "M_A2_MiniWall", skip_bottom=True)
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(sx * s - (0.006 if sx > 0 else 0), sy * s - (0.006 if sy > 0 else 0), MH + 0.006,
                   sx * s + (0.006 if sx < 0 else 0), sy * s + (0.006 if sy < 0 else 0), MH + 0.011, "M_A2_MiniWall")
    mb.box(-s + 0.003, -s + 0.003, MH + 0.006, s - 0.003, s - 0.003, MH + 0.0068, "M_A2_SandRidge")
    child(obj(mb, name + "_Merlon", loc, uv=0.1), g)
    return g


def build_sandtable():
    L = _layout()
    # ---- 桌子：面板、沙框、四腿、横枨
    mb = K.MB()
    hw, hd = TABLE_W / 2, TABLE_D / 2
    mb.box(-hw, -hd, TABLE_TOP - 0.04, hw, hd, TABLE_TOP, "M_A2_TableWood")
    mb.box(-hw + 0.02, -hd + 0.02, TABLE_TOP - 0.12, hw - 0.02, hd - 0.02, TABLE_TOP - 0.04, "M_A2_TableDark")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(sx * (hw - 0.03) - 0.03, sy * (hd - 0.03) - 0.03, 0, sx * (hw - 0.03) + 0.03, sy * (hd - 0.03) + 0.03,
                   TABLE_TOP - 0.04, "M_A2_TableDark")
    for sy in (-1, 1):
        mb.box(-hw + 0.05, sy * (hd - 0.03) - 0.015, 0.12, hw - 0.05, sy * (hd - 0.03) + 0.015, 0.16, "M_A2_TableDark")
    for sx in (-1, 1):
        mb.box(sx * (hw - 0.03) - 0.015, -hd + 0.05, 0.12, sx * (hw - 0.03) + 0.015, hd - 0.05, 0.16, "M_A2_TableDark")
    # 沙槽底（沙面下的木板）与沙框（前左角单独做子物体，1941 断角时隐藏）
    mb.box(-HX, -HY, TABLE_TOP, HX, HY, SAND_Z - 0.012, "M_A2_SandDark")
    top = SAND_Z + 0.025
    mb.box(-hw, hd - RIM, TABLE_TOP, hw, hd, top, "M_A2_TableWood")
    mb.box(-hw + 0.2, -hd, TABLE_TOP, hw, -hd + RIM, top, "M_A2_TableWood")
    mb.box(-hw, -hd + 0.2, TABLE_TOP, -hw + RIM, hd - RIM, top, "M_A2_TableWood")
    mb.box(hw - RIM, -hd + RIM, TABLE_TOP, hw, hd - RIM, top, "M_A2_TableWood")
    obj(mb, "Table", (0, 0, 0), uv=0.5)
    mb = K.MB()
    mb.box(0, 0, TABLE_TOP, 0.2, RIM, top, "M_A2_TableWood")
    mb.box(0, RIM, TABLE_TOP, RIM, 0.2, top, "M_A2_TableWood")
    obj(mb, "Rim_Corner_FL", (-hw, -hd, 0), uv=0.5)

    # ---- 沙面地形
    build_sand_surface(L)

    # ---- 静态缩微：北官道、东码头路、坟地、盐田、墙边木牌
    mb = K.MB()
    X0, Y0, X1, Y1 = mrect(1, 200, 7, 260)
    mb.box(X0, Y0, 0, HX, Y1, 0.0015, "M_A2_SandDark")                 # 北面官道
    for k in range(7):                                                  # 坟地：西北城外一片小土包 + 碑
        x, y = 0.47 + (k % 3) * 0.025, 0.12 + (k // 3) * 0.03 + (k % 2) * 0.008
        el(mb, (x, y, 0), 0.008, 0.008, 0.006, "M_A2_Grave", seg=6, rings=2, zmin=0.0)
        mb.box(x - 0.003, y + 0.008, 0, x + 0.003, y + 0.010, 0.01, "M_A2_StoneDark")
    for k in range(6):                                                  # 盐田：东南海边一排白格
        x = -0.36 + k * 0.03
        mb.box(x, -0.335, 0, x + 0.025, -0.31, 0.001, "M_A2_Salt")
    for nm, (x, z, rot) in TOWERS.items():                              # 东墙/北墙的木牌（插小旗处）
        X, Y = m2t(x, z)
        dx, dy = (0.0, -0.03) if rot == 90 else (0.03, 0.0)
        mb.box(X + dx - 0.006, Y + dy - 0.0015, 0, X + dx + 0.006, Y + dy + 0.0015, 0.022, "M_A2_MiniWood")
    obj(mb, "Static_Minis", (0, 0, SAND_Z), uv=0.25)

    # ---- 墙线两案：沙埂（Ridge_<案> 组 → Ridge_<案>_NN 分段，按墙线顺序，原点在段底中心，本地 Z 缩放 0→1 逐段隆起）、
    #      浅沟（Trench_*）、麻线（Twine_<案>_NN，平铺沙面，沙埂隆起时被盖住）、两根木签 ↔ 墙垛（StakeMerlon_<案>_A/B）
    for key, lines in (("River", WALL_RIVER), ("Hill", WALL_HILL)):
        pts = [m2t(*p) for p in lines[0]]
        build_ridge_segments(key, pts)
        mb = K.MB()
        _poly_strips(mb, pts, 0.012, -0.001, 0.0008, "M_A2_TableDark", ext=0.006)
        obj(mb, "Trench_" + key, (0, 0, SAND_Z), uv=0.25)
        for tag, p in zip("AB", STAKES[key]):
            X, Y = m2t(*p)
            anchor(f"ANCHOR_Stake_{key}_{tag}", (X, Y, SAND_Z), 0.03)
            build_stake_merlon(f"StakeMerlon_{key}_{tag}", (X, Y, SAND_Z))
            fx(f"FX_Stake_{key}_{tag}", (X, Y, SAND_Z + 0.004))
        mid = pts[len(pts) // 2]
        fx(f"FX_SandDust_{key}", (mid[0], mid[1], SAND_Z + 0.01))

    # ---- 1945：蒙布
    mb = K.MB()
    mb.frustum((-hw - 0.03, -hd - 0.03, hw + 0.03, hd + 0.03), (-hw + 0.05, -hd + 0.05, hw - 0.05, hd - 0.05),
               TABLE_TOP - 0.18, top + 0.03, "M_A2_Paper")
    obj(mb, "Cover_1945", (0, 0, 0), uv=0.5)

    # ---- 锚点、镜头位、热区、特效
    anchor("ANCHOR_SandOrigin", (0, 0, SAND_Z), 0.1)
    anchor("ANCHOR_Stand", (0, -0.75, 0), 0.3)
    anchor("ANCHOR_Stand_Shugao", (0.75, -0.55, 0), 0.3)
    anchor("ANCHOR_Stand_Pei", (-0.8, -0.5, 0), 0.3)
    fx("FX_SandDust", (0, 0, SAND_Z + 0.02))
    ex, ey = m2t(113, 0)
    nx_, ny_ = m2t(0, 185)
    anchor("CAM_Overview", (0, -0.62, SAND_Z + 0.62), 0.08)
    anchor("CAM_East", (ex, ey - 0.45, SAND_Z + 0.45), 0.08)
    anchor("CAM_North", (nx_ + 0.45, ny_ - 0.2, SAND_Z + 0.45), 0.08)
    anchor("LOOK_Overview", (0, 0, SAND_Z), 0.05)
    anchor("LOOK_East", (ex, ey, SAND_Z), 0.05)
    anchor("LOOK_North", (nx_, ny_, SAND_Z), 0.05)
    wx, wy = m2t(113, -56)
    hx_, hy_ = m2t(60, 222)
    col_box("COL_Hot_EastWall", (ex, ey, SAND_Z + 0.02), (0.74, 0.06, 0.05))
    col_box("COL_Hot_NorthWall", (nx_, ny_, SAND_Z + 0.02), (0.06, 0.5, 0.05))
    col_box("COL_Hot_WaterGate", (wx, wy, SAND_Z + 0.02), (0.06, 0.06, 0.05))
    col_box("COL_Hot_WangHouse", (hx_, hy_, SAND_Z + 0.02), (0.05, 0.05, 0.05))
    fx("FX_Water_E", (wx, wy - 0.02, SAND_Z + 0.004))
    # 墙线热区：西墙两案之间那条带（贴河 x=-113 ~ 靠山 x=-140），沙盘模式下点它 = 开始拉墙线
    lx0, ly0, lx1, ly1 = mrect(-145, -190, -108, 190)
    col_box("COL_Hot_WallLine", ((lx0 + lx1) / 2, (ly0 + ly1) / 2, SAND_Z + 0.02), (lx1 - lx0, ly1 - ly0, 0.05))
    # 敌台议题：东墙/北墙木牌顶上的插旗点（PROP_Sand_Flags 的 Flag_NN 原点放这里）+ 插旗/升台扬沙
    for nm, (x, z, rot) in TOWERS.items():
        X, Y = m2t(x, z)
        dx, dy = (0.0, -0.03) if rot == 90 else (0.03, 0.0)
        anchor(f"ANCHOR_Flag_{nm.split('_')[1]}", (X + dx, Y + dy, SAND_Z + 0.022), 0.02)
        fx(f"FX_{nm}_Rise", (X, Y, SAND_Z + 0.006))
    # 王宅木片：墙外原位 / 推进墙内的落位（与 PROP_Sand_House 的 House_20 一致），推木片时的扬沙
    for nm, (x, z) in (("Out", HOUSE20_OUT), ("In", HOUSE20_IN)):
        X, Y = m2t(x, z)
        anchor(f"ANCHOR_House_20_{nm}", (X, Y, SAND_Z), 0.02)
    X, Y = m2t(*HOUSE20_IN)
    fx("FX_House_20", (X, Y, SAND_Z + 0.004))

    # ---- 纸卡托：桌子正面挂一条斜木托，放四张议题纸卡（PROP_Sand_Flags 的 Card_* 原点对 ANCHOR_Card_*，局部旋转清零）
    tray = group("CardTray_Root", (0, -hd, TABLE_TOP))
    mb = K.MB()
    with mb.at(0, 0, 0, rx=14):
        mb.box(-0.27, -0.13, -0.018, 0.27, 0.0, 0.0, "M_A2_TableWood")
        mb.box(-0.27, -0.135, 0.0, 0.27, -0.125, 0.008, "M_A2_TableDark")               # 前挡条（卡片不滑落）
    for sx in (-1, 1):                                                                    # 两个托架
        mb.prism([(0.0, -0.02), (-0.1, -0.046), (0.0, -0.11)], "x", sx * 0.22 - 0.012, sx * 0.22 + 0.012, "M_A2_TableDark")
    child(obj(mb, "CardTray", (0, -hd, TABLE_TOP), uv=0.5), tray)
    import mathutils
    tilt = mathutils.Matrix.Rotation(math.radians(14), 3, "X")
    for i, key in enumerate(SAND_CARDS):
        p = tilt @ V((-0.195 + i * 0.13, -0.065, 0.0))
        e = anchor(f"ANCHOR_Card_{key}", (p.x, -hd + p.y, TABLE_TOP + p.z), 0.03)
        e.rotation_euler = (math.radians(14), 0, 0)

    # ---- 1941：断角（Rim_Corner_FL 隐藏后显示劈裂的残茬）+ 从缺口漏到桌面和地上的沙堆
    mb = K.MB()
    for k, (x0, x1, h_) in enumerate(((0.0, 0.012, 0.07), (0.012, 0.022, 0.045), (0.022, 0.03, 0.06), (0.03, 0.035, 0.03))):
        mb.box(0.2 - x1, 0, TABLE_TOP, 0.2 - x0, RIM, TABLE_TOP + h_, "M_A2_TableWood")      # 前沿残茬（参差）
        mb.box(0, 0.2 - x1, TABLE_TOP, RIM, 0.2 - x0, TABLE_TOP + h_ * 0.8, "M_A2_TableWood")  # 左沿残茬
    mb.prism([(0.0, 0.0), (0.06, 0.0), (0.0, 0.05)], "z", TABLE_TOP, TABLE_TOP + 0.012, "M_A2_TableDark")  # 桌面裂开的一块
    obj(mb, "Rim_Broken_FL_1941", (-hw, -hd, 0), uv=0.5)
    mb = K.MB()
    el(mb, (0.06, 0.05, SAND_Z - 0.012), 0.07, 0.06, 0.012, "M_A2_Sand", seg=8, rings=2, zmin=0.0)        # 缺口处塌下来的沙
    el(mb, (-0.05, -0.04, 0.0), 0.09, 0.07, 0.018, "M_A2_Sand", seg=8, rings=2, zmin=0.0)                # 地上一摊
    el(mb, (0.02, -0.08, 0.0), 0.05, 0.04, 0.01, "M_A2_SandDark", seg=6, rings=2, zmin=0.0)
    obj(mb, "SandSpill_1941", (-hw, -hd, 0), uv=0.25)


# ====================================================================== 沙盘套件（原点 = 沙面中心 ANCHOR_SandOrigin）
MW, MH = 0.012, 0.016          # 缩微城墙：宽 1.2 cm（6 m）、高 1.6 cm（夸张，俯视好认）


def _wall_piece(mb, length, crenel=True):
    """一段墙条：沿 +X，中心在原点、底在 0，外侧（垛口侧）朝 -Y。"""
    mb.box(-length / 2, -MW / 2, 0, length / 2, MW / 2, MH, "M_A2_MiniWall", skip_bottom=True)
    if crenel:
        n = max(1, int(length / 0.02))
        for i in range(n):
            x = -length / 2 + (i + 0.5) * length / n
            mb.box(x - 0.003, -MW / 2, MH, x + 0.003, -MW / 2 + 0.0028, MH + 0.004, "M_A2_MiniWall", skip_bottom=True)


def _runs(lines, gaps):
    """把折线切成墙条：每段约 5 cm，门洞处让出缺口。返回 [(中心X, 中心Y, 长, 朝向度)]。"""
    out = []
    for pts in lines:
        for a, b in zip(pts, pts[1:]):
            A, B = V(m2t(*a) + (0,)), V(m2t(*b) + (0,))
            d = B - A
            Ltot = d.length
            u = d / Ltot
            ang = math.degrees(math.atan2(u.y, u.x))
            # 缺口（门、敌台）沿线投影
            cuts = []
            for gx, gy, gw in gaps:
                t = (V((gx, gy, 0)) - A).dot(u)
                off = (V((gx, gy, 0)) - (A + u * t)).length
                if 0 < t < Ltot and off < 0.004:
                    cuts.append((t - gw / 2, t + gw / 2))
            cuts.sort()
            spans, s0 = [], MW / 2
            for c0, c1 in cuts:
                spans.append((s0, c0))
                s0 = c1
            spans.append((s0, Ltot - MW / 2))
            for s, e in spans:
                if e - s < 0.004:
                    continue
                n = max(1, round((e - s) / 0.05))
                for i in range(n):
                    t0 = s + (e - s) * i / n
                    t1 = s + (e - s) * (i + 1) / n
                    c = A + u * ((t0 + t1) / 2)
                    out.append((c.x, c.y, t1 - t0, ang))
    return out


def _corners(lines):
    pts = []
    for line in lines:
        for p in line:
            pts.append(m2t(*p))
    return pts


def _gaps():
    g = []
    for d, w in ((GATES, 0.03), (WATERGATES, 0.022), (TOWERS, 0.026)):
        for x, z, _ in d.values():
            g.append(m2t(x, z) + (w,))
    return g


def build_sand_wall():
    """城墙条一套（已按永昌堡轮廓摆好，三组可整组开关；每段都是独立子物体，可复制拼接）。"""
    gaps = _gaps()
    for gname, lines in (("Wall_Fixed", WALL_FIXED), ("Wall_River", WALL_RIVER), ("Wall_Hill", WALL_HILL)):
        g = group(gname)
        for i, (x, y, Lg, ang) in enumerate(_runs(lines, gaps)):
            mb = K.MB()
            # 折线都按俯视顺时针走（北→东→南→西），城外在行进方向左手：墙条垛口转到本地 +Y 再按走向旋转
            with mb.at(0, 0, 0, 180):
                _wall_piece(mb, Lg)
            ob = obj(mb, f"{gname}_{i + 1:02d}", (x, y, 0), uv=0.1)
            ob.rotation_euler = (0, 0, math.radians(ang))
            ob.parent = g
        for j, p in enumerate(CORNERS[gname]):
            X, Y = m2t(*p)
            mb = K.MB()
            mb.box(-0.011, -0.011, 0, 0.011, 0.011, MH + 0.004, "M_A2_MiniWall", skip_bottom=True)
            mb.box(-0.012, -0.012, MH + 0.004, 0.012, 0.012, MH + 0.006, "M_A2_SandRidge")
            ob = obj(mb, f"{gname}_Corner_{j + 1}", (X, Y, 0), uv=0.1)
            ob.parent = g
    # 散件母版（可拼）：直段 5 cm / 2.5 cm、转角、门段，排在沙盘外侧，团结里可复制
    kit = group("Kit", (0, -0.5, 0))
    for i, (nm, Lg) in enumerate((("Kit_Straight_L", 0.05), ("Kit_Straight_S", 0.025))):
        mb = K.MB()
        _wall_piece(mb, Lg)
        child(obj(mb, nm, (-0.1 + i * 0.08, -0.5, 0), uv=0.1), kit)
    mb = K.MB()
    mb.box(-0.011, -0.011, 0, 0.011, 0.011, MH + 0.004, "M_A2_MiniWall")
    child(obj(mb, "Kit_Corner", (0.04, -0.5, 0), uv=0.1), kit)
    mb = K.MB()
    for sx in (-1, 1):
        mb.box(sx * 0.0125 - 0.005, -MW / 2, 0, sx * 0.0125 + 0.005, MW / 2, MH + 0.002, "M_A2_MiniWall")
    mb.box(-0.0175, -MW / 2, MH * 0.6, 0.0175, MW / 2, MH + 0.002, "M_A2_MiniWall")
    child(obj(mb, "Kit_GateSeg", (0.1, -0.5, 0), uv=0.1), kit)


def _gate_tower(mb, w=0.03):
    """缩微门楼：墩台（门洞）+ 一层小楼 + 歇山小顶。沿 X 放、外侧 -Y。"""
    d = MW + 0.008
    for sx in (-1, 1):
        mb.box(sx * w / 2 - 0.009 * sx, -d / 2, 0, sx * w / 2, d / 2, MH + 0.003, "M_A2_MiniWall")
    mb.box(-w / 2, -d / 2, MH * 0.55, w / 2, d / 2, MH + 0.003, "M_A2_MiniWall")
    mb.box(-w / 2 + 0.004, -d / 2 + 0.003, MH + 0.003, w / 2 - 0.004, d / 2 - 0.003, MH + 0.012, "M_A2_MiniWood")
    mb.hip(-w / 2 - 0.002, -d / 2 - 0.002, w / 2 + 0.002, d / 2 + 0.002, MH + 0.012, 0.008, 0.008, "M_A2_MiniRoof")


def _water_gate(mb, w=0.022):
    d = MW + 0.004
    for sx in (-1, 1):
        mb.box(sx * w / 2 - 0.006 * sx, -d / 2, 0, sx * w / 2, d / 2, MH, "M_A2_MiniWall")
    mb.box(-w / 2, -d / 2, MH * 0.6, w / 2, d / 2, MH, "M_A2_MiniWall")
    for sx in (-1, 1):       # 闸槽
        mb.box(sx * 0.0045 - 0.0008, -d / 2 - 0.0012, 0, sx * 0.0045 + 0.0008, -d / 2, MH * 0.6, "M_A2_MiniIron")


def _place(ob, x, z, rot):
    X, Y = m2t(x, z)
    ob.location = (X, Y, ob.location.z)
    # 布局 rot：0/90/180/270 = 外侧朝北/东/南/西（沙盘 +X/-Y/-X/+Y）；本地外侧朝 -Y，所以转 90-rot 度
    ob.rotation_euler = (0, 0, math.radians(90 - rot))
    return ob


def build_sand_gate():
    """门楼/水门一套：四门门楼（西门两案）、瓮城、五座水门；东水门带闸板/石条/水面两态/小船/石堆。"""
    for nm, (x, z, rot) in GATES.items():
        mb = K.MB()
        _gate_tower(mb)
        _place(obj(mb, nm, (0, 0, 0), uv=0.1), x, z, rot)
    mb = K.MB()                     # 环海门瓮城：门外半圈
    mb.box(-0.022, -0.02, 0, 0.022, -0.014, MH * 0.85, "M_A2_MiniWall")
    for sx in (-1, 1):
        mb.box(sx * 0.022 - 0.006 * (sx > 0), -0.02, 0, sx * 0.022 + 0.006 * (sx < 0), -0.004, MH * 0.85, "M_A2_MiniWall")
    _place(obj(mb, "Wengcheng_E", (0, 0, 0), uv=0.1), 113, 40, 90)
    for nm, (x, z, rot) in WATERGATES.items():
        mb = K.MB()
        _water_gate(mb)
        _place(obj(mb, nm, (0, 0, 0), uv=0.1), x, z, rot)
    # 东水门的状态件（都在水门本地坐标里，原点 = 水门底中心，外侧 -Y）
    x, z, rot = WATERGATES["WaterGate_E"]
    parts = []
    mb = K.MB()
    mb.box(-0.0055, -0.0005, 0, 0.0055, 0.0005, MH * 0.58, "M_A2_MiniWood")
    parts.append(("Gate_Board", mb, (0, -MW / 2 - 0.0006, 0.0)))          # 闸板：开闸时上提/抽走
    mb = K.MB()
    for k in range(3):
        mb.box(-0.0055, -0.002, k * 0.0035, 0.0055, 0.002, k * 0.0035 + 0.0033, "M_A2_StoneLight")
    parts.append(("Gate_StoneBar", mb, (0, 0.0, 0.0)))                     # 石条：闭闸时推进闸槽
    for nm, mat, z0 in (("Water_Still", "M_A2_MiniWater", -0.0035), ("Water_Flow", "M_A2_MiniWaterFlow", -0.003)):
        mb = K.MB()
        mb.box(-0.0045, -0.05, 0, 0.0045, 0.05, 0.0006, mat)
        parts.append((nm, mb, (0, 0, z0)))                                 # 水面两态（开闸换流水材质+法线滚动）
    mb = K.MB()
    mb.prism([(0, -0.009), (0.0022, -0.005), (0.0022, 0.006), (-0.0022, 0.006), (-0.0022, -0.005)], "z", 0, 0.002, "M_A2_MiniWood")
    mb.box(-0.0004, -0.001, 0.002, 0.0004, 0.001, 0.006, "M_A2_MiniWood")
    parts.append(("Boat", mb, (0, 0.025, -0.0025)))                        # 开闸：城内小船
    mb = K.MB()
    for i, (px, py, r) in enumerate(((0, 0, 0.004), (0.003, 0.004, 0.003), (-0.003, 0.003, 0.0028), (0.001, -0.004, 0.0025))):
        el(mb, (px, py, 0), r, r, r * 0.7, "M_A2_StoneDark", seg=6, rings=2, zmin=0.0)
    parts.append(("StonePile", mb, (0, 0.02, -0.004)))                     # 闭闸：水退露出石堆
    mb = K.MB()                                                            # 流水条纹：浅色短划，周期 12.5 mm
    for k in range(8):
        y0 = -0.05 + k * 0.0125
        for j, (x, dy) in enumerate(((-0.0022, 0.0), (0.0018, 0.006))):
            mb.box(x - 0.0006, y0 + dy, 0, x + 0.0006, y0 + dy + 0.005, 0.0002, "M_A2_MiniWaterLine")
    parts.append(("Water_Flow_Lines", mb, (0, 0, -0.003 + 0.0006)))       # 开闸：沿本地 -Y（出城、往海）每秒移 12.5 mm 循环
    wg = bpy.data.objects["WaterGate_E"]
    for nm, mb_, loc in parts:
        ob = obj(mb_, nm, loc, uv=0.1)
        ob.parent = wg
    # 两态的起止位（水门本地坐标；动画 = 子物体从一个锚点 Lerp 到另一个）
    for nm, loc in (("ANCHOR_GateBoard_In", (0, -MW / 2 - 0.0006, 0.0)),            # 闸板在槽里（闭）
                    ("ANCHOR_GateBoard_Up", (0, -MW / 2 - 0.0006, MH * 0.62)),      # 闸板沿槽上提到顶（开 · 中途）
                    ("ANCHOR_GateBoard_Out", (0.016, -0.012, 0.0006)),              # 抽走后平放在墙外岸上（开 · 终点，带 X 旋转 90°）
                    ("ANCHOR_StoneBar_Out", (0, 0.028, 0.0)),                       # 石条在城内岸边待推（开）
                    ("ANCHOR_StoneBar_In", (0, 0.0, 0.0)),                          # 石条推进闸槽（闭）
                    ("ANCHOR_Boat_In", (0, 0.025, -0.0025)),                        # 小船在城内（开 · 起点）
                    ("ANCHOR_Boat_Out", (0, -0.03, -0.0025)),                       # 小船穿过水门到城外（开 · 终点）
                    ("ANCHOR_Water_High", (0, 0, -0.0035)),                         # 死水水位
                    ("ANCHOR_Water_Low", (0, 0, -0.0058))):                         # 水退（闭 · 露出石堆）
        e = anchor(nm, loc, 0.006, parent=wg)
        if nm == "ANCHOR_GateBoard_Out":
            e.rotation_euler = (math.radians(90), 0, 0)
    for nm, loc in (("FX_WaterGate_E_Splash", (0, 0.004, 0.0)), ("FX_WaterGate_E_Flow", (0, -0.006, -0.002))):
        e = fx(nm, loc)
        e.empty_display_size = 0.01
        e.parent = wg


def build_sand_tower():
    """敌台 2 座（东台对海口 / 北台对官道），台上小炮是子物体 <台名>_Cannon（原点在炮架底，升起：本地 Z 从 -0.012 到 0）。
    「墙里凸出一座台」：<台名> 本地 Z 从 -0.024（埋在沙面下）升到 0；没选的那座显示 <台名>_Flat（补缺口的平墙）。"""
    for nm, (x, z, rot) in TOWERS.items():
        mb = K.MB()
        w, d = 0.026, 0.03
        mb.box(-w / 2, -d + MW / 2, 0, w / 2, MW / 2, MH + 0.004, "M_A2_MiniWall")
        mb.crenels(-w / 2, w / 2, -d + MW / 2, -d + MW / 2 + 0.003, MH + 0.004, MH + 0.008, "M_A2_MiniWall", 0.004, 0.003)
        for sx in (-1, 1):
            mb.box(sx * w / 2 - (0.003 if sx > 0 else 0), -d + MW / 2, MH + 0.004, sx * w / 2 + (0.003 if sx < 0 else 0),
                   MW / 2, MH + 0.008, "M_A2_MiniWall")
        t = _place(obj(mb, nm, (0, 0, 0), uv=0.1), x, z, rot)
        mb = K.MB()
        mb.box(-0.004, -0.003, 0, 0.004, 0.003, 0.003, "M_A2_MiniWood")
        with mb.at(0, 0, 0.0045, rx=90):
            mb.cyl(0, 0, -0.002, 0.011, 0.002, "M_A2_MiniIron", seg=6, r_top=0.0016)
        c = obj(mb, nm + "_Cannon", (0, -d / 2 + MW / 2 - 0.004, MH + 0.004), uv=0.1)
        c.parent = t
        # 没选这座台时补上的平墙（墙条在敌台处留了缺口）：<台名>_Flat，与 <台名> 二选一显示
        mb = K.MB()
        _wall_piece(mb, 0.028)
        _place(obj(mb, nm + "_Flat", (0, 0, 0), uv=0.1), x, z, rot)


def _house(mb, kind, s=1.0):
    """缩微民居片（原点底中心，正面 -Y）。"""
    R, Wl = "M_A2_MiniRoof", "M_A2_MiniWood"
    if kind == 0:      # 单间
        mb.box(-0.008 * s, -0.006 * s, 0, 0.008 * s, 0.006 * s, 0.006 * s, Wl)
        mb.prism([(-0.0075 * s, 0.006 * s), (0.0075 * s, 0.006 * s), (0, 0.011 * s)], "x", -0.009 * s, 0.009 * s, R)
    elif kind == 1:    # 长屋
        mb.box(-0.014 * s, -0.005 * s, 0, 0.014 * s, 0.005 * s, 0.006 * s, Wl)
        mb.prism([(-0.0065 * s, 0.006 * s), (0.0065 * s, 0.006 * s), (0, 0.0105 * s)], "x", -0.015 * s, 0.015 * s, R)
    elif kind == 2:    # 曲尺
        mb.box(-0.01 * s, -0.005 * s, 0, 0.01 * s, 0.005 * s, 0.006 * s, Wl)
        mb.box(0.004 * s, 0.005 * s, 0, 0.01 * s, 0.014 * s, 0.006 * s, Wl)
        mb.prism([(-0.0065 * s, 0.006 * s), (0.0065 * s, 0.006 * s), (0, 0.0105 * s)], "x", -0.011 * s, 0.011 * s, R)
        mb.prism([(0.003 * s, 0.006 * s), (0.011 * s, 0.006 * s), (0.007 * s, 0.0095 * s)], "y", 0.0065 * s, 0.015 * s, R)
    else:              # 合院（王宅）：四面围合
        for x0, y0, x1, y1 in ((-0.014, -0.012, 0.014, -0.006), (-0.014, 0.006, 0.014, 0.012),
                               (-0.014, -0.006, -0.009, 0.006), (0.009, -0.006, 0.014, 0.006)):
            mb.box(x0 * s, y0 * s, 0, x1 * s, y1 * s, 0.006 * s, Wl)
            mb.box(x0 * s - 0.001, y0 * s - 0.001, 0.006 * s, x1 * s + 0.001, y1 * s + 0.001, 0.0085 * s, R)


def build_sand_house():
    """民居片 20 个（House_01..20）：按布局里的民居位置抽样摆好；House_20 = 王叔杲宅（北墙外，宅院抉择可推进墙内）。"""
    L = _layout()
    def ok(p):
        X, Y = m2t(p["x"], p["z"])
        return abs(X) < HX - 0.03 and SEA_Y + 0.04 < Y < 0.28
    hs = [p for p in L["plots"] if p["kind"] in ("house_s", "house_l", "courtyard", "shop", "hall_small") and ok(p)]
    hs.sort(key=lambda p: (round(p["z"] / 60), p["x"]))
    step = max(1, len(hs) // 19)
    pick = hs[::step][:19]
    for i, p in enumerate(pick):
        kind = {"house_s": 0, "shop": 1, "house_l": 2, "hall_small": 1, "courtyard": 2}[p["kind"]] if i % 5 else 0
        mb = K.MB()
        _house(mb, kind, 1.0 + 0.15 * ((i * 7) % 3))
        X, Y = m2t(p["x"], p["z"])
        ob = obj(mb, f"House_{i + 1:02d}", (X, Y, 0), uv=0.1)
        ob.rotation_euler = (0, 0, math.radians(-p.get("rot", 0)))
    mb = K.MB()
    _house(mb, 3, 1.1)
    X, Y = m2t(*HOUSE20_OUT)
    obj(mb, "House_20", (X, Y, 0), uv=0.1)
    anchor("ANCHOR_House_20_Out", (X, Y, 0), 0.02)        # 「留在墙外」= 原位
    X2, Y2 = m2t(*HOUSE20_IN)
    anchor("ANCHOR_House_20_In", (X2, Y2, 0), 0.02)       # 「圈进墙内」时推到这里（中途抬高约 3 cm 越过北墙）
    X3, Y3 = m2t(HOUSE20_OUT[0] + 3, 185)
    anchor("ANCHOR_House_20_Over", (X3, Y3, 0.03), 0.02)  # 推木片越墙的中间点


def build_sand_flags():
    """小旗 6 / 木签 4 / 麻线 / 米粒 3 堆（排成一排；单件原点在底中心，插入点 = 原点）。返回排到的 x，纸卡接着往后排。"""
    x = -0.2
    for i, mat in enumerate(("M_A2_FlagRed", "M_A2_FlagRed", "M_A2_FlagBlue", "M_A2_FlagBlue", "M_A2_FlagYellow", "M_A2_FlagYellow")):
        mb = K.MB()
        mb.cyl(0, 0, 0, 0.06, 0.0012, "M_A2_MiniWood", seg=4)
        mb.prism([(0.0, 0.058), (0.0, 0.04), (0.022, 0.049)], "y", -0.0004, 0.0004, mat)
        obj(mb, f"Flag_{i + 1:02d}", (x, 0, 0), uv=0.1)
        x += 0.03
    for i in range(4):
        mb = K.MB()
        mb.cyl(0, 0, 0.006, 0.09, 0.0022, "M_A2_MiniWood", seg=5)
        mb.cyl(0, 0, 0, 0.006, 0.0002, "M_A2_MiniWood", seg=5, r_top=0.0022)
        mb.cyl(0, 0, 0.075, 0.08, 0.0028, "M_A2_Twine", seg=5)
        obj(mb, f"Stake_{i + 1:02d}", (x, 0, 0), uv=0.1)
        x += 0.03
    mb = K.MB()
    mb.box(0, -0.0006, -0.0006, 0.1, 0.0006, 0.0006, "M_A2_Twine")
    obj(mb, "Twine", (x, 0, 0.078), uv=0.1)               # 沿 +X 长 0.1 m，原点在一端；缩放 X 拉到两签之间
    x += 0.14
    for i in range(3):
        mb = K.MB()
        for k in range(14):
            a = k * 2.4
            r = 0.003 * math.sqrt(k)
            mb.box(r * math.cos(a) - 0.0008, r * math.sin(a) - 0.0005, 0, r * math.cos(a) + 0.0008, r * math.sin(a) + 0.0005,
                   0.0009 + 0.0004 * (k % 3 == 0), "M_A2_Rice")
        obj(mb, f"Rice_{i + 1:02d}", (x, 0, 0), uv=0.1)
        x += 0.03
    # 议题纸卡 Card_Wall/Tower/Water/House 带贴图，见 rupu_a2_sand.build_cards（PROP_Sand_Flags 的配方在那里包了一层）
    return x


# ====================================================================== 族约碑 / 木牌 / 名录 / 田契 / 图卷
def build_stele():
    """族约碑：须弥座 + 碑身 + 圆首；碑面三块刻字区 Clause_1..3（右起竖排），各有 _Blank / _Carved 两态。"""
    mb = K.MB()
    mb.box(-0.8, -0.45, 0, 0.8, 0.45, 0.12, "M_A2_StoneDark")
    mb.frustum((-0.72, -0.38, 0.72, 0.38), (-0.62, -0.3, 0.62, 0.3), 0.12, 0.3, "M_A2_Stone")
    mb.box(-0.6, -0.28, 0.3, 0.6, 0.28, 0.42, "M_A2_StoneDark")
    mb.frustum((-0.62, -0.3, 0.62, 0.3), (-0.7, -0.36, 0.7, 0.36), 0.42, 0.5, "M_A2_Stone")
    T, Wd, Z0, Z1 = 0.13, 0.5, 0.5, 2.3
    mb.box(-Wd, -T, Z0, Wd, T, Z1, "M_A2_Stone")
    pts = [(-Wd, Z1)] + [(Wd * math.cos(math.pi - math.pi * k / 8), Z1 + 0.32 * math.sin(math.pi * k / 8)) for k in range(1, 8)] + [(Wd, Z1)]
    mb.prism(pts, "y", -T, T, "M_A2_Stone")
    mb.box(-Wd - 0.002, -T - 0.004, Z0 + 0.06, Wd + 0.002, -T, Z0 + 0.09, "M_A2_StoneDark")     # 碑面边框
    mb.box(-Wd - 0.002, -T - 0.004, Z1 - 0.06, Wd + 0.002, -T, Z1 - 0.03, "M_A2_StoneDark")
    for sx in (-1, 1):
        mb.box(sx * (Wd - 0.03) - 0.015, -T - 0.004, Z0 + 0.06, sx * (Wd - 0.03) + 0.015, -T, Z1 - 0.03, "M_A2_StoneDark")
    # 碑额「王氏族约」：四个字块
    for k in range(4):
        x = 0.12 - k * 0.08
        mb.box(x - 0.03, -T - 0.006, Z1 + 0.06, x + 0.03, -T, Z1 + 0.13, "M_A2_Carved")
    # 左侧（读到最后）已刻好的总纲两行
    for col in range(2):
        x = -0.36 + col * 0.07
        for k in range(10):
            mb.box(x - 0.018, -T - 0.003, 1.95 - k * 0.12, x + 0.018, -T, 1.95 - k * 0.12 + 0.07, "M_A2_Carved")
    obj(mb, "Stele", (0, 0, 0), uv=1.0)
    for i in range(3):
        x = 0.33 - i * 0.2
        g = group(f"Clause_{i + 1}", (x, -T, 1.4))
        mb = K.MB()
        mb.box(-0.075, -0.004, -0.75, 0.075, 0.0, 0.75, "M_A2_StoneLight")
        child(obj(mb, f"Clause_{i + 1}_Blank", (x, -T, 1.4), uv=1.0), g)
        mb = K.MB()
        mb.box(-0.075, -0.003, -0.75, 0.075, 0.0, 0.75, "M_A2_Stone")
        for col in range(2):
            cx = 0.035 - col * 0.07
            for k in range(11 - col * 3):
                z = 0.66 - k * 0.13
                mb.box(cx - 0.022, -0.006, z - 0.045, cx + 0.022, -0.002, z + 0.045, "M_A2_Carved")
        child(obj(mb, f"Clause_{i + 1}_Carved", (x, -T, 1.4), uv=1.0), g)
        fx(f"FX_Chisel_{i + 1}", (x, -T - 0.02, 1.4))
    anchor("ANCHOR_Carver", (0.2, -0.75, 0), 0.3)


def _board(mb, ink_cols, L=0.26, Wd=0.085, T=0.014):
    pts = [(-Wd / 2, -L / 2), (Wd / 2, -L / 2), (Wd / 2, L / 2 - 0.02), (Wd / 2 - 0.015, L / 2), (-Wd / 2 + 0.015, L / 2), (-Wd / 2, L / 2 - 0.02)]
    mb.prism(pts, "z", 0, T, "M_A2_Board")
    for c in range(ink_cols):
        x = 0.02 - c * 0.02
        n = 7 - c * 2
        for k in range(n):
            y = 0.08 - k * 0.028
            mb.box(x - 0.006, y - 0.009, T, x + 0.006, y + 0.009, T + 0.0006, "M_A2_Ink")


def build_covenant():
    """族约木牌 10 块（Board_01..10，第 1—5 块一排、6—10 一排，平放；原点在每块底中心）。"""
    for i in range(10):
        mb = K.MB()
        _board(mb, 1 + (i % 3))
        x = -0.24 + (i % 5) * 0.12
        y = 0.0 if i < 5 else 0.3
        obj(mb, f"Board_{i + 1:02d}", (x, y, 0), uv=0.2)
    fx("FX_Ink", (0, 0, 0.03))


def build_roster():
    """义师名录一套：摊开的名录 + 逐行显现的墨行 InkRow_01..12、合上的册、卷、名签、笔、砚、印、印迹。"""
    mb = K.MB()
    for sx in (-1, 1):
        mb.box(min(0, sx * 0.19), -0.13, 0, max(0, sx * 0.19), 0.13, 0.006, "M_A2_Silk")
        mb.box(min(0, sx * 0.183), -0.123, 0.006, max(0, sx * 0.183), 0.123, 0.016 - 0.002 * (sx > 0), "M_A2_PaperOld")
    obj(mb, "Roster_Open", (0, 0, 0), uv=0.2)
    for i in range(12):     # 右页起、右起竖排（读序），每行一个名字
        x = 0.165 - i * 0.029 - (0.012 if i >= 6 else 0)
        mb = K.MB()
        for k in range(3 if i % 4 else 4):
            mb.box(-0.004, -k * 0.026 - 0.009, 0, 0.004, -k * 0.026 + 0.009, 0.0006, "M_A2_Ink")
        obj(mb, f"InkRow_{i + 1:02d}", (x, 0.09, 0.0161 - 0.002 * (x > 0)), uv=0.2)
    mb = K.MB()
    mb.box(-0.13, -0.095, 0, 0.13, 0.095, 0.035, "M_A2_PaperOld")
    mb.box(-0.132, -0.097, 0.035, 0.132, 0.097, 0.04, "M_A2_Silk")
    mb.box(-0.132, -0.097, -0.003, 0.132, 0.097, 0.0, "M_A2_Silk")
    mb.box(-0.11, -0.08, 0.04, -0.08, 0.08, 0.041, "M_A2_Paper")
    obj(mb, "Roster_Closed", (0.38, 0, 0.003), uv=0.2)
    mb = K.MB()
    with mb.at(0, 0, 0.028, ry=90):
        mb.cyl(0, 0, -0.16, 0.16, 0.028, "M_A2_PaperOld", seg=10)
        mb.cyl(0, 0, -0.19, 0.19, 0.008, "M_A2_WoodDark", seg=6)
    mb.box(-0.004, -0.03, 0.04, 0.004, 0.0, 0.058, "M_A2_SealRed")
    obj(mb, "Roster_Scroll", (0, 0.3, 0), uv=0.2)
    mb = K.MB()
    for k in range(6):
        mb.box(-0.025 + (k % 2) * 0.003, -0.07, k * 0.008, 0.025 + (k % 2) * 0.003, 0.07, k * 0.008 + 0.007, "M_A2_WoodLight")
    obj(mb, "NameTag_Stack", (0.38, 0.25, 0), uv=0.2)
    for i in range(4):
        mb = K.MB()
        mb.box(-0.025, -0.07, 0, 0.025, 0.07, 0.007, "M_A2_WoodLight")
        mb.cyl(0, 0.055, 0.007, 0.0075, 0.005, "M_A2_WoodDark", seg=6)
        for k in range(2 if i < 2 else 0):
            mb.box(-0.006, 0.02 - k * 0.03, 0.007, 0.006, 0.035 - k * 0.03, 0.0075, "M_A2_Ink")
        obj(mb, f"NameTag_{i + 1:02d}", (0.5 + i * 0.07, 0.0, 0), uv=0.2)
    mb = K.MB()      # 笔：原点在握笔处，笔杆沿本地 +Z
    mb.cyl(0, 0, -0.06, 0.12, 0.004, "M_A2_Fir", seg=6)
    mb.cyl(0, 0, -0.085, -0.06, 0.001, "M_A2_Ink", seg=6, r_top=0.0045)
    ob = obj(mb, "Brush", (-0.3, 0.05, 0.0045), uv=0.2)
    ob.rotation_euler = (math.radians(-90), 0, 0)
    mb = K.MB()
    mb.box(-0.06, -0.09, 0, 0.06, 0.09, 0.025, "M_A2_StoneDark")
    mb.box(-0.045, -0.04, 0.025, 0.045, 0.07, 0.027, "M_A2_Ink")
    obj(mb, "Inkstone", (-0.3, -0.12, 0), uv=0.2)
    mb = K.MB()      # 印：方印 + 钮
    mb.box(-0.022, -0.022, 0, 0.022, 0.022, 0.045, "M_A2_StoneLight")
    el(mb, (0, 0, 0.055), 0.016, 0.016, 0.014, "M_A2_StoneLight", seg=6, rings=3)
    mb.box(-0.0215, -0.0215, -0.0005, 0.0215, 0.0215, 0.0, "M_A2_SealRed")
    obj(mb, "Seal", (-0.45, 0.1, 0.0005), uv=0.2)
    mb = K.MB()
    mb.box(-0.021, -0.021, 0, 0.021, 0.021, 0.0005, "M_A2_SealRed")
    obj(mb, "Seal_Mark", (-0.08, -0.07, 0.0161), uv=0.2)    # 盖印后显示（左页落款处）


def build_deed():
    """田契：摊开（竖排契文、边框、两方红印）+ 折起两态。"""
    mb = K.MB()
    mb.box(-0.2, -0.15, 0, 0.2, 0.15, 0.002, "M_A2_PaperOld")
    for x0, y0, x1, y1 in ((-0.19, -0.14, 0.19, -0.135), (-0.19, 0.135, 0.19, 0.14), (-0.19, -0.14, -0.185, 0.14), (0.185, -0.14, 0.19, 0.14)):
        mb.box(x0, y0, 0.002, x1, y1, 0.0025, "M_A2_Ink")
    for c in range(9):
        x = 0.16 - c * 0.034
        n = 9 if c not in (0, 8) else 4
        for k in range(n):
            y = 0.11 - k * 0.026
            mb.box(x - 0.006, y - 0.009, 0.002, x + 0.006, y + 0.009, 0.0025, "M_A2_Ink")
    for x, y, s in ((-0.13, -0.08, 0.05), (0.05, -0.1, 0.04)):
        mb.box(x - s / 2, y - s / 2, 0.0025, x + s / 2, y + s / 2, 0.003, "M_A2_SealRed")
    obj(mb, "Deed_Flat", (0, 0, 0), uv=0.2)
    mb = K.MB()
    for k in range(4):
        mb.box(-0.1, -0.075, k * 0.0025, 0.1, 0.075, k * 0.0025 + 0.0022, "M_A2_PaperOld")
    mb.box(-0.02, -0.075, 0.01, 0.02, 0.075, 0.0108, "M_A2_SealRed")
    obj(mb, "Deed_Folded", (0.35, 0, 0), uv=0.2)


def build_blueprint():
    """建堡图卷：卷起 / 展开（城墙轮廓、河道、敌台标记）两态 + 1941 烧残页。"""
    mb = K.MB()
    with mb.at(0, 0, 0.035, ry=90):
        mb.cyl(0, 0, -0.3, 0.3, 0.035, "M_A2_PaperOld", seg=10)
        mb.cyl(0, 0, -0.34, 0.34, 0.012, "M_A2_Lacquer", seg=6)
        mb.cyl(0, 0, 0.32, 0.345, 0.018, "M_A2_Bronze", seg=6)
        mb.cyl(0, 0, -0.345, -0.32, 0.018, "M_A2_Bronze", seg=6)
    mb.box(-0.004, -0.036, 0.0, 0.004, 0.036, 0.072, "M_A2_Silk")
    obj(mb, "Scroll_Rolled", (0, 0.55, 0), uv=0.2)
    mb = K.MB()
    mb.box(-0.3, -0.22, 0, 0.3, 0.22, 0.002, "M_A2_PaperOld")
    for sy in (-1, 1):
        with mb.at(0, sy * 0.23, 0.014, ry=90):
            mb.cyl(0, 0, -0.33, 0.33, 0.014, "M_A2_Lacquer", seg=6)
            mb.cyl(0, 0, 0.31, 0.34, 0.018, "M_A2_Bronze", seg=6)
            mb.cyl(0, 0, -0.34, -0.31, 0.018, "M_A2_Bronze", seg=6)
    # 图：城墙轮廓（细墨线）、上下河、敌台方块、北面官道
    s = 0.0011
    X0, X1, Y0, Y1 = -185 * s, 185 * s, -113 * s, 113 * s
    for a, b in (((X0, Y0), (X1, Y0)), ((X0, Y1), (X1, Y1)), ((X0, Y0), (X0, Y1)), ((X1, Y0), (X1, Y1))):
        mb.box(min(a[0], b[0]) - 0.003, min(a[1], b[1]) - 0.003, 0.002, max(a[0], b[0]) + 0.003, max(a[1], b[1]) + 0.003, 0.0025, "M_A2_Ink")
    for x in (-40, 48):
        mb.box(X0 - 0.02, -x * s - 0.002, 0.002, X1 + 0.01, -x * s + 0.002, 0.0024, "M_A2_FlagBlue")
    for (x, z, _) in list(TOWERS.values()) + [(-72, -185, 0), (80, -185, 0), (-113, -96, 0), (113, -112, 0)]:
        mb.box(z * s - 0.008, -x * s - 0.008, 0.002, z * s + 0.008, -x * s + 0.008, 0.0028, "M_A2_SealRed" if (x, z) in [(113, 112), (-72, 185)] else "M_A2_Ink")
    for c in range(4):
        mb.box(-0.27 + c * 0.012, 0.1, 0.002, -0.265 + c * 0.012, 0.2, 0.0024, "M_A2_Ink")
    obj(mb, "Scroll_Open", (0, 0, 0), uv=0.2)
    mb = K.MB()
    slab(mb, [(-0.09, -0.07), (0.03, -0.08), (0.1, -0.02), (0.07, 0.06), (-0.02, 0.09), (-0.1, 0.03)], 0, 0.0015, "M_A2_PaperOld")
    slab(mb, [(0.03, -0.08), (0.1, -0.02), (0.095, -0.015), (0.03, -0.072)], 0.0015, 0.002, "M_PR_Char")
    mb.box(-0.06, -0.05, 0.0015, 0.05, -0.047, 0.002, "M_A2_Ink")
    mb.box(-0.06, -0.05, 0.0015, -0.057, 0.06, 0.002, "M_A2_Ink")
    obj(mb, "Fragment_1941", (0.5, 0.3, 0), uv=0.2)


# ====================================================================== 筑堡：测绘、脚手架、石料、灰浆、绞盘、车、工具、绳
def build_survey():
    """测绘一组：罗盘、垂准（立杆吊锤）、墨斗、木桩 3、丈杆。"""
    mb = K.MB()
    mb.box(-0.1, -0.1, 0, 0.1, 0.1, 0.025, "M_A2_Lacquer")
    mb.cyl(0, 0, 0.025, 0.035, 0.085, "M_A2_Bronze", seg=12)
    mb.cyl(0, 0, 0.035, 0.037, 0.06, "M_A2_Paper", seg=12)
    mb.box(-0.002, -0.04, 0.037, 0.002, 0.04, 0.04, "M_A2_SealRed")
    for k in range(8):       # 盘面刻度
        a = k * math.pi / 4
        mb.box(0.07 * math.cos(a) - 0.004, 0.07 * math.sin(a) - 0.004, 0.035, 0.07 * math.cos(a) + 0.004, 0.07 * math.sin(a) + 0.004, 0.038, "M_A2_Ink")
    obj(mb, "Compass", (0, 0, 0), uv=0.2)
    mb = K.MB()
    mb.cyl(0, 0, 0, 1.3, 0.02, "M_A2_Fir", seg=6, r_top=0.018)
    mb.box(-0.01, -0.3, 1.25, 0.01, 0.0, 1.28, "M_A2_Fir")
    tb(mb, (0, -0.28, 1.25), (0, -0.28, 0.35), 0.002, "M_A2_Twine", seg=4)
    mb.cyl(0, -0.28, 0.27, 0.35, 0.02, "M_A2_Bronze", seg=8, r_top=0.004)
    obj(mb, "Plumb", (0.4, 0, 0), uv=0.3)
    mb = K.MB()      # 墨斗
    mb.box(-0.06, -0.12, 0, 0.06, 0.12, 0.06, "M_A2_WoodDark")
    with mb.at(0, 0.04, 0.05, ry=90):
        mb.cyl(0, 0, -0.065, 0.065, 0.045, "M_A2_Wood", seg=10)
    mb.box(-0.025, -0.11, 0.06, 0.025, -0.04, 0.075, "M_A2_Ink")
    obj(mb, "LineReel", (0.8, 0, 0), uv=0.2)
    for i in range(3):
        mb = K.MB()
        mb.cyl(0, 0, 0.12, 0.6, 0.035, "M_A2_Fir", seg=6)
        mb.cyl(0, 0, 0, 0.12, 0.004, "M_A2_Fir", seg=6, r_top=0.035)
        mb.cyl(0, 0, 0.55, 0.6, 0.038, "M_A2_SealRed", seg=6)
        obj(mb, f"Stake_{i + 1:02d}", (1.1 + i * 0.2, 0, 0), uv=0.3)
    mb = K.MB()      # 丈杆：一丈（约 3.2 m）方杆，每尺一道墨，平放
    mb.box(-1.6, -0.02, 0, 1.6, 0.02, 0.04, "M_A2_WoodLight")
    for k in range(11):
        x = -1.6 + k * 0.32
        mb.box(x - 0.004, -0.0205, 0.0, x + 0.004, 0.0205, 0.0405, "M_A2_Ink")
    obj(mb, "MeasurePole", (0.6, 0.6, 0), uv=0.3)


def build_scaffold():
    """杉木脚手架：标准段（2 m 宽 1.1 m 深 2 m 一层，可上下左右拼）、转角段、梯（单独子物体，原点在底）。"""
    R = 0.05

    def lash(mb, p):
        mb.cyl(p[0], p[1], p[2] - 0.05, p[2] + 0.05, R + 0.012, "M_A2_Lashing", seg=6)

    def bay(mb, posts, ledgers, deck):
        for x, y in posts:
            tb(mb, (x, y, 0), (x, y, 2.35), R, "M_A2_Fir", seg=6, r1=R * 0.8)
        for a, b, z in ledgers:
            tb(mb, (a[0], a[1], z), (b[0], b[1], z), R * 0.75, "M_A2_Fir", seg=5)
            lash(mb, (a[0], a[1], z))
            lash(mb, (b[0], b[1], z))
        for x0, y0, x1, y1 in deck:
            n = max(2, int(abs(x1 - x0) / 0.26) if abs(x1 - x0) > abs(y1 - y0) else int(abs(y1 - y0) / 0.26))
            for k in range(n):
                if abs(x1 - x0) > abs(y1 - y0):
                    yy0 = y0 + (y1 - y0) * k / n
                    mb.box(x0, yy0 + 0.01, 2.0, x1, yy0 + (y1 - y0) / n - 0.01, 2.04, "M_A2_WoodLight")
                else:
                    xx0 = x0 + (x1 - x0) * k / n
                    mb.box(xx0 + 0.01, y0, 2.0, xx0 + (x1 - x0) / n - 0.01, y1, 2.04, "M_A2_WoodLight")

    # 标准段：沿 X 2 m，靠墙一侧 +Y
    mb = K.MB()
    P = [(-1.0, -0.55), (1.0, -0.55), (-1.0, 0.55), (1.0, 0.55)]
    led = []
    for z in (1.0, 1.96):
        led += [((-1.0, -0.55), (1.0, -0.55), z), ((-1.0, 0.55), (1.0, 0.55), z), ((-1.0, -0.55), (-1.0, 0.55), z), ((1.0, -0.55), (1.0, 0.55), z)]
    bay(mb, P, led, [(-1.05, -0.6, 1.05, 0.6)])
    tb(mb, (-1.0, -0.55, 0.1), (1.0, -0.55, 1.9), R * 0.6, "M_A2_Fir", seg=5)        # 外侧斜撑
    tb(mb, (-1.0, -0.55, 2.3), (1.0, -0.55, 2.3), R * 0.6, "M_A2_Fir", seg=5)       # 护身栏
    obj(mb, "Bay_Standard", (0, 0, 0), uv=0.5)
    # 转角段：1.1 × 1.1，绕城墙阳角（墙角在 +X+Y）
    mb = K.MB()
    P = [(-0.55, -0.55), (0.55, -0.55), (-0.55, 0.55)]
    led = []
    for z in (1.0, 1.96):
        led += [((-0.55, -0.55), (0.55, -0.55), z), ((-0.55, -0.55), (-0.55, 0.55), z)]
    bay(mb, P, led, [(-0.6, -0.6, 0.6, 0.0), (-0.6, 0.0, 0.0, 0.6)])
    tb(mb, (-0.55, -0.55, 2.3), (0.55, -0.55, 2.3), R * 0.6, "M_A2_Fir", seg=5)
    tb(mb, (-0.55, -0.55, 2.3), (-0.55, 0.55, 2.3), R * 0.6, "M_A2_Fir", seg=5)
    obj(mb, "Bay_Corner", (2.0, 0, 0), uv=0.5)
    # 梯：3 m，两根边杆 + 横档（竖放，靠在标准段外侧时倾斜 15°）
    mb = K.MB()
    for sx in (-1, 1):
        tb(mb, (sx * 0.22, 0, 0), (sx * 0.2, 0, 3.0), 0.035, "M_A2_Fir", seg=5)
    for k in range(10):
        z = 0.25 + k * 0.28
        tb(mb, (-0.22, 0, z), (0.22, 0, z), 0.02, "M_A2_Fir", seg=4)
    ob = obj(mb, "Ladder", (3.2, 0, 0), uv=0.5)
    ob.rotation_euler = (math.radians(-12), 0, 0)
    anchor("ANCHOR_Climb", (3.2, -0.4, 0), 0.3)


def build_stone(size, chisel=3):
    """料石：倒角方块 + 面上錾纹 + 两侧绳槽。"""
    sx, sy, sz = size
    c = 0.025
    mb = K.MB()
    mb.box(-sx / 2, -sy / 2, c, sx / 2, sy / 2, sz - c, "M_A2_Stone")
    mb.frustum((-sx / 2, -sy / 2, sx / 2, sy / 2), (-sx / 2 + c, -sy / 2 + c, sx / 2 - c, sy / 2 - c), sz - c, sz, "M_A2_StoneLight")
    mb.frustum((-sx / 2 + c, -sy / 2 + c, sx / 2 - c, sy / 2 - c), (-sx / 2, -sy / 2, sx / 2, sy / 2), 0, c, "M_A2_Stone")
    for k in range(chisel):
        x = -sx / 2 + (k + 1) * sx / (chisel + 1)
        mb.box(x - 0.004, -sy / 2 - 0.003, c + 0.02, x + 0.004, -sy / 2, sz - c - 0.02, "M_A2_StoneDark")
    for sxx in (-1, 1):        # 绳槽
        x = sxx * sx * 0.3
        mb.box(x - 0.015, -sy / 2 - 0.002, sz - 0.004, x + 0.015, sy / 2 + 0.002, sz + 0.0, "M_A2_StoneDark")
    return mb


def build_stone_s():
    obj(build_stone((0.4, 0.25, 0.2), 2), "PROP_StoneBlock_S")


def build_stone_m():
    obj(build_stone((0.7, 0.35, 0.3), 3), "PROP_StoneBlock_M")


def build_stone_l():
    obj(build_stone((1.1, 0.5, 0.45), 5), "PROP_StoneBlock_L")


def build_mortar():
    """灰浆一组：木桶（铁箍、绳提手、灰浆面）、拌灰槽、抹子（原点在握柄）。"""
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.42, 0.2, "M_A2_Wood", seg=12, r_top=0.23)
    for z in (0.08, 0.34):
        mb.cyl(0, 0, z, z + 0.03, 0.21 + z * 0.07, "M_A2_Iron", seg=12)
    mb.cyl(0, 0, 0.36, 0.38, 0.215, "M_A2_Mortar", seg=12)
    for sx in (-1, 1):
        tb(mb, (sx * 0.22, 0, 0.4), (sx * 0.08, 0, 0.62), 0.01, "M_A2_Rope", seg=4)
    tb(mb, (-0.08, 0, 0.62), (0.08, 0, 0.62), 0.01, "M_A2_Rope", seg=4)
    obj(mb, "Bucket", (0, 0, 0), uv=0.3)
    mb = K.MB()
    mb.frustum((-0.6, -0.18, 0.6, 0.18), (-0.65, -0.24, 0.65, 0.24), 0.05, 0.3, "M_A2_Wood")
    mb.box(-0.6, -0.2, 0.26, 0.6, 0.2, 0.28, "M_A2_Mortar")
    for x in (-0.5, 0.5):
        mb.box(x - 0.05, -0.2, 0, x + 0.05, 0.2, 0.05, "M_A2_WoodDark")
    obj(mb, "Trough", (0.9, 0, 0), uv=0.3)
    mb = K.MB()
    mb.box(-0.06, -0.13, 0, 0.06, 0.05, 0.006, "M_A2_Iron")
    tb(mb, (0, 0.0, 0.006), (0, 0.0, 0.06), 0.006, "M_A2_Iron", seg=4)
    tb(mb, (0, -0.08, 0.06), (0, 0.06, 0.06), 0.014, "M_A2_Wood", seg=6)
    obj(mb, "Trowel", (0.0, -0.45, 0), uv=0.3)
    fx("FX_Splash", (0.9, 0, 0.32))


def build_winch():
    """绞盘吊架：三脚杉木架 + 顶滑轮 + 地面绞车；Drum 绕本地 X 转（原点在轴心），Hook 上下（原点在钩顶），Rope_Hang 按 Z 缩放。"""
    mb = K.MB()
    top = V((0, 0.0, 4.0))
    for a in (90, 210, 330):
        p = V((1.3 * math.cos(math.radians(a)), 1.3 * math.sin(math.radians(a)), 0))
        tb(mb, p, top + V((0, 0, 0.15)), 0.07, "M_A2_Fir", seg=6, r1=0.055)
    mb.cyl(0, 0, 3.85, 4.15, 0.12, "M_A2_Lashing", seg=8)
    with mb.at(0, 0, 3.8, ry=90):
        mb.cyl(0, 0, -0.03, 0.03, 0.12, "M_A2_WoodDark", seg=10)
    # 绞车架（在 -Y 一侧，朝玩家）
    for sx in (-1, 1):
        mb.box(sx * 0.55 - 0.06, -1.55, 0, sx * 0.55 + 0.06, -1.25, 0.85, "M_A2_WoodDark")
        mb.box(sx * 0.55 - 0.06, -1.9, 0, sx * 0.55 + 0.06, -0.9, 0.1, "M_A2_WoodDark")
    tb(mb, (0, -1.4, 0.7), (0, 0.0, 3.8), 0.012, "M_A2_Rope", seg=4)      # 绞车到滑轮的绳
    obj(mb, "Frame", (0, 0, 0), uv=0.5)
    mb = K.MB()
    with mb.at(0, 0, 0, ry=90):
        mb.cyl(0, 0, -0.5, 0.5, 0.1, "M_A2_Wood", seg=10)
        mb.cyl(0, 0, -0.62, 0.62, 0.035, "M_A2_Iron", seg=6)
        mb.cyl(0, 0, -0.2, 0.2, 0.115, "M_A2_Rope", seg=10)
    for k in range(4):
        a = k * math.pi / 2
        for sx in (-1, 1):
            tb(mb, (sx * 0.45, 0, 0), (sx * 0.45, 0.55 * math.cos(a), 0.55 * math.sin(a)), 0.025, "M_A2_Wood", seg=4)
    obj(mb, "Drum", (0, -1.4, 0.7), uv=0.5)
    mb = K.MB()
    mb.box(-0.002, -0.002, -1.0, 0.002, 0.002, 0.0, "M_A2_Rope")
    mb.box(-0.012, -0.012, -1.0, 0.012, 0.012, 0.0, "M_A2_Rope")
    obj(mb, "Rope_Hang", (0.12, 0, 3.8), uv=0.5)         # 长 1 m 往下，缩放 Z = 吊绳长度
    mb = K.MB()
    mb.cyl(0, 0, -0.1, 0.0, 0.03, "M_A2_Iron", seg=6)
    tb(mb, (0, 0, -0.1), (0, 0, -0.25), 0.015, "M_A2_Iron", seg=4)
    tb(mb, (0, 0, -0.25), (0.08, 0, -0.3), 0.015, "M_A2_Iron", seg=4)
    tb(mb, (0.08, 0, -0.3), (0.1, 0, -0.2), 0.015, "M_A2_Iron", seg=4)
    obj(mb, "Hook", (0.12, 0, 1.2), uv=0.5)
    anchor("ANCHOR_Crank", (0.85, -1.4, 0), 0.3)
    anchor("ANCHOR_Load", (0.12, 0, 0), 0.3)


def build_wheelbarrow():
    """独轮车：中置大轮 + 两侧载货架 + 后把手（朝 +Y），轮罩；Wheel 子物体绕本地 X 转（原点在轴）。"""
    mb = K.MB()
    for sx in (-1, 1):
        tb(mb, (sx * 0.18, -0.65, 0.45), (sx * 0.28, 0.95, 0.62), 0.03, "M_A2_Wood", seg=5)    # 车辕 → 把手
        mb.box(sx * 0.1, -0.45, 0.46, sx * 0.5, 0.45, 0.5, "M_A2_WoodLight")                 # 载货板
        mb.box(sx * 0.48, -0.45, 0.46, sx * 0.5, 0.45, 0.6, "M_A2_Wood")
        tb(mb, (sx * 0.24, 0.6, 0.55), (sx * 0.24, 0.6, 0.0), 0.025, "M_A2_Wood", seg=4)       # 后支腿
    for sx in (-1, 1):       # 轮罩：两片侧板 + 顶上三根横档（轮子从中间露出）
        mb.prism([(-0.46, 0.46), (0.46, 0.46), (0.3, 0.82), (-0.3, 0.82)], "x", sx * 0.05 - 0.008, sx * 0.05 + 0.008, "M_A2_WoodDark")
    for y in (-0.25, 0.0, 0.25):
        mb.box(-0.06, y - 0.02, 0.82, 0.06, y + 0.02, 0.85, "M_A2_Wood")
    mb.box(-0.2, -0.66, 0.4, 0.2, -0.6, 0.5, "M_A2_Wood")
    obj(mb, "Body", (0, 0, 0), uv=0.5)
    mb = K.MB()
    wheel(mb, 0.38, 0.06, "M_A2_Wood", "M_A2_WoodDark", spokes=8)
    obj(mb, "Wheel", (0, 0, 0.38), uv=0.5)
    anchor("ANCHOR_Push", (0, 1.1, 0), 0.3)


def build_flatcart():
    """板车：平板 + 两轮 + 前车辕（朝 -Y，拉车）；Wheel_L / Wheel_R 绕本地 X 转。"""
    mb = K.MB()
    mb.box(-0.55, -0.9, 0.5, 0.55, 0.9, 0.56, "M_A2_WoodLight")
    for sx in (-1, 1):
        mb.box(sx * 0.55 - 0.04 * (sx > 0), -0.9, 0.56, sx * 0.55 + 0.04 * (sx < 0), 0.9, 0.66, "M_A2_Wood")
        tb(mb, (sx * 0.35, -0.6, 0.5), (sx * 0.28, -2.1, 0.55), 0.035, "M_A2_Wood", seg=5)
        mb.box(sx * 0.62 - 0.03, -0.12, 0.42, sx * 0.62 + 0.03, 0.12, 0.5, "M_A2_WoodDark")
    tb(mb, (-0.3, -1.9, 0.55), (0.3, -1.9, 0.55), 0.025, "M_A2_Wood", seg=4)
    tb(mb, (0, 0.85, 0.5), (0, 1.0, 0.0), 0.03, "M_A2_Wood", seg=4)
    obj(mb, "Bed", (0, 0, 0), uv=0.5)
    for nm, sx in (("Wheel_L", 1), ("Wheel_R", -1)):
        mb = K.MB()
        wheel(mb, 0.45, 0.07, "M_A2_Wood", "M_A2_WoodDark", spokes=10)
        obj(mb, nm, (sx * 0.7, 0, 0.45), uv=0.5)
    anchor("ANCHOR_Pull", (0, -2.3, 0), 0.3)


def build_tools():
    """工具一组：凿、锤、锯、夯、铁锹、木槌。每件原点在握点、沿本地 +Z（团结 +Y）；平放在地上展示。"""
    T = []
    mb = K.MB()       # 凿（錾）：八棱铁杆，尖头朝 -Z
    mb.cyl(0, 0, -0.12, 0.12, 0.012, "M_A2_Iron", seg=8)
    mb.cyl(0, 0, -0.17, -0.12, 0.002, "M_A2_Iron", seg=8, r_top=0.012)
    T.append(("Chisel", mb, 0.013))
    mb = K.MB()       # 手锤
    mb.cyl(0, 0, -0.1, 0.22, 0.014, "M_A2_Wood", seg=6)
    mb.box(-0.06, -0.025, 0.2, 0.06, 0.025, 0.25, "M_A2_Iron")
    T.append(("Hammer", mb, 0.06))
    mb = K.MB()       # 框锯：H 形木框 + 锯条 + 绞绳
    for sx in (-1, 1):
        mb.box(sx * 0.3 - 0.015, -0.012, -0.05, sx * 0.3 + 0.015, 0.012, 0.35, "M_A2_Wood")
    mb.box(-0.3, -0.012, 0.13, 0.3, 0.012, 0.16, "M_A2_Wood")
    mb.box(-0.3, -0.002, -0.03, 0.3, 0.002, 0.0, "M_A2_Iron")
    tb(mb, (-0.3, 0, 0.33), (0.3, 0, 0.33), 0.006, "M_A2_Rope", seg=4)
    T.append(("Saw", mb, 0.015))
    mb = K.MB()       # 夯：木杵（下端粗墩）+ 两根横把
    mb.cyl(0, 0, -0.9, -0.6, 0.11, "M_A2_WoodDark", seg=8, r_top=0.08)
    mb.cyl(0, 0, -0.6, 0.45, 0.035, "M_A2_Wood", seg=6)
    tb(mb, (-0.22, 0, 0.0), (0.22, 0, 0.0), 0.02, "M_A2_Wood", seg=4)
    T.append(("Rammer", mb, 0.11))
    mb = K.MB()       # 铁锹
    mb.cyl(0, 0, -0.75, 0.45, 0.018, "M_A2_Wood", seg=6)
    mb.box(-0.12, -0.012, -1.05, 0.12, 0.012, -0.75, "M_A2_Iron")
    mb.box(-0.06, -0.01, 0.45, 0.06, 0.01, 0.48, "M_A2_Wood")
    T.append(("Shovel", mb, 0.12))
    mb = K.MB()       # 木槌
    mb.cyl(0, 0, -0.1, 0.25, 0.016, "M_A2_Wood", seg=6)
    with mb.at(0, 0, 0.29, ry=90):
        mb.cyl(0, 0, -0.1, 0.1, 0.06, "M_A2_WoodDark", seg=8)
    T.append(("Mallet", mb, 0.06))
    x = -0.9
    for nm, mb, r in T:
        ob = obj(mb, nm, (x, 0, r), uv=0.3)
        ob.rotation_euler = (math.radians(-90), 0, 0)
        x += 0.35


def _rope_path(mb, pts, r, mat, seg=4):
    for a, b in zip(pts, pts[1:]):
        tb(mb, a, b, r, mat, seg=seg)


def build_rope():
    """绳索一组：绳卷、拉绳（4 m，原点在一端，沿 +X）、吊索（兜住料石的双股吊索 + 顶环，原点在底）。"""
    mb = K.MB()
    for k in range(5):
        rr = 0.22 - (k % 2) * 0.03
        z = 0.025 + k * 0.035
        pts = [(rr * math.cos(2 * math.pi * i / 10), rr * math.sin(2 * math.pi * i / 10), z) for i in range(11)]
        _rope_path(mb, pts, 0.02, "M_A2_Rope", seg=4)
    obj(mb, "Coil", (0, 0, 0), uv=0.3)
    mb = K.MB()
    pts = [(4.0 * i / 12, 0.06 * math.sin(i * 1.3), 0.02) for i in range(13)]
    _rope_path(mb, pts, 0.018, "M_A2_Rope", seg=4)
    obj(mb, "PullRope", (0.5, 0, 0), uv=0.3)
    mb = K.MB()
    for sy in (-0.2, 0.2):
        _rope_path(mb, [(0, sy, 1.0), (-0.38, sy, 0.48), (-0.38, sy, 0.02), (0.38, sy, 0.02), (0.38, sy, 0.48), (0, sy, 1.0)], 0.018, "M_A2_Rope")
    with mb.at(0, 0, 1.05, rx=90):
        for i in range(8):
            a0, a1 = 2 * math.pi * i / 8, 2 * math.pi * (i + 1) / 8
            tb(mb, (0.06 * math.cos(a0), 0.06 * math.sin(a0), 0), (0.06 * math.cos(a1), 0.06 * math.sin(a1), 0), 0.012, "M_A2_Iron", seg=4)
    _rope_path(mb, [(0, -0.2, 1.0), (0, 0, 1.0), (0, 0.2, 1.0)], 0.018, "M_A2_Rope")
    obj(mb, "Sling", (-0.9, 0, 0), uv=0.3)


# ====================================================================== 第二幕动作（Humanoid 共用，GESTURE_HOOKS）
# 写法同 rupu_char.gesture_keys：_pose(L/R=(前抬, 外张), LF/RF=屈肘, 骨骼=矩阵)；_legs(P, 大腿前抬, 小腿后屈, 脚)；
# 第三项是髋高偏移（m，按 1.75 m 人）。桌面类动作按桌高 0.8—0.86 m（沙盘、供桌）摆手。
_X = lambda a: C._rot("X", a)
_Z = lambda a: C._rot("Z", a)
_Y = lambda a: C._rot("Y", a)
P_ = C._pose
LG = C._legs


def _stagger(P, front=25, front_shin=15, back=-15, back_shin=8, side_front="Left"):
    """前后弓步。"""
    other = "Right" if side_front == "Left" else "Left"
    LG(P, front, front_shin, -(front - front_shin) * 0.5, side_front)
    LG(P, back, back_shin, 5, other)
    return P


def g_spear_stamp():
    """王沛枪顿地：右手握竖枪在身侧，提起→顿下，三下，短（第 9/19/29 帧落地）。"""
    hold = dict(R=(22, 14), RF=72, Chest=_X(-3), Head=_X(-2))
    up = dict(R=(30, 10), RF=84, Chest=_X(-3), Head=_X(-4))
    down = lambda: (LG(P_(R=(14, 14), RF=58, Spine=_X(4), Head=_X(6)), 8, 12, -4), -0.015)
    keys = [(0, P_(**hold), 0)]
    for f in (4, 14, 24):
        keys.append((f, P_(**up), 0))
        P, up_ = down()
        keys.append((f + 5, P, up_))
    keys.append((44, P_(**hold), 0))
    return 44, keys


def g_point_line():
    """王沛指墙线：右臂平伸指远处，沿墙线从右扫到左，头跟着转，收手。"""
    return 64, [(0, C._base(), 0),
                (12, P_(R=(82, 42), RF=6, Neck=_Z(-18), Head=_X(-4), Chest=_Z(-6)), 0),
                (20, P_(R=(84, 40), RF=4, Neck=_Z(-18), Head=_X(-4), Chest=_Z(-6)), 0),
                (42, P_(R=(86, -4), RF=4, Neck=_Z(6), Head=_X(-4), Chest=_Z(6)), 0),
                (52, P_(R=(84, -6), RF=6, Neck=_Z(6), Head=_X(-2), Chest=_Z(6)), 0),
                (64, C._base(), 0)]


def g_kneel_die():
    """王沛跪死：中矢后仰一顿 → 右手拄枪单膝、再双膝跪地，头垂下，不倒，停在最后一帧。"""
    return 56, [(0, P_(R=(22, 14), RF=72), 0),
                (5, P_(R=(30, 20), RF=60, Spine=_X(-12), Chest=_X(-6), Head=_X(-10), L=(25, 20), LF=40), 0),
                (14, LG(LG(P_(R=(30, 14), RF=70, Spine=_X(10), Head=_X(10), L=(10, 10), LF=30), 60, 75, -15, "Left"),
                        5, 90, 55, "Right"), -0.3),
                (28, LG(P_(R=(30, 12), RF=78, Spine=_X(14), Chest=_X(6), Head=_X(22), L=(4, 6), LF=12), 0, 90, 60), -0.45),
                (56, LG(P_(R=(28, 12), RF=78, Spine=_X(18), Chest=_X(8), Head=_X(32), L=(2, 4), LF=10), 0, 90, 60), -0.46)]


def g_slam_deed():
    """王叔杲拍田契：右手举到肩前 → 前倾一掌拍在桌上，按住半秒，起身。"""
    return 40, [(0, C._base(), 0),
                (8, P_(R=(95, 15), RF=105, Spine=_X(4), Head=_X(-4)), 0),
                (12, P_(R=(52, 4), RF=12, Spine=_X(20), Chest=_X(10), Head=_X(14), L=(10, 8), LF=20), -0.03),
                (24, P_(R=(52, 4), RF=12, Spine=_X(20), Chest=_X(10), Head=_X(4), L=(10, 8), LF=20), -0.03),
                (40, C._base(), 0)]


def g_abacus():
    """王叔杲拨算盘：左手托盘、右手在盘上拨三下，停（第 10/18/26 帧拨）。"""
    base = dict(L=(36, -18), LF=62, Spine=_X(14), Head=_X(20))
    keys = [(0, C._base(), 0), (6, P_(**base, R=(44, -12), RF=74), 0)]
    for f in (10, 18, 26):
        keys += [(f, P_(**base, R=(46, -16), RF=86), 0), (f + 4, P_(**base, R=(44, -10), RF=72), 0)]
    keys += [(48, P_(**{**base, "Head": _X(10)}, R=(40, -8), RF=70), 0)]
    return 48, keys


def g_unroll():
    """王叔杲展开图卷：双手在身前桌上并拢 → 向两边推开，停在展开姿势。"""
    return 40, [(0, C._base(), 0),
                (10, P_(L=(50, -26), LF=62, R=(50, -26), RF=62, Spine=_X(18), Head=_X(16)), -0.02),
                (28, P_(L=(52, 22), LF=22, R=(52, 22), RF=22, Spine=_X(22), Head=_X(18)), -0.02),
                (40, P_(L=(48, 24), LF=26, R=(48, 24), RF=26, Spine=_X(18), Head=_X(10)), -0.02)]


def g_close_gap():
    """王德合龙：弓步、双手抵住最后一块（门扇/石）往前推合，较劲三下，最后一推到位后站直。"""
    push = lambda d, sp: _stagger(P_(L=(82 + d, -6), LF=24 - d, R=(82 + d, -6), RF=24 - d, Spine=_X(sp), Chest=_X(8), Head=_X(-8)),
                                  35, 30, -25, 6)
    return 64, [(0, C._base(), 0),
                (10, push(0, 22), -0.08),
                (18, push(4, 26), -0.1),
                (26, push(-2, 24), -0.08),
                (34, push(6, 28), -0.1),
                (44, push(12, 30), -0.11),
                (52, push(12, 30), -0.11),
                (64, P_(L=(20, 4), LF=20, R=(20, 4), RF=20, Chest=_X(-4), Head=_X(-6)), 0)]


def g_hand_tag():
    """王德递腰牌：右手到左胯摘牌 → 双手（右手为主）递向前，微低头，停住。"""
    return 40, [(0, C._base(), 0),
                (10, P_(R=(22, -34), RF=68, Spine=_Z(-8), Head=_X(14)), 0),
                (24, P_(R=(72, 6), RF=14, L=(55, -10), LF=40, Spine=_X(10), Head=_X(10)), 0),
                (40, P_(R=(74, 6), RF=12, L=(58, -12), LF=38, Spine=_X(14), Head=_X(16)), 0)]


def g_fall_dead():
    """王德倒地：中刀一顿 → 跪倒 → 向前扑倒趴在地上，停住（整身绕髋前倾，髋落到 0.13 m）。"""
    lie = LG(P_(Hips=_X(84), Spine=_X(2), Head=_X(-30), Neck=_Z(20), L=(150, 30), LF=30, R=(120, 40), RF=40), 0, 8, 30)
    return 40, [(0, P_(Hips=_X(0)), 0),
                (5, P_(Hips=_X(0), Spine=_X(-14), Chest=_X(-6), Head=_X(-12), L=(30, 18), LF=50, R=(40, 10), RF=70), 0),
                (16, LG(P_(Hips=_X(0), Spine=_X(20), Chest=_X(10), Head=_X(20), L=(30, 10), LF=30, R=(40, 0), RF=50), 0, 90, 55), -0.45),
                (26, LG(P_(Hips=_X(45), Spine=_X(10), Head=_X(-10), L=(90, 20), LF=20, R=(90, 20), RF=20), 0, 40, 30), -0.58),
                (34, lie, -0.79),
                (40, lie, -0.79)]


def g_plant_stake():
    """王砚插木签/插小旗：俯身右手举签 → 一下插进沙里，手停一下再收回。"""
    return 36, [(0, C._base(), 0),
                (10, P_(R=(96, 4), RF=70, L=(30, 10), LF=40, Spine=_X(14), Head=_X(20)), 0),
                (16, P_(R=(60, -4), RF=8, L=(30, 10), LF=40, Spine=_X(28), Chest=_X(8), Head=_X(24)), -0.03),
                (24, P_(R=(60, -4), RF=8, L=(30, 10), LF=40, Spine=_X(28), Chest=_X(8), Head=_X(24)), -0.03),
                (36, C._base(), 0)]


def g_pull_string():
    """王砚拉麻线：俯身捏住签上的线头 → 沿桌面往右拉出一条线，头跟着看，收手。"""
    return 48, [(0, C._base(), 0),
                (8, P_(R=(58, -16), RF=46, L=(40, 6), LF=40, Spine=_X(22), Head=_X(22)), -0.02),
                (30, P_(R=(46, 50), RF=14, L=(40, 6), LF=40, Spine=_X(20) @ _Z(-10), Neck=_Z(-22), Head=_X(20)), -0.02),
                (38, P_(R=(46, 52), RF=12, L=(40, 6), LF=40, Spine=_X(20) @ _Z(-10), Neck=_Z(-22), Head=_X(16)), -0.02),
                (48, C._base(), 0)]


def _step_cycle(T, upper, lean_hips=-0.04, stride=26):
    """原地迈步循环（推/抬/拉车用）：upper(t) 返回 _pose 参数。"""
    keys = []
    for i, ph in enumerate((0.0, 0.25, 0.5, 0.75, 1.0)):
        P = P_(**upper(ph))
        a = "Left" if ph in (0.0, 0.25, 1.0) else "Right"
        b = "Right" if a == "Left" else "Left"
        if ph in (0.0, 0.5, 1.0):
            LG(P, stride, 18, -6, a)
            LG(P, -stride * 0.6, 10, 8, b)
        else:
            LG(P, stride * 0.3, 8, -2, a)
            LG(P, stride * 0.2, 50, 10, b)
        keys.append((round(ph * T), P, lean_hips - (0.0 if ph in (0.25, 0.75) else 0.02)))
    return T, keys


def g_push_loop():
    """推（王砚推石入闸、群众推车/推石）：前倾、双手低前方抵住，原地迈步。"""
    return _step_cycle(28, lambda t: dict(L=(62, -4), LF=28, R=(62, -4), RF=28, Spine=_X(28), Chest=_X(6), Head=_X(-14)), -0.06, 28)


def g_carry_loop():
    """抬石（双手捧石在腹前、身子后仰）原地走。"""
    return _step_cycle(32, lambda t: dict(L=(24, -10), LF=62, R=(24, -10), RF=62, Spine=_X(-8), Chest=_X(-4), Head=_X(4)), -0.03, 18)


def g_load_cannon():
    """王砚装炮：半蹲，双手横握送弹杆往炮口里捅两下，抽回。"""
    base = lambda lf, rf, l, r, sp: _stagger(P_(L=(l, -12), LF=lf, R=(r, -18), RF=rf, Spine=_X(sp), Head=_X(4)), 30, 30, -15, 15)
    return 48, [(0, C._base(), 0),
                (8, base(70, 90, 60, 50, 10), -0.06),
                (16, base(10, 30, 86, 80, 22), -0.1),
                (24, base(70, 90, 60, 50, 10), -0.06),
                (32, base(10, 30, 86, 80, 22), -0.1),
                (48, C._base(), 0)]


def g_chisel_loop():
    """凿碑/凿石：左手在胸前扶錾、右手抡锤敲下（第 10 帧落锤）。"""
    hold = dict(L=(70, -16), LF=74, Head=_X(12), Spine=_X(8))
    return 16, [(0, P_(**hold, R=(108, 24), RF=96), 0),
                (6, P_(**hold, R=(118, 20), RF=104), 0),
                (10, P_(**hold, R=(66, -10), RF=62, Chest=_X(4)), -0.01),
                (16, P_(**hold, R=(108, 24), RF=96), 0)]


def g_write_loop():
    """写名：俯身在桌前，左手按纸、右手执笔小幅运笔（竖排，一笔一笔往下）。"""
    b = dict(L=(40, -6), LF=48, Spine=_X(26), Chest=_X(10), Head=_X(22))
    return 48, [(0, P_(**b, R=(46, -10), RF=70), -0.03),
                (10, P_(**b, R=(44, -8), RF=76), -0.03),
                (20, P_(**b, R=(47, -12), RF=66), -0.03),
                (30, P_(**b, R=(44, -7), RF=78), -0.03),
                (40, P_(**b, R=(46, -11), RF=68), -0.03),
                (48, P_(**b, R=(46, -10), RF=70), -0.03)]


def g_stamp():
    """盖印：左手按住册页，右手提印 → 用力按下（停半秒）→ 提起回站。"""
    b = dict(L=(40, -6), LF=48, Head=_X(22))
    return 40, [(0, C._base(), 0),
                (8, P_(**b, R=(62, -6), RF=100, Spine=_X(14)), 0),
                (14, P_(**b, R=(46, -6), RF=40, Spine=_X(24), Chest=_X(8)), -0.04),
                (26, P_(**b, R=(46, -6), RF=40, Spine=_X(24), Chest=_X(8)), -0.04),
                (32, P_(**b, R=(60, -6), RF=96, Spine=_X(14)), 0),
                (40, C._base(), 0)]


def g_ram_loop():
    """夯土：双手握夯杵在胸前 → 举起 → 屈膝砸下（第 14 帧落夯）。"""
    up = LG(P_(L=(104, -22), LF=64, R=(104, -22), RF=64, Spine=_X(-4), Head=_X(-6)), 0, 0, 0)
    down = LG(P_(L=(36, -22), LF=62, R=(36, -22), RF=62, Spine=_X(18), Chest=_X(6), Head=_X(10)), 28, 50, -22)
    mid = LG(P_(L=(70, -22), LF=70, R=(70, -22), RF=70, Spine=_X(6), Head=_X(2)), 10, 18, -8)
    return 24, [(0, mid, -0.03), (6, up, 0.0), (14, down, -0.1), (18, down, -0.1), (24, mid, -0.03)]


def g_climb_loop():
    """爬架/爬梯：原地交替伸手抓高处、抬腿踩档（团结里按循环把根节点往上移约 0.56 m/循环）。"""
    def k(f, side):
        o = "Right" if side == "Left" else "Left"
        s1, s2 = ("L", "R") if side == "Left" else ("R", "L")
        P = P_(**{s1: (165, 8), s1 + "F": 20, s2: (110, 8), s2 + "F": 70}, Spine=_X(6), Head=_X(-16))
        LG(P, 70, 95, -10, side)
        LG(P, 8, 20, 10, o)
        return (f, P, 0.0)
    return 24, [k(0, "Left"), k(12, "Right"), k(24, "Left")]


def g_haul_loop():
    """拉绳：弓步后仰，双手交替一把一把往怀里拉（吊石、拉绞绳）。"""
    def k(f, a, b):
        P = P_(L=(a[0], -12), LF=a[1], R=(b[0], -12), RF=b[1], Spine=_X(-14), Chest=_X(-4), Head=_X(4))
        return (f, _stagger(P, 30, 26, -18, 12), -0.07)
    return 24, [k(0, (75, 10), (15, 70)), k(12, (15, 70), (75, 10)), k(24, (75, 10), (15, 70))]


A2_GESTURES = {
    "A2_SpearStamp": g_spear_stamp, "A2_PointLine": g_point_line, "A2_KneelDie": g_kneel_die,
    "A2_SlamDeed": g_slam_deed, "A2_Abacus": g_abacus, "A2_UnrollScroll": g_unroll,
    "A2_CloseGap": g_close_gap, "A2_HandTag": g_hand_tag, "A2_FallDead": g_fall_dead,
    "A2_PlantStake": g_plant_stake, "A2_PullString": g_pull_string, "A2_PushLoop": g_push_loop,
    "A2_LoadCannon": g_load_cannon, "A2_ChiselLoop": g_chisel_loop, "A2_WriteLoop": g_write_loop,
    "A2_Stamp": g_stamp, "A2_CarryLoop": g_carry_loop, "A2_RamLoop": g_ram_loop,
    "A2_ClimbLoop": g_climb_loop, "A2_HaulRopeLoop": g_haul_loop,
}
def _grounded(fn):
    """落地修正：build_gesture 调用时场景里已有人物，逐个关键帧摆姿势、量网格最低点，把髋高调到脚（或膝、身体）刚好贴地。"""
    def wrapped():
        total, keys = fn()
        rigs = [o for o in bpy.context.scene.objects if o.type == "ARMATURE"]
        if not rigs:
            return total, keys
        rig = rigs[-1]
        mesh = next((o for o in rig.children if o.type == "MESH"), None)
        if mesh is None:
            return total, keys
        prev = bpy.context.view_layer.objects.active
        bpy.context.view_layer.objects.active = rig
        out = []
        for f, P, up in keys:
            for pb in rig.pose.bones:
                pb.rotation_mode = "QUATERNION"
                pb.rotation_quaternion = (1, 0, 0, 0)
                pb.location = (0, 0, 0)
            for b, R in P.items():
                C.set_rot(rig, b, R)
            rig.pose.bones["Hips"].location = (0, up, 0)
            bpy.context.view_layer.update()
            dg = bpy.context.evaluated_depsgraph_get()
            ev = mesh.evaluated_get(dg)
            me = ev.to_mesh()
            mz = min((mesh.matrix_world @ v.co).z for v in me.vertices)
            ev.to_mesh_clear()
            out.append((f, P, round(up - mz, 4)))
        for pb in rig.pose.bones:
            pb.rotation_quaternion = (1, 0, 0, 0)
            pb.location = (0, 0, 0)
        bpy.context.view_layer.objects.active = prev
        return total, out
    return wrapped


C.GESTURE_HOOKS.update({k: _grounded(v) for k, v in A2_GESTURES.items()})


# ====================================================================== 注册
def recipes():
    R = {}
    for n in A2_CAST:
        R[n] = ("Characters", (lambda nm=n: C.build_character(nm, A2_CAST[nm])))
    R.update({
        "ENV_SandTable": ("Environments", build_sandtable),
        "PROP_Sand_Wall": ("Props", build_sand_wall),
        "PROP_Sand_Gate": ("Props", build_sand_gate),
        "PROP_Sand_Tower": ("Props", build_sand_tower),
        "PROP_Sand_House": ("Props", build_sand_house),
        "PROP_Sand_Flags": ("Props", build_sand_flags),
        "ENV_Stele": ("Environments", build_stele),
        "PROP_Covenant": ("Props", build_covenant),
        "PROP_Roster": ("Props", build_roster),
        "PROP_Deed": ("Props", build_deed),
        "PROP_Blueprint": ("Props", build_blueprint),
        "PROP_Survey": ("Props", build_survey),
        "PROP_Scaffold": ("Props", build_scaffold),
        "PROP_StoneBlock_S": ("Props", build_stone_s),
        "PROP_StoneBlock_M": ("Props", build_stone_m),
        "PROP_StoneBlock_L": ("Props", build_stone_l),
        "PROP_Mortar": ("Props", build_mortar),
        "PROP_Winch": ("Props", build_winch),
        "PROP_Cart_Wheelbarrow": ("Props", build_wheelbarrow),
        "PROP_Cart_Flat": ("Props", build_flatcart),
        "PROP_Tools": ("Props", build_tools),
        "PROP_Rope": ("Props", build_rope),
    })
    for k in A2_GESTURES:
        R[f"CH_WangYan_1941@{k}"] = ("Characters", (lambda kk=k: C.build_gesture(kk)))
    return R
