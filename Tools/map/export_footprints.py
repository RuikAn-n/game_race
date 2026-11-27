"""
导出明代建筑/场景件的占地包围盒 -> Data/map/ming_footprints.json（供团结里做自动间距 / 重叠检查）
=====================================================================================

用法（Blender 无界面，只读 .blend，不改任何文件）：
    /Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/map/export_footprints.py -- \
        [--out Data/map/ming_footprints.json] [--with-roc]

扫描：ArtSource/Buildings/BLD_MING_*.blend、ArtSource/Environments/ENV_MING_*.blend，
      以及第二幕场景件 ENV_WangHouse / ENV_SaltField / ENV_SaltFurnace / ENV_NorthGate_Build。
      --with-roc 时再加 BLD_ROC_*（对照同 kind 的民国模型）。

坐标全部换成**团结局部坐标**（模型旋转 0 摆放时）：x = 东(右)，y = 上，z = 北(正面方向)。
Blender -> 团结：x_u = -x_b，z_u = -y_b，y_u = z_b（与 rupu_pipeline 的 FBX 导出轴一致）。

每个资产输出（单位 m）：
  base   : 「落地占地」——z_b < BASE_H（默认 1.0 m）的顶点包围盒（台基、墙脚、门台），做建筑间不重叠检查用这个
  full   : 全部可见网格（含屋檐出挑、旗杆）的包围盒，做屋檐互相穿插检查用这个
  col    : COL_* 碰撞体包围盒（没有 COL_ 时为 null，团结里整个网格做碰撞，等同 full）
  anchors: ANCHOR_* 的局部位置（团结坐标）
  kinds  : era_kits.json 里用到这个资产的 kind；plot = 布局里该 kind 的占地 w×d（团结 x×z）；
  overhang: base 超出 plot 的距离 [西, 东, 南(背), 北(正面)]，正数 = 伸出（台阶、坡道常见）
  fits   : max(overhang) <= PLOT_TOL；不在布局里的件为 null
"""
import glob
import json
import os
import sys

import bpy

REPO = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".."))
BASE_H = 1.0
PLOT_TOL = 0.35
EXTRA_ENV = ("ENV_WangHouse", "ENV_SaltField", "ENV_SaltFurnace", "ENV_NorthGate_Build")


def to_unity(v):
    return (-v[0], v[2], -v[1])


def bbox(points):
    if not points:
        return None
    mn = [min(p[i] for p in points) for i in range(3)]
    mx = [max(p[i] for p in points) for i in range(3)]
    r = lambda a: [round(x, 3) + 0.0 for x in a]   # noqa: E731（+0.0 去掉 -0.0）
    return {"min": r(mn), "max": r(mx), "size": r([mx[i] - mn[i] for i in range(3)])}


def scan(path):
    with bpy.data.libraries.load(path) as (src, dst):
        dst.objects = list(src.objects)
    objs = [o for o in dst.objects if o is not None]
    full, base, col, anchors = [], [], [], {}
    for o in objs:
        n = o.name
        if n.startswith("REF_"):
            continue
        if o.type == "EMPTY" and n.startswith("ANCHOR_"):
            anchors[n] = [round(x, 3) + 0.0 for x in to_unity(o.matrix_world.translation)]
            continue
        if o.type != "MESH":
            continue
        mw = o.matrix_world
        pts = [mw @ v.co for v in o.data.vertices]
        if n.startswith("COL_"):
            col += [to_unity(p) for p in pts]
            continue
        full += [to_unity(p) for p in pts]
        if not n.startswith("NOCOL_"):
            base += [to_unity(p) for p in pts if p.z < BASE_H]
    for o in objs:
        bpy.data.objects.remove(o)
    for m in list(bpy.data.meshes):
        if m.users == 0:
            bpy.data.meshes.remove(m)
    return {"base": bbox(base), "full": bbox(full), "col": bbox(col), "anchors": anchors}


def main(argv):
    out = os.path.join(REPO, "Data", "map", "ming_footprints.json")
    if "--out" in argv:
        out = os.path.abspath(argv[argv.index("--out") + 1])
    files = sorted(glob.glob(os.path.join(REPO, "ArtSource", "Buildings", "BLD_MING_*.blend")))
    files += sorted(glob.glob(os.path.join(REPO, "ArtSource", "Environments", "ENV_MING_*.blend")))
    files += [os.path.join(REPO, "ArtSource", "Environments", n + ".blend") for n in EXTRA_ENV]
    if "--with-roc" in argv:
        files += sorted(glob.glob(os.path.join(REPO, "ArtSource", "Buildings", "BLD_ROC_*.blend")))

    kits = json.load(open(os.path.join(REPO, "Data", "map", "era_kits.json"), encoding="utf-8"))["kits"]
    lay = json.load(open(os.path.join(REPO, "Data", "map", "yongchang_layout.json"), encoding="utf-8"))
    plot_size = {}
    for p in lay["plots"]:
        plot_size.setdefault(p["kind"], (p["w"], p["d"]))

    assets = {}
    for f in files:
        if not os.path.exists(f):
            print("[skip] 没有", os.path.relpath(f, REPO))
            continue
        name = os.path.splitext(os.path.basename(f))[0]
        r = scan(f)
        kinds = [k["kind"] for k in kits if name in k.get("ming", []) + k.get("roc", [])]
        r["category"] = os.path.basename(os.path.dirname(f))
        r["kinds"] = kinds
        r["plot"] = None
        r["fits"] = None
        r["overhang"] = None
        if kinds and plot_size.get(kinds[0], (0, 0)) != (0, 0) and r["base"]:
            w, d = plot_size[kinds[0]]
            r["plot"] = [w, d]
            b = r["base"]
            # 超出 plot 的距离（m，正数 = 伸出）：[西 -x, 东 +x, 南(背面) -z, 北(正面) +z]
            oh = [round(v, 3) + 0.0 for v in (-w / 2 - b["min"][0], b["max"][0] - w / 2,
                                              -d / 2 - b["min"][2], b["max"][2] - d / 2)]
            r["overhang"] = oh
            r["fits"] = max(oh) <= PLOT_TOL
        assets[name] = r
        fb = r["base"]["size"] if r["base"] else None
        print(f"[fp] {name:32s} base {fb}  fits={r['fits']}  overhang={r['overhang']}")

    data = {
        "_doc": "明代建筑/场景件占地（Tools/map/export_footprints.py 生成，不手改）。团结局部坐标：x 东、y 上、z 北(正面)，"
                "模型旋转 0 时；摆放后按物体的 position / rotationY 变换。base = 离地 1 m 以下的可见网格包围盒（台基/墙脚，"
                "建筑互不重叠检查用）；full = 含屋檐的全包围盒；col = COL_* 碰撞体；plot = 布局 kind 的占地 w×d；"
                "overhang = base 超出 plot 的距离 [西,东,南(背),北(正面)]；fits = max(overhang) <= 0.35。说明见 Docs/act2_city_lod.md。",
        "base_height": BASE_H,
        "plot_tolerance": PLOT_TOL,
        "assets": assets,
    }
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=1)
    print("[OK] 写出", os.path.relpath(out, REPO), len(assets), "个资产")


if __name__ == "__main__":
    main(sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else [])
