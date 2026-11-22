#!/usr/bin/env python3
"""
永昌堡 总地图布局生成器（与年代无关的「同一套布局」）
==================================================

输出：
  Data/map/yongchang_layout.json   Blender（地形/道路/田）与团结（摆放建筑）共用的唯一数据源
  Data/map/yongchang_layout.svg    俯视预览（北在上）

坐标（全部用团结世界坐标，单位米）：
  x = 东，z = 北，y = 上；堡中心在 (0, 0)。
  rot = 绕 y 轴的偏航角（度），0 表示模块正面（Blender 的 -Y）朝北(+Z)，90 朝东，180 朝南，270 朝西。
  城墙类模块的「正面」= 朝堡外。

史料依据（大体吻合即可，见 Docs/map_yongchang.md）：
  - 堡呈长方形，南北约 738 m、东西约 445 m，墙高约 8 m，周长约 2.4–2.7 km
  - 四陆门：东「环海」（最大城楼，下有瓮城）、南「迎川」（临河）、西「镇山」（靠罗山）、北「通市」（通集市）
  - 水门四座（上河、下河南北两端各一）；敌台 12 座；外有护城河
  - 城内上河（宽约 13 m，偏西）、下河（宽约 8 m，偏东）南北贯穿
    上河向西开五浃：西宅、状元、三房、西门、上仓；下河向东开五浃：扑树、经魁、御史、板桥、圣门
  - 王氏祖祠（嘉靖二十一年，规模为堡内之冠）、布政司祠、世大夫祠、都堂第（三面临水）、状元第、王德故居
  - 堡内有水田百余亩，战时可自给
演绎（游戏需要，非史实）：东水门（板桥浃穿东墙出城）、汤和庙位置、粮仓位置、码头/盐场/哨卡位置。

平面距离按 PLAN_SCALE 压缩（建筑、城墙高度、河宽下限保持真实尺度），保证第三人称可走、俯视可读。
"""
import json
import math
import os
import random
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
OUT_JSON = os.path.join(REPO, "Data", "map", "yongchang_layout.json")
OUT_SVG = os.path.join(REPO, "Data", "map", "yongchang_layout.svg")

PLAN_SCALE = 0.5
SEED = 1558
rng = random.Random(SEED)

# ------------------------------------------------------------------ 城墙
WX, WZ = 113.0, 185.0          # 城墙中线半宽（东西 226 m，南北 370 m）
WALL_T = 5.0                   # 墙基厚
SLOT = 8.0                     # 城墙模块长度
CORNER = 10.0                  # 角台边长
WALK_H = 7.0                   # 马面/走道高度
INNER = 2.5                    # 墙中线到内墙面
OUTER = 2.5
RING_W = 5.0
# 堡内可建区（环城路内侧）
UX0, UX1, UZ0, UZ1 = -WX + INNER + 3 + RING_W + 0.5, WX - INNER - 3 - RING_W - 0.5, \
                     -WZ + INNER + 3 + RING_W + 0.5, WZ - INNER - 3 - RING_W - 0.5   # ±102, ±174

BOUNDS = (-340.0, -320.0, 330.0, 320.0)   # x0 z0 x1 z1
SEA_X = 230.0
HILL_X = -195.0                # 罗山山脚（往西地形抬升）

# 侧面：outward normal n，模块局部 +X 在世界中的方向 t，rot
SIDES = {
    "N": dict(n=(0, 1), t=(1, 0), rot=0, count=27),
    "E": dict(n=(1, 0), t=(0, -1), rot=90, count=45),
    "S": dict(n=(0, -1), t=(-1, 0), rot=180, count=27),
    "W": dict(n=(-1, 0), t=(0, 1), rot=270, count=45),
}


def slot_center(side, i):
    if side in "NS":
        return (-WX + CORNER / 2 + SLOT * i + SLOT / 2, WZ if side == "N" else -WZ)
    return (WX if side == "E" else -WX, -WZ + CORNER / 2 + SLOT * i + SLOT / 2)


# 每侧特殊模块：slot -> (kind, name, 占用格数)
SPECIAL = {
    "N": {13: ("gate_base", "通市门", 2), 8: ("watergate", "上河北水门", 1), 19: ("watergate", "下河北水门", 1),
          4: ("ditai", "北敌台·西", 1), 23: ("ditai", "北敌台·东", 1)},
    "S": {11: ("gate_base", "迎川门", 2), 8: ("watergate", "上河南水门", 1), 19: ("watergate", "下河南水门", 1),
          4: ("ditai", "南敌台·西", 1), 23: ("ditai", "南敌台·东", 1)},
    "W": {23: ("gate_base", "镇山门", 2), 10: ("ditai", "西敌台·南", 1), 36: ("ditai", "西敌台·北", 1)},
    "E": {26: ("gate_base_l", "环海门", 3), 15: ("watergate", "东水门（演绎）", 1),
          8: ("ditai", "东敌台·南", 1), 36: ("ditai", "东敌台·北", 1)},
}
GATE_TOWER = {"通市门": "gate_tower", "迎川门": "gate_tower", "镇山门": "gate_tower", "环海门": "gate_tower_huanhai"}

# ------------------------------------------------------------------ 尺寸表（局部 w=沿正面宽, d=进深）
SIZES = {
    "house_s": (10, 7), "house_l": (12, 8), "shop": (6, 10), "shop_west": (8, 12),
    "courtyard": (20, 18), "hall_small": (14, 20), "ancestral_hall": (20, 36), "temple": (16, 22),
    "granary": (20, 12), "checkpoint": (8, 8), "dock": (20, 18), "salt_shed": (12, 8),
}


def r2(v):
    return round(v, 3)


class Layout:
    def __init__(self):
        self.wall = []
        self.water = []
        self.roads = []
        self.bridges = []
        self.plots = []
        self.fields = []
        self.anchors = []
        self.trees = []
        self.poles = []
        self.steps = []
        self.occ = []          # (x0,z0,x1,z1,tag)

    # -------------------------------------------------------------- 占用
    def free(self, rect, margin=0.0, ignore=()):
        x0, z0, x1, z1 = rect
        for o in self.occ:
            if o[4] in ignore:
                continue
            if x0 < o[2] + margin and x1 > o[0] - margin and z0 < o[3] + margin and z1 > o[1] - margin:
                return False
        return True

    def block(self, rect, tag):
        self.occ.append((*rect, tag))


L = Layout()


def rect_c(cx, cz, sx, sz):
    return (cx - sx / 2, cz - sz / 2, cx + sx / 2, cz + sz / 2)


def footprint(kind, x, z, rot, size=None):
    w, d = size or SIZES[kind]
    if rot % 180 == 0:
        return rect_c(x, z, w, d)
    return rect_c(x, z, d, w)


# ------------------------------------------------------------------ 1 城墙
def build_wall():
    n = 0
    for side, sd in SIDES.items():
        i = 0
        spec = SPECIAL[side]
        while i < sd["count"]:
            if i in spec:
                kind, name, span = spec[i]
                cs = [slot_center(side, k) for k in range(i, i + span)]
                cx = sum(c[0] for c in cs) / span
                cz = sum(c[1] for c in cs) / span
                L.wall.append(dict(id=f"W{side}{i:02d}", kind=kind, x=r2(cx), z=r2(cz), y=0, rot=sd["rot"],
                                   side=side, name=name))
                if kind.startswith("gate_base"):
                    L.plots.append(dict(id=f"GT_{side}", kind=GATE_TOWER[name], x=r2(cx), z=r2(cz), y=WALK_H,
                                        rot=sd["rot"], w=0, d=0, name=name + "城楼", eras="ROC,MING"))
                i += span
            else:
                cx, cz = slot_center(side, i)
                L.wall.append(dict(id=f"W{side}{i:02d}", kind="wall_seg", x=r2(cx), z=r2(cz), y=0, rot=sd["rot"],
                                   side=side, name=""))
                i += 1
            n += 1
    # 角台：城墙接在模块局部 -X 与 -Z 两面，外侧是 +X/+Z
    for name, (sx, sz, rot) in {"东北角台": (1, 1, 0), "东南角台": (1, -1, 90), "西南角台": (-1, -1, 180),
                                "西北角台": (-1, 1, 270)}.items():
        L.wall.append(dict(id="WC_" + name, kind="corner_tower", x=WX * sx, z=WZ * sz, y=0, rot=rot, side="C", name=name))
    # 瓮城：贴在环海门外
    L.wall.append(dict(id="W_Wengcheng", kind="wengcheng", x=WX + OUTER, z=40.0, y=0, rot=90, side="E", name="环海门瓮城"))

    # 马道（登城坡道），模块局部 +X 方向抬升，紧贴内墙面
    def ramp_near(side, along_center, half_len, tag):
        sd = SIDES[side]
        t, nn = sd["t"], sd["n"]
        if side in "NS":
            p = (along_center, WZ if side == "N" else -WZ)
        else:
            p = (WX if side == "E" else -WX, along_center)
        # 放在 gate 的 -t 一侧，向 +t 抬升到门边
        off = half_len + 2 + 7
        cx = p[0] - t[0] * off - nn[0] * 4
        cz = p[1] - t[1] * off - nn[1] * 4
        L.wall.append(dict(id="WR_" + tag, kind="wall_ramp", x=r2(cx), z=r2(cz), y=0, rot=sd["rot"], side=side,
                           name="马道·" + tag))

    ramp_near("N", 4, 8, "通市门")
    ramp_near("S", -12, 8, "迎川门")
    ramp_near("W", 12, 8, "镇山门")
    ramp_near("E", 40, 12, "环海门")
    ramp_near("N", -84, 0, "西北")
    ramp_near("S", 84, 0, "东南")
    ramp_near("W", 140, 0, "西北")
    ramp_near("E", -140, 0, "东南")
    # 城墙及墙内外缓冲带整体占用
    L.block((-WX - CORNER / 2 - 0.5, -WZ - 9, WX + CORNER / 2 + 0.5, -WZ + INNER + 3), "wall")
    L.block((-WX - CORNER / 2 - 0.5, WZ - INNER - 3, WX + CORNER / 2 + 0.5, WZ + 9), "wall")
    L.block((-WX - 9, -WZ, -WX + INNER + 3, WZ), "wall")
    L.block((WX - INNER - 3, -WZ, WX + 9, WZ), "wall")
    L.block((WX + OUTER, 40 - 14.5, WX + OUTER + 18.5, 40 + 14.5), "wall")


# ------------------------------------------------------------------ 2 水系
def W(id_, name, kind, x0, z0, x1, z1, bottom):
    L.water.append(dict(id=id_, name=name, kind=kind, x0=x0, z0=z0, x1=x1, z1=z1, bottom=bottom))
    L.block((x0, z0, x1, z1), "water")


WEST_JIA = [("西宅浃", 140), ("状元浃", 85), ("三房浃", 45), ("西门浃", -8), ("上仓浃", -110)]
EAST_JIA = [("扑树浃", 150), ("经魁浃", 95), ("御史浃", 0), ("圣门浃", -130)]


def build_water():
    W("WT_ShangHe", "上河", "canal", -43, -205, -37, 200, -1.6)
    W("WT_XiaHe", "下河", "canal", 46, -205, 50, 200, -1.6)
    for i, (nm, z) in enumerate(WEST_JIA):
        W(f"WT_JW{i}", nm, "jia", -98, z - 1.5, -40, z + 1.5, -1.5)
    for i, (nm, z) in enumerate(EAST_JIA):
        W(f"WT_JE{i}", nm, "jia", 48, z - 1.5, 98, z + 1.5, -1.5)
    W("WT_JE_Banqiao", "板桥浃（经东水门出城）", "jia", 48, -58, 145, -54, -1.6)
    W("WT_Basin", "东水门内塘", "pond", 84, -64, 100, -48, -1.8)
    W("WT_MoatN", "北护城河", "moat", -132.5, 194.5, 150, 204.5, -2.0)
    W("WT_MoatW", "西护城河", "moat", -132.5, -215, -122.5, 204.5, -2.0)
    W("WT_MoatE", "东护城河", "moat", 140, -215, 150, 204.5, -2.0)
    W("WT_River", "迎川河（南）", "river", BOUNDS[0], -215, SEA_X + 2, -197, -2.2)
    W("WT_Sea", "海", "sea", SEA_X, BOUNDS[1], BOUNDS[2], BOUNDS[3], -3.0)


# ------------------------------------------------------------------ 3 道路（中线段 + 宽度 -> 矩形）
def R(id_, name, kind, w, x0, z0, x1, z1):
    if x0 == x1:
        rect = (x0 - w / 2, min(z0, z1), x0 + w / 2, max(z0, z1))
    else:
        rect = (min(x0, x1), z0 - w / 2, max(x0, x1), z0 + w / 2)
    L.roads.append(dict(id=id_, name=name, kind=kind, w=w, x0=rect[0], z0=rect[1], x1=rect[2], z1=rect[3],
                        ax=0 if x0 == x1 else 1))   # ax=0 沿 z（南北向），1 沿 x


def P(id_, name, x0, z0, x1, z1):
    L.roads.append(dict(id=id_, name=name, kind="plaza", w=0, x0=x0, z0=z0, x1=x1, z1=z1, ax=-1))


RZ = WZ - INNER - 3 - RING_W / 2     # 177
RX = WX - INNER - 3 - RING_W / 2     # 105


def build_roads():
    R("RD_RingN", "环城路·北", "ring", RING_W, -RX - 2.5, RZ, RX + 2.5, RZ)
    R("RD_RingS", "环城路·南", "ring", RING_W, -RX - 2.5, -RZ, RX + 2.5, -RZ)
    R("RD_RingW", "环城路·西", "ring", RING_W, -RX, -RZ - 2.5, -RX, RZ + 2.5)
    R("RD_RingE", "环城路·东", "ring", RING_W, RX, -RZ - 2.5, RX, RZ + 2.5)
    R("RD_MainN", "主街（通市门—横街）", "main", 6, 4, -44, 4, RZ)
    R("RD_MainS", "南街（迎川门）", "main", 6, -12, -RZ, -12, -42)
    R("RD_CrossW", "横街·西（镇山门）", "street", 6, -RX, 12, 33, 12)
    R("RD_CrossJ", "横街·折", "street", 6, 30, 9, 30, 43)
    R("RD_CrossE", "横街·东（环海门）", "street", 6, 27, 40, RX, 40)
    R("RD_Lane110", "北巷", "lane", 4, -RX, 110, RX, 110)
    R("RD_LaneM44", "中巷", "lane", 4, -RX, -44, RX, -44)
    R("RD_LaneM140", "南巷", "lane", 4, -RX, -140, RX, -140)
    R("RD_LaneW", "西直巷", "lane", 3.5, -72, -RZ, -72, RZ)
    R("RD_LaneE", "东直巷", "lane", 3.5, 78, -RZ, 78, RZ)
    for i, x in enumerate((-44.25, -35.75)):
        R(f"RD_ShangHe{i}", "上河沿河路", "path", 2.5, x, -RZ, x, RZ)
    for i, x in enumerate((44.75, 51.25)):
        R(f"RD_XiaHe{i}", "下河沿河路", "path", 2.5, x, -RZ, x, RZ)
    # 出城路
    R("RD_OutN", "通市官道（北）", "outer_main", 6, 4, RZ, 4, BOUNDS[3])
    R("RD_OutS", "南渡路", "outer", 5, -12, BOUNDS[1], -12, -RZ)
    R("RD_OutW", "罗山路（西）", "outer", 5, HILL_X - 6, 12, -RX, 12)
    R("RD_OutE", "码头路（东）", "outer_main", 6, RX, 40, SEA_X - 4, 40)
    R("RD_OutSalt", "盐场路", "outer", 3.5, 170, 37, 170, -90)
    # 广场
    P("PZ_Zhenshan", "镇山门内广场", -102, 2, -80, 24)
    P("PZ_Zuci", "祖祠前庭", -31, 15, -9, 24)
    P("PZ_Huanhai", "环海门校场", 82, 28, 102.4, 52)
    P("PZ_Tonshi", "通市门内", -8, 160, 16, 174.4)
    P("PZ_Temple", "汤和庙前（巡游）", 0, -174.4, 24, -166)
    P("PZ_Dock", "码头前", 214, 30, SEA_X, 52)
    for r in L.roads:
        L.block((r["x0"], r["z0"], r["x1"], r["z1"]), "road")


# ------------------------------------------------------------------ 4 桥（路 ∩ 水 自动）
def bridge_kind(span, width):
    for s in (3, 4, 6, 10, 18):
        if span <= s + 0.6:
            return f"bridge_{s}{'n' if width <= 3.6 else 'w'}" if s <= 6 else f"bridge_{s}w", s
    return "bridge_18w", 18


def build_bridges():
    n = 0
    for r in L.roads:
        if r["ax"] < 0:
            continue
        for w in L.water:
            if w["kind"] == "sea":
                continue
            x0, z0 = max(r["x0"], w["x0"]), max(r["z0"], w["z0"])
            x1, z1 = min(r["x1"], w["x1"]), min(r["z1"], w["z1"])
            if x1 - x0 <= 0.01 or z1 - z0 <= 0.01:
                continue
            span = (z1 - z0) if r["ax"] == 0 else (x1 - x0)
            other = (x1 - x0) if r["ax"] == 0 else (z1 - z0)
            if other < r["w"] - 0.01:    # 路只擦到水边，不跨
                continue
            kind, s = bridge_kind(span, r["w"])
            cx, cz = (x0 + x1) / 2, (z0 + z1) / 2
            L.bridges.append(dict(id=f"BR{n:03d}", kind=kind, x=r2(cx), z=r2(cz), rot=0 if r["ax"] == 0 else 90,
                                  span=s, road=r["id"], water=w["id"], name=f"{w['name']}·{r['name']}"))
            n += 1


# ------------------------------------------------------------------ 5 地标
def landmark(id_, kind, name, x, z, rot, eras="ROC,MING", y=0.0):
    fp = footprint(kind, x, z, rot)
    w, d = SIZES[kind]
    L.plots.append(dict(id=id_, kind=kind, x=r2(x), z=r2(z), y=y, rot=rot, w=w, d=d, name=name, eras=eras))
    L.block(fp, "landmark")


def build_landmarks():
    landmark("LM_Zuci", "ancestral_hall", "王氏祖祠（大宗祠）", -20, 42, 180)
    landmark("LM_Temple", "temple", "汤和庙（演绎位置）", 12, -155, 180)
    landmark("LM_Granary1", "granary", "上仓·东仓（演绎）", -88, -97, 180)
    landmark("LM_Granary2", "granary", "上仓·西仓（演绎）", -58, -97, 180)
    landmark("LM_Buzhengsi", "hall_small", "布政司祠", 25, 80, 180)
    landmark("LM_Shidafu", "hall_small", "世大夫祠", 25, -100, 180)
    landmark("LM_Zhuangyuan", "hall_small", "状元第", -58, 98, 180)
    landmark("LM_Dutang", "hall_small", "都堂第（三面临水）", 64, -10, 270)
    landmark("LM_WangDe", "courtyard", "王德故居", 33, 135, 90)
    landmark("LM_WangShugao", "courtyard", "王叔杲宅（墙外）", 60, 232, 180)
    landmark("LM_CP_North", "checkpoint", "日伪哨卡·通市门外", 13, 212, 270, eras="ROC")
    landmark("LM_CP_East", "checkpoint", "日伪哨卡·码头路", 160, 47, 180, eras="ROC")
    landmark("LM_Dock", "dock", "永强码头", 236, 40, 90)
    landmark("LM_Salt1", "salt_shed", "盐场灶舍", 172, -80, 180)
    landmark("LM_Salt2", "salt_shed", "盐场卤舍", 202, -80, 180)


# ------------------------------------------------------------------ 6 田（水田 / 盐田）
def field(id_, kind, name, rect, cw, cd, dike=0.8):
    x0, z0, x1, z1 = rect
    cells = []
    nx = max(1, int((x1 - x0 + dike) // (cw + dike)))
    nz = max(1, int((z1 - z0 + dike) // (cd + dike)))
    # 把余量平分到格子
    cw2 = (x1 - x0 - dike * (nx - 1)) / nx
    cd2 = (z1 - z0 - dike * (nz - 1)) / nz
    for i in range(nx):
        for j in range(nz):
            cx0 = x0 + i * (cw2 + dike)
            cz0 = z0 + j * (cd2 + dike)
            c = (cx0, cz0, cx0 + cw2, cz0 + cd2)
            if L.free(c, 0.6):
                cells.append(dict(x0=r2(c[0]), z0=r2(c[1]), x1=r2(c[2]), z1=r2(c[3])))
    if not cells:
        return
    L.fields.append(dict(id=id_, kind=kind, name=name, x0=x0, z0=z0, x1=x1, z1=z1, cells=cells))
    for c in cells:
        L.block((c["x0"], c["z0"], c["x1"], c["z1"]), "field")


def build_inner_fields():
    field("FD_InNE1", "paddy", "堡内水田·东北", (54, 114, 75.5, 146), 10, 7.5)
    field("FD_InNE2", "paddy", "堡内水田·东北", (80.5, 114, 100, 146), 9, 7.5)
    field("FD_InSW1", "paddy", "堡内水田·西南", (-100, -172, -75, -144), 12, 6.5)
    field("FD_InSW2", "paddy", "堡内水田·西南", (-69, -172, -47, -144), 10, 6.5)
    field("FD_Salt", "salt", "盐田", (156, -192, 222, -90), 7, 7, 0.6)


def build_outer_fields():
    field("FD_OutN_W", "paddy", "北郊水田", (-188, 214, -20, 316), 12, 9)
    field("FD_OutN_E", "paddy", "北郊水田", (28, 214, 222, 316), 12, 9)
    field("FD_OutW_N", "paddy", "西郊水田（罗山脚）", (HILL_X + 8, 22, -140, 192), 10, 9)
    field("FD_OutW_S", "paddy", "西郊水田（罗山脚）", (HILL_X + 8, -192, -140, 2), 10, 9)
    field("FD_OutS_W", "paddy", "南岸水田", (-188, -316, -22, -224), 12, 9)
    field("FD_OutS_E", "paddy", "南岸水田", (-2, -316, 222, -224), 12, 9)
    field("FD_OutE_N", "paddy", "海塘内水田", (156, 60, 222, 190), 10, 9)


# ------------------------------------------------------------------ 7 沿街填房
FRONTAGE = {
    "main": dict(mix=[("shop", .6), ("shop_west", .15), ("house_l", .25)], gap=(0.9, 1.6), skip=0.03),
    "street": dict(mix=[("shop", .4), ("house_l", .4), ("shop_west", .1), ("house_s", .1)], gap=(1.0, 2.0), skip=0.05),
    "outer_main": dict(mix=[("shop", .5), ("house_l", .3), ("shop_west", .2)], gap=(1.0, 3.0), skip=0.15),
    "path": dict(mix=[("house_s", .5), ("house_l", .4), ("courtyard", .1)], gap=(1.0, 2.5), skip=0.12),
    "lane": dict(mix=[("house_s", .45), ("house_l", .35), ("courtyard", .2)], gap=(1.0, 2.5), skip=0.12),
    "ring": dict(mix=[("house_s", .6), ("house_l", .3), ("courtyard", .1)], gap=(1.2, 3.0), skip=0.25),
    "outer": dict(mix=[("house_s", .65), ("courtyard", .2), ("house_l", .15)], gap=(4.0, 16.0), skip=0.35),
}


def pick(mix):
    r = rng.random()
    acc = 0
    for k, p in mix:
        acc += p
        if r <= acc:
            return k
    return mix[-1][0]


def inside_town(rect):
    return rect[0] >= UX0 and rect[2] <= UX1 and rect[1] >= UZ0 and rect[3] <= UZ1


def outside_ok(rect):
    fort = (-WX - 20, -WZ - 30, WX + 38, WZ + 20)
    if rect[0] < fort[2] and rect[2] > fort[0] and rect[1] < fort[3] and rect[3] > fort[1]:
        return False
    return rect[0] > HILL_X + 4 and rect[2] < SEA_X - 6 and rect[1] > BOUNDS[1] + 4 and rect[3] < BOUNDS[3] - 4


ROT_FACING = {(0, 1): 0, (1, 0): 90, (0, -1): 180, (-1, 0): 270}   # 正面朝向 -> rot


def fill_frontage(road, cfg, region_ok, setback=0.4):
    n = 0
    ax = road["ax"]
    if ax < 0:
        return 0
    if ax == 0:   # 南北向路：两侧在 ±x
        sides = [((1, 0), road["x1"]), ((-1, 0), road["x0"])]
        t0, t1 = road["z0"], road["z1"]
    else:
        sides = [((0, 1), road["z1"]), ((0, -1), road["z0"])]
        t0, t1 = road["x0"], road["x1"]
    for v, edge in sides:
        facing = (-v[0], -v[1])
        rot = ROT_FACING[facing]
        t = t0 + rng.uniform(0, 2)
        while t < t1:
            kind = pick(cfg["mix"])
            w, d = SIZES[kind]
            along = t + w / 2
            if along + w / 2 > t1:
                break
            off = edge + (v[0] + v[1]) * (setback + d / 2)
            if ax == 0:
                x, z = off, along
            else:
                x, z = along, off
            fp = footprint(kind, x, z, rot)
            if region_ok(fp) and L.free(fp, 0.9, ignore=("road",)) and L.free(fp, 0.1) and rng.random() > cfg["skip"]:
                L.plots.append(dict(id=f"P{len(L.plots):04d}", kind=kind, x=r2(x), z=r2(z), y=0, rot=rot,
                                    w=w, d=d, name="", eras="ROC,MING" if kind != "shop_west" else "ROC,MING"))
                L.block(fp, "plot")
                n += 1
                t += w + rng.uniform(*cfg["gap"])
            else:
                t += 1.5
    return n


def build_plots():
    order = ["main", "street", "outer_main", "path", "lane", "ring", "outer"]
    for k in order:
        for r in L.roads:
            if r["kind"] != k:
                continue
            region = inside_town if not k.startswith("outer") else outside_ok
            fill_frontage(r, FRONTAGE[k], region)
    # 堡内空地：院落/小屋（留出菜园和空地）
    for _ in range(900):
        kind = "courtyard" if rng.random() < 0.45 else rng.choice(["house_s", "house_l"])
        rot = rng.choice([180, 180, 180, 0, 90, 270])
        x = rng.uniform(UX0, UX1)
        z = rng.uniform(UZ0, UZ1)
        fp = footprint(kind, x, z, rot)
        if inside_town(fp) and L.free(fp, 2.2, ignore=("road",)) and L.free(fp, 0.6):
            L.plots.append(dict(id=f"P{len(L.plots):04d}", kind=kind, x=r2(x), z=r2(z), y=0, rot=rot,
                                w=SIZES[kind][0], d=SIZES[kind][1], name="", eras="ROC,MING"))
            L.block(fp, "plot")


# ------------------------------------------------------------------ 8 河埠头、树、电线杆、锚点
def build_steps():
    # 上河两岸每 ~45m 一处；护城河/南河在城门边各一处（取水点）
    zs = [-150, -100, -60, -20, 30, 70, 125, 160]
    for i, z in enumerate(zs):
        for side, x, rot in (("W", -43 + 1.2, 90), ("E", -37 - 1.2, 270)):
            fp = rect_c(x, z, 2.4, 4.2)
            if L.free(fp, 0.3, ignore=("water", "road")):
                L.steps.append(dict(id=f"ST_SH{i}{side}", kind="canal_steps", x=x, z=z, rot=rot, name="上河河埠头"))
                L.block(fp, "steps")
    extra = [("ST_MoatN", 20, 194.5 + 1.2, 0, "北护城河取水埠"),
             ("ST_River", 4, -197 - 1.2, 180, "迎川河取水埠"),
             ("ST_MoatW", -122.5 - 1.2, -6, 270, "西护城河取水埠"),
             ("ST_MoatE", 140 + 1.2, 20, 90, "东护城河取水埠"),
             ("ST_Basin", 92, -48 - 1.2, 180, "东水门内塘埠头")]
    for id_, x, z, rot, nm in extra:
        L.steps.append(dict(id=id_, kind="canal_steps", x=r2(x), z=r2(z), rot=rot, name=nm))
    # 修正：正面朝水。北护城河南岸：水在北 -> rot 0；南河北岸：水在南 -> 180；西河东岸：水在西 -> 270；东河西岸：水在东 -> 90；内塘北岸：水在南 -> 180
    fix = {"ST_MoatN": 0, "ST_River": 180, "ST_MoatW": 270, "ST_MoatE": 90, "ST_Basin": 180}
    for s in L.steps:
        if s["id"] in fix:
            s["rot"] = fix[s["id"]]


def build_trees():
    def try_tree(x0, z0, x1, z1, n, kinds, margin=2.5):
        k = 0
        for _ in range(n * 30):
            if k >= n:
                break
            x, z = rng.uniform(x0, x1), rng.uniform(z0, z1)
            kind = rng.choice(kinds)
            r = 3.2 if kind == "tree_camphor" else 1.6
            fp = rect_c(x, z, r * 2, r * 2)
            if L.free(fp, margin * 0.3):
                L.trees.append(dict(kind=kind, x=r2(x), z=r2(z), rot=rng.randrange(0, 360), s=r2(rng.uniform(0.85, 1.25))))
                L.block(fp, "tree")
                k += 1
    # 地标旁的古樟
    for x, z in ((-34, 26), (-6, 26), (-2, -168), (26, -168), (-104, 20), (100, 50)):
        if L.free(rect_c(x, z, 5, 5), 0):
            L.trees.append(dict(kind="tree_camphor", x=x, z=z, rot=rng.randrange(0, 360), s=1.2))
            L.block(rect_c(x, z, 5, 5), "tree")
    try_tree(UX0, UZ0, UX1, UZ1, 90, ["tree_camphor", "tree_small", "tree_small"])
    try_tree(-WX - 8, -WZ - 8, WX + 30, WZ + 8, 40, ["tree_small"], 1.0)      # 墙外缓冲带
    try_tree(HILL_X, BOUNDS[1] + 5, SEA_X - 8, BOUNDS[3] - 5, 260, ["tree_camphor", "tree_small"])


def build_poles():
    # 民国电线杆：主街东侧、通市官道、码头路
    chains = [
        ("PL_Main", [(6.6, z) for z in range(-40, 178, 28)]),
        ("PL_OutN", [(6.6, z) for z in range(206, 320, 30)]),
        ("PL_Cross", [(x, 14.6) for x in range(-100, 30, 25)]),
        ("PL_OutE", [(x, 42.6) for x in range(154, 226, 24)]),
    ]
    for id_, pts in chains:
        L.poles.append(dict(id=id_, eras="ROC", points=[dict(x=r2(p[0]), z=r2(p[1])) for p in pts]))


def build_anchors():
    A = lambda id_, x, y, z, rot, note: L.anchors.append(dict(id=id_, x=r2(x), y=r2(y), z=r2(z), rot=rot, note=note))
    for w in L.wall:
        if w["kind"].startswith("gate_base"):
            nm = w["name"]
            A(f"anchor_gate_{w['side']}", w["x"], 0, w["z"], w["rot"], nm + " 门洞（门扇/闸挂点）")
            A(f"anchor_gatetop_{w['side']}", w["x"], WALK_H, w["z"], w["rot"], nm + " 城楼（旗号/指挥）")
        if w["kind"] == "watergate":
            A(f"anchor_watergate_{w['id']}", w["x"], -0.9, w["z"], w["rot"], w["name"] + "（闸门挂点）")
        if w["kind"] in ("ditai", "corner_tower"):
            sx, sz = SIDES.get(w["side"], dict(n=(0, 0)))["n"] if w["side"] in SIDES else (0, 0)
            A(f"anchor_cannon_{w['id']}", w["x"] + sx * 4, WALK_H, w["z"] + sz * 4, w["rot"], w["name"] + " 火炮位")
    A("anchor_zuci_door", -20, 0, 24, 180, "祖祠正门")
    A("anchor_sandtable", -20, 0, 40, 180, "祖祠内沙盘（第二幕）")
    A("anchor_temple_front", 12, 0, -169, 180, "汤和庙前（巡游起点）")
    A("anchor_granary", -73, 0, -104, 180, "粮仓（第 6 波）")
    A("anchor_paddy_inner", 77, 0, 130, 0, "堡内水田（分粮）")
    A("anchor_muster_huanhai", 92, 0, 40, 90, "环海门校场")
    A("anchor_watergate_arena", 92, 0, -56, 90, "东水门内塘（Boss 赤焰）")
    A("anchor_wengcheng_arena", WX + 11.5, 0, 40, 90, "瓮城（Boss 鬼倭 第 3 阶段）")
    A("anchor_dock", 230, 0.3, 40, 90, "码头（1941 运输线）")
    A("anchor_saltfield", 190, 0, -120, 180, "盐场")
    A("anchor_wang_shugao_house", 60, 0, 222, 180, "王叔杲宅门（宅院抉择）")
    A("spawn_1941", 222, 0.1, 40, 270, "1941 归堡：码头下船")
    A("spawn_1560", -20, 0.1, 18, 0, "1560：祖祠前庭")
    A("enemy_sea", 300, 0, 40, 270, "倭寇登陆（海面/火船）")
    A("enemy_north_road", 4, 0, 312, 180, "北面官道来敌")
    A("enemy_river", -12, 0, -300, 0, "南岸来敌")


def build_meta():
    return dict(
        name="永昌堡（Yongchang Fort）总地图布局",
        version=1,
        seed=SEED,
        plan_scale=PLAN_SCALE,
        notes="平面按 0.5 压缩；墙高/建筑/人物为真实尺度。x=东 z=北，单位米。由 Tools/map/gen_layout.py 生成，勿手改。",
        wall=dict(half_x=WX, half_z=WZ, thickness=WALL_T, slot=SLOT, corner=CORNER, walk_height=WALK_H),
        town=dict(x0=UX0, z0=UZ0, x1=UX1, z1=UZ1),
        bounds=dict(x0=BOUNDS[0], z0=BOUNDS[1], x1=BOUNDS[2], z1=BOUNDS[3]),
        sea_x=SEA_X, hill_x=HILL_X, water_level=-0.9,
    )


# ------------------------------------------------------------------ SVG 预览
def write_svg(data):
    b = data["meta"]["bounds"]
    s = 1.4
    W_, H_ = (b["x1"] - b["x0"]) * s, (b["z1"] - b["z0"]) * s
    X = lambda x: (x - b["x0"]) * s
    Z = lambda z: (b["z1"] - z) * s
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{W_:.0f}" height="{H_:.0f}" '
           f'viewBox="0 0 {W_:.0f} {H_:.0f}" font-family="PingFang SC, sans-serif">',
           f'<rect width="100%" height="100%" fill="#cfc6ad"/>',
           f'<rect x="{X(b["x0"])}" y="0" width="{(data["meta"]["hill_x"] - b["x0"]) * s}" height="{H_}" fill="#8f9a7c"/>']

    def rect(x0, z0, x1, z1, fill, extra=""):
        out.append(f'<rect x="{X(x0):.1f}" y="{Z(z1):.1f}" width="{(x1 - x0) * s:.1f}" height="{(z1 - z0) * s:.1f}" fill="{fill}" {extra}/>')

    for f in data["fields"]:
        for c in f["cells"]:
            rect(c["x0"], c["z0"], c["x1"], c["z1"], "#9fb39a" if f["kind"] == "paddy" else "#e9e6dc")
    for w in data["water"]:
        rect(w["x0"], w["z0"], w["x1"], w["z1"], "#4F6B6A")
    for r in data["roads"]:
        rect(r["x0"], r["z0"], r["x1"], r["z1"], {"main": "#b8ab90", "street": "#b8ab90", "plaza": "#c2b69c",
                                                   "outer_main": "#b8ab90"}.get(r["kind"], "#a99c80"))
    for wp in data["wall"]:
        k = wp["kind"]
        if k == "corner_tower":
            rect(wp["x"] - 5, wp["z"] - 5, wp["x"] + 5, wp["z"] + 5, "#3a3a36")
            continue
        if k == "wall_ramp":
            ln, th = 14, 3
        elif k == "wengcheng":
            ln, th = 28, 18
        else:
            ln = {"gate_base": 16, "gate_base_l": 24}.get(k, 8)
            th = {"gate_base": 7, "gate_base_l": 9, "ditai": 5}.get(k, 5)
        rot = wp["rot"]
        cx, cz = wp["x"], wp["z"]
        if k == "ditai":
            sd = SIDES[wp["side"]]["n"]
            rect(*(lambda c: c)(rect_c(cx + sd[0] * 4.25, cz + sd[1] * 4.25, 8 if rot % 180 == 0 else 6, 6 if rot % 180 == 0 else 8)), "#55554d")
        if k == "wengcheng":
            rect(cx, cz - 14, cx + 18, cz + 14, "#55554d")
            rect(cx, cz - 10, cx + 14, cz + 10, "#cfc6ad")
            continue
        sx, sz = (ln, th) if rot % 180 == 0 else (th, ln)
        col = {"gate_base": "#8A5A3B", "gate_base_l": "#C4552E", "watergate": "#2f4a49", "wall_ramp": "#77776d"}.get(k, "#4a4a44")
        rect(*rect_c(cx, cz, sx, sz), col)
    for br in data["bridges"]:
        ln = br["span"] + 2
        wd = 3.2 if br["kind"].endswith("n") else 6.4
        sx, sz = (wd, ln) if br["rot"] == 0 else (ln, wd)
        rect(*rect_c(br["x"], br["z"], sx, sz), "#d9d2bf", 'stroke="#555" stroke-width="0.5"')
    colors = {"ancestral_hall": "#8A5A3B", "temple": "#C4552E", "hall_small": "#9a6a4b", "granary": "#7a6a4a",
              "checkpoint": "#5E6B5A", "dock": "#6e5a40", "salt_shed": "#a99", "gate_tower": "#8A5A3B",
              "gate_tower_huanhai": "#C4552E", "shop": "#6f6a62", "shop_west": "#7d6f63", "courtyard": "#56595a",
              "house_s": "#5f6262", "house_l": "#55585a"}
    for p in data["plots"]:
        if p["w"] == 0:
            continue
        fp = footprint(p["kind"], p["x"], p["z"], p["rot"], (p["w"], p["d"]))
        rect(*fp, colors.get(p["kind"], "#666"))
        # 正面标记
        fx = {0: (0, 1), 90: (1, 0), 180: (0, -1), 270: (-1, 0)}[p["rot"]]
        hw = (p["d"] / 2) if True else 0
        out.append(f'<circle cx="{X(p["x"] + fx[0] * hw * 0.8):.1f}" cy="{Z(p["z"] + fx[1] * hw * 0.8):.1f}" r="1.2" fill="#E8DCC8"/>')
    for t in data["trees"]:
        out.append(f'<circle cx="{X(t["x"]):.1f}" cy="{Z(t["z"]):.1f}" r="{(3.0 if t["kind"] == "tree_camphor" else 1.5) * s * t["s"]:.1f}" fill="#3f5a3a" opacity="0.8"/>')
    for st in data["steps"]:
        out.append(f'<circle cx="{X(st["x"]):.1f}" cy="{Z(st["z"]):.1f}" r="2" fill="#E8DCC8" stroke="#333" stroke-width="0.4"/>')
    for ch in data["poles"]:
        pts = " ".join(f'{X(p["x"]):.1f},{Z(p["z"]):.1f}' for p in ch["points"])
        out.append(f'<polyline points="{pts}" fill="none" stroke="#222" stroke-width="0.6" stroke-dasharray="3,2"/>')
    for a in data["anchors"]:
        out.append(f'<circle cx="{X(a["x"]):.1f}" cy="{Z(a["z"]):.1f}" r="1.6" fill="#C4552E"/>')
    # 标注
    labels = [(w["name"], w["x"], w["z"]) for w in data["wall"] if w["kind"].startswith("gate_base")]
    labels += [(w["name"], (w["x0"] + w["x1"]) / 2, min(w["z1"], 168)) for w in data["water"] if w["kind"] == "canal"]
    labels += [(p["name"], p["x"], p["z"]) for p in data["plots"] if p["name"] and p["w"] > 0]
    labels += [(w["name"], w["x0"] + 6, (w["z0"] + w["z1"]) / 2) for w in data["water"] if w["kind"] == "jia"]
    labels += [("罗山", -300, 0), ("海", 280, 120), ("迎川河", -250, -206), ("盐田", 190, -140), ("北郊水田", -100, 260)]
    for t, x, z in labels:
        out.append(f'<text x="{X(x):.1f}" y="{Z(z):.1f}" font-size="9" fill="#111" text-anchor="middle" '
                   f'stroke="#E8DCC8" stroke-width="2.2" paint-order="stroke">{t}</text>')
    out.append(f'<text x="12" y="22" font-size="16" fill="#111">永昌堡 总地图布局 v{data["meta"]["version"]}（北在上，平面 ×{PLAN_SCALE}）</text>')
    # 比例尺
    out.append(f'<rect x="12" y="34" width="{100 * s}" height="4" fill="#111"/><text x="{12 + 100 * s + 4}" y="40" font-size="10">100 m</text>')
    out.append("</svg>")
    with open(OUT_SVG, "w", encoding="utf-8") as f:
        f.write("\n".join(out))


def main():
    build_wall()
    build_water()
    build_roads()
    build_bridges()
    build_landmarks()
    build_inner_fields()
    build_steps()
    build_plots()
    build_outer_fields()
    build_trees()
    build_poles()
    build_anchors()
    data = dict(meta=build_meta(), wall=L.wall, water=L.water, roads=L.roads, bridges=L.bridges, plots=L.plots,
                fields=L.fields, steps=L.steps, trees=L.trees, poles=L.poles, anchors=L.anchors)
    os.makedirs(os.path.dirname(OUT_JSON), exist_ok=True)
    with open(OUT_JSON, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    write_svg(data)
    kinds = {}
    for p in L.plots:
        kinds[p["kind"]] = kinds.get(p["kind"], 0) + 1
    wk = {}
    for w in L.wall:
        wk[w["kind"]] = wk.get(w["kind"], 0) + 1
    bk = {}
    for b in L.bridges:
        bk[b["kind"]] = bk.get(b["kind"], 0) + 1
    print("[layout] wall", wk)
    print("[layout] plots", kinds)
    print("[layout] bridges", bk)
    print("[layout] water", len(L.water), "roads", len(L.roads), "fields", len(L.fields),
          "cells", sum(len(f["cells"]) for f in L.fields), "trees", len(L.trees), "steps", len(L.steps),
          "anchors", len(L.anchors))
    print("[layout] ->", OUT_JSON)


if __name__ == "__main__":
    main()
