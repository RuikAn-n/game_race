# 第二幕：世界里的城墙、工地、水门、城门、王宅、盐场、殉难现场

依据：[`第二幕_策划对照与建模缺口.md`](第二幕_策划对照与建模缺口.md) §5 P0（明代城墙、水门、城门、王宅、盐场、工地 overlay）、§9 第四步（墙线 → 世界城墙段出现、水门开闭、殉难/合龙）和第五步 2（工地脚手架 / 石料 / 灰浆 / 夯土），以及 [`入谱_第二幕_筑堡_策划案_v1.md`](入谱_第二幕_筑堡_策划案_v1.md) 拍 3、拍 5、拍 6、§5、§8、§9。

都是程序化白模：

- 新资产由 `Tools/blender/rupu_a2_site.py` 生成。
- 改过的明代资产（城门、水门闸、王宅、盐灶、盐具）在 `Tools/blender/rupu_ming_civic.py` 里。

两个文件都由 `build_yongchang.py` 驱动导出。

## 总表

| 资产 | 分类 | 三角面 | 状态 |
|---|---|---:|---|
| `BLD_Wall_Seg_Build` | Buildings | 1.5k | 新 |
| `BLD_Wall_Gap` | Buildings | 0.7k | 新 |
| `ENV_A2_WorkSite_Wall` | Environments | 2.5k | 新 |
| `ENV_A2_WorkSite_Yard` | Environments | 3.9k | 新 |
| `ENV_A2_Aftermath_NorthGate` | Environments | 5.4k | 新 |
| `BLD_MING_GateTower` | Buildings | 3.7k | 改：加城门门扇、门闩、COL |
| `BLD_MING_WaterGate_Sluice` | Buildings | 1.6k | 改：开 / 闭两组 |
| `ENV_WangHouse` | Environments | 6.8k | 改：拆梁两态、锚点 |
| `ENV_SaltFurnace` | Environments | 2.3k | 改：火 / 卤水 / 盐各三态 |
| `PROP_SaltSet` | Props | 1.5k | 改：加起盐产出 |

全部 `[OK]`，规格在限内（Buildings ≤20k，Environments ≤40k，Props ≤3k）。明代建筑的自动 LOD 由 `rupu_pipeline.py` 在导出时加，这里的面数只算 LOD0。

**坐标换算**：Blender 的 −Y（城外 / 正面）进团结后是 +Z，Blender 的 +Y（城内）是 −Z，Blender 的 Z 是团结的 Y。

凡是要转动的部件，都另放了一个带旋转的参考空物体 `ANCHOR_*_Open`。脚本把 `localRotation` 插值到它的 `localRotation` 就行，不用自己换算轴向。

## 1. 城墙生长与合龙

### `BLD_Wall_Seg_Build`：分阶段墙段

![四个阶段（从城内看）：Stage_0 → Stage_3](images/act2/site_wall_stages.jpg)

占地、原点、剖面都和 `BLD_Wall_Seg` 一样：8 m（x −4..4），原点在墙中线的地面，墙高 7.0，走道面 7.08，外侧收分，城外在 −Y。根是空物体 `BLD_Wall_Seg_Build`，下面四个阶段**互斥**，一次只开一个：

| 子物体 | 内容 |
|---|---|
| `Stage_0` | 基槽和放线：踩实的槽底，头一层毛石；两侧是弃土埂；内外两道红头木桩，桩间拉麻线；两端有龙门板，中间一根中线桩 |
| `Stage_1` | 半高墙加模板：条石基础到 1.5，外包石半砌到 2.5，夯土芯到 3.0。顶上架着正在夯的一版板筑模板（3.0..3.6），两根夯杵 |
| `Stage_2` | 墙身砌好但没有垛：新石墙身到 7.0，有走道铺面和压檐石；垛墙只砌了两块墙根；墙面有灰缝线 |
| `Stage_3` | 完成态，和 `BLD_Wall_Seg` 几何、材质完全一样，换成正式墙段时不会跳 |

「墙线 → 世界城墙段出现」的做法：

1. 沙盘墙线定下来以后，沿墙线摆这种墙段（位置和 `BLD_Wall_Seg` 相同）。
2. 按工期依次切换 Stage_0 → 3。每次切换让新的 Stage 从 −Z 升起，或者把 Y 缩放从 0 拉到 1，用时 0.6 s。
3. 同时在 `FX_WallRise` / `FX_RamDust` 放特效。

锚点：`ANCHOR_Ram_1/2`（Stage_1 顶上夯土位）、`ANCHOR_Stake_Out`（城外放线位）、`ANCHOR_Walk`（走道）。

### `BLD_Wall_Gap`：合龙缺口

![缺口加临时木栅 / Gap_Fill 推到一半 / 合龙后（城外看，合龙石）](images/act2/site_wall_gap.jpg)

占地同 `BLD_Wall_Seg`。主体 `BLD_Wall_Gap` 由三部分组成：

- 全长墙基砌到 2.5 m，缺口底铺了一层灰浆。
- 两端 x ±3..±4 是砌到顶的墙头，带走道和垛墙。
- 墙头每隔一层（0.5 m 一层，从 2.5 起的第 0、2、4… 层）向缺口里伸出半块石头（0.5 m），这就是留槎。

| 子物体 | 说明 |
|---|---|
| `Gap_Fill` | 最后一段，x −3..3，从 2.5 m 砌到垛口，每一层都和留槎咬合；城外一面嵌合龙石（`M_Plaque`，文字贴图可以接 rupu_a2_text）。**原点在合龙段底面中心 (0, 0, 2.5)**，摆好后就是闭合位置 |
| `ANCHOR_GapFill_Start` | 推入的起点，Blender (0, 5.6, 2.5)，团结里是 localPosition (0, 2.5, −5.6)。**推入方向是从城内 +Y 沿 −Y 平推**（团结里沿 +Z）。因为留槎是横向咬合的，沿这个方向推不会穿插。改成从上往下吊入（起点 z+6）也可以 |
| `Gap_Barricade` | 缺口里临时堵的木栅和两层土袋。殉难段「墙没合龙」时显示，合龙后隐藏 |
| `FX_ClosureDust`、`ANCHOR_Closure`（王德合龙站位）、`ANCHOR_Gap_Defend`（守缺口） | |

和 `ENV_NorthGate_Build` 的关系：那是一整片 40 m 的工地场景，带叠加式的 Stage 和 Closure。这两个 8 m 模块用在世界城墙上：摆在哪一段都行，可以多段并排。

## 2. 工地 overlay

### `ENV_A2_WorkSite_Wall`：沿墙一段

![沿墙工地（和 Stage_2 墙段叠放）](images/act2/site_worksite_wall.jpg)

和 `BLD_Wall_Seg` / `BLD_Wall_Seg_Build` 用**同一个原点、同一个旋转叠放**；东西都在城内侧（+Y），只有放线桩在城外。

| 子物体 | 内容 |
|---|---|
| `Scaffold` | 满跨毛竹脚手架：两排立杆，2 / 4 / 6 m 三层跳板，外侧护栏，剪刀撑，爬梯；顶上有吊杆、滑轮和吊石兜 |
| `StakeLine` | 城外墙脚的放线桩、麻线、龙门板 |
| `RamForm` | 地面上一副板筑模板（木模板、立柱、穿杆、半满的分层夯土），两根夯杵 |
| `Mortar` | 灰浆站：拌灰槽、石灰堆、灰桶、灰耙 |
| `Stones` | 条石垛、散石、碎石 |
| `Timber` | 跳板备料 |
| `Bamboo` | 地上一捆毛竹，脚手架端头斜靠一排 |

锚点：`ANCHOR_Lay_1/2`（跳板上砌石）、`Ram`、`Mortar`、`Carry_From/To`（抬石）、`Climb`、`Hoist`、`StakeLine`。特效：`FX_Mortar`、`FX_RamDust`。

### `ENV_A2_WorkSite_Yard`：料场

![料场](images/act2/site_worksite_yard.jpg)

约 22 × 16，原点在场地中心地面，−Y 朝路。子物体：

| 子物体 | 内容 |
|---|---|
| `Ground` | 踩实的泥地 |
| `Stones` | 两座条石垛、块石、两堆碎石、两个凿石位（垫墩、半成品石、石屑） |
| `Lime` | 石灰池、石灰堆、筛子、灰桶、水缸 |
| `Timber` | 原木堆、跳板堆、锯马（上面架着一根原木） |
| `Bamboo` | 竹架，斜靠一排毛竹，地上两捆 |
| `RamForm` | 示范夯的板筑模板 |
| `Shed` | 工棚：四柱，单坡草顶，工具架，记名桌和椅子 |
| `Cart` | 平板车（车上一块石）、独轮车 |
| `Fence` | 三面木栏 |

锚点：`ANCHOR_Chisel_1/2`、`Lime`、`Saw`、`Load`、`Ram_1/2`、`RosterDesk`（工地日「记名」）、`Foreman`、`StoneStack`、`Carry_Out`、`cam_top`。特效：`FX_Chisel_1/2`、`FX_LimeDust`、`FX_RamDust`。

工地日的「巡工 / 记名 / 劝人」站位都可以从这两个 overlay 的锚点里挑。

## 3. 水门 `BLD_MING_WaterGate_Sluice`：开 / 闭两组

![左：State_Closed（闸板落下、石条、死水）；右：State_Open（闸板升起、流水、小船）](images/act2/site_sluice.jpg)

套件还是摆在 `BLD_Wall_WaterGate` 的同一位置、同一旋转。会切换的部件分成两组，**A 只需要 SetActive 其中一组**：

| 组 | 子物体 |
|---|---|
| `State_Closed` | `Sluice_Gate`（闸板落到洞底 z −1.8）、`NOCOL_Sluice_Rope`、`Sluice_Latch`（门闩）、`Sluice_StoneBar_1..3`（三根石条叠在石条槽里）、`NOCOL_Water_Still`（深色死水面，z −0.87） |
| `State_Open` | `Sluice_Gate_Open`（闸板升 1.8 m，底边 0.0，离水面 0.9 m）、`NOCOL_Sluice_Rope_Open`（短绳）、`NOCOL_Water_Flow`（浅色流水面，带白纹，闸下翻花）、`Sluice_Boat`（舢板，停在城内一侧）、`FX_WaterFlow`、`FX_Splash` |

两组共用的部件：闸槽和城顶绞盘架（主网格），以及 `Sluice_WinchDrum`（绕本地 X 转）。锚点 `ANCHOR_Sluice_Spot_1..3`、`ANCHOR_Winch`、`ANCHOR_Latch` 没有变。

想播过程动画的话，有两种做法：

- **开闸**：保持 `State_Closed`，依次抽掉 `Sluice_Latch`、把 `Sluice_Gate` 的 localPosition.y 加 1.8、转 `Sluice_WinchDrum`，然后切到 `State_Open`。
- **闭闸**：在 `State_Closed` 里依次显示三根石条。

地图的总水面在 −0.9，两种水面都抬高了 2–3 cm，避免闪烁。

## 4. 城门 `BLD_MING_GateTower`：门扇、碰撞、通道

![关门（城外）/ 开门（城内看，门扇贴到洞壁）](images/act2/site_gate.jpg)

城门洞属于下面的 `BLD_Wall_GateBase`（洞宽 4.4，拱脚 3.6，拱顶 5.8，洞深 ±3.5）。城楼原点比它高 7.0 m，所以门扇和碰撞体都放在城楼的本地 z = −7.0（也就是门洞地面）。**外轮廓占地没有变**：包围盒仍然是 x ±7.25，y ±4.45。

| 子物体 | 说明 |
|---|---|
| `Gate_Door_L` / `Gate_Door_R` | 门扇，各宽 2.04，顶边贴合券形。**原点在门轴底端**：(±2.05, −2.45, −7.0)，靠城外一侧。关的时候横在门洞里。开门是绕竖轴转 90°，转向城内贴到洞壁上，旋转值照 `ANCHOR_Gate_Door_L_Open` / `_R_Open` 取（在 Blender 里左扇是 rz +90°，右扇是 −90°）。门扇上有拼板缝、铁叶、门钉、门环座，城内面有穿带 |
| `COL_Gate_Door_L/R` | 门扇碰撞，挂在门扇下面跟着转。关门时挡路，开门时贴墙 |
| `Gate_Bar` | 门闩，横架在门轴立枋的门闩托上（城内侧）。开门前先抽走或隐藏，它没有碰撞 |
| 门框（并在主网格里） | 门轴立枋、门闩托、6 cm 门槛石，可以直接走过去 |
| `COL_Gate_Pier_L/R` | 门洞两侧的墩台（x ±2.2..±7.2） |
| `COL_Gate_Jamb_L/R` | 门轴立枋 |
| `COL_Gate_Vault` | 券顶以上 |
| `COL_Tower_*` | 城楼底层：楼板、8 根柱、穿堂的前后墙和两端墙（两端墙各留 1.6 m 的门）；`COL_Tower_Upper` 是上层体块，挡相机用 |

**通道检查**：门扇打开后，在 x ±1.5、高 0..3.5、y ±3.5 的范围里，没有任何 `COL_*` 进入。实际净宽 3.92（两扇开门的碰撞之间），到拱脚的净高 3.6。

注意 1：按 `RupuMapBuilder.SetupColliders` 的约定，资产里一旦有 `COL_*`，**就只用 COL 做碰撞**。所以城楼的柱、墙、楼板都补上了 COL，城墙走道照样可以穿过城楼的前廊、后廊和穿堂。

注意 2：`BLD_Wall_GateBase`（build_yongchang.py）里烘焙着一对开启状态的门扇，贴在洞壁上。新门扇打开时正好和它们重合。但是关门时，城内一侧还能看到那对烘焙门扇。要彻底干净，需要在 `gate_base()` 里去掉烘焙门扇，那个文件这次不归我改。

锚点：`ANCHOR_Gate_Out` / `Gate_In`（门洞外 / 内各 2 m）、`ANCHOR_Gate_Bar`（抬门闩的站位），以及原有的 `ANCHOR_walk_W/E`、`lookout`。

## 5. 王宅 `ENV_WangHouse`：验收和拆梁

![拆梁后的俯视（屋脊塌口、梁横在天井）/ 厅内完整 / 厅内拆梁后](images/act2/site_wanghouse_beam.jpg)

### 逐项验收

| 项 | 结果 |
|---|---|
| 大门 | 门洞 1.9 × 2.6（x ±0.95，z 0.35..2.95），石门框，门额。`Door_L/R` 的原点在门轴，开门照 `ANCHOR_Door_L_Open` / `_R_Open`（朝院内转 90°） |
| 门屋到天井 | 门屋后墙开 3.0 m 宽的口，地坪从 0.35 降到 0.1，只有一级 |
| 台阶 | 大门前踏步顶 0.22，门屋台基 0.35；正厅前两级（0.25 / 0.45），厅地坪 0.45；厢房、书房地坪 0.3，门洞 1.2 × 2.2 |
| 正厅 | 明间开敞，净宽约 2.6（柱间），高 3.45 |
| 梁木 | 原来屋面下面是填实的，五架梁以上看不见。**这次正厅屋面改成不填实**：抬梁、瓜柱、檩都露出来，两端山尖单独补墙。拆梁后的塌口能透出天空 |
| 室内锚点 | 已补，见下 |

### 拆梁两态

两组二选一：

| 组 | 子物体 |
|---|---|
| `State_Beam_Intact` | `Beam_Removable`：明间东缝 x=1.5 的五架梁，0.34 × 0.45 × 5.3。**原点在前端**，也就是前金柱 y=4.2 处的梁底中心，梁沿 +Y 伸出。可以绕原点下摆，也可以整根平移。`Truss_Upper_E`：这一缝的瓜柱、三架梁、脊瓜柱。`ROOF_Hall`：完整屋面 |
| `State_Beam_Removed` | `ROOF_Hall_Broken`：x 0.3..2.7 的屋脊和上段坡没了，只剩檐口一段；塌口边挂着一片断下来的瓦面、几根断椽、碎瓦檐。`Beam_Fallen`：拆下来的梁，横放在天井的两块垫木上（x −2.4..2.9，y −1.0），原点同样在梁的一端。`Rubble_Hall`：厅里塌下来的瓦堆、碎瓦、斜搭的三架梁、瓜柱。`FX_RoofDust` |

拆梁演出的建议顺序：

1. 王叔杲站到 `ANCHOR_Beam_Ladder`。
2. `Beam_Removable` 下摆或下移。
3. 切到 `State_Beam_Removed`。
4. 播 `FX_RoofDust`。
5. 梁扛出门，走到 `ANCHOR_Beam_Carry_Out`。

俯视时隐藏 `ROOF_*` 的做法不变（`ROOF_Hall` / `ROOF_Hall_Broken` 都在各自组里）。

### 锚点（宅院抉择）

原有锚点都保留，新增这些：

| 锚点 | 用途 |
|---|---|
| `ANCHOR_Shugao` | 王叔杲默认站位：厅内，和 `shugao_hall` 同位 |
| `ANCHOR_Shugao_Gate` | 门口送客 |
| `ANCHOR_Door` | 大门外，交互点 |
| `ANCHOR_Door_Inner` | 门屋里 |
| `ANCHOR_Interior_Hall` / `_Study` / `_Wing` / `_Courtyard` / `_GateHall` | 各间室内中心 |
| `ANCHOR_Beam_Ladder` / `ANCHOR_Beam_Carry_Out` | 拆梁 |
| `ANCHOR_Cost_Outside` | 宅子正前方 18 m（城外侧）：「不圈」时墙外孤宅的镜头位，或放代价表现，比如族人搬家当、哨位 |
| `ANCHOR_Cost_Inside` | 宅后 18 m：「圈进」时新砌围墙的参考位 |
| `ANCHOR_cam_wallview` | 从城墙方向看宅子的斜俯视 |

## 6. 盐场三阶段：`ENV_SaltFurnace` 和 `PROP_SaltSet`

![火候拍（Fire_1 + Brine_Full + Salt_None）/ 卤水拍（Fire_2 + Brine_Half + Salt_Crust）/ 起盐拍（Fire_0 + Brine_Low + Salt_Heap）](images/act2/site_saltfurnace.jpg)

`ENV_SaltFurnace` 有三组状态，**每组三选一 SetActive**：

| 组 | 子物体 |
|---|---|
| `Fire` | `Fire_0`：熄火，只有灰和两根黑炭。`Fire_1`：文火，三根柴、暗炭火、三簇小火舌。`Fire_2`：旺火，六根柴，火舌窜出火口舔上灶脸，火口上沿熏黑 |
| `Brine` | `Brine_Full`：满锅，z 1.10。`Brine_Half`：半锅，z 1.03，液面有浮盐花，锅沿析出一圈盐霜。`Brine_Low`：见底，z 0.975，锅沿盐圈更宽 |
| `Salt` | `Salt_None`：锅底只有一层湿膜。`Salt_Crust`：薄盐壳、盐花、锅沿盐圈。`Salt_Heap`：耙成中间一堆加五小堆，有耙印 |

**改动**：原来的 `Pan_Brine` / `Pan_Salt` 由这几组替代，主网格火口里原来烘焙的余烬也挪进了 `Fire_*`。旧代码里如果引用了 `Pan_Brine`，请改成 `Brine_*`。

想做连续动画也可以：在同一组里插值 `Brine_*` 的 z。特效挂点 `FX_Fire / Smoke / Steam`、站位 `ANCHOR_Stoke / Pour / Scoop` 没有变。

![起盐产出](images/act2/site_saltset.jpg)

`PROP_SaltSet` 原有的部件不变，新增起盐后的产出：

| 子物体 | 说明 |
|---|---|
| `SaltBasket_Full` / `SaltBasket_Empty` | 二选一，位置相同 |
| `SaltOutput_1/2/3` | 三选一，每煮好一锅换下一档。盐堆变大，盐袋 2 → 4 → 6 |
| `SaltPole` | 挑盐扁担加两筐满盐，起盐完成后显示，可以做「挑去换银」 |

## 7. 北门殉难战后现场 `ENV_A2_Aftermath_NorthGate`

![战后现场：俯视 / 低机位](images/act2/site_aftermath.jpg)

约 22 × 16，原点在现场中心的地面。**+Y 方向 10 m 是北门门洞**（`ANCHOR_Gate`），−Y 是城外官道。摆法：原点放在北门门洞外约 10 m，旋转和门的朝向一致。

| 子物体 | 内容 |
|---|---|
| `Debris` | 四杆断枪（两截加枪头、红缨），约 50 支箭（插地的大多从城外斜射进来，也有平躺的，还有一筒撒了），四面藤牌（三面破了，一面斜靠在土袋上），两把倭刀断刃，翻倒的独轮车，被冲散的门口土袋，两只草鞋 |
| `Flags` | 三面倒伏的旗：旗杆平躺，旗面耷拉在地上（`M_Flag`，明代是火色） |
| `Spear_Planted` | 王沛插在门口的枪（「枪留下。人出去。」），原点是入土点。玩家拿走 `spear_pei` 后隐藏 |
| `NOCOL_Decal_Blood` | 血迹贴花，低饱和暗褐 `M_A2S_Blood` / `M_A2S_BloodDry`：五大片，每片周围有溅点，另有两道朝门口的拖痕（遗体被拖回门里） |
| `NOCOL_Decal_Scorch` | 火罐烧痕和碎陶片 |
| `NOCOL_Decal_Trample` | 踩烂的泥 |

贴花都是 4 mm 厚的薄片，离地 4–16 mm，分层错开防闪烁。名字带 `NOCOL_`，不加碰撞，也会关阴影。

锚点：

| 锚点 | 用途 |
|---|---|
| `ANCHOR_Body_WangPei` / `ANCHOR_Body_WangDe` | 两具遗体，放在大片血迹上 |
| `ANCHOR_Body_Militia_1..3` / `ANCHOR_Body_Wokou_1..2` | 其他遗体 |
| `ANCHOR_Tag_De` | 王德腰牌掉落处，对应「守工地合龙」只找回腰牌 |
| `ANCHOR_Spear_Pei` | 王沛的枪 |
| `ANCHOR_Mourner_1/2` | 族人跪位 |
| `ANCHOR_cam_top` | 俯视机位 |

特效：`FX_Smoke_1/2`，余烟。

三选一的现场差异可以这样做：

- **跟王沛出城**：完整显示，`Spear_Planted` 已被拿走。
- **守工地合龙**：完整显示，遗体位只留腰牌。
- **护民撤祠堂**：遗体位空，只剩拖痕和血迹，对应「两具遗体都没抢回」。

## 材质

新增的 `M_A2S_*`（`rupu_a2_site.py`），颜色都写在 Base Color 里：

`M_A2S_Blood` `M_A2S_BloodDry` `M_A2S_Scorch` `M_A2S_Rattan` `M_A2S_RattanDark` `M_A2S_Fletch` `M_A2S_Trample` `M_A2S_Thatch`

新增的 `M_MC_*`（`rupu_ming_civic.py`）：

`M_MC_Flame` `M_MC_FlameCore` `M_MC_Ember` `M_MC_PanWet` `M_MC_WaterFlow` `M_MC_WaterStill` `M_MC_Foam`

这些材质只在 1560 出现，所以没有写进 `era_materials.json`。

## 重新生成

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/build_yongchang.py -- \
  --only BLD_Wall_Seg_Build,BLD_Wall_Gap,ENV_A2_WorkSite_Wall,ENV_A2_WorkSite_Yard,ENV_A2_Aftermath_NorthGate,BLD_MING_GateTower,BLD_MING_WaterGate_Sluice,ENV_WangHouse,ENV_SaltFurnace,PROP_SaltSet \
  --force --preview <预览目录>
```

## 还没做

- `BLD_Wall_GateBase` 里烘焙的那对开启门扇没有去掉（原因见 §4 注意 2）。
- 墙线生长、合龙推入、拆梁、开闸都只给了几何、原点和参考位。动画由 A 在脚本里插值，没有做 Animator 资产。
- 血迹、烧痕用的是低模面片加纯色，没有做贴图边缘的羽化。
- 世界城墙段沿沙盘墙线自动对齐（缺口清单 §5「世界城墙段没有自动对齐」）是场景脚本的事，这里只提供了 8 m 模块。
