"""
《入谱》第一幕 1941 · P0 道具与街市环境（Blender bpy，程序化白模）
=====================================================================

由 build_yongchang.py 的驱动统一生成/导出（RECIPES 里的 PROP_* / ENV_* 条目），对应
Docs/入谱_当前建模缺口清单.md 第一节 1.2 / 1.3。

约定：
  - 正面朝 Blender -Y（团结 +Z），1 unit = 1 m；道具原点在底面中心，环境原点在地面中心。
  - 会动、会切换状态的部件做成**单独子物体**（名字固定，团结里按名字找）：
      族谱 Book_Closed / Book_Open / Case / Case_Lid / Page_1..3 / Page_Joined / Ink_Father
      飞机 Propeller（枢轴在桨毂）  残旗 Pole（枢轴在旗座，可做倒下动画）
      军刀 Sword / Scabbard  铺门 Door_L / Door_R（枢轴在门轴）/ Chest / Chest_Lid
      牌位 Ink（墨污状态）/ Name（未涂黑状态）  火场 State_Burning / State_Burnt
  - 名为 FX_* 的空物体是特效挂点（烛火、香烟、火、烟），团结里按名字挂粒子。
"""
import math

import bpy
from mathutils import Vector

import rupu_kit as K

ACT1_PALETTE = {
    "M_PR_Paper": "#d9ccb0", "M_PR_PaperOld": "#c4b38f", "M_PR_Ink": "#141210", "M_PR_BookCover": "#3e4a57",
    "M_PR_Thread": "#c9c2b0", "M_PR_Bronze": "#5a4a32", "M_PR_Ash": "#8c877c", "M_PR_Candle": "#b8402c",
    "M_PR_Ember": "#C4552E", "M_PR_Fruit": "#a8643a", "M_PR_Plate": "#cfc8b6", "M_PR_Leather": "#3a2a1e",
    "M_PR_Brass": "#8f7a44", "M_PR_Glass": "#2a3236", "M_PR_Bellows": "#1c1a18",
    "M_PR_PlaneBody": "#5e6450", "M_PR_PlaneUnder": "#8a8c80", "M_PR_Hinomaru": "#8a2e26", "M_PR_Prop": "#2a2622",
    "M_PR_FlagRed": "#6e2a22", "M_PR_FlagPale": "#c9bfa8", "M_PR_Blood": "#3f1512", "M_PR_FlagWhite": "#d6d0c2",
    "M_PR_Steel": "#4a4d4f", "M_PR_Khaki": "#6b6446", "M_PR_Crate": "#7a6a4a",
    "M_PR_Bamboo": "#9a8a5a", "M_PR_Greens": "#5a6b3e", "M_PR_Fish": "#8a8e88", "M_PR_Sack": "#b0a07a",
    "M_PR_Jar": "#6a4a36", "M_PR_JarGlaze": "#3a3a30", "M_PR_Canvas": "#a49a80", "M_PR_Gold": "#9a8248",
    "M_PR_Char": "#1e1a17", "M_PR_CharWood": "#2e2520", "M_PR_Rubble": "#7a7268", "M_PR_PostGreen": "#3e5246",
    "M_PR_Lantern": "#b07a4a", "M_PR_Sandbag": "#9b8f6e", "M_PR_Photo": "#8a7a5c", "M_PR_Frame": "#2e2420",
}
K.PALETTE.update(ACT1_PALETTE)


# ---------------------------------------------------------------- 小工具
def obj(mb, name, loc=(0.0, 0.0, 0.0), uv=0.5):
    """把 MB（局部坐标、原点即枢轴）生成物体并放到 loc。"""
    ob = mb.to_object(name, uv_scale=uv)
    ob.location = loc
    return ob


def fx(name, loc):
    """特效挂点（空物体，团结里按 FX_* 名字挂粒子）。"""
    e = bpy.data.objects.new(name, None)
    e.empty_display_type = "SPHERE"
    e.empty_display_size = 0.1
    e.location = loc
    bpy.context.scene.collection.objects.link(e)
    return e


def loft_y(mb, sections, mat, seg=8, cap0=True, cap1=True):
    """沿 Y 的放样：sections=[(y, cx, cz, rx, rz)]，椭圆截面（机身、枪管）。"""
    rings = []
    for y, cx, cz, rx, rz in sections:
        pts = [(cx + rx * math.cos(2 * math.pi * i / seg), y, cz + rz * math.sin(2 * math.pi * i / seg)) for i in range(seg)]
        rings.append(mb.addv(pts))
    for a, b in zip(rings, rings[1:]):
        for i in range(seg):
            j = (i + 1) % seg
            mb.face([a + i, a + j, b + j, b + i], mat)
    if cap0:
        mb.face([rings[0] + i for i in range(seg)], mat)
    if cap1:
        mb.face([rings[-1] + i for i in reversed(range(seg))], mat)


def slab(mb, pts, z0, z1, mat):
    """XY 平面多边形（逆时针）拉成 z0..z1 的薄片（纸页、旗面、碎瓦）。"""
    mb.prism(pts, "z", z0, z1, mat)


def disc(mb, x, y, z, r, mat, seg=12, t=0.004):
    mb.cyl(x, y, z, z + t, r, mat, seg=seg)


# ================================================================= 1.2 核心道具
def build_genealogy():
    """族谱套件：半本线装谱（合/开）、谱匣（匣身+盖）、三张散页、拼合页 + 父名墨污。"""
    # 半本谱（合）：只有正常厚度的一半，书口一侧撕得参差
    mb = K.MB()
    mb.box(-0.13, -0.09, 0, 0.13, 0.09, 0.004, "M_PR_BookCover")
    mb.box(-0.128, -0.088, 0.004, 0.126, 0.088, 0.016, "M_PR_PaperOld")
    for i, dy in enumerate((-0.07, -0.02, 0.03, 0.075)):   # 书口撕口：几片翘起的残页
        mb.box(0.118, dy, 0.006 + 0.002 * (i % 2), 0.134, dy + 0.02, 0.009 + 0.002 * (i % 2), "M_PR_PaperOld")
    mb.box(-0.13, -0.09, 0.016, 0.13, 0.09, 0.02, "M_PR_BookCover")
    mb.box(-0.12, -0.075, 0.02, -0.085, 0.075, 0.021, "M_PR_FlagPale")          # 题签
    for y in (-0.06, -0.02, 0.02, 0.06):                                     # 线装四眼
        mb.box(-0.127, y - 0.002, -0.0005, -0.115, y + 0.002, 0.0205, "M_PR_Thread")
    obj(mb, "Book_Closed", (0, 0, 0))
    # 半本谱（开）：摊开两页，左页写满、右页下排一格墨污（父名），右下角缺角
    mb = K.MB()
    mb.box(-0.26, -0.09, 0, 0.0, 0.09, 0.006, "M_PR_BookCover")
    mb.box(0.0, -0.09, 0, 0.26, 0.09, 0.006, "M_PR_BookCover")
    slab(mb, [(-0.25, -0.085), (-0.005, -0.085), (-0.005, 0.085), (-0.25, 0.085)], 0.006, 0.012, "M_PR_PaperOld")
    slab(mb, [(0.005, -0.085), (0.2, -0.085), (0.25, -0.04), (0.25, 0.085), (0.005, 0.085)], 0.006, 0.012, "M_PR_PaperOld")
    for k in range(6):                                                       # 竖排字行
        x = -0.23 + k * 0.038
        mb.box(x, -0.07, 0.012, x + 0.006, 0.07, 0.0125, "M_PR_Ink")
    for k in range(4):
        x = 0.03 + k * 0.038
        mb.box(x, -0.02, 0.012, x + 0.006, 0.07, 0.0125, "M_PR_Ink")
    mb.box(0.18, -0.03, 0.012, 0.215, 0.06, 0.0128, "M_PR_Ink")              # 父名被墨涂黑
    obj(mb, "Book_Open", (0.0, -0.32, 0))
    # 谱匣：樟木匣 + 盖（盖单独，枢轴在后沿，可翻开）
    mb = K.MB()
    mb.box(-0.17, -0.12, 0, 0.17, 0.12, 0.012, "M_PR_WoodDark")
    for x0, x1, y0, y1 in ((-0.17, 0.17, -0.12, -0.105), (-0.17, 0.17, 0.105, 0.12), (-0.17, -0.155, -0.12, 0.12), (0.155, 0.17, -0.12, 0.12)):
        mb.box(x0, y0, 0.012, x1, y1, 0.09, "M_PR_WoodDark")
    mb.box(-0.02, -0.124, 0.06, 0.02, -0.12, 0.085, "M_PR_Brass")             # 锁扣
    obj(mb, "Case", (-0.42, 0, 0))
    mb = K.MB()
    mb.box(-0.175, -0.245, 0, 0.175, 0.0, 0.03, "M_PR_WoodDark")                  # 枢轴=后沿
    mb.box(-0.12, -0.2, 0.03, 0.12, -0.045, 0.034, "M_PR_Wood")
    obj(mb, "Case_Lid", (-0.42, 0.125, 0.09))
    # 三张散页（撕口不规则）+ 拼合后的整页
    pages = [
        [(-0.09, -0.12), (0.02, -0.12), (0.035, -0.02), (0.0, 0.05), (-0.09, 0.05)],
        [(0.0, 0.05), (0.035, -0.02), (0.09, -0.01), (0.09, 0.12), (-0.02, 0.12)],
        [(-0.09, 0.05), (0.0, 0.05), (-0.02, 0.12), (-0.09, 0.12)],
        [(0.02, -0.12), (0.09, -0.12), (0.09, -0.01), (0.035, -0.02)],
    ]
    spots = [(0.42, -0.1), (0.62, 0.02), (0.5, 0.18)]
    for i, (sx, sy) in enumerate(spots):
        mb = K.MB()
        pts = pages[i] if i < 2 else pages[2] + []
        cx = sum(p[0] for p in pts) / len(pts)
        cy = sum(p[1] for p in pts) / len(pts)
        slab(mb, [(x - cx, y - cy) for x, y in pts], 0, 0.0015, "M_PR_Paper")
        for k in range(3):
            x = -0.03 + k * 0.025
            mb.box(x, -0.03, 0.0015, x + 0.004, 0.03, 0.0018, "M_PR_Ink")
        obj(mb, f"Page_{i + 1}", (sx, sy, 0.0))
    mb = K.MB()
    slab(mb, [(-0.09, -0.12), (0.09, -0.12), (0.09, 0.12), (-0.09, 0.12)], 0, 0.0015, "M_PR_Paper")
    for k in range(6):
        x = -0.075 + k * 0.03
        mb.box(x, -0.1, 0.0015, x + 0.005, 0.1, 0.0018, "M_PR_Ink")
    obj(mb, "Page_Joined", (0.75, -0.3, 0))
    mb = K.MB()
    slab(mb, [(-0.02, -0.03), (0.025, -0.035), (0.03, 0.02), (0.0, 0.04), (-0.028, 0.02)], 0.0018, 0.0026, "M_PR_Ink")
    obj(mb, "Ink_Father", (0.79, -0.3, 0))


def build_plane():
    """日军单发低单翼战斗机：机身放样、固定起落架、机翼红日徽、可转螺旋桨（Propeller 子物体）。"""
    mb = K.MB()
    z = 1.55
    loft_y(mb, [(-3.7, 0, z, 0.55, 0.55), (-3.2, 0, z, 0.62, 0.62), (-1.6, 0, z + 0.05, 0.58, 0.62),
                (0.4, 0, z + 0.08, 0.48, 0.55), (2.4, 0, z + 0.2, 0.28, 0.34), (3.8, 0, z + 0.32, 0.1, 0.12)],
           "M_PR_PlaneBody", seg=10)
    loft_y(mb, [(-1.2, 0, z + 0.55, 0.05, 0.05), (-0.9, 0, z + 0.62, 0.34, 0.3), (0.3, 0, z + 0.6, 0.32, 0.26),
                (0.9, 0, z + 0.45, 0.06, 0.06)], "M_PR_Glass", seg=8)
    with mb.at(0, 0, z - 0.42):                                                 # 下单翼 + 翼面红日徽
        mb.prism([(-5.4, 0.0), (-1.2, 0.06), (1.2, 0.06), (5.4, 0.0)], "y", -1.88, -0.4, "M_PR_PlaneBody")
        for sx in (-1, 1):
            disc(mb, sx * 3.6, -1.15, 0.065, 0.45, "M_PR_Hinomaru", seg=14)
    with mb.at(0, 0, z + 0.25):                                                 # 平尾
        mb.prism([(-1.9, 0), (1.9, 0), (1.4, 0.05), (-1.4, 0.05)], "y", 3.0, 3.7, "M_PR_PlaneBody")
    with mb.at(0, 0, z + 0.3):
        mb.prism([(3.0, 0), (3.8, 0), (3.85, 1.0), (3.45, 1.05)], "x", -0.04, 0.04, "M_PR_PlaneBody")   # 垂尾
    for sx in (-1, 1):                                                            # 固定起落架 + 整流罩
        mb.box(sx * 1.25 - 0.06, -1.5, 0.35, sx * 1.25 + 0.06, -1.3, z - 0.42, "M_PR_PlaneBody")
        loft_y(mb, [(-1.9, sx * 1.25, 0.38, 0.05, 0.05), (-1.6, sx * 1.25, 0.38, 0.17, 0.36), (-1.1, sx * 1.25, 0.4, 0.15, 0.3),
                    (-0.8, sx * 1.25, 0.45, 0.04, 0.05)], "M_PR_PlaneBody", seg=8)
        mb.box(sx * 1.25 - 0.05, -1.55, 0.0, sx * 1.25 + 0.05, -1.25, 0.08, "M_PR_Prop")
    mb.box(-0.04, 3.4, z - 0.15, 0.04, 3.55, z + 0.2, "M_PR_PlaneBody")          # 尾轮支柱（短）
    mb.box(-0.05, 3.38, z - 0.3, 0.05, 3.57, z - 0.15, "M_PR_Prop")
    with mb.at(0, 0, z):
        loft_y(mb, [(-1.0, 0, -0.5, 0.35, 0.08), (2.0, 0, -0.45, 0.25, 0.06)], "M_PR_PlaneUnder", seg=8)
    obj(mb, "Plane_Body", (0, 0, 0), uv=2.0)
    # 螺旋桨直接按最终朝向建（不靠物体旋转，FBX 导入后轴向才稳定）：桨毂沿机身轴 Y，两片桨叶竖在 XZ 平面
    mb = K.MB()
    loft_y(mb, [(0.15, 0, 0, 0.13, 0.13), (-0.1, 0, 0, 0.1, 0.1), (-0.25, 0, 0, 0.02, 0.02)], "M_PR_Prop", seg=8)
    for sz in (-1, 1):
        mb.box(-0.08, -0.02, sz * 0.12, 0.08, 0.02, sz * 1.25, "M_PR_Prop")
    obj(mb, "Propeller", (0, -3.95, z), uv=2.0)
    fx("FX_Trail_L", (-5.4, 0.0, z - 0.45))
    fx("FX_Trail_R", (5.4, 0.0, z - 0.45))


def build_fallen_flag():
    """残旗：三级石阶 + 旗座 + 6 m 旗杆斜倒 72°（Pole 枢轴在旗座，可做倒下动画）+ 破旗面与旧血。"""
    mb = K.MB()
    for k in range(3):
        mb.box(-1.6, -0.45 * (3 - k), 0.18 * k, 1.6, 0.0, 0.18 * (k + 1), "M_Stone_Base")
    mb.box(-1.6, 0.0, 0, 1.6, 1.2, 0.54, "M_Stone_Base")
    obj(mb, "Steps", (0, 0, 0), uv=1.0)
    mb = K.MB()
    mb.box(-0.32, -0.32, 0, 0.32, 0.32, 0.36, "M_Wall_Stone")
    mb.box(-0.12, -0.12, 0.36, 0.12, 0.12, 0.4, "M_PR_WoodDark")
    obj(mb, "Base", (0.8, 0.6, 0.54), uv=1.0)
    mb = K.MB()
    mb.cyl(0, 0, 0, 6.0, 0.05, "M_PR_WoodDark", seg=8, r_top=0.035)
    mb.cyl(0, 0, 5.95, 6.05, 0.06, "M_PR_Brass", seg=8)
    # 破旗面（挂在杆上段，撕成三片，边缘缺口），旧血两块
    with mb.at(0, 0, 4.3):
        mb.prism([(0.04, 1.6), (1.3, 1.55), (1.15, 1.2), (1.4, 0.95), (0.04, 1.05)], "y", -0.006, 0.006, "M_PR_FlagRed")
        mb.prism([(0.04, 1.05), (1.2, 0.9), (0.95, 0.55), (0.04, 0.5)], "y", -0.006, 0.006, "M_PR_FlagRed")
        mb.prism([(0.04, 0.5), (0.7, 0.42), (0.35, 0.05), (0.04, 0.12)], "y", -0.006, 0.006, "M_PR_FlagRed")
        mb.prism([(0.35, 1.45), (0.75, 1.42), (0.7, 1.12), (0.38, 1.15)], "y", -0.009, 0.009, "M_PR_FlagPale")
        mb.prism([(0.5, 0.95), (0.85, 0.9), (0.72, 0.65), (0.48, 0.7)], "y", -0.012, 0.012, "M_PR_Blood")
        mb.prism([(0.12, 0.45), (0.4, 0.38), (0.25, 0.2)], "y", -0.012, 0.012, "M_PR_Blood")
    ob = obj(mb, "Pole", (0.8, 0.6, 0.94), uv=1.0)
    # 从旗座朝台阶下（-Y）倒下、搭着石阶，杆梢落地；破旗面摊在地上
    ob.rotation_euler = (math.radians(98), 0, math.radians(-15))
    mb = K.MB()
    slab(mb, [(-0.3, -0.2), (0.25, -0.25), (0.35, 0.15), (-0.1, 0.3), (-0.35, 0.05)], 0, 0.003, "M_PR_Blood")
    obj(mb, "Blood_Steps", (0.55, -0.7, 0.36))


def build_incense_set():
    """香案套件：铜香炉（香灰 + 三炷香）、一对烛台、两盘供果、三只酒盅；FX_* 为烛火/香烟挂点。"""
    mb = K.MB()
    mb.cyl(0, 0, 0.06, 0.2, 0.16, "M_PR_Bronze", seg=12, r_top=0.19)
    mb.cyl(0, 0, 0.2, 0.215, 0.2, "M_PR_Bronze", seg=12)
    mb.cyl(0, 0, 0.19, 0.2, 0.18, "M_PR_Ash", seg=12)
    for a in (90, 210, 330):
        x, y = 0.12 * math.cos(math.radians(a)), 0.12 * math.sin(math.radians(a))
        mb.cyl(x, y, 0, 0.08, 0.02, "M_PR_Bronze", seg=6)
    for sx in (-1, 1):
        mb.box(sx * 0.19, -0.02, 0.2, sx * 0.23, 0.02, 0.3, "M_PR_Bronze")
    obj(mb, "Burner", (0, 0, 0))
    mb = K.MB()
    for dx in (-0.04, 0.0, 0.04):
        mb.cyl(dx, 0, 0, 0.3, 0.004, "M_PR_Candle", seg=4)
        mb.cyl(dx, 0, 0.3, 0.31, 0.005, "M_PR_Ember", seg=4)
    obj(mb, "Incense_Sticks", (0, 0, 0.2))
    fx("FX_IncenseSmoke", (0, 0, 0.52))
    for sx, nm in ((-1, "L"), (1, "R")):
        mb = K.MB()
        mb.cyl(0, 0, 0, 0.02, 0.07, "M_PR_Bronze", seg=8)
        mb.cyl(0, 0, 0.02, 0.26, 0.018, "M_PR_Bronze", seg=6)
        mb.cyl(0, 0, 0.26, 0.28, 0.06, "M_PR_Bronze", seg=8)
        mb.cyl(0, 0, 0.28, 0.44, 0.025, "M_PR_Candle", seg=8)
        obj(mb, f"Candle_{nm}", (sx * 0.5, 0.05, 0))
        fx(f"FX_Candle_{nm}", (sx * 0.5, 0.05, 0.47))
    for sx in (-1, 1):
        mb = K.MB()
        mb.cyl(0, 0, 0, 0.02, 0.12, "M_PR_Plate", seg=10, r_top=0.14)
        for (dx, dy, dz) in ((-0.04, -0.03, 0.06), (0.045, -0.02, 0.06), (0.0, 0.045, 0.06), (0.0, 0.0, 0.12)):
            mb.ico(dx, dy, dz, 0.045, "M_PR_Fruit")
        obj(mb, f"Fruit_{'L' if sx < 0 else 'R'}", (sx * 0.3, -0.12, 0))
    mb = K.MB()
    for dx in (-0.09, 0.0, 0.09):
        mb.cyl(dx, 0, 0, 0.04, 0.022, "M_PR_Plate", seg=8, r_top=0.03)
    obj(mb, "Cups", (0, -0.25, 0))


def build_camera():
    """王砚的折叠相机（1941）：机身、皮腔、镜头、取景器；Case 为皮套（带背带扣）。"""
    mb = K.MB()
    mb.box(-0.075, -0.02, 0.0, 0.075, 0.02, 0.1, "M_PR_Leather")
    mb.box(-0.074, -0.021, 0.008, 0.074, 0.021, 0.092, "M_PR_Bellows")
    mb.hexa([(-0.045, -0.02, 0.02), (0.045, -0.02, 0.02), (0.03, -0.11, 0.035), (-0.03, -0.11, 0.035),
             (-0.045, -0.02, 0.08), (0.045, -0.02, 0.08), (0.03, -0.11, 0.065), (-0.03, -0.11, 0.065)], "M_PR_Bellows")
    mb.box(-0.032, -0.118, 0.028, 0.032, -0.11, 0.072, "M_PR_Steel")
    with mb.at(0, -0.12, 0.05, rx=90):
        mb.cyl(0, 0, 0, 0.012, 0.018, "M_PR_Glass", seg=10)
    mb.box(0.035, -0.012, 0.1, 0.06, 0.012, 0.115, "M_PR_Steel")
    mb.box(-0.06, -0.008, 0.1, -0.045, 0.008, 0.106, "M_PR_Steel")
    obj(mb, "Camera", (0, 0, 0))
    mb = K.MB()
    mb.box(-0.085, -0.03, 0.0, 0.085, 0.03, 0.12, "M_PR_Leather")
    mb.box(-0.087, -0.032, 0.09, 0.087, 0.032, 0.125, "M_CH_WY41_Bag")
    for sx in (-1, 1):
        mb.box(sx * 0.087 - 0.006, -0.008, 0.06, sx * 0.087 + 0.006, 0.008, 0.11, "M_PR_Brass")
    obj(mb, "Case", (0.3, 0, 0))


def build_rifle():
    """三八式步枪（1.28 m）：竖立，枪托着地（原点=枪托底），刺刀单独子物体 Bayonet。"""
    mb = K.MB()
    mb.hexa([(-0.02, -0.06, 0.0), (0.02, -0.06, 0.0), (0.02, 0.05, 0.0), (-0.02, 0.05, 0.0),
             (-0.017, -0.02, 0.28), (0.017, -0.02, 0.28), (0.017, 0.02, 0.28), (-0.017, 0.02, 0.28)], "M_PR_Wood")
    mb.box(-0.018, -0.022, 0.28, 0.018, 0.022, 0.92, "M_PR_Wood")
    mb.cyl(0, 0.0, 0.92, 1.28, 0.008, "M_PR_Steel", seg=6)
    mb.box(-0.013, -0.03, 0.42, 0.013, 0.0, 0.52, "M_PR_Steel")                 # 机匣
    mb.box(0.012, -0.03, 0.48, 0.05, -0.022, 0.49, "M_PR_Steel")               # 拉机柄
    mb.box(-0.012, 0.02, 0.4, 0.012, 0.045, 0.43, "M_PR_Steel")                # 扳机护圈
    for z in (0.62, 0.86):
        mb.box(-0.02, -0.024, z, 0.02, 0.024, z + 0.015, "M_PR_Steel")
    mb.box(-0.004, 0.02, 0.35, 0.004, 0.024, 0.9, "M_CH_JA_Leather")           # 背带
    obj(mb, "Rifle", (0, 0, 0))
    mb = K.MB()
    mb.box(-0.004, -0.012, 0.0, 0.004, 0.012, 0.4, "M_PR_Steel")
    mb.box(-0.012, -0.02, 0.0, 0.012, 0.02, 0.1, "M_PR_WoodDark")
    obj(mb, "Bayonet", (0.0, 0.0, 1.18))


def build_sword():
    """九八式军刀：Sword（刀身+柄，原点=刀柄末端）与 Scabbard（鞘，原点=鞘口）分开，可拔刀/收刀。"""
    mb = K.MB()
    mb.box(-0.014, -0.012, 0.0, 0.014, 0.012, 0.26, "M_CH_JA_Leather")        # 柄
    mb.cyl(0, 0, 0.26, 0.272, 0.04, "M_PR_Brass", seg=8)                      # 镡
    with mb.at(0, 0, 0.272, rx=-2):
        mb.prism([(-0.014, 0.0), (0.014, 0.0), (0.012, 0.68), (0.0, 0.72), (-0.012, 0.66)], "y", -0.003, 0.003, "M_PR_Steel")
    obj(mb, "Sword", (0, 0, 0.72))
    mb = K.MB()
    mb.box(-0.018, -0.008, -0.72, 0.018, 0.008, 0.0, "M_PR_Steel")
    mb.box(-0.02, -0.01, -0.06, 0.02, 0.01, -0.04, "M_PR_Brass")
    mb.box(-0.02, -0.01, -0.74, 0.02, 0.01, -0.7, "M_PR_Brass")
    obj(mb, "Scabbard", (0.1, 0, 0.74))


def build_ammo_box():
    """弹药箱：木箱 + 铁扣 + 两条绳把手，盖上压一盒子弹。"""
    mb = K.MB()
    mb.box(-0.3, -0.18, 0, 0.3, 0.18, 0.26, "M_PR_Crate")
    for x in (-0.25, 0.25):
        mb.box(x - 0.02, -0.185, 0, x + 0.02, 0.185, 0.27, "M_PR_Steel")
    for sx in (-1, 1):
        mb.box(sx * 0.3, -0.05, 0.16, sx * 0.32, 0.05, 0.18, "M_PR_Sack")
    mb.box(-0.08, -0.05, 0.27, 0.08, 0.05, 0.31, "M_PR_Khaki")
    obj(mb, "AmmoBox", (0, 0, 0))


def build_vendor_goods():
    """摊货一组：扁担 + 两只菜筐、竹匾里的鱼、米袋两只、陶罐三只、杆秤。"""
    def basket(mb, x, y, r=0.24, h=0.28, fill="M_PR_Greens"):
        mb.cyl(x, y, 0, h, r * 0.85, "M_PR_Bamboo", seg=10, r_top=r)
        mb.cyl(x, y, h - 0.02, h + 0.06, r * 0.92, fill, seg=10, r_top=r * 0.6)
    mb = K.MB()
    basket(mb, -0.7, 0)
    basket(mb, 0.7, 0)
    for sx in (-1, 1):                                                         # 筐绳
        for a in (45, 135, 225, 315):
            x = sx * 0.7 + 0.18 * math.cos(math.radians(a))
            y = 0.18 * math.sin(math.radians(a))
            mb.box(x - 0.006, y - 0.006, 0.3, x + 0.006, y + 0.006, 0.95, "M_PR_Thread")
    mb.box(-0.95, -0.025, 0.93, 0.95, 0.025, 0.97, "M_PR_Bamboo")              # 扁担（挑在地上靠着筐）
    obj(mb, "Pole_Baskets", (0, 0, 0))
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.05, 0.36, "M_PR_Bamboo", seg=12)
    for k, (dx, dy, a) in enumerate(((-0.12, -0.05, 20), (0.0, 0.06, -10), (0.12, -0.04, 35), (-0.02, -0.14, 80))):
        with mb.at(dx, dy, 0.05, rz=a):
            mb.ico(0, 0, 0.025, 0.04, "M_PR_Fish", sx=2.8, sy=1.0, sz=0.6)
            mb.prism([(0.1, 0.0), (0.16, 0.04), (0.16, -0.04)], "z", 0.02, 0.03, "M_PR_Fish")
    obj(mb, "Fish_Tray", (1.3, 0.1, 0))
    mb = K.MB()
    for dx, h in ((-0.18, 0.5), (0.2, 0.44)):
        mb.cyl(dx, 0, 0, h, 0.17, "M_PR_Sack", seg=8, r_top=0.12)
        mb.cyl(dx, 0, h, h + 0.06, 0.05, "M_PR_Sack", seg=6)
    obj(mb, "Rice_Sacks", (-1.4, 0.2, 0))
    mb = K.MB()
    for dx, dy, r, h in ((-0.2, 0, 0.14, 0.34), (0.12, 0.05, 0.11, 0.26), (0.0, -0.22, 0.09, 0.2)):
        mb.cyl(dx, dy, 0, h * 0.7, r * 0.7, "M_PR_Jar", seg=10, r_top=r)
        mb.cyl(dx, dy, h * 0.7, h, r, "M_PR_JarGlaze", seg=10, r_top=r * 0.55)
    obj(mb, "Jars", (-0.4, 0.8, 0))
    mb = K.MB()
    with mb.at(0, 0, 0.0, ry=90):
        mb.cyl(0, 0, -0.45, 0.45, 0.012, "M_PR_WoodDark", seg=6)
    mb.cyl(0.3, 0, -0.2, -0.05, 0.035, "M_PR_Steel", seg=6)                     # 秤砣
    mb.box(0.298, -0.003, -0.05, 0.302, 0.003, 0.0, "M_PR_Thread")
    mb.cyl(-0.35, 0, -0.3, -0.28, 0.12, "M_PR_Bamboo", seg=8)                  # 秤盘
    for a in (0, 120, 240):
        x = -0.35 + 0.1 * math.cos(math.radians(a))
        mb.box(x - 0.002, -0.002, -0.28, x + 0.002, 0.002, 0.0, "M_PR_Thread")
    ob = obj(mb, "Steelyard", (0.4, 0.8, 0.3))


def build_banner_shrine():
    """祠堂幡：竖杆 + 横担 + 长条幡（三段飘带）。"""
    mb = K.MB()
    mb.cyl(0, 0, 0, 3.6, 0.035, "M_PR_WoodDark", seg=8)
    mb.box(-0.02, -0.02, 3.4, 0.6, 0.02, 3.44, "M_PR_WoodDark")
    mb.box(0.1, -0.004, 1.3, 0.5, 0.004, 3.4, "M_PR_FlagRed")
    mb.box(0.15, -0.006, 2.4, 0.45, 0.006, 3.2, "M_PR_FlagPale")
    for k, x in enumerate((0.12, 0.27, 0.42)):
        mb.box(x, -0.004, 0.9 + 0.1 * k, x + 0.06, 0.004, 1.3, "M_PR_FlagRed")
    mb.cyl(0, 0, 0, 0.12, 0.16, "M_Wall_Stone", seg=8)
    obj(mb, "Banner", (0, 0, 0), uv=1.0)


def build_banner_street():
    """街市横幅：两根竹竿之间拉一条布幅（标语，字后贴）。"""
    mb = K.MB()
    for sx in (-1, 1):
        mb.cyl(sx * 2.2, 0, 0, 3.6, 0.04, "M_PR_Bamboo", seg=6)
    mb.box(-2.15, -0.004, 2.7, 2.15, 0.004, 3.3, "M_PR_FlagPale")
    for k in range(8):
        x = -1.8 + k * 0.5
        mb.box(x, -0.007, 2.8, x + 0.3, 0.007, 3.2, "M_PR_Ink")
    obj(mb, "Banner", (0, 0, 0), uv=1.0)


def build_flag_japan():
    """日军旗：旗杆 + 白底红日旗面（哨卡/占领祠堂门口）。"""
    mb = K.MB()
    mb.cyl(0, 0, 0, 3.4, 0.03, "M_PR_WoodDark", seg=8)
    mb.ico(0, 0, 3.45, 0.05, "M_PR_Brass")
    mb.box(0.03, -0.004, 2.4, 1.23, 0.004, 3.2, "M_PR_FlagWhite")
    with mb.at(0.63, 0, 2.8, rx=90):
        mb.cyl(0, 0, -0.008, 0.008, 0.24, "M_PR_Hinomaru", seg=14)
    mb.box(-0.25, -0.25, 0, 0.25, 0.25, 0.15, "M_PR_Sandbag")
    obj(mb, "Flag", (0, 0, 0), uv=1.0)


def build_door_loot():
    """砸门抢箱：两扇铺门板（Door_L / Door_R，枢轴在门轴，可踹开）+ 樟木箱（Chest / Chest_Lid）。"""
    for nm, sx in (("Door_L", -1), ("Door_R", 1)):
        mb = K.MB()
        x0, x1 = (0.0, 0.9) if sx < 0 else (-0.9, 0.0)
        mb.box(x0, -0.03, 0, x1, 0.03, 2.4, "M_Wood_Dark")
        for z in (0.4, 1.2, 2.0):
            mb.box(x0 + 0.05, -0.04, z, x1 - 0.05, -0.03, z + 0.08, "M_PR_WoodDark")
        mb.box(x0 + (0.75 if sx < 0 else 0.07), -0.05, 1.1, x0 + (0.83 if sx < 0 else 0.15), -0.03, 1.3, "M_PR_Steel")
        obj(mb, nm, (sx * 0.9, 0, 0), uv=1.0)
    mb = K.MB()
    mb.box(-0.45, -0.28, 0, 0.45, 0.28, 0.45, "M_PR_Jar")
    for x in (-0.35, 0.35):
        mb.box(x - 0.025, -0.29, 0, x + 0.025, 0.29, 0.46, "M_PR_Steel")
    mb.box(-0.04, -0.29, 0.32, 0.04, -0.28, 0.42, "M_PR_Brass")
    obj(mb, "Chest", (0.6, -1.2, 0), uv=1.0)
    mb = K.MB()
    mb.box(-0.46, -0.58, 0, 0.46, 0.0, 0.09, "M_PR_Jar")                        # 枢轴=后沿
    obj(mb, "Chest_Lid", (0.6, -0.92, 0.45), uv=1.0)


def build_tablet_father():
    """父亲王世清牌位：座 + 牌身 + 顶；Name（金字，未涂黑）与 Ink（墨污）两种状态子物体。"""
    mb = K.MB()
    mb.box(-0.14, -0.08, 0, 0.14, 0.08, 0.08, "M_PR_WoodDark")
    mb.box(-0.1, -0.025, 0.08, 0.1, 0.025, 0.56, "M_Red_Lacquer")
    mb.prism([(-0.12, 0.56), (0.12, 0.56), (0.08, 0.64), (-0.08, 0.64)], "y", -0.03, 0.03, "M_PR_WoodDark")
    obj(mb, "Tablet", (0, 0, 0), uv=1.0)
    mb = K.MB()
    for k in range(5):
        z = 0.14 + k * 0.075
        mb.box(-0.02, -0.03, z, 0.02, -0.025, z + 0.05, "M_PR_Gold")
    obj(mb, "Name", (0, 0, 0))
    mb = K.MB()
    slab(mb, [(-0.06, 0), (0.05, 0.0), (0.07, 0.3), (0.01, 0.36), (-0.07, 0.28)], 0, 0.004, "M_PR_Ink")
    ob = obj(mb, "Ink", (0, -0.03, 0.12))
    ob.rotation_euler = (math.radians(90), 0, 0)


FATHER_CFG = dict(H=1.74, outfit="robe", top="M_CH_WY41_Robe", pants="M_CH_WY41_Pants", shoe="M_CH_WY41_Shoe",
                  hair="short", beard="goatee", extras=["glasses"], bulk=0.97,
                  desc="王世清（王砚之父，1940 年失踪）：只用来渲染照片，不单独出 3D 资产")


def build_father_photo():
    """父亲王世清照片：先渲一张旧照片（半身、深褐单色、暗角）存成 T_FatherPhoto_D.png，再做相框 + 照片面。"""
    import os
    import rupu_char as C
    scene = bpy.context.scene
    world = scene.world or bpy.data.worlds.new("PhotoWorld")
    scene.world = world
    world.color = (0.55, 0.52, 0.46)                                           # 照相馆布景的浅灰底
    rig = C.build_character("NPC_WangShiqing", FATHER_CFG)
    bust = [o for o in scene.objects if o.parent == rig] + [rig]
    bpy.context.view_layer.objects.active = rig            # 照相：两臂自然垂下（借用待机姿势）
    bpy.ops.object.mode_set(mode="POSE")
    pose, _ = C.pose_at(0.0, "idle")
    for b, R in pose.items():
        C.set_rot(rig, b, R)
    bpy.ops.object.mode_set(mode="OBJECT")
    bpy.context.view_layer.update()
    cam_data = bpy.data.cameras.new("PhotoCam")
    cam_data.type = "ORTHO"
    cam_data.ortho_scale = 0.62
    cam = bpy.data.objects.new("PhotoCam", cam_data)
    scene.collection.objects.link(cam)
    cam.location = (0.0, -3.0, 1.5)
    cam.rotation_euler = (math.radians(90), 0, 0)
    scene.camera = cam
    ref = bpy.data.collections.get("_REF")
    if ref:
        ref.hide_render = True
    scene.render.engine = "BLENDER_WORKBENCH"
    scene.display.shading.light = "STUDIO"
    scene.display.shading.color_type = "MATERIAL"
    scene.display.shading.show_shadows = True
    scene.display.shading.show_cavity = True
    scene.render.film_transparent = False
    scene.render.resolution_x = 768
    scene.render.resolution_y = 1024
    # .blend 在配方执行完才保存，这里按仓库约定直接算出资产目录
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out_dir = os.path.join(root, "Project_rupu", "Assets", "Art", "Props", "PROP_FatherPhoto")
    os.makedirs(out_dir, exist_ok=True)
    tex_path = os.path.join(out_dir, "T_FatherPhoto_D.png")
    scene.render.filepath = tex_path
    bpy.ops.render.render(write_still=True)
    # 调成旧照片：灰度 → 深褐、提一点对比、四角暗、边缘泛黄
    img = bpy.data.images.load(tex_path)
    W_, H_ = img.size
    px = list(img.pixels)
    for j in range(H_):
        for i in range(W_):
            k = (j * W_ + i) * 4
            lum = 0.3 * px[k] + 0.59 * px[k + 1] + 0.11 * px[k + 2]
            lum = min(1.0, max(0.0, (lum - 0.5) * 1.25 + 0.5))
            dx, dy = (i / W_ - 0.5) * 1.6, (j / H_ - 0.5) * 1.3
            vig = max(0.0, 1.0 - 0.55 * (dx * dx + dy * dy))
            lum *= vig
            px[k], px[k + 1], px[k + 2] = lum * 0.92 + 0.05, lum * 0.78 + 0.04, lum * 0.58 + 0.03
    img.pixels = px
    img.filepath_raw = tex_path
    img.file_format = "PNG"
    img.save()
    for o in bust + [cam]:
        bpy.data.objects.remove(o, do_unlink=True)
    if ref:
        ref.hide_render = False
    # 相框 + 照片面（照片材质用上面渲的贴图）
    mb = K.MB()
    mb.box(-0.13, -0.015, 0.0, 0.13, 0.0, 0.32, "M_PR_Frame")
    with mb.at(0, 0.0, 0.0):
        mb.box(-0.1, -0.06, 0.0, 0.1, 0.0, 0.012, "M_PR_Frame")                # 底托
    mb.box(-0.02, 0.0, 0.0, 0.02, 0.1, 0.25, "M_PR_Frame")                     # 背撑
    obj(mb, "Frame", (0, 0, 0), uv=1.0)
    me = bpy.data.meshes.new("Photo")
    me.from_pydata([(-0.1, -0.017, 0.035), (0.1, -0.017, 0.035), (0.1, -0.017, 0.295), (-0.1, -0.017, 0.295)], [], [(0, 1, 2, 3)])
    me.uv_layers.new(name="UVMap")
    for li, uv in zip(range(4), ((0, 0), (1, 0), (1, 1), (0, 1))):
        me.uv_layers[0].data[li].uv = uv
    mat = bpy.data.materials.new("M_FatherPhoto")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = img
    nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.6
    me.materials.append(mat)
    ob = bpy.data.objects.new("Photo", me)
    scene.collection.objects.link(ob)


# ================================================================= 1.3 街市 / 火场环境
def shop_shell(mb, w=6.0, d=5.0, h=6.2, burnt=False):
    """两层铺面外壳（与 BLD_ROC 街屋同尺度）：烧过的版本墙头参差、窗洞焦黑。"""
    wall = "M_PR_Char" if burnt else "M_Plaster"
    lower = "M_PR_CharWood" if burnt else "M_Plaster_Lower"
    mb.box(-w / 2, -d / 2, 0, w / 2, d / 2, 0.3, "M_Stone_Base")
    for x0, x1 in ((-w / 2, -w / 2 + 0.3), (w / 2 - 0.3, w / 2)):           # 两侧山墙（烧后上沿缺口）
        mb.box(x0, -d / 2, 0.3, x1, d / 2, h - (0.8 if burnt and x0 > 0 else 0), wall)
    mb.box(-w / 2, d / 2 - 0.3, 0.3, w / 2, d / 2, h - (1.4 if burnt else 0), wall)
    mb.box(-w / 2, -d / 2, 0.3, w / 2, -d / 2 + 0.25, 1.0, lower)              # 前檐下矮墙
    for x in (-w / 2 + 0.3, -w / 6, w / 6, w / 2 - 0.5):                       # 铺面立柱（烧焦）
        mb.box(x, -d / 2, 1.0, x + 0.2, -d / 2 + 0.2, 3.2, "M_PR_CharWood")
    mb.box(-w / 2, -d / 2, 3.2, w / 2, -d / 2 + 0.3, 3.5, "M_PR_CharWood")       # 二层楼板梁
    if not burnt:
        mb.box(-w / 2, -d / 2, 3.5, w / 2, -d / 2 + 0.25, h, wall)
        for cx in (-1.6, 0.0, 1.6):
            mb.box(cx - 0.5, -d / 2 - 0.02, 4.2, cx + 0.5, -d / 2 + 0.01, 5.2, "M_PR_Char")      # 窗洞熏黑
    else:
        mb.prism([(-w / 2, 3.5), (w / 2, 3.5), (w / 2, 4.3), (1.2, 5.1), (-0.4, 4.0), (-1.8, 4.9), (-w / 2, 4.1)],
                 "y", -d / 2, -d / 2 + 0.25, wall)


def build_fire_shop():
    """燃烧铺面（街尾火场）：State_Burning（正在烧：屋顶半塌、火挂点）与 State_Burnt（烧尽：只剩焦壳、梁柱倒地、瓦砾）。"""
    for state, burnt in (("State_Burning", False), ("State_Burnt", True)):
        mb = K.MB()
        shop_shell(mb, burnt=burnt)
        if not burnt:
            mb.prism([(-3.1, 6.2), (3.1, 6.2), (3.1, 6.6), (0.6, 7.4), (-1.0, 6.4)], "y", -2.8, 2.8, "M_Roof_Tile")
            with mb.at(-1.5, 0, 3.5, ry=-28):                                  # 一根正在塌的檩条
                mb.box(-0.1, -2.6, 0, 0.1, 2.6, 0.22, "M_PR_CharWood")
        else:
            for x, rz, rx in ((-1.4, 15, 0), (0.6, -40, 8), (1.8, 70, -6)):     # 倒地梁柱
                with mb.at(x, -0.4, 0.15, rz=rz, rx=rx):
                    mb.box(-0.12, -2.2, 0, 0.12, 2.2, 0.24, "M_PR_CharWood")
            for k in range(26):                                               # 瓦砾/焦木堆
                x = -2.6 + (k * 0.97) % 5.2
                y = -2.2 + (k * 1.31) % 4.2
                s = 0.15 + (k % 4) * 0.08
                mb.box(x - s, y - s * 0.7, 0.3, x + s, y + s * 0.7, 0.3 + s * 0.8, "M_PR_Rubble" if k % 3 else "M_Roof_Tile")
        obj(mb, state, (0, 0, 0), uv=2.0)
    # 门前地上的焦木与碎瓦（两种状态共用）
    mb = K.MB()
    for k in range(14):
        x = -2.8 + (k * 0.43) % 5.6
        y = -3.9 + (k * 0.71) % 1.3
        with mb.at(x, y, 0, rz=k * 37):
            mb.box(-0.4 + 0.02 * k, -0.06, 0, 0.4, 0.06, 0.1, "M_PR_CharWood" if k % 2 else "M_Roof_Tile")
    obj(mb, "Debris_Front", (0, 0, 0), uv=2.0)
    for i, p in enumerate(((-1.6, -2.2, 2.0), (1.4, -1.8, 3.5), (0.2, 0.5, 5.6))):
        fx(f"FX_Fire_{i + 1}", p)
    fx("FX_Smoke", (0.0, 0.0, 6.8))


def build_ruin(kind):
    """被炸铺面三种：A 断墙转角 + 瓦砾，B 屋顶塌落（梁斜插、瓦片散落），C 弹坑 + 碎石。"""
    mb = K.MB()
    if kind == "A":
        mb.box(-3.0, 1.6, 0, 1.6, 1.9, 0.3, "M_Stone_Base")
        mb.prism([(-3.0, 0.3), (1.6, 0.3), (1.6, 1.4), (0.4, 2.6), (-0.8, 1.6), (-1.9, 3.4), (-3.0, 3.1)], "y", 1.6, 1.9, "M_Plaster")
        mb.prism([(1.6, 0.3), (-1.6, 0.3), (-1.6, 2.2), (0.2, 1.3), (1.6, 1.8)], "x", 1.3, 1.6, "M_Plaster")
        for k in range(22):
            x = -2.6 + (k * 0.83) % 4.2
            y = -1.4 + (k * 1.17) % 2.8
            s = 0.12 + (k % 5) * 0.07
            mb.box(x - s, y - s, 0, x + s, y + s * 0.8, s * 1.1, "M_PR_Rubble" if k % 3 else "M_Plaster")
    elif kind == "B":
        for sx in (-1, 1):
            mb.box(sx * 2.6 - 0.15, -2.0, 0, sx * 2.6 + 0.15, 2.0, 2.4 if sx < 0 else 1.2, "M_Plaster")
        for x, ry, rz in ((-1.2, 32, 8), (0.3, -24, -6), (1.4, 40, 14)):
            with mb.at(x, 0, 0.6, ry=ry, rz=rz):
                mb.box(-0.1, -2.3, 0, 0.1, 2.3, 0.2, "M_PR_CharWood")
        with mb.at(-0.6, 0.3, 0.2, ry=-14):
            mb.box(-1.8, -1.6, 0, 1.6, 1.4, 0.12, "M_Roof_Tile")
        for k in range(30):
            x = -2.2 + (k * 0.61) % 4.4
            y = -2.4 + (k * 0.93) % 4.6
            with mb.at(x, y, 0, rz=k * 29):
                mb.box(-0.14, -0.1, 0, 0.14, 0.1, 0.03, "M_Roof_Tile")
    else:
        segs = 14
        for i in range(segs):                                                  # 弹坑：外翻土沿 + 坑底
            a0, a1 = 2 * math.pi * i / segs, 2 * math.pi * (i + 1) / segs
            r0, r1, r2 = 0.9, 1.7, 2.3
            p = lambda r, a, z: (r * math.cos(a), r * math.sin(a), z)
            b = mb.addv([p(r0, a0, -0.02), p(r0, a1, -0.02), p(r1, a1, 0.35), p(r1, a0, 0.35)])
            mb.face([b, b + 1, b + 2, b + 3], "M_Mud")
            b = mb.addv([p(r1, a0, 0.35), p(r1, a1, 0.35), p(r2, a1, 0.0), p(r2, a0, 0.0)])
            mb.face([b, b + 1, b + 2, b + 3], "M_Mud")
        mb.cyl(0, 0, -0.04, -0.02, 0.92, "M_Mud", seg=segs)
        for k in range(16):
            a = k * 2.3
            r = 1.9 + (k % 4) * 0.35
            with mb.at(r * math.cos(a), r * math.sin(a), 0, rz=k * 41):
                mb.box(-0.2, -0.12, 0, 0.2, 0.12, 0.15 + (k % 3) * 0.06, "M_Road_Stone" if k % 2 else "M_PR_Rubble")
    obj(mb, f"Ruin_{kind}", (0, 0, 0), uv=2.0)


def build_stall(kind):
    """商贩摊三种：Veg 菜摊（矮桌+筐+布棚），Snack 小吃摊（炉灶+锅+蒸笼+条凳），Goods 杂货（货架+坛罐+秤）。"""
    mb = K.MB()
    # 共用：四根竹竿撑一块布棚
    for sx in (-1, 1):
        for sy in (-1, 1):
            mb.cyl(sx * 1.1, sy * 0.8, 0, 2.3 if sy > 0 else 2.0, 0.03, "M_PR_Bamboo", seg=6)
    mb.hexa([(-1.25, -0.95, 1.98), (1.25, -0.95, 1.98), (1.25, 0.95, 2.28), (-1.25, 0.95, 2.28),
             (-1.25, -0.95, 2.0), (1.25, -0.95, 2.0), (1.25, 0.95, 2.3), (-1.25, 0.95, 2.3)], "M_PR_Canvas")
    if kind == "Veg":
        mb.box(-1.0, -0.6, 0.45, 1.0, 0.6, 0.5, "M_PR_Wood")
        for sx in (-1, 1):
            for sy in (-1, 1):
                mb.box(sx * 0.95 - 0.03, sy * 0.55 - 0.03, 0, sx * 0.95 + 0.03, sy * 0.55 + 0.03, 0.45, "M_PR_WoodDark")
        for k, x in enumerate((-0.65, 0.0, 0.65)):
            mb.cyl(x, 0.0, 0.5, 0.68, 0.26, "M_PR_Bamboo", seg=10, r_top=0.3)
            mb.cyl(x, 0.0, 0.66, 0.74, 0.27, "M_PR_Greens" if k != 1 else "M_PR_Fruit", seg=10, r_top=0.18)
        mb.cyl(1.4, -0.3, 0, 0.3, 0.22, "M_PR_Bamboo", seg=10, r_top=0.25)
    elif kind == "Snack":
        mb.box(-1.0, -0.4, 0, -0.2, 0.4, 0.75, "M_Brick_Grey")                   # 炉灶
        mb.cyl(-0.6, 0.0, 0.75, 0.9, 0.32, "M_PR_Steel", seg=12, r_top=0.36)   # 铁锅
        mb.cyl(-0.85, 0.3, 0.75, 1.6, 0.06, "M_Brick_Grey", seg=6)               # 烟囱
        for k in range(3):                                                    # 蒸笼
            mb.cyl(0.5, 0.0, 0.5 + k * 0.12, 0.6 + k * 0.12, 0.28, "M_PR_Bamboo", seg=12)
        mb.box(0.1, -0.4, 0.45, 0.9, 0.4, 0.5, "M_PR_Wood")
        for sx in (0.15, 0.85):
            mb.box(sx - 0.03, -0.35, 0, sx + 0.03, 0.35, 0.45, "M_PR_WoodDark")
        mb.box(-0.8, -1.3, 0.4, 0.8, -1.1, 0.45, "M_PR_Wood")                    # 条凳
        for x in (-0.7, 0.7):
            mb.box(x - 0.03, -1.27, 0, x + 0.03, -1.13, 0.4, "M_PR_WoodDark")
        fx("FX_StoveSmoke", (-0.85, 0.3, 1.7))
    else:
        for z in (0.0, 0.6, 1.2):                                              # 三层货架
            mb.box(-1.0, 0.3, z, 1.0, 0.75, z + 0.05, "M_PR_Wood")
        for sx in (-1, 1):
            mb.box(sx * 1.0 - 0.04, 0.3, 0, sx * 1.0 + 0.04, 0.75, 1.3, "M_PR_WoodDark")
        for k in range(9):
            x = -0.8 + (k % 3) * 0.75
            z = 0.05 + (k // 3) * 0.6
            mb.cyl(x, 0.52, z, z + 0.35 - (k % 2) * 0.1, 0.13, "M_PR_Jar" if k % 2 else "M_PR_JarGlaze", seg=8, r_top=0.09)
        mb.box(-0.9, -0.6, 0.7, 0.9, -0.1, 0.75, "M_PR_Wood")
        for sx in (-0.85, 0.85):
            mb.box(sx - 0.03, -0.55, 0, sx + 0.03, -0.15, 0.7, "M_PR_WoodDark")
        mb.box(-0.5, -0.5, 0.75, -0.1, -0.2, 0.95, "M_PR_Sack")
    obj(mb, f"Stall_{kind}", (0, 0, 0), uv=1.0)


def build_notice_wall():
    """告示墙：一段矮墙贴满告示/布告（1941 街市），墙头盖瓦。"""
    mb = K.MB()
    mb.box(-1.6, -0.15, 0, 1.6, 0.15, 2.2, "M_Plaster")
    mb.box(-1.7, -0.25, 2.2, 1.7, 0.25, 2.35, "M_Roof_Tile")
    for k, (x, z, w, hh) in enumerate(((-1.2, 0.9, 0.6, 0.8), (-0.4, 1.1, 0.5, 0.7), (0.3, 0.8, 0.7, 0.9), (1.1, 1.2, 0.4, 0.55),
                                        (-0.9, 0.3, 0.5, 0.45))):
        mb.box(x - w / 2, -0.165, z, x + w / 2, -0.15, z + hh, "M_PR_Paper" if k % 2 else "M_PR_FlagPale")
        for r in range(3):
            mb.box(x - w / 2 + 0.06, -0.17, z + hh - 0.15 - r * 0.15, x + w / 2 - 0.06, -0.165, z + hh - 0.12 - r * 0.15, "M_PR_Ink")
    obj(mb, "NoticeWall", (0, 0, 0), uv=1.0)


def build_postbox():
    """邮筒：墨绿圆筒 + 圆顶 + 投信口。"""
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.1, 0.24, "M_Stone_Base", seg=10)
    mb.cyl(0, 0, 0.1, 1.15, 0.2, "M_PR_PostGreen", seg=12)
    mb.ico(0, 0, 1.15, 0.2, "M_PR_PostGreen", sz=0.5, subdiv=2)
    mb.box(-0.08, -0.205, 0.95, 0.08, -0.19, 0.98, "M_PR_Char")
    mb.box(-0.1, -0.205, 0.6, 0.1, -0.195, 0.8, "M_PR_FlagPale")
    obj(mb, "Postbox", (0, 0, 0), uv=1.0)


def build_street_lamp():
    """路灯：铁杆 + 弯臂 + 纸灯笼罩（1941 江南小镇）。FX_Lamp 为灯光挂点。"""
    mb = K.MB()
    mb.cyl(0, 0, 0, 0.3, 0.12, "M_Stone_Base", seg=8)
    mb.cyl(0, 0, 0.3, 3.3, 0.04, "M_PR_Steel", seg=6)
    mb.box(-0.02, -0.02, 3.2, 0.02, -0.7, 3.24, "M_PR_Steel")
    mb.box(-0.004, -0.66, 2.9, 0.004, -0.64, 3.2, "M_PR_Steel")
    mb.cyl(0, -0.65, 2.5, 2.9, 0.14, "M_PR_Lantern", seg=8, r_top=0.12)
    mb.cyl(0, -0.65, 2.88, 2.95, 0.15, "M_PR_Steel", seg=8, r_top=0.05)
    obj(mb, "StreetLamp", (0, 0, 0), uv=1.0)
    fx("FX_Lamp", (0, -0.65, 2.7))


def build_bollard():
    """石墩一对（路口/桥头）。"""
    mb = K.MB()
    for x in (-0.8, 0.8):
        mb.box(x - 0.18, -0.18, 0, x + 0.18, 0.18, 0.55, "M_Wall_Stone")
        mb.prism([(x - 0.18, 0.55), (x + 0.18, 0.55), (x, 0.7)], "y", -0.18, 0.18, "M_Wall_Stone")
    obj(mb, "Bollards", (0, 0, 0), uv=1.0)


def build_bamboo_baskets():
    """竹筐/竹篓一堆：三只叠放 + 一只倒扣。"""
    mb = K.MB()
    for x, y, z, r, h in ((0, 0, 0, 0.3, 0.4), (0.62, 0.1, 0, 0.26, 0.36), (0.3, 0.05, 0.38, 0.25, 0.34)):
        mb.cyl(x, y, z, z + h, r * 0.85, "M_PR_Bamboo", seg=10, r_top=r)
    mb.cyl(-0.6, -0.2, 0, 0.35, 0.3, "M_PR_Bamboo", seg=10, r_top=0.24)
    obj(mb, "Baskets", (0, 0, 0), uv=1.0)


def build_checkpoint():
    """哨卡道具：弧形沙袋墙、两架拒马、一根横杆路障（Barrier，可抬起）。日军旗另见 PROP_Flag_Japan。"""
    mb = K.MB()
    for row in range(4):                                                     # 沙袋墙（错缝四层）
        for i in range(9):
            a = math.radians(-50 + i * 12.5 + (6 if row % 2 else 0))
            x, y = 2.2 * math.sin(a), -2.2 * math.cos(a) + 2.2
            with mb.at(x, y, row * 0.22, rz=math.degrees(a)):
                mb.box(-0.3, -0.18, 0, 0.3, 0.18, 0.22, "M_PR_Sandbag")
    obj(mb, "Sandbags", (0, 0, 0), uv=1.0)
    for nm, x in (("Cheval_1", -3.6), ("Cheval_2", 3.6)):                        # 拒马：横木 + X 形支腿
        mb = K.MB()
        with mb.at(0, 0, 0.55, ry=90):
            mb.cyl(0, 0, -1.2, 1.2, 0.07, "M_PR_Wood", seg=6)
        for k in range(5):
            xx = -1.0 + k * 0.5
            for a in (40, -40):
                with mb.at(xx, 0, 0.55, rx=a):
                    mb.box(-0.03, -0.03, -0.75, 0.03, 0.03, 0.75, "M_PR_WoodDark")
        mb.box(-1.1, -0.01, 0.5, 1.1, 0.01, 0.52, "M_PR_Steel")                    # 铁丝
        obj(mb, nm, (x, -1.0, 0), uv=1.0)
    mb = K.MB()
    mb.box(-0.15, -0.15, 0, 0.15, 0.15, 1.0, "M_PR_WoodDark")
    obj(mb, "Barrier_Post", (-2.6, -2.4, 0), uv=1.0)
    mb = K.MB()
    mb.box(0.0, -0.05, -0.05, 4.8, 0.05, 0.05, "M_PR_FlagWhite")
    for k in range(5):
        mb.box(0.4 + k * 0.9, -0.055, -0.055, 0.85 + k * 0.9, 0.055, 0.055, "M_PR_Hinomaru")
    obj(mb, "Barrier", (-2.6, -2.4, 0.95), uv=1.0)


# ---------------------------------------------------------------- 注册
def recipes():
    R = {
        "PROP_Genealogy": ("Props", build_genealogy),
        "PROP_JapanesePlane": ("Props", build_plane),
        "PROP_FallenFlag": ("Props", build_fallen_flag),
        "PROP_IncenseSet": ("Props", build_incense_set),
        "PROP_Camera_1941": ("Props", build_camera),
        "PROP_JpRifle": ("Props", build_rifle),
        "PROP_JpSword": ("Props", build_sword),
        "PROP_JpAmmoBox": ("Props", build_ammo_box),
        "PROP_VendorGoods": ("Props", build_vendor_goods),
        "PROP_Banner_Shrine": ("Props", build_banner_shrine),
        "PROP_Banner_Street": ("Props", build_banner_street),
        "PROP_Flag_Japan": ("Props", build_flag_japan),
        "PROP_Door_Loot": ("Props", build_door_loot),
        "PROP_Tablet_Father": ("Props", build_tablet_father),
        "PROP_FatherPhoto": ("Props", build_father_photo),
        "PROP_NoticeWall": ("Props", build_notice_wall),
        "PROP_Postbox": ("Props", build_postbox),
        "PROP_StreetLamp": ("Props", build_street_lamp),
        "PROP_Bollards": ("Props", build_bollard),
        "PROP_BambooBaskets": ("Props", build_bamboo_baskets),
        "ENV_Fire_Shop": ("Environments", build_fire_shop),
        "ENV_Checkpoint_Props": ("Environments", build_checkpoint),
    }
    for k in ("A", "B", "C"):
        R[f"ENV_Ruin_{k}"] = ("Environments", (lambda kk=k: build_ruin(kk)))
    for k in ("Veg", "Snack", "Goods"):
        R[f"ENV_VendorStall_{k}"] = ("Environments", (lambda kk=k: build_stall(kk)))
    return R
