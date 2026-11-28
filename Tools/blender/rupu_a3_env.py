"""
《入谱》第三幕「守城」· 战场 overlay / 场景件（Docs/第三幕_建模清单.md §3.3 / §3.4 / §4.2 / §9）
（Blender bpy，程序化白模；由 build_yongchang.py 统一生成/导出，recipes() 返回 {资产名: (分类, 生成函数)}）

约定：
  - overlay = 叠在已有明代建筑上的一层（同原点、同朝向直接摆上去）：
      ENV_A3_WallFire / ENV_A3_WallTowerDamage 对 BLD_Wall_Seg / BLD_Wall_DiTai（原点 = 墙中线地面，走道面 7.08，城外 -Y）；
      ENV_A3_GranaryDamage 对 BLD_MING_Granary（20×12，门在 x=±5 的正面 y=-6）；
      ENV_A3_BarbicanDefense / ENV_A3_BarbicanGate 对 BLD_Wall_Wengcheng（原点 = 主墙外皮中点，瓮城院 x −10..10、y −14..0，外门洞 y −18..−14）；
      其他（码头、闸室、街垒、集市、水田、祖祠、1941 谱桌、炮位）是独立的一块，原点 = 地面中心。
  - 可走面：地面/台面网格 + COL_*（只碰撞）；火线：NOCOL_FireLine_* 火苗 + TRIG_FireLine_* 盒形网格（触发体，
    团结里去掉渲染器、加 BoxCollider isTrigger）；水面 NOCOL_Water（不加碰撞）。
  - 嵌入的道具（火盆、沙袋、箭捆……）是同一套 rupu_a3_props 生成函数摆出来的，物体名加前缀 <前缀>_，挂在 <前缀> 空物体下。
  - 锚点名按清单 §9 的拼装表：ANCHOR_PlayerStart_* / ANCHOR_Cannon / ANCHOR_Ladder_1..6 ……；FX_* 特效挂点。
  - 材质前缀 M_A3E_*（颜色写在 Base Color）。
"""
import math
import random

import bpy
from mathutils import Vector

import rupu_kit as K
import rupu_act2 as A2
import rupu_a3_props as P
import rupu_a3_text as T3

K.PALETTE.update({
    "M_A3E_Char": "#2f2a25", "M_A3E_CharWood": "#3a302a", "M_A3E_Scorch": "#3a3530", "M_A3E_Soot": "#24211e",
    "M_A3E_Plank": "#6b5a46", "M_A3E_PlankOld": "#5e5244", "M_A3E_Stone": "#7a7b71", "M_A3E_StoneDark": "#5f6058",
    "M_A3E_Wet": "#4f5450", "M_A3E_WaterLine": "#3e4642", "M_A3E_Water": "#4F6B6A", "M_A3E_Mud": "#4a4436",
    "M_A3E_Brick": "#6e6e68", "M_A3E_Rubble": "#86847a", "M_A3E_BloodCloth": "#4a3128", "M_A3E_Cloth": "#8a8270",
    "M_A3E_Stubble": "#8f8a5a", "M_A3E_Paddy": "#6f8a7a", "M_A3E_Dike": "#7a7a55", "M_A3E_Ash": "#6a6660",
    "M_A3E_Grain": "#d6c48a", "M_A3E_Floor": "#8a8274", "M_A3E_Desk": "#4a3426", "M_A3E_Glass": "#8fa0a0",
    "M_A3E_Lamp": "#d8c890", "M_A3E_Ink": "#141210", "M_A3E_Iron": "#45484a", "M_A3E_Rope": "#a08a5a",
    "M_A3E_Tile": "#3f4545", "M_A3E_Lacquer": "#5a2a22", "M_A3E_Candle": "#e8e0c8", "M_A3E_Fire": "#C4552E",
    "M_A3E_Ember": "#e08040", "M_A3E_Paper": "#E8DCC8", "M_A3E_Sand": "#9b8f6e", "M_A3E_Trigger": "#c05050",
})

WALK = 7.08
obj, tb, el = A2.obj, A2.tb, A2.el
anchor, fx, group, under, col_box, rock, flame = P.anchor, P.fx, P.group, P.under, P.col_box, P.rock, P.flame


def place(fn, prefix, loc=(0, 0, 0), rz=0.0):
    """在场景里摆一件 rupu_a3_props 道具：调用生成函数，新物体名加前缀、挂到带旋转的空物体 <prefix> 下。"""
    before = set(bpy.context.scene.objects)
    fn()
    new = [o for o in bpy.context.scene.objects if o not in before]
    g = bpy.data.objects.new(prefix, None)
    g.empty_display_type = "PLAIN_AXES"
    g.empty_display_size = 0.3
    bpy.context.scene.collection.objects.link(g)
    g.location = loc
    g.rotation_euler = (0, 0, math.radians(rz))
    for o in new:
        o.name = f"{prefix}_{o.name}"
        if o.parent is None:
            o.parent = g
    return g


def trig(name, c, s, rz=0.0):
    """触发体：盒形网格 TRIG_*（中心 c、尺寸 s、绕 Z 转 rz 度）。团结里去掉渲染器，加 BoxCollider（isTrigger，取网格包围盒）。"""
    mb = K.MB()
    with mb.at(c[0], c[1], c[2], rz):
        mb.box(-s[0] / 2, -s[1] / 2, -s[2] / 2, s[0] / 2, s[1] / 2, s[2] / 2, "M_A3E_Trigger")
    return obj(mb, name, uv=1.0)


def fire_line(name, a, b, z=0.0, n=6, r=0.12, h=0.5, rng=None):
    """一条火线：沿 a→b 排一串火苗（NOCOL_FireLine_*）+ 焦黑地面条带 + 触发体 TRIG_FireLine_*。"""
    rng = rng or random.Random(1)
    a, b = Vector(a), Vector(b)
    fl = K.MB()
    sc = K.MB()
    d = (b - a)
    L = d.length
    for i in range(n):
        p = a + d * ((i + 0.5) / n)
        P.flame(fl, p.x + rng.uniform(-0.1, 0.1), p.y + rng.uniform(-0.1, 0.1), z, r * rng.uniform(0.8, 1.2), h * rng.uniform(0.7, 1.2))
    ang = math.degrees(math.atan2(d.y, d.x))
    m = (a + b) / 2
    with sc.at(m.x, m.y, z, ang):
        sc.box(-L / 2 - 0.2, -0.35, 0.0, L / 2 + 0.2, 0.35, 0.012, "M_A3E_Scorch")
    obj(fl, f"NOCOL_FireLine_{name}", uv=0.5)
    obj(sc, f"NOCOL_Scorch_{name}", uv=0.5)
    trig(f"TRIG_FireLine_{name}", (m.x, m.y, z + 0.5), (L + 0.3, 0.6, 1.0), ang)
    fx(f"FX_Fire_{name}", (m.x, m.y, z + 0.3))


def charred_plank_floor(mb, x0, x1, y0, y1, z, rng, gaps=(), t=0.06, w=0.3):
    """木板铺面（沿 X），部分板烧焦/烧断（gaps 里的 (x, y) 附近不铺）。"""
    y = y0
    k = 0
    while y < y1 - 1e-3:
        yy = min(y + w - 0.02, y1)
        segs = [(x0, x1)]
        for gx, gy, gr in gaps:
            if abs((y + yy) / 2 - gy) < gr:
                new = []
                for a, b in segs:
                    if gx - gr > a:
                        new.append((a, min(b, gx - gr * rng.uniform(0.5, 1.0))))
                    if gx + gr < b:
                        new.append((max(a, gx + gr * rng.uniform(0.5, 1.0)), b))
                segs = new
        for a, b in segs:
            mat = "M_A3E_CharWood" if rng.random() < 0.35 else ("M_A3E_PlankOld" if k % 2 else "M_A3E_Plank")
            mb.box(a, y, z - t + rng.uniform(-0.01, 0.0), b, yy, z, mat)
        y += w
        k += 1


def crate(mb, x, y, z, s, rz=0.0, mat="M_A3E_Plank", burnt=False):
    with mb.at(x, y, z, rz):
        mb.box(-s / 2, -s / 2, 0, s / 2, s / 2, s * (0.6 if burnt else 1.0), "M_A3E_CharWood" if burnt else mat)
        if not burnt:
            for zz in (0.05, s - 0.1):
                mb.box(-s / 2 - 0.01, -s / 2 - 0.01, zz, s / 2 + 0.01, s / 2 + 0.01, zz + 0.05, "M_A3E_PlankOld")


def pile(mb, x, y, z0, z1, r=0.15, mat="M_A3E_CharWood", broken=False):
    mb.cyl(x, y, z0, z1 if not broken else z1 - 0.4, r, mat, seg=7)
    if broken:
        mb.cyl(x, y, z1 - 0.4, z1 - 0.15, r, mat, seg=7, r_top=0.03)


# ====================================================================== §3.3 P0 战场 overlay
def build_burning_dock():
    """W1 东门码头烧焦段（独立一块，12×10 m）：原点 = 水面中心，码头面高 1.0 m（与 BLD_MING_Dock 驳岸台面接平时整体下移 0.7）。
    Deck 焦黑木板铺面（局部烧穿成洞，洞口 COL 另给），断桩、烧塌的货箱、半截缆桩和一盘铁链；三道火线 NOCOL_FireLine_1..3
    （触发体 TRIG_FireLine_*，不挡路）；FX_Smoke_1..3；COL_Deck 可走面（不含烧穿的洞）。
    锚点（§9 A）：ANCHOR_PlayerStart_E（+Y 岸侧）、ANCHOR_Cannon（岸侧炮位）、ANCHOR_BossLand（赤焰跳上码头的落点）、
    ANCHOR_Water（火船靠泊）、ANCHOR_Retreat（退路）。"""
    rng = random.Random(101)
    Z = 1.0
    holes = [(2.5, -2.0, 0.6), (-3.0, 1.2, 0.5)]
    mb = K.MB()
    charred_plank_floor(mb, -6, 6, -5, 5, Z, rng, gaps=holes)
    for x in (-5.5, -2.0, 2.0, 5.5):                                     # 横梁 + 桩
        mb.box(x - 0.12, -5, Z - 0.3, x + 0.12, 5, Z - 0.06, "M_A3E_CharWood")
        for y in (-4.5, -1.5, 1.5, 4.5):
            pile(mb, x, y, -1.2, Z - 0.3, 0.14)
    for x, y in ((-1.0, -5.6), (1.5, -5.8), (4.0, -5.5)):                 # 断桩（伸出码头外，水里）
        pile(mb, x, y, -1.2, Z + 0.6, 0.15, broken=True)
    obj(mb, "Deck", uv=1.0)
    cg = K.MB()                                                            # 货物：烧塌的货箱、桶、麻包
    for x, y, s, b in ((-4.6, 3.6, 0.8, False), (-3.8, 3.9, 0.7, True), (-4.4, 2.8, 0.6, True), (4.5, 3.5, 0.8, False),
                       (3.6, 3.8, 0.6, True)):
        crate(cg, x, y, Z, s, rng.uniform(-15, 15), burnt=b)
    for x, y in ((-2.0, 4.2), (-1.4, 4.4)):
        P.lathe(cg, [(0.22, Z), (0.26, Z + 0.35), (0.22, Z + 0.7)], "M_A3E_CharWood", seg=10, x=x, y=y)
    for x, y in ((1.0, 4.3), (1.6, 4.1), (1.3, 4.5)):
        el(cg, (x, y, Z + 0.15), 0.35, 0.22, 0.15, "M_A3E_Sand", seg=8, rings=3)
    obj(cg, "Cargo", uv=0.5)
    ch = K.MB()                                                            # 缆桩 + 一盘铁链 + 拖到水里的一段
    ch.cyl(-5.2, -4.4, Z, Z + 0.55, 0.16, "M_A3E_Stone", seg=8)
    for k in range(3):
        for i in range(10):
            a = 2 * math.pi * i / 10
            ch.box(-4.4 + 0.3 * math.cos(a) - 0.04, -4.2 + 0.3 * math.sin(a) - 0.02, Z + k * 0.04, -4.4 + 0.3 * math.cos(a) + 0.04,
                   -4.2 + 0.3 * math.sin(a) + 0.02, Z + k * 0.04 + 0.04, "M_A3E_Iron")
    for i in range(8):
        ch.box(-4.1 - 0.02, -4.5 - i * 0.12, Z - i * 0.15, -4.1 + 0.02, -4.4 - i * 0.12, Z - i * 0.15 + 0.04, "M_A3E_Iron")
    obj(ch, "Chain", uv=0.5)
    for k, (a, b) in enumerate((((-5, -3.5), (-1, -3.0)), ((0.5, -0.5), (4.5, 0.6)), ((-2.5, 2.4), (0.5, 3.0)))):
        fire_line(str(k + 1), a, b, Z, rng=rng)
    for k, (x, y) in enumerate(((-3.5, -3.6), (3.0, 0.0), (-4.0, 3.5))):
        fx(f"FX_Smoke_{k + 1}", (x, y, Z + 0.8))
    deck = K.MB()
    deck.box(-6, -5, Z - 0.06, 6, 5, Z, "M_A3E_Plank")
    obj(deck, "COL_Deck", uv=1.0)
    for k, (x, y, r) in enumerate(holes):
        P.col_box(f"COL_Hole_{k + 1}", (x, y, Z + 0.5), (2 * r, 2 * r, 1.0))           # 烧穿的洞：拦住不让掉下去
    anchor("ANCHOR_PlayerStart_E", (0, 4.4, Z))
    anchor("ANCHOR_Cannon", (4.4, 2.0, Z))
    anchor("ANCHOR_BossLand", (0.0, -3.0, Z))
    anchor("ANCHOR_Water", (0.0, -7.5, 0.0))
    anchor("ANCHOR_Retreat", (-5.0, 5.5, Z))


def build_water_gate_interior():
    """W2/W4 东水门闸室（独立一块，原点 = 渠底中心）：两侧石壁（10 m 长、5 m 高，渠宽 4.4 m）带闸槽（y=0）和湿痕水位线，
    渠底 0、水面 NOCOL_Water 在 0.9（到腰）；右侧（+X）一条 1.2 m 宽石台走道（高 1.5）+ 湿台阶下到渠底；
    Grille 铁栅（在闸槽上游 y=+3 的另一道槽里，原点在栅底，沿 +Z 升 2.5 m 打开）；两只壁上火把 FX_Torch_1/2；
    COL_Wall_L/R、COL_Ledge。锚点（§9 B）：ANCHOR_Sluice_Spot_1..3（放石条的三个位置，沿闸槽）、ANCHOR_Winch（走道上绞盘）、
    ANCHOR_Latch（闸栓）、ANCHOR_Boat（小船停靠）、ANCHOR_PlayerStart_W。"""
    rng = random.Random(102)
    Wc, L, H = 4.4, 10.0, 5.0
    mb = K.MB()
    xr = Wc / 2 + 1.2                                                                         # 右墙内皮（走道台外侧）
    for xa, xb, face in ((-Wc / 2 - 1.0, -Wc / 2, -Wc / 2), (xr, xr + 1.0, xr)):
        mb.box(xa, -L / 2, -0.3, xb, L / 2, H, "M_A3E_Stone")
        for z in range(1, 10):                                                            # 条石横缝
            mb.box(face - 0.006, -L / 2, z * 0.5, face + 0.006, L / 2, z * 0.5 + 0.02, "M_A3E_StoneDark")
    mb.box(Wc / 2, -L / 2, -0.3, xr, L / 2, 1.5, "M_A3E_Stone")                                # 走道台
    mb.box(-Wc / 2, -L / 2, -0.3, Wc / 2, L / 2, 0.0, "M_A3E_StoneDark")                       # 渠底
    for i in range(5):                                                                        # 台阶（-Y 端，从走道台下到渠底）
        mb.box(Wc / 2 - 0.3 * (i + 1), -L / 2, 0, Wc / 2 - 0.3 * i, -L / 2 + 1.2, 1.5 - 0.3 * (i + 1), "M_A3E_Wet")
    for y in (0.0, 3.0):                                                                      # 两道闸槽（竖槽：贴两壁的突起）
        mb.box(-Wc / 2, y - 0.15, 0, -Wc / 2 + 0.12, y + 0.15, H, "M_A3E_StoneDark")
        mb.box(Wc / 2 - 0.12, y - 0.15, 0, Wc / 2, y + 0.15, H, "M_A3E_StoneDark")
    mb.box(-Wc / 2 - 0.3, -0.25, H, Wc / 2 + 1.5, 0.25, H + 0.4, "M_A3E_StoneDark")             # 闸楣
    obj(mb, "Chamber", uv=1.0)
    wl = K.MB()                                                                               # 湿痕 / 水位线（贴墙薄片）
    for sx in (-1, 1):
        x = sx * (Wc / 2 - 0.005)
        wl.box(x - 0.004, -L / 2, 0.0, x + 0.004, L / 2, 1.4, "M_A3E_Wet")
        wl.box(x - 0.006, -L / 2, 1.38, x + 0.006, L / 2, 1.43, "M_A3E_WaterLine")
    obj(wl, "NOCOL_WetMarks", uv=1.0)
    w = K.MB()
    w.box(-Wc / 2, -L / 2, 0.88, Wc / 2, L / 2, 0.9, "M_A3E_Water")
    obj(w, "NOCOL_Water", uv=2.0)
    gr = K.MB()                                                                               # 铁栅
    for i in range(9):
        x = -Wc / 2 + 0.1 + i * (Wc - 0.2) / 8
        gr.box(x - 0.03, -0.03, 0, x + 0.03, 0.03, 3.2, "M_A3E_Iron")
        gr.cyl(x, 0, -0.15, 0.0, 0.03, "M_A3E_Iron", seg=4, r_top=0.005)
    for z in (0.6, 1.6, 2.6, 3.1):
        gr.box(-Wc / 2 + 0.05, -0.04, z, Wc / 2 - 0.05, 0.04, z + 0.08, "M_A3E_Iron")
    obj(gr, "Grille", (0, 3.0, 0), uv=0.5)
    anchor("ANCHOR_Grille_Open", (0, 3.0, 2.5), 0.2)
    for k, y in enumerate((-2.5, 2.0)):
        tm = K.MB()
        tm.box(-0.04, -0.04, -0.1, 0.04, 0.04, 0.1, "M_A3E_Iron")
        tb(tm, (0, 0, 0), (0.25, 0, 0.15), 0.012, "M_A3E_Iron", seg=4)
        tm.cyl(0.25, 0, 0.12, 0.35, 0.035, "M_A3E_Cloth", seg=6)
        P.flame(tm, 0.25, 0, 0.35, 0.04, 0.22)
        obj(tm, f"Torch_{k + 1}", (-Wc / 2, y, 3.0), uv=0.3)
        fx(f"FX_Torch_{k + 1}", (-Wc / 2 + 0.25, y, 3.45))
    P.col_box("COL_Wall_L", (-Wc / 2 - 0.5, 0, H / 2), (1.0, L, H))
    P.col_box("COL_Wall_R", (Wc / 2 + 1.7, 0, H / 2), (1.0, L, H))
    P.col_box("COL_Ledge", (Wc / 2 + 0.6, 0, 0.75), (1.2, L, 1.5))
    for k in range(3):
        anchor(f"ANCHOR_Sluice_Spot_{k + 1}", (-1.4 + k * 1.4, -0.5, 0.0))
    anchor("ANCHOR_Winch", (Wc / 2 + 0.6, 0.6, 1.5))
    anchor("ANCHOR_Latch", (Wc / 2 + 0.6, -0.6, 1.5))
    anchor("ANCHOR_Boat", (-0.8, -3.0, 0.9))
    anchor("ANCHOR_PlayerStart_W", (Wc / 2 + 0.6, -4.2, 1.5))


def build_north_gate_barricade():
    """W3/W7 北门 / 通市街街垒（独立一块 14×10 m，原点 = 门洞内侧路面中心，门在 -Y）：翻倒的摊子、板车、沙袋垛、箭捆、
    破旗，留出中间 4.4 m 宽的通道（门洞净宽）；掩体都有 COL_。锚点（§9 C）：ANCHOR_Cover_1..4、ANCHOR_Flag、
    ANCHOR_Ladder_1..6（云梯搭墙位置，按 BLD_Wall_Seg 局部 (x, −5.25, 0) 换算到本块：门两侧城墙外）、ANCHOR_Ram（冲车停门洞外）、
    ANCHOR_GateInside、ANCHOR_PlayerStart_N。"""
    rng = random.Random(103)
    place(lambda: P.build_barricade(), "Barricades", (-6.2, -1.0, 0), 0)                       # 4 模块：x −6.2..1.3
    mb = K.MB()
    with mb.at(4.2, -0.6, 0, 15):                                                             # 翻倒的货摊：桌面立起、棚架倒地
        mb.box(-1.0, -0.05, 0, 1.0, 0.05, 0.9, "M_A3E_PlankOld")
        for x in (-0.9, 0.9):
            tb(mb, (x, 0.05, 0.85), (x, 0.8, 0.85), 0.04, "M_A3E_Plank", seg=5)
        tb(mb, (-1.0, 0.4, 0.05), (1.2, 1.6, 0.2), 0.035, "M_A3E_Plank", seg=5)
        mb.box(-1.2, 1.0, 0.0, 1.1, 2.2, 0.05, "M_A3E_Cloth")
    obj(mb, "Stall", uv=0.5)
    P.col_box("COL_Stall", (4.2, -0.6, 0.45), (2.1, 0.4, 0.9))
    place(P.build_sandbag, "Sandbags", (3.2, 2.5, 0), -10)
    place(P.build_arrow_bundle, "Arrows", (5.8, 2.0, 0), 30)
    fl = K.MB()                                                                               # 破旗：斜倒的旗杆 + 撕破的旗面
    tb(fl, (6.0, 0.5, 0), (4.6, 3.2, 2.0), 0.03, "M_A3E_Plank", seg=6)
    obj(fl, "Flag_Pole", uv=0.5)
    m = K.get_mat("M_A3P_FlagRed")
    f, b = T3.wavy_cloth("NOCOL_Flag_Torn", 0.0, 0.8, -0.6, 0.0, m, nx=5, nz=3, amp=0.08)
    for o in (f, b):
        o.location = (4.6, 3.2, 2.0)
        o.rotation_euler = (0, math.radians(20), math.radians(110))
    anchor("ANCHOR_Flag", (4.6, 3.4, 0))
    for k, (x, y) in enumerate(((-6.2, -0.2), (-3.7, -0.2), (-1.2, -0.2), (4.2, 0.2))):
        anchor(f"ANCHOR_Cover_{k + 1}", (x, y + 0.4, 0))
    for k in range(6):
        sx = -1 if k < 3 else 1
        anchor(f"ANCHOR_Ladder_{k + 1}", (sx * (6.0 + (k % 3) * 4.0), -5.25 - 4.0, 0))
    anchor("ANCHOR_Ram", (0, -9.5, 0))
    anchor("ANCHOR_GateInside", (0, -3.0, 0))
    anchor("ANCHOR_PlayerStart_N", (0, 4.5, 0))


def build_wall_fire():
    """W4/W7 东墙火段 overlay（两段 BLD_Wall_Seg 长 16 m，x −8..8；原点 = 墙中线地面，同墙段）：
    走道上焦痕、两处被打碎的垛口（BrokenMerlon_1/2：碎块堆在走道上，原垛口用 MerlonCap 盖住断面）、外墙面烟熏痕、
    三道火线（走道上，NOCOL + TRIG）、两只火盆 + 两只火篮。锚点：ANCHOR_Fire_1..3（灭火点，离火 ≤2.5 m）、ANCHOR_WaterWheel
    （城内墙根水车位）、ANCHOR_Breach（破口位，换 ENV_WallBreach）、ANCHOR_PlayerStart_D。"""
    rng = random.Random(104)
    sc = K.MB()
    for x, w in ((-5.5, 2.2), (-0.5, 3.0), (4.5, 2.0)):
        sc.box(x - w / 2, -1.4, WALK, x + w / 2, 1.2, WALK + 0.01, "M_A3E_Scorch")
    for x in (-5.0, 3.0):                                                                     # 外墙面烟熏（-Y 面）
        sc.prism([(-2.2, 5.0), (-2.08, 5.0), (-2.06, 8.6), (-2.18, 8.6)], "x", x - 1.2, x + 1.2, "M_A3E_Soot")
    obj(sc, "NOCOL_Scorch", uv=1.0)
    for k, x in enumerate((-3.0, 2.0)):
        rb = K.MB()
        for i in range(7):
            rock(rb, x + rng.uniform(-0.8, 0.8), rng.uniform(-1.3, -0.5), WALK, rng.uniform(0.12, 0.22), rng, "M_A3E_Rubble")
        rb.box(x - 0.65, -2.1, 7.95, x + 0.65, -1.5, 8.1, "M_A3E_StoneDark")                     # 断口压顶（盖住缺垛）
        obj(rb, f"BrokenMerlon_{k + 1}", uv=0.5)
        P.col_box(f"COL_Rubble_{k + 1}", (x, -0.9, WALK + 0.2), (1.6, 0.8, 0.4))
    for k, (a, b) in enumerate((((-7, 0.2), (-4.5, -0.4)), ((-1.5, 0.6), (0.8, 0.0)), ((3.5, -0.6), (6.0, 0.3)))):
        fire_line(str(k + 1), a, b, WALK, n=5, rng=rng)
        anchor(f"ANCHOR_Fire_{k + 1}", ((a[0] + b[0]) / 2, 1.6, WALK))
    place(P.build_brazier, "Brazier_1", (-6.5, 1.8, WALK))
    place(P.build_brazier, "Brazier_2", (5.5, 1.8, WALK))
    place(P.build_fire_basket, "FireBasket_1", (-1.0, 2.4, WALK), 180)
    place(P.build_fire_basket, "FireBasket_2", (7.0, 2.4, WALK), 180)
    anchor("ANCHOR_WaterWheel", (0, 6.0, 0))
    anchor("ANCHOR_Breach", (-4.0, 0, 0))
    anchor("ANCHOR_PlayerStart_D", (7.5, 0.5, WALK))


def build_granary_damage():
    """W6 粮仓破损 overlay（叠 BLD_MING_Granary 20×12，同原点）：东门（x=+5）门扇被撞破——DoorFrame_Broken 盖住原门框、
    Door_Leaf_L 倒在坡道上、Door_Leaf_R 斜挂；正面右半屋檐塌下一角 Eave_Collapse（瓦片 + 断椽堆在台基前，不挡门）；
    门口到台基下散了一地米 NOCOL_Grain、泥脚印 NOCOL_Footprints；门里冒火 NOCOL_Fire + FX_Fire / FX_Smoke。
    锚点（§9 F）：ANCHOR_GranaryDoor（门口）、ANCHOR_Grain_1..3（抢粮点）、ANCHOR_Scale（秤）、ANCHOR_Distribute（分粮站位）。"""
    rng = random.Random(105)
    zb = 0.9
    dx = 5.0
    yf = -6.0
    mb = K.MB()
    mb.box(dx - 1.1, yf - 0.06, zb, dx - 0.95, yf + 0.06, zb + 2.6, "M_A3E_CharWood")              # 门框（左边焦黑）
    mb.box(dx + 0.95, yf - 0.06, zb, dx + 1.1, yf + 0.06, zb + 2.3, "M_A3E_Plank")
    with mb.at(dx + 1.1, yf, zb + 2.3, 0, -12, 0):
        mb.box(-0.15, -0.06, 0, 0.0, 0.06, 0.5, "M_A3E_Plank")
    mb.box(dx - 1.1, yf - 0.08, zb + 2.55, dx + 1.2, yf + 0.08, zb + 2.7, "M_A3E_CharWood")
    obj(mb, "DoorFrame_Broken", uv=0.5)
    lf = K.MB()
    lf.box(-0.95, 0, 0, 0.0, 0.08, 2.4, "M_A3E_PlankOld")
    lf.box(-0.9, -0.02, 0.4, -0.05, 0.0, 0.5, "M_A3E_Iron")
    o = obj(lf, "Door_Leaf_L", (dx - 0.1, yf - 0.6, zb - 0.45), uv=0.5)
    o.rotation_euler = (math.radians(-82), 0, math.radians(8))
    rf = K.MB()
    rf.box(0, 0, 0, 0.95, 0.08, 2.4, "M_A3E_PlankOld")
    o = obj(rf, "Door_Leaf_R", (dx + 0.95, yf - 0.05, zb + 0.05), uv=0.5)
    o.rotation_euler = (0, math.radians(-8), math.radians(60))
    ev = K.MB()                                                                                 # 塌檐：断椽 + 碎瓦堆
    for i in range(6):
        x = 6.8 + i * 0.4
        tb(ev, (x, yf - 0.2, zb + 0.1), (x + rng.uniform(-0.3, 0.3), yf - 2.0, 0.05), 0.05, "M_A3E_CharWood", seg=5)
    for i in range(14):
        with ev.at(6.6 + rng.uniform(0, 2.8), yf - 0.9 - rng.uniform(0, 1.5), 0.0, rng.uniform(0, 180), rng.uniform(-15, 15)):
            ev.box(-0.2, -0.12, 0, 0.2, 0.12, 0.04, "M_A3E_Tile")
    obj(ev, "Eave_Collapse", uv=0.5)
    P.col_box("COL_Eave", (8.0, yf - 1.6, 0.3), (3.0, 1.6, 0.6))
    gr = K.MB()
    for i in range(10):
        el(gr, (dx + rng.uniform(-1.2, 1.4), yf - 0.4 - rng.uniform(0, 3.0), 0.0 if i > 3 else zb - 0.4),
           rng.uniform(0.15, 0.45), rng.uniform(0.1, 0.3), 0.03, "M_A3E_Grain", seg=7, rings=2, zmin=0.0)
    obj(gr, "NOCOL_Grain", uv=0.5)
    fp = K.MB()
    for i in range(14):
        with fp.at(dx + rng.uniform(-2, 2), yf - 1.0 - i * 0.4, 0.005, rng.uniform(-30, 30)):
            fp.box(-0.05, -0.12, 0, 0.05, 0.12, 0.004, "M_A3E_Mud")
    obj(fp, "NOCOL_Footprints", uv=0.5)
    fl = K.MB()
    for x in (4.4, 5.2, 5.8):
        P.flame(fl, x, yf + 0.8, zb, 0.25, 1.0)
    obj(fl, "NOCOL_Fire", uv=0.5)
    fx("FX_Fire", (dx, yf + 0.8, zb + 0.6))
    fx("FX_Smoke", (dx, yf + 0.5, zb + 2.8))
    anchor("ANCHOR_GranaryDoor", (dx, yf - 1.8, 0))
    for k, (x, y) in enumerate(((-5.0, -7.5), (0.0, -8.0), (3.5, -8.5))):
        anchor(f"ANCHOR_Grain_{k + 1}", (x, y, 0))
    anchor("ANCHOR_Scale", (-2.0, -9.5, 0))
    anchor("ANCHOR_Distribute", (-2.0, -10.4, 0))
    for k, x in enumerate((-8.0, 8.0)):
        anchor(f"ANCHOR_PaddyGate_{k + 1}", (x, 9.0, 0))


def build_barbican_defense():
    """W8 瓮城防守 overlay（叠 BLD_Wall_Wengcheng，同原点；院子 x −10..10、y −14..0）：东西两侧墙头各两堆擂石（走道 7.08），
    院里沿两侧墙根的拒马 / 沙袋（中间 8 m 圆内留空 = Boss 战场），外门洞内侧一副临时木闸 Gate_Temp（原点在闸底，沿 +Z 升起打开），
    主墙门洞上方挂一口警钟（PROP_A3_Bell），院墙内面一道射孔木板墙（ArrowSlits）、地上几块暗色血布。
    锚点（§9 H）：ANCHOR_RockDrop_1..4、ANCHOR_BarbicanGate、ANCHOR_Flag、ANCHOR_PlayerStart_H、ANCHOR_Escape、ANCHOR_ArenaCenter。"""
    rng = random.Random(106)
    for k, (x, y) in enumerate(((-12.0, -5.0), (-12.0, -11.0), (12.0, -5.0), (12.0, -11.0))):
        place(P.build_rock_pile, f"RockPile_{k + 1}", (x, y, WALK), 90 if x < 0 else -90)
        anchor(f"ANCHOR_RockDrop_{k + 1}", (x + (1.8 if x < 0 else -1.8), y, 0))
    place(P.build_sandbag, "Sandbags_W", (-8.8, -2.5, 0), 90)
    place(P.build_sandbag, "Sandbags_E", (8.8, -2.5, 0), -90)
    gt = K.MB()                                                                               # 临时木闸
    for i in range(8):
        x = -2.1 + i * 0.6
        gt.box(x, -0.08, 0, x + 0.5, 0.08, 4.6, "M_A3E_PlankOld")
    for z in (0.6, 2.3, 4.0):
        gt.box(-2.2, -0.14, z, 2.2, -0.08, z + 0.2, "M_A3E_Iron")
    obj(gt, "Gate_Temp", (0, -13.8, 0), uv=0.5)
    anchor("ANCHOR_Gate_Open", (0, -13.8, 4.0), 0.2)
    P.col_box("COL_Gate_Temp", (0, -13.8, 2.3), (4.4, 0.3, 4.6))
    place(P.build_bell, "Bell", (6.0, -0.6, 0), 0)
    sl = K.MB()                                                                               # 射孔木板墙（西墙内面）
    sl.box(-9.95, -12.5, 0, -9.75, -3.5, 2.2, "M_A3E_Plank")
    for i in range(5):
        y = -11.5 + i * 2.0
        sl.box(-9.76, y - 0.08, 1.3, -9.74, y + 0.08, 1.7, "M_A3E_Soot")
    obj(sl, "ArrowSlits", uv=0.5)
    bc = K.MB()
    for i in range(4):
        with bc.at(rng.uniform(-6, 6), rng.uniform(-12, -3), 0.004, rng.uniform(0, 180)):
            bc.box(-0.4, -0.25, 0, 0.4, 0.25, 0.006, "M_A3E_BloodCloth")
    obj(bc, "NOCOL_BloodCloth", uv=0.5)
    anchor("ANCHOR_BarbicanGate", (0, -12.6, 0))
    anchor("ANCHOR_Flag", (-6.0, -1.0, 0))
    anchor("ANCHOR_ArenaCenter", (0, -7.0, 0))
    anchor("ANCHOR_PlayerStart_H", (0, -1.5, 0))
    anchor("ANCHOR_Escape", (-9.0, -0.8, 0))


def build_battle_debris():
    """战场残骸一块（8×8 m，随处叠放）：断箭、破盾、头盔、石块、断枪杆、暗色血布（不血腥）。全部 NOCOL_（不挡路），
    只有两块大石头带 COL_。原点 = 中心地面。"""
    rng = random.Random(107)
    place(P.build_arrow_stuck, "Arrows_1", (-2.0, 1.5, 0), 20)
    place(P.build_arrow_stuck, "Arrows_2", (1.5, -2.0, 0), -70)
    place(P.build_shield_broken, "Shields", (-2.5, -2.5, 0), 35)
    place(P.build_helmet, "Helmets", (0.5, 2.5, 0), -20)
    rk = K.MB()
    for i in range(6):
        rock(rk, rng.uniform(-3.5, 3.5), rng.uniform(-3.5, 3.5), 0, rng.uniform(0.08, 0.16), rng, "M_A3E_Rubble")
    obj(rk, "NOCOL_Stones", uv=0.5)
    bg = K.MB()
    for k, (x, y) in enumerate(((3.0, 2.8), (-3.2, 0.2))):
        rock(bg, x, y, 0, 0.35, rng, "M_A3E_Stone")
        P.col_box(f"COL_Rock_{k + 1}", (x, y, 0.25), (0.8, 0.7, 0.5))
    obj(bg, "Rocks", uv=0.5)
    sp = K.MB()
    tb(sp, (-0.5, 0.3, 0.02), (1.1, -0.1, 0.02), 0.016, "M_A3P_Wood", seg=5)
    tb(sp, (1.25, -0.15, 0.02), (1.8, -0.3, 0.02), 0.016, "M_A3P_Wood", seg=5)
    sp.prism([(1.8, -0.33), (1.8, -0.27), (2.05, -0.33)], "z", 0.01, 0.02, "M_A3P_Iron")
    obj(sp, "NOCOL_BrokenSpear", uv=0.5)
    bc = K.MB()
    for i in range(3):
        with bc.at(rng.uniform(-3, 3), rng.uniform(-3, 3), 0.004, rng.uniform(0, 180)):
            bc.box(-0.3, -0.2, 0, 0.3, 0.2, 0.006, "M_A3E_BloodCloth")
    obj(bc, "NOCOL_BloodCloth", uv=0.5)


# ====================================================================== §4.2 P1 场景件
def build_wall_tower_damage():
    """敌台/炮位破损 overlay（叠 BLD_Wall_DiTai，同原点）：前垛墙炸掉一个口（Breach_Front：碎石堆 + 压顶断口），
    炮位垫石边一圈焦痕、断掉的炮车轮和木板、散落砖块；COL_Rubble。不挡炮线：碎石堆在左前角。"""
    rng = random.Random(108)
    mb = K.MB()
    for i in range(10):
        rock(mb, rng.uniform(-3.4, -1.6), rng.uniform(-7.6, -6.4), WALK, rng.uniform(0.12, 0.25), rng, "M_A3E_Rubble")
    mb.box(-3.0, -8.25, 7.95, -1.6, -7.55, 8.1, "M_A3E_StoneDark")
    obj(mb, "Breach_Front", uv=0.5)
    P.col_box("COL_Rubble", (-2.5, -7.0, WALK + 0.25), (1.8, 1.2, 0.5))
    sc = K.MB()
    sc.box(-1.6, -7.8, WALK, 1.6, -5.2, WALK + 0.01, "M_A3E_Scorch")
    obj(sc, "NOCOL_Scorch", uv=0.5)
    db = K.MB()
    with db.at(2.0, -4.0, WALK + 0.06, 30, 0, 80):
        A2.wheel(db, 0.35, 0.07, "M_A3E_CharWood", "M_A3E_Iron", spokes=6, seg=10)
    for i in range(4):
        with db.at(rng.uniform(0.5, 3), rng.uniform(-6, -3), WALK, rng.uniform(0, 180)):
            db.box(-0.6, -0.1, 0, 0.6, 0.1, 0.04, "M_A3E_CharWood")
    for i in range(10):
        with db.at(rng.uniform(-3, 3), rng.uniform(-7.5, -2.5), WALK, rng.uniform(0, 180)):
            db.box(-0.12, -0.06, 0, 0.12, 0.06, 0.06, "M_A3E_Brick")
    obj(db, "NOCOL_Debris", uv=0.5)


def build_flooded_street():
    """积水街道（16×6 m，原点 = 路面中心）：浅水面 NOCOL_Water（5 cm，不没脚）、水里漂的木板/篮子、半淹的箱子、
    路边被冲倒的水缸。只有箱子带 COL_。W2/W7。"""
    rng = random.Random(109)
    w = K.MB()
    w.box(-8, -2.8, 0.0, 8, 2.8, 0.05, "M_A3E_Water")
    obj(w, "NOCOL_Water", uv=2.0)
    fl = K.MB()
    for i in range(5):
        with fl.at(rng.uniform(-7, 7), rng.uniform(-2.2, 2.2), 0.05, rng.uniform(0, 180)):
            fl.box(-0.5, -0.1, 0, 0.5, 0.1, 0.03, "M_A3E_Plank")
    P.lathe(fl, [(0.15, 0.04), (0.22, 0.2)], "M_A3P_Bamboo", seg=8, x=2.5, y=1.2)
    obj(fl, "NOCOL_Floating", uv=0.5)
    cr = K.MB()
    crate(cr, -3.0, 2.0, 0.0, 0.7, 20)
    crate(cr, -2.3, 2.3, 0.0, 0.5, -10)
    with cr.at(5.5, -2.2, 0.25, 0, 80, 20):
        P.lathe(cr, [(0.2, -0.3), (0.3, 0.0), (0.22, 0.3)], "M_A3P_Clay", seg=10)
    obj(cr, "Crates", uv=0.5)
    P.col_box("COL_Crates", (-2.7, 2.1, 0.35), (1.4, 1.0, 0.7))


def _stall_frame(mb, x, y, rz, burnt=True, fallen=False):
    """集市摊位骨架（2.4×1.6 m），烧焦/塌落。"""
    m = "M_A3E_CharWood" if burnt else "M_A3E_Plank"
    with mb.at(x, y, 0, rz):
        for px, py in ((-1.2, -0.8), (1.2, -0.8), (-1.2, 0.8), (1.2, 0.8)):
            h = 2.2 if py > 0 else 2.0
            if fallen and px > 0:
                h = 1.0
            mb.box(px - 0.05, py - 0.05, 0, px + 0.05, py + 0.05, h, m)
        mb.box(-1.2, -0.8, 0.8, 1.2, 0.2, 0.85, m)
        if fallen:
            tb(mb, (-1.2, -0.8, 2.0), (1.4, -0.2, 0.1), 0.05, m, seg=5)
            tb(mb, (-1.2, 0.8, 2.2), (1.3, 1.2, 0.1), 0.05, m, seg=5)
        else:
            for xx in (-1.2, 0.0, 1.2):
                tb(mb, (xx, -0.9, 2.0), (xx, 0.9, 2.2), 0.04, m, seg=5)


def build_market_fire():
    """集市火场（12×8 m，原点 = 街心）：三座烧焦的摊位骨架（一座塌了半边）、倒地焦梁、烧剩的货（陶罐碎片、焦麻包）、
    两处火苗 + 一道火线（中间街道 3 m 留空、不挡主路）；FX_Fire_*、FX_Smoke_1..2；摊位 COL_。W3/W7。"""
    rng = random.Random(110)
    mb = K.MB()
    _stall_frame(mb, -4.0, 2.6, 0)
    _stall_frame(mb, 0.5, 2.8, 5, fallen=True)
    _stall_frame(mb, 4.5, -2.8, 180)
    for i in range(6):
        with mb.at(rng.uniform(-5, 5), rng.uniform(1.6, 3.6), 0, rng.uniform(0, 180)):
            mb.box(-0.15, -0.1, 0, 0.15, 0.1, 0.12, "M_A3P_ClayDark")
    tb(mb, (-2.0, -2.0, 0.08), (1.0, -3.2, 0.08), 0.08, "M_A3E_CharWood", seg=6)
    obj(mb, "Stalls", uv=0.5)
    for k, (x, y, rz) in enumerate(((-4.0, 2.6, 0), (0.5, 2.8, 5), (4.5, -2.8, 180))):
        c = P.col_box(f"COL_Stall_{k + 1}", (x, y, 0.45), (2.6, 1.8, 0.9))
        c.rotation_euler = (0, 0, math.radians(rz))
    fl = K.MB()
    for x, y in ((0.0, 3.0), (0.8, 2.4), (4.2, -3.0)):
        P.flame(fl, x, y, 0.0, 0.3, 1.1)
    obj(fl, "NOCOL_Fire", uv=0.5)
    fx("FX_Fire_1", (0.4, 2.7, 0.6))
    fx("FX_Fire_2", (4.2, -3.0, 0.6))
    fire_line("1", (-5.5, -1.8), (-2.5, -2.2), 0.0, n=5, rng=rng)
    fx("FX_Smoke_1", (0.4, 2.7, 2.0))
    fx("FX_Smoke_2", (4.5, -2.8, 2.0))
    sc = K.MB()
    sc.box(-6, 1.4, 0, 6, 4.0, 0.01, "M_A3E_Ash")
    obj(sc, "NOCOL_Ash", uv=1.0)


def build_paddy_fire():
    """水田火/烟（12×12 m，原点 = 中心，水面高 0）：四块水田（水面 NOCOL_Water、田里一行行稻茬），中间十字田埂 1.4 m 宽
    （COL_Dike_*，可走；踩田水减速由 A 处理），三堆烧着的稻草（NOCOL_Fire + FX_Fire_*，离田埂 ≥1 m），FX_Smoke_1..3，
    两个稻捆（PROP_A3_RiceBale）。W6。"""
    rng = random.Random(111)
    dk = K.MB()
    dk.box(-6, -0.7, -0.3, 6, 0.7, 0.15, "M_A3E_Dike")
    dk.box(-0.7, -6, -0.3, 0.7, 6, 0.15, "M_A3E_Dike")
    for sx in (-1, 1):
        dk.box(-6, sx * 6 - 0.4, -0.3, 6, sx * 6 + 0.4, 0.15, "M_A3E_Dike")
        dk.box(sx * 6 - 0.4, -6, -0.3, sx * 6 + 0.4, 6, 0.15, "M_A3E_Dike")
    obj(dk, "Dikes", uv=1.0)
    P.col_box("COL_Dike_X", (0, 0, -0.07), (12, 1.4, 0.45))
    P.col_box("COL_Dike_Y", (0, 0, -0.07), (1.4, 12, 0.45))
    md = K.MB()
    md.box(-6, -6, -0.35, 6, 6, -0.3, "M_A3E_Mud")
    obj(md, "PaddyBed", uv=2.0)
    w = K.MB()
    for sx in (-1, 1):
        for sy in (-1, 1):
            w.box(min(sx * 0.7, sx * 5.6), min(sy * 0.7, sy * 5.6), -0.04, max(sx * 0.7, sx * 5.6), max(sy * 0.7, sy * 5.6), -0.02,
                  "M_A3E_Paddy")
    obj(w, "NOCOL_Water", uv=2.0)
    st = K.MB()
    for sx in (-1, 1):
        for sy in (-1, 1):
            for i in range(6):
                for j in range(6):
                    x = sx * (1.3 + i * 0.75)
                    y = sy * (1.3 + j * 0.75)
                    st.cyl(x, y, -0.3, 0.05, 0.05, "M_A3E_Stubble", seg=4, r_top=0.02)
    obj(st, "NOCOL_Stubble", uv=0.5)
    fl = K.MB()
    for k, (x, y) in enumerate(((-3.5, 3.5), (3.0, -3.8), (3.8, 3.0))):
        el(fl, (x, y, -0.04), 0.5, 0.4, 0.2, "M_A3E_Char", seg=8, rings=3, zmin=0.0)
        P.flame(fl, x, y, 0.1, 0.3, 0.9)
        fx(f"FX_Fire_{k + 1}", (x, y, 0.5))
        fx(f"FX_Smoke_{k + 1}", (x, y, 1.8))
    obj(fl, "NOCOL_Fire", uv=0.5)
    place(P.build_rice_bale, "RiceBale_1", (-1.5, -1.6, 0.15), 0)
    place(P.build_rice_bale, "RiceBale_2", (1.4, 1.6, 0.15), 40)


def build_shrine_night():
    """祖祠夜战布置 overlay（叠 BLD_INT_AncestralHall 正厅，原点 = 厅地面中心，供桌在 +Y）：两排烛架（NOCOL 火苗 + FX_Candle_*）、
    两盏挂灯笼（PROP_A3_Lantern）、一条翻倒的长凳、地上暗色血布；供桌前 2 m 留空（愧顽簿 / 指认站位不挡）。
    锚点（§9 E）：ANCHOR_BlameBook（供桌左侧）、ANCHOR_Suspect_1..3、ANCHOR_Evidence_1..3、ANCHOR_Record、ANCHOR_Respawn。"""
    rng = random.Random(112)
    mb = K.MB()
    for sx in (-1, 1):
        for k in range(3):
            x, y = sx * 3.2, -1.5 + k * 1.8
            mb.cyl(x, y, 0, 0.04, 0.18, "M_A3P_Bronze", seg=8)
            mb.cyl(x, y, 0.04, 1.1, 0.025, "M_A3P_Bronze", seg=6)
            mb.cyl(x, y, 1.1, 1.14, 0.1, "M_A3P_Bronze", seg=8)
            mb.cyl(x, y, 1.14, 1.32, 0.025, "M_A3E_Candle", seg=6)
    obj(mb, "CandleStands", uv=0.3)
    fl = K.MB()
    for sx in (-1, 1):
        for k in range(3):
            x, y = sx * 3.2, -1.5 + k * 1.8
            P.flame(fl, x, y, 1.32, 0.02, 0.07)
            fx(f"FX_Candle_{'L' if sx < 0 else 'R'}{k + 1}", (x, y, 1.36))
    obj(fl, "NOCOL_CandleFlames", uv=0.3)
    place(P.build_lantern, "Lantern_L", (-2.0, 3.6, 3.2), 180)
    place(P.build_lantern, "Lantern_R", (2.0, 3.6, 3.2), 180)
    bn = K.MB()
    with bn.at(-2.2, -3.0, 0, 25, 85, 0):
        bn.box(-0.9, -0.15, 0.0, 0.9, 0.15, 0.06, "M_A3P_WoodDark")
        for x in (-0.7, 0.7):
            bn.box(x - 0.04, -0.12, -0.4, x + 0.04, 0.12, 0.0, "M_A3P_WoodDark")
    obj(bn, "Bench_Fallen", uv=0.3)
    bc = K.MB()
    for i in range(2):
        with bc.at(rng.uniform(-2.5, 2.5), rng.uniform(-3.5, -2.0), 0.004, rng.uniform(0, 180)):
            bc.box(-0.35, -0.22, 0, 0.35, 0.22, 0.006, "M_A3E_BloodCloth")
    obj(bc, "NOCOL_BloodCloth", uv=0.5)
    anchor("ANCHOR_BlameBook", (-1.2, 2.4, 0))
    for k in range(3):
        anchor(f"ANCHOR_Suspect_{k + 1}", (-1.6 + k * 1.6, -0.6, 0))
        anchor(f"ANCHOR_Evidence_{k + 1}", (-2.6 + k * 2.6, 1.0, 0))
    anchor("ANCHOR_Record", (0, 1.6, 0))
    anchor("ANCHOR_Respawn", (0, -4.0, 0))


def build_ink_desk_1941():
    """1941 谱桌（独立小台 3×3 m，不占 1560 空间；每波 match cut）：地板一块、半面墙带木格窗（窗玻璃 NOCOL_RainGlass，雨在外面，
    FX_Rain 窗外）、书桌、椅子、桌上油灯（FX_Lamp）、摊开的族谱（Roster：T_A3_RosterPage「守城錄」三十名）、
    王砚誊写的新纸页（InkPage：T_A3_1941_Ink，最后一行半干）、砚台、笔架、毛笔。cam_matchcut = 俯拍纸面的机位。"""
    fl = K.MB()
    fl.box(-1.5, -1.5, -0.05, 1.5, 1.5, 0.0, "M_A3E_Floor")
    fl.box(-1.5, 1.4, 0.0, 1.5, 1.55, 2.8, "M_Plaster")
    fl.box(-1.5, 1.38, 0.0, 1.5, 1.42, 0.9, "M_A3P_WoodDark")
    for x in (-0.8, 0.8):
        fl.box(x - 0.05, 1.36, 1.0, x + 0.05, 1.44, 2.2, "M_A3P_WoodDark")
    fl.box(-0.85, 1.36, 0.95, 0.85, 1.44, 1.0, "M_A3P_WoodDark")
    fl.box(-0.85, 1.36, 2.2, 0.85, 1.44, 2.25, "M_A3P_WoodDark")
    for x in (-0.4, 0.0, 0.4):
        fl.box(x - 0.015, 1.37, 1.0, x + 0.015, 1.43, 2.2, "M_A3P_WoodDark")
    fl.box(-0.8, 1.37, 1.585, 0.8, 1.43, 1.615, "M_A3P_WoodDark")
    obj(fl, "Room", uv=1.0)
    gl = K.MB()
    gl.box(-0.75, 1.395, 1.0, 0.75, 1.405, 2.2, "M_A3E_Glass")
    obj(gl, "NOCOL_RainGlass", uv=1.0)
    fx("FX_Rain", (0, 2.0, 1.6))
    dk = K.MB()
    dk.box(-0.8, 0.3, 0.74, 0.8, 1.0, 0.78, "M_A3E_Desk")
    for x in (-0.75, 0.75):
        for y in (0.35, 0.95):
            dk.box(x - 0.03, y - 0.03, 0, x + 0.03, y + 0.03, 0.74, "M_A3E_Desk")
    dk.box(-0.25, -0.35, 0.44, 0.25, 0.05, 0.48, "M_A3P_WoodDark")                              # 椅
    for x in (-0.22, 0.22):
        for y in (-0.32, 0.02):
            dk.box(x - 0.02, y - 0.02, 0, x + 0.02, y + 0.02, 0.44, "M_A3P_WoodDark")
    dk.box(-0.25, -0.37, 0.48, 0.25, -0.33, 0.95, "M_A3P_WoodDark")
    P.lathe(dk, [(0.06, 0.78), (0.07, 0.82), (0.03, 0.86), (0.05, 0.9), (0.04, 1.02), (0.05, 1.1)], "M_A3E_Lamp", seg=8, x=0.6, y=0.85)
    dk.box(-0.65, 0.75, 0.78, -0.47, 0.88, 0.8, "M_A3E_Ink")                                      # 砚
    dk.box(-0.62, 0.78, 0.8, -0.5, 0.85, 0.802, "M_A3P_Oil")
    tb(dk, (-0.4, 0.8, 0.79), (-0.18, 0.88, 0.79), 0.005, "M_A3P_Bamboo", seg=5)                 # 笔
    obj(dk, "Desk", uv=0.5)
    fx("FX_Lamp", (0.6, 0.85, 1.12))
    rb = K.MB()                                                                                  # 摊开的族谱（书本）
    rb.box(-0.26, 0.42, 0.78, 0.26, 0.78, 0.8, "M_A3P_BookCover")
    rb.box(-0.25, 0.43, 0.8, 0.25, 0.77, 0.81, "M_A3P_PageEdge")
    obj(rb, "Roster", uv=0.3)
    m1 = T3.mat_from("Environments", "ENV_A3_1941_InkDesk", "RosterPage", T3.roster_tex, 0.95)
    T3.quad_xy("Roster_Page", -0.25, 0.25, 0.43, 0.77, 0.812, m1)
    m2 = T3.mat_from("Environments", "ENV_A3_1941_InkDesk", "1941_Ink", T3.ink1941_tex, 0.95)
    ip = T3.quad_xy("InkPage", 0.3, 0.55, 0.42, 0.76, 0.782, m2)
    ip.rotation_euler = (0, 0, math.radians(-6))
    cam = bpy.data.objects.new("cam_matchcut", None)
    cam.empty_display_type = "ARROWS"
    bpy.context.scene.collection.objects.link(cam)
    cam.location = (0.1, 0.4, 1.6)
    cam.rotation_euler = (math.radians(25), 0, 0)
    anchor("ANCHOR_Sit", (0, -0.15, 0))


def build_cannon_platform():
    """环海楼炮位（独立一块 6×5 m，原点 = 台面中心；摆在环海楼城墙顶 BLD_Wall_GateBaseL 走道上时整体抬 7.08）：
    木铺台（COL_Platform）、前沿（-Y）加厚的护墙带一个炮眼（炮线朝 -Y，眼前无遮挡）、两侧沙袋掩体、
    后面一架炮弹 + 两只火药桶 + 炮具架、立在侧边的教学木牌 ManualBoard（T_A3_CannonManual：一裝藥 / 二裝彈 / 三點火）。
    锚点：ANCHOR_CannonPost（炮放这里，炮口朝 -Y）、ANCHOR_Loader（装填手）、ANCHOR_Gunner（点火手，炮尾左后）。"""
    mb = K.MB()
    mb.box(-3, -2.5, 0, 3, 2.5, 0.12, "M_A3E_Plank")
    for x in (-2.5, 0, 2.5):
        mb.box(x - 0.1, -2.5, -0.15, x + 0.1, 2.5, 0.0, "M_A3E_PlankOld")
    mb.box(-3, -2.8, 0, -0.7, -2.4, 1.1, "M_A3E_Stone")                                           # 护墙 + 炮眼（x −0.7..0.7）
    mb.box(0.7, -2.8, 0, 3, -2.4, 1.1, "M_A3E_Stone")
    mb.box(-0.7, -2.8, 0, 0.7, -2.4, 0.45, "M_A3E_Stone")
    mb.box(-3.1, -2.9, 1.1, 3.1, -2.3, 1.2, "M_A3E_StoneDark")
    obj(mb, "Platform", uv=1.0)
    P.col_box("COL_Platform", (0, 0, 0.06), (6, 5, 0.12))
    P.col_box("COL_Parapet_L", (-1.85, -2.6, 0.6), (2.3, 0.4, 1.2))
    P.col_box("COL_Parapet_R", (1.85, -2.6, 0.6), (2.3, 0.4, 1.2))
    place(P.build_sandbag, "Sandbags_L", (-2.6, -1.2, 0.12), 90)
    place(P.build_cannonball, "Balls", (1.6, 1.5, 0.12), 0)
    place(P.build_powder_keg, "Keg_1", (-1.6, 1.8, 0.12))
    place(P.build_powder_keg, "Keg_2", (-2.2, 1.6, 0.12))
    place(P.build_cannon_tools, "Tools", (2.2, 0.2, 0.12), -90)
    bd = K.MB()
    for x in (-0.45, 0.45):
        bd.box(x - 0.04, -0.04, 0, x + 0.04, 0.04, 1.6, "M_A3P_WoodDark")
    bd.box(-0.5, -0.03, 0.9, 0.5, 0.03, 1.6, "M_A3P_WoodDark")
    obj(bd, "ManualBoard", (-2.4, 0.6, 0.12), uv=0.5)
    m = T3.mat_from("Environments", "ENV_A3_CannonPlatform", "CannonManual", T3.manual_tex, 0.9)
    T3.quad_xz("NOCOL_TXT_Manual", -0.45 - 2.4, 0.45 - 2.4, 1.0 + 0.12, 1.55 + 0.12, 0.6 - 0.035, m)
    anchor("ANCHOR_CannonPost", (0, -1.4, 0.12))
    anchor("ANCHOR_Loader", (0.9, -1.8, 0.12))
    anchor("ANCHOR_Gunner", (-0.5, -0.4, 0.12))


def build_barbican_gate():
    """瓮城闸门 / 落石孔（叠 BLD_Wall_Wengcheng 外门洞，同原点；门洞 x ±2.2、y −18..−14、拱顶 5.6）：
    门洞内侧一副铁皮包木千斤闸 Gate_Slide（原点在闸底，团结里沿 +Z 落下/升起：开 = 4.2 m，闭 = 0；ANCHOR_Gate_Open 参考），
    闸槽、门洞上方墙顶（走道 7.08）的绞盘 Winch（ANCHOR_Winch）、三个落石孔石板 MurderHoles（孔下方 ANCHOR_RockDrop_1..3）。
    关门时门内侧 1 m 内清人（ANCHOR_Gate 在门洞中心）。"""
    yg = -14.4
    gt = K.MB()
    for i in range(7):
        x = -2.1 + i * 0.6
        gt.box(x, -0.1, 0, x + 0.58, 0.1, 5.4, "M_A3P_WoodDark")
    for z in (0.3, 1.6, 2.9, 4.2):
        gt.box(-2.15, -0.14, z, 2.15, -0.1, z + 0.18, "M_A3E_Iron")
    for i in range(7):
        gt.cyl(-1.8 + i * 0.6, 0, -0.2, 0.0, 0.05, "M_A3E_Iron", seg=4, r_top=0.005)
    obj(gt, "Gate_Slide", (0, yg, 0), uv=0.5)
    anchor("ANCHOR_Gate_Open", (0, yg, 4.2), 0.2)
    P.col_box("COL_Gate_Slide", (0, yg, 2.7), (4.4, 0.3, 5.4))
    gr = K.MB()
    for sx in (-1, 1):
        gr.box(sx * 2.2 - 0.15, yg - 0.2, 0, sx * 2.2 + 0.15, yg + 0.2, 5.6, "M_A3E_StoneDark")
    obj(gr, "Grooves", uv=0.5)
    wn = K.MB()
    for sx in (-1, 1):
        wn.box(sx * 1.0 - 0.1, -0.3, 0, sx * 1.0 + 0.1, 0.3, 1.1, "M_A3P_WoodDark")
    with wn.at(0, 0, 0.9, 0, 90, 0):
        wn.cyl(0, 0, -1.0, 1.0, 0.15, "M_A3P_Wood", seg=8)
    for k in range(4):
        a = math.pi / 2 * k
        tb(wn, (0.8, 0, 0.9), (0.8, 0.8 * math.cos(a), 0.9 + 0.8 * math.sin(a)), 0.03, "M_A3P_Wood", seg=5)
    tb(wn, (0, 0, 0.9), (0, -0.0, 0.0 - 0.5), 0.02, "M_A3E_Rope", seg=4)
    obj(wn, "Winch", (0, -15.5, WALK), uv=0.5)
    anchor("ANCHOR_Winch", (1.6, -15.5, WALK))
    mh = K.MB()
    mh.box(-2.6, -17.2, WALK - 0.02, 2.6, -14.9, WALK + 0.06, "M_A3E_StoneDark")
    for k in range(3):
        x = -1.5 + k * 1.5
        mh.box(x - 0.3, -16.3, WALK + 0.06, x + 0.3, -15.7, WALK + 0.08, "M_A3E_Soot")
    obj(mh, "MurderHoles", uv=0.5)
    for k in range(3):
        anchor(f"ANCHOR_RockDrop_{k + 1}", (-1.5 + k * 1.5, -16.0, 0))
    anchor("ANCHOR_Gate", (0, -16.0, 0))


# ====================================================================== 注册
def recipes():
    R = {
        "ENV_A3_BurningDock": build_burning_dock, "ENV_A3_WaterGateInterior": build_water_gate_interior,
        "ENV_A3_NorthGateBarricade": build_north_gate_barricade, "ENV_A3_WallFire": build_wall_fire,
        "ENV_A3_GranaryDamage": build_granary_damage, "ENV_A3_BarbicanDefense": build_barbican_defense,
        "ENV_A3_BattleDebris": build_battle_debris,
        "ENV_A3_WallTowerDamage": build_wall_tower_damage, "ENV_A3_FloodedStreet": build_flooded_street,
        "ENV_A3_MarketFire": build_market_fire, "ENV_A3_PaddyFire": build_paddy_fire, "ENV_A3_ShrineNight": build_shrine_night,
        "ENV_A3_1941_InkDesk": build_ink_desk_1941, "ENV_A3_CannonPlatform": build_cannon_platform,
        "ENV_A3_BarbicanGate": build_barbican_gate,
    }
    return {k: ("Environments", v) for k, v in R.items()}
