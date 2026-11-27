"""
《入谱》明代 1560 公共建筑 BLD_MING_*（祖祠、汤和庙、城楼、环海楼、水门闸套件）+ 第二幕场景组（北门工地、王叔杲宅、盐场）
（Blender bpy，程序化白模；由 build_yongchang.py 统一生成/导出，recipes() 返回 {资产名: (分类, 生成函数)}）

对应 Docs/入谱_当前建模缺口清单.md 3.2 / 3.5，说明见 Docs/ming_buildings_civic.md。

约定：
  - 正面朝 Blender -Y（团结 +Z），1 unit = 1 m。建筑原点在占地中心地面；城楼/环海楼原点在城墙顶面（布局 y=7.0），
    与同 kind 的 BLD_ROC_* 完全对齐（占地、朝向、台基高度、门位）。
  - 建筑尽量只用 era_materials.json 里的语义材质（团结按年代换色）；新材质前缀 M_MC_*。
  - 会动 / 会切换状态的部件是固定名字的子物体：Sluice_Gate、Beam_Removable、Stage_1/2/3、Closure、Door_L/R、
    Pan_Brine、Lid、SaltPan_<n> ……；ROOF_* 可整体隐藏（俯视）；FX_* 特效挂点；ANCHOR_* 站位 / 交互点。
"""
import math
import random

import bpy
from mathutils import Vector

import rupu_kit as K

MC_PALETTE = {
    "M_MC_RammedEarth": "#9a8462",   # 夯土
    "M_MC_EarthLayer": "#81704f",    # 夯土层间（深一档，显出分层）
    "M_MC_StoneNew": "#aaa28d",      # 新凿条石
    "M_MC_Lime": "#dcd6c6",          # 石灰 / 灰浆
    "M_MC_Bamboo": "#9f9060",        # 毛竹脚手架
    "M_MC_Rope": "#a48e62",          # 麻绳
    "M_MC_Plank": "#9a7850",         # 新木板（跳板、夹板）
    "M_MC_StakeTip": "#b0452e",      # 放线木桩红头
    "M_MC_Clay": "#7c5a40",          # 陶缸
    "M_MC_ClayGlaze": "#3e3830",     # 缸口釉
    "M_MC_Brine": "#6d8782",         # 卤水
    "M_MC_PanDry": "#b3a892",        # 干涸盐田
    "M_MC_Iron": "#3a3632",          # 铁锅 / 火钳
    "M_MC_Ash": "#5c5750",           # 灶灰
    "M_MC_Char": "#2a2420",          # 灶膛黑
    "M_MC_StoveMud": "#8d6e50",      # 土灶
    "M_MC_Straw": "#a8945e",         # 引火草 / 草绳
    "M_MC_Sack": "#b7a780",          # 麻袋
    "M_MC_Reed": "#8f8458",          # 芦席风障
    "M_MC_Log": "#6e5236",           # 柴
    "M_MC_LogEnd": "#b09468",        # 柴截面
    # 第二幕补缺口（Docs/act2_site.md）：盐灶三档火、卤水 / 盐三态、水门开闭水面
    "M_MC_Flame": "#c9622f",         # 火舌（火色 #C4552E 提亮一档）
    "M_MC_FlameCore": "#dc9a4e",     # 火芯
    "M_MC_Ember": "#7e3424",         # 暗炭火
    "M_MC_PanWet": "#4a4842",        # 锅底湿膜（未出盐）
    "M_MC_WaterFlow": "#5d7a77",     # 开闸流水（比水色浅）
    "M_MC_WaterStill": "#3f5452",    # 闭闸死水（深、发暗）
    "M_MC_Foam": "#b9c2b8",          # 水花 / 流水白纹
}
K.PALETTE.update(MC_PALETTE)
# 引用的 era_materials 语义材质，在 K.PALETTE 里没有的补上预览色（团结里由年代材质库覆盖）
K.PALETTE.setdefault("M_Floor_Brick", "#7d7566")
K.PALETTE.setdefault("M_Floor_Wood", "#6b5039")
K.PALETTE.setdefault("M_Bronze", "#8a6a3a")
K.PALETTE.setdefault("M_Cloth_Red", "#8c3a2e")
K.PALETTE.setdefault("M_Ceiling", "#4a3a2c")

WALK = 7.08


# ====================================================================== 小工具
def obj(mb, name, loc=(0.0, 0.0, 0.0), uv=2.0):
    """MB（局部坐标，原点即枢轴）生成物体并放到 loc；空的跳过。"""
    if not mb.f:
        return None
    ob = mb.to_object(name, uv_scale=uv)
    ob.location = loc
    return ob


def _empty(name, loc, kind, size):
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = kind
    e.empty_display_size = size
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def anchor(name, x, y, z=0.0):
    return _empty(name, (x, y, z), "ARROWS", 0.3)


def fx(name, x, y, z):
    return _empty(name, (x, y, z), "SPHERE", 0.12)


def group(name, loc=(0.0, 0.0, 0.0)):
    """状态组空物体（团结里整组 SetActive）。放在原点，子物体的位置不受影响。"""
    return _empty(name, loc, "PLAIN_AXES", 0.4)


def under(g, *obs):
    """挂到组下（组只有平移），保持世界位置不变。"""
    for ob in obs:
        if ob is None:
            continue
        ob.parent = g
        ob.location = ob.location - g.location
    return obs[0] if obs else None


def ref_rot(name, loc, rz_deg):
    """带旋转的参考空物体：团结里把门扇 / 构件的 localRotation 插值到它的 localRotation 即为「开」（避开坐标轴换算）。"""
    e = _empty(name, loc, "ARROWS", 0.5)
    e.rotation_euler = (0.0, 0.0, math.radians(rz_deg))
    return e


def beam(mb, p0, p1, w, mat, h=None):
    """任意方向的方木 / 竹竿 / 绳：截面 w×h，从 p0 到 p1。"""
    h = w if h is None else h
    p0, p1 = Vector(p0), Vector(p1)
    d = (p1 - p0).normalized()
    up = Vector((0, 0, 1)) if abs(d.z) < 0.9 else Vector((1, 0, 0))
    s = d.cross(up).normalized() * (w / 2)
    u = s.cross(d).normalized() * (h / 2)
    cs = [(-1, -1), (1, -1), (1, 1), (-1, 1)]
    pts = [tuple(p0 + a * s + b * u) for a, b in cs] + [tuple(p1 + a * s + b * u) for a, b in cs]
    mb.hexa(pts, mat)


def plinth(mb, x0, y0, x1, y1, h=0.35, g=0.15, mat="M_Stone_Base"):
    mb.box(x0 - g, y0 - g, -0.3, x1 + g, y1 + g, h, mat)


def col(mb, x, y, z0, z1, r=0.2, mat="M_Red_Lacquer", base=True, seg=8):
    if base:
        mb.box(x - r * 1.5, y - r * 1.5, z0, x + r * 1.5, y + r * 1.5, z0 + 0.14, "M_Stone_Base")
        z0 += 0.14
    mb.cyl(x, y, z0, z1, r, mat, seg=seg)


def dougong(mb, x, y, z, s=1.0):
    """简化斗拱：坐斗 + 十字栱。"""
    mb.box(x - 0.24 * s, y - 0.24 * s, z, x + 0.24 * s, y + 0.24 * s, z + 0.16 * s, "M_Wood_Dark")
    mb.box(x - 0.42 * s, y - 0.11 * s, z + 0.16 * s, x + 0.42 * s, y + 0.11 * s, z + 0.3 * s, "M_Wood")
    mb.box(x - 0.11 * s, y - 0.42 * s, z + 0.16 * s, x + 0.11 * s, y + 0.42 * s, z + 0.3 * s, "M_Wood")


def lattice_window(mb, cx, cz, w, h, yf, n=3):
    """面朝 -Y 的直棂 / 方格窗：框 + 暗窗心 + 窗棂。"""
    mb.box(cx - w / 2 - 0.1, yf - 0.05, cz - h / 2 - 0.1, cx + w / 2 + 0.1, yf + 0.01, cz + h / 2 + 0.1, "M_Wood")
    mb.box(cx - w / 2, yf - 0.07, cz - h / 2, cx + w / 2, yf - 0.04, cz + h / 2, "M_Window")
    for i in range(1, n + 1):
        x = cx - w / 2 + w * i / (n + 1)
        mb.box(x - 0.025, yf - 0.09, cz - h / 2, x + 0.025, yf - 0.06, cz + h / 2, "M_Wood")
    mb.box(cx - w / 2, yf - 0.09, cz - 0.025, cx + w / 2, yf - 0.06, cz + 0.025, "M_Wood")


def geshan(mb, x0, x1, z0, z1, yf, n):
    """面朝 -Y 的一排格扇门：扇框、格心、棂条、裙板。"""
    w = (x1 - x0) / n
    zl = z0 + (z1 - z0) * 0.4
    for i in range(n):
        a, b = x0 + i * w, x0 + (i + 1) * w
        mb.box(a + 0.02, yf - 0.06, z0, b - 0.02, yf, z1, "M_Wood")
        mb.box(a + 0.1, yf - 0.08, zl, b - 0.1, yf - 0.05, z1 - 0.12, "M_Window")
        cx = (a + b) / 2
        mb.box(cx - 0.025, yf - 0.1, zl, cx + 0.025, yf - 0.07, z1 - 0.12, "M_Wood")
        for k in (1, 2):
            zz = zl + (z1 - 0.12 - zl) * k / 3
            mb.box(a + 0.1, yf - 0.1, zz - 0.025, b - 0.1, yf - 0.07, zz + 0.025, "M_Wood")
        mb.box(a + 0.1, yf - 0.08, z0 + 0.15, b - 0.1, yf - 0.05, zl - 0.12, "M_Wood_Dark")


def xieshan(mb, x0, y0, x1, y1, ze, rise, inset=None, mat="M_Roof_Tile", curl=True, gable_mat="M_Wood"):
    """歇山顶（屋脊沿 X）：四坡底 + 上部山花（竖直三角面）。"""
    hd = (y1 - y0) / 2
    ym = (y0 + y1) / 2
    if inset is None:
        inset = min((x1 - x0) * 0.24, hd * 0.95)
    mb.hip_roof(x0, y0, x1, y1, ze, rise, inset, mat, curl=curl)
    f = 0.48
    zg = ze + rise * f
    gx0, gx1 = x0 + inset * 0.62, x1 - inset * 0.62
    gh = hd * (1 - f) * 1.08
    mb.gable_fill(gx0, gx1, ym - gh, ym + gh, zg, rise * (1 - f) + 0.04, mat)
    for gx, s in ((gx0, -1), (gx1, 1)):           # 山花板
        mb.prism([(ym - gh * 0.86, zg + 0.08), (ym + gh * 0.86, zg + 0.08), (ym, ze + rise - 0.05)], "x",
                 gx + s * 0.01, gx + s * 0.05, gable_mat)


def wall_x(mb, y0, y1, x0, x1, z0, z1, mat, opens=()):
    """沿 X 的墙（厚 y0..y1），opens=[(xa, xb, zb, zt)] 是真洞口。"""
    cur = x0
    for xa, xb, zb, zt in sorted(opens):
        if xa > cur:
            mb.box(cur, y0, z0, xa, y1, z1, mat)
        if zb > z0:
            mb.box(xa, y0, z0, xb, y1, zb, mat)
        if zt < z1:
            mb.box(xa, y0, zt, xb, y1, z1, mat)
        cur = xb
    if x1 > cur:
        mb.box(cur, y0, z0, x1, y1, z1, mat)


def wall_y(mb, x0, x1, y0, y1, z0, z1, mat, opens=()):
    """沿 Y 的墙（厚 x0..x1），opens=[(ya, yb, zb, zt)]。"""
    cur = y0
    for ya, yb, zb, zt in sorted(opens):
        if ya > cur:
            mb.box(x0, cur, z0, x1, ya, z1, mat)
        if zb > z0:
            mb.box(x0, ya, z0, x1, yb, zb, mat)
        if zt < z1:
            mb.box(x0, ya, zt, x1, yb, z1, mat)
        cur = yb
    if y1 > cur:
        mb.box(x0, cur, z0, x1, y1, z1, mat)


def wall_cap(mb, x0, x1, y, z, t=0.35, axis="x"):
    """院墙顶小瓦檐。"""
    if axis == "x":
        mb.gable_roof(x0, x1, y - t / 2, y + t / 2, z, 0.28, ohf=0.18, ohs=0.0, ridge=False, curl=False, t=0.08)
    else:
        mb.gable_roof_y(y - t / 2, y + t / 2, x0, x1, z, 0.28, ohf=0.18, ohs=0.0, ridge=False, curl=False, t=0.08)   # 此时 x0/x1 = Y 范围，y = 墙中线 X


def ring(mb, x, y, z0, z1, r0, r1, mat, seg=16):
    """圆环（锅沿、缸口）：seg 个凸四边形块。"""
    for i in range(seg):
        a0, a1 = 2 * math.pi * i / seg, 2 * math.pi * (i + 1) / seg
        pts = [(x + r0 * math.cos(a0), y + r0 * math.sin(a0)), (x + r1 * math.cos(a0), y + r1 * math.sin(a0)),
               (x + r1 * math.cos(a1), y + r1 * math.sin(a1)), (x + r0 * math.cos(a1), y + r0 * math.sin(a1))]
        mb.prism(pts, "z", z0, z1, mat)


def table(mb, x0, y0, x1, y1, z0, h, mat="M_Wood", top=0.06, leg=0.07):
    mb.box(x0, y0, z0 + h - top, x1, y1, z0 + h, mat)
    for x, y in ((x0, y0), (x1 - leg, y0), (x1 - leg, y1 - leg), (x0, y1 - leg)):
        mb.box(x, y, z0, x + leg, y + leg, z0 + h - top, mat)


def chair(mb, cx, cy, z0, face=0):
    """官帽椅简化：face=0 面朝 -Y，1 朝 +Y，2 朝 +X，3 朝 -X。"""
    with mb.at(cx, cy, z0, (0, 180, 90, -90)[face]):
        mb.box(-0.26, -0.24, 0.42, 0.26, 0.24, 0.47, "M_Wood_Dark")
        for x, y in ((-0.26, -0.24), (0.2, -0.24), (0.2, 0.18), (-0.26, 0.18)):
            mb.box(x, y, 0, x + 0.06, y + 0.06, 0.42, "M_Wood_Dark")
        mb.box(-0.26, 0.18, 0.47, 0.26, 0.24, 1.05, "M_Wood_Dark")


def jar(mb, x, y, z0, r, h, mat="M_MC_Clay", seg=12):
    """陶缸：缸脚 → 鼓腹 → 缸肩 → 缸口（口沿上釉）。"""
    mb.cyl(x, y, z0, z0 + h * 0.18, r * 0.72, mat, seg=seg, r_top=r * 0.92)
    mb.cyl(x, y, z0 + h * 0.18, z0 + h * 0.62, r * 0.92, mat, seg=seg, r_top=r)
    mb.cyl(x, y, z0 + h * 0.62, z0 + h * 0.92, r, mat, seg=seg, r_top=r * 0.9)
    mb.cyl(x, y, z0 + h * 0.92, z0 + h, r * 0.94, "M_MC_ClayGlaze", seg=seg, r_top=r * 0.96)


# 城墙剖面（与 build_yongchang.wall_body 一致：外侧 -Y 收分，墙高 7.0，走道 7.08）
def y_out(z):
    return -2.5 + 0.4 * (z + 0.5) / 7.5


def wall_body(mb, x0, x1, parapet=True, crenel=True, mat="M_Wall_Stone"):
    mb.prism([(-2.5, -0.5), (2.5, -0.5), (2.5, 7.0), (-2.1, 7.0)], "x", x0, x1, mat)
    mb.box(x0, -2.75, -0.5, x1, -2.35, 0.45, "M_Stone_Base")
    mb.box(x0, -1.5, 7.0, x1, 2.5, WALK, "M_Wall_Top")
    mb.box(x0, 2.35, 6.75, x1, 2.6, 7.0, "M_Stone_Base")
    if parapet:
        mb.box(x0, -2.1, 7.0, x1, -1.5, 7.95, "M_Wall_Stone")
        mb.box(x0, -2.2, 7.95, x1, -1.4, 8.05, "M_Wall_Top")
        if crenel:
            mb.crenels(x0, x1, -2.1, -1.5, 8.05, 8.75, "M_Wall_Stone")


def wall_slice(mb, x0, x1, z0, z1, mat, yi=2.5):
    """城墙剖面的一层（z0..z1），外侧收分。"""
    mb.prism([(y_out(z0), z0), (yi, z0), (yi, z1), (y_out(z1), z1)], "x", x0, x1, mat)


# ====================================================================== A. 明代建筑
def r_ancestral():
    """王氏祖祠（明 1560，新祠）：门厅（凹廊、抱鼓石、悬山顶）→ 廊庑 → 月台 → 正厅（五开间格扇、歇山）→ 后堂。20 x 36。
    台基与 BLD_ROC_AncestralHall 一致（门厅 0.55 / 正厅 0.9 / 后堂 0.6），门窗对齐 BLD_INT_AncestralHall。"""
    mb = K.MB()
    x0, x1 = -10, 10
    # ---------- 门厅（-18..-11）：前檐凹廊 1.4 m
    plinth(mb, x0, -18, x1, -11, 0.55)
    mb.box(-2.6, -18.85, -0.3, 2.6, -18.15, 0.28, "M_Stone_Base")                   # 踏步
    zf = 0.55
    mb.box(x0, -16.6, zf, x1, -11, 4.8, "M_Plaster")
    mb.box(x0 - 0.02, -16.63, zf, x1 + 0.02, -11, 1.5, "M_Brick_Grey")             # 青砖裙墙
    for sx in (-1, 1):                                                              # 墀头（廊两端墙垛）
        xa, xb = (x0, x0 + 1.4) if sx < 0 else (x1 - 1.4, x1)
        mb.box(xa, -18, zf, xb, -16.6, 4.8, "M_Plaster")
        mb.box(xa - 0.02, -18.02, zf, xb + 0.02, -16.6, 1.5, "M_Brick_Grey")
        mb.box(xa - 0.08, -18.1, 4.4, xb + 0.08, -16.6, 4.8, "M_Brick_Grey")
    for x in (-6.6, -2.1, 2.1, 6.6):                                                # 廊柱
        col(mb, x, -17.55, zf, 4.55, 0.19)
    mb.box(-8.6, -17.75, 4.2, 8.6, -17.35, 4.6, "M_Wood")                           # 额枋
    for x in (-6.6, -4.35, -2.1, 0.0, 2.1, 4.35, 6.6):
        dougong(mb, x, -17.55, 4.6, 0.8)
    mb.door(0, 2.8, 3.4, -16.6, zf, mat="M_Red_Lacquer")
    mb.box(-1.5, -16.72, zf, 1.5, -16.6, zf + 0.15, "M_Stone_Base")                # 门槛
    for x in (-0.7, 0.7):                                                           # 门簪
        mb.box(x - 0.12, -16.82, 4.0, x + 0.12, -16.6, 4.2, "M_Wood_Dark")
    for x in (-0.7, 0.7):                                                           # 门钉（简化成两排）
        for z in (1.6, 2.4, 3.2):
            mb.box(x - 0.6, -16.68, z, x + 0.6, -16.64, z + 0.06, "M_Bronze")
    for sx in (-1, 1):                                                              # 抱鼓石
        x = sx * 1.75
        mb.box(x - 0.22, -17.3, zf, x + 0.22, -16.6, zf + 0.5, "M_Stone_Base")
        mb.box(x - 0.18, -17.1, zf + 0.5, x + 0.18, -16.6, zf + 1.15, "M_Stone_Base")
    mb.box(-1.8, -16.75, 4.25, 1.8, -16.6, 4.75, "M_Plaque")                        # 大门匾（在廊内）
    for x in (-4.6, 4.6):
        lattice_window(mb, x, zf + 2.85, 1.4, 1.3, -16.6)
    mb.gable_roof(x0, x1, -18, -11, 4.8, 2.4, ohf=0.9, ohs=0.25)
    # ---------- 廊庑 + 内院
    for sx in (-1, 1):
        xo, xi = (x0, x0 + 2.6) if sx < 0 else (x1, x1 - 2.6)
        xa, xb = min(xo, xi), max(xo, xi)
        mb.box(xo if sx < 0 else xo - 0.45, -11, -0.2, xo + 0.45 if sx < 0 else xo, 10, 4.2, "M_Plaster")
        mb.box(xa, -11, -0.2, xb, 10, 0.35, "M_Stone_Base")
        for y in range(-10, 10, 3):
            col(mb, xi, y, 0.35, 3.2, 0.15)
        mb.box(xi - 0.14, -11, 3.0, xi + 0.14, 10, 3.3, "M_Wood")
        mb.shed_roof_y(-11, 10, xo, xi - sx * 0.6, 4.4, 3.2)
    mb.box(x0 + 2.6, -11, -0.1, x1 - 2.6, 10, 0.1, "M_Road_Stone")
    mb.box(-1.4, -11, 0.1, 1.4, -6.0, 0.13, "M_Stone_Base")                         # 御路
    # 鼎炉（院心）
    mb.box(-0.8, -9.2, 0.1, 0.8, -7.6, 0.45, "M_Stone_Base")
    mb.cyl(0, -8.4, 0.45, 1.25, 0.55, "M_Bronze", seg=10, r_top=0.65)
    mb.hip(-0.75, -9.15, 0.75, -7.65, 1.25, 0.55, 0.75, "M_Bronze")
    # ---------- 月台 + 正厅
    mb.box(-6.5, -6.0, -0.2, 6.5, -2.6, 0.9, "M_Stone_Base")
    for k in range(3):
        mb.box(-2.2, -7.5 + k * 0.5, -0.2, 2.2, -6.0, 0.3 * (k + 1), "M_Stone_Base")
    for sx in (-1, 1):                                                              # 月台石栏
        xa, xb = (2.4, 6.5) if sx > 0 else (-6.5, -2.4)
        mb.box(xa, -6.0, 0.9, xb, -5.8, 1.4, "M_Stone_Base")
        mb.box(sx * 6.5 - (0.2 if sx > 0 else 0.0), -5.8, 0.9, sx * 6.5 + (0.0 if sx > 0 else 0.2), -2.6, 1.4, "M_Stone_Base")
    plinth(mb, -7.4, -2.6, 7.4, 7, 0.9, g=0.1)
    zh = 0.9
    mb.box(-7.0, -1.2, zh, 7.0, 6.6, 5.8, "M_Plaster")
    mb.box(-6.8, -1.26, zh, 6.8, -1.18, 5.6, "M_Wood")
    geshan(mb, -3.6, 3.6, zh, zh + 4.3, -1.26, 8)                                   # 中三间格扇
    for x in (-5.4, 5.4):
        lattice_window(mb, x, zh + 3.1, 1.6, 2.0, -1.26)
        mb.box(x - 1.1, -1.3, zh, x + 1.1, -1.22, zh + 1.9, "M_Wood_Dark")         # 槛墙板
    for x in (-6.4, -3.6, -1.2, 1.2, 3.6, 6.4):
        col(mb, x, -2.1, zh, 5.6, 0.2)
        dougong(mb, x, -2.1, 5.6, 0.9)
    mb.box(-6.8, -2.3, 5.1, 6.8, -1.9, 5.6, "M_Wood")                               # 檐枋
    mb.box(-1.6, -2.32, 4.45, 1.6, -2.22, 5.05, "M_Plaque")
    for sx in (-1, 1):                                                              # 山墙窗（对齐内景侧墙窗 / 侧门）
        with mb.at(sx * 7.0, 1.0, 0, -90 * sx):
            mb.door(0, 1.6, 2.7, 0, zh, mat="M_Wood_Dark")
        with mb.at(sx * 7.0, 4.2, 0, -90 * sx):
            lattice_window(mb, 0, zh + 3.1, 1.4, 1.6, 0)
    xieshan(mb, -8.8, -3.7, 8.8, 8.1, 5.8, 3.5)
    # 后天井：井
    mb.box(-0.6, 7.8, 0.0, 0.6, 9.0, 0.7, "M_Stone_Base")
    mb.box(-0.42, 8.02, 0.6, 0.42, 8.78, 0.72, "M_Window")
    # ---------- 后堂（10..18）：前檐格扇
    plinth(mb, x0, 10, x1, 18, 0.6)
    mb.box(x0, 10, 0.6, x1, 18, 5.0, "M_Plaster")
    mb.box(x0 + 0.5, 9.95, 0.6, x1 - 0.5, 10.02, 4.9, "M_Wood")
    geshan(mb, -1.6, 1.6, 0.6, 4.4, 9.95, 4)
    for x in (-5.5, 5.5):
        lattice_window(mb, x, 3.1, 1.8, 1.6, 9.95)
    for x in (-8.0, -4.0, 4.0, 8.0):
        mb.box(x - 0.16, 9.8, 0.6, x + 0.16, 9.96, 4.9, "M_Red_Lacquer")
    mb.gable_roof(x0, x1, 10, 18, 5.0, 2.8, ohf=0.8, ohs=0.25)
    # ---------- 门前功名旗杆（与民国版同位）
    for x in (-6.5, 6.5):
        mb.box(x - 0.5, -19.8, -0.1, x + 0.5, -19.0, 0.5, "M_Stone_Base")
        mb.box(x - 0.12, -19.75, 0.5, x - 0.06, -19.05, 1.8, "M_Stone_Base")
        mb.box(x + 0.06, -19.75, 0.5, x + 0.12, -19.05, 1.8, "M_Stone_Base")
        mb.cyl(x, -19.4, 0.5, 9.5, 0.13, "M_Red_Lacquer", seg=6, r_top=0.08)
        mb.hip(x - 0.4, -19.8, x + 0.4, -19.0, 6.2, -0.3, 0.4, "M_Wood_Dark")
        mb.box(x - 0.4, -19.8, 6.2, x + 0.4, -19.0, 6.4, "M_Wood_Dark")
    mb.to_object("BLD_MING_AncestralHall")
    anchor("ANCHOR_door_front", 0, -19.0, 0.0)
    anchor("ANCHOR_courtyard", 0, -8.0, 0.1)
    anchor("ANCHOR_hall_front", 0, -4.2, 0.9)
    anchor("ANCHOR_hall_door", 0, -1.6, 0.9)


def r_temple():
    """汤和庙（明）：三开间红墙山门（歇山）+ 院内香炉、幡杆 + 重檐歇山正殿。16 x 22。巡游起点。"""
    mb = K.MB()
    x0, x1 = -8, 8
    # ---------- 山门（-11..-7）
    plinth(mb, x0, -11, x1, -7, 0.4)
    mb.box(-2.4, -11.8, -0.3, 2.4, -11.15, 0.2, "M_Stone_Base")
    mb.box(-5.2, -10.2, 0.4, 5.2, -7.4, 4.3, "M_Wall_Red")
    for sx in (-1, 1):                                                              # 八字墙
        xa, xb = (5.2, 8.0) if sx > 0 else (-8.0, -5.2)
        mb.box(xa, -10.6, -0.2, xb, -7.0, 3.4, "M_Wall_Red")
        mb.box(xa - 0.05, -10.65, -0.2, xb + 0.05, -7.0, 0.8, "M_Stone_Base")
        mb.gable_roof(xa, xb, -10.6, -7.0, 3.4, 0.6, ohf=0.25, ohs=0.1, ridge=True, curl=False, t=0.12)
    for x in (-5.0, -1.6, 1.6, 5.0):
        col(mb, x, -10.7, 0.4, 4.1, 0.18)
        dougong(mb, x, -10.7, 4.1, 0.8)
    mb.box(-5.2, -10.9, 3.75, 5.2, -10.5, 4.15, "M_Wood")
    mb.door(0, 2.4, 3.1, -10.2, 0.4, mat="M_Red_Lacquer")
    for x in (-3.4, 3.4):
        mb.door(x, 1.4, 2.4, -10.2, 0.4, mat="M_Red_Lacquer")
    mb.box(-1.3, -10.35, 3.55, 1.3, -10.2, 4.05, "M_Plaque")
    xieshan(mb, -6.4, -11.8, 6.4, -6.2, 4.3, 2.2)
    # ---------- 院墙 + 院
    for xa, xb in ((x0, x0 + 0.4), (x1 - 0.4, x1)):
        mb.box(xa, -7, -0.2, xb, 11, 3.8, "M_Wall_Red")
        mb.box(xa - 0.12, -7, 3.8, xb + 0.12, 11, 4.0, "M_Roof_Ridge")
    mb.box(x0 + 0.4, 10.6, -0.2, x1 - 0.4, 11, 3.8, "M_Wall_Red")
    mb.box(x0 + 0.4, 10.48, 3.8, x1 - 0.4, 11.12, 4.0, "M_Roof_Ridge")
    mb.box(x0 + 0.4, -7, -0.1, x1 - 0.4, 10.6, 0.1, "M_Road_Stone")
    mb.box(-1.2, -7, 0.1, 1.2, 0.2, 0.13, "M_Stone_Base")
    # 香炉（三足鼎）
    mb.box(-0.9, -3.9, 0.1, 0.9, -2.1, 0.5, "M_Stone_Base")
    mb.cyl(0, -3.0, 0.5, 1.5, 0.5, "M_Bronze", seg=10, r_top=0.6)
    mb.hip(-0.7, -3.7, 0.7, -2.3, 1.5, 0.7, 0.7, "M_Bronze")
    mb.box(-0.12, -3.12, 2.2, 0.12, -2.88, 2.45, "M_Bronze")
    # 幡杆（巡游）
    for x in (-5.2, 5.2):
        mb.box(x - 0.45, -5.6, 0.1, x + 0.45, -4.7, 0.6, "M_Stone_Base")
        mb.cyl(x, -5.15, 0.6, 9.0, 0.1, "M_Red_Lacquer", seg=6, r_top=0.07)
        mb.box(x - 0.6, -5.2, 8.6, x + 0.6, -5.1, 8.7, "M_Wood_Dark")
        mb.box(x - 0.5, -5.18, 4.2, x + 0.5, -5.12, 8.6, "M_Flag")
    # 石灯
    for x in (-3.0, 3.0):
        mb.box(x - 0.3, -0.7, 0.1, x + 0.3, -0.1, 0.3, "M_Stone_Base")
        mb.box(x - 0.1, -0.5, 0.3, x + 0.1, -0.3, 1.0, "M_Stone_Base")
        mb.box(x - 0.28, -0.68, 1.0, x + 0.28, -0.12, 1.4, "M_Stone_Base")
        mb.box(x - 0.18, -0.72, 1.1, x + 0.18, -0.08, 1.3, "M_Window")
        mb.hip(x - 0.38, -0.78, x + 0.38, -0.02, 1.4, 0.35, 0.38, "M_Stone_Base")
    # ---------- 正殿（重檐歇山）
    plinth(mb, -6.5, 1.0, 6.5, 10.4, 0.8)
    for k in range(3):
        mb.box(-2.0, 0.25 + k * 0.25, -0.2, 2.0, 1.0, 0.27 * (k + 1), "M_Stone_Base")
    mb.box(-5.6, 2.8, 0.8, 5.6, 9.8, 4.4, "M_Wall_Red")
    mb.box(-5.4, 2.74, 0.8, 5.4, 2.82, 4.2, "M_Wood")
    geshan(mb, -3.4, 3.4, 0.8, 4.1, 2.74, 6)
    for x in (-4.5, 4.5):
        lattice_window(mb, x, 2.9, 1.4, 1.6, 2.74)
    for x in (-5.6, -3.4, -1.2, 1.2, 3.4, 5.6):
        col(mb, x, 1.75, 0.8, 4.2, 0.18)
        dougong(mb, x, 1.75, 4.2, 0.8)
    mb.box(-5.6, 1.55, 3.85, 5.6, 1.95, 4.2, "M_Wood")
    mb.hip_roof(-7.4, 0.5, 7.4, 11.0, 4.3, 1.1, 1.4, curl=True)
    mb.box(-4.6, 3.8, 4.4, 4.6, 8.8, 6.6, "M_Wall_Red")
    for x in (-3.3, -1.1, 1.1, 3.3):
        lattice_window(mb, x, 5.95, 1.4, 0.6, 3.8)
    mb.box(-1.2, 3.65, 5.0, 1.2, 3.8, 5.5, "M_Plaque")
    xieshan(mb, -6.1, 2.4, 6.1, 10.2, 6.5, 2.8)
    mb.to_object("BLD_MING_Temple")
    anchor("ANCHOR_procession_start", 0, -12.6, 0.0)
    anchor("ANCHOR_gate_in", 0, -6.2, 0.1)
    anchor("ANCHOR_incense", 0, -4.4, 0.1)
    anchor("ANCHOR_hall_front", 0, 0.0, 0.1)
    anchor("ANCHOR_altar", 0, 8.4, 0.8)


def gate_tower_ming(mb, half, hd, h1, h2):
    """明代城楼：底层外围柱廊（城墙走道从两侧前后廊或中间穿堂通过）+ 木构内厅；平座；上层木构 + 重檐歇山。
    原点在城墙走道面（布局 y=7.0），占地与 ROC 城楼一致（2half × 2hd）。"""
    mb.box(-half, -hd, 0, half, hd, 0.2, "M_Stone_Base")
    xs = [-half + 0.4 + (2 * half - 0.8) * i / 3 for i in range(4)]
    for x in xs:
        for y in (-hd + 0.4, hd - 0.4):
            col(mb, x, y, 0.2, h1, 0.18, base=False)
    # 内厅（穿堂）：前后格扇，两端开门
    cx0, cx1 = -half + 1.8, half - 1.8
    cy0, cy1 = -hd + 2.0, hd - 1.4
    t = 0.16
    ym = (cy0 + cy1) / 2
    geshan(mb, cx0, cx1, 0.2, h1, cy0 + 0.06, 6)
    mb.box(cx0, cy0, 0.2, cx1, cy0 + 0.06, h1, "M_Wood")
    mb.box(cx0, cy1 - t, 0.2, cx1, cy1, h1, "M_Wood")
    for x in (cx0, cx1 - t):
        wall_y(mb, x, x + t, cy0, cy1, 0.2, h1, "M_Wood", [(ym - 0.8, ym + 0.8, 0.2, 2.5)])
    mb.box(-1.3, cy0 - 0.02, h1 - 0.95, 1.3, cy0 + 0.0, h1 - 0.35, "M_Plaque")
    # 楼板 + 腰檐
    mb.box(-half - 0.2, -hd - 0.2, h1, half + 0.2, hd + 0.2, h1 + 0.3, "M_Wood")
    for x in xs:
        for y in (-hd + 0.4, hd - 0.4):
            dougong(mb, x, y, h1 - 0.35, 0.75)
    mb.hip_roof(-half - 1.1, -hd - 1.1, half + 1.1, hd + 1.1, h1 - 0.2, 1.0, 1.2, curl=True)
    zb = h1 + 0.3
    # 平座栏杆（四面）
    mb.box(-half - 0.1, -hd - 0.1, zb + 0.55, half + 0.1, -hd + 0.1, zb + 0.6, "M_Wood")
    mb.railing(-half - 0.1, half + 0.1, -hd - 0.05, zb + 0.6, 0.85, axis="x")
    mb.railing(-half - 0.1, half + 0.1, hd + 0.05, zb + 0.6, 0.85, axis="x")
    mb.railing(-hd, hd, -half - 0.05, zb + 0.6, 0.85, axis="y")
    mb.railing(-hd, hd, half + 0.05, zb + 0.6, 0.85, axis="y")
    # 上层
    ux, uy = half - 0.9, hd - 0.7
    mb.box(-ux, -uy, zb, ux, uy, zb + h2, "M_Wood")
    for k in range(4):
        x = -ux + 2 * ux * (k + 0.5) / 4
        lattice_window(mb, x, zb + h2 * 0.55, 1.3, h2 * 0.5, -uy)
        with mb.at(0, 0, 0, 180):
            lattice_window(mb, x, zb + h2 * 0.55, 1.3, h2 * 0.5, -uy)
    for sx in (-1, 1):
        with mb.at(sx * ux, 0, 0, -90 * sx):
            lattice_window(mb, 0, zb + h2 * 0.55, 1.4, h2 * 0.5, 0)
    for x in (-ux, ux):
        for y in (-uy, uy):
            mb.box(x - 0.16, y - 0.16, zb, x + 0.16, y + 0.16, zb + h2, "M_Red_Lacquer")
    mb.box(-1.4, -uy - 0.12, zb + h2 * 0.78, 1.4, -uy, zb + h2 - 0.05, "M_Plaque")
    xieshan(mb, -half - 0.7, -hd - 0.7, half + 0.7, hd + 0.7, zb + h2 - 0.15, 2.6 + half * 0.08)


def r_gate_tower():
    """明代城门楼（通市 / 迎川 / 镇山三门），12 x 6.4，坐在 BLD_Wall_GateBase 上（原点 = 城墙顶 y=7.0，对齐方式同 ROC 城楼）。"""
    mb = K.MB()
    gate_tower_ming(mb, 6.0, 3.2, 3.4, 2.6)
    gate_doors_frame(mb)
    mb.to_object("BLD_MING_GateTower")
    anchor("ANCHOR_walk_W", -6.6, 0.2, 0.08)
    anchor("ANCHOR_walk_E", 6.6, 0.2, 0.08)
    anchor("ANCHOR_lookout", 0, -3.3, 3.7)
    gate_doors_and_cols()


# 城门洞（BLD_Wall_GateBase：门洞宽 4.4、拱脚 3.6、拱顶 5.8、洞深 y ±3.5；GateBase 原点在地面，城楼原点在其上 7.0 m）
GATE_ZG = -7.0          # 门洞地面（城楼本地）
GATE_TW, GATE_SPRING, GATE_YH = 4.4, 3.6, 3.5
GATE_HX, GATE_HY = 2.05, -2.45      # 门轴（铰链）位置：贴门洞内壁、靠城外一侧，与 GateBase 烘焙的开启门扇重合
GATE_LEAF_W = 2.04                  # 每扇宽（两扇中缝 2 cm）


def _arch_top(x):
    r = GATE_TW / 2
    return GATE_SPRING + math.sqrt(max(0.0, r * r - x * x)) - 0.06


def gate_doors_frame(mb):
    """门框（门轴立枋 + 门闩托 + 低门槛），并进城楼主网格。都在门洞两侧 0.15 m 内，不挡通道。"""
    zg = GATE_ZG
    for s in (-1, 1):
        x0, x1 = sorted((s * 2.08, s * 2.2))
        mb.box(x0, GATE_HY - 0.15, zg, x1, GATE_HY + 0.15, zg + _arch_top(2.1) - 0.05, "M_Wood_Dark")   # 门轴立枋
        mb.box(x0, GATE_HY + 0.12, zg + 1.45, x1, GATE_HY + 0.42, zg + 1.75, "M_Wood_Dark")  # 门闩托
    mb.box(-2.2, GATE_HY - 0.12, zg - 0.02, 2.2, GATE_HY + 0.12, zg + 0.06, "M_Stone_Base")          # 门槛石（6 cm，可直接走过）


def gate_doors_and_cols():
    """城门门扇 Gate_Door_L/R（原点 = 门轴底端；闭合时横在门洞里，开 = 绕 Z 转 90° 朝城内贴到洞壁）、门闩 Gate_Bar，
    以及 COL_*（有 COL_ 时团结只用 COL_ 做碰撞）：城楼底层（楼板、柱、穿堂墙）、上层体块、门洞两侧墩台、券顶，门扇各带一块 COL 随门转。"""
    zg = GATE_ZG
    for nm, s in (("Gate_Door_L", -1), ("Gate_Door_R", 1)):
        d = K.MB()
        # 本地坐标：门轴在原点，门扇朝门洞中线伸出（左扇 +X，右扇 -X）
        us = [0.0, 0.5, 1.0, 1.5, 1.8, GATE_LEAF_W]
        top = [(u, _arch_top(s * (GATE_HX - u))) for u in us]
        pts = [(-s * 0.0, 0.0), (-s * GATE_LEAF_W, 0.0)] + [(-s * u, z) for u, z in reversed(top)]
        d.prism(pts, "y", -0.06, 0.06, "M_Wood_Dark")
        for k in range(1, 5):                                              # 拼板缝（城外面）
            u = GATE_LEAF_W * k / 5
            d.box(-s * u - 0.012, -0.075, 0.1, -s * u + 0.012, -0.06, _arch_top(s * (GATE_HX - u)) - 0.15, "M_Wood")
        for z in (0.5, 1.6, 2.7, 3.6):                                     # 铁叶（横带）
            ua = GATE_LEAF_W - 0.05
            d.box(min(0, -s * ua), -0.08, z, max(0, -s * ua), -0.06, z + 0.12, "M_MC_Iron")
        for r, z in enumerate((0.95, 1.4, 2.15, 3.15)):                    # 门钉
            for c in range(4):
                u = 0.3 + c * 0.45
                d.box(-s * u - 0.05, -0.1, z - 0.05, -s * u + 0.05, -0.06, z + 0.05, "M_Bronze")
        for z in (0.8, 2.9):                                               # 城内面穿带
            d.box(min(0, -s * 1.95), 0.06, z, max(0, -s * 1.95), 0.12, z + 0.2, "M_Wood")
        d.box(-s * (GATE_LEAF_W - 0.35) - 0.1, -0.1, 1.5, -s * (GATE_LEAF_W - 0.35) + 0.1, -0.06, 1.7, "M_MC_Iron")   # 门环座
        leaf = obj(d, nm, (s * GATE_HX, GATE_HY, zg))
        c = K.MB()
        c.box(min(0, -s * GATE_LEAF_W), -0.09, 0.0, max(0, -s * GATE_LEAF_W), 0.13, 4.3, "M_Wood_Dark")
        cob = obj(c, "COL_" + nm, (s * GATE_HX, GATE_HY, zg))
        cob.parent = leaf
        cob.location = (0.0, 0.0, 0.0)
        # 开门参考：左扇 Blender rz +90°、右扇 -90°（门扇转到 +Y = 城内，贴洞壁）
        ref_rot(f"ANCHOR_{nm}_Open", (s * GATE_HX, GATE_HY, zg), -90 * s)
    gb = K.MB()                                                            # 门闩（关门时横架在门闩托上，开门前抽走）
    gb.box(-2.18, -0.1, -0.12, 2.18, 0.1, 0.12, "M_Wood")
    for x in (-1.2, 1.2):
        gb.box(x - 0.06, -0.12, -0.14, x + 0.06, 0.12, 0.14, "M_MC_Iron")
    obj(gb, "Gate_Bar", (0, GATE_HY + 0.27, zg + 1.6 + 0.15 + 0.12))
    # ---- COL_*：城楼（原点 = 城墙顶 7.0；走道面 0.08，楼板 0.2）
    half, hd, h1 = 6.0, 3.2, 3.4
    cb = lambda nm, *b: obj(_colbox(*b), nm)
    cb("COL_Tower_Floor", -half, -hd, -0.1, half, hd, 0.2)
    xs = [-half + 0.4 + (2 * half - 0.8) * i / 3 for i in range(4)]
    for i, x in enumerate(xs):
        for j, y in enumerate((-hd + 0.4, hd - 0.4)):
            cb(f"COL_Tower_Col_{i + 1}{'FB'[j]}", x - 0.2, y - 0.2, 0.2, x + 0.2, y + 0.2, h1)
    cx0, cx1, cy0, cy1, ym = -half + 1.8, half - 1.8, -hd + 2.0, hd - 1.4, (-hd + 2.0 + hd - 1.4) / 2
    cb("COL_Tower_HallFront", cx0, cy0 - 0.06, 0.2, cx1, cy0 + 0.08, h1)
    cb("COL_Tower_HallBack", cx0, cy1 - 0.16, 0.2, cx1, cy1, h1)
    for k, x in enumerate((cx0, cx1 - 0.16)):                          # 两端墙，留 1.6 m 门
        cb(f"COL_Tower_HallEnd_{k + 1}a", x, cy0, 0.2, x + 0.16, ym - 0.8, h1)
        cb(f"COL_Tower_HallEnd_{k + 1}b", x, ym + 0.8, 0.2, x + 0.16, cy1, h1)
        cb(f"COL_Tower_HallEnd_{k + 1}c", x, ym - 0.8, 2.5, x + 0.16, ym + 0.8, h1)
    cb("COL_Tower_Upper", -half - 0.2, -hd - 0.2, h1, half + 0.2, hd + 0.2, 9.0)
    # ---- COL_*：门洞（与 BLD_Wall_GateBase 重合；通道 x ±2.08 净宽 4.16、净高到拱脚 3.6）
    for s, nm in ((-1, "L"), (1, "R")):
        pa, pb = sorted((s * 2.2, s * 7.2))                                # 门洞两侧墩台（到 ±7.2，不超出城楼占地 ±7.25）
        cb(f"COL_Gate_Pier_{nm}", pa, -GATE_YH, zg - 0.5, pb, GATE_YH, 0.0)
        ja, jb = sorted((s * 2.08, s * 2.2))
        cb(f"COL_Gate_Jamb_{nm}", ja, GATE_HY - 0.15, zg, jb, GATE_HY + 0.15, zg + 4.2)
    cb("COL_Gate_Vault", -2.2, -GATE_YH, zg + GATE_SPRING + GATE_TW / 2, 2.2, GATE_YH, 0.0)
    anchor("ANCHOR_Gate_Out", 0, -GATE_YH - 2.0, zg)
    anchor("ANCHOR_Gate_In", 0, GATE_YH + 2.0, zg)
    anchor("ANCHOR_Gate_Bar", 0, GATE_HY + 1.0, zg)


def _colbox(x0, y0, z0, x1, y1, z1):
    c = K.MB()
    c.box(x0, y0, z0, x1, y1, z1, "M_Stone_Base")
    return c


def r_huanhai():
    """明代环海楼（东门城楼，20 x 8.8，坐在 BLD_Wall_GateBaseL 上，原点 = 城墙顶）。
    尺寸与 BLD_INT_HuanhaiLou 一致：底层砖墙（前后中央券门、两端走道门、射孔/炮窗），二层楼面 4.2，
    上层军议厅（窗位对齐内景）+ 前檐平座，后/两端腰檐，顶上重檐歇山。
    屋顶拆成 ROOF_Upper / ROOF_Waist，俯视军议时可隐藏。"""
    G = K.MB()           # 外壳
    RU, RW = K.MB(), K.MB()
    H1, ZS, H2 = 3.9, 4.2, 3.1
    ZT = ZS + H2
    G.box(-10.0, -4.5, 0, 10.0, 4.5, 0.12, "M_Stone_Base")
    # ---------- 底层：前后墙（中央券门 + 炮窗/射孔）
    for sy in (-1, 1):
        ya, yb = (-4.4, -3.8) if sy < 0 else (3.8, 4.4)
        G.arch_slab(-10, 10, -2.4, 2.4, 0.12, 2.6, H1, ya, yb, "M_Brick_Grey", seg=8)
        yf = ya if sy < 0 else yb
        with G.at(0, 0, 0, 0 if sy < 0 else 180):
            yl = -4.4
            for x in (-8.4, -6.2, 6.2, 8.4):                      # 射孔（对齐内景 slit）
                G.box(x - 0.15, yl - 0.03, 1.4, x + 0.15, yl + 0.02, 2.4, "M_Window")
                G.box(x - 0.3, yl - 0.06, 1.25, x + 0.3, yl + 0.0, 1.4, "M_Stone_Base")
            G.box(-2.75, yl - 0.08, 0.12, -2.4, yl + 0.0, 2.6, "M_Wall_Top")   # 券门石框
            G.box(2.4, yl - 0.08, 0.12, 2.75, yl + 0.0, 2.6, "M_Wall_Top")
            r = 2.75
            for i in range(8):
                a0 = math.pi - math.pi * i / 8
                a1 = math.pi - math.pi * (i + 1) / 8
                zc = 2.6
                rz = 1.25
                p = [(r * math.cos(a0), zc + (rz + 0.35) * math.sin(a0)), (r * math.cos(a1), zc + (rz + 0.35) * math.sin(a1)),
                     (2.4 * math.cos(a1), zc + rz * math.sin(a1)), (2.4 * math.cos(a0), zc + rz * math.sin(a0))]
                G.prism(p, "y", yl - 0.08, yl + 0.0, "M_Wall_Top")
        _ = yf
    # 炮窗（城外一侧，方窗带石框；在射孔之间）
    for x in (-4.1, 4.1):
        G.box(x - 0.45, -4.46, 1.2, x + 0.45, -4.4, 2.0, "M_Stone_Base")
        G.box(x - 0.32, -4.49, 1.3, x + 0.32, -4.44, 1.9, "M_Window")
    # 两端墙（接城墙走道，真门洞 1.6 x 2.6）+ 射孔
    for sx in (-1, 1):
        xa, xb = (-10.0, -9.5) if sx < 0 else (9.5, 10.0)
        wall_y(G, xa, xb, -3.8, 3.8, 0.12, H1, "M_Brick_Grey", [(-0.8, 0.8, 0.12, 2.6)])
        xf = xa if sx < 0 else xb
        for y in (-2.6, 2.6):
            G.box(xf - 0.02, y - 0.15, 1.4, xf + 0.02, y + 0.15, 2.4, "M_Window")
        G.box(xf - 0.06, -1.0, 2.6, xf + 0.06, 1.0, 2.85, "M_Wall_Top")
    # 底层内隔墙（与内景一致，保证穿行路线）
    wall_y(G, -2.6, -2.2, -3.8, 3.8, 0.12, H1, "M_Plaster", [(-0.7, 0.7, 0.12, 2.4)])
    wall_y(G, 2.2, 2.6, -3.8, 3.8, 0.12, H1, "M_Plaster", [(-1.7, -0.3, 0.12, 2.4)])
    # ---------- 二层楼板 + 平座（斗拱托）
    G.box(-10.0, -4.4, H1, 10.0, 4.4, ZS, "M_Floor_Wood")
    G.box(-10.1, -4.5, H1 - 0.05, 10.1, 4.5, H1 + 0.08, "M_Wood_Dark")
    G.box(-9.4, -5.4, H1, 9.4, -4.4, ZS, "M_Floor_Wood")
    for x in range(-9, 10, 2):
        G.box(x - 0.15, -5.4, 3.2, x + 0.15, -4.4, H1, "M_Wood_Dark")
        dougong(G, x, -4.9, H1 - 0.25, 0.6)
    G.railing(-9.4, 9.4, -5.35, ZS, 0.95, "M_Wood_Dark", axis="x", post=1.6)
    for sx in (-1, 1):
        G.railing(-5.35, -4.4, 9.35 * sx, ZS, 0.95, "M_Wood_Dark", axis="y", post=1.0)
    # ---------- 上层军议厅（墙在 y=±3.6、x=±9.0，窗位同内景）
    G.box(-9.2, -3.8, ZS, 9.2, 3.8, ZT, "M_Plaster")
    G.box(-9.22, -3.82, ZS, 9.22, 3.82, ZS + 0.6, "M_Wood_Dark")
    for x in (-7.2, -3.6, 3.6, 7.2):
        lattice_window(G, x, ZS + 1.85, 1.8, 1.7, -3.8)
        with G.at(0, 0, 0, 180):
            lattice_window(G, x, ZS + 1.9, 1.6, 1.4, -3.8)
    geshan(G, -1.2, 1.2, ZS, ZS + 2.5, -3.8, 4)
    for sx in (-1, 1):
        with G.at(sx * 9.2, 0, 0, -90 * sx):
            lattice_window(G, 0, ZS + 1.85, 1.8, 1.5, 0)
    G.box(-1.6, -3.86, ZS + 2.6, 1.6, -3.8, ZT - 0.1, "M_Plaque")
    for x in (-9.0, -5.4, -1.8, 1.8, 5.4, 9.0):                     # 上层檐柱（廊）
        for y in (-4.25, 4.25):
            G.cyl(x, y, ZS, ZT - 0.1, 0.17, "M_Red_Lacquer", seg=8)
            dougong(G, x, y, ZT - 0.25, 0.7)
    for sx in (-1, 1):
        G.cyl(sx * 9.85, 0, ZS, ZT - 0.1, 0.17, "M_Red_Lacquer", seg=8)
    G.box(-10.0, -4.4, ZT - 0.45, 10.0, -4.1, ZT - 0.15, "M_Wood")
    G.box(-10.0, 4.1, ZT - 0.45, 10.0, 4.4, ZT - 0.15, "M_Wood")
    # 旗杆（门台东北角，俯视可见）
    G.box(10.6, 2.9, 0, 11.6, 3.9, 0.45, "M_Stone_Base")
    G.cyl(11.1, 3.4, 0.45, 13.0, 0.11, "M_Wood_Dark", seg=6, r_top=0.07)
    G.box(11.1, 3.37, 9.6, 13.6, 3.43, 12.8, "M_Flag")
    G.to_object("BLD_MING_HuanhaiLou")
    # ---------- 屋顶
    RW.shed_roof(-10.6, 10.6, 3.8, 5.6, ZS + 1.0, ZS + 0.15)                       # 后腰檐
    for sx in (-1, 1):
        RW.shed_roof_y(-4.4, 5.6, sx * 9.2, sx * 10.9, ZS + 1.0, ZS + 0.15)          # 两端腰檐
    xieshan(RU, -11.2, -6.0, 11.2, 5.8, ZT - 0.1, 3.6)
    RU.box(-10.0, -4.45, ZT - 0.15, 10.0, 4.45, ZT, "M_Wood_Dark")               # 顶层梁箍（隐藏屋顶后可见）
    obj(RW, "ROOF_Waist")
    obj(RU, "ROOF_Upper")
    anchor("ANCHOR_walk_W", -10.8, 0, 0.08)
    anchor("ANCHOR_walk_E", 10.8, 0, 0.08)
    anchor("ANCHOR_gate_out", 0, -6.0, 0.08)
    anchor("ANCHOR_gate_in", 0, 6.0, 0.08)
    anchor("ANCHOR_balcony", 0, -4.9, ZS)
    anchor("ANCHOR_muster_table", 0, -0.4, ZS + 0.9)
    anchor("ANCHOR_flagpole", 11.1, 3.4, 0.45)
    anchor("ANCHOR_cam_top_upper", 0, 0, 24.0)


def r_sluice():
    """水门闸套件（配合 BLD_Wall_WaterGate 使用，放在同一位置、同一旋转）。
    水门门洞：x ±3.2、洞底 z=-1.8、拱脚 1.6、拱顶 4.8、洞深 y ±2.5；原有外侧闸槽在 y≈-0.7。
    本套件在城内一侧加：木闸槽（y≈1.15）+ 可升降闸板 Sluice_Gate + 门闩 Sluice_Latch + 石条槽（y≈1.75）三根石条
    Sluice_StoneBar_1..3（闭闸）+ 城顶绞盘 Sluice_Winch / Sluice_WinchDrum。
    会切换的件分两组：State_Closed（闸板落下、门闩、石条、死水 NOCOL_Water_Still）/ State_Open（闸板升起 Sluice_Gate_Open、
    短吊绳、流水 NOCOL_Water_Flow、小船 Sluice_Boat、FX_WaterFlow/FX_Splash），团结里二选一 SetActive。"""
    F = K.MB()
    zb = -1.8
    # 闸槽（两侧石槽柱，贴在门洞内壁）
    for s in (-1, 1):
        for y0, y1 in ((0.85, 1.05), (1.25, 1.45), (1.55, 1.62), (1.9, 1.97)):
            F.box(s * 2.96, y0, zb, s * 3.22, y1, 2.65, "M_Stone_Base")
        F.box(s * 3.0, 0.85, zb, s * 3.22, 1.97, zb + 0.25, "M_Stone_Base")
        F.box(s * 2.9, 1.25, 0.55, s * 3.22, 1.5, 0.75, "M_Wood_Dark")               # 门闩托
    F.box(-3.2, 0.8, zb - 0.1, 3.2, 2.05, zb, "M_Stone_Base")                       # 闸底槛石
    # 城顶：闸缝盖板 + 绞盘架
    F.box(-3.2, 0.95, WALK, 3.2, 1.35, WALK + 0.06, "M_MC_Iron")
    for x in (-2.0, 2.0):
        F.box(x - 0.15, 0.55, WALK, x + 0.15, 1.75, WALK + 0.2, "M_Wood_Dark")
        F.box(x - 0.1, 1.05, WALK, x + 0.1, 1.25, WALK + 1.25, "M_Wood_Dark")
        beam(F, (x, 0.65, WALK + 0.2), (x, 1.15, WALK + 1.2), 0.1, "M_Wood_Dark")
        beam(F, (x, 1.65, WALK + 0.2), (x, 1.15, WALK + 1.2), 0.1, "M_Wood_Dark")
    obj(F, "BLD_MING_WaterGate_Sluice")
    # ---- 两套状态组：State_Closed / State_Open（团结里二选一 SetActive；绞盘鼓、闸槽是公用的）
    gc, go = group("State_Closed"), group("State_Open")

    def gate_board(name, z):
        """闸板（枢轴在底边中心）。闭：底边在洞底 z=-1.8；开：升 1.8 m（底边 0.0，露出水面 0.9 m）。"""
        g = K.MB()
        g.box(-2.94, -0.08, 0, 2.94, 0.08, 2.6, "M_Wood")
        for zz in (0.3, 1.0, 1.7, 2.35):
            g.box(-2.94, -0.11, zz, 2.94, 0.11, zz + 0.14, "M_MC_Iron")
        for x in (-1.2, 1.2):
            g.box(x - 0.08, -0.13, 2.45, x + 0.08, 0.13, 2.75, "M_MC_Iron")          # 吊环
        for i in range(-5, 6):
            g.box(i * 0.52 - 0.012, -0.085, 0, i * 0.52 + 0.012, 0.085, 2.6, "M_Wood_Dark")
        return obj(g, name, (0, 1.15, z))

    def rope(name, z_gate):
        rp = K.MB()
        for x in (-1.2, 1.2):
            rp.box(x - 0.02, -0.02, 0, x + 0.02, 0.02, WALK + 0.7 - (z_gate + 2.75), "M_MC_Rope")
        return obj(rp, name, (0, 1.15, z_gate + 2.75))

    def water(name, mat, z, streaks):
        """门洞里的水面（地图总水面 -0.9，这里抬 2–3 cm 防闪烁），y 覆盖洞深 ±2.5 再各伸 0.6 m。"""
        w = K.MB()
        w.box(-3.18, -3.1, z - 0.02, 3.18, 3.1, z, mat)
        if streaks:                                                        # 流水白纹（顺洞身方向的细长条）+ 闸下翻花
            rng = random.Random(15)
            for i in range(14):
                x = -2.8 + i * 0.43 + rng.uniform(-0.08, 0.08)
                y0 = rng.uniform(-3.0, -0.6)
                w.box(x - 0.035, y0, z, x + 0.035, y0 + rng.uniform(1.2, 2.4), z + 0.008, "M_MC_Foam")
            for i in range(9):
                x = -2.7 + i * 0.68
                w.box(x - 0.22, 1.32, z, x + 0.22, 1.32 + rng.uniform(0.35, 0.8), z + 0.05, "M_MC_Foam")
        return obj(w, name, uv=1.0)

    # 闭闸：闸板落到底 + 门闩 + 三根石条 + 死水
    under(gc, gate_board("Sluice_Gate", zb), rope("NOCOL_Sluice_Rope", zb))
    lt = K.MB()
    lt.box(-3.15, -0.09, -0.1, 3.15, 0.09, 0.1, "M_Wood_Dark")
    for x in (-1.0, 1.0):
        lt.box(x - 0.06, -0.11, -0.12, x + 0.06, 0.11, 0.12, "M_MC_Iron")
    under(gc, obj(lt, "Sluice_Latch", (0, 1.37, 0.85)))
    for i in range(3):                                                     # 石条（推进外侧石槽，三根叠放）
        sb = K.MB()
        sb.box(-2.94, -0.13, 0, 2.94, 0.13, 0.48, "M_MC_StoneNew")
        sb.box(-2.94, -0.135, 0.22, 2.94, 0.135, 0.26, "M_Stone_Base")
        under(gc, obj(sb, f"Sluice_StoneBar_{i + 1}", (0, 1.76, zb + 0.5 * i)))
    under(gc, water("NOCOL_Water_Still", "M_MC_WaterStill", -0.87, False))
    # 开闸：闸板升 1.8 m（吊绳变短）+ 流水面（白纹、闸下翻花）+ 一条过闸小船；门闩、石条不在
    under(go, gate_board("Sluice_Gate_Open", zb + 1.8), rope("NOCOL_Sluice_Rope_Open", zb + 1.8))
    under(go, water("NOCOL_Water_Flow", "M_MC_WaterFlow", -0.86, True))
    bt = K.MB()                                                            # 小船（敞口舢板，长 4.4 m，沿 Y 停在城内一侧）
    bt.box(-0.5, -1.7, 0.0, 0.5, 1.7, 0.08, "M_Wood_Dark")                   # 船底
    for sx in (-1, 1):                                                     # 两舷（外倾）
        bt.prism([(sx * 0.5, 0.0), (sx * 0.56, 0.0), (sx * 0.8, 0.5), (sx * 0.74, 0.5)], "y", -1.7, 1.7, "M_Wood")
        bt.box(min(sx * 0.72, sx * 0.84), -1.7, 0.48, max(sx * 0.72, sx * 0.84), 1.7, 0.54, "M_Wood_Dark")   # 舷缘
    for y0, y1, tip in ((1.7, 2.4, 2.4), (-1.7, -2.1, -2.1)):              # 船头 / 船尾（收尖、上翘）
        bt.prism([(-0.8, 0.5), (0.8, 0.5), (0.5, 0.0), (-0.5, 0.0)], "y", min(y0, y0 + (y1 - y0) * 0.01), max(y0, y0 + (y1 - y0) * 0.01), "M_Wood")
        bt.hexa([(-0.5, y0, 0.0), (0.5, y0, 0.0), (0.06, tip, 0.25), (-0.06, tip, 0.25),
                 (-0.8, y0, 0.54), (0.8, y0, 0.54), (0.08, tip, 0.7), (-0.08, tip, 0.7)], "M_Wood")
    for y in (-0.9, 0.7):                                                  # 横梁（坐板）
        bt.box(-0.74, y - 0.1, 0.36, 0.74, y + 0.1, 0.43, "M_Wood_Dark")
    bt.box(-0.25, -1.4, 0.08, 0.25, -1.1, 0.4, "M_MC_Sack")                 # 一袋货
    beam(bt, (0.3, 1.0, 0.45), (0.9, -2.6, 0.05), 0.06, "M_Wood")           # 篙
    under(go, obj(bt, "Sluice_Boat", (0.6, 4.6, -0.95)))
    fxw, fxs = fx("FX_WaterFlow", 0, 1.15, -0.4), fx("FX_Splash", 0, 2.4, -0.5)
    under(go, fxw, fxs)
    # 绞盘鼓（枢轴在轴心，绕 X 转）
    dr = K.MB()
    with dr.at(0, 0, 0, 0, 0, 90):
        dr.cyl(0, 0, -1.85, 1.85, 0.22, "M_Wood", seg=10)
        for zc in (-1.85, 1.85):
            dr.cyl(0, 0, zc - 0.06, zc + 0.06, 0.34, "M_Wood_Dark", seg=10)
        dr.cyl(0, 0, -2.4, 2.4, 0.05, "M_MC_Iron", seg=6)
    for x in (-2.35, 2.35):                                                         # 绞把（十字）
        dr.box(x - 0.04, -0.7, -0.05, x + 0.04, 0.7, 0.05, "M_Wood_Dark")
        dr.box(x - 0.04, -0.05, -0.7, x + 0.04, 0.05, 0.7, "M_Wood_Dark")
    for x in (-1.2, 1.2):
        with dr.at(0, 0, 0, 0, 0, 90):
            dr.cyl(0, 0, x - 0.12, x + 0.12, 0.27, "M_MC_Rope", seg=10)
    obj(dr, "Sluice_WinchDrum", (0, 1.15, WALK + 1.2))
    for i, (x, y, z) in enumerate(((-2.85, 1.15, -1.5), (2.85, 1.15, -1.5), (0, 1.76, -1.6))):
        anchor(f"ANCHOR_Sluice_Spot_{i + 1}", x, y, z)
    anchor("ANCHOR_Winch", 0, 2.1, WALK)
    anchor("ANCHOR_Latch", 0, 2.4, -0.3)


# ====================================================================== B. 第二幕场景组
def r_northgate():
    """北门工地（筑堡主线，「墙线隆起」）。城墙沿 X，城外 = -Y，剖面与 BLD_Wall_Seg 一致（墙高 7.0、8 m 模数）。
    x -20..-12 与 12..20 为已完工墙段（2 模块），中间 24 m（3 模块）在建：
      Stage_1 条石基础（到 1.5 m）→ Stage_2 外包半砌石 + 夯土（到 4.0 m，缺口处到 2.5 m）→ Stage_3 砌到墙顶（缺口两侧留槎）
      → Closure 合龙段（x -4..4，王德合龙）。四个子物体叠加显示。"""
    rng = random.Random(1560)
    # ---------- 地面 + 已完工墙段
    gnd = K.MB()
    gnd.box(-26, -12, 0, 26, 20, 0.03, "M_Road_Earth")
    for _ in range(26):                                                    # 踩实的泥 / 碎石屑
        x, y = rng.uniform(-24, 24), rng.uniform(-10, 18)
        if abs(y) < 3:
            continue
        gnd.box(x - rng.uniform(0.6, 1.6), y - rng.uniform(0.4, 1.2), 0.03, x + rng.uniform(0.6, 1.6), y + rng.uniform(0.4, 1.2), 0.045,
                rng.choice(["M_Mud", "M_MC_EarthLayer", "M_MC_EarthLayer"]))
    obj(gnd, "Ground", uv=4.0)
    wd = K.MB()
    for a, b in ((-20, -12), (12, 20)):
        wall_body(wd, a, b)
        wd.box(a + 3.8, -2.45, 6.4, a + 4.2, -1.9, 6.6, "M_Stone_Base")
    obj(wd, "Wall_Done")
    # ---------- Stage_1：条石基础 -0.5..1.5（全段，包括缺口）
    s1 = K.MB()
    wall_slice(s1, -12, 12, -0.5, 0.5, "M_Stone_Base")
    wall_slice(s1, -12, 12, 0.5, 1.5, "M_MC_StoneNew")
    s1.box(-12, -2.75, -0.5, 12, -2.35, 0.45, "M_Stone_Base")
    for x in range(-12, 12, 2):                                            # 条石竖缝
        s1.box(x + (0.0 if (x // 2) % 2 else 1.0) - 0.02, y_out(0.5) - 0.02, 0.5, x + (0.0 if (x // 2) % 2 else 1.0) + 0.02, y_out(1.5) + 0.0, 1.5, "M_Mud")
    s1.box(-12, y_out(0.5) - 0.02, 0.48, 12, y_out(0.5) + 0.05, 0.52, "M_Mud")
    obj(s1, "Stage_1")
    # ---------- Stage_2：外包石 + 夯土（两侧到 4.0，缺口到 2.5）
    s2 = K.MB()

    def earth_core(mb, a, b, z0, z1, yi_face=2.0, stone_in_top=None):
        n = int(round((z1 - z0) / 0.5))
        for k in range(n):
            za, zc = z0 + k * 0.5, z0 + (k + 1) * 0.5
            mb.prism([(y_out(za) + 0.7, za), (yi_face, za), (yi_face, zc), (y_out(zc) + 0.7, zc)], "x", a, b,
                     "M_MC_RammedEarth" if k % 2 == 0 else "M_MC_EarthLayer")
        # 外包石（比夯土低半层 → 半砌）
        mb.prism([(y_out(z0), z0), (y_out(z0) + 0.7, z0), (y_out(z1 - 0.5) + 0.7, z1 - 0.5), (y_out(z1 - 0.5), z1 - 0.5)], "x", a, b, "M_MC_StoneNew")
        # 内侧包石到 stone_in_top，再往上露夯土层 + 夹板
        sit = stone_in_top if stone_in_top is not None else z1 - 1.0
        mb.box(a, yi_face, z0, b, 2.5, sit, "M_MC_StoneNew")
        return sit

    for a, b in ((-12, -4), (4, 12)):
        sit = earth_core(s2, a, b, 1.5, 4.0)
        # 外包石顶上零散码放的石块（半砌）
        for i in range(int(b - a)):
            x = a + i + rng.uniform(0.05, 0.25)
            if rng.random() < 0.6:
                s2.box(x, y_out(3.5) + 0.02, 3.5, x + rng.uniform(0.5, 0.9), y_out(3.5) + 0.62, 3.5 + rng.choice((0.25, 0.5)), "M_MC_StoneNew")
        # 内侧夹板（夯土模板）+ 立桩
        s2.box(a, 2.5, sit, b, 2.58, 4.05, "M_MC_Plank")
        for x in range(int(a) + 1, int(b), 2):
            s2.box(x - 0.06, 2.58, sit - 0.3, x + 0.06, 2.7, 4.3, "M_Wood_Dark")
    earth_core(s2, -4, 4, 1.5, 2.5, stone_in_top=2.0)
    s2.box(-4, 2.5, 2.0, 4, 2.58, 2.55, "M_MC_Plank")
    obj(s2, "Stage_2")
    # ---------- Stage_3：两侧砌到墙顶（4.0..7.0 + 走道 + 部分垛墙），缺口边留槎
    s3 = K.MB()
    for a, b in ((-12, -4), (4, 12)):
        wall_slice(s3, a, b, 4.0, 7.0, "M_MC_StoneNew")
        s3.box(a, -1.5, 7.0, b, 2.5, WALK, "M_Wall_Top")
        s3.box(a, 2.35, 6.75, b, 2.6, 7.0, "M_Stone_Base")
        pa, pb = (a, b - 2.0) if a < 0 else (a + 2.0, b)
        s3.box(pa, -2.1, 7.0, pb, -1.5, 7.95, "M_Wall_Stone")
        s3.box(pa, -2.2, 7.95, pb, -1.4, 8.05, "M_Wall_Top")
        ca, cb = (a, b - 4.0) if a < 0 else (a + 4.0, b)
        s3.crenels(ca, cb, -2.1, -1.5, 8.05, 8.75, "M_Wall_Stone")
        # 留槎（缺口端每隔一层伸出半块）
        e = b if a < 0 else a
        sgn = 1 if a < 0 else -1
        for k in range(6):
            za = 4.0 + k * 0.5
            if k % 2 == 0:
                s3.prism([(y_out(za), za), (2.5, za), (2.5, za + 0.5), (y_out(za + 0.5), za + 0.5)], "x",
                         min(e, e + sgn * 0.5), max(e, e + sgn * 0.5), "M_MC_StoneNew")
        # 缺口下面那一层（2.5..4.0）的留槎
        for k in range(3):
            za = 2.5 + k * 0.5
            if k % 2 == 1:
                s3.prism([(y_out(za), za), (2.5, za), (2.5, za + 0.5), (y_out(za + 0.5), za + 0.5)], "x",
                         min(e, e + sgn * 0.5), max(e, e + sgn * 0.5), "M_MC_StoneNew")
    obj(s3, "Stage_3")
    # ---------- Closure：合龙段 x -4..4（2.5 → 墙顶）
    cl = K.MB()
    wall_slice(cl, -4, 4, 2.5, 7.0, "M_MC_StoneNew")
    cl.box(-4, -1.5, 7.0, 4, 2.5, WALK, "M_Wall_Top")
    cl.box(-4, 2.35, 6.75, 4, 2.6, 7.0, "M_Stone_Base")
    cl.box(-6, -2.1, 7.0, 6, -1.5, 7.95, "M_Wall_Stone")
    cl.box(-6, -2.2, 7.95, 6, -1.4, 8.05, "M_Wall_Top")
    cl.crenels(-8, 8, -2.1, -1.5, 8.05, 8.75, "M_Wall_Stone")
    cl.box(-0.9, -2.26, 4.6, 0.9, -2.18, 5.4, "M_Plaque")                    # 合龙石（刻字）
    obj(cl, "Closure")
    # ---------- 脚手架（城内侧 y 2.75..4.15，缺口处空出给吊架）
    sc = K.MB()
    xs = [-12.0, -9.5, -7.0, -4.6, 4.6, 7.0, 9.5, 12.0]
    for x in xs:
        for y in (2.8, 4.1):
            sc.cyl(x, y, 0, 7.8, 0.06, "M_MC_Bamboo", seg=6)
    for a, b in ((-12.0, -4.6), (4.6, 12.0)):
        for z in (2.0, 4.0, 6.0):
            for y in (2.8, 4.1):
                sc.box(a - 0.2, y - 0.04, z - 0.1, b + 0.2, y + 0.04, z - 0.02, "M_MC_Bamboo")
            for i in range(int((b - a) / 1.25)):                          # 跳板
                xa = a + i * 1.25
                sc.box(xa + 0.02, 2.75, z, xa + 1.23, 4.15, z + 0.05, "M_MC_Plank")
        for x in (a, b):
            for z in (2.0, 4.0, 6.0):
                sc.box(x - 0.04, 2.7, z - 0.1, x + 0.04, 4.2, z - 0.02, "M_MC_Bamboo")
        beam(sc, (a, 4.15, 0.2), (b, 4.15, 6.0), 0.07, "M_MC_Bamboo")         # 剪刀撑
        beam(sc, (b, 4.18, 0.2), (a, 4.18, 6.0), 0.07, "M_MC_Bamboo")
    for x in (-8.2,):                                                       # 爬梯（外侧）
        for dx in (-0.25, 0.25):
            sc.box(x + dx - 0.03, 4.25, 0, x + dx + 0.03, 4.33, 6.6, "M_Wood_Dark")
        for k in range(18):
            z = 0.3 + k * 0.35
            sc.box(x - 0.25, 4.26, z, x + 0.25, 4.32, z + 0.04, "M_Wood_Dark")
    # 吊架（三脚，跨在缺口城内侧）
    apex = (0, 3.6, 9.0)
    for p in ((-2.6, 6.8, 0), (2.6, 6.8, 0), (0, 2.75, 2.5)):
        beam(sc, p, apex, 0.16, "M_Wood_Dark")
    sc.box(-0.15, 3.45, 8.55, 0.15, 3.75, 8.9, "M_MC_Iron")
    sc.box(-0.015, 3.585, 5.2, 0.015, 3.615, 8.55, "M_MC_Rope")             # 吊绳
    sc.box(-0.35, 3.3, 4.9, 0.35, 3.9, 5.2, "M_MC_Rope")                    # 吊石兜
    beam(sc, (0, 3.6, 8.7), (3.6, 8.6, 0.8), 0.03, "M_MC_Rope")              # 牵到绞盘
    # 上料木桥（坡道顶 → 脚手架 4.0 层）
    sc.box(5.0, 4.15, 3.95, 8.0, 5.0, 4.05, "M_MC_Plank")
    obj(sc, "Scaffold")
    # ---------- 坡道（城内，沿 X 从 x=20 升到 x=6，顶 4.0）
    rp = K.MB()
    rp.prism([(6.0, 0.0), (21.0, 0.0), (6.0, 4.0)], "y", 5.0, 8.0, "M_MC_RammedEarth")
    rp.prism([(6.0, 4.0), (21.0, 0.0), (21.0, 0.06), (6.0, 4.06)], "y", 5.4, 7.6, "M_MC_Plank")
    for y in (5.0, 7.95):
        beam(rp, (21.0, y + 0.025, 0.05), (6.0, y + 0.025, 4.05), 0.18, "M_MC_Log")
    rp.box(4.6, 5.0, 0, 6.0, 8.0, 4.0, "M_MC_RammedEarth")
    obj(rp, "Ramp")
    # ---------- 石料场 / 灰浆 / 放线 / 木栏
    yd = K.MB()
    for row in range(3):                                                   # 条石垛
        for i in range(4 - row):
            x = -15.5 + i * 1.3 + row * 0.65
            yd.box(x, 10.0, row * 0.42, x + 1.2, 11.2, row * 0.42 + 0.4, "M_MC_StoneNew")
    for i in range(7):                                                     # 块石
        x, y = -11.0 + rng.uniform(-1.6, 1.6), 12.4 + rng.uniform(-0.8, 0.8)
        s = rng.uniform(0.45, 0.7)
        yd.box(x - s / 2, y - s / 2, 0, x + s / 2, y + s / 2, s * 0.8, "M_MC_StoneNew")
    yd.cyl(-8.0, 10.6, 0, 0.7, 1.4, "M_Stone_Base", seg=9, r_top=0.25)       # 碎石堆
    yd.box(-13.0, 13.5, 0, -12.2, 14.3, 0.55, "M_Wood_Dark")                 # 凿石垫墩
    # 灰浆槽 + 石灰堆 + 桶
    yd.box(0.6, 8.6, 0, 3.6, 9.8, 0.5, "M_MC_Plank")
    yd.box(0.72, 8.72, 0.3, 3.48, 9.68, 0.45, "M_MC_Lime")
    yd.cyl(5.6, 10.6, 0, 0.9, 1.2, "M_MC_Lime", seg=9, r_top=0.2)
    for x, y in ((4.2, 8.6), (4.6, 9.4)):
        yd.cyl(x, y, 0, 0.45, 0.24, "M_MC_Plank", seg=8, r_top=0.27)
        yd.cyl(x, y, 0.4, 0.43, 0.24, "M_MC_Lime", seg=8)
    # 放线木桩（城外侧墙脚线 + 合龙中线）+ 麻线
    stakes = [(x, -3.3) for x in range(-12, 13, 3)] + [(-12, 3.0), (12, 3.0)]
    for x, y in stakes:
        yd.box(x - 0.05, y - 0.05, 0, x + 0.05, y + 0.05, 0.75, "M_Wood")
        yd.box(x - 0.06, y - 0.06, 0.62, x + 0.06, y + 0.06, 0.78, "M_MC_StakeTip")
    yd.box(-12, -3.31, 0.66, 12, -3.29, 0.68, "M_MC_Rope")
    for x in (-4.0, 4.0):                                                  # 缺口两端插木签
        yd.box(x - 0.04, -3.5, 0, x + 0.04, -3.42, 1.1, "M_Wood")
        yd.box(x - 0.01, -3.5, 1.0, x + 0.3, -3.48, 1.2, "M_MC_StakeTip")
    # 木栏（石料场外圈）
    for (xa, ya), (xb, yb) in (((-17.0, 9.0), (-17.0, 15.5)), ((-17.0, 15.5), (-6.5, 15.5))):
        n = int(math.hypot(xb - xa, yb - ya) / 1.8)
        for i in range(n + 1):
            x, y = xa + (xb - xa) * i / n, ya + (yb - ya) * i / n
            yd.box(x - 0.06, y - 0.06, 0, x + 0.06, y + 0.06, 1.1, "M_Wood_Dark")
        for z in (0.5, 0.95):
            beam(yd, (xa, ya, z), (xb, yb, z), 0.06, "M_Wood")
    obj(yd, "Yard")
    # ---------- 挂点 / 站位
    fx("FX_RamDust_1", -8.0, 1.2, 4.05)
    fx("FX_RamDust_2", 8.0, 1.2, 4.05)
    fx("FX_WallRise", 0.0, 0.0, 1.5)
    fx("FX_Chisel", -12.6, 13.9, 0.6)
    fx("FX_MortarSplash", 2.1, 9.2, 0.5)
    fx("FX_ClosureDust", 0.0, 0.0, 7.1)
    for nm, p in (("ANCHOR_Closure", (0, 0.6, 2.5)), ("ANCHOR_WangPei_Watch", (-16.0, -0.6, WALK)),
                  ("ANCHOR_WangDe", (2.0, 3.2, 0)), ("ANCHOR_Ram_1", (-8.0, 1.2, 4.0)), ("ANCHOR_Ram_2", (8.0, 1.2, 4.0)),
                  ("ANCHOR_Carry_From", (-11.0, 9.2, 0)), ("ANCHOR_Carry_To", (-1.5, 5.4, 0)),
                  ("ANCHOR_Winch", (3.6, 8.6, 0)), ("ANCHOR_Gantry_Hook", (0, 3.6, 5.0)),
                  ("ANCHOR_Mortar", (2.1, 10.4, 0)), ("ANCHOR_Stake_A", (-4.0, -3.8, 0)), ("ANCHOR_Stake_B", (4.0, -3.8, 0)),
                  ("ANCHOR_Climb", (-8.2, 4.7, 0)), ("ANCHOR_Ramp_Top", (6.5, 6.5, 4.0)), ("ANCHOR_RosterDesk", (12.0, 12.0, 0)),
                  ("ANCHOR_StoneYard", (-12.0, 12.0, 0)), ("ANCHOR_cam_top", (0, 4.0, 45.0))):
        anchor(nm, *p)


def r_wanghouse():
    """王叔杲宅（墙外，一进院落）：门屋 → 天井 → 正厅（五开间，抬梁外露；Beam_Removable 可拆）+ 东书房 + 西厢房。18 x 22。"""
    S = K.MB()
    RG, RH, RS, RW = K.MB(), K.MB(), K.MB(), K.MB()
    # ---------- 地坪
    S.box(-9.15, -11.15, -0.2, 9.15, 11.15, 0.1, "M_Road_Stone")
    S.box(-1.0, -7.0, 0.1, 1.0, 2.5, 0.12, "M_Stone_Base")                 # 甬道
    # ---------- 院墙（前墙两翼 + 侧墙前段）
    for sx in (-1, 1):
        xa, xb = (-9.0, -4.5) if sx < 0 else (4.5, 9.0)
        S.box(xa, -11.0, 0.1, xb, -10.65, 3.4, "M_Plaster")
        S.box(xa, -11.02, 0.1, xb, -10.63, 0.9, "M_Plaster_Lower")
        wall_cap(S, xa, xb, -10.825, 3.4)
        xw = (-9.0, -8.65) if sx < 0 else (8.65, 9.0)
        S.box(xw[0], -10.65, 0.1, xw[1], -6.0, 3.4, "M_Plaster")
        wall_cap(S, -10.65, -6.0, (xw[0] + xw[1]) / 2, 3.4, axis="y")
    # ---------- 门屋（-11..-7）
    S.box(-4.5, -11.0, 0.1, 4.5, -7.0, 0.35, "M_Stone_Base")
    S.box(-1.4, -11.6, -0.2, 1.4, -11.0, 0.22, "M_Stone_Base")
    wall_x(S, -11.0, -10.6, -4.5, 4.5, 0.35, 3.6, "M_Plaster", [(-0.95, 0.95, 0.35, 2.95)])
    S.box(-4.5, -11.02, 0.35, 4.5, -10.6, 1.0, "M_Plaster_Lower")
    S.box(-1.15, -11.08, 0.35, -0.95, -10.95, 3.15, "M_Stone_Base")         # 石门框
    S.box(0.95, -11.08, 0.35, 1.15, -10.95, 3.15, "M_Stone_Base")
    S.box(-1.15, -11.08, 2.95, 1.15, -10.95, 3.15, "M_Stone_Base")
    S.box(-1.0, -11.12, 3.2, 1.0, -11.02, 3.5, "M_Plaque")                  # 门额
    for sx in (-1, 1):
        S.box(sx * 4.5 - (0.35 if sx > 0 else 0.0), -10.6, 0.35, sx * 4.5 + (0.0 if sx < 0 else 0.0) + (0.35 if sx < 0 else 0.0), -7.0, 3.6, "M_Plaster")
    wall_x(S, -7.35, -7.0, -4.15, 4.15, 0.35, 3.6, "M_Plaster", [(-1.5, 1.5, 0.35, 3.0)])
    for x in (-1.5, 1.5):
        S.cyl(x, -7.18, 0.35, 3.6, 0.15, "M_Wood_Dark", seg=8)
    for x in (-3.0, 3.0):
        lattice_window(S, x, 2.1, 1.0, 0.8, -11.0)
    RG.gable_roof(-4.5, 4.5, -11.0, -7.0, 3.6, 1.7, ohf=0.6, ohs=0.25)
    # 门扇（枢轴在门轴，团结里绕 Z 转开）
    for nm, hx, sgn in (("Door_L", -0.95, 1), ("Door_R", 0.95, -1)):
        d = K.MB()
        a, b = (0.0, 0.95) if sgn > 0 else (-0.95, 0.0)
        d.box(a, -0.05, 0, b, 0.05, 2.6, "M_Wood_Dark")
        d.box(a + 0.08, -0.07, 0.4, b - 0.08, -0.05, 2.3, "M_Wood")
        d.box((b - 0.18) if sgn > 0 else (a + 0.1), -0.11, 1.3, (b - 0.1) if sgn > 0 else (a + 0.18), -0.05, 1.42, "M_MC_Iron")
        obj(d, nm, (hx, -10.8, 0.35))
    # ---------- 西厢房（-9..-4.5, -6..1.5）
    S.box(-9.0, -6.0, 0.1, -4.5, 1.5, 0.3, "M_Stone_Base")
    wall_y(S, -4.85, -4.5, -6.0, 1.5, 0.3, 3.3, "M_Plaster", [(-3.4, -2.2, 0.3, 2.5), (-0.6, 0.9, 1.1, 2.3)])
    S.box(-9.0, -6.0, 0.3, -4.85, -5.65, 3.3, "M_Plaster")
    S.box(-9.0, 1.15, 0.3, -4.85, 1.5, 3.3, "M_Plaster")
    S.box(-9.0, -5.65, 0.3, -8.65, 1.15, 3.3, "M_Plaster")
    with S.at(-4.5, 0.15, 0, -90):
        lattice_window(S, 0, 1.7, 1.5, 1.2, 0)
    for x, y, r in ((-8.0, -4.8, 0.4), (-7.1, -4.9, 0.32), (-8.1, 0.4, 0.36)):
        jar(S, x, y, 0.3, r, r * 2.0)
    table(S, -8.6, -2.6, -7.6, -1.0, 0.3, 0.8, "M_Wood_Dark")
    RW.gable_roof_y(-9.0, -4.5, -6.0, 1.5, 3.3, 1.5, ohf=0.55, ohs=0.25)
    # ---------- 东书房（4.5..9, -6..1.5）
    S.box(4.5, -6.0, 0.1, 9.0, 1.5, 0.3, "M_Stone_Base")
    wall_y(S, 4.5, 4.85, -6.0, 1.5, 0.3, 3.3, "M_Plaster", [(-4.2, -3.0, 0.3, 2.5), (-1.6, 0.8, 1.0, 2.5)])
    S.box(4.85, -6.0, 0.3, 9.0, -5.65, 3.3, "M_Plaster")
    S.box(4.85, 1.15, 0.3, 9.0, 1.5, 3.3, "M_Plaster")
    S.box(8.65, -5.65, 0.3, 9.0, 1.15, 3.3, "M_Plaster")
    with S.at(4.5, -0.4, 0, 90):
        for k in range(3):                                                # 大窗：三扇格窗
            lattice_window(S, -0.8 + 0.8 * k, 1.75, 0.7, 1.4, 0, n=2)
    with S.at(9.0, -2.0, 0, 90):
        lattice_window(S, 0, 2.0, 0.8, 0.6, 0)
    # 书房陈设：书案、椅、书架、画缸
    table(S, 6.9, -2.4, 7.7, -0.6, 0.3, 0.82, "M_Wood")
    S.box(7.2, -1.9, 1.12, 7.45, -1.1, 1.15, "M_Paper")
    S.box(7.0, -2.25, 1.12, 7.18, -2.05, 1.18, "M_Window")                 # 砚
    chair(S, 8.2, -1.5, 0.3, face=3)
    S.box(5.2, 0.75, 0.3, 8.4, 1.15, 2.6, "M_Wood_Dark")                    # 书架
    for z in (0.9, 1.5, 2.1):
        S.box(5.3, 0.8, z, 8.3, 1.1, z + 0.05, "M_Wood")
        for i in range(10):
            x = 5.35 + i * 0.29
            S.box(x, 0.82, z + 0.05, x + 0.2, 1.08, z + 0.05 + 0.3 + 0.06 * (i % 3), "M_Paper" if i % 2 else "M_Cloth_Red")
    jar(S, 5.4, -5.0, 0.3, 0.25, 0.55, "M_Brick_Grey")
    RS.gable_roof_y(4.5, 9.0, -6.0, 1.5, 3.3, 1.5, ohf=0.55, ohs=0.25)
    # ---------- 天井：太平缸、花台
    jar(S, 0, -2.6, 0.1, 0.55, 0.8, "M_Brick_Grey")
    S.cyl(0, -2.6, 0.74, 0.76, 0.5, "M_Water", seg=12)
    for x in (-3.0, 3.0):
        S.box(x - 0.9, -5.4, 0.1, x + 0.9, -3.8, 0.55, "M_Brick_Grey")
        S.box(x - 0.8, -5.3, 0.55, x + 0.8, -3.9, 0.6, "M_Mud")
        S.ico(x, -4.6, 1.2, 0.7, "M_Leaf", sz=0.8)
        S.cyl(x, -4.6, 0.6, 0.9, 0.06, "M_Bark", seg=5)
    # ---------- 正厅（2.5..11）
    zf = 0.45
    S.box(-9.0, 2.5, 0.1, 9.0, 11.0, zf, "M_Stone_Base")
    for k in range(2):
        S.box(-1.5, 1.9 + k * 0.3, -0.1, 1.5, 2.5, 0.25 + k * 0.2, "M_Stone_Base")
    S.box(-8.6, 4.2, zf, 8.6, 10.6, zf + 0.02, "M_Floor_Brick")
    S.box(-9.0, 10.6, zf, 9.0, 11.0, 5.0, "M_Plaster")                      # 后墙
    for sx in (-1, 1):                                                      # 山墙（伸到前檐）
        xa, xb = (-9.0, -8.6) if sx < 0 else (8.6, 9.0)
        S.box(xa, 2.5, zf, xb, 10.6, 5.0, "M_Plaster")
        S.box(xa - 0.02, 2.48, zf, xb + 0.02, 10.6, 1.2, "M_Plaster_Lower")
    for sx in (-1, 1):                                                      # 前檐墙：次间、梢间格扇
        for xa in (1.5, 4.5):
            x0_, x1_ = (xa, xa + 3.0) if sx > 0 else (-xa - 3.0, -xa)
            geshan(S, x0_ + 0.15, x1_ - 0.15, zf, 3.9, 4.27, 4)
            S.box(x0_, 4.13, 3.9, x1_, 4.27, 4.9, "M_Wood")
        x0_, x1_ = (7.5, 8.6) if sx > 0 else (-8.6, -7.5)
        S.box(x0_, 4.0, zf, x1_, 4.27, 4.9, "M_Plaster")
    S.box(-1.5, 4.13, 3.9, 1.5, 4.27, 4.4, "M_Wood")                         # 明间敞开，上留横披
    S.box(-1.4, 4.05, 3.95, 1.4, 4.13, 4.35, "M_Plaque")
    for x in (-7.5, -4.5, -1.5, 1.5, 4.5, 7.5):                             # 檐柱 + 金柱
        col(S, x, 3.0, zf, 4.9, 0.17)
        col(S, x, 4.2, zf, 4.9, 0.19)
    for x in (-4.5, -1.5, 1.5, 4.5):
        col(S, x, 9.5, zf, 4.9, 0.19)
    S.box(-8.6, 2.85, 4.4, 8.6, 3.15, 4.85, "M_Wood")                       # 檐枋
    S.box(-8.6, 4.05, 4.5, 8.6, 4.35, 4.9, "M_Wood")                        # 金枋
    S.box(-8.6, 9.35, 4.5, 8.6, 9.65, 4.9, "M_Wood")
    for x in (-4.5, -1.5, 4.5):                                             # 五架梁（x=1.5 那根单独做 Beam_Removable）
        S.box(x - 0.17, 4.2, 4.5, x + 0.17, 9.5, 4.95, "M_Wood")
    for x in (-4.5, -1.5, 4.5):                                             # 瓜柱 + 三架梁（x=1.5 那一缝单独做 Truss_Upper_E）
        for y in (5.6, 8.1):
            S.box(x - 0.1, y - 0.1, 4.95, x + 0.1, y + 0.1, 5.6, "M_Wood_Dark")
        S.box(x - 0.14, 5.4, 5.6, x + 0.14, 8.3, 5.9, "M_Wood")
        S.box(x - 0.1, 6.75, 5.9, x + 0.1, 6.95, 6.7, "M_Wood_Dark")
    for y, z in ((3.0, 4.85), (4.2, 4.95), (5.6, 5.6), (6.85, 6.7), (8.1, 5.6), (9.5, 4.95)):   # 檩
        S.box(-8.6, y - 0.1, z, 8.6, y + 0.1, z + 0.18, "M_Ceiling")
    # 中堂：匾、画、条案、八仙桌、太师椅；两侧客椅
    S.box(-1.6, 10.52, 3.9, 1.6, 10.6, 4.5, "M_Plaque")
    S.box(-0.7, 10.55, 1.7, 0.7, 10.6, 3.6, "M_Paper")
    for x in (-1.3, 1.3):
        S.box(x - 0.25, 10.56, 1.9, x + 0.25, 10.6, 3.5, "M_Paper")
    table(S, -1.8, 9.85, 1.8, 10.4, zf, 0.95, "M_Wood_Dark")
    table(S, -0.5, 8.6, 0.5, 9.6, zf, 0.82, "M_Wood_Dark")
    chair(S, -0.85, 9.15, zf, face=0)
    chair(S, 0.85, 9.15, zf, face=0)
    for sx in (-1, 1):
        for y in (5.6, 7.4):
            chair(S, sx * 3.2, y, zf, face=2 if sx < 0 else 3)
        S.box(sx * 3.2 - 0.25, 6.3, zf, sx * 3.2 + 0.25, 6.7, zf + 0.7, "M_Wood_Dark")
    # 正厅屋面不填实（抬梁、檩外露，拆梁后的塌口能看见天），两端山尖单独补墙
    RH.gable_roof(-9.0, 9.0, 2.5, 11.0, 5.0, 2.9, ohf=0.9, ohs=0.3, fill=False)
    for xa, xb in ((-9.0, -8.6), (8.6, 9.0)):
        S.gable_fill(xa, xb, 2.5, 11.0, 5.0, 2.9, "M_Plaster")
    S.to_object("ENV_WangHouse")
    obj(RG, "ROOF_Gate")
    obj(RH, "ROOF_Hall")
    obj(RS, "ROOF_Study")
    obj(RW, "ROOF_Wing")
    wanghouse_beam_states(zf)
    for nm, p in (("ANCHOR_enter", (0, -12.3, 0)), ("ANCHOR_gate_in", (0, -6.4, 0.1)), ("ANCHOR_courtyard_talk", (0, -0.8, 0.12)),
                  ("ANCHOR_shugao_hall", (0, 8.0, zf)), ("ANCHOR_yan_hall", (0, 5.6, zf)), ("ANCHOR_beam_below", (1.5, 6.85, zf)),
                  ("ANCHOR_beam_drop", (3.0, -1.2, 0.12)), ("ANCHOR_study_desk", (7.3, -1.5, 1.12)), ("ANCHOR_study_seat", (8.2, -1.5, 0.3)),
                  ("ANCHOR_cam_hall", (0, -2.0, 3.4)), ("ANCHOR_cam_top", (0, 0, 32.0)),
                  # 第二幕宅院抉择（Docs/act2_site.md）：人物默认站位、门、室内各间、墙内外代价镜头
                  ("ANCHOR_Shugao", (0, 8.0, zf)), ("ANCHOR_Shugao_Gate", (0.9, -12.0, 0)),
                  ("ANCHOR_Door", (0, -11.9, 0.0)), ("ANCHOR_Door_Inner", (0, -9.0, 0.35)),
                  ("ANCHOR_Interior_Hall", (0, 6.6, zf)), ("ANCHOR_Interior_Study", (6.6, -2.6, 0.3)),
                  ("ANCHOR_Interior_Wing", (-6.6, -2.0, 0.3)), ("ANCHOR_Interior_Courtyard", (0, -4.8, 0.12)),
                  ("ANCHOR_Interior_GateHall", (0, -9.0, 0.35)),
                  ("ANCHOR_Beam_Ladder", (2.1, 6.85, zf)), ("ANCHOR_Beam_Carry_Out", (0, -12.8, 0)),
                  ("ANCHOR_Cost_Outside", (0, -18.0, 0)), ("ANCHOR_Cost_Inside", (0, 18.0, 0)),
                  ("ANCHOR_cam_wallview", (-14.0, -20.0, 9.0))):
        anchor(nm, *p)
    for nm, hx, sgn in (("Door_L", -0.95, 1), ("Door_R", 0.95, -1)):       # 门扇开启参考（转 90° 朝院内）
        ref_rot(f"ANCHOR_{nm}_Open", (hx, -10.8, 0.35), 90 * sgn)


def wanghouse_beam_states(zf):
    """拆梁两态。State_Beam_Intact：Beam_Removable（五架梁，原点在前端 = 前金柱 y=4.2 的梁底中心，梁沿 +Y 伸 5.3 m）、
    Truss_Upper_E（这一缝的瓜柱 + 三架梁 + 脊瓜柱）、ROOF_Hall（完整屋面）。
    State_Beam_Removed：ROOF_Hall_Broken（东次间屋脊塌口 x 0.3..2.7）、Beam_Fallen（拆下的梁，横在天井两块垫木上）、
    Rubble_Hall（厅里塌下的瓦、断椽和三架梁）、FX_RoofDust。"""
    gi, gr = group("State_Beam_Intact"), group("State_Beam_Removed")
    roof_hall = bpy.data.objects.get("ROOF_Hall")
    under(gi, roof_hall)
    bm = K.MB()
    bm.box(-0.17, 0.0, 0.0, 0.17, 5.3, 0.45, "M_Wood")
    for y in (0.0, 5.12):                                                  # 梁头榫（深一档）
        bm.box(-0.175, y, 0.05, 0.175, y + 0.18, 0.4, "M_Wood_Dark")
    under(gi, obj(bm, "Beam_Removable", (1.5, 4.2, 4.5)))
    tr = K.MB()
    for y in (5.6, 8.1):
        tr.box(-0.1, y - 0.1, 4.95, 0.1, y + 0.1, 5.6, "M_Wood_Dark")
    tr.box(-0.14, 5.4, 5.6, 0.14, 8.3, 5.9, "M_Wood")
    tr.box(-0.1, 6.75, 5.9, 0.1, 6.95, 6.7, "M_Wood_Dark")
    under(gi, obj(tr, "Truss_Upper_E", (1.5, 0, 0)))
    # 塌口屋面：x 0.3..2.7 去掉脊和上段坡，只剩檐口一段；塌口边挂一片下垂的瓦面、几根断椽
    rb = K.MB()
    for xa, xb in ((-9.3, 0.3), (2.7, 9.3)):
        rb.gable_roof(xa, xb, 2.5, 11.0, 5.0, 2.9, ohf=0.9, ohs=0.0, fill=False, curl=False)
    ym, zr = 6.75, 5.0 + 2.9 + 0.12
    for xe in (-9.3, 9.3 - 0.55):
        rb.box(xe, ym - 0.22, zr + 0.2, xe + 0.55, ym + 0.22, zr + 0.6, "M_Roof_Ridge")
    half, ku, kz = 4.25, 4.25 * K.MB.KU, K.MB.KZ
    zk = 5.0 + 2.9 * (1 - kz) + 0.12
    slope2 = 2.9 * (1 - kz) / (half - ku)
    for sgn in (-1, 1):                                                    # 塌口里保留的下段坡
        yk, ya = ym + sgn * ku, ym + sgn * (half + 0.9)
        ze = 5.0 + 0.12 - slope2 * 0.9
        rb.prism([(yk, zk), (ya, ze), (ya, ze - 0.18), (yk, zk - 0.22)], "x", 0.3, 2.7, "M_Roof_Tile")
    with rb.at(1.5, ym - ku + 0.2, zk - 0.1, 0, -28, 0):                   # 前坡上段断下来，挂在檩上斜插进厅
        rb.box(-1.0, -0.05, -1.5, 0.9, 0.18, 0.0, "M_Roof_Tile")
    for i, (x, a) in enumerate(((0.6, 18), (1.3, -12), (2.2, 25), (1.8, 40))):   # 断椽
        beam(rb, (x, ym - ku - 0.2, zk - 0.05), (x + 0.15 * (i - 1.5), ym - 0.6 + i * 0.35, zk + 0.6 - i * 0.45), 0.08, "M_Wood_Dark")
    rb.box(0.2, ym - ku - 0.25, zk - 0.25, 2.8, ym - ku + 0.05, zk - 0.05, "M_Roof_Ridge")    # 塌口边的碎瓦檐
    rb.box(0.2, ym + ku - 0.05, zk - 0.25, 2.8, ym + ku + 0.25, zk - 0.05, "M_Roof_Ridge")
    under(gr, obj(rb, "ROOF_Hall_Broken"))
    # 拆下的梁：平放在天井两块垫木上（与 Beam_Removable 同截面，原点同样在梁一端）
    bf = K.MB()
    with bf.at(0, 0, 0, -90):                                              # 沿 +X 横放（x -2.4..2.9，避开太平缸）
        bf.box(-0.17, 0.0, 0.0, 0.17, 5.3, 0.45, "M_Wood")
        for y in (0.0, 5.12):
            bf.box(-0.175, y, 0.05, 0.175, y + 0.18, 0.4, "M_Wood_Dark")
        for y in (0.7, 4.4):
            bf.box(-0.35, y - 0.12, -0.18, 0.35, y + 0.12, 0.0, "M_Wood_Dark")
    under(gr, obj(bf, "Beam_Fallen", (-2.4, -1.0, 0.12 + 0.18)))
    # 厅里的塌落物：瓦堆、碎瓦、断下的三架梁、瓜柱
    rh = K.MB()
    rng = random.Random(41)
    rh.cyl(1.5, 6.9, zf, zf + 0.45, 0.9, "M_Roof_Tile", seg=8, r_top=0.25)
    for _ in range(14):
        x, y = 1.5 + rng.uniform(-1.4, 1.4), 6.9 + rng.uniform(-1.6, 1.6)
        a = rng.uniform(0, 180)
        with rh.at(x, y, zf, a):
            rh.box(-0.16, -0.12, 0, 0.16, 0.12, 0.04, "M_Roof_Tile" if rng.random() < 0.7 else "M_Roof_Ridge")
    beam(rh, (0.6, 5.5, zf + 0.12), (2.6, 8.2, zf + 0.6), 0.28, "M_Wood")   # 三架梁斜搭在瓦堆上
    beam(rh, (2.3, 5.8, zf + 0.1), (2.9, 6.4, zf + 0.1), 0.2, "M_Wood_Dark")
    beam(rh, (0.4, 7.9, zf + 0.1), (0.5, 8.6, zf + 0.1), 0.2, "M_Wood_Dark")
    under(gr, obj(rh, "Rubble_Hall"))
    under(gr, fx("FX_RoofDust", 1.5, 6.85, 6.0))


# ---------------------------------------------------------------------- 盐场
PAN_STATE = ["M_MC_Brine", "M_MC_Brine", "M_MC_Brine", "M_Salt", "M_Salt", "M_Salt", "M_MC_PanDry", "M_MC_PanDry"]


def r_saltfield():
    """盐田组：8 块盐田（4 x 2）、田埂、卤水沟（带小闸板）、北侧芦席风障。32 x 22。
    每块盐田 SaltPan_<n> 是单独物体：三态（浅水 / 结晶 / 干涸）靠换材质 M_MC_Brine / M_Salt / M_MC_PanDry；
    结晶态另有 SaltPan_<n>_Heaps（耙起的小盐堆，默认只给 4–6 号）。"""
    rng = random.Random(7)
    g = K.MB()
    g.box(-16, -11, -0.32, 16, 5.4, -0.12, "M_Mud")                         # 池底
    # 外围田埂路（宽）、中间主埂、分埂
    g.box(-16, -11, -0.32, 16, -9.6, 0.06, "M_Dike")
    g.box(-16, 7.4, -0.32, 16, 11, 0.06, "M_Dike")
    g.box(-16, -9.6, -0.32, -14.6, 7.4, 0.06, "M_Dike")
    g.box(14.6, -9.6, -0.32, 16, 7.4, 0.06, "M_Dike")
    g.box(-14.6, -1.4, -0.32, 14.6, 0.0, 0.06, "M_Dike")                    # 中埂（行走主路）
    pans = []
    xs = [(-14.6, -7.5), (-7.5, -0.4), (-0.4, 6.7), (6.7, 14.6)]
    for (ya, yb) in ((-9.6, -1.4), (0.0, 5.4)):
        for i, (xa, xb) in enumerate(xs):
            a = xa + (0.0 if i == 0 else 0.3)
            b = xb - (0.0 if i == 3 else 0.3)
            pans.append((a, ya, b, yb))
    for i in range(1, 4):                                                   # 分埂
        x = xs[i][0]
        g.box(x - 0.3, -9.6, -0.32, x + 0.3, 5.4, 0.04, "M_Dike")
    # 卤水沟（北侧，y 5.4..7.4）
    g.box(-14.6, 5.4, -0.32, 14.6, 5.75, 0.04, "M_Dike")
    g.box(-14.6, 7.05, -0.32, 14.6, 7.4, 0.04, "M_Dike")
    g.box(-14.6, 5.75, -0.32, 14.6, 7.05, -0.3, "M_Mud")
    for i, (a, ya, b, yb) in enumerate(pans):                              # 进水口小闸板
        cx = (a + b) / 2
        if yb > 0:
            g.box(cx - 0.35, 5.35, -0.2, cx + 0.35, 5.8, 0.12, "M_Wood_Dark")
    # 风障：芦席 + 木桩
    for i in range(16):
        x = -15.0 + i * 2.0
        g.box(x - 0.07, 9.6, 0, x + 0.07, 9.74, 2.1, "M_Wood_Dark")
    g.box(-15.0, 9.62, 0.25, 15.0, 9.7, 1.95, "M_MC_Reed")
    for z in (0.7, 1.4):
        g.box(-15.0, 9.58, z, 15.0, 9.74, z + 0.05, "M_MC_Rope")
    obj(g, "ENV_SaltField", uv=4.0)
    wt = K.MB()
    wt.box(-14.6, 5.75, -0.3, 14.6, 7.05, -0.1, "M_MC_Brine")
    obj(wt, "NOCOL_BrineChannel", uv=4.0)
    for n, (a, ya, b, yb) in enumerate(pans, start=1):
        p = K.MB()
        p.box(a - (a + b) / 2, ya - (ya + yb) / 2, -0.04, b - (a + b) / 2, yb - (ya + yb) / 2, 0.0, PAN_STATE[n - 1])
        obj(p, f"SaltPan_{n}", ((a + b) / 2, (ya + yb) / 2, -0.07), uv=4.0)
        if PAN_STATE[n - 1] == "M_Salt":
            h = K.MB()
            for _ in range(7):
                x = rng.uniform(-(b - a) / 2 + 0.8, (b - a) / 2 - 0.8)
                y = rng.uniform(-(yb - ya) / 2 + 0.8, (yb - ya) / 2 - 0.8)
                r = rng.uniform(0.35, 0.6)
                h.cyl(x, y, -0.01, r * 0.8, r, "M_Salt", seg=8, r_top=0.08)
            obj(h, f"SaltPan_{n}_Heaps", ((a + b) / 2, (ya + yb) / 2, -0.07))
    for n, (a, ya, b, yb) in enumerate(pans, start=1):
        anchor(f"ANCHOR_Pan_{n}", (a + b) / 2, (ya + yb) / 2, -0.07)
    anchor("ANCHOR_Path_W", -15.3, -0.7, 0.06)
    anchor("ANCHOR_Path_E", 15.3, -0.7, 0.06)
    anchor("ANCHOR_Furnace", 0.0, -13.5, 0.0)
    anchor("ANCHOR_cam_top", 0, 0, 36.0)


def vat(size):
    r, h = {"S": (0.32, 0.6), "M": (0.48, 0.85), "L": (0.68, 1.1)}[size]
    mb = K.MB()
    jar(mb, 0, 0, 0, r, h)
    obj(mb, "Vat", uv=0.5)
    b = K.MB()
    b.cyl(0, 0, -0.01, 0.0, r * 0.86, "M_MC_Brine", seg=14)
    obj(b, "Brine", (0, 0, h * 0.86), uv=0.5)                  # 液面：上下平移表示卤水多少
    ld = K.MB()
    ld.cyl(0, 0, 0, 0.04, r * 1.0, "M_Wood", seg=12)
    ld.box(-r * 0.5, -0.04, 0.04, r * 0.5, 0.04, 0.1, "M_Wood_Dark")
    ld.box(-r * 0.95, -0.03, 0.0, r * 0.95, 0.03, 0.045, "M_Wood_Dark")
    off = 0.0 if size == "S" else r * 0.55
    obj(ld, "Lid", (off, 0, h), uv=0.5)
    if size != "S":                                            # 水瓢挂在缸沿
        lp = K.MB()
        lp.cyl(0, 0, 0, 0.1, 0.11, "M_MC_LogEnd", seg=8, r_top=0.13)
        beam(lp, (0.0, 0.1, 0.08), (0.0, 0.5, 0.18), 0.035, "M_Wood")
        obj(lp, "Ladle", (-r * 0.45, -r * 0.2, h - 0.02), uv=0.5)


def r_furnace():
    """煮盐灶：夯土灶台 + 大铁锅（Pan_Brine 卤水面 / Pan_Salt 结晶层，两态叠放）+ 前火口 + 后烟囱 + 灰坑 + 卤槽 + 小柴堆。约 5 x 6。"""
    mb = K.MB()
    mb.frustum((-1.7, -1.4, 1.7, 1.4), (-1.55, -1.25, 1.55, 1.25), 0, 0.95, "M_MC_StoveMud")
    mb.box(-1.75, -1.45, 0, 1.75, 1.45, 0.12, "M_Brick_Red")
    # 锅：外沿 + 锅腹（下沉）
    ring(mb, 0, 0, 0.93, 1.16, 0.98, 1.14, "M_MC_Iron", seg=16)
    mb.cyl(0, 0, 0.93, 0.95, 0.99, "M_MC_Iron", seg=16)
    # 火口（前 -Y）
    mb.box(-0.5, -1.47, 0.12, 0.5, -1.38, 0.7, "M_MC_Char")
    mb.box(-0.62, -1.52, 0.7, 0.62, -1.35, 0.86, "M_Brick_Red")
    for sx in (-1, 1):
        mb.box(min(sx * 0.5, sx * 0.62), -1.52, 0.12, max(sx * 0.5, sx * 0.62), -1.35, 0.7, "M_Brick_Red")
    mb.box(-0.42, -1.49, 0.12, 0.42, -1.45, 0.16, "M_MC_Ash")               # 火口灰（余烬 / 火苗在 Fire_0/1/2 里）
    mb.box(-0.9, -2.5, -0.06, 0.9, -1.45, 0.02, "M_MC_Ash")                 # 灰坑
    # 烟囱（后 +Y）
    mb.frustum((-0.45, 1.15, 0.45, 1.95), (-0.3, 1.3, 0.3, 1.8), 0, 3.8, "M_MC_StoveMud")
    mb.box(-0.36, 1.24, 3.8, 0.36, 1.86, 3.95, "M_Brick_Red")
    mb.box(-0.2, 1.4, 3.9, 0.2, 1.7, 3.96, "M_MC_Char")
    # 卤槽（+X 侧，从缸位斜到锅沿）
    beam(mb, (2.8, 0.0, 1.05), (1.0, 0.0, 1.12), 0.28, "M_Wood", h=0.12)
    for y in (-0.13, 0.13):
        beam(mb, (2.8, y, 1.12), (1.0, y, 1.19), 0.04, "M_Wood_Dark", h=0.1)
    for x in (2.6, 1.8):
        mb.box(x - 0.05, -0.05, 0, x + 0.05, 0.05, 1.0, "M_Wood_Dark")
    # 起盐踏台（-X 侧）
    mb.box(-2.5, -0.8, 0, -1.7, 0.8, 0.35, "M_Wood")
    # 小柴堆（火口旁）
    for k, (x, z) in enumerate(((-1.4, 0.08), (-1.2, 0.08), (-1.0, 0.08), (-1.3, 0.24), (-1.1, 0.24))):
        with mb.at(x, -2.0, z, 0, 0, 0):
            beam(mb, (0, -0.55, 0), (0, 0.55, 0), 0.15, "M_MC_Log")
    obj(mb, "ENV_SaltFurnace", uv=1.0)
    furnace_states()
    fx("FX_Fire", 0, -1.2, 0.35)
    fx("FX_Smoke", 0, 1.55, 4.0)
    fx("FX_Steam", 0, 0, 1.15)
    anchor("ANCHOR_Stoke", 0, -2.3, 0)
    anchor("ANCHOR_Pour", 3.2, 0, 0)
    anchor("ANCHOR_Scoop", -2.1, 0, 0.35)


def _flame(mb, x, y, z, r, h, lean=0.0):
    """低模火舌：外焰四棱锥（火色）+ 内焰小锥（火芯色）。"""
    with mb.at(x, y, z, 45, 0, lean):
        mb.cyl(0, 0, 0, h, r, "M_MC_Flame", seg=4, r_top=0.005)
        mb.cyl(0, 0, 0, h * 0.55, r * 0.55, "M_MC_FlameCore", seg=4, r_top=0.005)


def furnace_states():
    """煮盐三拍的三组状态，每组三选一 SetActive：
    Fire：Fire_0（熄：灰 + 两根黑炭）/ Fire_1（文火：三根柴、暗炭火、三簇小火舌）/ Fire_2（旺火：柴满、火舌窜出火口舔上灶脸）
    Brine：Brine_Full（满锅 z 1.10）/ Brine_Half（半锅 1.03，锅沿析出一圈盐霜）/ Brine_Low（见底 0.975，盐堆冒出液面）
    Salt：Salt_None（锅底湿膜）/ Salt_Crust（锅底薄盐壳 + 锅沿盐圈 + 浮花）/ Salt_Heap（耙成的盐堆 + 盐耙印）
    推荐组合：火候拍 Fire_1→2 + Brine_Full + Salt_None；卤水拍 Brine_Half + Salt_Crust；起盐拍 Fire_0 + Brine_Low + Salt_Heap。"""
    gf, gb, gs = group("Fire"), group("Brine"), group("Salt")
    y0 = -1.5                                                              # 火口外沿
    # ---- 火
    f0 = K.MB()
    f0.box(-0.45, y0 - 0.25, 0.12, 0.45, y0 + 0.05, 0.17, "M_MC_Ash")
    for x, a in ((-0.15, 15), (0.18, -10)):
        with f0.at(x, y0 - 0.1, 0.2, a):
            beam(f0, (0, -0.25, 0), (0, 0.25, 0), 0.09, "M_MC_Char")
    under(gf, obj(f0, "Fire_0", uv=0.5))
    f1 = K.MB()
    f1.box(-0.4, y0 - 0.2, 0.12, 0.4, y0 + 0.05, 0.18, "M_MC_Ember")
    for x, a in ((-0.2, 20), (0.0, 0), (0.22, -18)):
        with f1.at(x, y0 - 0.1, 0.22, a):
            beam(f1, (0, -0.3, 0), (0, 0.35, 0), 0.1, "M_MC_Log")
    for x, h in ((-0.18, 0.22), (0.05, 0.3), (0.24, 0.2)):
        _flame(f1, x, y0 - 0.05, 0.25, 0.09, h)
    under(gf, obj(f1, "Fire_1", uv=0.5))
    f2 = K.MB()
    f2.box(-0.48, y0 - 0.3, 0.12, 0.48, y0 + 0.05, 0.2, "M_MC_Ember")
    for x, z, a in ((-0.3, 0.22, 22), (-0.1, 0.22, 5), (0.12, 0.22, -8), (0.32, 0.22, -25), (-0.18, 0.34, -12), (0.15, 0.34, 15)):
        with f2.at(x, y0 - 0.12, z, a):
            beam(f2, (0, -0.4, 0), (0, 0.4, 0), 0.1, "M_MC_Log")
    for x, h, ln in ((-0.32, 0.38, -12), (-0.12, 0.55, -4), (0.08, 0.62, 3), (0.28, 0.45, 10), (-0.02, 0.4, 0), (0.4, 0.3, 18)):
        _flame(f2, x, y0 - 0.08, 0.3, 0.12, h, ln)
    for x in (-0.25, 0.0, 0.25):                                           # 舔上灶脸的火舌
        _flame(f2, x, y0 + 0.04, 0.72, 0.08, 0.32, 0)
    f2.box(-0.62, -1.535, 0.7, 0.62, -1.525, 0.9, "M_MC_Char")              # 火口上沿熏黑
    under(gf, obj(f2, "Fire_2", uv=0.5))
    # ---- 卤水（锅腹内径 0.98，锅底 0.95，锅沿顶 1.16）
    for nm, z, r in (("Brine_Full", 1.10, 0.98), ("Brine_Half", 1.03, 0.97), ("Brine_Low", 0.975, 0.96)):
        b = K.MB()
        b.cyl(0, 0, -0.02, 0.0, r, "M_MC_Brine", seg=16)
        if nm == "Brine_Half":                                             # 液面浮花 + 锅沿盐霜圈
            rng = random.Random(3)
            for _ in range(9):
                a, rr = rng.uniform(0, 6.28), rng.uniform(0.2, 0.8)
                b.cyl(rr * math.cos(a), rr * math.sin(a), 0.0, 0.006, rng.uniform(0.05, 0.11), "M_Salt", seg=5)
            ring(b, 0, 0, 0.0, 0.06, 0.9, 0.975, "M_Salt", seg=16)
        if nm == "Brine_Low":
            ring(b, 0, 0, 0.0, 0.12, 0.88, 0.975, "M_Salt", seg=16)
        under(gb, obj(b, nm, (0, 0, z)))
    # ---- 盐
    s0 = K.MB()
    s0.cyl(0, 0, 0.0, 0.006, 0.97, "M_MC_PanWet", seg=16)
    under(gs, obj(s0, "Salt_None", (0, 0, 0.95)))
    s1 = K.MB()
    s1.cyl(0, 0, 0.0, 0.015, 0.95, "M_Salt", seg=16)
    rng = random.Random(9)
    for _ in range(12):
        a, rr = rng.uniform(0, 6.28), rng.uniform(0.1, 0.8)
        s1.cyl(rr * math.cos(a), rr * math.sin(a), 0.015, 0.04, rng.uniform(0.06, 0.14), "M_Salt", seg=5, r_top=0.03)
    ring(s1, 0, 0, 0.0, 0.14, 0.9, 0.975, "M_Salt", seg=16)
    under(gs, obj(s1, "Salt_Crust", (0, 0, 0.95)))
    s2 = K.MB()
    s2.cyl(0, 0, 0.0, 0.02, 0.95, "M_Salt", seg=16)
    s2.cyl(0, 0, 0.02, 0.36, 0.55, "M_Salt", seg=10, r_top=0.1)
    for a in range(5):
        ang = a * 1.26 + 0.3
        s2.cyl(0.62 * math.cos(ang), 0.62 * math.sin(ang), 0.02, 0.17, 0.2, "M_Salt", seg=6, r_top=0.04)
    for k in range(4):                                                     # 耙印（暗槽）
        ang = k * 1.57 + 0.6
        with s2.at(0.75 * math.cos(ang), 0.75 * math.sin(ang), 0.02, math.degrees(ang)):
            s2.box(-0.12, -0.015, 0, 0.12, 0.015, 0.006, "M_MC_PanWet")
    under(gs, obj(s2, "Salt_Heap", (0, 0, 0.95)))


def r_saltset():
    """盐具组：盐堆、盐袋 x3、盐铲、盐筐、盐耙。原点在组中心地面。"""
    h = K.MB()
    h.cyl(0, 0, 0, 0.75, 0.95, "M_Salt", seg=10, r_top=0.12)
    h.cyl(0.55, 0.35, 0, 0.45, 0.55, "M_Salt", seg=8, r_top=0.08)
    obj(h, "SaltHeap", (-0.9, 0.4, 0), uv=0.5)
    for i, (x, y, rz, z) in enumerate(((0.75, 0.6, 10, 0), (1.35, 0.5, -8, 0), (1.05, 0.55, 90, 0.42))):
        bg = K.MB()
        with bg.at(0, 0, 0, rz):
            bg.frustum((-0.32, -0.22, 0.32, 0.22), (-0.28, -0.19, 0.28, 0.19), 0, 0.36, "M_MC_Sack")
            bg.frustum((-0.28, -0.19, 0.28, 0.19), (-0.1, -0.08, 0.1, 0.08), 0.36, 0.46, "M_MC_Sack")
            bg.box(-0.11, -0.09, 0.43, 0.11, 0.09, 0.48, "M_MC_Rope")
        obj(bg, f"SaltBag_{i + 1}", (x, y, z), uv=0.5)
    sh = K.MB()                                                    # 盐铲（平放）
    sh.box(-0.16, -0.2, 0, 0.16, 0.12, 0.025, "M_Wood")
    beam(sh, (0, 0.1, 0.02), (0, 1.25, 0.06), 0.045, "M_Wood_Dark")
    obj(sh, "SaltShovel", (-0.2, -0.75, 0), uv=0.5)
    bk = K.MB()                                                    # 盐筐（竹）
    bk.cyl(0, 0, 0, 0.36, 0.28, "M_MC_Bamboo", seg=10, r_top=0.34)
    bk.cyl(0, 0, 0.3, 0.33, 0.31, "M_Salt", seg=10)
    bk.cyl(0, 0, 0.34, 0.38, 0.35, "M_Wood_Dark", seg=10)
    obj(bk, "SaltBasket", (0.8, -0.5, 0), uv=0.5)
    rk = K.MB()                                                    # 盐耙（平放）
    rk.box(-0.4, -0.04, 0, 0.4, 0.04, 0.08, "M_Wood")
    for k in range(7):
        x = -0.36 + k * 0.12
        rk.box(x - 0.015, -0.1, 0, x + 0.015, -0.04, 0.06, "M_Wood_Dark")
    beam(rk, (0, 0.04, 0.04), (0, 1.6, 0.06), 0.04, "M_Wood_Dark")
    obj(rk, "SaltRake", (-1.6, -0.9, 0), uv=0.5)
    saltset_output()


def _basket(mb, x, y, full=True, r=0.34):
    mb.cyl(x, y, 0, 0.36, r * 0.82, "M_MC_Bamboo", seg=10, r_top=r)
    mb.cyl(x, y, 0.34, 0.38, r + 0.02, "M_Wood_Dark", seg=10)
    if full:
        mb.cyl(x, y, 0.36, 0.62, r * 0.96, "M_Salt", seg=10, r_top=0.08)


def saltset_output():
    """起盐后的产出：盐筐满 / 空两态、三档盐产出堆（每煮一锅多一档）、挑盐扁担（两筐满盐）。
    SaltBasket_Full / SaltBasket_Empty 二选一；SaltOutput_1/2/3 三选一（越往后越大，盐袋越多）；SaltPole 起盐完成后显示。"""
    bf = K.MB()
    _basket(bf, 0, 0, True)
    obj(bf, "SaltBasket_Full", (2.0, -0.6, 0), uv=0.5)
    be = K.MB()
    _basket(be, 0, 0, False)
    be.cyl(0, 0, 0.0, 0.02, 0.27, "M_Salt", seg=8)
    obj(be, "SaltBasket_Empty", (2.0, -0.6, 0), uv=0.5)
    for k in (1, 2, 3):
        o = K.MB()
        r = 0.45 + 0.25 * k
        o.cyl(0, 0, 0, r * 0.75, r, "M_Salt", seg=10, r_top=0.1)
        for j in range(k):
            o.cyl(r * 0.8 * math.cos(j * 2.1), r * 0.8 * math.sin(j * 2.1), 0, r * 0.4, r * 0.45, "M_Salt", seg=8, r_top=0.06)
        for j in range(2 * k):                                             # 扎好的盐袋
            with o.at(r + 0.45, -0.6 + j * 0.5, 0, 8 * (j % 3 - 1)):
                o.frustum((-0.3, -0.2, 0.3, 0.2), (-0.26, -0.17, 0.26, 0.17), 0, 0.34, "M_MC_Sack")
                o.frustum((-0.26, -0.17, 0.26, 0.17), (-0.09, -0.07, 0.09, 0.07), 0.34, 0.44, "M_MC_Sack")
        obj(o, f"SaltOutput_{k}", (1.0, 2.8, 0), uv=0.5)
    p = K.MB()                                                             # 扁担 + 两筐（平放地上，原点在扁担中点下地面）
    for x in (-0.75, 0.75):
        _basket(p, x, 0, True, r=0.28)
        for a in (0, 90, 180, 270):                                        # 筐绳
            dx, dy = 0.26 * math.cos(math.radians(a)), 0.26 * math.sin(math.radians(a))
            beam(p, (x + dx, dy, 0.36), (x, 0, 1.05), 0.012, "M_MC_Rope")
    beam(p, (-1.0, 0, 1.05), (1.0, 0, 1.05), 0.06, "M_Wood", h=0.04)
    obj(p, "SaltPole", (-2.2, 2.3, 0), uv=0.5)


def r_firewood():
    """柴组：柴垛（码好的劈柴 + 两根桩）、引火草捆、火钳。原点在组中心地面。"""
    w = K.MB()
    for row, n in enumerate((5, 4, 3)):
        for i in range(n):
            x = -0.4 * (n - 1) / 2 + 0.4 * i
            z = 0.17 + row * 0.32
            with w.at(x, 0, z, 0, 90, 0):
                w.cyl(0, 0, -0.6, 0.6, 0.16, "M_MC_Log", seg=6)
    for x in (-1.15, 1.15):
        w.box(x - 0.06, -0.06, 0, x + 0.06, 0.06, 1.2, "M_Wood_Dark")
    obj(w, "WoodStack", (0, 0.5, 0), uv=0.5)
    k = K.MB()
    for i, (x, y) in enumerate(((0, 0), (0.32, 0.05), (0.16, 0.28))):
        k.cyl(x, y, 0, 0.75, 0.13, "M_MC_Straw", seg=7, r_top=0.11)
        k.cyl(x, y, 0.32, 0.4, 0.145, "M_MC_Rope", seg=7)
    obj(k, "Kindling", (1.7, -0.3, 0), uv=0.5)
    t = K.MB()                                                  # 火钳（平放，两股交叉）
    beam(t, (-0.05, 0, 0.02), (0.04, 0.85, 0.03), 0.025, "M_MC_Iron")
    beam(t, (0.05, 0, 0.02), (-0.04, 0.85, 0.03), 0.025, "M_MC_Iron")
    t.box(-0.03, 0.05, 0.0, 0.03, 0.11, 0.05, "M_MC_Iron")
    obj(t, "FireTongs", (-1.4, -0.9, 0), uv=0.5)


def recipes():
    R = {
        "BLD_MING_AncestralHall": ("Buildings", r_ancestral),
        "BLD_MING_Temple": ("Buildings", r_temple),
        "BLD_MING_GateTower": ("Buildings", r_gate_tower),
        "BLD_MING_HuanhaiLou": ("Buildings", r_huanhai),
        "BLD_MING_WaterGate_Sluice": ("Buildings", r_sluice),
        "ENV_NorthGate_Build": ("Environments", r_northgate),
        "ENV_WangHouse": ("Environments", r_wanghouse),
        "ENV_SaltField": ("Environments", r_saltfield),
        "ENV_SaltFurnace": ("Environments", r_furnace),
        "PROP_SaltSet": ("Props", r_saltset),
        "PROP_Firewood": ("Props", r_firewood),
    }
    for s in ("S", "M", "L"):
        R[f"PROP_BrineVat_{s}"] = ("Props", (lambda ss=s: vat(ss)))
    return R
