# 第二幕 · 明代建筑 LOD + 城市 P1 部件

对应 [第二幕_策划对照与建模缺口.md](第二幕_策划对照与建模缺口.md) 中 §5 P0 的最后一行「LOD」、§5 P1（道路、市场、城墙外）以及 §9 第一步第 1 条「自动检查建筑包围盒」。

| 部分 | 文件 |
|---|---|
| LOD 生成（导出管线） | `Tools/blender/rupu_pipeline.py` |
| LOD 分组（团结导入） | `Tools/unity_seed/Assets/_Rupu/Editor/RupuArtImporter.cs`，已用 `Tools/mac/seed_unity_project.sh` 同步到工程 |
| 城市部件生成器 | `Tools/blender/rupu_a2_city.py`（`build_yongchang.py` 会自动导入） |
| 占地包围盒 | `Tools/map/export_footprints.py` 生成 `Data/map/ming_footprints.json` |

---

## 1 LOD（BLD_MING_* 自动三级）

### 怎么生成

`rupu_pipeline.do_export()` 默认对 **Buildings 分类中以 `BLD_MING_` 开头的资产**生成 LOD。生成流程如下：

1. 先做规格检查。这时场景里只有原网格，所以**三角面只算 LOD0**；`validate()` 也会跳过名字带 `_LOD1+` 的物体。
2. 在可见网格中挑出要做 LOD 的对象。`COL_*`、`NOCOL_*`、`ANCHOR_*`、`FX_*`、空物体、骨骼网格，以及少于 **200** 三角面的小件（门闩、绳子、屋顶小块等）都不参与。对每个入选网格各复制两份：
   - **LOD1**（目标约 50%）：先删掉孤立的小件，标准是最长边小于 0.30 m，或第二长边小于 0.06 m，例如门钉、窗棂、椽头。如果面数仍超标，再按包围盒最大面面积从小到大删件，只删面积小于 0.6 m² 的件。
   - **LOD2**（目标约 20%）：删件标准放宽到 0.80 m / 0.15 m / 3 m²，栏杆、窗框、檐柱都会被删掉。
   - 删完后面数仍高出目标 25% 以上时，才用 Decimate（Collapse）补足。白模是用盒子拼的，所以优先整件删除，这样外形最干净。
3. 结构：原网格改名为 `<原名>_LOD0`，下面挂两个子物体 `NOCOL_<原名>_LOD1` 和 `NOCOL_<原名>_LOD2`，局部变换为 0。
4. 导出 FBX，然后在 `finally` 中**删掉 LOD 物体并把名字改回原名**。`.blend` 不保存 LOD。`build_yongchang.py` 在导出前就已存盘，之后也不再保存。

开关：命令行加 `--no-lod` 关闭，加 `--lod` 对任意资产强制开启。Python 调用时用 `do_export(lod=True/False)`。参数位于 `rupu_pipeline.py` 顶部的 `LOD_LEVELS` 和 `LOD_MIN_TRIS`。

> 为什么 LOD1/2 挂在 LOD0 **下面**，而不是按团结惯例做成同级：一是门扇、闸门、屋顶这类会被脚本移动或隐藏的部件，远处的 LOD 能跟着一起动、一起隐藏；二是 `NOCOL_` 前缀能让 `RupuMapBuilder.SetupColliders` 不给 LOD1/2 加 MeshCollider，否则一栋楼会叠三层碰撞。`_LODn` 后缀仍然沿用团结的命名约定。

### 团结里怎么分组

`RupuArtImporter.OnPostprocessModel` 每次导入 `Assets/Art/` 下的模型时都会做以下处理：

- 找出所有名字以 `_LOD<n>` 结尾的渲染器。LOD1+ 的父物体就是 LOD0：FBX 只有一个根节点时，团结会把它并进模型根并改用文件名，所以按父子关系识别 LOD0，不依赖名字。
- 删除模型里所有已有的 LODGroup（包括团结按命名约定自动建的），然后在**模型根**上新建一个 LODGroup。
- LOD0 物体去掉 `_LOD0` 后缀，物体名与做 LOD 之前一致，按名字找物体的脚本不受影响。
- 切换屏占比为 `LodScreenHeights = {0.30, 0.10, 0}`，最后一级为 0，表示**永不剔除**（俯视指挥时要能看到全城）。`fadeMode = None`。想调整距离，改这个数组后重新导入即可。
- 不在任何一级中的网格始终显示，包括小于 200 面的小件、`NOCOL_` 旗面以及会被删掉渲染器的 `COL_*`。

**给 A 的提醒**：隐藏建筑请用 `gameObject.SetActive(false)`，或者遍历 `GetComponentsInChildren<Renderer>()`。只关 LOD0 的 `renderer.enabled` 的话，远处仍会显示 LOD1/2。

### 验证结果

已用 `--force` 重导 13 个明代建筑，全部 [OK]，三角面在规格内。之后在 Blender 中重新导入 FBX 检查结构，例如 `BLD_MING_Courtyard.fbx`：

```text
ANCHOR_Door / ANCHOR_MainDoor / ANCHOR_Yard     EMPTY
BLD_MING_Courtyard_LOD0                         MESH  3048
  NOCOL_BLD_MING_Courtyard_LOD1  (parent=LOD0)  MESH  1896
  NOCOL_BLD_MING_Courtyard_LOD2  (parent=LOD0)  MESH   604
```

重导后的 .blend 全部扫了一遍，没有残留任何 `_LOD` 物体。

| 资产 | LOD0 / LOD1 / LOD2 三角面 |
|---|---|
| BLD_MING_House_S_A | 924 / 576 / 180 |
| BLD_MING_House_S_B | 1156 / 578 / 288 |
| BLD_MING_House_L_A | 1678 / 922 / 310 |
| BLD_MING_House_L_B | 1902 / 950 / 380 |
| BLD_MING_Shop_A | 958 / 478 / 202 |
| BLD_MING_Shop_B | 658 / 328 / 142 |
| BLD_MING_ShopWest | 2156 / 1076 / 428 |
| BLD_MING_Courtyard | 3048 / 1896 / 608 |
| BLD_MING_HallSmall | 2208 / 1312 / 440 |
| BLD_MING_Granary | 1692 / 1044 / 336 |
| BLD_MING_Dock | 998 / 502 / 198 |
| BLD_MING_SaltShed | 508 / 254 / 104 |
| BLD_MING_Temple | 2748 / 1400 / 648 |

`BLD_MING_GateTower`、`_WaterGate_Sluice`、`_AncestralHall`、`_HuanhaiLou` 正在由其他人改（贴字、开闭部件），这次没有重导。主代理最后统一重导时会自动带上 LOD，不需要额外操作。

左起依次为 LOD0、LOD1、LOD2：

![合院 LOD](images/act2/city_lod_courtyard.jpg)
![汤和庙 LOD](images/act2/city_lod_temple.jpg)
![店屋 LOD](images/act2/city_lod_shop.jpg)

---

## 2 城市 P1 部件（`rupu_a2_city.py`）

下文方位一律用**团结**坐标：+Z 是正面，+X 是东或右（Blender 中 −Y 为正面，+X 对应团结 −X）。

### 2.1 石板路：直段 / 十字 / 丁字 / 转角

![路面件](images/act2/city_roads.jpg)

| 资产 | 尺寸 | 通路边 | 用于 |
|---|---|---|---|
| `ENV_MING_Road_Straight` / `_L4` | 6×6 / 4×4 | N、S | 主街、横街（6 m）/ 巷道（4 m） |
| `ENV_MING_Road_Cross` / `_L4` | 同上 | N、S、E、W | 十字路口 |
| `ENV_MING_Road_Tee` / `_L4` | 同上 | N、S、E | 丁字路口（支路向东；转 90° 或 180° 可得其他方向） |
| `ENV_MING_Road_Corner` / `_L4` | 同上 | S、E | 街角（从南来往东转；转 90° 可得其他三个角） |

- 宽度与 `gen_layout.py` 一致：主街、横街宽 6 m，巷道宽 4 m（西、东直巷 3.5 m 也用 `_L4`，两侧各多出 0.25 m，正好落在建筑退线 0.4 m 以内）。宽度**包含两侧的沟**。6 m 宽的路是沟沿石 0.25 + 明沟 0.4 + 石板 4.7，4 m 宽的路是 0.2 + 0.3 + 2.8。
- 封闭的边（临街房屋一侧）有一整条沟沿石和明沟。两条通路边相夹的角上，两条路的沟在角上汇合。每条长沟的中段盖一块石盖板（局部盖板）。
- 路面为横向条石错缝铺设，行宽 0.6 m，石缝中露出深色垫层。**顶面高 z = 0.12**，沟沿石高 0.14，沟底 0.02。地面 `ENV_Yongchang_Ground` 是平的 z = 0，路面件直接盖在上面。
- `COL_Walk` 是整块平板，顶面 0.12，所以人物走过沟不会被绊。
- 原点在件中心的地面上。直段沿 Z 方向排，步长 6 m（巷道 4 m）。按布局摆放：例如 `RD_MainN` 的中线是 x = 4，就在 x = 4、z 每 6 m 放一块 Straight；在与 `RD_CrossW`（z = 12）相交的地方放 Cross。

### 2.2 排水沟单件、跨沟石板桥、城墙外连接

![排水沟与城外](images/act2/city_drain_outer.jpg)

| 资产 | 说明 |
|---|---|
| `PROP_MING_Drain_Straight` | 独立明沟，长 2 m（沿 Z），内宽 0.5，沟沿高 0.36，条石沟墙加压顶，带 `NOCOL_DrainWater` |
| `PROP_MING_Drain_Covered` | 同一段沟，上面盖三块石盖板，顶面 0.46 |
| `PROP_MING_Drain_Outfall` | 沟口跌水：沟从 −Z 来，在 +Z 端挑出一块跌水石，水落入小石池。带 `NOCOL_DrainWater` / `PoolWater` / `Fall`，特效挂点 `FX_Splash` |
| `BLD_MING_SlabBridge` | 跨沟石板桥：三块条石跨过 1.2 m 宽的沟，桥面 0.47，两端有踏步，路沿 Z。已有的 `BLD_Bridge_*` 是跨河用的，3 m 起跨、带栏板，没有跨沟的小桥，所以不算重复 |
| `ENV_MING_DirtRoad_Straight` | 城外土路，宽 5 m（与 `RD_OutW` / `RD_OutS` 一致）、长 10 m，沿 Z 方向，原点在中心。顶面 0.05，带车辙、路边草和碎石，有 `COL_Walk` |
| `ENV_MING_DirtRoad_Bend` | 90° 弯道：入口在原点、朝 +Z，向右转，出口中心在 (8, 0, 8)、朝 +X。左转只需把件转过来从出口进入 |
| `ENV_MING_DirtRoad_Ridge` | 田埂：顶宽 0.6、底宽 1.3、高 0.3、长 10 m，顶上有踩出的土路，两侧长草 |
| `PROP_MING_Culvert` | 涵洞：土路（沿 Z、宽 5 m）拱起 0.8 m 跨过一条沿 X 的沟，两侧是带券洞的石墙加压顶和八字翼墙，两头坡道落回 0.05。总长 7.6 m，带 `NOCOL_DitchWater` |
| `PROP_MING_MileStone` | 路边界石，高 1.0 m。正面有一块 `M_Plaque` 刻字面（空白 UV，留给贴字） |

建议的接法：王宅（西墙外，x = −58）到镇山门（`RD_OutW`，z = 12）之间用 Straight + Bend 接成土路，过护城河外的沟时用 Culvert，路口立一块 MileStone。盐场（城内东北）到环海门、码头路一段用 `ENV_MING_Road_*` 接横街。田间小路用 Ridge。

### 2.3 市场

![市场货物](images/act2/city_market_goods.jpg)
![市场一排](images/act2/city_market_row.jpg)

| 资产 | 内容 |
|---|---|
| `PROP_MING_MarketGoods_Cloth` | 条凳上三层布卷（靛蓝、本色、褐、赭红），竹架上挂一匹展开的布，地上竖着两卷 |
| `PROP_MING_MarketGoods_Pottery` | 草席上一口大缸（盛水）、五只坛罐、一摞碗 |
| `PROP_MING_MarketGoods_Bamboo` | 一摞簸箕加一只斜靠的、三层蒸笼、竹凳、两把扫帚、带提梁的竹篮 |
| `PROP_MING_MarketGoods_Fish` | 两只细颈鱼篓、一只木盆（盆里有水和鱼）、鱼架上一只摊着鱼的竹匾 |
| `PROP_MING_MarketGoods_Rice` | 麻袋垛（三只躺、两只立）、敞口米袋（堆出米尖）、木斗 |
| `PROP_MING_MarketGoods_Veg` | 扁担挑两只筐（青菜、萝卜），地上有一捆萝卜、两只南瓜、几颗白菜 |
| `ENV_MING_MarketRow` | 一排三个摊位，12 × 3.6 m，正面（+Z）临街，分别是布匹摊、陶器摊、鱼摊，摊位之间放米袋、菜担、竹器。棚面单独成 `NOCOL_Awnings`；站位挂点为 `ANCHOR_Vendor_1..3`、`ANCHOR_Buyer_1..3`，俯视机位为 `ANCHOR_cam_top` |

思路沿用 `rupu_act1.py` 的街市，改成明代暖褐色板。货物用新的材质 `M_MKM_*`，颜色写在 Base Color 里。这些材质不在 `era_materials.json` 中，团结会保留 FBX 自带的颜色。木构部分沿用 `M_Wood` / `M_Wood_Dark`，会按年代自动换色。

所有资产都通过了规格检查：Environments 最大 3.9k / 40k，Props 最大 0.8k / 3k，Buildings 0.1k / 20k。生成命令：

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/build_yongchang.py -- \
  --only ENV_MING_Road_Straight,ENV_MING_Road_Cross,...  --force --preview <目录>
```

---

## 3 占地包围盒 `Data/map/ming_footprints.json`

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/map/export_footprints.py -- [--out 路径] [--with-roc]
```

只读取 .blend，不修改任何文件。扫描范围是 `BLD_MING_*`、`ENV_MING_*`，以及 `ENV_WangHouse`、`ENV_SaltField`、`ENV_SaltFurnace`、`ENV_NorthGate_Build`。加 `--with-roc` 时还会扫描 `BLD_ROC_*`。改了建筑后重跑一次即可。

格式如下。坐标是**团结局部坐标**，即模型旋转为 0 时 x 指东、y 指上、z 指北（正面），单位 m：

```json
{
 "base_height": 1.0, "plot_tolerance": 0.35,
 "assets": {
  "BLD_MING_House_S_A": {
   "category": "Buildings",
   "base": {"min": [-5.15, -0.3, -3.65], "max": [5.15, 0.5, 3.97], "size": [10.3, 0.8, 7.62]},
   "full": {"min": [-5.5, -0.3, -4.15], "max": [5.5, 6.12, 4.15], "size": [11.0, 6.42, 8.3]},
   "col": null,
   "anchors": {"ANCHOR_Door": [0.0, 0.0, 0.0]},
   "kinds": ["house_s"], "plot": [10, 7],
   "overhang": [0.15, 0.15, 0.15, 0.47], "fits": false
  }
 }
}
```

- `base`：离地 1 m 以下的可见网格（不含 `NOCOL_`）的包围盒，也就是台基、墙脚、台阶。**判断建筑之间是否重叠时用它。**
- `full`：包含屋檐出挑、旗杆的全包围盒，用来检查屋檐互相穿插。
- `col`：`COL_*` 碰撞体的包围盒。没有 `COL_*` 时为 `null`，团结里整个网格都参与碰撞，范围等同 `full`。
- `kinds` / `plot`：`era_kits.json` 中用到这个资产的 kind，以及布局里该 kind 的占地 w×d。
- `overhang`：`base` 超出 plot 的距离，按 [西, 东, 南（背面）, 北（正面）] 排列，正数表示伸出。`fits` 的条件是 `max(overhang) <= 0.35`。

A 在场景里的用法：对每个摆放的物体，按 `position` 和 `rotationY` 把 `base` 的四个角变换到世界坐标，再两两做 OBB 或 AABB 相交检查；也可以按 `overhang` 检查与道路矩形（`yongchang_layout.json` 的 `roads`）的退线。

**当前结果**：伸出基本都在**正面**，来自台阶和月台，两侧普遍只有 0.15 m 的台基余量。

| 资产 | 正面伸出 |
|---|---|
| BLD_MING_AncestralHall | 1.8 m（门前月台，前面是祖祠前庭广场，没有影响） |
| BLD_MING_Granary | 1.8 m |
| BLD_MING_Temple | 0.8 m |
| BLD_MING_HallSmall | 0.6 m |
| BLD_MING_House_S_A / S_B / L_A | 0.47 m（比布局的临街退线 0.4 m 多出 7 cm，伸进路面边） |

Granary 和 Temple 前面如果没有留空地，需要在布局里多退一点。

---

## 4 没做的和原因

- **没有把路面件自动铺进场景**：这需要改 `gen_layout.py` 或 `RupuMapBuilder.cs`，不在我负责的文件范围内。建议 A 或主代理按 2.1 节的规则，用布局的 `roads` 矩形逐格摆放：相交处放 Cross / Tee，其余放 Straight。
- **不同宽度的路口**（4 m 巷道接 6 m 主街）没有专门的过渡件。直接把 `_L4` 直段接到 6 m Tee 的开口边上即可，开口边是满铺石板，只是巷道的沟在接口处断开。
- **市场人群、叫卖声、第二幕环境音**不属于建模，没有做。
- **界石刻字**：`M_Plaque` 面已经留好，等贴字流程（`rupu_a2_text.py`）来做。
- **四座正在被修改的明代建筑**（GateTower / WaterGate_Sluice / AncestralHall / HuanhaiLou）这次没有重导，原因见第 1 节。
- **没有在团结里实测 LODGroup**：按要求没有运行团结。导入逻辑已对照 FBX 的实际结构写好，打开工程后对应 FBX 会自动重新导入。验收时选一栋明代建筑，确认根物体上有 LODGroup（3 级，最后一级为 0），并且拉远镜头时会切换。
