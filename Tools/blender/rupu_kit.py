"""
《入谱》程序化白模工具包（Blender bpy / bmesh）
================================================

给 build_yongchang.py 用的几何与材质小工具。所有尺寸单位为米。
约定（与 Docs/asset_spec.md 一致）：
  - 模型正面朝 Blender -Y；原点在地面中心（建筑）或脚底中心（道具）。
  - 颜色写在 Principled BSDF 的 Base Color（会导出）；同时写 diffuse_color 只为视口/预览好看。
  - 材质名是「语义名」（M_Roof_Tile、M_Plaster…），团结里按名字换成年代材质库（Data/map/era_materials.json）。
  - 名为 COL_* 的物体只做碰撞（团结里去掉渲染器）；名为 NOCOL_* 的物体不加碰撞。
"""
import math
from contextlib import contextmanager

import bmesh
import bpy
from mathutils import Matrix, Vector

# 预览/导出用的默认色（民国基调）。最终颜色以团结年代材质库为准。
PALETTE = {
    "M_Roof_Tile": "#3f4545", "M_Roof_Ridge": "#2b2f2f", "M_Plaster": "#cbc4b1", "M_Plaster_Lower": "#8e8d84",
    "M_Wood": "#6b5039", "M_Wood_Dark": "#3e2f24", "M_Window": "#26231f", "M_Stone_Base": "#8a897f",
    "M_Brick_Grey": "#6e6e68", "M_Brick_Red": "#874e3d", "M_Wall_Stone": "#7a7b71", "M_Wall_Top": "#a29e8f",
    "M_Wall_Red": "#8c4a3a", "M_Red_Lacquer": "#7d3a2c", "M_Sign": "#2c2a26", "M_Plaque": "#3a2a1c",
    "M_Paper": "#E8DCC8", "M_Sandbag": "#9b8f6e", "M_Metal_Roof": "#596060", "M_Thatch": "#8f7d55",
    "M_Leaf": "#4f6b45", "M_Leaf_Far": "#4a5b40", "M_Bark": "#4a3a2c", "M_Flag": "#c9c2b0", "M_Metal": "#3a3a3a",
    "M_Ground_Town": "#a59a82", "M_Ground_Grass": "#7d8a62", "M_Bank_Stone": "#6f706a", "M_Mud": "#4a4436",
    "M_Road_Stone": "#a09b8c", "M_Road_Earth": "#8d8068", "M_Water": "#4F6B6A", "M_Paddy_Water": "#6f8a7a",
    "M_Dike": "#7a7a55", "M_Salt": "#dcd8cc", "M_Hill": "#6c7a58", "M_Fire": "#C4552E",
}


def srgb_to_linear(c):
    return c / 12.92 if c <= 0.04045 else ((c + 0.055) / 1.055) ** 2.4


def hex_rgba(h, linear=True):
    h = h.lstrip("#")
    rgb = [int(h[i:i + 2], 16) / 255.0 for i in (0, 2, 4)]
    if linear:
        rgb = [srgb_to_linear(c) for c in rgb]
    return (*rgb, 1.0)


def get_mat(name):
    m = bpy.data.materials.get(name)
    if m is not None:
        return m
    m = bpy.data.materials.new(name)
    try:
        m.use_nodes = True          # Blender 5 起已默认启用，旧版本需要
    except Exception:
        pass
    hexc = PALETTE.get(name, "#888888")
    m.diffuse_color = hex_rgba(hexc)
    nt = m.node_tree
    bsdf = None
    if nt is not None:
        for n in nt.nodes:
            if n.type == "BSDF_PRINCIPLED":
                bsdf = n
        if bsdf is None:
            bsdf = nt.nodes.new("ShaderNodeBsdfPrincipled")
            out = next((n for n in nt.nodes if n.type == "OUTPUT_MATERIAL"), None) or nt.nodes.new("ShaderNodeOutputMaterial")
            nt.links.new(bsdf.outputs[0], out.inputs[0])
        bsdf.inputs["Base Color"].default_value = hex_rgba(hexc)
        bsdf.inputs["Roughness"].default_value = 0.35 if "Water" in name else 0.9
    return m


class MB:
    """网格累加器：往里加盒子、棱柱、屋顶，最后 to_object() 生成一个物体（多材质槽）。"""

    def __init__(self):
        self.v = []
        self.f = []
        self.fm = []
        self.mats = []
        self.stack = [Matrix.Identity(4)]

    # ---------------- 变换
    @contextmanager
    def at(self, x=0.0, y=0.0, z=0.0, rz=0.0, rx=0.0, ry=0.0):
        """局部变换：平移后依次绕 Z、Y、X 旋转（度）。rx/ry 默认 0，与旧调用一致。"""
        m = (self.stack[-1] @ Matrix.Translation((x, y, z)) @ Matrix.Rotation(math.radians(rz), 4, "Z")
             @ Matrix.Rotation(math.radians(ry), 4, "Y") @ Matrix.Rotation(math.radians(rx), 4, "X"))
        self.stack.append(m)
        try:
            yield
        finally:
            self.stack.pop()

    def _mi(self, name):
        if name not in self.mats:
            self.mats.append(name)
        return self.mats.index(name)

    def addv(self, pts):
        base = len(self.v)
        m = self.stack[-1]
        for p in pts:
            self.v.append(m @ Vector(p))
        return base

    def face(self, idx, mat):
        self.f.append(tuple(idx))
        self.fm.append(self._mi(mat))

    # ---------------- 基本体
    def hexa(self, p, mat, skip_bottom=False):
        """8 点六面体，顶点顺序同 box：底 0..3（逆时针），顶 4..7。"""
        b = self.addv(p)
        faces = [(4, 5, 6, 7), (0, 1, 5, 4), (1, 2, 6, 5), (2, 3, 7, 6), (3, 0, 4, 7)]
        if not skip_bottom:
            faces.append((0, 3, 2, 1))
        for fc in faces:
            self.face([b + i for i in fc], mat)

    def box(self, x0, y0, z0, x1, y1, z1, mat, skip_bottom=False):
        if x0 > x1:
            x0, x1 = x1, x0
        if y0 > y1:
            y0, y1 = y1, y0
        if z0 > z1:
            z0, z1 = z1, z0
        self.hexa([(x0, y0, z0), (x1, y0, z0), (x1, y1, z0), (x0, y1, z0),
                   (x0, y0, z1), (x1, y0, z1), (x1, y1, z1), (x0, y1, z1)], mat, skip_bottom)

    def boxc(self, cx, cy, z0, sx, sy, z1, mat):
        self.box(cx - sx / 2, cy - sy / 2, z0, cx + sx / 2, cy + sy / 2, z1, mat)

    def frustum(self, b, t, z0, z1, mat):
        """底矩形 b=(x0,y0,x1,y1) 在 z0，顶矩形 t 在 z1（用于有收分的墙体/台基）。"""
        self.hexa([(b[0], b[1], z0), (b[2], b[1], z0), (b[2], b[3], z0), (b[0], b[3], z0),
                   (t[0], t[1], z1), (t[2], t[1], z1), (t[2], t[3], z1), (t[0], t[3], z1)], mat)

    def prism(self, pts, axis, a0, a1, mat):
        """凸多边形 pts（在垂直于 axis 的平面内的 2D 坐标）沿 axis 从 a0 拉到 a1。
        axis='x': pts=(y,z)；axis='y': pts=(x,z)；axis='z': pts=(x,y)。"""
        def P(u, v, a):
            if axis == "x":
                return (a, u, v)
            if axis == "y":
                return (u, a, v)
            return (u, v, a)
        n = len(pts)
        b = self.addv([P(u, v, a0) for u, v in pts] + [P(u, v, a1) for u, v in pts])
        self.face([b + i for i in range(n)], mat)
        self.face([b + n + i for i in reversed(range(n))], mat)
        for i in range(n):
            j = (i + 1) % n
            self.face([b + i, b + j, b + n + j, b + n + i], mat)

    def cyl(self, x, y, z0, z1, r, mat, seg=8, r_top=None):
        rt = r if r_top is None else r_top
        pts0 = [(x + r * math.cos(2 * math.pi * i / seg), y + r * math.sin(2 * math.pi * i / seg), z0) for i in range(seg)]
        pts1 = [(x + rt * math.cos(2 * math.pi * i / seg), y + rt * math.sin(2 * math.pi * i / seg), z1) for i in range(seg)]
        b = self.addv(pts0 + pts1)
        self.face([b + i for i in reversed(range(seg))], mat)
        self.face([b + seg + i for i in range(seg)], mat)
        for i in range(seg):
            j = (i + 1) % seg
            self.face([b + i, b + j, b + seg + j, b + seg + i], mat)

    def ico(self, x, y, z, r, mat, sx=1.0, sy=1.0, sz=1.0, subdiv=1):
        bm = bmesh.new()
        bmesh.ops.create_icosphere(bm, subdivisions=subdiv, radius=r)
        base = len(self.v)
        m = self.stack[-1]
        for v in bm.verts:
            self.v.append(m @ Vector((x + v.co.x * sx, y + v.co.y * sy, z + v.co.z * sz)))
        for f in bm.faces:
            self.face([base + v.index for v in f.verts], mat)
        bm.free()

    # ---------------- 建筑部件
    # 微凹屋面剖面：上段陡（距脊 KU*半进深内落 KZ*举高），下段缓
    KU, KZ = 0.55, 0.70

    def _profile(self, y0, y1, z, rise):
        half = (y1 - y0) / 2
        ym = (y0 + y1) / 2
        zk = z + rise * (1 - self.KZ)
        return ym, half, zk

    def gable_fill(self, x0, x1, y0, y1, z, rise, mat="M_Plaster"):
        """山墙/屋下填充（屋脊沿 X），轮廓与 gable_roof 的微凹屋面一致，拆成两个凸块。"""
        ym, half, zk = self._profile(y0, y1, z, rise)
        ku = half * self.KU
        self.prism([(ym - half, z), (ym + half, z), (ym + ku, zk), (ym - ku, zk)], "x", x0, x1, mat)
        self.prism([(ym - ku, zk), (ym + ku, zk), (ym, z + rise)], "x", x0, x1, mat)

    def gable_roof(self, x0, x1, y0, y1, z, rise, ohf=0.6, ohs=0.3, mat="M_Roof_Tile", ridge=True,
                   ridge_mat="M_Roof_Ridge", curl=True, fill=True, t=0.22):
        """硬山/悬山屋顶（屋脊沿 X）：两段折线做出微凹屋面 + 屋脊 + 脊端起翘。"""
        ym, half, zk = self._profile(y0, y1, z, rise)
        lift = 0.12
        ku = half * self.KU
        zr = z + rise + lift
        zkl = zk + lift
        slope2 = (zk - z) / (half - ku)           # 下段坡度
        ze = z + lift - slope2 * ohf
        for s in (-1, 1):
            yk = ym + s * ku
            ya = ym + s * (half + ohf)
            self.prism([(ym, zr), (yk, zkl), (yk, zkl - t), (ym, zr - t)], "x", x0 - ohs, x1 + ohs, mat)
            self.prism([(yk, zkl), (ya, ze), (ya, ze - t * 0.8), (yk, zkl - t)], "x", x0 - ohs, x1 + ohs, mat)
        if fill:
            self.gable_fill(x0, x1, y0, y1, z, rise, mat)
        if ridge:
            self.box(x0 - ohs, ym - 0.2, zr - 0.12, x1 + ohs, ym + 0.2, zr + 0.28, ridge_mat)
            if curl:
                for xe in (x0 - ohs, x1 + ohs - 0.55):
                    self.box(xe, ym - 0.22, zr + 0.2, xe + 0.55, ym + 0.22, zr + 0.6, ridge_mat)

    def gable_roof_y(self, x0, x1, y0, y1, z, rise, ohf=0.6, ohs=0.3, mat="M_Roof_Tile", **kw):
        """屋脊沿 Y 的硬山顶。"""
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hw, hd = (x1 - x0) / 2, (y1 - y0) / 2
        with self.at(cx, cy, 0, 90):
            self.gable_roof(-hd, hd, -hw, hw, z, rise, ohf, ohs, mat, **kw)

    def gable_fill_y(self, x0, x1, y0, y1, z, rise, mat="M_Plaster"):
        cx, cy = (x0 + x1) / 2, (y0 + y1) / 2
        hw, hd = (x1 - x0) / 2, (y1 - y0) / 2
        with self.at(cx, cy, 0, 90):
            self.gable_fill(-hd, hd, -hw, hw, z, rise, mat)

    def hip(self, x0, y0, x1, y1, ze, rise, inset, mat="M_Roof_Tile"):
        """庑殿/四坡顶实体：檐口矩形在 ze，屋脊在 ze+rise，脊两端各缩进 inset。"""
        ym = (y0 + y1) / 2
        inset = min(inset, (x1 - x0) / 2 - 0.01)
        b = self.addv([(x0, y0, ze), (x1, y0, ze), (x1, y1, ze), (x0, y1, ze),
                       (x0 + inset, ym, ze + rise), (x1 - inset, ym, ze + rise)])
        self.face([b + 0, b + 3, b + 2, b + 1], mat)            # 底
        self.face([b + 0, b + 1, b + 5, b + 4], mat)            # 前坡
        self.face([b + 2, b + 3, b + 4, b + 5], mat)            # 后坡
        self.face([b + 3, b + 0, b + 4], mat)                   # 左
        self.face([b + 1, b + 2, b + 5], mat)                   # 右

    def hip_roof(self, x0, y0, x1, y1, ze, rise, inset, mat="M_Roof_Tile", ridge_mat="M_Roof_Ridge", curl=True):
        self.hip(x0, y0, x1, y1, ze, rise, inset, mat)
        ym = (y0 + y1) / 2
        zr = ze + rise
        if x1 - x0 - 2 * inset > 0.5:
            self.box(x0 + inset - 0.1, ym - 0.2, zr - 0.12, x1 - inset + 0.1, ym + 0.2, zr + 0.3, ridge_mat)
            if curl:
                for xe in (x0 + inset - 0.3, x1 - inset - 0.3):
                    self.box(xe, ym - 0.22, zr + 0.2, xe + 0.6, ym + 0.22, zr + 0.75, ridge_mat)
        # 四角起翘（翼角）：小斜块
        if curl:
            for cx, cy in ((x0, y0), (x1, y0), (x1, y1), (x0, y1)):
                sx = 1 if cx > (x0 + x1) / 2 else -1
                sy = 1 if cy > ym else -1
                self.box(cx - sx * 0.6, cy - sy * 0.6, ze - 0.05, cx + sx * 0.15, cy + sy * 0.15, ze + 0.25, ridge_mat)

    def shed_roof(self, x0, x1, y_hi, y_lo, z_hi, z_lo, mat="M_Roof_Tile", t=0.18):
        """单坡顶（沿 X 拉伸），从 y_hi(高) 落到 y_lo(低)。"""
        pts = [(y_hi, z_hi), (y_lo, z_lo), (y_lo, z_lo - t), (y_hi, z_hi - t)]
        if y_lo < y_hi:
            pts = list(reversed(pts))
        self.prism(pts, "x", x0, x1, mat)

    def shed_roof_y(self, y0, y1, x_hi, x_lo, z_hi, z_lo, mat="M_Roof_Tile", t=0.18):
        pts = [(x_hi, z_hi), (x_lo, z_lo), (x_lo, z_lo - t), (x_hi, z_hi - t)]
        if x_lo < x_hi:
            pts = list(reversed(pts))
        self.prism(pts, "y", y0, y1, mat)

    def mating_wall(self, x, y0, y1, z, rise, t=0.4, mat="M_Plaster", cap="M_Roof_Ridge", outward=1):
        """马头墙（封火山墙）：在 x 处、沿 Y 的三级阶梯山墙。"""
        d = y1 - y0
        steps = [(0.0, 1 / 6, 0.75), (1 / 6, 1 / 3, 1.5), (1 / 3, 2 / 3, rise + 0.9), (2 / 3, 5 / 6, 1.5), (5 / 6, 1.0, 0.75)]
        xa, xb = (x - t, x) if outward > 0 else (x, x + t)
        for a, b, h in steps:
            ya, yb = y0 + d * a, y0 + d * b
            self.box(xa, ya, z - 0.1, xb, yb, z + h, mat)
            self.box(xa - 0.12, ya - 0.05, z + h, xb + 0.12, yb + 0.05, z + h + 0.18, cap)

    def door(self, cx, w, h, y_face, z0=0.0, mat="M_Wood_Dark", out=0.05):
        self.box(cx - w / 2, y_face - out, z0, cx + w / 2, y_face + 0.02, z0 + h, mat)

    def window(self, cx, cz, w, h, y_face, mat="M_Window", out=0.04, frame="M_Wood"):
        self.box(cx - w / 2 - 0.08, y_face - out, cz - h / 2 - 0.08, cx + w / 2 + 0.08, y_face + 0.01, cz + h / 2 + 0.08, frame)
        self.box(cx - w / 2, y_face - out - 0.02, cz - h / 2, cx + w / 2, y_face, cz + h / 2, mat)

    def window_x(self, cy, cz, w, h, x_face, sign, mat="M_Window"):
        """侧墙（法线 ±X）上的窗。sign=+1 表示面朝 +X。"""
        xa, xb = (x_face - 0.01, x_face + 0.05) if sign > 0 else (x_face - 0.05, x_face + 0.01)
        self.box(xa, cy - w / 2, cz - h / 2, xb, cy + w / 2, cz + h / 2, mat)

    def arch_window(self, cx, z0, w, h, y_face, mat="M_Window", seg=6):
        """拱窗（民国西式立面）：矩形 + 半圆顶。"""
        r = w / 2
        self.box(cx - r, y_face - 0.05, z0, cx + r, y_face + 0.01, z0 + h - r, mat)
        zc = z0 + h - r
        for i in range(seg):
            a0 = math.pi * i / seg
            a1 = math.pi * (i + 1) / seg
            pts = [(cx, zc), (cx + r * math.cos(a0), zc + r * math.sin(a0)), (cx + r * math.cos(a1), zc + r * math.sin(a1))]
            self.prism(pts, "y", y_face - 0.05, y_face + 0.01, mat)

    def arch_slab(self, x0, x1, ax0, ax1, z0, spring, ztop, y0, y1, mat, seg=8):
        """带拱洞（洞底到 z0）的墙体，洞沿 Y 贯通。用凸块拼，避免凹多边形。"""
        self.box(x0, y0, z0, ax0, y1, ztop, mat)
        self.box(ax1, y0, z0, x1, y1, ztop, mat)
        cx, r = (ax0 + ax1) / 2, (ax1 - ax0) / 2
        if spring + r > ztop - 0.05:
            r = max(0.3, ztop - 0.05 - spring)
        for i in range(seg):
            a0 = math.pi - math.pi * i / seg
            a1 = math.pi - math.pi * (i + 1) / seg
            p0 = (cx + (ax1 - ax0) / 2 * math.cos(a0), spring + r * math.sin(a0))
            p1 = (cx + (ax1 - ax0) / 2 * math.cos(a1), spring + r * math.sin(a1))
            self.prism([p0, p1, (p1[0], ztop), (p0[0], ztop)], "y", y0, y1, mat)
        # 拱脚以下两侧墙面已由墩子提供；洞口上方补一块到拱脚（墩子之间 spring 以下是空的）

    def crenels(self, x0, x1, y0, y1, z0, ztop, mat, merlon=1.3, gap=0.7, axis="x"):
        """垛口：沿 axis 在 [x0,x1] 内排垛（z0 起到 ztop）。axis='y' 时 x0/x1 表示 y 范围、y0/y1 表示 x 范围。"""
        L = x1 - x0
        n = max(1, int((L + gap) // (merlon + gap)))
        used = n * merlon + (n - 1) * gap
        s = x0 + (L - used) / 2
        for i in range(n):
            a = s + i * (merlon + gap)
            if axis == "x":
                self.box(a, y0, z0, a + merlon, y1, ztop, mat)
            else:
                self.box(y0, a, z0, y1, a + merlon, ztop, mat)

    def railing(self, x0, x1, y, z0, h=0.9, mat="M_Wood_Dark", axis="x", post=1.2):
        if axis == "x":
            self.box(x0, y - 0.05, z0 + h - 0.08, x1, y + 0.05, z0 + h, mat)
            self.box(x0, y - 0.04, z0 + 0.25, x1, y + 0.04, z0 + 0.32, mat)
            n = max(1, int((x1 - x0) / post))
            for i in range(n + 1):
                x = x0 + (x1 - x0) * i / n
                self.box(x - 0.06, y - 0.06, z0, x + 0.06, y + 0.06, z0 + h, mat)
        else:
            self.box(y - 0.05, x0, z0 + h - 0.08, y + 0.05, x1, z0 + h, mat)
            self.box(y - 0.04, x0, z0 + 0.25, y + 0.04, x1, z0 + 0.32, mat)
            n = max(1, int((x1 - x0) / post))
            for i in range(n + 1):
                x = x0 + (x1 - x0) * i / n
                self.box(y - 0.06, x - 0.06, z0, y + 0.06, x + 0.06, z0 + h, mat)

    # ---------------- 输出
    def to_object(self, name, uv_scale=2.0, collection=None):
        me = bpy.data.meshes.new(name)
        bm = bmesh.new()
        vs = [bm.verts.new(v) for v in self.v]
        bm.verts.ensure_lookup_table()
        for idx, mi in zip(self.f, self.fm):
            try:
                f = bm.faces.new([vs[i] for i in idx])
                f.material_index = mi
            except ValueError:
                pass   # 重复面
        bmesh.ops.remove_doubles(bm, verts=bm.verts, dist=1e-5)
        bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
        box_uv(bm, uv_scale)
        bm.to_mesh(me)
        bm.free()
        for m in self.mats:
            me.materials.append(get_mat(m))
        for p in me.polygons:
            p.use_smooth = False
        ob = bpy.data.objects.new(name, me)
        (collection or bpy.context.scene.collection).objects.link(ob)
        return ob


def box_uv(bm, scale=2.0):
    """世界尺度盒式投影：每 scale 米一个贴图周期，所有资产纹素密度一致。"""
    uv = bm.loops.layers.uv.verify()
    for f in bm.faces:
        n = f.normal
        ax = max(range(3), key=lambda i: abs(n[i]))
        a, b = [(1, 2), (0, 2), (0, 1)][ax]
        for l in f.loops:
            co = l.vert.co
            l[uv].uv = (co[a] / scale, co[b] / scale)


def clear_scene_keep_ref():
    ref = bpy.data.collections.get("_REF")
    keep = set(ref.all_objects) if ref else set()
    for o in list(bpy.context.scene.objects):
        if o not in keep:
            bpy.data.objects.remove(o, do_unlink=True)
    for me in list(bpy.data.meshes):
        if me.users == 0:
            bpy.data.meshes.remove(me)
