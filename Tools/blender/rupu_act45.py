"""
《入谱》第四幕 1941 藏谱/寻谱 + 第五幕 1945 修谱/巡游 · 环境、道具、人物
（Blender bpy，程序化白模；由 build_yongchang.py 统一生成/导出，recipes() 返回 {资产名: (分类, 生成函数)}）

对应 Docs/入谱_当前建模缺口清单.md 第五、六节 + 第七节 PROP_Genealogy_System 的模型部分。说明见 Docs/act45_assets.md。

约定：
  - 正面朝 Blender -Y（团结 +Z），1 unit = 1 m；道具原点在底面中心，环境原点在地面中心
    （贴墙件 ENV_Hide_Wall / ENV_Hide_Plaque 的原点在贴墙面的底边中点，几何全部在 y<0 一侧）。
  - 会动、会切换状态的部件是固定名字的子物体（Brick_Loose / Plaque / Windlass / Bucket / Rim_Stone /
    Page_01..12 / Slot_1..8 / Cloth / Seg_01..08 …），团结里按名字找；子物体原点 = 枢轴。
  - ANCHOR_* 空物体是互动 / 站位 / 藏谱点，FX_* 空物体是特效挂点（灰尘、雪、烛火、香烟）。
  - 需要换字 / 换贴图的面（旗面 Cloth、龙灯灯面 *_Face、匾面、页槽、印文）用 0..1 平面 UV，其余是 0.5 m 盒式 UV。
  - 材质前缀：第四幕 M_A4_*，第五幕 M_A5_*，人物 M_A5C_*；祠堂废墟沿用内景的语义材质（M_Plaster 等）以便年代材质库替换。
"""
import math
import random

import bmesh
import bpy
from mathutils import Vector

import rupu_kit as K
import rupu_char as RC
from rupu_act1 import loft_y, slab

A45_PALETTE = {
    # ---- 第四幕 1941 冬
    "M_A4_Snow": "#d9d9d2", "M_A4_Ash": "#5f5b55", "M_A4_AshLight": "#8a857c", "M_A4_Char": "#26211d",
    "M_A4_CharWood": "#33291f", "M_A4_Mud": "#4f4637", "M_A4_Rubble": "#77716a", "M_A4_Tile": "#45494a",
    "M_A4_Brick": "#6c6a63", "M_A4_BrickDark": "#55534d", "M_A4_Cavity": "#16130f", "M_A4_Plaster": "#bdb6a4",
    "M_A4_Stone": "#85847b", "M_A4_StoneDark": "#5f5e57", "M_A4_Water": "#2f3d3c", "M_A4_Rope": "#8a7a58",
    "M_A4_Wood": "#6b5039", "M_A4_WoodDark": "#3e2f24", "M_A4_WoodOld": "#5a4a3a", "M_A4_Iron": "#4a4c4c",
    "M_A4_Bronze": "#7a6038", "M_A4_PlaqueFace": "#2f2418", "M_A4_PlaqueGold": "#8f7a44", "M_A4_RedLacquer": "#6e352a",
    "M_A4_Paper": "#ddd2bb", "M_A4_PaperOld": "#c2b190", "M_A4_PaperBurnt": "#2b231c", "M_A4_PaperScorch": "#8a6a44",
    "M_A4_Ink": "#151311", "M_A4_Cloth": "#7a6e52", "M_A4_Sack": "#a8986e", "M_A4_Khaki": "#6b6446",
    "M_A4_Steel": "#4a4d4f", "M_A4_Lens": "#c9c4a8", "M_A4_LedgerCover": "#4a3a2a", "M_A4_SealStrip": "#d9d0bc",
    "M_A4_SealRed": "#8a2e26",
    # ---- 第五幕 1945 修谱 / 巡游
    "M_A5_Wood": "#6e5139", "M_A5_WoodDark": "#3b2c21", "M_A5_Lacquer": "#7d3a2c", "M_A5_Felt": "#4c544c",
    "M_A5_Paper": "#e3d8c2", "M_A5_PaperNew": "#ece3cf", "M_A5_PaperOld": "#c8b894", "M_A5_Ink": "#141210",
    "M_A5_Paste": "#e6e0cf", "M_A5_Porcelain": "#d3d1c6", "M_A5_PorcelainBlue": "#4a5d6e", "M_A5_Bronze": "#8a6a3a",
    "M_A5_Stone": "#4a4a46", "M_A5_InkStone": "#2a2b2b", "M_A5_Bamboo": "#a08c5a", "M_A5_Hair": "#2a241e",
    "M_A5_SealStone": "#b5a17c", "M_A5_SealRed": "#9a3328", "M_A5_SealPad": "#8a2e26",
    "M_A5_BookCover": "#2f3f54", "M_A5_BookLabel": "#e0d6bf", "M_A5_Thread": "#d6cfbe", "M_A5_SlotInk": "#1a1714",
    "M_A5_CaseWood": "#5a3e2a", "M_A5_Brass": "#9a8248", "M_A5_ClothRed": "#8c3a2e", "M_A5_ClothYellow": "#b89a4a",
    "M_A5_ClothGreen": "#4e6450", "M_A5_ClothBlue": "#44586a", "M_A5_ClothWhite": "#d8d0bc", "M_A5_FlagFace": "#c9b98e",
    "M_A5_Pig": "#c79a86", "M_A5_PigDark": "#8a5a4a", "M_A5_Chicken": "#c8a05a", "M_A5_Fish": "#8e928a",
    "M_A5_Bun": "#e3d4b8", "M_A5_BunPink": "#c47a6a", "M_A5_Candle": "#a83a2a", "M_A5_Flame": "#C4552E",
    "M_A5_PaperGold": "#b8984e", "M_A5_PaperMoney": "#d6c79c", "M_A5_Plate": "#cfcbbd",
    "M_A5_LanternRed": "#a8402e", "M_A5_LanternFace": "#d8c8a0", "M_A5_DragonGreen": "#4f6b52", "M_A5_DragonGold": "#a88a48",
    "M_A5_DragonScale": "#5e7a5a", "M_A5_Eye": "#141210", "M_A5_EyeWhite": "#e0d8c8",
    "M_A5_DrumSkin": "#cdbb94", "M_A5_DrumRed": "#8a3428", "M_A5_Nail": "#9a8248", "M_A5_Gong": "#9a7a3e",
    "M_A5_Rope": "#8a7a58", "M_A5_StoneBase": "#8a897f", "M_A5_Board": "#2f2418", "M_A5_BoardGold": "#a08848",
    "M_A5_Roof": "#3f4545",
}
K.PALETTE.update(A45_PALETTE)


# ================================================================= 小工具
def obj(mb, name, loc=(0.0, 0.0, 0.0), uv=0.5):
    ob = mb.to_object(name, uv_scale=uv)
    ob.location = loc
    return ob


def empty(name, loc, kind="SPHERE", size=0.12):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind
    e.empty_display_size = size
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def fx(name, loc):
    return empty(name, loc, "SPHERE", 0.1)


def anchor(name, loc):
    return empty(name, loc, "ARROWS", 0.3)


def uv01(ob, a=0, b=2, flip_axis=None):
    """平面 0..1 UV：u 取坐标轴 a，v 取轴 b（0=x 1=y 2=z），按物体包围盒归一化。
    flip_axis=(轴, 符号)：法线在该轴上与符号同向的面 u 镜像，让背面也读成正字。"""
    me = ob.data
    if not me.uv_layers:
        me.uv_layers.new()
    uvl = me.uv_layers.active.data
    co = [v.co for v in me.vertices]
    lo = [min(c[i] for c in co) for i in range(3)]
    hi = [max(c[i] for c in co) for i in range(3)]
    da = max(hi[a] - lo[a], 1e-6)
    db = max(hi[b] - lo[b], 1e-6)
    for p in me.polygons:
        flip = flip_axis is not None and p.normal[flip_axis[0]] * flip_axis[1] > 0.3
        for li in p.loop_indices:
            c = co[me.loops[li].vertex_index]
            u = (c[a] - lo[a]) / da
            uvl[li].uv = (1.0 - u if flip else u, (c[b] - lo[b]) / db)


def poly_xy(mb, pts, z0, z1, mat):
    """XY 凸多边形薄片（纸页、雪片、灰）。"""
    mb.prism(pts, "z", z0, z1, mat)


def blob(rng, cx, cy, r, n=7, sq=1.0):
    """不规则凸多边形（雪堆、灰堆、泥渍的平面轮廓）。"""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        rr = r * (0.75 + 0.25 * rng.random())
        pts.append((cx + rr * math.cos(a), cy + rr * math.sin(a) * sq))
    return pts


def mound(mb, rng, cx, cy, z0, r, h, mat, n=8):
    """低矮土堆：底面不规则多边形，收到顶部小多边形（凸）。"""
    base = blob(rng, cx, cy, r, n)
    top = [(cx + (x - cx) * 0.35, cy + (y - cy) * 0.35) for x, y in base]
    b = mb.addv([(x, y, z0) for x, y in base] + [(x, y, z0 + h) for x, y in top])
    mb.face([b + i for i in reversed(range(n))], mat)
    mb.face([b + n + i for i in range(n)], mat)
    for i in range(n):
        j = (i + 1) % n
        mb.face([b + i, b + j, b + n + j, b + n + i], mat)


def rubble(mb, rng, cx, cy, z0, spread, count, mats, smin=0.06, smax=0.22):
    """一堆乱石碎瓦：随机朝向的小块。"""
    for _ in range(count):
        x = cx + (rng.random() - 0.5) * 2 * spread
        y = cy + (rng.random() - 0.5) * 2 * spread
        s = smin + (smax - smin) * rng.random()
        with mb.at(x, y, z0, rz=rng.random() * 180, rx=(rng.random() - 0.5) * 30, ry=(rng.random() - 0.5) * 30):
            mb.box(-s, -s * 0.6, 0, s, s * 0.6, s * (0.4 + 0.5 * rng.random()), mats[rng.randrange(len(mats))])


def beam(mb, p0, p1, w, mat):
    """两点间的方木（任意方向）。"""
    p0, p1 = Vector(p0), Vector(p1)
    d = p1 - p0
    L = d.length
    rz = math.degrees(math.atan2(-d.x, d.y))
    rx = math.degrees(math.atan2(d.z, math.hypot(d.x, d.y)))
    with mb.at(p0.x, p0.y, p0.z, rz=rz, rx=rx):
        mb.box(-w / 2, 0, -w / 2, w / 2, L, w / 2, mat)


def page_lines(mb, x0, y0, x1, y1, z, n, mat="M_A4_Ink", t=0.0004):
    """竖排墨字行（沿 Y 的细条）。"""
    for k in range(n):
        x = x0 + (x1 - x0) * (k + 0.5) / n
        mb.box(x - 0.0025, y0, z, x + 0.0025, y1, z + t, mat)


# ================================================================= 第四幕 · 藏谱点
def build_hide_wall():
    """夹墙藏谱点：贴在后堂西墙内侧砌出的一道「夹墙」（宽 2.4、高 2.6、厚 0.4），中下部一组松动的砖 Brick_Loose 可抽出，
    后面是墙洞（夹层空腔）。原点在贴墙面（y=0）的底边中点，正面朝 -Y。"""
    W, H = 1.2, 2.6
    yf, yb = -0.40, -0.28            # 前皮（砖 + 灰）
    hx0, hx1, hz0, hz1 = -0.33, 0.33, 0.62, 1.02   # 洞口
    mb = K.MB()
    mb.box(-W - 0.04, yf - 0.04, 0, W + 0.04, 0, 0.14, "M_A4_StoneDark")          # 墙脚石
    # 前皮：洞口四周拼出
    mb.box(-W, yf, 0.14, W, yb, hz0, "M_A4_Brick")
    mb.box(-W, yf, hz1, W, yb, H, "M_A4_Plaster")
    mb.box(-W, yf, hz0, hx0, yb, hz1, "M_A4_Brick")
    mb.box(hx1, yf, hz0, W, yb, hz1, "M_A4_Brick")
    mb.box(-W, yf, H, W, 0, H + 0.12, "M_A4_StoneDark")                            # 压顶
    for sx in (-1, 1):                                                              # 两端收口墙
        mb.box(sx * W - (0.12 if sx > 0 else 0), yf, 0.14, sx * W + (0 if sx > 0 else 0.12), 0, H, "M_A4_Plaster")
    # 灰皮剥落处露出的砖缝（下半部）：横缝 + 错缝竖缝
    for r in range(7):
        z = 0.2 + r * 0.075
        if z > hz0 - 0.02:
            break
        mb.box(-W + 0.02, yf - 0.006, z, W - 0.02, yf, z + 0.012, "M_A4_BrickDark")
        for k in range(9):
            x = -W + 0.15 + k * 0.26 + (0.13 if r % 2 else 0)
            mb.box(x, yf - 0.006, z - 0.063, x + 0.012, yf, z, "M_A4_BrickDark")
    for r in range(5):                                                              # 洞口两侧砖缝
        z = hz0 + 0.04 + r * 0.08
        for x0, x1 in ((-W + 0.02, hx0 - 0.01), (hx1 + 0.01, W - 0.02)):
            mb.box(x0, yf - 0.006, z, x1, yf, z + 0.012, "M_A4_BrickDark")
    # 灰皮剥落边缘 + 裂缝
    mb.prism([(-W + 0.02, hz0 + 0.42), (-0.2, hz0 + 0.6), (0.5, hz0 + 0.48), (W - 0.02, hz0 + 0.62), (W - 0.02, hz0 + 0.45), (-W + 0.02, hz0 + 0.36)],
             "y", yf - 0.012, yf, "M_A4_Plaster")
    for (a, b) in (((0.42, 1.3), (0.55, 1.85)), ((0.55, 1.85), (0.48, 2.3)), ((-0.6, 1.6), (-0.82, 2.1))):
        beam(mb, (a[0], yf - 0.004, a[1]), (b[0], yf - 0.004, b[1]), 0.012, "M_A4_Cavity")
    # 墙洞：夹层空腔（洞口后面的暗盒）+ 后壁贴原墙
    mb.box(hx0 - 0.2, yb, hz0 - 0.06, hx1 + 0.2, -0.02, hz0, "M_A4_Cavity")
    mb.box(hx0 - 0.2, -0.04, hz0, hx1 + 0.2, -0.02, hz1 + 0.15, "M_A4_Cavity")
    for sx in (-1, 1):
        mb.box(sx * (hx1 + 0.2) - 0.02, yb, hz0, sx * (hx1 + 0.2) + 0.02, -0.02, hz1 + 0.15, "M_A4_Cavity")
    mb.box(hx0 - 0.2, yb, hz1 + 0.13, hx1 + 0.2, -0.02, hz1 + 0.15, "M_A4_Cavity")
    obj(mb, "Wall", (0, 0, 0), uv=0.5)
    # 松砖：2 × 5 块砖拼成一块，枢轴在正面中点，向 -Y 抽出
    mb = K.MB()
    for r in range(5):
        for c in range(2):
            x0 = -0.32 + c * 0.32 + 0.004
            z0 = -0.2 + r * 0.08 + 0.004
            mb.box(x0, 0.0, z0, x0 + 0.312, 0.12, z0 + 0.072, "M_A4_Brick" if (r + c) % 3 else "M_A4_BrickDark")
    mb.box(-0.3, 0.12, -0.18, 0.3, 0.13, 0.18, "M_A4_BrickDark")
    obj(mb, "Brick_Loose", (0, yf - 0.012, (hz0 + hz1) / 2), uv=0.5)
    # 抽出后掉在地上的碎灰
    mb = K.MB()
    rng = random.Random(41)
    rubble(mb, rng, 0.0, yf - 0.25, 0.0, 0.3, 9, ["M_A4_Plaster", "M_A4_Brick"], 0.02, 0.06)
    obj(mb, "NOCOL_Crumbs", (0, 0, 0))
    anchor("ANCHOR_Hide", (0, (yb - 0.02) / 2, hz0 + 0.01))
    anchor("ANCHOR_Use", (0, -1.0, 0))
    fx("FX_Dust", (0, yf - 0.05, (hz0 + hz1) / 2))


def build_hide_well():
    """井中藏谱点：八角石井栏 + 井筒（地下 2.2 m，水面 -1.7）+ 辘轳（Windlass 绕 X 转）+ 吊桶（Bucket）+ 绳（Rope），
    井栏正面一块栏石 Rim_Stone 可抽出，里面是暗格。替换祠堂后天井的 INT_Well（同位置 ANCHOR_hide_well）。"""
    R0, R1, Hc = 0.82, 0.58, 0.72        # 栏外半径 / 内半径 / 栏高
    n = 8
    mb = K.MB()
    mb.box(-1.25, -1.25, -0.02, 1.25, 1.25, 0.05, "M_A4_Stone")                      # 井台
    for i in range(n):
        a0 = 2 * math.pi * (i - 0.5) / n - math.pi / 2
        a1 = 2 * math.pi * (i + 0.5) / n - math.pi / 2
        p = [(R0 * math.cos(a0), R0 * math.sin(a0)), (R0 * math.cos(a1), R0 * math.sin(a1)),
             (R1 * math.cos(a1), R1 * math.sin(a1)), (R1 * math.cos(a0), R1 * math.sin(a0))]
        if i == 0:                       # 正面（-Y）这块：只留内半，外半是 Rim_Stone，中间挖暗格
            rm = 0.7
            q = [(rm * math.cos(a0), rm * math.sin(a0)), (rm * math.cos(a1), rm * math.sin(a1)), p[2], p[3]]
            mb.prism(list(reversed(q)), "z", 0.05, 0.22, "M_A4_Stone")
            mb.prism(list(reversed(q)), "z", 0.5, Hc, "M_A4_Stone")
            mb.box(-0.2, -0.69, 0.22, 0.2, -0.6, 0.5, "M_A4_Cavity")                # 暗格
            for sx in (-1, 1):
                mb.box(sx * 0.2 - 0.04 * (1 if sx < 0 else 0), -0.7, 0.22, sx * 0.2 + 0.04 * (1 if sx > 0 else 0), -0.6, 0.5, "M_A4_Stone")
            continue
        mb.prism(list(reversed(p)), "z", 0.05, Hc, "M_A4_Stone" if i % 2 else "M_A4_StoneDark")
    # 井筒（地下）+ 水面
    for i in range(n):                                    # 井筒：一圈石壁（中间是空的）
        a0 = 2 * math.pi * (i - 0.5) / n - math.pi / 2
        a1 = 2 * math.pi * (i + 0.5) / n - math.pi / 2
        p = [(R1 * math.cos(a0), R1 * math.sin(a0)), (R1 * math.cos(a1), R1 * math.sin(a1)),
             ((R1 + 0.15) * math.cos(a1), (R1 + 0.15) * math.sin(a1)), ((R1 + 0.15) * math.cos(a0), (R1 + 0.15) * math.sin(a0))]
        mb.prism(p, "z", -2.2, 0.05, "M_A4_StoneDark")
    mb.cyl(0, 0, -1.72, -1.7, R1, "M_A4_Water", seg=8)
    # 栏顶的绳磨沟
    mb.box(-0.12, -0.6, Hc, 0.12, -0.56, Hc + 0.01, "M_A4_Rope")
    # 辘轳架：两根立柱 + 横撑
    for sx in (-1, 1):
        mb.box(sx * 0.9 - 0.06, -0.08, 0.05, sx * 0.9 + 0.06, 0.08, 1.75, "M_A4_WoodOld")
        mb.box(sx * 0.9 - 0.08, -0.25, 0.05, sx * 0.9 + 0.08, 0.25, 0.14, "M_A4_StoneDark")
        beam(mb, (sx * 0.9, -0.05, 0.5), (sx * 0.9, -0.42, 0.05), 0.06, "M_A4_WoodOld")
        beam(mb, (sx * 0.9, 0.05, 0.5), (sx * 0.9, 0.42, 0.05), 0.06, "M_A4_WoodOld")
    obj(mb, "Well", (0, 0, 0), uv=0.5)
    # 辘轳：轴（沿 X）+ 绕绳的鼓 + 摇把（+X 端），枢轴在轴心
    mb = K.MB()
    with mb.at(0, 0, 0, ry=90):
        mb.cyl(0, 0, -0.98, 0.98, 0.03, "M_A4_Iron", seg=6)
        mb.cyl(0, 0, -0.42, 0.42, 0.11, "M_A4_WoodOld", seg=10)
        for z in (-0.3, -0.1, 0.1, 0.3):
            mb.cyl(0, 0, z - 0.02, z + 0.02, 0.118, "M_A4_Rope", seg=10)
    mb.box(0.98, -0.025, -0.025, 1.03, 0.025, 0.32, "M_A4_WoodOld")
    mb.box(1.03, -0.02, 0.27, 1.2, 0.02, 0.31, "M_A4_WoodOld")
    obj(mb, "Windlass", (0, 0, 1.6), uv=0.5)
    # 绳：从鼓下沿垂到桶提梁（团结里可按 Bucket 位置拉伸 Z）
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.5, 0.012, "M_A4_Rope", seg=5)
    obj(mb, "Rope", (0, -0.1, 0.98), uv=0.5)
    # 吊桶：枢轴在提梁顶
    mb = K.MB()
    mb.cyl(0, 0, -0.36, -0.08, 0.13, "M_A4_WoodOld", seg=10, r_top=0.15)
    for z in (-0.32, -0.14):
        mb.cyl(0, 0, z, z + 0.025, 0.142 if z > -0.2 else 0.135, "M_A4_Iron", seg=10)
    mb.box(-0.15, -0.01, -0.1, -0.14, 0.01, 0.0, "M_A4_Iron")
    mb.box(0.14, -0.01, -0.1, 0.15, 0.01, 0.0, "M_A4_Iron")
    mb.box(-0.15, -0.01, -0.01, 0.15, 0.01, 0.0, "M_A4_Iron")
    obj(mb, "Bucket", (0, -0.1, 0.98), uv=0.5)
    # 井沿暗格的盖石（外半块栏石），向 -Y 抽出
    mb = K.MB()
    a0 = 2 * math.pi * (-0.5) / n - math.pi / 2
    a1 = 2 * math.pi * 0.5 / n - math.pi / 2
    q = [(R0 * math.cos(a0), R0 * math.sin(a0)), (R0 * math.cos(a1), R0 * math.sin(a1)),
         (0.7 * math.cos(a1), 0.7 * math.sin(a1)), (0.7 * math.cos(a0), 0.7 * math.sin(a0))]
    cy = -0.76
    mb.prism([(x, y - cy) for x, y in reversed(q)], "z", 0.0, 0.28, "M_A4_StoneDark")
    obj(mb, "Rim_Stone", (0, cy, 0.22), uv=0.5)
    anchor("ANCHOR_Hide", (0, -0.645, 0.23))
    anchor("ANCHOR_Hide_Bucket", (0, -0.1, 0.7))
    anchor("ANCHOR_Use", (0, -1.4, 0))
    fx("FX_Water", (0, 0, -1.69))
    fx("FX_Dust", (0, -0.8, 0.35))


def build_hide_plaque():
    """匾后藏谱点：挂在正厅后墙（神龛上方）的大匾（5.0 × 1.1），Plaque 枢轴在上沿铰链、下沿向外掀起，背后是浅凹槽（暗格）。
    另带一架靠墙竹梯 Ladder（爬上去才够得着）。原点在正厅地面、贴墙面（y=0）的中点；匾底高 3.05 m。
    完全罩住内景原有大匾（内景匾在墙面外 6 cm 内），放在 BLD_INT_AncestralHall 局部坐标 (0, 6.2, 0.9)。"""
    zb, zt, hw = 3.0, 4.15, 2.55
    mb = K.MB()
    # 凹槽框：贴墙的木框，深 0.13，里面暗
    mb.box(-hw, -0.2, zb, hw, -0.07, zb + 0.08, "M_A4_WoodDark")
    mb.box(-hw, -0.2, zt - 0.08, hw, -0.07, zt, "M_A4_WoodDark")
    for sx in (-1, 1):
        mb.box(sx * hw - (0.08 if sx > 0 else 0), -0.2, zb, sx * hw + (0 if sx > 0 else 0.08), -0.07, zt, "M_A4_WoodDark")
    mb.box(-hw + 0.08, -0.09, zb + 0.08, hw - 0.08, -0.07, zt - 0.08, "M_A4_Cavity")
    mb.box(-1.2, -0.2, zb + 0.08, 1.2, -0.09, zb + 0.1, "M_A4_Cavity")               # 凹槽底（放谱）
    for sx in (-1, 1):                                                                # 上沿两个铰链座
        mb.box(sx * 1.6 - 0.08, -0.24, zt - 0.04, sx * 1.6 + 0.08, -0.07, zt + 0.06, "M_A4_Iron")
    obj(mb, "Frame", (0, 0, 0), uv=0.5)
    # 匾：铜边 + 匾心 + 四字凸起（换贴图时用 Plaque 的 0..1 UV）
    mb = K.MB()
    mb.box(-hw - 0.02, -0.08, -(zt - zb) - 0.02, hw + 0.02, 0.0, 0.0, "M_A4_Bronze")
    mb.box(-hw + 0.12, -0.095, -(zt - zb) + 0.12, hw - 0.12, -0.08, -0.12, "M_A4_PlaqueFace")
    for k in range(4):
        x = -1.65 + k * 1.1
        mb.box(x - 0.32, -0.105, -0.88, x + 0.32, -0.095, -0.27, "M_A4_PlaqueGold")
    for sx in (-1, 1):
        mb.box(sx * 1.6 - 0.05, -0.04, -0.1, sx * 1.6 + 0.05, 0.04, 0.03, "M_A4_Iron")
    ob = obj(mb, "Plaque", (0, -0.21, zt), uv=0.5)
    uv01(ob, 0, 2)
    # 竹梯：靠墙斜放，脚在 y=-1.3
    mb = K.MB()
    top = (0, -0.25, zb - 0.1)
    for sx in (-0.24, 0.24):
        beam(mb, (sx, -1.35, 0.0), (sx, top[1], top[2]), 0.05, "M_A5_Bamboo")
    for k in range(9):
        t = (k + 1) / 10
        y = -1.35 + (top[1] + 1.35) * t
        z = top[2] * t
        mb.box(-0.26, y - 0.02, z - 0.02, 0.26, y + 0.02, z + 0.02, "M_A5_Bamboo")
    obj(mb, "Ladder", (0.9, 0, 0), uv=0.5)
    anchor("ANCHOR_Hide", (0, -0.15, zb + 0.1))
    anchor("ANCHOR_Use", (0.9, -1.6, 0))
    anchor("ANCHOR_Climb_Top", (0.9, -0.6, zb - 1.3))
    fx("FX_Dust", (0, -0.25, zb))


# ================================================================= 第四幕 · 1941 冬破祠
def _bm_edit(ob, fn):
    me = ob.data
    bm = bmesh.new()
    bm.from_mesh(me)
    fn(bm)
    bm.to_mesh(me)
    bm.free()
    me.update()


def _delete_faces(ob, pred):
    """删除中心点满足 pred(Vector) 的面。"""
    def f(bm):
        bmesh.ops.delete(bm, geom=[fc for fc in bm.faces if pred(fc.calc_center_median())], context="FACES")
    _bm_edit(ob, f)


def _inside_box(c, x0, y0, z0, x1, y1, z1):
    return x0 <= c.x <= x1 and y0 <= c.y <= y1 and z0 <= c.z <= z1


def _cut_hole(ob, hole, zmin, step=0.5, fill=False, region=(-9, -4, 9, 9)):
    """在网格上按 step 网格切开（只切 z>zmin 且在 region 内的面），删掉中心落在 hole(x,y) 内的面。
    fill=True 时把切出的小断口（梁的断头）补上。"""
    def f(bm):
        x0, y0, x1, y1 = region
        sel = [fc for fc in bm.faces if all(v.co.z > zmin for v in fc.verts)
               and all(x0 <= v.co.x <= x1 and y0 <= v.co.y <= y1 for v in fc.verts)]
        geom = list(set([v for fc in sel for v in fc.verts])) + list(set([e for fc in sel for e in fc.edges])) + sel
        x = x0
        while x <= x1:
            r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(x, 0, 0), plane_no=(1, 0, 0))
            geom = list(set(geom) | set(r["geom"]))
            geom = [g for g in geom if g.is_valid]
            x += step
        y = y0
        while y <= y1:
            r = bmesh.ops.bisect_plane(bm, geom=geom, plane_co=(0, y, 0), plane_no=(0, 1, 0))
            geom = list(set(geom) | set(r["geom"]))
            geom = [g for g in geom if g.is_valid]
            y += step
        dead = [fc for fc in bm.faces if fc.calc_center_median().z > zmin and hole(fc.calc_center_median())]
        bmesh.ops.delete(bm, geom=dead, context="FACES")
        if fill:
            edges = [e for e in bm.edges if e.is_boundary and all(v.co.z > zmin for v in e.verts)]
            if edges:
                bmesh.ops.holes_fill(bm, edges=edges, sides=8)
    _bm_edit(ob, f)


def build_shrine_ruin():
    """1941 冬破祠：调用 build_interiors 生成祠堂内景（同尺寸、同锚点），再做破坏：正厅屋顶塌洞（梁断）、
    前廊一根金柱倒地、供桌翻倒、牌位倒散碎裂、大匾被砸落、门厅一扇门倒地，积雪（塌洞下、内院、天井）、灰烬、瓦砾。"""
    import build_interiors as BI
    BI.r_int_ancestral()
    ZH = 0.9
    sc = bpy.context.scene.objects
    rng = random.Random(1941)

    # 洞的轮廓：以 (-0.6, 2.4) 为中心的不规则椭圆
    def hole(c, cx=-0.6, cy=2.4, rx=3.7, ry=2.6):
        a = math.atan2(c.y - cy, c.x - cx)
        rr = 1.0 + 0.18 * math.sin(3 * a) + 0.1 * math.cos(5 * a + 1)
        return ((c.x - cx) / rx) ** 2 + ((c.y - cy) / ry) ** 2 < rr * rr
    _cut_hole(sc["ROOF_Main"], hole, 5.0, step=0.6, region=(-9.0, -4.0, 9.0, 8.5))
    _cut_hole(sc["INT_Shell"], lambda c: hole(c, rx=3.1, ry=2.2), 4.85, step=0.5, fill=True, region=(-7.0, -1.0, 7.0, 6.4))
    # 倒柱：前排右侧金柱 (3.4, 0.2)
    colx, coly = 3.4, 0.2
    _delete_faces(sc["INT_Shell"], lambda c: _inside_box(c, colx - 0.22, coly - 0.22, ZH + 0.1, colx + 0.22, coly + 0.22, 5.01))
    _delete_faces(sc["COL_Hall"], lambda c: _inside_box(c, colx - 0.21, coly - 0.21, ZH - 0.01, colx + 0.21, coly + 0.21, 5.01))
    # 大匾：从墙上砸落
    _delete_faces(sc["INT_Shell"], lambda c: _inside_box(c, -2.41, 6.13, 3.99, 2.41, 6.21, 4.91))
    # 供桌、香案：换成翻倒版
    _delete_faces(sc["COL_Hall"], lambda c: _inside_box(c, -1.31, 1.59, ZH - 0.01, 1.31, 3.81, ZH + 0.96))
    for n in ("INT_Altar", "INT_Tablets"):
        bpy.data.objects.remove(sc[n], do_unlink=True)

    # ---------------- 断梁、塌下的椽子、瓦砾堆（洞下）
    mb = K.MB()
    for p0, p1 in (((-3.4, 0.2, 5.15), (-1.0, 1.4, ZH + 0.15)), ((1.9, 3.8, 5.15), (0.6, 2.2, ZH + 0.3)),
                   ((-2.6, 4.6, 5.7), (-1.2, 3.4, ZH + 0.1)), ((0.0, -0.9, 5.5), (-0.3, 1.0, ZH + 1.2))):
        beam(mb, p0, p1, 0.24, "M_A4_CharWood")
    for k in range(14):                                                                  # 洞口边缘垂下的断椽
        a = 2 * math.pi * k / 14
        x = -0.6 + 3.3 * math.cos(a)
        y = 2.4 + 2.3 * math.sin(a)
        L = 0.5 + 0.9 * rng.random()
        beam(mb, (x, y, 5.75), (x - 0.25 * math.cos(a) * L, y - 0.25 * math.sin(a) * L, 5.75 - L), 0.08, "M_A4_CharWood")
    mound(mb, rng, -0.6, 2.2, ZH, 1.9, 0.5, "M_A4_Rubble", n=9)
    rubble(mb, rng, -0.6, 2.3, ZH + 0.3, 2.2, 70, ["M_A4_Tile", "M_A4_Rubble", "M_A4_CharWood", "M_A4_Tile"], 0.06, 0.24)
    rubble(mb, rng, 1.8, -1.6, ZH, 1.2, 14, ["M_A4_Tile", "M_A4_Rubble"], 0.05, 0.14)     # 前廊下
    for k in range(10):                                                                  # 碎窗格、断格扇
        x = -6 + rng.random() * 12
        y = -0.6 + rng.random() * 6
        with mb.at(x, y, ZH + 0.02, rz=rng.random() * 180):
            mb.box(-0.5, -0.03, 0, 0.5, 0.03, 0.05, "M_Wood_Dark")
            mb.box(-0.03, -0.3, 0, 0.03, 0.3, 0.05, "M_Wood_Dark")
    # 门厅：一扇门板倒在地上
    with mb.at(-1.2, -15.6, 0.0, rz=18):
        mb.box(-0.7, -1.6, 0, 0.7, 1.6, 0.09, "M_Wood_Dark")
        for y in (-1.1, 0.0, 1.1):
            mb.box(-0.7, y - 0.05, 0.09, 0.7, y + 0.05, 0.12, "M_Wood")
    obj(mb, "RUIN_Debris", (0, 0, 0), uv=0.5)

    # ---------------- 倒柱（单独物体，枢轴在柱脚）
    mb = K.MB()
    with mb.at(0, 0, 0.2, rz=-62, rx=-86):
        mb.cyl(0, 0, 0, 3.9, 0.2, "M_Red_Lacquer", seg=8)
        mb.cyl(0, 0, 3.9, 4.05, 0.2, "M_A4_Char", seg=8, r_top=0.12)                      # 断头焦黑
    obj(mb, "RUIN_Column", (colx, coly, ZH), uv=0.5)

    # ---------------- 翻倒的供桌、香案、香炉、烛台、谱匣（空）
    mb = K.MB()
    with mb.at(0.2, 3.1, ZH, rz=8, rx=-90):                                               # 供桌向前翻倒，桌面朝前
        mb.box(-1.3, 0.0, -0.07, 1.3, 0.8, 0.0, "M_Red_Lacquer")
        for x in (-1.2, 1.12):
            for z in (0.0, 0.72):
                mb.box(x, z, 0.0, x + 0.08, z + 0.08, 0.88, "M_Wood_Dark")
    with mb.at(-0.3, 1.5, ZH, rz=-30, ry=90):                                             # 香案侧翻
        mb.box(0.0, -0.3, -0.9, 0.06, 0.3, 0.9, "M_Wood")
        for z in (-0.8, 0.72):
            mb.box(0.06, -0.25, z, 0.85, -0.17, z + 0.08, "M_Wood_Dark")
            mb.box(0.06, 0.17, z, 0.85, 0.25, z + 0.08, "M_Wood_Dark")
    with mb.at(1.3, 1.0, ZH + 0.2, rz=40, rx=80):                                         # 香炉滚倒
        mb.cyl(0, 0, -0.15, 0.15, 0.2, "M_Bronze", seg=10, r_top=0.26)
    for x, y, rz in ((-1.6, 2.0, 30), (0.9, 0.3, -70)):                                     # 烛台倒地
        with mb.at(x, y, ZH + 0.05, rz=rz, rx=90):
            mb.cyl(0, 0, 0, 0.4, 0.05, "M_Bronze", seg=6, r_top=0.03)
    with mb.at(2.1, 2.6, ZH, rz=25):                                                      # 空谱匣：盖子甩开
        mb.box(-0.15, -0.22, 0, 0.15, 0.22, 0.15, "M_Wood_Dark")
        mb.box(-0.13, -0.2, 0.15, 0.13, 0.2, 0.151, "M_A4_Cavity")
        with mb.at(0.4, 0.1, 0, rz=50):
            mb.box(-0.15, -0.22, 0, 0.15, 0.22, 0.04, "M_Wood_Dark")
    for x in (-1.5, 0.0, 1.5):                                                            # 蒲团踢散
        with mb.at(x + rng.random() - 0.5, 0.2 + rng.random() * 0.6, ZH):
            mb.cyl(0, 0, 0, 0.1, 0.32, "M_Cloth_Red", seg=10)
    obj(mb, "RUIN_Altar", (0, 0, 0), uv=0.5)

    # ---------------- 牌位：一半还立着（歪），一半倒在台阶和地上，几块断成两截
    tiers = [(5.55, ZH + 0.40), (5.95, ZH + 0.80), (6.0, ZH + 1.20)]
    mb = K.MB()

    def tablet(x, y, z, w=0.2, h=0.55, d=0.1, body="M_Wood_Dark", cap="M_Red_Lacquer", rx=0.0, rz=0.0, broken=False):
        with mb.at(x, y, z, rz=rz, rx=rx):
            mb.box(-w / 2 - 0.03, -d / 2 - 0.02, 0, w / 2 + 0.03, d / 2 + 0.02, 0.07, "M_Wood")
            top = h * (0.55 if broken else 1.0)
            mb.box(-w / 2, -d / 2, 0.07, w / 2, d / 2, top, body)
            if broken:
                mb.prism([(-w / 2, top), (w / 2, top), (w / 2, top + 0.06), (-w / 2 + 0.05, top + 0.12)], "y", -d / 2, d / 2, "M_A4_Char")
            else:
                mb.box(-w / 2 - 0.02, -d / 2 - 0.01, h, w / 2 + 0.02, d / 2 + 0.01, h + 0.05, cap)
            mb.box(-w * 0.28, -d / 2 - 0.012, h * 0.35, w * 0.28, -d / 2, min(top, h * 0.85), "M_Bronze")
    rows = [(-4.6, 4.7, 0.45, 0), (-4.2, 4.3, 0.45, 1)]
    for x0, x1, dx, ti in rows:
        x = x0
        while x < x1:
            if ti == 0 and abs(x - 1.8) < 0.2:
                x += dx
                continue
            y, z = tiers[ti]
            r = rng.random()
            if r < 0.45:
                tablet(x, y, z, rz=(rng.random() - 0.5) * 16, rx=(rng.random() - 0.5) * 8, broken=r < 0.12)
            elif r < 0.75:                                                               # 向前倒在台沿上
                tablet(x, y - 0.25, z + 0.02, rx=-80 - rng.random() * 10, rz=(rng.random() - 0.5) * 30)
            else:                                                                        # 掉到地上，碎
                tablet(x + (rng.random() - 0.5) * 0.6, 4.2 - rng.random() * 1.4, ZH + 0.02,
                       rx=-90, rz=rng.random() * 360, broken=rng.random() < 0.5)
            x += dx
    for x, sx in ((-3.2, 1), (-2.3, -1), (2.3, 1), (3.2, -1)):
        tablet(x, 6.0, tiers[2][1], w=0.26, h=0.7, rz=sx * 6)
    tablet(-0.9, 6.0, tiers[2][1], w=0.34, h=0.95, d=0.12, body="M_Red_Lacquer", cap="M_Bronze", rz=-4)      # 王沛公（立着）
    tablet(0.9, 5.3, tiers[1][1] + 0.05, w=0.34, h=0.95, d=0.12, body="M_Red_Lacquer", cap="M_Bronze", rx=-84, rz=12)   # 王叔杲公（倒）
    obj(mb, "RUIN_Tablets", (0, 0, 0), uv=0.5)

    # ---------------- 被砸落的大匾：断成两截，一截斜靠神龛，一截砸在地上
    mb = K.MB()
    with mb.at(-1.3, 4.9, ZH + 0.5, rz=6, rx=-62):
        mb.box(-1.15, -0.03, -0.45, 1.15, 0.03, 0.45, "M_Bronze")
        mb.box(-1.05, -0.045, -0.35, 1.05, -0.03, 0.35, "M_Plaque")
        mb.prism([(1.15, -0.45), (1.3, -0.2), (1.2, 0.1), (1.15, 0.45)], "y", -0.03, 0.03, "M_A4_Char")
    with mb.at(1.6, 4.4, ZH + 0.02, rz=-24):
        mb.box(-1.1, -0.45, 0, 1.1, 0.45, 0.06, "M_Bronze")
        mb.box(-1.0, -0.35, 0.06, 1.0, 0.35, 0.075, "M_Plaque")
        mb.prism([(-1.1, -0.45), (-1.25, -0.1), (-1.1, 0.45)], "z", 0, 0.06, "M_A4_Char")
    rubble(mb, rng, 1.6, 4.2, ZH, 0.6, 8, ["M_Bronze", "M_Plaque"], 0.03, 0.09)
    obj(mb, "RUIN_Plaque", (0, 0, 0), uv=0.5)

    # ---------------- 积雪（塌洞下、内院、后天井、廊下飘进来的）+ 灰烬（冷的）
    mb = K.MB()
    for cx, cy, r in ((-0.6, 2.3, 2.6), (-2.3, 1.2, 1.2), (1.5, 3.4, 1.0)):
        poly_xy(mb, blob(rng, cx, cy, r, 10), ZH + 0.02, ZH + 0.05, "M_A4_Snow")
    mound(mb, rng, -0.7, 2.3, ZH + 0.48, 1.0, 0.12, "M_A4_Snow", n=9)
    poly_xy(mb, [(-7.3, -10.9), (7.3, -10.9), (7.3, -6.1), (2.2, -6.0), (-2.2, -6.0), (-7.3, -6.1)], 0.0, 0.05, "M_A4_Snow")   # 内院
    for sx in (-1, 1):
        poly_xy(mb, sorted_ccw([(sx * 6.5, -6.0), (sx * 7.35, -6.0), (sx * 7.35, 9.8), (sx * 7.4, 9.8)]), 0.0, 0.04, "M_A4_Snow")
        poly_xy(mb, sorted_ccw([(sx * 6.9, -2.6), (sx * 7.35, -2.6), (sx * 7.35, 9.8), (sx * 6.9, 9.8)]), 0.0, 0.05, "M_A4_Snow")
    poly_xy(mb, [(-7.3, 7.05), (7.3, 7.05), (7.3, 8.75), (-7.3, 8.75)], 0.0, 0.05, "M_A4_Snow")      # 后天井
    for k in range(9):                                                                           # 廊下和门厅里飘进的小雪片
        x = -8 + rng.random() * 16
        y = -10 + rng.random() * 8
        poly_xy(mb, blob(rng, x, y, 0.4 + rng.random() * 0.5, 7), 0.36 if abs(x) > 7.4 else 0.0, 0.4 if abs(x) > 7.4 else 0.06, "M_A4_Snow")
    for cx, cy, r in ((0.3, 3.4, 0.6), (-1.6, 3.8, 0.45), (2.6, 1.6, 0.4)):                        # 冷灰
        mound(mb, rng, cx, cy, ZH, r, 0.08, "M_A4_Ash", n=8)
    for k in range(6):                                                                           # 墙脚积灰
        x = -6 + k * 2.4
        poly_xy(mb, blob(rng, x, 5.9 - (0.3 if abs(x) < 4.6 else 0), 0.5, 7, 0.5), ZH + 0.02, ZH + 0.035, "M_A4_AshLight")
    obj(mb, "NOCOL_RUIN_SnowAsh", (0, 0, 0), uv=1.0)

    # ---------------- 碰撞补充：倒柱、翻倒供桌、瓦砾堆
    mb = K.MB()
    with mb.at(colx, coly, ZH + 0.2, rz=-62, rx=-86):
        mb.box(-0.2, -0.2, 0, 0.2, 0.2, 4.0, "M_Plaster")
    mb.box(-1.1, 2.3, ZH, 1.5, 3.2, ZH + 0.8, "M_Plaster")
    mb.cyl(-0.6, 2.2, ZH, ZH + 0.35, 1.5, "M_Plaster", seg=8, r_top=0.6)
    obj(mb, "COL_Ruin", (0, 0, 0))

    # ---------------- 锚点（内景锚点由 build_interiors 生成，名字和位置不变）+ 寻谱点 + 特效
    pages = [(-2.4, 1.0, ZH), (0.9, 4.6, ZH), (-4.6, 4.2, ZH), (3.6, -0.9, ZH), (-0.2, -3.8, ZH), (-5.8, -8.4, 0.0),
             (4.4, -9.6, 0.0), (8.4, -4.0, 0.35), (-8.4, 3.5, 0.35), (1.2, 7.6, 0.0), (-4.2, 13.6, 0.6), (6.5, 16.2, 0.6)]
    for i, p in enumerate(pages):
        anchor(f"ANCHOR_search_page_{i + 1:02d}", p)
    anchor("ANCHOR_search_photo", (-6.2, 16.6, 0.6))          # 后堂谱柜脚下找到父亲照片
    anchor("ANCHOR_search_case", (2.1, 2.6, ZH))
    anchor("ANCHOR_cam_ruin", (6.0, -4.0, 4.5))
    fx("FX_SnowFall", (-0.6, 2.4, 9.0))
    fx("FX_Dust_Hall", (-0.6, 2.4, 2.0))
    fx("FX_Dust_Rear", (0.0, 14.0, 2.0))
    fx("FX_Dust_Gate", (0.0, -14.0, 2.0))


def sorted_ccw(pts):
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    return sorted(pts, key=lambda p: math.atan2(p[1] - cy, p[0] - cx))


# ================================================================= 第四幕 · 道具
def build_scattered_pages():
    """散落谱页 12 张（Page_01..12）：平摊 / 对折 / 烧边 / 沾泥 / 撕角 / 卷边，按 1.6 × 1.2 m 散开；每页原点在页中心落地。"""
    rng = random.Random(12)
    W, Hh = 0.09, 0.125
    kinds = ["flat", "fold", "burnt", "mud", "torn", "fold", "burnt", "flat", "mud", "curl", "burnt", "torn"]
    for i, kd in enumerate(kinds):
        mb = K.MB()
        paper = "M_A4_PaperOld" if i % 3 else "M_A4_Paper"
        if kd == "fold":                                  # 对折：右半页立起 35°
            slab(mb, [(-W, -Hh), (0, -Hh), (0, Hh), (-W, Hh)], 0, 0.0015, paper)
            with mb.at(0, 0, 0, ry=-35):
                slab(mb, [(0, -Hh), (W, -Hh), (W, Hh), (0, Hh)], 0, 0.0015, paper)
                page_lines(mb, 0.01, -Hh + 0.02, W - 0.01, Hh - 0.02, 0.0015, 3)
            page_lines(mb, -W + 0.01, -Hh + 0.02, -0.01, Hh - 0.02, 0.0015, 3)
        elif kd == "curl":                                # 卷边：三段折线翘起
            slab(mb, [(-W, -Hh), (W * 0.3, -Hh), (W * 0.3, Hh), (-W, Hh)], 0, 0.0015, paper)
            with mb.at(W * 0.3, 0, 0, ry=-25):
                slab(mb, [(0, -Hh), (W * 0.4, -Hh), (W * 0.4, Hh), (0, Hh)], 0, 0.0015, paper)
                with mb.at(W * 0.4, 0, 0, ry=-45):
                    slab(mb, [(0, -Hh), (W * 0.35, -Hh), (W * 0.35, Hh), (0, Hh)], 0, 0.0015, paper)
            page_lines(mb, -W + 0.01, -Hh + 0.02, W * 0.25, Hh - 0.02, 0.0015, 4)
        elif kd == "burnt":                               # 烧边：轮廓残缺 + 一圈焦边 + 焦黄晕
            pts = [(-W, -Hh), (W * 0.4, -Hh), (W * 0.9, -Hh * 0.4), (W * 0.7, Hh * 0.5), (0.0, Hh), (-W, Hh)]
            slab(mb, pts, 0, 0.0015, paper)
            slab(mb, [(W * 0.3, -Hh), (W * 0.4, -Hh), (W * 0.9, -Hh * 0.4), (W * 0.7, Hh * 0.5), (0.0, Hh), (W * 0.1, Hh * 0.6)],
                 0.0015, 0.0018, "M_A4_PaperScorch")
            slab(mb, [(W * 0.6, -Hh * 0.75), (W * 0.9, -Hh * 0.4), (W * 0.7, Hh * 0.5), (W * 0.5, Hh * 0.55)],
                 0.0018, 0.0021, "M_A4_PaperBurnt")
            slab(mb, [(W * 0.15, Hh * 0.8), (W * 0.45, Hh * 0.68), (0.0, Hh), (-0.004, Hh * 0.98)], 0.0018, 0.0021, "M_A4_PaperBurnt")
            page_lines(mb, -W + 0.01, -Hh + 0.02, W * 0.1, Hh - 0.02, 0.0015, 4)
        elif kd == "torn":                                # 撕角：缺一个大角
            slab(mb, [(-W, -Hh), (W, -Hh), (W, Hh * 0.1), (W * 0.2, Hh), (-W, Hh)], 0, 0.0015, paper)
            page_lines(mb, -W + 0.01, -Hh + 0.02, W * 0.15, Hh - 0.02, 0.0015, 4 if i % 2 else 3)
        else:
            slab(mb, [(-W, -Hh), (W, -Hh), (W, Hh), (-W, Hh)], 0, 0.0015, paper)
            page_lines(mb, -W + 0.01, -Hh + 0.02, W - 0.01, Hh - 0.02, 0.0015, 6)
        if kd == "mud" or i in (4, 10):                   # 泥渍 / 鞋印
            slab(mb, blob(rng, (rng.random() - 0.5) * W, (rng.random() - 0.5) * Hh, 0.05, 7), 0.0016, 0.0024, "M_A4_Mud")
            if kd == "mud":
                for k in range(4):
                    slab(mb, [(-0.025, -0.012 + k * 0.03 - 0.05), (0.025, -0.012 + k * 0.03 - 0.05), (0.025, k * 0.03 - 0.05),
                              (-0.025, k * 0.03 - 0.05)], 0.0016, 0.0026, "M_A4_Mud")
        x = (i % 4 - 1.5) * 0.42 + (rng.random() - 0.5) * 0.15
        y = (i // 4 - 1) * 0.42 + (rng.random() - 0.5) * 0.15
        ob = obj(mb, f"Page_{i + 1:02d}", (x, y, 0.0), uv=0.5)
        ob.rotation_euler = (0, 0, 0)
        # 页面整体再转一个角度（直接转顶点，保持物体旋转为 0）
        _rotate_mesh_z(ob, rng.random() * 360)


def _rotate_mesh_z(ob, deg):
    from mathutils import Matrix
    ob.data.transform(Matrix.Rotation(math.radians(deg), 4, "Z"))
    ob.data.update()


def build_search_debris():
    """瓦砾 / 灰烬 / 断木，几个可散布的子物体（各自原点在底面中心）：
    Rubble_Pile 碎砖瓦堆、Ash_Pile 灰烬堆（带焦木头）、Beam_Broken 断梁（劈裂端）、Tiles_Scatter 散落碎瓦、Planks 断板一摞、Snow_Patch 积雪片。"""
    rng = random.Random(44)
    mb = K.MB()
    mound(mb, rng, 0, 0, 0, 0.9, 0.35, "M_A4_Rubble", n=9)
    rubble(mb, rng, 0, 0, 0.15, 0.75, 36, ["M_A4_Tile", "M_A4_Rubble", "M_A4_Brick", "M_A4_Tile"], 0.05, 0.18)
    obj(mb, "Rubble_Pile", (-2.0, 0, 0))
    mb = K.MB()
    mound(mb, rng, 0, 0, 0, 0.6, 0.16, "M_A4_Ash", n=9)
    mound(mb, rng, 0.1, 0.05, 0.1, 0.3, 0.08, "M_A4_AshLight", n=7)
    for k in range(6):
        with mb.at((rng.random() - 0.5) * 0.7, (rng.random() - 0.5) * 0.7, 0.08, rz=rng.random() * 180, ry=(rng.random() - 0.5) * 30):
            mb.box(-0.25, -0.03, 0, 0.25, 0.03, 0.05, "M_A4_Char")
    rubble(mb, rng, 0, 0, 0.12, 0.4, 6, ["M_A4_PaperBurnt"], 0.02, 0.05)
    obj(mb, "Ash_Pile", (-0.4, 0.2, 0))
    mb = K.MB()
    mb.box(-1.2, -0.11, 0, 0.9, 0.11, 0.22, "M_A4_CharWood")
    for k, (dy, dz) in enumerate(((-0.07, 0.04), (0.0, 0.13), (0.07, 0.06))):         # 劈裂的端头
        mb.prism([(0.9, dz - 0.04), (1.15 + 0.12 * k, dz), (0.9, dz + 0.05)], "y", dy - 0.03, dy + 0.03, "M_A4_WoodOld")
    mb.box(-1.2, -0.112, 0.08, -0.6, 0.112, 0.2, "M_A4_Char")
    obj(mb, "Beam_Broken", (1.2, 0.4, 0))
    mb = K.MB()
    for k in range(18):
        with mb.at((rng.random() - 0.5) * 1.4, (rng.random() - 0.5) * 1.0, 0, rz=rng.random() * 180, rx=(rng.random() - 0.5) * 20):
            mb.prism([(-0.1, 0), (0.1, 0), (0.08, 0.02), (-0.08, 0.02)], "y", -0.06 - 0.05 * rng.random(), 0.07, "M_A4_Tile")
    obj(mb, "Tiles_Scatter", (-1.0, -1.4, 0))
    mb = K.MB()
    for k in range(5):
        with mb.at(0, 0, k * 0.045, rz=(rng.random() - 0.5) * 30):
            mb.box(-0.8 + 0.2 * rng.random(), -0.12, 0, 0.8, 0.12, 0.04, "M_A4_WoodOld" if k % 2 else "M_A4_CharWood")
    obj(mb, "Planks", (1.0, -1.3, 0))
    mb = K.MB()
    poly_xy(mb, blob(rng, 0, 0, 0.8, 10, 0.7), 0, 0.04, "M_A4_Snow")
    mound(mb, rng, 0.2, 0.1, 0.02, 0.35, 0.08, "M_A4_Snow", n=8)
    obj(mb, "Snow_Patch", (2.6, -0.6, 0))


def build_search_kit():
    """日军搜查工具（刺刀已在 PROP_JpRifle，不重复）：Flashlight 方头军用手电、Crowbar 铁撬、Sack 麻袋（鼓的，扎口）、
    Ledger 登记簿（合）+ Ledger_Open（摊开）、Seal_Strip 封条（交叉两条，贴门/箱用）。"""
    mb = K.MB()                                                                       # 手电：立放，灯头朝 -Y
    mb.box(-0.032, -0.02, 0, 0.032, 0.02, 0.13, "M_A4_Khaki")
    mb.box(-0.04, -0.03, 0.06, 0.04, 0.02, 0.13, "M_A4_Khaki")
    with mb.at(0, -0.03, 0.095, rx=90):
        mb.cyl(0, 0, 0, 0.02, 0.034, "M_A4_Steel", seg=10)
        mb.cyl(0, 0, 0.02, 0.022, 0.028, "M_A4_Lens", seg=10)
    mb.box(-0.008, -0.022, 0.13, 0.008, 0.022, 0.15, "M_A4_Steel")
    mb.box(-0.03, 0.02, 0.03, 0.03, 0.026, 0.12, "M_A4_Iron")
    obj(mb, "Flashlight", (-0.5, 0, 0))
    fx("FX_Flashlight", (-0.5, -0.06, 0.095))
    mb = K.MB()                                                                       # 铁撬：平放，一端弯钩分叉
    mb.box(-0.4, -0.012, 0, 0.32, 0.012, 0.024, "M_A4_Iron")
    with mb.at(0.32, 0, 0, rz=0, ry=-40):
        mb.box(0, -0.012, 0, 0.1, 0.012, 0.024, "M_A4_Iron")
    mb.prism([(-0.4, 0), (-0.47, 0.004), (-0.47, 0.012), (-0.4, 0.024)], "y", -0.014, 0.014, "M_A4_Iron")
    obj(mb, "Crowbar", (0, 0.3, 0))
    mb = K.MB()                                                                       # 麻袋
    mb.ico(0, 0, 0.2, 0.25, "M_A4_Sack", sx=1.0, sy=0.75, sz=0.85, subdiv=1)
    mb.cyl(0, 0, 0.38, 0.47, 0.06, "M_A4_Sack", seg=6, r_top=0.09)
    mb.cyl(0, 0, 0.4, 0.43, 0.065, "M_A4_Rope", seg=6)
    ob = obj(mb, "Sack", (0.6, 0.1, 0))
    _drop_to_ground(ob)
    mb = K.MB()                                                                       # 登记簿（合）
    mb.box(-0.11, -0.15, 0, 0.11, 0.15, 0.025, "M_A4_LedgerCover")
    mb.box(-0.105, -0.145, 0.004, 0.115, 0.145, 0.021, "M_A4_Paper")
    mb.box(-0.06, -0.1, 0.025, 0.06, 0.05, 0.026, "M_A4_SealStrip")
    obj(mb, "Ledger", (0.0, -0.3, 0))
    mb = K.MB()                                                                       # 登记簿（开）：表格格线
    mb.box(-0.22, -0.15, 0, 0.22, 0.15, 0.006, "M_A4_LedgerCover")
    for sx in (-1, 1):
        mb.box(sx * 0.005 if sx > 0 else -0.21, -0.14, 0.006, 0.21 if sx > 0 else -0.005, 0.14, 0.012, "M_A4_Paper")
        for k in range(6):
            y = -0.12 + k * 0.045
            mb.box(-0.205 if sx < 0 else 0.01, y, 0.012, -0.01 if sx < 0 else 0.205, y + 0.002, 0.0124, "M_A4_Ink")
    for x in (-0.15, -0.08, 0.06, 0.13):
        mb.box(x, -0.13, 0.012, x + 0.002, 0.13, 0.0124, "M_A4_Ink")
    mb.box(0.12, 0.08, 0.012, 0.16, 0.12, 0.0126, "M_A4_SealRed")
    obj(mb, "Ledger_Open", (0.35, -0.45, 0))
    mb = K.MB()                                                                       # 封条：两条交叉，平放
    for rz in (30, -30):
        with mb.at(0, 0, 0, rz=rz):
            mb.box(-0.3, -0.04, 0, 0.3, 0.04, 0.002, "M_A4_SealStrip")
            mb.box(-0.04, -0.035, 0.002, 0.04, 0.035, 0.003, "M_A4_SealRed")
    ob = obj(mb, "Seal_Strip", (-0.4, -0.5, 0))
    uv01(ob, 0, 1)


def _drop_to_ground(ob):
    zmin = min(v.co.z for v in ob.data.vertices)
    for v in ob.data.vertices:
        v.co.z -= zmin
    ob.data.update()


# ================================================================= 第五幕 · 修谱
def build_repair_table():
    """修谱长案（2.6 × 0.8 × 0.82）：毛毡、两根铜压尺 Ruler_1/2、浆糊碗 Paste_Bowl（带刷）、待补页 Page_Repair_1..3（有缺口/裂缝）、
    新纸一摞 Paper_Stack、油灯 Lamp，案后一条长凳 Bench。写字站位在 -Y 一侧。"""
    L, Wd, H = 1.3, 0.4, 0.82
    mb = K.MB()
    mb.box(-L, -Wd, H - 0.06, L, Wd, H, "M_A5_Wood")
    mb.box(-L - 0.04, -Wd, H - 0.06, -L, Wd, H + 0.04, "M_A5_WoodDark")          # 翘头
    mb.box(L, -Wd, H - 0.06, L + 0.04, Wd, H + 0.04, "M_A5_WoodDark")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(sx * (L - 0.12) - 0.04, sy * (Wd - 0.08) - 0.04, 0, sx * (L - 0.12) + 0.04, sy * (Wd - 0.08) + 0.04, H - 0.06, "M_A5_WoodDark")
        mb.box(sx * (L - 0.12) - 0.035, -Wd + 0.08, 0.12, sx * (L - 0.12) + 0.035, Wd - 0.08, 0.17, "M_A5_WoodDark")
    mb.box(-L + 0.12, -Wd + 0.06, H - 0.16, L - 0.12, -Wd + 0.1, H - 0.06, "M_A5_WoodDark")   # 牙板
    mb.box(-0.9, -0.32, H, 0.9, 0.3, H + 0.006, "M_A5_Felt")                         # 毛毡
    obj(mb, "Table", (0, 0, 0))
    mb = K.MB()                                                                       # 长凳（写字的人坐/站在 -Y）
    mb.box(-0.9, -0.13, 0.42, 0.9, 0.13, 0.47, "M_A5_Wood")
    for sx in (-1, 1):
        mb.box(sx * 0.75 - 0.04, -0.1, 0, sx * 0.75 + 0.04, 0.1, 0.42, "M_A5_WoodDark")
    obj(mb, "Bench", (0, -0.85, 0))
    for i, x in enumerate((-0.55, 0.45)):                                            # 铜压尺
        mb = K.MB()
        mb.box(-0.02, -0.17, 0, 0.02, 0.17, 0.018, "M_A5_Bronze")
        mb.box(-0.008, -0.04, 0.018, 0.008, 0.04, 0.03, "M_A5_Bronze")
        obj(mb, f"Ruler_{i + 1}", (x, -0.02, H + 0.006))
    mb = K.MB()                                                                       # 浆糊碗 + 刷
    mb.cyl(0, 0, 0, 0.012, 0.045, "M_A5_Porcelain", seg=10)
    mb.cyl(0, 0, 0.012, 0.06, 0.05, "M_A5_Porcelain", seg=10, r_top=0.075)
    mb.cyl(0, 0, 0.045, 0.048, 0.068, "M_A5_Paste", seg=10)
    with mb.at(0.02, 0, 0.05, ry=-60):
        mb.box(-0.006, -0.012, 0, 0.006, 0.012, 0.16, "M_A5_Bamboo")
        mb.box(-0.008, -0.016, -0.03, 0.008, 0.016, 0.0, "M_A5_Hair")
    obj(mb, "Paste_Bowl", (1.05, 0.22, H))
    for i, (x, y, rz) in enumerate(((-0.25, 0.0, 3), (0.12, 0.05, -5), (-0.05, 0.18, 8))):   # 待补页
        mb = K.MB()
        slab(mb, [(-0.09, -0.125), (0.09, -0.125), (0.09, 0.02), (0.03, 0.06), (0.09, 0.125), (-0.09, 0.125)], 0, 0.0015, "M_A5_PaperOld")
        slab(mb, [(0.03, 0.06), (0.09, 0.02), (0.09, 0.125)], 0, 0.0012, "M_A5_PaperNew")         # 补上的新纸
        page_lines(mb, -0.08, -0.11, 0.02, 0.11, 0.0015, 4, "M_A5_Ink")
        ob = obj(mb, f"Page_Repair_{i + 1}", (x, y, H + 0.007 + 0.002 * i))
        _rotate_mesh_z(ob, rz)
        uv01(ob, 0, 1)
    mb = K.MB()                                                                       # 新纸一摞
    for k in range(6):
        mb.box(-0.1, -0.13, k * 0.004, 0.1, 0.13, k * 0.004 + 0.004, "M_A5_PaperNew")
    obj(mb, "Paper_Stack", (-1.0, 0.15, H + 0.006))
    mb = K.MB()                                                                       # 油灯（灯座 + 灯盏）
    mb.cyl(0, 0, 0, 0.02, 0.06, "M_A5_Bronze", seg=8)
    mb.cyl(0, 0, 0.02, 0.22, 0.012, "M_A5_Bronze", seg=6)
    mb.cyl(0, 0, 0.22, 0.25, 0.05, "M_A5_Porcelain", seg=8, r_top=0.06)
    obj(mb, "Lamp", (1.1, -0.2, H))
    fx("FX_Lamp", (1.1 + 0.04, -0.2, H + 0.27))
    anchor("ANCHOR_Writer", (0, -0.75, 0))
    anchor("ANCHOR_Book", (0.0, 0.0, H + 0.007))
    anchor("ANCHOR_BrushInk", (0.75, 0.1, H + 0.006))
    anchor("ANCHOR_Seal", (-0.75, -0.15, H + 0.006))
    fx("FX_Ink", (0.0, -0.05, H + 0.02))


def build_brush_ink():
    """文房：Brush 毛笔（原点在笔杆中点，搁在笔架上）、Brush_Small、BrushRest 山形笔架、Inkstone 砚（带墨池）、InkStick 墨锭、WaterDropper 水盂。"""
    mb = K.MB()                                                                       # 笔架：三峰
    mb.box(-0.09, -0.015, 0, 0.09, 0.015, 0.012, "M_A5_WoodDark")
    for x, h in ((-0.06, 0.05), (0.0, 0.07), (0.06, 0.05)):
        mb.prism([(x - 0.03, 0.012), (x + 0.03, 0.012), (x, 0.012 + h)], "y", -0.012, 0.012, "M_A5_WoodDark")
    obj(mb, "BrushRest", (0, 0.12, 0))
    for name, L, r, y, z in (("Brush", 0.24, 0.0055, 0.12, 0.05), ("Brush_Small", 0.19, 0.004, 0.12, 0.05)):
        mb = K.MB()
        with mb.at(0, 0, 0, ry=90):
            mb.cyl(0, 0, -L / 2, L / 2, r, "M_A5_Bamboo", seg=6)
            mb.cyl(0, 0, L / 2, L / 2 + 0.008, r * 1.1, "M_A5_WoodDark", seg=6)
            mb.cyl(0, 0, L / 2 + 0.008, L / 2 + 0.04, r * 1.2, "M_A5_Hair", seg=6, r_top=0.0008)
        ob = obj(mb, name, (0.02 if name == "Brush" else -0.01, y + (0.0 if name == "Brush" else 0.0), z + (0.0 if name == "Brush" else 0.018)))
    # 砚：长方石砚，前低后高的墨池
    mb = K.MB()
    mb.box(-0.07, -0.1, 0, 0.07, 0.1, 0.03, "M_A5_InkStone")
    mb.box(-0.055, -0.085, 0.03, 0.055, 0.03, 0.032, "M_A5_Stone")
    mb.box(-0.055, 0.045, 0.012, 0.055, 0.085, 0.022, "M_A5_Ink")                     # 墨池
    for x0, x1, y0, y1 in ((-0.07, 0.07, 0.03, 0.045), (-0.07, 0.07, 0.085, 0.1), (-0.07, -0.055, 0.03, 0.1), (0.055, 0.07, 0.03, 0.1)):
        mb.box(x0, y0, 0.02, x1, y1, 0.03, "M_A5_InkStone")
    obj(mb, "Inkstone", (-0.05, -0.1, 0))
    mb = K.MB()                                                                       # 墨锭：斜靠砚边
    mb.box(-0.01, -0.04, 0, 0.01, 0.04, 0.012, "M_A5_Ink")
    mb.box(-0.008, -0.03, 0.012, 0.008, 0.03, 0.0125, "M_A5_PaperGold")
    obj(mb, "InkStick", (0.07, -0.08, 0))
    mb = K.MB()                                                                       # 水盂：扁圆瓷罐 + 小勺
    mb.cyl(0, 0, 0, 0.01, 0.025, "M_A5_PorcelainBlue", seg=10)
    mb.cyl(0, 0, 0.01, 0.035, 0.04, "M_A5_PorcelainBlue", seg=10, r_top=0.035)
    mb.cyl(0, 0, 0.035, 0.045, 0.035, "M_A5_PorcelainBlue", seg=10, r_top=0.018)
    with mb.at(0.0, 0, 0.04, ry=-50):
        mb.box(-0.002, -0.003, 0, 0.002, 0.003, 0.06, "M_A5_Bronze")
    obj(mb, "WaterDropper", (0.12, 0.0, 0))
    fx("FX_InkDrip", (-0.05, -0.08, 0.035))


def build_seal():
    """印章（王氏宗族印）：Seal 方印（钮雕成卧兽，原点在印面中心），SealPad_Box 圆瓷印泥盒（含印泥）+ SealPad_Lid 盖，
    Stamp_Mark 盖在纸上的红印（0..1 UV，换印文贴图）。"""
    mb = K.MB()
    s = 0.028
    mb.box(-s, -s, 0, s, s, 0.004, "M_A5_SealRed")                                  # 印面沾印泥
    mb.box(-s, -s, 0.004, s, s, 0.055, "M_A5_SealStone")
    mb.ico(0, 0, 0.07, 0.024, "M_A5_SealStone", sx=1.0, sy=1.3, sz=0.7, subdiv=1)    # 卧兽钮
    mb.ico(0, -0.028, 0.08, 0.012, "M_A5_SealStone", subdiv=1)
    obj(mb, "Seal", (0, 0, 0))
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.004, 0.035, "M_A5_Porcelain", seg=12)
    mb.cyl(0, 0, 0.004, 0.025, 0.045, "M_A5_Porcelain", seg=12, r_top=0.046)
    mb.cyl(0, 0, 0.025, 0.026, 0.04, "M_A5_SealPad", seg=12)
    obj(mb, "SealPad_Box", (0.12, 0, 0))
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.018, 0.047, "M_A5_PorcelainBlue", seg=12, r_top=0.04)
    mb.cyl(0, 0, 0.018, 0.024, 0.03, "M_A5_PorcelainBlue", seg=12, r_top=0.022)
    obj(mb, "SealPad_Lid", (0.12, 0.11, 0))
    mb = K.MB()
    mb.box(-s, -s, 0, s, s, 0.0004, "M_A5_SealRed")
    ob = obj(mb, "Stamp_Mark", (-0.1, 0, 0))
    uv01(ob, 0, 1)
    fx("FX_Stamp", (0, 0, 0.0))


def build_genealogy_final():
    """修好的族谱（与 PROP_Genealogy 同风格，但新、完整）：Book_Closed 合（整本厚度、新靛蓝书衣、新题签）、Book_Open 开（两页写满），
    Slot_1..8 八个关键页槽（开本上的八条竖格，团结里按序点亮/显字）、Case 新谱匣 + Case_Lid（枢轴在后沿）、Ribbon 包谱的红绸带。"""
    mb = K.MB()
    mb.box(-0.13, -0.09, 0, 0.13, 0.09, 0.004, "M_A5_BookCover")
    mb.box(-0.128, -0.088, 0.004, 0.128, 0.088, 0.03, "M_A5_PaperNew")
    mb.box(-0.13, -0.09, 0.03, 0.13, 0.09, 0.034, "M_A5_BookCover")
    mb.box(-0.12, -0.075, 0.034, -0.08, 0.075, 0.0352, "M_A5_BookLabel")             # 题签
    for y in (-0.06, -0.02, 0.02, 0.06):
        mb.box(-0.127, y - 0.002, -0.0005, -0.115, y + 0.002, 0.0345, "M_A5_Thread")
    ob = obj(mb, "Book_Closed", (0, 0, 0))
    mb = K.MB()
    mb.box(-0.26, -0.09, 0, 0.0, 0.09, 0.006, "M_A5_BookCover")
    mb.box(0.0, -0.09, 0, 0.26, 0.09, 0.006, "M_A5_BookCover")
    mb.box(-0.25, -0.085, 0.006, -0.004, 0.085, 0.016, "M_A5_PaperNew")
    mb.box(0.004, -0.085, 0.006, 0.25, 0.085, 0.016, "M_A5_PaperNew")
    mb.box(-0.004, -0.085, 0.006, 0.004, 0.085, 0.012, "M_A5_Thread")
    for x0, x1 in ((-0.24, -0.135), (0.135, 0.24)):                                  # 页槽以外的已有字行
        page_lines(mb, x0, -0.07, x1, 0.07, 0.016, 3, "M_A5_Ink")
    obj(mb, "Book_Open", (0.0, -0.32, 0))
    for i in range(8):                                                               # 八个关键页槽：右→左竖排（右页 1..4，左页 5..8）
        mb = K.MB()
        mb.box(-0.011, -0.07, 0, 0.011, 0.07, 0.0006, "M_A5_SlotInk")
        x = 0.115 - (i % 4) * 0.028 if i < 4 else -0.025 - (i % 4) * 0.028
        ob = obj(mb, f"Slot_{i + 1}", (x, -0.32, 0.016))
        uv01(ob, 0, 1)
    mb = K.MB()                                                                      # 新谱匣：樟木 + 铜角 + 锁扣
    mb.box(-0.17, -0.12, 0, 0.17, 0.12, 0.012, "M_A5_CaseWood")
    for x0, x1, y0, y1 in ((-0.17, 0.17, -0.12, -0.105), (-0.17, 0.17, 0.105, 0.12), (-0.17, -0.155, -0.12, 0.12), (0.155, 0.17, -0.12, 0.12)):
        mb.box(x0, y0, 0.012, x1, y1, 0.09, "M_A5_CaseWood")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(sx * 0.172 - 0.012, sy * 0.122 - 0.012, 0, sx * 0.172 + 0.012, sy * 0.122 + 0.012, 0.025, "M_A5_Brass")
    mb.box(-0.02, -0.124, 0.06, 0.02, -0.12, 0.085, "M_A5_Brass")
    obj(mb, "Case", (-0.42, 0, 0))
    mb = K.MB()
    mb.box(-0.175, -0.245, 0, 0.175, 0.0, 0.03, "M_A5_CaseWood")
    mb.box(-0.12, -0.2, 0.03, 0.12, -0.045, 0.034, "M_A5_Lacquer")
    mb.box(-0.08, -0.17, 0.034, 0.08, -0.075, 0.035, "M_A5_BookLabel")
    ob = obj(mb, "Case_Lid", (-0.42, 0.125, 0.09))
    mb = K.MB()                                                                      # 红绸带：缠在合着的谱上（十字）
    mb.box(-0.132, -0.012, -0.001, 0.132, 0.012, 0.036, "M_A5_ClothRed")
    mb.box(0.04, -0.092, -0.001, 0.062, 0.092, 0.036, "M_A5_ClothRed")
    mb.box(0.03, -0.02, 0.036, 0.072, 0.02, 0.045, "M_A5_ClothRed")
    obj(mb, "Ribbon", (0, 0, 0))
    fx("FX_Glow", (0, -0.32, 0.03))


# ================================================================= 第五幕 · 路祭 / 巡游道具
def build_offering():
    """路祭供桌陈设：Table 供桌（红桌围）+ Pig 猪头、Chicken 整鸡、Fish 鱼（三牲，各在盘里）、Peaches 面桃一盘、
    Candle_L/R 红烛、PaperMoney 纸钱/元宝、Censer 小香炉。烛火 / 香烟挂点 FX_*。"""
    H = 0.86
    mb = K.MB()
    mb.box(-0.8, -0.35, H - 0.05, 0.8, 0.35, H, "M_A5_WoodDark")
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.box(sx * 0.74 - 0.04, sy * 0.29 - 0.04, 0, sx * 0.74 + 0.04, sy * 0.29 + 0.04, H - 0.05, "M_A5_WoodDark")
    mb.box(-0.82, -0.37, 0.25, 0.82, -0.355, H, "M_A5_ClothRed")                     # 桌围
    mb.box(-0.82, -0.375, H - 0.14, 0.82, -0.37, H - 0.06, "M_A5_ClothYellow")
    obj(mb, "Table", (0, 0, 0))

    def plate(m, r=0.13):
        m.cyl(0, 0, 0, 0.012, r * 0.7, "M_A5_Plate", seg=12)
        m.cyl(0, 0, 0.012, 0.025, r * 0.7, "M_A5_Plate", seg=12, r_top=r)
    mb = K.MB()                                                                      # 猪头
    plate(mb, 0.18)
    mb.ico(0, 0.02, 0.12, 0.11, "M_A5_Pig", sx=1.0, sy=1.15, sz=0.85, subdiv=1)
    mb.cyl(0, -0.09, 0.1, 0.12, 0.045, "M_A5_PigDark", seg=8)
    with mb.at(0, -0.09, 0.1, rx=90):
        mb.cyl(0, 0, 0, 0.06, 0.05, "M_A5_Pig", seg=8, r_top=0.045)
    for sx in (-1, 1):
        mb.prism([(sx * 0.05, 0.19), (sx * 0.11, 0.2), (sx * 0.09, 0.28)], "y", 0.02, 0.05, "M_A5_PigDark")
        mb.box(sx * 0.04 - 0.012, -0.075, 0.15, sx * 0.04 + 0.012, -0.07, 0.165, "M_A5_Eye")
    obj(mb, "Pig", (0, 0.05, H))
    mb = K.MB()                                                                      # 整鸡（卧姿）
    plate(mb, 0.15)
    mb.ico(0, 0, 0.08, 0.08, "M_A5_Chicken", sx=1.0, sy=1.4, sz=0.75, subdiv=1)
    with mb.at(0, -0.1, 0.1, rx=30):
        mb.cyl(0, 0, 0, 0.07, 0.022, "M_A5_Chicken", seg=6, r_top=0.016)
    mb.ico(0, -0.13, 0.17, 0.03, "M_A5_Chicken", subdiv=1)
    mb.box(-0.006, -0.15, 0.19, 0.006, -0.12, 0.215, "M_A5_Candle")
    obj(mb, "Chicken", (-0.45, 0.02, H))
    mb = K.MB()                                                                      # 鱼
    mb.cyl(0, 0, 0, 0.02, 0.12, "M_A5_Plate", seg=12)
    loft_y(mb, [(-0.14, 0, 0.04, 0.005, 0.01), (-0.08, 0, 0.045, 0.03, 0.035), (0.05, 0, 0.045, 0.028, 0.03), (0.12, 0, 0.04, 0.008, 0.012)],
           "M_A5_Fish", seg=6)
    with mb.at(0, 0.13, 0.04):
        mb.prism([(0.0, 0.0), (0.05, 0.035), (0.05, -0.035)], "x", -0.003, 0.003, "M_A5_Fish")
    obj(mb, "Fish", (0.45, 0.02, H))
    mb = K.MB()                                                                      # 面桃：盘里堆一座（底 7、上 3、顶 1）
    plate(mb, 0.14)
    pts = [(0, 0, 0)] + [(0.06 * math.cos(a * math.pi / 3), 0.06 * math.sin(a * math.pi / 3), 0) for a in range(6)] + \
          [(0.032 * math.cos(a * 2 * math.pi / 3), 0.032 * math.sin(a * 2 * math.pi / 3), 0.045) for a in range(3)] + [(0, 0, 0.085)]
    for x, y, z in pts:
        mb.ico(x, y, 0.045 + z, 0.03, "M_A5_Bun", sz=1.05, subdiv=1)
        mb.ico(x, y - 0.004, 0.072 + z, 0.008, "M_A5_BunPink", subdiv=1)
    obj(mb, "Peaches", (0.0, -0.2, H))
    for name, x in (("Candle_L", -0.68), ("Candle_R", 0.68)):
        mb = K.MB()
        mb.cyl(0, 0, 0, 0.02, 0.05, "M_A5_Bronze", seg=8)
        mb.cyl(0, 0, 0.02, 0.09, 0.012, "M_A5_Bronze", seg=6)
        mb.cyl(0, 0, 0.09, 0.1, 0.03, "M_A5_Bronze", seg=8)
        mb.cyl(0, 0, 0.1, 0.32, 0.02, "M_A5_Candle", seg=8)
        mb.box(-0.004, -0.004, 0.32, 0.004, 0.004, 0.34, "M_A5_Ink")
        obj(mb, name, (x, 0.12, H))
        fx(f"FX_{name}", (x, 0.12, H + 0.36))
    mb = K.MB()                                                                      # 纸钱两摞 + 两只纸元宝
    for k in range(8):
        mb.box(-0.06, -0.035, k * 0.005, 0.06, 0.035, k * 0.005 + 0.005, "M_A5_PaperMoney" if k % 2 else "M_A5_PaperGold")
    for sx in (-1, 1):
        with mb.at(0.16 * sx, 0, 0):
            mb.prism(
                     [(-0.05, 0.0), (0.05, 0.0), (0.07, 0.04), (-0.07, 0.04)], "y", -0.025, 0.025, "M_A5_PaperGold")
            mb.ico(0, 0, 0.035, 0.022, "M_A5_PaperGold", subdiv=1)
    obj(mb, "PaperMoney", (-0.45, -0.22, H))
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.09, 0.07, "M_A5_Bronze", seg=10, r_top=0.09)
    mb.cyl(0, 0, 0.09, 0.095, 0.08, "M_A4_AshLight", seg=10)
    for k in range(3):
        mb.box(-0.03 + 0.03 * k - 0.002, -0.002, 0.09, -0.03 + 0.03 * k + 0.002, 0.002, 0.3, "M_A5_Candle")
    obj(mb, "Censer", (0.45, -0.2, H))
    fx("FX_Incense", (0.45, -0.2, H + 0.32))
    anchor("ANCHOR_Kneel", (0, -0.9, 0))


def _flag_cloth(name, pts_fn, loc, mat="M_A5_FlagFace", nu=6, wave=0.06):
    """旗面：沿 X 分 nu 段，每段一块凸四边形薄片，按正弦在 Y 方向起伏；0..1 UV（正反都读正字）。"""
    mb = K.MB()
    for i in range(nu):
        u0, u1 = i / nu, (i + 1) / nu
        q = pts_fn(u0, u1)                    # [(x,z) × 4]，逆时针
        y0 = wave * math.sin(u0 * math.pi * 1.6)
        y1 = wave * math.sin(u1 * math.pi * 1.6)
        b = mb.addv([(q[0][0], y0 - 0.004, q[0][1]), (q[1][0], y1 - 0.004, q[1][1]), (q[2][0], y1 - 0.004, q[2][1]), (q[3][0], y0 - 0.004, q[3][1]),
                     (q[0][0], y0 + 0.004, q[0][1]), (q[1][0], y1 + 0.004, q[1][1]), (q[2][0], y1 + 0.004, q[2][1]), (q[3][0], y0 + 0.004, q[3][1])])
        mb.face([b + 0, b + 1, b + 2, b + 3], mat)
        mb.face([b + 7, b + 6, b + 5, b + 4], mat)
        for a_, b_ in ((0, 1), (1, 2), (2, 3), (3, 0)):
            mb.face([b + a_, b + 4 + a_, b + 4 + b_, b + b_], mat)
    ob = obj(mb, name, loc)
    uv01(ob, 0, 2, flip_axis=(1, 1))
    return ob


def build_parade_flag(kind):
    """姓氏旗（三种形制，杆底在原点；旗面 Cloth 单独、0..1 UV 换字）：
    A 大方旗（4.6 m 杆 + 横杆，旗面 1.0 × 2.2 垂挂，镶边由贴图画）；B 三角牙旗（3.8 m 杆，旗面三角 + 锯齿火焰边 Fringe）；
    C 长幡（3.4 m 丁字杆，窄长幡 0.55 × 2.0，燕尾 + 两条飘带 Streamers）。"""
    mb = K.MB()
    if kind == "A":
        Hp = 4.6
        mb.cyl(0, 0, 0, Hp, 0.03, "M_A5_WoodDark", seg=8, r_top=0.025)
        mb.box(-0.06, -0.02, Hp - 0.22, 1.12, 0.02, Hp - 0.18, "M_A5_WoodDark")           # 横杆
        mb.cyl(1.12, 0, Hp - 0.3, Hp - 0.2, 0.03, "M_A5_ClothRed", seg=6)
        mb.prism([(-0.04, Hp), (0.04, Hp), (0.0, Hp + 0.22)], "y", -0.012, 0.012, "M_A5_Brass")   # 枪头
        mb.cyl(0, 0, Hp - 0.12, Hp, 0.07, "M_A5_ClothRed", seg=8, r_top=0.03)             # 红缨
        obj(mb, "Pole", (0, 0, 0))
        _flag_cloth("Cloth", lambda u0, u1: [(0.06 + 1.0 * u0, Hp - 2.42), (0.06 + 1.0 * u1, Hp - 2.42),
                                              (0.06 + 1.0 * u1, Hp - 0.22), (0.06 + 1.0 * u0, Hp - 0.22)], (0, 0, 0), wave=0.05)
    elif kind == "B":
        Hp = 3.8
        mb.cyl(0, 0, 0, Hp, 0.028, "M_A5_WoodDark", seg=8, r_top=0.022)
        mb.ico(0, 0, Hp + 0.05, 0.06, "M_A5_Brass", subdiv=1)
        mb.cyl(0, 0, Hp - 0.1, Hp, 0.06, "M_A5_ClothYellow", seg=8, r_top=0.03)
        obj(mb, "Pole", (0, 0, 0))
        top, bot, wdt = Hp - 0.15, Hp - 1.75, 1.15      # 三角：竖边贴杆，尖朝外

        def tri(u0, u1):
            def zt(u):
                return top - (top - (bot + 0.45)) * u
            def zb(u):
                return bot + 0.45 * u
            return [(0.03 + wdt * u0, zb(u0)), (0.03 + wdt * u1, zb(u1)), (0.03 + wdt * u1, zt(u1)), (0.03 + wdt * u0, zt(u0))]
        _flag_cloth("Cloth", tri, (0, 0, 0), wave=0.05)
        fr = K.MB()                                                                       # 锯齿火焰边（斜边 + 底边外侧）
        for k in range(7):
            u = (k + 0.5) / 7
            x = 0.03 + wdt * u
            zb_ = bot + 0.45 * u
            y = 0.05 * math.sin(u * math.pi * 1.6)
            fr.prism([(x - 0.06, zb_ + 0.01), (x + 0.06, zb_ + 0.04), (x, zb_ - 0.12)], "y", y - 0.004, y + 0.004, "M_A5_ClothRed")
            zt_ = top - (top - (bot + 0.45)) * u
            fr.prism([(x - 0.06, zt_ - 0.01), (x, zt_ + 0.12), (x + 0.06, zt_ - 0.04)], "y", y - 0.004, y + 0.004, "M_A5_ClothRed")
        obj(fr, "Fringe", (0, 0, 0))
    else:
        Hp = 3.4
        mb.cyl(0, 0, 0, Hp, 0.028, "M_A5_WoodDark", seg=8, r_top=0.022)
        mb.box(-0.03, -0.02, Hp - 0.08, 0.75, 0.02, Hp - 0.03, "M_A5_WoodDark")            # 丁字挑杆
        mb.box(0.1, -0.03, Hp - 0.12, 0.68, 0.03, Hp - 0.08, "M_A5_Lacquer")               # 幡头横木
        mb.ico(0, 0, Hp + 0.04, 0.05, "M_A5_Brass", subdiv=1)
        obj(mb, "Pole", (0, 0, 0))
        x0, x1, ztop, L = 0.12, 0.66, Hp - 0.12, 2.0

        def banner(u0, u1):          # 这里 u 沿竖直方向：把参数映射到 (x, z)，保持逆时针
            z0_ = ztop - L * u1
            z1_ = ztop - L * u0
            return [(x0, z0_), (x1, z0_), (x1, z1_), (x0, z1_)]
        mb2 = K.MB()
        nu = 5
        for i in range(nu):
            u0, u1 = i / nu, (i + 1) / nu
            q = banner(u0, u1)
            yy0 = 0.04 * math.sin(u1 * math.pi * 1.5)
            yy1 = 0.04 * math.sin(u0 * math.pi * 1.5)
            b = mb2.addv([(q[0][0], yy0 - 0.004, q[0][1]), (q[1][0], yy0 - 0.004, q[1][1]), (q[2][0], yy1 - 0.004, q[2][1]), (q[3][0], yy1 - 0.004, q[3][1]),
                          (q[0][0], yy0 + 0.004, q[0][1]), (q[1][0], yy0 + 0.004, q[1][1]), (q[2][0], yy1 + 0.004, q[2][1]), (q[3][0], yy1 + 0.004, q[3][1])])
            mb2.face([b + 0, b + 1, b + 2, b + 3], "M_A5_FlagFace")
            mb2.face([b + 7, b + 6, b + 5, b + 4], "M_A5_FlagFace")
            for a_, b_ in ((0, 1), (1, 2), (2, 3), (3, 0)):
                mb2.face([b + a_, b + 4 + a_, b + 4 + b_, b + b_], "M_A5_FlagFace")
        zb_ = ztop - L
        yb = 0.04 * math.sin(math.pi * 1.5)
        for xa, xb in ((x0, (x0 + x1) / 2), ((x0 + x1) / 2, x1)):                       # 燕尾
            mb2.prism([(xa, zb_), (xb, zb_), ((xa + xb) / 2 + (0.04 if xa == x0 else -0.04), zb_ - 0.25)], "y", yb - 0.004, yb + 0.004, "M_A5_FlagFace")
        ob = obj(mb2, "Cloth", (0, 0, 0))
        uv01(ob, 0, 2, flip_axis=(1, 1))
        st = K.MB()                                                                       # 两条飘带
        for x in (0.08, 0.7):
            st.box(x - 0.025, -0.003, ztop - 1.5, x + 0.025, 0.003, ztop, "M_A5_ClothRed")
        obj(st, "Streamers", (0, 0, 0))
    anchor("ANCHOR_Grip", (0, 0, 1.1))


def build_dragon_lantern():
    """拼字龙灯（舞龙队，8 节 + 头尾）：龙沿 +Y 排开、龙头朝 -Y；Head / Seg_01..08 / Tail 各自是物体，原点在提杆底端（握杆处在 1.0 m），
    灯面换字：Seg_NN_Face（两侧各一块灯面，0..1 UV，背面镜像成正字），八节拼一句话。"""
    sp = 1.25
    n = 8
    hc = 2.15                                         # 灯笼中心高
    # 龙头
    mb = K.MB()
    mb.cyl(0, 0, 0, hc - 0.25, 0.022, "M_A5_Bamboo", seg=6)
    z = hc
    mb.box(-0.26, -0.3, z - 0.22, 0.26, 0.25, z + 0.2, "M_A5_DragonGreen")              # 头颅
    mb.prism([(-0.2, z - 0.12), (0.2, z - 0.12), (0.16, z + 0.1), (-0.16, z + 0.1)], "y", -0.75, -0.3, "M_A5_DragonGreen")   # 上吻
    mb.box(-0.17, -0.7, z - 0.32, 0.17, -0.3, z - 0.2, "M_A5_LanternRed")                # 下颚（张嘴）
    mb.box(-0.15, -0.76, z - 0.2, 0.15, -0.72, z - 0.12, "M_A5_EyeWhite")                # 牙
    for sx in (-1, 1):
        mb.box(sx * 0.26 - 0.03, -0.32, z + 0.02, sx * 0.26 + 0.03, -0.18, z + 0.14, "M_A5_EyeWhite")    # 眼
        mb.box(sx * 0.29 - 0.01, -0.29, z + 0.05, sx * 0.29 + 0.01, -0.21, z + 0.11, "M_A5_Eye")
        beam(mb, (sx * 0.15, -0.05, z + 0.2), (sx * 0.35, 0.35, z + 0.65), 0.05, "M_A5_DragonGold")     # 角
        beam(mb, (sx * 0.12, -0.72, z - 0.02), (sx * 0.6, -0.95, z - 0.35), 0.02, "M_A5_DragonGold")   # 须
        with mb.at(sx * 0.27, 0, 0):                                                     # 鬃（腮边）
            mb.box(-0.02, -0.1, z - 0.3, 0.02, 0.32, z + 0.18, "M_A5_DragonScale")
    mb.ico(0, -0.74, z + 0.05, 0.06, "M_A5_LanternRed", subdiv=1)                         # 鼻珠
    obj(mb, "Head", (0, 0, 0), uv=0.5)
    fx("FX_Head_Light", (0, -0.2, hc))
    # 身节
    for i in range(n):
        y = sp * (i + 1)
        zc = hc + 0.22 * math.sin(i * 0.9)
        mb = K.MB()
        mb.cyl(0, 0, 0, zc - 0.3, 0.02, "M_A5_Bamboo", seg=6)
        with mb.at(0, 0, zc, rx=90):
            mb.cyl(0, 0, -0.32, 0.32, 0.3, "M_A5_DragonScale" if i % 2 else "M_A5_DragonGreen", seg=8)
            for zz in (-0.34, 0.3):
                mb.cyl(0, 0, zz, zz + 0.04, 0.32, "M_A5_DragonGold", seg=8)
            mb.cyl(0, 0, -0.06, 0.06, 0.31, "M_A5_LanternRed", seg=8)
        mb.box(-0.025, -0.3, zc + 0.27, 0.025, 0.3, zc + 0.38, "M_A5_DragonScale")      # 背鳍
        for k in range(3):
            yy = -0.22 + 0.22 * k
            mb.prism([(yy - 0.07, zc + 0.36), (yy + 0.07, zc + 0.36), (yy, zc + 0.52)], "x", -0.02, 0.02, "M_A5_DragonGold")
        obj(mb, f"Seg_{i + 1:02d}", (0, y, 0), uv=0.5)
        fm = K.MB()                                                                     # 灯面（两侧）
        for sx in (-1, 1):
            xx = sx * 0.3 * math.cos(math.pi / 8)
            fm.box(xx - 0.006 if sx > 0 else xx - 0.004, -0.2, zc - 0.17, xx + 0.004 if sx > 0 else xx + 0.006, 0.2, zc + 0.17, "M_A5_LanternFace")
        ob = obj(fm, f"Seg_{i + 1:02d}_Face", (0, y, 0), uv=0.5)
        uv01(ob, 1, 2, flip_axis=(0, -1))
        fx(f"FX_Seg_{i + 1:02d}_Light", (0, y, zc))
    # 龙尾
    y = sp * (n + 1)
    zc = hc + 0.22 * math.sin(n * 0.9)
    mb = K.MB()
    mb.cyl(0, 0, 0, zc - 0.2, 0.02, "M_A5_Bamboo", seg=6)
    loft_y(mb, [(-0.2, 0, zc, 0.24, 0.24), (0.3, 0, zc + 0.05, 0.16, 0.16), (0.8, 0, zc + 0.2, 0.04, 0.04)], "M_A5_DragonScale", seg=8)
    mb.prism([(0.7, zc + 0.1), (1.2, zc - 0.3), (1.3, zc + 0.6)], "x", -0.02, 0.02, "M_A5_DragonGold")
    obj(mb, "Tail", (0, y, 0), uv=0.5)
    # 龙珠（领舞的人举）
    mb = K.MB()
    mb.cyl(0, 0, 0, 2.0, 0.018, "M_A5_Bamboo", seg=6)
    mb.ico(0, 0, 2.2, 0.2, "M_A5_LanternRed", subdiv=1)
    obj(mb, "Pearl", (0, -2.0, 0), uv=0.5)
    fx("FX_Pearl_Light", (0, -2.0, 2.2))
    for i in range(n + 2):
        anchor(f"ANCHOR_Carrier_{i:02d}", (0.35, sp * i, 0))


def build_drum_gong():
    """锣鼓一套：Drum 大鼓（鼓面朝上，铜钉一圈）放在 DrumFrame 抬鼓架上（两根 2.4 m 抬杠 + 四腿），Drumstick_L/R 鼓槌，
    Gong 大锣（枢轴在吊绳顶，可摆动）+ Gong_Handle 锣架提手 + Gong_Mallet 锣槌，Cymbal_L/R 一对钹。"""
    mb = K.MB()
    for sx in (-1, 1):
        mb.box(sx * 0.42 - 0.03, -1.2, 0.62, sx * 0.42 + 0.03, 1.2, 0.68, "M_A5_WoodDark")   # 抬杠
        for sy in (-1, 1):
            mb.box(sx * 0.42 - 0.03, sy * 0.4 - 0.03, 0, sx * 0.42 + 0.03, sy * 0.4 + 0.03, 0.62, "M_A5_WoodDark")
    for sy in (-1, 1):
        mb.box(-0.45, sy * 0.4 - 0.03, 0.56, 0.45, sy * 0.4 + 0.03, 0.62, "M_A5_WoodDark")
        mb.box(-0.45, sy * 0.4 - 0.025, 0.15, 0.45, sy * 0.4 + 0.025, 0.2, "M_A5_WoodDark")
    obj(mb, "DrumFrame", (0, 0, 0))
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.08, 0.36, "M_A5_DrumRed", seg=14, r_top=0.4)
    mb.cyl(0, 0, 0.08, 0.32, 0.4, "M_A5_DrumRed", seg=14, r_top=0.36)
    mb.cyl(0, 0, 0.32, 0.33, 0.35, "M_A5_DrumSkin", seg=14)
    mb.cyl(0, 0, -0.01, 0.0, 0.35, "M_A5_DrumSkin", seg=14)
    for k in range(14):
        a = 2 * math.pi * (k + 0.5) / 14
        mb.box(0.365 * math.cos(a) - 0.012, 0.365 * math.sin(a) - 0.012, 0.29, 0.365 * math.cos(a) + 0.012, 0.365 * math.sin(a) + 0.012, 0.31, "M_A5_Nail")
    for sx in (-1, 1):
        mb.box(sx * 0.4 - 0.02, -0.03, 0.12, sx * 0.4 + 0.02, 0.03, 0.2, "M_A5_Brass")
    obj(mb, "Drum", (0, 0, 0.62))
    for name, x in (("Drumstick_L", -0.15), ("Drumstick_R", 0.15)):
        mb = K.MB()
        with mb.at(0, 0, 0, rx=90):
            mb.cyl(0, 0, -0.18, 0.18, 0.014, "M_A5_WoodDark", seg=6, r_top=0.011)
        mb.ico(0, -0.19, 0, 0.022, "M_A5_ClothRed", subdiv=1)
        obj(mb, name, (x, -0.6, 0.97))
    mb = K.MB()                                                                       # 锣：吊在提手下
    with mb.at(0, 0, -0.35, rx=90):
        mb.cyl(0, 0, -0.02, 0.02, 0.26, "M_A5_Gong", seg=16)
        mb.cyl(0, 0, -0.035, -0.02, 0.07, "M_A5_Gong", seg=10)
    mb.box(-0.004, -0.004, -0.1, 0.004, 0.004, 0.0, "M_A5_Rope")
    obj(mb, "Gong", (1.3, 0, 0.82))
    mb = K.MB()
    mb.box(-0.02, -0.02, 0, 0.02, 0.02, 0.5, "M_A5_WoodDark")
    mb.box(-0.02, -0.02, 0.5, 0.2, 0.02, 0.54, "M_A5_WoodDark")
    obj(mb, "Gong_Handle", (1.1, 0, 0.32))
    mb = K.MB()
    mb.box(-0.01, -0.15, -0.01, 0.01, 0.15, 0.01, "M_A5_WoodDark")
    mb.ico(0, -0.17, 0, 0.03, "M_A5_ClothRed", subdiv=1)
    obj(mb, "Gong_Mallet", (1.3, -0.5, 0.03))
    for name, x in (("Cymbal_L", -1.1), ("Cymbal_R", -1.45)):
        mb = K.MB()
        mb.cyl(0, 0, 0, 0.012, 0.15, "M_A5_Gong", seg=14, r_top=0.12)
        mb.cyl(0, 0, 0.012, 0.045, 0.055, "M_A5_Gong", seg=10, r_top=0.035)
        mb.box(-0.025, -0.006, 0.045, 0.025, 0.006, 0.05, "M_A5_ClothRed")
        obj(mb, name, (x, 0, 0))


# ================================================================= 第五幕 · 巡游场景
def lantern_round(mb, x, y, zt, r=0.18, drop=0.25):
    """圆灯笼：吊绳 + 灯身（8 边桶）+ 上下黑口 + 穗子。"""
    mb.box(x - 0.008, y - 0.008, zt - drop, x + 0.008, y + 0.008, zt, "M_A5_Rope")
    z1 = zt - drop
    mb.cyl(x, y, z1 - 0.05, z1, r * 0.55, "M_A5_WoodDark", seg=8)
    mb.cyl(x, y, z1 - 0.05 - r * 1.6, z1 - 0.05, r, "M_A5_LanternRed", seg=8)
    mb.cyl(x, y, z1 - 0.1 - r * 1.6, z1 - 0.05 - r * 1.6, r * 0.55, "M_A5_WoodDark", seg=8)
    mb.box(x - 0.012, y - 0.012, z1 - 0.32 - r * 1.6, x + 0.012, y + 0.012, z1 - 0.1 - r * 1.6, "M_A5_ClothYellow")


def sag_line(mb, p0, p1, sag, n, w, mat, lanterns=0, pennants=None):
    """两点间下垂的绳（n 段方木）；lanterns>0 时沿绳挂灯笼，pennants=[颜色…] 时挂三角小旗。"""
    p0, p1 = Vector(p0), Vector(p1)
    pts = []
    for i in range(n + 1):
        t = i / n
        p = p0.lerp(p1, t)
        p.z -= sag * 4 * t * (1 - t)
        pts.append(p)
    for a, b in zip(pts, pts[1:]):
        beam(mb, a, b, w, mat)
    if lanterns:
        for k in range(lanterns):
            t = (k + 1) / (lanterns + 1)
            p = p0.lerp(p1, t)
            p.z -= sag * 4 * t * (1 - t)
            lantern_round(mb, p.x, p.y, p.z, r=0.16, drop=0.12)
    if pennants:
        d = (p1 - p0)
        m = 2 * n
        for k in range(m):
            t = (k + 0.5) / m
            p = p0.lerp(p1, t)
            p.z -= sag * 4 * t * (1 - t)
            ang = math.degrees(math.atan2(d.y, d.x))
            with mb.at(p.x, p.y, p.z, rz=ang):
                mb.prism([(-0.12, 0.0), (0.12, 0.0), (0.0, -0.32)], "y", -0.003, 0.003, pennants[k % len(pennants)])


def build_temple_front():
    """汤和庙前广场的巡游布置（庙本身是地图建筑 BLD_ROC_Temple，不在这里）：广场约 24 × 16 m，原点在广场中心，庙在 +Y 一侧。
    Caimen 彩门（-Y 入口，6.4 m 宽三间扎彩牌楼）+ Caimen_Board 门额（0..1 UV 换字）、Xiangting 香亭（抬杠 + 小四坡顶）、
    FlagBases 八对夹杆石（ANCHOR_Flag_01..08 插 PROP_ParadeFlag）、Benches 观礼长凳 6 条、Lantern_Lines 灯笼串、
    OfferingTable_Spot 路祭位（ANCHOR_Offering 放 PROP_Offering）。"""
    S, C = K.MB(), K.MB()
    # ---- 彩门：两根主柱 + 两根边柱，三层横楣，顶上扎彩小屋顶，挂灯笼与彩球
    y0 = -6.5
    for x, h in ((-3.2, 5.6), (3.2, 5.6), (-5.0, 4.2), (5.0, 4.2)):
        S.box(x - 0.35, y0 - 0.35, 0, x + 0.35, y0 + 0.35, 0.45, "M_A5_StoneBase")         # 夹杆石座
        S.cyl(x, y0, 0, h, 0.13, "M_A5_Lacquer", seg=8)
        for k in range(int(h / 0.6)):                                                      # 缠红绿彩布
            z = 0.6 + k * 0.6
            S.cyl(x, y0, z, z + 0.18, 0.145, "M_A5_ClothGreen" if k % 2 else "M_A5_ClothRed", seg=8)
        C.box(x - 0.35, y0 - 0.35, 0, x + 0.35, y0 + 0.35, h, "M_Plaster")
    for z0_, z1_, x0_, x1_, mat in ((4.4, 4.65, -3.4, 3.4, "M_A5_Lacquer"), (5.35, 5.6, -3.4, 3.4, "M_A5_Lacquer"),
                                    (3.4, 3.6, -5.2, -3.2, "M_A5_Lacquer"), (3.4, 3.6, 3.2, 5.2, "M_A5_Lacquer")):
        S.box(x0_, y0 - 0.16, z0_, x1_, y0 + 0.16, z1_, mat)
    S.box(-5.2, y0 - 0.18, 4.0, -3.2, y0 + 0.18, 4.2, "M_A5_ClothYellow")
    S.box(3.2, y0 - 0.18, 4.0, 5.2, y0 + 0.18, 4.2, "M_A5_ClothYellow")
    S.gable_roof(-3.7, 3.7, y0 - 0.7, y0 + 0.7, 5.6, 0.9, ohf=0.35, ohs=0.25, mat="M_A5_ClothRed", ridge_mat="M_A5_ClothYellow")
    for sx in (-1, 1):
        S.gable_roof(sx * 4.1 - 1.0, sx * 4.1 + 1.0, y0 - 0.55, y0 + 0.55, 4.2, 0.6, ohf=0.25, ohs=0.15, mat="M_A5_ClothRed",
                     ridge_mat="M_A5_ClothYellow")
    S.ico(0, y0, 7.05, 0.28, "M_A5_ClothRed", subdiv=1)                                    # 顶上彩球
    for x in (-2.0, 2.0):                                                                  # 门洞上的彩球 + 垂绸
        S.ico(x, y0 - 0.2, 4.2, 0.22, "M_A5_ClothRed", subdiv=1)
        S.box(x - 0.08, y0 - 0.22, 3.2, x + 0.08, y0 - 0.18, 4.1, "M_A5_ClothRed")
    for x in (-3.2, 3.2, -5.0, 5.0):
        lantern_round(S, x, y0 - 0.45, 3.9 if abs(x) < 4 else 3.3, r=0.2, drop=0.15)
        S.box(x - 0.02, y0 - 0.45, 3.9 if abs(x) < 4 else 3.3, x + 0.02, y0 - 0.12, (3.9 if abs(x) < 4 else 3.3) + 0.03, "M_A5_WoodDark")
    mb = K.MB()                                                                            # 门额（换字）
    mb.box(-1.4, -0.06, -0.35, 1.4, 0.0, 0.35, "M_A5_BoardGold")
    mb.box(-1.3, -0.075, -0.27, 1.3, -0.06, 0.27, "M_A5_Board")
    ob = obj(mb, "Caimen_Board", (0, y0 - 0.17, 4.98))
    uv01(ob, 0, 2)
    # ---- 香亭：抬阁（四根抬杠）+ 方台 + 四柱 + 小四坡顶 + 宝顶，台上一只香炉
    xt, yt = 0.0, 1.5
    X = K.MB()
    for sx in (-1, 1):
        X.box(xt + sx * 0.55 - 0.04, yt - 1.6, 0.62, xt + sx * 0.55 + 0.04, yt + 1.6, 0.7, "M_A5_WoodDark")
    for sx in (-1, 1):
        for sy in (-1, 1):
            X.box(xt + sx * 0.55 - 0.05, yt + sy * 0.55 - 0.05, 0, xt + sx * 0.55 + 0.05, yt + sy * 0.55 + 0.05, 0.62, "M_A5_WoodDark")
    X.box(xt - 0.7, yt - 0.7, 0.7, xt + 0.7, yt + 0.7, 0.82, "M_A5_Lacquer")
    X.box(xt - 0.72, yt - 0.72, 0.5, xt + 0.72, yt - 0.7, 0.82, "M_A5_ClothYellow")
    for sx in (-1, 1):
        for sy in (-1, 1):
            X.cyl(xt + sx * 0.58, yt + sy * 0.58, 0.82, 2.2, 0.045, "M_A5_Lacquer", seg=6)
    X.box(xt - 0.66, yt - 0.66, 2.1, xt + 0.66, yt + 0.66, 2.2, "M_A5_WoodDark")
    X.hip_roof(xt - 0.95, yt - 0.95, xt + 0.95, yt + 0.95, 2.2, 0.7, 0.9, mat="M_A5_Roof", ridge_mat="M_A5_ClothYellow", curl=False)
    X.ico(xt, yt, 3.05, 0.12, "M_A5_Brass", subdiv=1)
    X.cyl(xt, yt, 0.82, 1.1, 0.18, "M_A5_Bronze", seg=10, r_top=0.24)
    X.cyl(xt, yt, 1.1, 1.12, 0.2, "M_A4_AshLight", seg=10)
    for k in range(4):                                                                     # 亭檐垂下的彩绸
        a = k * math.pi / 2 + math.pi / 4
        X.box(xt + 0.85 * math.cos(a) - 0.04, yt + 0.85 * math.sin(a) - 0.04, 1.5, xt + 0.85 * math.cos(a) + 0.04,
              yt + 0.85 * math.sin(a) + 0.04, 2.2, "M_A5_ClothRed")
    C.box(xt - 0.75, yt - 1.6, 0, xt + 0.75, yt + 1.6, 2.2, "M_Plaster")
    obj(X, "Xiangting", (0, 0, 0), uv=1.0)
    fx("FX_Incense", (xt, yt, 1.2))
    # ---- 旗杆座：广场两侧各四对夹杆石
    F = K.MB()
    flags = []
    for sx in (-1, 1):
        for k, y in enumerate((-4.0, -1.0, 2.0, 5.0)):
            x = sx * 8.5
            for dy in (-0.16, 0.16):
                F.box(x - 0.22, y + dy - 0.07, 0, x + 0.22, y + dy + 0.07, 1.0, "M_A5_StoneBase")
                F.prism([(x - 0.22, 1.0), (x + 0.22, 1.0), (x, 1.15)], "y", y + dy - 0.07, y + dy + 0.07, "M_A5_StoneBase")
            F.box(x - 0.3, y - 0.3, 0, x + 0.3, y + 0.3, 0.08, "M_A5_StoneBase")
            C.box(x - 0.25, y - 0.25, 0, x + 0.25, y + 0.25, 1.1, "M_Plaster")
            flags.append((x, y))
    obj(F, "FlagBases", (0, 0, 0), uv=1.0)
    # ---- 观礼长凳：两侧各三条，面向中轴
    B = K.MB()
    for sx in (-1, 1):
        for y in (-3.5, -0.5, 3.0):
            x = sx * 6.2
            B.box(x - 0.18, y - 1.0, 0.42, x + 0.18, y + 1.0, 0.47, "M_A5_Wood")
            for dy in (-0.8, 0.8):
                B.box(x - 0.14, y + dy - 0.04, 0, x + 0.14, y + dy + 0.04, 0.42, "M_A5_WoodDark")
            C.box(x - 0.18, y - 1.0, 0, x + 0.18, y + 1.0, 0.47, "M_Plaster")
    obj(B, "Benches", (0, 0, 0), uv=1.0)
    # ---- 灯笼串：彩门两主柱顶 → 庙前两根灯杆
    Lm = K.MB()
    for sx in (-1, 1):
        Lm.cyl(sx * 3.6, 7.0, 0, 5.0, 0.07, "M_A5_WoodDark", seg=6)
        Lm.box(sx * 3.6 - 0.3, 7.0 - 0.3, 0, sx * 3.6 + 0.3, 7.0 + 0.3, 0.3, "M_A5_StoneBase")
        C.box(sx * 3.6 - 0.3, 6.7, 0, sx * 3.6 + 0.3, 7.3, 5.0, "M_Plaster")
        sag_line(Lm, (sx * 3.2, y0, 5.5), (sx * 3.6, 7.0, 4.9), 0.9, 10, 0.025, "M_A5_Rope", lanterns=6)
    sag_line(Lm, (-3.6, 7.0, 4.9), (3.6, 7.0, 4.9), 0.6, 8, 0.025, "M_A5_Rope", lanterns=4)
    sag_line(Lm, (-3.2, y0, 5.5), (3.6, 7.0, 4.9), 1.2, 12, 0.02, "M_A5_Rope",
             pennants=["M_A5_ClothRed", "M_A5_ClothYellow", "M_A5_ClothGreen", "M_A5_ClothBlue"])
    sag_line(Lm, (3.2, y0, 5.5), (-3.6, 7.0, 4.9), 1.2, 12, 0.02, "M_A5_Rope",
             pennants=["M_A5_ClothYellow", "M_A5_ClothRed", "M_A5_ClothBlue", "M_A5_ClothGreen"])
    obj(Lm, "NOCOL_Lantern_Lines", (0, 0, 0), uv=1.0)
    obj(S, "Caimen", (0, 0, 0), uv=1.0)
    obj(C, "COL_TempleFront", (0, 0, 0))
    for i, (x, y) in enumerate(flags):
        anchor(f"ANCHOR_Flag_{i + 1:02d}", (x, y, 0))
    anchor("ANCHOR_Offering", (0, -2.2, 0))
    anchor("ANCHOR_ParadeStart", (0, 6.0, 0))
    anchor("ANCHOR_ParadeExit", (0, -8.5, 0))
    anchor("ANCHOR_WangYan_Watch", (-4.6, -2.0, 0))
    anchor("ANCHOR_Elder_Watch", (4.6, -2.0, 0))
    anchor("ANCHOR_cam_top", (0, 0, 30.0))
    for i, (x, y) in enumerate(((-6.2, -3.5), (-6.2, -0.5), (-6.2, 3.0), (6.2, -3.5), (6.2, -0.5), (6.2, 3.0))):
        anchor(f"ANCHOR_Bench_{i + 1}", (x, y, 0.47))
    fx("FX_Firecracker_L", (-3.2, y0 - 0.5, 0.3))
    fx("FX_Firecracker_R", (3.2, y0 - 0.5, 0.3))


def build_street_parade():
    """巡游主街装饰的可平铺模块：一段 9 m（沿 Y，y ∈ [-4.5, 4.5]），街宽 6 m（两侧杆在 x = ±3.35，落在街沿外）。
    子物体可按段开关：Poles 两侧竹竿（每侧两根，夹杆石底）、Bunting 跨街彩带（两条三角小旗串）、Lanterns 跨街灯笼串、
    FlagBases 旗阵底座（两侧各 3 个，ANCHOR_Flag_L1..R3）、Banner_L/R 沿街竖幅（0..1 UV 换字）。首尾相接无缝。"""
    xs = 3.35
    P, C = K.MB(), K.MB()
    for sx in (-1, 1):
        for y in (-2.25, 2.25):
            P.cyl(sx * xs, y, 0, 5.2, 0.05, "M_A5_Bamboo", seg=6, r_top=0.04)
            P.box(sx * xs - 0.18, y - 0.18, 0, sx * xs + 0.18, y + 0.18, 0.35, "M_A5_StoneBase")
            P.ico(sx * xs, y, 5.25, 0.08, "M_A5_ClothRed", subdiv=1)
            C.box(sx * xs - 0.18, y - 0.18, 0, sx * xs + 0.18, y + 0.18, 5.2, "M_Plaster")
        P.box(sx * xs - 0.02, -2.25, 4.6, sx * xs + 0.02, 2.25, 4.64, "M_A5_Rope")      # 同侧两杆之间的顺街绳
    obj(P, "Poles", (0, 0, 0), uv=1.0)
    obj(C, "COL_Street_Parade", (0, 0, 0))
    Bt = K.MB()
    sag_line(Bt, (-xs, -2.25, 5.0), (xs, -2.25, 5.0), 0.5, 8, 0.02, "M_A5_Rope",
             pennants=["M_A5_ClothRed", "M_A5_ClothYellow", "M_A5_ClothGreen", "M_A5_ClothBlue", "M_A5_ClothWhite"])
    sag_line(Bt, (-xs, -2.25, 4.62), (xs, 2.25, 4.62), 0.4, 10, 0.02, "M_A5_Rope",
             pennants=["M_A5_ClothYellow", "M_A5_ClothRed", "M_A5_ClothBlue", "M_A5_ClothWhite", "M_A5_ClothGreen"])
    sag_line(Bt, (xs, -2.25, 4.62), (-xs, 2.25, 4.62), 0.4, 10, 0.02, "M_A5_Rope",
             pennants=["M_A5_ClothRed", "M_A5_ClothGreen", "M_A5_ClothYellow", "M_A5_ClothBlue", "M_A5_ClothWhite"])
    obj(Bt, "NOCOL_Bunting", (0, 0, 0), uv=1.0)
    Lt = K.MB()
    sag_line(Lt, (-xs, 2.25, 5.0), (xs, 2.25, 5.0), 0.6, 8, 0.02, "M_A5_Rope", lanterns=5)
    obj(Lt, "NOCOL_Lanterns", (0, 0, 0), uv=1.0)
    F = K.MB()
    bases = []
    for sx, side in ((-1, "L"), (1, "R")):
        for k, y in enumerate((-3.4, 0.0, 3.4)):
            x = sx * (xs - 0.3)
            F.box(x - 0.25, y - 0.25, 0, x + 0.25, y + 0.25, 0.12, "M_A5_StoneBase")
            for dy in (-0.11, 0.11):
                F.box(x - 0.15, y + dy - 0.05, 0.12, x + 0.15, y + dy + 0.05, 0.75, "M_A5_StoneBase")
            bases.append((f"ANCHOR_Flag_{side}{k + 1}", x, y))
    obj(F, "FlagBases", (0, 0, 0), uv=1.0)
    for sx, side in ((-1, "L"), (1, "R")):                                              # 沿街竖幅：挂在同侧顺街绳上
        mb = K.MB()
        mb.box(-0.02, -0.5, -0.03, 0.02, 0.5, 0.0, "M_A5_WoodDark")
        mb.box(-0.006, -0.45, -1.85, 0.006, 0.45, -0.03, "M_A5_FlagFace")
        mb.box(-0.008, -0.45, -1.85, 0.008, 0.45, -1.78, "M_A5_ClothRed")
        ob = obj(mb, f"Banner_{side}", (sx * xs, 0.0, 4.6))
        uv01(ob, 1, 2, flip_axis=(0, -1) if sx > 0 else (0, 1))
    for n, x, y in bases:
        anchor(n, (x, y, 0.12))
    anchor("ANCHOR_Path_In", (0, -4.5, 0))
    anchor("ANCHOR_Path_Out", (0, 4.5, 0))
    fx("FX_Confetti", (0, 0, 5.0))


# ================================================================= 第五幕 · 人物（rupu_char.build_character + 钩子）
A45_CHAR_PALETTE = {
    "M_A5C_WY45_Robe": "#a6a596", "M_A5C_WY45_Pants": "#34383a", "M_A5C_Armband": "#1a1918",
    "M_A5C_WB45_Robe": "#5e5245",
    "M_A5C_PC_Pants": "#3a3832", "M_A5C_PC_SashRed": "#8c3a2e", "M_A5C_PC_SashYellow": "#a88a48",
    "M_A5C_PC_A_Coat": "#c4bca8", "M_A5C_PC_B_Coat": "#46566a", "M_A5C_PC_C_Coat": "#4a4a46", "M_A5C_PC_C_Hat": "#2e2a26",
    "M_A5C_PC_D_Robe": "#5f6252", "M_A5C_PC_E_Ao": "#7a5a58", "M_A5C_PC_E_Skirt": "#2b2a2c", "M_A5C_PC_F_Coat": "#8a4e40",
    "M_A5C_Towel": "#d6d0c0", "M_A5C_Flower": "#a8402e", "M_A5C_Strap": "#4a3a2a", "M_A5C_Pad": "#7a6a52",
}
K.PALETTE.update(A45_CHAR_PALETTE)
V = Vector


def _ring_band(S, hc, r, h, mat, z0=0.3, z1=0.55, k=1.1):
    S.add(*RC.rings_mesh([(hc + V((0, 0.004 * h, r[2] * z0)), r[0] * k, r[1] * (k - 0.02)),
                          (hc + V((0, 0.004 * h, r[2] * z1)), r[0] * (k - 0.04), r[1] * (k - 0.06))], seg=10), mat, RC.W("Head"))


def _hair_headband(S, J, hc, r, hm, h, cfg):
    """短发 + 红布头巾带，脑后打结垂两条短尾。"""
    RC.hair_short(S, hc, r, hm, h)
    _ring_band(S, hc, r, h, cfg.get("band", "M_A5C_PC_SashRed"))
    S.add(*RC.box(hc + V((0, r[1] * 1.08, r[2] * 0.4)), (0.03 * h, 0.02 * h, 0.03 * h)), cfg.get("band", "M_A5C_PC_SashRed"), RC.W("Head"))
    for sx in (-1, 1):
        S.add(*RC.box(hc + V((sx * 0.012 * h, r[1] * 1.1, r[2] * 0.0)), (0.012 * h, 0.006 * h, 0.06 * h), rot=RC._eu(0, sx * 15, 0)),
              cfg.get("band", "M_A5C_PC_SashRed"), RC.W("Head"))


def _hair_towel(S, J, hc, r, hm, h, cfg):
    """短发 + 白羊肚毛巾包头，额前打结。"""
    RC.hair_short(S, hc, r, hm, h)
    _ring_band(S, hc, r, h, "M_A5C_Towel", 0.25, 0.85, 1.12)
    S.add(*RC.box(hc + V((0, -r[1] * 1.1, r[2] * 0.6)), (0.035 * h, 0.02 * h, 0.025 * h)), "M_A5C_Towel", RC.W("Head"))


def _hair_tuft(S, J, hc, r, hm, h, cfg):
    """孩童：短发 + 头顶一撮冲天小辫扎红绳。"""
    RC.hair_short(S, hc, r, hm, h)
    S.add(*RC.ellipsoid(hc + V((0, 0.0, r[2] * 1.12)), 0.018 * h, 0.018 * h, 0.03 * h, seg=6, rings=3), hm, RC.W("Head"))
    S.add(*RC.tube(hc + V((0, 0, r[2] * 1.0)), hc + V((0, 0, r[2] * 1.06)), 0.016 * h, 0.016 * h, seg=6), "M_A5C_Flower", RC.W("Head"))


def _ex_armband(S, J, h, cfg, tw, hipsW):
    """左臂黑纱（孝）。"""
    a, b = J["armL"], J["elbowL"]
    S.add(*RC.tube(a + (b - a) * 0.42, a + (b - a) * 0.62, 0.036 * h, 0.034 * h, seg=8), "M_A5C_Armband", RC.W("LeftUpperArm"))


def _ex_flag_socket(S, J, h, cfg, tw, hipsW):
    """举旗手：腰前的旗兜（皮杯）+ 斜挎背带。"""
    S.add(*RC.tube(V((0, -0.085 * h, 0.44 * h)), V((0, -0.09 * h, 0.5 * h)), 0.022 * h, 0.026 * h, seg=8), "M_A5C_Strap", hipsW)
    _ex_strap(S, J, h, cfg, tw, hipsW)


def _ex_strap(S, J, h, cfg, tw, hipsW):
    a = J["chest_t"] + V((-0.07 * h, 0, 0))
    b = V((0.1 * h, 0, 0.5 * h))
    for yy in (-0.068 * h, 0.066 * h):
        d = b - a
        mid = (a + b) / 2 + V((0, yy, 0))
        ang = math.degrees(math.atan2(d.x, d.z))
        S.add(*RC.box(mid, (0.02 * h, 0.006 * h, d.length), rot=RC._eu(0, ang, 0)), "M_A5C_Strap", tw)


def _ex_shoulder_pad(S, J, h, cfg, tw, hipsW):
    """扛灯：右肩垫布。"""
    p = J["armR"] + V((0.01 * h, 0, 0.03 * h))
    S.add(*RC.box(p, (0.07 * h, 0.08 * h, 0.018 * h)), "M_A5C_Pad", {"RightShoulder": 0.5, "Chest": 0.5})


def _ex_hair_flower(S, J, h, cfg, tw, hipsW):
    """妇人：髻边一朵红绒花（节庆）。"""
    hs = cfg.get("head", 1.0)
    hc = J["head"] + V((0, -0.004 * h, 0.064 * h * hs))
    S.add(*RC.ellipsoid(hc + V((0.03 * h, 0.06 * h * hs, 0.0)), 0.014 * h, 0.012 * h, 0.014 * h, seg=6, rings=3), "M_A5C_Flower", RC.W("Head"))


RC.HAIR_HOOKS.update({"A45_headband": _hair_headband, "A45_towel": _hair_towel, "A45_tuft": _hair_tuft})
RC.EXTRA_HOOKS.update({"A45_armband": _ex_armband, "A45_flag_socket": _ex_flag_socket, "A45_strap": _ex_strap,
                       "A45_shoulder_pad": _ex_shoulder_pad, "A45_hair_flower": _ex_hair_flower})

_CROWD_BASE = dict(H=1.70, outfit="jacket", pants="M_A5C_PC_Pants", shoe="M_CH_ClothShoe", sash="M_A5C_PC_SashRed", cuff=1.15)


def _crowd(**kw):
    c = dict(_CROWD_BASE)
    c.update(kw)
    return c


A45_CAST = {
    "CH_WangYan_1945": dict(H=1.75, outfit="robe", top="M_A5C_WY45_Robe", pants="M_A5C_WY45_Pants", shoe="M_CH_WY41_Shoe",
                            hair="short", extras=["camera_bag", "A45_armband"], cuff=1.18, brow_tilt=5,
                            desc="王砚 1945：29 岁，同脸同身高；夏天浅灰白长衫、深裤，袖口挽起（修谱），左臂黑纱（给父亲戴孝），仍斜挎相机包"),
    "NPC_WangBingzhi_1945": dict(H=1.67, outfit="robe", top="M_A5C_WB45_Robe", pants="M_A5C_WB45_Robe", shoe="M_CH_WB_Shoe",
                                 skin="M_CH_Skin_Old", hair="melon_cap", brow="M_CH_Hair_White", beard="long_white", hunch=1.45,
                                 bulk=0.88, extras=["magua"],
                                 desc="王秉之 1945：近 70，比 1941 更瘦更驼（矮 3 cm），褪色灰褐长袍外罩黑马褂、瓜皮帽、白长须（拐杖用 PROP_Cane_Bingzhi）"),
    "NPC_ParadeCrowd_A": _crowd(H=1.74, top="M_A5C_PC_A_Coat", hair="A45_headband", band="M_A5C_PC_SashRed", wrap="M_CH_Wrap",
                                extras=["A45_flag_socket"], desc="巡游·举旗手：本白短褂、红头巾带、红腰带、绑腿，腰前旗兜 + 背带"),
    "NPC_ParadeCrowd_B": _crowd(H=1.72, top="M_A5C_PC_B_Coat", hair="A45_towel", sash="M_A5C_PC_SashYellow", wrap="M_CH_Wrap",
                                bulk=1.04, extras=["A45_shoulder_pad"], desc="巡游·扛灯/舞龙手：靛蓝短褂、白毛巾包头、黄腰带、右肩垫布"),
    "NPC_ParadeCrowd_C": _crowd(H=1.68, top="M_A5C_PC_C_Coat", hair="brim_hat", hair_mat="M_A5C_PC_C_Hat", brow_tilt=-4,
                                extras=["A45_strap"], desc="巡游·锣鼓手：深灰短褂、旧毡帽、红腰带、斜挎锣带"),
    "NPC_ParadeCrowd_D": _crowd(H=1.62, outfit="robe", top="M_A5C_PC_D_Robe", pants="M_A5C_PC_D_Robe", sash=None,
                                skin="M_CH_Skin_Old", hair="short", hair_mat="M_CH_Hair_Grey", brow="M_CH_Hair_Grey",
                                beard="short_grey", hunch=0.6, bulk=0.92, brow_tilt=-10,
                                desc="巡游·老人：灰绿长衫、灰短发短须、微驼，眉眼和善（观礼/路祭）"),
    "NPC_ParadeCrowd_E": _crowd(H=1.57, outfit="robe", top="M_A5C_PC_E_Ao", skirt="M_A5C_PC_E_Skirt", pants="M_A5C_PC_E_Skirt",
                                sash=None, hair="back_bun", hem=0.03, bulk=0.9, trim="M_A5C_PC_E_Skirt", brow_tilt=-8,
                                extras=["ao_hem", "A45_hair_flower"], desc="巡游·妇人：豆沙红袄黑裙、脑后低髻簪红绒花"),
    "NPC_ParadeCrowd_F": _crowd(H=1.2, head=1.3, top="M_A5C_PC_F_Coat", sash=None, hair="A45_tuft", bulk=0.95,
                                desc="巡游·孩童：8 岁，节庆红褂、头顶冲天小辫扎红绳、大头比例"),
}


# ================================================================= 第五幕 · 动作（CH_WangYan_1941 骨架，Humanoid 共用）
def _walk_keys(period, over, steps=8):
    """在走路循环上覆盖上半身：over(t) -> {骨骼或 L/R/LF/RF: 值}。"""
    keys = []
    for i in range(steps + 1):
        f = round(i * period / steps)
        t = (f / period) % 1.0
        P, up = RC.pose_at(t, "walk")
        P = dict(P)
        for k, v in over(t).items():
            if k in ("L", "R"):
                sg = 1 if k == "L" else -1
                P[("Left" if k == "L" else "Right") + "UpperArm"] = RC._arm(sg, *v)
            elif k in ("LF", "RF"):
                sg = 1 if k == "LF" else -1
                P[("Left" if k == "LF" else "Right") + "LowerArm"] = RC._fore(sg, v)
            else:
                P[k] = v
        keys.append((f, P, up))
    return period, keys


def _g_flag_walk():
    """抬旗行走：右手在胸前、左手在腹前一上一下握竖直旗杆，身子微后仰。"""
    X = lambda a: RC._rot("X", a)
    return _walk_keys(24, lambda t: dict(R=(34, -26), RF=78, L=(20, -20), LF=62, Chest=X(-4), Spine=X(-2)))


def _g_lantern_walk():
    """舞龙灯：双手把提杆举过头，杆头随步子左右画弧（每节错相位即成龙）。"""
    X, Z = (lambda a: RC._rot("X", a)), (lambda a: RC._rot("Z", a))

    def over(t):
        s = math.sin(2 * math.pi * t)
        return dict(R=(135 + 15 * s, 8 + 10 * s), RF=30, L=(110 + 12 * s, -4 - 8 * s), LF=55,
                    Spine=X(-3) @ Z(7 * s), Chest=Z(5 * s), Head=X(-12))
    return _walk_keys(32, over, steps=8)


def _g_gong():
    """敲锣：左手提锣在胸前，右手锣槌后引 → 敲 ×2。"""
    X = lambda a: RC._rot("X", a)
    hold = dict(L=(62, 10), LF=42)
    up = RC._pose(R=(62, 40), RF=115, Spine=X(-2), **hold)
    hit = RC._pose(R=(78, 12), RF=48, Spine=X(4), Head=X(4), **hold)
    return 24, [(0, up, 0), (5, hit, 0), (12, up, 0), (17, hit, 0), (24, up, 0)]


def _g_drum():
    """擂鼓：双槌交替往下砸（鼓面在腰高）。"""
    X = lambda a: RC._rot("X", a)
    a = RC._pose(R=(80, 10), RF=100, L=(45, 5), LF=40, Spine=X(10))
    b = RC._pose(R=(45, 5), RF=40, L=(80, 10), LF=100, Spine=X(10))
    return 20, [(0, a, 0), (5, RC._pose(R=(50, 8), RF=45, L=(60, 8), LF=70, Spine=X(12)), 0), (10, b, 0),
                (15, RC._pose(R=(60, 8), RF=70, L=(50, 8), LF=45, Spine=X(12)), 0), (20, a, 0)]


def _g_write():
    """修谱写字（站在案前）：俯身、左手按纸，右手执笔小幅竖行移动、偶尔回砚舔墨。"""
    X, Z = (lambda a: RC._rot("X", a)), (lambda a: RC._rot("Z", a))
    base = dict(Spine=X(18), Chest=X(8), Head=X(24), L=(42, -18), LF=72)
    keys = []
    for i, (fwd, side, bend) in enumerate(((52, -8, 78), (50, -6, 70), (48, -6, 64), (50, -8, 72), (54, -2, 84), (62, 10, 90), (52, -8, 78))):
        keys.append((i * 8, RC._pose(R=(fwd, side), RF=bend, Neck=Z(-3 if i == 5 else 0), **base), 0))
    return 48, keys


def _g_stamp():
    """盖印：右手取印 → 举起呵气 → 双手按下（停住）→ 抬起回站姿。"""
    X = lambda a: RC._rot("X", a)
    return 48, [(0, RC._base(), 0),
                (8, RC._pose(R=(48, -6), RF=55, Spine=X(10), Head=X(14)), 0),
                (16, RC._pose(R=(70, -18), RF=115, Head=X(4)), 0),
                (24, RC._pose(R=(46, -14), RF=58, L=(44, -22), LF=62, Spine=X(22), Chest=X(8), Head=X(22)), 0),
                (34, RC._pose(R=(45, -14), RF=56, L=(44, -22), LF=62, Spine=X(24), Chest=X(8), Head=X(24)), 0),
                (42, RC._pose(R=(55, -10), RF=80, Spine=X(8), Head=X(10)), 0),
                (48, RC._base(), 0)]


A45_GESTURES = {"A45_FlagWalkLoop": _g_flag_walk, "A45_LanternWalkLoop": _g_lantern_walk, "A45_GongLoop": _g_gong,
                "A45_DrumLoop": _g_drum, "A45_WriteLoop": _g_write, "A45_Stamp": _g_stamp}
RC.GESTURE_HOOKS.update(A45_GESTURES)


# ================================================================= 注册
def recipes():
    R = {
        "ENV_Hide_Wall": ("Environments", build_hide_wall),
        "ENV_Hide_Well": ("Environments", build_hide_well),
        "ENV_Hide_Plaque": ("Environments", build_hide_plaque),
        "ENV_Shrine_Ruin_1941": ("Environments", build_shrine_ruin),
        "PROP_ScatteredPages": ("Props", build_scattered_pages),
        "PROP_SearchDebris": ("Props", build_search_debris),
        "PROP_JapaneseSearchKit": ("Props", build_search_kit),
        "ENV_RepairTable": ("Environments", build_repair_table),
        "PROP_BrushInk": ("Props", build_brush_ink),
        "PROP_Seal": ("Props", build_seal),
        "PROP_Genealogy_Final": ("Props", build_genealogy_final),
        "PROP_Offering": ("Props", build_offering),
        "PROP_DragonLantern": ("Props", build_dragon_lantern),
        "PROP_DrumGong": ("Props", build_drum_gong),
        "ENV_TempleFront": ("Environments", build_temple_front),
        "ENV_Street_Parade": ("Environments", build_street_parade),
    }
    for k in ("A", "B", "C"):
        R[f"PROP_ParadeFlag_{k}"] = ("Props", (lambda kk=k: build_parade_flag(kk)))
    for n in A45_CAST:
        R[n] = ("Characters", (lambda nm=n: RC.build_character(nm, A45_CAST[nm])))
    for g in A45_GESTURES:
        R[f"CH_WangYan_1941@{g}"] = ("Characters", (lambda gg=g: RC.build_gesture(gg)))
    return R
