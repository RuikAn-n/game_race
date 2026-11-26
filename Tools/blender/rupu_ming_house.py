"""
《入谱》明代 1560 民用建筑 BLD_MING_*（民居、店屋、西街店、合院、小祠、粮仓、码头、盐舍），占地与同 kind 的 ROC 一致
（Blender bpy，程序化白模；由 build_yongchang.py 统一生成/导出，recipes() 返回 {资产名: (分类, 生成函数)}）

约定（与 BLD_ROC_* 完全一致，布局不改即可互换）：
  - 原点在占地中心地面，正面（门、街面）朝 Blender -Y；台基/地面高度与同 kind 的 ROC 模型相同。
  - 整栋是一个网格（团结里整体加 MeshCollider，与 ROC 相同，不放 COL_*）；
    布幌/酒旗这类薄片单独做 NOCOL_* 子物体；ANCHOR_* 空物体标门口站位，FX_* 空物体是特效挂点。
  - 只用 era_materials.json 里已有的语义材质名（M_Roof_Tile / M_Plaster / M_Wood …），团结里按年代自动换色。
风格：浙南明代民居——白灰墙、青瓦悬山/硬山、穿斗木构外露、木格窗、石台基；无玻璃、招牌、电线。
"""
import bpy

import rupu_kit as K

MB_KU, MB_KZ = K.MB.KU, K.MB.KZ


# ====================================================================== 小工具
def plinth(mb, x0, y0, x1, y1, h=0.35, g=0.15, mat="M_Stone_Base"):
    mb.box(x0 - g, y0 - g, -0.3, x1 + g, y1 + g, h, mat)


def empty(name, loc, kind="ARROWS", size=0.4):
    o = bpy.data.objects.new(name, None)
    o.empty_display_type = kind
    o.empty_display_size = size
    o.location = loc
    bpy.context.scene.collection.objects.link(o)
    return o


def prof_z(y, y0, y1, h, rise):
    """gable_roof 微凹剖面在 y 处的高度（屋面下表面附近），用于山面木构不穿出屋面。"""
    half = (y1 - y0) / 2
    d = abs(y - (y0 + y1) / 2)
    ku = half * MB_KU
    if d >= half:
        return h
    if d >= ku:
        return h + rise * (1 - MB_KZ) * (half - d) / (half - ku)
    return h + rise * (1 - MB_KZ) + rise * MB_KZ * (ku - d) / ku


def lat_win(mb, cx, cz, w, h, yf=0.0, nv=None, nh=1):
    """木格窗（直棂/方格），面朝 -Y，贴在 y=yf 的墙面外。侧墙用 mb.at(..., rz=±90) 包一层。"""
    x0, x1, z0, z1 = cx - w / 2, cx + w / 2, cz - h / 2, cz + h / 2
    t = 0.08
    mb.box(x0, yf - 0.02, z0, x1, yf + 0.01, z1, "M_Window")
    mb.box(x0 - t, yf - 0.07, z0 - t, x1 + t, yf - 0.01, z0, "M_Wood")
    mb.box(x0 - t, yf - 0.07, z1, x1 + t, yf - 0.01, z1 + t, "M_Wood")
    mb.box(x0 - t, yf - 0.07, z0, x0, yf - 0.01, z1, "M_Wood")
    mb.box(x1, yf - 0.07, z0, x1 + t, yf - 0.01, z1, "M_Wood")
    nv = nv or max(2, int(round(w / 0.24)))
    for i in range(1, nv):
        x = x0 + w * i / nv
        mb.box(x - 0.025, yf - 0.05, z0, x + 0.025, yf - 0.02, z1, "M_Wood")
    for j in range(1, nh + 1):
        z = z0 + h * j / (nh + 1)
        mb.box(x0, yf - 0.05, z - 0.025, x1, yf - 0.02, z + 0.025, "M_Wood")


def plank_door(mb, cx, w, h, yf, z0, mat="M_Wood_Dark", frame="M_Wood", zan=True):
    """对开板门：门框 + 两扇门板（中缝）+ 门簪。面朝 -Y。"""
    mb.box(cx - w / 2 - 0.14, yf - 0.06, z0, cx + w / 2 + 0.14, yf + 0.01, z0 + h + 0.16, frame)
    mb.box(cx - w / 2, yf - 0.09, z0, cx - 0.02, yf - 0.05, z0 + h, mat)
    mb.box(cx + 0.02, yf - 0.09, z0, cx + w / 2, yf - 0.05, z0 + h, mat)
    if zan:
        for x in (cx - w / 4, cx + w / 4):
            mb.box(x - 0.08, yf - 0.2, z0 + h + 0.02, x + 0.08, yf - 0.05, z0 + h + 0.14, "M_Wood_Dark")


def geshan(mb, x0, x1, n, yf, z0, z1, skip=()):
    """槅扇门/窗一排：n 扇，上部方格心（暗底 + 木棂），下部裙板。面朝 -Y。skip 里的扇号留空（做门洞）。"""
    w = (x1 - x0) / n
    zs = z0 + (z1 - z0) * 0.42
    for i in range(n):
        a, b = x0 + i * w + 0.03, x0 + (i + 1) * w - 0.03
        if i in skip:
            mb.box(a, yf - 0.02, z0, b, yf + 0.01, z1, "M_Window")
            continue
        mb.box(a, yf - 0.04, z0, b, yf + 0.01, z1, "M_Wood")
        mb.box(a + 0.09, yf - 0.06, zs, b - 0.09, yf - 0.04, z1 - 0.12, "M_Window")
        for k in (1, 2):
            x = a + 0.09 + (b - a - 0.18) * k / 3
            mb.box(x - 0.02, yf - 0.08, zs, x + 0.02, yf - 0.05, z1 - 0.12, "M_Wood")
        for k in (1, 2, 3):
            z = zs + (z1 - 0.12 - zs) * k / 4
            mb.box(a + 0.09, yf - 0.08, z - 0.02, b - 0.09, yf - 0.05, z + 0.02, "M_Wood")
        mb.box(a + 0.12, yf - 0.06, z0 + 0.2, b - 0.12, yf - 0.04, zs - 0.15, "M_Wood_Dark")   # 裙板


def gable_frame(mb, xf, s, y0, y1, z0, h, rise, n=4, mat="M_Wood_Dark"):
    """悬山山面外露的穿斗木构：n+1 根柱子顶到屋面下 + 两道穿枋。xf 是山墙面，s=+1 朝 +X，-1 朝 -X。"""
    xa, xb = sorted((xf, xf + 0.06 * s))
    ym = (y0 + y1) / 2
    for i in range(n + 1):
        y = y0 + (y1 - y0) * i / n
        ya, yb = max(y0, y - 0.1), min(y1, y + 0.1)
        zt = prof_z(y, y0, y1, h, rise) - 0.08
        mb.box(xa, ya, z0, xb, yb, zt, mat)
    mb.box(xa, y0, h - 0.3, xb, y1, h - 0.1, mat)
    half = (y1 - y0) / 2
    zb = h + rise * (1 - MB_KZ) * 0.9
    dy = half * MB_KU * 0.95
    mb.box(xa, ym - dy, zb - 0.18, xb, ym + dy, zb, mat)
    mb.box(xa, y0, z0 + 0.9, xb, y1, z0 + 1.05, mat)


def yingshan(mb, x0, x1, y0, y1, h, rise, t=0.35, ohf=0.6, lift=0.3):
    """硬山顶：两端山墙高出屋面（白灰墙 + 黑瓦压顶），屋面夹在两山之间。"""
    for xa, xb in ((x0, x0 + t), (x1 - t, x1)):
        mb.box(xa, y0, h - 0.2, xb, y1, h + lift, "M_Plaster")
        mb.gable_fill(xa, xb, y0, y1, h + lift, rise, "M_Plaster")
        mb.gable_roof(xa, xb, y0, y1, h + lift, rise, ohf=0.12, ohs=0.08, mat="M_Roof_Ridge",
                      ridge=False, fill=False, t=0.12)
    mb.gable_roof(x0 + t, x1 - t, y0, y1, h, rise, ohf=ohf, ohs=0.0)


def xieshan(mb, x0, y0, x1, y1, ze, rise, mat_gable="M_Wood_Dark"):
    """歇山顶近似（屋脊沿 X）：四坡下檐 + 上部两坡小山面（山花板）。x0..y1 是檐口矩形。"""
    half = (y1 - y0) / 2
    ym = (y0 + y1) / 2
    inset = min(half * 1.0, (x1 - x0) / 2 - 0.5)
    mb.hip(x0, y0, x1, y1, ze, rise, inset)
    zs = ze + rise * 0.48
    ga, gb = x0 + inset * 0.55, x1 - inset * 0.55
    hy = half * 0.52
    mb.gable_fill(ga, gb, ym - hy, ym + hy, zs, rise * 0.52 + 0.05, mat_gable)
    mb.gable_roof(ga, gb, ym - hy, ym + hy, zs, rise * 0.52 + 0.05, ohf=0.15, ohs=0.25, fill=False)
    for cx, cy in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):        # 翼角起翘
        sx = 1 if cx > (x0 + x1) / 2 else -1
        sy = 1 if cy > ym else -1
        mb.prism([(cx - sx * 0.7, ze - 0.02), (cx + sx * 0.12, ze + 0.32), (cx + sx * 0.12, ze + 0.12), (cx - sx * 0.7, ze - 0.12)][::sx],
                 "y", cy - 0.12, cy + 0.12, "M_Roof_Ridge")


def tile_cap(mb, x0, x1, y0, y1, z, axis="x"):
    """院墙顶的小两坡瓦顶。"""
    if axis == "x":
        mb.gable_roof(x0, x1, y0, y1, z, 0.25, ohf=0.14, ohs=0.0, ridge=False, fill=True, t=0.08)
    else:
        mb.gable_roof_y(x0, x1, y0, y1, z, 0.25, ohf=0.14, ohs=0.0, ridge=False, fill=True, t=0.08)


def wall_x(mb, x0, x1, yc, z0, h, t=0.3, cap=True):
    mb.box(x0, yc - t / 2, z0, x1, yc + t / 2, h, "M_Plaster")
    mb.box(x0 - 0.02, yc - t / 2 - 0.02, z0, x1 + 0.02, yc + t / 2 + 0.02, z0 + 0.6, "M_Plaster_Lower")
    if cap:
        tile_cap(mb, x0, x1, yc - t / 2, yc + t / 2, h)


def wall_y(mb, y0, y1, xc, z0, h, t=0.3, cap=True):
    mb.box(xc - t / 2, y0, z0, xc + t / 2, y1, h, "M_Plaster")
    mb.box(xc - t / 2 - 0.02, y0 - 0.02, z0, xc + t / 2 + 0.02, y1 + 0.02, z0 + 0.6, "M_Plaster_Lower")
    if cap:
        tile_cap(mb, xc - t / 2, xc + t / 2, y0, y1, h, axis="y")


def step(mb, cx, w, yf, ztop, n=1, d=0.32):
    """台基前踏步（向 -Y 伸出）。"""
    for k in range(n):
        zt = ztop * (n - k) / (n + 1)
        mb.box(cx - w / 2, yf - d * (k + 1), -0.3, cx + w / 2, yf - d * k, zt, "M_Stone_Base")


def post(mb, x, y, z0, z1, r=0.11, mat="M_Wood_Dark"):
    mb.box(x - r, y - r, z0, x + r, y + r, z1, mat)


def banner(name, x, y, ztop, w=0.5, h=1.6, arm=0.9, mat="M_Flag"):
    """布幌：从墙面挑出的横杆 + 垂布（NOCOL_，团结里不加碰撞；布片可做风动 shader）。"""
    mb = K.MB()
    mb.box(x - 0.04, y - arm, ztop - 0.04, x + 0.04, y, ztop + 0.04, "M_Wood_Dark")
    mb.box(x - w / 2, y - arm + 0.2 - 0.02, ztop - 0.06 - h, x + w / 2, y - arm + 0.2 + 0.02, ztop - 0.06, mat)
    mb.box(x - w / 2 - 0.03, y - arm + 0.2 - 0.03, ztop - 0.06 - h * 0.18, x + w / 2 + 0.03, y - arm + 0.2 + 0.03,
           ztop - 0.06 - h * 0.12, "M_Cloth_Red")
    mb.to_object(name, uv_scale=1.0)


# ====================================================================== house_s 10 x 7
def r_house_s_a():
    """三开间悬山平房，前檐廊（四根檐柱），木板前檐 + 直棂窗，山面穿斗外露。10 x 7，门 x=0。"""
    mb = K.MB()
    x0, x1, y0, y1, h, z0 = -5, 5, -3.5, 3.5, 3.4, 0.35
    yw = -2.3                                   # 前檐墙（廊深 1.2）
    plinth(mb, x0, y0, x1, y1, z0)
    step(mb, 0, 2.0, y0 - 0.15, z0)
    mb.box(x0, yw, z0, x1, y1, h, "M_Plaster")
    mb.box(x0 - 0.02, yw, z0, x1 + 0.02, y1 + 0.02, z0 + 0.7, "M_Plaster_Lower")
    mb.box(x0 + 0.2, yw - 0.05, z0, x1 - 0.2, yw + 0.01, h - 0.05, "M_Wood")
    for x in (-1.6, 1.6):                       # 金柱
        post(mb, x, yw - 0.1, z0, h, 0.1)
    plank_door(mb, 0, 1.5, 2.3, yw - 0.05, z0)
    for x in (-3.3, 3.3):
        lat_win(mb, x, 1.95, 1.7, 1.0, yw - 0.05)
    for x in (-4.75, -1.6, 1.6, 4.75):          # 檐柱 + 柱础
        mb.box(x - 0.2, y0 + 0.15, z0, x + 0.2, y0 + 0.55, z0 + 0.15, "M_Stone_Base")
        post(mb, x, y0 + 0.35, z0, h)
    mb.box(x0 + 0.05, y0 + 0.24, h - 0.4, x1 - 0.05, y0 + 0.46, h - 0.1, "M_Wood_Dark")     # 檐枋
    for x in (-4.75, 4.75):                     # 廊下穿枋
        mb.box(x - 0.07, y0 + 0.35, h - 0.55, x + 0.07, yw, h - 0.4, "M_Wood_Dark")
    gable_frame(mb, x1, 1, yw, y1, z0, h, 2.0, n=3)
    gable_frame(mb, x0, -1, yw, y1, z0, h, 2.0, n=3)
    with mb.at(x1, 1.4, 0, 90):
        lat_win(mb, 0, 2.1, 0.9, 0.7, 0.0, nh=0)
    mb.gable_roof(x0, x1, y0, y1, h, 2.0, ohf=0.65, ohs=0.5)
    mb.to_object("BLD_MING_House_S_A")
    empty("ANCHOR_Door", (0, y0 - 0.6, 0))


def r_house_s_b():
    """小院平房：前院墙 + 门罩小门楼，后屋硬山、两山马头墙，白墙石勒脚。10 x 7，院门 x=-1.8。"""
    mb = K.MB()
    x0, x1, y0, y1, z0 = -5, 5, -3.5, 3.5, 0.3
    yh = -1.0                                   # 屋前檐墙；y0..yh 是小天井
    h = 3.3
    plinth(mb, x0, y0, x1, y1, z0)
    step(mb, -1.8, 1.6, y0 - 0.15, z0)
    mb.box(x0 + 0.3, y0 + 0.3, z0, x1 - 0.3, yh, z0 + 0.04, "M_Road_Stone")
    # 院墙（前 + 两侧），门洞 x=-1.8
    gx0, gx1 = -2.45, -1.15
    wall_x(mb, x0, gx0 - 0.2, y0 + 0.15, z0, 2.5)
    wall_x(mb, gx1 + 0.2, x1, y0 + 0.15, z0, 2.5)
    for xc in (x0 + 0.15, x1 - 0.15):
        wall_y(mb, y0 + 0.3, yh, xc, z0, 2.5)
    # 门楼：两垛 + 门 + 小瓦顶
    for xa in (gx0 - 0.25, gx1):
        mb.box(xa, y0 - 0.05, z0, xa + 0.25, y0 + 0.4, 2.9, "M_Plaster")
    mb.box(gx0, y0 - 0.05, 2.35, gx1, y0 + 0.4, 2.9, "M_Plaster")
    plank_door(mb, -1.8, 1.2, 2.0, y0 + 0.1, z0, zan=False)
    mb.box(gx0 - 0.1, y0 - 0.12, 2.75, gx1 + 0.1, y0 - 0.04, 2.95, "M_Wood_Dark")
    mb.gable_roof(gx0 - 0.3, gx1 + 0.3, y0 - 0.35, y0 + 0.65, 2.95, 0.55, ohf=0.3, ohs=0.2, curl=False)
    # 后屋
    mb.box(x0, yh, z0, x1, y1, h, "M_Plaster")
    mb.box(x0 - 0.03, yh - 0.03, z0, x1 + 0.03, y1 + 0.03, z0 + 0.9, "M_Stone_Base")
    mb.box(-3.0, yh - 0.05, z0, 2.5, yh + 0.01, h - 0.1, "M_Wood")
    plank_door(mb, -1.8, 1.1, 2.1, yh - 0.05, z0, zan=False)
    lat_win(mb, 0.9, 1.9, 1.6, 1.0, yh - 0.05)
    lat_win(mb, 3.6, 2.3, 0.7, 0.6, yh - 0.03, nh=0)
    mb.gable_roof(x0 + 0.4, x1 - 0.4, yh, y1, h, 1.7, ohf=0.5, ohs=0.0)
    mb.mating_wall(x0 + 0.4, yh, y1, h, 1.7, outward=1)
    mb.mating_wall(x1 - 0.4, yh, y1, h, 1.7, outward=-1)
    mb.to_object("BLD_MING_House_S_B")
    empty("ANCHOR_Door", (-1.8, y0 - 0.6, 0))


# ====================================================================== house_l 12 x 8
def r_house_l_a():
    """两层木楼：底层白墙木前檐 + 腰檐，二层木板壁 + 一长排直棂槛窗，悬山顶、山面穿斗。12 x 8，门 x=0。"""
    mb = K.MB()
    x0, x1, y0, y1, z0 = -6, 6, -4, 4, 0.35
    plinth(mb, x0, y0, x1, y1, z0)
    step(mb, 0, 2.2, y0 - 0.15, z0)
    mb.box(x0, y0, z0, x1, y1, 3.3, "M_Plaster")
    mb.box(x0 - 0.02, y0 - 0.02, z0, x1 + 0.02, y1 + 0.02, z0 + 0.7, "M_Plaster_Lower")
    mb.box(-4.6, y0 - 0.05, z0, 4.6, y0 + 0.01, 3.2, "M_Wood")
    plank_door(mb, 0, 1.7, 2.4, y0 - 0.05, z0)
    for x in (-3.0, 3.0):
        lat_win(mb, x, 1.9, 1.9, 1.1, y0 - 0.05)
    for x in (-5.85, -4.6, 4.6, 5.85):
        post(mb, x, y0 - 0.05, z0, 6.0, 0.12)
    mb.shed_roof(x0 - 0.25, x1 + 0.25, y0 + 0.1, y0 - 0.95, 3.8, 3.15)                   # 腰檐
    # 二层
    yu = y0 + 0.3
    mb.box(x0, yu, 3.3, x1, y1, 5.9, "M_Wood")
    mb.box(x0, yu - 0.12, 3.3, x1, yu, 3.55, "M_Wood_Dark")                              # 楼板枋
    for x in (-3.0, 0.0, 3.0):
        post(mb, x, yu - 0.04, 3.55, 5.9, 0.09)
    for xa, xb in ((-5.6, -3.2), (-2.8, -0.2), (0.2, 2.8), (3.2, 5.6)):
        lat_win(mb, (xa + xb) / 2, 4.85, xb - xa - 0.25, 0.9, yu, nh=0)
    gable_frame(mb, x1, 1, yu, y1, 3.3, 5.9, 2.3, n=4)
    gable_frame(mb, x0, -1, yu, y1, 3.3, 5.9, 2.3, n=4)
    gable_frame(mb, x1, 1, y0, y1, z0, 3.3, 0.01, n=4)
    gable_frame(mb, x0, -1, y0, y1, z0, 3.3, 0.01, n=4)
    mb.gable_roof(x0, x1, yu, y1, 5.9, 2.3, ohf=0.6, ohs=0.5)
    mb.to_object("BLD_MING_House_L_A")
    empty("ANCHOR_Door", (0, y0 - 0.7, 0))


def r_house_l_b():
    """曲尺形宅：后排两层硬山楼（马头墙）+ 右前单层厢屋（山面朝街）+ 左前小院（院门 x=-2.2）。12 x 8。"""
    mb = K.MB()
    x0, x1, y0, y1, z0 = -6, 6, -4, 4, 0.35
    yb = -0.6                                   # 后楼前墙
    plinth(mb, x0, y0, x1, y1, z0)
    # 后楼（两层，硬山 + 马头墙）
    hb = 5.9
    mb.box(x0, yb, z0, x1, y1, hb, "M_Plaster")
    mb.box(x0 - 0.03, yb - 0.03, z0, x1 + 0.03, y1 + 0.03, z0 + 0.9, "M_Stone_Base")
    mb.box(-5.4, yb - 0.05, z0, 1.0, yb + 0.01, 3.1, "M_Wood")
    plank_door(mb, -2.2, 1.3, 2.3, yb - 0.05, z0)
    lat_win(mb, -4.3, 1.9, 1.3, 1.0, yb - 0.05)
    lat_win(mb, -0.1, 1.9, 1.3, 1.0, yb - 0.05)
    mb.shed_roof(x0 + 0.3, 1.0, yb + 0.05, yb - 0.85, 3.6, 3.05)                       # 院内披檐
    mb.box(x0 + 0.3, yb - 0.12, 3.25, 1.0, yb, 3.4, "M_Wood_Dark")
    for x in (-3.8, -0.6, 3.5):
        lat_win(mb, x, 4.7, 1.5, 0.9, yb - 0.03, nh=0)
    mb.gable_roof(x0 + 0.4, x1 - 0.4, yb, y1, hb, 2.0, ohf=0.5, ohs=0.0)
    mb.mating_wall(x0 + 0.4, yb, y1, hb, 2.0, outward=1)
    mb.mating_wall(x1 - 0.4, yb, y1, hb, 2.0, outward=-1)
    # 右前厢屋（屋脊沿 Y，山面朝街，悬山）
    wa, wb, hw = 1.0, 6.0, 3.1
    mb.box(wa, y0, z0, wb, yb, hw, "M_Plaster")
    mb.box(wa - 0.03, y0 - 0.03, z0, wb + 0.03, yb, z0 + 0.9, "M_Stone_Base")
    mb.gable_roof_y(wa, wb, y0, yb + 0.3, hw, 1.6, ohf=0.35, ohs=0.35)
    gable_y_front = y0
    plank_door(mb, 2.2, 1.2, 2.2, gable_y_front, z0, mat="M_Wood")
    lat_win(mb, 4.6, 1.9, 1.2, 0.9, gable_y_front)
    lat_win(mb, 3.5, 3.85, 0.9, 0.45, gable_y_front, nh=0)
    for x in (wa + 0.1, wb - 0.1):              # 山面穿斗：边柱
        post(mb, x, y0 - 0.04, z0, hw, 0.09)
    mb.box(wa, y0 - 0.1, hw - 0.3, wb, y0 - 0.02, hw - 0.12, "M_Wood_Dark")
    # 左前小院：院墙 + 小门
    wall_x(mb, x0, -3.0, y0 + 0.15, z0, 2.3)
    wall_x(mb, -1.4, wa, y0 + 0.15, z0, 2.3)
    wall_y(mb, y0 + 0.3, yb, x0 + 0.15, z0, 2.3)
    for xa in (-3.2, -1.4):
        mb.box(xa, y0 - 0.02, z0, xa + 0.2, y0 + 0.32, 2.6, "M_Plaster")
    plank_door(mb, -2.2, 1.2, 1.95, y0 + 0.12, z0, zan=False)
    mb.box(-3.2, y0 - 0.02, 2.3, -1.2, y0 + 0.32, 2.6, "M_Plaster")
    mb.gable_roof(-3.45, -0.95, y0 - 0.3, y0 + 0.6, 2.6, 0.5, ohf=0.25, ohs=0.15, curl=False)
    mb.box(x0 + 0.3, y0 + 0.3, z0, wa, yb, z0 + 0.04, "M_Road_Stone")
    mb.to_object("BLD_MING_House_L_B")
    empty("ANCHOR_Door", (-2.2, y0 - 0.6, 0))
    empty("ANCHOR_Door_2", (2.2, y0 - 0.6, 0))


# ====================================================================== shop 6 x 10
def r_shop_a():
    """两层店屋：底层全开间铺面（排门板半卸、柜台），二层出挑木楼 + 长槛窗，悬山顶，挑出布幌。6 x 10。"""
    mb = K.MB()
    x0, x1, y0, y1, z0 = -3, 3, -5, 5, 0.25
    yf = y0 + 0.8                               # 铺面后退 0.8，上层挑出到 y0
    plinth(mb, x0, y0, x1, y1, z0, g=0.05)
    mb.box(x0, yf, z0, x1, y1, 3.2, "M_Plaster")
    for xa in (x0, x1 - 0.22):
        mb.box(xa, y0 + 0.1, z0, xa + 0.22, yf, 3.2, "M_Plaster")
    mb.box(x0 + 0.22, yf - 0.03, z0, x1 - 0.22, yf + 0.01, 3.0, "M_Window")              # 铺内暗面
    for i in range(5):                                                                    # 排门板（左侧装上）
        xa = x0 + 0.26 + i * 0.4
        mb.box(xa, yf - 0.12, z0, xa + 0.38, yf - 0.04, 3.0, "M_Wood")
    for i in range(4):                                                                    # 卸下的门板靠墙
        mb.box(x1 - 0.5 - i * 0.07, yf - 0.6, z0, x1 - 0.45 - i * 0.07, yf - 0.2, 2.7, "M_Wood")
    mb.box(-0.6, y0 + 0.25, z0, 2.2, y0 + 0.7, 1.0, "M_Wood_Dark")                          # 柜台
    mb.box(-0.65, y0 + 0.2, 1.0, 2.25, y0 + 0.75, 1.08, "M_Wood")
    mb.box(x0 + 0.22, yf - 0.1, 3.0, x1 - 0.22, yf, 3.2, "M_Wood_Dark")                     # 额枋
    for x in (x0 + 0.12, x1 - 0.12):                                                        # 檐柱撑起出挑
        post(mb, x, y0 + 0.12, z0, 3.25, 0.1)
    # 二层出挑
    mb.box(x0, y0 + 0.02, 3.2, x1, y1, 3.42, "M_Wood_Dark")
    mb.box(x0, y0 + 0.05, 3.42, x1, y1, 5.9, "M_Wood")
    for x in (x0 + 0.1, 0.0, x1 - 0.1):
        post(mb, x, y0 + 0.02, 3.42, 5.9, 0.08)
    lat_win(mb, -1.45, 4.65, 2.4, 1.0, y0 + 0.05)
    lat_win(mb, 1.45, 4.65, 2.4, 1.0, y0 + 0.05)
    gable_frame(mb, x1, 1, y0 + 0.05, y1, 3.42, 5.9, 2.4, n=5)
    gable_frame(mb, x0, -1, y0 + 0.05, y1, 3.42, 5.9, 2.4, n=5)
    mb.gable_roof(x0, x1, y0 + 0.05, y1, 5.9, 2.4, ohf=0.5, ohs=0.25)
    mb.to_object("BLD_MING_Shop_A")
    banner("NOCOL_Banner", 2.55, y0 + 0.05, 5.0, w=0.45, h=1.5, arm=0.75)
    empty("ANCHOR_Counter", (0.8, y0 - 0.3, 0))


def r_shop_b():
    """一层半店屋：山面朝街的悬山顶（屋脊沿进深），前出披檐两柱，排门板 + 中门，山尖阁楼小窗。6 x 10。"""
    mb = K.MB()
    x0, x1, y0, y1, z0 = -3, 3, -5, 5, 0.25
    yf = y0 + 0.8
    h = 4.0
    plinth(mb, x0, y0, x1, y1, z0, g=0.05)
    mb.box(x0, yf, z0, x1, y1, h, "M_Plaster")
    mb.box(x0 - 0.02, yf, z0, x1 + 0.02, y1 + 0.02, z0 + 0.7, "M_Plaster_Lower")
    mb.box(x0 + 0.25, yf - 0.03, z0, x1 - 0.25, yf + 0.01, 2.9, "M_Window")
    for i in range(10):                                                                     # 排门板，中间两块卸下
        if i in (4, 5):
            continue
        xa = x0 + 0.27 + i * 0.546
        mb.box(xa, yf - 0.1, z0, xa + 0.53, yf - 0.03, 2.85, "M_Wood")
    mb.box(x0 + 0.2, yf - 0.1, 2.85, x1 - 0.2, yf, 3.05, "M_Wood_Dark")
    # 前披檐 + 两檐柱
    for x in (x0 + 0.2, x1 - 0.2):
        mb.box(x - 0.18, y0 + 0.12, z0, x + 0.18, y0 + 0.48, z0 + 0.12, "M_Stone_Base")
        post(mb, x, y0 + 0.3, z0, 3.05, 0.1)
    mb.box(x0, y0 + 0.2, 2.9, x1, y0 + 0.4, 3.1, "M_Wood_Dark")
    mb.shed_roof(x0 - 0.15, x1 + 0.15, yf + 0.05, y0 - 0.2, 3.5, 2.95)
    # 山面：穿斗 + 阁楼窗
    for x in (-1.5, 0.0, 1.5):
        zt = prof_z(x, x0, x1, h, 2.3) - 0.1
        mb.box(x - 0.08, yf - 0.06, 3.5, x + 0.08, yf, zt, "M_Wood_Dark")
    mb.box(x0, yf - 0.06, 3.85, x1, yf, 4.0, "M_Wood_Dark")
    lat_win(mb, -0.75, 4.75, 0.9, 0.55, yf - 0.06, nh=0)
    lat_win(mb, 0.75, 4.75, 0.9, 0.55, yf - 0.06, nh=0)
    with mb.at(x1, 2.5, 0, 90):
        lat_win(mb, 0, 2.3, 1.0, 0.7, 0.0, nh=0)
    mb.gable_roof_y(x0, x1, yf, y1, h, 2.3, ohf=0.3, ohs=0.4)
    mb.to_object("BLD_MING_Shop_B")
    empty("ANCHOR_Door", (0, y0 - 0.4, 0))


# ====================================================================== shop_west 8 x 12（明代：两层客栈/酒楼）
def r_shop_west():
    """两层木构客栈：底层前檐廊 + 一排槅扇门，腰檐，二层木楼 + 槛窗，歇山顶（山花朝街），门前酒旗。8 x 12。"""
    mb = K.MB()
    x0, x1, y0, y1, z0 = -4, 4, -6, 6, 0.3
    yw = -5.0
    plinth(mb, x0, y0, x1, y1, z0, g=0.05)
    step(mb, 0, 2.4, y0 - 0.05, z0)
    mb.box(x0, yw, z0, x1, y1, 3.4, "M_Plaster")
    mb.box(x0 - 0.02, yw, z0, x1 + 0.02, y1 + 0.02, z0 + 0.7, "M_Plaster_Lower")
    geshan(mb, -3.7, 3.7, 8, yw, z0, 3.0, skip=(3, 4))
    mb.box(x0, yw - 0.1, 3.0, x1, yw, 3.4, "M_Wood_Dark")
    for x in (-3.8, -1.3, 1.3, 3.8):
        mb.box(x - 0.2, y0 + 0.15, z0, x + 0.2, y0 + 0.55, z0 + 0.15, "M_Stone_Base")
        post(mb, x, y0 + 0.35, z0, 3.5, 0.12)
    mb.box(x0, y0 + 0.25, 3.2, x1, y0 + 0.45, 3.45, "M_Wood_Dark")
    mb.shed_roof(x0 - 0.3, x1 + 0.3, yw + 0.1, y0 - 0.35, 3.95, 3.3)                     # 腰檐
    for xs in (x0, x1):                                                                  # 两侧腰檐（绕山面）
        s = 1 if xs > 0 else -1
        mb.shed_roof_y(yw, y1 + 0.1, xs - s * 0.05, xs + s * 0.4, 3.85, 3.55)
    # 二层
    yu = yw
    h2 = 6.5
    mb.box(x0 + 0.1, yu, 3.4, x1 - 0.1, y1 - 0.1, h2, "M_Wood")
    mb.box(x0, yu - 0.15, 3.45, x1, y1, 3.7, "M_Wood_Dark")
    for x in (-3.8, -1.3, 1.3, 3.8):
        post(mb, x, yu - 0.05, 3.7, h2, 0.1)
    for cx in (-2.55, 0.0, 2.55):
        lat_win(mb, cx, 5.0, 2.0, 1.1, yu)
    mb.railing(x0 + 0.1, x1 - 0.1, yu - 0.2, 3.7, h=0.55, post=0.9)
    for xs, s in ((x1 - 0.1, 1), (x0 + 0.1, -1)):
        for cy in (-2.0, 2.5):
            with mb.at(xs, cy, 0, 90 * s):
                lat_win(mb, 0, 5.0, 1.6, 0.9, 0.0, nh=0)
    # 歇山顶，屋脊沿 Y（山花朝街）
    with mb.at(0, 0.45, 0, 90):
        xieshan(mb, -5.95, -4.4, 5.95, 4.4, h2, 2.9)
    mb.to_object("BLD_MING_ShopWest")
    # 酒旗：门前高杆
    fl = K.MB()
    fl.box(3.95 - 0.25, y0 - 0.55, -0.3, 3.95 + 0.25, y0 - 0.05, 0.4, "M_Stone_Base")
    fl.cyl(3.95, y0 - 0.3, 0.4, 8.2, 0.07, "M_Wood_Dark", seg=6, r_top=0.05)
    fl.box(2.7, y0 - 0.33, 7.9, 3.95, y0 - 0.27, 7.96, "M_Wood_Dark")                       # 横杆沿立面
    fl.box(2.8, y0 - 0.32, 5.6, 3.85, y0 - 0.28, 7.9, "M_Flag")
    fl.box(2.75, y0 - 0.34, 7.3, 3.9, y0 - 0.26, 7.55, "M_Cloth_Red")
    fl.to_object("NOCOL_WineFlag", uv_scale=1.0)
    empty("ANCHOR_Door", (0, y0 - 0.7, 0))


# ====================================================================== courtyard 20 x 18
def r_courtyard():
    """三合院：正屋五开间（前廊、硬山高出屋面）+ 东西厢悬山 + 前院墙瓦顶门楼，院中水井、水缸。20 x 18。"""
    mb = K.MB()
    mb.box(-9.6, -8.6, -0.1, 9.6, 2.0, 0.08, "M_Road_Stone")
    # 正屋（后），面朝院（-Y）
    z0 = 0.4
    plinth(mb, -10, 2, 10, 9, z0, g=0.1)
    step(mb, 0, 3.0, 1.9, z0, n=1)
    yw = 3.3
    h = 3.9
    mb.box(-10, yw, z0, 10, 9, h, "M_Plaster")
    mb.box(-10.02, yw, z0, 10.02, 9.02, z0 + 0.8, "M_Plaster_Lower")
    geshan(mb, -1.8, 1.8, 4, yw, z0, 3.5, skip=(1, 2))
    mb.box(-9.6, yw - 0.05, z0, -1.8, yw + 0.01, 3.6, "M_Wood")
    mb.box(1.8, yw - 0.05, z0, 9.6, yw + 0.01, 3.6, "M_Wood")
    for x in (-6.8, -3.8, 3.8, 6.8):
        lat_win(mb, x, 2.25, 2.0, 1.1, yw - 0.05)
    for x in (-9.5, -5.4, -1.9, 1.9, 5.4, 9.5):
        mb.box(x - 0.2, 2.2, z0, x + 0.2, 2.6, z0 + 0.12, "M_Stone_Base")
        post(mb, x, 2.4, z0, h, 0.12)
    mb.box(-9.6, 2.28, h - 0.45, 9.6, 2.52, h - 0.1, "M_Wood_Dark")
    yingshan(mb, -10, 10, 2, 9, h, 2.4, t=0.4, ohf=0.6)
    # 两厢（屋脊沿 Y，悬山），面朝院内
    for sx in (-1, 1):
        xa, xb = (-10, -5.4) if sx < 0 else (5.4, 10)
        xf = xb if sx < 0 else xa                           # 朝院一面
        plinth(mb, xa, -6, xb, 2, 0.35, g=0.05)
        mb.box(xa, -6, 0.35, xb, 2, 3.3, "M_Plaster")
        rz = 90 if sx < 0 else -90
        L = (lambda wy: wy) if sx < 0 else (lambda wy: -wy)   # 世界 y -> 局部 x
        with mb.at(xf, 0, 0, rz):
            # 局部：正面朝 -Y（朝院），局部 x 沿世界 ±Y
            a, b = sorted((L(-5.6), L(1.6)))
            mb.box(a, -0.05, 0.35, b, 0.01, 3.2, "M_Wood")
            plank_door(mb, L(-2.0), 1.2, 2.2, -0.05, 0.35)
            lat_win(mb, L(0.0), 2.0, 1.5, 1.0, -0.05)
            lat_win(mb, L(-4.2), 2.0, 1.5, 1.0, -0.05)
        mb.gable_roof_y(xa, xb, -6, 2, 3.3, 1.7, ohf=0.5, ohs=0.3)
        gable_frame_y = -6
        for x in (xa + 0.1, (xa + xb) / 2, xb - 0.1):
            zt = prof_z(x, xa, xb, 3.3, 1.7) - 0.08
            mb.box(x - 0.09, gable_frame_y - 0.06, 0.35, x + 0.09, gable_frame_y, zt, "M_Wood_Dark")
        mb.box(xa, gable_frame_y - 0.06, 3.0, xb, gable_frame_y, 3.2, "M_Wood_Dark")
    # 院墙 + 门楼
    wall_x(mb, -10, -2.0, -8.8, -0.2, 2.9, t=0.4)
    wall_x(mb, 2.0, 10, -8.8, -0.2, 2.9, t=0.4)
    for xc in (-9.8, 9.8):
        wall_y(mb, -8.6, -6, xc, -0.2, 2.9, t=0.4)
    for xa in (-2.0, 1.5):
        mb.box(xa, -9.25, -0.2, xa + 0.5, -8.35, 3.6, "M_Plaster")
        mb.box(xa - 0.02, -9.27, -0.2, xa + 0.52, -8.33, 0.7, "M_Stone_Base")
    mb.box(-1.5, -9.2, 2.85, 1.5, -8.4, 3.6, "M_Plaster")
    mb.box(-1.6, -9.32, 3.05, 1.6, -9.2, 3.25, "M_Wood_Dark")
    mb.box(-0.6, -9.3, 2.85, 0.6, -9.2, 3.05, "M_Plaque")
    mb.box(-1.5, -9.3, -0.2, 1.5, -8.4, 0.1, "M_Stone_Base")
    plank_door(mb, 0, 1.5, 2.5, -8.75, 0.1)
    mb.gable_roof(-2.4, 2.4, -9.6, -8.0, 3.6, 0.9, ohf=0.4, ohs=0.25)
    # 院内：水井、水缸
    mb.cyl(-3.2, -3.8, 0.08, 0.75, 0.62, "M_Stone_Base", seg=8)
    mb.cyl(-3.2, -3.8, 0.4, 0.76, 0.45, "M_Water", seg=8)
    mb.box(-3.95, -3.9, 0.08, -3.75, -3.7, 1.8, "M_Wood_Dark")
    mb.box(-2.65, -3.9, 0.08, -2.45, -3.7, 1.8, "M_Wood_Dark")
    mb.box(-3.95, -3.88, 1.6, -2.45, -3.72, 1.75, "M_Wood_Dark")
    mb.cyl(3.6, -2.6, 0.08, 0.95, 0.5, "M_Brick_Red", seg=8, r_top=0.6)
    mb.cyl(3.6, -2.6, 0.95, 0.96, 0.55, "M_Water", seg=8)
    mb.to_object("BLD_MING_Courtyard")
    empty("ANCHOR_Door", (0, -10.0, 0))
    empty("ANCHOR_Yard", (0, -3.0, 0.08))
    empty("ANCHOR_MainDoor", (0, 1.4, 0.08))


# ====================================================================== hall_small 14 x 20
def r_hall_small():
    """一进祠第（明）：门厅硬山马头墙 + 红漆大门、抱鼓石、门罩匾；院内香炉；正厅歇山、红柱前廊、槅扇。14 x 20。"""
    mb = K.MB()
    x0, x1 = -7, 7
    # 门厅
    plinth(mb, x0, -10, x1, -5, 0.45)
    step(mb, 0, 2.8, -10.15, 0.45, n=1)
    mb.box(x0, -10, 0.45, x1, -5, 4.2, "M_Plaster")
    mb.box(x0 - 0.03, -10.03, 0.45, x1 + 0.03, -4.97, 1.5, "M_Stone_Base")
    plank_door(mb, 0, 2.4, 3.0, -10.03, 0.45, mat="M_Red_Lacquer", frame="M_Stone_Base")
    for x in (-1.75, 1.75):                                                               # 抱鼓石
        mb.box(x - 0.22, -10.6, 0.0, x + 0.22, -10.1, 0.95, "M_Stone_Base")
        with mb.at(x, -10.35, 1.25, 0, 0, 90):
            mb.cyl(0, 0, -0.12, 0.12, 0.32, "M_Stone_Base", seg=8)
    mb.box(-1.2, -10.16, 3.62, 1.2, -10.05, 4.1, "M_Plaque")
    mb.gable_roof(-2.3, 2.3, -10.75, -9.95, 4.25, 0.55, ohf=0.35, ohs=0.25, curl=False)              # 门罩
    for x in (-4.6, 4.6):
        lat_win(mb, x, 3.2, 0.8, 0.6, -10.03, nh=0)
    mb.gable_roof(x0 + 0.4, x1 - 0.4, -10, -5, 4.2, 1.9, ohf=0.6, ohs=0.0)
    mb.mating_wall(x0 + 0.4, -10, -5, 4.2, 1.9)
    mb.mating_wall(x1 - 0.4, -10, -5, 4.2, 1.9, outward=-1)
    # 院墙 + 院
    for xc in (x0 + 0.2, x1 - 0.2):
        wall_y(mb, -5, 2.2, xc, -0.2, 4.0, t=0.4)
    mb.box(x0 + 0.4, -5, -0.1, x1 - 0.4, 2.2, 0.1, "M_Road_Stone")
    mb.box(-0.9, -3.3, 0.1, 0.9, -0.9, 0.18, "M_Stone_Base")                                # 甬道
    mb.box(-0.6, -2.4, 0.1, 0.6, -1.2, 0.55, "M_Stone_Base")                                # 香炉
    mb.cyl(0, -1.8, 0.55, 1.15, 0.42, "M_Bronze", seg=8, r_top=0.5)
    mb.hip(-0.55, -2.35, 0.55, -1.25, 1.15, 0.35, 0.55, "M_Bronze")
    # 正厅
    plinth(mb, x0, 2.2, x1, 10, 0.65)
    step(mb, 0, 3.2, 2.05, 0.65, n=2, d=0.3)
    yw = 3.6
    mb.box(x0, yw, 0.65, x1, 10, 4.9, "M_Plaster")
    geshan(mb, -4.2, 4.2, 8, yw, 0.65, 4.2, skip=(3, 4))
    mb.box(x0 + 0.3, yw - 0.05, 0.65, -4.2, yw + 0.01, 4.6, "M_Wood")
    mb.box(4.2, yw - 0.05, 0.65, x1 - 0.3, yw + 0.01, 4.6, "M_Wood")
    mb.box(x0 + 0.3, yw - 0.1, 4.2, x1 - 0.3, yw, 4.6, "M_Wood_Dark")
    for x in (-6.4, -4.2, -1.4, 1.4, 4.2, 6.4):
        mb.cyl(x, 2.65, 0.65, 0.85, 0.27, "M_Stone_Base", seg=8)
        mb.cyl(x, 2.65, 0.85, 4.9, 0.17, "M_Red_Lacquer", seg=8)
    mb.box(x0 + 0.2, 2.5, 4.45, x1 - 0.2, 2.8, 4.85, "M_Red_Lacquer")
    mb.box(-1.3, 2.45, 3.9, 1.3, 2.55, 4.4, "M_Plaque")
    xieshan(mb, x0 - 0.4, 1.3, x1 + 0.4, 10.9, 4.9, 3.0)
    mb.to_object("BLD_MING_HallSmall")
    empty("ANCHOR_Door", (0, -10.9, 0))
    empty("ANCHOR_Censer", (0, -2.9, 0.1))
    empty("ANCHOR_Hall", (0, 4.4, 0.65))
    empty("FX_Incense", (0, -1.8, 1.2), kind="SPHERE", size=0.15)


# ====================================================================== granary 20 x 12
def r_granary():
    """官/社仓：高石台基 + 防潮孔，石勒脚白墙，外露木柱，两座板门带门罩、坡道，小方格高窗，通长气楼。20 x 12。"""
    mb = K.MB()
    x0, x1, y0, y1 = -10, 10, -6, 6
    zb, h = 0.9, 5.0
    plinth(mb, x0, y0, x1, y1, zb, g=0.2)
    for x in range(-9, 10, 2):                                                             # 台基通风孔
        if abs(abs(x) - 5) < 1.5:
            continue
        mb.box(x - 0.15, y0 - 0.24, 0.3, x + 0.15, y0 - 0.15, 0.55, "M_Window")
    mb.box(x0, y0, zb, x1, y1, h, "M_Plaster")
    mb.box(x0 - 0.04, y0 - 0.04, zb, x1 + 0.04, y1 + 0.04, 1.9, "M_Stone_Base")
    for x in range(-10, 11, 4):
        post(mb, x if abs(x) < 10 else x - 0.1 * (1 if x > 0 else -1), y0 - 0.02, 1.9, h, 0.15)
    mb.box(x0, y0 - 0.1, h - 0.35, x1, y0 + 0.02, h - 0.1, "M_Wood_Dark")
    for x in (-5, 5):
        plank_door(mb, x, 2.0, 2.6, y0 - 0.04, zb, mat="M_Wood")
        mb.prism([(y0 - 0.2, 0.9), (y0 - 1.8, -0.05), (y0 - 0.2, -0.05)], "x", x - 1.2, x + 1.2, "M_Stone_Base")
        mb.shed_roof(x - 1.6, x + 1.6, y0 + 0.05, y0 - 0.9, 4.1, 3.75)                    # 门罩
    for x in (-8, -2, 2, 8):
        lat_win(mb, x, 4.0, 0.8, 0.6, y0 - 0.04, nv=3, nh=1)
    with mb.at(0, y1, 0, 180):
        for x in (-8, -4, 0, 4, 8):
            lat_win(mb, x, 4.0, 0.8, 0.6, -0.04, nv=3, nh=1)
    gable_frame(mb, x1, 1, y0, y1, 1.9, h, 3.0, n=4)
    gable_frame(mb, x0, -1, y0, y1, 1.9, h, 3.0, n=4)
    mb.gable_roof(x0, x1, y0, y1, h, 3.0, ohf=0.8, ohs=0.45)
    # 通长气楼
    mb.box(-7.0, -0.75, 7.6, 7.0, 0.75, 8.75, "M_Wood_Dark")
    for x in range(-6, 7, 2):
        mb.box(x - 0.6, -0.8, 7.95, x + 0.6, 0.8, 8.5, "M_Window")
    mb.gable_roof(-7.0, 7.0, -0.75, 0.75, 8.75, 0.55, ohf=0.35, ohs=0.3, curl=False)
    mb.to_object("BLD_MING_Granary")
    empty("ANCHOR_Door", (-5, y0 - 2.2, 0))
    empty("ANCHOR_Door_2", (5, y0 - 2.2, 0))


# ====================================================================== dock 20 x 18
def r_dock():
    """明代埠头：条石驳岸平台 + 下水石阶 + 木栈桥，瓦顶货棚（三面板壁），系缆石、麻包、陶缸、灯笼杆。20 x 18，正面(-Y)朝海。"""
    mb = K.MB()
    zt = 0.3
    yq = -4.0                                   # 驳岸前沿
    mb.box(-10, yq, -3.0, 10, 9, zt - 0.06, "M_Bank_Stone")
    mb.box(-10, yq, zt - 0.06, 10, 9, zt, "M_Road_Stone")
    for k, z in enumerate((-2.4, -1.6, -0.8)):                                             # 条石错缝
        mb.box(-10, yq - 0.06, z, 10, yq, z + 0.12, "M_Stone_Base")
    mb.box(-10, yq - 0.1, zt - 0.2, 10, yq + 0.25, zt + 0.08, "M_Stone_Base")              # 压边石
    # 下水石阶（左前，沿岸下行）
    for k in range(7):
        z = zt - 0.35 * (k + 1)
        mb.box(-9.6, yq - 0.6 * (k + 1), -3.0, -6.4, yq - 0.6 * k, z, "M_Stone_Base")
    # 木栈桥（右前，伸到 y=-9）
    bx0, bx1 = 1.0, 5.0
    mb.box(bx0, -9.0, 0.12, bx1, yq, zt, "M_Wood")
    for y in (-8.7, -6.9, -5.1):
        for x in (bx0 + 0.2, (bx0 + bx1) / 2, bx1 - 0.2):
            mb.box(x - 0.15, y - 0.15, -3.2, x + 0.15, y + 0.15, 0.12, "M_Wood_Dark")
    mb.box(bx0, -9.0, zt, bx1, -8.85, zt + 0.12, "M_Wood_Dark")
    for x in (bx0 + 0.15, bx1 - 0.15):
        mb.box(x - 0.06, -9.0, zt, x + 0.06, yq, zt + 0.1, "M_Wood_Dark")
    # 系缆石
    for x, y in ((-5.0, yq + 0.6), (-1.0, yq + 0.6), (7.0, yq + 0.6), (bx0 + 0.4, -8.4), (bx1 - 0.4, -8.4)):
        mb.box(x - 0.2, y - 0.2, zt, x + 0.2, y + 0.2, zt + 0.55, "M_Stone_Base")
        mb.box(x - 0.26, y - 0.26, zt + 0.42, x + 0.26, y + 0.26, zt + 0.6, "M_Stone_Base")
    # 货棚：三面板壁、前敞，瓦顶悬山
    sx0, sx1, sy0, sy1, sh = -9.2, -1.6, 1.8, 8.2, 3.4
    mb.box(sx0, sy1 - 0.12, zt, sx1, sy1, sh, "M_Wood")
    for xa in (sx0, sx1 - 0.12):
        mb.box(xa, sy0, zt, xa + 0.12, sy1, sh, "M_Wood")
    for x in (sx0 + 0.06, (sx0 + sx1) / 2, sx1 - 0.06):
        mb.box(x - 0.2, sy0 - 0.2, zt, x + 0.2, sy0 + 0.2, zt + 0.12, "M_Stone_Base")
        post(mb, x, sy0, zt, sh, 0.11)
    mb.box(sx0, sy0 - 0.1, sh - 0.35, sx1, sy0 + 0.1, sh - 0.1, "M_Wood_Dark")
    mb.gable_roof(sx0, sx1, sy0, sy1, sh, 1.5, ohf=0.5, ohs=0.35)
    # 货物：麻包、木箱、陶缸
    for x, y, z in ((-7.6, 4.4, zt), (-6.6, 4.4, zt), (-7.1, 5.3, zt), (-7.1, 4.8, zt + 0.5), (-3.2, 5.6, zt),
                    (2.4, 1.2, zt), (3.3, 1.2, zt), (2.85, 1.25, zt + 0.5)):
        mb.ico(x, y, z + 0.27, 0.5, "M_Sandbag", sx=1.0, sy=0.7, sz=0.55)
    for x, y, z in ((5.6, 3.0, zt), (6.8, 3.0, zt), (6.2, 3.0, zt + 1.0), (-4.2, 3.4, zt)):
        mb.box(x - 0.55, y - 0.55, z, x + 0.55, y + 0.55, z + 1.0, "M_Wood")
    for x, y in ((8.2, 6.2), (8.9, 5.4), (8.0, 4.9)):
        mb.cyl(x, y, zt, zt + 0.85, 0.32, "M_Brick_Red", seg=8, r_top=0.26)
    # 灯笼杆（木杆 + 纸灯）
    mb.cyl(8.5, -3.2, zt, 3.8, 0.07, "M_Wood_Dark", seg=6)
    mb.box(8.5 - 0.04, -3.2, 3.6, 8.5 + 0.04, -3.9, 3.68, "M_Wood_Dark")
    mb.cyl(8.5, -3.8, 2.95, 3.55, 0.2, "M_Paper", seg=8, r_top=0.16)
    mb.to_object("BLD_MING_Dock")
    empty("ANCHOR_Jetty", (3.0, -8.2, zt))
    empty("ANCHOR_Steps", (-8.0, -7.5, zt - 0.35 * 6))
    empty("FX_Lantern", (8.5, -3.8, 3.25), kind="SPHERE", size=0.15)


# ====================================================================== salt_shed 12 x 8
def r_saltshed():
    """煎盐灶舍（明）：茅草四坡敞棚、后半截土墙，砖砌盐灶 + 铁盘（盘铁）+ 烟囱，卤缸、卤池、柴垛、盐堆。12 x 8。"""
    mb = K.MB()
    for x in (-5.7, -1.9, 1.9, 5.7):
        for y in (-3.7, 0.0, 3.7):
            if y == 0.0 and abs(x) < 3:
                continue
            mb.box(x - 0.13, y - 0.13, 0, x + 0.13, y + 0.13, 2.85, "M_Wood_Dark")
    for y in (-3.7, 3.7):
        mb.box(-5.8, y - 0.1, 2.6, 5.8, y + 0.1, 2.8, "M_Wood_Dark")
    mb.box(-5.85, 3.55, 0, 5.85, 3.85, 1.4, "M_Plaster_Lower")                              # 后土墙
    mb.box(-5.85, -0.5, 0, -5.55, 3.55, 1.4, "M_Plaster_Lower")
    mb.hip(-6.4, -4.45, 6.4, 4.45, 2.75, 2.2, 3.2, "M_Thatch")
    mb.box(-6.4, -4.45, 2.6, 6.4, -4.25, 2.78, "M_Thatch")                                    # 草檐厚度
    mb.box(-6.4, 4.25, 2.6, 6.4, 4.45, 2.78, "M_Thatch")
    mb.box(-3.3, -0.25, 4.85, 3.3, 0.25, 5.1, "M_Thatch")                                    # 草脊压条
    # 卤池（左）
    mb.box(-4.8, -2.4, 0, -1.2, 2.0, 0.6, "M_Stone_Base")
    mb.box(-4.6, -2.2, 0.35, -1.4, 1.8, 0.58, "M_Water")
    # 卤缸
    for x, y in ((-5.0, 2.8), (-4.1, 2.9), (-3.2, 2.8)):
        mb.cyl(x, y, 0, 0.9, 0.38, "M_Brick_Red", seg=8, r_top=0.42)
    # 盐灶 + 盘铁 + 烟囱
    mb.box(0.8, -1.5, 0, 4.2, 1.5, 0.95, "M_Brick_Red")
    mb.box(0.65, -1.65, 0.95, 4.35, 1.65, 1.1, "M_Metal")
    for x, y in ((1.8, -0.6), (3.0, 0.5), (2.2, 0.7)):
        mb.ico(x, y, 1.1, 0.42, "M_Salt", sx=1.0, sy=1.0, sz=0.45)
    mb.box(2.0, -1.56, 0.15, 3.0, -1.48, 0.7, "M_Window")                                    # 灶口
    mb.box(3.3, 1.5, 0, 4.1, 2.3, 5.4, "M_Brick_Red")
    mb.box(3.2, 1.4, 5.4, 4.2, 2.4, 5.55, "M_Brick_Red")
    # 柴垛、盐堆
    for k in range(4):
        mb.box(4.8, -3.3 + k * 0.05, k * 0.3, 5.6, -1.2 - k * 0.05, k * 0.3 + 0.3, "M_Wood_Dark")
    mb.ico(-0.2, -2.9, 0.28, 0.75, "M_Salt", sz=0.38)
    mb.to_object("BLD_MING_SaltShed")
    empty("FX_Fire", (2.5, -1.4, 0.4), kind="SPHERE", size=0.15)
    empty("FX_Smoke", (3.7, 1.9, 5.6), kind="SPHERE", size=0.15)
    empty("FX_Steam", (2.5, 0.0, 1.2), kind="SPHERE", size=0.15)
    empty("ANCHOR_Stove", (2.5, -2.3, 0))


def recipes():
    B = "Buildings"
    return {
        "BLD_MING_House_S_A": (B, r_house_s_a),
        "BLD_MING_House_S_B": (B, r_house_s_b),
        "BLD_MING_House_L_A": (B, r_house_l_a),
        "BLD_MING_House_L_B": (B, r_house_l_b),
        "BLD_MING_Shop_A": (B, r_shop_a),
        "BLD_MING_Shop_B": (B, r_shop_b),
        "BLD_MING_ShopWest": (B, r_shop_west),
        "BLD_MING_Courtyard": (B, r_courtyard),
        "BLD_MING_HallSmall": (B, r_hall_small),
        "BLD_MING_Granary": (B, r_granary),
        "BLD_MING_Dock": (B, r_dock),
        "BLD_MING_SaltShed": (B, r_saltshed),
    }
