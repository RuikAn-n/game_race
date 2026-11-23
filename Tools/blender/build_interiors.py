"""
《入谱》室内场景白模：王氏祖祠（祠堂）内部 + 环海楼内部
=====================================================

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      -P Tools/blender/build_interiors.py -- [--only A,B] [--force] [--no-export] [--preview DIR]

  或：Tools/mac/build_interiors.sh [同上参数]

产出（ArtSource/Buildings/*.blend + Project_rupu/Assets/Art/Buildings/<名>/<名>.fbx）：
  BLD_INT_AncestralHall   祠堂内景，占地与 BLD_ROC_AncestralHall 一致（20 x 36）
  BLD_INT_HuanhaiLou      环海楼内景，占地与 BLD_ROC_HuanhaiLou 一致（20 x 8.8，两层 + 城门洞）

约定（与 Docs/asset_spec.md 一致，另加室内约定见 Docs/interiors.md）：
  - 1 unit = 1 m；正面朝 Blender -Y；原点在地面中心。
  - 同一套几何给 1560 / 1941 两个年代，只换材质、贴花、道具（积灰、烧痕、断角）。
  - 屋顶按「可整体隐藏」拆开：ROOF_*。俯视（军议 / 指挥 / 整备）时团结里隐藏 ROOF_*；
    环海楼再按层拆：INT_Floor2 / INT_Upper* 隐藏后可以俯视底层。
  - COL_* 只做碰撞；ANCHOR_* 是空物体，标出互动点 / NPC 站位 / 镜头位。
  - 可交互物件单独成物体：供桌、牌位、沙盘台座、议事桌、族约碑、井、旗杆……
"""
import math
import os
import sys
import traceback

import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rupu_kit as K          # noqa: E402
import rupu_pipeline as RP    # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))

# 室内新增语义材质（同步写进 Data/map/era_materials.json）
K.PALETTE.update({
    "M_Floor_Brick": "#7d7566",   # 青砖地
    "M_Floor_Wood": "#6b5039",    # 木楼板
    "M_Bronze": "#8a6a3a",        # 铜：香炉、钟、匾边
    "M_Cloth_Red": "#8c3a2e",     # 红布：蒲团、灯笼、旗缨
    "M_Ceiling": "#4a3a2c",       # 梁架 / 天花
})

RECIPES = {}


def recipe(category, name):
    def deco(fn):
        RECIPES[name] = (category, fn)
        return fn
    return deco


# ============================================================ 通用小工具
def _emit(mbs, axis, c, a0, a1, t, za, zb, mat):
    for mb in mbs:
        if axis == "x":
            mb.box(a0, c - t / 2, za, a1, c + t / 2, zb, mat)
        else:
            mb.box(c - t / 2, a0, za, c + t / 2, a1, zb, mat)


def wall_run(mbs, axis, c, a0, a1, t, z0, z1, mat, opens=(), trim="M_Wood_Dark"):
    """带洞口的墙。axis='x'：墙沿 X、位于 y=c；axis='y'：沿 Y、位于 x=c。
    opens: (中心, 宽, 顶, 底, 种类) 种类 door / win / slit。mbs[0] 是渲染网格，其余是碰撞网格。"""
    cur = a0
    for cen, w, top, sill, kind in sorted(opens, key=lambda o: o[0]):
        s, e = cen - w / 2, cen + w / 2
        if s > cur:
            _emit(mbs, axis, c, cur, s, t, z0, z1, mat)
        if sill > z0:
            _emit(mbs, axis, c, s, e, t, z0, sill, mat)
        if top < z1:
            _emit(mbs, axis, c, s, e, t, top, z1, mat)
        cur = e
        sh = mbs[0]
        tt = t + 0.1
        if trim:
            if kind != "slit":
                _emit([sh], axis, c, s - 0.1, s, tt, sill, top, trim)
                _emit([sh], axis, c, e, e + 0.1, tt, sill, top, trim)
                _emit([sh], axis, c, s - 0.1, e + 0.1, tt, top, top + 0.14, trim)
            if kind == "win":
                _emit([sh], axis, c, s - 0.1, e + 0.1, tt, sill - 0.1, sill + 0.04, trim)
                n = max(2, int(w / 0.28))
                for i in range(1, n):
                    a = s + w * i / n
                    _emit([sh], axis, c, a - 0.025, a + 0.025, 0.08, sill, top, trim)
                _emit([sh], axis, c, s, e, 0.08, (sill + top) / 2 - 0.025, (sill + top) / 2 + 0.025, trim)
    if cur < a1:
        _emit(mbs, axis, c, cur, a1, t, z0, z1, mat)


def arch_top(mb, ax0, ax1, spring, ztop, y0, y1, mat, seg=8):
    """门洞上方的拱形楣（洞口自 spring 以上呈椭圆拱）。"""
    cx, hw = (ax0 + ax1) / 2, (ax1 - ax0) / 2
    r = min(hw, ztop - 0.1 - spring)
    for i in range(seg):
        a0 = math.pi - math.pi * i / seg
        a1 = math.pi - math.pi * (i + 1) / seg
        p0 = (cx + hw * math.cos(a0), spring + r * math.sin(a0))
        p1 = (cx + hw * math.cos(a1), spring + r * math.sin(a1))
        mb.prism([p0, p1, (p1[0], ztop), (p0[0], ztop)], "y", y0, y1, mat)


def table(mb, x0, y0, x1, y1, z0, h, mat="M_Wood", top_t=0.07, leg=0.08):
    mb.box(x0, y0, z0 + h - top_t, x1, y1, z0 + h, mat)
    for x in (x0 + 0.1, x1 - 0.1 - leg):
        for y in (y0 + 0.1, y1 - 0.1 - leg):
            mb.box(x, y, z0, x + leg, y + leg, z0 + h - top_t, "M_Wood_Dark")
    mb.box(x0 + 0.1, y0 + 0.1, z0 + h - top_t - 0.1, x1 - 0.1, y1 - 0.1, z0 + h - top_t, "M_Wood_Dark")


def stool(mb, cx, cy, z0, w=0.4, h=0.45):
    mb.box(cx - w / 2, cy - w / 2, z0 + h - 0.05, cx + w / 2, cy + w / 2, z0 + h, "M_Wood")
    for dx in (-1, 1):
        for dy in (-1, 1):
            mb.box(cx + dx * w * 0.38 - 0.03, cy + dy * w * 0.38 - 0.03, z0, cx + dx * w * 0.38 + 0.03, cy + dy * w * 0.38 + 0.03, z0 + h - 0.05, "M_Wood_Dark")


def lantern(mb, x, y, zt, drop=0.5, w=0.32):
    mb.box(x - 0.015, y - 0.015, zt - drop, x + 0.015, y + 0.015, zt, "M_Wood_Dark")
    mb.box(x - w / 2, y - w / 2, zt - drop - 0.42, x + w / 2, y + w / 2, zt - drop, "M_Cloth_Red")
    mb.box(x - w / 2 - 0.03, y - w / 2 - 0.03, zt - drop - 0.05, x + w / 2 + 0.03, y + w / 2 + 0.03, zt - drop, "M_Wood_Dark")
    mb.box(x - w / 2 - 0.03, y - w / 2 - 0.03, zt - drop - 0.47, x + w / 2 + 0.03, y + w / 2 + 0.03, zt - drop - 0.42, "M_Wood_Dark")


def jar(mb, x, y, z0, r, h, mat="M_Brick_Grey", seg=10):
    mb.cyl(x, y, z0, z0 + h * 0.75, r, mat, seg=seg, r_top=r * 1.08)
    mb.cyl(x, y, z0 + h * 0.75, z0 + h, r * 1.08, mat, seg=seg, r_top=r * 0.8)


def anchor(name, x, y, z=0.0, size=0.3):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = "ARROWS"
    o.empty_display_size = size
    o.location = (x, y, z)
    bpy.context.scene.collection.objects.link(o)
    return o


def emit_objects(parts):
    """parts: [(物体名, MB)]，空的跳过。"""
    for name, mb in parts:
        if mb.f:
            mb.to_object(name)


# ============================================================ 祠堂
@recipe("Buildings", "BLD_INT_AncestralHall")
def r_int_ancestral():
    """王氏祖祠内景（三进）：门厅 → 内院（廊庑、鼎炉）→ 月台 → 正厅（神龛牌位、供桌、沙盘台、议事桌、族约碑）→ 后天井（井）→ 后堂（谱库）。"""
    S, C = K.MB(), K.MB()                       # 外壳（渲染）/ 碰撞
    FUR, ALT, TAB, TABF = K.MB(), K.MB(), K.MB(), K.MB()
    SAND, ROS, STE, WELL, YARD = K.MB(), K.MB(), K.MB(), K.MB(), K.MB()
    RG, RC, RM, RR = K.MB(), K.MB(), K.MB(), K.MB()   # 屋顶：门厅 / 廊庑 / 正厅 / 后堂
    WM = [S, C]                                  # 墙同时写入渲染与碰撞
    ZH = 0.9                                     # 正厅地面
    ZB = 0.6                                     # 后堂地面

    # ---------- 地面
    S.box(-10, -18, -0.3, 10, -11, 0, "M_Floor_Brick")               # 门厅
    S.box(-10, -11, -0.3, 10, 18, 0, "M_Road_Stone")                 # 内院 / 天井
    S.box(-1.4, -11, 0, 1.4, -7.5, 0.03, "M_Stone_Base")             # 中轴御路
    S.box(-1.4, -11, 0, 1.4, -7.5, 0.03, "M_Stone_Base")
    for sx in (-1, 1):                                               # 廊庑（抬高 0.35）
        xa, xb = (7.4, 10) if sx > 0 else (-10, -7.4)
        S.box(xa, -11, 0, xb, 10, 0.35, "M_Stone_Base")
    S.box(-7.4, -2.6, 0, 7.4, 7, ZH, "M_Stone_Base")                 # 正厅台基
    S.box(-7.0, -1.2, ZH, 7.0, 6.6, ZH + 0.02, "M_Floor_Brick")      # 正厅铺地
    S.box(-6.5, -6, 0, 6.5, -2.6, ZH, "M_Stone_Base")                # 月台
    for k in range(3):                                               # 月台正面台阶（三级，踏面 0.5）
        S.box(-2.2, -7.5 + 0.5 * k, 0, 2.2, -6.0, 0.3 * (k + 1), "M_Stone_Base")
    S.box(-10, 10, 0, 10, 18, ZB, "M_Floor_Wood")                    # 后堂
    S.box(-2.0, 8.8, 0, 2.0, 10, 0.3, "M_Stone_Base")                # 后堂前两级
    S.box(-2.0, 9.4, 0, 2.0, 10, ZB, "M_Stone_Base")
    for sx in (-1, 1):                                               # 正厅侧门外的踏步（0.9 → 0.35）
        S.box(sx * 7.4 if sx > 0 else -7.9, 0.2, 0, 7.9 if sx > 0 else -7.4, 1.8, 0.62, "M_Stone_Base")
    # 碰撞：地面台基
    C.box(-10, -18, -0.3, 10, 18, 0, "M_Plaster")
    C.box(-7.4, -2.6, 0, 7.4, 7, ZH, "M_Plaster")
    C.box(-6.5, -6, 0, 6.5, -2.6, ZH, "M_Plaster")
    C.box(-10, 10, 0, 10, 18, ZB, "M_Plaster")
    for sx in (-1, 1):
        C.box(7.4 * sx if sx > 0 else -10, -11, 0, 10 if sx > 0 else -7.4, 10, 0.35, "M_Plaster")
    C.prism([(-7.5, 0), (-6.0, 0.9), (-6.0, 0)], "x", -2.2, 2.2, "M_Plaster")          # 台阶用斜坡碰撞
    C.prism([(8.8, 0), (10.0, 0.6), (10.0, 0)], "x", -2.0, 2.0, "M_Plaster")

    # ---------- 墙
    wall_run(WM, "x", -17.8, -10, 10, 0.4, 0, 4.8, "M_Plaster",           # 临街正门
             [(0, 2.8, 3.4, 0, "door"), (-4.6, 1.4, 3.5, 2.2, "win"), (4.6, 1.4, 3.5, 2.2, "win")])
    S.box(-1.7, -17.97, 0, 1.7, -17.6, 0.12, "M_Stone_Base")           # 门槛石
    wall_run(WM, "x", -11.2, -10, 10, 0.4, 0, 4.8, "M_Plaster",           # 门厅 / 内院隔墙
             [(0, 4.4, 3.8, 0, "door"), (-8.7, 1.6, 3.0, 0.35, "door"), (8.7, 1.6, 3.0, 0.35, "door")])
    for sx in (-1, 1):                                                    # 左右外墙
        c = 9.775 * sx
        wall_run(WM, "y", c, -18, -11, 0.45, 0, 4.8, "M_Plaster")
        wall_run(WM, "y", c, -11, 10, 0.45, 0, 4.2, "M_Plaster",
                 [(-7, 1.4, 3.2, 1.8, "win"), (-1, 1.4, 3.2, 1.8, "win"), (5, 1.4, 3.2, 1.8, "win")])
        wall_run(WM, "y", c, 10, 18, 0.45, 0, 5.0, "M_Plaster", [(14, 1.4, 3.8, 1.8, "win")])
    wall_run(WM, "x", 17.8, -10, 10, 0.4, 0, 5.0, "M_Plaster", [(-5, 1.6, 3.6, 1.8, "win"), (5, 1.6, 3.6, 1.8, "win")])
    wall_run(WM, "x", 10.2, -10, 10, 0.4, 0, 5.0, "M_Plaster",           # 后堂前墙
             [(0, 3.2, 3.8, ZB, "door"), (-5.5, 1.8, 3.4, 1.4, "win"), (5.5, 1.8, 3.4, 1.4, "win")])
    wall_run(WM, "x", -1.0, -7, 7, 0.4, ZH, 5.8, "M_Plaster",            # 正厅前墙：大格扇门洞敞开
             [(0, 5.0, 4.3, ZH, "door"), (-5.4, 1.6, 4.2, 2.2, "win"), (5.4, 1.6, 4.2, 2.2, "win")])
    wall_run(WM, "x", 6.4, -7, 7, 0.4, ZH, 5.8, "M_Plaster")             # 正厅后墙（神龛靠此墙）
    for sx in (-1, 1):
        wall_run(WM, "y", 6.8 * sx, -1.2, 6.6, 0.4, ZH, 5.8, "M_Plaster",
                 [(1.0, 1.6, 3.6, ZH, "door"), (4.2, 1.4, 4.2, 2.0, "win")])
    # 正厅前墙格扇（敞开的两扇，贴在门洞两侧）
    for sx in (-1, 1):
        S.box(sx * 2.5 - (0.55 if sx > 0 else 0.0), -1.3, ZH, sx * 2.5 + (0.0 if sx > 0 else 0.55), -1.15, 4.2, "M_Wood")
        for z in (1.6, 2.8, 3.8):
            S.box(sx * 2.5 - (0.55 if sx > 0 else 0.0), -1.32, z, sx * 2.5 + (0.0 if sx > 0 else 0.55), -1.14, z + 0.06, "M_Wood_Dark")

    # ---------- 柱、梁
    for sx in (-1, 1):                                                    # 廊庑檐柱
        for y in range(-10, 10, 3):
            S.box(sx * 7.4 - 0.25, y - 0.25, 0.35, sx * 7.4 + 0.25, y + 0.25, 0.5, "M_Stone_Base")
            S.cyl(sx * 7.4, y, 0.5, 3.1, 0.17, "M_Red_Lacquer", seg=8)
            C.box(sx * 7.4 - 0.17, y - 0.17, 0.35, sx * 7.4 + 0.17, y + 0.17, 3.1, "M_Wood")
        S.box(sx * 7.4 - 0.15, -11, 3.1, sx * 7.4 + 0.15, 10, 3.4, "M_Wood_Dark")
    for x in (-6.4, -3.6, -1.2, 1.2, 3.6, 6.4):                          # 正厅前廊柱（外观一致）
        S.box(x - 0.3, -2.4, ZH, x + 0.3, -1.8, ZH + 0.12, "M_Stone_Base")
        S.cyl(x, -2.1, ZH + 0.12, 5.8, 0.2, "M_Red_Lacquer", seg=8)
        C.box(x - 0.2, -2.3, ZH, x + 0.2, -1.9, 5.0, "M_Wood")
    S.box(-7.2, -2.3, 5.2, 7.2, -1.9, 5.8, "M_Wood_Dark")
    for y in (0.2, 3.8):                                                  # 正厅金柱 + 抬梁
        for x in (-6.2, -3.4, 3.4, 6.2):
            S.box(x - 0.3, y - 0.3, ZH, x + 0.3, y + 0.3, ZH + 0.12, "M_Stone_Base")
            S.cyl(x, y, ZH + 0.12, 5.0, 0.2, "M_Red_Lacquer", seg=8)
            C.box(x - 0.2, y - 0.2, ZH, x + 0.2, y + 0.2, 5.0, "M_Wood")
        S.box(-6.9, y - 0.2, 4.9, 6.9, y + 0.2, 5.4, "M_Ceiling")
    for x in (-6.2, -3.4, 0, 3.4, 6.2):
        S.box(x - 0.1, -1.0, 5.4, x + 0.1, 6.4, 5.7, "M_Ceiling")
    for y in (-0.8, 1.6, 3.0, 5.0):
        S.box(-6.9, y - 0.1, 5.7, 6.9, y + 0.1, 5.85, "M_Ceiling")
    for x in (-8, -4, 0, 4, 8):                                           # 门厅、后堂梁
        S.box(x - 0.15, -18, 4.45, x + 0.15, -11, 4.8, "M_Ceiling")
        S.box(x - 0.15, 10, 4.6, x + 0.15, 18, 5.0, "M_Ceiling")
    for y in (-14.5,):
        S.box(-10, y - 0.15, 4.45, 10, y + 0.15, 4.8, "M_Ceiling")
    for x in (-6.0, 6.0):                                                 # 门厅立柱（承重）
        S.cyl(x, -14.5, 0, 4.45, 0.2, "M_Red_Lacquer", seg=8)
        C.box(x - 0.2, -14.7, 0, x + 0.2, -14.3, 4.45, "M_Wood")

    # ---------- 屋顶（ROOF_*，俯视时隐藏）
    RG.gable_roof(-9.55, 9.55, -18, -11, 4.8, 2.4, ohf=0.8, ohs=0.0)
    RG.mating_wall(-9.55, -18, -11, 4.8, 2.4, t=0.45)
    RG.mating_wall(9.55, -18, -11, 4.8, 2.4, t=0.45, outward=-1)
    for sx in (-1, 1):
        xo, xi = (-10, -7.4) if sx < 0 else (10, 7.4)
        RC.shed_roof_y(-11, 10, xo, xi - sx * 0.6, 4.4, 3.2)
    RM.hip_roof(-8.6, -3.6, 8.6, 8.0, 5.6, 3.3, 3.2)
    RM.gable_fill(-5.4, 5.4, -1.2, 6.6, 7.4, 1.5, "M_Roof_Tile")
    RR.gable_roof(-9.55, 9.55, 10, 18, 5.0, 2.8, ohf=0.7, ohs=0.0)
    RR.mating_wall(-9.55, 10, 18, 5.0, 2.8, t=0.45)
    RR.mating_wall(9.55, 10, 18, 5.0, 2.8, t=0.45, outward=-1)

    # ============ 正厅：神龛与牌位（族老："上面供奉王沛公、王叔杲公，你父亲在下面这一排"）
    tiers = [(4.9, 6.2, ZH + 0.40, 5.0), (5.4, 6.2, ZH + 0.80, 4.6), (5.9, 6.2, ZH + 1.20, 4.2)]
    for y0, y1, zt, hx in tiers:
        S.box(-hx, y0, ZH, hx, y1, zt, "M_Wood_Dark")
        S.box(-hx - 0.05, y0 - 0.05, zt - 0.06, hx + 0.05, y0 + 0.02, zt, "M_Red_Lacquer")   # 台沿
        C.box(-hx, y0, ZH, hx, y1, zt, "M_Plaster")
    z0, z1, z2 = tiers[0][2], tiers[1][2], tiers[2][2]

    def tablet(mb, x, y, z, w=0.2, h=0.55, d=0.1, cap="M_Red_Lacquer", body="M_Wood_Dark"):
        mb.box(x - w / 2 - 0.03, y - d / 2 - 0.02, z, x + w / 2 + 0.03, y + d / 2 + 0.02, z + 0.07, "M_Wood")
        mb.box(x - w / 2, y - d / 2, z + 0.07, x + w / 2, y + d / 2, z + h, body)
        mb.box(x - w / 2 - 0.02, y - d / 2 - 0.01, z + h, x + w / 2 + 0.02, y + d / 2 + 0.01, z + h + 0.05, cap)
        mb.box(x - w * 0.28, y - d / 2 - 0.012, z + h * 0.35, x + w * 0.28, y - d / 2, z + h * 0.85, "M_Bronze")   # 金字位

    x = -4.6
    while x < 4.7:                                   # 下排（含王世清）
        if abs(x - 1.8) > 0.2:
            tablet(TAB, x, 5.55, z0)
        x += 0.45
    x = -4.2
    while x < 4.3:
        tablet(TAB, x, 5.95, z1)
        x += 0.45
    for x in (-3.2, -2.3, 2.3, 3.2):
        tablet(TAB, x, 6.0, z2, w=0.26, h=0.7)
    tablet(TAB, -0.9, 6.0, z2, w=0.34, h=0.95, d=0.12, cap="M_Bronze", body="M_Red_Lacquer")   # 王沛公
    tablet(TAB, 0.9, 6.0, z2, w=0.34, h=0.95, d=0.12, cap="M_Bronze", body="M_Red_Lacquer")    # 王叔杲公
    tablet(TABF, 1.8, 5.55, z0, body="M_Sign")                                                  # 王世清（谱上被涂黑）
    TABF.box(1.8 - 0.07, 5.55 - 0.062, z0 + 0.25, 1.8 + 0.07, 5.55 - 0.05, z0 + 0.45, "M_Sign")
    # 大匾 + 两侧帷幔
    S.box(-2.4, 6.17, 4.0, 2.4, 6.2, 4.9, "M_Bronze")
    S.box(-2.25, 6.14, 4.12, 2.25, 6.17, 4.78, "M_Plaque")
    for sx in (-1, 1):
        S.box(sx * 5.3 - 0.35 if sx > 0 else -5.65, 6.1, 2.4, sx * 5.3 + 0.35 if sx > 0 else -4.95, 6.2, 5.6, "M_Cloth_Red")
    # 柱上楹联
    for x in (-3.4, 3.4):
        S.box(x - 0.14, 3.55, 2.2, x + 0.14, 3.58, 4.6, "M_Plaque")
        S.box(x - 0.08, 3.52, 2.5, x + 0.08, 3.55, 4.3, "M_Paper")
    # 暗格：「藏进夹墙、井里、匾后」——匾后与夹墙留互动点，墙面做一块可开的板
    S.box(-6.62, 4.4, ZH + 0.6, -6.58, 5.4, ZH + 2.2, "M_Wood")

    # ============ 供桌、香案
    table(ALT, -1.3, 3.0, 1.3, 3.8, ZH, 0.95, mat="M_Red_Lacquer")
    ALT.box(-1.45, 2.95, ZH + 0.88, 1.45, 3.85, ZH + 0.97, "M_Wood_Dark")
    ALT.cyl(0, 3.4, ZH + 0.95, ZH + 1.25, 0.2, "M_Bronze", seg=10, r_top=0.26)           # 香炉
    ALT.box(-0.28, 3.12, ZH + 1.25, 0.28, 3.68, ZH + 1.27, "M_Ceiling")
    for sx in (-0.85, 0.85):                                                              # 烛台
        ALT.cyl(sx, 3.4, ZH + 0.95, ZH + 1.35, 0.05, "M_Bronze", seg=6, r_top=0.03)
        ALT.cyl(sx, 3.4, ZH + 1.35, ZH + 1.5, 0.04, "M_Paper", seg=6)
        ALT.box(sx - 0.015, 3.385, ZH + 1.5, sx + 0.015, 3.415, ZH + 1.58, "M_Fire")
    for sx in (-0.5, 0.5):                                                                # 供品
        ALT.cyl(sx, 3.55, ZH + 0.95, ZH + 1.0, 0.16, "M_Plaster", seg=8)
        ALT.ico(sx, 3.55, ZH + 1.08, 0.09, "M_Brick_Red", subdiv=1)
    ALT.box(0.9, 3.15, ZH + 0.95, 1.2, 3.6, ZH + 1.1, "M_Wood_Dark")                      # 谱匣（残谱放这里）
    ALT.box(0.9, 3.15, ZH + 1.1, 1.2, 3.6, ZH + 1.14, "M_Bronze")
    table(ALT, -0.9, 1.6, 0.9, 2.2, ZH, 0.85, mat="M_Wood")                               # 香案
    ALT.cyl(0, 1.9, ZH + 0.85, ZH + 1.0, 0.18, "M_Bronze", seg=10, r_top=0.22)
    for x in (-1.5, 0.0, 1.5):                                                            # 蒲团
        ALT.cyl(x, 0.5, ZH, ZH + 0.1, 0.32, "M_Cloth_Red", seg=10)
        ALT.cyl(x, 0.5, ZH + 0.1, ZH + 0.13, 0.27, "M_Sandbag", seg=10)

    # ============ 沙盘台座（第二幕：供桌左侧 1.2 x 0.8；沙盘本体另做，这里只出桌子和矮边）
    table(SAND, -5.4, 2.6, -4.2, 3.4, ZH, 0.85, mat="M_Wood")
    SAND.box(-5.45, 2.55, ZH + 0.85, -4.15, 2.6, ZH + 0.95, "M_Wood_Dark")
    SAND.box(-5.45, 3.4, ZH + 0.85, -4.15, 3.45, ZH + 0.95, "M_Wood_Dark")
    SAND.box(-5.45, 2.6, ZH + 0.85, -5.4, 3.4, ZH + 0.95, "M_Wood_Dark")
    SAND.box(-4.2, 2.6, ZH + 0.85, -4.15, 3.4, ZH + 0.95, "M_Wood_Dark")
    SAND.box(-5.4, 2.6, ZH + 0.85, -4.2, 3.4, ZH + 0.88, "M_Sandbag")

    # ============ 议事桌（拍田契、摊名录；右侧，沿 Y）+ 长凳
    table(ROS, 4.3, 1.7, 5.3, 4.3, ZH, 0.85, mat="M_Wood")
    for sx in (3.55, 6.05):
        ROS.box(sx - 0.2, 1.9, ZH, sx + 0.2, 4.1, ZH + 0.45, "M_Wood")
        for y in (2.0, 4.0):
            ROS.box(sx - 0.15, y - 0.04, ZH - 0.0, sx - 0.1, y + 0.04, ZH + 0.45, "M_Wood_Dark")
    ROS.box(4.45, 2.2, ZH + 0.85, 5.15, 3.4, ZH + 0.87, "M_Paper")                          # 名录纸
    for i in range(8):                                                                    # 名牌
        ROS.box(4.5 + 0.08 * (i % 4), 3.6 + 0.12 * (i // 4), ZH + 0.85, 4.5 + 0.08 * (i % 4) + 0.06, 3.6 + 0.12 * (i // 4) + 0.09, ZH + 0.9, "M_Wood")

    # ============ 族约碑（第二幕 3 条上碑）
    STE.box(6.0, 4.9, ZH, 6.5, 6.1, ZH + 0.25, "M_Stone_Base")
    STE.box(6.12, 5.0, ZH + 0.25, 6.38, 6.0, ZH + 2.1, "M_Wall_Stone")
    STE.box(6.08, 4.96, ZH + 2.1, 6.42, 6.04, ZH + 2.2, "M_Stone_Base")
    for i in range(3):
        STE.box(6.09, 5.12, ZH + 1.35 + 0.22 * i, 6.12, 5.88, ZH + 1.35 + 0.22 * i + 0.1, "M_Wood_Dark")   # 刻字槽

    # ============ 战鼓（春祭敲鼓）
    FUR.cyl(5.0, 0.4, ZH + 0.45, ZH + 1.25, 0.5, "M_Red_Lacquer", seg=10, r_top=0.42)
    FUR.cyl(5.0, 0.4, ZH + 1.25, ZH + 1.29, 0.42, "M_Sandbag", seg=10)
    for z in (ZH + 0.6, ZH + 1.1):
        FUR.cyl(5.0, 0.4, z, z + 0.06, 0.5, "M_Bronze", seg=10)
    for dx in (-0.45, 0.45):
        FUR.box(5.0 + dx - 0.05, 0.3, ZH, 5.0 + dx + 0.05, 0.5, ZH + 0.5, "M_Wood_Dark")
    FUR.box(4.7, 0.2, ZH + 1.3, 5.3, 0.25, ZH + 1.34, "M_Wood")

    # ============ 门厅：条凳（正中不放影壁：留给军官进门站位）
    for sx in (-1, 1):
        FUR.box(sx * 8.0 - 0.9, -16.8, 0, sx * 8.0 + 0.9, -16.4, 0.45, "M_Wood")

    # ============ 内院：鼎炉、太平缸、灯笼
    YARD.box(-0.9, -9.4, 0, 0.9, -8.2, 0.35, "M_Stone_Base")                               # 香鼎台
    YARD.cyl(0, -8.8, 0.35, 0.85, 0.5, "M_Bronze", seg=10, r_top=0.62)
    for a in (0, 120, 240):
        YARD.box(0.3 * math.cos(math.radians(a)) - 0.06, -8.8 + 0.3 * math.sin(math.radians(a)) - 0.06, 0.35,
                 0.3 * math.cos(math.radians(a)) + 0.06, -8.8 + 0.3 * math.sin(math.radians(a)) + 0.06, 0.55, "M_Bronze")
    for sx in (-1, 1):
        jar(YARD, sx * 5.2, -7.0, 0, 0.6, 0.95, "M_Brick_Grey", seg=10)                    # 太平缸
        YARD.cyl(sx * 5.2, -7.0, 0.96, 0.98, 0.5, "M_Water", seg=10)
    for y in (-9, -3, 3, 8):                                                               # 廊下灯笼
        for sx in (-1, 1):
            lantern(YARD, sx * 7.4, y, 3.0)
    for x in (-3.4, 3.4):
        lantern(FUR, x, -1.9, 5.7, drop=0.45)
    for x in (-1.0, 1.0):
        lantern(FUR, x, 2.0, 5.2, drop=0.35)
    C.cyl(0, -8.8, 0, 0.9, 0.55, "M_Plaster", seg=8)

    # ============ 后天井：井（藏谱处之一）
    WELL.cyl(0, 8.4, 0, 0.85, 0.85, "M_Stone_Base", seg=12, r_top=0.8)
    WELL.cyl(0, 8.4, 0.84, 0.86, 0.55, "M_Mud", seg=12)
    for sx in (-1, 1):
        WELL.box(sx * 0.7 - 0.05, 8.3, 0.85, sx * 0.7 + 0.05, 8.5, 2.2, "M_Wood_Dark")
    WELL.box(-0.8, 8.3, 2.1, 0.8, 8.5, 2.2, "M_Wood_Dark")
    WELL.cyl(0, 8.4, 1.9, 2.05, 0.08, "M_Wood", seg=6)
    C.cyl(0, 8.4, 0, 0.9, 0.85, "M_Plaster", seg=8)

    # ============ 后堂：谱库（族谱柜、长案、夹墙暗门）
    for i, x0 in enumerate((-9.0, -3.0, 3.0)):                                            # 三组谱柜靠北墙
        FUR.box(x0, 17.3, ZB, x0 + 6.0, 17.6, ZB + 2.5, "M_Wood")
        FUR.box(x0, 17.0, ZB, x0 + 6.0, 17.3, ZB + 0.12, "M_Wood_Dark")
        FUR.box(x0, 17.0, ZB + 2.4, x0 + 6.0, 17.3, ZB + 2.55, "M_Wood_Dark")
        for k in range(4):
            FUR.box(x0, 17.0, ZB + 0.12 + k * 0.57, x0 + 6.0, 17.3, ZB + 0.17 + k * 0.57, "M_Wood_Dark")
        for k in range(1, 6):
            FUR.box(x0 + k, 17.0, ZB + 0.12, x0 + k + 0.05, 17.3, ZB + 2.4, "M_Wood_Dark")
        for r in range(4):                                                               # 书函
            for c in range(6):
                if (r * 7 + c * 3 + i) % 4 != 0:
                    FUR.box(x0 + c + 0.12, 17.05, ZB + 0.2 + r * 0.57, x0 + c + 0.88, 17.28, ZB + 0.2 + r * 0.57 + 0.38, "M_Paper")
    C.box(-9.0, 17.0, ZB, 9.0, 17.6, ZB + 2.5, "M_Plaster")
    table(FUR, -1.8, 13.0, 1.8, 14.0, ZB, 0.85, mat="M_Wood")                             # 修谱长案
    for x in (-1.2, 0, 1.2):
        stool(FUR, x, 14.8, ZB)
        stool(FUR, x, 12.2, ZB)
    FUR.box(-0.5, 13.2, ZB + 0.85, 0.5, 13.8, ZB + 0.9, "M_Paper")
    C.box(-1.8, 13.0, ZB, 1.8, 14.0, ZB + 0.85, "M_Plaster")
    S.box(-9.55, 13.0, ZB, -9.5, 14.2, ZB + 2.2, "M_Plaster_Lower")                       # 夹墙暗门（藏谱处之二）

    # ---------- 碰撞：家具与柱
    C.box(-1.3, 3.0, ZH, 1.3, 3.8, ZH + 0.95, "M_Plaster")
    C.box(-0.9, 1.6, ZH, 0.9, 2.2, ZH + 0.85, "M_Plaster")
    C.box(-5.4, 2.6, ZH, -4.2, 3.4, ZH + 0.85, "M_Plaster")
    C.box(3.55, 1.7, ZH, 6.05, 4.3, ZH + 0.85, "M_Plaster")
    C.box(6.0, 4.9, ZH, 6.5, 6.1, ZH + 2.2, "M_Plaster")
    C.cyl(5.0, 0.4, ZH, ZH + 1.3, 0.5, "M_Plaster", seg=8)
    emit_objects([("INT_Shell", S), ("COL_Hall", C),
                  ("INT_Courtyard", YARD), ("INT_Furniture", FUR),
                  ("INT_Altar", ALT), ("INT_Tablets", TAB), ("INT_Tablet_WangShiqing", TABF),
                  ("INT_Sandtable_Stand", SAND), ("INT_Roster_Table", ROS), ("INT_Stele", STE), ("INT_Well", WELL),
                  ("ROOF_Gate", RG), ("ROOF_Corridor", RC), ("ROOF_Main", RM), ("ROOF_Rear", RR)])

    # ---------- 锚点（团结里按名字找）
    for n, x, y, z in [
        ("ANCHOR_enter_street", 0, -17.0, 0), ("ANCHOR_courtyard_kin", -3.0, -6.0, 0),
        ("ANCHOR_elder_lead", 0, -9.8, 0), ("ANCHOR_officer", 0, -12.4, 0),
        ("ANCHOR_soldier_L", -1.3, -13.2, 0), ("ANCHOR_soldier_R", 1.3, -13.2, 0),
        ("ANCHOR_pray", 0, 0.5, ZH), ("ANCHOR_altar", 0, 3.4, ZH + 1.0),
        ("ANCHOR_pages_join", 0, 1.9, ZH + 1.0), ("ANCHOR_tablet_pei", -0.9, 6.0, z2 + 0.5),
        ("ANCHOR_tablet_gao", 0.9, 6.0, z2 + 0.5), ("ANCHOR_tablet_father", 1.8, 5.55, z0 + 0.3),
        ("ANCHOR_sandtable", -4.8, 3.0, ZH + 0.95), ("ANCHOR_roster_table", 4.8, 3.0, ZH + 0.9),
        ("ANCHOR_stele", 6.0, 5.5, ZH + 1.5), ("ANCHOR_drum", 5.0, 0.4, ZH),
        ("ANCHOR_wangbingzhi", 2.4, 1.0, ZH), ("ANCHOR_faction_jiao", -3.0, 0.6, ZH),
        ("ANCHOR_faction_shao", 3.0, 0.6, ZH), ("ANCHOR_faction_cang", 0, -0.2, ZH),
        ("ANCHOR_hide_plaque", 0, 6.1, 4.3), ("ANCHOR_hide_wall", -9.4, 13.6, ZB),
        ("ANCHOR_hide_well", 0, 8.4, 0), ("ANCHOR_pu_cabinet", 0, 16.6, ZB),
        ("ANCHOR_cam_hall", 0, -4.5, 3.0), ("ANCHOR_cam_top", 0, 0, 36.0),
    ]:
        anchor(n, x, y, z)


# ============================================================ 环海楼
@recipe("Buildings", "BLD_INT_HuanhaiLou")
def r_int_huanhai():
    """环海楼内景（东门城楼，20 x 8.8）：
    底层 = 中间城门洞（千斤闸、双扇门） + 西侧值房（兵器架、铺位、灶） + 东侧楼梯间（沙袋、火罐、水缸）；
    上层 = 军议厅（长桌、舆图、战鼓、兵器架、铜钟、旗座），前檐出平座。原点在地面（城墙走道面）。"""
    G, GC = K.MB(), K.MB()              # 底层外壳 / 碰撞
    F2, F2C = K.MB(), K.MB()            # 二层楼板、平座
    U, UC = K.MB(), K.MB()              # 上层墙柱梁 / 碰撞
    FG, FU, FLAG, GATE = K.MB(), K.MB(), K.MB(), K.MB()
    RM, RE = K.MB(), K.MB()             # 屋顶：上檐 / 腰檐
    H1, ZS, H2 = 3.9, 4.2, 3.1          # 底层净高、二层楼面、二层高
    ZT = ZS + H2                        # 7.3
    GM = [G, GC]
    UM = [U, UC]

    # ---------- 底层地面
    G.box(-10, -4.4, -0.3, 10, 4.4, 0, "M_Floor_Brick")
    G.box(-2.4, -4.4, 0, 2.4, 4.4, 0.02, "M_Road_Stone")                                  # 门洞石板路
    for i in range(-5, 6):                                                                # 车辙石条
        G.box(-1.9, i * 0.8 - 0.02, 0.02, -1.5, i * 0.8 + 0.02, 0.04, "M_Stone_Base")
        G.box(1.5, i * 0.8 - 0.02, 0.02, 1.9, i * 0.8 + 0.02, 0.04, "M_Stone_Base")
    GC.box(-10, -4.4, -0.3, 10, 4.4, 0, "M_Plaster")

    # ---------- 底层墙：前后（城外 / 城内）墙开拱门，两端墙开走道门 + 射孔，门洞两侧隔墙
    for y in (-4.1, 4.1):
        wall_run(GM, "x", y, -10, -2.4, 0.6, 0, H1, "M_Brick_Grey", [(-6.2, 0.3, 2.4, 1.4, "slit"), (-8.4, 0.3, 2.4, 1.4, "slit")], trim=None)
        wall_run(GM, "x", y, 2.4, 10, 0.6, 0, H1, "M_Brick_Grey", [(6.2, 0.3, 2.4, 1.4, "slit"), (8.4, 0.3, 2.4, 1.4, "slit")], trim=None)
        arch_top(G, -2.4, 2.4, 2.6, H1, y - 0.3, y + 0.3, "M_Brick_Grey")
        GC.box(-2.4, y - 0.3, 2.6, 2.4, y + 0.3, H1, "M_Plaster")
        G.box(-2.55, y - 0.35, 0, -2.4, y + 0.35, 2.6, "M_Wall_Top")                       # 门洞石框
        G.box(2.4, y - 0.35, 0, 2.55, y + 0.35, 2.6, "M_Wall_Top")
    for sx in (-1, 1):                                                                    # 两端墙（接城墙走道）
        wall_run(GM, "y", 9.75 * sx, -4.4, 4.4, 0.5, 0, H1, "M_Brick_Grey",
                 [(0, 1.6, 2.6, 0, "door"), (-2.6, 0.3, 2.4, 1.4, "slit"), (2.6, 0.3, 2.4, 1.4, "slit")])
    wall_run(GM, "y", -2.4, -3.8, 3.8, 0.4, 0, H1, "M_Plaster", [(0.0, 1.4, 2.4, 0, "door")])      # 西侧隔墙（门洞 / 值房）
    wall_run(GM, "y", 2.4, -3.8, 3.8, 0.4, 0, H1, "M_Plaster", [(-1.0, 1.4, 2.4, 0, "door")])      # 东侧隔墙（门洞 / 楼梯间）
    G.box(-2.6, -3.8, 0, 2.6, 3.8, 0.0, "M_Floor_Brick")

    # ---------- 底层梁：门洞天花梁，房间梁
    for y in (-3.2, -1.6, 0.0, 1.6, 3.2):
        G.box(-2.4, y - 0.15, 3.4, 2.4, y + 0.15, H1, "M_Ceiling")
    for sx in (-1, 1):
        for y in (-3.0, 0.0, 3.0):
            G.box(sx * 2.4 - (0.0 if sx > 0 else 7.2), y - 0.15, 3.5, sx * 2.4 + (7.2 if sx > 0 else 0.0), y + 0.15, H1, "M_Ceiling")
        for x in (sx * 6.0,):
            G.cyl(x, 0, 0, 3.5, 0.2, "M_Red_Lacquer", seg=8)
            GC.box(x - 0.2, -0.2, 0, x + 0.2, 0.2, 3.5, "M_Plaster")

    # ---------- 东侧楼梯（21 级，通向二层，向 +X 升）
    for k in range(21):
        x0 = 3.0 + 0.26 * k
        G.box(x0, 2.2, 0, x0 + 0.26, 3.6, 0.2 * (k + 1), "M_Wood")
        G.box(x0, 2.18, 0.2 * (k + 1) - 0.04, x0 + 0.26, 2.2, 0.2 * (k + 1), "M_Wood_Dark")
    GC.prism([(3.0, 0), (8.46, 4.2), (8.46, 0)], "y", 2.2, 3.6, "M_Plaster")
    # 楼梯外侧栏杆
    for i in range(9):
        t = i / 8
        xs, zs = 3.0 + 5.46 * t, 0.2 + 4.2 * t
        G.box(xs - 0.04, 2.1, zs, xs + 0.04, 2.18, zs + 0.9, "M_Wood_Dark")
    G.prism([(3.0, 0.2 + 0.9 - 0.08), (8.46, 4.2 + 0.9 - 0.08), (8.46, 4.2 + 0.9), (3.0, 0.2 + 0.9)], "y", 2.08, 2.2, "M_Wood_Dark")

    # ---------- 二层楼板 + 平座（楼梯口留洞）
    for x0, y0, x1, y1 in [(-10, -4.4, 10, 2.2), (-10, 2.2, 3.0, 4.4), (8.6, 2.2, 10, 4.4), (3.0, 3.6, 8.6, 4.4)]:
        F2.box(x0, y0, H1, x1, y1, ZS, "M_Floor_Wood")
        F2C.box(x0, y0, H1, x1, y1, ZS, "M_Plaster")
    F2.box(-9.4, -5.4, H1, 9.4, -4.4, ZS, "M_Floor_Wood")                                  # 前檐平座
    F2C.box(-9.4, -5.4, H1, 9.4, -4.4, ZS, "M_Plaster")
    for x in range(-9, 10, 2):
        F2.box(x - 0.15, -5.4, 3.2, x + 0.15, -4.4, H1, "M_Wood_Dark")                      # 斗拱托梁
    F2.railing(-9.4, 9.4, -5.35, ZS, 0.95, "M_Wood_Dark", axis="x", post=1.6)
    for sx in (-1, 1):
        F2.railing(-5.35, -4.4, 9.35 * sx, ZS, 0.95, "M_Wood_Dark", axis="y", post=1.0)
        F2C.box(9.3 * sx - 0.05, -5.4, ZS, 9.3 * sx + 0.05, -4.4, ZS + 0.95, "M_Plaster")
    F2C.box(-9.4, -5.4, ZS, 9.4, -5.3, ZS + 0.95, "M_Plaster")
    F2.railing(3.0, 8.6, 2.1, ZS, 0.95, "M_Wood_Dark", axis="x", post=1.4)                  # 楼梯口护栏
    F2.railing(2.2, 3.6, 3.0, ZS, 0.95, "M_Wood_Dark", axis="y", post=0.8)
    F2C.box(3.0, 2.05, ZS, 8.6, 2.15, ZS + 0.95, "M_Plaster")
    F2C.box(2.95, 2.2, ZS, 3.05, 3.6, ZS + 0.95, "M_Plaster")

    # ---------- 上层墙（军议厅）
    wall_run(UM, "x", -3.6, -9.0, 9.0, 0.4, ZS, ZT, "M_Plaster",
             [(-7.2, 1.8, ZS + 2.7, ZS + 1.0, "win"), (-3.6, 1.8, ZS + 2.7, ZS + 1.0, "win"),
              (0.0, 2.4, ZS + 2.5, ZS, "door"),
              (3.6, 1.8, ZS + 2.7, ZS + 1.0, "win"), (7.2, 1.8, ZS + 2.7, ZS + 1.0, "win")])
    wall_run(UM, "x", 3.6, -9.0, 9.0, 0.4, ZS, ZT, "M_Plaster",
             [(-7.2, 1.6, ZS + 2.6, ZS + 1.2, "win"), (-3.6, 1.6, ZS + 2.6, ZS + 1.2, "win"),
              (3.6, 1.6, ZS + 2.6, ZS + 1.2, "win"), (7.2, 1.6, ZS + 2.6, ZS + 1.2, "win")])
    for sx in (-1, 1):
        wall_run(UM, "y", 9.0 * sx, -3.4, 3.4, 0.4, ZS, ZT, "M_Plaster", [(0, 1.8, ZS + 2.6, ZS + 1.1, "win")])
    U.box(-9.4, -3.9, ZS, 9.4, -3.8, ZS + 0.3, "M_Wood_Dark")                               # 踢脚
    # 上层柱、梁
    for x in (-7.2, -4.2, 4.2, 7.2):
        U.box(x - 0.3, -2.9 - 0.3, ZS, x + 0.3, -2.9 + 0.3, ZS + 0.12, "M_Stone_Base")
        U.cyl(x, -2.9, ZS + 0.12, ZT - 0.3, 0.2, "M_Red_Lacquer", seg=8)
        UC.box(x - 0.2, -3.1, ZS, x + 0.2, -2.7, ZS + 2.6, "M_Wood")
    for x in (-7.2, -4.2, -1.2, 1.8):
        U.cyl(x, 2.1, ZS + 0.12, ZT - 0.3, 0.2, "M_Red_Lacquer", seg=8)
        U.box(x - 0.3, 2.1 - 0.3, ZS, x + 0.3, 2.1 + 0.3, ZS + 0.12, "M_Stone_Base")
        UC.box(x - 0.2, 1.9, ZS, x + 0.2, 2.3, ZS + 2.6, "M_Wood")
    for x in (-8.0, -4.0, 0.0, 4.0, 8.0):
        U.box(x - 0.15, -3.6, ZT - 0.55, x + 0.15, 3.6, ZT - 0.25, "M_Ceiling")
    for y in (-2.9, 0.0, 2.1):
        U.box(-9.0, y - 0.12, ZT - 0.25, 9.0, y + 0.12, ZT, "M_Ceiling")
    U.box(-9.0, -3.6, ZT - 0.1, 9.0, -3.2, ZT + 0.1, "M_Wood_Dark")

    # ---------- 屋顶
    RM.hip_roof(-9.9, -4.5, 9.9, 4.5, ZT - 0.15, 3.2, 4.5)
    RE.shed_roof(-10.6, 10.6, -4.4, -6.2, 3.95, 3.2)
    RE.shed_roof(-10.6, 10.6, 4.4, 6.2, 3.95, 3.2)
    RE.shed_roof_y(-4.4, 4.4, -10.0, -11.8, 3.95, 3.2)
    RE.shed_roof_y(-4.4, 4.4, 10.0, 11.8, 3.95, 3.2)

    # ============ 底层家具
    # 城门双扇（打开，贴在门洞侧壁）
    for y0, y1 in ((-3.75, -1.7), (1.7, 3.75)):
        for sx in (-1, 1):
            xc = sx * 2.28
            GATE.box(xc - 0.07, y0, 0, xc + 0.07, y1, 3.2, "M_Red_Lacquer")
            for z in (0.5, 1.6, 2.7):
                GATE.box(xc - 0.1, y0, z, xc + 0.1, y1, z + 0.1, "M_Metal")
            for i in range(4):
                for z in (0.3, 0.9, 1.5, 2.1, 2.7):
                    yy = y0 + 0.25 + i * (y1 - y0 - 0.5) / 3
                    GATE.box(xc - 0.12 if sx > 0 else xc + 0.07, yy - 0.04, z - 0.04, xc - 0.07 if sx > 0 else xc + 0.12, yy + 0.04, z + 0.04, "M_Metal")
    GATE.box(-2.3, -3.0, 1.0, 2.3, -2.9, 1.12, "M_Wood_Dark")                               # 门闩（靠在洞口前）
    # 千斤闸（提起，只露上半格栅）
    for i in range(-6, 7):
        GATE.box(i * 0.34 - 0.05, 0.9, 2.9, i * 0.34 + 0.05, 1.1, H1, "M_Wood_Dark")
    for z in (3.05, 3.5):
        GATE.box(-2.3, 0.85, z, 2.3, 1.15, z + 0.12, "M_Metal")
    GATE.box(-0.05, 0.98, H1 - 0.02, 0.05, 1.02, H1 + 0.0, "M_Metal")
    # 值房（西）：兵器架、铺位、值守桌、灶、水缸
    for x in (-8.2, -7.6, -7.0, -6.4, -5.8, -5.2):
        FG.box(x - 0.025, 3.05, 0.25, x + 0.025, 3.1, 2.5, "M_Wood_Dark")                      # 枪杆
        FG.box(x - 0.04, 3.04, 2.5, x + 0.04, 3.11, 2.64, "M_Metal")                           # 枪头
        FG.box(x - 0.05, 3.04, 2.2, x + 0.05, 3.11, 2.3, "M_Cloth_Red")                        # 枪缨
    FG.box(-8.5, 3.0, 0, -4.9, 3.2, 0.2, "M_Wood")
    FG.box(-8.5, 3.0, 1.1, -4.9, 3.2, 1.2, "M_Wood")
    FG.box(-8.5, 3.0, 0, -8.4, 3.2, 1.3, "M_Wood_Dark")
    FG.box(-5.0, 3.0, 0, -4.9, 3.2, 1.3, "M_Wood_Dark")
    for x0 in (-9.2, -6.9, -4.6):                                                           # 铺位
        FG.box(x0, -3.7, 0.3, x0 + 2.0, -2.7, 0.4, "M_Wood")
        for dx in (0.05, 1.85):
            for dy in (-3.65, -2.85):
                FG.box(x0 + dx, dy, 0, x0 + dx + 0.1, dy + 0.1, 0.3, "M_Wood_Dark")
        FG.box(x0 + 0.05, -3.65, 0.4, x0 + 1.95, -2.75, 0.46, "M_Thatch")
        FG.box(x0 + 0.1, -3.6, 0.46, x0 + 0.7, -3.0, 0.6, "M_Cloth_Red")
    table(FG, -7.6, -0.7, -5.8, 0.2, 0, 0.8)
    stool(FG, -8.0, -0.3, 0)
    stool(FG, -6.7, 0.7, 0)
    stool(FG, -6.7, -1.3, 0)
    FG.box(-5.4, -0.55, 0.8, -5.0, -0.2, 0.84, "M_Paper")
    FG.box(-9.4, 1.4, 0, -8.2, 2.3, 0.8, "M_Brick_Grey")                                      # 灶
    FG.cyl(-8.8, 1.85, 0.8, 1.05, 0.32, "M_Metal", seg=8, r_top=0.36)
    FG.box(-9.4, 2.3, 0.8, -9.0, 2.7, 2.6, "M_Brick_Grey")                                  # 烟道
    jar(FG, -9.1, -1.6, 0, 0.45, 0.95)
    jar(FG, -3.3, -3.2, 0, 0.4, 0.8)
    lantern(FG, -6.7, -0.3, 3.5, drop=0.4)
    # 楼梯间（东）：沙袋、火罐架、水缸、水桶
    for r in range(3):
        for c in range(4 - r):
            FG.box(4.2 + c * 0.62 + r * 0.31, -3.5, r * 0.22, 4.2 + c * 0.62 + r * 0.31 + 0.58, -3.0, r * 0.22 + 0.2, "M_Sandbag")
    for r in range(2):
        for c in range(3 - r):
            FG.box(9.0 - 0.5, -3.5 + c * 0.55 + r * 0.27, r * 0.22, 9.4, -3.5 + c * 0.55 + r * 0.27 + 0.5, r * 0.22 + 0.2, "M_Sandbag")
    FG.box(6.6, -3.7, 0.0, 8.8, -3.4, 0.08, "M_Wood")
    for z in (0.08, 0.75):
        FG.box(6.6, -3.7, z, 8.8, -3.0, z + 0.06, "M_Wood")
    for x in (6.7, 8.7):
        FG.box(x - 0.04, -3.65, 0, x + 0.04, -3.05, 1.5, "M_Wood_Dark")
    for z in (0.14, 0.81):                                                                  # 火罐
        for i in range(5):
            xx = 6.9 + i * 0.4
            for yy in (-3.55, -3.25):
                FG.cyl(xx, yy, z, z + 0.4, 0.14, "M_Brick_Red", seg=8, r_top=0.11)
                FG.cyl(xx, yy, z + 0.36, z + 0.42, 0.1, "M_Fire", seg=8)
    jar(FG, 9.0, -1.4, 0, 0.5, 0.95)
    jar(FG, 9.0, 1.5, 0, 0.5, 0.95)
    for x, y in ((4.0, -2.2), (4.6, -2.4), (4.3, -1.7)):
        FG.cyl(x, y, 0, 0.36, 0.22, "M_Wood", seg=8, r_top=0.18)
    lantern(FG, 5.0, 0.4, 3.5, drop=0.4)
    for x in (5.6,):
        GC.box(x - 1.0, -3.75, 0, x + 3.8, -2.9, 1.5, "M_Plaster")

    # ============ 上层家具：军议
    table(FU, -3.0, -1.1, 3.0, 0.3, ZS, 0.85)
    FU.box(-2.7, -1.0, ZS + 0.85, 2.7, 0.2, ZS + 0.87, "M_Paper")                             # 舆图
    for i, (px, py, m) in enumerate([(-2.0, -0.6, "M_Fire"), (-1.1, -0.2, "M_Fire"), (0.3, -0.5, "M_Fire"), (1.6, 0.0, "M_Water"),
                                     (2.2, -0.7, "M_Water"), (-0.5, 0.0, "M_Water"), (0.9, -0.8, "M_Fire")]):
        FU.cyl(px, py, ZS + 0.87, ZS + 1.0, 0.04, m, seg=6)
    FU.box(-2.7, -0.05, ZS + 0.87, 2.7, 0.0, ZS + 0.89, "M_Water")                           # 图上的海岸线（示意）
    for x in (-2.4, -0.8, 0.8, 2.4):
        stool(FU, x, -1.8, ZS)
        stool(FU, x, 1.0, ZS)
    stool(FU, -3.7, -0.4, ZS)
    stool(FU, 3.7, -0.4, ZS)
    UC.box(-3.0, -1.1, ZS, 3.0, 0.3, ZS + 0.85, "M_Plaster")
    # 舆图（挂后墙）
    FU.box(-2.6, 3.37, ZS + 0.9, 2.6, 3.4, ZS + 2.7, "M_Paper")
    for b in ((-2.7, 3.35, ZS + 0.85, 2.7, 3.4, ZS + 0.95), (-2.7, 3.35, ZS + 2.65, 2.7, 3.4, ZS + 2.75),
              (-2.7, 3.35, ZS + 0.85, -2.6, 3.4, ZS + 2.75), (2.6, 3.35, ZS + 0.85, 2.7, 3.4, ZS + 2.75)):
        FU.box(*b, "M_Wood_Dark")
    # 战鼓
    FU.cyl(-8.2, -2.4, ZS + 0.5, ZS + 1.4, 0.5, "M_Red_Lacquer", seg=10, r_top=0.42)
    FU.cyl(-8.2, -2.4, ZS + 1.4, ZS + 1.44, 0.42, "M_Sandbag", seg=10)
    for z in (ZS + 0.65, ZS + 1.2):
        FU.cyl(-8.2, -2.4, z, z + 0.06, 0.5, "M_Bronze", seg=10)
    for dx in (-0.45, 0.45):
        FU.box(-8.2 + dx - 0.05, -2.55, ZS, -8.2 + dx + 0.05, -2.25, ZS + 0.55, "M_Wood_Dark")
    FU.box(-8.55, -2.7, ZS + 1.46, -8.15, -2.65, ZS + 1.5, "M_Wood")
    UC.cyl(-8.2, -2.4, ZS, ZS + 1.5, 0.52, "M_Plaster", seg=8)
    # 兵器架（沛公的枪 2.6 m 就挂在这里）
    FU.box(8.25, -3.1, ZS, 8.55, -0.5, ZS + 0.12, "M_Wood_Dark")
    for z in (0.7, 1.6):
        FU.box(8.3, -3.1, ZS + z, 8.5, -0.5, ZS + z + 0.08, "M_Wood")
    for y in (-3.1, -0.58):
        FU.box(8.3, y, ZS, 8.5, y + 0.08, ZS + 1.9, "M_Wood_Dark")
    for i in range(7):
        y = -2.9 + i * 0.36
        FU.box(8.37, y, ZS + 0.12, 8.43, y + 0.06, ZS + 2.6 if i == 3 else ZS + 2.3, "M_Wood_Dark")
        FU.box(8.35, y - 0.01, (ZS + 2.6 if i == 3 else ZS + 2.3), 8.45, y + 0.07, (ZS + 2.74 if i == 3 else ZS + 2.44), "M_Metal")
        FU.box(8.34, y - 0.02, ZS + 2.0, 8.46, y + 0.08, ZS + 2.12, "M_Cloth_Red")
    UC.box(8.2, -3.1, ZS, 8.6, -0.5, ZS + 1.0, "M_Plaster")
    # 铜钟（警钟）
    FU.box(-8.6, 1.6, ZS, -8.4, 1.8, ZS + 2.4, "M_Wood_Dark")
    FU.box(-7.2, 1.6, ZS, -7.0, 1.8, ZS + 2.4, "M_Wood_Dark")
    FU.box(-8.7, 1.62, ZS + 2.3, -6.9, 1.78, ZS + 2.5, "M_Wood_Dark")
    FU.cyl(-7.8, 1.7, ZS + 1.1, ZS + 2.25, 0.3, "M_Bronze", seg=10, r_top=0.15)
    FU.box(-7.82, 1.4, ZS + 1.4, -7.78, 2.4, ZS + 1.48, "M_Wood")
    UC.box(-8.6, 1.5, ZS, -7.0, 1.9, ZS + 1.0, "M_Plaster")
    # 弹药箱、炮弹（东台火炮取用）
    for i, (x, y) in enumerate(((7.0, -2.6), (7.7, -2.6), (7.35, -2.6))):
        z = ZS if i < 2 else ZS + 0.45
        FU.box(x - 0.3, y - 0.25, z, x + 0.3, y + 0.25, z + 0.45, "M_Wood")
        FU.box(x - 0.3, y - 0.27, z + 0.2, x + 0.3, y - 0.25, z + 0.26, "M_Metal")
    for r in range(3):
        for c in range(3 - r):
            FU.ico(5.5 + c * 0.26 + r * 0.13, -3.0, ZS + 0.11 + r * 0.2, 0.12, "M_Metal", subdiv=1)
    UC.box(6.6, -3.0, ZS, 8.1, -2.3, ZS + 0.9, "M_Plaster")
    # 值事案
    table(FU, -8.0, 2.6, -6.6, 3.3, ZS, 0.8)
    stool(FU, -7.3, 2.1, ZS)
    FU.box(-7.8, 2.8, ZS + 0.8, -7.2, 3.1, ZS + 0.83, "M_Paper")
    # 灯笼
    for x in (-6.0, -2.0, 2.0, 6.0):
        lantern(FU, x, -2.9, ZT - 0.3, drop=0.35)
    # 旗座 + 旗杆（旗杆单独成物体：1941 倒下 / 1560 完好；枢轴在旗座中心）
    FLAG.box(-0.35, 2.55, ZS, 0.35, 3.25, ZS + 0.35, "M_Stone_Base")
    FLAG.cyl(0, 2.9, ZS + 0.35, ZS + 3.7, 0.07, "M_Wood_Dark", seg=6, r_top=0.05)
    FLAG.box(0.05, 2.88, ZS + 2.7, 1.45, 2.92, ZS + 3.55, "M_Flag")
    FLAG.box(0.0, 2.86, ZS + 2.7, 0.06, 2.94, ZS + 3.55, "M_Wood_Dark")
    FLAG.box(0.05, 2.87, ZS + 2.7, 1.45, 2.93, ZS + 2.78, "M_Cloth_Red")
    UC.box(-0.35, 2.55, ZS, 0.35, 3.25, ZS + 0.35, "M_Plaster")

    emit_objects([("INT_Ground", G), ("COL_Ground", GC), ("INT_Floor2", F2), ("COL_Floor2", F2C),
                  ("INT_Upper", U), ("COL_Upper", UC),
                  ("INT_Gate", GATE), ("INT_Furniture_Ground", FG), ("INT_Furniture_Upper", FU), ("INT_Flagpole", FLAG),
                  ("ROOF_Main", RM), ("ROOF_Eaves", RE)])
    for n, x, y, z in [
        ("ANCHOR_gate_out", 0, -6.0, 0), ("ANCHOR_gate_in", 0, 6.0, 0),
        ("ANCHOR_walk_W", -9.9, 0, 0), ("ANCHOR_walk_E", 9.9, 0, 0),
        ("ANCHOR_stair_bottom", 3.1, 2.9, 0), ("ANCHOR_stair_top", 8.8, 2.9, ZS),
        ("ANCHOR_guard_post", -6.5, 0.2, 0), ("ANCHOR_spear_rack", 8.4, -1.8, ZS),
        ("ANCHOR_muster_table", 0, -0.4, ZS + 0.9), ("ANCHOR_wang_pei", -2.2, -2.3, ZS),
        ("ANCHOR_wang_shugao", 2.2, 1.1, ZS), ("ANCHOR_wang_yan", 0, -1.7, ZS),
        ("ANCHOR_balcony", 0, -4.9, ZS), ("ANCHOR_cannon_post", 6.0, -4.9, ZS),
        ("ANCHOR_bell", -7.8, 1.7, ZS), ("ANCHOR_flagpole", 0, 2.9, ZS),
        ("ANCHOR_look_sea", 0, -6.0, ZS + 1.6),
        ("ANCHOR_cam_top_upper", 0, 0, 24.0), ("ANCHOR_cam_top_ground", 0, 0, 20.0),
    ]:
        anchor(n, x, y, z)


# ============================================================ 预览渲染
def _bbox_center(objs):
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            mn = Vector((min(mn[i], w[i]) for i in range(3)))
            mx = Vector((max(mx[i], w[i]) for i in range(3)))
    return mn, mx


def render_shots(outdir, name, shots):
    """shots: [(文件后缀, 'ortho'|'persp', 位置, 目标, 隐藏前缀元组, 参数)]。"""
    scene = bpy.context.scene
    scene.render.engine = "BLENDER_WORKBENCH"
    sh = scene.display.shading
    sh.light = "STUDIO"
    sh.color_type = "MATERIAL"
    sh.show_shadows = False
    sh.show_cavity = True
    sh.cavity_type = "WORLD"
    scene.render.resolution_x, scene.render.resolution_y = 1100, 800
    ref = bpy.data.collections.get("_REF")
    if ref:
        ref.hide_render = True
    for suffix, kind, loc, tgt, hide, param in shots:
        cd = bpy.data.cameras.new("PrevCam")
        cam = bpy.data.objects.new("PrevCam", cd)
        scene.collection.objects.link(cam)
        if kind == "ortho":
            cd.type = "ORTHO"
            cd.ortho_scale = param
        else:
            cd.lens = param
        cd.clip_start, cd.clip_end = 0.05, 400
        cam.location = Vector(loc)
        direction = Vector(tgt) - Vector(loc)
        up = "Y" if abs(direction.normalized().z) < 0.99 else "Y"
        cam.rotation_euler = direction.to_track_quat("-Z", up).to_euler()
        scene.camera = cam
        for o in scene.objects:
            if o.type == "MESH":
                o.hide_render = any(o.name.startswith(p) for p in hide)
        scene.render.filepath = os.path.join(outdir, f"{name}_{suffix}.png")
        bpy.ops.render.render(write_still=True)
        bpy.data.objects.remove(cam, do_unlink=True)
    for o in scene.objects:
        o.hide_render = False


PREVIEWS = {
    "BLD_INT_AncestralHall": [
        ("top", "ortho", (0, 0, 60), (0, 0, 0), ("ROOF_",), 42),
        ("top_roof", "ortho", (0, -0.01, 60), (0, 0, 0), ("COL_",), 42),
        ("hall_to_altar", "persp", (0, -1.2, 2.6), (0, 4.5, 1.9), ("ROOF_", "COL_"), 28),
        ("courtyard", "persp", (0, -16.5, 2.2), (0, -4.0, 1.8), ("ROOF_", "COL_"), 26),
        ("hall_cut", "persp", (13.0, -9.0, 9.5), (0, 2.0, 1.5), ("ROOF_Main", "ROOF_Corridor", "COL_"), 32),
        ("rear", "persp", (0, 8.2, 2.4), (0, 16.0, 1.6), ("ROOF_", "COL_"), 30),
    ],
    "BLD_INT_HuanhaiLou": [
        ("top_upper", "ortho", (0, 0, 40), (0, 0, 0), ("ROOF_", "COL_"), 24),
        ("top_ground", "ortho", (0, 0, 40), (0, 0, 0), ("ROOF_", "COL_", "INT_Floor2", "INT_Upper"), 24),
        ("upper_hall", "persp", (-8.0, 2.8, 6.4), (2.0, -1.0, 5.4), ("ROOF_", "COL_"), 22),
        ("upper_hall_b", "persp", (7.5, 2.6, 6.2), (-3.0, -1.5, 5.0), ("ROOF_", "COL_"), 22),
        ("gate_passage", "persp", (0, -8.0, 1.6), (0, 3.0, 1.9), ("ROOF_", "COL_"), 24),
        ("stair_room", "persp", (3.2, -3.0, 1.7), (8.0, 1.5, 1.6), ("ROOF_", "COL_", "INT_Floor2", "INT_Upper"), 24),
        ("cut", "persp", (16.0, -16.0, 14.0), (0, 0, 3.0), ("ROOF_", "COL_"), 32),
    ],
}


# ============================================================ 驱动
def main(argv):
    only = set(argv[argv.index("--only") + 1].split(",")) if "--only" in argv else None
    force = "--force" in argv
    export = "--no-export" not in argv
    preview = argv[argv.index("--preview") + 1] if "--preview" in argv else None
    if preview:
        os.makedirs(preview, exist_ok=True)
    if "--list" in argv:
        for n, (c, _) in sorted(RECIPES.items()):
            print(f"{c:12s} {n}")
        return 0
    fails = []
    for name, (cat, fn) in RECIPES.items():
        if only and name not in only:
            continue
        blend = os.path.join(REPO, "ArtSource", cat, name + ".blend")
        if os.path.exists(blend) and not force:
            print(f"[skip] {name}（已存在，--force 覆盖）")
            continue
        try:
            RP.new_template(cat, name, os.path.dirname(blend))
            fn()
            bpy.ops.wm.save_as_mainfile(filepath=blend)
            errors, warnings, stats = RP.validate()
            for w in warnings:
                if "旋转" in w or "没有骨架" in w:
                    continue
                print(f"[WARN] {name}: {w}")
            if errors:
                fails.append(name)
                for e in errors:
                    print(f"[ERROR] {name}: {e}")
                continue
            if export:
                ok, errors, warnings, stats = RP.do_export()
                if not ok:
                    fails.append(name)
            if preview:
                render_shots(preview, name, PREVIEWS[name])
            print(f"[OK] {name:26s} {stats['tris']:6d} tris  -> "
                  f"{os.path.relpath(stats['target'], REPO) if export else blend}")
        except Exception:
            traceback.print_exc()
            fails.append(name)
    if fails:
        print("[FAIL]", ", ".join(fails))
        return 1
    return 0


if __name__ == "__main__":
    args = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    sys.exit(main(args))
