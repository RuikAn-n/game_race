"""
《入谱》第二幕 · 城市 P1 部件（让城市像城市）—— 明代 1560
=============================================================

由 build_yongchang.py 统一生成/导出（recipes() 返回 {资产名: (分类, 生成函数)}）。
对应 Docs/第二幕_策划对照与建模缺口.md §5 P1「道路 / 市场 / 城墙外」，说明见 Docs/act2_city_lod.md。

  路口与街角  ENV_MING_Road_Straight / _Cross / _Tee / _Corner（主街、横街 6 m）
              ENV_MING_Road_*_L4（巷道 4 m）
              石板路面 + 两侧石砌明沟（局部石盖板），顶面 z=0.12，COL_Walk 是平的走面（沟不绊脚）
  排水沟单件  PROP_MING_Drain_Straight / _Covered / _Outfall（沟口跌水）
  跨沟石板桥  BLD_MING_SlabBridge（已有的 BLD_Bridge_* 是跨河 3 m 起、带栏板的桥，这个是跨沟 1.2 m 的三块条石）
  城墙外      ENV_MING_DirtRoad_Straight / _Bend（土路 5 m）/ _Ridge（田埂），PROP_MING_Culvert（涵洞），PROP_MING_MileStone（界石）
  市场        PROP_MING_MarketGoods_Cloth / _Pottery / _Bamboo / _Fish / _Rice / _Veg，组合 ENV_MING_MarketRow

约定：1 unit = 1 m；正面朝 Blender -Y（团结 +Z）。Blender +X = 团结 -X。
      道路件原点在件中心地面；道具原点在底面中心（最低点 z=0）。
      COL_* 只做碰撞，NOCOL_* 不加碰撞（水面、布棚），ANCHOR_* 站位。
"""
import math
import random

import bpy

import rupu_kit as K

CITY_PALETTE = {
    "M_MKM_ClothIndigo": "#4a5560", "M_MKM_ClothBrown": "#8A5A3B", "M_MKM_ClothRaw": "#cbbd9c", "M_MKM_ClothRed": "#9a4632",
    "M_MKM_Pot": "#7a5236", "M_MKM_PotGlaze": "#3b332b", "M_MKM_Bamboo": "#a38a58", "M_MKM_BambooDark": "#7a6640",
    "M_MKM_Fish": "#8a8e86", "M_MKM_Sack": "#b3a17a", "M_MKM_Rice": "#E8DCC8", "M_MKM_Greens": "#5d6e40",
    "M_MKM_Radish": "#d9d0bd", "M_MKM_Fruit": "#a8643a", "M_MKM_Rope": "#9c8a64", "M_MKM_Awning": "#b8a882",
    "M_MKM_Mat": "#9a8556",
}
K.PALETTE.update(CITY_PALETTE)

ROAD_TOP = 0.12          # 石板路顶面
CURB_TOP = 0.14          # 沟沿石
DIRT_TOP = 0.05          # 土路顶面


# ====================================================================== 小工具
def empty(name, loc, kind="ARROWS", size=0.3):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = kind
    o.empty_display_size = size
    o.location = loc
    bpy.context.scene.collection.objects.link(o)
    return o


def _norm(x, y):
    d = math.hypot(x, y) or 1.0
    return x / d, y / d


def strip(mb, center, ht, hb, zt, mat, zb=0.0, caps=True):
    """沿折线 center[(x,y)...] 拉一条梯形截面的带（土路、田埂、车辙）：顶宽 2*ht 在 zt，底宽 2*hb 在 zb。"""
    n = len(center)
    rings = []
    for k, (cx, cy) in enumerate(center):
        a = center[max(0, k - 1)]
        b = center[min(n - 1, k + 1)]
        dx, dy = _norm(b[0] - a[0], b[1] - a[1])
        nx, ny = -dy, dx                                   # 左手法向
        rings.append(mb.addv([(cx + nx * hb, cy + ny * hb, zb), (cx + nx * ht, cy + ny * ht, zt),
                              (cx - nx * ht, cy - ny * ht, zt), (cx - nx * hb, cy - ny * hb, zb)]))
    for r0, r1 in zip(rings, rings[1:]):
        mb.face([r0 + 2, r1 + 2, r1 + 1, r0 + 1], mat)        # 顶
        mb.face([r0 + 1, r1 + 1, r1 + 0, r0 + 0], mat)        # 左坡
        mb.face([r0 + 3, r1 + 3, r1 + 2, r0 + 2], mat)        # 右坡
    if caps:
        r = rings[0]
        mb.face([r + 3, r + 2, r + 1, r + 0], mat)
        r = rings[-1]
        mb.face([r + 0, r + 1, r + 2, r + 3], mat)


def tuft(mb, x, y, z, s, mat="M_Ground_Grass"):
    mb.cyl(x, y, z, z + 0.35 * s, 0.2 * s, mat, seg=4, r_top=0.02)
    mb.cyl(x + 0.12 * s, y + 0.05 * s, z, z + 0.25 * s, 0.13 * s, "M_Leaf", seg=3, r_top=0.01)


# ====================================================================== 1 石板路：直段 / 十字 / 丁字 / 转角
SIDE = {"N": "yn", "S": "yp", "E": "xn", "W": "xp"}     # 团结方位 -> Blender 边（团结 +Z = Blender -Y，+X = -X）


def paving(mb, rect, hx, hy, rng, row=0.6, ln=1.5, gap=0.025):
    """rect 内铺横向条石（行宽 row、错缝），石缝里露出深色垫层。"""
    x0, y0, x1, y1 = rect
    mb.box(x0, y0, 0.0, x1, y1, ROAD_TOP - 0.025, "M_Bank_Stone")
    for k in range(math.floor((y0 + hy) / row), math.ceil((y1 + hy) / row)):
        ga, gb = -hy + k * row, -hy + (k + 1) * row
        ya, yb = max(y0, ga), min(y1, gb)
        if yb - ya < 0.02:
            continue
        ya += gap / 2 if ya == ga else 0.0          # 只在条石的真缝上留缝；被格子边裁开处不留（相邻格接着铺）
        yb -= gap / 2 if yb == gb else 0.0
        off = (k % 2) * ln / 2
        for m in range(math.floor((x0 + hx + off) / ln) - 1, math.ceil((x1 + hx + off) / ln) + 1):
            ha, hb = -hx - off + m * ln, -hx - off + (m + 1) * ln
            xa, xb = max(x0, ha), min(x1, hb)
            if xb - xa < 0.02:
                continue
            xa += gap / 2 if xa == ha else 0.0
            xb -= gap / 2 if xb == hb else 0.0
            z1 = ROAD_TOP + rng.uniform(-0.004, 0.003) * (1 if (k * 7 + m) % 3 else 0)
            mb.box(xa, ya, ROAD_TOP - 0.025, xb, yb, z1, "M_Road_Stone", skip_bottom=True)


def road_tile(name, W, open_u, L=None):
    """W 宽（路宽，含两侧沟）× L 长的路面件。open_u：通路的边（团结方位 N/S/E/W）。
    封闭的边 = 临街房屋一侧：沿边一条沟沿石 + 一条明沟；两条通路边夹的角上，沟从两路汇到角上。"""
    op = {SIDE[s] for s in open_u}
    L = L or W
    curb, drain = (0.25, 0.4) if W >= 5 else (0.2, 0.3)
    hx, hy = W / 2, L / 2
    xs = [-hx, -hx + curb, -hx + curb + drain, hx - curb - drain, hx - curb, hx]
    ys = [-hy, -hy + curb, -hy + curb + drain, hy - curb - drain, hy - curb, hy]

    def band(i, neg, pos):
        return {0: (neg, 0), 1: (neg, 1), 2: None, 3: (pos, 1), 4: (pos, 0)}[i]

    def role(bx, by):
        if bx is None and by is None:
            return "pave"
        if by is None or bx is None:
            side, k = bx or by
            if side in op:
                return "pave"
            return "curb" if k == 0 else "drain"
        xc, yc = bx[0] not in op, by[0] not in op
        a, b = bx[1], by[1]
        if xc and yc:
            return "drain" if (a == 1 and b == 1) else "curb"
        if xc:
            return "curb" if a == 0 else "drain"
        if yc:
            return "curb" if b == 0 else "drain"
        return "curb" if (a == 0 and b == 0) else "drain"

    rng = random.Random(hash(name) & 0xffff)
    mb = K.MB()
    for i in range(5):
        for j in range(5):
            bx, by = band(i, "xn", "xp"), band(j, "yn", "yp")
            r = role(bx, by)
            rect = (xs[i], ys[j], xs[i + 1], ys[j + 1])
            if r == "pave":
                paving(mb, rect, hx, hy, rng)
            elif r == "curb":
                mb.box(rect[0], rect[1], 0.0, rect[2], rect[3], CURB_TOP, "M_Stone_Base")
            else:
                mb.box(rect[0], rect[1], 0.0, rect[2], rect[3], 0.02, "M_Mud")
                # 沿边长沟的中段盖一块石盖板（局部盖板，留出明沟）
                if (bx is None) != (by is None):
                    long_x = bx is None
                    if long_x:
                        cx = 0.0
                        mb.box(cx - 0.4, rect[1] - 0.06, ROAD_TOP - 0.02, cx + 0.4, rect[3] + 0.06, ROAD_TOP + 0.035, "M_Stone_Base")
                    else:
                        cy = 0.0
                        mb.box(rect[0] - 0.06, cy - 0.4, ROAD_TOP - 0.02, rect[2] + 0.06, cy + 0.4, ROAD_TOP + 0.035, "M_Stone_Base")
    mb.to_object(name, uv_scale=2.0)
    col = K.MB()
    col.box(-hx, -hy, 0.0, hx, hy, ROAD_TOP, "M_Road_Stone")
    col.to_object("COL_Walk")


ROAD_KINDS = {
    "Straight": {"N", "S"},
    "Cross": {"N", "S", "E", "W"},
    "Tee": {"N", "S", "E"},
    "Corner": {"S", "E"},
}


# ====================================================================== 2 排水沟单件 / 跨沟石板桥
def drain_run(mb, y0, y1, covered=False):
    """独立明沟一段（沿 Y）：两道条石沟墙 + 压顶 + 沟底，内宽 0.5。"""
    n = max(1, round((y1 - y0) / 1.0))
    for k in range(n):
        a = y0 + (y1 - y0) * k / n + 0.01
        b = y0 + (y1 - y0) * (k + 1) / n - 0.01
        for s in (-1, 1):
            mb.box(s * 0.25, a, 0.0, s * 0.45, b, 0.30, "M_Bank_Stone")
            mb.box(s * 0.22, a, 0.30, s * 0.5, b, 0.36, "M_Stone_Base")
    mb.box(-0.25, y0, 0.0, 0.25, y1, 0.03, "M_Mud")
    if covered:
        m = max(1, int((y1 - y0) / 0.66))
        for k in range(m):
            a = y0 + (y1 - y0) * k / m + 0.03
            b = y0 + (y1 - y0) * (k + 1) / m - 0.03
            mb.box(-0.5, a, 0.36, 0.5, b, 0.46, "M_Stone_Base")


def water_strip(name, x0, y0, x1, y1, z):
    w = K.MB()
    w.box(x0, y0, z - 0.01, x1, y1, z, "M_Water", skip_bottom=True)
    return w.to_object(name, uv_scale=2.0)


def r_drain_straight():
    mb = K.MB()
    drain_run(mb, -1.0, 1.0)
    mb.to_object("PROP_MING_Drain_Straight", uv_scale=1.0)
    water_strip("NOCOL_DrainWater", -0.25, -1.0, 0.25, 1.0, 0.07)


def r_drain_covered():
    mb = K.MB()
    drain_run(mb, -1.0, 1.0, covered=True)
    mb.to_object("PROP_MING_Drain_Covered", uv_scale=1.0)


def r_drain_outfall():
    """沟口跌水：明沟从后(+Y)流来，到前沿伸出一块挑出的跌水石，水落进前面的小石池（前 -Y 接河岸 / 大沟）。"""
    mb = K.MB()
    drain_run(mb, -0.2, 1.2)
    mb.box(-0.5, -0.32, 0.0, 0.5, -0.2, 0.36, "M_Bank_Stone")            # 沟口挡墙
    mb.box(-0.22, -0.62, 0.24, 0.22, -0.2, 0.31, "M_Stone_Base")          # 跌水石（挑出）
    mb.box(-0.6, -1.5, 0.0, 0.6, -0.32, 0.03, "M_Mud")                    # 池底
    for x0, x1, y0, y1 in ((-0.6, -0.45, -1.5, -0.32), (0.45, 0.6, -1.5, -0.32), (-0.45, 0.45, -1.5, -1.35)):
        mb.box(x0, y0, 0.0, x1, y1, 0.22, "M_Bank_Stone")
    mb.to_object("PROP_MING_Drain_Outfall", uv_scale=1.0)
    water_strip("NOCOL_DrainWater", -0.25, -0.2, 0.25, 1.2, 0.07)
    water_strip("NOCOL_PoolWater", -0.45, -1.35, 0.45, -0.32, 0.14)
    fall = K.MB()
    fall.prism([(-0.6, 0.3), (-0.6, 0.27), (-0.72, 0.13), (-0.75, 0.13)], "x", -0.16, 0.16, "M_Water")
    fall.to_object("NOCOL_Fall", uv_scale=1.0)
    empty("FX_Splash", (0, -0.75, 0.14), "SPHERE", 0.1)


def r_slab_bridge():
    """跨沟石板桥：两岸条石桥墩，三块条石并排架过 1.2 m 的沟；两端各一级踏步。"""
    mb = K.MB()
    for s in (-1, 1):
        mb.box(-1.15, s * 0.6, 0.0, 1.15, s * 1.15, 0.32, "M_Bank_Stone")           # 桥墩
        mb.box(-1.0, s * 1.6, 0.0, 1.0, s * 1.15, 0.16, "M_Stone_Base")              # 踏步
    for k in range(3):
        x0 = -0.96 + k * 0.65
        mb.box(x0, -1.3, 0.32, x0 + 0.62, 1.3, 0.47, "M_Stone_Base")
    mb.box(-1.15, -0.6, 0.0, 1.15, 0.6, 0.02, "M_Mud")
    mb.to_object("BLD_MING_SlabBridge", uv_scale=1.0)
    water_strip("NOCOL_DitchWater", -1.6, -0.6, 1.6, 0.6, 0.08)


# ====================================================================== 3 城墙外：土路 / 弯道 / 田埂 / 涵洞 / 界石
def dirt_road(name, center, rng):
    mb = K.MB()
    strip(mb, center, 2.4, 2.75, DIRT_TOP, "M_Road_Earth")
    for off in (-0.8, 0.8):                                        # 两道车辙
        pts = []
        for k, (cx, cy) in enumerate(center):
            a = center[max(0, k - 1)]
            b = center[min(len(center) - 1, k + 1)]
            dx, dy = _norm(b[0] - a[0], b[1] - a[1])
            pts.append((cx - dy * off, cy + dx * off))
        strip(mb, pts, 0.11, 0.13, DIRT_TOP + 0.006, "M_Mud", zb=DIRT_TOP - 0.004, caps=False)
    # 路边杂草、碎石
    for k in range(len(center) - 1):
        (ax, ay), (bx, by) = center[k], center[k + 1]
        seg = math.hypot(bx - ax, by - ay)
        dx, dy = _norm(bx - ax, by - ay)
        for _ in range(max(1, int(seg / 0.8))):
            t = rng.random()
            px, py = ax + (bx - ax) * t, ay + (by - ay) * t
            side = rng.choice((-1, 1))
            d = rng.uniform(2.6, 3.0)
            tuft(mb, px - dy * d * side, py + dx * d * side, 0.0, rng.uniform(0.8, 1.4))
            if rng.random() < 0.3:
                d = rng.uniform(2.2, 2.5)
                mb.ico(px - dy * d * side, py + dx * d * side, DIRT_TOP, 0.09, "M_Stone_Base", 1.3, 1.0, 0.6, subdiv=1)
    mb.to_object(name, uv_scale=2.0)
    col = K.MB()
    strip(col, center, 2.4, 2.75, DIRT_TOP, "M_Road_Earth")
    col.to_object("COL_Walk")


def r_dirt_straight():
    dirt_road("ENV_MING_DirtRoad_Straight", [(0, 5.0), (0, 0.0), (0, -5.0)], random.Random(31))


BEND_R = 8.0


def r_dirt_bend():
    """90° 弯：入口在原点、朝团结 +Z 出发，向右（团结 +X）转，出口中心在团结 (8, 0, 8)、朝 +X。"""
    n = 12
    pts = []
    for k in range(n + 1):
        t = math.radians(90 * k / n)
        pts.append((-BEND_R + BEND_R * math.cos(t), -BEND_R * math.sin(t)))
    dirt_road("ENV_MING_DirtRoad_Bend", pts, random.Random(32))


def r_ridge():
    """田埂：顶宽 0.6、底宽 1.3、高 0.3，长 10 m，顶上踩出的土路 + 两侧草。"""
    rng = random.Random(33)
    mb = K.MB()
    pts = [(0, 5.0), (0.08, 2.5), (0, 0.0), (-0.08, -2.5), (0, -5.0)]
    strip(mb, pts, 0.3, 0.65, 0.3, "M_Dike")
    strip(mb, pts, 0.14, 0.16, 0.306, "M_Road_Earth", zb=0.296, caps=False)
    for _ in range(18):
        y = rng.uniform(-4.8, 4.8)
        s = rng.choice((-1, 1))
        tuft(mb, s * rng.uniform(0.25, 0.5), y, rng.uniform(0.05, 0.2), rng.uniform(0.7, 1.2))
    mb.to_object("ENV_MING_DirtRoad_Ridge", uv_scale=2.0)


def r_culvert():
    """涵洞：土路（沿 Y，宽 5）从一条沟（沿 X）上拱起跨过，两侧石砌洞口墙 + 压顶；路面 0.8 高，两头坡道落回土路 0.05。"""
    mb = K.MB()
    top, half = 0.8, 1.2
    with mb.at(0, 0, 0, rz=90):          # arch_slab 的洞沿局部 Y -> 转 90° 后沿 X 穿过路基
        mb.arch_slab(-half, half, -0.32, 0.32, 0.0, 0.32, top - 0.05, -2.5, 2.5, "M_Bank_Stone", seg=6)
    mb.box(-2.5, -half, top - 0.05, 2.5, half, top, "M_Road_Earth")
    for s in (-1, 1):                                                         # 坡道
        if s > 0:
            mb.prism([(half, 0.0), (half + 2.6, 0.0), (half + 2.6, DIRT_TOP), (half, top)], "x", -2.5, 2.5, "M_Road_Earth")
        else:
            mb.prism([(-half - 2.6, 0.0), (-half, 0.0), (-half, top), (-half - 2.6, DIRT_TOP)], "x", -2.5, 2.5, "M_Road_Earth")
    for s in (-1, 1):                                                         # 洞口墙（突出路肩，带压顶）
        x0, x1 = (2.5, 2.85) if s > 0 else (-2.85, -2.5)
        with mb.at(0, 0, 0, rz=90):
            mb.arch_slab(-half - 0.3, half + 0.3, -0.32, 0.32, 0.0, 0.32, top + 0.35, -x1, -x0, "M_Bank_Stone", seg=6)
        mb.box(x0 - 0.05, -half - 0.35, top + 0.35, x1 + 0.05, half + 0.35, top + 0.45, "M_Stone_Base")
        for sg in (-1, 1):                                                    # 两翼小八字墙
            ya, yb = sg * (half + 0.3), sg * (half + 1.2)
            mb.prism([(ya, 0.0), (yb, 0.0), (ya, top + 0.3)], "x", x0, x1, "M_Bank_Stone")
    mb.box(-3.8, -0.32, 0.0, 3.8, 0.32, 0.02, "M_Mud")
    mb.to_object("PROP_MING_Culvert", uv_scale=1.0)
    water_strip("NOCOL_DitchWater", -3.8, -0.32, 3.8, 0.32, 0.08)


def r_milestone():
    """路边界石：方座 + 抹角石柱，正面（-Y）一块刻字面（M_Plaque，留给贴字）。"""
    mb = K.MB()
    mb.box(-0.26, -0.18, 0.0, 0.26, 0.18, 0.12, "M_Bank_Stone")
    mb.frustum((-0.16, -0.1, 0.16, 0.1), (-0.14, -0.09, 0.14, 0.09), 0.12, 0.92, "M_Stone_Base")
    mb.hexa([(-0.14, -0.09, 0.92), (0.14, -0.09, 0.92), (0.14, 0.09, 0.92), (-0.14, 0.09, 0.92),
             (-0.05, -0.03, 1.02), (0.05, -0.03, 1.02), (0.05, 0.03, 1.02), (-0.05, 0.03, 1.02)], "M_Stone_Base")
    mb.box(-0.09, -0.106, 0.3, 0.09, -0.09, 0.82, "M_Plaque")
    mb.to_object("PROP_MING_MileStone", uv_scale=0.5)


# ====================================================================== 4 市场：明代货物
def bench(mb, w, d, h, mat="M_Wood"):
    mb.box(-w / 2, -d / 2, h - 0.05, w / 2, d / 2, h, mat)
    for sx in (-1, 1):
        for sy in (-1, 1):
            x, y = sx * (w / 2 - 0.08), sy * (d / 2 - 0.08)
            mb.box(x - 0.03, y - 0.03, 0.0, x + 0.03, y + 0.03, h - 0.05, "M_Wood_Dark")


def jar(mb, x, y, r, h, body="M_MKM_Pot", glaze="M_MKM_PotGlaze", seg=10, z=0.0):
    mb.cyl(x, y, z, z + h * 0.55, r * 0.68, body, seg=seg, r_top=r)
    mb.cyl(x, y, z + h * 0.55, z + h * 0.9, r, glaze, seg=seg, r_top=r * 0.5)
    mb.cyl(x, y, z + h * 0.9, z + h, r * 0.42, glaze, seg=seg, r_top=r * 0.48)


def basket(mb, x, y, r, h, fill=None, z=0.0, mat="M_MKM_Bamboo"):
    mb.cyl(x, y, z, z + h, r * 0.82, mat, seg=10, r_top=r)
    mb.cyl(x, y, z + h - 0.01, z + h + 0.012, r * 1.04, "M_MKM_BambooDark", seg=10)
    if fill:
        mb.cyl(x, y, z + h - 0.03, z + h + 0.07, r * 0.95, fill, seg=10, r_top=r * 0.55)


def bolt(mb, x, y, z, r, length, mat):
    with mb.at(x, y, z, ry=90):
        mb.cyl(0, 0, -length / 2, length / 2, r, mat, seg=8)


def g_cloth(mb):
    """布匹：条凳上码成三层的布卷 + 后面竹架上挂一匹展开的布 + 地上竖两卷。"""
    bench(mb, 1.3, 0.62, 0.45)
    cols = ["M_MKM_ClothIndigo", "M_MKM_ClothRaw", "M_MKM_ClothBrown", "M_MKM_ClothRed", "M_MKM_ClothIndigo", "M_MKM_ClothRaw"]
    k = 0
    for layer, ys in enumerate(((-0.19, 0.0, 0.19), (-0.095, 0.095), (0.0,))):
        for y in ys:
            bolt(mb, 0, y, 0.45 + 0.09 + layer * 0.16, 0.09, 1.0, cols[k % len(cols)])
            k += 1
    for x in (-0.6, 0.6):
        mb.cyl(x, 0.5, 0.0, 1.7, 0.025, "M_MKM_Bamboo", seg=6)
    mb.cyl(-0.65, 0.5, 1.62, 1.66, 0.02, "M_MKM_Bamboo", seg=6)
    with mb.at(0, 0.5, 1.64, ry=90):
        mb.cyl(0, 0, -0.68, 0.68, 0.02, "M_MKM_Bamboo", seg=6)
    mb.box(-0.5, 0.49, 0.6, 0.5, 0.51, 1.63, "M_MKM_ClothIndigo")
    mb.box(-0.2, 0.47, 0.62, -0.1, 0.49, 1.6, "M_MKM_ClothRaw")         # 一道浅色条纹
    for x, m in ((0.85, "M_MKM_ClothBrown"), (0.95, "M_MKM_ClothRed")):
        mb.cyl(x, -0.1 + (x - 0.85) * 2.5, 0.0, 0.95, 0.09, m, seg=8)


def g_pottery(mb):
    """陶器：草席上一口大缸 + 大小坛罐 + 一摞碗。"""
    mb.box(-0.8, -0.55, 0.0, 0.8, 0.55, 0.015, "M_MKM_Mat")
    mb.cyl(-0.4, 0.15, 0.015, 0.55, 0.24, "M_MKM_Pot", seg=12, r_top=0.33)       # 缸
    mb.cyl(-0.4, 0.15, 0.55, 0.6, 0.35, "M_MKM_PotGlaze", seg=12)
    mb.cyl(-0.4, 0.15, 0.55, 0.605, 0.28, "M_Water", seg=12)
    for x, y, r, h in ((0.15, 0.25, 0.17, 0.48), (0.5, 0.2, 0.13, 0.36), (0.25, -0.2, 0.11, 0.3), (0.58, -0.22, 0.09, 0.24),
                       (-0.05, -0.3, 0.08, 0.2)):
        jar(mb, x, y, r, h, z=0.015)
    for k in range(5):                                                          # 一摞碗
        z = 0.015 + k * 0.045
        mb.cyl(-0.55, -0.3, z, z + 0.05, 0.06, "M_MKM_Radish", seg=10, r_top=0.11)


def g_bamboo(mb):
    """竹器：一摞簸箕 + 一只斜靠的簸箕、三层蒸笼、竹凳、两把扫帚、带提梁的竹篮。"""
    for k in range(4):
        z = k * 0.035
        mb.cyl(-0.45, 0.0, z, z + 0.035, 0.34 - k * 0.01, "M_MKM_Bamboo" if k % 2 else "M_MKM_BambooDark", seg=12, r_top=0.36)
    with mb.at(-0.45, 0.42, 0.0, rx=72):
        mb.cyl(0, 0.36, 0, 0.035, 0.36, "M_MKM_Bamboo", seg=12)
    for k in range(3):
        z = k * 0.13
        mb.cyl(0.25, 0.15, z, z + 0.12, 0.2, "M_MKM_Bamboo", seg=12)
    mb.cyl(0.25, 0.15, 0.39, 0.43, 0.21, "M_MKM_BambooDark", seg=12, r_top=0.08)
    mb.box(0.45, -0.45, 0.38, 0.85, -0.15, 0.42, "M_MKM_Bamboo")                # 竹凳
    for x in (0.48, 0.82):
        for y in (-0.42, -0.18):
            mb.box(x - 0.02, y - 0.02, 0.0, x + 0.02, y + 0.02, 0.38, "M_MKM_BambooDark")
    for x in (0.95, 1.05):                                                      # 扫帚（靠墙斜立）
        with mb.at(x, 0.3, 0.032, ry=-12 if x < 1 else 10):
            mb.cyl(0, 0, 0.35, 1.3, 0.015, "M_MKM_Bamboo", seg=5)
            mb.cyl(0, 0, 0.0, 0.4, 0.14, "M_MKM_BambooDark", seg=6, r_top=0.03)
    basket(mb, -0.1, -0.35, 0.16, 0.2)
    mb.box(-0.27, -0.37, 0.21, -0.25, -0.33, 0.42, "M_MKM_BambooDark")
    mb.box(0.05, -0.37, 0.21, 0.07, -0.33, 0.42, "M_MKM_BambooDark")
    mb.box(-0.27, -0.37, 0.4, 0.07, -0.33, 0.43, "M_MKM_BambooDark")


def fish(mb, x, y, z, a, s=1.0):
    with mb.at(x, y, z, rz=a):
        mb.ico(0, 0, 0.0, 0.05 * s, "M_MKM_Fish", sx=2.6, sy=0.9, sz=0.55)
        mb.prism([(0.12 * s, 0.0), (0.18 * s, 0.045 * s), (0.18 * s, -0.045 * s)], "z", -0.005, 0.005, "M_MKM_Fish")


def g_fish(mb):
    """鱼货：两只鱼篓（细颈竹篓）、一只木盆（水 + 鱼）、木架上一只浅竹匾摊着鱼。"""
    for x, y in ((-0.6, 0.2), (-0.35, 0.4)):
        mb.cyl(x, y, 0.0, 0.25, 0.15, "M_MKM_Bamboo", seg=10, r_top=0.2)
        mb.cyl(x, y, 0.25, 0.42, 0.2, "M_MKM_Bamboo", seg=10, r_top=0.08)
        mb.cyl(x, y, 0.42, 0.48, 0.08, "M_MKM_BambooDark", seg=10, r_top=0.1)
    mb.cyl(0.05, -0.1, 0.0, 0.28, 0.3, "M_Wood", seg=12, r_top=0.36)            # 木盆
    for a in range(0, 360, 30):                                                 # 盆沿（一圈箍木）
        with mb.at(0.05 + 0.345 * math.cos(math.radians(a)), -0.1 + 0.345 * math.sin(math.radians(a)), 0.0, rz=a):
            mb.box(-0.025, -0.095, 0.27, 0.025, 0.095, 0.31, "M_Wood_Dark")
    mb.cyl(0.05, -0.1, 0.28, 0.284, 0.33, "M_Water", seg=12)
    for k, a in enumerate((10, 70, 150, 230)):
        fish(mb, 0.05 + 0.15 * math.cos(math.radians(a)), -0.1 + 0.15 * math.sin(math.radians(a)), 0.3, a + 90)
    with mb.at(0.75, 0.15, 0.0):                                                # 鱼架 + 竹匾
        bench(mb, 0.8, 0.6, 0.6)
        mb.cyl(0, 0, 0.6, 0.65, 0.34, "M_MKM_Bamboo", seg=12)
        for dx, dy, a in ((-0.12, -0.05, 20), (0.02, 0.07, -10), (0.13, -0.06, 35), (-0.02, -0.15, 80), (0.15, 0.12, 120)):
            fish(mb, dx, dy, 0.67, a, 0.9)


def g_rice(mb):
    """米粮：一垛麻袋（三躺两立）+ 敞口米袋堆出米尖 + 木斗量器。"""
    for y in (-0.22, 0.22):
        with mb.at(-0.5, y, 0.2, ry=90):
            mb.cyl(0, 0, -0.35, 0.35, 0.2, "M_MKM_Sack", seg=8)
    with mb.at(-0.5, 0.0, 0.52, ry=90):
        mb.cyl(0, 0, -0.33, 0.33, 0.19, "M_MKM_Sack", seg=8)
    for x in (0.0, 0.2):
        mb.cyl(x, 0.35, 0.0, 0.55, 0.19, "M_MKM_Sack", seg=8, r_top=0.15)
        mb.cyl(x, 0.35, 0.55, 0.62, 0.06, "M_MKM_Rope", seg=6)
    mb.cyl(0.35, -0.15, 0.0, 0.42, 0.22, "M_MKM_Sack", seg=10, r_top=0.25)       # 敞口米袋
    mb.cyl(0.35, -0.15, 0.4, 0.5, 0.25, "M_MKM_Sack", seg=10, r_top=0.27)
    mb.cyl(0.35, -0.15, 0.42, 0.56, 0.24, "M_MKM_Rice", seg=10, r_top=0.03)
    mb.frustum((0.6, -0.55, 0.88, -0.27), (0.56, -0.59, 0.92, -0.23), 0.0, 0.18, "M_Wood")   # 斗
    mb.box(0.6, -0.55, 0.15, 0.88, -0.27, 0.17, "M_MKM_Rice")


def g_veg(mb):
    """菜担：扁担 + 两只菜筐（青菜 / 萝卜），地上一捆萝卜、两只南瓜、几颗白菜。"""
    basket(mb, -0.55, 0.0, 0.24, 0.28, "M_MKM_Greens")
    basket(mb, 0.55, 0.0, 0.24, 0.28, "M_MKM_Radish")
    for sx in (-1, 1):
        for a in (45, 135, 225, 315):
            x = sx * 0.55 + 0.17 * math.cos(math.radians(a))
            y = 0.17 * math.sin(math.radians(a))
            mb.box(x - 0.007, y - 0.007, 0.3, x + 0.007, y + 0.007, 0.92, "M_MKM_Rope")
    mb.box(-0.95, -0.025, 0.9, 0.95, 0.025, 0.95, "M_MKM_Bamboo")
    for k in range(5):                                                          # 一捆萝卜
        with mb.at(0.0, -0.45 + k * 0.03, 0.085, ry=90, rz=8 * k):
            mb.cyl(0, 0, -0.12, 0.1, 0.035, "M_MKM_Radish", seg=6, r_top=0.045)
            mb.cyl(0, 0, 0.1, 0.25, 0.04, "M_MKM_Greens", seg=5, r_top=0.08)
    for x, y in ((0.55, -0.5), (0.8, -0.35)):
        mb.ico(x, y, 0.11, 0.16, "M_MKM_Fruit", 1.0, 1.0, 0.7)
    for x, y in ((-0.5, -0.45), (-0.75, -0.35), (-0.3, -0.55)):
        mb.ico(x, y, 0.1, 0.12, "M_MKM_Greens", 1.0, 1.0, 0.85)


GOODS = {"Cloth": g_cloth, "Pottery": g_pottery, "Bamboo": g_bamboo, "Fish": g_fish, "Rice": g_rice, "Veg": g_veg}


def goods_prop(kind):
    mb = K.MB()
    GOODS[kind](mb)
    mb.to_object(f"PROP_MING_MarketGoods_{kind}", uv_scale=0.5)


def stall_frame(mb, aw, x0, x1, y0=-1.0, y1=1.0):
    """明代摊棚：四根木柱 + 后高前低的竹席棚（棚面单独做 NOCOL_ 到 aw 里）。"""
    for x in (x0 + 0.1, x1 - 0.1):
        mb.box(x - 0.05, y0 - 0.05, 0.0, x + 0.05, y0 + 0.05, 2.1, "M_Wood_Dark")
        mb.box(x - 0.05, y1 - 0.05, 0.0, x + 0.05, y1 + 0.05, 2.45, "M_Wood_Dark")
        mb.box(x - 0.04, y0, 2.0, x + 0.04, y1, 2.08, "M_Wood_Dark")
    aw.hexa([(x0 - 0.15, y0 - 0.45, 1.98), (x1 + 0.15, y0 - 0.45, 1.98), (x1 + 0.15, y1 + 0.15, 2.48), (x0 - 0.15, y1 + 0.15, 2.48),
             (x0 - 0.15, y0 - 0.45, 2.02), (x1 + 0.15, y0 - 0.45, 2.02), (x1 + 0.15, y1 + 0.15, 2.52), (x0 - 0.15, y1 + 0.15, 2.52)],
            "M_MKM_Awning")


def r_market_row():
    """一排三个摊位（12 × 3.6 m），正面（-Y）临街：布匹摊、陶器摊、鱼摊，摊间是米袋、菜担、竹器。"""
    mb = K.MB()
    aw = K.MB()
    for cx in (-4.0, 0.0, 4.0):
        stall_frame(mb, aw, cx - 1.5, cx + 1.5)
    with mb.at(-4.0, 0.1, 0.0):
        g_cloth(mb)
    with mb.at(0.0, 0.0, 0.0):
        g_pottery(mb)
    with mb.at(4.3, 0.1, 0.0):
        g_fish(mb)
    with mb.at(-2.0, -1.1, 0.0, rz=90):
        g_rice(mb)
    with mb.at(2.0, -1.2, 0.0, rz=-15):
        g_veg(mb)
    with mb.at(-5.6, 1.3, 0.0, rz=180):
        g_bamboo(mb)
    for x in (-3.2, 1.2, 5.0):                                                  # 摊主坐的小凳
        mb.box(x - 0.2, 0.75, 0.32, x + 0.2, 0.95, 0.36, "M_Wood")
        for dx in (-0.16, 0.16):
            mb.box(x + dx - 0.02, 0.77, 0.0, x + dx + 0.02, 0.93, 0.32, "M_Wood_Dark")
    mb.to_object("ENV_MING_MarketRow", uv_scale=0.5)
    aw.to_object("NOCOL_Awnings", uv_scale=1.0)
    for k, x in enumerate((-4.0, 0.0, 4.0), 1):
        empty(f"ANCHOR_Vendor_{k}", (x + 0.6, 0.85, 0.0))
        empty(f"ANCHOR_Buyer_{k}", (x, -1.8, 0.0))
    empty("ANCHOR_cam_top", (0, 0, 14.0))


# ====================================================================== 配方
def recipes():
    R = {}
    for kind, opens in ROAD_KINDS.items():
        R[f"ENV_MING_Road_{kind}"] = ("Environments", (lambda k=kind, o=opens: road_tile(f"ENV_MING_Road_{k}", 6.0, o)))
        R[f"ENV_MING_Road_{kind}_L4"] = ("Environments", (lambda k=kind, o=opens: road_tile(f"ENV_MING_Road_{k}_L4", 4.0, o)))
    R.update({
        "PROP_MING_Drain_Straight": ("Props", r_drain_straight),
        "PROP_MING_Drain_Covered": ("Props", r_drain_covered),
        "PROP_MING_Drain_Outfall": ("Props", r_drain_outfall),
        "BLD_MING_SlabBridge": ("Buildings", r_slab_bridge),
        "ENV_MING_DirtRoad_Straight": ("Environments", r_dirt_straight),
        "ENV_MING_DirtRoad_Bend": ("Environments", r_dirt_bend),
        "ENV_MING_DirtRoad_Ridge": ("Environments", r_ridge),
        "PROP_MING_Culvert": ("Props", r_culvert),
        "PROP_MING_MileStone": ("Props", r_milestone),
        "ENV_MING_MarketRow": ("Environments", r_market_row),
    })
    for kind in GOODS:
        R[f"PROP_MING_MarketGoods_{kind}"] = ("Props", (lambda k=kind: goods_prop(k)))
    return R
