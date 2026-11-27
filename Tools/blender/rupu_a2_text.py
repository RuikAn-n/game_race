"""
《入谱》第二幕 · 文字贴图：族约碑碑文 + 凿碑三态、族约木牌、义师名录（30 名 × 4 段书写）、印文、匾额、旗面、灯面
（Blender bpy；由 build_yongchang.py 在 rupu_act2 / rupu_ming_civic 之后导入，recipes() 里同名配方覆盖原配方 = 「包装配方」）

对应 Docs/第二幕_策划对照与建模缺口.md §5 P0「族约碑」「义师名录」「文字贴图」、§9 第五步 1/3/4。文档见 Docs/act2_text.md。

做法：
  - 文字贴图：临时场景里用 Blender 文字对象（宋体，只烘进贴图，不分发字体文件）+ Workbench 平光渲出黑白/分通道遮罩，
    再用 numpy 合成底色（石纹、纸纹、木纹、漆面）、凿刻斜光、墨色、做旧。设计坐标 = 贴图所在表面的真实米数，
    贴图都是方形 PNG（1024/2048），非方形表面在贴图里横/竖向拉伸，贴回表面后字是方的。
  - 包装：先调用原配方（不改 rupu_act2.py / rupu_ming_civic.py 源码），再按材质 + 位置找到匾/旗/纸面，
    在正面外 2–5 mm 加贴字面片（NOCOL_TXT_*，挂在原物体下）；需要切换状态的部件（碑文、名录墨行）用固定名字的子物体。
  - 原配方从 build_yongchang 当前的 RECIPES 里取（若前面的模块已包装过同名资产，就接着包装，不会把它覆盖掉）。

单独运行（出文档预览图，读已生成的 .blend）：
  Blender -b --factory-startup -P Tools/blender/rupu_a2_text.py -- --shots Docs/images/act2
"""
import math
import os
import sys

import bpy
import bmesh
from mathutils import Vector

HERE = os.path.dirname(os.path.abspath(__file__))
if HERE not in sys.path:
    sys.path.insert(0, HERE)

import rupu_kit as K           # noqa: E402

REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
ART = os.path.join(REPO, "Project_rupu", "Assets", "Art")
TMP = os.path.join(REPO, "Builds", "tmp", "a2_text")
FONT_PATH = "/System/Library/Fonts/Supplemental/Songti.ttc"

K.PALETTE.update({"M_A2T_Wood": "#6b4a32", "M_A2T_WoodDark": "#3e2c20", "M_A2T_Iron": "#3a3a3a", "M_A2T_Stone": "#8a877e"})


# ====================================================================== 内容（文言、竖排右起；繁体，与明代匾额碑刻一致）
STELE_TITLE = "王氏族約"
STELE_PREAMBLE = ["倭患日亟闔族築堡以衛桑梓", "約成刻石子孫世守毋敢有違"]
STELE_DATE = "嘉靖三十九年春王氏合族公立"
# 策划案 §6 六条（顺序 = clause id 1..6，供 clause_term_1..3 取值）
CLAUSES = [
    ("助築者免徭役三年", "助筑者免徭役三年"),
    ("守城死者祠中留名", "守城死者，祠中留名"),
    ("三更後不得開城門", "三更后不得开城门"),
    ("鹽場歸公牙行不得抽", "盐场归公，牙行不得抽"),
    ("寇至婦孺先撤入祠", "寇至，妇孺先撤入祠（妇孺先撤）"),
    ("匠人日給雙糧", "匠人日给双粮"),
]
# 族约十章木牌：1–6 = 上面六条（可选），7–10 是不上碑的其余四章
COVENANT_EXTRA = [("敬祖宗睦族人", "敬祖宗，睦族人"), ("子弟勤耕讀", "子弟勤耕读"), ("禁賭博鬥毆", "禁赌博斗殴"),
                  ("修譜毋遺一人", "修谱毋遗一人")]
CN_NUM = ["一", "二", "三", "四", "五", "六", "七", "八", "九", "十"]

# 义师名录 30 名：(名字, 身份, 年岁, 殁注 or None)。殁注用朱笔；「只记死者」只写有殁注的 6 人
ROSTER = [
    ("王汝明", "鄉勇", "廿四", None), ("王大順", "民夫", "三十一", None), ("王阿四", "民夫", "十九", None),
    ("王叔通", "鄉勇", "廿八", None), ("王二郎", "石匠", "四十", None), ("陳阿福", "民夫", "卅五", None),
    ("王汝良", "鄉勇", "廿二", None), ("王福", "鄉勇", "廿六", "北門歿"), ("王小乙", "民夫", "十七", "墜架歿"),
    ("王光祖", "夯匠", "卅八", None), ("林阿七", "木匠", "卅三", None), ("王汝貴", "鄉勇", "廿五", None),
    ("王三官", "民夫", "廿九", None), ("王叔遠", "鄉勇", "三十", None), ("王阿狗", "民夫", "十六", None),
    ("王長春", "鐵匠", "四十二", None), ("王汝成", "弓手", "廿三", None), ("周大", "民夫", "四十五", None),
    ("王四九", "民夫", "五十", "石壓歿"), ("王叔達", "牌手", "廿七", None), ("王細弟", "民夫", "十八", None),
    ("王汝忠", "鄉勇", "廿一", None), ("王阿保", "民夫", "卅二", None), ("王光明", "石匠", "卅六", None),
    ("王大用", "鄉勇", "廿九", None), ("黃阿三", "民夫", "二十", None), ("王五十", "民夫", "卅四", None),
    ("王汝和", "鄉勇", "廿四", "巡海歿"), ("王德", "義師", "二十", "北門歿"), ("王沛", "義師", "六十二", "北門歿"),
]
NAMELESS_SLOTS = (29, 30)       # 殉难段「护民撤祠堂」：两具遗体没抢回，只能写「無名」
ROSTER_TITLE = "永昌義師名錄"
SEAL_TEXT = "王氏宗祠"          # 2×2：右列「王氏」、左列「宗祠」

# 匾额 / 旗 / 纸面：(资产, 材质, 位置提示(x,y,z；None=不比), 内容键)
PLAQUES = {
    "BLD_MING_AncestralHall": [("M_Plaque", (0, -16.7, 4.5), "Gate", "王氏宗祠", "lacquer"),
                               ("M_Plaque", (0, -2.27, 4.75), "Hall", "追遠堂", "lacquer")],
    "BLD_MING_GateTower": [("M_Plaque", (0, -2.56, 6.0), "Gate", None, "lacquer"),        # 三门名：见 GATE_NAMES
                           ("M_Plaque", (0, -1.21, 2.75), "Inner", "永昌堡", "lacquer")],
    # 环海楼原匾（y -3.86，z ZS+2.6..ZT-0.1）正好被前面的檐枋（y -4.4..-4.1，z ZT-0.45..ZT-0.15）挡住，
    # 所以另做一块匾挂在檐枋正面（HANG：x0, x1, 背面 y, z0, z1）
    "BLD_MING_HuanhaiLou": [("HANG", (-1.5, 1.5, -4.405, 6.2, 7.1), "Gate", "環海樓", "lacquer"),
                            ("M_Flag", (12.35, 3.4, None), "Flag", "王", "flag")],
    "ENV_NorthGate_Build": [("M_Plaque", (0, -2.22, 5.0), "Closure", None, "stone_closure")],
    "ENV_WangHouse": [("M_Plaque", (0, -11.07, 3.35), "GateLintel", "世澤綿長", "lacquer"),
                      ("M_Plaque", (0, 4.09, 4.15), "Hall", "敦本堂", "lacquer"),
                      ("M_Plaque", (0, 10.56, 4.2), "ZhongTang", "清白傳家", "lacquer"),
                      ("M_Paper", (0, 10.57, 2.65), "Scroll", "守", "scroll"),
                      ("M_Paper", (1.3, 10.58, 2.7), "Couplet_R", "耕讀傳家久", "couplet"),
                      ("M_Paper", (-1.3, 10.58, 2.7), "Couplet_L", "詩書繼世長", "couplet")],
}
GATE_NAMES = [("TongShi", "通市門", "北门"), ("YingChuan", "迎川門", "南门"), ("ZhenShan", "鎮山門", "西门")]
CLOSURE_COLS = [("嘉靖庚申冬", 0.075), ("北垣合龍", 0.15), ("王氏闔族立", 0.075)]      # 合龙石：右起三列


# ====================================================================== numpy 底纹
def _np():
    import numpy as np
    return np


def hexrgb(h):
    np = _np()
    h = h.lstrip("#")
    return np.array([int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)])


def vnoise(rng, n, size):
    """n×n 格的平滑值噪声，放大到 size×size。"""
    np = _np()
    g = rng.random((n + 1, n + 1))
    t = np.linspace(0, n, size, endpoint=False)
    i = t.astype(int)
    f = t - i
    f = f * f * (3 - 2 * f)
    a, b, c, d = g[i][:, i], g[i][:, i + 1], g[i + 1][:, i], g[i + 1][:, i + 1]
    fy, fx = f[:, None], f[None, :]
    return a * (1 - fx) * (1 - fy) + b * fx * (1 - fy) + c * (1 - fx) * fy + d * fx * fy


def fbm(rng, size, octs=((3, 0.45), (9, 0.3), (27, 0.17), (81, 0.08))):
    out = sum(vnoise(rng, n, size) * w for n, w in octs)
    return out / sum(w for _, w in octs)


def streaks(rng, size, axis, length, density=1.0):
    """沿某轴拉长的纤维/木纹噪声（0 均值，首尾循环）。axis=0 沿 v（竖），1 沿 u（横）。"""
    np = _np()
    r = rng.random((size, size)) * density
    k = max(1, int(length))
    pad = np.concatenate([np.take(r, range(size - k, size), axis=axis), r], axis=axis)
    c = np.cumsum(pad, axis=axis)
    m = (np.take(c, range(k, size + k), axis=axis) - np.take(c, range(0, size), axis=axis)) / k
    return m - m.mean()


def shift(m, dx, dy):
    """平移遮罩（dx 像素向右、dy 像素向上；行 0 在底部）。"""
    np = _np()
    return np.roll(np.roll(m, dy, axis=0), dx, axis=1)


def carve(base, m, deep, dpx=2, shadow=0.2, light=0.12):
    """凿刻：遮罩 m 内填暗色，左上内沿压暗、右下内沿提亮（光从左上来）。"""
    np = _np()
    m3 = m[:, :, None]
    out = base * (1 - m3) + deep[None, None, :] * m3 if deep.ndim == 1 else base * (1 - m3) + deep * m3
    ul = shift(m, dpx, -dpx)          # 把左上邻居搬到当前像素
    dr = shift(m, -dpx, dpx)
    sh = np.clip(m - ul, 0, 1)
    hl = np.clip(m - dr, 0, 1)
    out = out - sh[:, :, None] * shadow + hl[:, :, None] * light
    rim = np.clip(shift(m, -dpx, dpx) - m, 0, 1)      # 刻口外沿一线高光
    out = out + rim[:, :, None] * light * 0.6
    return out


def stone_bg(rng, size, hexc, amp=0.07):
    np = _np()
    base = hexrgb(hexc)
    n = fbm(rng, size)
    sp = rng.random((size, size))
    speck = (sp > 0.985) * 0.06 - (sp < 0.01) * 0.07
    v = (n - 0.5) * amp * 2 + speck
    return np.clip(base[None, None, :] + v[:, :, None], 0, 1)


def paper_bg(rng, size, hexc="#E8DCC8", aged=0.05):
    np = _np()
    base = hexrgb(hexc)
    fib = streaks(rng, size, 0, size // 40) * 0.6 + streaks(rng, size, 1, size // 60) * 0.4
    blot = fbm(rng, size, ((4, 0.6), (12, 0.4)))
    grain = rng.random((size, size)) * 0.03 - 0.015
    v = fib * 0.25 + (blot - 0.5) * aged + grain
    out = base[None, None, :] + v[:, :, None]
    out = out - (np.clip(blot - 0.62, 0, 1) * 0.3)[:, :, None] * np.array([0.2, 0.5, 1.0])      # 黄斑
    return np.clip(out, 0, 1)


def wood_bg(rng, size, hexc, axis=0, amp=0.08):
    """木纹/布纹：axis=0 纹理竖向（沿 v），1 横向。"""
    np = _np()
    base = hexrgb(hexc)
    g = streaks(rng, size, axis, size // 8) * 3.0 + streaks(rng, size, axis, size // 30) * 1.5
    yy, xx = np.mgrid[0:size, 0:size] / float(size)
    coord = xx if axis == 0 else yy
    ring = np.sin((coord * 40 + fbm(rng, size, ((3, 1.0),)) * 8) * math.pi)
    v = g * amp + ring * amp * 0.25 + (fbm(rng, size, ((5, 1.0),)) - 0.5) * amp
    return np.clip(base[None, None, :] + v[:, :, None], 0, 1)


def ink_on(base, m, ink, wet=0.0, rng=None):
    """墨写在纸上：遮罩边缘略洇，墨色不匀。"""
    np = _np()
    if rng is not None:
        m = np.clip(m * (0.86 + 0.14 * rng.random(m.shape)), 0, 1)
    m3 = m[:, :, None]
    return base * (1 - m3) + ink[None, None, :] * m3


# ====================================================================== 遮罩渲染（Workbench 平光）
# Songti.ttc 里的字体序号：0 SC Black、2 TC Bold、5 TC Light、7 TC Regular。Blender 只能读 .ttc 的第 0 个（简体黑体，缺很多繁体字），
# 所以把要用的那一个拆成单独的 .ttf 放在 Builds/tmp（不入库、不分发），只用来烘贴图。
FACE_BOLD, FACE_REGULAR = 2, 7
_FONTS = {}


def _extract_face(idx):
    import struct
    out = os.path.join(TMP, f"Songti_face{idx}.ttf")
    if os.path.exists(out):
        return out
    d = open(FONT_PATH, "rb").read()
    n = struct.unpack(">I", d[8:12])[0]
    o = struct.unpack(">%dI" % n, d[12:12 + 4 * n])[idx]
    nt = struct.unpack(">H", d[o + 4:o + 6])[0]
    recs = [struct.unpack(">4sIII", d[o + 12 + 16 * k:o + 28 + 16 * k]) for k in range(nt)]
    head = bytearray(d[o:o + 12])
    body, cur = bytearray(), 12 + 16 * nt
    dirs = bytearray()
    for tag, cs, off, ln in recs:
        dirs += struct.pack(">4sIII", tag, cs, cur + len(body), ln)
        body += d[off:off + ln]
        body += b"\0" * ((4 - len(body) % 4) % 4)
    os.makedirs(TMP, exist_ok=True)
    with open(out, "wb") as f:
        f.write(bytes(head) + bytes(dirs) + bytes(body))
    return out


def font(face=FACE_BOLD):
    f = _FONTS.get(face)
    try:
        ok = f is not None and f.name in bpy.data.fonts and bpy.data.fonts[f.name] == f
    except ReferenceError:          # 换了新场景（read_factory_settings）后旧字体对象失效
        ok = False
    if not ok:
        f = None
        if os.path.exists(FONT_PATH):
            try:
                f = bpy.data.fonts.load(_extract_face(face), check_existing=True)
            except Exception as e:
                print("[a2_text] 拆字体失败，退回 .ttc 第 0 个：", e)
                f = bpy.data.fonts.load(FONT_PATH, check_existing=True)
        _FONTS[face] = f
    return f


class Canvas:
    """设计坐标 = 表面米数，原点在表面中心，x 向右、y 向上（= 贴图 v 向上）。颜色是遮罩通道（0/1 的 RGB）。"""

    def __init__(self, W, H, size=2048, face=FACE_BOLD):
        self.W, self.H, self.size, self.face = W, H, size, face
        sc = bpy.data.scenes.new("A2T_TexScene")
        sc.render.engine = "BLENDER_WORKBENCH"
        sc.display.shading.light = "FLAT"
        sc.display.shading.color_type = "MATERIAL"
        sc.display.shading.show_shadows = False
        sc.display.shading.show_cavity = False
        try:
            sc.display.render_aa = "16"
        except Exception:
            pass
        sc.view_settings.view_transform = "Standard"
        sc.render.resolution_x = sc.render.resolution_y = size
        sc.render.resolution_percentage = 100
        sc.render.film_transparent = False
        sc.render.image_settings.file_format = "PNG"
        sc.render.image_settings.color_mode = "RGB"
        self.sc = sc
        self.made, self.mats = [], {}
        self.root = bpy.data.objects.new("A2T_Root", None)
        sc.collection.objects.link(self.root)
        self.root.scale = (1.0 / W, 1.0 / H, 1.0)
        cd = bpy.data.cameras.new("A2T_Cam")
        cd.type = "ORTHO"
        cd.ortho_scale = 1.0
        self.cd = cd
        cam = bpy.data.objects.new("A2T_Cam", cd)
        sc.collection.objects.link(cam)
        cam.location = (0, 0, 5)
        sc.camera = cam
        self.cam = cam
        self.rect(-W, -H, W, H, (0, 0, 0), z=-0.01)

    def mat(self, rgb):
        key = tuple(round(c, 3) for c in rgb)
        m = self.mats.get(key)
        if m is None:
            m = bpy.data.materials.new("A2T_tmp")
            m.diffuse_color = (*key, 1.0)
            self.mats[key] = m
        return m

    def _link(self, ob):
        self.sc.collection.objects.link(ob)
        ob.parent = self.root
        self.made.append(ob)
        return ob

    def poly(self, pts, rgb=(1, 1, 1), z=0.001):
        me = bpy.data.meshes.new("A2T_poly")
        me.from_pydata([(x, y, z) for x, y in pts], [], [list(range(len(pts)))])
        me.materials.append(self.mat(rgb))
        return self._link(bpy.data.objects.new("A2T_poly", me))

    def rect(self, x0, y0, x1, y1, rgb=(1, 1, 1), z=0.001):
        return self.poly([(x0, y0), (x1, y0), (x1, y1), (x0, y1)], rgb, z)

    def frame(self, x0, y0, x1, y1, t, rgb=(1, 1, 1), z=0.001, ty=None):
        ty = t if ty is None else ty
        self.rect(x0, y0, x1, y0 + ty, rgb, z)
        self.rect(x0, y1 - ty, x1, y1, rgb, z)
        self.rect(x0, y0, x0 + t, y1, rgb, z)
        self.rect(x1 - t, y0, x1, y1, rgb, z)

    def disc(self, cx, cy, rx, ry=None, rgb=(1, 1, 1), z=0.001, seg=64):
        ry = rx if ry is None else ry
        return self.poly([(cx + rx * math.cos(2 * math.pi * k / seg), cy + ry * math.sin(2 * math.pi * k / seg)) for k in range(seg)], rgb, z)

    def char(self, ch, x, y, s, rgb=(1, 1, 1), z=0.002, sx=1.0):
        f = font(self.face)
        if f is None:                       # 没字体：一个方块占位
            return self.rect(x - s * 0.4 * sx, y - s * 0.4, x + s * 0.4 * sx, y + s * 0.4, rgb, z)
        cu = bpy.data.curves.new("A2T_txt", "FONT")
        cu.body = ch
        cu.font = f
        cu.size = s
        cu.align_x = "CENTER"
        cu.align_y = "CENTER"
        cu.materials.append(self.mat(rgb))
        ob = self._link(bpy.data.objects.new("A2T_txt", cu))
        ob.location = (x, y - s * 0.02, z)
        ob.scale = (sx, 1.0, 1.0)
        return ob

    def column(self, text, x, ytop, s, rgb=(1, 1, 1), pitch=1.08, sx=1.0):
        """竖排一列（从上往下）；返回最后一个字的下沿 y。"""
        y = ytop
        for ch in text:
            self.char(ch, x, y - s / 2, s, rgb, sx=sx)
            y -= s * pitch
        return y + s * (pitch - 1)

    def row_rtl(self, text, xc, y, s, rgb=(1, 1, 1), pitch=1.12, sx=1.0):
        """横排右起（明代匾额读法：从右往左）。"""
        n = len(text)
        for k, ch in enumerate(text):
            self.char(ch, xc + ((n - 1) / 2 - k) * s * pitch * sx, y, s, rgb, sx=sx)

    def render(self, tag):
        np = _np()
        os.makedirs(TMP, exist_ok=True)
        path = os.path.join(TMP, f"{tag}_mask.png")
        self.sc.render.filepath = path
        bpy.ops.render.render(write_still=True, scene=self.sc.name)
        for o in self.made:
            data = o.data
            bpy.data.objects.remove(o, do_unlink=True)
            if isinstance(data, bpy.types.Curve):
                bpy.data.curves.remove(data)
            elif isinstance(data, bpy.types.Mesh):
                bpy.data.meshes.remove(data)
        bpy.data.objects.remove(self.root, do_unlink=True)
        bpy.data.objects.remove(self.cam, do_unlink=True)
        bpy.data.cameras.remove(self.cd)
        for m in self.mats.values():
            bpy.data.materials.remove(m)
        bpy.data.scenes.remove(self.sc)
        img = bpy.data.images.load(path, check_existing=False)
        w, h = img.size
        px = np.empty(w * h * 4, dtype=np.float32)
        img.pixels.foreach_get(px)
        bpy.data.images.remove(img)
        return px.reshape(h, w, 4)[:, :, :3].astype(np.float64)


def save_tex(arr, path):
    """numpy (h,w,3) → PNG（sRGB），返回重新载入的 bpy 图像。"""
    np = _np()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    h, w = arr.shape[:2]
    name = os.path.splitext(os.path.basename(path))[0]
    img = bpy.data.images.new(name + "_gen", w, h, alpha=False)
    a = np.ones((h, w, 4), dtype=np.float32)
    a[:, :, :3] = np.clip(arr, 0, 1)
    img.pixels.foreach_set(a.ravel())
    img.filepath_raw = path
    img.file_format = "PNG"
    img.save()
    bpy.data.images.remove(img)
    out = bpy.data.images.load(path, check_existing=False)
    out.name = name
    out["mean_rgb"] = [float(c) for c in arr.reshape(-1, 3).mean(axis=0)]
    return out


def tex_mat(name, img, rough=0.85):
    """贴图材质：图像接 Principled BSDF Base Color（Base Color 默认值设白，团结里不被乘暗）。"""
    m = bpy.data.materials.get(name) or bpy.data.materials.new(name)
    try:
        m.use_nodes = True
    except Exception:
        pass
    nt = m.node_tree
    bsdf = next((n for n in nt.nodes if n.type == "BSDF_PRINCIPLED"), None)
    if bsdf is None:
        bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
        out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None) or nt.nodes.new("ShaderNodeOutputMaterial")
        nt.links.new(bsdf.outputs[0], out.inputs[0])
    bsdf.inputs["Base Color"].default_value = (1, 1, 1, 1)
    bsdf.inputs["Roughness"].default_value = rough
    tn = nt.nodes.new("ShaderNodeTexImage")
    tn.image = img
    nt.links.new(tn.outputs["Color"], bsdf.inputs["Base Color"])
    nt.nodes.active = tn
    mean = img.get("mean_rgb", [0.7, 0.7, 0.7])
    m.diffuse_color = (*[K.srgb_to_linear(c) for c in mean], 1.0)
    return m


def asset_dir(cat, name):
    return os.path.join(ART, cat, name)


# ====================================================================== 网格小工具
def mesh_obj(name, verts, faces, uvs, mat, parent=None, loc=(0, 0, 0)):
    """uvs：每个面一组 (u,v)，顺序同面的顶点。"""
    me = bpy.data.meshes.new(name)
    me.from_pydata([tuple(v) for v in verts], [], faces)
    uvl = me.uv_layers.new(name="UVMap")
    for poly, fuv in zip(me.polygons, uvs):
        for li, uv in zip(poly.loop_indices, fuv):
            uvl.data[li].uv = uv
    mats = mat if isinstance(mat, (list, tuple)) else [mat]
    for m in mats:
        me.materials.append(m)
    me.update()
    ob = bpy.data.objects.new(name, me)
    bpy.context.scene.collection.objects.link(ob)
    if parent is not None:
        ob.parent = parent
    ob.location = loc
    return ob


def quad_xz(name, x0, x1, z0, z1, y, mat, uv=(0, 0, 1, 1), facing=-1, parent=None):
    """竖立面片，正面朝 facing·Y（-1 = 朝 -Y）。UV (u0,v0,u1,v1) 对应 (x0,z0)-(x1,z1)。"""
    u0, v0, u1, v1 = uv
    P = [(x0, y, z0), (x1, y, z0), (x1, y, z1), (x0, y, z1)]
    U = [(u0, v0), (u1, v0), (u1, v1), (u0, v1)]
    if facing > 0:
        P, U = P[::-1], U[::-1]
    return mesh_obj(name, P, [[0, 1, 2, 3]], [U], mat, parent)


def quad_xy(name, x0, x1, y0, y1, z, mat, uv=(0, 0, 1, 1), parent=None):
    """平放面片，正面朝 +Z。UV 对应 (x0,y0)-(x1,y1)。"""
    u0, v0, u1, v1 = uv
    return mesh_obj(name, [(x0, y0, z), (x1, y0, z), (x1, y1, z), (x0, y1, z)], [[0, 1, 2, 3]],
                    [[(u0, v0), (u1, v0), (u1, v1), (u0, v1)]], mat, parent)


def strip_faces(ob, matname):
    """删掉物体里用某材质的面（用贴图替换原来的「墨块/刻块」几何）。"""
    me = ob.data
    idx = [i for i, m in enumerate(me.materials) if m is not None and m.name == matname]
    if not idx:
        return 0
    bm = bmesh.new()
    bm.from_mesh(me)
    dead = [f for f in bm.faces if f.material_index in idx]
    bmesh.ops.delete(bm, geom=dead, context="FACES")
    bm.to_mesh(me)
    bm.free()
    me.update()
    return len(dead)


def clusters(matname):
    """场景里所有用 matname 的面，按连通分块，返回 [(物体, 局部 min, 局部 max, 世界中心)]。"""
    out = []
    for ob in bpy.context.scene.objects:
        if ob.type != "MESH" or ob.name.startswith("REF_"):
            continue
        me = ob.data
        idx = {i for i, m in enumerate(me.materials) if m is not None and m.name == matname}
        if not idx:
            continue
        faces = [p for p in me.polygons if p.material_index in idx]
        parent = {}

        def find(a):
            while parent.setdefault(a, a) != a:
                parent[a] = parent[parent[a]]
                a = parent[a]
            return a
        for p in faces:
            vs = list(p.vertices)
            for v in vs[1:]:
                ra, rb = find(vs[0]), find(v)
                if ra != rb:
                    parent[ra] = rb
        groups = {}
        for p in faces:
            groups.setdefault(find(p.vertices[0]), []).append(p)
        for ps in groups.values():
            co = [me.vertices[v].co for p in ps for v in p.vertices]
            mn = Vector((min(c.x for c in co), min(c.y for c in co), min(c.z for c in co)))
            mx = Vector((max(c.x for c in co), max(c.y for c in co), max(c.z for c in co)))
            out.append((ob, mn, mx, ob.matrix_world @ ((mn + mx) / 2)))
    return out


def find_cluster(matname, hint, tol=1.5):
    best, bd = None, 1e9
    for c in clusters(matname):
        w = c[3]
        d = math.sqrt(sum((w[i] - hint[i]) ** 2 for i in range(3) if hint[i] is not None))
        if d < bd:
            best, bd = c, d
    if best is None or bd > tol:
        print(f"[a2_text] 找不到 {matname} 面（提示 {hint}，最近 {bd:.2f} m），跳过")
        return None
    return best


# ====================================================================== 族约碑 ENV_Stele
ST_T, ST_W, ST_Z0, ST_Z1 = 0.13, 0.5, 0.5, 2.3        # 与 rupu_act2.build_stele 一致
SLOT_X = (0.33, 0.13, -0.07)                          # Clause_1..3（右起）
SLOT_W, SLOT_H, SLOT_ZC = 0.15, 1.5, 1.4
FACE = (-0.455, 0.455, 0.59, 2.24)                    # 碑面边框内
HEAD = (-0.21, 0.21, 2.305, 2.575)                    # 碑额（圆首正面）
STATES = ("Hit1", "Hit2", "Carved")


def _stele_textures(d):
    np = _np()
    rng = np.random.default_rng(1560)
    deep = hexrgb("#3a3833")
    # ---- 碑面（总纲 + 落款，左侧；条款槽被 Clause_N_Blank 盖住，这里留素面）
    W, H = FACE[1] - FACE[0], FACE[3] - FACE[2]
    cv = Canvas(W, H, 2048)
    x_l = FACE[0] - (FACE[0] + FACE[1]) / 2         # 画布坐标：中心 0
    cols_x = [-0.225, -0.32]
    for x, s in zip(cols_x, STELE_PREAMBLE):
        cv.column(s, x, H / 2 - 0.12, 0.082, pitch=1.13)
    cv.column(STELE_DATE, -0.41, H / 2 - 0.42, 0.046, pitch=1.15)
    for k, x in enumerate(SLOT_X):                      # 条款槽外一圈细刻线（让槽看起来是预留的）
        cx = x - (FACE[0] + FACE[1]) / 2
        cz = SLOT_ZC - (FACE[2] + FACE[3]) / 2
        cv.frame(cx - SLOT_W / 2 - 0.012, cz - SLOT_H / 2 - 0.012, cx + SLOT_W / 2 + 0.012, cz + SLOT_H / 2 + 0.012, 0.004)
    cv.frame(x_l + 0.012, -H / 2 + 0.012, -x_l - 0.012, H / 2 - 0.012, 0.005)
    m = cv.render("stele_face")[:, :, 0]
    base = stone_bg(rng, 2048, "#8a877e")
    face = carve(base, m, deep, dpx=3)
    img_face = save_tex(face, os.path.join(d, "T_ENV_Stele_Face_D.png"))
    # ---- 碑额：2×2 篆额位（右列「王氏」、左列「族約」）+ 额框
    W, H = HEAD[1] - HEAD[0], HEAD[3] - HEAD[2]
    cv = Canvas(W, H, 1024)
    s = 0.1
    cv.column(STELE_TITLE[:2], 0.058, H / 2 - 0.022, s, pitch=1.08)
    cv.column(STELE_TITLE[2:], -0.058, H / 2 - 0.022, s, pitch=1.08)
    cv.frame(-W / 2 + 0.008, -H / 2 + 0.006, W / 2 - 0.008, H / 2 - 0.006, 0.006)
    m = cv.render("stele_head")[:, :, 0]
    yy, xx = np.mgrid[0:1024, 0:1024] / 1023.0
    base = stone_bg(np.random.default_rng(7), 1024, "#8a877e")
    head = carve(base, m, deep, dpx=3)
    img_head = save_tex(head, os.path.join(d, "T_ENV_Stele_Title_D.png"))
    # ---- 条款图集：6 列（每列一条），R/G/B = 第 1/2/3 下凿出的字
    W, H = SLOT_W * 6, SLOT_H
    cv = Canvas(W, H, 2048)
    for i, (txt, _) in enumerate(CLAUSES):
        cx = -W / 2 + SLOT_W * (i + 0.5)
        n = len(txt)
        s = min(0.112, (SLOT_H - 0.16) / (n * 1.12))
        y = H / 2 - 0.08
        for k, ch in enumerate(txt):
            g = min(2, k * 3 // n)
            cv.char(ch, cx, y - s / 2, s, tuple(1.0 if j == g else 0.0 for j in range(3)))
            y -= s * 1.12
    mk = cv.render("stele_clauses")
    base = stone_bg(np.random.default_rng(11), 2048, "#a6a296", amp=0.05)       # = M_A2_StoneLight（Clause_N_Blank）
    chip = rng.random((2048, 2048))
    rough = (fbm(np.random.default_rng(5), 2048, ((60, 0.5), (180, 0.5))) > 0.5).astype(float)
    imgs = {}
    for si, st in enumerate(STATES):
        full = np.clip(sum(mk[:, :, g] for g in range(si + 1)), 0, 1)
        out = carve(base, full, deep, dpx=3)
        if si < 2:                       # 正在凿的那几个字：只凿出一半（斑驳的凿痕 + 石屑）
            part = mk[:, :, si + 1] * rough
            out = carve(out, part, deep * 1.25, dpx=2, shadow=0.12, light=0.08)
            grow = np.clip(sum(shift(mk[:, :, si + 1], dx, dy) for dx in (-9, 0, 9) for dy in (-9, 0, 9)), 0, 1)
            dust = grow * (chip > 0.93)
            out = out + dust[:, :, None] * 0.12
        imgs[st] = save_tex(out, os.path.join(d, f"T_ENV_Stele_Clauses_{st}_D.png"))
    return img_face, img_head, imgs


def build_stele_text(orig):
    def fn():
        orig()
        d = asset_dir("Environments", "ENV_Stele")
        img_face, img_head, imgs = _stele_textures(d)
        st = bpy.data.objects.get("Stele")
        if st is not None:
            strip_faces(st, "M_A2_Carved")          # 原来的刻字方块换成贴图
        m_face = tex_mat("M_A2T_Stele_Face", img_face, 0.92)
        m_head = tex_mat("M_A2T_Stele_Title", img_head, 0.92)
        quad_xz("NOCOL_TXT_Stele_Face", FACE[0], FACE[1], FACE[2], FACE[3], -ST_T - 0.0025, m_face, parent=st)
        quad_xz("NOCOL_TXT_Stele_Title", HEAD[0], HEAD[1], HEAD[2], HEAD[3], -ST_T - 0.001, m_head, parent=st)
        mats = {s: tex_mat(f"M_A2T_Stele_{s}", imgs[s], 0.92) for s in STATES}
        demo = {1: (1, "Carved"), 2: (3, "Hit2")}       # 预览图里：槽 1 刻成第 1 条，槽 2 凿到第二下的第 3 条，槽 3 空白
        for n in (1, 2, 3):
            g = bpy.data.objects.get(f"Clause_{n}")
            old = bpy.data.objects.get(f"Clause_{n}_Carved")
            if old is not None:
                bpy.data.objects.remove(old, do_unlink=True)
            for t in range(1, 7):
                u0, u1 = (t - 1) / 6, t / 6
                for s in STATES:
                    q = quad_xz(f"Clause_{n}_T{t}_{s}", -SLOT_W / 2, SLOT_W / 2, -SLOT_H / 2, SLOT_H / 2, -0.0048, mats[s],
                                uv=(u0, 0, u1, 1), parent=g)
                    q.hide_render = demo.get(n) != (t, s)
    return fn


# ====================================================================== 族约木牌 PROP_Covenant
BOARD_W, BOARD_L, BOARD_T = 0.085, 0.26, 0.014


def build_covenant_text(orig):
    def fn():
        np = _np()
        orig()
        d = asset_dir("Props", "PROP_Covenant")
        texts = [c[0] for c in CLAUSES] + [c[0] for c in COVENANT_EXTRA]
        cw, ch_ = BOARD_W - 0.012, BOARD_L - 0.05          # 每块牌子上贴字的区域
        W, H = cw * 5, ch_ * 2
        cv = Canvas(W, H, 2048)
        for i, t in enumerate(texts):
            cx = -W / 2 + cw * (i % 5 + 0.5)
            cy = H / 2 - ch_ * (i // 5 + 0.5)
            top = cy + ch_ / 2
            cv.column("第" + CN_NUM[i], cx + 0.024, top - 0.006, 0.011, (0, 1, 0), pitch=1.1)
            n = len(t)
            s = min(0.024, (ch_ - 0.03) / (n * 1.1))
            cv.column(t, cx - 0.002, top - 0.012, s, (1, 0, 0), pitch=1.1)
        mk = cv.render("covenant")
        rng = np.random.default_rng(10)
        base = wood_bg(rng, 2048, "#9a7a56", axis=0, amp=0.06)
        out = ink_on(base, mk[:, :, 0], hexrgb("#1a1714"), rng=rng)
        out = ink_on(out, mk[:, :, 1] * 0.85, hexrgb("#8a3a2c"), rng=rng)         # 章次朱书
        img = save_tex(out, os.path.join(d, "T_PROP_Covenant_Boards_D.png"))
        mat = tex_mat("M_A2T_Covenant_Boards", img, 0.8)
        for i in range(10):
            b = bpy.data.objects.get(f"Board_{i + 1:02d}")
            if b is None:
                continue
            strip_faces(b, "M_A2_Ink")
            u0, u1 = (i % 5) / 5, (i % 5 + 1) / 5
            v1 = 1 - (i // 5) / 2
            v0 = v1 - 0.5
            y0 = -BOARD_L / 2 + 0.012
            quad_xy(f"NOCOL_TXT_Board_{i + 1:02d}", -cw / 2, cw / 2, y0, y0 + ch_, BOARD_T + 0.0004, mat, uv=(u0, v0, u1, v1), parent=b)
    return fn


# ====================================================================== 义师名录 PROP_Roster
RS_W, RS_H = 0.366, 0.246                 # 摊开两页（左 x<0，右 x>0），原点在书脊中心
RS_ZL, RS_ZR = 0.016, 0.014               # 左/右页面高度（与 rupu_act2.build_roster 一致）
RS_PITCH = (0.175 - 0.008) / 15           # 每页 15 列
RS_YT, RS_YB = 0.106, -0.106              # 界栏上下
NSEG = 4


def slot_x(i):
    """第 i 个名字（1..30）的列中心 x：右页从外沿往书脊，再左页从书脊往外沿。"""
    if i <= 15:
        return 0.175 - (i - 0.5) * RS_PITCH
    return -0.008 - (i - 15 - 0.5) * RS_PITCH


RS_YD = -0.03                             # 上下栏分界：上栏写身份 + 名字，下栏写年岁 + 殁注
NAME_SPAN = 0.05                          # 名字占的高度（两字名、三字名都拉到同样长，名录的写法）


def _name_slots(n):
    s_big = 0.0094
    y0 = RS_YT - 0.024 - s_big / 2
    return s_big, [y0 - (NAME_SPAN - s_big) * (k / (n - 1) if n > 1 else 0) for k in range(n)]


def _roster_column(cv, i, entry, ink=(1, 0, 0), red=(0, 1, 0), nameless=False):
    """画一列：上栏 身份（小字）→ 名字（拉开）；下栏 年岁 → 殁注（朱笔）。返回 (ytop, ybot)。"""
    name, role, age, dead = entry
    x = slot_x(i)
    s_sm = 0.0056
    ytop = RS_YT - 0.005
    cv.column(role, x, ytop, s_sm, ink, pitch=1.12)
    if nameless:
        name = "無名"
    s_big, ys = _name_slots(len(name))
    for ch, y in zip(name, ys):
        cv.char(ch, x, y, s_big, ink)
    y = RS_YD - 0.004
    if not nameless:
        y = cv.column("年" + age, x, y, s_sm, ink, pitch=1.12) - 0.004
    if dead:
        y = cv.column(dead, x, y, s_sm, red, pitch=1.12)
    return ytop, y


def _roster_page_lines(cv, rgb=(0, 0, 1)):
    for sx in (-1, 1):
        xa, xb = (0.006, 0.177) if sx > 0 else (-0.177, -0.006)
        cv.frame(xa, RS_YB - 0.004, xb, RS_YT + 0.004, 0.0012, rgb)                       # 粗边
        cv.frame(xa + 0.0022, RS_YB - 0.0018, xb - 0.0022, RS_YT + 0.0018, 0.0003, rgb)   # 细边
        cv.rect(xa + 0.0022, RS_YD - 0.00016, xb - 0.0022, RS_YD + 0.00016, rgb)          # 上下栏分界
        for k in range(1, 15):
            x = (0.175 - k * RS_PITCH) if sx > 0 else (-0.008 - k * RS_PITCH)
            cv.rect(x - 0.00016, RS_YB - 0.0018, x + 0.00016, RS_YT + 0.0018, rgb)


def _roster_textures(d):
    np = _np()
    rng = np.random.default_rng(30)
    paper = paper_bg(rng, 2048, "#E2D4BA", aged=0.07)
    yy, xx = np.mgrid[0:2048, 0:2048]
    spine = np.exp(-((xx - 1023.5) / 45.0) ** 2)                                   # 书脊处纸面下陷，暗一点
    paper = paper - spine[:, :, None] * 0.08
    line = hexrgb("#6b3a2e")                                                        # 朱丝栏（褪色）
    # 1) 空页：纸 + 界栏
    cv = Canvas(RS_W, RS_H, 2048)
    _roster_page_lines(cv)
    lines = cv.render("roster_lines")[:, :, 2]
    page = ink_on(paper, lines * 0.75, line)
    ranges = {}
    # 2) 写满：30 名（墨 R、朱 G）；手写用常规体
    cv = Canvas(RS_W, RS_H, 2048, face=FACE_REGULAR)
    for i, e in enumerate(ROSTER, 1):
        ranges[i] = _roster_column(cv, i, e)
    mk = cv.render("roster_ink")
    ink_rgb, red_rgb = hexrgb("#17130f"), hexrgb("#9a3424")
    bleed = np.clip(sum(shift(mk[:, :, 0], dx, dy) for dx in (-1, 0, 1) for dy in (-1, 0, 1)) / 9.0, 0, 1)
    full = ink_on(page, np.maximum(mk[:, :, 0], bleed * 0.35), ink_rgb, rng=rng)
    full = ink_on(full, mk[:, :, 1], red_rgb, rng=rng)
    faded = page + (full - page) * 0.45                     # 墨淡（隔几天的名字）：同一张纸底，墨只剩 45%
    # 3) 无名：29、30 两列
    cv = Canvas(RS_W, RS_H, 2048, face=FACE_REGULAR)
    nl_ranges = {}
    for i in NAMELESS_SLOTS:
        nl_ranges[i] = _roster_column(cv, i, ROSTER[i - 1], nameless=True)
    mk2 = cv.render("roster_nameless")
    nameless = ink_on(ink_on(page, mk2[:, :, 0], ink_rgb, rng=rng), mk2[:, :, 1], red_rgb, rng=rng)
    # 4) 跳过：空白格（□，古籍缺字的写法）——跳过的行留着这个，不能补
    cv = Canvas(RS_W, RS_H, 2048)
    s_big, ys = _name_slots(3)
    for i in range(1, 31):
        x = slot_x(i)
        for c in ys:
            cv.frame(x - 0.0036, c - 0.0036, x + 0.0036, c + 0.0036, 0.0005)
    mk3 = cv.render("roster_skip")[:, :, 0]
    skip = ink_on(page, mk3 * 0.55, hexrgb("#4a3e34"))
    imgs = {k: save_tex(v, os.path.join(d, f"T_PROP_Roster_{k}_D.png"))
            for k, v in (("Page", page), ("Ink", full), ("InkFaded", faded), ("Nameless", nameless), ("Skip", skip))}
    # 题签、印文
    cv = Canvas(0.03, 0.16, 1024)
    cv.column(ROSTER_TITLE, 0, 0.068, 0.019, pitch=1.15)
    cv.frame(-0.0135, -0.0765, 0.0135, 0.0765, 0.0008)
    m = cv.render("roster_slip")[:, :, 0]
    slip = ink_on(paper_bg(np.random.default_rng(3), 1024, "#E8DCC8", aged=0.04), m, ink_rgb)
    imgs["Slip"] = save_tex(slip, os.path.join(d, "T_PROP_Roster_Slip_D.png"))
    imgs["Seal"] = seal_tex(os.path.join(d, "T_PROP_Roster_Seal_D.png"), SEAL_TEXT)
    return imgs, ranges, nl_ranges


def seal_tex(path, text, size=1024):
    """白文方印：朱底，字留纸色；四边和笔画边缘做残破。"""
    np = _np()
    S = 0.042
    cv = Canvas(S, S, size)
    s = 0.0175
    cv.column(text[:2], 0.0095, S / 2 - 0.0035, s, pitch=1.02)
    cv.column(text[2:], -0.0095, S / 2 - 0.0035, s, pitch=1.02)
    m = cv.render("seal")[:, :, 0]
    rng = np.random.default_rng(42)
    paper = paper_bg(rng, size, "#E2D4BA")
    yy, xx = np.mgrid[0:size, 0:size] / (size - 1)
    edge = np.minimum(np.minimum(xx, 1 - xx), np.minimum(yy, 1 - yy))
    n = fbm(rng, size, ((20, 0.5), (60, 0.5)))
    red = (edge > 0.012 + 0.02 * n) & (rng.random((size, size)) > 0.04)
    red = red.astype(float) * (1 - m) * (n > 0.18)
    return save_tex(ink_on(paper, red * 0.92, hexrgb("#a8402e")), path)


def build_roster_text(orig):
    def fn():
        orig()
        d = asset_dir("Props", "PROP_Roster")
        imgs, ranges, nl_ranges = _roster_textures(d)
        mats = {k: tex_mat(f"M_A2T_Roster_{k}", imgs[k], 0.9) for k in imgs}
        for o in [o for o in bpy.context.scene.objects if o.name.startswith("InkRow_") or o.name == "Seal_Mark"]:
            bpy.data.objects.remove(o, do_unlink=True)
        op = bpy.data.objects.get("Roster_Open")

        def U(x):
            return (x + RS_W / 2) / RS_W

        def V(y):
            return (y + RS_H / 2) / RS_H
        # 纸面（两页各一片，挂在 Roster_Open 下）
        quad_xy("NOCOL_TXT_Roster_PageR", 0.0, 0.181, -0.121, 0.121, RS_ZR + 0.0002, mats["Page"],
                uv=(U(0.0), V(-0.121), U(0.181), V(0.121)), parent=op)
        quad_xy("NOCOL_TXT_Roster_PageL", -0.181, 0.0, -0.121, 0.121, RS_ZL + 0.0002, mats["Page"],
                uv=(U(-0.181), V(-0.121), U(0.0), V(0.121)), parent=op)
        # 30 个名字槽：InkRow_NN（空物体）下 _S1.._S4 逐段显示、_Skip 空白格；29、30 另有 _Nameless_S1..S4
        for i in range(1, 31):
            x = slot_x(i)
            z = (RS_ZR if x > 0 else RS_ZL) + 0.0004
            g = bpy.data.objects.new(f"InkRow_{i:02d}", None)
            g.empty_display_type = "PLAIN_AXES"
            g.empty_display_size = 0.01
            g.location = (x, RS_YT - 0.008, z)
            bpy.context.scene.collection.objects.link(g)
            x0, x1 = x - RS_PITCH / 2 + 0.0004, x + RS_PITCH / 2 - 0.0004

            def segs(prefix, rng_, mat):
                yt, yb = rng_[0] + 0.002, rng_[1] - 0.003
                for k in range(NSEG):
                    ya, yb_ = yt - (yt - yb) * k / NSEG, yt - (yt - yb) * (k + 1) / NSEG
                    q = quad_xy(f"{prefix}_S{k + 1}", x0 - x, x1 - x, yb_ - g.location.y, ya - g.location.y, 0.0, mat,
                                uv=(U(x0), V(yb_), U(x1), V(ya)), parent=g)
                    yield q
            demo_written = i <= 9 or i in (12, 13)          # 预览：写了 11 个，第 10、11 列跳过，第 14 列写到一半
            for k, q in enumerate(segs(f"InkRow_{i:02d}", ranges[i], mats["Ink"])):
                q.hide_render = not (demo_written or (i == 14 and k < 2))
            _, ys = _name_slots(3)
            yt, yb = ys[0] + 0.006, ys[-1] - 0.006
            q = quad_xy(f"InkRow_{i:02d}_Skip", x0 - x, x1 - x, yb - g.location.y, yt - g.location.y, 0.0, mats["Skip"],
                        uv=(U(x0), V(yb), U(x1), V(yt)), parent=g)
            q.hide_render = i not in (10, 11)
            if i in NAMELESS_SLOTS:
                for q in segs(f"InkRow_{i:02d}_Nameless", nl_ranges[i], mats["Nameless"]):
                    q.hide_render = True
        # 印迹（盖印后显示）：左页下栏、第 24–27 列（这几人没有殁注）的空处
        quad_xy("Seal_Mark", -0.021, 0.021, -0.021, 0.021, 0.0, mats["Seal"]).location = (-0.119, -0.087, RS_ZL + 0.0007)
        # 合册题签
        cl = bpy.data.objects.get("Roster_Closed")
        if cl is not None:
            quad_xy("NOCOL_TXT_Roster_Slip", -0.11, -0.08, -0.08, 0.08, 0.0414, mats["Slip"], parent=cl)
    return fn


# ====================================================================== 匾 / 旗 / 纸面（包装明代建筑）
def plaque_tex(path, W, H, text, style, size=1024, seed=0):
    np = _np()
    rng = np.random.default_rng(seed)
    cv = Canvas(W, H, size)
    if style in ("lacquer", "stone"):
        b = min(W, H) * 0.09
        cv.frame(-W / 2, -H / 2, W / 2, H / 2, b, (0, 1, 0))                         # 边框（G）
        cv.frame(-W / 2 + b * 1.25, -H / 2 + b * 1.25, W / 2 - b * 1.25, H / 2 - b * 1.25, b * 0.12, (0, 0, 1))   # 内金线（B）
        n = len(text)
        s = min((H - 2.6 * b) * 0.86, (W - 2.6 * b) * 0.9 / (n * 1.12))
        cv.row_rtl(text, 0, 0, s, (1, 0, 0))
    elif style == "couplet":
        n = len(text)
        s = min(W * 0.72, H * 0.9 / (n * 1.1))
        cv.column(text, 0, H / 2 - (H - n * s * 1.1) / 2, s, (1, 0, 0), pitch=1.1)
        cv.frame(-W / 2 + 0.02, -H / 2 + 0.02, W / 2 - 0.02, H / 2 - 0.02, 0.006, (0, 0, 1))
    elif style == "scroll":
        cv.char(text, 0, 0.05, min(W, H) * 0.78, (1, 0, 0))
        cv.column("嘉靖庚申叔杲書", W / 2 - 0.12, H / 2 - 0.25, 0.045, (1, 0, 0))
        cv.rect(W / 2 - 0.15, H / 2 - 0.66, W / 2 - 0.09, H / 2 - 0.6, (0, 1, 0))       # 名章（朱）
        cv.frame(-W / 2 + 0.03, -H / 2 + 0.12, W / 2 - 0.03, H / 2 - 0.12, 0.012, (0, 0, 1))  # 绫裱边
    mk = cv.render(os.path.splitext(os.path.basename(path))[0])
    R, G, B = mk[:, :, 0], mk[:, :, 1], mk[:, :, 2]
    if style == "lacquer":
        base = wood_bg(rng, size, "#3a2618", axis=1, amp=0.03)
        base = base + (fbm(rng, size, ((6, 1.0),)) - 0.5)[:, :, None] * 0.05
        out = ink_on(base, G, hexrgb("#5a3e26"))
        out = ink_on(out, B, hexrgb("#8f7a44"))
        gold = hexrgb("#b39a5c")
        wear = (fbm(rng, size, ((30, 0.6), (90, 0.4))) > 0.32).astype(float)        # 金字剥落
        out = carve(out, R * wear, gold, dpx=2, shadow=-0.05, light=0.05)
    elif style == "stone":
        base = stone_bg(rng, size, "#a6a296", amp=0.05)
        out = carve(base, G * 0.0 + B, hexrgb("#55524b"), dpx=2)
        out = carve(out, R, hexrgb("#3a3833"), dpx=3)
    elif style == "couplet":
        base = paper_bg(rng, size, "#8f4a38", aged=0.06)
        out = ink_on(base, B * 0.5, hexrgb("#6a3426"))
        out = ink_on(out, R, hexrgb("#1a1512"), rng=rng)
    else:   # scroll
        base = paper_bg(rng, size, "#E2D4BA", aged=0.06)
        out = ink_on(base, B, hexrgb("#5a6466"))
        out = ink_on(out, R, hexrgb("#17130f"), rng=rng)
        out = ink_on(out, G, hexrgb("#a8402e"))
    return save_tex(out, path)


def flag_tex(path, W, H, text="王", field="#9a3a2c", size=1024, seed=3):
    """义师旗：朱底、火焰牙边（上、下、旗尾三边）、靠杆一侧黑旗袖，中间纸色圆心黑「王」。旗杆在画布左（x=-W/2）。"""
    np = _np()
    cv = Canvas(W, H, size)
    t = min(W, H) * 0.11
    sleeve = W * 0.07
    cv.rect(-W / 2, -H / 2, -W / 2 + sleeve, H / 2, (0, 0, 1))                         # 旗袖（B）
    n = 7
    for side in (-1, 1):                                                               # 上下牙边
        y_in = side * (H / 2 - t)
        y_out = side * H / 2
        x0 = -W / 2 + sleeve
        step = (W - sleeve) / n
        for k in range(n):
            xa = x0 + k * step
            cv.poly([(xa, y_in), (xa + step, y_in), (xa + step * 0.5, y_out)] if side > 0 else
                    [(xa, y_in), (xa + step * 0.5, y_out), (xa + step, y_in)], (0, 1, 0))
        cv.rect(x0, min(y_in, y_in + side * -t * 0.2), W / 2, max(y_in, y_in + side * -t * 0.2), (0, 1, 0))
    m_ = 6
    step = (H - 2 * t) / m_
    for k in range(m_):                                                                # 旗尾牙边
        ya = -H / 2 + t + k * step
        cv.poly([(W / 2 - t, ya), (W / 2, ya + step * 0.5), (W / 2 - t, ya + step)], (0, 1, 0))
    cv.rect(W / 2 - t * 1.2, -H / 2 + t * 0.8, W / 2 - t, H / 2 - t * 0.8, (0, 1, 0))
    r = min(W - sleeve - 2 * t, H - 2 * t) * 0.36
    cx = sleeve / 2
    cv.disc(cx, 0, r, rgb=(1, 1, 0))                                                   # 纸色圆心（R+G）
    cv.char(text, cx, 0.0, r * 1.45, (1, 0, 1), z=0.003)                               # 字（R+B）
    mk = cv.render(os.path.splitext(os.path.basename(path))[0])
    R, G, B = mk[:, :, 0], mk[:, :, 1], mk[:, :, 2]
    rng = np.random.default_rng(seed)
    base = wood_bg(rng, size, field, axis=0, amp=0.025)                                # 布纹：细竖纹
    base = base + (streaks(rng, size, 1, size // 50) * 0.15)[:, :, None]
    disc_m = np.clip(R * G, 0, 1)
    char_m = np.clip(R * B, 0, 1)
    edge_m = np.clip(G - disc_m, 0, 1)
    sleeve_m = np.clip(B - char_m, 0, 1)
    out = ink_on(base, edge_m, hexrgb("#2e2a26"))
    out = ink_on(out, sleeve_m, hexrgb("#24211e"))
    out = ink_on(out, disc_m, hexrgb("#d8ccb2"))
    out = ink_on(out, char_m, hexrgb("#1a1714"))
    fade = fbm(rng, size, ((4, 0.6), (12, 0.4)))
    out = out * (0.92 + 0.12 * fade[:, :, None])                                       # 日晒不匀
    return save_tex(out, path)


def _decal_on_cluster(c, name, mat, facing=-1, off=0.003, uv=(0, 0, 1, 1)):
    ob, mn, mx, _ = c
    y = mn.y - off if facing < 0 else mx.y + off
    return quad_xz(name, mn.x, mx.x, mn.z, mx.z, y, mat, uv=uv, facing=facing, parent=ob)


def build_plaques(asset, cat, orig):
    def fn():
        orig()
        d = asset_dir(cat, asset)
        for k, (matname, hint, key, text, style) in enumerate(PLAQUES[asset]):
            if matname == "HANG":                   # 自带一块匾板（原匾被挡住时）
                x0, x1, yb, z0, z1 = hint
                host = bpy.data.objects.get(asset)
                mb = K.MB()
                mb.box(x0, yb - 0.07, z0, x1, yb, z1, "M_Plaque")
                mb.box(x0 - 0.06, yb - 0.09, z0 - 0.06, x1 + 0.06, yb - 0.05, z0, "M_Wood_Dark")      # 下边框托
                board = mb.to_object(f"NOCOL_Plaque_{key}", uv_scale=1.0)
                board.parent = host
                c = (board, Vector((x0, yb - 0.07, z0)), Vector((x1, yb, z1)), None)
            else:
                c = find_cluster(matname, hint)
            if c is None:
                continue
            ob, mn, mx, _ = c
            W, H = mx.x - mn.x, mx.z - mn.z
            seed = 100 + k
            if style == "flag":
                img = flag_tex(os.path.join(d, f"T_{asset}_{key}_D.png"), W, H, text)
                mat = tex_mat(f"M_A2T_{asset[4:]}_{key}", img, 0.95)
                _decal_on_cluster(c, f"NOCOL_TXT_{key}_Front", mat, -1, 0.002)
                _decal_on_cluster(c, f"NOCOL_TXT_{key}_Back", mat, +1, 0.002)
            elif asset == "BLD_MING_GateTower" and key == "Gate":
                for j, (gk, gname, _) in enumerate(GATE_NAMES):     # 三门同一模型：三片叠放，最前面的是通市门；A 按门 SetActive 一片
                    img = plaque_tex(os.path.join(d, f"T_{asset}_Gate_{gk}_D.png"), W, H, gname, "lacquer", seed=seed + j)
                    mat = tex_mat(f"M_A2T_GateTower_{gk}", img, 0.6)
                    q = _decal_on_cluster(c, f"NOCOL_TXT_Gate_{gk}", mat, -1, 0.006 - j * 0.0015)
                    q.hide_render = j > 0
            elif style == "stone_closure":
                img = closure_tex(os.path.join(d, f"T_{asset}_{key}_D.png"), W, H)
                mat = tex_mat(f"M_A2T_NorthGate_{key}", img, 0.92)
                _decal_on_cluster(c, f"NOCOL_TXT_{key}", mat, -1, 0.003)
            else:
                img = plaque_tex(os.path.join(d, f"T_{asset}_{key}_D.png"), W, H, text, style, seed=seed)
                mat = tex_mat(f"M_A2T_{asset[4:] if asset.startswith('BLD_') else asset}_{key}", img,
                              0.6 if style == "lacquer" else 0.9)
                _decal_on_cluster(c, f"NOCOL_TXT_{key}", mat, -1, 0.003)
    return fn


def closure_tex(path, W, H, size=1024):
    """合龙石：右起三列（年款小字 / 「北垣合龍」大字 / 立石人小字），浅凿。"""
    np = _np()
    cv = Canvas(W, H, size)
    xs = [W * 0.3, 0.0, -W * 0.3]
    for (t, s), x in zip(CLOSURE_COLS, xs):
        n = len(t)
        cv.column(t, x, (n * s * 1.08) / 2, s, pitch=1.08)
    cv.frame(-W / 2 + 0.03, -H / 2 + 0.03, W / 2 - 0.03, H / 2 - 0.03, 0.012)
    m = cv.render("closure")[:, :, 0]
    rng = np.random.default_rng(9)
    base = stone_bg(rng, size, "#a6a296", amp=0.06)
    return save_tex(carve(base, m, hexrgb("#4a4741"), dpx=2), path)


# ====================================================================== 新道具：义师旗、王字灯笼
def build_flag_wang():
    """义师「王」字旗：夹杆石 + 4.6 m 旗杆 + 1.2×1.6 旗面（两面贴图，带一点风吹的起伏）。
    插在敌台 / 城门 / 北门工地。原点在夹杆石底中心；旗面靠杆一侧在 x=0，往 +X 飘。"""
    import rupu_act2 as A2
    mb = K.MB()
    mb.box(-0.22, -0.16, 0, 0.22, 0.16, 0.42, "M_A2_StoneDark")
    mb.cyl(0, 0, 0.0, 4.6, 0.045, "M_A2_WoodDark", seg=8, r_top=0.032)
    mb.cyl(0, 0, 4.6, 4.7, 0.05, "M_A2_Brass", seg=8, r_top=0.0)
    for z in (3.0, 4.5):
        mb.cyl(0, 0, z - 0.02, z + 0.02, 0.052, "M_A2_Rope", seg=8)
    A2.obj(mb, "Pole", (0, 0, 0), uv=0.5)
    W, H, ztop = 1.2, 1.6, 4.5
    d = asset_dir("Props", "PROP_Flag_Wang")
    img = flag_tex(os.path.join(d, "T_PROP_Flag_Wang_D.png"), W, H)
    mat = tex_mat("M_A2T_Flag_Wang", img, 0.95)
    nx, nz = 8, 4
    verts, faces, uvs = [], [], []
    for side in (0, 1):
        b = len(verts)
        for j in range(nz + 1):
            for i in range(nx + 1):
                u, v = i / nx, j / nz
                x = 0.05 + u * (W - 0.05)
                y = 0.07 * math.sin(u * 2.6 * math.pi + 0.4) * u + (0.0015 if side else -0.0015)
                verts.append((x, y, ztop - H + v * H - 0.08 * u * u))
        for j in range(nz):
            for i in range(nx):
                a = b + j * (nx + 1) + i
                q = [a, a + 1, a + nx + 2, a + nx + 1]
                uq = [(i / nx, j / nz), ((i + 1) / nx, j / nz), ((i + 1) / nx, (j + 1) / nz), (i / nx, (j + 1) / nz)]
                if side:
                    q, uq = q[::-1], uq[::-1]
                faces.append(q)
                uvs.append(uq)
    mesh_obj("NOCOL_Flag", verts, faces, uvs, mat)
    A2.anchor("ANCHOR_FlagTop", (0, 0, 4.6), 0.2)


LAN_R, LAN_Z0, LAN_Z1, LAN_SEG, LAN_RING = 0.16, 0.05, 0.41, 16, 8


def build_lantern_wang():
    """明代「王」字纸灯笼：竹篾椭圆灯身（贴图：纸面、篾骨、上下朱边、前后各一个「王」）+ 上下木圈 + 提梁 + 提杆。
    原点在灯底中心；Stick（提杆，妇人提灯用）可隐藏；ANCHOR_Hang 是挂钩点；FX_Light 是灯芯（点光/自发光挂点）。"""
    import rupu_act2 as A2
    np = _np()
    H = LAN_Z1 - LAN_Z0
    Wc = 2 * math.pi * LAN_R
    d = asset_dir("Props", "PROP_Lantern_Wang")
    cv = Canvas(Wc, H, 1024)
    for u in (0.25, 0.75):                                   # u=0.75 朝 -Y（正面），0.25 朝 +Y（背面）
        cv.char("王", -Wc / 2 + u * Wc, 0.0, 0.17, (1, 0, 0))
    for k in range(1, 9):                                    # 篾骨（横向细线）
        y = -H / 2 + H * k / 9
        cv.rect(-Wc / 2, y - 0.0012, Wc / 2, y + 0.0012, (0, 1, 0))
    cv.rect(-Wc / 2, H / 2 - 0.03, Wc / 2, H / 2, (0, 0, 1))
    cv.rect(-Wc / 2, -H / 2, Wc / 2, -H / 2 + 0.03, (0, 0, 1))
    mk = cv.render("lantern")
    rng = np.random.default_rng(77)
    base = paper_bg(rng, 1024, "#d8c8a0", aged=0.08)
    out = ink_on(base, mk[:, :, 1] * 0.5, hexrgb("#8a7450"))
    out = ink_on(out, mk[:, :, 2], hexrgb("#8a3a2c"))
    out = ink_on(out, mk[:, :, 0], hexrgb("#1c1815"), rng=rng)
    img = save_tex(out, os.path.join(d, "T_PROP_Lantern_Wang_D.png"))
    mat = tex_mat("M_A2T_Lantern_Wang", img, 0.8)
    verts, faces, uvs = [], [], []
    zc, hz = (LAN_Z0 + LAN_Z1) / 2, H / 2
    for j in range(LAN_RING + 1):
        v = j / LAN_RING
        z = LAN_Z0 + v * H
        r = max(0.085, LAN_R * math.sqrt(max(0.0, 1 - ((z - zc) / (hz * 1.18)) ** 2)))
        for i in range(LAN_SEG + 1):
            a = 2 * math.pi * i / LAN_SEG
            verts.append((r * math.cos(a), r * math.sin(a), z))
    for j in range(LAN_RING):
        for i in range(LAN_SEG):
            a = j * (LAN_SEG + 1) + i
            faces.append([a, a + 1, a + LAN_SEG + 2, a + LAN_SEG + 1])
            uvs.append([(i / LAN_SEG, j / LAN_RING), ((i + 1) / LAN_SEG, j / LAN_RING),
                        ((i + 1) / LAN_SEG, (j + 1) / LAN_RING), (i / LAN_SEG, (j + 1) / LAN_RING)])
    mesh_obj("Lantern_Body", verts, faces, uvs, mat)
    mb = K.MB()
    mb.cyl(0, 0, 0.0, LAN_Z0 + 0.005, 0.092, "M_A2_WoodDark", seg=12)
    mb.cyl(0, 0, LAN_Z1 - 0.005, LAN_Z1 + 0.03, 0.09, "M_A2_WoodDark", seg=12)
    A2.tb(mb, (-0.085, 0, LAN_Z1 + 0.03), (0, 0, LAN_Z1 + 0.16), 0.006, "M_A2_Iron", seg=4)      # 提梁
    A2.tb(mb, (0.085, 0, LAN_Z1 + 0.03), (0, 0, LAN_Z1 + 0.16), 0.006, "M_A2_Iron", seg=4)
    A2.obj(mb, "Lantern_Caps", (0, 0, 0), uv=0.3)
    mb = K.MB()
    A2.tb(mb, (0, 0, LAN_Z1 + 0.16), (0, 0.0, LAN_Z1 + 0.22), 0.004, "M_A2_Rope", seg=4)
    A2.tb(mb, (-0.05, 0, LAN_Z1 + 0.22), (0.9, 0, LAN_Z1 + 0.42), 0.012, "M_A2_Fir", seg=6)           # 提杆（往 +X 斜上）
    A2.obj(mb, "Stick", (0, 0, 0), uv=0.3)
    A2.anchor("ANCHOR_Hang", (0, 0, LAN_Z1 + 0.16), 0.05)
    A2.anchor("ANCHOR_Hold", (0.85, 0, LAN_Z1 + 0.41), 0.05)
    A2.fx("FX_Light", (0, 0, zc))


# ====================================================================== 注册
def _orig(name):
    """取当前的原配方：优先 build_yongchang 已汇总的 RECIPES（保留前面模块的包装），否则从源模块取。"""
    main = sys.modules.get("__main__")
    R = getattr(main, "RECIPES", None)
    if isinstance(R, dict) and name in R:
        return R[name]
    import rupu_act2
    import rupu_ming_civic
    for m in (rupu_act2, rupu_ming_civic):
        r = m.recipes()
        if name in r:
            return r[name]
    raise KeyError(name)


def recipes():
    R = {}
    for name, wrap in (("ENV_Stele", build_stele_text), ("PROP_Covenant", build_covenant_text), ("PROP_Roster", build_roster_text)):
        cat, fn = _orig(name)
        R[name] = (cat, wrap(fn))
    for asset in PLAQUES:
        cat, fn = _orig(asset)
        R[asset] = (cat, build_plaques(asset, cat, fn))
    R["PROP_Flag_Wang"] = ("Props", build_flag_wang)
    R["PROP_Lantern_Wang"] = ("Props", build_lantern_wang)
    return R


# ====================================================================== 文档预览（贴图着色的近景）
SHOTS = [
    # (资产, 分类, 文件名, 取景对象（名字前缀；None=整个场景）, 视线方向(从目标指向相机), 留边倍数, 宽, 高, 剖切深度 m（None=不剖）)
    ("ENV_Stele", "Environments", "text_stele.png", None, (0.25, -1, 0.15), 1.1, 900, 1100, None),
    ("ENV_Stele", "Environments", "text_stele_slots.png", ["Clause_"], (0, -1, 0), 1.15, 700, 1000, None),
    ("PROP_Covenant", "Props", "text_covenant.png", ["Board_"], (0, -0.25, 1), 1.12, 1100, 800, None),
    ("PROP_Roster", "Props", "text_roster.png", ["Roster_Open"], (0, -0.12, 1), 1.08, 1200, 860, None),
    ("PROP_Roster", "Props", "text_roster_closed.png", ["Roster_Closed"], (0, -0.2, 1), 1.3, 700, 700, None),
    ("BLD_MING_AncestralHall", "Buildings", "text_ancestral_gate.png", ["NOCOL_TXT_Gate"], (0.1, -1, -0.1), 1.5, 1000, 500, 0.15),
    ("BLD_MING_AncestralHall", "Buildings", "text_ancestral_hall.png", ["NOCOL_TXT_Hall"], (0.1, -1, -0.1), 1.5, 1000, 500, 0.15),
    ("BLD_MING_GateTower", "Buildings", "text_gatetower.png", ["NOCOL_TXT_Gate_"], (0.08, -1, 0.04), 1.8, 1000, 500, 0.3),
    ("BLD_MING_HuanhaiLou", "Buildings", "text_huanhai.png", ["NOCOL_TXT_Gate"], (0.1, -1, -0.15), 1.8, 1000, 600, 0.3),
    ("BLD_MING_HuanhaiLou", "Buildings", "text_huanhai_flag.png", ["NOCOL_TXT_Flag_Front"], (0.35, -1, 0.1), 1.4, 800, 900, None),
    ("ENV_NorthGate_Build", "Environments", "text_closure.png", ["NOCOL_TXT_Closure"], (0.15, -1, 0.05), 1.3, 1000, 600, 0.6),
    ("ENV_WangHouse", "Environments", "text_wanghouse_gate.png", ["NOCOL_TXT_GateLintel"], (0.1, -1, -0.05), 1.6, 1000, 500, 0.2),
    ("ENV_WangHouse", "Environments", "text_wanghouse_hall.png", ["NOCOL_TXT_ZhongTang", "NOCOL_TXT_Couplet", "NOCOL_TXT_Scroll"],
     (0, -1, 0.05), 1.15, 900, 1000, 0.6),
    ("PROP_Flag_Wang", "Props", "text_flag.png", None, (0.3, -1, 0.1), 1.05, 700, 1100, None),
    ("PROP_Lantern_Wang", "Props", "text_lantern.png", ["Lantern_"], (0.2, -1, 0.15), 1.3, 700, 800, None),
]


def _bbox(prefixes):
    mn = Vector((1e9, 1e9, 1e9))
    mx = -mn
    for o in bpy.context.scene.objects:
        if o.type != "MESH" or o.name.startswith(("REF_", "COL_")):
            continue
        if prefixes and not any(o.name.startswith(p) for p in prefixes):
            continue
        for v in o.bound_box:
            w = o.matrix_world @ Vector(v)
            mn = Vector((min(mn[i], w[i]) for i in range(3)))
            mx = Vector((max(mx[i], w[i]) for i in range(3)))
    return mn, mx


def shot(path, prefixes, view, margin, w, h, clip=None):
    sc = bpy.context.scene
    mn, mx = _bbox(prefixes)
    c = (mn + mx) / 2
    d = Vector(view).normalized()
    ext = mx - mn
    if abs(d.z) < 0.9:
        side = Vector((-d.y, d.x, 0)).normalized()
        up = d.cross(side).normalized()
    else:
        side, up = Vector((1, 0, 0)), Vector((0, 1, 0))
    wx = sum(abs(side[i]) * ext[i] for i in range(3))
    wy = sum(abs(up[i]) * ext[i] for i in range(3))
    cd = bpy.data.cameras.new("ShotCam")
    cd.type = "ORTHO"
    cd.ortho_scale = (max(wx, wy * w / h) if w >= h else max(wy, wx * h / w)) * margin     # 正交尺寸 = 长边
    cam = bpy.data.objects.new("ShotCam", cd)
    sc.collection.objects.link(cam)
    dist = 60.0
    cam.location = c + d * dist
    cam.rotation_euler = (c - cam.location).to_track_quat("-Z", "Y").to_euler()
    cd.clip_start = dist - clip if clip else 0.1
    cd.clip_end = dist + 200
    sc.camera = cam
    sc.render.engine = "BLENDER_WORKBENCH"
    sc.display.shading.light = "STUDIO"
    sc.display.shading.color_type = "TEXTURE"
    sc.display.shading.show_shadows = False
    sc.display.shading.show_cavity = True
    sc.view_settings.view_transform = "Standard"
    sc.render.resolution_x, sc.render.resolution_y = w, h
    sc.render.resolution_percentage = 100
    sc.render.image_settings.file_format = "PNG"
    sc.render.filepath = path
    ref = bpy.data.collections.get("_REF")
    if ref:
        ref.hide_render = True
    bpy.ops.render.render(write_still=True)
    bpy.data.objects.remove(cam, do_unlink=True)


def make_shots(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    for asset, cat, fname, pre, v, mg, w, h, clip in SHOTS:
        blend = os.path.join(REPO, "ArtSource", cat, asset + ".blend")
        if not os.path.exists(blend):
            print("[shot] 缺", blend)
            continue
        bpy.ops.wm.open_mainfile(filepath=blend)
        shot(os.path.join(out_dir, fname), pre, v, mg, w, h, clip)
        print("[shot]", fname)


if __name__ == "__main__":
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    if "--shots" in argv:
        make_shots(os.path.abspath(argv[argv.index("--shots") + 1]))
