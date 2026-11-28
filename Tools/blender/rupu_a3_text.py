"""
《入谱》第三幕 · 文字贴图（Docs/第三幕_建模清单.md §7.2）
（Blender bpy；工具函数给 rupu_a3_props / rupu_a3_env 在生成时调用，贴图存在各自资产文件夹；recipes() 另出一件 PROP_A3_Placard）

做法同 rupu_a2_text：Blender 文字对象（宋体，只烘进贴图、不分发字体）+ Workbench 平光渲遮罩，numpy 合成底色/墨色/做旧。
文字一律不进网格：贴在单独的 0..1 UV 面片上（NOCOL_TXT_* 或清单要求的固定名字），换贴图即换字。
双面件（旗、名签、纸页）背面是另一片，U 翻转，所以从背面看也是正字（清单 §11.1「背面不反字」）。

贴图（T_A3_*，都在对应资产文件夹里）：
  Flag_Wang / Flag_Tanghe / Flag_Blank（PROP_A3_WallBanner、PROP_A3_SignalFlag 用）、Unit_Blue / Unit_Red（PROP_A3_UnitMarker）、
  Placard_Huanhai / Tongshi / Zuci（PROP_A3_Placard）、NameTag_01..30（PROP_A3_NameWall / PROP_A3_NameTag）、
  BlamePage_01..03（PROP_A3_BlameBook）、RosterPage + 1941_Ink（ENV_A3_1941_InkDesk）、GrainSack（PROP_A3_GrainSack）、
  CannonManual（ENV_A3_CannonPlatform）。
"""
import math
import os

import bpy

import rupu_kit as K
import rupu_a2_text as T2

Canvas, save_tex, tex_mat, hexrgb, ink_on = T2.Canvas, T2.save_tex, T2.tex_mat, T2.hexrgb, T2.ink_on
paper_bg, wood_bg, fbm, carve, streaks = T2.paper_bg, T2.wood_bg, T2.fbm, T2.carve, T2.streaks
asset_dir, mesh_obj, quad_xz, quad_xy = T2.asset_dir, T2.mesh_obj, T2.quad_xz, T2.quad_xy


def _np():
    import numpy
    return numpy


# ====================================================================== 内容（繁体，竖排右起）
# 名墙 30 人：守城八日的阵亡者 / 死难百姓（与第二幕义师名录不重复，最后一位「無名」）
NAMES = [
    ("王汝明", "東門"), ("王大順", "東門"), ("陳阿福", "東門"), ("王叔通", "水門"), ("林阿七", "水門"),
    ("王汝良", "水門"), ("王三官", "北門"), ("周大", "北門"), ("黃阿三", "北門"), ("王長春", "東牆"),
    ("王汝成", "東牆"), ("王細弟", "東牆"), ("吳阿六", "祖祠"), ("王光明", "祖祠"), ("何三妹", "粮倉"),
    ("王阿娣", "粮倉"), ("張阿土", "粮倉"), ("王大用", "北門"), ("王五十", "北門"), ("鄭阿九", "東牆"),
    ("王汝和", "東牆"), ("王阿保", "北門"), ("李二", "北門"), ("王叔達", "瓮城"), ("王汝忠", "瓮城"),
    ("王小乙", "瓮城"), ("王光祖", "環海樓"), ("王四九", "環海樓"), ("林阿妹", "環海樓"), ("無名", "瓮城"),
]
DATE = "嘉靖庚申夏"

# 愧顽簿三页（每页一个跨页：右页标题/族规，左页条目）
BLAME_PAGES = [
    ("愧頑簿", ["族中有臨陣脫逃", "通倭賣糧私開城門者", "書名於此", "生不入祠死不入譜"], []),
    ("六月初五", ["夜半東水門閂開", "門外泊小船三隻", "倭自水道入"], ["陳某　鹽商　夜見其舟", "王執　掌門鑰", "阿貴　當夜守門"]),
    ("六月初六", ["存糧夜少三十石", "粮倉後牆有新洞"], ["陳某　私售米於船", "王執　簿上有塗改", "阿貴　母被擄於倭營"]),
]
ROSTER_TITLE = "永昌王氏族譜　守城錄"
UNIT = {"Blue": ("義", "#3e5260"), "Red": ("倭", "#9a3a2c")}
FLAGS = {"Wang": ("王", "#9a3a2c"), "Tanghe": ("湯", "#b0924a"), "Blank": (None, "#c9bfa6")}
PLACARDS = {"Huanhai": "環海樓", "Tongshi": "通市門", "Zuci": "王氏祖祠"}


# ====================================================================== 面片：双面、背面正字
def two_sided_xz(name, x0, x1, z0, z1, y, mat, t=0.002, parent=None, uv=(0, 0, 1, 1)):
    """竖立的贴字面片：<name>_Front 朝 -Y，<name>_Back 朝 +Y（U 翻转 = 背面也是正字）。返回 (前, 后)。"""
    u0, v0, u1, v1 = uv
    f = quad_xz(name + "_Front", x0, x1, z0, z1, y - t, mat, uv=uv, facing=-1, parent=parent)
    b = quad_xz(name + "_Back", x0, x1, z0, z1, y + t, mat, uv=(u1, v0, u0, v1), facing=+1, parent=parent)
    return f, b


def wavy_cloth(name, x0, x1, z0, z1, mat, nx=8, nz=6, amp=0.04, waves=1.5, parent=None, back=True, t=0.003):
    """旗面：XZ 平面（旗杆在 x0 一侧），沿 X 有正弦起伏，UV 0..1 占满；背面一片 U 翻转。返回 (前, 后)。"""
    def build(nm, sgn):
        verts, faces, uvs = [], [], []
        for j in range(nz + 1):
            for i in range(nx + 1):
                u, v = i / nx, j / nz
                x = x0 + (x1 - x0) * u
                y = amp * math.sin(u * waves * 2 * math.pi) * u + sgn * t
                verts.append((x, y, z0 + (z1 - z0) * v))
        for j in range(nz):
            for i in range(nx):
                a = j * (nx + 1) + i
                q = [a, a + 1, a + nx + 2, a + nx + 1]
                uvq = [(i / nx, j / nz), ((i + 1) / nx, j / nz), ((i + 1) / nx, (j + 1) / nz), (i / nx, (j + 1) / nz)]
                if sgn > 0:
                    q, uvq = q[::-1], [(1 - u, v) for u, v in uvq[::-1]]
                faces.append(q)
                uvs.append(uvq)
        return mesh_obj(nm, verts, faces, uvs, mat, parent)
    f = build(name if not back else name + "_Front", -1)
    b = build(name + "_Back", +1) if back else None
    return f, b


# ====================================================================== 贴图
def flag_tex(path, W, H, key, seed=3):
    text, field = FLAGS[key]
    if text is not None:
        return T2.flag_tex(path, W, H, text, field, seed=seed)
    np = _np()                                   # 无字旗：素布 + 牙边 + 旗袖，不写字
    rng = np.random.default_rng(seed)
    cv = Canvas(W, H, 1024)
    t = min(W, H) * 0.1
    cv.rect(-W / 2, -H / 2, -W / 2 + W * 0.07, H / 2, (0, 0, 1))
    cv.frame(-W / 2, -H / 2, W / 2, H / 2, t * 0.5, (0, 1, 0))
    mk = cv.render(os.path.splitext(os.path.basename(path))[0])
    base = wood_bg(rng, 1024, field, axis=0, amp=0.025)
    out = ink_on(base, mk[:, :, 1], hexrgb("#5a5246"))
    out = ink_on(out, mk[:, :, 2], hexrgb("#3a352e"))
    return save_tex(out * (0.92 + 0.12 * fbm(rng, 1024, ((4, 0.6), (12, 0.4)))[:, :, None]), path)


def unit_tex(path, key, seed=5):
    """兵牌小旗：方旗，左侧旗袖，中间一个字（蓝「義」/ 红「倭」）。"""
    ch, field = UNIT[key]
    np = _np()
    rng = np.random.default_rng(seed)
    W, H = 0.24, 0.18
    cv = Canvas(W, H, 512)
    cv.rect(-W / 2, -H / 2, -W / 2 + 0.02, H / 2, (0, 0, 1))
    cv.char(ch, 0.01, 0, 0.13, (1, 0, 0))
    mk = cv.render(os.path.splitext(os.path.basename(path))[0])
    base = wood_bg(rng, 512, field, axis=0, amp=0.02)
    out = ink_on(base, mk[:, :, 2], hexrgb("#2a2622"))
    out = ink_on(out, mk[:, :, 0], hexrgb("#e2d6bc"))
    return save_tex(out, path)


def placard_tex(path, W, H, key, seed=11):
    return T2.plaque_tex(path, W, H, PLACARDS[key], "lacquer", seed=seed)


def name_tag_tex(path, idx, W=0.05, H=0.2, seed=0):
    """木名签：竖写名字（大）+ 下方小字（殁地·日期）；第 30 个「無名」墨淡。贴图竖长方形（512×512 拉伸到 5×20 cm）。"""
    name, place = NAMES[idx]
    np = _np()
    rng = np.random.default_rng(200 + idx)
    cv = Canvas(W, H, 512, face=T2.FACE_REGULAR)
    n = len(name)
    s = min(W * 0.8, H * 0.58 / (n * 1.05))
    cv.column(name, 0, H / 2 - H * 0.08, s, (1, 0, 0), pitch=1.05, sx=1.0)
    sub = place + "歿"
    s2 = min(W * 0.32, H * 0.3 / (len(sub) * 1.05))
    cv.column(sub, 0, -H / 2 + H * 0.34, s2, (0, 1, 0), pitch=1.05)
    cv.frame(-W / 2, -H / 2, W / 2, H / 2, W * 0.05, (0, 0, 1), ty=H * 0.0125)
    mk = cv.render(os.path.splitext(os.path.basename(path))[0])
    base = wood_bg(rng, 512, "#b8a27e", axis=1, amp=0.05)
    out = ink_on(base, mk[:, :, 2], hexrgb("#8a7456"))
    ink = hexrgb("#3a3430") if name == "無名" else hexrgb("#16120f")
    out = ink_on(out, mk[:, :, 0], ink, rng=rng)
    out = ink_on(out, mk[:, :, 1] * 0.85, hexrgb("#3a2e26"), rng=rng)
    return save_tex(out, path)


def _page(cv, W, H, cols, x_right, pitch, s, ink_ch=(1, 0, 0)):
    x = x_right
    for text in cols:
        cv.column(text, x, H / 2 - H * 0.08, s, ink_ch, pitch=1.06)
        x -= pitch
    return x


def blame_tex(path, k, W=0.9, H=0.6, seed=0):
    """愧顽簿跨页（0.9×0.6 m，右页=标题/事由，左页=嫌疑条目；中缝）：黄纸、黑墨、朱笔圈点、右上「王氏宗祠」小印。"""
    title, right, left = BLAME_PAGES[k]
    np = _np()
    rng = np.random.default_rng(300 + k)
    cv = Canvas(W, H, 2048, face=T2.FACE_REGULAR)
    cv.rect(-0.004, -H / 2, 0.004, H / 2, (0, 0, 1))                                   # 中缝
    for side in (-1, 1):                                                               # 版框 + 界行
        x0, x1 = (0.025, W / 2 - 0.03) if side > 0 else (-W / 2 + 0.03, -0.025)
        cv.frame(x0, -H / 2 + 0.035, x1, H / 2 - 0.035, 0.003, (0, 0, 1))
        n = 8
        for i in range(1, n):
            x = x0 + (x1 - x0) * i / n
            cv.rect(x - 0.0008, -H / 2 + 0.035, x + 0.0008, H / 2 - 0.035, (0, 0, 1))
    pitch = (W / 2 - 0.055) / 8
    cv.column(title, W / 2 - 0.03 - pitch * 0.5, H / 2 - 0.06, 0.05, (1, 0, 0), pitch=1.1)
    _page(cv, W, H, right, W / 2 - 0.03 - pitch * 1.5, pitch, 0.03)
    if left:
        x = -0.025 - pitch * 0.5
        for e in left:
            cv.column(e, x, H / 2 - 0.06, 0.03, (1, 0, 0), pitch=1.06)
            cv.disc(x, H / 2 - 0.075, 0.022, rgb=(0, 1, 0))                             # 朱圈（嫌疑）
            x -= pitch * 1.3
        for j in range(3):                                                             # 证据纸片贴位（淡框）
            cv.frame(-W / 2 + 0.05 + j * 0.12, -H / 2 + 0.06, -W / 2 + 0.15 + j * 0.12, -H / 2 + 0.16, 0.002, (0, 1, 0))
    cv.rect(W / 2 - 0.075, H / 2 - 0.09, W / 2 - 0.045, H / 2 - 0.06, (0, 1, 0))      # 小印
    mk = cv.render(os.path.splitext(os.path.basename(path))[0])
    R, G, B = mk[:, :, 0], mk[:, :, 1], mk[:, :, 2]
    base = paper_bg(rng, 2048, "#d9c69a", aged=0.08)
    out = ink_on(base, B * 0.55, hexrgb("#8a5a3b"))
    out = ink_on(out, R, hexrgb("#15110e"), rng=rng)
    out = ink_on(out, np.clip(G - R, 0, 1) * 0.85, hexrgb("#a8402e"), rng=rng)
    return save_tex(out, path)


def roster_tex(path, W=0.5, H=0.34, seed=0):
    """1941 谱桌上摊开的族谱跨页：「守城錄」标题 + 30 个名字（与名墙同一份），旧纸、褪墨。"""
    np = _np()
    rng = np.random.default_rng(401)
    cv = Canvas(W, H, 2048, face=T2.FACE_REGULAR)
    cv.rect(-0.002, -H / 2, 0.002, H / 2, (0, 0, 1))
    cv.column(ROSTER_TITLE, W / 2 - 0.03, H / 2 - 0.03, 0.022, (1, 0, 0), pitch=1.08)
    x = W / 2 - 0.07
    for i, (nm, pl) in enumerate(NAMES):
        if i == 15:
            x = -0.03
        cv.column(nm, x, H / 2 - 0.04, 0.016, (1, 0, 0), pitch=1.06)
        cv.column(pl + "歿", x, -0.02, 0.011, (0, 1, 0), pitch=1.06)
        x -= 0.0135
    mk = cv.render(os.path.splitext(os.path.basename(path))[0])
    base = paper_bg(rng, 2048, "#cbbd9e", aged=0.12)
    out = ink_on(base, mk[:, :, 2] * 0.5, hexrgb("#7a5a40"))
    out = ink_on(out, mk[:, :, 0] * 0.9, hexrgb("#2a2420"), rng=rng)
    out = ink_on(out, mk[:, :, 1] * 0.7, hexrgb("#6a3428"), rng=rng)
    return save_tex(out, path)


def ink1941_tex(path, W=0.25, H=0.34, seed=0):
    """1941 墨迹页：王砚在新纸上誊写（前几行墨重、最后一行半干），右下角一圈雨水洇开的水渍。match cut 用。"""
    np = _np()
    rng = np.random.default_rng(402)
    cv = Canvas(W, H, 1024, face=T2.FACE_REGULAR)
    x = W / 2 - 0.025
    for k, (nm, pl) in enumerate(NAMES[:8]):
        cv.column(f"{nm}　{pl}歿", x, H / 2 - 0.03, 0.017, (1, 0, 0) if k < 7 else (0, 1, 0), pitch=1.06)
        x -= 0.026
    cv.disc(W / 2 - 0.06, -H / 2 + 0.07, 0.05, 0.04, rgb=(0, 0, 1))
    mk = cv.render(os.path.splitext(os.path.basename(path))[0])
    base = paper_bg(rng, 1024, "#e6dcc6", aged=0.03)
    stain = mk[:, :, 2] * (0.6 + 0.4 * fbm(rng, 1024, ((8, 1.0),)))
    out = base * (1 - stain[:, :, None] * 0.18)
    out = ink_on(out, mk[:, :, 0], hexrgb("#100d0b"), rng=rng)
    out = ink_on(out, mk[:, :, 1] * 0.7, hexrgb("#3a3430"), rng=rng)
    return save_tex(out, path)


def sack_tex(path, seed=0):
    """粮袋印记：麻布底，中间朱红方印「糧」，下面一行小字「王氏義倉」。"""
    np = _np()
    rng = np.random.default_rng(501)
    W = H = 0.4
    cv = Canvas(W, H, 1024)
    cv.frame(-0.11, -0.07, 0.11, 0.15, 0.012, (1, 0, 0))
    cv.char("糧", 0, 0.04, 0.17, (1, 0, 0))
    cv.row_rtl("王氏義倉", 0, -0.12, 0.045, (0, 1, 0))
    mk = cv.render(os.path.splitext(os.path.basename(path))[0])
    base = wood_bg(rng, 1024, "#a4946e", axis=0, amp=0.04)
    base = base + (streaks(rng, 1024, 1, 1024 // 40) * 0.12)[:, :, None]
    wear = 0.75 + 0.25 * fbm(rng, 1024, ((40, 1.0),))
    out = ink_on(base, mk[:, :, 0] * wear, hexrgb("#8a3428"))
    out = ink_on(out, mk[:, :, 1] * wear, hexrgb("#2a2420"))
    return save_tex(out, path)


def manual_tex(path, W=0.9, H=0.6, seed=0):
    """火炮教学图（木牌上贴纸）：三格「一 裝藥 / 二 裝彈 / 三 點火」，每格一个线描小图（炮身 + 药包 / 弹 / 火绳）。"""
    np = _np()
    rng = np.random.default_rng(601)
    cv = Canvas(W, H, 2048)
    for k, (num, cap) in enumerate((("一", "裝藥"), ("二", "裝彈"), ("三", "點火"))):
        cx = W / 3 - k * W / 3                                                       # 右起
        cv.frame(cx - W / 6 + 0.02, -H / 2 + 0.03, cx + W / 6 - 0.02, H / 2 - 0.03, 0.004, (0, 0, 1))
        cv.row_rtl(num + cap, cx, H / 2 - 0.08, 0.05, (1, 0, 0))
        cv.rect(cx - 0.11, -0.06, cx + 0.07, 0.02, (1, 0, 0))                          # 炮身
        cv.disc(cx - 0.11, -0.02, 0.05, rgb=(1, 0, 0))
        cv.disc(cx - 0.06, -0.12, 0.035, rgb=(1, 0, 0))                                # 炮车轮
        if k == 0:
            cv.rect(cx + 0.09, -0.04, cx + 0.15, 0.0, (0, 1, 0))                       # 药包
            cv.rect(cx + 0.15, -0.025, cx + 0.25, -0.015, (1, 0, 0))                   # 送药杆
        elif k == 1:
            cv.disc(cx + 0.11, -0.02, 0.025, rgb=(1, 0, 0))                            # 弹
        else:
            cv.rect(cx - 0.16, 0.02, cx - 0.155, 0.12, (1, 0, 0))                      # 火绳杆
            cv.disc(cx - 0.157, 0.13, 0.015, rgb=(0, 1, 0))                            # 火
    mk = cv.render(os.path.splitext(os.path.basename(path))[0])
    base = paper_bg(rng, 2048, "#dccca8", aged=0.07)
    out = ink_on(base, mk[:, :, 2] * 0.6, hexrgb("#6a5040"))
    out = ink_on(out, mk[:, :, 0], hexrgb("#1a1512"), rng=rng)
    out = ink_on(out, mk[:, :, 1], hexrgb("#b0402c"))
    return save_tex(out, path)


def mat_from(cat, asset, tex_name, maker, rough=0.9, **kw):
    """生成贴图（存进 Assets/Art/<cat>/<asset>/T_A3_<tex_name>_D.png）并返回贴图材质 M_A3T_<tex_name>。"""
    path = os.path.join(asset_dir(cat, asset), f"T_A3_{tex_name}_D.png")
    img = maker(path, **kw)
    return tex_mat(f"M_A3T_{tex_name}", img, rough)


# ====================================================================== PROP_A3_Placard：三块匾（环海楼 / 通市门 / 王氏祖祠）
def build_placards():
    """三块明代黑漆金字匾，各自独立子物体 Placard_<键>（板 + 正面贴字 NOCOL_TXT_<键>），原点在匾底中心，挂墙用。
    已有建筑上的匾（第二幕 rupu_a2_text）不动；这三块给第三幕夜战 / 破损场景单独摆，或替换被烧坏的匾。"""
    x = -2.4
    for key, (w, h) in (("Huanhai", (1.8, 0.7)), ("Tongshi", (1.6, 0.62)), ("Zuci", (2.0, 0.7))):
        mb = K.MB()
        mb.box(-w / 2, 0, 0, w / 2, 0.06, h, "M_Plaque")
        mb.box(-w / 2 - 0.06, -0.02, -0.06, w / 2 + 0.06, 0.08, 0.0, "M_Wood_Dark")
        mb.box(-w / 2 - 0.06, -0.02, h, w / 2 + 0.06, 0.08, h + 0.06, "M_Wood_Dark")
        board = mb.to_object(f"Placard_{key}", uv_scale=1.0)
        board.location = (x + w / 2, 0, 0)
        m = mat_from("Props", "PROP_A3_Placard", f"Placard_{key}", placard_tex, 0.6, W=w, H=h, key=key)
        quad_xz(f"NOCOL_TXT_{key}", -w / 2, w / 2, 0, h, -0.003, m, parent=board)
        x += w + 0.4


def recipes():
    return {"PROP_A3_Placard": ("Props", build_placards)}
