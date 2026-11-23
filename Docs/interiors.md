# 室内场景白模：祠堂 + 环海楼

依据：`入谱_第一幕_人物文本.md`、`入谱_第二幕_筑堡_策划案_v1.md`。程序化生成，脚本 `Tools/blender/build_interiors.py`，一键 `Tools/mac/build_interiors.sh`（`--force` 会覆盖手改，`--preview DIR` 出预览图）。预览图在 `Docs/images/interiors/`。

| 资产 | 三角面 | 占地 | 对应外观 |
|---|---|---|---|
| `BLD_INT_AncestralHall` | 13.7k（含碰撞网格） | 20 × 36 | `BLD_ROC_AncestralHall` |
| `BLD_INT_HuanhaiLou` | 12.3k（含碰撞网格） | 20 × 8.8，两层 | `BLD_ROC_HuanhaiLou` |

## 通用约定

- 原点在地面中心，正面朝 Blender -Y（团结 +Z），1 unit = 1 m。
- 同一套几何给 1560 / 1941，只换材质、贴花、道具（积灰、烧痕、断角）。新增语义材质 `M_Floor_Brick / M_Floor_Wood / M_Bronze / M_Cloth_Red / M_Ceiling` 已写入 `Data/map/era_materials.json`。
- **屋顶可整体隐藏**：`ROOF_*` 俯视时（军议、战中指挥、战后整备）整体 SetActive(false)。环海楼再多一层：隐藏 `INT_Floor2`、`INT_Upper*` 可以俯视底层。
- `COL_*` 只做碰撞（团结导入器会去掉渲染）；`ANCHOR_*` 是空物体，团结里按名字找位置。
- 可交互 / 会变化的物件单独成物体，不并进外壳。

## 祠堂 `BLD_INT_AncestralHall`

空间顺序（−Y → +Y）：门厅 → 内院（廊庑、鼎炉、太平缸）→ 月台三级台阶 → 正厅（地面 +0.9）→ 后天井（井）→ 后堂（谱库，地面 +0.6）。

| 物体 | 内容 | 出处 |
|---|---|---|
| `INT_Tablets` | 三层神龛，约 50 块牌位；顶层居中两块大牌位 | 族老：「上面供奉的两位是王沛公、王叔杲公，你父亲在下面这一排」 |
| `INT_Tablet_WangShiqing` | 下排的王世清牌位，单独成物体，字面涂黑 | 谱上父亲名字被墨涂黑；1941 / 1560 可换材质 |
| `INT_Altar` | 供桌（香炉、烛台、供品、谱匣）、香案、三个蒲团 | 王砚上香；残谱放供桌拼合 |
| `INT_Sandtable_Stand` | 沙盘台座 1.2 × 0.8（供桌左侧），沙盘本体另做 | 第二幕 §4.2 `anchor_sandtable` |
| `INT_Roster_Table` | 议事长桌 + 长凳 + 名录纸 + 名牌 | 拍 1 王叔杲拍田契；拍 7 记名 |
| `INT_Stele` | 族约碑，三道刻字槽 | 第二幕 §6 三条上碑 |
| `INT_Well` | 后天井的井 | 藏谱派：「藏进夹墙、井里、匾后」 |
| `INT_Courtyard` | 鼎炉、太平缸、廊下灯笼 | 内院族亲对话、军官进院 |
| `INT_Furniture` | 战鼓（春祭）、门厅条凳、谱柜三组、修谱长案 | 春祭被打断、后堂谱库 |
| `INT_Shell` | 地面、墙、柱、梁、大匾 | |
| `ROOF_Gate / Corridor / Main / Rear` | 四块屋顶，各自可隐藏 | |

门厅正中不放影壁，留给「日本军官和两名士兵走进祠堂，站定后才开口」。

锚点：`ANCHOR_enter_street / courtyard_kin / elder_lead / officer / soldier_L / soldier_R / pray / altar / pages_join / tablet_pei / tablet_gao / tablet_father / sandtable / roster_table / stele / drum / wangbingzhi / faction_jiao / faction_shao / faction_cang / hide_plaque / hide_wall / hide_well / pu_cabinet / cam_hall / cam_top`。三派站位在正厅供桌前，位置是示意，A 可直接挪。

## 环海楼 `BLD_INT_HuanhaiLou`

东门城楼，底层 = 中间城门洞 + 两侧房间，上层 = 军议厅，前檐出平座。

底层：

- 门洞（宽 4.8）：前后拱门，双扇城门敞开贴在侧壁（`INT_Gate`），千斤闸提起，只露上半格栅。
- 西侧值房：兵器架、三张铺位、值守桌、灶、水缸。
- 东侧楼梯间：21 级木楼梯通二层，沙袋、火罐架、水缸、水桶。
- 两端墙各有一扇走道门，接城墙走道。外墙有射孔。

上层（军议厅）：

- 长桌 + 舆图 + 红蓝棋子（红 = 倭，蓝 = 我，示意）、12 张凳，墙上挂舆图，对应第二幕「军议」「战中指挥」。
- 战鼓、兵器架（挂着 2.6 m 的长枪，王沛的枪）、铜钟（警钟）、弹药箱和炮弹、值事案。
- `INT_Flagpole`：旗座 + 旗杆 + 旗，单独成物体，枢轴在旗座中心，1941 脚本让它倒下（「旗杆斜倒在石阶上，旗面沾旧血」）。倒下后「石阶」要用环海楼外的台阶，这个资产不含外部台阶。
- 前檐平座有栏杆，`ANCHOR_cannon_post` 是东台火炮位。

分层隐藏：`ROOF_Main`（上檐）→ `INT_Upper` + `INT_Floor2`（上层）→ 剩底层；`ROOF_Eaves` 是腰檐。

锚点：`ANCHOR_gate_out / gate_in / walk_W / walk_E / stair_bottom / stair_top / guard_post / spear_rack / muster_table / wang_pei / wang_shugao / wang_yan / balcony / cannon_post / bell / flagpole / look_sea / cam_top_upper / cam_top_ground`。

## 还没做

- 团结里的场景（光照、门的开合、顶视镜头切换）和碰撞整理。资产只到 FBX。
- 明代 `BLD_MING_INT_*`：几何不动，换材质即可；牌位、沙盘、家具的明代版需要另做。
- 1941 的积灰、香灰、烧痕贴花，沙盘的三套皮肤。
- 贴图：目前全是纯色材质，UV 是 2 m 盒式投影。
