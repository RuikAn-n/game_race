# 第三幕「守城」：补充建模（玩家战斗套件、战场、社会 Boss 道具、百姓、动画事件）

依据：[`第三幕_建模清单.md`](第三幕_建模清单.md)（同名 `.xlsx` 是同一份清单的表格版，状态列已更新）。敌人、Boss、攻守城道具、39 个战斗动作上一批已经做完，见 [`act3_enemies.md`](act3_enemies.md)，这次没有重做。

全部是程序化白模：低模、纯色材质。文字面（旗、匾、名签、愧顽簿、族谱页、粮袋印、火炮教学图）是贴图，贴在单独的 0..1 UV 面片上。

| 模块（`Tools/blender/`） | 内容 |
|---|---|
| `rupu_a3_cast.py` | 20 个人物、55 个 `A3_*` 动作、枪 / 扁担 / 藤牌、伤兵 / 遗体静态件、担架 |
| `rupu_a3_props.py` | 39 件道具（§3.1、§3.2、§3.4、§4.3） |
| `rupu_a3_env.py` | 15 块战场 overlay / 场景件（§3.3、§3.4、§4.2） |
| `rupu_a3_text.py` | 文字贴图（§7.2）+ `PROP_A3_Placard` |
| `rupu_a3_shots.py` | 本文档的预览图（只读 .blend，不改资产） |

团结侧新增：`RupuAnimEvents.cs`（写动画事件）、`Runtime/RupuAnimEventRelay.cs`（事件接收）、`RupuVfx.BuildAct3()`（12 个特效）。

**检查结果**：
- 178 个 FBX 全部通过 `rupu_pipeline` 规格检查并导出，面数都在上限内。这 178 个包括新资产，以及因为修鬼倭而重新导出的敌人和 Boss 片段。
- 团结导入没有报错。
- 89 个人形 Avatar 全部有效。
- `AC_Humanoid_Locomotion` 自动收进了 55 个 `A3_*` 动作，现在共 110 个状态。
- Windows 包构建成功，0 错误。
- 新资产 150 条已登记到 `Data/asset_manifest.csv`。

## 0. 清单逐项对照

| 清单 | 状态 | 说明 |
|---|---|---|
| §2.1 鬼倭跪地裙甲穿地 0.23 m | ✅ 修好 | 实测穿地的是袴（`M_BS_GW_Hakama`），不是草摺。原因是膝盖以下的下摆只跟着大腿转。现在膝下改为跟小腿走：给 `rupu_char` 加了可选参数 `skirt_knee`，只有鬼倭开启。另外所有敌人和 Boss 片段都加了逐帧落地修正（`rupu_enemy.ground_keys`，只抬不压）。修完后跪地最低点是 -0.02 m（布料贴地），处决倒地是 -0.01 m，倒下过程中最差一帧 -0.06 m |
| §2.1 FBX 没有动画事件 | ✅ | 数据统一写在 `Data/anim_events.json`，共 79 个片段（第三幕 A3 40 个、第二幕 A2 9 个、敌人/Boss 30 个），再由 `RupuAnimEvents` 写进 clip 导入设置，已经执行过。详见 §5 |
| §2.1 旗面/匾/名签/谱页无字 | ✅ 第三幕部分 | 见 §4 |
| §2.1 码头可走面 / 水火无碰撞 | ✅ | `ENV_A3_BurningDock` 自带 `COL_Deck`。水面一律 `NOCOL_Water`，火线是 `NOCOL_FireLine_*` 加触发体 `TRIG_FireLine_*` |
| §2.1 敌人/Boss 配色 | ⏸ P2 | 没做 |
| §3.1–3.5 P0 共 39 项 | ✅ 全部 | 见 §1–§3 |
| §4.1–4.3 P1 共 39 项 | ✅ 全部 | 同上 |
| §6 动画：玩家 P0 16 个 + P1 10 个、义师 8、百姓 8、阿贵/王叔杲/族老 8 | ✅ 50 个，另加 5 个 | 帧数、循环、事件按 xlsx「动画」表（md 没写帧数的以 xlsx 为准）。另外加了 5 个静态 / 被绑姿势（见 §2）。复用的 `A2_LoadCannon/WriteLoop/PushLoop/ClimbLoop` 本来就有 |
| §7.2 文字贴图 | ✅ 全部 15 种（名签 30 张） | 见 §4 |
| §8.1 VFX 12 个 | ✅ | `PF_VFX_A3_*`，见 §5 |
| §7.1 UI、§7.3 2D 主画面、§8.2 音频 | ⏸ | 不属于建模，这次没做 |
| §5 P2 打磨（配色、2K 贴图、LOD、天气、结算页） | ⏸ | 没做 |

## 1. 人物（`rupu_a3_cast.py`，Characters，Humanoid 22 骨）

![P0 人物：阿贵、四个难民、战损王砚、枪、扁担](images/act3/chars_p0.jpg)
![P1 人物：难民 E–H、伤兵、遗体、义师三兵种、陈盐商、王执、阿贵母亲、藤牌、阿贵短枪](images/act3/chars_p1.jpg)

所有第三幕人物都带 `rupu_enemy` 的插槽：`SOCKET_Hand_R/L`、`SOCKET_Back`、`FX_Hit`、`FX_HitHead`。武器挂在插槽下面，局部位置和旋转清零即可。

| 资产 | 身高 | 外观 | 复用 |
|---|---:|---|---|
| `NPC_A3_Agui` | 1.68 | 17 岁义师。灰纸甲、皮护臂、腰牌，戴王德留下的旧头巾，右肩有补丁，身上有泥污 | 义师 D |
| `NPC_A3_Refugee_A` | 1.50 | 逃难老妇。灰袄、褐头巾、驼背、背包袱 | — |
| `NPC_A3_Refugee_B` | 1.57 | 抱孩妇人。深青袄、高髻，胸前背带兜着襁褓 | — |
| `NPC_A3_Refugee_C` | 1.30 | 12 岁半大男孩。短褂、赤脚、总角、补丁 | — |
| `NPC_A3_Refugee_D` | 1.64 | 老农。斗笠、补丁裤、汗巾、微驼；扁担用 `PROP_A3_CarryPole` | 民夫 C |
| `CH_WangYan_1560_Battle` | 1.75 | 战损王砚，和 1560 版同脸同高。左肩布护肩、右前臂绑带、斜背枪带、泥污 | 王砚 1560 |
| `NPC_A3_Refugee_E` | 1.66 | 老翁。灰旧长衫、白须；拐杖用 `PROP_Staff_Elder` | — |
| `NPC_A3_Refugee_F` | 1.56 | 孕妇。褐袄、腹部隆起 | — |
| `NPC_A3_Refugee_G` | 1.50 | 15 岁少女。褪色旧红袄、长辫红头绳（和 1941 的阿禾区分） | — |
| `NPC_A3_Refugee_H` | 1.70 | 货郎。蓝灰头巾、垫肩；扁担竹筐用 `PROP_A3_CarryPole` | 民夫 A |
| `NPC_A3_Wounded_A` / `_B` | — | 断臂伤兵（吊带、绷带）/ 头伤伤兵（头绷带）。不血腥，只有一小块暗色 | 义师 A / B |
| `NPC_A3_Corpse_A` / `_B` | — | 阵亡义师 / 民夫。配 `A3_CorpseSide` / `A3_CorpseProne` 和盖席 | 义师 D / 民夫 B |
| `NPC_A3_Militia_Spear` | — | 枪兵：红缨斗笠、靛青短褐，持 `PROP_A3_Spear` | 义师 D |
| `NPC_A3_Militia_Bow` | — | 弓手：纸甲、箭囊，另外背一张弓 | 义师 B |
| `NPC_A3_Militia_Shield` | — | 牌手：左手藤牌 `PROP_A3_RattanShield`，右手短刀 | 义师 C |
| `NPC_A3_Chen` | 1.68 | 陈盐商。胖、紫灰绸衫、东坡巾、玉佩，前襟露出一叠银票 | — |
| `NPC_A3_WangZhi` | 1.70 | 王执。瘦、灰直裰、网巾、灰短须、眉头紧；手抖靠 `A3_ElderBook` | — |
| `NPC_A3_Mother` | 1.53 | 阿贵母亲。病容（苍白肤色）、灰发髻，胸和腰各绑一道麻绳；柱子是场景件，配 `A3_BoundLoop` | — |

**手持件**：原点都在握点，`+Z` 指向杆头或刃。

| 资产 | 说明 |
|---|---|
| `PROP_A3_Spear` | 王砚、义师枪兵用的枪。全长 2.4 m（握点前 1.9 m、后 0.5 m），带枪缨。`ANCHOR_FrontGrip` 是前手位置，`FX_Tip` 是枪尖 |
| `PROP_A3_Spear_Agui` | 阿贵的短枪，2.0 m，没有缨，杆上缠一道旧布 |
| `PROP_A3_RattanShield` | 藤牌，直径 0.75 m，挂 `SOCKET_Hand_L` |
| `PROP_A3_CarryPole` | 扁担加两只竹筐。原点在扁担中点，`ANCHOR_Shoulder` 对齐右肩 |

## 2. 动作（`CH_WangYan_1941@A3_*`，共 55 个）

所有动作共用骨架，会自动进入 `AC_Humanoid_Locomotion`，状态名就是 `A3_*`。根运动已经烘进姿势：跪、倒、坐的高度变化直接作用在身体上，平移由脚本移动 transform。持枪动作的手是用 IK 求解到枪杆上的，枪挂在 `SOCKET_Hand_R`。下面截图里的枪就是这样挂上去的。

![玩家枪术：待机 / 一段刺 / 二段扫 / 三段抡 / 蓄力破防 / 处决](images/act3/anim_player_spear.jpg)
![玩家防守：格挡 / 弹反 / 闪避 / 受击 / 死亡 / 战斗走 / 战斗跑](images/act3/anim_player_defense.jpg)
![玩家任务：开炮、转水轮、升旗、拉闸、擂鼓、提水、泼水、点引信、插旗、关门、扶人、远望、跪](images/act3/anim_player_tasks.jpg)
![义师：待机 / 刺 / 射箭 / 盾撞 / 阵亡 / 搬运 / 溃退 / 欢呼](images/act3/anim_ally.jpg)
![百姓：惊慌 / 逃 / 躲 / 搬 / 跪求 / 哭 / 接粮 / 孩童哭](images/act3/anim_civ.jpg)
![阿贵、王叔杲、族老，以及伤兵 / 遗体 / 被绑静态姿势](images/act3/anim_story.jpg)

| 组 | 片段（帧，事件） |
|---|---|
| 玩家 P0 | `A3_CombatIdleLoop` 48 · `A3_CombatWalk` 32 Footstep@0/16 · `A3_CombatRun` 24 Footstep@0/12 · `A3_SpearThrust1` 30 AttackHit@12 · `A3_SpearThrust2` 28 AttackHit@11 · `A3_SpearSweep` 36 AttackHit@18 · `A3_SpearHeavy` 48 AttackHit@28（0–22 蓄力）· `A3_BlockLoop` 24 · `A3_Parry` 24 Parry@4 · `A3_Dodge` 24 · `A3_Hit` 20 Stagger@3 · `A3_Death` 40 Death@26 · `A3_Execute` 48 Execute@24 · `A3_CannonFire` 40 CannonFire@18 · `A3_WinchLoop` 24 · `A3_RaiseFlag` 32 |
| 玩家 P1 | `A3_PullLever` 24 Lever@15 · `A3_BeatDrum` 24 DrumHit@6/18 · `A3_CarryBucket` 32 循环 · `A3_ThrowWater` 30 Splash@15 · `A3_LightFuse` 24 Ignite@9 · `A3_PlantFlag` 28 Plant@14 · `A3_CloseGate` 36 · `A3_HelpUp` 32 Grab@9 · `A3_Lookout` 48 循环 · `A3_Kneel` 40（停在末帧） |
| 义师 | `A3_AllyIdle` 48 · `A3_AllyFight` 36 AttackHit@14 · `A3_AllyShoot` 40 AttackHit@28 · `A3_AllyShield` 36 盾撞 AttackHit@21 · `A3_AllyDeath` 36 Death@24 · `A3_AllyCarry` 32 循环 · `A3_AllyFlee` 28 循环 · `A3_AllyCheer` 32 |
| 百姓 | `A3_CivPanic` 32 · `A3_CivRun` 24 · `A3_CivHide` 40 · `A3_CivCarry` 32 · `A3_CivKneel` 40 · `A3_CivGrieve` 48 · `A3_CivReceive` 32 Receive@9 · `A3_CivChildCry` 40（除跪、接粮外都循环） |
| 阿贵 / 王叔杲 / 族老 | `A3_AguiSpear` 36 AttackHit@16（架势低、刺得犹豫）· `A3_AguiKneel` 40 · `A3_AguiFear` 32 循环 · `A3_AguiRun` 24 · `A3_ShugaoReport` 48 · `A3_ShugaoKey` 32 Give@18 · `A3_ElderBook` 48（翻一页，手微抖）· `A3_ElderAccuse` 32 Accuse@9 |
| 静态 / 被绑（新增） | `A3_WoundedSit` 靠墙坐 · `A3_WoundedLie` 仰躺 · `A3_CorpseSide` 侧卧 · `A3_CorpseProne` 俯卧 · `A3_BoundLoop` 被绑在柱上（72 帧循环，双臂反剪，柱心在身后 0.15 m） |

**站位约定**：
- `A3_CannonFire` 沿用 `A2_FireCannon` 的站位：炮尾火门在脚底原点左 0.5 m、前 1.0 m、高 0.87 m。
- `A3_BeatDrum` 站在 `PROP_A3_WarDrum` 的 `ANCHOR_Play`。
- `A3_Execute` 的对象跪在身前约 1.8 m，枪尖落在离地 0.35 m 左右。
- `A3_WinchLoop` 和 `A3_CloseGate` 是原地推。

## 3. 道具（`rupu_a3_props.py`，Props ≤3k）

![社会 Boss / 记谱：愧顽簿、名墙、名签、粮袋四态、粮斗秤、粮车、匾、钥匙](images/act3/props_social.jpg)
![指挥 / 守城：信号旗、战鼓、火盆、箭捆、擂石、油坛、街垒 4 模块、拦江浮栅、小船、水槽、水桶、兵牌、长幡、火篮、炮具、闸具](images/act3/props_command.jpg)
![P1：炮弹、火药桶、断箭、破盾、头盔、稻捆、鱼篓农具、更漏、铜钟、锣、号角、火把、灯笼、沙袋、绳卷](images/act3/props_p1.jpg)
![伤兵、遗体（带盖席）、担架伤兵、尸架、盖尸席](images/act3/static_poses.jpg)

清单里的「数量 N」指场景里摆 N 个，资产本身只做一件。需要变体的做成一组并排的子物体，命名为「资产名_变体」。状态件是固定名字的子物体，脚本用 `SetActive` 切换。和清单子物体名不同的地方见本节末尾的「命名差异」。

| 资产 | 面数 | 子物体 / 锚点 |
|---|---:|---|
| `PROP_A3_BlameBook` 愧顽簿 | 220 | `Book_Open`（摊开 0.9×0.6）下挂 `Spread_01..03`，每组是 `Page_L_0k` / `Page_R_0k`（三个跨页贴图 `T_A3_BlamePage_01..03`）；还有 `Book_Closed`、`Tab_01..03`、`Stamp`、`ANCHOR_Read`、`ANCHOR_Accuse`、`FX_Ink` |
| `PROP_A3_NameWall` 祠堂名墙 | 1.1k | 3.6×2.2 m，带檐顶和底座。`Slot_01..30` 每排 10 个、右起；`NameTag_01..30`（每个一张字）、`Brush`、`ANCHOR_Write`、`FX_Ink` |
| `PROP_A3_NameTag` 名签 | 20 | 6×24 cm（清单写的「5×2 cm」按 5×20 cm 理解，略放大以便看清）。原点在底边，换材质 `M_A3T_NameTag_xx` 就换名字 |
| `PROP_A3_GrainSack` 粮袋 | 672 | `Sack_Full`（正面印「糧」）、`Sack_Open`、`Sack_Empty`、`Sack_Broken` 四态互斥，散米是 `NOCOL_Grain_Spill`，另有 `ANCHOR_Grab` |
| `PROP_A3_GrainMeasure` 粮斗/秤 | 356 | `Measure`、`Stand`、`Scale`（原点在提纽）、`Weight`、`Scoop`、`ANCHOR_Use` |
| `PROP_A3_GrainCart` 粮车 | 890 | `Bed`、`Wheel_L/R`（原点在轮轴，绕 X 转）、`Sack_1..3`、`ANCHOR_Pull` |
| `PROP_A3_SignalFlag` 信号旗 | 744 | 青 / 红 / 白三面：`Flag_Blue/Red/White`，每面是 `Pole_*`（2.4 m）+ `NOCOL_Cloth_*_Front/Back`（0..1 UV）+ `ANCHOR_Grip_*` + `FX_Cloth_*` |
| `PROP_A3_WarDrum` 战鼓 | 726 | 鼓面直径 1.1 m、朝 -Y、中心高 1.25 m。`Drum`、`Stand`、`Stick_L/R`、`ANCHOR_Play`、`FX_Hit` |
| `PROP_A3_Brazier` 火盆 | 479 | `Legs`、`Basket`、`NOCOL_Fire`、`FX_Fire`、`ANCHOR_Light` |
| `PROP_A3_ArrowBundle` 箭捆 | 440 | 20 支一捆，横放在两个 X 架上。`Bundle`、`Rack`、`ANCHOR_Take` |
| `PROP_A3_RockPile` 擂石 | 488 | 14 块，`Rocks`、`COL_Rocks`、`ANCHOR_Push`（+Y 城内一侧）、`FX_Dust` |
| `PROP_A3_OilJar` 油坛 | 380 | `Jar`、`Lid`、`ANCHOR_Pour`、`FX_Pour` |
| `PROP_A3_Barricade` 街垒 | 1.5k | 4 个模块，每块 2 m 宽，间隔 2.5 m：`Barricade_Wood/Stone/Cart/Sand`，各带 `COL_*` 和 `ANCHOR_Cover_*` |
| `PROP_A3_GateBoom` 拦江浮栅 | 684 | `Boom`（6 根原木，原点在水面）、`Chain_L/R`、`ANCHOR_Release` |
| `PROP_A3_Skiff` 小船 | 272 | 3.2 m，原点在水线，吃水 0.25 m。`Hull`、`Oar`、`ANCHOR_Stand` |
| `PROP_A3_WaterTrough` 水槽 | 144 | `Trough`、`NOCOL_Water`、`ANCHOR_Fill` |
| `PROP_A3_Bucket` 水桶 | 272 | `Bucket`、`NOCOL_Water`（满桶时显示）、`ANCHOR_Handle` |
| `PROP_A3_UnitMarker` 兵牌 | 112 | `Marker_Blue`（「義」）/ `Marker_Red`（「倭」），每个是 `Pole_*` + `NOCOL_Cloth_*_Front/Back` + `ANCHOR_Plant_*` |
| `PROP_A3_WallBanner` 长幡 | 636 | 3.5 m 竖幡三面：`Banner_Wang`（王）/ `Banner_Tanghe`（湯）/ `Banner_Blank`（无字），各带 `ANCHOR_Grip_*` |
| `PROP_A3_Key` 城门钥匙 | 100 | `Key`（原点在握点）、`Tag`、`ANCHOR_Hold` |
| `PROP_A3_FireBasket` 火篮 | 401 | `Post`、`Chain`（可晃）、`Basket`、`NOCOL_Fire`、`FX_Fire` |
| `PROP_A3_CannonTools` 炮具 | 616 | `Rack`、`Rammer`、`Ladle`、`Match`（每件原点在握点）、`Balls`、`PowderBag`，以及 `ANCHOR_Rammer/Ladle/Match`、`FX_Match` |
| `PROP_A3_SluiceTools` 闸具 | 724 | `Post`、`Hook`、`Crowbar`、`Rope` |
| `PROP_A3_CorpseCover` 盖尸席 | 212 | `NOCOL_Cover`（盖着时）、`NOCOL_Cover_Flat`（掀开后） |
| `PROP_A3_Wounded` 伤兵 | 2.6k | `Wounded_Sit`（靠墙坐，墙在 +Y 0.35）、`Wounded_Lie`（躺草席）、`Mat`、`ANCHOR_Wall`、`ANCHOR_Tend_*`。由 NPC_A3_Wounded_A/B 摆姿势后烘成静态网格 |
| `PROP_A3_Corpse` 遗体 | 2.9k | `Corpse_Side` / `Corpse_Prone`，各配一张盖席 `Cover_Side/Prone`（可单独隐藏）。不血腥 |
| `PROP_A3_Stretcher_Wounded` | 1.5k | `Stretcher`、`Wounded`、`ANCHOR_Carry_F/B` |
| `PROP_A3_Bier` 尸架 | — | `Bier`、`Cloth`（白布盖着人形）、`ANCHOR_Carry_F/B` |
| P1：`Cannonball` `PowderKeg` `ArrowStuck` `ShieldBroken` `Helmet` `RiceBale` `FishTrap` `WaterClock` `Bell` `Gong` `Horn` `Torch` `Lantern` `Sandbag` `RopeCoil` | 72–876 | 都带 `PROP_A3_` 前缀。变体并排：`Ball_Iron/Stone/Stack`、`NOCOL_Arrow_1..4`、`Broken_Rattan/Wood/Plank`、`Helmet_Ming/Jingasa/Kabuto`、`Sandbag/Stack`。可动件：`PowderKeg/Lid`、`WaterClock/Float`（沿 Z 上升 0..0.25 m）、`Bell/Bell`（原点在钟钮）+ `Striker`、`Gong/Mallet`。挂点：`FX_Burst`、`FX_Ring`、`FX_Sound`、`FX_Fire`、`FX_Glow`。`Lantern` 前面有一片 `NOCOL_Lantern_Face`（0..1 UV，可贴字） |

**命名差异**（以模型为准）：
- 不该有碰撞的子物体都加了 `NOCOL_` 前缀，包括水面、旗布、火、盖布、散米和贴字面片。
- 愧顽簿三页做成 `Spread_0k` 组。
- 信号旗、兵牌、长幡的变体名后面都加了 `_<颜色或键>`。

## 4. 文字贴图（`rupu_a3_text.py`，§7.2）

| 贴图 | 用在 | 内容 |
|---|---|---|
| `T_A3_Flag_Wang` / `Tanghe` / `Blank` | `PROP_A3_WallBanner` | 「王」字朱旗、「湯」字黄旗、无字素旗（有牙边和旗袖） |
| `T_A3_Unit_Blue` / `Red` | `PROP_A3_UnitMarker` | 蓝「義」、红「倭」 |
| `T_A3_Placard_Huanhai` / `Tongshi` / `Zuci` | `PROP_A3_Placard` | 「環海樓」「通市門」「王氏祖祠」，黑漆金字、右起读 |
| `T_A3_NameTag_01..30` | `PROP_A3_NameWall`、`PROP_A3_NameTag` | 30 个名字，下面小字写殁地（東門 / 水門 / 北門 / 東牆 / 祖祠 / 粮倉 / 瓮城 / 環海樓）。第 30 个是「無名」，墨色较淡 |
| `T_A3_BlamePage_01..03` | `PROP_A3_BlameBook` | 第 1 页：题「愧頑簿」和族规；第 2、3 页：六月初五水门夜开、六月初六粮少三十石。陈某、王执、阿贵三条嫌疑用朱圈标出，另有证据纸片的贴位和小印 |
| `T_A3_RosterPage` | `ENV_A3_1941_InkDesk` | 1941 族谱跨页「永昌王氏族譜　守城錄」，收录同样的 30 个名字 |
| `T_A3_1941_Ink` | 同上 | 王砚新誊的一页，最后一行墨半干，右下角有一圈雨水洇痕 |
| `T_A3_GrainSack` | `PROP_A3_GrainSack` | 朱印「糧」和「王氏義倉」 |
| `T_A3_CannonManual` | `ENV_A3_CannonPlatform` | 三格教学图：一裝藥 / 二裝彈 / 三點火，附线描小图 |

名字、页面文字、殁地都写在 `rupu_a3_text.py` 顶部的 `NAMES` 和 `BLAME_PAGES` 里，改完重新生成即可。

所有双面件（旗、兵牌、幡）背面另有一片 U 方向翻转的面片，所以从背面看也是正字。

## 5. 战场 overlay / 场景件（`rupu_a3_env.py`，Environments）

![P0 战场：烧焦码头、水门闸室、北门街垒、东墙火段、粮仓破损、瓮城防守、战场残骸、小船](images/act3/env_p0.jpg)
![P1 场景：敌台破损、积水街道、集市火场、水田火、祖祠夜战、1941 谱桌、环海楼炮位、瓮城闸门](images/act3/env_p1.jpg)

**通用约定**：
- 叠加件（overlay）的原点和朝向都和它对应的明代建筑一样，摆在建筑上即可，不用再对齐。
- 嵌在场景里的道具，物体名前面会加上组名作前缀，例如 `Brazier_1_Basket`。
- 火线由三部分组成：`NOCOL_FireLine_*`（火苗）、`NOCOL_Scorch_*`（焦痕）、`TRIG_FireLine_*`（触发盒网格）。触发盒在团结里要去掉渲染器，加一个 `isTrigger` 的 BoxCollider。它不会挡路。
- 每条火线都有对应的特效挂点 `FX_Fire_*`。

| 资产 | 叠在 / 原点 | 面数 | 内容与锚点（§9 拼装表） |
|---|---|---:|---|
| `ENV_A3_BurningDock`（W1） | 独立 12×10 m，原点在水面，码头面高 1.0 | 2.8k | 焦黑木板（两处烧穿，用 `COL_Hole_*` 拦住）、断桩、烧塌的货、缆桩铁链、3 道火线、`FX_Smoke_1..3`、`COL_Deck`；锚点 `ANCHOR_PlayerStart_E` / `Cannon` / `BossLand` / `Water` / `Retreat` |
| `ENV_A3_WaterGateInterior`（W2/W4） | 独立，原点在渠底中心 | 0.9k | 渠宽 4.4 m、石壁高 5 m，水面高 0.9 m（齐腰）；右侧有 1.2 m 宽、1.5 m 高的走道和下渠台阶。两道闸槽，`Grille` 铁栅沿 +Z 升 2.5 m 打开（参考 `ANCHOR_Grille_Open`）。另有湿痕水位线、两支火把、`COL_Wall_L/R`、`COL_Ledge`；锚点 `ANCHOR_Sluice_Spot_1..3` / `Winch` / `Latch` / `Boat` / `PlayerStart_W` |
| `ENV_A3_NorthGateBarricade`（W3/W7） | 独立 14×10 m，原点在门洞内侧，门朝 -Y | 2.5k | 4 个街垒模块、翻倒的货摊、沙袋、箭捆、破旗；中间留 4.4 m 通道。锚点 `ANCHOR_Cover_1..4` / `Flag` / `Ladder_1..6` / `Ram` / `GateInside` / `PlayerStart_N` |
| `ENV_A3_WallFire`（W4/W7） | 两段 `BLD_Wall_Seg`（x -8..8） | 3.1k | 走道焦痕、外墙烟熏、两处碎垛口（`BrokenMerlon_1/2`，带 `COL_Rubble_*`）、3 道火线、2 个火盆、2 个火篮；锚点 `ANCHOR_Fire_1..3` / `WaterWheel` / `Breach` / `PlayerStart_D` |
| `ENV_A3_GranaryDamage`（W6） | `BLD_MING_Granary` | 0.9k | 东门（x=+5）门扇被撞破（`DoorFrame_Broken`、`Door_Leaf_L/R`）、塌檐 `Eave_Collapse`（不挡门）、`NOCOL_Grain`、`NOCOL_Footprints`、门里冒火；锚点 `ANCHOR_GranaryDoor` / `Grain_1..3` / `Scale` / `Distribute` / `PaddyGate_1..2` |
| `ENV_A3_BarbicanDefense`（W8） | `BLD_Wall_Wengcheng` | 3.6k | 两侧墙头 4 堆擂石、墙根沙袋（中心 8 m 留空）、外门洞临时木闸 `Gate_Temp`（沿 +Z 升起打开）、警钟、射孔木板墙、血布；锚点 `ANCHOR_RockDrop_1..4` / `BarbicanGate` / `Flag` / `ArenaCenter` / `PlayerStart_H` / `Escape` |
| `ENV_A3_BattleDebris` | 独立 8×8 m | 1.1k | 断箭、破盾、头盔、碎石、断枪、血布，全部 NOCOL；只有两块大石带 `COL_Rock_*` |
| `ENV_A3_WallTowerDamage` | `BLD_Wall_DiTai` | 0.7k | 前垛口炸开（碎石放在左前角，不挡炮线）、炮位焦痕、断炮车轮、散砖 |
| `ENV_A3_FloodedStreet` | 独立 16×6 m | 0.2k | 5 cm 浅水（`NOCOL_Water`）、漂浮物、半淹的箱子（带 COL） |
| `ENV_A3_MarketFire` | 独立 12×8 m | 0.8k | 三座烧焦的摊位（一座塌了半边）、焦梁、火苗、1 道火线；中间 3 m 留空 |
| `ENV_A3_PaddyFire`（W6） | 独立 12×12 m | 2.5k | 四块水田、十字田埂宽 1.4 m（`COL_Dike_X/Y`）、稻茬、3 堆烧着的稻草、2 个稻捆 |
| `ENV_A3_ShrineNight`（W5） | `BLD_INT_AncestralHall` 正厅 | 1.4k | 6 个烛架、2 盏灯笼、翻倒的长凳、血布；锚点 `ANCHOR_BlameBook` / `Suspect_1..3` / `Evidence_1..3` / `Record` / `Respawn` |
| `ENV_A3_1941_InkDesk` | 独立 3×3 m | 0.5k | 半面墙、木格窗（`NOCOL_RainGlass`、`FX_Rain`）、书桌、椅子、油灯 `FX_Lamp`、族谱 `Roster_Page`、新页 `InkPage`、砚、笔；`cam_matchcut` 是俯拍纸面的机位，另有 `ANCHOR_Sit` |
| `ENV_A3_CannonPlatform`（W8） | 独立 6×5 m（放到城墙上时整体抬高 7.08） | 2.7k | 木台、炮眼护墙（炮线朝 -Y）、沙袋、炮弹、火药桶、炮具、教学木牌；锚点 `ANCHOR_CannonPost` / `Loader` / `Gunner` |
| `ENV_A3_BarbicanGate`（W8） | `BLD_Wall_Wengcheng` 外门洞 | 0.4k | 千斤闸 `Gate_Slide`（开 4.2 m，参考 `ANCHOR_Gate_Open`，带 `COL_Gate_Slide`）、闸槽、墙顶绞盘 `Winch`、3 个落石孔；锚点 `ANCHOR_Winch` / `RockDrop_1..3` / `Gate` |

## 6. 动画事件与特效

**写入动画事件**：
1. 编辑 `Data/anim_events.json`。
2. 在团结里执行菜单「入谱 > 人物 > 写入动画事件」，或运行 `-executeMethod Rupu.EditorTools.RupuAnimEvents.ApplyCLI`。

这个工具的行为：
- 只替换 JSON 里出现过的事件名，在 Inspector 里另加的事件会保留，可以重复执行。
- JSON 里的 `loop` 字段会覆盖导入器按文件名猜出的循环设置。
- **接收方**：在有 Animator 的物体上挂 `Rupu.RupuAnimEventRelay`，然后订阅 `OnEvent(string)`。它为每个事件名都准备了同名方法，所以不会出现「AnimationEvent 没有接收者」的报错。

**事件名**：
- 约定名：`AttackHit`、`PhaseChange`、`Stagger`、`Death`、`Footstep`。
- 建议名：`Parry`、`Execute`、`CannonFire`、`Ignite`、`DrumHit`、`Splash`、`Plant`、`Lever`、`Grab`、`Give`、`Accuse`、`Receive`，以及第二幕的 `PryEffort`、`BeamFall`、`Sleeve`。

**特效**：在团结里执行菜单「入谱 > 特效 > 生成全部特效」，会新增 12 个 `PF_VFX_A3_*`。标「一次」的不自动播放，需要由脚本调用 `Play()`。

| 预制体 | 说明 |
|---|---|
| `ArrowVolley`（一次） | 12 支箭齐射，带尾迹，沿本地 +Z 抛 |
| `RockFall`（一次） | 落石，0.9 s 后落地扬尘 |
| `OilPour` | 油流；子物体 `FireLine` 是 3 m 火线，脚本打开 |
| `WaterBurst` | 开闸水柱加泡沫 |
| `Steam` | 蒸汽 |
| `GateSplinter`（一次） | 门板碎裂成大块 |
| `WallCollapse`（一次） | 缺口塌落，8 m 宽，带石块和大尘 |
| `InkLine`（一次） | 墨迹逐笔写出一行，0.24 m |
| `RainSplash` | 雨打地面溅点，10×10 m |
| `CrowdDust` | 人群扬尘 |
| `FlagRip`（一次） | 旗面撕裂的碎布 |
| `BloodMist`（一次） | 暗色点状血雾，不血腥 |

## 7. 重新生成

```bash
cd /Users/anruikang/Downloads/game_race
B=/Applications/Blender.app/Contents/MacOS/Blender
# 列出第三幕资产
$B -b --factory-startup -P Tools/blender/build_yongchang.py -- --list | grep -E "A3_|_Battle"
# 重建某几个（改过的要加 --force）
$B -b --factory-startup -P Tools/blender/build_yongchang.py -- --only PROP_A3_NameWall,CH_WangYan_1941@A3_SpearHeavy --force
# 重出文档预览图
$B -b --factory-startup -P Tools/blender/rupu_a3_shots.py -- --out Docs/images/act3 --anims
```

**改哪里**：
- 改动作姿势：编辑 `rupu_a3_cast.py` 的 `g_*()`。
- 改帧数：编辑 `A3_SPEC`，它按 xlsx 的帧数统一改时。
- 改事件帧：编辑 `Data/anim_events.json`，改完重新执行「写入动画事件」。

## 8. 还没做 / 需要确认

- **UI / 2D / 音频**（清单 §7.1、§7.3、§8.2）、**P2 打磨**（敌人和 Boss 配色、2K 建筑贴图、LOD、天气、结算页）这次都没做。
- **名字和页面文字**：名墙 30 人的名字和殁地、愧顽簿三页的事由，都是按清单的剧情点自拟的。策划案 `第三幕_守城_策划案_v1.md` 不在仓库里，需要 A 或策划确认后再改 `rupu_a3_text.py`。
- **名签尺寸**：清单写的是 5×2 cm，我按 5×20 cm 理解，实际做成 6×24 cm。
- **动画帧数和事件**：md 和 xlsx 有出入时以 xlsx 为准。只有 xlsx 里没有事件的几个任务动作（拉闸、泼水、插旗等），我加了建议事件。
- **场景接入**：资产已经导入团结，但第三幕场景还没有摆，归 A 负责。叠加件按原点直接叠到对应建筑上即可。
- **鬼倭处决片段**：倒地过程中有一帧最低点在 -0.06 m，静止帧都贴地。
- **白模材质**：贴字面片是贴图材质。其他部分都是纯色材质，进团结后按 `era_materials.json` 的语义名换年代材质。
