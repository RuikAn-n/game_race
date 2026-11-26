# 明代 1560 民用建筑（`KIT_Ming_House`）

依据：[`入谱_当前建模缺口清单.md`](入谱_当前建模缺口清单.md) 3.2 `KIT_Ming_House`，以及「明代建筑不要继续用 ROC 模型占位」。
全部是程序化白模（低模、纯色语义材质），生成脚本 `Tools/blender/rupu_ming_house.py`，由 `build_yongchang.py` 统一导出 FBX 到 `Project_rupu/Assets/Art/Buildings/BLD_MING_*/`。

![12 个明代民用建筑（明代年代色）](images/ming/house_overview_34.jpg)

## 对照表

每个 kind 的占地尺寸、朝向（正面朝 Blender -Y，导入团结后朝 +Z）、原点（占地中心地面）、门的位置、台基高度都和同 kind 的 `BLD_ROC_*` 一致，布局 `yongchang_layout.json` 不用改，年代切换只改 `era_kits.json`。

| kind（占地） | 资产 | 状态 | 造型 | 三角面 |
|---|---|---|---|---:|
| house_s（10×7） | `BLD_MING_House_S_A` | ✅ | 三开间悬山平房，前檐廊四根檐柱，木板前檐、直棂窗，山面穿斗木构外露；门 x=0，台基 0.35 | 924 |
| house_s | `BLD_MING_House_S_B` | ✅ | 小院平房：前院墙 + 瓦顶小门楼（院门 x=-1.8），后屋硬山、两山马头墙，石勒脚；台基 0.3 | 1156 |
| house_l（12×8） | `BLD_MING_House_L_A` | ✅ | 两层木楼：底层白墙木前檐 + 腰檐，二层木板壁 + 一长排槛窗，悬山顶；门 x=0 | 1678 |
| house_l | `BLD_MING_House_L_B` | ✅ | 曲尺形宅：后排两层硬山楼（马头墙）+ 右前单层厢屋（山面朝街，门 x=2.2）+ 左前小院（院门 x=-2.2） | 1902 |
| shop（6×10） | `BLD_MING_Shop_A` | ✅ | 两层店屋：底层全开间铺面（排门板半卸、柜台），二层出挑木楼，悬山顶，挑出布幌 | 994 |
| shop | `BLD_MING_Shop_B` | ✅ | 一层半店屋：山面朝街的悬山顶（屋脊沿进深），前出披檐两柱，排门板 + 中门，山尖阁楼窗 | 658 |
| shop_west（8×12） | `BLD_MING_ShopWest` | ✅ | 明代没有西式店面，做成两层木构客栈/酒楼：前檐廊 + 一排槅扇门，三面腰檐，二层槛窗 + 栏杆，歇山顶（山花朝街），门前酒旗 | 2224 |
| courtyard（20×18） | `BLD_MING_Courtyard` | ✅ | 三合院：正屋五开间（前廊、硬山高出屋面）、东西厢悬山（门窗朝院）、前院墙瓦顶门楼（门 x=0）、院中水井和水缸 | 3048 |
| hall_small（14×20） | `BLD_MING_HallSmall` | ✅ | 一进祠第：门厅硬山马头墙、红漆大门、抱鼓石、门罩、匾；院内甬道和铜香炉；正厅歇山、红柱前廊、槅扇门 | 2208 |
| granary（20×12） | `BLD_MING_Granary` | ✅ | 官仓/社仓：0.9 m 高石台基带防潮孔，石勒脚白墙、外露木柱，两座板门带门罩和坡道（x=±5），方格高窗，屋脊上一条通长气楼 | 1692 |
| dock（20×18） | `BLD_MING_Dock` | ✅ | 埠头：条石驳岸平台（y≥-4，顶面 0.3）、左前下水石阶、右前木栈桥伸到 y=-9、瓦顶货棚（三面板壁）、系缆石、麻包、木箱、陶缸、纸灯笼杆；正面(-Y)朝海 | 998 |
| salt_shed（12×8） | `BLD_MING_SaltShed` | ✅ | 煎盐灶舍：茅草四坡敞棚、后半截土墙，砖灶 + 盘铁（铁盘）+ 盐堆 + 烟囱，卤池、卤缸、柴垛 | 508 |

A/B 一眼可分：S_A 悬山前廊 vs S_B 院墙门楼 + 马头墙；L_A 两层腰檐整体一坡 vs L_B 曲尺形（俯视是 L 形屋顶）；Shop_A 屋脊横向、二层出挑 vs Shop_B 屋脊纵向、山面朝街。

![俯视（军议 / 战中指挥镜头）](images/ming/house_overview_top.jpg)

## 和民国版的区别

- 没有玻璃窗、招牌、电线、西式立面、铁皮屋顶、路灯；窗都是木格窗（直棂/方格），门是对开板门或槅扇。
- 墙面以白灰墙为主，下部是石勒脚或墙裙；木构（柱、穿枋）外露；屋顶分悬山、硬山（马头墙）、歇山三种。
- 码头从「木栈台 + 铁皮仓棚」改成「条石驳岸 + 下水石阶 + 小木栈桥 + 瓦棚」；盐舍从「两坡茅棚 + 铁锅」改成「四坡茅棚 + 盘铁灶」。

## 材质

只用 `Data/map/era_materials.json` 里已有的语义材质名，没有新材质：
`M_Roof_Tile` `M_Roof_Ridge` `M_Plaster` `M_Plaster_Lower` `M_Wood` `M_Wood_Dark` `M_Window` `M_Stone_Base` `M_Road_Stone` `M_Red_Lacquer` `M_Plaque` `M_Bronze` `M_Flag` `M_Cloth_Red` `M_Bank_Stone` `M_Water` `M_Brick_Red` `M_Sandbag`（麻包）`M_Paper`（灯笼）`M_Thatch` `M_Salt` `M_Metal`（盘铁）。
团结里按年代材质库自动换成 ming 色。上面的预览图已经按 `era_materials.json` 的 ming 色渲染。

## 子物体 / 挂点约定

| 名称 | 所在资产 | 说明 |
|---|---|---|
| `BLD_MING_*`（主网格） | 全部 | 整栋一个网格，和 ROC 一样整体加 MeshCollider（不放 `COL_*`） |
| `NOCOL_Banner` | Shop_A | 布幌（横杆 + 垂布），不加碰撞，可以挂风动 |
| `NOCOL_WineFlag` | ShopWest | 门前酒旗杆和旗，不加碰撞 |
| `ANCHOR_Door` / `ANCHOR_Door_2` | 民居、店、合院、祠、仓 | 门外站位（地面高度），给 NPC 进出、开门互动用 |
| `ANCHOR_Counter` | Shop_A | 柜台前，摊主或买卖互动站位 |
| `ANCHOR_Yard` / `ANCHOR_MainDoor` | Courtyard | 院中、正屋门前（宅院抉择可用） |
| `ANCHOR_Censer` / `ANCHOR_Hall` | HallSmall | 香炉前、正厅前廊 |
| `ANCHOR_Jetty` / `ANCHOR_Steps` | Dock | 栈桥头（靠船）、下水石阶底 |
| `ANCHOR_Stove` | SaltShed | 灶口前，煮盐小游戏站位 |
| `FX_Incense` | HallSmall | 香炉烟 |
| `FX_Lantern` | Dock | 灯笼光点 |
| `FX_Fire` / `FX_Smoke` / `FX_Steam` | SaltShed | 灶火、烟囱烟、盐盘蒸汽 |

## 给 A 的接入说明

1. 在 `Data/map/era_kits.json` 填 ming 字段（建议如下），然后重新生成永昌堡场景，明代就不再用 ROC 模型占位：

```json
{ "kind": "house_s",    "ming": ["BLD_MING_House_S_A", "BLD_MING_House_S_B"] },
{ "kind": "house_l",    "ming": ["BLD_MING_House_L_A", "BLD_MING_House_L_B"] },
{ "kind": "shop",       "ming": ["BLD_MING_Shop_A", "BLD_MING_Shop_B"] },
{ "kind": "shop_west",  "ming": ["BLD_MING_ShopWest"] },
{ "kind": "courtyard",  "ming": ["BLD_MING_Courtyard"] },
{ "kind": "hall_small", "ming": ["BLD_MING_HallSmall"] },
{ "kind": "granary",    "ming": ["BLD_MING_Granary"] },
{ "kind": "dock",       "ming": ["BLD_MING_Dock"] },
{ "kind": "salt_shed",  "ming": ["BLD_MING_SaltShed"] }
```

2. 碰撞走 `RupuMapBuilder` 的现有规则：没有 `COL_*`，所以所有非 `NOCOL_*` 网格加 MeshCollider（和 ROC 相同）。
3. 码头：可走面是驳岸平台（y≥-4，顶 0.3 m）和右前栈桥（x 1–5），平台前沿和石阶之间是水面；民国版整片都是木台，明代版前沿留了水。玩家若需要在码头前沿走动，注意别让导航把石阶/栈桥之外的区域当成地面。
4. 外形包围盒比 ROC 略大的地方（都是檐口或旗杆，不影响布局）：ShopWest 的歇山檐和酒旗在 x ±4.5、后檐到 y=6.5（ROC 是 ±4.3 / 6.0）；HallSmall 门前抱鼓石到 y=-10.6、正厅翼角到 x ±7.5。
5. 屋顶从俯视看：悬山/硬山都有明显的正脊和脊端起翘，歇山（ShopWest、HallSmall 正厅）有上下两段，曲尺宅俯视是 L 形，三合院和祠第中间露出院子。

## 重新生成

```bash
cd /Users/anruikang/Downloads/game_race
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/build_yongchang.py -- \
  --only BLD_MING_House_S_A,BLD_MING_House_S_B,BLD_MING_House_L_A,BLD_MING_House_L_B,BLD_MING_Shop_A,BLD_MING_Shop_B,BLD_MING_ShopWest,BLD_MING_Courtyard,BLD_MING_HallSmall,BLD_MING_Granary,BLD_MING_Dock,BLD_MING_SaltShed \
  --force --preview /tmp/ming_house_preview
```

（已存在的 .blend 默认跳过，`--force` 才会覆盖；手改过的 .blend 不要带 `--force`。）

## 细节图

| | |
|---|---|
| ![曲尺宅](images/ming/house_House_L_B.jpg) | ![客栈](images/ming/house_ShopWest.jpg) |
| ![三合院](images/ming/house_Courtyard.jpg) | ![一进祠第](images/ming/house_HallSmall.jpg) |

## 还没做的

- 贴图（瓦垄、木纹、灰墙斑驳、纸纹）：现在是纯色语义材质，等风格贴图统一做。
- 室内：门窗都是贴面，进不去。需要进屋的剧情（王叔杲宅）由 `ENV_WangHouse` 另做。
- 院墙、门楼没有单独拆成可拼接模块；明代街巷若需要额外的院墙段，可以从 `wall_x` / `wall_y` 辅助函数再出一个 `BLD_MING_YardWall`。
- 破损态（倭寇焚掠后的残屋）没做。
