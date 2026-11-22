# 资产规格（B 交付标准）

由 `Tools/blender/rupu_pipeline.py`（导出前检查）和 `RupuArtImporter.cs`（导入时套默认值）自动执行，以下为人工对照表。

## 通用
| 项 | 规定 |
|---|---|
| 单位 | 1 unit = 1 米；Blender Metric，Unit Scale 1.0 |
| 朝向 | Blender 中模型正面朝 **-Y**；导入团结后正面朝 **+Z**，旋转 0，缩放 1 |
| Pivot | 角色/敌人/道具：脚底中心（模型最低点 z=0）；建筑：地面角点或中心，按 anchorHint 说明 |
| 变换 | 导出前应用缩放、旋转（Ctrl+A） |
| FBX | Forward -Z / Up Y / Apply Transform / FBX All 缩放 / 无叶骨 |
| 碰撞 | 不随模型导出；在团结里加 Box/Capsule，建筑用组合碰撞 |

## 面数上限（三角面）
| 分类 | 上限 | 动画类型 |
|---|---|---|
| Characters（NPC） | 8,000 | Humanoid |
| Enemies | 8,000 | Humanoid（共用骨架，换武器/贴图） |
| Bosses | 15,000 | Generic |
| Props | 3,000 | 无 |
| Buildings | 20,000 / 模块 | 无 |
| Environments | 40,000 / 块 | 无 |

## 命名
| 前缀 | 用途 | 例 |
|---|---|---|
| `NPC_` `EN_` `BOSS_` `BLD_` `PROP_` `ENV_` | 模型 / 资产名 | `NPC_WangYan`、`EN_Blade`、`BOSS_ChiYan` |
| `PF_` | Prefab | `PF_NPC_WangYan` |
| `M_` / `T_` | 材质 / 贴图 | `M_WangYan_Body`、`T_WangYan_Body_D` |
| `AN_` | 动画片段 | `AN_Humanoid_Walk` |
| `VO_` `SFX_` `BGM_` | 音频 | `SFX_Parry_01` |
| 贴图后缀 | `_D` 颜色 / `_N` 法线 / `_ORM` 遮蔽-粗糙-金属 / `_Mask` | 导入器按后缀判断 sRGB 与法线 |

动画文件：`<模型名>@<动作>.fbx`；文件名含 idle/walk/run/loop 的片段自动开启 Loop Time。

## 动画事件（与 A 约定）
`AttackHit` `PhaseChange` `Stagger` `Death` `Footstep`

## 贴图 / UI / 音频
- 贴图 1024/2048 PNG；颜色贴图 sRGB；UI 放 `Art/UI/`，导入器自动设为 Sprite、关闭 Mipmap
- UI 1920×1080，9-slice，安全区 5%
- 音频 48kHz；VO 单声道 -16 LUFS；SFX -18；BGM -20（BGM 自动设为 Streaming）

## 色板
民国灰绿 `#5E6B5A` · 明代暖褐 `#8A5A3B` · 纸色 `#E8DCC8` · 火色 `#C4552E` · 水色 `#4F6B6A`
