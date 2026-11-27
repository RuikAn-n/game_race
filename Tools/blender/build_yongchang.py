"""
永昌堡 总地图：一键生成全部白模资产（Blender 无界面）
====================================================

  /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup \
      -P Tools/blender/build_yongchang.py -- [--only A,B] [--force] [--no-export] [--preview DIR] [--list]

  或：Tools/mac/build_yongchang.sh [同上参数]

每个资产生成一个 ArtSource/<分类>/<资产名>.blend（带 _REF 参考人），并经 rupu_pipeline 检查 + 导出 FBX 到
Project_rupu/Assets/Art/<分类>/<资产名>/。已存在的 .blend 默认跳过（保护美术手改），--force 覆盖。

资产分三组：
  通用（两个年代共用几何，只换材质）：城墙、敌台、角台、城门台、水门、马道、瓮城、桥、河埠头
  民国（BLD_ROC_*）：民居、店屋、西式店面、合院、祠堂、庙、仓、城楼、环海楼、哨卡、码头、盐舍
  环境（ENV_*）：地面（按布局切出河道/护城河/道路）、水面、田、罗山
  人物（CH_/NPC_，见 rupu_char.py）：王砚 1941/1560、王沛、王叔杲、王德、王秉之 + 共用 Idle/Walk/Run 动画 + 枪/拐/算盘
明代（BLD_MING_*）以后按同一 kind 和同一占地尺寸另做，布局不用动（见 Data/map/era_kits.json）。

坐标：模型正面朝 Blender -Y。地形按团结世界坐标 (x东, z北) 生成，换算 Blender (X, Y) = (-x, -z)，
导出后正好落在团结世界的 (x, z)。
"""
import json
import math
import os
import random
import sys
import traceback

import bmesh
import bpy
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import rupu_kit as K          # noqa: E402
import rupu_pipeline as RP    # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
LAYOUT = os.path.join(REPO, "Data", "map", "yongchang_layout.json")

WALK = 7.08     # 城墙走道面高度（墙体 7.0 + 铺面 0.08）

RECIPES = {}


def recipe(category, name):
    def deco(fn):
        RECIPES[name] = (category, fn)
        return fn
    return deco


def load_layout():
    with open(LAYOUT, encoding="utf-8") as f:
        return json.load(f)


# ====================================================================== 城墙（通用）
def wall_body(mb, x0, x1, parapet=True, crenel=True):
    """一段城墙：外侧（-Y）收分，走道铺面，外侧垛口。"""
    mb.prism([(-2.5, -0.5), (2.5, -0.5), (2.5, 7.0), (-2.1, 7.0)], "x", x0, x1, "M_Wall_Stone")
    mb.box(x0, -2.75, -0.5, x1, -2.35, 0.45, "M_Stone_Base")                       # 勒脚
    mb.box(x0, -1.5, 7.0, x1, 2.5, WALK, "M_Wall_Top")                             # 走道铺面
    mb.box(x0, 2.35, 6.75, x1, 2.6, 7.0, "M_Stone_Base")                           # 内侧压檐石
    if parapet:
        mb.box(x0, -2.1, 7.0, x1, -1.5, 7.95, "M_Wall_Stone")
        mb.box(x0, -2.2, 7.95, x1, -1.4, 8.05, "M_Wall_Top")
        if crenel:
            mb.crenels(x0, x1, -2.1, -1.5, 8.05, 8.75, "M_Wall_Stone")


@recipe("Buildings", "BLD_Wall_Seg")
def r_wall_seg():
    mb = K.MB()
    wall_body(mb, -4, 4)
    # 排水口（外墙小石嘴）
    mb.box(-0.2, -2.45, 6.4, 0.2, -1.9, 6.6, "M_Stone_Base")
    mb.to_object("BLD_Wall_Seg")


@recipe("Buildings", "BLD_Wall_DiTai")
def r_ditai():
    mb = K.MB()
    wall_body(mb, -4, 4, parapet=False)
    # 敌台（马面）：向外凸 6 m，有收分
    mb.frustum((-4, -8.5, 4, -2.3), (-3.7, -8.2, 3.7, -2.3), -0.5, 7.0, "M_Wall_Stone")
    mb.box(-4.2, -8.75, -0.5, 4.2, -8.35, 0.45, "M_Stone_Base")
    mb.box(-3.7, -8.2, 7.0, 3.7, -1.5, WALK, "M_Wall_Top")
    # 三面垛墙
    mb.box(-3.7, -8.2, 7.0, 3.7, -7.6, 7.95, "M_Wall_Stone")
    mb.box(-3.7, -7.6, 7.0, -3.1, -2.1, 7.95, "M_Wall_Stone")
    mb.box(3.1, -7.6, 7.0, 3.7, -2.1, 7.95, "M_Wall_Stone")
    mb.crenels(-3.7, 3.7, -8.2, -7.6, 7.95, 8.7, "M_Wall_Stone", merlon=1.1, gap=0.6)
    mb.crenels(-7.6, -2.1, -3.7, -3.1, 7.95, 8.7, "M_Wall_Stone", merlon=1.1, gap=0.6, axis="y")
    mb.crenels(-7.6, -2.1, 3.1, 3.7, 7.95, 8.7, "M_Wall_Stone", merlon=1.1, gap=0.6, axis="y")
    # 炮位垫石
    mb.box(-1.0, -7.4, WALK, 1.0, -5.6, WALK + 0.15, "M_Stone_Base")
    mb.to_object("BLD_Wall_DiTai")


@recipe("Buildings", "BLD_Wall_Corner")
def r_corner():
    """角台 10x10。城墙接在 +X 面与 +Y 面中部（团结局部 -X / -Z），外侧是 -X/-Y。"""
    mb = K.MB()
    mb.frustum((-5, -5, 5, 5), (-4.7, -4.7, 5, 5), -0.5, 7.0, "M_Wall_Stone")
    mb.box(-5.2, -5.2, -0.5, 5.0, -4.8, 0.45, "M_Stone_Base")
    mb.box(-5.2, -5.2, -0.5, -4.8, 5.0, 0.45, "M_Stone_Base")
    mb.box(-4.7, -4.7, 7.0, 5, 5, WALK, "M_Wall_Top")
    # 外侧两面垛墙 + 接墙处的外半段
    mb.box(-4.7, -4.7, 7.0, 5.0, -4.1, 7.95, "M_Wall_Stone")          # -Y 面（含 +X 面外半段转角）
    mb.box(-4.7, -4.1, 7.0, -4.1, 5.0, 7.95, "M_Wall_Stone")          # -X 面
    mb.box(4.4, -4.1, 7.0, 5.0, -1.5, 7.95, "M_Wall_Stone")           # +X 面外段（接北/南墙垛墙）
    mb.box(-4.1, 4.4, 7.0, -1.5, 5.0, 7.95, "M_Wall_Stone")           # +Y 面外段
    mb.crenels(-4.7, 5.0, -4.7, -4.1, 7.95, 8.7, "M_Wall_Stone")
    mb.crenels(-4.1, 5.0, -4.7, -4.1, 7.95, 8.7, "M_Wall_Stone", axis="y")
    # 角楼（小哨亭）
    for x, y in ((-3.6, -3.6), (-0.6, -3.6), (-0.6, -0.6), (-3.6, -0.6)):
        mb.box(x - 0.13, y - 0.13, WALK, x + 0.13, y + 0.13, WALK + 2.6, "M_Wood_Dark")
    mb.hip_roof(-4.4, -4.4, 0.2, 0.2, WALK + 2.5, 1.4, 2.3)
    mb.to_object("BLD_Wall_Corner")


def gate_base(mb, half, depth, tw, spring, plaque=True):
    yh = depth / 2
    mb.arch_slab(-half, half, -tw / 2, tw / 2, -0.5, spring, 7.0, -yh, yh, "M_Wall_Stone", seg=10)
    mb.box(-half - 0.2, -yh - 0.25, -0.5, -tw / 2 - 0.3, -yh + 0.1, 0.5, "M_Stone_Base")
    mb.box(tw / 2 + 0.3, -yh - 0.25, -0.5, half + 0.2, -yh + 0.1, 0.5, "M_Stone_Base")
    # 门洞券脸（外圈石）
    r = tw / 2 + 0.35
    for i in range(10):
        a0 = math.pi - math.pi * i / 10
        a1 = math.pi - math.pi * (i + 1) / 10
        p = [(r * math.cos(a0), spring + r * math.sin(a0)), (r * math.cos(a1), spring + r * math.sin(a1)),
             ((tw / 2) * math.cos(a1), spring + (tw / 2) * math.sin(a1)), ((tw / 2) * math.cos(a0), spring + (tw / 2) * math.sin(a0))]
        mb.prism(p, "y", -yh - 0.08, -yh + 0.01, "M_Stone_Base")
    mb.box(-half, -yh, 7.0, half, yh, WALK, "M_Wall_Top")
    mb.box(-half, -yh, 7.0, half, -yh + 0.6, 7.95, "M_Wall_Stone")
    mb.box(-half, -yh - 0.1, 7.95, half, -yh + 0.7, 8.05, "M_Wall_Top")
    mb.crenels(-half, -tw / 2 - 1.5, -yh, -yh + 0.6, 8.05, 8.75, "M_Wall_Stone")
    mb.crenels(tw / 2 + 1.5, half, -yh, -yh + 0.6, 8.05, 8.75, "M_Wall_Stone")
    if plaque:
        mb.box(-1.4, -yh - 0.12, spring + tw / 2 + 0.6, 1.4, -yh + 0.01, spring + tw / 2 + 1.4, "M_Plaque")
    # 门扇（开启状态，贴在洞内两侧）
    for s in (-1, 1):
        mb.box(s * tw / 2 - s * 0.12, -yh + 1.0, 0, s * tw / 2 - s * 0.02, -yh + 1.0 + tw / 2 - 0.1, spring + 0.6, "M_Wood_Dark")


@recipe("Buildings", "BLD_Wall_GateBase")
def r_gate_base():
    mb = K.MB()
    gate_base(mb, 8.0, 7.0, 4.4, 3.6)
    mb.to_object("BLD_Wall_GateBase")


@recipe("Buildings", "BLD_Wall_GateBaseL")
def r_gate_base_l():
    mb = K.MB()
    gate_base(mb, 12.0, 9.0, 5.0, 3.8)
    mb.to_object("BLD_Wall_GateBaseL")


@recipe("Buildings", "BLD_Wall_WaterGate")
def r_watergate():
    mb = K.MB()
    mb.arch_slab(-4, 4, -3.2, 3.2, -1.8, 1.6, 7.0, -2.5, 2.5, "M_Wall_Stone", seg=10)
    mb.box(-4, -1.5, 7.0, 4, 2.5, WALK, "M_Wall_Top")
    mb.box(-4, -2.1, 7.0, 4, -1.5, 7.95, "M_Wall_Stone")
    mb.box(-4, -2.2, 7.95, 4, -1.4, 8.05, "M_Wall_Top")
    mb.crenels(-4, 4, -2.1, -1.5, 8.05, 8.75, "M_Wall_Stone")
    # 闸槽（两侧竖槽石）
    for s in (-1, 1):
        mb.box(s * 3.12, -0.9, -1.8, s * 3.45, -0.5, 4.6, "M_Stone_Base")
    # 闸门（半开，团结里可做动画；anchor_watergate_* 挂点）
    mb.box(-3.15, -0.8, 1.2, 3.15, -0.6, 4.4, "M_Wood_Dark")
    mb.box(-3.0, -2.6, 4.9, 3.0, -2.45, 5.3, "M_Plaque")
    mb.to_object("BLD_Wall_WaterGate")


@recipe("Buildings", "BLD_Wall_Ramp")
def r_ramp():
    """马道：沿内墙面的登城踏步，向团结局部 +X（Blender -X）升高。正面(-Y)贴墙。"""
    mb = K.MB()
    n = 20
    L = 14.0
    for k in range(n):
        xa = 7 - L * k / n
        xb = 7 - L * (k + 1) / n
        top = WALK * (k + 1) / n
        mb.box(xb, -1.5, 0, xa, 1.5, top, "M_Wall_Stone" if k % 5 else "M_Stone_Base")
    # 外侧挡墙 + 矮墙
    mb.prism([(7, 0), (-7, 0), (-7, WALK + 0.8), (7, 0.8)], "y", 1.5, 1.9, "M_Wall_Stone")
    mb.to_object("BLD_Wall_Ramp")
    col = K.MB()
    col.prism([(7.6, 0), (-7, WALK), (-7, 0)], "y", -1.5, 1.5, "M_Wall_Stone")
    col.to_object("COL_Ramp")


@recipe("Buildings", "BLD_Wall_Wengcheng")
def r_wengcheng():
    """瓮城：原点在主墙外皮中点，向外(-Y)伸出 18 m，宽 28 m，外门朝外。"""
    mb = K.MB()
    for x0, x1 in ((-14, -10), (10, 14)):
        mb.box(x0, -18, -0.5, x1, 0, 7.0, "M_Wall_Stone")
        mb.box(x0, -18, 7.0, x1, 0, WALK, "M_Wall_Top")
    mb.arch_slab(-10, 10, -2.2, 2.2, -0.5, 3.4, 7.0, -18, -14, "M_Wall_Stone", seg=10)
    mb.box(-10, -18, 7.0, 10, -14, WALK, "M_Wall_Top")
    mb.box(-14.2, -18.25, -0.5, -2.6, -17.85, 0.45, "M_Stone_Base")      # 勒脚（门洞处断开，可通行）
    mb.box(2.6, -18.25, -0.5, 14.2, -17.85, 0.45, "M_Stone_Base")
    # 外侧垛墙
    mb.box(-14, -18, WALK, 14, -17.4, 7.95, "M_Wall_Stone")
    mb.box(-14, -17.4, WALK, -13.4, 0, 7.95, "M_Wall_Stone")
    mb.box(13.4, -17.4, WALK, 14, 0, 7.95, "M_Wall_Stone")
    mb.crenels(-14, 14, -18, -17.4, 7.95, 8.7, "M_Wall_Stone")
    mb.crenels(-17.4, -2.6, -14, -13.4, 7.95, 8.7, "M_Wall_Stone", axis="y")
    mb.crenels(-17.4, -2.6, 13.4, 14, 7.95, 8.7, "M_Wall_Stone", axis="y")
    mb.box(-1.4, -18.15, 5.8, 1.4, -17.99, 6.6, "M_Plaque")
    mb.to_object("BLD_Wall_Wengcheng")


# ====================================================================== 桥 / 河埠头（通用）
def make_bridge(name, span, width):
    mb = K.MB()
    L = span + 2.4
    hw = width / 2
    top = 0.25
    mb.box(-hw, -L / 2, top - 0.42, hw, L / 2, top, "M_Stone_Base")
    # 桥头压石（两端斜坡感）
    for s in (-1, 1):
        mb.box(-hw - 0.15, s * L / 2 - (0.6 if s > 0 else 0), -0.6, hw + 0.15, s * L / 2 + (0.6 if s < 0 else 0), 0.12, "M_Bank_Stone")
    # 栏板
    for sx in (-1, 1):
        x0, x1 = (sx * hw - 0.28, sx * hw) if sx > 0 else (sx * hw, sx * hw + 0.28)
        mb.box(x0, -span / 2 - 0.4, top, x1, span / 2 + 0.4, top + 0.55, "M_Stone_Base")
        n = max(2, int(span / 1.6) + 1)
        for i in range(n + 1):
            y = -span / 2 - 0.4 + (span + 0.8) * i / n
            mb.box(x0 - 0.04, y - 0.14, top, x1 + 0.04, y + 0.14, top + 0.75, "M_Stone_Base")
    # 桥墩
    if span >= 9:
        piers = [0.0] if span < 14 else [-span / 6, span / 6]
        for y in piers:
            mb.box(-hw + 0.2, y - 0.5, -2.4, hw - 0.2, y + 0.5, top - 0.42, "M_Bank_Stone")
            mb.prism([(-hw + 0.2, -2.4), (-hw - 0.8, -2.4), (-hw + 0.2, top - 0.42)], "y", y - 0.5, y + 0.5, "M_Bank_Stone")
            mb.prism([(hw - 0.2, -2.4), (hw - 0.2, top - 0.42), (hw + 0.8, -2.4)], "y", y - 0.5, y + 0.5, "M_Bank_Stone")
    mb.to_object(name)


for _span in (3, 4, 6):
    for _w, _tag in ((3.2, "n"), (6.4, "w")):
        _nm = f"BLD_Bridge_{_span}{_tag}"
        RECIPES[_nm] = ("Buildings", (lambda s=_span, w=_w, nm=_nm: make_bridge(nm, s, w)))
RECIPES["BLD_Bridge_10w"] = ("Buildings", lambda: make_bridge("BLD_Bridge_10w", 10, 6.4))
RECIPES["BLD_Bridge_18w"] = ("Buildings", lambda: make_bridge("BLD_Bridge_18w", 18, 6.4))


@recipe("Buildings", "BLD_CanalSteps")
def r_steps():
    """河埠头：后沿(+Y)接岸顶 z=0，向水(-Y)下到河底 -1.6。宽 4.2。"""
    mb = K.MB()
    n = 5
    for k in range(n):
        ya = 1.2 - 2.4 * k / n
        yb = 1.2 - 2.4 * (k + 1) / n
        top = -1.6 * (k + 0.5) / n
        mb.box(-2.1, yb, -1.8, 2.1, ya, top, "M_Stone_Base" if k % 2 else "M_Bank_Stone")
    mb.box(-2.4, -1.2, -1.8, -2.1, 1.2, 0.15, "M_Bank_Stone")
    mb.box(2.1, -1.2, -1.8, 2.4, 1.2, 0.15, "M_Bank_Stone")
    mb.to_object("BLD_CanalSteps")
    col = K.MB()
    col.prism([(1.3, 0.0), (-1.3, -1.65), (1.3, -1.65)], "x", -2.1, 2.1, "M_Stone_Base")
    col.to_object("COL_Steps")


# ====================================================================== 道具（通用）
@recipe("Props", "PROP_Tree_Camphor")
def r_tree_camphor():
    rng = random.Random(7)
    mb = K.MB()
    mb.cyl(0, 0, 0, 3.4, 0.38, "M_Bark", seg=7, r_top=0.26)
    mb.prism([(0.1, 2.6), (1.4, 4.4), (1.2, 4.6), (-0.1, 2.9)], "y", -0.15, 0.15, "M_Bark")
    mb.prism([(-0.1, 2.4), (-1.5, 4.0), (-1.3, 4.25), (0.1, 2.8)], "y", -0.15, 0.15, "M_Bark")
    for x, y, z, r in ((0, 0, 5.4, 2.6), (1.6, 0.6, 4.7, 2.0), (-1.5, -0.4, 4.6, 2.1), (0.3, -1.4, 4.9, 1.9), (-0.4, 1.3, 6.2, 1.8)):
        mb.ico(x, y, z, r, "M_Leaf", 1.0, 1.0, 0.78)
    mb.to_object("PROP_Tree_Camphor")
    col = K.MB()
    col.box(-0.35, -0.35, 0, 0.35, 0.35, 3.2, "M_Bark")
    col.to_object("COL_Trunk")


@recipe("Props", "PROP_Tree_Small")
def r_tree_small():
    mb = K.MB()
    mb.cyl(0, 0, 0, 2.2, 0.17, "M_Bark", seg=6, r_top=0.12)
    mb.ico(0, 0, 2.9, 1.4, "M_Leaf", 1.0, 1.0, 0.9)
    mb.ico(0.5, 0.3, 3.7, 1.0, "M_Leaf", 1.0, 1.0, 0.9)
    mb.to_object("PROP_Tree_Small")
    col = K.MB()
    col.box(-0.17, -0.17, 0, 0.17, 0.17, 2.0, "M_Bark")
    col.to_object("COL_Trunk")


@recipe("Props", "PROP_ROC_TelegraphPole")
def r_pole():
    """民国电线杆。横担两端与中部的瓷瓶顶点供团结拉线：局部 (±0.8, 6.75, 0)、(±0.35, 6.75, 0)。"""
    mb = K.MB()
    mb.frustum((-0.13, -0.13, 0.13, 0.13), (-0.09, -0.09, 0.09, 0.09), 0, 7.2, "M_Wood_Dark")
    mb.box(-0.95, -0.06, 6.5, 0.95, 0.06, 6.62, "M_Wood_Dark")
    for x in (-0.8, -0.35, 0.35, 0.8):
        mb.cyl(x, 0, 6.62, 6.78, 0.05, "M_Paper", seg=6)
    mb.prism([(-0.6, 6.2), (-0.05, 6.5), (-0.05, 6.4)], "y", -0.03, 0.03, "M_Wood_Dark")
    mb.prism([(0.6, 6.2), (0.05, 6.4), (0.05, 6.5)], "y", -0.03, 0.03, "M_Wood_Dark")
    mb.to_object("PROP_ROC_TelegraphPole")
    col = K.MB()
    col.box(-0.13, -0.13, 0, 0.13, 0.13, 6.5, "M_Wood_Dark")
    col.to_object("COL_Pole")


# ====================================================================== 民国建筑（BLD_ROC_*）
def plinth(mb, x0, y0, x1, y1, h=0.35, g=0.15, mat="M_Stone_Base"):
    mb.box(x0 - g, y0 - g, -0.3, x1 + g, y1 + g, h, mat)


@recipe("Buildings", "BLD_ROC_House_S_A")
def r_house_s_a():
    """单层三开间民居，前檐廊。10 x 7。"""
    mb = K.MB()
    x0, x1, y0, y1, h, z0 = -5, 5, -3.5, 3.5, 3.6, 0.35
    plinth(mb, x0, y0, x1, y1, z0)
    mb.box(x0, y0 + 1.1, z0, x1, y1, h, "M_Plaster")
    mb.box(x0 - 0.02, y0 + 1.1, z0, x1 + 0.02, y1 + 0.02, 1.1, "M_Plaster_Lower")
    for xa in (x0, x1 - 0.4):
        mb.box(xa, y0, z0, xa + 0.4, y0 + 1.1, h, "M_Plaster")
    mb.box(x0 + 0.4, y0 + 1.04, z0, x1 - 0.4, y0 + 1.12, h, "M_Wood")
    mb.door(0, 1.8, 2.4, y0 + 1.04, z0)
    for x in (-3.0, 3.0):
        mb.window(x, 2.0, 1.6, 1.1, y0 + 1.04)
    for x in (-1.6, 1.6):
        mb.box(x - 0.12, y0 + 0.15, z0, x + 0.12, y0 + 0.39, h, "M_Wood_Dark")
    mb.window_x(0.8, 2.2, 1.0, 0.8, x1, 1)
    mb.gable_roof(x0, x1, y0, y1, h, 2.1, ohf=0.6, ohs=0.3)
    mb.to_object("BLD_ROC_House_S_A")


@recipe("Buildings", "BLD_ROC_House_S_B")
def r_house_s_b():
    """单层民居，青砖下碱 + 马头墙（封火山墙）。10 x 7。"""
    mb = K.MB()
    x0, x1, y0, y1, h, z0 = -5, 5, -3.5, 3.5, 3.5, 0.3
    plinth(mb, x0, y0, x1, y1, z0)
    mb.box(x0, y0, z0, x1, y1, h, "M_Plaster")
    mb.box(x0 - 0.03, y0 - 0.03, z0, x1 + 0.03, y1 + 0.03, 1.3, "M_Brick_Grey")
    mb.door(-1.8, 1.5, 2.3, y0, z0)
    mb.box(-2.9, y0 - 0.25, 2.75, -0.7, y0, 2.9, "M_Roof_Ridge")        # 门罩
    for x in (1.2, 3.4):
        mb.window(x, 2.1, 1.1, 0.9, y0)
    mb.gable_roof(x0 + 0.4, x1 - 0.4, y0, y1, h, 2.0, ohf=0.55, ohs=0.0)
    mb.mating_wall(x0 + 0.4, y0, y1, h, 2.0, outward=1)
    mb.mating_wall(x1 - 0.4, y0, y1, h, 2.0, outward=-1)
    mb.to_object("BLD_ROC_House_S_B")


@recipe("Buildings", "BLD_ROC_House_L_A")
def r_house_l_a():
    """两层木楼民居，前有腰檐。12 x 8。"""
    mb = K.MB()
    x0, x1, y0, y1, z0 = -6, 6, -4, 4, 0.35
    plinth(mb, x0, y0, x1, y1, z0)
    mb.box(x0, y0, z0, x1, y1, 3.4, "M_Plaster")
    mb.box(x0 + 0.3, y0 - 0.04, z0, x1 - 0.3, y0 + 0.02, 3.3, "M_Wood")
    mb.door(0, 2.0, 2.5, y0 - 0.04, z0)
    for x in (-3.8, 3.8):
        mb.window(x, 1.9, 2.0, 1.1, y0 - 0.04)
    mb.shed_roof(x0 - 0.2, x1 + 0.2, y0 + 0.1, y0 - 0.9, 3.75, 3.1)
    mb.box(x0, y0 + 0.3, 3.4, x1, y1, 6.0, "M_Plaster")
    mb.box(x0 + 0.3, y0 + 0.26, 3.6, x1 - 0.3, y0 + 0.32, 5.9, "M_Wood")
    for x in (-4.0, -1.35, 1.35, 4.0):
        mb.window(x, 4.75, 1.5, 1.0, y0 + 0.26)
    mb.gable_fill(x0, x1, y0 + 0.3, y1, 6.0, 2.3)
    mb.gable_roof(x0, x1, y0 + 0.3, y1, 6.0, 2.3, ohf=0.6, ohs=0.3)
    mb.to_object("BLD_ROC_House_L_A")


@recipe("Buildings", "BLD_ROC_House_L_B")
def r_house_l_b():
    """两层民居，二楼挑廊栏杆 + 马头墙。12 x 8。"""
    mb = K.MB()
    x0, x1, y0, y1, z0 = -6, 6, -4, 4, 0.35
    plinth(mb, x0, y0, x1, y1, z0)
    mb.box(x0, y0 + 0.9, z0, x1, y1, 6.1, "M_Plaster")
    mb.box(x0 - 0.03, y0 + 0.87, z0, x1 + 0.03, y1 + 0.03, 1.2, "M_Brick_Grey")
    mb.door(-2.2, 1.6, 2.4, y0 + 0.87, z0)
    mb.door(2.2, 1.6, 2.4, y0 + 0.87, z0, mat="M_Wood")
    mb.box(x0 + 0.4, y0, 3.2, x1 - 0.4, y0 + 0.9, 3.4, "M_Wood")             # 挑廊楼板
    for x in (x0 + 0.5, -2.0, 2.0, x1 - 0.5):
        mb.box(x - 0.1, y0 + 0.1, z0, x + 0.1, y0 + 0.3, 3.2, "M_Wood_Dark")
    mb.railing(x0 + 0.4, x1 - 0.4, y0 + 0.08, 3.4)
    for x in (-3.6, 0, 3.6):
        mb.window(x, 4.7, 1.4, 1.1, y0 + 0.87)
    mb.gable_roof(x0 + 0.4, x1 - 0.4, y0, y1, 6.1, 2.4, ohf=0.5, ohs=0.0)
    mb.mating_wall(x0 + 0.4, y0, y1, 6.1, 2.4, outward=1)
    mb.mating_wall(x1 - 0.4, y0, y1, 6.1, 2.4, outward=-1)
    mb.to_object("BLD_ROC_House_L_B")


@recipe("Buildings", "BLD_ROC_Shop_A")
def r_shop_a():
    """两层店屋，底层排门板开铺，二层挑出，竖招牌。6 x 10。"""
    mb = K.MB()
    x0, x1, y0, y1, z0 = -3, 3, -5, 5, 0.25
    plinth(mb, x0, y0, x1, y1, z0, g=0.05)
    mb.box(x0, y0 + 0.8, z0, x1, y1, 3.3, "M_Plaster")
    for xa in (x0, x1 - 0.25):
        mb.box(xa, y0, z0, xa + 0.25, y0 + 0.8, 3.3, "M_Plaster")
    mb.box(x0 + 0.25, y0 + 0.75, z0, x1 - 0.25, y0 + 0.8, 3.2, "M_Window")          # 铺内暗面
    for i in range(6):
        xa = x0 + 0.3 + i * 0.36
        mb.box(xa, y0 + 0.62, z0, xa + 0.34, y0 + 0.7, 3.1, "M_Wood")                  # 门板（左半）
    mb.box(x0 + 0.3, y0 + 0.1, z0, x1 - 0.3, y0 + 0.55, 1.05, "M_Wood_Dark")          # 柜台
    mb.shed_roof(x0 - 0.1, x1 + 0.1, y0 + 0.3, y0 - 0.7, 3.55, 3.0)
    mb.box(x0, y0 + 0.3, 3.3, x1, y1, 6.0, "M_Wood")
    for x in (-1.3, 1.3):
        mb.window(x, 4.7, 1.3, 1.0, y0 + 0.3)
    mb.gable_roof(x0, x1, y0 + 0.3, y1, 6.0, 2.5, ohf=0.5, ohs=0.25)
    mb.box(2.35, y0 - 0.45, 1.6, 2.85, y0 - 0.33, 4.6, "M_Sign")                    # 竖招牌
    mb.box(2.55, y0 - 0.4, 4.6, 2.65, y0 + 0.3, 4.7, "M_Wood_Dark")
    mb.to_object("BLD_ROC_Shop_A")


@recipe("Buildings", "BLD_ROC_Shop_B")
def r_shop_b():
    """一层半店屋（带阁楼），横匾招牌，马头墙。6 x 10。"""
    mb = K.MB()
    x0, x1, y0, y1, z0 = -3, 3, -5, 5, 0.25
    plinth(mb, x0, y0, x1, y1, z0, g=0.05)
    mb.box(x0, y0, z0, x1, y1, 4.4, "M_Plaster")
    mb.box(x0 + 0.3, y0 - 0.04, z0, x1 - 0.3, y0 + 0.02, 2.9, "M_Window")
    for i in range(4):
        xa = x1 - 0.3 - (i + 1) * 0.4
        mb.box(xa, y0 - 0.12, z0, xa + 0.38, y0 - 0.04, 2.8, "M_Wood")
    mb.box(x0 + 0.4, y0 - 0.18, 3.05, x1 - 0.4, y0 - 0.04, 3.6, "M_Sign")              # 横招牌
    mb.window(0, 3.95, 1.6, 0.5, y0)
    mb.gable_roof(x0 + 0.3, x1 - 0.3, y0, y1, 4.4, 2.6, ohf=0.6, ohs=0.0)
    mb.mating_wall(x0 + 0.3, y0, y1, 4.4, 2.6, outward=1)
    mb.mating_wall(x1 - 0.3, y0, y1, 4.4, 2.6, outward=-1)
    mb.to_object("BLD_ROC_Shop_B")


@recipe("Buildings", "BLD_ROC_ShopWest")
def r_shop_west():
    """民国西式立面店屋：女儿墙山花、拱窗、壁柱、招牌带。8 x 12。"""
    mb = K.MB()
    x0, x1, y0, y1 = -4, 4, -6, 6
    mb.box(x0, y0, -0.3, x1, y1, 6.8, "M_Brick_Grey")
    yf = y0 - 0.25
    mb.box(x0, yf, -0.3, x1, y0, 8.3, "M_Plaster")
    mb.box(-2.0, yf, 8.3, 2.0, y0, 9.1, "M_Plaster")
    mb.box(-0.8, yf, 9.1, 0.8, y0, 9.5, "M_Plaster")
    mb.box(x0 - 0.15, yf - 0.15, 6.55, x1 + 0.15, y0 + 0.05, 6.85, "M_Stone_Base")      # 檐口线脚
    mb.box(x0 - 0.1, yf - 0.1, 8.3, x1 + 0.1, y0 + 0.05, 8.45, "M_Stone_Base")
    for x in (x0, -1.33, 1.33, x1):
        mb.box(x - 0.2, yf - 0.12, -0.3, x + 0.2, yf, 8.3, "M_Plaster")                 # 壁柱
    for x in (-2.66, 0.0, 2.66):
        mb.box(x - 1.0, yf - 0.05, 0.0, x + 1.0, yf + 0.01, 2.9, "M_Window")            # 底层铺面
        mb.arch_window(x, 4.0, 1.0, 1.9, yf)
    mb.box(x0 + 0.3, yf - 0.1, 3.05, x1 - 0.3, yf, 3.65, "M_Sign")
    mb.gable_roof_y(x0, x1, y0, y1, 6.8, 1.4, ohf=0.3, ohs=0.0, ridge=False)
    mb.to_object("BLD_ROC_ShopWest")


def courtyard_house(mb, x0, x1, y0, y1, h, rise, front_y, mat="M_Plaster", wood_front=True, z0=0.4, inset=0.0, ohs=0.3):
    """院内一栋（屋脊沿 X），front_y 表示正面在 y0 还是 y1。"""
    plinth(mb, x0, y0, x1, y1, z0, g=0.1)
    mb.box(x0, y0, z0, x1, y1, h, mat)
    yf = y0 if front_y < 0 else y1
    if wood_front:
        if front_y < 0:
            mb.box(x0 + 0.3, yf - 0.05, z0, x1 - 0.3, yf + 0.01, h - 0.1, "M_Wood")
        else:
            mb.box(x0 + 0.3, yf - 0.01, z0, x1 - 0.3, yf + 0.05, h - 0.1, "M_Wood")
    mb.gable_roof(x0 + inset, x1 - inset, y0, y1, h, rise, ohf=0.6, ohs=ohs)


@recipe("Buildings", "BLD_ROC_Courtyard")
def r_courtyard():
    """三合院：正屋 + 两厢 + 前院墙门楼。20 x 18。"""
    mb = K.MB()
    mb.box(-9.6, -8.6, -0.1, 9.6, 2.0, 0.08, "M_Road_Stone")
    # 正屋（后），正面朝院（-Y）
    courtyard_house(mb, -10, 10, 2, 9, 3.9, 2.4, -1, inset=0.4, ohs=0.0)
    mb.door(0, 1.8, 2.5, 2 - 0.05, 0.4)
    for x in (-6, -3, 3, 6):
        mb.window(x, 2.2, 1.6, 1.1, 2 - 0.05)
    mb.mating_wall(-10, 2, 9, 3.9, 2.4, t=0.4, outward=-1)
    mb.mating_wall(10, 2, 9, 3.9, 2.4, t=0.4, outward=1)
    # 两厢（屋脊沿 Y），面朝院内
    for sx in (-1, 1):
        xa, xb = (-10, -5.4) if sx < 0 else (5.4, 10)
        plinth(mb, xa, -6, xb, 2, 0.35, g=0.05)
        mb.box(xa, -6, 0.35, xb, 2, 3.3, "M_Plaster")
        xf = xb if sx < 0 else xa
        mb.box(xf - 0.01 if sx < 0 else xf - 0.05, -5.6, 0.35, xf + 0.05 if sx < 0 else xf + 0.01, 1.6, 3.2, "M_Wood")
        mb.gable_roof_y(xa, xb, -6, 2, 3.3, 1.7, ohf=0.5, ohs=0.25)
    # 院墙 + 门楼
    mb.box(-10, -9, -0.2, -1.8, -8.6, 2.9, "M_Plaster")
    mb.box(1.8, -9, -0.2, 10, -8.6, 2.9, "M_Plaster")
    mb.box(-10.1, -9.1, 2.9, -1.8, -8.5, 3.1, "M_Roof_Ridge")
    mb.box(1.8, -9.1, 2.9, 10.1, -8.5, 3.1, "M_Roof_Ridge")
    for xa, xb in ((-10, -9.6), (9.6, 10)):
        mb.box(xa, -8.6, -0.2, xb, -6, 2.9, "M_Plaster")
    mb.box(-1.8, -9.3, -0.2, 1.8, -8.3, 3.5, "M_Plaster")
    mb.door(0, 1.5, 2.5, -9.3, 0.1)
    mb.gable_roof(-2.2, 2.2, -9.4, -8.2, 3.5, 0.8, ohf=0.4, ohs=0.25)
    mb.to_object("BLD_ROC_Courtyard")


@recipe("Buildings", "BLD_ROC_HallSmall")
def r_hall_small():
    """一进祠第（布政司祠 / 世大夫祠 / 状元第 / 都堂第共用）：门厅 + 院 + 正厅。14 x 20。"""
    mb = K.MB()
    x0, x1 = -7, 7
    # 门厅
    plinth(mb, x0, -10, x1, -5, 0.45)
    mb.box(x0, -10, 0.45, x1, -5, 4.2, "M_Plaster")
    mb.box(x0 - 0.03, -10.03, 0.45, x1 + 0.03, -4.97, 1.4, "M_Brick_Grey")
    mb.door(0, 2.4, 3.0, -10.03, 0.45, mat="M_Red_Lacquer")
    mb.box(-1.3, -10.12, 3.55, 1.3, -10.02, 4.05, "M_Plaque")
    for x in (-4.5, 4.5):
        mb.window(x, 2.4, 1.0, 1.0, -10.03)
    mb.gable_roof(x0 + 0.4, x1 - 0.4, -10, -5, 4.2, 1.9, ohf=0.6, ohs=0.0)
    mb.mating_wall(x0 + 0.4, -10, -5, 4.2, 1.9)
    mb.mating_wall(x1 - 0.4, -10, -5, 4.2, 1.9, outward=-1)
    # 院墙 + 院
    for xa, xb in ((x0, x0 + 0.4), (x1 - 0.4, x1)):
        mb.box(xa, -5, -0.2, xb, 2.2, 4.0, "M_Plaster")
        mb.box(xa - 0.1, -5, 4.0, xb + 0.1, 2.2, 4.2, "M_Roof_Ridge")
    mb.box(x0 + 0.4, -5, -0.1, x1 - 0.4, 2.2, 0.1, "M_Road_Stone")
    # 正厅（前檐柱廊）
    plinth(mb, x0, 2.2, x1, 10, 0.65)
    mb.box(x0, 3.6, 0.65, x1, 10, 4.9, "M_Plaster")
    mb.box(x0 + 0.3, 3.55, 0.65, x1 - 0.3, 3.62, 4.8, "M_Wood")
    for x in (-5.4, -2.7, 0, 2.7, 5.4):
        mb.cyl(x, 2.6, 0.65, 4.9, 0.17, "M_Red_Lacquer", seg=8)
    mb.door(0, 2.2, 3.0, 3.55, 0.65)
    mb.gable_roof(x0, x1, 2.2, 10, 4.9, 2.9, ohf=0.9, ohs=0.4)
    mb.to_object("BLD_ROC_HallSmall")


@recipe("Buildings", "BLD_ROC_AncestralHall")
def r_ancestral():
    """王氏祖祠（三进）：门厅 + 廊庑 + 正厅（歇山） + 后堂。20 x 36。民国时是旧祠：积灰、褪色由材质负责。"""
    mb = K.MB()
    x0, x1 = -10, 10
    # 门厅
    plinth(mb, x0, -18, x1, -11, 0.55)
    mb.box(x0, -18, 0.55, x1, -11, 4.8, "M_Plaster")
    mb.box(x0 - 0.03, -18.03, 0.55, x1 + 0.03, -10.97, 1.6, "M_Brick_Grey")
    mb.door(0, 2.8, 3.4, -18.03, 0.55, mat="M_Red_Lacquer")
    for x in (-4.6, 4.6):
        mb.door(x, 1.6, 2.6, -18.03, 0.55, mat="M_Red_Lacquer")
    mb.box(-1.8, -18.14, 4.05, 1.8, -18.02, 4.65, "M_Plaque")
    mb.gable_roof(x0 + 0.45, x1 - 0.45, -18, -11, 4.8, 2.4, ohf=0.8, ohs=0.0)
    mb.mating_wall(x0 + 0.45, -18, -11, 4.8, 2.4, t=0.45)
    mb.mating_wall(x1 - 0.45, -18, -11, 4.8, 2.4, t=0.45, outward=-1)
    # 廊庑（两侧单坡）
    for sx in (-1, 1):
        xo, xi = (x0, x0 + 2.6) if sx < 0 else (x1, x1 - 2.6)
        xa, xb = min(xo, xi), max(xo, xi)
        mb.box(xo - 0.0 if sx < 0 else xo - 0.45, -11, -0.2, xo + 0.45 if sx < 0 else xo, 10, 4.2, "M_Plaster")
        mb.box(xa, -11, -0.2, xb, 10, 0.35, "M_Stone_Base")
        for y in range(-10, 10, 3):
            mb.box(xi - 0.12, y - 0.12, 0.35, xi + 0.12, y + 0.12, 3.2, "M_Wood_Dark")
        mb.shed_roof_y(-11, 10, xo, xi - sx * 0.6, 4.4, 3.2)
    mb.box(x0 + 2.6, -11, -0.1, x1 - 2.6, 10, 0.1, "M_Road_Stone")
    # 正厅月台 + 正厅（歇山近似：四坡 + 脊）
    mb.box(-6.5, -6.0, -0.2, 6.5, -2.6, 0.9, "M_Stone_Base")
    for k in range(3):
        mb.box(-2.0, -6.9 + k * 0.3, -0.2, 2.0, -6.0, 0.3 * (k + 1), "M_Stone_Base")
    plinth(mb, -7.4, -2.6, 7.4, 7, 0.9, g=0.1)
    mb.box(-7.0, -1.2, 0.9, 7.0, 6.6, 5.8, "M_Plaster")
    mb.box(-6.7, -1.26, 0.9, 6.7, -1.18, 5.6, "M_Wood")
    for x in (-6.4, -3.6, -1.2, 1.2, 3.6, 6.4):
        mb.cyl(x, -2.1, 0.9, 5.8, 0.2, "M_Red_Lacquer", seg=8)
    mb.door(0, 2.6, 3.4, -1.26, 0.9)
    mb.box(-1.6, -2.3, 4.7, 1.6, -2.2, 5.3, "M_Plaque")
    mb.hip_roof(-8.6, -3.6, 8.6, 8.0, 5.6, 3.3, 3.2)
    mb.gable_fill(-5.4, 5.4, -1.2, 6.6, 7.4, 1.5, "M_Roof_Tile")
    # 后堂
    plinth(mb, x0, 10, x1, 18, 0.6)
    mb.box(x0, 10, 0.6, x1, 18, 5.0, "M_Plaster")
    mb.box(x0 + 0.5, 9.95, 0.6, x1 - 0.5, 10.02, 4.9, "M_Wood")
    mb.gable_roof(x0 + 0.45, x1 - 0.45, 10, 18, 5.0, 2.8, ohf=0.7, ohs=0.0)
    mb.mating_wall(x0 + 0.45, 10, 18, 5.0, 2.8, t=0.45)
    mb.mating_wall(x1 - 0.45, 10, 18, 5.0, 2.8, t=0.45, outward=-1)
    # 门前旗杆石（功名旗杆）
    for x in (-6.5, 6.5):
        mb.box(x - 0.5, -19.8, -0.1, x + 0.5, -19.0, 0.5, "M_Stone_Base")
        mb.cyl(x, -19.4, 0.5, 9.0, 0.12, "M_Wood_Dark", seg=6, r_top=0.08)
        mb.box(x - 0.35, -19.75, 6.0, x + 0.35, -19.05, 6.25, "M_Wood_Dark")
    mb.to_object("BLD_ROC_AncestralHall")


@recipe("Buildings", "BLD_ROC_Temple")
def r_temple():
    """汤和庙：红墙山门 + 院内香炉 + 重檐正殿。16 x 22。"""
    mb = K.MB()
    x0, x1 = -8, 8
    plinth(mb, x0, -11, x1, -7, 0.4)
    mb.box(x0, -11, 0.4, x1, -7, 4.4, "M_Wall_Red")
    mb.box(-1.4, -11.05, 0.4, 1.4, -10.95, 3.4, "M_Window")
    mb.box(-1.6, -11.15, 3.5, 1.6, -11.02, 4.1, "M_Plaque")
    for x in (-5, 5):
        mb.box(x - 0.8, -11.05, 1.4, x + 0.8, -10.98, 2.6, "M_Window")
    mb.hip_roof(x0 - 0.6, -11.8, x1 + 0.6, -6.2, 4.3, 1.9, 2.0)
    for xa, xb in ((x0, x0 + 0.4), (x1 - 0.4, x1)):
        mb.box(xa, -7, -0.2, xb, 11, 3.8, "M_Wall_Red")
        mb.box(xa - 0.1, -7, 3.8, xb + 0.1, 11, 4.0, "M_Roof_Ridge")
    mb.box(x0 + 0.4, 10.6, -0.2, x1 - 0.4, 11, 3.8, "M_Wall_Red")
    mb.box(x0 + 0.4, -7, -0.1, x1 - 0.4, 10.6, 0.1, "M_Road_Stone")
    # 香炉
    mb.box(-0.7, -3.7, 0.1, 0.7, -2.3, 0.6, "M_Stone_Base")
    mb.box(-0.5, -3.5, 0.6, 0.5, -2.5, 1.5, "M_Metal")
    mb.hip(-0.75, -3.75, 0.75, -2.25, 1.5, 0.6, 0.75, "M_Metal")
    # 正殿：重檐
    plinth(mb, -6.5, 1.0, 6.5, 10.4, 0.8)
    mb.box(-6.0, 2.6, 0.8, 6.0, 10.0, 4.4, "M_Wall_Red")
    mb.box(-5.7, 2.55, 0.8, 5.7, 2.62, 4.2, "M_Wood")
    for x in (-5.6, -2.8, 0, 2.8, 5.6):
        mb.cyl(x, 1.6, 0.8, 4.2, 0.18, "M_Red_Lacquer", seg=8)
    mb.door(0, 2.4, 3.0, 2.55, 0.8)
    mb.hip_roof(-7.4, 0.4, 7.4, 11.0, 4.0, 1.1, 1.4, curl=False)
    mb.box(-4.8, 3.6, 4.4, 4.8, 9.2, 6.4, "M_Wall_Red")
    mb.hip_roof(-6.2, 2.2, 6.2, 10.6, 6.2, 2.6, 2.6)
    mb.to_object("BLD_ROC_Temple")


@recipe("Buildings", "BLD_ROC_Granary")
def r_granary():
    """粮仓：高台基、厚墙、小高窗、屋脊气楼。20 x 12。"""
    mb = K.MB()
    x0, x1, y0, y1 = -10, 10, -6, 6
    plinth(mb, x0, y0, x1, y1, 0.9, g=0.2)
    mb.box(x0, y0, 0.9, x1, y1, 5.0, "M_Plaster")
    for x in range(-10, 11, 4):
        mb.box(x - 0.15, y0 - 0.08, 0.9, x + 0.15, y0, 5.0, "M_Wood_Dark")
    for x in (-5, 5):
        mb.door(x, 2.2, 2.6, y0 - 0.08, 0.9, mat="M_Wood")
        mb.prism([(y0 - 0.2, 0.9), (y0 - 1.8, -0.05), (y0 - 0.2, -0.05)], "x", x - 1.2, x + 1.2, "M_Stone_Base")
    for x in (-8, -2, 2, 8):
        mb.window(x, 4.3, 0.8, 0.45, y0 - 0.08)
    mb.gable_roof(x0, x1, y0, y1, 5.0, 3.0, ohf=0.8, ohs=0.4)
    for x in (-5, 5):
        mb.box(x - 1.0, -0.8, 8.0, x + 1.0, 0.8, 8.8, "M_Wood_Dark")
        mb.gable_roof(x - 1.3, x + 1.3, -1.0, 1.0, 8.8, 0.6, ohf=0.2, ohs=0.15, ridge=False)
    mb.to_object("BLD_ROC_Granary")


def gate_tower(mb, half, hd, ncol, h1, h2):
    """城楼：底层柱廊可穿行（只有柱子），上层木构，重檐四坡。原点在城墙走道面。"""
    mb.box(-half, -hd, 0, half, hd, 0.2, "M_Stone_Base")
    xs = [-half + 0.4 + (2 * half - 0.8) * i / (ncol - 1) for i in range(ncol)]
    for x in xs:
        for y in (-hd + 0.4, hd - 0.4):
            mb.cyl(x, y, 0.2, h1, 0.18, "M_Red_Lacquer", seg=8)
    mb.box(-half - 0.2, -hd - 0.2, h1, half + 0.2, hd + 0.2, h1 + 0.3, "M_Wood")
    mb.hip_roof(-half - 1.1, -hd - 1.1, half + 1.1, hd + 1.1, h1 - 0.2, 1.0, 1.2, curl=True)
    zb = h1 + 0.3
    mb.box(-half + 0.8, -hd + 0.6, zb, half - 0.8, hd - 0.6, zb + h2, "M_Wood")
    for x in xs[1:-1]:
        mb.window(x, zb + h2 * 0.55, 1.2, h2 * 0.45, -hd + 0.6)
    mb.railing(-half - 0.1, half + 0.1, -hd - 0.1, zb, 0.85, axis="x")
    mb.box(-1.3, -hd + 0.5, zb + h2 * 0.15, 1.3, -hd + 0.58, zb + h2 * 0.15 + 0.7, "M_Plaque")
    mb.hip_roof(-half - 0.7, -hd - 0.7, half + 0.7, hd + 0.7, zb + h2 - 0.15, 2.4 + half * 0.08, half * 0.45)


@recipe("Buildings", "BLD_ROC_GateTower")
def r_gate_tower():
    mb = K.MB()
    gate_tower(mb, 6.0, 3.2, 4, 3.4, 2.6)
    mb.to_object("BLD_ROC_GateTower")


@recipe("Buildings", "BLD_ROC_HuanhaiLou")
def r_huanhai():
    """环海楼：东门城楼，堡内最大（史载占地七百余平方米，这里按游戏尺度 20 x 8.8）。"""
    mb = K.MB()
    gate_tower(mb, 10.0, 4.4, 6, 3.9, 3.1)
    mb.to_object("BLD_ROC_HuanhaiLou")


@recipe("Buildings", "BLD_ROC_Checkpoint")
def r_checkpoint():
    """日伪哨卡（1941）：沙袋工事、岗亭、拒马、旗杆。8 x 8。只在民国场景出现。"""
    mb = K.MB()
    rng = random.Random(41)

    def bags(x0, x1, y0, y1):
        along_x = (x1 - x0) >= (y1 - y0)
        L = (x1 - x0) if along_x else (y1 - y0)
        for row in range(3):
            n = int(L / 0.62)
            off = 0.31 if row % 2 else 0
            for i in range(n):
                a = (x0 if along_x else y0) + off + i * 0.62
                b = a + 0.58
                if b > (x1 if along_x else y1):
                    break
                z0 = row * 0.32
                if along_x:
                    mb.box(a, y0, z0, b, y1, z0 + 0.3, "M_Sandbag")
                else:
                    mb.box(x0, a, z0, x1, b, z0 + 0.3, "M_Sandbag")

    bags(-4, 4, 3.3, 3.9)
    bags(-4, -3.4, -1.5, 3.3)
    bags(3.4, 4, -1.5, 3.3)
    bags(-4, -1.2, -3.9, -3.3)
    # 岗亭
    mb.box(0.8, 0.4, 0, 2.8, 2.4, 2.4, "M_Wood")
    mb.box(1.2, 0.36, 1.0, 2.4, 0.42, 1.6, "M_Window")
    mb.shed_roof(0.6, 3.0, 2.6, 0.2, 2.75, 2.45, "M_Metal_Roof")
    # 拒马 / 栏杆
    for x in (1.0, 3.8):
        mb.box(x - 0.08, -3.9, 0, x + 0.08, -3.7, 1.1, "M_Wood_Dark")
    mb.box(-0.6, -3.86, 0.95, 3.9, -3.74, 1.05, "M_Paper")
    # 旗杆 + 旗（布面图案用贴图，这里只给形状）
    mb.cyl(-3.0, 2.6, 0, 6.5, 0.06, "M_Wood_Dark", seg=6)
    mb.box(-2.95, 2.58, 5.4, -1.5, 2.62, 6.3, "M_Flag")
    mb.to_object("BLD_ROC_Checkpoint")


@recipe("Buildings", "BLD_ROC_Dock")
def r_dock():
    """永强码头（民国）：木栈台伸入海面、铁皮仓棚、系缆桩、货箱。20 x 18，正面(-Y)朝海。"""
    mb = K.MB()
    mb.box(-10, 6, -0.6, 10, 9, 0.3, "M_Stone_Base")
    mb.box(-10, -9, 0.12, 10, 6, 0.3, "M_Wood")
    for y in (-8.6, -5.0, -1.4, 2.2, 5.6):
        for x in (-9.6, -4.8, 0, 4.8, 9.6):
            mb.box(x - 0.16, y - 0.16, -3.2, x + 0.16, y + 0.16, 0.12, "M_Wood_Dark")
    mb.box(-10, -9, 0.3, 10, -8.8, 0.45, "M_Wood_Dark")
    # 仓棚
    mb.box(-9.2, 0.2, 0.3, -1.0, 5.8, 3.6, "M_Wood")
    mb.box(-6.4, 0.14, 0.3, -3.8, 0.22, 2.9, "M_Window")
    mb.gable_roof(-9.2, -1.0, 0.2, 5.8, 3.6, 1.2, ohf=0.5, ohs=0.3, mat="M_Metal_Roof", ridge=False)
    # 系缆桩
    for x in (-7, -2, 3, 8):
        mb.cyl(x, -8.4, 0.3, 0.9, 0.18, "M_Metal", seg=8)
    # 货箱堆
    for x, y, z in ((2, 1, 0.3), (3.3, 1, 0.3), (2.6, 2.3, 0.3), (2.6, 1.6, 1.3), (6, 3, 0.3)):
        mb.box(x - 0.6, y - 0.6, z, x + 0.6, y + 0.6, z + 1.0, "M_Wood")
    # 路灯
    mb.cyl(8.5, 4.5, 0.3, 4.6, 0.07, "M_Metal", seg=6)
    mb.box(8.3, 4.3, 4.6, 8.7, 4.7, 5.0, "M_Paper")
    mb.to_object("BLD_ROC_Dock")


@recipe("Buildings", "BLD_ROC_SaltShed")
def r_saltshed():
    """盐场灶舍：敞棚、茅草顶、卤池、砖灶与烟囱。12 x 8。"""
    mb = K.MB()
    for x in (-5.7, -1.9, 1.9, 5.7):
        for y in (-3.7, 3.7):
            mb.box(x - 0.12, y - 0.12, 0, x + 0.12, y + 0.12, 2.8, "M_Wood_Dark")
    mb.gable_roof(-6, 6, -4, 4, 2.8, 1.8, ohf=0.6, ohs=0.4, mat="M_Thatch", ridge_mat="M_Thatch", curl=False)
    mb.box(-4.8, -2.4, 0, -1.2, 2.4, 0.8, "M_Wood_Dark")
    mb.box(-4.6, -2.2, 0.6, -1.4, 2.2, 0.78, "M_Salt")
    mb.box(0.8, -1.5, 0, 4.2, 1.5, 1.2, "M_Brick_Red")
    mb.cyl(2.5, 0, 1.2, 1.5, 1.1, "M_Metal", seg=10)
    mb.box(3.4, 0.6, 0, 4.0, 1.2, 4.6, "M_Brick_Red")
    mb.to_object("BLD_ROC_SaltShed")


# ====================================================================== 环境（ENV_*，读布局）
def u2b(x, z, y=0.0):
    return (-x, -z, y)


ROAD_MAT = {"main": "M_Road_Stone", "street": "M_Road_Stone", "plaza": "M_Road_Stone", "outer_main": "M_Road_Stone",
            "lane": "M_Road_Earth", "path": "M_Road_Earth", "ring": "M_Road_Earth", "outer": "M_Road_Earth"}
ROAD_PRI = {"plaza": 0, "main": 1, "outer_main": 1, "street": 2, "ring": 3, "lane": 4, "path": 5, "outer": 6}


class RawMesh:
    """直接给定朝向的面（地形这类开放网格用，不做法线重算）。"""

    def __init__(self):
        self.v, self.f, self.n, self.fm, self.mats = [], [], [], [], []

    def mi(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def quad(self, pts, normal, mat):
        b = len(self.v)
        self.v.extend(pts)
        self.f.append((b, b + 1, b + 2, b + 3))
        self.n.append(Vector(normal))
        self.fm.append(self.mi(mat))

    def tri(self, pts, normal, mat):
        b = len(self.v)
        self.v.extend(pts)
        self.f.append((b, b + 1, b + 2))
        self.n.append(Vector(normal))
        self.fm.append(self.mi(mat))

    def to_object(self, name, uv_scale=2.0, weld=True):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        vs = [bm.verts.new(v) for v in self.v]
        for idx, nrm, mi in zip(self.f, self.n, self.fm):
            try:
                f = bm.faces.new([vs[i] for i in idx])
            except ValueError:
                continue
            f.material_index = mi
            f.normal_update()
            if f.normal.dot(nrm) < 0:
                f.normal_flip()
        if weld:
            bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-4)
        K.box_uv(bm, uv_scale)
        bm.to_mesh(me)
        bm.free()
        for m in self.mats:
            me.materials.append(K.get_mat(m))
        ob = bpy.data.objects.new(name, me)
        bpy.context.scene.collection.objects.link(ob)
        return ob


def build_ground_grid(lay):
    meta = lay["meta"]
    b = meta["bounds"]
    X0, Z0, X1, Z1 = b["x0"], b["z0"], meta["sea_x"], b["z1"]
    wx, wz = meta["wall"]["half_x"], meta["wall"]["half_z"]
    water = [w for w in lay["water"] if w["kind"] != "sea"]
    roads = lay["roads"]

    def clip(v, a, c):
        return min(max(v, a), c)
    xs, zs = {X0, X1, -wx, wx}, {Z0, Z1, -wz, wz}
    for r in water + roads:
        xs.update((clip(r["x0"], X0, X1), clip(r["x1"], X0, X1)))
        zs.update((clip(r["z0"], Z0, Z1), clip(r["z1"], Z0, Z1)))
    xs = sorted({round(v, 3) for v in xs})
    zs = sorted({round(v, 3) for v in zs})
    nx, nz = len(xs) - 1, len(zs) - 1

    def inside(r, x, z):
        return r["x0"] <= x <= r["x1"] and r["z0"] <= z <= r["z1"]

    land = [[None] * nz for _ in range(nx)]     # 材质名 或 None
    depth = [[0.0] * nz for _ in range(nx)]
    for i in range(nx):
        cx = (xs[i] + xs[i + 1]) / 2
        for j in range(nz):
            cz = (zs[j] + zs[j + 1]) / 2
            ws = [w["bottom"] for w in water if inside(w, cx, cz)]
            if ws:
                depth[i][j] = min(ws)
                continue
            rs = [r for r in roads if inside(r, cx, cz)]
            if rs:
                land[i][j] = ROAD_MAT[min(rs, key=lambda r: ROAD_PRI[r["kind"]])["kind"]]
            elif -wx <= cx <= wx and -wz <= cz <= wz:
                land[i][j] = "M_Ground_Town"
            else:
                land[i][j] = "M_Ground_Grass"

    rm = RawMesh()

    def top(i, j):
        return 0.0 if land[i][j] else depth[i][j]

    # 顶面：按行合并同材质/同深度
    for j in range(nz):
        i = 0
        while i < nx:
            key = land[i][j] or ("W", depth[i][j])
            k = i
            while k + 1 < nx and (land[k + 1][j] or ("W", depth[k + 1][j])) == key:
                k += 1
            y = top(i, j)
            mat = land[i][j] or "M_Mud"
            xa, xb, za, zb = xs[i], xs[k + 1], zs[j], zs[j + 1]
            rm.quad([u2b(xa, za, y), u2b(xb, za, y), u2b(xb, zb, y), u2b(xa, zb, y)], (0, 0, 1), mat)
            i = k + 1
    # 竖面：相邻格高差（岸壁 / 水底台阶）
    for i in range(nx):
        for j in range(nz):
            h = top(i, j)
            if i + 1 < nx:
                h2 = top(i + 1, j)
                if abs(h - h2) > 1e-4:
                    x = xs[i + 1]
                    lo, hi = min(h, h2), max(h, h2)
                    nrm_x = 1 if h > h2 else -1   # 朝低的一侧（团结 x）
                    mat = "M_Bank_Stone" if (land[i][j] or land[i + 1][j]) else "M_Mud"
                    rm.quad([u2b(x, zs[j], lo), u2b(x, zs[j + 1], lo), u2b(x, zs[j + 1], hi), u2b(x, zs[j], hi)],
                            (-nrm_x, 0, 0), mat)
            if j + 1 < nz:
                h2 = top(i, j + 1)
                if abs(h - h2) > 1e-4:
                    z = zs[j + 1]
                    lo, hi = min(h, h2), max(h, h2)
                    nrm_z = 1 if h > h2 else -1
                    mat = "M_Bank_Stone" if (land[i][j] or land[i][j + 1]) else "M_Mud"
                    rm.quad([u2b(xs[i], z, lo), u2b(xs[i + 1], z, lo), u2b(xs[i + 1], z, hi), u2b(xs[i], z, hi)],
                            (0, -nrm_z, 0), mat)
    # 外边裙边（东侧即海塘）
    for j in range(nz):
        for i, x, s in ((0, X0, -1), (nx - 1, X1, 1)):
            h = top(i, j)
            rm.quad([u2b(x, zs[j], -3.5), u2b(x, zs[j + 1], -3.5), u2b(x, zs[j + 1], h), u2b(x, zs[j], h)],
                    (-s, 0, 0), "M_Bank_Stone")
    for i in range(nx):
        for j, z, s in ((0, Z0, -1), (nz - 1, Z1, 1)):
            h = top(i, j)
            rm.quad([u2b(xs[i], z, -3.5), u2b(xs[i + 1], z, -3.5), u2b(xs[i + 1], z, h), u2b(xs[i], z, h)],
                    (0, -s, 0), "M_Bank_Stone")
    # 海塘压顶
    ob = rm.to_object("Ground")
    # 远景地面（地图外一圈，低 1 cm）
    far = RawMesh()
    F = 1800
    y = -0.01
    for xa, za, xb, zb in ((-F, Z1, X1, F), (-F, -F, X1, Z0), (-F, Z0, X0, Z1)):
        far.quad([u2b(xa, za, y), u2b(xb, za, y), u2b(xb, zb, y), u2b(xa, zb, y)], (0, 0, 1), "M_Ground_Grass")
    far.to_object("Ground_Far", uv_scale=8.0)
    # 海塘石栏（东岸）
    sw = K.MB()
    sw.box(-X1 - 0.6, -Z1, 0.0, -X1 + 0.6, -Z0, 0.6, "M_Bank_Stone")
    sw.to_object("Seawall")
    return ob


@recipe("Environments", "ENV_Yongchang_Ground")
def r_env_ground():
    build_ground_grid(load_layout())


@recipe("Environments", "ENV_Yongchang_Water")
def r_env_water():
    lay = load_layout()
    y = lay["meta"]["water_level"]
    rm = RawMesh()
    rm.quad([u2b(-1800, -1800, y), u2b(3200, -1800, y), u2b(3200, 1800, y), u2b(-1800, 1800, y)], (0, 0, 1), "M_Water")
    rm.to_object("NOCOL_Water", uv_scale=8.0)


def build_fields(fields, name):
    water = RawMesh()
    dikes = K.MB()
    for f in fields:
        salt = f["kind"] == "salt"
        surf = "M_Salt" if salt else "M_Paddy_Water"
        yw = 0.03 if salt else 0.05
        dw = 0.3 if salt else 0.4
        dh = 0.16 if salt else 0.24
        for c in f["cells"]:
            x0, z0, x1, z1 = c["x0"], c["z0"], c["x1"], c["z1"]
            water.quad([u2b(x0, z0, yw), u2b(x1, z0, yw), u2b(x1, z1, yw), u2b(x0, z1, yw)], (0, 0, 1), surf)
            # 田埂：每格四周各 dw 宽（相邻格的埂正好拼满 0.8 的间隔）
            for a, bb, c2, d2 in ((x0 - dw, z0 - dw, x1 + dw, z0), (x0 - dw, z1, x1 + dw, z1 + dw),
                                  (x0 - dw, z0, x0, z1), (x1, z0, x1 + dw, z1)):
                p0, p1 = u2b(a, bb), u2b(c2, d2)
                dikes.box(p0[0], p0[1], -0.05, p1[0], p1[1], dh, "M_Dike", skip_bottom=True)
    water.to_object("NOCOL_" + name + "_Surface", uv_scale=4.0, weld=False)
    dikes.to_object(name + "_Dikes")


@recipe("Environments", "ENV_Yongchang_FieldsIn")
def r_env_fields_in():
    lay = load_layout()
    build_fields([f for f in lay["fields"] if f["id"].startswith("FD_In") or f["kind"] == "salt"], "FieldsIn")


@recipe("Environments", "ENV_Yongchang_FieldsOut")
def r_env_fields_out():
    lay = load_layout()
    build_fields([f for f in lay["fields"] if f["id"].startswith("FD_Out")], "FieldsOut")


def hill_h(x, z, foot):
    d = foot - x
    if d <= 0:
        return -1.5
    s = lambda e0, e1, v: 0.0 if v <= e0 else 1.0 if v >= e1 else ((v - e0) / (e1 - e0)) ** 2 * (3 - 2 * (v - e0) / (e1 - e0))
    base = s(0, 140, d) * 42 + max(0.0, d - 140) * 0.16
    n = (14 * math.sin(x * 0.021 + 1.3) * math.sin(z * 0.017 + 0.4) + 8 * math.sin(x * 0.05 + z * 0.031)
         + 5 * math.sin(z * 0.07 - x * 0.02) + 3 * math.sin(x * 0.13 + z * 0.11))
    return base + n * s(0, 90, d) - 1.5


@recipe("Environments", "ENV_Luoshan_Hills")
def r_env_hills():
    """罗山（堡西）：低模起伏山体 + 山上远景树（锥体）。"""
    lay = load_layout()
    foot = lay["meta"]["hill_x"] + 8
    xa, xb, za, zb = -950.0, foot + 6, -900.0, 900.0
    nx, nz = 56, 120
    rm = RawMesh()
    P = lambda i, j: (xa + (xb - xa) * i / nx, za + (zb - za) * j / nz)
    H = {}
    for i in range(nx + 1):
        for j in range(nz + 1):
            x, z = P(i, j)
            H[i, j] = hill_h(x, z, foot)
    for i in range(nx):
        for j in range(nz):
            pts = []
            for ii, jj in ((i, j), (i + 1, j), (i + 1, j + 1), (i, j + 1)):
                x, z = P(ii, jj)
                pts.append(u2b(x, z, H[ii, jj]))
            rm.quad(pts, (0, 0, 1), "M_Hill")
    ob = rm.to_object("Hills", uv_scale=6.0)
    rng = random.Random(1560)
    trees = K.MB()
    for _ in range(650):
        x = rng.uniform(xa, foot - 12)
        z = rng.uniform(-600, 600)
        h = hill_h(x, z, foot)
        if h < 2:
            continue
        r = rng.uniform(2.5, 4.5)
        tall = rng.uniform(6, 11)
        bx, by, _ = u2b(x, z)
        trees.cyl(bx, by, h - 0.5, h + tall, r, "M_Leaf_Far", seg=5, r_top=0.05)
    trees.to_object("NOCOL_HillTrees", uv_scale=6.0)


# ====================================================================== 人物（rupu_char.py）
import rupu_char  # noqa: E402
RECIPES.update(rupu_char.recipes())

# ====================================================================== 第一幕道具 / 街市（rupu_act1.py）
import rupu_act1  # noqa: E402
RECIPES.update(rupu_act1.recipes())

# ====================================================================== 其余各幕（每个模块一个文件，互不干扰）
import importlib  # noqa: E402
for _m in ("rupu_act1p1", "rupu_ming_house", "rupu_ming_civic", "rupu_act2", "rupu_enemy", "rupu_act45"):
    RECIPES.update(importlib.import_module(_m).recipes())
# 第二幕补缺口（Docs/第二幕_策划对照与建模缺口.md）。排在后面，同名配方会覆盖前面的（用于包装已有资产）
for _m in ("rupu_a2_sand", "rupu_a2_text", "rupu_a2_site", "rupu_a2_anim", "rupu_a2_city"):
    if os.path.exists(os.path.join(os.path.dirname(os.path.abspath(__file__)), _m + ".py")):
        RECIPES.update(importlib.import_module(_m).recipes())


# ====================================================================== 驱动
def render_preview(path, name):
    scene = bpy.context.scene
    objs = [o for o in scene.objects if o.type == "MESH" and not o.name.startswith("REF_") and not o.name.startswith("COL_")]
    if not objs:
        return
    mn = Vector((1e9, 1e9, 1e9))
    mx = Vector((-1e9, -1e9, -1e9))
    for o in objs:
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            mn = Vector((min(mn[i], w[i]) for i in range(3)))
            mx = Vector((max(mx[i], w[i]) for i in range(3)))
    c = (mn + mx) / 2
    size = (mx - mn).length
    cam_data = bpy.data.cameras.new("PrevCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = size * 1.05
    cam = bpy.data.objects.new("PrevCam", cam_data)
    scene.collection.objects.link(cam)
    d = Vector((0.9, -1.4, 1.1)).normalized()       # 从前右上方看（正面 -Y）
    cam.location = c + d * size * 2
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    cam_data.clip_end = size * 10
    scene.camera = cam
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.render.resolution_x = 900
    scene.render.resolution_y = 700
    scene.render.filepath = path
    ref = bpy.data.collections.get("_REF")
    if ref:
        ref.hide_render = name.startswith("ENV_")
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)


def main(argv):
    only = None
    force = "--force" in argv
    export = "--no-export" not in argv
    preview = None
    if "--only" in argv:
        only = set(argv[argv.index("--only") + 1].split(","))
    if "--preview" in argv:
        preview = argv[argv.index("--preview") + 1]
        os.makedirs(preview, exist_ok=True)
    if "--list" in argv:
        for n, (c, _) in sorted(RECIPES.items()):
            print(f"{c:13s} {n}")
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
                render_preview(os.path.join(preview, name + ".png"), name)
            print(f"[OK] {name:28s} {stats['tris']:6d} tris  -> {os.path.relpath(stats['target'], REPO) if export else blend}")
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
