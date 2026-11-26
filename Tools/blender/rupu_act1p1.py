"""
《入谱》第一幕 1941 · P1 补充（街坊扩展、小吃摊、挑担推车、告示、弹坑、街垒、自行车、黄包车、电话、皮箱）
（Blender bpy，程序化白模；由 build_yongchang.py 统一生成/导出，recipes() 返回 {资产名: (分类, 生成函数)}）

对应 Docs/入谱_当前建模缺口清单.md 第二节（第一幕 P1）。约定同 rupu_act1.py：
  - 正面朝 Blender -Y（团结 +Z），1 unit = 1 m；道具原点在底面中心，环境原点在地面中心。
  - 会动/会切状态的部件是固定名字的子物体（Wheel_* / Body / Lid / Pot_Lid / Handset / Crank / Reel / Cloth*），
    枢轴已放在转轴上（车轴、铰链、旗杆），团结里按名字找、绕本地轴转。
  - FX_* 空物体 = 特效挂点；ANCHOR_* 空物体 = 站位锚点；COL_* 只碰撞；NOCOL_* 不加碰撞。
  - 告示三张的纸面文字是渲染出来的贴图 T_Poster_<A|B|C>_D.png（1024，思源宋体 OFL，找不到字体时退回色块）。
  - 人物用 rupu_char.build_character + 本模块注册的钩子（名字都带 P1_ 前缀）。
"""
import math
import os
import random

import bpy
from mathutils import Vector

import rupu_kit as K
import rupu_char as C
from rupu_act1 import obj, fx

P1_PALETTE = {
    # 道具 / 环境
    "M_P1_Wood": "#6b5039", "M_P1_WoodDark": "#3e2f24", "M_P1_WoodPale": "#8a7458", "M_P1_WoodGrey": "#6e665a",
    "M_P1_Bamboo": "#9a8a5a", "M_P1_Basket": "#8f7d55", "M_P1_Rope": "#9a8a66", "M_P1_Brick": "#6e6e68",
    "M_P1_Clay": "#7a6450", "M_P1_Iron": "#3a3c3d", "M_P1_Steel": "#4a4d4f", "M_P1_Ember": "#C4552E",
    "M_P1_Bowl": "#cfc8b6", "M_P1_BowlBlue": "#4e5e6e", "M_P1_Noodle": "#d8c89a", "M_P1_Broth": "#7a5a3a",
    "M_P1_Oil": "#4a3820", "M_P1_Youtiao": "#a8743a", "M_P1_Bun": "#ddd5c0", "M_P1_Cloth": "#a49a80",
    "M_P1_ClothBlue": "#4a5560", "M_P1_ClothRed": "#7a4440", "M_P1_Quilt": "#6e5246", "M_P1_QuiltBlue": "#56606a",
    "M_P1_Earth": "#5e5444", "M_P1_EarthDark": "#3e382e", "M_P1_Mud": "#4a4436", "M_P1_Stone": "#a09b8c",
    "M_P1_StoneDark": "#7a776c", "M_P1_Puddle": "#4F6B6A", "M_P1_Plaster": "#cbc4b1", "M_P1_PlasterDirty": "#9a9384",
    "M_P1_Scorch": "#2e2a26", "M_P1_Rubble": "#7a7268", "M_P1_Sandbag": "#9b8f6e", "M_P1_SandbagDark": "#857a5c",
    "M_P1_Wire": "#2e2c2a", "M_P1_FlagWhite": "#d6d0c2", "M_P1_FlagRed": "#8a2e26", "M_P1_Concrete": "#8e8a80",
    "M_P1_BikeFrame": "#2a2e2c", "M_P1_Rubber": "#1c1a18", "M_P1_Chrome": "#7a7c7a", "M_P1_Leather": "#4a3524",
    "M_P1_LeatherBrown": "#6a4a32", "M_P1_Brass": "#8f7a44", "M_P1_Hood": "#2b2a28", "M_P1_Seat": "#5a2e26",
    "M_P1_Khaki": "#57513a", "M_P1_KhakiLight": "#6b6446", "M_P1_Bakelite": "#1e1c1a", "M_P1_Lacquer": "#7d3a2c",
    "M_P1_PaperBack": "#c4b38f", "M_P1_WetStain": "#9a9486", "M_P1_Sign": "#d0c8b4", "M_P1_Paint": "#8a2e26",
    "M_P1_Glass": "#2a3236", "M_P1_Lamp": "#b07a4a",
    # 告示贴图只在渲染时用（不进资产）
    "M_P1_TexInk": "#1a1714", "M_P1_TexRed": "#9a3028", "M_P1_TexPaper": "#ddd0b4", "M_P1_TexPaperB": "#d2c6a6",
    "M_P1_TexPaperC": "#cfc6ae", "M_P1_TexGrey": "#8a8070", "M_P1_TexFace": "#b8a888",
    # 人物（P1 街坊）
    "M_P1C_MO_Ao": "#6e7a80", "M_P1C_MO_Pants": "#2e3440", "M_P1C_Swaddle": "#8a5a50", "M_P1C_SwaddleIn": "#c9bfa8",
    "M_P1C_Pin": "#a8a49a", "M_P1C_PO_Coat": "#4e5248", "M_P1C_PO_Pants": "#3a3630", "M_P1C_Towel": "#d0c8b4",
    "M_P1C_Pad": "#6a5a44", "M_P1C_BG_Coat": "#6a6252", "M_P1C_BG_Pants": "#4e4a40", "M_P1C_Patch1": "#5a5e58",
    "M_P1C_Patch2": "#7a6a4a", "M_P1C_Patch3": "#4e4038", "M_P1C_Bowl": "#8a7a62",
    "M_P1C_ST_Uniform": "#2a3038", "M_P1C_ST_Cap": "#1e2226", "M_P1C_ST_Bag": "#8a7e62", "M_P1C_ST_Shoe": "#1a1816",
    "M_P1C_SK_Robe": "#6a5a40", "M_P1C_SK_Vest": "#2a2622", "M_P1C_SK_Hat": "#3a3530", "M_P1C_SK_Band": "#1a1816",
    "M_P1C_Gold": "#9a8248", "M_P1C_OW_Ao": "#3e3832", "M_P1C_OW_Pants": "#26262a", "M_P1C_OW_Hood": "#1e1d1c",
    "M_P1C_Jade": "#6a8070", "M_P1C_TD_Coat": "#7a5040", "M_P1C_TD_Pants": "#4a4a50", "M_P1C_TigerCap": "#9a7440",
    "M_P1C_Silver": "#b8b4a8", "M_P1C_RW_Coat": "#6a6250", "M_P1C_RW_Pants": "#3a3a36", "M_P1C_Kerchief": "#56606a",
}
K.PALETTE.update(P1_PALETTE)

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ================================================================= 小工具
def bar(mb, p0, p1, r, mat, seg=6, r1=None):
    """任意方向的圆管（车架、车杠、铁丝、绳）。"""
    p0, p1 = Vector(p0), Vector(p1)
    u, v = C._frame(p1 - p0)
    r1 = r if r1 is None else r1
    pts = []
    for p, rr in ((p0, r), (p1, r1)):
        for i in range(seg):
            a = 2 * math.pi * i / seg
            pts.append(tuple(p + u * (rr * math.cos(a)) + v * (rr * math.sin(a))))
    b = mb.addv(pts)
    for i in range(seg):
        j = (i + 1) % seg
        mb.face([b + i, b + j, b + seg + j, b + seg + i], mat)
    mb.face([b + i for i in reversed(range(seg))], mat)
    mb.face([b + seg + i for i in range(seg)], mat)


def torus_x(mb, c, R, rr, mat, seg=18, sides=4):
    """轮胎/轮圈：圆环在 YZ 平面，轴沿 X。"""
    cx, cy, cz = c
    b = mb.addv([(cx + rr * math.sin(2 * math.pi * k / sides),
                  cy + (R + rr * math.cos(2 * math.pi * k / sides)) * math.cos(2 * math.pi * i / seg),
                  cz + (R + rr * math.cos(2 * math.pi * k / sides)) * math.sin(2 * math.pi * i / seg))
                 for i in range(seg) for k in range(sides)])
    for i in range(seg):
        i2 = (i + 1) % seg
        for k in range(sides):
            k2 = (k + 1) % sides
            mb.face([b + i * sides + k, b + i2 * sides + k, b + i2 * sides + k2, b + i * sides + k2], mat)


def wheel_x(mb, c, R, tire, rim_mat, tire_mat, spokes=12, hub=0.04, seg=18, spoke_r=0.004):
    """带辐条的车轮（轴沿 X）。"""
    torus_x(mb, c, R, tire, tire_mat, seg=seg, sides=4)
    torus_x(mb, c, R - tire * 1.2, tire * 0.45, rim_mat, seg=seg, sides=3)
    cx, cy, cz = c
    with mb.at(cx, cy, cz, ry=90):
        mb.cyl(0, 0, -0.05, 0.05, hub, rim_mat, seg=8)
    for k in range(spokes):
        a = 2 * math.pi * k / spokes
        bar(mb, (cx + (0.03 if k % 2 else -0.03), cy, cz),
            (cx, cy + (R - tire * 1.3) * math.cos(a), cz + (R - tire * 1.3) * math.sin(a)), spoke_r, rim_mat, seg=3)


def sack(mb, x, y, z, rz, mat, L=0.56, Wd=0.32, Hh=0.2):
    """沙袋/米袋：八棱截面的软袋（比方盒子圆一些）。"""
    w, c = Wd / 2, 0.05
    with mb.at(x, y, z, rz=rz):
        mb.prism([(-w, c), (-w + c, 0), (w - c, 0), (w, c), (w, Hh - c), (w - c, Hh), (-w + c, Hh), (-w, Hh - c)],
                 "x", -L / 2, L / 2, mat)


def chair(mb, x, y, z, rz=0.0, rx=0.0, ry=0.0, mat="M_P1_Wood"):
    with mb.at(x, y, z, rz=rz, rx=rx, ry=ry):
        mb.box(-0.22, -0.22, 0.43, 0.22, 0.22, 0.47, mat)
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.box(sx * 0.2 - 0.02, sy * 0.2 - 0.02, 0, sx * 0.2 + 0.02, sy * 0.2 + 0.02, 0.43, "M_P1_WoodDark")
            mb.box(sx * 0.2 - 0.02, 0.18, 0.47, sx * 0.2 + 0.02, 0.22, 0.95, "M_P1_WoodDark")
        mb.box(-0.2, 0.18, 0.82, 0.2, 0.22, 0.92, mat)
        mb.box(-0.2, 0.18, 0.62, 0.2, 0.22, 0.68, mat)


def crate(mb, x, y, z, sx, sy, sz, rz=0.0, mat="M_P1_WoodPale"):
    with mb.at(x, y, z, rz=rz):
        mb.box(-sx / 2, -sy / 2, 0, sx / 2, sy / 2, sz, mat)
        for xx in (-sx / 2, sx / 2 - 0.05):
            mb.box(xx, -sy / 2 - 0.01, 0, xx + 0.05, sy / 2 + 0.01, sz, "M_P1_WoodDark")


def bowl(mb, x, y, z, r=0.07, mat="M_P1_Bowl", fill=None):
    mb.cyl(x, y, z, z + r * 0.7, r * 0.45, mat, seg=8, r_top=r)
    if fill:
        mb.cyl(x, y, z + r * 0.5, z + r * 0.62, r * 0.85, fill, seg=8)


def corner_cap(mb, cx, cy, sx, sy, z0, z1, s=0.03, t=0.004, mat="M_P1_Brass"):
    """箱子铜包角：角点 (cx,cy)，sx/sy 指向外侧。"""
    xa, xb = sorted((cx + sx * t, cx - sx * s))
    ya, yb = sorted((cy + sy * t, cy - sy * s))
    mb.box(xa, ya, z0, xb, yb, z1, mat)


def anchor(name, loc, rz=0.0):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "ARROWS"
    e.empty_display_size = 0.3
    e.location = loc
    e.rotation_euler = (0, 0, math.radians(rz))
    bpy.context.scene.collection.objects.link(e)
    return e


def crater(mb, rng, r_in, r_rim, r_out, rim_h, a0=0.0, a1=2 * math.pi, seg=18, depth=0.03,
           mats=("M_P1_EarthDark", "M_P1_Earth", "M_P1_Mud")):
    """弹坑：坑底（略低于地面）→ 内坡 → 外翻土沿（rim_h）→ 落回地面。a0..a1 可只做一段弧（靠墙）。"""
    full = abs(a1 - a0 - 2 * math.pi) < 1e-6
    n = seg if full else seg + 1
    jit = [0.82 + 0.36 * rng.random() for _ in range(n)]
    if full:
        jit.append(jit[0])
    ang = [a0 + (a1 - a0) * i / seg for i in range(seg + 1)]
    prof = [(r_in, -depth), (r_in + (r_rim - r_in) * 0.55, rim_h * 0.45), (r_rim, rim_h), (r_out, 0.0)]
    rings = []
    for rr, zz in prof:
        rings.append(mb.addv([(rr * jit[i] * math.cos(a), rr * jit[i] * math.sin(a), zz * (0.75 + 0.5 * jit[i] - 0.4))
                              for i, a in enumerate(ang)]))
    for k in range(len(prof) - 1):
        m = mats[min(k, len(mats) - 1)]
        for i in range(seg):
            mb.face([rings[k] + i, rings[k] + i + 1, rings[k + 1] + i + 1, rings[k + 1] + i], m)
    c = mb.addv([(0, 0, -depth - 0.005)])
    for i in range(seg):
        mb.face([c, rings[0] + i + 1, rings[0] + i], mats[0])
    return jit


# ================================================================= CHR_Townsperson 扩展（8 个）
def _front_y(J, z, h, cfg, k=0.066):
    return C.spine_y(J, z) - k * h * cfg.get("bulk", 1.0)


def hair_student_cap(S, J, hc, r, hm, h, cfg):
    """学生帽：直帽墙 + 平顶 + 黑漆帽舌 + 铜帽徽。"""
    rx, ry, rz = r
    C.hair_short(S, hc, r, "M_CH_Hair", h)
    S.add(*C.rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.35)), rx * 1.08, ry * 1.06),
                         (hc + Vector((0, 0.006 * h, rz * 1.12)), rx * 1.14, ry * 1.14)], seg=12), hm, C.W("Head"))
    S.add(*C.box(hc + Vector((0, -ry * 1.18, rz * 0.4)), (rx * 1.4, ry * 0.55, 0.006 * h), rot=C._eu(-14, 0, 0)),
          "M_P1C_ST_Shoe", C.W("Head"))
    S.add(*C.box(hc + Vector((0, -ry * 1.13, rz * 0.8)), (0.016 * h, 0.004 * h, 0.014 * h)), "M_P1C_Gold", C.W("Head"))


def hair_tiger_cap(S, J, hc, r, hm, h, cfg):
    """虎头帽（幼童）：包住头顶和后脑，两只小耳朵，额前三道「王」字纹 + 虎眼。"""
    rx, ry, rz = r
    S.add(*C.ellipsoid(hc + Vector((0, 0.008 * h, 0.004 * h)), rx * 1.12, ry * 1.1, rz * 1.06, seg=10, rings=4, zmin=-0.3),
          hm, C.W("Head"))
    for sx in (-1, 1):
        S.add(*C.ellipsoid(hc + Vector((sx * rx * 0.7, 0.01 * h, rz * 0.98)), 0.02 * h, 0.012 * h, 0.022 * h, seg=6, rings=3),
              hm, C.W("Head"))
        S.add(*C.box(hc + Vector((sx * rx * 0.42, -ry * 1.08, rz * 0.5)), (0.016 * h, 0.004 * h, 0.01 * h)), "M_CH_Eye", C.W("Head"))
    for k, w in enumerate((0.03, 0.022, 0.03)):
        S.add(*C.box(hc + Vector((0, -ry * 1.1, rz * (0.62 + 0.1 * k))), (w * h, 0.004 * h, 0.004 * h)), "M_CH_Eye", C.W("Head"))
    S.add(*C.box(hc + Vector((0, -ry * 1.1, rz * 0.72)), (0.004 * h, 0.004 * h, 0.022 * h)), "M_CH_Eye", C.W("Head"))
    S.add(*C.box(hc + Vector((0, ry * 0.9, -rz * 0.55)), (rx * 1.6, 0.01 * h, rz * 0.6)), hm, {"Head": 0.6, "Neck": 0.4})


def hair_hood(S, J, hc, r, hm, h, cfg):
    """老妇黑风帽：罩住头顶两鬓垂到后颈，额前抹额缀一块玉。"""
    rx, ry, rz = r
    C.hair_short(S, hc, r, "M_CH_Hair_Grey", h)
    S.add(*C.ellipsoid(hc + Vector((0, 0.012 * h, 0.006 * h)), rx * 1.16, ry * 1.12, rz * 1.06, seg=10, rings=4, zmin=-0.45),
          hm, C.W("Head"))
    S.add(*C.box(hc + Vector((0, ry * 0.85, -rz * 0.75)), (rx * 1.9, 0.02 * h, rz * 0.8)), hm, {"Head": 0.5, "Neck": 0.5})
    S.add(*C.rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.25)), rx * 1.19, ry * 1.15),
                         (hc + Vector((0, 0.004 * h, rz * 0.42)), rx * 1.18, ry * 1.14)], seg=10), "M_P1C_OW_Hood", C.W("Head"))
    S.add(*C.box(hc + Vector((0, -ry * 1.16, rz * 0.34)), (0.018 * h, 0.006 * h, 0.014 * h)), "M_P1C_Jade", C.W("Head"))


def hair_towel(S, J, hc, r, hm, h, cfg):
    """挑夫：剃短的头 + 额前扎一圈汗巾，右前打结。"""
    rx, ry, rz = r
    S.add(*C.ellipsoid(hc + Vector((0, 0.004 * h, 0.01 * h)), rx * 1.03, ry * 1.02, rz * 0.96, seg=10, rings=4, zmin=0.1),
          hm, C.W("Head"))
    S.add(*C.rings_mesh([(hc + Vector((0, 0.003 * h, rz * 0.28)), rx * 1.1, ry * 1.08),
                         (hc + Vector((0, 0.003 * h, rz * 0.52)), rx * 1.08, ry * 1.06)], seg=10), "M_P1C_Towel", C.W("Head"))
    S.add(*C.box(hc + Vector((-rx * 0.8, -ry * 0.8, rz * 0.4)), (0.024 * h, 0.02 * h, 0.02 * h)), "M_P1C_Towel", C.W("Head"))


def hair_messy(S, J, hc, r, hm, h, cfg):
    """乞丐：蓬乱的头发（几团乱发 + 后颈长发）。"""
    rx, ry, rz = r
    C.hair_short(S, hc, r, hm, h)
    for (dx, dy, dz, s) in ((0.6, 0.2, 0.85, 1.0), (-0.65, 0.3, 0.8, 0.9), (0.1, 0.6, 0.95, 1.1), (-0.3, -0.5, 0.92, 0.8),
                            (0.75, 0.6, 0.35, 0.8), (-0.8, 0.55, 0.3, 0.85)):
        S.add(*C.ellipsoid(hc + Vector((dx * rx, dy * ry, dz * rz)), 0.024 * h * s, 0.022 * h * s, 0.018 * h * s, seg=6, rings=3),
              hm, C.W("Head"))
    S.add(*C.box(hc + Vector((0, ry * 0.9, -rz * 0.7)), (rx * 1.5, 0.02 * h, rz * 0.8)), hm, {"Head": 0.6, "Neck": 0.4})


def hair_fedora(S, J, hc, r, hm, h, cfg):
    """掌柜礼帽：高帽身（顶上捏凹）+ 黑缎帽带 + 一圈帽檐。"""
    rx, ry, rz = r
    C.hair_short(S, hc, r, "M_CH_Hair", h)
    S.add(*C.rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.4)), rx * 1.1, ry * 1.08),
                         (hc + Vector((0, 0.004 * h, rz * 1.15)), rx * 1.0, ry * 0.98),
                         (hc + Vector((0, 0.004 * h, rz * 1.3)), rx * 0.82, ry * 0.7)], seg=12), hm, C.W("Head"))
    S.add(*C.rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.42)), rx * 1.12, ry * 1.1),
                         (hc + Vector((0, 0.004 * h, rz * 0.62)), rx * 1.08, ry * 1.06)], seg=12), "M_P1C_SK_Band", C.W("Head"))
    S.add(*C.rings_mesh([(hc + Vector((0, 0.004 * h, rz * 0.36)), rx * 1.8, ry * 1.7),
                         (hc + Vector((0, 0.004 * h, rz * 0.42)), rx * 1.8, ry * 1.7)], seg=12), hm, C.W("Head"))


def hair_kerchief(S, J, hc, r, hm, h, cfg):
    """逃难妇人：方头巾对折包头、下巴下打结（与 P0 妇女脑后打结的包头巾区分）。"""
    rx, ry, rz = r
    C.hair_short(S, hc, r, "M_CH_Hair", h)
    S.add(*C.ellipsoid(hc + Vector((0, 0.01 * h, 0.01 * h)), rx * 1.14, ry * 1.12, rz * 1.05, seg=10, rings=4, zmin=-0.35),
          hm, C.W("Head"))
    for sx in (-1, 1):
        S.add(*C.box(hc + Vector((sx * rx * 0.85, -ry * 0.25, -rz * 0.72)), (0.012 * h, 0.03 * h, 0.06 * h), rot=C._eu(0, sx * 18, 0)),
              hm, C.W("Head"))
    S.add(*C.box(hc + Vector((0, -ry * 0.55, -rz * 1.05)), (0.03 * h, 0.022 * h, 0.022 * h)), hm, {"Head": 0.6, "Neck": 0.4})
    S.add(*C.box(hc + Vector((0, ry * 1.0, -rz * 0.5)), (rx * 1.2, 0.01 * h, rz * 0.9)), hm, {"Head": 0.6, "Neck": 0.4})


def ex_baby(S, J, h, c, tw, hipsW):
    """母亲胸前背带里的婴儿：襁褓 + 小脑袋 + 交叉背带。"""
    fy = _front_y(J, 0.7 * h, h, c)
    S.add(*C.ellipsoid((0, fy - 0.055 * h, 0.66 * h), 0.068 * h, 0.05 * h, 0.085 * h, seg=8, rings=4), "M_P1C_Swaddle", C.W("Chest"))
    S.add(*C.ellipsoid((0, fy - 0.06 * h, 0.755 * h), 0.04 * h, 0.036 * h, 0.04 * h, seg=8, rings=4), "M_CH_Skin", C.W("Chest"))
    S.add(*C.ellipsoid((0, fy - 0.058 * h, 0.77 * h), 0.044 * h, 0.04 * h, 0.034 * h, seg=8, rings=3, zmin=0.0), "M_P1C_SwaddleIn",
          C.W("Chest"))
    for sx in (-1, 1):
        a = Vector((sx * 0.07 * h, fy - 0.01 * h, 0.8 * h))
        b = Vector((-sx * 0.06 * h, C.spine_y(J, 0.62 * h) + 0.066 * h, 0.6 * h))
        S.add(*C.tube(a, a + Vector((0, 0.13 * h, 0.03 * h)), 0.008 * h, 0.008 * h, seg=4), "M_P1C_Swaddle", C.W("Chest"))
        S.add(*C.tube(a + Vector((0, 0.13 * h, 0.03 * h)), b, 0.008 * h, 0.008 * h, seg=4), "M_P1C_Swaddle", tw)


def ex_hairpin(S, J, h, c, tw, hipsW):
    hc = J["head"] + Vector((0, -0.004 * h, 0.064 * h))
    S.add(*C.box(hc + Vector((0.0, 0.075 * h, -0.004 * h)), (0.08 * h, 0.006 * h, 0.006 * h), rot=C._eu(0, 15, 0)), "M_P1C_Pin",
          C.W("Head"))


def ex_shoulder_pad(S, J, h, c, tw, hipsW):
    """挑夫：右肩垫肩布 + 脖子上搭的汗巾。"""
    S.add(*C.box(J["armR"] + Vector((0.035 * h, 0, 0.038 * h)), (0.09 * h, 0.12 * h, 0.018 * h)), "M_P1C_Pad",
          {"RightShoulder": 0.5, "Chest": 0.5})
    nz = J["neck"].z
    S.add(*C.rings_mesh([(Vector((0, J["neck"].y, nz - 0.02 * h)), 0.036 * h, 0.032 * h),
                         (Vector((0, J["neck"].y, nz + 0.004 * h)), 0.034 * h, 0.03 * h)], seg=8), "M_P1C_Towel", C.W("Neck"))
    for sx in (-1, 1):
        S.add(*C.box((sx * 0.03 * h, J["neck"].y - 0.06 * h, nz - 0.07 * h), (0.022 * h, 0.006 * h, 0.1 * h)), "M_P1C_Towel", C.W("Chest"))


def ex_rags(S, J, h, c, tw, hipsW):
    """乞丐：补丁、草绳腰带、破下摆布条、左胯一只破碗。"""
    bk = c.get("bulk", 1.0)
    for (x, z, w, hh, m, back) in ((0.04, 0.66, 0.05, 0.06, "M_P1C_Patch1", False), (-0.05, 0.56, 0.06, 0.05, "M_P1C_Patch2", False),
                                   (0.02, 0.7, 0.07, 0.06, "M_P1C_Patch3", True), (-0.04, 0.5, 0.05, 0.05, "M_P1C_Patch1", True)):
        y = C.spine_y(J, z * h) + (1 if back else -1) * 0.067 * h * bk
        S.add(*C.box((x * h, y, z * h), (w * h, 0.006 * h, hh * h)), m, tw)
    for s_, side in (("L", "Left"), ("R", "Right")):
        S.add(*C.box(J["knee" + s_] + Vector((0, -0.03 * h, 0.04 * h)), (0.04 * h, 0.006 * h, 0.04 * h)), "M_P1C_Patch2",
              C.W(side + "UpperLeg"))
    S.add(*C.rings_mesh([(Vector((0, 0, 0.49 * h)), 0.098 * h * bk, 0.07 * h * bk),
                         (Vector((0, 0, 0.505 * h)), 0.097 * h * bk, 0.069 * h * bk)], seg=10), "M_P1_Rope", hipsW)
    for k, (x, y) in enumerate(((0.08, -0.03), (-0.06, -0.06), (0.03, 0.07), (-0.09, 0.03), (0.06, 0.06))):
        sg = 1 if x > 0 else -1
        S.add(*C.box((x * h, y * h, 0.4 * h), (0.022 * h, 0.006 * h, 0.08 * h + 0.012 * h * k), rot=C._eu(0, 0, math.degrees(math.atan2(y, x)) + 90)),
              c["top"], {"Hips": 0.4, ("LeftUpperLeg" if sg > 0 else "RightUpperLeg"): 0.6})
    S.add(*C.tube((0.11 * h, -0.02 * h, 0.4 * h), (0.11 * h, -0.02 * h, 0.44 * h), 0.02 * h, 0.04 * h, seg=8), "M_P1C_Bowl", hipsW)
    S.add(*C.box((0.11 * h, -0.02 * h, 0.47 * h), (0.006 * h, 0.006 * h, 0.06 * h)), "M_P1_Rope", hipsW)


def ex_student(S, J, h, c, tw, hipsW):
    """学生装：立领、五颗铜扣、两个胸袋；左肩斜挎帆布书包到右胯。"""
    bk = c.get("bulk", 1.0)
    S.add(*C.tube(J["neck"] + Vector((0, 0, -0.02 * h)), J["neck"] + Vector((0, 0, 0.022 * h)), 0.034 * h, 0.031 * h, seg=8),
          c["top"], C.W("Neck"))
    for k in range(5):
        z = 0.5 * h + k * 0.062 * h
        S.add(*C.box((0, C.spine_y(J, z) - 0.068 * h * bk, z), (0.01 * h, 0.006 * h, 0.01 * h)), "M_P1C_Gold", tw)
    for sx in (-1, 1):
        z = 0.73 * h
        S.add(*C.box((sx * 0.05 * h, C.spine_y(J, z) - 0.07 * h * bk, z), (0.04 * h, 0.006 * h, 0.04 * h)), c["top"], tw)
    a = J["chest_t"] + Vector((0.07 * h, 0, 0))
    b = Vector((-0.1 * h, 0, 0.5 * h))
    d = b - a
    ang = math.degrees(math.atan2(d.x, d.z))
    for yy in (-0.068 * h, 0.066 * h):
        S.add(*C.box((a + b) / 2 + Vector((0, yy, 0)), (0.018 * h, 0.006 * h, d.length), rot=C._eu(0, ang, 0)), "M_P1C_ST_Bag", tw)
    S.add(*C.box((-0.115 * h, -0.01 * h, 0.46 * h), (0.035 * h, 0.12 * h, 0.09 * h)), "M_P1C_ST_Bag", hipsW)
    S.add(*C.box((-0.134 * h, -0.01 * h, 0.485 * h), (0.004 * h, 0.12 * h, 0.04 * h)), "M_P1C_ST_Uniform", hipsW)


def ex_vest(S, J, h, c, tw, hipsW):
    """掌柜：长衫外罩的黑缎马甲（无袖）+ 铜扣 + 怀表链。"""
    bk = c.get("bulk", 1.0) * 1.06
    rings = []
    for z, rxx, ryy in ((0.47 * h, 0.1, 0.072), (0.56 * h, 0.09, 0.064), (0.64 * h, 0.097, 0.067), (0.72 * h, 0.108, 0.069),
                        (J["chest_t"].z - 0.006 * h, 0.105, 0.062)):
        rings.append((Vector((0, C.spine_y(J, z), z)), rxx * h * bk, ryy * h * bk))
    S.add(*C.rings_mesh(rings, seg=10, cap0=False), "M_P1C_SK_Vest", tw)
    for k in range(5):
        z = 0.5 * h + k * 0.055 * h
        S.add(*C.box((0, C.spine_y(J, z) - 0.071 * h * bk, z), (0.012 * h, 0.006 * h, 0.01 * h)), "M_P1C_Gold", tw)
    for k in range(7):          # 怀表链：右胸袋垂到中扣
        t = k / 6
        p = Vector((-0.05 * h * (1 - t), 0, (0.62 - 0.05 * math.sin(math.pi * t)) * h))
        p.y = C.spine_y(J, p.z) - 0.073 * h * bk
        S.add(*C.box(p, (0.012 * h, 0.004 * h, 0.004 * h)), "M_P1C_Gold", tw)


def ex_mustache(S, J, h, c, tw, hipsW):
    hc = J["head"] + Vector((0, -0.004 * h, 0.064 * h))
    for sx in (-1, 1):
        S.add(*C.box(hc + Vector((sx * 0.012 * h, -0.058 * h, -0.024 * h)), (0.022 * h, 0.006 * h, 0.006 * h), rot=C._eu(0, sx * 22, 0)),
              "M_CH_Hair", C.W("Head"))


def ex_basket_arm(S, J, h, c, tw, hipsW):
    """老妇：左前臂挎一只竹篮（T 姿势时挂在前臂下）。"""
    e, w = J["elbowL"], J["wristL"]
    m = e + (w - e) * 0.5
    S.add(*C.tube(m + Vector((0, 0, -0.17 * h)), m + Vector((0, 0, -0.07 * h)), 0.07 * h, 0.085 * h, seg=8), "M_P1_Basket",
          C.W("LeftLowerArm"))
    for sy in (-1, 1):
        S.add(*C.box(m + Vector((0, sy * 0.045 * h, -0.035 * h)), (0.01 * h, 0.006 * h, 0.075 * h), rot=C._eu(sy * 32, 0, 0)),
              "M_P1_Bamboo", C.W("LeftLowerArm"))
    S.add(*C.box(m + Vector((0, 0, -0.065 * h)), (0.11 * h, 0.12 * h, 0.012 * h)), "M_P1_Cloth", C.W("LeftLowerArm"))


def ex_lock(S, J, h, c, tw, hipsW):
    """幼童：胸前银长命锁。"""
    z = 0.69 * h
    fy = _front_y(J, z, h, c, k=0.07)
    S.add(*C.box((0, fy - 0.006 * h, z), (0.06 * h, 0.01 * h, 0.04 * h)), "M_P1C_Silver", C.W("Chest"))
    for sx in (-1, 1):
        S.add(*C.box((sx * 0.024 * h, fy - 0.004 * h, z + 0.06 * h), (0.005 * h, 0.005 * h, 0.09 * h), rot=C._eu(0, -sx * 18, 0)),
              "M_P1C_Silver", C.W("Chest"))


def ex_back_basket(S, J, h, c, tw, hipsW):
    """逃难妇人：背篓（上口大、底小）+ 篓里的包袱 + 两根背带；胸前再挎一个小包袱。"""
    by = C.spine_y(J, 0.65 * h) + 0.07 * h * c.get("bulk", 1.0) + 0.09 * h
    S.add(*C.tube((0, by, 0.47 * h), (0, by + 0.01 * h, 0.86 * h), 0.07 * h, 0.115 * h, seg=10), "M_P1_Basket", tw)
    S.add(*C.ellipsoid((0.01 * h, by + 0.01 * h, 0.87 * h), 0.09 * h, 0.08 * h, 0.05 * h, seg=8, rings=3), "M_P1_QuiltBlue", C.W("Chest"))
    S.add(*C.tube((-0.06 * h, by, 0.88 * h), (0.07 * h, by + 0.02 * h, 0.92 * h), 0.022 * h, 0.022 * h, seg=6), "M_P1_Quilt", C.W("Chest"))
    for sx in (-1, 1):
        S.add(*C.box((sx * 0.06 * h, _front_y(J, 0.68 * h, h, c) - 0.004 * h, 0.68 * h), (0.014 * h, 0.006 * h, 0.24 * h)), "M_P1_Rope", tw)
    S.add(*C.box((0.07 * h, _front_y(J, 0.52 * h, h, c) - 0.03 * h, 0.5 * h), (0.11 * h, 0.06 * h, 0.08 * h), rot=C._eu(0, 0, 8)),
          "M_P1_ClothBlue", hipsW)


for _k, _f in (("P1_student_cap", hair_student_cap), ("P1_tiger_cap", hair_tiger_cap), ("P1_hood", hair_hood),
               ("P1_towel", hair_towel), ("P1_messy", hair_messy), ("P1_fedora", hair_fedora), ("P1_kerchief", hair_kerchief)):
    C.HAIR_HOOKS[_k] = _f
for _k, _f in (("P1_baby", ex_baby), ("P1_hairpin", ex_hairpin), ("P1_shoulder_pad", ex_shoulder_pad), ("P1_rags", ex_rags),
               ("P1_student", ex_student), ("P1_vest", ex_vest), ("P1_mustache", ex_mustache),
               ("P1_basket_arm", ex_basket_arm), ("P1_lock", ex_lock), ("P1_back_basket", ex_back_basket)):
    C.EXTRA_HOOKS[_k] = _f

P1_CAST = {
    "NPC_TownMother": dict(H=1.58, outfit="jacket", top="M_P1C_MO_Ao", pants="M_P1C_MO_Pants", shoe="M_CH_ClothShoe",
                           hair="back_bun", bulk=0.94, brow_tilt=-8, extras=["P1_hairpin", "P1_baby"],
                           desc="街坊·抱孩子的母亲 1941：28 岁，浅灰蓝大襟袄、深蓝裤、低髻插银簪，胸前背带兜着襁褓婴儿"),
    "NPC_TownPorter": dict(H=1.74, outfit="jacket", top="M_P1C_PO_Coat", pants="M_P1C_PO_Pants", shoe="M_CH_Straw",
                           sleeve="M_CH_Skin_Dark", cuff=0.95, wrap="M_CH_Skin_Dark", sash="M_P1_Rope", skin="M_CH_Skin_Dark",
                           hair="P1_towel", bulk=1.08, hunch=0.15, brow_tilt=6, extras=["P1_shoulder_pad"],
                           desc="街坊·挑夫 1941：32 岁，壮，深灰短褂挽袖、裤腿卷到膝、草鞋，额扎汗巾、颈搭汗巾、右肩垫肩（扁担挑子另为 PROP_Load_Pole）"),
    "NPC_TownBeggar": dict(H=1.63, outfit="jacket", top="M_P1C_BG_Coat", pants="M_P1C_BG_Pants", shoe="M_CH_Skin_Dark",
                           skin="M_CH_Skin_Dark", hair="P1_messy", hair_mat="M_CH_Hair", bulk=0.82, hunch=0.45, brow_tilt=-14,
                           beard="short_grey", extras=["P1_rags"],
                           desc="街坊·乞丐 1941：瘦、驼，打满补丁的破短褂、草绳腰带、破布条下摆、赤脚、乱发、花白短须，左胯挂破碗"),
    "NPC_TownStudent": dict(H=1.73, outfit="jacket", top="M_P1C_ST_Uniform", pants="M_P1C_ST_Uniform", shoe="M_P1C_ST_Shoe",
                            hair="P1_student_cap", hair_mat="M_P1C_ST_Cap", bulk=0.9, brow_tilt=10, extras=["P1_student"],
                            desc="街坊·学生 1941：18 岁，深藏青立领学生装、五颗铜扣、学生帽，斜挎帆布书包，皱眉"),
    "NPC_TownShopkeeper": dict(H=1.66, outfit="robe", top="M_P1C_SK_Robe", pants="M_P1C_SK_Robe", shoe="M_CH_EL_Shoe",
                               hem=0.1, hair="P1_fedora", hair_mat="M_P1C_SK_Hat", bulk=1.24, brow_tilt=-4,
                               extras=["P1_vest", "P1_mustache"],
                               desc="街坊·铺子掌柜 1941：50 岁，胖，驼色长衫外罩黑缎马甲、怀表链、礼帽、八字胡"),
    "NPC_TownOldWoman": dict(H=1.47, outfit="jacket", top="M_P1C_OW_Ao", pants="M_P1C_OW_Pants", shoe="M_CH_ClothShoe",
                             skin="M_CH_Skin_Old", hair="P1_hood", hair_mat="M_P1C_OW_Hood", brow="M_CH_Hair_Grey",
                             wrap="M_P1C_OW_Hood", hunch=0.6, bulk=0.85, brow_tilt=-10, extras=["P1_basket_arm"],
                             desc="街坊·老太太 1941：75 岁，矮小、背驼，深褐袄黑裤扎裤脚、黑风帽缀玉抹额，左臂挎竹篮"),
    "NPC_TownToddler": dict(H=1.02, head=1.4, outfit="jacket", top="M_P1C_TD_Coat", pants="M_P1C_TD_Pants",
                            shoe="M_CH_ClothShoe", hair="P1_tiger_cap", hair_mat="M_P1C_TigerCap", bulk=1.12, cuff=1.25,
                            extras=["P1_lock"],
                            desc="街坊·幼童 1941：4 岁，圆滚滚的棉袄、虎头帽、胸前银长命锁（比 P0 的族中男孩小一号）"),
    "NPC_TownRefugeeWoman": dict(H=1.60, outfit="jacket", top="M_P1C_RW_Coat", pants="M_P1C_RW_Pants", shoe="M_CH_Straw",
                                 wrap="M_CH_Wrap", hair="P1_kerchief", hair_mat="M_P1C_Kerchief", bulk=0.9, hunch=0.2,
                                 brow_tilt=-12, extras=["P1_back_basket"],
                                 desc="街坊·逃难妇人 1941：40 岁，土灰短袄、绑腿草鞋、下巴打结的方头巾，背篓装铺盖，胸前挎包袱"),
}


# ================================================================= PROP_StreetFood 小吃摊 2
def build_food_noodle():
    """面担（馄饨担式）：前柜炉灶 + 汤锅（Pot_Lid 可揭）、后柜抽屉 + 碗架，两柜间扁担；前面一条长凳摆两碗面。"""
    mb = K.MB()
    # 前柜（灶）：x<0
    with mb.at(-0.75, 0, 0):
        mb.box(-0.28, -0.24, 0, 0.28, 0.24, 0.72, "M_P1_WoodDark")
        mb.box(-0.26, -0.22, 0.08, 0.26, 0.22, 0.7, "M_P1_Wood")
        mb.box(-0.12, -0.25, 0.18, 0.12, -0.2, 0.36, "M_P1_Scorch")                 # 灶口
        mb.box(-0.1, -0.252, 0.19, 0.1, -0.24, 0.24, "M_P1_Ember")
        mb.cyl(0, 0, 0.72, 0.78, 0.25, "M_P1_Clay", seg=12)
        mb.cyl(0, 0, 0.78, 0.98, 0.2, "M_P1_Iron", seg=12, r_top=0.22)            # 汤锅
        mb.cyl(0.18, 0.16, 0.72, 1.35, 0.04, "M_P1_Iron", seg=6)                   # 小烟囱
        for sy in (-1, 1):                                                         # 担架弯梁
            mb.box(-0.27, sy * 0.22 - 0.02, 0.72, -0.23, sy * 0.22 + 0.02, 1.42, "M_P1_WoodDark")
            mb.box(0.23, sy * 0.22 - 0.02, 0.72, 0.27, sy * 0.22 + 0.02, 1.42, "M_P1_WoodDark")
        mb.box(-0.27, -0.24, 1.38, 0.27, 0.24, 1.44, "M_P1_WoodDark")
        mb.box(-0.3, -0.26, 0.0, 0.3, 0.26, 0.06, "M_P1_WoodDark")
    # 后柜（抽屉 + 碗架）：x>0
    with mb.at(0.75, 0, 0):
        mb.box(-0.25, -0.22, 0, 0.25, 0.22, 0.9, "M_P1_Wood")
        for k in range(4):
            z = 0.1 + k * 0.19
            mb.box(-0.22, -0.23, z, 0.22, -0.22, z + 0.15, "M_P1_WoodPale")
            mb.box(-0.03, -0.24, z + 0.06, 0.03, -0.23, z + 0.09, "M_P1_Brass")
        mb.box(-0.27, -0.24, 0.9, 0.27, 0.24, 0.94, "M_P1_WoodDark")
        for k, (x, y) in enumerate(((-0.13, -0.1), (0.1, -0.1), (-0.12, 0.1))):
            for s in range(4 - k):                                                 # 叠起的碗
                bowl(mb, x, y, 0.94 + s * 0.045, 0.075, "M_P1_BowlBlue" if s % 2 else "M_P1_Bowl")
        mb.cyl(0.13, 0.11, 0.94, 1.12, 0.035, "M_P1_Bamboo", seg=6)               # 筷筒
        for dx in (-0.01, 0.01):
            mb.box(0.13 + dx - 0.003, 0.11 - 0.003, 1.0, 0.13 + dx + 0.003, 0.11 + 0.003, 1.2, "M_P1_Bamboo")
        for sy in (-1, 1):
            mb.box(-0.25, sy * 0.2 - 0.02, 0.94, -0.21, sy * 0.2 + 0.02, 1.42, "M_P1_WoodDark")
            mb.box(0.21, sy * 0.2 - 0.02, 0.94, 0.25, sy * 0.2 + 0.02, 1.42, "M_P1_WoodDark")
        mb.box(-0.25, -0.22, 1.38, 0.25, 0.22, 1.44, "M_P1_WoodDark")
    bar(mb, (-1.15, 0, 1.47), (1.15, 0, 1.47), 0.03, "M_P1_Bamboo", seg=6)        # 扁担
    # 长凳 + 两碗面 + 小方凳
    mb.box(-0.8, -0.95, 0.42, 0.8, -0.73, 0.47, "M_P1_WoodPale")
    for x in (-0.68, 0.68):
        for y in (-0.92, -0.76):
            mb.box(x - 0.025, y - 0.02, 0, x + 0.025, y + 0.02, 0.42, "M_P1_WoodDark")
    bowl(mb, -0.3, -0.84, 0.47, 0.08, "M_P1_BowlBlue", fill="M_P1_Noodle")
    bowl(mb, 0.25, -0.84, 0.47, 0.08, "M_P1_Bowl", fill="M_P1_Broth")
    mb.box(0.35, -0.86, 0.5, 0.5, -0.84, 0.508, "M_P1_Bamboo")
    mb.box(-0.15, -1.45, 0.0, 0.15, -1.2, 0.32, "M_P1_Wood")
    obj(mb, "Stall", (0, 0, 0), uv=1.0)
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.03, 0.215, "M_P1_Wood", seg=12, r_top=0.2)
    mb.box(-0.06, -0.015, 0.03, 0.06, 0.015, 0.07, "M_P1_WoodDark")
    obj(mb, "Pot_Lid", (-0.75, 0, 0.98), uv=1.0)
    fx("FX_Steam", (-0.75, 0, 1.06))
    fx("FX_StoveFire", (-0.75, -0.22, 0.25))
    fx("FX_StoveSmoke", (-0.57, 0.16, 1.38))
    anchor("ANCHOR_Vendor", (-0.75, 0.65, 0), 180)
    anchor("ANCHOR_Customer_1", (-0.3, -0.84, 0))
    anchor("ANCHOR_Customer_2", (0.25, -0.84, 0))


def build_food_steamer():
    """蒸笼 + 油锅早点摊：圆泥灶上五层蒸笼（Steamer_Lid 可揭）、方灶上浅油锅 + 沥油铁架油条、案板一屉包子、竹竿挑布幌子、矮凳。"""
    mb = K.MB()
    # 蒸笼灶（x<0）
    mb.cyl(-0.75, 0, 0, 0.7, 0.36, "M_P1_Clay", seg=12, r_top=0.32)
    mb.box(-0.87, -0.36, 0.12, -0.63, -0.3, 0.32, "M_P1_Scorch")
    mb.cyl(-0.75, 0, 0.7, 0.76, 0.33, "M_P1_Iron", seg=12)
    for k in range(5):
        z = 0.76 + k * 0.13
        mb.cyl(-0.75, 0, z, z + 0.12, 0.3, "M_P1_Bamboo", seg=12)
        mb.cyl(-0.75, 0, z + 0.1, z + 0.125, 0.305, "M_P1_WoodPale", seg=12)
    # 油锅灶（x>0，方砖灶）+ 浅油锅 + 沥油架油条
    mb.box(0.3, -0.35, 0, 1.0, 0.35, 0.72, "M_P1_Brick")
    mb.box(0.55, -0.36, 0.14, 0.75, -0.34, 0.34, "M_P1_Scorch")
    mb.cyl(0.65, 0, 0.72, 0.82, 0.22, "M_P1_Iron", seg=12, r_top=0.36)
    mb.cyl(0.65, 0, 0.78, 0.8, 0.3, "M_P1_Oil", seg=12)
    mb.box(0.92, -0.3, 0.84, 1.18, 0.3, 0.85, "M_P1_Wire")                         # 沥油架
    for sy in (-1, 1):
        mb.box(0.92, sy * 0.3 - 0.01, 0.72, 0.94, sy * 0.3 + 0.01, 0.85, "M_P1_Wire")
        mb.box(1.16, sy * 0.3 - 0.01, 0.0, 1.18, sy * 0.3 + 0.01, 0.85, "M_P1_Wire")
    for k in range(5):
        y = -0.22 + k * 0.11
        mb.box(0.94, y - 0.025, 0.85, 1.16, y + 0.025, 0.895, "M_P1_Youtiao")
    mb.box(0.98, 0.3, 0.84, 1.04, 0.34, 1.2, "M_P1_Bamboo")                         # 长竹筷
    # 案板 + 一屉包子
    mb.box(-0.35, 0.45, 0.68, 0.55, 0.95, 0.73, "M_P1_WoodPale")
    for x in (-0.3, 0.5):
        for y in (0.5, 0.9):
            mb.box(x - 0.025, y - 0.025, 0, x + 0.025, y + 0.025, 0.68, "M_P1_WoodDark")
    mb.box(-0.25, 0.5, 0.73, 0.3, 0.9, 0.76, "M_P1_Bamboo")
    for k in range(10):
        mb.ico(-0.18 + (k % 5) * 0.11, 0.6 + (k // 5) * 0.18, 0.79, 0.045, "M_P1_Bun", sz=0.75)
    # 竹竿 + 布幌子（「早点」写在贴图位，白模用色块）
    mb.cyl(-1.3, 0.3, 0, 2.6, 0.03, "M_P1_Bamboo", seg=6)
    mb.box(-1.3, 0.3 - 0.015, 2.5, -0.6, 0.3 + 0.015, 2.53, "M_P1_Bamboo")
    mb.box(-1.12, 0.3 - 0.004, 1.65, -0.78, 0.3 + 0.004, 2.48, "M_P1_ClothBlue")
    mb.box(-1.08, 0.3 - 0.008, 1.95, -0.82, 0.3 + 0.008, 2.35, "M_P1_Sign")
    # 矮凳两只
    for x in (-0.2, 0.3):
        mb.box(x - 0.14, -0.95, 0.28, x + 0.14, -0.72, 0.32, "M_P1_Wood")
        for sx in (-1, 1):
            mb.box(x + sx * 0.11 - 0.02, -0.92, 0, x + sx * 0.11 + 0.02, -0.75, 0.28, "M_P1_WoodDark")
    obj(mb, "Stall", (0, 0, 0), uv=1.0)
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.1, 0.31, "M_P1_Bamboo", seg=12, r_top=0.18)
    mb.cyl(0, 0, 0.1, 0.14, 0.06, "M_P1_WoodDark", seg=6)
    obj(mb, "Steamer_Lid", (-0.75, 0, 1.41), uv=1.0)
    fx("FX_Steam", (-0.75, 0, 1.58))
    fx("FX_OilSmoke", (0.65, 0, 0.9))
    fx("FX_StoveFire_1", (-0.75, -0.33, 0.22))
    fx("FX_StoveFire_2", (0.65, -0.35, 0.24))
    anchor("ANCHOR_Vendor", (0.2, 0.0, 0), 0)
    anchor("ANCHOR_Customer_1", (-0.2, -0.84, 0))
    anchor("ANCHOR_Customer_2", (0.3, -0.84, 0))


# ================================================================= PROP_Load 挑担/推车 2
def build_load_pole():
    """逃难挑子：扁担沿 Y（前筐 -Y、后筐 +Y）；放在地上时两筐着地、扁担中点高 1.34 m（ANCHOR_Shoulder）。
    原点在扁担中点正下方地面。挑起时把整个道具抬到 ANCHOR_Shoulder 对齐挑夫右肩（1.74 m 的挑夫约 +0.1 m）。"""
    mb = K.MB()
    pts = [(0, -0.85, 1.3), (0, -0.4, 1.33), (0, 0.0, 1.34), (0, 0.4, 1.33), (0, 0.85, 1.3)]   # 微弯的扁担
    for a, b in zip(pts, pts[1:]):
        mb.hexa([(-0.035, a[1], a[2] - 0.02), (0.035, a[1], a[2] - 0.02), (0.035, b[1], b[2] - 0.02), (-0.035, b[1], b[2] - 0.02),
                 (-0.035, a[1], a[2] + 0.02), (0.035, a[1], a[2] + 0.02), (0.035, b[1], b[2] + 0.02), (-0.035, b[1], b[2] + 0.02)],
                "M_P1_Bamboo")
    for sy, contents in ((-1, "front"), (1, "back")):
        yc = sy * 0.78
        z0 = 0.0
        mb.cyl(0, yc, z0, z0 + 0.34, 0.22, "M_P1_Basket", seg=10, r_top=0.27)
        mb.cyl(0, yc, z0 + 0.32, z0 + 0.36, 0.28, "M_P1_Bamboo", seg=10)
        for k in range(4):
            a = math.pi / 4 + k * math.pi / 2
            bar(mb, (0.26 * math.cos(a), yc + 0.26 * math.sin(a), z0 + 0.35), (0, yc, 1.28), 0.006, "M_P1_Rope", seg=3)
        if contents == "front":
            mb.box(-0.2, yc - 0.18, z0 + 0.3, 0.2, yc + 0.18, z0 + 0.55, "M_P1_ClothBlue")                    # 包袱
            mb.box(-0.04, yc - 0.19, z0 + 0.5, 0.04, yc + 0.19, z0 + 0.6, "M_P1_ClothBlue")
            mb.cyl(0.08, yc - 0.05, z0 + 0.55, z0 + 0.72, 0.1, "M_P1_Iron", seg=8, r_top=0.08)             # 铁壶
            bar(mb, (0.08, yc - 0.13, z0 + 0.66), (0.08, yc - 0.22, z0 + 0.74), 0.015, "M_P1_Iron", seg=4)
        else:
            with mb.at(0, yc, z0 + 0.5, ry=90):                                                         # 被卷
                mb.cyl(0, 0, -0.26, 0.26, 0.17, "M_P1_Quilt", seg=8)
            for x in (-0.15, 0.15):
                with mb.at(x, yc, z0 + 0.5, ry=90):
                    mb.cyl(0, 0, -0.015, 0.015, 0.175, "M_P1_Rope", seg=8)
            mb.cyl(-0.1, yc + 0.08, z0 + 0.62, z0 + 0.76, 0.13, "M_P1_Iron", seg=8, r_top=0.15)            # 铁锅扣着
    obj(mb, "Load", (0, 0, 0), uv=1.0)
    anchor("ANCHOR_Shoulder", (0, 0, 1.34))


def build_load_cart():
    """独轮车（鸡公车）装家当：中间大木轮（Wheel 枢轴在轮轴）+ 轮罩 + 两侧货台 + 后把手和支腿；左右堆被卷、箱子、椅子、锅。"""
    mb = K.MB()
    R = 0.4
    mb.box(-0.07, -0.55, R + 0.05, 0.07, 0.55, R + 0.12, "M_P1_WoodDark")          # 龙骨
    for sx in (-1, 1):
        mb.box(sx * 0.07, -0.6, R + 0.08, sx * 0.55, 0.55, R + 0.13, "M_P1_Wood")    # 货台
        mb.box(sx * 0.5, -0.6, R + 0.13, sx * 0.55, 0.55, R + 0.22, "M_P1_WoodDark")
        bar(mb, (sx * 0.15, 0.3, R + 0.1), (sx * 0.3, 1.45, 0.62), 0.03, "M_P1_WoodDark", seg=6)   # 把手
        mb.box(sx * 0.25 - 0.025, 0.9 - 0.025, 0, sx * 0.25 + 0.025, 0.9 + 0.025, 0.56, "M_P1_WoodDark")   # 支腿
        mb.box(sx * 0.12 - 0.02, -0.04, R - 0.05, sx * 0.12 + 0.02, 0.04, R + 0.1, "M_P1_WoodDark")       # 轴座
    # 轮罩（拱形木架）
    for i in range(6):
        a0, a1 = math.pi * i / 6, math.pi * (i + 1) / 6
        mb.prism([(-0.5 * math.cos(a0), R + 0.12 + 0.5 * math.sin(a0) * 0.7), (-0.5 * math.cos(a1), R + 0.12 + 0.5 * math.sin(a1) * 0.7),
                  (-0.44 * math.cos(a1), R + 0.12 + 0.44 * math.sin(a1) * 0.7), (-0.44 * math.cos(a0), R + 0.12 + 0.44 * math.sin(a0) * 0.7)],
                 "x", -0.08, 0.08, "M_P1_WoodDark")
    # 左侧：被卷 + 木箱；右侧：箱子 + 倒扣椅子 + 铁锅
    with mb.at(0.31, -0.15, R + 0.36, rx=90):
        mb.cyl(0, 0, -0.35, 0.35, 0.2, "M_P1_Quilt", seg=8)
    for y in (-0.35, 0.05):
        with mb.at(0.31, y, R + 0.36, rx=90):
            mb.cyl(0, 0, -0.02, 0.02, 0.205, "M_P1_Rope", seg=8)
    crate(mb, 0.31, 0.35, R + 0.13, 0.38, 0.32, 0.3)
    crate(mb, -0.31, -0.2, R + 0.13, 0.4, 0.5, 0.34, mat="M_P1_Lacquer")
    mb.box(-0.5, -0.45, R + 0.47, -0.12, 0.05, R + 0.5, "M_P1_Brass")
    chair(mb, -0.3, 0.3, R + 0.13 + 0.97, rx=180, mat="M_P1_WoodPale")
    mb.cyl(-0.31, -0.2, R + 0.47, R + 0.6, 0.15, "M_P1_Iron", seg=8, r_top=0.19)
    bar(mb, (0.05, -0.5, R + 0.6), (0.05, 0.4, R + 0.6), 0.008, "M_P1_Rope", seg=3)
    obj(mb, "Cart", (0, 0, 0), uv=1.0)
    mb = K.MB()
    wheel_x(mb, (0, 0, 0), R - 0.03, 0.035, "M_P1_WoodDark", "M_P1_WoodDark", spokes=10, hub=0.06, seg=16, spoke_r=0.018)
    obj(mb, "Wheel", (0, 0, R), uv=1.0)
    anchor("ANCHOR_Pusher", (0, 1.65, 0), 180)


# ================================================================= PROP_JapaneseFlag 2
def rising_sun(mb, w, hgt, cx, cz, rays=16, t=0.004):
    """旭日旗旗面：在 XZ 平面（厚 t），旗杆边在 x=0；按扇区拼 16 道红白相间的光芒 + 中心红日。"""
    corners = [(0, 0), (w, 0), (w, hgt), (0, hgt)]

    def hit(a):
        dx, dz = math.cos(a), math.sin(a)
        best = 1e9
        for v, d in ((0 - cx, dx), (w - cx, dx)):
            if abs(d) > 1e-9:
                s = v / d
                if s > 0:
                    best = min(best, s)
        for v, d in ((0 - cz, dz), (hgt - cz, dz)):
            if abs(d) > 1e-9:
                s = v / d
                if s > 0:
                    best = min(best, s)
        return (cx + dx * best, cz + dz * best)
    for k in range(rays):
        a0 = 2 * math.pi * k / rays + math.pi / rays
        a1 = a0 + 2 * math.pi / rays
        pts = [(cx, cz), hit(a0)]
        cs = []
        for (x, z) in corners:
            ac = math.atan2(z - cz, x - cx) % (2 * math.pi)
            if (ac - a0) % (2 * math.pi) < (a1 - a0):
                cs.append(((ac - a0) % (2 * math.pi), (x, z)))
        pts += [p for _, p in sorted(cs)]
        pts.append(hit(a1))
        mb.prism(pts, "y", -t, t, "M_P1_FlagRed" if k % 2 == 0 else "M_P1_FlagWhite")
    with mb.at(cx, 0, cz, rx=90):
        mb.cyl(0, 0, -t * 1.6, t * 1.6, hgt * 0.26, "M_P1_FlagRed", seg=16)


def build_flag_pole():
    """哨卡独立高旗杆：沙袋压住的方木座 + 6.5 m 杆 + 升旗绳 + 旭日旗（Cloth 单独子物体，枢轴在杆顶挂点，可做风动）。"""
    mb = K.MB()
    mb.box(-0.35, -0.35, 0, 0.35, 0.35, 0.3, "M_P1_Concrete")
    mb.box(-0.1, -0.1, 0.3, 0.1, 0.1, 0.55, "M_P1_WoodDark")
    for k in range(4):
        a = k * 90
        sack(mb, 0.5 * math.cos(math.radians(a)), 0.5 * math.sin(math.radians(a)), 0, a + 90, "M_P1_Sandbag", L=0.6)
        sack(mb, 0.5 * math.cos(math.radians(a + 45)) * 1.1, 0.5 * math.sin(math.radians(a + 45)) * 1.1, 0.0, a + 135,
             "M_P1_SandbagDark", L=0.45)
    mb.cyl(0, 0, 0.3, 6.5, 0.05, "M_P1_WoodDark", seg=8, r_top=0.035)
    mb.ico(0, 0, 6.56, 0.07, "M_P1_Brass")
    mb.box(0.045, -0.006, 0.9, 0.055, 0.006, 6.4, "M_P1_Rope")
    mb.box(0.04, -0.03, 1.2, 0.09, 0.03, 1.26, "M_P1_Steel")                        # 系绳羊角
    obj(mb, "Pole", (0, 0, 0), uv=1.0)
    mb = K.MB()
    with mb.at(0.04, 0, -1.2):
        rising_sun(mb, 1.8, 1.2, 0.68, 0.6)
    obj(mb, "Cloth", (0, 0, 6.35), uv=1.0)


def hinomaru(mb, w, hgt, t=0.004, rdisc=None):
    mb.box(0, -t, 0, w, t, hgt, "M_P1_FlagWhite")
    with mb.at(w / 2, 0, hgt / 2, rx=90):
        mb.cyl(0, 0, -t * 1.8, t * 1.8, rdisc or hgt * 0.3, "M_P1_FlagRed", seg=16)


def build_flag_wall():
    """墙挂/门楣日旗：Flag_Hung（门楣上钉着横挂的日章旗 + 顶杆）与 Flag_Crossed（铁托架上交叉两面小旗）。原点 = 墙面上旗下沿中点，墙在 +Y。"""
    mb = K.MB()
    with mb.at(-0.75, -0.012, 0):
        hinomaru(mb, 1.5, 1.0)
    bar(mb, (-0.82, -0.02, 1.0), (0.82, -0.02, 1.0), 0.015, "M_P1_WoodDark", seg=6)
    for x in (-0.82, 0.82):
        mb.box(x - 0.015, -0.03, 0.97, x + 0.015, 0.0, 1.03, "M_P1_Steel")
    for x, z in ((-0.73, 0.03), (0.73, 0.03)):
        mb.box(x - 0.01, -0.02, z - 0.01, x + 0.01, -0.01, z + 0.01, "M_P1_Steel")
    obj(mb, "Flag_Hung", (0, 0, 0), uv=1.0)
    mb = K.MB()
    mb.box(-0.12, -0.03, 0, 0.12, 0.0, 0.14, "M_P1_Steel")                          # 托架
    mb.box(-0.04, -0.12, 0.02, 0.04, -0.03, 0.1, "M_P1_Steel")
    obj(mb, "Bracket", (0, 0, 1.25), uv=1.0)
    for nm, sx in (("Flag_Crossed_L", -1), ("Flag_Crossed_R", 1)):
        mb = K.MB()
        with mb.at(0, 0, 0, ry=sx * 35, rx=-12):
            mb.cyl(0, 0, 0, 1.3, 0.015, "M_P1_WoodDark", seg=6)
            mb.ico(0, 0, 1.33, 0.03, "M_P1_Brass")
            with mb.at(0, 0, 0.75):
                if sx < 0:
                    mb.box(-0.6, -0.004, 0, -0.015, 0.004, 0.42, "M_P1_FlagWhite")
                    with mb.at(-0.31, 0, 0.21, rx=90):
                        mb.cyl(0, 0, -0.007, 0.007, 0.125, "M_P1_FlagRed", seg=14)
                else:
                    mb.box(0.015, -0.004, 0, 0.6, 0.004, 0.42, "M_P1_FlagWhite")
                    with mb.at(0.31, 0, 0.21, rx=90):
                        mb.cyl(0, 0, -0.007, 0.007, 0.125, "M_P1_FlagRed", seg=14)
        obj(mb, nm, (0, -0.08, 1.3), uv=1.0)


# ================================================================= PROP_WantedPoster 告示/通缉 3（文字贴图）
POSTERS = {
    "A": dict(W=0.6, H=0.85, paper="M_P1_TexPaper", title="佈告",
              cols=["爲維持地方治安起見", "自卽日起本鎭實行宵禁", "每晚九時至翌晨六時", "禁止一切行人出入", "違者以通匪論處", "決不寬貸 此佈"],
              foot="昭和十六年　月　日", seal=True, portrait=False),
    "B": dict(W=0.55, H=0.8, paper="M_P1_TexPaperB", title="通緝",
              cols=["匪犯一名", "年約三十", "身長五尺餘", "密報者重賞", "窩藏者同罪"],
              foot="憲兵隊", seal=True, portrait=True),
    "C": dict(W=0.6, H=0.85, paper="M_P1_TexPaperC", title="告示",
              cols=["凡本鎭居民", "限十日內赴維持會", "領取良民證", "逾期不領者", "一律以匪論處"],
              foot="維持會　啓", seal=False, portrait=False),
}
FONT_CANDIDATES = [
    os.path.expanduser("~/Library/Fonts/SourceHanSerifCN-Heavy.otf"),
    os.path.expanduser("~/Library/Fonts/SourceHanSerifCN-Bold.otf"),
    "/Library/Fonts/SourceHanSerifCN-Heavy.otf",
    "/usr/share/fonts/opentype/noto/NotoSerifCJK-Bold.ttc",
    "C:/Windows/Fonts/simsun.ttc",
    "/System/Library/Fonts/Supplemental/Songti.ttc",
    "/System/Library/Fonts/Songti.ttc",
]


def _font():
    for p in FONT_CANDIDATES:
        if os.path.exists(p):
            try:
                return bpy.data.fonts.load(p, check_existing=True)
            except Exception:
                continue
    return None


def _smooth_noise(np, rng, n, size):
    g = rng.random((n + 1, n + 1))
    t = np.linspace(0, n, size, endpoint=False)
    i = t.astype(int)
    f = t - i
    f = f * f * (3 - 2 * f)
    a, b, c, d = g[i][:, i], g[i][:, i + 1], g[i + 1][:, i], g[i + 1][:, i + 1]
    fy, fx = f[:, None], f[None, :]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def render_poster_tex(key, path, size=1024):
    """在临时场景里用 Workbench 平光渲出告示纸面（文字竖排右起），再用 numpy 做旧/撕/雨淋。"""
    import numpy as np
    spec = POSTERS[key]
    Wp, Hp = spec["W"], spec["H"]
    sx = Hp / Wp                    # 贴图是方的、纸是竖长的：字在贴图里横向拉宽，贴到纸上才是方字
    sc = bpy.data.scenes.new("P1_TexScene")
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_shadows = False
    sc.display.shading.show_cavity = False
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    made = []

    def link(ob):
        sc.collection.objects.link(ob)
        made.append(ob)
        return ob
    cd = bpy.data.cameras.new("P1_TexCam")
    cd.type = "ORTHO"
    cd.ortho_scale = 1.0
    cam = link(bpy.data.objects.new("P1_TexCam", cd))
    cam.location = (0, 0, 5)
    sc.camera = cam

    def quad(x0, y0, x1, y1, mat, z=0.0):
        mb = K.MB()
        mb.box(x0, y0, z - 0.001, x1, y1, z, mat)
        ob = mb.to_object("P1_TexQuad", collection=sc.collection)
        made.append(ob)
        return ob
    quad(-0.6, -0.6, 0.6, 0.6, spec["paper"], z=-0.01)
    font = _font()

    def text(s, x, y, size_, mat, align_y="TOP"):
        if font is None:                    # 没字体：每个字一个墨块
            n = s.count("\n") + 1 if "\n" in s else len(s)
            vertical = "\n" in s
            for k in range(n if vertical else len(s)):
                cx = x if vertical else x + (k - len(s) / 2 + 0.5) * size_ / sx
                cy = (y - (k + 0.5) * size_) if vertical else y - size_ / 2
                quad(cx - size_ * 0.4 / sx, cy - size_ * 0.4, cx + size_ * 0.4 / sx, cy + size_ * 0.4, mat, z=0.001)
            return
        cu = bpy.data.curves.new("P1_TexText", "FONT")
        cu.body = s
        cu.font = font
        cu.size = size_
        cu.align_x = "CENTER"
        cu.align_y = align_y
        cu.space_line = 0.62
        ob = link(bpy.data.objects.new("P1_TexText", cu))
        ob.location = (x, y, 0.002)
        ob.scale = (sx * 1.0, 1.0, 1.0)
        ob.data.materials.append(K.get_mat(mat))
    # 边框：双线
    m = 0.045
    for (a, b, c_, d) in ((-0.5 + m, 0.5 - m - 0.006, 0.5 - m, 0.5 - m), (-0.5 + m, -0.5 + m, 0.5 - m, -0.5 + m + 0.006),
                          (-0.5 + m, -0.5 + m, -0.5 + m + 0.006 * 0.7, 0.5 - m), (0.5 - m - 0.006 * 0.7, -0.5 + m, 0.5 - m, 0.5 - m)):
        quad(a, b, c_, d, "M_P1_TexInk", z=0.001)
    text(spec["title"], 0.0, 0.44, 0.15, "M_P1_TexInk")
    quad(-0.4, 0.255, 0.4, 0.262, "M_P1_TexInk", z=0.001)
    cols = spec["cols"]
    csz = min(0.095, 0.5 / (0.6 * max(len(c) for c in spec["cols"])))
    top = 0.225
    if spec["portrait"]:            # 通缉：中上一张木刻画像，字列放在画像下面
        quad(-0.17, -0.05, 0.17, 0.235, "M_P1_TexInk", z=0.001)
        quad(-0.16, -0.04, 0.16, 0.225, "M_P1_TexFace", z=0.0015)
        mb = K.MB()
        mb.cyl(0, 0.155, 0.002, 0.003, 0.064, "M_P1_TexInk", seg=16)                    # 头发
        mb.cyl(0, 0.108, 0.0032, 0.0036, 0.06, "M_P1_TexPaperB", seg=16)                # 脸（盖住头发下半）
        for sx_ in (-1, 1):                                                             # 耳
            mb.box(sx_ * 0.062 - 0.008, 0.095, 0.003, sx_ * 0.062 + 0.008, 0.125, 0.0034, "M_P1_TexPaperB")
        mb.box(-0.04, 0.128, 0.004, -0.01, 0.133, 0.005, "M_P1_TexInk")                 # 眉
        mb.box(0.01, 0.128, 0.004, 0.04, 0.133, 0.005, "M_P1_TexInk")
        mb.box(-0.032, 0.115, 0.004, -0.014, 0.123, 0.005, "M_P1_TexInk")               # 眼
        mb.box(0.014, 0.115, 0.004, 0.032, 0.123, 0.005, "M_P1_TexInk")
        mb.box(-0.004, 0.09, 0.004, 0.004, 0.112, 0.005, "M_P1_TexGrey")                # 鼻
        mb.box(-0.02, 0.075, 0.004, 0.02, 0.08, 0.005, "M_P1_TexInk")                  # 嘴
        mb.prism([(-0.15, -0.04), (0.15, -0.04), (0.08, 0.045), (-0.08, 0.045)], "z", 0.002, 0.003, "M_P1_TexInk")  # 肩
        mb.prism([(-0.03, 0.045), (0.03, 0.045), (0.0, -0.01)], "z", 0.003, 0.004, "M_P1_TexPaperB")  # 领口
        ob = mb.to_object("P1_TexFaceMesh", collection=sc.collection)
        made.append(ob)
        top = -0.075
        csz = 0.088
    n = len(cols)
    span = 0.7
    for k, s in enumerate(cols):             # 竖排，右起
        x = span / 2 - (k + 0.5) * span / n
        text("\n".join(s.replace(" ", "　")), x, top, csz, "M_P1_TexInk")
    text(spec["foot"], 0.0, -0.37, 0.042, "M_P1_TexInk")
    if spec["seal"]:                         # 朱印
        quad(0.17, -0.43, 0.3, -0.3, "M_P1_TexRed", z=0.003)
        quad(0.185, -0.415, 0.285, -0.315, spec["paper"], z=0.0035)
        quad(0.2, -0.4, 0.27, -0.33, "M_P1_TexRed", z=0.004)
    sc.render.filepath = path
    bpy.ops.render.render(write_still=True, scene=sc.name)
    for o in made:
        bpy.data.objects.remove(o, do_unlink=True)
    bpy.data.cameras.remove(cd)
    bpy.data.scenes.remove(sc)
    # ---- 后期（numpy）：纸纹、做旧；B 加脏污；C 雨淋：墨往下流、水渍圈、纸色变暗
    img = bpy.data.images.load(path, check_existing=False)
    Wd, Hd = img.size
    px = np.empty(Wd * Hd * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    a = px.reshape(Hd, Wd, 4)
    rgb = a[:, :, :3].astype(np.float64)
    rng = np.random.default_rng({"A": 11, "B": 23, "C": 37}[key])
    lum = rgb.mean(axis=2)
    ink = np.clip((0.55 - lum) / 0.45, 0, 1)                     # 墨/朱的遮罩
    fiber = rng.random((Hd, Wd)) * 0.05 - 0.025
    blot = _smooth_noise(np, rng, 9, Hd)
    yy, xx = np.mgrid[0:Hd, 0:Wd]
    edge = np.minimum(np.minimum(xx, Wd - 1 - xx), np.minimum(yy, Hd - 1 - yy)) / (Wd * 0.5)
    age = np.clip(0.18 - edge, 0, 0.18) / 0.18                    # 边缘泛黄
    tint = np.array([0.0, -0.03, -0.08])
    rgb = rgb + fiber[:, :, None] + (blot[:, :, None] - 0.5) * 0.08 + age[:, :, None] * (tint - 0.08)
    if key == "A":
        rgb += 0.02
    if key == "B":
        dirt = _smooth_noise(np, rng, 5, Hd)
        rgb -= np.clip(dirt - 0.55, 0, 1)[:, :, None] * 0.35 * np.array([1.0, 1.05, 1.15])
        rgb -= (np.clip(0.3 - yy / Hd, 0, 0.3) / 0.3)[:, :, None] * 0.12               # 下沿溅泥
    if key == "C":
        drip_len = np.clip(rng.random(Wd) ** 2.5 * 1.8, 0.05, 1.4)                    # 每列流淌长度（稀疏的细流）
        drip_len = np.convolve(drip_len, np.ones(3) / 3, mode="same")
        run = ink.copy()
        for k in range(1, 70, 2):                                                       # 行 0 在底部：往下流 = 往小行号拖
            sh = np.zeros_like(ink)
            sh[:-k, :] = ink[k:, :]
            fall = np.clip(1 - k / (70 * np.maximum(drip_len, 1e-3)), 0, 1)[None, :]
            run = np.maximum(run, sh * fall * 0.55)
        rgb = rgb * (1 - run[:, :, None] * 0.55) + run[:, :, None] * 0.55 * np.array([0.18, 0.17, 0.17])
        wet = _smooth_noise(np, rng, 3, Hd)
        tide = np.exp(-((wet - 0.6) / 0.03) ** 2)                                       # 水渍圈（淡）
        rgb -= (np.clip(wet - 0.6, 0, 1) * 0.3)[:, :, None] + tide[:, :, None] * 0.05
        rgb = (rgb - 0.5) * 0.82 + 0.46                                                 # 湿纸：发灰、对比降低
        rgb -= (np.clip(0.45 - yy / Hd, 0, 0.45))[:, :, None] * 0.25                    # 下半吸水更暗
    a[:, :, :3] = np.clip(rgb, 0, 1)
    a[:, :, 3] = 1.0
    img.pixels.foreach_set(a.reshape(-1).astype(np.float32))
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return img


def _clip(poly, c, above):
    """凸多边形 (u,v) 按直线 u+v=c 裁剪：above=True 保留 u+v>=c 一侧。"""
    f = (lambda q: q[0] + q[1] - c) if above else (lambda q: c - q[0] - q[1])
    out = []
    for k in range(len(poly)):
        a, b = poly[k], poly[(k + 1) % len(poly)]
        fa, fb = f(a), f(b)
        if fa >= 0:
            out.append(a)
        if (fa >= 0) != (fb >= 0):
            t = fa / (fa - fb)
            out.append((a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t))
    return out


def poster_sheet(name, Wp, Hp, front_mat, nx, nz, keep=None, deform=None, fold=None, y0=-0.003):
    """纸面网格（XZ 平面、正面朝 -Y，背面贴墙）：keep(u,v) 决定格子留不留（撕破），deform(u,v)->(dx,dy,dz)（起翘/鼓包），
    fold=(c, lift)：u+v>c 的角沿折线翻折到前面（露出纸背）。UV = 纸面上的 (u,v)。"""
    verts, faces, uvs, mats = [], [], [], []
    keep = keep or (lambda u, v: True)
    deform = deform or (lambda u, v: (0.0, 0.0, 0.0))

    def P(u, v):
        dx, dy, dz = deform(u, v)
        return Vector(((u - 0.5) * Wp + dx, y0 + dy, v * Hp + dz))
    if fold:
        c, lift = fold
        p0 = Vector(((c - 1.0 - 0.5) * Wp, 0, 1.0 * Hp))       # 折线上一点 (u=c-1, v=1)
        d = Vector((Wp, 0, -Hp)).normalized()

    def refl(p):
        q = Vector((p.x, 0, p.z))
        f = p0 + d * (q - p0).dot(d)
        r = 2 * f - q
        return Vector((r.x, y0 - lift, r.z))
    for i in range(nx):
        for j in range(nz):
            u0, u1, v0, v1 = i / nx, (i + 1) / nx, j / nz, (j + 1) / nz
            uc, vc = (u0 + u1) / 2, (v0 + v1) / 2
            corner = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
            if not keep(uc, vc) and not (fold is not None and uc + vc > fold[0]):
                continue
            parts = [(corner, False)]
            if fold is not None:                # 跨折线的格子按折线精确切成两块（折边是直线）
                parts = [(q, f) for q, f in ((_clip(corner, fold[0], False), False), (_clip(corner, fold[0], True), True))
                         if len(q) >= 3]
            for poly, folded in parts:
                if not folded and not keep(uc, vc):
                    continue
                pts = [P(u, v) for u, v in poly]
                if folded:
                    pts = [refl(p) for p in pts]
                n = len(poly)
                for side in (0, 1):             # 0 正面（贴图），1 背面（纸背色，贴墙一侧）
                    b = len(verts)
                    off = Vector((0, 0.0012 if side else 0.0, 0))
                    if folded:
                        off = -off
                    verts += [tuple(p + off) for p in pts]
                    order = list(range(n)) if side == 0 else list(reversed(range(n)))
                    faces.append([b + k for k in order])
                    uvs.append([poly[k] for k in order])
                    mats.append(side)
    me = bpy.data.meshes.new(name)
    me.from_pydata(verts, [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for poly, fuv in zip(me.polygons, uvs):
        poly.material_index = mats[poly.index]
        for li, uv in zip(poly.loop_indices, fuv):
            uvl.data[li].uv = uv
    me.materials.append(front_mat)
    me.materials.append(K.get_mat("M_P1_PaperBack"))
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def poster_material(key, img):
    mat = bpy.data.materials.new(f"M_P1_Poster_{key}")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = img
    nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.5 if key == "C" else 0.9
    mat.diffuse_color = K.hex_rgba(K.PALETTE[POSTERS[key]["paper"]])
    return mat


def build_poster(key):
    """告示/通缉：A 刚贴上（布告·宵禁，右上角微翘），B 撕破（通缉·画像，右上角翻折、左下撕掉一块），C 雨打湿（告示·良民证，墨往下流、纸鼓包、左下角卷起，墙上一道水痕）。
    原点 = 纸下沿中点、贴墙面（墙在 +Y）。"""
    spec = POSTERS[key]
    Wp, Hp = spec["W"], spec["H"]
    out_dir = os.path.join(REPO, "Project_rupu", "Assets", "Art", "Props", f"PROP_Poster_{key}")
    os.makedirs(out_dir, exist_ok=True)
    img = render_poster_tex(key, os.path.join(out_dir, f"T_Poster_{key}_D.png"))
    mat = poster_material(key, img)
    if key == "A":
        poster_sheet("Poster", Wp, Hp, mat, 6, 8,
                     deform=lambda u, v: (0.0, -0.05 * max(0.0, u + v - 1.7) ** 1.5 * 6, 0.0))
    elif key == "B":
        jit = [0.03 * math.sin(k * 2.7) + 0.02 * math.sin(k * 7.3) for k in range(40)]

        def keep(u, v):
            i = int(u * 16)
            return v > 0.1 + 0.32 * (1 - u) ** 1.4 + jit[i] and not (u > 0.82 and v < 0.12 + jit[i + 3])
        poster_sheet("Poster", Wp, Hp, mat, 16, 22, keep=keep, fold=(1.62, 0.006))
        mb = K.MB()                                                                   # 撕剩的纸边
        for k, (x, z, w, hh) in enumerate(((-0.24, 0.02, 0.05, 0.03), (-0.17, 0.05, 0.04, 0.04), (-0.21, 0.13, 0.03, 0.03))):
            mb.box(x, -0.0025, z, x + w, -0.0012, z + hh, "M_P1_PaperBack")
        obj(mb, "Paper_Remnants", (0, 0, 0))
    else:
        def deform(u, v):
            bul = -0.008 * math.sin(math.pi * u) * math.sin(math.pi * v)
            d = max(0.0, 0.32 - math.hypot(u, v))
            return (0.03 * d, bul - 0.6 * d * d, 0.05 * d - 0.006 * (1 - v))
        poster_sheet("Poster", Wp, Hp, mat, 10, 14, deform=deform)
        mb = K.MB()                                                                   # 墙上水痕（纸下沿往下的湿印）
        mb.prism([(-0.22, 0.02), (0.24, 0.02), (0.2, -0.08), (-0.18, -0.1)], "y", -0.0015, -0.0006, "M_P1_WetStain")
        for x, L, w in ((-0.12, 0.3, 0.03), (0.02, 0.22, 0.02), (0.15, 0.36, 0.025)):          # 几道往下淌的水痕
            mb.prism([(x - w, -0.05), (x + w, -0.05), (x + w * 0.4, -L), (x - w * 0.4, -L)], "y", -0.0015, -0.0006, "M_P1_WetStain")
        obj(mb, "NOCOL_WetStain", (0, 0, 0.0))
    anchor("ANCHOR_Read", (0, -0.9, 0), 0)


# ================================================================= ENV_BombCrater 弹坑 2
def build_crater_a():
    """路面小弹坑：石板路被炸出一个浅坑（半径约 1.3 m），坑底积水，周围石板碎裂翘起、碎块四散。"""
    rng = random.Random(1941)
    mb = K.MB()
    crater(mb, rng, 0.55, 1.0, 1.45, 0.22, seg=16, mats=("M_P1_EarthDark", "M_P1_Earth", "M_P1_Mud"))
    mb.cyl(0, 0, -0.025, -0.012, 0.45, "M_P1_Puddle", seg=12)
    for k in range(9):                                         # 坑沿裂开翘起的路面石板
        a = 2 * math.pi * k / 9 + rng.uniform(-0.2, 0.2)
        r = 1.0 + rng.uniform(-0.1, 0.25)
        with mb.at(r * math.cos(a), r * math.sin(a), 0.05, rz=math.degrees(a) - 90, rx=rng.uniform(-35, -12)):
            mb.box(-0.22, -0.4, 0, 0.22, 0.05, 0.06, "M_P1_Stone" if k % 3 else "M_P1_StoneDark")
    for k in range(10):                                        # 完整的路面石板残片（环外，平放）
        a = 2 * math.pi * k / 10 + 0.3
        r = 1.65 + rng.uniform(0, 0.4)
        with mb.at(r * math.cos(a), r * math.sin(a), 0, rz=math.degrees(a) + rng.uniform(-20, 20)):
            mb.box(-0.25, -0.18, 0, 0.25, 0.18, 0.04, "M_P1_Stone")
    for k in range(18):
        a = rng.uniform(0, 2 * math.pi)
        r = rng.uniform(1.2, 2.4)
        s = rng.uniform(0.05, 0.12)
        with mb.at(r * math.cos(a), r * math.sin(a), 0, rz=rng.uniform(0, 90)):
            mb.box(-s, -s * 0.8, 0, s, s * 0.8, s, "M_P1_Rubble" if k % 2 else "M_P1_StoneDark")
    obj(mb, "Crater", (0, 0, 0), uv=2.0)


def build_crater_b():
    """靠墙大弹坑：墙脚被炸出半圆大坑（半径约 2.8 m），墙面炸塌一块、熏黑；坑沿翻起大石板、断砖、半截门槛。墙在 +Y。"""
    rng = random.Random(1942)
    mb = K.MB()
    crater(mb, rng, 1.2, 2.2, 3.1, 0.5, a0=math.pi, a1=2 * math.pi, seg=14)       # 只做墙前半圆（-Y 一侧）
    # 墙前那条边：坑沿靠墙的一段土坡
    mb.prism([(-3.1, 0.0), (3.1, 0.0), (2.2, 0.45), (-2.2, 0.45)], "y", -0.05, 0.6, "M_P1_Mud")
    # 墙：6 m 长、0.35 厚、3 m 高，中间炸出缺口（参差墙头）、底部被掏空
    wy0, wy1 = 0.6, 0.95
    mb.prism([(-3.2, 0.0), (-1.1, 0.0), (-1.1, 2.3), (-1.6, 2.8), (-3.2, 3.0)], "y", wy0, wy1, "M_P1_Plaster")
    mb.prism([(1.2, 0.0), (3.2, 0.0), (3.2, 3.0), (1.7, 2.9), (1.2, 2.0)], "y", wy0, wy1, "M_P1_Plaster")
    mb.prism([(-1.1, 1.6), (-0.3, 2.1), (0.6, 1.9), (1.2, 1.4), (1.2, 2.0), (-1.1, 2.3)], "y", wy0, wy1, "M_P1_Plaster")  # 缺口上方的残墙
    mb.prism([(-1.1, 0.0), (1.2, 0.0), (1.2, 0.35), (-1.1, 0.35)], "y", wy0 + 0.05, wy1, "M_P1_Brick")
    for (x0, z0, x1, z1) in ((-2.9, 0.0, -1.2, 1.0), (1.3, 0.0, 2.8, 0.9)):
        mb.box(x0, wy0 - 0.01, z0, x1, wy0, z1, "M_P1_PlasterDirty")
    for pts in ([(-2.0, 0.35), (-1.1, 0.35), (-1.1, 2.25), (-1.5, 2.6), (-1.9, 1.4)],        # 熏黑（只在缺口两侧和上方的残墙上）
                [(1.2, 0.35), (2.1, 0.35), (2.3, 1.2), (1.7, 2.4), (1.2, 1.95)],
                [(-1.1, 1.7), (-0.3, 2.15), (0.6, 1.95), (1.2, 1.45), (1.2, 1.95), (-1.1, 2.25)]):
        mb.prism(pts, "y", wy0 - 0.012, wy0 - 0.004, "M_P1_Scorch")
    mb.box(-3.3, wy0 - 0.08, 3.0, -1.5, wy1 + 0.08, 3.12, "M_Roof_Tile")
    mb.box(1.6, wy0 - 0.08, 2.9, 3.3, wy1 + 0.08, 3.02, "M_Roof_Tile")
    # 翻起的大石板（靠坑沿，斜立）
    for k in range(7):
        a = math.pi + math.pi * (k + 0.5) / 7 + rng.uniform(-0.1, 0.1)
        r = 2.1 + rng.uniform(-0.1, 0.3)
        with mb.at(r * math.cos(a), r * math.sin(a), 0.2, rz=math.degrees(a) - 90, rx=rng.uniform(-70, -40)):
            mb.box(-0.4, -0.9, 0, 0.4, 0.0, 0.1, "M_P1_Stone" if k % 2 else "M_P1_StoneDark")
    # 坑底：塌下来的砖堆、半截门槛（石条）
    for k in range(26):
        x = rng.uniform(-1.4, 1.4)
        y = rng.uniform(-1.2, 0.5)
        s = rng.uniform(0.08, 0.16)
        with mb.at(x, y, 0.0, rz=rng.uniform(0, 180), rx=rng.uniform(-20, 20)):
            mb.box(-s * 1.8, -s * 0.9, 0, s * 1.8, s * 0.9, s, "M_P1_Brick" if k % 3 else "M_P1_Plaster")
    with mb.at(0.4, -0.6, 0.15, rz=24, ry=-14):
        mb.box(-0.9, -0.15, 0, 0.9, 0.15, 0.2, "M_P1_StoneDark")
    for k in range(16):
        a = rng.uniform(math.pi, 2 * math.pi)
        r = rng.uniform(2.9, 4.0)
        s = rng.uniform(0.06, 0.14)
        with mb.at(r * math.cos(a), r * math.sin(a), 0, rz=rng.uniform(0, 90)):
            mb.box(-s, -s, 0, s, s, s * 0.8, "M_P1_Rubble")
    obj(mb, "Crater", (0, 0, 0), uv=2.0)


# ================================================================= ENV_Barricade 街垒/拒马 3
def build_barricade_a():
    """家具门板街垒：拆下的门板斜靠成一排，后面倒放的八仙桌、侧翻的衣柜、椅子、木箱、米袋、木桶、车轮——居民/守军仓促堵街。约 5 m 宽。"""
    rng = random.Random(7)
    mb = K.MB()
    for k, x in enumerate((-1.9, -1.0, -0.05, 0.9, 1.85)):                # 门板（前排斜靠）
        with mb.at(x + rng.uniform(-0.08, 0.08), -0.35, 0, rz=rng.uniform(-6, 6), rx=-rng.uniform(18, 30)):
            mb.box(-0.45, -0.03, 0, 0.45, 0.03, 1.9 - 0.15 * (k % 2), "M_Wood_Dark" if k % 2 else "M_P1_WoodGrey")
            for z in (0.35, 1.0, 1.6):
                mb.box(-0.4, -0.05, z, 0.4, -0.03, z + 0.08, "M_P1_WoodDark")
    with mb.at(-1.3, 0.55, 0):                                            # 侧翻的衣柜
        mb.box(-0.95, -0.3, 0, 0.95, 0.3, 0.6, "M_P1_Lacquer")
        mb.box(-0.9, -0.31, 0.05, 0.9, -0.3, 0.55, "M_P1_WoodDark")
        mb.box(-0.05, -0.33, 0.25, 0.05, -0.31, 0.35, "M_P1_Brass")
    with mb.at(0.6, 0.55, 0, rz=8):                                       # 四脚朝天的八仙桌
        mb.box(-0.5, -0.5, 0, 0.5, 0.5, 0.05, "M_P1_Wood")
        mb.box(-0.47, -0.47, 0.05, 0.47, 0.47, 0.14, "M_P1_WoodDark")
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.box(sx * 0.44 - 0.035, sy * 0.44 - 0.035, 0.05, sx * 0.44 + 0.035, sy * 0.44 + 0.035, 0.85, "M_P1_WoodDark")
    chair(mb, -0.2, 0.75, 0.6, rz=30, ry=75)
    chair(mb, 1.8, 0.4, 0.0, rz=-120, rx=-80)
    chair(mb, -1.5, 0.55, 0.6, rz=200)
    crate(mb, 2.3, 0.2, 0, 0.55, 0.5, 0.5, rz=12)
    crate(mb, 2.3, 0.2, 0.5, 0.45, 0.4, 0.4, rz=-8)
    crate(mb, -2.4, 0.1, 0, 0.6, 0.5, 0.55, rz=-15)
    for k, (x, y, z, rz) in enumerate(((-0.6, 0.25, 0, 10), (-0.1, 0.3, 0, -20), (-0.35, 0.3, 0.2, 5), (1.2, 0.0, 0, 70))):
        sack(mb, x, y, z, rz, "M_P1_Cloth" if k % 2 else "M_P1_Sandbag", L=0.6, Wd=0.38, Hh=0.24)
    mb.cyl(0.15, 0.1, 0.0, 0.75, 0.25, "M_P1_Wood", seg=10)              # 木桶
    for z in (0.12, 0.6):
        mb.cyl(0.15, 0.1, z, z + 0.04, 0.255, "M_P1_Iron", seg=10)
    with mb.at(2.4, 0.75, 0.0, rz=90):                                    # 斜靠的板车轮
        with mb.at(0, 0, 0, rx=-15):
            wheel_x(mb, (0, 0, 0.5), 0.48, 0.03, "M_P1_WoodDark", "M_P1_WoodDark", spokes=8, hub=0.07, seg=14, spoke_r=0.02)
    obj(mb, "Barricade", (0, 0, 0), uv=1.0)
    mb = K.MB()
    mb.box(-2.7, -0.7, 0, 2.7, 1.0, 1.7, "M_P1_Wood")
    obj(mb, "COL_Barricade", (0, 0, 0), uv=1.0)


def build_barricade_b():
    """铁丝网路障：一排打进地里的木桩（6 根）拉四道带刺铁丝 + 交叉斜拉，桩前地上一卷蛇腹铁丝网，桩上挂「禁止通行」木牌（色块）。
    铁丝本身是 NOCOL_Wire（不加碰撞），整体挡人用 COL_Fence。"""
    rng = random.Random(9)
    mb = K.MB()
    xs = [-2.5 + k for k in range(6)]
    for k, x in enumerate(xs):
        with mb.at(x, 0, 0, rx=rng.uniform(-4, 4), ry=rng.uniform(-5, 5)):
            mb.cyl(0, 0, 0, 1.45, 0.06, "M_P1_WoodGrey" if k % 2 else "M_P1_Wood", seg=6, r_top=0.05)
            mb.cyl(0, 0, 1.45, 1.52, 0.05, "M_P1_WoodDark", seg=6, r_top=0.01)
        bar(mb, (x, 0.0, 1.2), (x + (0.6 if k < 3 else -0.6), 0.7, 0.0), 0.03, "M_P1_WoodDark", seg=5)       # 斜撑
    sign = K.MB()
    sign.box(-0.35, -0.08, 0.85, 0.35, -0.06, 1.2, "M_P1_Sign")
    for k in range(4):
        sign.box(-0.27 + k * 0.145, -0.085, 0.94, -0.17 + k * 0.145, -0.08, 1.1, "M_P1_Paint")
    sign.box(-0.004, -0.07, 1.2, 0.004, -0.06, 1.32, "M_P1_Wire")
    obj(sign, "Sign", (-0.5, 0, 0), uv=1.0)
    mb.box(-0.06, -0.07, 0, 0.06, 0.07, 0.25, "M_P1_Wood")
    obj(mb, "Posts", (0, 0, 0), uv=1.0)
    w = K.MB()
    for z in (0.3, 0.65, 1.0, 1.35):                                       # 四道横铁丝 + 刺
        bar(w, (xs[0], -0.06, z), (xs[-1], -0.06, z - 0.02), 0.006, "M_P1_Wire", seg=3)
        for k in range(21):
            x = xs[0] + 0.12 + k * 0.24
            w.box(x - 0.025, -0.065, z - 0.003, x + 0.025, -0.055, z + 0.003, "M_P1_Wire")
            w.box(x - 0.003, -0.08, z - 0.003, x + 0.003, -0.04, z + 0.003, "M_P1_Wire")
    for a, b in zip(xs, xs[1:]):                                           # 交叉斜拉
        bar(w, (a, -0.06, 0.2), (b, -0.06, 1.3), 0.005, "M_P1_Wire", seg=3)
        bar(w, (a, -0.06, 1.3), (b, -0.06, 0.2), 0.005, "M_P1_Wire", seg=3)
    R, yc, zc = 0.38, -0.7, 0.36                                          # 蛇腹铁丝网（螺旋）
    turns, per = 11, 12
    prev = None
    for k in range(turns * per + 1):
        t = k / per * 2 * math.pi
        x = xs[0] + (xs[-1] - xs[0]) * k / (turns * per)
        p = (x, yc + R * math.cos(t), zc + R * math.sin(t) * 0.95)
        if prev is not None:
            bar(w, prev, p, 0.006, "M_P1_Wire", seg=3)
        prev = p
    obj(w, "NOCOL_Wire", (0, 0, 0), uv=1.0)
    col = K.MB()
    col.box(xs[0] - 0.1, -1.1, 0, xs[-1] + 0.1, 0.1, 1.5, "M_P1_Wire")
    obj(col, "COL_Fence", (0, 0, 0), uv=1.0)


def build_barricade_c():
    """沙袋矮墙带射击口：两排错缝五层沙袋（约 1.0 m 高、4.2 m 长）+ 右端折回 1.6 m 成 L 形；两个射击口用木板做框和过梁，墙后一条射击踏板、一只弹药箱。"""
    mb = K.MB()
    L, Wd, Hh = 0.55, 0.32, 0.2
    loops = [(-1.2, 0.48), (0.9, 0.48)]                                   # 射击口中心 x 与宽度
    x0, x1 = -2.1, 2.1

    def in_loop(xa, xb, layer):
        if layer != 3:
            return False
        return any(xb > c - w / 2 and xa < c + w / 2 for c, w in loops)
    for layer in range(5):
        z = layer * Hh
        rows = (-0.17, 0.17) if layer < 4 else (0.0,)
        off = (L / 2) if layer % 2 else 0.0
        x = x0 - off
        while x < x1 - 0.05:
            xa, xb = max(x, x0), min(x + L, x1)
            if xb - xa > 0.15 and not in_loop(xa, xb, layer):
                for y in rows:
                    sack(mb, (xa + xb) / 2, y, z, 0, "M_P1_Sandbag" if (layer + int(x * 3)) % 3 else "M_P1_SandbagDark",
                         L=xb - xa - 0.02, Wd=Wd, Hh=Hh)
            x += L
        # L 形折回（沿 +Y）
        yb0, yb1 = 0.35, 1.95
        y = yb0 - (L / 2 if layer % 2 == 0 else 0.0)
        while y < yb1 - 0.05:
            ya, yb = max(y, yb0), min(y + L, yb1)
            if yb - ya > 0.15:
                for xx in ((x1 - 0.17, x1 - 0.5) if layer < 4 else (x1 - 0.33,)):
                    sack(mb, xx, (ya + yb) / 2, z, 90, "M_P1_SandbagDark" if layer % 2 else "M_P1_Sandbag",
                         L=yb - ya - 0.02, Wd=Wd, Hh=Hh)
            y += L
    for c, w in loops:                                                     # 射击口：两侧立板 + 过梁 + 底板
        mb.box(c - w / 2 - 0.04, -0.36, 0.6, c - w / 2, 0.36, 0.8, "M_P1_WoodGrey")
        mb.box(c + w / 2, -0.36, 0.6, c + w / 2 + 0.04, 0.36, 0.8, "M_P1_WoodGrey")
        mb.box(c - w / 2 - 0.12, -0.38, 0.8, c + w / 2 + 0.12, 0.38, 0.84, "M_P1_Wood")
        mb.box(c - w / 2, -0.36, 0.58, c + w / 2, 0.36, 0.6, "M_P1_Wood")
    mb.box(-2.0, 0.45, 0, 1.5, 0.85, 0.18, "M_P1_WoodGrey")                 # 射击踏板
    for x in (-1.9, -0.2, 1.4):
        mb.box(x - 0.05, 0.45, 0, x + 0.05, 0.85, 0.12, "M_P1_WoodDark")
    crate(mb, 0.0, 1.2, 0, 0.6, 0.3, 0.25, rz=5, mat="M_P1_Khaki")
    for x in (-2.15, 2.15):
        mb.cyl(x, -0.36, 0, 1.15, 0.045, "M_P1_Wood", seg=6)
    obj(mb, "Sandbags", (0, 0, 0), uv=1.0)
    for k, (c, w) in enumerate(loops):
        anchor(f"ANCHOR_Loophole_{k + 1}", (c, 0.65, 0.18), 180)


# ================================================================= PROP_Bicycle / PROP_Rickshaw / PROP_Telephone / PROP_Suitcase
def build_bicycle():
    """1941 老式自行车（28 寸、平把、后货架、前灯、车铃、挡泥板、撑脚）：车头朝 -Y；Wheel_F / Wheel_R 枢轴在轴心。"""
    R = 0.34
    yf, yr = -0.56, 0.56
    mb = K.MB()
    bb = (0, 0.04, 0.3)
    seat = (0, 0.22, 0.86)
    head_t, head_b = (0, -0.4, 0.9), (0, -0.44, 0.72)
    fa, ra = (0, yf, R), (0, yr, R)
    for a, b, r in ((bb, seat, 0.018), (seat, head_t, 0.017), (bb, head_b, 0.02), (head_b, head_t, 0.024)):
        bar(mb, a, b, r, "M_P1_BikeFrame", seg=6)
    for sx in (-1, 1):
        bar(mb, (sx * 0.02, 0.04, 0.3), (sx * 0.05, yr, R), 0.011, "M_P1_BikeFrame", seg=5)        # 后下叉
        bar(mb, (sx * 0.02, 0.22, 0.85), (sx * 0.05, yr, R), 0.01, "M_P1_BikeFrame", seg=5)        # 后上叉
        bar(mb, (sx * 0.02, -0.44, 0.72), (sx * 0.05, yf, R), 0.012, "M_P1_BikeFrame", seg=5)      # 前叉
        bar(mb, (sx * 0.12, 0.55, 0.62), (sx * 0.12, yr + 0.02, R), 0.007, "M_P1_BikeFrame", seg=4)  # 货架撑
        bar(mb, (sx * 0.04, yr + 0.1, 0.2), (sx * 0.1, yr + 0.18, 0.0), 0.009, "M_P1_BikeFrame", seg=4)   # 撑脚
    bar(mb, (0, -0.42, 0.9), (0, -0.4, 1.04), 0.014, "M_P1_Chrome", seg=6)                        # 把立
    for sx in (-1, 1):
        bar(mb, (0, -0.4, 1.04), (sx * 0.22, -0.3, 1.05), 0.011, "M_P1_Chrome", seg=6)            # 平把（后掠）
        bar(mb, (sx * 0.22, -0.3, 1.05), (sx * 0.3, -0.24, 1.04), 0.016, "M_P1_Rubber", seg=6)
    mb.box(-0.13, 0.42, 0.62, 0.13, 0.82, 0.64, "M_P1_BikeFrame")                                   # 后货架
    for x in (-0.06, 0.0, 0.06):
        mb.box(x - 0.005, 0.42, 0.64, x + 0.005, 0.82, 0.648, "M_P1_BikeFrame")
    bar(mb, seat, (0, 0.24, 0.95), 0.012, "M_P1_Chrome", seg=6)                                     # 座管
    mb.prism([(-0.1, 0.95), (0.1, 0.95), (0.03, 1.0), (-0.03, 1.0)], "y", 0.16, 0.36, "M_P1_LeatherBrown")   # 车座（后宽前窄）
    with mb.at(0, 0.24, 0.94):
        mb.box(-0.1, 0.02, -0.02, 0.1, 0.12, 0.0, "M_P1_Chrome")
    with mb.at(0, 0.04, 0.3, ry=90):                                                                # 牙盘 + 曲柄 + 脚蹬
        mb.cyl(0, 0, -0.06, -0.05, 0.1, "M_P1_Chrome", seg=12)
    for sx, ang in ((-1, 30), (1, 210)):
        a = math.radians(ang)
        p = (sx * 0.08, 0.04 + 0.16 * math.cos(a), 0.3 + 0.16 * math.sin(a))
        bar(mb, (sx * 0.07, 0.04, 0.3), p, 0.01, "M_P1_Chrome", seg=4)
        xa, xb = sorted((p[0], p[0] + sx * 0.08))
        mb.box(xa, p[1] - 0.04, p[2] - 0.012, xb, p[1] + 0.04, p[2] + 0.012, "M_P1_Rubber")
    bar(mb, (0.05, 0.04, 0.3), (0.05, yr, R), 0.008, "M_P1_Iron", seg=3)                           # 链条（上下两道）
    bar(mb, (0.05, 0.04, 0.4), (0.05, yr, R + 0.04), 0.008, "M_P1_Iron", seg=3)
    for yc, a0, a1 in ((yf, 20, 160), (yr, 10, 170)):                                                # 挡泥板（弧片）
        segs = 7
        for i in range(segs):
            t0 = math.radians(a0 + (a1 - a0) * i / segs)
            t1 = math.radians(a0 + (a1 - a0) * (i + 1) / segs)
            rr = R + 0.04
            mb.prism([(yc - rr * math.cos(t0), R + rr * math.sin(t0)), (yc - rr * math.cos(t1), R + rr * math.sin(t1)),
                      (yc - (rr + 0.012) * math.cos(t1), R + (rr + 0.012) * math.sin(t1)),
                      (yc - (rr + 0.012) * math.cos(t0), R + (rr + 0.012) * math.sin(t0))], "x", -0.035, 0.035, "M_P1_BikeFrame")
    with mb.at(0, -0.47, 0.86, rx=90):                                                               # 前灯
        mb.cyl(0, 0, 0, 0.07, 0.045, "M_P1_Chrome", seg=8)
        mb.cyl(0, 0, 0.07, 0.075, 0.04, "M_P1_Lamp", seg=8)
    mb.cyl(0.14, -0.32, 1.06, 1.1, 0.025, "M_P1_Chrome", seg=8)                                     # 车铃
    obj(mb, "Frame", (0, 0, 0), uv=1.0)
    for nm, yc in (("Wheel_F", yf), ("Wheel_R", yr)):
        w = K.MB()
        wheel_x(w, (0, 0, 0), R - 0.018, 0.018, "M_P1_Chrome", "M_P1_Rubber", spokes=16, hub=0.025, seg=20, spoke_r=0.003)
        obj(w, nm, (0, yc, R), uv=1.0)


def build_rickshaw():
    """黄包车：两只大辐条轮（Wheel_L/R）+ Body（车座、靠背、折起的黑篷、脚踏板、两根长车杠），Body 枢轴在车轴。
    默认是停放态：车杠前端着地、车身后仰约 21°；拉起来时绕车轴（本地 X）把车身转回 21°，车杠水平、把手高约 0.78 m。"""
    R = 0.46
    w = K.MB()
    for nm, sx in (("Wheel_L", 1), ("Wheel_R", -1)):
        w = K.MB()
        wheel_x(w, (0, 0, 0), R - 0.025, 0.025, "M_P1_WoodDark", "M_P1_Rubber", spokes=16, hub=0.05, seg=20, spoke_r=0.008)
        obj(w, nm, (sx * 0.58, 0, R), uv=1.0)
    mb = K.MB()
    with mb.at(0, 0, 0, rx=21):                                           # 拉起态建模，整体转成停放态
        bar(mb, (-0.62, 0, 0), (0.62, 0, 0), 0.025, "M_P1_Iron", seg=6)                     # 车轴
        for sx in (-1, 1):
            bar(mb, (sx * 0.4, 0.25, 0.25), (sx * 0.27, -2.05, 0.32), 0.028, "M_P1_WoodDark", seg=6)    # 车杠
            bar(mb, (sx * 0.4, 0.05, -0.02), (sx * 0.4, 0.2, 0.28), 0.03, "M_P1_Iron", seg=5)            # 吊架
            mb.box(sx * 0.45 - 0.01, -0.3, 0.05, sx * 0.45 + 0.01, 0.45, 0.42, "M_P1_Hood")          # 两侧挡板
            # 挡泥板（弧）
            for i in range(6):
                t0, t1 = math.radians(20 + 140 * i / 6), math.radians(20 + 140 * (i + 1) / 6)
                rr = R + 0.04
                mb.prism([(-rr * math.cos(t0), rr * math.sin(t0)), (-rr * math.cos(t1), rr * math.sin(t1)),
                          (-(rr + 0.015) * math.cos(t1), (rr + 0.015) * math.sin(t1)), (-(rr + 0.015) * math.cos(t0), (rr + 0.015) * math.sin(t0))],
                         "x", sx * 0.58 - 0.06, sx * 0.58 + 0.06, "M_P1_Hood")
        bar(mb, (-0.29, -2.0, 0.32), (0.29, -2.0, 0.32), 0.022, "M_P1_WoodDark", seg=6)              # 横把
        mb.box(-0.45, -0.3, 0.3, 0.45, 0.35, 0.42, "M_P1_Hood")                                       # 车斗
        mb.box(-0.42, -0.25, 0.42, 0.42, 0.3, 0.5, "M_P1_Seat")                                       # 坐垫
        mb.prism([(0.3, 0.42), (0.48, 0.42), (0.6, 1.05), (0.48, 1.05)], "x", -0.43, 0.43, "M_P1_Seat")   # 靠背
        mb.prism([(-0.3, 0.3), (-0.3, 0.2), (-0.75, -0.05), (-0.8, 0.02)], "x", -0.36, 0.36, "M_P1_Hood")  # 脚踏板
        mb.box(-0.36, -0.82, -0.06, 0.36, -0.7, 0.02, "M_P1_Hood")
        for i in range(5):                                                                            # 折起的车篷（向后叠）
            t = 20 + i * 14
            a = math.radians(t)
            r = 0.65 - i * 0.03
            cy, cz = 0.55, 0.55
            mb.prism([(cy + r * math.cos(a) * 0.4, cz + r * math.sin(a)), (cy + (r + 0.04) * math.cos(a) * 0.4, cz + (r + 0.04) * math.sin(a)),
                      (cy + (r + 0.04) * math.cos(a) * 0.4 + 0.06, cz + (r + 0.04) * math.sin(a) - 0.02),
                      (cy + r * math.cos(a) * 0.4 + 0.06, cz + r * math.sin(a) - 0.02)], "x", -0.46, 0.46, "M_P1_Hood")
        for sx in (-1, 1):
            bar(mb, (sx * 0.46, 0.55, 0.55), (sx * 0.46, 0.75, 1.2), 0.012, "M_P1_Iron", seg=4)       # 篷骨
            mb.box(sx * 0.47 - 0.02, -0.33, 0.6, sx * 0.47 + 0.02, 0.35, 0.64, "M_P1_Iron")             # 扶手
        mb.cyl(0.4, -0.35, 0.42, 0.5, 0.03, "M_P1_Brass", seg=6)                                     # 铜灯座
    obj(mb, "Body", (0, 0, R), uv=1.0)
    anchor("ANCHOR_Puller", (0, -2.25, 0), 180)
    anchor("ANCHOR_Seat", (0, 0.05, 0.55), 0)


def build_telephone():
    """日军野战电话套件：弹药箱当桌（Table）上一台皮套野战电话机（Phone + Handset 可拿起 + Crank 手摇柄）、一台交换机箱（Switchboard，插孔面板 + 塞绳），
    地上一架电话线轴（Reel 枢轴在轴心，可转）拉出一根线。"""
    mb = K.MB()
    mb.box(-0.5, -0.25, 0, 0.5, 0.25, 0.42, "M_P1_Khaki")
    for x in (-0.45, 0.4):
        mb.box(x, -0.26, 0, x + 0.05, 0.26, 0.42, "M_P1_WoodDark")
    mb.box(-0.52, -0.27, 0.42, 0.52, 0.27, 0.46, "M_P1_WoodGrey")
    mb.box(-0.1, -0.262, 0.15, 0.1, -0.25, 0.3, "M_P1_Sign")
    obj(mb, "Table", (0, 0, 0), uv=1.0)
    mb = K.MB()                                                            # 电话机：皮套木盒
    mb.box(-0.14, -0.09, 0, 0.14, 0.09, 0.2, "M_P1_Leather")
    mb.box(-0.145, -0.095, 0.0, 0.145, 0.095, 0.03, "M_P1_LeatherBrown")
    mb.box(-0.12, -0.096, 0.05, 0.12, -0.09, 0.17, "M_P1_KhakiLight")
    mb.box(-0.09, -0.1, 0.09, -0.05, -0.096, 0.13, "M_P1_Brass")
    mb.box(0.05, -0.1, 0.09, 0.09, -0.096, 0.13, "M_P1_Bakelite")
    for sx in (-1, 1):
        mb.box(sx * 0.13, -0.01, 0.2, sx * 0.13 + sx * 0.012, 0.01, 0.26, "M_P1_Leather")
    mb.box(-0.13, -0.008, 0.26, 0.13, 0.008, 0.27, "M_P1_Leather")         # 背带
    mb.box(-0.1, -0.04, 0.2, 0.1, 0.04, 0.215, "M_P1_Bakelite")             # 听筒座
    obj(mb, "Phone", (-0.22, -0.02, 0.46), uv=1.0)
    mb = K.MB()                                                            # 听筒（手柄 + 两端）
    mb.box(-0.09, -0.015, 0, 0.09, 0.015, 0.025, "M_P1_Bakelite")
    for sx in (-1, 1):
        mb.cyl(sx * 0.09, 0, -0.005, 0.03, 0.028, "M_P1_Bakelite", seg=8)
    mb.box(-0.02, -0.02, 0.025, 0.02, 0.02, 0.035, "M_P1_Bakelite")
    obj(mb, "Handset", (-0.22, -0.02, 0.68), uv=1.0)
    mb = K.MB()
    mb.box(0, -0.01, -0.01, 0.025, 0.01, 0.01, "M_P1_Steel")
    mb.box(0.02, -0.01, -0.07, 0.03, 0.01, 0.01, "M_P1_Steel")
    mb.box(0.03, -0.012, -0.08, 0.06, 0.012, -0.06, "M_P1_Bakelite")
    obj(mb, "Crank", (-0.08, -0.02, 0.58), uv=1.0)
    mb = K.MB()                                                            # 交换机箱
    mb.box(-0.2, -0.15, 0, 0.2, 0.15, 0.48, "M_P1_Khaki")
    mb.box(-0.205, -0.155, 0.46, 0.205, 0.155, 0.5, "M_P1_WoodDark")
    mb.box(-0.17, -0.152, 0.2, 0.17, -0.15, 0.44, "M_P1_Bakelite")
    for i in range(5):
        for j in range(3):
            x = -0.13 + i * 0.065
            z = 0.25 + j * 0.065
            mb.box(x - 0.012, -0.156, z - 0.012, x + 0.012, -0.152, z + 0.012, "M_P1_Brass")
    mb.box(-0.17, -0.25, 0.14, 0.17, -0.15, 0.17, "M_P1_WoodGrey")         # 翻下的键板
    for k in range(4):
        x = -0.12 + k * 0.08
        mb.box(x - 0.008, -0.23, 0.17, x + 0.008, -0.21, 0.2, "M_P1_Bakelite")
        bar(mb, (x, -0.22, 0.2), (x * 0.6 + 0.02 * k, -0.165, 0.32 - 0.03 * k), 0.004, "M_P1_Bakelite", seg=3)   # 塞绳
    for sx in (-1, 1):
        mb.box(sx * 0.2, -0.03, 0.3, sx * 0.2 + sx * 0.02, 0.03, 0.36, "M_P1_Steel")
    obj(mb, "Switchboard", (0.22, 0.02, 0.46), uv=1.0)
    mb = K.MB()                                                            # 线轴架（A 字形）
    for sx in (-1, 1):
        bar(mb, (sx * 0.14, -0.18, 0), (sx * 0.14, 0, 0.36), 0.015, "M_P1_Iron", seg=4)
        bar(mb, (sx * 0.14, 0.18, 0), (sx * 0.14, 0, 0.36), 0.015, "M_P1_Iron", seg=4)
    bar(mb, (0, 0, 0.36), (0, 0, 0.6), 0.012, "M_P1_Iron", seg=4)
    mb.box(-0.06, -0.012, 0.6, 0.06, 0.012, 0.625, "M_P1_Iron")
    obj(mb, "Reel_Stand", (-0.85, 0.2, 0), uv=1.0)
    mb = K.MB()
    with mb.at(0, 0, 0, ry=90):
        mb.cyl(0, 0, -0.13, -0.11, 0.18, "M_P1_Iron", seg=12)
        mb.cyl(0, 0, 0.11, 0.13, 0.18, "M_P1_Iron", seg=12)
        mb.cyl(0, 0, -0.11, 0.11, 0.13, "M_P1_Wire", seg=12)
        mb.cyl(0, 0, -0.16, 0.16, 0.02, "M_P1_Steel", seg=6)
    mb.box(0.16, -0.01, -0.01, 0.18, 0.01, 0.12, "M_P1_Steel")
    mb.box(0.15, -0.015, 0.1, 0.2, 0.015, 0.14, "M_P1_Bakelite")
    obj(mb, "Reel", (-0.85, 0.2, 0.36), uv=1.0)
    mb = K.MB()
    bar(mb, (-0.85, 0.06, 0.3), (-0.6, -0.1, 0.004), 0.004, "M_P1_Wire", seg=3)
    bar(mb, (-0.6, -0.1, 0.004), (-0.3, 0.0, 0.004), 0.004, "M_P1_Wire", seg=3)
    bar(mb, (-0.3, 0.0, 0.004), (0.1, 0.27, 0.3), 0.004, "M_P1_Wire", seg=3)
    bar(mb, (0.1, 0.27, 0.3), (0.2, 0.17, 0.62), 0.004, "M_P1_Wire", seg=3)
    bar(mb, (-0.22, 0.06, 0.66), (0.05, 0.1, 0.75), 0.003, "M_P1_Bakelite", seg=3)   # 电话机到交换机
    bar(mb, (0.05, 0.1, 0.75), (0.08, 0.12, 0.8), 0.003, "M_P1_Bakelite", seg=3)
    obj(mb, "NOCOL_Wires", (0, 0, 0), uv=1.0)
    anchor("ANCHOR_Operator", (0, -0.6, 0), 0)


def build_suitcase():
    """皮箱：平放的旧牛皮箱（铜包角、两道皮带、铜搭扣、前侧提手）；Lid 枢轴在后沿铰链，Contents 是箱里叠的衣服、一本书、一个小相框。
    合上 = Lid 旋转 0；打开 = Lid 绕铰链（本地 X）向后翻约 105°。"""
    Wd, D, Hb, Hl = 0.66, 0.4, 0.13, 0.07
    mb = K.MB()
    mb.box(-Wd / 2, -D / 2, 0, Wd / 2, D / 2, 0.012, "M_P1_LeatherBrown")
    for (x0, y0, x1, y1) in ((-Wd / 2, -D / 2, Wd / 2, -D / 2 + 0.012), (-Wd / 2, D / 2 - 0.012, Wd / 2, D / 2),
                             (-Wd / 2, -D / 2, -Wd / 2 + 0.012, D / 2), (Wd / 2 - 0.012, -D / 2, Wd / 2, D / 2)):
        mb.box(x0, y0, 0.012, x1, y1, Hb, "M_P1_LeatherBrown")
    mb.box(-Wd / 2 + 0.012, -D / 2 + 0.012, 0.012, Wd / 2 - 0.012, D / 2 - 0.012, 0.016, "M_P1_ClothRed")    # 衬布
    for sx in (-1, 1):
        for sy in (-1, 1):
            corner_cap(mb, sx * Wd / 2, sy * D / 2, sx, sy, -0.002, 0.04)
        mb.box(sx * 0.17 - 0.02, -D / 2 - 0.006, 0.0, sx * 0.17 + 0.02, D / 2 + 0.006, Hb, "M_P1_Leather")    # 皮带（箱身段）
        mb.box(sx * 0.17 - 0.03, -D / 2 - 0.012, Hb - 0.05, sx * 0.17 + 0.03, -D / 2 - 0.004, Hb - 0.01, "M_P1_Brass")
        mb.box(sx * 0.07 - 0.02, -D / 2 - 0.01, Hb - 0.03, sx * 0.07 + 0.02, -D / 2, Hb, "M_P1_Brass")          # 搭扣下半
    bar(mb, (-0.07, -D / 2 - 0.01, Hb - 0.035), (-0.05, -D / 2 - 0.05, Hb - 0.06), 0.008, "M_P1_Leather", seg=5)   # 提手
    bar(mb, (-0.05, -D / 2 - 0.05, Hb - 0.06), (0.05, -D / 2 - 0.05, Hb - 0.06), 0.01, "M_P1_Leather", seg=5)
    bar(mb, (0.05, -D / 2 - 0.05, Hb - 0.06), (0.07, -D / 2 - 0.01, Hb - 0.035), 0.008, "M_P1_Leather", seg=5)
    obj(mb, "Case", (0, 0, 0), uv=1.0)
    mb = K.MB()                                                            # 箱里的东西
    for k, (x, m) in enumerate(((-0.17, "M_P1_ClothBlue"), (0.0, "M_P1_Cloth"), (0.17, "M_P1_QuiltBlue"))):
        mb.box(x - 0.08, -0.15, 0.016, x + 0.08, 0.15, 0.06 + 0.012 * k, m)
    mb.box(0.15, -0.1, 0.1, 0.27, 0.06, 0.118, "M_P1_Leather")
    with mb.at(-0.1, 0.04, 0.075, rz=12):
        mb.box(-0.05, -0.065, 0, 0.05, 0.065, 0.012, "M_P1_WoodDark")
        mb.box(-0.04, -0.055, 0.012, 0.04, 0.055, 0.014, "M_P1_PaperBack")
    obj(mb, "Contents", (0, 0, 0), uv=1.0)
    mb = K.MB()                                                            # 箱盖：枢轴在后沿，几何向 -Y 展开
    mb.box(-Wd / 2, -D, Hl - 0.012, Wd / 2, 0, Hl, "M_P1_LeatherBrown")
    for (x0, y0, x1, y1) in ((-Wd / 2, -D, Wd / 2, -D + 0.012), (-Wd / 2, -0.012, Wd / 2, 0.0),
                             (-Wd / 2, -D, -Wd / 2 + 0.012, 0), (Wd / 2 - 0.012, -D, Wd / 2, 0)):
        mb.box(x0, y0, 0, x1, y1, Hl - 0.012, "M_P1_LeatherBrown")
    mb.box(-Wd / 2 - 0.004, -D - 0.004, 0, Wd / 2 + 0.004, -D + 0.01, 0.012, "M_P1_Leather")      # 箱口包边
    for sx in (-1, 1):
        mb.box(sx * 0.17 - 0.02, -D - 0.006, 0.0, sx * 0.17 + 0.02, 0.006, Hl + 0.004, "M_P1_Leather")
        mb.box(sx * 0.07 - 0.02, -D - 0.01, 0.0, sx * 0.07 + 0.02, -D, 0.03, "M_P1_Brass")
        for sy, y in ((-1, -D), (1, 0.0)):
            corner_cap(mb, sx * Wd / 2, y, sx, sy, Hl - 0.03, Hl + 0.003)
    mb.box(-0.16, -D + 0.1, Hl, 0.16, -D + 0.3, Hl + 0.002, "M_P1_Sign")      # 贴在盖上的旧行李签
    obj(mb, "Lid", (0, D / 2, Hb), uv=1.0)


# ================================================================= 注册
def recipes():
    R = {}
    for n, cfg in P1_CAST.items():
        R[n] = ("Characters", (lambda nm=n, c=cfg: C.build_character(nm, c)))
    R["PROP_StreetFood_Noodle"] = ("Props", build_food_noodle)
    R["PROP_StreetFood_Steamer"] = ("Props", build_food_steamer)
    R["PROP_Load_Pole"] = ("Props", build_load_pole)
    R["PROP_Load_Cart"] = ("Props", build_load_cart)
    R["PROP_Flag_Japan_Pole"] = ("Props", build_flag_pole)
    R["PROP_Flag_Japan_Wall"] = ("Props", build_flag_wall)
    for k in ("A", "B", "C"):
        R[f"PROP_Poster_{k}"] = ("Props", (lambda kk=k: build_poster(kk)))
    R["ENV_BombCrater_A"] = ("Environments", build_crater_a)
    R["ENV_BombCrater_B"] = ("Environments", build_crater_b)
    R["ENV_Barricade_A"] = ("Environments", build_barricade_a)
    R["ENV_Barricade_B"] = ("Environments", build_barricade_b)
    R["ENV_Barricade_C"] = ("Environments", build_barricade_c)
    R["PROP_Bicycle"] = ("Props", build_bicycle)
    R["PROP_Rickshaw"] = ("Props", build_rickshaw)
    R["PROP_Telephone"] = ("Props", build_telephone)
    R["PROP_Suitcase"] = ("Props", build_suitcase)
    return R
