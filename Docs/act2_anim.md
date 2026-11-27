# 第二幕补缺口：动作与手持道具

依据：[`第二幕_策划对照与建模缺口.md`](第二幕_策划对照与建模缺口.md) §1（拍 1 开工、拍 5 王宅、拍 6 殉难）、§4（王沛 / 王叔杲 / 王德）、§7，以及 [`入谱_第二幕_筑堡_策划案_v1.md`](入谱_第二幕_筑堡_策划案_v1.md) 拍 1、§3、§5、§9。补的是 [`act2_assets.md`](act2_assets.md) 里「还没做」的拆梁、饭篮、明代灯笼，以及试炮、看船、1v3 枪术、义师出战、护民、遗体、族老甩袖。

生成脚本：`Tools/blender/rupu_a2_anim.py`（`build_yongchang.py` 自动导入）。没有改 `rupu_char.py` / `rupu_act2.py`。

## 动作（Humanoid 共用，资产名 `CH_WangYan_1941@<动作>`）

写法与 `rupu_act2.py` 的 `A2_GESTURES` 相同，经 `rupu_char.GESTURE_HOOKS` 注册，并套用 `rupu_act2._grounded` **自动落地**（每个关键帧都量网格最低点，脚、膝、背刚好贴地，生成时逐帧检查最低点都是 0.000）。本模块另外做了两件事：

- **手臂求解**：拿道具的手（枪、撬杠、火绳杆、短刀）不靠手摆角度，而是给出握点和杆的方向，由一个小的 FK + 坐标下降求解器反算上臂、前臂、前臂旋转和腕偏。握点就是 `rupu_enemy` 的 `SOCKET_Hand_*` 位置，虎口方向是道具的 +Z。双手持杆时，两手都落在同一根杆上，误差 ≤ 5 cm。
- **弓步放平双脚**：`lunge()` 根据前腿姿势自动求后腿屈膝，让两只脚踝一样高、两脚放平，不会出现一只脚贴地、另一只悬空。

| 动作 | 帧（24 fps） | 谁 / 哪一拍 | 说明 | 事件帧（建议） |
|---|---|---|---|---|
| `A2_PryBeam` | 72 | 王叔杲·拍 5 王宅拆梁 | 双手斜握撬杠 → 举起，把爪头插进头顶前方约 2.1 m 的梁缝 → 往下猛压两下 → 梁落、撬杠一空 → 后退半步仰头看 → 站定 | `PryEffort`@24、`PryEffort`@38、`BeamFall`@44 |
| `A2_LookOutLoop` | 96（循环） | 王沛·拍 1 北门看船 | 右手搭凉棚遮在眉上远眺，左手扶住身侧立着的枪；重心左右慢慢换，头微微扫 | — |
| `A2_FireCannon` | 64 | 王沛·试炮 | 右手火绳杆探向左前方炮尾火门 → 点火 → 侧身扭开、左手捂耳、缩肩 → 炮响时人一震 → 回头看炮，站直 | `Ignite`@16、`AttackHit`@30（炮响） |
| `A2_SpearIdleLoop` | 48（循环） | 王沛·1v3 | 持枪戒备：左脚在前、左肩朝前，右手握在右胯、左手在前，枪尖略高过腰 | — |
| `A2_SpearThrust` | 30 | 王沛·1v3 | 回抽（6）→ 弓步直刺，后手推到前手边 → 收回 | `AttackHit`@12 |
| `A2_SpearSweep` | 36 | 王沛·1v3 | 右拧，枪头甩到右前（8）→ 向左横扫 → 收势 | `AttackHit`@15 |
| `A2_SpearParry` | 24 | 王沛·1v3 | 双手把枪杆横举到额前上方架住 → 顶一下 → 落回戒备 | `Parry`@5（格挡判定窗口 5–10） |
| `A2_SpearHit` | 20 | 王沛·1v3 | 胸口挨一下，上身后仰、枪尖挑起、前脚收半步 → 回戒备 | `Stagger`@3 |
| `A2_MilitiaCharge` | 28 | 王德 / 义师·出战 | 右手短刀高举、左手前指，压低身子，前脚一蹬，停在冲锋姿势（接 Run） | `Footstep`@16 |
| `A2_MilitiaSlash` | 26 | 王德 / 义师 | 刀举到右肩上方（7）→ 斜劈到左胯前 → 收回胸前 | `AttackHit`@11 |
| `A2_GuideCrowdLoop` | 32（循环） | 护民撤祠堂 | 右手指向前方（祠堂），身子半侧、回头看人群，左手一下一下往前招 | — |
| `A2_ShieldCivilianLoop` | 32（循环） | 护民撤祠堂 | 面朝来敌，两臂向后张开把人挡在身后，原地倒退。根节点每循环往后移约 0.7 m | — |
| `A2_FleeLoop` | 16（循环） | 平民 | 弯腰缩脖、双手捂住后脑，原地小跑 | — |
| `A2_CarryChildRunLoop` | 16（循环） | 平民妇人 | 双臂把孩子搂在胸前、身子前倾，原地小跑。孩子另外摆，贴在胸口 | — |
| `A2_CorpseLie` | 4（静态） | 王沛遗体 | 仰卧，头偏向右，两臂摊在地上，右膝微屈。枪单独摆在右手边地上。王德的遗体用 `A2_FallDead` 的末帧 | — |
| `A2_ElderObject` | 48 | 族老·拍 1 / 拍 5「以公谋私」 | 右手收到胸前，一拂袖甩开 → 下巴一抬，向右后转约 175° → 双手背到身后站定（停在末帧） | `Sleeve`@14 |

事件名里 `AttackHit` / `Stagger` / `Footstep` 是 CLAUDE.md 约定的；`PryEffort`、`BeamFall`、`Ignite`、`Parry`、`Sleeve` 是建议名，A 可以改。**管线还不能把事件写进 FBX**，请在团结的 clip 导入设置里按上表的帧号加（帧号是 24 fps 原帧）。

### 关键帧检查图

每行一个动作，每格一个关键帧，帧号标在右上角。白模用的是 `CH_WangYan_1941`。手上挂的是预览用道具，按插槽约定挂：枪、撬杠、火绳杆、短刀。双手杆由后手插槽瞄向前手插槽。

![王叔杲拆梁 / 王沛看船 / 王沛试炮](images/act2/anim_0_shugao_pei.jpg)

![王沛枪术：戒备 / 直刺 / 横扫 / 格挡 / 受击](images/act2/anim_1_spear.jpg)

![义师冲锋 / 劈砍 / 族老甩袖转身 / 王沛遗体](images/act2/anim_2_militia_elder.jpg)

![护民：引路 / 张臂护人倒退 / 护头小跑 / 抱孩子小跑](images/act2/anim_3_civilians.jpg)

侧视（检查撬杠角度、点火探身、弓步贴地和遗体贴地）：

![侧视](images/act2/anim_side.jpg)

## 手持道具（Props）

![撬杠 / 火绳杆 / 饭篮 / 明代灯笼](images/act2/anim_props.jpg)

| 资产 | 三角面 | 造型 | 原点 / 子物体 |
|---|---|---|---|
| `PROP_PryBar` | 120 | 1.25 m 八棱铁撬杠，缠麻握把，上端弯成分叉羊角爪，下端是扁錾口 | 原点在后手握点（离尾端 0.15 m），+Z 朝爪；`FX_Tip` 是爪尖 |
| `PROP_Linstock` | 480 | 1.2 m 木火绳杆，杆头双股铁叉夹着点着的火绳，余下的绳在杆上缠几圈 | 原点在握点，+Z 朝杆头；`FX_Match` 是火绳头（挂火星和烟） |
| `PROP_FoodBasket` | 872 | 圆竹提篮，两色篾圈，竹提梁。蓝灰盖布盖住后半个篮口，露出一碗青花碗盛的饭；布下还有一碗菜和一双筷子 | 原点在篮底中心；子物体 `Basket`、`Cloth`、`Bowl_1`（露出来的饭，可单独拿出递人）、`Bowl_2`；`ANCHOR_Grip` 是提梁顶的握点 |
| `PROP_MingLantern` | 712 | 竹竿提灯：带竹节的竿，竿头向前弯出挂钩，挂一盏鼓形竹骨纸灯笼，上盖、底托、红穗 | 原点在竿的握点，+Z 朝竿头。`Lantern` 是挂钩枢轴的子物体；`Lantern/Lantern_Face` 是灯面前方（-Y）±50° 的贴字面片，UV 0–1 占满，材质 `M_A2AN_LanternFace`，贴「王」字或其他字的贴图用它；`Lantern/FX_Glow` 是灯光挂点 |

撬杠、火绳杆、灯笼按 `rupu_enemy` 武器的约定，原点就是握点，所以生成时会报 `[WARN] 模型最低点 z<0`，这是有意的。饭篮原点在底面中心，报的 WARN 已经修掉。

## 给 A 的接入要点

1. **控制器不需要另外登记**：`RupuCharacters.AllGestures()` 会扫描 `Assets/Art/Characters/CH_WangYan_1941@*` 目录，自动把新动作收进 `AC_Humanoid_Locomotion` 作为同名状态。导入 FBX 后，重建一次控制器即可（菜单或 `RupuCharacters.ControllersCLI`）。脚本用 `CrossFade("A2_SpearThrust")` 这样的方式进入。
2. **循环**：名字带 `Loop` 的由导入器自动设成循环。`A2_PryBeam`、`A2_FireCannon`、`A2_ElderObject`、`A2_MilitiaCharge`、`A2_CorpseLie` 都停在末帧，保持姿势时不要自动回 Locomotion。
3. **根运动已经烘进姿势**：`A2_ElderObject` 末帧整个人转了约 175°。接下来要走开的话，把角色根节点旋转 +175°（向右后），再切回 Idle / Walk。`A2_ShieldCivilianLoop` 是原地倒退，由脚本按每循环约 0.7 m 往后移。
4. **道具挂法**：在人物右手骨（或左手骨）下建一个空物体当插槽，朝向和 `rupu_enemy.socket_rest` 一样（+Z 是虎口方向，T 姿势时朝前；-Y 是指节方向）。道具做它的子物体，局部位置和旋转清零。具体搭配：
   - 枪 `PROP_Spear_Pei`：原点在枪尾，挂到右手时沿 +Z 后移 0.5 m（握在枪尾往前 0.5 m 处）。`A2_LookOutLoop` 用左手扶枪，沿 +Z 后移 1.0 m，枪尾正好落地。
   - 双手杆（枪、撬杠）：建议在后手插槽上加 Aim / LookAt 约束，瞄向前手插槽。这样杆一定穿过两只手；检查图就是这么挂的。
   - 火绳杆 `PROP_Linstock`、短刀直接挂右手。
   - 灯笼 `PROP_MingLantern`：挂手后，每帧把 `Lantern` 的世界旋转扶正（或加 HingeJoint），灯笼就会自然下垂。
   - 饭篮：`ANCHOR_Grip` 对齐手部插槽。
5. **试炮站位**：炮尾火门（`PROP_Cannon_Ming` 的 `FX_Fuse`）应在王沛脚底原点的左 0.5 m、前 1.0 m、高 0.87 m，第 16 帧火绳头正好碰到火门。炮响用第 30 帧：触发 `FX_Muzzle` 和炮管后坐。
6. **拆梁**：梁缝在人物前方约 0.9 m、高约 2.1 m。第 44 帧让梁木（`ENV_WangHouse` 的梁木实体）落下。
7. **遗体**：王沛用 `A2_CorpseLie`，王德用 `A2_FallDead` 的末帧（第 40 帧）。断枪和战后现场由另一位同事做。

## 重新生成

```bash
cd /Users/anruikang/Downloads/game_race
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/build_yongchang.py -- \
  --only PROP_PryBar,PROP_Linstock,PROP_FoodBasket,PROP_MingLantern,CH_WangYan_1941@A2_PryBeam,CH_WangYan_1941@A2_SpearThrust,... --force
```

名单见 `rupu_a2_anim.recipes()`。改动作就改 `rupu_a2_anim.py` 里的 `g_*` 函数：握点和杆的方向写在 `wield()` / `reach()` 的参数里，求解器会自己算手臂。`REACH_LOG` 记录每次求解的握点误差，调试时可以打印出来看。

## 没做 / 限制

- 动画事件没写进 FBX（管线不支持），帧号见上表。
- `A2_SpearComboLoop` 没做（任务说不必）。连招可以由 Thrust → Sweep 用 CrossFade 串起来。
- 手只有一整块，没有手指骨。握杆靠插槽和 Aim 约束，手形不会真的握住。
- 抱孩子小跑没有绑孩子模型。孩子 `NPC_MingChild` 需要另外摆一个蜷缩姿势贴在胸口，或者用一个包袱道具代替。
