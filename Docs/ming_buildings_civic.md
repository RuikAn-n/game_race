# 明代 1560 公共建筑 + 第二幕场景组

依据：[`入谱_当前建模缺口清单.md`](入谱_当前建模缺口清单.md) 3.2、3.5，[`入谱_美术建模清单.md`](入谱_美术建模清单.md) 3.2、3.4、3.6，[`入谱_第二幕_筑堡_策划案_v1.md`](入谱_第二幕_筑堡_策划案_v1.md)。
全部是程序化白模，生成器是 `Tools/blender/rupu_ming_civic.py`（由 `build_yongchang.py` 驱动）。明代民居套件 `KIT_Ming_House` 在另一份文档里。

![明代环海楼](images/ming/civic_huanhai_front.jpg)

## 完成情况

| 清单 ID | 资产 | 状态 | 三角面 |
|---|---|---|---:|
| `BLD_MING_AncestralHall` | `BLD_MING_AncestralHall` | ✅ | 4.1k |
| `BLD_MING_Temple` | `BLD_MING_Temple` | ✅ | 2.7k |
| （城门楼，地图 kind `gate_tower`） | `BLD_MING_GateTower` | ✅ | 2.6k |
| `BLD_MING_HuanhaiLou` | `BLD_MING_HuanhaiLou` | ✅ | 3.8k |
| `BLD_MING_WaterGate` | `BLD_Wall_WaterGate`（共用几何）+ `BLD_MING_WaterGate_Sluice` | ✅ | 0.9k |
| `KIT_Ming_Wall` | `BLD_Wall_*`（共用几何，换材质）+ `ENV_NorthGate_Build` 的工地件 | ✅（不重做城墙） | — |
| `ENV_NorthGate_Build` | `ENV_NorthGate_Build` | ✅ | 3.9k |
| `ENV_WangHouse` | `ENV_WangHouse` | ✅ | 6.3k |
| `ENV_SaltField` / `ENV_SaltPan` | `ENV_SaltField`（8 块盐田是子物体 `SaltPan_1..8`） | ✅ | 1.1k |
| `ENV_BrineVat` 3 尺寸 | `PROP_BrineVat_S` / `_M` / `_L` | ✅ | 0.3k × 3 |
| `ENV_SaltFurnace` | `ENV_SaltFurnace` | ✅ | 0.7k |
| `ENV_SaltShed` | 用 `salt_shed`（另一个子代理做 `BLD_MING_SaltShed`） | — 不在本批 | |
| `PROP_Salt` | `PROP_SaltSet` | ✅ | 0.4k |
| `PROP_Firewood` | `PROP_Firewood` | ✅ | 0.4k |

所有资产都通过了规格检查（Buildings ≤20k，Environments ≤40k，Props ≤3k）。

## A. 替换地图里 ROC 占位的明代建筑

四座建筑和同 kind 的民国模型对齐：占地、朝向（正面 −Y，进团结后是 +Z）、原点、台基高度、门位都一致。下面是量出来的包围盒（含檐口、旗杆）：

| 资产 | 包围盒 x / y | 对照 ROC | 原点 |
|---|---|---|---|
| `BLD_MING_AncestralHall` | ±10.25 / −19.8..18.8 | ±10.15 / −19.8..18.7 | 占地中心地面 |
| `BLD_MING_Temple` | ±8.15 / −11.95..11.15 | ±8.75 / −11.95..11.0 | 占地中心地面 |
| `BLD_MING_GateTower` | ±7.25 / ±4.45 | ±7.25 / ±4.45 | 城墙顶（布局 y=7.0），坐在 `BLD_Wall_GateBase` 上 |
| `BLD_MING_HuanhaiLou` | −11.35..13.6 / −6.15..5.95 | ±11.25 / ±5.65 | 城墙顶，坐在 `BLD_Wall_GateBaseL` 上（+X 多出的是旗面） |

### 祖祠 `BLD_MING_AncestralHall`（20 × 36）

![祖祠](images/ming/civic_ancestral_front.jpg)

和民国版一样分三进，台基也一样：门厅 0.55、正厅 0.9、后堂 0.6。明代版是刚建好的新祠：门厅前面有 1.4 m 深的凹廊，配四根廊柱、额枋斗拱、抱鼓石、门簪、门钉和大门匾，屋顶是悬山。两侧是廊庑，内院有御路和鼎炉。月台三级台阶，带石栏。正厅五开间，中间三间是格扇，两侧次间开窗，屋顶是歇山。后天井有井，后堂前檐也是格扇。门前那对功名旗杆和民国版在同一个位置。

门窗位置对齐室内的 `BLD_INT_AncestralHall`：正门 2.8 × 3.4，±4.6 处开窗；正厅前檐中间 5 m 开敞，±5.4 处开窗；山墙在 y=1.0 处开侧门。所以进出室内场景时外壳的门窗是对得上的。第二幕用到的沙盘、族约碑、名录桌都在室内场景里，外壳只是外观。

锚点：`ANCHOR_door_front / courtyard / hall_front / hall_door`。

俯视图：![祖祠俯视](images/ming/civic_ancestral_top.jpg)

### 汤和庙 `BLD_MING_Temple`（16 × 22，巡游起点）

![汤和庙](images/ming/civic_temple_front.jpg)

山门是三开间红墙，前有檐柱、斗拱、三门、匾，屋顶歇山，两侧是八字墙。院子里有三足鼎香炉、两根挂红幡的幡杆（明代 `M_Flag` 是火色）和一对石灯。正殿六柱五开间，前面是格扇，屋顶是重檐歇山，腰檐下面带一圈高窗。

锚点：`ANCHOR_procession_start`（山门外，巡游起点）、`gate_in`、`incense`、`hall_front`、`altar`。

### 城门楼 `BLD_MING_GateTower`（12 × 6.4）

![城门楼](images/ming/civic_gatetower_front.jpg)

底层外圈 4 × 2 根柱子，中间是木构穿堂：前面一排格扇，后墙是木板，两端各开一个 1.6 m 的门。城墙走道上的人可以从前廊、后廊或者穿堂走过去，这一点和民国版的空柱廊一样。往上是楼板、腰檐、四面平座栏杆，上层木构四面开窗，挂匾，屋顶是重檐歇山。

锚点：`ANCHOR_walk_W / walk_E`（走道进出口）、`ANCHOR_lookout`（平座）。

> **第二幕补充**（见 [`act2_site.md`](act2_site.md) §4）：加了可开合的城门门扇 `Gate_Door_L/R`（原点在门轴，放在城楼本地 z=−7.0 的门洞里）、门闩 `Gate_Bar`，以及一整套 `COL_*`（城楼底层和门洞），门洞净宽 3.9、净高 3.6。外轮廓占地没有变。

### 环海楼 `BLD_MING_HuanhaiLou`（20 × 8.8）

尺寸照 `BLD_INT_HuanhaiLou` 做：底层净高 3.9，二层楼面 4.2，上层 3.1。

- **底层**是青砖墙。前后墙正中各开一个券门（宽 4.8，券脚 2.6），券脸是石的。射孔在 ±6.2 和 ±8.4，位置和内景一样；城外一侧另有两个炮窗（±4.1）。两端墙各开一个真门洞（1.6 × 2.6），城墙走道可以穿过楼底。内部有两道隔墙，门位和内景一致。
- **二层**楼板带前檐平座（y −5.4..−4.4），下面是斗拱托梁，平座外沿有栏杆。上层军议厅的墙在 y=±3.8、x=±9.2，窗位照内景；正面是格扇加匾。外围一圈檐柱，每根柱头有斗拱。
- **屋顶**拆成两个子物体：后面和两端的腰檐 `ROOF_Waist`，顶上的大歇山 `ROOF_Upper`。俯视军议时可以隐藏，露出楼板和城墙顶。正常俯视看到的是一个清楚的歇山轮廓：屋脊颜色较浅，四角起翘。
- 门台东北角有一根 13 m 的旗杆，挂火色旗，俯视也能看见。

![环海楼俯视](images/ming/civic_huanhai_top.jpg)

锚点（和内景同名，方便共用脚本）：`ANCHOR_walk_W / walk_E / gate_out / gate_in / balcony / muster_table / flagpole / cam_top_upper`。

### 水门：`BLD_Wall_WaterGate` + 闸套件 `BLD_MING_WaterGate_Sluice`

![闸套件](images/ming/civic_sluice.jpg)

城墙、敌台、水门、马道、瓮城两个年代共用几何，只换材质，**这次没有重做**。清单里 `BLD_MING_WaterGate` 的玩法需求（策划案 §4.2：「把石条推进闸槽（闭），或抽走闸板（开）」，以及「下河摸闸，找 3 个闸位」）用一个配套的闸套件来满足。

先量了 `BLD_Wall_WaterGate` 的门洞：x ±3.2，洞底 z=−1.8，拱脚 1.6，拱顶 4.8，洞深 y ±2.5。原有的外侧闸槽在 y≈−0.7，那块半开的闸板是烘在网格里的。套件放在**城内一侧**，和水门同位置、同旋转摆放：

| 子物体 | 说明 |
|---|---|
| `BLD_MING_WaterGate_Sluice` | 两侧石闸槽（木闸槽 y 0.85..1.45，石条槽 y 1.55..1.97）、闸底槛石、门闩托、城顶闸缝铁盖板和绞盘架 |
| `Sluice_Gate` | 闸板 5.9 × 2.6，带铁箍和吊环。枢轴在底边中心，关闸时在洞底。**沿 +Z 平移约 1.8 m 就是开闸**；再往上会碰到拱腹，看起来像缩进墙里的闸缝 |
| `NOCOL_Sluice_Rope` | 两根吊绳，从闸板顶连到绞盘。开闸时可以缩短 Z 或直接隐藏 |
| `Sluice_Latch` | 门闩横木，架在 z=0.85 的门闩托上，抽走后才能提闸 |
| `Sluice_StoneBar_1..3` | 三根石条，叠在外侧石条槽里（z −1.8 / −1.3 / −0.8），表示「闭」。玩法里从岸上推进来 |
| `Sluice_WinchDrum` | 城顶绞盘鼓，枢轴在轴心，**绕局部 X 轴转** |
| `FX_WaterFlow` / `FX_Splash` | 开闸后的水流、水花 |
| `ANCHOR_Sluice_Spot_1..3` | 水下三个闸位（摸闸小游戏） |
| `ANCHOR_Winch` / `ANCHOR_Latch` | 城顶绞盘操作位 / 水边拔门闩的站位 |

> **第二幕补充**（见 [`act2_site.md`](act2_site.md) §3）：会切换的部件改成两组 `State_Closed` / `State_Open`，A 只需 SetActive。闭闸组是 `Sluice_Gate`、`Sluice_Latch`、`Sluice_StoneBar_1..3`、死水；开闸组是 `Sluice_Gate_Open`、流水、`Sluice_Boat`。上表的名字在闭闸组里都还在。

`KIT_Ming_Wall` 的「墙身、垛口、马道、门洞、水门、台阶」都由现有的 `BLD_Wall_*` 换明代材质得到。明代特有的施工状态（夯土、半砌、留槎、合龙）放在下面的北门工地里。

## B. 第二幕场景组

### 北门工地 `ENV_NorthGate_Build`（筑堡主线 / 殉难）

| Stage_1 | Stage_1+2 | Stage_1+2+3 |
|---|---|---|
| ![](images/ming/civic_northgate_stage1.jpg) | ![](images/ming/civic_northgate_stage2.jpg) | ![](images/ming/civic_northgate_stage3.jpg) |

| 缺口未合龙（城外看） | 合龙后 |
|---|---|
| ![](images/ming/civic_northgate_gap.jpg) | ![](images/ming/civic_northgate_closed.jpg) |

城墙沿 X 方向，城外在 −Y，剖面和 `BLD_Wall_Seg` 的 `wall_body` 一样：底宽 5 m，外侧收分，墙高 7.0，走道面 7.08。整段长 40 m，正好是 5 个 8 m 模块：

- `Wall_Done`：x −20..−12 和 12..20 两段已完工城墙，带垛口。
- `Stage_1`：x −12..12 的条石基础，从 −0.5 到 1.5 m，缺口处也有。
- `Stage_2`：外侧包石，内侧是分层夯土（0.5 m 一层，两种土色交替），外包石比夯土低半层，石块零散码放，看起来是半砌状态。内侧露出夯土层，有夹板和立桩。两侧墙段砌到 4.0 m，缺口 x −4..4 只到 2.5 m。
- `Stage_3`：两侧墙段砌到墙顶，走道铺好，垛墙只砌了一部分，用的是新石色 `M_MC_StoneNew`。靠缺口的两端每隔一层伸出半块石头（留槎）。
- `Closure`：合龙段，x −4..4，从 2.5 m 砌到垛口，城外一面嵌一块合龙石（匾）。

**四个物体是叠加关系**：依次打开 Stage_1 → Stage_2 → Stage_3 → Closure。「墙线隆起」可以对每个 Stage 做从 −Z 升起的动画，配 `FX_WallRise`。王德合龙就是打开 `Closure`，配 `FX_ClosureDust`。

其他子物体：

- `Scaffold`：城内侧脚手架，毛竹立杆，2、4、6 m 三层跳板，有剪刀撑和外侧爬梯，缺口处留空。缺口上方是三脚吊架，带滑轮和吊石兜，牵绳通到绞盘位。坡道顶有一块上料木板桥。
- `Ramp`：城内土坡道，从 x=21 地面升到 x=6，高 4.0，接 Stage_2 的高度。坡面铺木板，两边有边木。
- `Yard`：石料场，有三层条石垛、块石、碎石堆、凿石垫墩。另外有灰浆槽（槽里是石灰面）、石灰堆、两个桶。城外墙脚有一排放线木桩（红头），桩间拉麻线。缺口两端各插一根木签（拉线、插签的玩法用）。石料场外围有木栏。
- `Ground`：52 × 32 的踩实泥地，比地图地面高 3 cm，避免 z-fighting。

| 挂点 / 锚点 | 用途 |
|---|---|
| `FX_RamDust_1/2` | 夯土尘 |
| `FX_WallRise` | 墙线隆起 |
| `FX_Chisel` | 凿石火星 |
| `FX_MortarSplash` | 灰浆溅 |
| `FX_ClosureDust` | 合龙 |
| `ANCHOR_Closure` | 王德合龙，站在缺口顶 |
| `ANCHOR_WangPei_Watch` | 王沛北门看船，站在已完工墙的走道上 |
| `ANCHOR_WangDe` | |
| `ANCHOR_Ram_1/2` | 夯土位 |
| `ANCHOR_Carry_From/To` | 抬石起点 / 终点 |
| `ANCHOR_Winch` | 放 `PROP_Winch` |
| `ANCHOR_Gantry_Hook` | 吊钩 |
| `ANCHOR_Mortar` | |
| `ANCHOR_Stake_A/B` | 插木签 |
| `ANCHOR_Climb` | 爬梯 |
| `ANCHOR_Ramp_Top` | |
| `ANCHOR_RosterDesk` | 工地日记名 |
| `ANCHOR_StoneYard` | |
| `ANCHOR_cam_top` | |

脚手架模块、石料（三尺寸）、灰浆具、绞盘、独轮车、工具、绳索这些单独道具（3.4 的 `PROP_Scaffold / StoneBlock / Mortar / Winch / Cart / Tools / Rope`）不在本批。工地里只留了它们的位置，以及一套固定的场景件。

### 王叔杲宅 `ENV_WangHouse`（18 × 22，墙外一进院）

| 外观 | 隐藏 `ROOF_*` |
|---|---|
| ![](images/ming/civic_wanghouse_front.jpg) | ![](images/ming/civic_wanghouse_noroof.jpg) |

院子从前往后依次是：

- **门屋**：有石门框、门额，门扇是 `Door_L` / `Door_R`，枢轴在门轴上，绕 Z 转开。门屋后面朝天井开敞。
- **天井**：中间是太平缸（有水面），两边各一个花台，一条甬道直通正厅。
- **东书房**：朝天井有门和三扇格窗。里面有书案（纸、砚）、椅子、书架和画缸。
- **西厢房**：有门和窗，里面放陶缸和条桌。
- **正厅**：五开间，地面 0.45。明间敞开，上面留横披匾；次间和梢间是格扇。前面有檐柱和金柱，后面一排金柱。梁架是抬梁式外露：五架梁、瓜柱、三架梁、檩。中堂挂匾和画，摆条案、八仙桌和两把太师椅，两侧各放两把客椅。

**`Beam_Removable`**：明间东侧（x=1.5）那根五架梁做成了单独物体，长 5.3 m，截面 0.34 × 0.45，枢轴在梁的中心。对应剧情里「他选不圈，但拆自家梁木去修水门」。拆梁动画可以先把梁沿 −Z 降下来，再挪到 `ANCHOR_beam_drop`（天井）。

屋顶拆成 `ROOF_Gate / ROOF_Hall / ROOF_Study / ROOF_Wing`，在厅里拍拆梁、或者俯视的时候可以隐藏。

> **第二幕补充**（见 [`act2_site.md`](act2_site.md) §5）：`Beam_Removable` 的**原点改到梁的前端**（前金柱 y=4.2 处的梁底），不再在梁中心。拆梁改成两组：`State_Beam_Intact`（梁、`Truss_Upper_E`、`ROOF_Hall`）和 `State_Beam_Removed`（`ROOF_Hall_Broken` 塌口、`Beam_Fallen`、`Rubble_Hall`）。正厅屋面改成不填实，梁架外露。另外补了 `ANCHOR_Shugao / Door / Interior_*` 等锚点。

锚点：`ANCHOR_enter / gate_in / courtyard_talk / shugao_hall / yan_hall / beam_below / beam_drop / study_desk / study_seat / cam_hall / cam_top`。

### 盐场

![盐田](images/ming/civic_saltfield.jpg)

**`ENV_SaltField`**（32 × 22）有 8 块盐田，排成 4 × 2。外围是宽田埂路，中间一条主埂把两排盐田分开，相邻盐田之间是分埂。北侧有卤水沟 `NOCOL_BrineChannel`，每块盐田的进水口有一块小闸板。最北边是芦席风障。

- 盐田 `SaltPan_1..8` 是单独物体。**三种状态靠换材质切换**：浅水 `M_MC_Brine`、结晶 `M_Salt`、干涸 `M_MC_PanDry`。默认 1–3 号是浅水，4–6 号是结晶，7–8 号是干涸。
- 结晶态另有耙起来的小盐堆 `SaltPan_n_Heaps`，目前只有 4–6 号有。别的盐田要用，可以复制一份过去。
- 锚点：`ANCHOR_Pan_1..8`、`ANCHOR_Path_W/E`；`ANCHOR_Furnace` 是建议的灶位，在场地南侧外面。

| 煮盐灶 | 卤水缸 L | 盐具 | 柴 |
|---|---|---|---|
| ![](images/ming/civic_saltfurnace.jpg) | ![](images/ming/civic_brinevat.jpg) | ![](images/ming/civic_saltset.jpg) | ![](images/ming/civic_firewood.jpg) |

- **`ENV_SaltFurnace`**：夯土灶台上架一口大铁锅，带锅沿。前面是火口（砖框、灶膛、余烬）和灰坑，后面是烟囱。+X 侧有卤槽，从缸位斜接到锅沿；−X 侧是起盐踏台；火口旁堆着几根柴。
  - ~~`Pan_Brine` / `Pan_Salt`~~ **第二幕补充时已替换**（见 [`act2_site.md`](act2_site.md) §6）：改成三组三态 `Fire_0/1/2`、`Brine_Full/Half/Low`、`Salt_None/Crust/Heap`，每组三选一。
  - 特效挂点：`FX_Fire`（火口）、`FX_Smoke`（烟囱顶）、`FX_Steam`（锅面）。
  - 三拍小游戏的站位：`ANCHOR_Stoke`（火候）、`ANCHOR_Pour`（卤水）、`ANCHOR_Scoop`（起盐）。
- **`PROP_BrineVat_S / M / L`**：陶缸，半径和高度分别是 0.32 × 0.6、0.48 × 0.85、0.68 × 1.1。子物体有 `Vat`、`Brine`（液面，上下平移表示卤水多少）、`Lid`（S 盖着，M 和 L 半开）、`Ladle`（只有 M 和 L 有）。
- **`PROP_SaltSet`**：`SaltHeap`（盐堆）、`SaltBag_1..3`（盐袋，其中一袋叠放）、`SaltShovel`（盐铲）、`SaltBasket`（盐筐）、`SaltRake`（盐耙）。第二幕补充了起盐产出：`SaltBasket_Full/Empty`、`SaltOutput_1/2/3`、`SaltPole`（见 [`act2_site.md`](act2_site.md) §6）。
- **`PROP_Firewood`**：`WoodStack`（三层柴垛加两根桩）、`Kindling`（引火草捆）、`FireTongs`（火钳）。

## 材质

建筑只用 `Data/map/era_materials.json` 里已有的语义材质，团结会按年代换色，包括 `M_Floor_Wood`、`M_Bronze`、`M_Cloth_Red`、`M_Ceiling`。本批新增的 `M_MC_*` 只用在工地、盐场和道具上，颜色已经写在 FBX 的 Base Color 里：

`M_MC_RammedEarth` `M_MC_EarthLayer` `M_MC_StoneNew` `M_MC_Lime` `M_MC_Bamboo` `M_MC_Rope` `M_MC_Plank` `M_MC_StakeTip` `M_MC_Clay` `M_MC_ClayGlaze` `M_MC_Brine` `M_MC_PanDry` `M_MC_Iron` `M_MC_Ash` `M_MC_Char` `M_MC_StoveMud` `M_MC_Straw` `M_MC_Sack` `M_MC_Reed` `M_MC_Log` `M_MC_LogEnd`

这些场景只在 1560 出现，所以没有写进年代材质表。要在 1941 复用的话（比如盐田），在 `era_materials.json` 里补上对应的行就行。

## 给 A 的接入说明

1. **年代套件**：在 `Data/map/era_kits.json` 的 `ming` 数组里填上：
   - `ancestral_hall` → `BLD_MING_AncestralHall`
   - `temple` → `BLD_MING_Temple`
   - `gate_tower` → `BLD_MING_GateTower`
   - `gate_tower_huanhai` → `BLD_MING_HuanhaiLou`

   然后重新生成明代场景。本子任务没有改这个文件。
2. **水门**：明代场景里，在每个 `BLD_Wall_WaterGate` 的同一位置、同一旋转再摆一个 `BLD_MING_WaterGate_Sluice`。开闸时 `Sluice_Gate` 的 localPosition.y（团结）加 1.8，同时转 `Sluice_WinchDrum`；闭闸时依次显示 `Sluice_StoneBar_1..3`。原水门网格里烘进去的那块外侧半开闸板保持不动。
3. **北门工地**：放在 `Map_Yongchang_MING` 北墙通市门旁边，替换 5 段 `BLD_Wall_Seg`（城外在 −Y，进团结后是 −Z，和 `BLD_Wall_Seg` 的朝向一致）；或者单独做一个工地场景。工地日的进度：
   - 第 1 天：`Stage_1`
   - 第 2–3 天：`+Stage_2`
   - 第 4–5 天：`+Stage_3`
   - 合龙：`+Closure`

   殉难段保持缺口，也就是不显示 `Closure`。
4. **宅院 / 盐场**：都是独立的小场景。会动的子物体名见上文。人物站位用 `ANCHOR_*`。
5. **碰撞**：主网格建议用 MeshCollider。名字带 `NOCOL_` 的（吊绳、卤水沟水面）不加碰撞。坡道 `Ramp` 是实体三棱柱，可以直接走上去。城门楼和环海楼的底层保留了通道，城墙走道可以穿楼而过。
6. **新动画状态**：本批没有新的人物动作。用到的物体动画（闸板升降、绞盘转、Stage 升起、拆梁、卤水面下降）都是简单的 Transform 动画，可以在脚本里直接插值。

## 重新生成

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/build_yongchang.py -- \
  --only BLD_MING_AncestralHall,BLD_MING_Temple,BLD_MING_GateTower,BLD_MING_HuanhaiLou,BLD_MING_WaterGate_Sluice,ENV_NorthGate_Build,ENV_WangHouse,ENV_SaltField,ENV_SaltFurnace,PROP_SaltSet,PROP_Firewood,PROP_BrineVat_S,PROP_BrineVat_M,PROP_BrineVat_L \
  --force --preview <预览目录>
```

## 还没做

- `ENV_SaltShed` 盐棚由另一个子代理做（`BLD_MING_SaltShed`），这里不做。
- 3.4 的工地道具（脚手架模块、三尺寸石料、灰浆具、绞盘、独轮车、工具、绳索）不在本批。工地里留了 `ANCHOR_Winch` 等位置。
- 盐田的三态目前靠换材质，没有做水面波纹、结晶纹理这类贴图。
- 1941 版的祖祠、汤和庙、城楼仍然用民国模型。如果要「同一套几何换材质」，可以把 `BLD_MING_*` 也填进 ROC 套件，但造型是明代新建的样子，积灰、残破要靠材质和贴花来做。
