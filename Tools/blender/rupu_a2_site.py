"""
《入谱》第二幕补缺口：世界里的城墙生长 / 合龙、工地 overlay、北门殉难战后现场
（Blender bpy，程序化白模；由 build_yongchang.py 自动导入，recipes() 返回 {资产名: (分类, 生成函数)}）

对应 Docs/第二幕_策划对照与建模缺口.md §5 P0「明代城墙 / 工地 overlay」、§9 第四步 2/5、第五步 2。说明见 Docs/act2_site.md。

约定（与 rupu_ming_civic 一致）：
  - 正面朝 Blender -Y（团结 +Z）= 城外；1 unit = 1 m。
  - 城墙件和 BLD_Wall_Seg 完全对齐：8 m 一段（x -4..4），原点在墙中线地面，墙高 7.0，走道面 7.08，外侧收分。
  - 状态件是固定名字的子物体 / 组（Stage_0..3、Gap_Fill……），团结里 SetActive 或插值 Transform；
    FX_* 特效挂点；ANCHOR_* 站位 / 交互点 / 动画参考位；NOCOL_* 不加碰撞（贴花、绳）。
  - 新材质前缀 M_A2S_*（颜色写在 Base Color）；工地材质沿用 rupu_ming_civic 的 M_MC_*。
"""
import math
import random

import bpy
from mathutils import Vector

import rupu_kit as K
import rupu_ming_civic as MC

WALK = 7.08

K.PALETTE.update({
    "M_A2S_Blood": "#4a3128",        # 血迹（低饱和暗褐，干后发黑）
    "M_A2S_BloodDry": "#5b4334",     # 拖痕 / 溅点（更淡）
    "M_A2S_Scorch": "#2f2a25",       # 火罐烧痕
    "M_A2S_Rattan": "#8a7448",       # 藤牌
    "M_A2S_RattanDark": "#5e4e32",   # 藤牌圈纹
    "M_A2S_Fletch": "#c8bfa8",       # 箭羽
    "M_A2S_Trample": "#6d6150",      # 踩烂的泥
    "M_A2S_Thatch": "#8f7d55",       # 工棚草顶
})

obj, anchor, fx, beam, group, under = MC.obj, MC.anchor, MC.fx, MC.beam, MC.group, MC.under
y_out, wall_slice, wall_body = MC.y_out, MC.wall_slice, MC.wall_body


def ref_loc(name, loc):
    """位置参考（动画起点等）。"""
    return MC._empty(name, loc, "CUBE", 0.25)


# ====================================================================== 共用小件
def stake(mb, x, y, h=0.8, tip=True):
    mb.box(x - 0.05, y - 0.05, 0, x + 0.05, y + 0.05, h, "M_Wood")
    if tip:
        mb.box(x - 0.06, y - 0.06, h - 0.14, x + 0.06, y + 0.06, h + 0.02, "M_MC_StakeTip")


def batter_board(mb, x, y, span=1.6, axis="y"):
    """龙门板（放线架）：两桩 + 横板，axis 是横板方向。"""
    for d in (-span / 2, span / 2):
        px, py = (x, y + d) if axis == "y" else (x + d, y)
        mb.box(px - 0.05, py - 0.05, 0, px + 0.05, py + 0.05, 1.0, "M_Wood")
    if axis == "y":
        mb.box(x - 0.03, y - span / 2 - 0.1, 0.78, x + 0.03, y + span / 2 + 0.1, 0.92, "M_MC_Plank")
    else:
        mb.box(x - span / 2 - 0.1, y - 0.03, 0.78, x + span / 2 + 0.1, y + 0.03, 0.92, "M_MC_Plank")


def ram_form(mb, x0, x1, y0, y1, z0, z_fill, z_top, earth_mats=("M_MC_RammedEarth", "M_MC_EarthLayer")):
    """夯土板筑模板：两侧木模板（三块横板）+ 两端挡板 + 外侧立柱（成对，顶上穿杆）+ 模内分层夯土（z0..z_fill，0.15 一层）。"""
    n = max(1, int(round((z_fill - z0) / 0.15)))
    for k in range(n):
        za, zb = z0 + (z_fill - z0) * k / n, z0 + (z_fill - z0) * (k + 1) / n
        mb.box(x0, y0, za, x1, y1, zb, earth_mats[k % 2])
    t = 0.06
    for k in range(3):                                                    # 横板
        za = z_top - 0.3 * (k + 1)
        mb.box(x0, y0 - t, za + 0.01, x1, y0, za + 0.29, "M_MC_Plank")
        mb.box(x0, y1, za + 0.01, x1, y1 + t, za + 0.29, "M_MC_Plank")
    for x in (x0 - t, x1):                                                # 挡板
        mb.box(x, y0 - t, z_top - 0.9, x + t, y1 + t, z_top, "M_MC_Plank")
    L = x1 - x0
    m = max(2, int(L / 1.2) + 1)
    for i in range(m):                                                    # 立柱 + 穿杆
        x = x0 + 0.15 + (L - 0.3) * i / (m - 1)
        for y in (y0 - t - 0.06, y1 + t + 0.06):
            mb.box(x - 0.05, y - 0.05, z_top - 1.1, x + 0.05, y + 0.05, z_top + 0.2, "M_Wood_Dark")
        mb.box(x - 0.03, y0 - 0.2, z_top + 0.05, x + 0.03, y1 + 0.2, z_top + 0.11, "M_Wood_Dark")


def rammer(mb, x, y, z=0.0, lean=0.0):
    """夯杵（立着 / 斜靠）：木杆 + 石夯头。"""
    with mb.at(x, y, z, 0, lean, 0):
        mb.cyl(0, 0, 0, 0.25, 0.13, "M_MC_StoneNew", seg=6)
        mb.cyl(0, 0, 0.25, 1.6, 0.035, "M_Wood", seg=5)
        mb.box(-0.25, -0.02, 1.3, 0.25, 0.02, 1.35, "M_Wood")


def stone_block(mb, x, y, z, sx, sy, sz, rz=0.0, mat="M_MC_StoneNew"):
    with mb.at(x, y, z, rz):
        mb.box(-sx / 2, -sy / 2, 0, sx / 2, sy / 2, sz - 0.03, mat)
        mb.box(-sx / 2 + 0.03, -sy / 2 + 0.03, sz - 0.03, sx / 2 - 0.03, sy / 2 - 0.03, sz, mat)


def stone_stack(mb, x, y, rows=3, n0=4, sx=1.1, sy=0.55, sz=0.42, rz=0.0):
    """条石垛（下宽上窄），底下两根垫木。"""
    with mb.at(x, y, 0, rz):
        w = n0 * (sx + 0.05)
        for yy in (-sy * 0.3, sy * 0.3):
            mb.box(-w / 2, yy - 0.06, 0, w / 2, yy + 0.06, 0.1, "M_Wood_Dark")
        for r in range(rows):
            n = n0 - r
            for i in range(n):
                cx = -(n - 1) * (sx + 0.05) / 2 + i * (sx + 0.05)
                stone_block(mb, cx, 0, 0.1 + r * sz, sx, sy, sz)


def rubble(mb, x, y, r, h, mat="M_Stone_Base", seg=8):
    mb.cyl(x, y, 0, h, r, mat, seg=seg, r_top=r * 0.25)


def mortar_station(mb, x, y, rng):
    """灰浆站：拌灰槽（槽里灰浆面）、石灰堆、两只灰桶、灰耙。"""
    mb.frustum((x - 1.4, y - 0.5, x + 1.4, y + 0.5), (x - 1.5, y - 0.6, x + 1.5, y + 0.6), 0, 0.5, "M_MC_Plank")
    mb.box(x - 1.38, y - 0.5, 0.36, x + 1.38, y + 0.5, 0.44, "M_MC_Lime")
    mb.cyl(x + 2.4, y + 0.2, 0, 0.75, 0.95, "M_MC_Lime", seg=9, r_top=0.18)
    for bx, by in ((x - 2.1, y - 0.2), (x - 2.0, y + 0.55)):
        mb.cyl(bx, by, 0, 0.42, 0.22, "M_MC_Plank", seg=8, r_top=0.26)
        mb.cyl(bx, by, 0.36, 0.39, 0.235, "M_MC_Lime", seg=8)
        mb.cyl(bx, by, 0.1, 0.14, 0.24, "M_MC_Iron", seg=8)
    beam(mb, (x - 0.6, y - 0.1, 0.45), (x + 0.6, y - 1.2, 0.05), 0.04, "M_Wood")          # 灰耙柄
    mb.box(x - 0.78, y - 0.05, 0.38, x - 0.42, y + 0.02, 0.5, "M_MC_Iron")


def timber_pile(mb, x, y, n=7, L=4.0, r=0.13, rz=0.0):
    """原木 / 方料堆：两根垫木 + 两层原木（沿本地 X）。"""
    with mb.at(x, y, 0, rz):
        w = n * 2 * r + 0.2
        for xx in (-L * 0.3, L * 0.3):
            mb.box(xx - 0.08, -w / 2, 0, xx + 0.08, w / 2, 0.12, "M_Wood_Dark")
        for i in range(n):
            yy = -(n - 1) * r + i * 2 * r
            with mb.at(0, yy, 0.12 + r, 0, 0, 90):
                mb.cyl(0, 0, -L / 2, L / 2, r, "M_MC_Log", seg=6)
        for i in range(n - 2):
            yy = -(n - 3) * r + i * 2 * r
            with mb.at(0.1, yy, 0.12 + 2.7 * r, 0, 0, 90):
                mb.cyl(0, 0, -L / 2 + 0.3, L / 2 - 0.2, r, "M_MC_Log", seg=6)


def plank_stack(mb, x, y, n=6, L=3.0, rz=0.0):
    with mb.at(x, y, 0, rz):
        for xx in (-L * 0.35, L * 0.35):
            mb.box(xx - 0.07, -0.4, 0, xx + 0.07, 0.4, 0.1, "M_Wood_Dark")
        for k in range(n):
            off = 0.04 * ((k * 7) % 3 - 1)
            mb.box(-L / 2 + off, -0.35, 0.1 + k * 0.06, L / 2 + off, 0.35, 0.1 + k * 0.06 + 0.05, "M_MC_Plank")


def bamboo_bundle(mb, x, y, n=9, L=6.0, rz=0.0, z=0.0, tilt=0.0):
    """毛竹捆（沿本地 X，两道草绳）。tilt 是绕本地 Y 的倾角（斜靠用）。"""
    with mb.at(x, y, z, rz, 0, tilt):
        for i in range(n):
            a = i * 2.4
            rr = 0.0 if i == 0 else 0.07 + 0.06 * (i // 6)
            yy, zz = rr * math.cos(a), 0.06 + 0.05 + rr * math.sin(a) + 0.07
            with mb.at(0, yy, zz, 0, 0, 90):
                mb.cyl(0, 0, -L / 2 + 0.05 * (i % 3), L / 2 - 0.08 * (i % 2), 0.045, "M_MC_Bamboo", seg=5)
        for xx in (-L * 0.3, L * 0.3):
            with mb.at(xx, 0, 0.18, 0, 0, 90):
                mb.cyl(0, 0, -0.05, 0.05, 0.2, "M_MC_Straw", seg=6)


def bucket(mb, x, y, fill="M_MC_Lime"):
    mb.cyl(x, y, 0, 0.42, 0.2, "M_MC_Plank", seg=8, r_top=0.24)
    mb.cyl(x, y, 0.08, 0.12, 0.215, "M_MC_Iron", seg=8)
    if fill:
        mb.cyl(x, y, 0.36, 0.39, 0.22, fill, seg=8)


def barrow(mb, x, y, rz=0.0, tipped=False):
    """独轮车（低模）：轮 + 两根车把 + 车斗。tipped=True 侧翻（战后现场）。"""
    with mb.at(x, y, 0.0 if not tipped else 0.35, rz, 75 if tipped else 0, 0):
        with mb.at(0, -0.7, 0.3, 0, 0, 90):
            mb.cyl(0, 0, -0.05, 0.05, 0.3, "M_Wood_Dark", seg=10)
        for sx in (-0.3, 0.3):
            beam(mb, (sx * 0.6, -0.7, 0.3), (sx, 1.0, 0.55), 0.06, "M_Wood")
            mb.box(sx - 0.03, 0.55, 0, sx + 0.03, 0.62, 0.45, "M_Wood_Dark")
        mb.frustum((-0.28, -0.5, 0.28, 0.4), (-0.38, -0.6, 0.38, 0.5), 0.35, 0.6, "M_MC_Plank")


# ====================================================================== 1. 城墙分阶段段 BLD_Wall_Seg_Build
def r_wall_seg_build():
    """与 BLD_Wall_Seg 同占地（8 m，x -4..4，墙中线地面为原点）的四个施工阶段，互斥显示（一次只开一个）：
    Stage_0 基槽 / 放线：踩实基槽 + 基槽里头一层毛石 + 两侧弃土埂 + 内外两道木桩线（红头、拉麻线）+ 两端龙门板
    Stage_1 半高墙 + 模板：条石基础 -0.5..1.5，外包石半砌到 2.5，内芯夯土到 3.0，顶上夯土模板（3.0..3.6 新一版正在夯）
    Stage_2 墙身无垛：新石墙身砌到 7.0 + 走道铺面 7.08 + 内侧压檐石，外侧垛墙只砌了两块墙根
    Stage_3 完成：与 BLD_Wall_Seg 同几何、同材质（换成它不会跳）。
    「墙线 → 世界城墙段出现」：Stage_k 从 -Z 升起（或缩放 Z 0→1）0.6 s，配 FX_WallRise / FX_RamDust。"""
    root = group("BLD_Wall_Seg_Build")
    rng = random.Random(8)
    # ---- Stage_0
    s0 = K.MB()
    s0.box(-4, -2.75, 0.0, 4, 2.6, 0.03, "M_Mud")                          # 基槽底（踩实）
    for x in range(-4, 4):                                                # 头一层毛石
        if rng.random() < 0.8:
            stone_block(s0, x + 0.5, rng.uniform(-1.6, 1.4), 0.03, rng.uniform(0.7, 0.95), rng.uniform(0.6, 1.2), 0.35,
                        rng.uniform(-8, 8), "M_Stone_Base")
    for y0, y1 in ((-3.9, -3.0), (2.85, 3.8)):                            # 弃土埂
        s0.prism([(y0, 0.0), (y1, 0.0), ((y0 + y1) / 2 + 0.1, 0.45), ((y0 + y1) / 2 - 0.1, 0.45)], "x", -4, 4, "M_MC_RammedEarth")
    for x in (-3.5, -1.5, 0.5, 2.5):                                      # 两道木桩线 + 麻线
        stake(s0, x, -2.75)
        stake(s0, x, 2.6)
    for y in (-2.75, 2.6):
        s0.box(-4, y - 0.01, 0.66, 4, y + 0.01, 0.68, "M_MC_Rope")
    for x in (-4.2, 4.2):
        batter_board(s0, x, -2.75, 0.9)
        batter_board(s0, x, 2.6, 0.9)
    s0.box(-0.2, -0.2, 0.03, 0.2, 0.2, 0.9, "M_Wood")                     # 中线桩
    under(root, obj(s0, "Stage_0"))
    # ---- Stage_1
    s1 = K.MB()
    wall_slice(s1, -4, 4, -0.5, 0.5, "M_Stone_Base")
    wall_slice(s1, -4, 4, 0.5, 1.5, "M_MC_StoneNew")
    s1.box(-4, -2.75, -0.5, 4, -2.35, 0.45, "M_Stone_Base")
    for k in range(3):                                                    # 夯土芯 1.5..3.0（内侧露夯层）
        za, zb = 1.5 + k * 0.5, 2.0 + k * 0.5
        s1.prism([(y_out(za) + 0.7, za), (2.5, za), (2.5, zb), (y_out(zb) + 0.7, zb)], "x", -4, 4,
                 "M_MC_RammedEarth" if k % 2 == 0 else "M_MC_EarthLayer")
    s1.prism([(y_out(1.5), 1.5), (y_out(1.5) + 0.7, 1.5), (y_out(2.5) + 0.7, 2.5), (y_out(2.5), 2.5)], "x", -4, 4, "M_MC_StoneNew")
    for i in range(7):                                                    # 外包石顶零散石块
        if rng.random() < 0.6:
            x = -3.8 + i * 1.1
            s1.box(x, y_out(2.5) + 0.02, 2.5, x + 0.8, y_out(2.5) + 0.62, 2.75, "M_MC_StoneNew")
    ram_form(s1, -4.0, 4.0, y_out(3.0) + 0.7, 2.5, 3.0, 3.25, 3.6)        # 顶上正在夯的一版
    rammer(s1, -1.5, 1.2, 3.25)
    rammer(s1, 1.8, 0.6, 3.25)
    under(root, obj(s1, "Stage_1"))
    # ---- Stage_2
    s2 = K.MB()
    wall_slice(s2, -4, 4, -0.5, 0.5, "M_Stone_Base")
    wall_slice(s2, -4, 4, 0.5, 7.0, "M_MC_StoneNew")
    s2.box(-4, -2.75, -0.5, 4, -2.35, 0.45, "M_Stone_Base")
    s2.box(-4, -1.5, 7.0, 4, 2.5, WALK, "M_Wall_Top")
    s2.box(-4, 2.35, 6.75, 4, 2.6, 7.0, "M_Stone_Base")
    for x in (-3.2, 1.0):                                                 # 垛墙墙根（刚起两块）
        s2.box(x, -2.1, 7.0, x + 1.4, -1.5, 7.45, "M_MC_StoneNew")
    for z in (1.5, 3.0, 4.5, 6.0):                                        # 灰缝线
        s2.box(-4, y_out(z) - 0.02, z - 0.02, 4, y_out(z) + 0.02, z + 0.02, "M_MC_Lime")
    under(root, obj(s2, "Stage_2"))
    # ---- Stage_3（= BLD_Wall_Seg）
    s3 = K.MB()
    wall_body(s3, -4, 4)
    s3.box(-0.2, -2.45, 6.4, 0.2, -1.9, 6.6, "M_Stone_Base")
    under(root, obj(s3, "Stage_3"))
    under(root, fx("FX_WallRise", 0, 0, 0.5), fx("FX_RamDust", 0, 1.2, 3.3))
    under(root, anchor("ANCHOR_Ram_1", -1.5, 1.2, 3.25), anchor("ANCHOR_Ram_2", 1.8, 0.6, 3.25),
          anchor("ANCHOR_Stake_Out", 0, -3.3, 0), anchor("ANCHOR_Walk", 0, 0.5, WALK))


# ====================================================================== 2. 合龙缺口 BLD_Wall_Gap
GAP_X = 3.0          # 缺口半宽（x -3..3），两端 x ±3..±4 是已砌墙头
GAP_Z0 = 2.5         # 缺口底（合龙前砌到这里）
TOOTH = 0.5          # 留槎伸出长度


def _tooth_course(k):
    """第 k 层（自 GAP_Z0 起 0.5 m 一层）两端墙头是否伸出半块（留槎）。"""
    return k % 2 == 0


def r_wall_gap():
    """合龙缺口件（与 BLD_Wall_Seg 同占地，原点墙中线地面）。
    BLD_Wall_Gap：全长墙基砌到 2.5，两端 x ±3..±4 砌到顶（走道、垛墙），墙头每隔一层伸出半块（留槎）。
    Gap_Fill：最后一段（x -3..3，2.5 → 垛口），层层与留槎咬合，外面嵌合龙石（M_Plaque）。原点 = 合龙段底面中心 (0, 0, 2.5)。
      推合方向：从城内一侧（+Y）沿 -Y 平推进缺口。起点参考 ANCHOR_GapFill_Start（y +5.6，整块已离开墙体），
      终点就是它自己的位置。也可以改成从上往下吊入（起点 z +6），咬合方向同样不冲突。
    Gap_Barricade：缺口里临时堵的木栅 + 沙土袋（殉难段「墙没合龙」时显示；合龙后隐藏）。"""
    G = K.MB()
    wall_slice(G, -4, 4, -0.5, 0.5, "M_Stone_Base")
    wall_slice(G, -4, 4, 0.5, GAP_Z0, "M_MC_StoneNew")
    G.box(-4, -2.75, -0.5, 4, -2.35, 0.45, "M_Stone_Base")
    for s in (-1, 1):
        a, b = sorted((s * GAP_X, s * 4.0))
        wall_slice(G, a, b, GAP_Z0, 7.0, "M_MC_StoneNew")
        G.box(a, -1.5, 7.0, b, 2.5, WALK, "M_Wall_Top")
        G.box(a, 2.35, 6.75, b, 2.6, 7.0, "M_Stone_Base")
        G.box(a, -2.1, 7.0, b, -1.5, 7.95, "M_Wall_Stone")
        G.box(a, -2.2, 7.95, b, -1.4, 8.05, "M_Wall_Top")
        for k in range(9):                                                # 留槎
            za = GAP_Z0 + k * 0.5
            if _tooth_course(k):
                ta, tb = sorted((s * GAP_X, s * (GAP_X - TOOTH)))
                G.prism([(y_out(za), za), (2.5, za), (2.5, za + 0.5), (y_out(za + 0.5), za + 0.5)], "x", ta, tb, "M_MC_StoneNew")
    G.box(-GAP_X + TOOTH, -1.0, GAP_Z0, GAP_X - TOOTH, 2.0, GAP_Z0 + 0.04, "M_MC_Lime")   # 缺口底铺好的灰浆
    obj(G, "BLD_Wall_Gap")
    # ---- Gap_Fill（本地原点 = 底面中心）
    F = K.MB()
    for k in range(9):
        za = k * 0.5
        w = GAP_X - TOOTH if _tooth_course(k) else GAP_X
        F.prism([(y_out(za + GAP_Z0), za), (2.5, za), (2.5, za + 0.5), (y_out(za + 0.5 + GAP_Z0), za + 0.5)], "x", -w, w,
                "M_MC_StoneNew")
    zt = 7.0 - GAP_Z0
    F.box(-GAP_X, -1.5, zt, GAP_X, 2.5, zt + 0.08, "M_Wall_Top")
    F.box(-GAP_X, 2.35, zt - 0.25, GAP_X, 2.6, zt, "M_Stone_Base")
    F.box(-GAP_X, -2.1, zt, GAP_X, -1.5, zt + 0.95, "M_Wall_Stone")
    F.box(-GAP_X, -2.2, zt + 0.95, GAP_X, -1.4, zt + 1.05, "M_Wall_Top")
    F.crenels(-4, 4, -2.1, -1.5, zt + 1.05, zt + 1.75, "M_Wall_Stone")
    zp = 4.6 - GAP_Z0
    F.box(-0.9, y_out(5.0) - 0.08, zp, 0.9, y_out(5.0) + 0.02, zp + 0.8, "M_Plaque")   # 合龙石（刻字）
    obj(F, "Gap_Fill", (0, 0, GAP_Z0))
    ref_loc("ANCHOR_GapFill_Start", (0, 5.6, GAP_Z0))
    # ---- Gap_Barricade（缺口里的临时木栅 + 土袋）
    B = K.MB()
    for x in (-2.4, -1.2, 0.0, 1.2, 2.4):
        beam(B, (x, -0.6, GAP_Z0), (x + 0.15, -1.4, GAP_Z0 + 2.2), 0.14, "M_Wood_Dark")
    for z in (0.7, 1.5):
        B.box(-2.7, -0.95 - z * 0.18, GAP_Z0 + z, 2.7, -0.82 - z * 0.18, GAP_Z0 + z + 0.16, "M_Wood")
    for i in range(8):
        x = -2.5 + i * 0.7
        B.frustum((x - 0.32, 0.0, x + 0.32, 0.6), (x - 0.28, 0.04, x + 0.28, 0.56), GAP_Z0 + 0.04, GAP_Z0 + 0.34, "M_Sandbag")
    for i in range(5):
        x = -2.0 + i * 0.9
        B.frustum((x - 0.32, 0.0, x + 0.32, 0.6), (x - 0.28, 0.04, x + 0.28, 0.56), GAP_Z0 + 0.34, GAP_Z0 + 0.64, "M_Sandbag")
    obj(B, "Gap_Barricade")
    fx("FX_ClosureDust", 0, 0, 7.1)
    anchor("ANCHOR_Closure", 0, 0.6, GAP_Z0 + 0.04)
    anchor("ANCHOR_Gap_Defend", 0, 2.2, GAP_Z0 + 0.04)


# ====================================================================== 3. 工地 overlay：沿墙一段
def scaffold_span(mb, x0, x1, y0=2.8, y1=4.1, levels=(2.0, 4.0, 6.0), top=7.8, ladder_x=None):
    """沿墙（城内侧）一跨完整脚手架：毛竹立杆（两排）、大横杆、小横杆、跳板、外侧护栏、剪刀撑、爬梯。"""
    n = max(2, int(round((x1 - x0) / 2.6)) + 1)
    xs = [x0 + (x1 - x0) * i / (n - 1) for i in range(n)]
    for x in xs:
        for y in (y0, y1):
            mb.cyl(x, y, 0, top, 0.06, "M_MC_Bamboo", seg=6)
            mb.box(x - 0.12, y - 0.12, 0, x + 0.12, y + 0.12, 0.06, "M_MC_Plank")          # 垫板
    for z in levels:
        for y in (y0, y1):
            mb.box(x0 - 0.2, y - 0.04, z - 0.1, x1 + 0.2, y + 0.04, z - 0.02, "M_MC_Bamboo")
        for x in xs:
            mb.box(x - 0.04, y0 - 0.15, z - 0.1, x + 0.04, y1 + 0.15, z - 0.02, "M_MC_Bamboo")
            mb.box(x - 0.08, y0 - 0.08, z - 0.16, x + 0.08, y0 + 0.08, z, "M_MC_Rope")       # 绑扎
        k = int((x1 - x0) / 1.25)
        for i in range(k):
            xa = x0 + i * (x1 - x0) / k
            mb.box(xa + 0.02, y0 - 0.05, z, xa + (x1 - x0) / k - 0.02, y1 + 0.05, z + 0.05, "M_MC_Plank")
        mb.box(x0, y1 - 0.03, z + 1.0, x1, y1 + 0.03, z + 1.06, "M_MC_Bamboo")              # 护栏
    beam(mb, (x0, y1 + 0.05, 0.2), (x1, y1 + 0.05, levels[-1]), 0.07, "M_MC_Bamboo")         # 剪刀撑
    beam(mb, (x1, y1 + 0.08, 0.2), (x0, y1 + 0.08, levels[-1]), 0.07, "M_MC_Bamboo")
    if ladder_x is not None:
        for dx in (-0.25, 0.25):
            beam(mb, (ladder_x + dx, y1 + 0.9, 0), (ladder_x + dx, y1 + 0.15, levels[-1] + 0.6), 0.07, "M_Wood_Dark")
        for k in range(int(levels[-1] / 0.35)):
            t = (k + 1) * 0.35 / (levels[-1] + 0.6)
            yy = y1 + 0.9 - 0.75 * t
            mb.box(ladder_x - 0.25, yy - 0.03, t * (levels[-1] + 0.6), ladder_x + 0.25, yy + 0.03, t * (levels[-1] + 0.6) + 0.04, "M_Wood_Dark")


def r_worksite_wall():
    """沿墙 8 m 一段的工地 overlay（与 BLD_Wall_Seg / BLD_Wall_Seg_Build 同原点同旋转叠放；墙中线地面，城外 -Y）。
    子物体（都是独立网格，可单独隐藏）：
      Scaffold 城内侧满跨脚手架（2/4/6 m 三层跳板、护栏、剪刀撑、爬梯）+ 顶上吊杆滑轮
      StakeLine 城外墙脚放线桩 + 麻线 + 龙门板
      RamForm 城内地面一副夯土板筑模板（半满）+ 两根夯杵
      Mortar 灰浆站（拌灰槽、石灰堆、灰桶）
      Stones 条石垛 + 散石
      Timber 方木 / 跳板备料；Bamboo 毛竹捆（地上一捆、斜靠一捆）"""
    rng = random.Random(81)
    sc = K.MB()
    scaffold_span(sc, -3.9, 3.9, ladder_x=2.0)
    beam(sc, (-0.6, 4.1, 7.8), (-0.6, 2.0, 8.6), 0.1, "M_Wood_Dark")              # 吊杆
    sc.cyl(-0.6, 2.0, 8.35, 8.55, 0.14, "M_MC_Iron", seg=8)
    sc.box(-0.615, 1.985, 6.4, -0.585, 2.015, 8.35, "M_MC_Rope")
    sc.box(-0.8, 1.8, 6.1, -0.4, 2.2, 6.4, "M_MC_Rope")
    obj(sc, "Scaffold")
    st = K.MB()
    for x in (-3.0, -1.0, 1.0, 3.0):
        stake(st, x, -3.3)
    st.box(-4, -3.31, 0.66, 4, -3.29, 0.68, "M_MC_Rope")
    batter_board(st, -4.3, -3.3, 1.0)
    obj(st, "StakeLine")
    rf = K.MB()
    ram_form(rf, -3.6, -0.6, 5.2, 6.2, 0.0, 0.45, 0.9)
    rammer(rf, -2.4, 5.7, 0.45)
    rammer(rf, -0.2, 6.6, 0.0, 12)
    obj(rf, "RamForm")
    mo = K.MB()
    mortar_station(mo, 1.6, 6.0, rng)
    obj(mo, "Mortar")
    so = K.MB()
    stone_stack(so, 2.0, 8.0, rows=2, n0=3, rz=0)
    for _ in range(4):
        stone_block(so, rng.uniform(-3.5, -0.5), rng.uniform(7.2, 8.6), 0, rng.uniform(0.5, 0.8), 0.4, 0.35, rng.uniform(-30, 30))
    rubble(so, -3.4, 4.9, 0.5, 0.35)
    obj(so, "Stones")
    tb = K.MB()
    plank_stack(tb, -1.8, 9.0, n=5, L=3.2)
    obj(tb, "Timber")
    bb = K.MB()
    bamboo_bundle(bb, 0.0, 10.0, n=9, L=6.5)
    for i in range(7):                                                    # 斜靠在脚手架端头的一排毛竹
        x = 4.15 + 0.03 * (i % 3)
        y = 2.95 + i * 0.16
        beam(bb, (x + 1.5, y, 0.0), (x, y + 0.05, 5.6 + 0.25 * (i % 3)), 0.09, "M_MC_Bamboo")
    obj(bb, "Bamboo")
    fx("FX_Mortar", 1.6, 6.0, 0.45)
    fx("FX_RamDust", -2.1, 5.7, 0.5)
    for nm, p in (("ANCHOR_Lay_1", (-2.0, 3.45, 4.05)), ("ANCHOR_Lay_2", (1.0, 3.45, 6.05)), ("ANCHOR_Ram", (-2.4, 5.0, 0)),
                  ("ANCHOR_Mortar", (1.6, 5.1, 0)), ("ANCHOR_Carry_From", (2.0, 7.3, 0)), ("ANCHOR_Carry_To", (-0.6, 4.6, 0)),
                  ("ANCHOR_Climb", (2.0, 5.2, 0)), ("ANCHOR_Hoist", (-0.6, 2.0, 0)), ("ANCHOR_StakeLine", (0, -3.8, 0))):
        anchor(nm, *p)


# ====================================================================== 4. 工地 overlay：料场
def r_worksite_yard():
    """料场（约 22 x 16，原点场地中心地面，-Y 朝路）。子物体：
      Ground 踩实泥地；Stones 两座条石垛、块石、碎石堆、两个凿石位（垫墩 + 半成品石 + 石屑）
      Lime 石灰池（木框）+ 石灰堆 + 筛子 + 灰桶 + 水缸；Timber 原木堆 + 跳板堆 + 锯马（架着一根）
      Bamboo 竹架斜靠一排毛竹 + 地上两捆；RamForm 一副板筑模板（示范夯）；Shed 工棚（四柱单坡草顶、工具架、记名桌）
      Cart 平板车 + 独轮车；Fence 后侧木栏。"""
    rng = random.Random(56)
    g = K.MB()
    g.box(-11, -8, 0, 11, 8, 0.03, "M_Road_Earth")
    for _ in range(18):
        x, y = rng.uniform(-10, 10), rng.uniform(-7, 7)
        g.box(x - rng.uniform(0.5, 1.4), y - rng.uniform(0.4, 1.0), 0.03, x + rng.uniform(0.5, 1.4), y + rng.uniform(0.4, 1.0), 0.04,
              rng.choice(["M_Mud", "M_MC_EarthLayer", "M_MC_Lime"]))
    obj(g, "Ground", uv=4.0)
    s = K.MB()
    stone_stack(s, -7.0, 4.6, rows=3, n0=4)
    stone_stack(s, -7.4, 1.6, rows=2, n0=3, sx=0.9, sy=0.5, sz=0.38, rz=8)
    for _ in range(9):
        stone_block(s, rng.uniform(-9.5, -3.5), rng.uniform(-2.5, -0.6), 0.03, rng.uniform(0.4, 0.8), rng.uniform(0.3, 0.5),
                    rng.uniform(0.25, 0.4), rng.uniform(0, 90))
    rubble(s, -3.2, 5.6, 1.1, 0.8)
    rubble(s, -2.0, 6.4, 0.6, 0.45)
    for cx, cy in ((-4.6, -4.4), (-2.4, -4.6)):                            # 凿石位
        s.box(cx - 0.35, cy - 0.35, 0.03, cx + 0.35, cy + 0.35, 0.5, "M_Wood_Dark")
        stone_block(s, cx, cy, 0.5, 0.9, 0.45, 0.4, 15)
        for _ in range(6):
            a, r = rng.uniform(0, 6.28), rng.uniform(0.5, 1.0)
            s.box(cx + r * math.cos(a) - 0.06, cy + r * math.sin(a) - 0.05, 0.03, cx + r * math.cos(a) + 0.06,
                  cy + r * math.sin(a) + 0.05, 0.08, "M_MC_StoneNew")
    obj(s, "Stones")
    l = K.MB()
    l.box(1.0, 3.6, 0, 4.4, 6.0, 0.4, "M_MC_Plank")                        # 石灰池
    l.box(1.12, 3.72, 0.28, 4.28, 5.88, 0.34, "M_MC_Lime")
    l.cyl(5.8, 5.0, 0, 1.0, 1.3, "M_MC_Lime", seg=10, r_top=0.25)
    with l.at(2.6, 2.6, 0, 20):                                            # 筛子（斜架）
        beam(l, (-0.5, 0, 0), (-0.5, 0.5, 0.9), 0.05, "M_Wood")
        beam(l, (0.5, 0, 0), (0.5, 0.5, 0.9), 0.05, "M_Wood")
        l.box(-0.6, 0.2, 0.55, 0.6, 0.35, 0.62, "M_MC_Rope")
    for x, y in ((4.8, 3.2), (5.4, 3.6), (0.6, 2.8)):
        bucket(l, x, y)
    MC.jar(l, 0.4, 6.3, 0.0, 0.45, 0.8, "M_MC_Clay")
    l.cyl(0.4, 6.3, 0.72, 0.74, 0.4, "M_Water", seg=12)
    obj(l, "Lime")
    t = K.MB()
    timber_pile(t, 6.6, -1.0, n=7, L=4.5)
    plank_stack(t, 7.2, -4.4, n=7, L=3.4)
    for x in (3.6, 5.0):                                                   # 锯马
        beam(t, (x, -4.6, 0), (x, -4.2, 0.85), 0.06, "M_Wood_Dark")
        beam(t, (x, -3.8, 0), (x, -4.2, 0.85), 0.06, "M_Wood_Dark")
    with t.at(4.3, -4.2, 0.95, 0, 0, 90):
        t.cyl(0, 0, -1.6, 1.6, 0.14, "M_MC_Log", seg=6)
    obj(t, "Timber")
    b = K.MB()
    for x in (8.2, 10.2):                                                  # 竹架
        b.box(x - 0.06, 5.9, 0, x + 0.06, 6.0, 2.2, "M_Wood_Dark")
    b.box(7.9, 5.9, 2.0, 10.5, 6.0, 2.1, "M_Wood_Dark")
    for i in range(14):
        x = 7.9 + i * 0.19
        beam(b, (x, 5.0, 0.0), (x + 0.05, 6.05, 2.15 + 0.6 * (i % 3) / 2), 0.08, "M_MC_Bamboo")
    bamboo_bundle(b, 8.6, 3.6, n=9, L=6.0, rz=0)
    bamboo_bundle(b, 8.8, 2.8, n=7, L=5.5, rz=4)
    obj(b, "Bamboo")
    rf = K.MB()
    ram_form(rf, -1.2, 1.8, -1.8, -0.6, 0.03, 0.6, 1.2)
    rammer(rf, 0.0, -1.2, 0.6)
    rammer(rf, 2.4, -2.2, 0.03, 10)
    obj(rf, "RamForm")
    sh = K.MB()                                                            # 工棚：x -1..4, y -7.5..-5
    for x in (-1.0, 4.0):
        for y, h in ((-7.5, 2.4), (-5.0, 3.0)):
            sh.box(x - 0.08, y - 0.08, 0, x + 0.08, y + 0.08, h, "M_Wood_Dark")
    sh.shed_roof(-1.5, 4.5, -4.5, -8.0, 3.15, 2.25, "M_A2S_Thatch", t=0.22)
    sh.box(-0.6, -7.3, 0.0, 1.8, -6.8, 1.6, "M_Wood_Dark")                  # 工具架
    for i in range(6):
        x = -0.4 + i * 0.4
        beam(sh, (x, -6.75, 0.05), (x + 0.05, -6.95, 1.75), 0.04, "M_Wood")
        sh.box(x - 0.1, -6.78, 0.0, x + 0.12, -6.7, 0.3, "M_MC_Iron" if i % 2 else "M_MC_Plank")
    MC.table(sh, 2.2, -6.6, 3.6, -5.8, 0.0, 0.8, "M_Wood")                  # 记名桌
    sh.box(2.5, -6.4, 0.8, 3.1, -6.0, 0.83, "M_Paper")
    sh.box(3.2, -6.4, 0.8, 3.35, -6.25, 0.86, "M_Window")
    MC.chair(sh, 2.9, -5.3, 0.0, face=1)
    obj(sh, "Shed")
    c = K.MB()
    c.box(-6.5, -6.8, 0.45, -3.9, -5.4, 0.55, "M_MC_Plank")                 # 平板车
    for y in (-6.8, -5.4):
        with c.at(-5.6, y, 0.4, 0, 90, 0):
            c.cyl(0, 0, -0.04, 0.04, 0.4, "M_Wood_Dark", seg=10)
    beam(c, (-3.9, -6.6, 0.5), (-2.6, -6.4, 0.75), 0.06, "M_Wood")
    beam(c, (-3.9, -5.6, 0.5), (-2.6, -5.8, 0.75), 0.06, "M_Wood")
    stone_block(c, -5.6, -6.1, 0.55, 1.0, 0.5, 0.42, 5)
    barrow(c, -8.6, -5.6, 30)
    obj(c, "Cart")
    f = K.MB()
    for (xa, ya), (xb, yb) in (((-10.8, -7.5), (-10.8, 7.6)), ((-10.8, 7.6), (10.8, 7.6)), ((10.8, 7.6), (10.8, -1.5))):
        n = int(math.hypot(xb - xa, yb - ya) / 2.0)
        for i in range(n + 1):
            x, y = xa + (xb - xa) * i / n, ya + (yb - ya) * i / n
            f.box(x - 0.06, y - 0.06, 0, x + 0.06, y + 0.06, 1.1, "M_Wood_Dark")
        for z in (0.5, 0.95):
            beam(f, (xa, ya, z), (xb, yb, z), 0.06, "M_Wood")
    obj(f, "Fence")
    fx("FX_Chisel_1", -4.6, -4.4, 0.95)
    fx("FX_Chisel_2", -2.4, -4.6, 0.95)
    fx("FX_LimeDust", 2.6, 4.8, 0.5)
    fx("FX_RamDust", 0.3, -1.2, 0.7)
    for nm, p in (("ANCHOR_Chisel_1", (-4.6, -5.3, 0)), ("ANCHOR_Chisel_2", (-2.4, -5.5, 0)), ("ANCHOR_Lime", (2.7, 3.0, 0)),
                  ("ANCHOR_Saw", (4.3, -5.0, 0)), ("ANCHOR_Load", (-5.2, -4.8, 0)), ("ANCHOR_Ram_1", (-0.4, -1.2, 0.6)),
                  ("ANCHOR_Ram_2", (1.2, -1.2, 0.6)), ("ANCHOR_RosterDesk", (2.9, -5.3, 0)), ("ANCHOR_Foreman", (0.5, -4.2, 0)),
                  ("ANCHOR_StoneStack", (-7.0, 3.3, 0)), ("ANCHOR_Carry_Out", (0, -8.6, 0)), ("ANCHOR_cam_top", (0, 0, 34.0))):
        anchor(nm, *p)


# ====================================================================== 5. 北门殉难战后现场
def blob(mb, x, y, rx, ry, mat, rng, z=0.012, n=10, rz=0.0, jag=0.25):
    """贴花面片：不规则（近凸）多边形，厚 4 mm 的薄片（法线朝上），贴地 z。"""
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = 1.0 - rng.uniform(0, jag)
        pts.append((rx * r * math.cos(a), ry * r * math.sin(a)))
    with mb.at(x, y, 0, rz):
        mb.prism(pts, "z", z, z + 0.004, mat)


def arrow(mb, p0, p1):
    """箭：杆 + 两片羽 + 铁镞。p0 镞端，p1 羽端。"""
    p0, p1 = Vector(p0), Vector(p1)
    beam(mb, p0, p1, 0.018, "M_Wood")
    d = (p1 - p0).normalized()
    beam(mb, p1 - d * 0.16, p1, 0.07, "M_A2S_Fletch", h=0.006)
    beam(mb, p0, p0 + d * 0.07, 0.03, "M_MC_Iron")


def spear_broken(mb, x, y, rz, L1=1.3, L2=0.9, gap=0.35, head=True):
    """断枪：枪杆两截（断口斜错开）+ 枪头 + 红缨。平放地上，沿本地 X。"""
    with mb.at(x, y, 0.035, rz):
        beam(mb, (0, 0, 0), (L1, 0, 0), 0.045, "M_Wood_Dark")
        beam(mb, (L1 + gap, 0.12, 0), (L1 + gap + L2, 0.3, 0), 0.045, "M_Wood_Dark")
        if head:
            with mb.at(-0.05, 0, 0, 0, 0, -90):
                mb.cyl(0, 0, 0, 0.32, 0.04, "M_MC_Iron", seg=4, r_top=0.003)
            mb.cyl(0.02, 0, -0.03, 0.05, 0.08, "M_Cloth_Red", seg=5)


def rattan_shield(mb, x, y, rz, r=0.42, missing=(0.0, 0.0), z=0.0, tilt=0.0):
    """藤牌（圆、中凸），missing=(a0,a1) 度：缺掉的一块（破牌）。"""
    with mb.at(x, y, z, rz, tilt, 0):
        seg = 14
        for i in range(seg):
            a0, a1 = 360 * i / seg, 360 * (i + 1) / seg
            if missing[0] <= a0 < missing[1]:
                continue
            p0 = (r * math.cos(math.radians(a0)), r * math.sin(math.radians(a0)))
            p1 = (r * math.cos(math.radians(a1)), r * math.sin(math.radians(a1)))
            mb.prism([(0, 0), p0, p1], "z", 0.0, 0.05, "M_A2S_Rattan")
            for rr in (0.55, 0.85):                                        # 圈纹
                q0, q1 = (p0[0] * rr, p0[1] * rr), (p1[0] * rr, p1[1] * rr)
                mb.prism([q0, q1, (q1[0] * 0.95, q1[1] * 0.95), (q0[0] * 0.95, q0[1] * 0.95)], "z", 0.05, 0.065, "M_A2S_RattanDark")
        mb.cyl(0, 0, 0.05, 0.12, 0.1, "M_A2S_RattanDark", seg=6, r_top=0.05)
        if missing[1] > missing[0]:                                        # 断口的藤条毛刺
            am = math.radians((missing[0] + missing[1]) / 2)
            for k in range(3):
                a = am + (k - 1) * 0.3
                beam(mb, (r * 0.4 * math.cos(a), r * 0.4 * math.sin(a), 0.03), (r * 0.8 * math.cos(a + 0.1), r * 0.8 * math.sin(a + 0.1), 0.03),
                     0.015, "M_A2S_Rattan")


def flag_fallen(mb, x, y, rz, rng, L=3.2, cloth=(1.1, 0.8)):
    """倒伏的旗：旗杆平躺，旗面耷拉在地上（几段起伏的薄片）。"""
    with mb.at(x, y, 0.04, rz):
        beam(mb, (0, 0, 0), (L, 0, 0), 0.06, "M_Wood_Dark")
        mb.cyl(L + 0.02, 0, -0.04, 0.04, 0.05, "M_MC_Iron", seg=5)
        cw, ch = cloth
        n = 5
        prev = (L - 0.05, 0.05, 0.02)
        for i in range(1, n + 1):
            cur = (L - 0.05 - cw * i / n, 0.05 + ch * 0.5 + rng.uniform(-0.12, 0.12), 0.02 + rng.uniform(0.0, 0.12))
            beam(mb, prev, cur, ch, "M_Flag", h=0.012)
            prev = cur


def r_aftermath_northgate():
    """北门殉难战后现场（约 22 x 16，原点 = 现场中心地面；+Y 方向 10 m 处就是北门门洞，-Y 是城外官道）。
    子物体：
      Debris 断枪、散落箭矢（插地 / 平躺）、破藤牌、倭刀断刃、翻倒的独轮车、散落的土袋、草鞋
      Flags 倒伏的旗（三面）
      Spear_Planted 王沛插在门口地上的枪（「枪留下。人出去。」）；玩家拿走 spear_pei 后隐藏
      NOCOL_Decal_Blood 血迹（大片 + 溅点 + 两道拖痕，低饱和暗褐）；NOCOL_Decal_Scorch 火罐烧痕；NOCOL_Decal_Trample 踩烂的泥
    锚点：ANCHOR_Body_WangPei / Body_WangDe（两具遗体）、Body_Militia_1..3、Body_Wokou_1..2、Tag_De（王德腰牌掉落处）、
      Spear_Pei、Mourner_1/2（护民段之后族人跪位）、cam_top。"""
    rng = random.Random(1560)
    d = K.MB()
    for x, y, rz, l1, l2 in ((-3.0, 1.0, 20, 1.3, 0.9), (2.5, -2.4, -35, 1.1, 1.2), (-6.5, -4.0, 70, 1.5, 0.6), (5.8, 2.6, 160, 1.2, 0.8)):
        spear_broken(d, x, y, rz, l1, l2)
    for _ in range(26):                                                    # 插地的箭（斜插，多从城外 -Y 射来）
        x, y = rng.uniform(-9, 9), rng.uniform(-6, 7)
        tilt = math.radians(rng.uniform(35, 65))
        az = math.radians(rng.uniform(70, 110))
        L = 0.75
        p0 = (x, y, -0.12)
        p1 = (x + L * math.cos(tilt) * math.cos(az) * 0.4, y + L * math.cos(tilt) * math.sin(az), -0.12 + L * math.sin(tilt))
        arrow(d, p0, p1)
    for _ in range(16):                                                    # 平躺的箭
        x, y = rng.uniform(-9, 9), rng.uniform(-6, 7)
        a = rng.uniform(0, 6.28)
        arrow(d, (x, y, 0.02), (x + 0.8 * math.cos(a), y + 0.8 * math.sin(a), 0.03))
    for i in range(2):                                                     # 一筒箭撒了
        with d.at(-1.2 + i * 0.3, -5.2, 0.12, 30 + i * 10, 0, 90):
            d.cyl(0, 0, -0.3, 0.3, 0.1, "M_A2S_Rattan", seg=7)
    for _ in range(6):
        x, y = -1.0 + rng.uniform(0, 1.6), -5.6 + rng.uniform(-0.6, 0.6)
        a = rng.uniform(0, 6.28)
        arrow(d, (x, y, 0.02), (x + 0.8 * math.cos(a), y + 0.8 * math.sin(a), 0.03))
    rattan_shield(d, -4.4, 2.6, 30, missing=(40, 120))
    rattan_shield(d, 3.6, 0.6, 0, missing=(200, 260), z=0.22, tilt=60)     # 斜靠在土袋上
    rattan_shield(d, 1.0, 4.6, 75)
    rattan_shield(d, -7.6, 0.2, 10, missing=(0, 150))
    for x, y, rz in ((0.6, -3.6, 15), (-5.4, 4.4, -60)):                   # 倭刀断刃
        with d.at(x, y, 0.02, rz):
            d.box(0, -0.018, 0, 0.55, 0.018, 0.01, "M_MC_Iron")
            d.box(-0.25, -0.022, 0, 0.0, 0.022, 0.03, "M_Wood_Dark")
            d.box(-0.02, -0.06, 0, 0.02, 0.06, 0.02, "M_MC_Iron")
    barrow(d, 6.8, -1.2, 40, tipped=True)
    for i in range(7):                                                     # 散落土袋（门口那道临时土袋墙被冲开）
        x, y = 1.5 + i * 0.75 + rng.uniform(-0.2, 0.2), 6.2 + rng.uniform(-0.6, 0.6)
        with d.at(x, y, 0, rng.uniform(-40, 40)):
            d.frustum((-0.32, -0.22, 0.32, 0.22), (-0.28, -0.18, 0.28, 0.18), 0, 0.28, "M_Sandbag")
    for x, y in ((-2.2, -1.4), (4.4, -4.6)):                               # 草鞋
        d.box(x - 0.13, y - 0.05, 0.0, x + 0.13, y + 0.05, 0.04, "M_MC_Straw")
    obj(d, "Debris", uv=0.5)
    fl = K.MB()
    flag_fallen(fl, -2.0, 3.6, -15, rng)
    flag_fallen(fl, 4.2, -5.2, 120, rng, L=2.6, cloth=(0.9, 0.7))
    flag_fallen(fl, -8.2, -2.6, 75, rng, L=2.8)
    obj(fl, "Flags", uv=0.5)
    sp = K.MB()                                                            # 插在地上的枪（原点 = 入土点）
    sp.cyl(0, 0, -0.3, 2.6, 0.03, "M_Wood_Dark", seg=6)
    sp.cyl(0, 0, 2.6, 2.95, 0.045, "M_MC_Iron", seg=4, r_top=0.003)
    sp.cyl(0, 0, 2.48, 2.62, 0.09, "M_Cloth_Red", seg=6, r_top=0.03)
    obj(sp, "Spear_Planted", (0.8, 8.2, 0.0), uv=0.5)
    bl = K.MB()
    for x, y, rx, ry, rz in ((-3.6, 0.2, 0.9, 0.6, 20), (2.0, -1.8, 0.7, 0.5, -30), (0.4, 3.0, 1.1, 0.7, 5), (-6.0, -3.2, 0.6, 0.45, 60),
                             (5.0, 1.8, 0.5, 0.4, 0)):
        blob(bl, x, y, rx, ry, "M_A2S_Blood", rng, z=0.012 + rng.uniform(0, 0.004), rz=rz)
        for _ in range(4):                                                 # 溅点
            a, r = rng.uniform(0, 6.28), rng.uniform(1.1, 1.8) * rx
            blob(bl, x + r * math.cos(a), y + r * math.sin(a), 0.12, 0.09, "M_A2S_BloodDry", rng, z=0.011, n=6)
    for (xa, ya), (xb, yb) in (((0.4, 3.0), (0.9, 7.4)), ((-3.6, 0.2), (-1.2, 6.2))):   # 拖痕（遗体被拖回门里）
        n = 6
        for i in range(n):
            t = i / n
            blob(bl, xa + (xb - xa) * t, ya + (yb - ya) * t, 0.32, 0.5, "M_A2S_BloodDry", rng, z=0.010 + 0.0005 * i,
                 rz=math.degrees(math.atan2(yb - ya, xb - xa)) + 90, n=7, jag=0.35)
    obj(bl, "NOCOL_Decal_Blood", uv=1.0)
    scr = K.MB()
    for x, y, r in ((-1.0, -2.6, 1.0), (6.4, 4.6, 0.8), (-8.0, 4.0, 0.7)):
        blob(scr, x, y, r, r * 0.85, "M_A2S_Scorch", rng, z=0.008, n=12, jag=0.35)
        for k in range(3):                                                 # 碎陶片（火罐）
            a = rng.uniform(0, 6.28)
            scr.box(x + 0.6 * r * math.cos(a) - 0.07, y + 0.6 * r * math.sin(a) - 0.05, 0.01, x + 0.6 * r * math.cos(a) + 0.07,
                    y + 0.6 * r * math.sin(a) + 0.05, 0.05, "M_MC_Clay")
    obj(scr, "NOCOL_Decal_Scorch", uv=1.0)
    tr = K.MB()
    for _ in range(12):
        blob(tr, rng.uniform(-9, 9), rng.uniform(-6, 7), rng.uniform(0.8, 1.6), rng.uniform(0.6, 1.1), "M_A2S_Trample", rng, z=0.004, n=9)
    obj(tr, "NOCOL_Decal_Trample", uv=2.0)
    for nm, p in (("ANCHOR_Body_WangPei", (0.4, 3.0, 0)), ("ANCHOR_Body_WangDe", (-3.6, 0.2, 0)), ("ANCHOR_Body_Militia_1", (2.0, -1.8, 0)),
                  ("ANCHOR_Body_Militia_2", (-6.0, -3.2, 0)), ("ANCHOR_Body_Militia_3", (5.0, 1.8, 0)), ("ANCHOR_Body_Wokou_1", (-1.6, -4.4, 0)),
                  ("ANCHOR_Body_Wokou_2", (3.4, -4.0, 0)), ("ANCHOR_Tag_De", (-3.0, 0.9, 0.02)), ("ANCHOR_Spear_Pei", (0.8, 8.2, 0)),
                  ("ANCHOR_Mourner_1", (0.4, 4.2, 0)), ("ANCHOR_Mourner_2", (-3.0, 1.4, 0)), ("ANCHOR_Gate", (0, 10.0, 0)),
                  ("ANCHOR_cam_top", (0, 0, 30.0))):
        anchor(nm, *p)
    fx("FX_Smoke_1", -1.0, -2.6, 0.2)
    fx("FX_Smoke_2", 6.4, 4.6, 0.2)


def recipes():
    return {
        "BLD_Wall_Seg_Build": ("Buildings", r_wall_seg_build),
        "BLD_Wall_Gap": ("Buildings", r_wall_gap),
        "ENV_A2_WorkSite_Wall": ("Environments", r_worksite_wall),
        "ENV_A2_WorkSite_Yard": ("Environments", r_worksite_yard),
        "ENV_A2_Aftermath_NorthGate": ("Environments", r_aftermath_northgate),
    }
