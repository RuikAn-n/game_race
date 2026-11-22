"""
《入谱》Blender -> 团结引擎 资产管线
=====================================

两种用法：

1) 作为插件（推荐日常使用）
   Blender > 编辑 > 偏好设置 > 插件 > 从磁盘安装 > 选本文件
   3D 视图按 N > "入谱" 标签页：  [检查]  [导出到团结工程]

2) 命令行 / 批量（CI、批量重导）
   blender -b ArtSource/Characters/NPC_WangYan.blend \
       -P Tools/blender/rupu_pipeline.py -- --export
   blender -b any.blend -P Tools/blender/rupu_pipeline.py -- --validate
   blender -b -P Tools/blender/rupu_pipeline.py -- --new-template Characters NPC_WangYan

约定（与 Docs/asset_spec.md 一致）：
- .blend 源文件放 ArtSource/<分类>/<资产名>.blend
- 导出到   Project_rupu/Assets/Art/<分类>/<资产名>/<资产名>.fbx
- 1 Blender 单位 = 1 米；模型正面朝 Blender 的 -Y；pivot 在脚底中心
- 名为 "_REF" 的集合（参考人、参考网格）永远不导出
- 导出轴：Forward -Z / Up Y / Apply Transform -> 团结里正面朝 +Z、旋转为 0、缩放为 1
"""

bl_info = {
    "name": "入谱 Rupu Pipeline",
    "author": "Rupu Team",
    "version": (1, 0, 0),
    "blender": (4, 2, 0),
    "location": "3D View > Sidebar > 入谱",
    "description": "检查并导出 FBX 到团结引擎工程",
    "category": "Import-Export",
}

import os
import sys

import bpy
import mathutils

# ---------------------------------------------------------------- 规格

CATEGORIES = ["Characters", "Enemies", "Bosses", "Buildings", "Props", "Environments"]

# 三角面上限（策划：角色 <= 8k；其余低模）
TRI_LIMITS = {
    "Characters": 8000,
    "Enemies": 8000,
    "Bosses": 15000,
    "Buildings": 20000,
    "Props": 3000,
    "Environments": 40000,
}

# 分类 -> 资产名前缀建议（只警告，不阻塞）
NAME_PREFIX = {
    "Characters": ("NPC_", "CH_"),
    "Enemies": ("EN_",),
    "Bosses": ("BOSS_",),
    "Buildings": ("BLD_",),
    "Props": ("PROP_",),
    "Environments": ("ENV_",),
}

REF_COLLECTION = "_REF"
EPS = 1e-3


# ---------------------------------------------------------------- 路径

def repo_root_from_blend(blend_path):
    """从 .blend 路径向上找到仓库根目录（同时含 ArtSource 与 Tools）。"""
    d = os.path.dirname(os.path.abspath(blend_path))
    while True:
        if os.path.isdir(os.path.join(d, "ArtSource")) and os.path.isdir(os.path.join(d, "Tools")):
            return d
        parent = os.path.dirname(d)
        if parent == d:
            return None
        d = parent


def asset_info(blend_path):
    """返回 (repo_root, category, asset_name)；无法识别时 category 为 None。"""
    root = repo_root_from_blend(blend_path)
    name = os.path.splitext(os.path.basename(blend_path))[0]
    category = None
    parts = os.path.normpath(os.path.abspath(blend_path)).split(os.sep)
    if "ArtSource" in parts:
        i = parts.index("ArtSource")
        if i + 1 < len(parts) and parts[i + 1] in CATEGORIES:
            category = parts[i + 1]
    return root, category, name


def export_path(root, category, name):
    return os.path.join(root, "Project_rupu", "Assets", "Art", category, name, name + ".fbx")


# ---------------------------------------------------------------- 检查

def exportable_objects(scene):
    ref = bpy.data.collections.get(REF_COLLECTION)
    ref_objs = set(ref.all_objects) if ref else set()
    return [o for o in scene.objects
            if o not in ref_objs and o.type in {"MESH", "ARMATURE", "EMPTY"} and not o.hide_get()]


def tri_count(obj, depsgraph):
    ev = obj.evaluated_get(depsgraph)
    mesh = ev.to_mesh()
    try:
        mesh.calc_loop_triangles()
        return len(mesh.loop_triangles)
    finally:
        ev.to_mesh_clear()


def validate(context=None):
    """返回 (errors, warnings, stats)。errors 非空时拒绝导出。"""
    context = context or bpy.context
    scene = context.scene
    errors, warnings = [], []
    blend = bpy.data.filepath

    if not blend:
        errors.append("文件尚未保存：请先保存到 ArtSource/<分类>/<资产名>.blend")
        return errors, warnings, {}

    root, category, name = asset_info(blend)
    if root is None:
        errors.append("找不到仓库根目录（向上没有 ArtSource/ 与 Tools/）")
    elif not os.path.isdir(os.path.join(root, "Project_rupu", "Assets")):
        errors.append("团结工程还不存在：先用团结 Hub 在仓库根目录新建 Project_rupu（Universal 3D 模板）")
    if category is None:
        errors.append("文件不在 ArtSource/<分类>/ 下，分类应为：" + "/".join(CATEGORIES))
    elif not name.startswith(NAME_PREFIX[category]):
        warnings.append(f"资产名 {name} 建议以 {' 或 '.join(NAME_PREFIX[category])} 开头")

    us = scene.unit_settings
    if us.system != "METRIC" or abs(us.scale_length - 1.0) > EPS:
        errors.append(f"单位应为 Metric / Unit Scale 1.0（当前 {us.system} / {us.scale_length}）")

    objs = exportable_objects(scene)
    if not objs:
        errors.append("没有可导出的物体（_REF 集合之外）")

    depsgraph = context.evaluated_depsgraph_get()
    total_tris = 0
    min_z = None
    for o in objs:
        if o.parent is None:
            if any(abs(s - 1.0) > EPS for s in o.scale):
                errors.append(f"{o.name}: 缩放未应用 {tuple(round(s, 3) for s in o.scale)}（Ctrl+A > 缩放）")
            if any(abs(r) > EPS for r in o.rotation_euler) and o.type != "ARMATURE":
                warnings.append(f"{o.name}: 旋转未应用（Ctrl+A > 旋转），进团结后可能带旋转")
        if o.type == "MESH":
            total_tris += tri_count(o, depsgraph)
            if len(o.data.materials) == 0:
                warnings.append(f"{o.name}: 没有材质，进团结会是默认材质")
            if not o.data.uv_layers:
                warnings.append(f"{o.name}: 没有 UV")
            for v in o.evaluated_get(depsgraph).bound_box:
                z = (o.matrix_world @ mathutils.Vector(v)).z
                min_z = z if min_z is None else min(min_z, z)

    if category:
        limit = TRI_LIMITS[category]
        if total_tris > limit:
            errors.append(f"三角面 {total_tris} 超过 {category} 上限 {limit}")

    if category in {"Characters", "Enemies", "Bosses", "Props"} and min_z is not None and abs(min_z) > 0.02:
        warnings.append(f"模型最低点 z={min_z:.3f}，pivot 应在脚底：把模型落到地面 (z=0)")

    arm = [o for o in objs if o.type == "ARMATURE"]
    if category in {"Characters", "Enemies", "Bosses"} and not arm:
        warnings.append("角色类资产没有骨架：如走 Mixamo 流程可忽略（导出静态网格后上传 Mixamo 绑定）")

    stats = {"objects": len(objs), "tris": total_tris, "category": category, "name": name,
             "target": export_path(root, category, name) if root and category else None}
    return errors, warnings, stats


# ---------------------------------------------------------------- 导出

def do_export(context=None):
    context = context or bpy.context
    errors, warnings, stats = validate(context)
    if errors:
        return False, errors, warnings, stats

    target = stats["target"]
    os.makedirs(os.path.dirname(target), exist_ok=True)

    # 只选中可导出物体
    objs = exportable_objects(context.scene)
    for o in context.scene.objects:
        o.select_set(o in objs)

    has_anim = any(o.animation_data for o in objs) or any(o.type == "ARMATURE" for o in objs)
    bpy.ops.export_scene.fbx(
        filepath=target,
        use_selection=True,
        object_types={"MESH", "ARMATURE", "EMPTY"},
        apply_unit_scale=True,
        apply_scale_options="FBX_SCALE_ALL",
        axis_forward="-Z",
        axis_up="Y",
        bake_space_transform=True,
        use_mesh_modifiers=True,
        mesh_smooth_type="FACE",
        use_tspace=True,
        add_leaf_bones=False,
        primary_bone_axis="Y",
        secondary_bone_axis="X",
        armature_nodetype="NULL",
        bake_anim=has_anim,
        bake_anim_use_all_actions=True,
        bake_anim_use_nla_strips=False,
        bake_anim_simplify_factor=0.0,
        path_mode="AUTO",
        embed_textures=False,
    )
    return True, errors, warnings, stats


# ---------------------------------------------------------------- 模板

def new_template(category, name, out_dir):
    """新建一个符合规格的 .blend：单位、参考人、正面箭头。"""
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene
    scene.unit_settings.system = "METRIC"
    scene.unit_settings.scale_length = 1.0
    scene.unit_settings.length_unit = "METERS"

    ref = bpy.data.collections.new(REF_COLLECTION)
    scene.collection.children.link(ref)

    # 1.75m 参考人（胶囊）
    bpy.ops.mesh.primitive_cylinder_add(radius=0.25, depth=1.25, location=(1.2, 0, 0.875))
    body = bpy.context.active_object
    body.name = "REF_Human_1.75m"
    bpy.ops.mesh.primitive_uv_sphere_add(radius=0.25, location=(1.2, 0, 1.5))
    head = bpy.context.active_object
    head.name = "REF_Head"
    # 正面指示：箭头指向 -Y
    bpy.ops.object.empty_add(type="SINGLE_ARROW", location=(0, 0, 0), rotation=(1.5708, 0, 0))
    arrow = bpy.context.active_object
    arrow.name = "REF_FRONT_-Y"
    arrow.empty_display_size = 1.0
    for o in (body, head, arrow):
        for c in o.users_collection:
            c.objects.unlink(o)
        ref.objects.link(o)
        o.hide_select = True
    ref.hide_render = True

    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, name + ".blend")
    bpy.ops.wm.save_as_mainfile(filepath=path)
    return path


# ---------------------------------------------------------------- UI

class RUPU_OT_validate(bpy.types.Operator):
    bl_idname = "rupu.validate"
    bl_label = "检查"

    def execute(self, context):
        errors, warnings, stats = validate(context)
        for w in warnings:
            self.report({"WARNING"}, w)
        for e in errors:
            self.report({"ERROR"}, e)
        if not errors:
            self.report({"INFO"}, f"通过：{stats.get('objects')} 个物体 / {stats.get('tris')} 三角面")
        return {"FINISHED"}


class RUPU_OT_export(bpy.types.Operator):
    bl_idname = "rupu.export"
    bl_label = "导出到团结工程"

    def execute(self, context):
        if bpy.data.is_dirty and bpy.data.filepath:
            bpy.ops.wm.save_mainfile()
        ok, errors, warnings, stats = do_export(context)
        for w in warnings:
            self.report({"WARNING"}, w)
        if not ok:
            for e in errors:
                self.report({"ERROR"}, e)
            return {"CANCELLED"}
        self.report({"INFO"}, "已导出 " + stats["target"])
        return {"FINISHED"}


class RUPU_PT_panel(bpy.types.Panel):
    bl_label = "入谱 资产管线"
    bl_space_type = "VIEW_3D"
    bl_region_type = "UI"
    bl_category = "入谱"

    def draw(self, context):
        col = self.layout.column(align=True)
        root, category, name = asset_info(bpy.data.filepath) if bpy.data.filepath else (None, None, None)
        col.label(text=f"分类: {category or '未识别'}")
        col.label(text=f"资产: {name or '未保存'}")
        if category:
            col.label(text=f"面数上限: {TRI_LIMITS[category]}")
        col.separator()
        col.operator("rupu.validate", icon="CHECKMARK")
        col.operator("rupu.export", icon="EXPORT")


CLASSES = (RUPU_OT_validate, RUPU_OT_export, RUPU_PT_panel)


def register():
    for c in CLASSES:
        bpy.utils.register_class(c)


def unregister():
    for c in reversed(CLASSES):
        bpy.utils.unregister_class(c)


# ---------------------------------------------------------------- CLI

def _cli(argv):
    def report(errors, warnings, stats):
        for w in warnings:
            print("[WARN]", w)
        for e in errors:
            print("[ERROR]", e)
        print("[STATS]", stats)

    if "--new-template" in argv:
        i = argv.index("--new-template")
        category, name = argv[i + 1], argv[i + 2]
        if category not in CATEGORIES:
            print("[ERROR] 分类应为", CATEGORIES)
            sys.exit(2)
        root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
        print("[OK] 新建", new_template(category, name, os.path.join(root, "ArtSource", category)))
        return
    if "--export" in argv:
        ok, errors, warnings, stats = do_export()
        report(errors, warnings, stats)
        print("[OK] 导出" if ok else "[FAIL] 未导出", stats.get("target"))
        sys.exit(0 if ok else 1)
    if "--validate" in argv:
        errors, warnings, stats = validate()
        report(errors, warnings, stats)
        sys.exit(1 if errors else 0)


if __name__ == "__main__":
    if "--" in sys.argv:
        _cli(sys.argv[sys.argv.index("--") + 1:])
    else:
        register()
