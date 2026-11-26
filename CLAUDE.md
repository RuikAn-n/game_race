# CLAUDE.md：《入谱》开发代理指南

## 项目

- **比赛**：2026 开源游戏开发大赛 OSGJ，主题「守·望」。仓库必须开源公开：https://github.com/RuikAn-n/game_race
- **游戏**：《入谱》。1941 / 1560 双线叙事，玩法是动作（三招一令）+ 守城策略 + 族谱结局。策划案在 `Docs/private/入谱_设计策划案_v3.0.pdf`，B 的职责在 `Docs/private/入谱_B执行手册.md`。
- **团队**：2 人 + AI。A 负责玩法和代码。**B（本机用户）负责建模、动画、美术、音频和视觉。**
- **视角**：探索和动作用第三人称；军议、战中指挥、战后整备用俯视，而且是同一个 3D 场景切换镜头，不另做策略地图。所以建筑的屋顶和城墙顶面必须从上往下看也清楚。
- **目标平台**：Windows x64。

## 环境（macOS Apple Silicon）

| 项 | 值 |
|---|---|
| 引擎 | 团结 Tuanjie **2022.3.62t18**（团结 1.11.1），路径 `/Applications/Tuanjie/Hub/Editor/2022.3.62t18/Tuanjie.app/Contents/MacOS/Tuanjie` |
| Hub | Tuanjie Cowork。许可证入口在 Hub「项目」页右上角的图标，用的是个人版 |
| 渲染 | URP 14.2.0-t1。管线资源在 `Assets/_Rupu/Settings/` |
| 包 | Cinemachine 2.10.3、ProBuilder 5.2.4、TextMeshPro、Timeline |
| 建模 | Blender 5.2（`/Applications/Blender.app`） |
| 其他 | Krita、Audacity、git-lfs、gh（已登录 RuikAn-n） |
| 测试 VM | VMware Fusion 里的 Win11 **ARM**，加密。没有加密密码，所以 vmrun 和共享文件夹都不可用。**不要修改它的 .vmx** |

运行 `Tools/mac/check_env.sh` 可以一次查看环境状态。

## 目录约定

```text
Project_rupu/            团结工程（Assets/ Packages/ ProjectSettings/ 入库，Library/ 等忽略）
  Assets/_Rupu/          管线脚本。源码在 Tools/unity_seed/，改源码后运行 Tools/mac/seed_unity_project.sh 同步
  Assets/Art/<分类>/<资产名>/   FBX、贴图、材质、prefab
  Assets/Audio/{VO,SFX,BGM}/
ArtSource/<分类>/<资产名>.blend   Blender 源文件（LFS），不要放进 Assets/
Tools/blender/rupu_pipeline.py   Blender 插件和命令行：规格检查 + FBX 导出
Tools/mac/               new_asset / blender_export_all / build_win / serve_build / check_env
Docs/                    日常用法.md（给人看的操作手册）、asset_spec.md、licenses.md、vo_manifest.csv、characters.md、map_yongchang.md
                         interiors.md、act1_assets.md（第一幕 P0/P1 资产与场景接入）、act2_assets.md、act3_enemies.md、act45_assets.md、
                         ming_buildings_house.md、ming_buildings_civic.md、建模缺口_完成情况.md（缺口清单逐节对照）
                         策划/文本：入谱_第二幕_筑堡_策划案_v1.md、入谱_第一幕_人物文本.md、入谱_美术建模清单.md、
                         入谱_当前建模缺口清单.md、第一幕_队友README.md
  Docs/private/          原始策划案 PDF、B 执行手册（只读原件，同样公开入库）
Data/asset_manifest.csv  资产总表
Builds/                  构建输出（忽略）
```

分类只能是：`Characters` `Enemies` `Bosses` `Buildings` `Props` `Environments`。

### 文档规则

- **作为附件加入对话的文档（用户拖进来、贴路径、放在 `new_docs/` 或 Downloads 里的 .md / .pdf / .docx 等）都要整理进 `Docs/`**：保留原文件名，同名已存在时先比对内容，相同就跳过，不同就以新版覆盖并在提交信息里说明。不要让这类文档只留在仓库外或 `new_docs/` 这样的临时目录里。
- 整理后在上面「目录约定」的 Docs 一行补上文件名；文档里的任务若已在其他会话完成，先看 git 记录和其他 worktree，避免重复做。
- `Docs/private/` 只是「原始资料、不改动」的意思，它同样会入库公开。含密码、密钥或不能公开的内容不要放进 Docs，告诉用户另存。

## 美术资产规范（必须遵守）

- **单位与朝向**：1 unit = 1 米。Blender 中模型正面朝 **-Y**，导入团结后正面朝 +Z、旋转 0、缩放 1。
- **Pivot**：角色、敌人、Boss、道具的原点在脚底中心，最低点 z=0。
- **变换**：导出前必须应用旋转和缩放（Ctrl+A）。
- **FBX 导出参数**：Forward -Z、Up Y、Apply Transform、FBX All 缩放、不加叶骨骼。统一走 `rupu_pipeline.py`，**不要手动调导出参数**。
- **三角面上限**：Characters / Enemies 8k，Bosses 15k，Props 3k，Buildings 20k（每个模块），Environments 40k（每块）。
- **命名前缀**：资产名用 `NPC_` / `CH_` / `EN_` / `BOSS_` / `BLD_` / `PROP_` / `ENV_`。其他类型：`PF_` prefab、`M_` 材质、`T_` 贴图、`AN_` 动画片段、`VO_` / `SFX_` / `BGM_` 音频。贴图后缀用 `_D` / `_N` / `_ORM` / `_Mask`。
- **材质颜色**：要设置在 **Principled BSDF 的 Base Color** 或贴图上。Blender 的 Viewport Display 颜色（`diffuse_color`）不会导出，进团结后会变成白色。
- **人形骨架**：Characters、Enemies、Bosses 都设为 Humanoid（导入器自动处理），共用 Mixamo 动画。动画文件命名为 `<模型>@<动作>.fbx`，文件名含 idle / walk / run / loop 的自动循环。
- **动画事件名**（与 A 约定）：`AttackHit` `PhaseChange` `Stagger` `Death` `Footstep`。
- **风格**：低模、纸纹、低饱和度。角色不做写实脸，表情靠贴图切换。
- **色板**：民国灰绿 `#5E6B5A`、明代暖褐 `#8A5A3B`、纸色 `#E8DCC8`、火色 `#C4552E`、水色 `#4F6B6A`。
- **贴图与音频**：贴图 1024 或 2048 的 PNG。音频 48kHz；VO 单声道 -16 LUFS，SFX -18，BGM -20。
- **入库前**：每个新资产都要在 `Data/asset_manifest.csv` 登记。第三方素材要在 `Docs/licenses.md` 登记，因为仓库公开，必须确认素材允许再分发。

## 标准操作（代理可以直接执行）

```bash
# 新建资产（生成带参考人和正面箭头的模板 .blend）
Tools/mac/new_asset.sh <分类> <资产名>
# 程序化建模：写一个 bpy 脚本，在 Blender 无界面模式下对 .blend 执行，然后导出
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup ArtSource/<分类>/<名>.blend -P your_script.py
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup ArtSource/<分类>/<名>.blend -P Tools/blender/rupu_pipeline.py -- --export
# 只检查规格不导出：把 --export 换成 --validate

# 团结命令行（编辑器打开同一工程时会被锁，需要用户关掉编辑器或在编辑器里点菜单）
T=/Applications/Tuanjie/Hub/Editor/2022.3.62t18/Tuanjie.app/Contents/MacOS/Tuanjie
$T -batchmode -nographics -quit -projectPath "$PWD/Project_rupu" -executeMethod <Class.Method> -logFile Builds/logs/x.log </dev/null
#   可用方法：Rupu.EditorTools.RupuProjectSetup.InitCLI（初始化工程 + 重建 ArtTest 场景）
#             Rupu.EditorTools.RupuProjectSetup.SetupURP
Tools/mac/build_win.sh [--release]     # 交叉编译 Win64（Mono 后端），输出 Builds/Windows/Rupu.exe
Tools/mac/build_yongchang.sh [--scene-only|--force]   # 永昌堡总地图：布局 → Blender 白模/地形 → 团结场景 + 截图 + 可走性自检
Tools/mac/serve_build.sh               # 在 VMware 内网发布 zip，VM 里用浏览器下载
```

在 VM 里测试的步骤：在 VM 的 Edge 打开 `http://172.16.52.1:8624/Rupu_Windows.zip`（另一个可用地址是 192.168.214.1），解压后运行 `Rupu.exe`。

## 永昌堡总地图（见 Docs/map_yongchang.md）

- 唯一数据源 `Data/map/yongchang_layout.json`（由 `Tools/map/gen_layout.py` 生成，不手改）；坐标为团结世界坐标 x=东 z=北，平面压缩 0.5，高度真实。
- 年代切换只改 `Data/map/era_kits.json`（kind → `BLD_ROC_*` / `BLD_MING_*`）和 `era_materials.json`（语义材质名 → 年代颜色）。明代模型必须与同 kind 的民国模型占地一致。
- 程序化白模由 `Tools/blender/build_yongchang.py` 生成，已存在的 .blend 默认跳过（保护手改）；`--force` 会覆盖。
- 碰撞约定：`COL_*` 只做碰撞，`NOCOL_*` 不加碰撞。
- 人物（见 Docs/characters.md）：`Tools/blender/rupu_char.py` 程序化生成，骨骼用团结 Humanoid 标准名；共用动画 `CH_WangYan_1941@Idle/Walk/Run` + 控制器 `AC_Humanoid_Locomotion`（Speed 参数）；场景摆放在 `era_kits.json` 的 `cast`。
- 各幕生成模块（每幕一个文件，由 build_yongchang.py 统一导入）：`rupu_act1p1` `rupu_ming_house` `rupu_ming_civic` `rupu_act2` `rupu_enemy` `rupu_act45`；人物扩展用 `rupu_char` 的 `HAIR_HOOKS/EXTRA_HOOKS/GESTURE_HOOKS`，不必改 rupu_char.py。共用动作自动收进 `AC_Humanoid_Locomotion`；敌人/Boss 动作在 `AC_Combat`（`RupuCharacters.ControllersCLI`）。
- 第一幕（见 Docs/act1_assets.md）：道具/街市 `Tools/blender/rupu_act1.py`；共用动作 `CH_WangYan_1941@<动作>` 是控制器里的同名状态，脚本 `CrossFade` 进入；NPC 挂 `Act1ClanActor`；特效 `RupuVfx`（`PF_VFX_*`，URP 粒子材质存成资产）；场景 `Act1RocSceneBuilder.Create`。人形动作片段的根运动一律烘进姿势。

## 注意事项（踩过的坑）

- **命令行调用团结时要加 `</dev/null`**，Bash 命令里不要出现会读 stdin 的命令，否则会卡住。
- **不要给 VM 用 `iex (iwr ...)` 这类"下载后直接执行脚本"的命令**，Windows Defender 会按木马规则拦截。
- **网络**：本机代理下 unity.cn 和百度连不上；`download.tuanjie.cn`（编辑器模块的下载服务器）和 GitHub 能连。缺少的编辑器模块可以从 `<editor>/modules.json` 里的 downloadUrl 下载 pkg，用 `pkgutil --expand-full` 解开，把 Payload 放到 modules.json 里写的 destination。
- **IL2CPP**：Mac 上只能出 Windows 的 Mono 包。IL2CPP 包和性能测试要在 A 的 x64 Windows 机器上做。VM 是 ARM 转译运行，只适合做冒烟测试。
- **URP RendererData**：用 `CreateInstance` 创建后着色器引用是空的，必须调用 `ResourceReloader.ReloadAllNullIn`。`SetupURP` 已经处理了这一点。
- **许可证**：个人版许可证会过期，联网后会自动续期。batchmode 报许可证错误时，让用户在 Hub 里刷新。

## Git

- 主分支 `main`。B 日常在 `b/content` 分支工作，每天合入 main。
- 用户要求时才 commit / push。提交信息末尾加 `Co-Authored-By` 行。
- 二进制文件按 `.gitattributes` 走 LFS。仓库公开，**不要提交任何密码或密钥**（VM 密码只记在本地 memory 里）。

## 资产总量与优先级（来自策划案，按 20 天压缩版排）

1. 永昌堡白模模块：城墙、环海楼、东水门、祠堂。第三人称和俯视两个视角都依赖它，最先做。
2. 1 套人形基础网格 → 7 个 NPC 换装（王砚、王秉之、王沛、王叔杲、阿禾、赵翻译、林师傅）。
3. 敌人：刀兵、弓兵、火罐兵、盾兵共用一套骨架，只换武器和贴图。
4. Boss：赤焰、鬼倭（人形），每个 3 个阶段。
5. 道具：火炮、水轮、闸门、旗、火罐、水桶、供桌、匾、谱箱。
6. 1941 版本：同一套几何换材质、贴花、道具（雨、雾、电线、标语）。
