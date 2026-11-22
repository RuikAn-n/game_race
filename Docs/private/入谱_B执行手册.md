# 《入谱》B 全流程工作手册（美术 / 音频 / 视觉）

> B 的输入：A/AI 给的资产 id、文本、UI 布局、过场脚本、VO 台词。
> B 的输出：能直接进 prefab、能直接播的**资产包 + 清单**。
> 这份是“从头到尾做什么”，不是排期。

## 1. 全流程总览

| 阶段 | B 做什么 | 产出 | 输入 |
|---|---|---|---|
| 0 开工配置 | 装软件、克隆工程、建目录、建清单 | 可工作的工程 + 空 `asset_manifest.csv` | 工程路径、Unity 版本 |
| 1 视觉定位 | 找史料/参考、定色板、定风格、盘资产 | 风格板 + 资产总表 | 世界观、时代设定 |
| 2 资产规格 | 定单位/pivot/碰撞/贴图/命名/音频/UI 规则 | `asset_spec.md` | A/AI 的技术约束 |
| 3 金样本 | 残谱 / 残旗 / 火炮 三个样本 | 3 个 prefab + 贴图 + 音效 | 互动 id、UI 线框 |
| 4 角色/敌人/Boss | 7 NPC、4 敌人、2 Boss，建模/绑定/动画 | 角色 prefab + 动画 + Boss 白模/阶段动画 | 角色小传、Boss 阶段 |
| 5 场景/建筑/道具 | 明代、1941、巡游三套场景与道具 | 场景 prefab + 美术摆放 | 场景清单、anchor 位置 |
| 6 动画/VFX | 攻击/受击/死亡、火/水/旗/灯/雨/烟 | 动画 clip + VFX prefab | 战斗节奏、招式表 |
| 7 UI 视觉 | 面板/按钮/图标/HUD/军议/指挥/族谱/图鉴/结局页 | UI 皮肤 prefab + 九宫格 | UI 布局线框 |
| 8 音频/VO | SFX、BGM、8—9 分钟 VO、混音 | 音频文件 + `vo_manifest.csv` | VO 台词、发音词典 |
| 9 2D 过场 | 开场/入谱/藏谱/寻谱/巡游 5 段分层 | 5 段过场 prefab/分层 | 过场脚本、时间轴 |
| 10 结局卡/主画面 | 10 张卡、5 张主画面、印章 | 卡面 + 主画面 + UI 皮肤 | 结局标题/文案 |
| 11 整合/QA | 进 `Content_*` 摆放、补清单、查 missing ref | 可交付资产包 | 全流程 build |
| 12 交付/备份 | 提交 `b/content`、打 tag、归档 | 资产包 + 清单 + 授权 | 最终 build |

## 2. 每个阶段的具体动作

### 0. 开工配置

- 装 Unity Hub + 与 A 相同补丁的 **Unity 2022.3 LTS**；只装 Editor，出 build 时再装 Windows Build Support。
- 装 Git + Git LFS；克隆仓库到 `D:\太平日月\Project_rupu`。
- 装 Blender、Krita/GIMP/Photoshop、Audacity/Reaper、DaVinci Resolve、OBS。
- 注册 AI 图像/TTS；准备麦克风/耳机。
- 建目录：

```text
Art/
  Characters/  Enemies/  Bosses/  Buildings/  Props/  Environments/
  UI/  VFX/  Cutscenes/  EndingCards/
Audio/
  VO/  SFX/  BGM/
Data/
  asset_manifest.csv
Docs/
  asset_spec.md  vo_manifest.csv  licenses.md
```

- 建 `asset_manifest.csv`：`assetId,类型,prefabPath,texturePath,animPath,audioPath,anchorHint,状态,负责人`。

### 1. 视觉定位

- 收集参考：永昌堡城墙/环海楼/水门/祠堂、汤和庙、拼字龙灯、民国温州码头/主街/废墟。
- 定色板：民国灰绿 `#5E6B5A`、明代暖褐 `#8A5A3B`、纸色 `#E8DCC8`、火色 `#C4552E`、水色 `#4F6B6A`。
- 定风格：低模、纸纹、低饱和、雨/火/烟；角色不做写实脸。
- 盘资产：6 建筑、4 环境、4 敌人、2 Boss、7 NPC、10 道具、UI 全套、5 过场、10 结局卡。
- 产出：1 页风格板 + 1 张资产总表（标“复用/新做”）。

### 2. 资产规格

- 单位 1 unit = 1 米；pivot 脚底中心；forward +Z。
- 碰撞：Box/胶囊；建筑用组合碰撞。
- 贴图：1024/2048 PNG sRGB；UI 用图集。
- 面数：角色 ≤8k 三角面；建筑/道具低模。
- 命名：`PF_ / M_ / T_ / AN_ / VO_ / SFX_ / BGM_`。
- UI：1920×1080；9-slice；安全区 5%。
- 音频：48kHz；VO 单声道 -16 LUFS；SFX -18；BGM -20。
- 写进 `Docs/asset_spec.md`，每件资产按它交。

### 3. 金样本

做三个样本，先证明“资产能进游戏”：

1. **残谱**：旧纸、墨迹、缺角；3 片可拼；开箱/拼合/确认三个状态。
2. **残旗**：布纹、血渍、木杆；触旗时旗面轻摆；入谱时淡出。
3. **火炮**：铁/木/铆钉；瞄准/装填/发射三个状态；炮口火光。

每个样本交：prefab + 贴图 + 材质 + 音效 + `assetId`。A/AI 接进 `Content_*`，B 在 build 里看比例/材质/声音。

### 4. 角色 / 敌人 / Boss

**7 个 NPC**：王砚、王秉之、王沛、王叔杲、阿禾、赵翻译、林师傅。

- 低模，4 套基础体型换装；Mixamo 人形动画复用。
- 每人：idle / walk / talk / 一个标志动作（王砚拍照、族长咳嗽、阿禾举灯、赵翻译点头哈腰）。
- 表情用贴图/材质切换，不做面部绑定。

**4 个敌人**：刀兵、弓兵、火罐兵、盾兵。

- 共用 1 套骨架；换武器/盾/火罐/贴图。
- 每个：idle / walk / attack / hit / death；攻击前摇 0.45—0.6 秒。

**2 个 Boss**：赤焰（水门）、鬼倭（环海楼/瓮城）。

- 每个 3 阶段；每阶段 2—3 招；白模先定体量，再做动画。
- 动画事件：`AttackHit`、`PhaseChange`、`Stagger`、`Death`，给 A/AI 接判定。
- 交：Boss prefab、3 阶段动画、武器/特效挂点、阶段 VFX。

### 5. 场景 / 建筑 / 道具

**明代（1560）**：城墙、环海楼、东水门、祠堂、汤和庙、主街、盐场、水田。

- 6 个建筑模块拼装；城墙/水门/环海楼做可交互挂点。
- 道具：火炮、水轮、闸门、旗、火罐、水桶、供桌、匾、谱箱。

**1941**：码头、主街、祠堂、废墟、日伪哨卡。

- 同一几何换材质/贴花/道具；雨、雾、电线、标语。
- 祠堂内景做藏谱/寻谱/修谱三个状态。

**巡游（1945）**：庙前、主街、祠堂。

- 道具：香炉、供桌、三牲/面桃/纸烛、姓氏旗、灯牌、龙灯、锣鼓。
- 人群：6 个循环 NPC，站/走/举灯/敲锣/看。

**摆放**：B 在 `Content_*` 摆建筑/道具/雾/人群；A/AI 放 anchor 和逻辑。每件资产在 `asset_manifest.csv` 写 `anchorHint`。

### 6. 动画 / VFX

- 敌人：攻击、受击、死亡、破防。
- Boss：阶段切换、招式、弱点、处决。
- 环境：雨、雾、火、水、蒸汽、旗摆、灯晃、烟。
- 交互：开箱、拼纸、触旗、转轮、装填、上香、摆供、排旗、拼字、盖印。
- 每个 VFX 交 prefab；挂点命名 `VFX_`；给 A/AI 事件名。

### 7. UI 视觉

- 互动面板：纸底、标题、图、正文、2—3 选项、确认、页码。
- HUD：血、体力、Boss 架势、交互提示。
- 军议：兵力/物资/战术/侦察/族谱五个页签。
- 指挥：北门/水门/内应/粮仓四个按钮。
- 族谱：谱页、墨迹、印章、缺口。
- 图鉴：条目卡、史料标签（史实/传说/演绎）。
- 结局页：标题、2—3 句尾声、四个墨点、剩余页数、三个按钮。
- 回廊：10 张空白页/已解锁页、印章。
- 交：UI 皮肤 prefab + 九宫格 + 图标；布局由 A/AI 套。

### 8. 音频 / VO

- SFX：刀风、弹反、脚步、火、水、闸门、旗、锣、鼓、开箱、纸、印章。
- BGM：民国低沉弦乐/环境、明代鼓点/劳动号子、巡游锣鼓。
- VO：8—9 分钟关键场；先试音 10—15 个音色，再生成/克隆。
- 发音词典：王砚 yàn、永昌堡 bǎo、倭寇 wō kòu、汤和 tāng hé、嘉靖 jiā jìng、族约 zú yuē、愧顽簿 kuì wán bù。
- 交：48kHz 文件 + `vo_manifest.csv`（voId/文件/时长/角色/对齐点）。

### 9. 2D 过场

5 段：开场（1941 春祭中断）、入谱（触旗回 1560）、藏谱（4/28 搜祠）、寻谱（1941 冬废墟）、巡游（1945 中元）。

- 每段 4—6 层：背景/中景/人物剪影/前景雨或火/字幕安全区。
- 局部动效：雨、火、旗、灯、镜头推拉。
- 交：分层 PNG/PSD + 过场 prefab；A/AI 接 `CutscenePlayer` 和字幕。

### 10. 结局卡 / 主画面

- 10 张卡：S、S2、A、A2、B、C、D、E、F、G。
- 5 张主画面：祠堂、环海楼、水门、巡游、废墟。
- 印章/边框/纸纹统一。
- 文案由 A/AI 给；B 做画面/排版/材质。

### 11. 整合 / QA

- 把 prefab 放进 `Content_Ming` / `Content_1941` / `Content_Parade`。
- 更新 `asset_manifest.csv`；每件资产有 `assetId`/路径/`anchorHint`。
- 查：missing ref、粉红材质、pivot 偏移、碰撞缺失、动画事件缺失、音频爆音、UI 遮挡。
- 在 build 里走一遍：视觉/音频/比例/灯光/字幕安全区。
- 修完提交 `b/content`。

### 12. 交付 / 备份

- 提交：prefab、贴图、材质、动画、VFX、UI、音频、过场、卡面。
- 交清单：`asset_manifest.csv`、`vo_manifest.csv`、`licenses.md`。
- 打 tag：`b/asset-v1`；每日备份到移动硬盘/云盘。
- 截图/录屏：给预告/商店页。

## 3. 资产导出与导入配置

### Blender → Unity

- 单位：Metric，1.0；Apply Transform。
- FBX 导出：Forward `-Z`、Up `Y`；Scale `1.0`；Apply Modifiers。
- 骨架：Humanoid；Mixamo 动画直接导入。
- 碰撞：Unity 里加 Box/胶囊；建筑用组合碰撞。

### Unity 导入

- Mesh：Read/Write `Off`；Mesh Compression `Off`；Generate Colliders `Off`。
- 材质：URP/Lit 或 URP/Simple Lit；低模用 Vertex Color 可选。
- 贴图：sRGB；Mip Maps `On`；Compression `Normal`；UI 用 `Sprite (2D and UI)`。
- 动画：Loop Time 按需；事件名统一。
- 音频：VO `Decompress On Load`；BGM `Streaming`；SFX `Decompress On Load`。

### UI

- Canvas Scaler：1920×1080，Match 0.5。
- 9-slice：四边 border 统一；安全区 5%。
- 字体：思源宋体（标题）+ 思源黑体（正文）；字号 18—28。

## 4. 配置清单

### 4.1 硬件

- Windows 10/11 64 位；16—32GB RAM；RTX 2060/8GB 以上；100GB 空闲 SSD。
- 麦克风 + 耳机；移动硬盘/云盘备份。

### 4.2 软件

- Unity Hub + Unity 2022.3 LTS（与 A 同补丁）。
- Git + Git LFS。
- Blender、Mixamo（网页）、Krita/GIMP/Photoshop。
- Audacity/Reaper、DaVinci Resolve、OBS。
- 飞书/Notion/腾讯文档（任务表）。

### 4.3 账号 / 权限

- Git 仓库 Write `b/content`；Unity 组织 Member。
- Asset Store 组织账号；AI 图像/TTS 账号。
- 字体授权（思源）；音乐/音效/模型授权；声音克隆书面同意。

### 4.4 工程配置

- 工程路径 `D:\太平日月\Project_rupu`；Unity 版本与 A 一致。
- Git LFS 跟踪：`*.png *.psd *.fbx *.wav *.ogg *.mp4`。
- 分支：`b/content`；每天合 `main`。
- 目录：`Art/ Audio/ Data/ Docs/ Cutscenes/`。

### 4.5 AI 工具

- 图像：Midjourney / Flux / SD / 即梦 / 通义万相。
- 音频：Qwen3-TTS / 豆包 / FireRedTTS3 / GPT-SoVITS。
- 辅助：背景移除、放大、降噪。
- 统一色板/风格词，避免每张图换风格。

### 4.6 交付配置

- `asset_manifest.csv` 每行有 `assetId`、路径、`anchorHint`、状态。
- `vo_manifest.csv` 每行有 `voId`、文件、时长、角色、对齐点。
- `licenses.md` 记录字体/音乐/音效/模型/声音授权。
- 每日提交 + 每周 tag；交付前跑一遍 missing ref 检查。

## 5. 每次交付的包

```text
交付包/
  Art/            角色/敌人/Boss/建筑/道具/环境/UI/VFX/过场/结局卡
  Audio/          VO/SFX/BGM
  Data/
    asset_manifest.csv
  Docs/
    asset_spec.md
    vo_manifest.csv
    licenses.md
  Screenshots/
```

## 6. 自检清单

- [ ] 每件资产有 `assetId`，在 `asset_manifest.csv` 里。
- [ ] prefab 能拖进 `Content_*`，Console 无报错。
- [ ] 贴图无丢失、材质无粉红。
- [ ] pivot 在脚底中心，比例 1 unit = 1 米。
- [ ] 动画事件名与 A/AI 约定一致。
- [ ] 音频 48kHz，VO -16 LUFS，无爆音。
- [ ] UI 9-slice 正常，1920×1080 不遮文本。
- [ ] 过场 5 段可播、可跳。
- [ ] `vo_manifest.csv` 与字幕时间轴对齐。
- [ ] `licenses.md` 有记录。

## 7. 一句话

**B 的全流程 = 视觉定位 → 资产规格 → 金样本 → 角色/场景/动画 → UI/音频/过场/卡 → 整合 → 交付。**
