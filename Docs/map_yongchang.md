# 永昌堡总地图（第一阶段：外景）

> 城内自由探索 + 战斗用的整张外景地图。**一套布局，两个年代**：现在建好的是民国（1941）版；明代（1560）用同一布局，只换建筑模型和材质。

![俯视全图](images/map/01_overview_topdown.jpg)

| 东南鸟瞰（民国） | 俯视指挥视角 |
|---|---|
| ![](images/map/02_overview_se.jpg) | ![](images/map/03_strategy_view.jpg) |
| **主街（电线、店屋、西式立面）** | **城墙走道 → 镇山门城楼，远处罗山** |
| ![](images/map/05_main_street.jpg) | ![](images/map/08_wall_walk.jpg) |
| **环海门 + 瓮城** | **同一布局的明代场景（目前用民国模型占位、明代配色）** |
| ![](images/map/11_wengcheng_top.jpg) | ![](images/map/MING_02_overview_se.jpg) |

布局总图（矢量，标了全部地名）：[`Data/map/yongchang_layout.svg`](../Data/map/yongchang_layout.svg)

---

## 1 史料依据与取舍

「大体吻合」即可。下面左列是查到的资料，右列是地图里的做法。

| 史料 | 地图做法 |
|---|---|
| 堡呈长方形，南北约 738 m（另说 778 m），东西约 445 m（另说 455 m），周长约 2.4–2.7 km，墙高约 8 m，基宽约 4 m | 长方形；**平面距离压缩 0.5 倍** → 226 × 370 m（墙中线）；墙高（走道 7 m + 垛口到 8.75 m）、墙厚 5 m、建筑、人物都按**真实尺度** |
| 四座陆门：东「环海」（最大城楼，下有旧瓮城），南「迎川」（临河），西「镇山」（靠罗山），北「通市」（通集市） | 四门方位照搬；环海门做 24 m 大门台 + 环海楼 + 外瓮城；南门外是迎川河；西门外是罗山；北门外是集市街 |
| 水门四座；敌台 12 座（另说 13） | 上河、下河南北两端各一座水门 = 4 座；敌台 12 = 4 角台 + 8 马面 |
| 城内开二渠「上河」（宽约 13 m，偏西）、「下河」（约 8 m，偏东），南北贯通；上河向西开五浃（西宅、状元、三房、西门、上仓），下河向东开五浃（扑树、经魁、御史、板桥、圣门） | 上河 6 m、下河 4 m 宽，贯穿南北，经水门通护城河；十浃按名字布置（宽 3 m） |
| 王氏祖祠（1542，规模为堡内之冠，三进）；布政司祠、世大夫祠、都堂第（三面临水）、状元第、王德故居（临水）；王沛故居已难觅 | 祖祠在横街北、上河东，做成三进；其余做成一进祠第 / 合院，按名字放在相应的浃、河边 |
| 堡内有水田百余亩，战时可自给 | 堡内东北、西南各一片水田（第 6 波分粮） |
| 外有护城河，现仅存部分 | 四面护城河；南面就是迎川河，东流入海 |

**演绎（游戏需要，史料没有或位置不明）**：东水门（板桥浃穿东墙出城，赤焰 Boss 场地）、汤和庙位置、粮仓（放在上仓浃边）、码头、盐场、日伪哨卡、王叔杲宅在北墙外（第二幕「宅院抉择」）。

资料来源：
- 温州市文化广电旅游局「永昌堡」（2018、2023）：https://wl.wenzhou.gov.cn/art/2023/3/24/art_1653027_58903626.html
- 温州市文化广电旅游局「永昌堡——温柔了硝烟 惊艳了岁月」（2015）：https://wl.wenzhou.gov.cn/art/2015/9/30/art_1642046_34552988.html
- 澎湃·湃客「东南海防古堡②：永昌堡」（2020）：https://www.thepaper.cn/newsDetail_forward_8953525
- 温州网「永昌堡：私家抗倭第一堡」（2022）：https://news.66wz.com/system/2022/12/18/105529703.shtml
- 龙湾新闻网（2019）：http://www.lwnews.net/system/2019/07/26/013575475.shtml

---

## 2 地图结构

坐标：团结世界坐标，**x = 东，z = 北**，堡中心在原点，1 unit = 1 m。

```text
 罗山（西，山体）  |  西郊水田  | 护城河 | 城墙 + 城内 | 护城河 | 海塘内水田/盐田/码头 | 海（东）
                      北：通市官道 + 集市街 + 北郊水田 + 王叔杲宅
                      南：迎川河（18 m）+ 南渡路 + 南岸水田
```

| 区 | 内容 |
|---|---|
| 城墙 | 122 段城墙、8 马面、4 角台（带角楼）、4 城门台 + 城楼、4 水门 + 东水门、8 处马道（登城踏步）、环海门瓮城。走道连续可走，高 7.08 m |
| 城内 | 环城路、主街（通市门—横街）、南街（迎川门）、横街（镇山门—环海门，中段折一下）、北/中/南三条横巷、东西两条直巷、上河/下河沿河路；6 个广场（镇山门内、祖祠前庭、环海门校场、通市门内、汤和庙前、码头前） |
| 水 | 上河、下河、十浃、东水门内塘、护城河、迎川河、海；37 座桥按「路 × 水」自动生成；21 处河埠头（落水后可以爬上岸，也是取水点） |
| 建筑 | 287 个建筑位：民居 / 店屋（主街和北门外集市）/ 西式店面 / 合院 / 祠第 / 祖祠 / 汤和庙 / 粮仓 / 哨卡 / 码头 / 盐舍 |
| 植被 | 390 棵樟树/小树；罗山上有远景树 |
| 民国专属 | 电线杆 + 自动拉线（主街、横街、北官道、码头路）、两处日伪哨卡 |

### 挂点（`Rupu.MapAnchor`，在场景 `Anchors/` 下，A 用 `MapAnchor.Find(id)` 查）

| id | 用途 |
|---|---|
| `anchor_gate_N/E/S/W`、`anchor_gatetop_*` | 城门门洞（门扇/闸）、城楼（旗号/指挥） |
| `anchor_watergate_W*` | 5 座水门的闸门位 |
| `anchor_cannon_*` | 马面、角台上的火炮位（12 个） |
| `anchor_zuci_door`、`anchor_sandtable` | 祖祠正门、祖祠内沙盘（第二幕） |
| `anchor_watergate_arena` | 东水门内塘（Boss 赤焰） |
| `anchor_wengcheng_arena`、`anchor_muster_huanhai` | 瓮城（Boss 鬼倭 第 3 阶段）、环海门校场 |
| `anchor_granary`、`anchor_paddy_inner` | 粮仓、堡内水田（第 6 波） |
| `anchor_temple_front` | 汤和庙前（1945 巡游起点） |
| `anchor_dock`、`anchor_saltfield`、`anchor_wang_shugao_house` | 码头、盐场、王叔杲宅门 |
| `spawn_1941`、`spawn_1560` | 出生点（1941 码头下船 / 1560 祖祠前庭） |
| `enemy_sea`、`enemy_north_road`、`enemy_river` | 敌人来向 |

---

## 3 民国 / 明代：同一布局换建筑

```text
Data/map/yongchang_layout.json   ← 布局：每个建筑只有 kind + 位置 + 朝向 + 占地（与年代无关）
Data/map/era_kits.json           ← kind → 民国模型 / 明代模型（可多个变体，按建筑 id 稳定随机）
Data/map/era_materials.json      ← 语义材质 → 民国颜色 / 明代颜色
```

- **城墙、水门、桥、河埠头**两个年代共用几何（`BLD_Wall_*`、`BLD_Bridge_*`），只换材质：民国偏灰绿、旧；明代偏暖褐、新。
- **建筑**单独建：民国是 `BLD_ROC_*`。做明代时按**同一个 kind、同样的占地尺寸**建 `BLD_MING_*`，填进 `era_kits.json` 的 `ming` 数组，重新生成明代场景即可，布局不用动。
- 只属于某个年代的东西用布局里的 `eras` 字段控制（哨卡、电线杆只在 ROC）。

| kind | 占地 w×d (m) | 民国模型 | 明代（待做） |
|---|---|---|---|
| house_s | 10×7 | `BLD_ROC_House_S_A`（前檐廊）、`_B`（马头墙） | `BLD_MING_House_S_*` |
| house_l | 12×8 | `BLD_ROC_House_L_A`（腰檐木楼）、`_B`（挑廊 + 马头墙） | |
| shop | 6×10 | `BLD_ROC_Shop_A`（排门板 + 竖招牌）、`_B`（阁楼 + 横匾） | |
| shop_west | 8×12 | `BLD_ROC_ShopWest`（民国西式立面） | 明代改成普通店屋 |
| courtyard | 20×18 | `BLD_ROC_Courtyard`（三合院） | |
| hall_small | 14×20 | `BLD_ROC_HallSmall`（布政司祠/世大夫祠/状元第/都堂第） | |
| ancestral_hall | 20×36 | `BLD_ROC_AncestralHall`（王氏祖祠三进） | |
| temple | 16×22 | `BLD_ROC_Temple`（汤和庙，重檐） | |
| granary | 20×12 | `BLD_ROC_Granary` | |
| gate_tower | 12×6.4 | `BLD_ROC_GateTower`（城楼，底层可穿行） | |
| gate_tower_huanhai | 20×8.8 | `BLD_ROC_HuanhaiLou`（环海楼） | |
| dock / salt_shed | 20×18 / 12×8 | `BLD_ROC_Dock` / `BLD_ROC_SaltShed` | |
| checkpoint | 8×8 | `BLD_ROC_Checkpoint`（只在 1941） | — |

明代场景现在也能生成（`Map_Yongchang_MING.unity`），缺的明代模型自动用民国模型占位，只换明代配色。这样可以先验证流程。

---

## 4 怎么改、怎么重新生成

```bash
Tools/mac/build_yongchang.sh               # 布局 → Blender（只补缺的 .blend，地形每次重导）→ 团结场景 + 截图 + 可走性自检
Tools/mac/build_yongchang.sh --scene-only  # 只改了 era_*.json（颜色/套件）时
Tools/mac/build_yongchang.sh --force       # 覆盖全部程序化 .blend（会丢掉在这些 .blend 里的手改）
```

团结编辑器里：菜单 **入谱 / 永昌堡 / 生成民国场景**、**生成明代场景**、**截图**、**可走性自检**。

| 想改什么 | 改哪里 |
|---|---|
| 城门、河、街、地标的位置，压缩比例 | `Tools/map/gen_layout.py`（顶部常量 + 各 `build_*` 函数），再跑流水线。随机种子固定为 1558，结果可复现 |
| 某栋建筑的造型 | 直接在 Blender 打开 `ArtSource/Buildings/BLD_ROC_*.blend` 手改 → N 面板「入谱 → 导出到团结工程」→ 团结里重新生成场景。**手改过的 .blend 不要再用 `--force`** |
| 年代配色 | `Data/map/era_materials.json` → `--scene-only` |
| 某个 kind 用哪个模型 / 加变体 | `Data/map/era_kits.json` → `--scene-only` |

碰撞约定：模型里名为 `COL_*` 的物体只做碰撞（马道、河埠头是斜面碰撞，树和电线杆只碰树干/杆身）；`NOCOL_*`（水面、田面、远景树）没有碰撞；其他网格自动加 MeshCollider。

可走性自检（每次生成后自动跑，6 条路线全部通过）：穿通市门出城过护城河、穿环海门和瓮城到码头路、上马道登城沿走道走、北巷过上河桥、落水后从河埠头上岸、城墙不可穿越。

---

## 5 资产清单（42 个，全部登记在 `Data/asset_manifest.csv`）

| 组 | 资产 | 三角面 |
|---|---|---|
| 城墙（通用） | `BLD_Wall_Seg` `_DiTai` `_Corner` `_GateBase` `_GateBaseL` `_WaterGate` `_Ramp` `_Wengcheng` | 132–590 |
| 桥（通用） | `BLD_Bridge_3n/3w/4n/4w/6n/6w/10w/18w`（数字 = 跨度 m，n/w = 窄 3.2 / 宽 6.4） | 132–420 |
| 河埠头 | `BLD_CanalSteps` | 92 |
| 民国建筑 | `BLD_ROC_*` 17 个 | 252–1518 |
| 道具 | `PROP_Tree_Camphor` `PROP_Tree_Small` `PROP_ROC_TelegraphPole` | 72–160 |
| 环境 | `ENV_Yongchang_Ground`（地面 + 道路 + 河道岸壁，按布局切出）`_Water` `_FieldsIn` `_FieldsOut` `ENV_Luoshan_Hills` | 2–25.7k（上限 40k） |

全部是**程序化白模**（`Tools/blender/build_yongchang.py` + `rupu_kit.py`），风格上是低模、纯色加纸纹（`T_PaperGrain_D`，团结里自动生成）、低饱和。后续美术可以在这些 .blend 上直接细化。

## 6 下一步（建议）

1. 明代建筑套件 `BLD_MING_*`（同 kind 同占地），先做 house_s / shop / gate_tower / ancestral_hall 四个最显眼的。
2. 民国氛围：雨、地面湿反光、标语贴花（墙面 `M_Plaster` 上加 decal）、破损墙段（城墙 `wall_seg` 加一个 `_Broken` 变体）。
3. 地面贴图：石板路、泥地的 `_D` 贴图替换纯色（材质名不变，团结里换贴图即可）。
4. 祖祠内景（藏谱/寻谱/修谱三态）属于下一阶段「内景」。
