"""
《入谱》第三幕「守城」· 道具（Docs/第三幕_建模清单.md §3.1 / §3.2 / §3.4 / §4.3）
（Blender bpy，程序化白模；由 build_yongchang.py 统一生成/导出，recipes() 返回 {资产名: (分类, 生成函数)}）

约定：
  - 1 unit = 1 m；正面朝 Blender -Y（团结 +Z）；原点在底面中心，手持件原点在握点（+Z = 杆/刃方向，同 rupu_enemy 武器约定）。
  - 清单里「数量 N」是场景里摆 N 个；资产本身是一件（或一组变体并排，名字 <资产>_<变体>）。
  - 状态件 = 固定名字的子物体，团结里 SetActive / 插值 Transform；ANCHOR_* 站位、握点；FX_* 特效挂点；
    COL_* 只碰撞；NOCOL_* 不加碰撞（水面、火、布、贴字面片）。
  - 文字面片用 rupu_a3_text 生成贴图（0..1 UV，背面一片 U 翻转）。
  - 材质前缀 M_A3P_*（颜色写在 Base Color）。
"""
import math
import random

import bpy
from mathutils import Vector

import rupu_kit as K
import rupu_act2 as A2
import rupu_a3_text as T3

K.PALETTE.update({
    "M_A3P_Wood": "#6b5039", "M_A3P_WoodDark": "#3e2f24", "M_A3P_WoodLight": "#8a6e50", "M_A3P_WoodOld": "#7a6a56",
    "M_A3P_Iron": "#45484a", "M_A3P_IronRust": "#5e4a3a", "M_A3P_Bronze": "#6a5a3a", "M_A3P_BronzeGreen": "#5a6a58",
    "M_A3P_Brass": "#8f7a44", "M_A3P_Rope": "#a08a5a", "M_A3P_Cloth": "#9b8f6e", "M_A3P_Burlap": "#a4946e",
    "M_A3P_Grain": "#d6c48a", "M_A3P_GrainDark": "#b8a46a", "M_A3P_Clay": "#8a5a3b", "M_A3P_ClayDark": "#6a4430",
    "M_A3P_Glaze": "#3e3a32", "M_A3P_Oil": "#2a241c", "M_A3P_Stone": "#8a877e", "M_A3P_StoneDark": "#6a675f",
    "M_A3P_Fire": "#C4552E", "M_A3P_Ember": "#e08040", "M_A3P_Ash": "#4a4642", "M_A3P_Char": "#2f2a25",
    "M_A3P_Water": "#4F6B6A", "M_A3P_Leather": "#5a4636", "M_A3P_DrumSkin": "#c8b48e", "M_A3P_Lacquer": "#5a2a22",
    "M_A3P_Bamboo": "#a8925e", "M_A3P_BambooDark": "#7a6640", "M_A3P_Straw": "#b8a26a", "M_A3P_Mat": "#9a8a5e",
    "M_A3P_Fletch": "#c8bfa8", "M_A3P_Paper": "#E8DCC8", "M_A3P_Red": "#8a3a30", "M_A3P_Gold": "#b39a5c",
    "M_A3P_FlagBlue": "#3e5260", "M_A3P_FlagRed": "#9a3a2c", "M_A3P_FlagWhite": "#d8ccb2",
    "M_A3P_BookCover": "#3e2a1e", "M_A3P_PageEdge": "#d9c69a", "M_A3P_Seal": "#a8402e", "M_A3P_Horn": "#c8b890",
    "M_A3P_Rattan": "#8a7448", "M_A3P_RattanDark": "#5e4e32", "M_A3P_Sand": "#9b8f6e", "M_A3P_Powder": "#2a2826",
    "M_A3P_Lantern": "#E8DCC8", "M_A3P_LanternCap": "#3e2f24",
})

obj, tb, el, bx = A2.obj, A2.tb, A2.el, A2.bx


def anchor(name, loc, size=0.1, parent=None):
    return A2.anchor(name, loc, size, parent)


def fx(name, loc, parent=None):
    return A2.anchor(name, loc, 0.06, parent, kind="SPHERE")


def group(name, loc=(0, 0, 0)):
    return A2.group(name, loc)


def under(g, *obs):
    for ob in obs:
        if ob is not None:
            A2.child(ob, g)
    return g


def col_box(name, c, s):
    return A2.col_box(name, c, s)


def lathe(mb, prof, mat, seg=12, x=0.0, y=0.0):
    """回转体：prof = [(r, z), ...] 自下而上。"""
    for (r0, z0), (r1, z1) in zip(prof, prof[1:]):
        if z1 > z0:
            mb.cyl(x, y, z0, z1, r0, mat, seg=seg, r_top=r1)


def rock(mb, x, y, z, r, rng, mat="M_A3P_Stone"):
    rz = r * rng.uniform(0.6, 0.85)
    el(mb, (x, y, z + rz), r * rng.uniform(0.9, 1.25), r * rng.uniform(0.8, 1.1), rz, mat, seg=6, rings=3)


def hoop(mb, r, z, mat="M_A3P_Iron", h=0.025, seg=14, x=0.0, y=0.0):
    mb.cyl(x, y, z, z + h, r, mat, seg=seg)


def flame(mb, x, y, z, r, h):
    mb.cyl(x, y, z, z + h * 0.45, r, "M_A3P_Ember", seg=7, r_top=r * 0.75)
    mb.cyl(x, y, z + h * 0.45, z + h, r * 0.75, "M_A3P_Fire", seg=7, r_top=0.01)


# ====================================================================== §3.1 社会 Boss / 记谱
def build_blame_book():
    """愧顽簿：摊开 0.9×0.6 m（Book_Open：封面板 + 两摞纸 + 三个跨页 Spread_01..03，每个跨页 = Page_L_0k / Page_R_0k），
    合上 0.45×0.6×0.07 m（Book_Closed，红绳捆）。Tab_01..03 红签条、Stamp 族印。原点 = 书底中心。"""
    W, D = 0.9, 0.6
    mb = K.MB()
    for sx in (-1, 1):
        mb.box(sx * 0.003, -D / 2 - 0.01, 0, sx * (W / 2 + 0.01), D / 2 + 0.01, 0.008, "M_A3P_BookCover")
        mb.box(sx * 0.01, -D / 2, 0.008, sx * (W / 2 - 0.005), D / 2, 0.03, "M_A3P_PageEdge")
    mb.box(-0.012, -D / 2, 0.0, 0.012, D / 2, 0.026, "M_A3P_PageEdge")
    for k, y in enumerate((-0.18, 0.0, 0.18)):                                     # 红签条（右页外沿）
        mb.box(W / 2 - 0.005, y - 0.012, 0.028, W / 2 + 0.03, y + 0.012, 0.031, "M_A3P_Red")
    op = obj(mb, "Book_Open", uv=0.3)
    for k in range(3):
        anchor(f"Tab_0{k + 1}", (W / 2 + 0.02, (-0.18, 0.0, 0.18)[k], 0.03), 0.03, op)
    for k in range(3):
        m = T3.mat_from("Props", "PROP_A3_BlameBook", f"BlamePage_0{k + 1}", T3.blame_tex, 0.95, k=k)
        g = group(f"Spread_0{k + 1}")
        z = 0.031 + 0.0005 * k
        pl = T3.quad_xy(f"Page_L_0{k + 1}", -W / 2 + 0.005, -0.004, -D / 2, D / 2, z, m, uv=(0, 0, 0.5, 1))
        pr = T3.quad_xy(f"Page_R_0{k + 1}", 0.004, W / 2 - 0.005, -D / 2, D / 2, z, m, uv=(0.5, 0, 1, 1))
        under(g, pl, pr)
        g.parent = op
    cb = K.MB()                                                                       # 合上的册子
    cb.box(-0.225, -0.3, 0, 0.225, 0.3, 0.07, "M_A3P_BookCover")
    cb.box(-0.22, -0.295, 0.008, 0.226, 0.295, 0.062, "M_A3P_PageEdge")
    for y in (-0.12, 0.12):
        cb.box(-0.23, y - 0.006, -0.002, 0.23, y + 0.006, 0.073, "M_A3P_Red")
    cb.box(-0.12, -0.29, 0.07, 0.0, 0.06, 0.072, "M_A3P_Paper")                       # 题签
    obj(cb, "Book_Closed", (0, 0, 0), uv=0.3)
    st = K.MB()                                                                       # 族印：方印 + 钮
    st.box(-0.03, -0.03, 0, 0.03, 0.03, 0.03, "M_A3P_Seal")
    st.box(-0.02, -0.02, 0.03, 0.02, 0.02, 0.06, "M_A3P_WoodDark")
    st.cyl(0, 0, 0.06, 0.075, 0.018, "M_A3P_WoodDark", seg=8)
    obj(st, "Stamp", (W / 2 + 0.12, 0.15, 0), uv=0.2)
    anchor("ANCHOR_Read", (0, -0.75, 0))
    anchor("ANCHOR_Accuse", (-0.9, -0.5, 0))
    fx("FX_Ink", (0.2, 0.0, 0.04))


TAG_W, TAG_H, TAG_T = 0.06, 0.24, 0.012


def _tag_mesh(name, idx, loc, parent=None):
    """名签：木片（原点在底边中心）+ 正面贴字面片（NOCOL_TXT_）。"""
    mb = K.MB()
    mb.box(-TAG_W / 2, -TAG_T / 2, 0, TAG_W / 2, TAG_T / 2, TAG_H, "M_A3P_WoodLight")
    mb.prism([(-TAG_W / 2, TAG_H), (TAG_W / 2, TAG_H), (0, TAG_H + 0.012)], "y", -TAG_T / 2, TAG_T / 2, "M_A3P_WoodLight")
    ob = obj(mb, name, loc, uv=0.2)
    if parent is not None:
        ob.parent = parent
    m = T3.mat_from("Props", _tag_mesh.asset, f"NameTag_{idx + 1:02d}", T3.name_tag_tex, 0.9, idx=idx, W=TAG_W, H=TAG_H)
    T3.quad_xz(f"NOCOL_TXT_{name}", -TAG_W / 2, TAG_W / 2, 0, TAG_H, -TAG_T / 2 - 0.0015, m, parent=ob)
    return ob


def build_name_wall():
    """祠堂名墙：3.6×2.2 m 木板墙（带小檐顶、两根立柱、底座），三行各 10 个名签槽 Slot_01..30（槽 = 凹进去的深色框），
    NameTag_01..30 是插在槽里的木名签（每个一张字，T_A3_NameTag_xx），初始全部挂好，脚本按记谱进度逐个 SetActive。
    Brush 毛笔搁在底座笔架上；ANCHOR_Write = 写名站位（墙前 0.9 m）；FX_Ink 墨迹。原点 = 底座底面中心。"""
    _tag_mesh.asset = "PROP_A3_NameWall"
    W, H, base = 3.6, 2.2, 0.35
    mb = K.MB()
    mb.box(-W / 2 - 0.15, -0.25, 0, W / 2 + 0.15, 0.2, base, "M_A3P_StoneDark")             # 底座
    mb.box(-W / 2, 0.0, base, W / 2, 0.08, base + H, "M_A3P_Lacquer")                       # 板
    for x in (-W / 2 - 0.08, W / 2 + 0.08):                                                 # 立柱
        mb.box(x - 0.08, -0.06, base, x + 0.08, 0.12, base + H + 0.25, "M_A3P_WoodDark")
    mb.box(-W / 2 - 0.3, -0.35, base + H + 0.2, W / 2 + 0.3, 0.3, base + H + 0.3, "M_A3P_WoodDark")
    mb.prism([(-0.35, base + H + 0.3), (0.3, base + H + 0.3), (0.0, base + H + 0.55)], "x", -W / 2 - 0.35, W / 2 + 0.35,
             "M_Roof_Tile")
    mb.box(-W / 2 - 0.05, -0.04, base + H - 0.25, W / 2 + 0.05, 0.0, base + H - 0.05, "M_A3P_WoodDark")  # 额板
    mb.box(-0.4, -0.3, base - 0.02, 0.4, -0.18, base + 0.06, "M_A3P_WoodDark")             # 笔架
    obj(mb, "NameWall", uv=0.5)
    rows, cols = 3, 10
    sx = (W - 0.4) / cols
    for r in range(rows):
        z = base + H - 0.6 - r * 0.52
        for c in range(cols):
            i = r * cols + c
            x = W / 2 - 0.2 - sx * (c + 0.5)                                               # 右起
            sm = K.MB()
            sm.box(-TAG_W / 2 - 0.012, -0.004, -0.015, TAG_W / 2 + 0.012, 0.0, TAG_H + 0.03, "M_A3P_WoodDark")
            obj(sm, f"Slot_{i + 1:02d}", (x, 0.0, z), uv=0.2)
            _tag_mesh(f"NameTag_{i + 1:02d}", i, (x, -TAG_T / 2 - 0.004, z))
    br = K.MB()
    tb(br, (0, 0, 0), (0, 0, 0.2), 0.006, "M_A3P_Bamboo", seg=6)
    br.cyl(0, 0, -0.035, 0.0, 0.002, "M_A3P_Oil", seg=6, r_top=0.008)
    b = obj(br, "Brush", (0.2, -0.24, base + 0.07), uv=0.2)
    b.rotation_euler = (math.radians(90), 0, math.radians(80))
    anchor("ANCHOR_Write", (0, -0.9, 0))
    fx("FX_Ink", (0, -0.02, base + 1.2))


def build_name_tag():
    """单个木名签（6×24 cm，可拿/可放；原点在底边中心）。默认贴第 1 个名字，换材质 M_A3T_NameTag_xx 即换名。"""
    _tag_mesh.asset = "PROP_A3_NameTag"
    _tag_mesh("NameTag", 0, (0, 0, 0))
    anchor("ANCHOR_Hold", (0, 0, TAG_H * 0.3), 0.03)


def _sack(mb, h=0.7, r=0.24, tied=True, mat="M_A3P_Burlap"):
    el(mb, (0, 0, h * 0.42), r, r * 0.75, h * 0.45, mat, seg=10, rings=5, zmin=-0.93)
    if tied:
        mb.cyl(0, 0, h * 0.82, h * 0.9, r * 0.22, "M_A3P_Rope", seg=8)
        mb.cyl(0, 0, h * 0.9, h, r * 0.28, mat, seg=8, r_top=r * 0.38)


def build_grain_sack():
    """粮袋四态（同一位置，互斥）：Sack_Full 扎口满袋（正面印「糧」NOCOL_TXT_Sack）、Sack_Open 敞口露米、Sack_Empty 瘪袋、
    Sack_Broken 破袋 + Grain_Spill 散米堆（破袋时一起显示）。ANCHOR_Grab = 抓口位。"""
    m = T3.mat_from("Props", "PROP_A3_GrainSack", "GrainSack", T3.sack_tex, 0.95)
    mb = K.MB()
    _sack(mb)
    full = obj(mb, "Sack_Full", uv=0.4)
    T3.quad_xz("NOCOL_TXT_Sack", -0.09, 0.09, 0.2, 0.4, -0.183, m, uv=(0.25, 0.25, 0.75, 0.75), parent=full)
    mb = K.MB()
    _sack(mb, 0.62, 0.25, tied=False)
    mb.cyl(0, 0, 0.5, 0.62, 0.17, "M_A3P_Burlap", seg=10, r_top=0.22)
    el(mb, (0, 0, 0.56), 0.18, 0.15, 0.05, "M_A3P_Grain", seg=10, rings=3, zmin=0.0)
    obj(mb, "Sack_Open", uv=0.4)
    mb = K.MB()
    el(mb, (0, 0, 0.04), 0.3, 0.26, 0.05, "M_A3P_Burlap", seg=10, rings=3, zmin=-1.0)
    mb.box(-0.05, 0.22, 0.0, 0.05, 0.42, 0.03, "M_A3P_Burlap")
    obj(mb, "Sack_Empty", uv=0.4)
    mb = K.MB()
    _sack(mb, 0.45, 0.25, tied=True)
    mb.box(-0.12, -0.2, 0.05, 0.1, -0.17, 0.24, "M_A3P_GrainDark")                      # 破口里的米
    obj(mb, "Sack_Broken", uv=0.4)
    mb = K.MB()
    el(mb, (0.05, -0.38, 0.0), 0.32, 0.24, 0.07, "M_A3P_Grain", seg=10, rings=3, zmin=0.0)
    el(mb, (-0.2, -0.55, 0.0), 0.12, 0.1, 0.03, "M_A3P_Grain", seg=8, rings=2, zmin=0.0)
    obj(mb, "NOCOL_Grain_Spill", uv=0.4)
    anchor("ANCHOR_Grab", (0, -0.1, 0.65), 0.05)


def build_grain_measure():
    """粮斗/秤：Measure 木斗（口 0.36 m 方，斗里平口米）、Scale 秤杆（挂在小木架上，原点 = 提纽）、Weight 秤砣、
    Scoop 刮板（斜靠斗边）。ANCHOR_Use = 量粮站位。"""
    mb = K.MB()
    mb.frustum((-0.14, -0.14, 0.14, 0.14), (-0.19, -0.19, 0.19, 0.19), 0, 0.26, "M_A3P_Wood")
    mb.box(-0.17, -0.17, 0.2, 0.17, 0.17, 0.245, "M_A3P_Grain")
    for z in (0.05, 0.2):
        mb.frustum((-0.15 - z * 0.2, -0.15 - z * 0.2, 0.15 + z * 0.2, 0.15 + z * 0.2),
                   (-0.152 - z * 0.2, -0.152 - z * 0.2, 0.152 + z * 0.2, 0.152 + z * 0.2), z, z + 0.02, "M_A3P_Iron")
    obj(mb, "Measure", uv=0.3)
    fr = K.MB()                                                                          # 秤架
    for x in (0.45, 1.05):
        fr.box(x - 0.025, -0.025, 0, x + 0.025, 0.025, 1.2, "M_A3P_WoodDark")
    fr.box(0.42, -0.03, 1.18, 1.08, 0.03, 1.24, "M_A3P_WoodDark")
    obj(fr, "Stand", uv=0.3)
    sc = K.MB()
    tb(sc, (-0.25, 0, 0), (0.55, 0, 0), 0.008, "M_A3P_WoodLight", seg=6, r1=0.006)
    tb(sc, (0, 0, 0), (0, 0, 0.12), 0.003, "M_A3P_Rope", seg=4)
    tb(sc, (-0.2, 0, 0), (-0.2, 0, -0.25), 0.002, "M_A3P_Rope", seg=3)
    sc.cyl(-0.2, 0, -0.3, -0.26, 0.012, "M_A3P_Iron", seg=6)
    for k in range(10):
        sc.cyl(0.05 + k * 0.05, 0, -0.0085, 0.0085, 0.0005 + 0.0025, "M_A3P_Brass", seg=4)
    obj(sc, "Scale", (0.75, 0, 1.06), uv=0.2)
    wt = K.MB()
    tb(wt, (0, 0, 0), (0, 0, -0.12), 0.002, "M_A3P_Rope", seg=3)
    lathe(wt, [(0.015, -0.2), (0.035, -0.17), (0.03, -0.13), (0.012, -0.12)], "M_A3P_Iron", seg=8)
    obj(wt, "Weight", (1.15, 0, 1.06), uv=0.2)
    sp = K.MB()
    sp.box(-0.2, -0.008, 0, 0.2, 0.008, 0.06, "M_A3P_WoodLight")
    s = obj(sp, "Scoop", (0.0, -0.2, 0.2), uv=0.2)
    s.rotation_euler = (math.radians(-60), 0, 0)
    anchor("ANCHOR_Use", (0, -0.6, 0))


def build_grain_cart():
    """粮车：两轮独辕平板车（车床 1.6×1.0 m，轮径 1.0 m），车上三袋粮。Wheel_L/R 原点在轮轴（绕本地 X 转），
    ANCHOR_Pull = 辕头拉车站位（-Y 端）。"""
    mb = K.MB()
    mb.box(-0.5, -0.8, 0.5, 0.5, 0.8, 0.56, "M_A3P_Wood")
    for x in (-0.5, 0.5):
        mb.box(x - 0.03, -0.8, 0.56, x + 0.03, 0.8, 0.7, "M_A3P_WoodDark")
        for y in (-0.7, 0.0, 0.7):
            mb.box(x - 0.025, y - 0.025, 0.56, x + 0.025, y + 0.025, 0.85, "M_A3P_WoodDark")
    for x in (-0.25, 0.25):                                                              # 双辕
        tb(mb, (x, -0.8, 0.53), (x * 0.6, -2.1, 0.75), 0.035, "M_A3P_WoodDark", seg=6)
    tb(mb, (-0.15, -2.05, 0.75), (0.15, -2.05, 0.75), 0.03, "M_A3P_WoodDark", seg=6)
    mb.box(-0.62, -0.05, 0.42, 0.62, 0.05, 0.5, "M_A3P_WoodDark")                        # 轴
    mb.box(-0.04, 0.7, 0, 0.04, 0.78, 0.5, "M_A3P_WoodDark")                              # 后撑脚
    obj(mb, "Bed", uv=0.4)
    for s, x in (("L", 0.62), ("R", -0.62)):
        w = K.MB()
        A2.wheel(w, 0.5, 0.08, "M_A3P_Wood", "M_A3P_Iron", spokes=8, seg=14)
        obj(w, f"Wheel_{s}", (x, 0, 0.5), uv=0.3)
    for k, (x, y, rz) in enumerate(((-0.2, -0.35, 80), (0.2, -0.3, 95), (0.0, 0.35, 88))):
        s = K.MB()
        with s.at(0, 0, 0, rz, 90, 0):
            el(s, (0, 0, 0), 0.22, 0.17, 0.4, "M_A3P_Burlap", seg=8, rings=4)
        obj(s, f"Sack_{k + 1}", (x, y, 0.75), uv=0.4)
    anchor("ANCHOR_Pull", (0, -2.3, 0))


# ====================================================================== §3.2 指挥 / 信号 / 守城
def _flag_pole(mb, h, r=0.022, finial=True):
    mb.cyl(0, 0, 0, h, r, "M_A3P_Wood", seg=8, r_top=r * 0.8)
    if finial:
        mb.cyl(0, 0, h, h + 0.06, r * 1.4, "M_A3P_Iron", seg=8, r_top=0.003)


def build_signal_flag():
    """信号旗 三色（青 / 红 / 白）并排三面：Flag_Blue/Red/White 各一组 = Pole（2.4 m）+ Cloth（0.9×0.7 m，0..1 UV 正反两片）
    + ANCHOR_Grip（离地 1.0 m 握杆）+ FX_Cloth（风动/撕裂特效）。原点 = 杆底；一组一组摆，或只开一组。"""
    for k, (key, mat) in enumerate((("Blue", "M_A3P_FlagBlue"), ("Red", "M_A3P_FlagRed"), ("White", "M_A3P_FlagWhite"))):
        g = group(f"Flag_{key}", (k * 1.3, 0, 0))
        mb = K.MB()
        _flag_pole(mb, 2.4)
        p = obj(mb, f"Pole_{key}", (k * 1.3, 0, 0), uv=0.3)
        f, b = T3.wavy_cloth(f"NOCOL_Cloth_{key}", 0.02, 0.92, 1.62, 2.32, K.get_mat(mat), amp=0.05)
        for o in (f, b):
            o.location = (k * 1.3, 0, 0)
        under(g, p, f, b)
        anchor(f"ANCHOR_Grip_{key}", (k * 1.3, 0, 1.0), 0.05, g)
        fx(f"FX_Cloth_{key}", (k * 1.3 + 0.45, 0, 1.97), g)


def build_war_drum():
    """战鼓：鼓面直径 1.1 m、鼓面朝 -Y（竖立在木架上，鼓心高 1.25 m），两根鼓槌 Stick_L/R 搁在架上。
    ANCHOR_Play = 擂鼓站位（鼓面前 0.55 m，配 A3_BeatDrum）；FX_Hit 鼓面中心。原点 = 架底中心。"""
    R, L, zc = 0.55, 0.6, 1.25
    mb = K.MB()
    with mb.at(0, 0, zc, rx=90):
        lathe(mb, [(R, -L / 2), (R * 1.08, -L / 4), (R * 1.12, 0), (R * 1.08, L / 4), (R, L / 2)], "M_A3P_Lacquer", seg=16)
        mb.cyl(0, 0, -L / 2 - 0.01, -L / 2, R - 0.01, "M_A3P_DrumSkin", seg=16)
        mb.cyl(0, 0, L / 2, L / 2 + 0.01, R - 0.01, "M_A3P_DrumSkin", seg=16)
        for z in (-L / 2 + 0.03, L / 2 - 0.04):
            mb.cyl(0, 0, z, z + 0.012, R + 0.012, "M_A3P_Brass", seg=16)
    obj(mb, "Drum", uv=0.4)
    st = K.MB()
    for x in (-0.75, 0.75):
        for y in (-0.25, 0.25):
            tb(st, (x, y, 0), (x * 0.85, y * 0.8, zc + 0.2), 0.04, "M_A3P_WoodDark", seg=6)
        tb(st, (x * 0.85, -0.2, zc + 0.2), (x * 0.85, 0.2, zc + 0.2), 0.035, "M_A3P_WoodDark", seg=6)
        tb(st, (x * 0.88, 0, zc), (x * 0.62, 0, zc), 0.035, "M_A3P_WoodDark", seg=6)
    tb(st, (-0.7, 0, 0.35), (0.7, 0, 0.35), 0.035, "M_A3P_WoodDark", seg=6)
    obj(st, "Stand", uv=0.4)
    for s, x in (("L", 0.15), ("R", -0.15)):
        sk = K.MB()
        tb(sk, (0, 0, 0), (0, 0, 0.42), 0.014, "M_A3P_Wood", seg=6)
        el(sk, (0, 0, 0.44), 0.035, 0.035, 0.035, "M_A3P_Red", seg=6, rings=3)
        o = obj(sk, f"Stick_{s}", (x + 0.7 * (1 if s == "L" else -1) * 0, -0.25, zc + 0.24), uv=0.2)
        o.rotation_euler = (math.radians(90), 0, math.radians(90 if s == "L" else -90))
    anchor("ANCHOR_Play", (0, -0.55 - L / 2, 0))
    fx("FX_Hit", (0, -L / 2 - 0.01, zc))


def build_brazier():
    """火盆：三脚铁架（高 1.0 m）托一只铁篮，篮里炭火。Basket / Legs 分开，NOCOL_Fire 火苗（小锥），FX_Fire 粒子位，
    ANCHOR_Light = 点火站位。原点 = 三脚中心地面。"""
    mb = K.MB()
    for k in range(3):
        a = 2 * math.pi * k / 3
        tb(mb, (0.35 * math.cos(a), 0.35 * math.sin(a), 0), (0.2 * math.cos(a), 0.2 * math.sin(a), 0.82), 0.02, "M_A3P_Iron", seg=5)
    hoop(mb, 0.22, 0.35, h=0.02, seg=10)
    obj(mb, "Legs", uv=0.3)
    bk = K.MB()
    hoop(bk, 0.2, 0.8, h=0.03, seg=12)
    hoop(bk, 0.32, 1.0, h=0.03, seg=12)
    for k in range(10):
        a = 2 * math.pi * k / 10
        tb(bk, (0.2 * math.cos(a), 0.2 * math.sin(a), 0.8), (0.32 * math.cos(a), 0.32 * math.sin(a), 1.02), 0.01, "M_A3P_Iron", seg=4)
    bk.cyl(0, 0, 0.8, 0.83, 0.2, "M_A3P_Iron", seg=12)
    el(bk, (0, 0, 0.84), 0.26, 0.26, 0.12, "M_A3P_Char", seg=10, rings=3, zmin=0.0)
    obj(bk, "Basket", uv=0.3)
    fl = K.MB()
    for x, y, r, h in ((0, 0, 0.14, 0.55), (0.1, 0.06, 0.08, 0.35), (-0.09, -0.05, 0.08, 0.38)):
        flame(fl, x, y, 0.9, r, h)
    obj(fl, "NOCOL_Fire", uv=0.3)
    fx("FX_Fire", (0, 0, 1.0))
    anchor("ANCHOR_Light", (0, -0.7, 0))


def build_arrow_bundle():
    """箭捆：20 支箭一捆（两道麻绳），斜靠在一个矮木架上；Bundle 整捆一件。ANCHOR_Take = 取箭手位。"""
    mb = K.MB()
    rng = random.Random(7)
    for i in range(20):
        a, rr = rng.uniform(0, 6.28), 0.035 * math.sqrt(rng.random())
        x, y = rr * math.cos(a), rr * math.sin(a)
        tb(mb, (x, y, 0), (x * 1.3, y * 1.3, 0.85), 0.004, "M_A3P_Bamboo", seg=3)
        tb(mb, (x * 1.27, y * 1.27, 0.72), (x * 1.3, y * 1.3, 0.85), 0.007, "M_A3P_Fletch", seg=3)
    for z in (0.25, 0.55):
        mb.cyl(0, 0, z, z + 0.03, 0.05, "M_A3P_Rope", seg=8)
    b = obj(mb, "Bundle", uv=0.2)
    b.rotation_euler = (math.radians(-90), 0, 0)
    b.location = (0, -0.42, 0.27)
    st = K.MB()
    for y in (-0.25, 0.25):                                                              # 两个小 X 架
        for sx in (-1, 1):
            tb(st, (sx * 0.15, y, 0), (-sx * 0.1, y, 0.3), 0.015, "M_A3P_WoodDark", seg=5)
    obj(st, "Rack", uv=0.3)
    anchor("ANCHOR_Take", (0, -0.6, 0))


def build_rock_pile():
    """擂石堆：城头垛口内侧一堆 14 块擂石（0.2–0.35 m），Rocks 整堆一件；推落时脚本生成单块或整堆播动画。
    ANCHOR_Push = 推石站位（+Y 城内侧），FX_Dust 落石尘。原点 = 堆底中心。"""
    mb = K.MB()
    rng = random.Random(11)
    pts = []
    for i in range(14):
        layer = 0 if i < 8 else (1 if i < 12 else 2)
        a = rng.uniform(0, 6.28)
        rr = (0.45 - layer * 0.15) * math.sqrt(rng.random())
        r = rng.uniform(0.11, 0.17)
        rock(mb, rr * math.cos(a), rr * math.sin(a) * 0.7, layer * 0.2, r, rng)
    obj(mb, "Rocks", uv=0.5)
    col_box("COL_Rocks", (0, 0, 0.25), (1.0, 0.7, 0.5))
    anchor("ANCHOR_Push", (0, 0.75, 0))
    fx("FX_Dust", (0, -0.6, 0.2))


def build_oil_jar():
    """油坛：陶坛（高 0.55 m，酱黑釉上半）+ Lid 木塞（可拔），坛肩两只耳。ANCHOR_Pour = 抱坛倾倒手位，FX_Pour 坛口。"""
    mb = K.MB()
    lathe(mb, [(0.12, 0), (0.2, 0.12), (0.24, 0.28), (0.2, 0.42), (0.1, 0.5), (0.09, 0.53), (0.1, 0.55)], "M_A3P_Clay", seg=12)
    lathe(mb, [(0.241, 0.3), (0.205, 0.42), (0.105, 0.5)], "M_A3P_Glaze", seg=12)
    for sx in (-1, 1):
        tb(mb, (sx * 0.17, 0, 0.44), (sx * 0.22, 0, 0.4), 0.02, "M_A3P_ClayDark", seg=5)
    obj(mb, "Jar", uv=0.3)
    ld = K.MB()
    ld.cyl(0, 0, 0, 0.06, 0.07, "M_A3P_Wood", seg=8, r_top=0.085)
    ld.cyl(0, 0, 0.06, 0.075, 0.1, "M_A3P_Cloth", seg=8)
    obj(ld, "Lid", (0, 0, 0.5), uv=0.2)
    anchor("ANCHOR_Pour", (0, -0.25, 0.35), 0.05)
    fx("FX_Pour", (0, 0, 0.56))


def build_barricade():
    """街垒 4 模块（各 2 m 宽，沿 X 并排间隔 2.5 m，可任意拼）：Barricade_Wood 木栅拒板、Barricade_Stone 乱石矮墙、
    Barricade_Cart 翻倒的板车、Barricade_Sand 沙袋墙。每个模块：网格 + COL_<模块> 碰撞盒 + ANCHOR_Cover_<模块>（+Y 守方掩蔽位）。
    原点 = 第一块底面中心。"""
    rng = random.Random(21)
    specs = ["Wood", "Stone", "Cart", "Sand"]
    for k, key in enumerate(specs):
        x0 = k * 2.5
        mb = K.MB()
        if key == "Wood":
            for x in (-0.9, 0.0, 0.9):
                tb(mb, (x, 0.3, 0), (x, -0.1, 1.2), 0.05, "M_A3P_WoodDark", seg=6)
            for z in (0.3, 0.65, 1.0):
                mb.box(-1.0, -0.02 + (z - 0.3) * -0.3, z, 1.0, 0.04 + (z - 0.3) * -0.3, z + 0.22, "M_A3P_WoodOld")
            for x in (-0.6, 0.6):
                tb(mb, (x, 0.0, 0.4), (x, -0.6, 0.9), 0.03, "M_A3P_Wood", seg=5)
            h = 1.25
        elif key == "Stone":
            for i in range(16):
                rock(mb, rng.uniform(-0.9, 0.9), rng.uniform(-0.2, 0.2), (i // 6) * 0.25, rng.uniform(0.15, 0.22), rng)
            h = 0.8
        elif key == "Cart":
            mb.box(-1.0, -0.05, 0.0, 1.0, 0.05, 0.9, "M_A3P_Wood")                       # 车床立起
            for z in (0.1, 0.8):
                mb.box(-1.0, -0.08, z, 1.0, -0.05, z + 0.06, "M_A3P_WoodDark")
            with mb.at(0.6, 0.35, 0.45, 0, 0, 0):
                A2.wheel(mb, 0.42, 0.07, "M_A3P_Wood", "M_A3P_Iron", spokes=6, seg=10)
            tb(mb, (-0.8, 0.05, 0.6), (-1.2, 1.1, 0.05), 0.035, "M_A3P_WoodDark", seg=5)
            h = 0.95
        else:
            for row in range(3):
                for i in range(4 - (row == 2)):
                    x = -0.75 + i * 0.5 + (0.25 if row % 2 else 0)
                    with mb.at(x, 0, row * 0.22, rng.uniform(-6, 6)):
                        el(mb, (0, 0, 0.11), 0.26, 0.17, 0.11, "M_A3P_Sand", seg=8, rings=3)
            h = 0.66
        g = group(f"Barricade_{key}", (x0, 0, 0))
        o = obj(mb, f"Mesh_{key}", (x0, 0, 0), uv=0.5)
        c = col_box(f"COL_{key}", (x0, 0, h / 2), (2.0, 0.5, h))
        a = anchor(f"ANCHOR_Cover_{key}", (x0, 0.6, 0))
        under(g, o, c, a)


def build_gate_boom():
    """水门拦江：一串原木浮栅（6 m，6 根 1 m 原木首尾铁环相连，浮在水面）+ 两端铁链拉到两侧墙根铁环。
    Boom 原点 = 浮栅中心水面；Chain_L/R 从墙环到浮栅端；ANCHOR_Release = 岸上放链绞盘站位。"""
    mb = K.MB()
    for i in range(6):
        x = -2.5 + i
        with mb.at(x, 0, 0, 0, 90, 0):
            mb.cyl(0, 0, -0.48, 0.48, 0.14, "M_A3P_WoodDark", seg=8)
        if i < 5:
            mb.cyl(x + 0.5, 0, -0.03, 0.03, 0.06, "M_A3P_Iron", seg=6)
    for i in range(6):                                                                    # 原木上的铁钉刺
        tb(mb, (-2.5 + i, 0, 0.12), (-2.5 + i, -0.1, 0.3), 0.012, "M_A3P_Iron", seg=4, r1=0.002)
    obj(mb, "Boom", uv=0.4)
    for s, sx in (("L", 1), ("R", -1)):
        ch = K.MB()
        a, b = Vector((sx * 3.0, 0, 0)), Vector((sx * 4.2, 0.0, 1.6))
        n = 12
        for k in range(n):
            p = a.lerp(b, k / n) + Vector((0, 0, -0.25 * math.sin(math.pi * k / n)))
            with ch.at(p.x, p.y, p.z, 0, 0, 90 * (k % 2)):
                ch.box(-0.06, -0.015, -0.03, 0.06, 0.015, 0.03, "M_A3P_Iron")
        ch.cyl(sx * 4.2, 0.1, 1.5, 1.7, 0.08, "M_A3P_Iron", seg=8)
        obj(ch, f"Chain_{s}", uv=0.3)
    anchor("ANCHOR_Release", (4.6, 0.8, 1.0))


def build_skiff():
    """小船：3.2 m 舢板（船宽 1.0、舷高 0.5），原点 = 船中心水线（船底在 -0.25 = 吃水），船头朝 -Y、略翘。
    Hull（外壳 + 内壳 + 舷缘 + 两块座板）/ Oar（单桨，搁在右舷）/ ANCHOR_Stand（船中站人）。"""
    mb = K.MB()
    L, B, top, keel = 3.2, 1.0, 0.25, -0.25
    N = 10
    st = []
    for i in range(N + 1):
        t = i / N
        y = -L / 2 + L * t
        w = max(0.03, B / 2 * math.sin(math.pi * t) ** 0.6)
        lift = 0.18 * max(0.0, 1 - t / 0.25) ** 2 + 0.08 * max(0.0, (t - 0.8) / 0.2) ** 2
        st.append((y, w, top + lift, keel + lift * 0.9))

    def ring(y, w, zt, zk, k):
        return [(-w * k, y, zt), (-w * 0.8 * k, y, (zt + zk) / 2 - 0.05), (0, y, zk + (1 - k) * 0.04),
                (w * 0.8 * k, y, (zt + zk) / 2 - 0.05), (w * k, y, zt)]
    outer = [mb.addv(ring(y, w, zt, zk, 1.0)) for y, w, zt, zk in st]
    inner = [mb.addv(ring(y, w, zt, zk + 0.04, max(0.0, 1 - 0.05 / w))) for y, w, zt, zk in st]
    for a, b in zip(range(N), range(1, N + 1)):
        for j in range(4):
            mb.face([outer[a] + j, outer[a] + j + 1, outer[b] + j + 1, outer[b] + j], "M_A3P_WoodOld")
            mb.face([inner[a] + j + 1, inner[a] + j, inner[b] + j, inner[b] + j + 1], "M_A3P_Wood")
        for j in (0, 4):
            mb.face([outer[a] + j, outer[b] + j, inner[b] + j, inner[a] + j], "M_A3P_WoodDark")
    for e in (0, N):
        for j in range(4):
            q = [outer[e] + j, outer[e] + j + 1, inner[e] + j + 1, inner[e] + j]
            mb.face(q if e == N else q[::-1], "M_A3P_WoodDark")
    for y in (-0.6, 0.5):
        w = B / 2 * math.sin(math.pi * (y + L / 2) / L) ** 0.6 - 0.06
        mb.box(-w, y - 0.12, 0.05, w, y + 0.12, 0.09, "M_A3P_Wood")
    obj(mb, "Hull", uv=0.5)
    oar = K.MB()
    tb(oar, (0, -1.0, 0), (0, 1.1, 0), 0.02, "M_A3P_Wood", seg=6)
    oar.box(-0.008, 1.1, -0.08, 0.008, 1.55, 0.08, "M_A3P_Wood")
    obj(oar, "Oar", (0.45, 0.0, 0.27), uv=0.3)
    anchor("ANCHOR_Stand", (0, 0, 0.09))


def build_water_trough():
    """水槽：木槽 1.6×0.5×0.55 m（四腿），NOCOL_Water 水面（低于槽沿 6 cm，不加碰撞）。ANCHOR_Fill = 打水站位。"""
    mb = K.MB()
    L, Wd, h0, h1 = 1.6, 0.5, 0.25, 0.55
    mb.box(-L / 2, -Wd / 2, h0, L / 2, Wd / 2, h0 + 0.05, "M_A3P_Wood")
    for sx in (-1, 1):
        mb.box(-L / 2, sx * Wd / 2 - 0.04, h0, L / 2, sx * Wd / 2 + 0.0 * sx, h1, "M_A3P_Wood")
        mb.box(sx * L / 2 - 0.04 * sx, -Wd / 2, h0, sx * L / 2, Wd / 2, h1, "M_A3P_WoodDark")
        for sy in (-1, 1):
            mb.box(sx * (L / 2 - 0.12) - 0.04, sy * (Wd / 2 - 0.06) - 0.04, 0, sx * (L / 2 - 0.12) + 0.04,
                   sy * (Wd / 2 - 0.06) + 0.04, h0, "M_A3P_WoodDark")
    for x in (-0.5, 0.5):
        mb.box(x - 0.02, -Wd / 2 - 0.01, h0, x + 0.02, Wd / 2 + 0.01, h1 + 0.01, "M_A3P_Iron")
    obj(mb, "Trough", uv=0.4)
    w = K.MB()
    w.box(-L / 2 + 0.05, -Wd / 2 + 0.05, h1 - 0.09, L / 2 - 0.05, Wd / 2 - 0.05, h1 - 0.06, "M_A3P_Water")
    obj(w, "NOCOL_Water", uv=0.5)
    anchor("ANCHOR_Fill", (0, -0.7, 0))


def _bucket(mb, r0=0.13, r1=0.16, h=0.32):
    lathe(mb, [(r0, 0), (r1, h)], "M_A3P_Wood", seg=12)
    hoop(mb, r0 + 0.006, 0.05, h=0.02, seg=12)
    hoop(mb, r1 - 0.004, h - 0.06, h=0.02, seg=12)
    pts = [(r1 * math.cos(math.pi * i / 8), 0, h + 0.2 * math.sin(math.pi * i / 8)) for i in range(9)]
    for a, b in zip(pts, pts[1:]):
        tb(mb, a, b, 0.006, "M_A3P_Rope", seg=4)


def build_bucket():
    """水桶：木桶（口径 0.32 m、高 0.32 m、两道铁箍）+ 绳提梁，NOCOL_Water 满桶水面（空桶时隐藏）。
    原点 = 桶底中心；ANCHOR_Handle = 提梁顶握点（对 SOCKET_Hand_*）。"""
    mb = K.MB()
    _bucket(mb)
    obj(mb, "Bucket", uv=0.3)
    w = K.MB()
    w.cyl(0, 0, 0.26, 0.27, 0.15, "M_A3P_Water", seg=12)
    obj(w, "NOCOL_Water", uv=0.3)
    anchor("ANCHOR_Handle", (0, 0, 0.52), 0.04)


def build_unit_marker():
    """兵牌小旗（军议城图 / 战中指挥用）：0.4 m 小竹签 + 0.24×0.18 m 方旗，Marker_Blue（「義」）/ Marker_Red（「倭」）各一，
    并排 0.4 m。每个：Pole_<色> / Cloth_<色>_Front/Back（贴字两片）/ ANCHOR_Plant_<色>（签尖 = 原点）。"""
    for k, key in enumerate(("Blue", "Red")):
        x = k * 0.4
        g = group(f"Marker_{key}", (x, 0, 0))
        mb = K.MB()
        mb.cyl(0, 0, 0, 0.4, 0.005, "M_A3P_Bamboo", seg=6)
        mb.cyl(0, 0, 0.0, 0.04, 0.001, "M_A3P_Bamboo", seg=6, r_top=0.005)
        mb.box(-0.025, -0.025, 0.0, 0.025, 0.025, 0.015, "M_A3P_WoodDark")                # 底座（插在城图上）
        p = obj(mb, f"Pole_{key}", (x, 0, 0), uv=0.1)
        m = T3.mat_from("Props", "PROP_A3_UnitMarker", f"Unit_{key}", T3.unit_tex, 0.9, key=key)
        f, b = T3.two_sided_xz(f"NOCOL_Cloth_{key}", 0.005, 0.245, 0.2, 0.38, 0.0, m)
        for o in (f, b):
            o.location = (x, 0, 0)
        under(g, p, f, b)
        anchor(f"ANCHOR_Plant_{key}", (x, 0, 0), 0.03, g)


def build_wall_banner():
    """城头长幡：3.5 m 竖杆 + 顶横杆挑一面 0.6×2.4 m 竖幡。三面并排（1.2 m）：Banner_Wang「王」（环海楼/城头）、
    Banner_Tanghe「湯」（汤和庙/巡游回响）、Banner_Blank 无字（「无名」选择）。每面：Pole_<键> / NOCOL_Cloth_<键>_Front/Back /
    ANCHOR_Grip_<键>。原点 = 第一根杆底。"""
    for k, key in enumerate(("Wang", "Tanghe", "Blank")):
        x = k * 1.2
        g = group(f"Banner_{key}", (x, 0, 0))
        mb = K.MB()
        _flag_pole(mb, 3.5, 0.03)
        tb(mb, (0, 0, 3.3), (0.68, 0, 3.3), 0.015, "M_A3P_Wood", seg=6)
        tb(mb, (0.68, 0, 3.3), (0.68, 0, 3.24), 0.004, "M_A3P_Rope", seg=3)
        p = obj(mb, f"Pole_{key}", (x, 0, 0), uv=0.3)
        m = T3.mat_from("Props", "PROP_A3_WallBanner", f"Flag_{key}", T3.flag_tex, 0.95, W=0.6, H=2.4, key=key)
        f, b = T3.wavy_cloth(f"NOCOL_Cloth_{key}", 0.06, 0.66, 0.84, 3.24, m, nx=4, nz=8, amp=0.03, waves=0.5)
        for o in (f, b):
            o.location = (x, 0, 0)
        under(g, p, f, b)
        anchor(f"ANCHOR_Grip_{key}", (x, 0, 1.0), 0.05, g)


def build_key():
    """城门钥匙：明式长柄铁钥匙（0.2 m）穿在一块小木牌上（牌上可贴字，0..1 UV 面片留空）。原点 = 握点（钥匙柄环），
    +Z 朝钥匙头。ANCHOR_Hold 同原点。"""
    mb = K.MB()
    with mb.at(0, 0, 0, rx=90):
        mb.cyl(0, 0, -0.005, 0.005, 0.03, "M_A3P_Iron", seg=10)
    tb(mb, (0, 0, 0.02), (0, 0, 0.2), 0.006, "M_A3P_Iron", seg=6)
    mb.box(-0.004, -0.025, 0.16, 0.004, 0.0, 0.18, "M_A3P_Iron")
    mb.box(-0.004, -0.025, 0.19, 0.004, 0.0, 0.2, "M_A3P_Iron")
    obj(mb, "Key", uv=0.1)
    tg = K.MB()
    tb(tg, (0, 0, -0.03), (0, 0, -0.08), 0.002, "M_A3P_Rope", seg=3)
    tg.box(-0.025, -0.005, -0.16, 0.025, 0.005, -0.08, "M_A3P_WoodLight")
    obj(tg, "Tag", uv=0.1)
    anchor("ANCHOR_Hold", (0, 0, 0), 0.03)


def build_fire_basket():
    """火篮（夜战照明）：墙根立的 L 形铁柱（2.4 m，挑出 0.6 m），吊链挂铁篮，篮里松明火。
    Post / Chain（原点在挑臂端，可晃）/ Basket（原点在链底）/ NOCOL_Fire / FX_Fire。原点 = 柱底。"""
    mb = K.MB()
    mb.box(-0.03, -0.03, 0, 0.03, 0.03, 2.4, "M_A3P_Iron")
    mb.box(-0.03, -0.63, 2.34, 0.03, 0.03, 2.4, "M_A3P_Iron")
    tb(mb, (0, 0, 2.0), (0, -0.4, 2.37), 0.012, "M_A3P_Iron", seg=4)
    mb.box(-0.12, -0.12, 0, 0.12, 0.12, 0.05, "M_A3P_StoneDark")
    obj(mb, "Post", uv=0.3)
    ch = K.MB()
    for k in range(6):
        with ch.at(0, 0, -0.05 - k * 0.07, 90 * (k % 2)):
            ch.box(-0.012, -0.004, -0.04, 0.012, 0.004, 0.0, "M_A3P_Iron")
    obj(ch, "Chain", (0, -0.6, 2.34), uv=0.2)
    bk = K.MB()
    hoop(bk, 0.1, -0.2, h=0.02, seg=10)
    hoop(bk, 0.18, -0.02, h=0.02, seg=10)
    for k in range(8):
        a = 2 * math.pi * k / 8
        tb(bk, (0.1 * math.cos(a), 0.1 * math.sin(a), -0.2), (0.18 * math.cos(a), 0.18 * math.sin(a), 0.0), 0.008, "M_A3P_Iron", seg=4)
    for k in range(3):
        a = 2 * math.pi * k / 3
        tb(bk, (0.18 * math.cos(a), 0.18 * math.sin(a), 0.0), (0, 0, 0.12), 0.004, "M_A3P_Iron", seg=3)
    el(bk, (0, 0, -0.1), 0.13, 0.13, 0.08, "M_A3P_Char", seg=8, rings=3, zmin=-0.2)
    obj(bk, "Basket", (0, -0.6, 2.34 - 0.55), uv=0.2)
    fl = K.MB()
    flame(fl, 0, 0, 0.0, 0.1, 0.35)
    obj(fl, "NOCOL_Fire", (0, -0.6, 2.34 - 0.62), uv=0.2)
    fx("FX_Fire", (0, -0.6, 1.9))


def build_cannon_tools():
    """炮具（摆在一副木架上，每件原点在握点、+Z 朝工作端，可挂 SOCKET_Hand_R）：Rammer 送弹杆（2.0 m，一头夯头一头刷）、
    Ladle 药勺（铜勺）、Match 火绳杆（火绳头 FX_Match）、Balls 一小堆炮弹、PowderBag 两包药包。
    ANCHOR_Rammer / ANCHOR_Ladle / ANCHOR_Match = 取用手位。原点 = 架底中心。"""
    rk = K.MB()
    for x in (-0.6, 0.6):
        rk.box(x - 0.03, -0.03, 0, x + 0.03, 0.03, 1.1, "M_A3P_WoodDark")
        for z in (0.5, 0.8, 1.05):
            rk.box(x - 0.03, -0.1, z, x + 0.03, 0.03, z + 0.04, "M_A3P_WoodDark")
    rk.box(-0.65, -0.03, 0.2, 0.65, 0.03, 0.25, "M_A3P_WoodDark")
    obj(rk, "Rack", uv=0.3)

    def tool(name, build, z, a_name):
        mb = K.MB()
        build(mb)
        o = obj(mb, name, (-0.7, -0.07, z), uv=0.2)
        o.rotation_euler = (0, math.radians(90), 0)
        anchor(a_name, (0.0, -0.07, z), 0.04)

    def rammer(mb):
        tb(mb, (0, 0, -0.9), (0, 0, 1.1), 0.02, "M_A3P_Wood", seg=6)
        mb.cyl(0, 0, 1.1, 1.22, 0.05, "M_A3P_WoodDark", seg=8)
        mb.cyl(0, 0, -1.0, -0.9, 0.055, "M_A3P_Cloth", seg=8)

    def ladle(mb):
        tb(mb, (0, 0, -0.9), (0, 0, 1.0), 0.018, "M_A3P_Wood", seg=6)
        with mb.at(0, 0.03, 1.1, rx=90):
            mb.cyl(0, 0, -0.03, 0.03, 0.05, "M_A3P_Bronze", seg=8)
        mb.box(-0.05, -0.0, 1.0, 0.05, 0.02, 1.25, "M_A3P_Bronze")

    def match(mb):
        tb(mb, (0, 0, -0.5), (0, 0, 0.7), 0.015, "M_A3P_Wood", seg=6)
        for sx in (-1, 1):
            tb(mb, (sx * 0.01, 0, 0.7), (sx * 0.03, 0, 0.8), 0.005, "M_A3P_Iron", seg=4)
        tb(mb, (0.03, 0, 0.8), (0.0, -0.02, 0.86), 0.006, "M_A3P_Rope", seg=4)
        tb(mb, (0.0, -0.02, 0.86), (0.0, -0.02, 0.88), 0.008, "M_A3P_Ember", seg=4)
    tool("Rammer", rammer, 1.09, "ANCHOR_Rammer")
    tool("Ladle", ladle, 0.84, "ANCHOR_Ladle")
    tool("Match", match, 0.54, "ANCHOR_Match")
    fx("FX_Match", (0.18, -0.07, 0.54))
    bl = K.MB()
    for i, (x, y, z) in enumerate(((0, 0, 0), (0.13, 0, 0), (0.065, 0.11, 0), (0.065, 0.04, 0.1))):
        el(bl, (x, y, z + 0.06), 0.06, 0.06, 0.06, "M_A3P_Iron", seg=8, rings=4)
    obj(bl, "Balls", (0.9, -0.1, 0), uv=0.2)
    pb = K.MB()
    for x in (0.0, 0.18):
        with pb.at(x, 0, 0.06, 0, 90, 0):
            pb.cyl(0, 0, -0.08, 0.08, 0.06, "M_A3P_Cloth", seg=8)
    obj(pb, "PowderBag", (-0.95, -0.1, 0), uv=0.2)


def build_sluice_tools():
    """闸具：Hook 挠钩（2.4 m 竹竿 + 铁钩，钩闸板 / 拉船）、Crowbar 撬棍（1.3 m 铁杠）、Rope 一盘麻绳，靠在一个木桩上。
    手持件原点在握点、+Z 朝工作端。原点 = 木桩底。"""
    st = K.MB()
    st.cyl(0, 0, 0, 1.1, 0.08, "M_A3P_WoodDark", seg=8)
    obj(st, "Post", uv=0.3)
    hk = K.MB()
    tb(hk, (0, 0, -0.6), (0, 0, 1.8), 0.02, "M_A3P_Bamboo", seg=6)
    tb(hk, (0, 0, 1.8), (0, 0, 1.98), 0.016, "M_A3P_Iron", seg=5)
    tb(hk, (0, 0, 1.92), (0, -0.12, 1.86), 0.01, "M_A3P_Iron", seg=4)
    tb(hk, (0, -0.12, 1.86), (0, -0.14, 1.74), 0.008, "M_A3P_Iron", seg=4, r1=0.003)
    h = obj(hk, "Hook", (0.12, -0.05, 0.6), uv=0.2)
    h.rotation_euler = (math.radians(-8), math.radians(-8), 0)
    cb = K.MB()
    tb(cb, (0, 0, -0.25), (0, 0, 1.05), 0.015, "M_A3P_Iron", seg=6)
    tb(cb, (0, 0, 1.05), (0, -0.06, 1.1), 0.013, "M_A3P_Iron", seg=5)
    c = obj(cb, "Crowbar", (-0.12, -0.06, 0.25), uv=0.2)
    c.rotation_euler = (math.radians(-10), math.radians(10), 0)
    rp = K.MB()
    for k in range(5):
        with rp.at(0, 0, 0.02 + k * 0.025):
            for i in range(10):
                a0, a1 = 2 * math.pi * i / 10, 2 * math.pi * (i + 1) / 10
                r = 0.2 - k * 0.006
                tb(rp, (r * math.cos(a0), r * math.sin(a0), 0), (r * math.cos(a1), r * math.sin(a1), 0), 0.012, "M_A3P_Rope", seg=4)
    obj(rp, "Rope", (0.0, -0.45, 0), uv=0.2)


def build_corpse_cover():
    """盖尸席：草席（1.9×0.9 m）盖在一具遗体上的隆起形状（底下不需要人形，单独放也像盖着人）；
    Cover 一件，NOCOL（不挡路）。原点 = 席底中心。另有 Cover_Flat 平铺（掀开后）。"""
    mb = K.MB()
    n = 10
    grid = []
    for j in range(n + 1):
        row = []
        for i in range(n + 1):
            u, v = i / n, j / n
            x, y = -0.45 + 0.9 * u, -0.95 + 1.9 * v
            body = math.exp(-((x / 0.24) ** 2)) * (0.22 if 0.15 < v < 0.95 else 0.12)
            head = math.exp(-((x / 0.12) ** 2 + ((v - 0.08) / 0.06) ** 2)) * 0.06
            edge = min(u, 1 - u, v, 1 - v)
            z = max(0.01, body + head - (0.02 if edge < 0.08 else 0))
            row.append(mb.addv([(x, y, z)]))
        grid.append(row)
    for j in range(n):
        for i in range(n):
            q = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
            mb.face(q, "M_A3P_Mat")
            mb.face(list(reversed(q)), "M_A3P_Mat")
    obj(mb, "NOCOL_Cover", uv=0.5)
    fl = K.MB()
    fl.box(-0.45, -0.95, 0, 0.45, 0.95, 0.01, "M_A3P_Mat")
    obj(fl, "NOCOL_Cover_Flat", (1.2, 0, 0), uv=0.5)


# ====================================================================== §4.3 P1 道具
def build_cannonball():
    """炮弹：Ball_Iron 铁弹（Φ0.12）、Ball_Stone 石弹（Φ0.16）单件 + Stack 一垛 10 个。原点 = 底面。"""
    mb = K.MB()
    el(mb, (0, 0, 0.06), 0.06, 0.06, 0.06, "M_A3P_Iron", seg=10, rings=5)
    obj(mb, "Ball_Iron", uv=0.2)
    mb = K.MB()
    el(mb, (0, 0, 0.08), 0.08, 0.08, 0.08, "M_A3P_Stone", seg=8, rings=4)
    obj(mb, "Ball_Stone", (0.3, 0, 0), uv=0.2)
    mb = K.MB()
    r = 0.06
    for layer, (n, off) in enumerate(((3, 0.0), (2, r * 0.58), (1, r * 1.15))):
        for i in range(n):
            for j in range(n - i):
                x = (i + j * 0.5) * 2 * r - (n - 1) * r + off * 0
                y = j * 2 * r * 0.866 - (n - 1) * r * 0.5
                el(mb, (x, y + off, r + layer * r * 1.63), r, r, r, "M_A3P_Iron", seg=8, rings=4)
    obj(mb, "Stack", (0.8, 0, 0), uv=0.2)


def build_powder_keg():
    """火药桶：鼓肚木桶（高 0.55 m）三道铁箍、Lid 桶盖（可掀）、桶身一块红纸封条。FX_Burst = 爆炸中心。"""
    mb = K.MB()
    lathe(mb, [(0.18, 0), (0.22, 0.14), (0.235, 0.275), (0.22, 0.41), (0.18, 0.55)], "M_A3P_Wood", seg=12)
    for z in (0.05, 0.25, 0.47):
        hoop(mb, 0.2 + (0.035 if z == 0.25 else 0.012), z, h=0.03, seg=12)
    mb.box(-0.06, -0.24, 0.3, 0.06, -0.22, 0.44, "M_A3P_Red")
    obj(mb, "Keg", uv=0.3)
    ld = K.MB()
    ld.cyl(0, 0, 0, 0.02, 0.18, "M_A3P_WoodDark", seg=12)
    obj(ld, "Lid", (0, 0, 0.55), uv=0.3)
    fx("FX_Burst", (0, 0, 0.3))


def build_arrow_stuck():
    """地面断箭（4 种：整箭斜插 / 半截 / 两支 / 箭杆断在地上），各一子物体 Arrow_1..4，并排 0.3 m。NOCOL（不挡路）。"""
    rng = random.Random(31)
    for k in range(4):
        mb = K.MB()
        n = 2 if k == 2 else 1
        for j in range(n):
            ox = j * 0.05
            L = (0.75, 0.38, 0.6, 0.45)[k]
            tilt = rng.uniform(15, 35)
            if k == 3:
                tb(mb, (ox - 0.2, 0, 0.004), (ox + 0.2, 0.03, 0.004), 0.004, "M_A3P_Bamboo", seg=3)
                tb(mb, (ox + 0.24, 0.04, 0.004), (ox + 0.36, 0.05, 0.004), 0.004, "M_A3P_Bamboo", seg=3)
                continue
            d = Vector((math.sin(math.radians(tilt)), 0.2, math.cos(math.radians(tilt)))).normalized()
            a = Vector((ox, 0, -0.08))
            tb(mb, a, a + d * L, 0.004, "M_A3P_Bamboo", seg=3)
            if k != 1:
                tb(mb, a + d * (L - 0.12), a + d * L, 0.008, "M_A3P_Fletch", seg=3)
        obj(mb, f"NOCOL_Arrow_{k + 1}", (k * 0.3, 0, 0), uv=0.2)


def build_shield_broken():
    """破盾 3 种：Broken_Rattan 裂开的藤牌（缺一块）、Broken_Wood 劈成两半的倭兵木盾、Broken_Plank 散开的盾板。平放地上。"""
    mb = K.MB()
    seg = 12
    for i in range(seg - 3):
        a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        mb.prism([(0, 0), (0.37 * math.cos(a0), 0.37 * math.sin(a0)), (0.37 * math.cos(a1), 0.37 * math.sin(a1))], "z", 0, 0.03,
                 "M_A3P_Rattan" if i % 2 else "M_A3P_RattanDark")
    el(mb, (0, 0, 0.03), 0.1, 0.1, 0.04, "M_A3P_RattanDark", seg=8, rings=3, zmin=0.0)
    obj(mb, "Broken_Rattan", uv=0.3)
    mb = K.MB()
    with mb.at(0, 0, 0, 12):
        mb.box(-0.3, -0.45, 0, -0.02, 0.45, 0.04, "M_A3P_WoodOld")
    with mb.at(0.08, 0.05, 0, -20):
        mb.box(0.0, -0.4, 0, 0.26, 0.42, 0.04, "M_A3P_WoodOld")
        mb.box(0.0, -0.06, 0.04, 0.2, 0.06, 0.07, "M_A3P_Iron")
    obj(mb, "Broken_Wood", (1.0, 0, 0), uv=0.3)
    mb = K.MB()
    rng = random.Random(4)
    for i in range(4):
        with mb.at(rng.uniform(-0.3, 0.3), rng.uniform(-0.3, 0.3), 0, rng.uniform(0, 180)):
            mb.box(-0.06, -0.35, 0, 0.06, 0.35, 0.03, "M_A3P_WoodOld")
    obj(mb, "Broken_Plank", (2.0, 0, 0), uv=0.3)


def build_helmet():
    """头盔 3 种（掉在地上，原点 = 着地点）：Helmet_Ming 明军铁盔（缨管）、Helmet_Jingasa 倭阵笠、Helmet_Kabuto 倭铁钵盔（錣）。"""
    mb = K.MB()
    el(mb, (0, 0, 0.0), 0.12, 0.12, 0.13, "M_A3P_Iron", seg=10, rings=4, zmin=0.0)
    mb.cyl(0, 0, 0.0, 0.02, 0.135, "M_A3P_Iron", seg=10)
    tb(mb, (0, 0, 0.12), (0, 0, 0.2), 0.008, "M_A3P_Brass", seg=5)
    mb.cyl(0, 0, 0.19, 0.24, 0.018, "M_A3P_Red", seg=6, r_top=0.004)
    o = obj(mb, "Helmet_Ming", uv=0.2)
    o.rotation_euler = (math.radians(70), 0, 0)
    o.location = (0, 0, 0.12)
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.1, 0.24, "M_A3P_Lacquer", seg=12, r_top=0.03)
    obj(mb, "Helmet_Jingasa", (0.6, 0, 0.0), uv=0.2)
    mb = K.MB()
    el(mb, (0, 0, 0.04), 0.11, 0.12, 0.11, "M_A3P_Iron", seg=10, rings=4, zmin=0.0)
    for k in range(3):
        mb.cyl(0, 0.02, 0.04 - k * 0.035, 0.04 - k * 0.035 + 0.03, 0.14 + k * 0.02, "M_A3P_Lacquer", seg=10)
    obj(mb, "Helmet_Kabuto", (1.2, 0, 0.0), uv=0.2)


def build_rice_bale():
    """稻捆：一捆稻草（高 0.9 m，两道草绳，穗头朝上散开）。原点 = 底；ANCHOR_Grab = 抱捆腰部。"""
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.55, 0.12, "M_A3P_Straw", seg=10, r_top=0.09)
    mb.cyl(0, 0, 0.55, 0.9, 0.09, "M_A3P_Straw", seg=10, r_top=0.2)
    for z in (0.2, 0.5):
        mb.cyl(0, 0, z, z + 0.03, 0.125 - z * 0.06, "M_A3P_Rope", seg=10)
    el(mb, (0, 0, 0.9), 0.2, 0.2, 0.06, "M_A3P_GrainDark", seg=10, rings=3, zmin=0.0)
    obj(mb, "Bale", uv=0.3)
    anchor("ANCHOR_Grab", (0, -0.15, 0.4), 0.05)


def build_fish_trap():
    """水田农具一组：FishTrap 竹鱼篓（口小肚大）、Hoe 锄头（斜靠）、Basket 竹筐。原点 = 鱼篓底。"""
    mb = K.MB()
    lathe(mb, [(0.1, 0), (0.17, 0.12), (0.15, 0.3), (0.07, 0.38), (0.08, 0.42)], "M_A3P_Bamboo", seg=10)
    for z in (0.08, 0.2, 0.32):
        hoop(mb, 0.165 if z < 0.3 else 0.1, z, "M_A3P_BambooDark", h=0.015, seg=10)
    obj(mb, "FishTrap", uv=0.2)
    hm = K.MB()
    tb(hm, (0, 0, 0), (0, 0, 1.2), 0.016, "M_A3P_Wood", seg=6)
    hm.box(-0.08, -0.18, 1.12, 0.08, -0.0, 1.2, "M_A3P_Iron")
    h = obj(hm, "Hoe", (0.4, 0.05, 0), uv=0.2)
    h.rotation_euler = (math.radians(15), 0, 0)
    bk = K.MB()
    lathe(bk, [(0.16, 0), (0.24, 0.2)], "M_A3P_Bamboo", seg=12)
    hoop(bk, 0.245, 0.19, "M_A3P_BambooDark", h=0.02, seg=12)
    obj(bk, "Basket", (-0.5, 0, 0), uv=0.2)


def build_water_clock():
    """更漏（军议 / 守夜计时）：三级铜壶阶梯滴水（木台三级），最下一只受水壶里竖一根刻箭 Float（随时间上升，
    脚本沿 Z 移动 0..0.25 m）。原点 = 木台底中心。"""
    mb = K.MB()
    for k in range(3):
        mb.box(-0.3 + k * 0.2, -0.2, 0, 0.3, 0.2, 0.25 + k * 0.25, "M_A3P_WoodDark")
    obj(mb, "Stand", uv=0.3)
    pots = K.MB()
    for k, (x, z) in enumerate(((0.2, 0.75), (0.0, 0.5), (-0.2, 0.25))):
        lathe(pots, [(0.07, z), (0.1, z + 0.08), (0.09, z + 0.18), (0.1, z + 0.2)], "M_A3P_BronzeGreen", seg=10, x=x)
        if k < 2:
            tb(pots, (x - 0.08, 0, z + 0.06), (x - 0.13, 0, z + 0.03), 0.008, "M_A3P_Bronze", seg=4)
    obj(pots, "Pots", uv=0.3)
    fl = K.MB()
    fl.box(-0.01, -0.01, 0.0, 0.01, 0.01, 0.4, "M_A3P_WoodLight")
    for k in range(8):
        fl.box(-0.012, -0.012, 0.05 + k * 0.04, 0.012, 0.012, 0.055 + k * 0.04, "M_A3P_Oil")
    obj(fl, "Float", (-0.2, 0, 0.3), uv=0.1)


def build_bell():
    """铜钟：木钟架（2.0 m 高）挂一口铜钟（口径 0.7 m），撞木 Striker 横吊在钟侧（绕吊点摆）。
    Bell 原点在钟钮（可晃）；FX_Ring = 钟声挂点；ANCHOR_Strike = 拉撞木站位。原点 = 架底中心。"""
    fr = K.MB()
    for x in (-0.7, 0.7):
        fr.box(x - 0.06, -0.06, 0, x + 0.06, 0.06, 2.1, "M_A3P_WoodDark")
        fr.box(x - 0.08, -0.3, 0, x + 0.08, 0.3, 0.1, "M_A3P_WoodDark")
    fr.box(-0.85, -0.08, 2.0, 0.85, 0.08, 2.15, "M_A3P_WoodDark")
    obj(fr, "Frame", uv=0.3)
    bl = K.MB()
    lathe(bl, [(0.35, -0.9), (0.33, -0.82), (0.27, -0.5), (0.24, -0.2), (0.2, -0.08), (0.12, 0.0)], "M_A3P_BronzeGreen", seg=16)
    for z in (-0.75, -0.45, -0.2):
        hoop(bl, 0.3 - (z + 0.75) * 0.1, z, "M_A3P_Bronze", h=0.02, seg=16)
    with bl.at(0, 0, 0.03, rx=90):
        bl.cyl(0, 0, -0.02, 0.02, 0.05, "M_A3P_Bronze", seg=8)
    obj(bl, "Bell", (0, 0, 2.0), uv=0.3)
    st = K.MB()
    with st.at(0, 0, 0, 0, 90, 0):
        st.cyl(0, 0, -0.5, 0.5, 0.06, "M_A3P_Wood", seg=8)
    for x in (-0.35, 0.35):
        tb(st, (x, 0, 0), (x * 0.5, 0, 0.7), 0.006, "M_A3P_Rope", seg=3)
    obj(st, "Striker", (0, -0.55, 1.4), uv=0.3)
    fx("FX_Ring", (0, 0, 1.5))
    anchor("ANCHOR_Strike", (0.8, -0.6, 0))


def build_gong():
    """锣：木架上挂一面铜锣（Φ0.55），锣槌 Mallet 挂在架侧（原点在握点）。FX_Ring / ANCHOR_Play。"""
    fr = K.MB()
    for x in (-0.4, 0.4):
        tb(fr, (x, 0.2, 0), (x, 0, 1.6), 0.03, "M_A3P_WoodDark", seg=6)
        tb(fr, (x, -0.2, 0), (x, 0, 1.6), 0.03, "M_A3P_WoodDark", seg=6)
    tb(fr, (-0.45, 0, 1.6), (0.45, 0, 1.6), 0.03, "M_A3P_WoodDark", seg=6)
    for x in (-0.12, 0.12):
        tb(fr, (x, 0, 1.6), (x, 0, 1.45), 0.004, "M_A3P_Rope", seg=3)
    obj(fr, "Frame", uv=0.3)
    gm = K.MB()
    with gm.at(0, 0, 0, rx=90):
        gm.cyl(0, 0, -0.03, 0.0, 0.275, "M_A3P_Bronze", seg=16)
        gm.cyl(0, 0, -0.05, -0.03, 0.08, "M_A3P_Bronze", seg=10)
    obj(gm, "Gong", (0, 0, 1.17), uv=0.3)
    ml = K.MB()
    tb(ml, (0, 0, -0.1), (0, 0, 0.25), 0.012, "M_A3P_Wood", seg=6)
    el(ml, (0, 0, 0.28), 0.04, 0.04, 0.04, "M_A3P_Cloth", seg=6, rings=3)
    obj(ml, "Mallet", (0.48, 0, 1.0), uv=0.2)
    fx("FX_Ring", (0, -0.05, 1.17))
    anchor("ANCHOR_Play", (0, -0.6, 0))


def build_horn():
    """号角：弯牛角（0.45 m）+ 铜吹口 + 背带。原点 = 握点（角身中段），+Z 朝喇叭口；FX_Sound = 喇叭口。"""
    mb = K.MB()
    pts = []
    for i in range(9):
        t = i / 8
        pts.append((Vector((0, -0.08 * math.sin(math.pi * t), -0.18 + 0.4 * t)), 0.012 + 0.045 * t ** 1.6))
    for (a, ra), (b, rb) in zip(pts, pts[1:]):
        tb(mb, a, b, ra, "M_A3P_Horn", seg=8, r1=rb)
    mb.cyl(0, 0, -0.2, -0.17, 0.016, "M_A3P_Brass", seg=8)
    for t in (0.3, 0.75):
        p = pts[int(t * 8)][0]
        mb.cyl(p.x, p.y, p.z, p.z + 0.015, pts[int(t * 8)][1] + 0.004, "M_A3P_Brass", seg=8)
    obj(mb, "Horn", uv=0.1)
    fx("FX_Sound", (0, 0, 0.23))


def build_torch():
    """火把：0.7 m 木柄，顶上缠油布头，NOCOL_Fire 火苗；原点 = 握点（离柄尾 0.15 m），+Z 朝火头。
    插在墙上 / 地上时整件立着即可。FX_Fire = 火头。"""
    mb = K.MB()
    mb.cyl(0, 0, -0.15, 0.5, 0.018, "M_A3P_Wood", seg=6, r_top=0.022)
    mb.cyl(0, 0, 0.45, 0.62, 0.04, "M_A3P_Cloth", seg=8, r_top=0.035)
    for z in (0.48, 0.58):
        mb.cyl(0, 0, z, z + 0.012, 0.043, "M_A3P_Rope", seg=8)
    obj(mb, "Torch", uv=0.2)
    fl = K.MB()
    flame(fl, 0, 0, 0.6, 0.05, 0.25)
    obj(fl, "NOCOL_Fire", uv=0.2)
    fx("FX_Fire", (0, 0, 0.7))


def build_lantern():
    """灯笼（祠堂 / 街）：竹骨纸灯笼（Φ0.32×0.42 m）挂在一根短挑杆上；Lantern 原点在挂钩（可晃），
    前面一片 NOCOL_Lantern_Face 0..1 UV 面片（贴「王」等字，换贴图即可），FX_Glow 灯光。原点 = 挂钩上方挑杆根部（挂墙）。"""
    mb = K.MB()
    tb(mb, (0, 0.05, 0), (0, -0.45, 0.06), 0.015, "M_A3P_WoodDark", seg=6)
    mb.box(-0.06, 0.03, -0.1, 0.06, 0.06, 0.1, "M_A3P_WoodDark")
    obj(mb, "Bracket", uv=0.2)
    lm = K.MB()
    tb(lm, (0, 0, 0), (0, 0, -0.06), 0.003, "M_A3P_Rope", seg=3)
    lm.cyl(0, 0, -0.1, -0.07, 0.08, "M_A3P_LanternCap", seg=10)
    lathe(lm, [(0.09, -0.52), (0.15, -0.42), (0.16, -0.31), (0.15, -0.2), (0.09, -0.1)], "M_A3P_Lantern", seg=12)
    lm.cyl(0, 0, -0.55, -0.52, 0.085, "M_A3P_LanternCap", seg=10)
    tb(lm, (0, 0, -0.55), (0, 0, -0.68), 0.012, "M_A3P_Red", seg=5, r1=0.02)
    lan = obj(lm, "Lantern", (0, -0.45, 0.03), uv=0.2)
    m = K.get_mat("M_A3P_Lantern")
    face = T3.quad_xz("NOCOL_Lantern_Face", -0.08, 0.08, -0.42, -0.2, -0.165, m, parent=lan)
    fx("FX_Glow", (0, -0.45, -0.3))


def build_sandbag():
    """沙袋：Sandbag 单袋（0.5×0.3×0.15，原点 = 底），Stack 八袋两层错缝垛（街垒 / 城墙补口）。"""
    mb = K.MB()
    el(mb, (0, 0, 0.075), 0.25, 0.15, 0.08, "M_A3P_Sand", seg=8, rings=3, zmin=-0.9)
    mb.box(0.2, -0.04, 0.03, 0.27, 0.04, 0.11, "M_A3P_Rope")
    obj(mb, "Sandbag", uv=0.3)
    mb = K.MB()
    rng = random.Random(41)
    for row, n in ((0, 5), (1, 3)):
        for i in range(n):
            x = -1.0 + i * 0.5 + row * 0.25
            with mb.at(x, 0, row * 0.15, rng.uniform(-5, 5)):
                el(mb, (0, 0, 0.075), 0.25, 0.15, 0.08, "M_A3P_Sand", seg=8, rings=3, zmin=-0.9)
    obj(mb, "Stack", (1.2, 0, 0), uv=0.3)


def build_rope_coil():
    """绳卷：一盘麻绳（Φ0.45），一头拖出 0.6 m。原点 = 底；ANCHOR_Grab。"""
    mb = K.MB()
    for k in range(6):
        r = 0.2 - (k % 3) * 0.04
        z = 0.02 + (k // 3) * 0.035
        for i in range(12):
            a0, a1 = 2 * math.pi * i / 12, 2 * math.pi * (i + 1) / 12
            tb(mb, (r * math.cos(a0), r * math.sin(a0), z), (r * math.cos(a1), r * math.sin(a1), z), 0.016, "M_A3P_Rope", seg=4)
    tb(mb, (0.2, 0, 0.02), (0.5, -0.4, 0.016), 0.016, "M_A3P_Rope", seg=4)
    obj(mb, "Rope", uv=0.2)
    anchor("ANCHOR_Grab", (0, -0.2, 0.06), 0.04)


# ====================================================================== 注册
def recipes():
    R = {
        "PROP_A3_BlameBook": build_blame_book, "PROP_A3_NameWall": build_name_wall, "PROP_A3_NameTag": build_name_tag,
        "PROP_A3_GrainSack": build_grain_sack, "PROP_A3_GrainMeasure": build_grain_measure, "PROP_A3_GrainCart": build_grain_cart,
        "PROP_A3_SignalFlag": build_signal_flag, "PROP_A3_WarDrum": build_war_drum, "PROP_A3_Brazier": build_brazier,
        "PROP_A3_ArrowBundle": build_arrow_bundle, "PROP_A3_RockPile": build_rock_pile, "PROP_A3_OilJar": build_oil_jar,
        "PROP_A3_Barricade": build_barricade, "PROP_A3_GateBoom": build_gate_boom, "PROP_A3_Skiff": build_skiff,
        "PROP_A3_WaterTrough": build_water_trough, "PROP_A3_Bucket": build_bucket, "PROP_A3_UnitMarker": build_unit_marker,
        "PROP_A3_WallBanner": build_wall_banner, "PROP_A3_Key": build_key, "PROP_A3_FireBasket": build_fire_basket,
        "PROP_A3_CannonTools": build_cannon_tools, "PROP_A3_SluiceTools": build_sluice_tools,
        "PROP_A3_CorpseCover": build_corpse_cover,
        "PROP_A3_Cannonball": build_cannonball, "PROP_A3_PowderKeg": build_powder_keg, "PROP_A3_ArrowStuck": build_arrow_stuck,
        "PROP_A3_ShieldBroken": build_shield_broken, "PROP_A3_Helmet": build_helmet, "PROP_A3_RiceBale": build_rice_bale,
        "PROP_A3_FishTrap": build_fish_trap, "PROP_A3_WaterClock": build_water_clock, "PROP_A3_Bell": build_bell,
        "PROP_A3_Gong": build_gong, "PROP_A3_Horn": build_horn, "PROP_A3_Torch": build_torch, "PROP_A3_Lantern": build_lantern,
        "PROP_A3_Sandbag": build_sandbag, "PROP_A3_RopeCoil": build_rope_coil,
    }
    return {k: ("Props", v) for k, v in R.items()}
