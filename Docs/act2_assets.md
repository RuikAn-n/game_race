# 第二幕 1560 筑堡：人物、沙盘、筑堡道具与动作

依据：[`入谱_当前建模缺口清单.md`](入谱_当前建模缺口清单.md) 3.3、3.4、3.6（动画部分），以及 [`入谱_第二幕_筑堡_策划案_v1.md`](入谱_第二幕_筑堡_策划案_v1.md)（沙盘 §4.2–4.5、族约 §6、名录 §7、殉难 §9）。
全部是程序化白模（低模、纯色材质），生成脚本是 `Tools/blender/rupu_act2.py`，由 `build_yongchang.py` 驱动导出 FBX。材质前缀：人物用 `M_A2C_*`，道具用 `M_A2_*`。

![沙盘：1:500 永昌堡，城墙、门楼、敌台、民居都已摆上](images/act2/sandtable_q.jpg)

## 完成情况

| 清单 ID | 状态 | 资产 |
|---|---|---|
| `CHR_MingElder` 1–2 | ✅ 2 | `NPC_MingElder_A` / `NPC_MingElder_B` |
| `CHR_Artisan` 4 型 | ✅ | `NPC_Artisan_Mason` / `_Carpenter` / `_Rammer` / `_Smith` |
| `CHR_Laborer` 6 变体 | ✅ | `NPC_Laborer_A..F` |
| `CHR_Militia` 4 变体 | ✅ | `NPC_Militia_A..D` |
| `CHR_MingWoman` 2 | ✅ | `NPC_MingWoman_A`（送饭）/ `_B`（提灯） |
| `CHR_MingChild` 1 | ✅ | `NPC_MingChild` |
| `ENV_SandTable` | ✅ | `ENV_SandTable` |
| `PROP_Sand_Wall` / `_Gate` / `_Tower` / `_House` / `_Flags` | ✅ | 同名，5 个资产（2026-11 按靠山 B 案重生成，补墙线分段、水门起止位、纸卡贴图） |
| 沙盘 1941 / 1945 皮肤 | ✅ | 断角/漏沙/蒙布几何 + `T_SandTable_Dust_Mask` + `RupuSandSkins` 生成 `_1941` / `_1945` 材质 |
| `ENV_Stele` | ✅ | `ENV_Stele` |
| `PROP_Covenant` 10 | ✅ | `PROP_Covenant`（`Board_01..10`） |
| `PROP_Roster` | ✅ | `PROP_Roster` |
| `PROP_Abacus` | — | 已有（`rupu_char.py`），没有重做 |
| `PROP_Deed` / `PROP_Blueprint` | ✅ | 同名 |
| `PROP_Survey` / `PROP_Scaffold` / `PROP_Mortar` / `PROP_Winch` / `PROP_Tools` / `PROP_Rope` | ✅ | 同名 |
| `PROP_StoneBlock` 3 尺寸 | ✅ | `PROP_StoneBlock_S` / `_M` / `_L` |
| `PROP_Cart` 2 | ✅ | `PROP_Cart_Wheelbarrow` / `PROP_Cart_Flat` |
| 3.6 动画（王沛 / 王叔杲 / 王德 / 王砚 / 群众） | ✅ 20 个 | 见下文「动作」 |
| 3.6 王沛试炮、王叔杲拆梁 | ⚠️ 未单做 | 试炮可以用 `A2_LoadCannon` 加 `A2_PointLine`；拆梁不在本次任务列表里 |
| 3.6 VFX | ⚠️ 只做了挂点 | 粒子不在本次范围。已留 `FX_SandDust*`、`FX_Water_E`、`FX_Chisel_1..3`、`FX_Splash`、`FX_Ink` |

## 人物（Characters，22 骨 Humanoid，每个 1.2k–1.8k 三角面）

明代服饰的共同标志是**交领右衽**：一道浅色领缘从左颈斜到右腋下（钩子 `a2_jiaoling`）。短褐的人物统一配绑腿和草鞋。

![族老、王叔杲、王沛、四匠人](images/act2/chars_elders_artisans.jpg)

| 资产 | 身高 | 三角面 | 造型 |
|---|---|---|---|
| `NPC_MingElder_A` | 1.66 | 1168 | 70 岁，赭褐道袍，戴高而方的四方平定巾，白长须，微驼，宽袖。族老里反对筑堡的主要声音 |
| `NPC_MingElder_B` | 1.73 | 1364 | 62 岁，高瘦，暗橄榄直裰外罩黑褐对襟褙子，戴东坡巾，灰短须 |
| `NPC_Artisan_Mason` | 1.70 | 1416 | 石匠：灰头巾，皮围裙到膝，帆布袖套，腰间挂錾子和手锤 |
| `NPC_Artisan_Carpenter` | 1.72 | 1310 | 木匠：网巾发髻，浅帆布围裙，背后插曲尺，腰挂墨斗，耳后夹笔 |
| `NPC_Artisan_Rammer` | 1.69 | 1310 | 夯土匠：粗壮，卷袖，戴斗笠，脖子搭白汗巾 |
| `NPC_Artisan_Smith` | 1.74 | 1404 | 铁匠：黑短褐，长皮围裙到小腿，皮护臂，左胯挂火钳 |

两位族老与王叔杲（蓝灰长衫、方巾、山羊须）、王沛（皮札甲）的区别在于：衣服是暖褐或橄榄色，戴高巾，留白须或灰须，A 驼背，B 罩着褙子。

![民夫 A–F](images/act2/chars_laborers.jpg)

民夫走的是模块化路线，靠换头饰、换颜色、换配件和调身高胖瘦来区分：

| 资产 | 头饰 | 配件 | 体型 | 三角面 |
|---|---|---|---|---|
| `NPC_Laborer_A` | 斗笠 | 汗巾 | 1.70 标准 | 1310 |
| `NPC_Laborer_B` | 蓝灰头巾 | 斜挎麻绳 | 1.76 高瘦 | 1432 |
| `NPC_Laborer_C` | 灰发髻 + 头带 | 衣裤打补丁 | 1.62 矮、老、驼背 | 1286 |
| `NPC_Laborer_D` | 网巾 | 右肩垫肩 + 灰汗巾 | 1.73 壮 | 1314 |
| `NPC_Laborer_E` | 褐包头巾 | 短蓑衣 | 1.67 | 1280 |
| `NPC_Laborer_F` | 白头巾 | 坎肩 | 1.64 半大后生 | 1384 |

![王德、义师 A–D、妇人、孩童](images/act2/chars_militia_women_child.jpg)

| 资产 | 三角面 | 造型 |
|---|---|---|
| `NPC_Militia_A` | 1768 | 红褐布面甲钉铜泡，红头巾，短刀，腰牌 |
| `NPC_Militia_B` | 1736 | 米黄纸甲压横绦，灰头巾，背箭囊（弓手） |
| `NPC_Militia_C` | 1838 | 靛青布面甲，红缨斗笠，背藤牌（牌手） |
| `NPC_Militia_D` | 1704 | 灰纸甲，靛头巾，皮护臂，短刀（长枪用道具） |
| `NPC_MingWoman_A` | 1404 | 送饭：褐袄长裙，青灰比甲，包头巾，白腰围 |
| `NPC_MingWoman_B` | 1414 | 提灯：浅褐袄黑裙，暗红比甲，高髻横簪，黑抹额 |
| `NPC_MingChild` | 1252 | 7 岁，赭红短袄，头两侧扎总角（红绳），挂长命锁 |

义师和王德是同一套系：短打、头巾、绑腿、腰牌。区别在于义师都穿布甲或纸甲，王德没有甲。

本次新增的钩子都在 `rupu_act2.py` 里，没有改 `rupu_char.py`：
- 头饰：`a2_fangjin`、`a2_dongpo`、`a2_wangjin`、`a2_toujin`、`a2_douli`（可加红缨）、`a2_woman_pin`、`a2_zongjiao`。
- 配件：`a2_jiaoling`、`a2_beizi`、`a2_bijia`、`a2_kanjian`、`a2_armor`（布 / 纸）、`a2_long_apron`、`a2_sleeves`、`a2_towel`、`a2_quiver`、`a2_shield_back` 等。

## 沙盘（策划案 §4.2–4.5）

> 2026-11 补缺口（[`第二幕_策划对照与建模缺口.md`](第二幕_策划对照与建模缺口.md) §3、§5 P0 沙盘行）：靠山 B 案重生成、墙线分段隆起、木签变墙垛、水门两态起止位、王宅木片三个落位、1941/1945 皮肤材质、四张议题纸卡。几何仍在 `rupu_act2.py`，积灰遮罩和纸卡贴图在 `rupu_a2_sand.py`（覆盖 `ENV_SandTable` / `PROP_Sand_Flags` 两个配方），团结侧皮肤材质由 `RupuSandSkins.cs` 生成。

### 坐标约定

- `ENV_SandTable` 是一张 1.2 × 0.8 m 的桌子，沙面高 0.86 m。永昌堡按 **1:500** 缩进沙面，数据直接读 `Data/map/yongchang_layout.json` 里的墙线、河、浃、护城河、内塘和田块。
- 方向：堡的南北长轴沿桌子长边，**北 = 本地 +X**；**东 = 本地 −Y**，也就是桌子正面，海和东墙朝向玩家；西侧后沿是山。
- 海和山都做了压缩，比实际离城更近。山脚起坡在本地 Y=0.29（布局 x≈−145），靠山案西墙（x=−140 → Y=0.28）正好压在山脚。另外加了西北城外的坟地和东南海边的盐田，供拉墙线时避开。
- 沙面是一张高度场：水面下凹成槽，后沿起山，平坦处已合并成大面。
- 沙盘套件 `PROP_Sand_Wall` / `Gate` / `Tower` / `House` 的**原点都等于沙面中心**。在团结里把它们放到 `ENV_SandTable/ANCHOR_SandOrigin` 上（局部坐标 0、旋转 0）即可对齐，不需要逐件摆。

![沙盘全景（靠山 B 案，1560 皮肤），前面斜托上是四张议题纸卡](images/act2/sandtable_q.jpg)

### 墙线两案（靠山 = B 案：西墙 x=−140、南墙 z=−185）

![俯视，左：贴河；右：靠山（上方是西/山）。没选的那条线只剩深色浅沟](images/act2/sandtable_river_vs_hill.jpg)

两案的北墙、东墙、南墙位置都一样（南墙都在 z=−185），**区别只在西侧**：贴河的西墙贴着护城河内岸（x=−113）；靠山把西墙推到山脚（x=−140），把西护城河和河岸圈进城里，南墙向西多出一段，北墙西端补一小段。

| 组 | 内容 |
|---|---|
| `Wall_Fixed` | 北墙 + 东墙全段（两案共用），转角 2 个（东北、东南） |
| `Wall_River` | 南墙（x 113 → −113）+ 西墙 x=−113，转角 2 个 |
| `Wall_Hill` | 南墙（x 113 → −140）+ 西墙 x=−140 + 北墙西端补段（−140 → −113），转角 2 个 |

两案各有一份南墙，整组开关时只会显示一份。南门和南水门也是一样：`GateTower_S` / `WaterGate_S1/S2` 跟贴河组，`GateTower_S_Hill` / `WaterGate_S1_Hill/S2_Hill` 跟靠山组，**B 案下两套位置相同**（名字保留，A 现有的开关逻辑不用改）。靠山组多两道涵洞水门 `WaterGate_SW_Hill` / `WaterGate_NW_Hill`，因为它的南墙西段和北墙补段各跨一次西护城河。

### 墙线动画：沙沿线隆起、木签变墙垛

![左：拉线中（木签插下，麻线铺在沙上，沙埂按序号逐段升起）；右：墙线固定（木签换成墙垛，墙条和西门出现）](images/act2/sand_ridge_rise.jpg)

| 子物体（`ENV_SandTable`） | 用法 |
|---|---|
| `Ridge_<案>` → `Ridge_<案>_01..NN` | 沙埂分段（贴河 24 段、靠山 26 段，每段约 5 cm，梯形截面），**按墙线顺序编号**：从东南角沿南墙往西，再沿西墙往北。每段原点在段底中心，本地 +X = 前进方向。逐段把本地 Z 缩放从 0 拉到 1（每段约 0.06 s，错开播放）就是「沙沿着线隆起来」；整组缩放 `Ridge_<案>` 的 Z 也行（旧做法仍兼容） |
| `Twine_<案>` → `Twine_<案>_01..NN` | 平铺在沙面的麻线段，与沙埂一一对应。拉线时逐段显示；沙埂那一段隆起完就把对应的麻线段隐藏，即「麻线被土盖住」 |
| `Trench_River` / `Trench_Hill` | 没选的那一侧只剩的浅沟 |
| `ANCHOR_Stake_<案>_A/B` | 两根木签插下的位置：A = 西南角，B = 西北角（两案分岔的地方） |
| `StakeMerlon_<案>_A/B` | 「木签变墙垛」成对件，原点 = 插签点。`_Stake` 是木签（与 `PROP_Sand_Flags/Stake_NN` 同形，签尖没入沙里 6 mm）；`_Merlon` 是比墙角台大一圈、四角带垛口的墙垛。墙线固定时 `_Stake` 缩到 0 或隐藏，`_Merlon` 本地 Z 0→1 长出来 |
| `FX_Stake_<案>_A/B`、`FX_SandDust_<案>` | 钉桩扬沙（插签时）、隆起尘浪（沿线中点） |
| `COL_Hot_WallLine` | 墙线热区：西侧两案之间的那条带，点它开始拉线 |

建议的播放顺序：插签 A、B（`A2_PlantStake`，`FX_Stake_*`）→ 麻线逐段出现（`A2_PullString`）→ 沙埂逐段隆起、麻线逐段隐藏（`FX_SandDust_<案>`）→ 木签换墙垛 → `Wall_<案>` 整组显示、`Trench_<另一案>` 显示 → 停 0.5 s。

### 敌台、水门、王宅

| 资产 | 子物体 / 挂点 | 用法 |
|---|---|---|
| `ENV_SandTable` | `ANCHOR_Flag_East` / `ANCHOR_Flag_North` | 东墙/北墙木牌顶上的插旗点，`PROP_Sand_Flags/Flag_NN` 原点放这里 |
| | `FX_Tower_East_Rise` / `FX_Tower_North_Rise` | 升台扬沙 |
| `PROP_Sand_Tower` | `Tower_East`（东台·对海口）/ `Tower_North`（北台·对官道） | 「墙里凸出一座台」：本地 Z 从 −0.024（埋在沙面下）升到 0；小炮 `<台>_Cannon` 本地 Z 从 −0.012 升到 0 |
| | `Tower_East_Flat` / `Tower_North_Flat` | 墙条在敌台处留了缺口，没选的那座显示这段平墙补上（与 `<台>` 二选一） |
| `PROP_Sand_Gate` | `WaterGate_E` 下：`Gate_Board`、`Gate_StoneBar`、`Water_Still`、`Water_Flow`、`Water_Flow_Lines`、`Boat`、`StonePile` | 状态件，水门本地坐标（外侧 −Y） |
| | `ANCHOR_GateBoard_In` → `_Up` → `_Out` | 开闸：闸板从槽里上提到顶，再平放到墙外岸上（`_Out` 带 X 90°） |
| | `ANCHOR_StoneBar_Out` → `_In` | 闭闸：石条从城内岸边推进闸槽（`A2_PushLoop`） |
| | `ANCHOR_Boat_In` → `_Out` | 开闸后小船从城内穿过水门到城外 |
| | `ANCHOR_Water_High` → `_Low` | 闭闸：死水 `Water_Still` 从常水位降到 `_Low`，露出 `StonePile` |
| | `Water_Flow_Lines` | 流水条纹（浅色短划，周期 12.5 mm）：开闸时沿本地 −Y（出城往海）每秒移 12.5 mm 循环；也可以对 `M_A2_MiniWaterFlow` 做 UV 滚动 |
| | `FX_WaterGate_E_Splash`、`FX_WaterGate_E_Flow` | 石条入槽水花；流水（`PF_VFX_WaterFlow` 的本地 +Z 已朝出城方向） |
| `PROP_Sand_House` | `House_20`（王叔杲宅，北墙外合院）+ `ANCHOR_House_20_Out`（原位）/ `_Over`（越墙中点，高 3 cm）/ `_In`（圈进墙内落位：北墙内、下河东岸，不压民居片和水田） | 「推一下，就是三百两」：Out → Over → In 两段插值；留在墙外就不动。`ENV_SandTable` 里同名的 `ANCHOR_House_20_Out/In` 是同一位置（在沙盘根下），另有 `FX_House_20` |

![左：东水门开闸（闸板搁岸上、流水条纹、小船）；右：闭闸（石条入槽、死水）](images/act2/sand_watergate.jpg)

### 纸卡（三议题 + 王宅）

![四张议题纸卡贴图：墙线 / 敌台 / 水门 / 王宅](images/act2/sand_cards.jpg)

- 贴图 `T_SandCard_Wall_D` / `_Tower_D` / `_Water_D` / `_House_D`（1024 方图，`Assets/Art/Props/PROP_Sand_Flags/`），Blender 文字（宋体）竖排右起 + Workbench 平光渲出，numpy 做旧纸纹。内容出自策划案 §4.1 / §5：右起第一列是议题，然后是**甲**（朱框）主列 + 副列、**乙**主列 + 副列，最左一列朱字是代价。
- 3D：`PROP_Sand_Flags` 里的 `Card_Wall` / `Card_Tower` / `Card_Water` / `Card_House` 是 9 cm 方卡（正面 5×5 格、四角微翘，正面 UV 正好 0..1），原点在卡底中心。`ENV_SandTable` 正面挂了一条斜木托 `CardTray`，四个落位 `ANCHOR_Card_<议题>`（从左到右：墙线、敌台、水门、王宅，已带 14° 倾角）——卡片挂到锚点下，局部坐标、旋转清零。
- **当 UI 用**：同一张贴图直接放 RawImage（或把导入类型改成 Sprite）。点选区按贴图横坐标 u（0 = 左，1 = 右）：议题 u 0.81–0.90；甲 u 0.57–0.73；乙 u 0.33–0.49；代价 u 0.17–0.24。

![斜木托上的四张纸卡](images/act2/sand_card_tray.jpg)

### 1941 / 1945 皮肤

![左：1941 断角（劈裂残茬 + 漏下的沙）；右：王宅木片推进墙内](images/act2/sand_1941_house20.jpg)

| 皮肤 | 几何 | 材质 |
|---|---|---|
| 1560 | 默认 | 导入的 `M_A2_*` |
| 1941 | 隐藏 `Rim_Corner_FL`，显示 `Rim_Broken_FL_1941`（前左角劈裂的残茬、桌面裂开一块）和 `SandSpill_1941`（缺口塌下来的沙、地上一摊） | `Skins/M_A2_<名>_1941.mat`：饱和度 ×0.45、向灰土色靠 35%，叠积灰遮罩 |
| 1945 | 同 1941，再显示 `Cover_1945`（蒙布），摆到祠堂角落 | `Skins/M_A2_<名>_1945.mat`：在 1941 上再压暗 30%，积灰略淡（盖着布） |

- 积灰遮罩 `T_SandTable_Dust_Mask.png`（1024，可平铺，RGB = A = 积灰量，`Assets/Art/Environments/ENV_SandTable/`）在生成 `ENV_SandTable` 时由 numpy 程序化写出。
- 皮肤材质在团结里生成：菜单 **入谱 / 第二幕 / 生成沙盘皮肤（1941 · 1945）**，或命令行 `-executeMethod Rupu.EditorTools.RupuSandSkins.BuildCLI`。它从 6 个沙盘 FBX 里收集 `M_A2_*`（含纸卡 `M_A2_Card_*`），复制出两套 .mat 到 `Assets/Art/Environments/ENV_SandTable/Skins/`。积灰用 URP Lit 自带的 Detail（`_DetailMask` 读 A 通道 + `_DetailAlbedoMap` 同一张图，`_DETAIL_SCALED`）：积灰处提亮、干净处略暗，不需要自定义着色器。可重复执行。
- 切皮肤（A）：遍历沙盘根下所有 Renderer，把 `sharedMaterials` 里名为 `X` 的换成 `Skins/X_1941`（或 `_1945`）。切回 1560 用原材质。

### 子物体总表（其余）

| 资产 | 子物体 / 挂点 | 用法 |
|---|---|---|
| `ENV_SandTable` | `Table`、`Sand`、`Static_Minis`（官道、坟地、盐田、东墙和北墙边插旗用的木牌）、`CardTray` | 静态 |
| | `CAM_Overview` / `CAM_East` / `CAM_North` + `LOOK_*` | 三个固定机位和对应的注视点（LookAt） |
| | `COL_Hot_EastWall` / `NorthWall` / `WaterGate` / `WangHouse` / `WallLine` | 沙盘模式 Raycast 用的热区，导入后去掉渲染器 |
| | `ANCHOR_SandOrigin`、`ANCHOR_Stand`、`ANCHOR_Stand_Shugao`、`ANCHOR_Stand_Pei` | 套件原点、王砚站位，王叔杲在右侧报数，王沛在左侧 |
| | `FX_SandDust`、`FX_Water_E` | 进沙盘扬沙、东水门水花 |
| `PROP_Sand_Wall` | `Wall_Fixed/River/Hill`：组空物体，整组 SetActive；下面是 `<组>_NN` 墙条和 `<组>_Corner_N` 转角 | 每段墙条约 5 cm、原点在底中心、可单独复制拼接。`Kit_Straight_L`（5 cm）/ `Kit_Straight_S`（2.5 cm）/ `Kit_Corner` / `Kit_GateSeg` 是散件母版，摆在桌外 Y=−0.5 处 |
| `PROP_Sand_Gate` | `GateTower_N/E/S/W`、`Wengcheng_E`、`WaterGate_E/N1/N2/S1/S2` + 靠山组 `GateTower_S_Hill/W_Hill`、`WaterGate_S1/S2/SW/NW_Hill` | 见上文 |
| `PROP_Sand_Flags` | `Flag_01..06`（红、蓝、黄各两面）、`Stake_01..04`、`Twine`、`Rice_01..03`、`Card_*` | 原点就是插入点。`Twine` 沿本地 +X 长 0.1 m、原点在一端，缩放 X 即可拉到两签之间 |

![东墙近景：垛口朝外、环海门和瓮城、东台、东水门和浃](images/act2/sandtable_eastwall.jpg)

### VFX 挂点（粒子在 `RupuVfx`，这里只留挂点）

| 动作 | 挂点 | 建议粒子 |
|---|---|---|
| 进沙盘 / 插旗 | `FX_SandDust`、`FX_Tower_*_Rise` | `PF_VFX_SandPuff` |
| 钉桩 | `FX_Stake_<案>_A/B` | `PF_VFX_SandPuff`（缩小） |
| 墙线隆起 | `FX_SandDust_<案>`，或逐段在 `Ridge_<案>_NN` 原点播 | `PF_VFX_WallRise`（沿本地 X，缩放到 5 cm 段长） |
| 推王宅木片 | `FX_House_20` | `PF_VFX_SandPuff` |
| 石条入槽 / 开闸流水 | `FX_WaterGate_E_Splash`、`FX_WaterGate_E_Flow`、`FX_Water_E` | `PF_VFX_MortarSplash`（改色）/ `PF_VFX_WaterFlow` |
| 凿碑火星 | `ENV_Stele/FX_Chisel_1..3` | `PF_VFX_StoneSparks` |

### 三角面与材质

`ENV_SandTable` 5220，`PROP_Sand_Wall` 2180，`PROP_Sand_Gate` 1292，`PROP_Sand_Tower` 272，`PROP_Sand_House` 556，`PROP_Sand_Flags` 1376（都在规格内）。

策划案说「1 材质、顶点色」，这里没有照做，改为每种地物一个 `M_A2_*` 纯色材质（沙、深沙、苔、田、水、流水、流水条纹、山、木、墙、瓦、铁），纸卡各一个带贴图的 `M_A2_Card_*`。原因是管线目前只认 Base Color；如果要压成一个材质，可以在团结里烘成顶点色。

## 族约 / 名录 / 田契 / 图卷 / 筑堡道具

![道具一览（白色胶囊是 1.75 m 参考人）](images/act2/props_sheet.jpg)

| 资产 | 三角面 | 造型 | 子物体 / 挂点 |
|---|---|---|---|
| `ENV_Stele` | 1182 | 须弥座、碑身、圆首，碑额四字「王氏族约」，左侧刻有总纲两行 | `Clause_1..3`（右起竖排）各含 `_Blank` / `_Carved` 两态；`FX_Chisel_1..3`；`ANCHOR_Carver` |
| `PROP_Covenant` | 1508 | 十块圆角木牌，墨字行数各不相同 | `Board_01..10`（平放两排）、`FX_Ink` |
| `PROP_Roster` | 1012 | 摊开的名录、合册、卷、名签、笔、砚、印 | `Roster_Open`、`InkRow_01..12`（写完一个名字显示一行，从右页起竖排）、`Roster_Closed`、`Roster_Scroll`、`NameTag_Stack`、`NameTag_01..04`、`Brush`（原点在握笔处，笔杆沿本地 +Z）、`Inkstone`、`Seal`、`Seal_Mark`（盖印后显示） |
| `PROP_Deed` | 996 | 竖排契文、边框、两方红印 | `Deed_Flat` / `Deed_Folded` |
| `PROP_Blueprint` | 488 | 图上画有城墙轮廓、上下河、敌台（东台、北台用红色标出） | `Scroll_Rolled` / `Scroll_Open` / `Fragment_1941`（1941 烧残页） |
| `PROP_Survey` | 652 | 罗盘、立杆垂准、墨斗、木桩、一丈长的丈杆 | `Compass`、`Plumb`、`LineReel`、`Stake_01..03`、`MeasurePole` |
| `PROP_Scaffold` | 996 | 杉木杆，绑扎处做了缠绳 | `Bay_Standard`（2 × 1.1 × 2 m，可上下左右拼，靠墙一侧为 +Y）、`Bay_Corner`、`Ladder`（3 m）、`ANCHOR_Climb` |
| `PROP_StoneBlock_S/M/L` | 80 / 92 / 116 | 倒角料石，带錾纹和顶面绳槽，尺寸分别为 0.4、0.7、1.1 m | — |
| `PROP_Mortar` | 304 | 铁箍木桶、拌灰槽、抹子 | `Bucket`、`Trough`、`Trowel`、`FX_Splash` |
| `PROP_Winch` | 444 | 4 m 三脚杉木架加顶滑轮，地面绞车 | `Frame`、`Drum`（绕本地 X 转）、`Rope_Hang`（向下 1 m，缩放 Z 等于吊绳长度）、`Hook`、`ANCHOR_Crank`、`ANCHOR_Load` |
| `PROP_Cart_Wheelbarrow` | 412 | 中置大轮、两侧载货板、轮罩，把手朝 +Y | `Body`、`Wheel`、`ANCHOR_Push` |
| `PROP_Cart_Flat` | 632 | 平板、两轮，车辕朝前（−Y） | `Bed`、`Wheel_L`、`Wheel_R`、`ANCHOR_Pull` |
| `PROP_Tools` | 294 | 錾子、手锤、框锯、木夯、铁锹、木槌 | `Chisel`、`Hammer`、`Saw`、`Rammer`、`Shovel`、`Mallet`。每件原点在握点、沿本地 +Z，平放展示时带了 −90° 旋转，挂到手上时把局部旋转清零 |
| `PROP_Rope` | 982 | 绳卷、4 m 拉绳、兜料石的双股吊索加顶环 | `Coil`、`PullRope`（沿 +X）、`Sling` |

## 动作（Humanoid 共用，资产名 `CH_WangYan_1941@<动作>`）

动作的关键帧写在 `rupu_act2.py` 的 `A2_GESTURES` 里，通过 `GESTURE_HOOKS` 注册，由 `rupu_char.build_gesture` 生成。

所有关键帧都做了**自动落地**（`_grounded`）：生成时逐帧量网格最低点，把髋高调到脚、膝或身体刚好贴地，所以跪、趴、弓步都不会穿地。名字带 `Loop` 的由导入器自动设成循环。桌面类动作按 0.8–0.86 m 的桌高（沙盘、供桌）摆手。

| 动作 | 帧（24 fps） | 对应清单 3.6 | 说明 |
|---|---|---|---|
| `A2_SpearStamp` | 44 | 王沛枪顿地 | 右手握竖枪提起再顿下，三下，短（第 9、19、29 帧落地） |
| `A2_PointLine` | 64 | 王沛指墙线 | 右臂平伸，沿墙线从右扫到左，头跟着转 |
| `A2_KneelDie` | 56 | 王沛跪死 | 中矢一顿，拄枪单膝，再双膝跪下垂头。**不倒，停在末帧** |
| `A2_SlamDeed` | 40 | 王叔杲拍田契 | 举手后一掌拍在桌上，按住半秒 |
| `A2_Abacus` | 48 | 王叔杲拨算盘 | 左手托盘，右手拨三下后停 |
| `A2_UnrollScroll` | 40 | 王叔杲展开图卷 | 双手并拢后向两边推开，停在展开姿势 |
| `A2_CloseGap` | 64 | 王德合龙 | 弓步双手推合，较劲几下，最后一推到位后站直 |
| `A2_HandTag` | 40 | 王德递腰牌 | 右手到左胯摘牌后向前递，微低头，停住 |
| `A2_FallDead` | 40 | 王德倒地 | 中刀，跪倒，向前扑倒趴地，停在末帧 |
| `A2_PlantStake` | 36 | 王砚插木签（也用于敌台插小旗） | 俯身举签，一下插进沙里 |
| `A2_PullString` | 48 | 王砚拉麻线 | 捏住线头沿桌面往右拉出墙线 |
| `A2_PushLoop` | 28 | 王砚推石入闸 + 群众推车 | 前倾，双手低抵，原地迈步 |
| `A2_LoadCannon` | 48 | 王砚装炮（试炮可配合 `A2_PointLine`） | 弓步，双手横握送弹杆捅两下 |
| `A2_ChiselLoop` | 16 | 王砚凿碑 + 石匠凿石 | 左手扶錾，右手抡锤，第 10 帧落锤。策划案要求「三下」，播 3 个循环即可 |
| `A2_WriteLoop` | 48 | 王砚写名 | 俯身，左手按纸，右手小幅运笔 |
| `A2_Stamp` | 40 | 王砚盖印 | 提印后按下，停半秒再提起。按下的瞬间显示 `Seal_Mark` |
| `A2_CarryLoop` | 32 | 群众抬石 | 双手捧石在腹前，后仰原地走 |
| `A2_RamLoop` | 24 | 群众夯土 | 举夯后屈膝砸下，第 14 帧落夯 |
| `A2_ClimbLoop` | 24 | 群众爬架 | 交替伸手、抬腿；在团结里把根节点按每循环约 0.56 m 往上移 |
| `A2_HaulRopeLoop` | 24 | 群众拉绳（吊石、绞绳） | 弓步后仰，双手交替往怀里拉 |

关键帧检查图（每行一个动作，每个人物是一个关键帧）：

| | |
|---|---|
| ![](images/act2/gestures_0.jpg) 指墙线 / 跪死 / 拍田契 / 算盘 / 展卷 | ![](images/act2/gestures_1.jpg) 合龙 / 递腰牌 / 倒地 / 插签 / 拉线 |
| ![](images/act2/gestures_2.jpg) 推 / 装炮 / 凿 / 写名 / 盖印 | ![](images/act2/gestures_3.jpg) 抬石 / 夯土 / 爬架 / 拉绳 |

实际播放的帧（倒地、推、跪死末帧），验证落地修正：

![](images/act2/gestures_fall_push_kneel.jpg)

### 给 A 的接入说明

- 每个动作要在 `AC_Humanoid_Locomotion` 里加一个**同名状态**（例如 `A2_SpearStamp`），脚本用 `CrossFade` 进入。这和第一幕的做法一样：无连线，`RupuArtImporter` 把根运动烘进姿势。
- `A2_KneelDie`、`A2_FallDead`、`A2_HandTag`、`A2_UnrollScroll` 停在末帧，需要保持姿势时不要自动回到 Locomotion。
- 手上的道具（枪、算盘、图卷、錾子和锤、笔、印、夯）没有绑在动作里。要挂到 `RightHand` / `LeftHand` 骨骼上：`PROP_Tools` 和 `Brush` 的原点就是握点。

## 重新生成

```bash
cd /Users/anruikang/Downloads/game_race
# 人物 / 道具 / 动作（--force 覆盖已存在的 .blend；名单见 rupu_act2.recipes()）
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/build_yongchang.py -- \
  --only ENV_SandTable,PROP_Sand_Wall,NPC_MingElder_A,CH_WangYan_1941@A2_SpearStamp,... --force
```

沙盘套件依赖 `Data/map/yongchang_layout.json`。布局重新生成后，需要重跑 `ENV_SandTable` 和 `PROP_Sand_*`（`ENV_SandTable` 会顺带写出积灰遮罩，`PROP_Sand_Flags` 会顺带渲出四张纸卡贴图），然后在团结里重跑 `RupuSandSkins.BuildCLI`。

## 还没做

- VFX 粒子：沙盘扬沙、墙线隆起、凿石火星、灰浆溅、夯土尘、墨迹、纸页、印章、水门水流、炊烟、雨。目前只留了挂点。
- 沙盘「1 个材质 + 顶点色」版本。
- 表情贴图、手指骨（手目前是一整块）。

## 第二幕补缺口（2026-11-27，对照 [`第二幕_策划对照与建模缺口.md`](第二幕_策划对照与建模缺口.md)）

| 文档 | 内容 | 生成模块 |
|---|---|---|
| 本文「沙盘」一节 | 靠山 B 案（西 −140 / 南 −185）、墙线分段隆起、木签变墙垛、水门开闭锚点、王宅木片三落位、1941/1945 皮肤（`RupuSandSkins.BuildCLI`）、纸卡 | `rupu_act2.py`、`rupu_a2_sand.py` |
| [`act2_text.md`](act2_text.md) | 族约碑凿三下、名录 30 名（5 秒四段 + 空白格）、匾 / 旗 / 灯 / 印文字贴图 | `rupu_a2_text.py` |
| [`act2_site.md`](act2_site.md) | 城墙生长四阶段、合龙缺口、工地 overlay、水门开闭、城门门扇与碰撞、王宅拆梁、盐场三阶段、北门战后现场 | `rupu_a2_site.py`、`rupu_ming_civic.py` |
| [`act2_anim.md`](act2_anim.md) | 拆梁、看船、试炮、1v3 枪术、义师出战、护民、遗体、族老拂袖；饭篮、明代灯笼、撬杠、火绳杆 | `rupu_a2_anim.py` |
| [`act2_city_lod.md`](act2_city_lod.md) | 明代建筑自动 LOD（导出时生成）、石板路路口 / 排水沟 / 墙外土路 / 市场货品、`Data/map/ming_footprints.json` 占地表 | `rupu_pipeline.py`、`rupu_a2_city.py` |
