# ROC 场景导入说明

## 来源

- 仓库：https://github.com/RuikAn-n/game_race
- 分支：`main`
- 提交：`7bf5cd1b0c05e87e2823a639c5822f97f90ba2ad`
- 仓库公开，本次导入**未使用任何账号登录**，也不需要凭证。
- 地图数据读取仓库根目录的 `Data/map/`（`RupuMapBuilder` 用 `Application.dataPath` 向上两级推算，与盘符无关）。

## 已导入

- `Project_rupu/Assets/Art/` 全部 335 个美术文件（FBX、材质、贴图、动画控制器）
- `Project_rupu/Assets/_Rupu/Scenes/Map_Yongchang_ROC.unity`
- `Project_rupu/Assets/_Rupu/Scenes/Map_Yongchang_MING.unity`
- URP 14.2.0-t1 工程设置、Packages、`UniversalRenderPipelineGlobalSettings`
- ROC 角色：王砚 1941、王秉之、王沛、王叔杲、王德
- ROC 建筑：祖祠、环海楼、四门、城墙、街屋、商铺、粮仓、盐棚、码头、电线杆等

## 新场景

`Assets/Scenes/Act1_ROC.unity`

在 `Map_Yongchang_ROC` 实景上接入：

- 第一幕 7 个互动点
- 族老/族亲/祭拜父亲/三派/日本军官/街市事件
- 王砚实际角色模型
- 王秉之实际角色模型
- 实际祖祠、环海楼、街市、城墙
- 玩家 CharacterController + 第三人称相机
- 对白、TTS、音频等待、镜头转向
- 街尾火光和哭喊事件

## 仍是临时占位

仓库没有提供以下模型，当前用临时人形/几何体：

- 日本军官、日本兵
- 商贩、街坊、三派群众
- 日军飞机
- 供桌、牌位、香炉、旗杆等小道具
- 室内神主位细节

这些按《入谱_美术建模清单.md》继续替换。

## 注意

- 场景坐标使用 ROC 总地图的真实坐标，不再使用原灰盒的 160×110 坐标。
- 祖祠位置约 `(-20, 0, 42)`，环海楼约 `(113, 7, 40)`。
- 原 `Act1_1941.unity` 灰盒版保留，可对照回退。
- 工程已切换到 URP；旧灰盒材质可能显示为粉色，不再作为主场景。

## 常见问题

### 画面全粉红

原因是 URP 材质在 Built-in 管线下渲染，或 GraphicsSettings 没有指定 URP Asset。

已修复：

- GraphicsSettings.defaultRenderPipeline = Assets/_Rupu/Settings/URP_Asset.asset
- 所有 QualitySettings.renderPipeline = 同一个 URP Asset

如果又出现粉红：Edit > Project Settings > Graphics 检查 Scriptable Render Pipeline Settings 是否为空。

### 王砚 T-pose

原因是角色模型没有挂 Animator Controller。已把 Assets/Art/Animations/AC_Humanoid_Locomotion.controller 挂到王砚模型，并按移动速度设置 Speed 参数。

### 打开场景时报 “cannot be used during play mode”

先停止 Play，再用 入谱 > 打开 Act1 ROC 场景（自动退出 Play）。
