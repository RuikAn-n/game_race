# 第三幕 1560 八波守城 · 敌人、Boss、攻守城道具、战斗动作

依据：[`入谱_当前建模缺口清单.md`](入谱_当前建模缺口清单.md) 第四节、策划案 v3.0「敌人 / 敌人出招模板 / 八波与双 Boss」、`private/入谱_B执行手册.md` 第 4 节。
全部是程序化白模（低模、纯色材质），生成脚本 `Tools/blender/rupu_enemy.py`（由 `build_yongchang.py` 统一驱动）。

![四兵种 A/B 变体（正面，武器挂在插槽上）](images/act3/enemies_front.jpg)

## 完成情况

| 清单项 | 状态 | 资产 |
|---|---|---|
| 4.1 `CHR_Enemy_Sword` 刀兵 ×2 | ✅ | `EN_Wokou_Sword_A`（真倭）/ `_B`（胁从）+ `PROP_EN_Katana` |
| 4.1 `CHR_Enemy_Archer` 弓兵 ×2 | ✅ | `EN_Wokou_Archer_A` / `_B` + `PROP_EN_Bow` + `PROP_EN_Arrow` |
| 4.1 `CHR_Enemy_FirePot` 火罐兵 ×2 | ✅ | `EN_Wokou_FirePot_A` / `_B` + `PROP_EN_FirePot` |
| 4.1 `CHR_Enemy_Shield` 盾兵 ×2 | ✅ | `EN_Wokou_Shield_A` / `_B` + `PROP_EN_Shield` |
| 4.2 `BOSS_Chiyan` 赤焰 3 阶段 | ✅ | `BOSS_Chiyan` + `PROP_BS_Chiyan_Axe`（扔的火罐用 `PROP_EN_FirePot`） |
| 4.2 `BOSS_Guiwo` 鬼倭 3 阶段 | ✅ | `BOSS_Guiwo` + `PROP_BS_Guiwo_Tachi` / `_Naginata` / `_Nodachi`（三阶段换武器） |
| 4.3 云梯 | ✅ | `PROP_SiegeLadder` |
| 4.3 攻城车/冲车 | ✅ | `PROP_BatteringRam` |
| 4.3 火船 | ✅ | `PROP_FireShip` |
| 4.3 火炮/炮位 | ✅ | `PROP_Cannon_Ming` + `PROP_CannonEmplacement`（实弹/散弹两堆） |
| 4.3 水轮/水车 | ✅ | `PROP_WaterWheel` |
| 4.3 闸门/门闩 | ✅ | `PROP_GateBar`（门扇 + 门闩 + 撞破态）。水门闸板仍用 `BLD_Wall_WaterGate` 自带的 |
| 4.3 拒马/鹿角 | ✅ | `PROP_Chevaux`（`Juma` + `Lujiao`） |
| 4.3 火罐/火油 | ✅ | `PROP_FireOil`（熬油灶 + 可倾倒铁锅 + 油坛 + 一筐火罐）；手投火罐 = `PROP_EN_FirePot` |
| 4.3 水桶/沙袋 | ✅ | `PROP_BucketSand` |
| 4.3 伤兵/担架 | ✅ | `PROP_Stretcher`（含平躺伤兵静态网格） |
| 4.3 城墙破损/门破/火起 | ✅ | `ENV_WallBreach`（破口 + 瓦砾 + 焦痕 + 焦梁）；门破 = `PROP_GateBar` 的 `Broken` |
| 4.4 刀/弓/火罐/盾 攻击、受击、死亡 | ✅ 19 个 | 见下「动作」 |
| 4.4 Boss 三阶段、弱点、处决 | ✅ 20 个 | 每个 Boss 5 个招式 + 阶段转换 + 弱点受击 + 破架势 + 被处决 |
| 4.4 血/火/水/烟/破片/箭矢、墙破/门碎/火势 VFX | ⚠️ 未做 | 按分工由主代理在团结里做；模型上已留 `FX_*` 挂点 |

## 敌人（Enemies，22 骨 Humanoid，与 rupu_char 人物同一套骨架）

A = 真倭（月代头/阵笠/具足，小袖 + 短袴绑腿），B = 胁从（明人包头/斗笠/棉甲，短褂）。每个兵种的标志在**俯视**下也能分：刀兵是光头顶 + 长刀线，弓兵是大圆阵笠 + 长弓，火罐兵背上一个方筐四个圆罐，盾兵面前一道粗盾线。

![俯视：刀兵 / 弓兵 / 火罐兵 / 盾兵（待机姿势）](images/act3/enemies_top.jpg)

| 资产 | 身高 | 三角面 | 造型 |
|---|---|---:|---|
| `EN_Wokou_Sword_A` | 1.64 | 1230 | 月代头发髻 + 白钵卷、靛色小袖束襷、短袴绑腿草鞋、左胯空刀鞘 |
| `EN_Wokou_Sword_B` | 1.68 | 1124 | 明人包头小髻、土褐短褂、红布腰带、绑腿 |
| `EN_Wokou_Archer_A` | 1.66 | 1428 | 黑漆阵笠、赭黄小袖、右后胯箙露箭羽、胁差 |
| `EN_Wokou_Archer_B` | 1.64 | 1236 | 斗笠、灰黄短褂、斜背箭壶 |
| `EN_Wokou_FirePot_A` | 1.68 | 1930 | 头巾兜 + 红额带、铁锈红短褂、背竹罐筐四罐、腰挂三罐 + 引火绳 |
| `EN_Wokou_FirePot_B` | 1.66 | 1906 | 浅色头兜 + 蒙口布、褐短褂、背罐筐、腰挂火罐 |
| `EN_Wokou_Shield_A` | 1.70 | 1676 | 铁钵盔垂錣、黑漆具足（胴/大袖/草摺），最壮 |
| `EN_Wokou_Shield_B` | 1.70 | 1384 | 黑包头、钉铜钉的棉甲背心 |

![背面：束襷、箙、罐筐、具足](images/act3/enemies_back.jpg)

### 武器（Props，原点在握把）

| 资产 | 三角面 | 说明 |
|---|---:|---|
| `PROP_EN_Katana` | 208 | 倭刀，刃长 0.68；`FX_Trail_Base` / `FX_Trail_Tip` 刀光 |
| `PROP_EN_Bow` | 320 | 和弓 2.1 m（上长下短）；子物体 `String`（松弦）/ `String_Drawn`（满弓），`ANCHOR_Nock`、`ANCHOR_ArrowRest` |
| `PROP_EN_Arrow` | 80 | 原点在箭尾；箭头朝局部 -Y（团结 +Z），做投射物时直接朝飞行方向；`FX_Trail` |
| `PROP_EN_FirePot` | 256 | 原点在掌心，罐身在下；`FX_Fuse` 引信 |
| `PROP_EN_Shield` | 224 | 0.6 × 1.16 m 木手牌，中央竖握把在原点，盾面朝 -Y；`FX_Block` |
| `PROP_BS_Chiyan_Axe` | 138 | 赤焰登船大斧，左手在柄后 0.45 m；`FX_AxeFire`、`FX_Trail_*` |
| `PROP_BS_Guiwo_Tachi` | 208 | 鬼倭一阶段太刀（金具、红柄卷） |
| `PROP_BS_Guiwo_Naginata` | 276 | 二阶段薙刀，杆 1.75 m，左手在杆后 0.45 m |
| `PROP_BS_Guiwo_Nodachi` | 208 | 三阶段野太刀，刃长 1.25 m |

## Boss（Bosses）

![阶段：赤焰 P1/P2/P3、鬼倭 P1/P2/P3（正面）](images/act3/bosses_phases_front.jpg)
![背面：火罐架（赤焰弱点）、指物旗](images/act3/bosses_phases_back.jpg)

阶段是同一骨架上**分别蒙皮的子物体**，导出时全部显示，团结里按阶段开关：

| Boss | 三角面 | 常驻（本体） | P1 | P2 | P3 |
|---|---:|---|---|---|---|
| `BOSS_Chiyan` 赤焰（第 4 波东水门） | 2934 | 1.92 m 壮汉，锈红乱发络腮胡、红额带、褪红无袖短褂、前臂缠布、腰挂火罐 | `Phase1_Mino`（蓑衣 + 宽斗笠，火船上）+ `Phase12_Armor` + `Phase12_Pack` | `Phase12_Armor`（焦黑胴 + 左大袖）+ `Phase12_Pack`（四火罐架） | `Phase3_ArmorBroken`（只剩半片胴）+ `Phase3_PackOpen`（罐碎、露红火芯） |
| `BOSS_Guiwo` 鬼倭（第 8 波环海楼/瓮城） | 2552 | 1.86 m，藏青直垂 + 黑袴、铠手甲脚、月代发髻 | `Phase1_Sashimono`（背指物旗）+ `Phase12_Armor` + `Phase12_Kabuto` + `Phase12_Mask` · 太刀 | 去掉指物旗 · 薙刀 | `Phase3_ArmorBroken`（被炮打碎：半片胴带裂口、只剩右袖）+ `Phase3_MaskBroken`（盔掉、半张面具）· 野太刀 |

显隐规则：名字里带 `1` 的在 P1 显示，带 `2` 的在 P2 显示，带 `3` 的在 P3 显示（`Phase12_*` = P1、P2 都显示）。

挂在骨骼上的空物体：

| 名字 | 骨骼 | 用途 |
|---|---|---|
| `SOCKET_Hand_R` / `SOCKET_Hand_L` | RightHand / LeftHand | 武器插槽（所有敌人和 Boss 都有） |
| `SOCKET_Back` | Chest | 背挂（收刀、背斧） |
| `SOCKET_Quiver`（弓兵）、`SOCKET_PotBasket`（火罐兵） | Hips/Chest | 抽箭、取罐的位置 |
| `FX_Hit` / `FX_HitHead` | Chest / Head | 受击火花/血点 |
| `WEAK_Chiyan_Pack` | Chest | 赤焰背包弱点（侦察过才高亮；P3 罐碎后外露） |
| `FX_Chiyan_Fuse_1..3`、`FX_Chiyan_PackFire`、`FX_Chiyan_Steam` | Chest | P1–2 引信火、P3 背包火、P3 水轮倒灌蒸汽 |
| `WEAK_Guiwo_ArmorJoint`（P1–2 右腋甲缝）、`WEAK_Guiwo_Chest`（P3 胴裂口） | Chest | 鬼倭弱点 |
| `FX_Guiwo_MaskEyes`、`FX_Guiwo_ArmorBreak`（P2→P3 碎甲）、`FX_Guiwo_Banner`（P1 旗烧） | Head / Chest | 特效挂点 |

## 攻守城道具

![道具总览（左上起：云梯、冲车、火船、火炮 / 炮位、水轮、城门门闩、拒马鹿角 / 火油、水桶沙袋、担架、城墙破口）](images/act3/props_sheet.jpg)

| 资产 | 三角面 | 子物体 / 挂点 | 说明 |
|---|---:|---|---|
| `PROP_SiegeLadder` | 640 | `Ladder`（枢轴在梯脚，绕 X 转 = 推梯）、`ANCHOR_Bottom` / `ANCHOR_Top`、`FX_Hook_L/R` | 8.9 m 竹梯，已按靠墙角度建好：放在 `BLD_Wall_Seg` 局部 (x, -5.25, 0)、同朝向，梯钩正好挂垛墙；`ANCHOR_Top` 在走道面 7.08 |
| `PROP_BatteringRam` | 755 | `Frame`、`Ram`（吊点枢轴，绕 X 摆）、`Wheel_FL/FR/BL/BR`（轮轴枢轴，绕 X 转）、`FX_RamHit`、`ANCHOR_Push_1..4`、`COL_Ram` | 生牛皮人字顶，俯视一块深色长方顶 |
| `PROP_FireShip` | 1338 | `Hull`、`Cargo` / `Cargo_Burnt`、`Mast`（桅脚枢轴可倒）、`FX_Fire_1..4`、`FX_Smoke`、`ANCHOR_Waterline`、`ANCHOR_Boss` | 8 m 火船，船头铁钩；原点在船底，**下沉 0.45 m 让 `ANCHOR_Waterline` 贴水面**；赤焰 P1 站 `ANCHOR_Boss` |
| `PROP_Cannon_Ming` | 432 | `Carriage`、`Barrel`（炮耳枢轴绕 X 俯仰，`FX_Muzzle` / `FX_Fuse` 是它的子物体）、`ANCHOR_Gunner` / `ANCHOR_Loader` | 明铁将军炮 + 木炮架，装药→装弹→点火 |
| `PROP_CannonEmplacement` | 1278 | `Platform`、`Ammo_Solid`（实弹）、`Ammo_Scatter`（散弹）、`Powder` + `Powder_Lid`、`ANCHOR_Cannon` / `_Gunner` / `_Powder` / `_Solid` / `_Scatter` | 2.8 m 方木平台，放在敌台炮位垫石上，炮放 `ANCHOR_Cannon` |
| `PROP_WaterWheel` | 1594 | `Frame`、`Wheel`（轮轴枢轴，绕 X 转，绞把随轮）、`Trough`、`ANCHOR_Turn`、`FX_Water` | 筒车式水轮，轮径 4.4 m；**轮底低于原点 0.35 m**，放进渠里 |
| `PROP_GateBar` | 1232 | `Door_L`（+X 侧）/ `Door_R`（枢轴在门轴，绕 Z 开）、`Bar`（门闩，向上抬）、`Bar_Sockets`、`Broken`（撞破态）、`FX_RamHit`、`FX_Splinters` | 配 `BLD_Wall_GateBase` 门洞宽 4.4、门高 4.2；原点在门洞地面中心，外侧 -Y。门破：隐藏 Door_L/R + Bar，显示 Broken |
| `PROP_Chevaux` | 844 | `Juma`（拒马枪，原点）、`Lujiao`（鹿角，+X 3.6 m）、`COL_Juma` / `COL_Lujiao` | 两件可分开摆 |
| `PROP_FireOil` | 694 | `Stove`、`Cauldron`（倾倒枢轴，绕 X 朝 -Y 倒）、`FX_Fire` / `FX_Pour`（随锅）/ `FX_Smoke`、`ANCHOR_Tip` | 熬火油（军令「火油」）；摆在走道上，-Y 朝城外 |
| `PROP_BucketSand` | 1158 | `Bucket`（单桶可拿，`ANCHOR_Handle`）、`Bucket_Row`、`Sandbags`、`Sandbag`、`SandBasket` | 第 4 波灭火 / 赤焰 P1「用水桶灭 3 处火」 |
| `PROP_Stretcher` | 1278 | `Stretcher`、`Wounded`（平躺伤兵静态网格）、`Bandage`、`ANCHOR_Bearer_Front/Back` | 伤兵用人物生成器摆好姿势后烘成静态网格 |
| `ENV_WallBreach` | 1508 | `Breach_Wall`、`Rubble` + `COL_Rubble`（坡道）、`Scorch`、`Burning_Debris`、`FX_Fire_1..3` / `FX_Smoke` / `FX_Dust`、`ANCHOR_BreachTop` / `ANCHOR_RubbleFoot` | **替换** `BLD_Wall_Seg`（同位置同朝向，8 m 模数、墙高 7、走道 7.08、垛口同款）：中段塌到约 3.2 m、墙外瓦砾坡可爬。`Scorch` 贴合原墙外立面/走道/垛墙，**单独叠在完好的 `BLD_Wall_Seg` 上就是「火起」状态** |

墙体材质沿用 `M_Wall_Stone` / `M_Wall_Top` / `M_Stone_Base`，年代材质库照样生效。

## 动作

所有片段都是 Humanoid，用出动作的那个模型骨架做；**A/B 变体共用**（例如 `EN_Wokou_Sword_B` 直接用 `EN_Wokou_Sword_A@EN_SwordAttack1`）。片段名即建议的 Animator 状态名（带 `EN_` / `BS_` 前缀，不会和别的幕撞名）；名字含 `Loop` / `Walk` 的自动循环。24 fps，根运动按现有导入设置烘进姿势。

| 刀兵 一段斩 0/11/14/18 | 弓兵 射箭 0/8/18/28 |
|---|---|
| ![](images/act3/anim_sword_attack1.jpg) | ![](images/act3/anim_bow_shoot.jpg) |
| 火罐兵 投掷 0/6/13/17/23 | 盾兵 冲撞 0/10/21、格挡、推进 |
| ![](images/act3/anim_pot_throw.jpg) | ![](images/act3/anim_shield.jpg) |
| 赤焰 下劈 / 三连 | 赤焰 扔罐 / 破架势 |
| ![](images/act3/anim_chiyan_chop_combo.jpg) | ![](images/act3/anim_chiyan_throw_stagger.jpg) |
| 鬼倭 薙刀横扫 / 野太刀 / 跪地 | 被处决、死亡（侧面） |
| ![](images/act3/anim_guiwo_weapons.jpg) | ![](images/act3/anim_death_executed.jpg) |

**动画事件**：管线还不能把事件写进 FBX，请 A 在团结的 clip 导入设置里按下表加（帧号 = 24 fps 原帧）。

| 文件 `<模型>@<动作>` | 帧数 | 建议事件 | 备注 |
|---|---:|---|---|
| `EN_Wokou_Sword_A@EN_SwordIdleLoop` | 48 | — | 中段架势，循环 |
| `…@EN_SwordAttack1` | 32 | `AttackHit`@14 | 举刀前摇 0–11（0.45 s）；斜斩 |
| `…@EN_SwordAttack2` | 28 | `AttackHit`@9 | 从一段收势起反撩；连斩 = Attack1 → Attack2 |
| `…@EN_SwordHit` | 20 | `Stagger`@3 | 通用受击 |
| `…@EN_SwordDeath` | 36 | `Death`@24 | 跪倒 → 扑地；14 帧左右松手丢刀 |
| `EN_Wokou_Archer_A@EN_BowIdleLoop` | 48 | — | 侧身持弓 |
| `…@EN_BowShoot` | 40 | `AttackHit`@28 | 8 扣箭（显示箭）、18–26 满弓（弓切 `String_Drawn`）、28 放箭（隐藏手上的箭、生成投射物） |
| `…@EN_BowHit` / `@EN_BowDeath` | 20 / 36 | `Stagger`@3 / `Death`@24 | |
| `EN_Wokou_FirePot_A@EN_PotIdleLoop` | 48 | — | 右手托罐 |
| `…@EN_PotThrow` | 34 | `AttackHit`@17 | 6 左手点引信（`FX_Fuse` 点燃），13 后引，17 出手（隐藏手上罐、生成投射物） |
| `…@EN_PotHit` / `@EN_PotDeath` | 20 / 36 | `Stagger`@3 / `Death`@24 | |
| `EN_Wokou_Shield_A@EN_ShieldIdleLoop` | 48 | — | |
| `…@EN_ShieldBash` | 36 | `AttackHit`@21 | 蓄力 0–17（0.7 s），21 撞出 |
| `…@EN_ShieldBlockLoop` | 24 | — | 举盾格挡，循环 |
| `…@EN_ShieldWalk` | 32 | `Footstep`@0、@16 | 举盾推进，原地踏步，配 0.14 m/s 根速度 |
| `…@EN_ShieldHit` / `@EN_ShieldDeath` | 20 / 36 | `Stagger`@3 / `Death`@24 | 重击/绕后破防用 Hit |
| `BOSS_Chiyan@BS_ChiyanIdleLoop` | 48 | — | 横斧喘气 |
| `…@BS_ChiyanAxeChop` | 44 | `AttackHit`@18 | 前摇 0–14；18–28 斧卡地（破绽）；也用来「砍水闸」 |
| `…@BS_ChiyanAxeCombo3` | 60 | `AttackHit`@15 / 25 / 44 | 头目模板 2 快 1 慢，红光 0–12；44 之后 1.8 s 破绽 |
| `…@BS_ChiyanAxeSpin` | 48 | `AttackHit`@16 / 22 / 28 | 旋斧一圈半，P3「没侦察 → 多 1 招」 |
| `…@BS_ChiyanPotThrow` | 34 | `AttackHit`@17 | P1 左手扔火罐（火罐挂 `SOCKET_Hand_L`），斧在右手 |
| `…@BS_ChiyanLeap` | 44 | `AttackHit`@28 | 原地起跳砸地；跳上码头的水平位移由脚本在 10–28 帧移动 |
| `…@BS_ChiyanPhaseChange` | 48 | `PhaseChange`@20 | 在 20 帧切阶段子物体 |
| `…@BS_ChiyanWeakHit` | 30 | `Stagger`@3 | 背包弱点被打，前扑 |
| `…@BS_ChiyanStaggerLoop` | 48 | — | 架势破：单膝跪、拄斧，处决窗口 |
| `…@BS_ChiyanExecuted` | 48 | `Death`@30 | 从跪姿被处决倒地（不血腥） |
| `BOSS_Guiwo@BS_GuiwoIdleLoop` | 48 | — | 八相架势（三种武器通用） |
| `…@BS_GuiwoCombo3` | 64 | `AttackHit`@15 / 23 / 46 | 太刀：红光 0–12，下劈、斜斩、蓄力横扫（2 快 1 慢） |
| `…@BS_GuiwoIaiDash` | 44 | `AttackHit`@14 | 突进居合横斩（约 0.8 m 前冲，烘在姿势里，结束回原位） |
| `…@BS_GuiwoNaginataSweep` | 48 | `AttackHit`@18 | P2 薙刀低扫 |
| `…@BS_GuiwoNaginataThrust` | 40 | `AttackHit`@16 | P2 薙刀突刺 |
| `…@BS_GuiwoNodachiCleave` | 56 | `AttackHit`@26 | P3 野太刀重劈，26–38 破绽 |
| `…@BS_GuiwoPhaseChange` | 48 | `PhaseChange`@20 | |
| `…@BS_GuiwoWeakHit` | 30 | `Stagger`@3 | |
| `…@BS_GuiwoStaggerLoop` | 48 | — | 跪地拄刀，处决窗口 |
| `…@BS_GuiwoExecuted` | 48 | `Death`@30 | |

走/跑仍用共用的 `CH_WangYan_1941@Walk/Run`。

## 给 A 的接入说明

- **挂武器**：武器 prefab 作为 `SOCKET_Hand_R/L` 的子物体，`localPosition = 0`、`localRotation = 0`。插槽和武器用同一套轴约定（+Z = 刃/弓臂方向，-Y = 刃口/正面），已在 Blender 里把两个 FBX 回导、按「子物体零变换」拼起来验证过方向一致。双手武器只挂右手，左手动作里已经握在柄后（倭刀 0.17 / 太刀 0.21 / 野太刀 0.30 / 大斧、薙刀 0.45 m）。
- **Humanoid 注意**：挂在手骨下的插槽空物体是 FBX 里的普通节点，Avatar 不受影响。握持姿势是 IK 解出来的，重定向到 B 变体时位置会略有偏差，看着不对就微调武器的局部偏移。
- **Boss 阶段**：`PhaseChange` 事件里按上面的显隐规则切子物体，同时换武器 prefab（鬼倭）。赤焰的弱点 `WEAK_Chiyan_Pack` 一直存在，「侦察过」只决定要不要高亮。
- **新 Animator 状态**：上表所有片段名，建议做成每个兵种 / Boss 自己的 Override Controller 或子状态机；循环片段（Loop/Walk）可以当 locomotion 的替换待机。
- **道具状态**：`PROP_GateBar` 的 Door_L/R 绕局部 Z（团结 Y）转开；Bar 向上抬约 0.5 m 后隐藏；`PROP_Cannon_Ming` 的 Barrel 绕 X 俯仰（建议 -5°～+15°）；`PROP_WaterWheel` 的 Wheel 绕 X 转（3 圈 = 转水轮完成）；`PROP_BatteringRam` 的 Ram 绕 X 摆 ±25°。
- **对位**：云梯放墙段局部 (x, -5.25, 0)；城墙破口直接替换墙段；火船下沉 0.45 m；炮放炮位 `ANCHOR_Cannon`；炮位放敌台垫石（`BLD_Wall_DiTai` 的 (0, -6.5, 7.08) 附近）。
- 部分道具原点按「握把 / 吃水 / 轮轴」设，生成时会出 `[WARN] 模型最低点 z<0`，是有意的（武器、弓、盾、水轮、跪姿片段第 0 帧）。

## 重新生成

```bash
cd /Users/anruikang/Downloads/game_race
# 列出本模块全部资产
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/build_yongchang.py -- --list | grep -E "EN_|BOSS_|PROP_(EN|BS)_|PROP_(SiegeLadder|BatteringRam|FireShip|Cannon|WaterWheel|GateBar|Chevaux|FireOil|BucketSand|Stretcher)|ENV_WallBreach"
# 重新生成其中几个（改过的资产要加 --force）
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/build_yongchang.py -- --only EN_Wokou_Sword_A,EN_Wokou_Sword_A@EN_SwordAttack1 --force
```

动作的姿势写在 `rupu_enemy.py` 的 `clips_*()` 里：`Poser` 先把描述（髋/脊柱角度、脚踝 IK 目标、武器握点与刃向）解成每根骨骼的旋转，再打关键帧。改招式就改那里的关键帧描述。

## 还没做

- VFX（血、火、水、烟、破片、箭矢、墙破/门碎/火势蔓延）：按分工在团结里做，挂点都已留好。
- 动画事件要在团结里手动加（见上表）。
- 敌人和 Boss 用的都是纯色材质，没做贴图和表情贴图；B 变体没有单独出动作（共用 A 的）。
- 义师 `CHR_Militia`（P1，复用敌人骨架）不在本次范围。
