"""
《入谱》第二幕 · 沙盘补缺口（Docs/第二幕_策划对照与建模缺口.md §3、§5 P0 沙盘行）
（Blender bpy；build_yongchang.py 在 rupu_act2 之后导入本模块，recipes() 里的同名配方覆盖 rupu_act2 的）

本模块做两件 rupu_act2 里没有的事，几何本身仍由 rupu_act2 的沙盘函数生成：
  - ENV_SandTable：生成后再程序化出积灰遮罩 T_SandTable_Dust_Mask.png（1941/1945 皮肤用，团结侧见 RupuSandSkins.cs）。
  - PROP_Sand_Flags：议题纸卡 Card_Wall / Card_Tower / Card_Water / Card_House 换成贴图纸卡。
    贴图 T_SandCard_<议题>_D.png 用 Blender 文字（宋体，竖排右起）+ Workbench 平光渲出，再 numpy 做旧纸纹；
    同一张贴图 A 也可以直接当 UI 用（1024 方图，版面见 CARD_LAYOUT）。
"""
import math
import os

import bpy

import rupu_kit as K
import rupu_act2 as A2

REPO = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
SONGTI = "/System/Library/Fonts/Supplemental/Songti.ttc"

K.PALETTE.update({
    "M_A2_TexInk": "#1e1a16", "M_A2_TexRed": "#a03a28", "M_A2_TexPaper": "#e8dcc8", "M_A2_TexRule": "#6a5a48",
})

# ====================================================================== 纸卡内容（策划案 §4.1、§4.3、§5 提炼）
# 每张：标题 + 甲乙两个选项（主列：选项与一句说明；副列：代价/回报）+ 一句代价（朱字）。竖排右起，全角空格断词。
SAND_CARD_TEXT = {
    "Wall": dict(title="城墙走向",
                 a=("贴河　护码头水门", "堡防加一　银二百两"),
                 b=("靠山　护田与粮道", "民心加一　银一百两"),
                 cost="墙走哪边　哪边就要拆屋"),
    "Tower": dict(title="敌台",
                  a=("东台　对海口", "炮口向海　防倭船"),
                  b=("北台　对官道", "箭楼当道　防陆路"),
                  cost="银只够筑一座台"),
    "Water": dict(title="水门",
                  a=("开闸　通舟楫运石", "工期少一天"),
                  b=("闭闸　防内应", "民心加一"),
                  cost="门开着方便人　也方便贼"),
    "House": dict(title="王宅",
                  a=("圈进墙内", "银三百两　工期加一天"),
                  b=("留在墙外", "宅子从此在墙外头"),
                  cost="推一下　就是三百两"),
}
# 版面（贴图坐标 x∈[-0.5,0.5] 右为 +；UI 用 u = x + 0.5）：各列中心 x
CARD_LAYOUT = dict(title=0.355, rule1=0.268, a_main=0.19, a_sub=0.105, rule2=0.03, b_main=-0.05, b_sub=-0.135,
                   rule3=-0.215, cost=-0.30)
CARD_SIZE = 0.09          # 3D 纸卡边长（米）


def _font():
    for p in (SONGTI, "/System/Library/Fonts/Songti.ttc"):
        if os.path.exists(p):
            try:
                return bpy.data.fonts.load(p, check_existing=True)
            except Exception:
                pass
    return None


def _smooth_noise(np, rng, n, size, periodic=False):
    """值噪声（n 格、size 像素）；periodic=True 时首尾相接，可平铺。"""
    g = rng.random((n + 1, n + 1))
    if periodic:
        g[n, :] = g[0, :]
        g[:, n] = g[:, 0]
    t = np.linspace(0, n, size, endpoint=False)
    i = t.astype(int)
    f = t - i
    f = f * f * (3 - 2 * f)
    a, b, c, d = g[i][:, i], g[i][:, i + 1], g[i + 1][:, i], g[i + 1][:, i + 1]
    fy, fx = f[:, None], f[None, :]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def _save_rgba(np, arr, name, path):
    """arr: (H, W, 4) float，行 0 在图像底部（Blender 约定）。"""
    H, W = arr.shape[:2]
    img = bpy.data.images.get(name) or bpy.data.images.new(name, W, H, alpha=True)
    if tuple(img.size) != (W, H):
        img.scale(W, H)
    img.pixels.foreach_set(np.clip(arr, 0, 1).astype(np.float32).reshape(-1))
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return img


# ====================================================================== 纸卡贴图
def render_card_tex(key, path, size=1024):
    """Workbench 平光渲出纸卡（竖排右起），再 numpy 做旧：纤维、云斑、四边泛黄、朱字略晕。"""
    import numpy as np
    spec = SAND_CARD_TEXT[key]
    L = CARD_LAYOUT
    sc = bpy.data.scenes.new("A2_CardScene")
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "FLAT"
    sc.display.shading.color_type = "MATERIAL"
    sc.display.shading.show_shadows = False
    sc.display.shading.show_cavity = False
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x = sc.render.resolution_y = size
    sc.render.resolution_percentage = 100
    sc.render.film_transparent = False
    sc.render.image_settings.file_format = "PNG"
    sc.render.image_settings.color_mode = "RGB"
    made, curves = [], []

    def link(ob):
        sc.collection.objects.link(ob)
        made.append(ob)
        return ob
    cd = bpy.data.cameras.new("A2_CardCam")
    cd.type = "ORTHO"
    cd.ortho_scale = 1.0
    cam = link(bpy.data.objects.new("A2_CardCam", cd))
    cam.location = (0, 0, 5)
    sc.camera = cam

    def quad(x0, y0, x1, y1, mat, z=0.0):
        mb = K.MB()
        mb.box(x0, y0, z - 0.001, x1, y1, z, mat)
        made.append(mb.to_object("A2_CardQuad", collection=sc.collection))
    font = _font()

    def column(s, x, top, sz, mat, gap=1.0):
        """竖排一列：每个字一个文字物体，逐字往下排（字距 = sz * gap），全角空格占半格。"""
        y = top
        for ch in s:
            if ch in " 　":
                y -= sz * 0.5 * gap
                continue
            if font is None:
                quad(x - sz * 0.4, y - sz * 0.9, x + sz * 0.4, y - sz * 0.1, mat, z=0.001)
            else:
                cu = bpy.data.curves.new("A2_CardText", "FONT")
                curves.append(cu)
                cu.body = ch
                cu.font = font
                cu.size = sz
                cu.align_x = "CENTER"
                cu.align_y = "TOP"
                ob = link(bpy.data.objects.new("A2_CardText", cu))
                ob.location = (x, y, 0.002)
                ob.data.materials.append(K.get_mat(mat))
            y -= sz * gap
        return y

    def vrule(x, y0, y1, w=0.003, mat="M_A2_TexRule"):
        quad(x - w / 2, y0, x + w / 2, y1, mat, z=0.001)

    quad(-0.6, -0.6, 0.6, 0.6, "M_A2_TexPaper", z=-0.01)
    m = 0.04                                         # 双线边框
    for (a, b, c_, d) in ((-0.5 + m, 0.5 - m - 0.007, 0.5 - m, 0.5 - m), (-0.5 + m, -0.5 + m, 0.5 - m, -0.5 + m + 0.007),
                          (-0.5 + m, -0.5 + m, -0.5 + m + 0.007, 0.5 - m), (0.5 - m - 0.007, -0.5 + m, 0.5 - m, 0.5 - m)):
        quad(a, b, c_, d, "M_A2_TexInk", z=0.001)
    m2 = m + 0.018
    for (a, b, c_, d) in ((-0.5 + m2, 0.5 - m2 - 0.0025, 0.5 - m2, 0.5 - m2), (-0.5 + m2, -0.5 + m2, 0.5 - m2, -0.5 + m2 + 0.0025),
                          (-0.5 + m2, -0.5 + m2, -0.5 + m2 + 0.0025, 0.5 - m2), (0.5 - m2 - 0.0025, -0.5 + m2, 0.5 - m2, 0.5 - m2)):
        quad(a, b, c_, d, "M_A2_TexInk", z=0.001)
    top, bot = 0.4, -0.4
    # 标题（大字，右起第一列）
    tsz = min(0.105, 0.74 / max(1, len(spec["title"])))
    column(spec["title"], L["title"], top + 0.005, tsz, "M_A2_TexInk", gap=1.08)
    for k in ("rule1", "rule2", "rule3"):
        vrule(L[k], bot, top)
    # 甲 / 乙：顶上一方朱印字，下接主列（大）+ 副列（小）
    for tag, (main, sub), xm, xs in (("甲", spec["a"], L["a_main"], L["a_sub"]), ("乙", spec["b"], L["b_main"], L["b_sub"])):
        quad(xm - 0.036, top - 0.072, xm + 0.036, top, "M_A2_TexRed", z=0.0012)
        quad(xm - 0.029, top - 0.065, xm + 0.029, top - 0.007, "M_A2_TexPaper", z=0.0014)
        column(tag, xm, top - 0.008, 0.056, "M_A2_TexRed")
        msz = min(0.07, 0.68 / max(1, len(main) - 0.5 * main.count("　")))
        column(main, xm, top - 0.095, msz, "M_A2_TexInk", gap=1.02)
        ssz = min(0.05, 0.7 / max(1, len(sub) - 0.5 * sub.count("　")))
        column(sub, xs, top - 0.04, ssz, "M_A2_TexInk", gap=1.05)
    # 代价（朱字，最左一列）
    csz = min(0.055, 0.76 / max(1, len(spec["cost"]) - 0.5 * spec["cost"].count("　")))
    column(spec["cost"], L["cost"], top - 0.02, csz, "M_A2_TexRed", gap=1.04)
    # 左下角一方小印「祠」
    quad(-0.43, -0.43, -0.355, -0.355, "M_A2_TexRed", z=0.0012)
    column("祠", -0.3925, -0.36, 0.055, "M_A2_TexPaper")

    sc.render.filepath = path
    bpy.ops.render.render(write_still=True, scene=sc.name)
    for o in made:
        bpy.data.objects.remove(o, do_unlink=True)
    for cu in curves:
        if cu.users == 0:
            bpy.data.curves.remove(cu)
    bpy.data.cameras.remove(cd)
    bpy.data.scenes.remove(sc)

    # ---- 做旧
    img = bpy.data.images.load(path, check_existing=False)
    Wd, Hd = img.size
    px = np.empty(Wd * Hd * 4, dtype=np.float32)
    img.pixels.foreach_get(px)
    a = px.reshape(Hd, Wd, 4)
    rgb = a[:, :, :3].astype(np.float64)
    rng = np.random.default_rng({"Wall": 41, "Tower": 43, "Water": 47, "House": 53}[key])
    fiber = rng.random((Hd, Wd)) * 0.05 - 0.025
    streak = np.repeat((rng.random((1, Wd)) - 0.5) * 0.03, Hd, axis=0)               # 竖向纸筋
    blot = _smooth_noise(np, rng, 7, Hd)
    yy, xx = np.mgrid[0:Hd, 0:Wd]
    edge = np.minimum(np.minimum(xx, Wd - 1 - xx), np.minimum(yy, Hd - 1 - yy)) / (Wd * 0.5)
    age = np.clip(0.16 - edge, 0, 0.16) / 0.16
    tint = np.array([0.0, -0.03, -0.08])
    rgb = rgb + (fiber + streak)[:, :, None] + (blot[:, :, None] - 0.5) * 0.07 + age[:, :, None] * (tint - 0.07)
    a[:, :, :3] = np.clip(rgb, 0, 1)
    a[:, :, 3] = 1.0
    img.pixels.foreach_set(a.reshape(-1).astype(np.float32))
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    return img


def card_material(key, img):
    mat = bpy.data.materials.new(f"M_A2_Card_{key}")
    mat.use_nodes = True
    nt = mat.node_tree
    bsdf = next(n for n in nt.nodes if n.type == "BSDF_PRINCIPLED")
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = img
    nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    bsdf.inputs["Roughness"].default_value = 0.92
    mat.diffuse_color = K.hex_rgba("#e8dcc8")
    return mat


def card_mesh(name, mat, s=CARD_SIZE, n=5, t=0.0006):
    """纸卡：正面 n×n 格（UV 0..1 正好铺满贴图，u→+X、v→+Y，从 -Y 看字是正的），四角微翘；背面与四边用 M_A2_Paper。
    原点在卡底面中心，平放。"""
    import bmesh
    me = bpy.data.meshes.new(name)
    me.materials.append(mat)
    me.materials.append(K.get_mat("M_A2_Paper"))
    bm = bmesh.new()
    uv = bm.loops.layers.uv.verify()

    def lift(u, v):
        return 0.0012 * ((2 * u - 1) ** 2) * ((2 * v - 1) ** 2)
    top, btm = {}, {}
    for i in range(n + 1):
        for j in range(n + 1):
            u, v = i / n, j / n
            x, y = (u - 0.5) * s, (v - 0.5) * s
            top[i, j] = bm.verts.new((x, y, t + lift(u, v)))
            btm[i, j] = bm.verts.new((x, y, lift(u, v)))
    rev = {vv: k for k, vv in top.items()}
    for i in range(n):
        for j in range(n):
            f = bm.faces.new((top[i, j], top[i + 1, j], top[i + 1, j + 1], top[i, j + 1]))
            f.material_index = 0
            for lp in f.loops:
                ii = rev[lp.vert]
                lp[uv].uv = (ii[0] / n, ii[1] / n)
            f = bm.faces.new((btm[i, j + 1], btm[i + 1, j + 1], btm[i + 1, j], btm[i, j]))
            f.material_index = 1
    ring = [(i, 0) for i in range(n)] + [(n, j) for j in range(n)] + [(i, n) for i in range(n, 0, -1)] + [(0, j) for j in range(n, 0, -1)]
    for k in range(len(ring)):
        a, b = ring[k], ring[(k + 1) % len(ring)]
        f = bm.faces.new((btm[a], btm[b], top[b], top[a]))
        f.material_index = 1
        for lp in f.loops:
            lp[uv].uv = (0.0, 0.0)
    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    for p in me.polygons:
        p.use_smooth = False
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    return ob


def build_cards(x):
    out_dir = os.path.join(REPO, "Project_rupu", "Assets", "Art", "Props", "PROP_Sand_Flags")
    os.makedirs(out_dir, exist_ok=True)
    for key in A2.SAND_CARDS:
        img = render_card_tex(key, os.path.join(out_dir, f"T_SandCard_{key}_D.png"))
        ob = card_mesh(f"Card_{key}", card_material(key, img))
        ob.location = (x + 0.06, 0, 0)
        x += 0.11
    return x


def build_sand_flags():
    x = A2.build_sand_flags()
    build_cards(x)


# ====================================================================== 积灰遮罩
def make_dust_mask(path, size=1024):
    """1941 积灰遮罩（可平铺）：大片落灰（低频 fbm）+ 细碎起伏 + 细尘点。
    RGB = A = 积灰量（1 = 厚灰）。团结 URP Lit 的 Detail Mask 读 A 通道，其他着色器读 R 也行。"""
    import numpy as np
    rng = np.random.default_rng(1941)
    f = np.zeros((size, size))
    for n, w in ((4, 0.45), (8, 0.25), (16, 0.15), (32, 0.08), (64, 0.05)):
        f += _smooth_noise(np, rng, n, size, periodic=True) * w
    f = (f - f.min()) / (f.max() - f.min())
    m = np.clip((f - 0.12) / 0.76, 0, 1)
    m = m * m * (3 - 2 * m)
    fine = _smooth_noise(np, rng, 48, size, periodic=True) - 0.5                         # 灰面细碎起伏
    m = np.clip(m + fine * 0.18, 0, 1)
    speck = rng.random((size, size))
    m = np.clip(m + (speck > 0.99) * 0.2 - (speck < 0.004) * 0.15, 0, 1)                   # 细尘点 / 落灰缺点
    m = 0.25 + 0.75 * m                                                                   # 到处都有一层薄灰
    arr = np.stack([m, m, m, m], axis=2)
    return _save_rgba(np, arr, "T_SandTable_Dust_Mask", path)


def build_sandtable():
    A2.build_sandtable()
    out_dir = os.path.join(REPO, "Project_rupu", "Assets", "Art", "Environments", "ENV_SandTable")
    os.makedirs(out_dir, exist_ok=True)
    make_dust_mask(os.path.join(out_dir, "T_SandTable_Dust_Mask.png"))


def recipes():
    return {
        "ENV_SandTable": ("Environments", build_sandtable),
        "PROP_Sand_Flags": ("Props", build_sand_flags),
    }
