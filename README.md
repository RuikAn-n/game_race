# 入谱 · Rupu

2026 开源游戏开发大赛（OSGJ，主题「守·望」）参赛作品。引擎：团结引擎（Tuanjie，Unity 中国版）。目标平台：Windows x64。

## 目录

```text
game_race/
├─ Project_rupu/          团结工程（Universal 3D / URP）
│  └─ Assets/
│     ├─ _Rupu/           管线脚本（从 Tools/unity_seed 拷入）
│     ├─ Art/             Blender 导出的 FBX、贴图、材质、prefab
│     └─ Audio/           VO / SFX / BGM
├─ ArtSource/             Blender 源文件 .blend（LFS，不进 Assets，团结不用装 Blender 也能打开工程）
├─ Tools/
│  ├─ blender/rupu_pipeline.py   Blender 插件 + 命令行：检查规格并导出 FBX
│  ├─ mac/                构建、虚拟机、批量导出脚本
│  ├─ windows/            VM 内运行脚本
│  └─ unity_seed/         要拷进工程的团结编辑器脚本
├─ Docs/                  资产规格、清单、授权记录（Docs/private/ 不入库）
├─ Data/asset_manifest.csv
└─ Builds/                构建输出（不入库，挂进 VM 作为共享文件夹）
```

## 工作流总览

```text
Blender (.blend, ArtSource/)
   │  N 面板「入谱」> 检查 / 导出        ← 单位、缩放、面数、pivot 校验
   ▼
Project_rupu/Assets/Art/<分类>/<资产名>/<资产名>.fbx
   │  RupuArtImporter 自动套导入规则      ← Humanoid、贴图/音频设置
   ▼
团结编辑器 (macOS Apple Silicon) ── 入谱 > 创建美术测试场景（第三人称 / Tab 俯视）
   │  入谱 > 构建 Windows x64   或   Tools/mac/build_win.sh
   ▼
Builds/Windows/Rupu.exe  ──(VMware 共享文件夹 RupuBuilds)──▶  Win11 VM: run_latest.bat
```

在 Mac 上做 Win64 构建用的是 **Mono** 后端，这是官方支持的跨平台构建。想要 IL2CPP，必须在 Windows 主机上构建，交给队友 A 的 Windows 机器出最终发布包即可。

## 1. 安装团结引擎（一次性）

工程已经建好并提交，团结版本 **2022.3.62t18**（团结 1.11.1），渲染管线 URP 14.2.0-t1。新成员只需要：

1. 安装 Tuanjie Cowork（团结 Hub），登录后在 Hub「项目」页右上角的「许可证」图标里激活**免费个人版**。
2. 安装编辑器 2022.3.62t18，并勾选模块 **Windows Build Support (Mono)**。
3. `git lfs install && git clone`，然后在 Hub 中添加并打开 `Project_rupu`。
4. 运行 `Tools/mac/check_env.sh`，确认所有项都是 ✓。

`Tools/unity_seed/` 是管线脚本的源。修改后运行 `Tools/mac/seed_unity_project.sh` 同步到工程里。

## 2. Blender 建模

- 安装插件：Blender > 偏好设置 > 插件 > 从磁盘安装 > `Tools/blender/rupu_pipeline.py`
- 新建资产：`Tools/mac/new_asset.sh Characters NPC_WangYan`
  - 生成的文件已设好公制单位，自带 1.75m 参考人和 -Y 正面箭头。这些放在 `_REF` 集合里，不会被导出。
- 做完后在 3D 视图按 N，打开「入谱」页签，点 **检查**，再点 **导出到团结工程**。
- 全量重导：`Tools/mac/blender_export_all.sh`
- 人形角色（推荐）：先导出不带骨架的 FBX，上传 [Mixamo](https://www.mixamo.com) 自动绑定，下载 FBX for Unity 后放进 `Assets/Art/Characters/<名>/`，导入器会自动设成 Humanoid。动画文件命名为 `<名>@Walk.fbx`，所有人形角色共用这些动画。

## 3. Windows 构建与测试

```bash
Tools/mac/build_win.sh            # Development 构建（编辑器需关闭；开着时用菜单 入谱 > 构建）
Tools/mac/build_win.sh --release
Tools/mac/vm_run.sh               # 启动 VM，挂载共享文件夹，可选自动运行
Tools/mac/build_and_test.sh       # 两步合一
```

VM 是加密的（Win11 TPM 需要加密），自动化需要两组密码，存在 macOS 钥匙串里，不会写进仓库：

```bash
security add-generic-password -s rupu-vm-enc -a vm -w '<VM 加密密码>'
security add-generic-password -s rupu-vm -a '<Windows 用户名>' -w '<Windows 密码>'
```

如果不想存密码，就在 Fusion 里手动加一次共享文件夹（名称 `RupuBuilds`，路径为本仓库的 `Builds/`），之后在 VM 里双击 `\\vmware-host\Shared Folders\RupuBuilds\run_latest.bat`。

> 这台 VM 是 **Windows 11 ARM**，x64 游戏要经过 Prism 转译，显卡是 VMware 的 DX11 虚拟显卡。所以 VM 只适合做**功能冒烟测试**：能启动、没有粉材质、输入和分辨率正常。帧率不代表真实玩家机器，性能测试请在队友 A 的 x64 Windows 实机上做。

## 4. Git 约定

- 分支：B 在 `b/content` 上工作，每天合入 `main`。
- 二进制资产（blend/fbx/png/wav 等）走 Git LFS，规则见 `.gitattributes`。
- **本仓库是公开的**：策划案、内部资料放 `Docs/private/`，该目录已被 gitignore。
