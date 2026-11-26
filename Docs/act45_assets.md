# 第四幕 1941 藏谱/寻谱 + 第五幕 1945 修谱/巡游 · 资产

依据：[`入谱_当前建模缺口清单.md`](入谱_当前建模缺口清单.md) 第五、六节 + 第七节 `PROP_Genealogy_System` 的模型部分，策划案 v3.0 第四段「藏谱与巡游」。
全部是程序化白模（低模、纯色材质），生成器 `Tools/blender/rupu_act45.py`。材质前缀：第四幕 `M_A4_*`，第五幕 `M_A5_*`，人物 `M_A5C_*`。破祠沿用内景的语义材质（`M_Plaster` 等），年代材质库照样生效。

![破祠俯视（含屋顶）：正厅屋顶塌洞](images/act45/ruin_top_roof.jpg)

## 对照表

| 清单 ID | 资产 | 状态 | 三角面 |
|---|---|---|---|
| `ENV_Hide_Wall` | `ENV_Hide_Wall` | ✅ | 1.3k |
| `ENV_Hide_Well` | `ENV_Hide_Well` | ✅ | 0.8k |
| `ENV_Hide_Plaque` | `ENV_Hide_Plaque` | ✅ | 0.3k |
| `ENV_Shrine_Ruin_1941` | `ENV_Shrine_Ruin_1941` | ✅ | 20.6k（含碰撞） |
| `PROP_FatherPhoto` | 已有（第一幕），没有重做 | ✅ | — |
| `PROP_ScatteredPages` | `PROP_ScatteredPages`（12 张） | ✅ | 1.3k |
| `PROP_SearchDebris` | `PROP_SearchDebris` | ✅ | 1.1k |
| `PROP_JapaneseSearchKit` | `PROP_JapaneseSearchKit` | ✅ | 0.5k |
| `VFX_Dust` | 不做（主代理在团结里统一做），模型上留了 `FX_Dust*` | ⚠️ | — |
| `ENV_RepairTable` | `ENV_RepairTable` | ✅ | 0.7k |
| `PROP_BrushInk` | `PROP_BrushInk` | ✅ | 0.4k |
| `PROP_Seal` | `PROP_Seal` | ✅ | 0.3k |
| `PROP_Genealogy_Final` / `PROP_Genealogy_System`（模型） | `PROP_Genealogy_Final` | ✅ | 0.5k |
| `PROP_Offering` | `PROP_Offering` | ✅ | 1.5k |
| `PROP_ParadeFlag` 10—20 | `PROP_ParadeFlag_A/B/C` 三种形制，按 10—20 份实例摆 | ✅ | 158 / 246 / 164 |
| `PROP_DragonLantern` | `PROP_DragonLantern` | ✅ | 1.9k |
| `PROP_DrumGong` | `PROP_DrumGong` | ✅ | 1.0k |
| `CHR_WangYan_1945` | `CH_WangYan_1945` | ✅ | 1.1k |
| `CHR_WangBingzhi_1945` | `NPC_WangBingzhi_1945` | ✅ | 1.2k |
| `CHR_ParadeCrowd` 6 循环 | `NPC_ParadeCrowd_A..F` + 6 个动作 | ✅ | 1.0—1.2k |
| `ENV_TempleFront` | `ENV_TempleFront` | ✅ | 6.0k |
| `ENV_Street_Parade` | `ENV_Street_Parade`（9 m 平铺模块） | ✅ | 2.0k |

## 第四幕 · 藏谱点

![三处藏谱点：夹墙、井、匾后（灰色胶囊是 1.75 m 参考人）](images/act45/hide_points.jpg)

三个资产都直接对着祠堂内景已有的锚点 `ANCHOR_hide_wall / hide_well / hide_plaque` 做。每个资产自带 `ANCHOR_Hide`（谱放的位置）、`ANCHOR_Use`（玩家站位）和 `FX_Dust`。

| 资产 | 造型 | 子物体（枢轴） |
|---|---|---|
| `ENV_Hide_Wall` | 后堂西墙内侧加砌的一道「夹墙」，2.4 × 2.6 m、厚 0.4 m。下半部灰皮剥落，露出砖，中间有一组松砖，后面是夹层空腔。**原点在贴墙面（y=0）的底边中点**，几何全部在 -Y 一侧 | `Wall`、`Brick_Loose`（2 × 5 块砖连成一块，枢轴在正面中点，沿 -Y 抽出 0.3 m 即露洞）、`NOCOL_Crumbs` |
| `ENV_Hide_Well` | 八角石井栏 + 井台 + 地下 2.2 m 的井筒（水面在 -1.7 m）+ 辘轳 + 吊桶。井栏正面那块外半栏石可以抽出，里面是暗格 | `Well`、`Windlass`（轴心，绕 X 转）、`Rope`（顶端，可拉长 Z）、`Bucket`（提梁顶）、`Rim_Stone`（沿 -Y 抽出）；另有 `ANCHOR_Hide_Bucket`，对应把谱放进吊桶沉井的结局 E「井底之谱」 |
| `ENV_Hide_Plaque` | 5.0 × 1.15 m 大匾 + 背后 13 cm 深的凹槽 + 一架靠墙竹梯。正好罩住内景原有的大匾 | `Frame`、`Plaque`（枢轴在上沿铰链，绕 X 让下沿往外掀约 35°）、`Ladder`；另有 `ANCHOR_Climb_Top` |

## 第四幕 · 1941 冬破祠

![破祠俯视（去掉屋顶）](images/act45/ruin_top.jpg)
![正厅：断梁、瓦砾雪堆、倒散的牌位](images/act45/ruin_hall.jpg)

`ENV_Shrine_Ruin_1941` 调用 `build_interiors.r_int_ancestral()`（没有改它），先生成完整的祠堂内景，再在上面做破坏。**原点、尺寸、全部 `ANCHOR_*` 名字和位置都与 `BLD_INT_AncestralHall` 一致**，在同一个位置整体替换即可。

- 正厅屋顶 `ROOF_Main` 切出一个约 7 × 5 m 的不规则塌洞，下面的梁架同步断开，断头已封口。洞口边垂着断椽，4 根梁斜插到地面。`ROOF_*` 仍然可以整体隐藏。
- 右侧前排金柱 (3.4, 0.2) 倒地，成为单独物体 `RUIN_Column`；它在 `COL_Hall` 里原有的碰撞已删除，新的碰撞放在 `COL_Ruin`。
- `INT_Altar` 换成 `RUIN_Altar`：供桌向前翻倒、香案侧翻、香炉滚倒、烛台倒地、空谱匣的盖子甩开、蒲团踢散。
- `INT_Tablets` 换成 `RUIN_Tablets`：大约一半还立着（有歪的、有断的），其余倒在台沿上或掉到地上；王叔杲公的大牌位倒了，王沛公的还立着。`INT_Tablet_WangShiqing` 保持原样。
- 大匾从墙上砸落，断成两截（`RUIN_Plaque`）。
- `RUIN_Debris`：塌洞下的瓦砾堆、前廊下的碎瓦、碎窗格；门厅里倒着一扇门板。
- `NOCOL_RUIN_SnowAsh`：塌洞下积雪，内院、廊下、后天井有雪，供桌一带有冷灰，墙脚积灰。
- 新增锚点：`ANCHOR_search_page_01..12`（12 个散页落点，可放 `PROP_ScatteredPages` 的页）、`ANCHOR_search_photo`（后堂谱柜脚下，放 `PROP_FatherPhoto`）、`ANCHOR_search_case`（空谱匣）、`ANCHOR_cam_ruin`。
- 特效挂点：`FX_SnowFall`（塌洞上方）、`FX_Dust_Hall / Rear / Gate`。

## 第四幕 · 道具

![散页、废墟散布件、日军搜查工具](images/act45/act4_props.jpg)

- `PROP_ScatteredPages`：`Page_01..12`。种类有平摊、对折（半页立起）、烧边（焦黄晕 + 焦黑边）、沾泥（含鞋印）、撕角、卷边。每页原点都在页中心并落地，可以单独拿起、单独摆放。
- `PROP_SearchDebris`：`Rubble_Pile`（碎砖瓦堆）、`Ash_Pile`（灰烬堆，带焦木和烧纸）、`Beam_Broken`（劈裂的断梁）、`Tiles_Scatter`（散落碎瓦）、`Planks`（断板一摞）、`Snow_Patch`（积雪片），各自原点在底面中心。
- `PROP_JapaneseSearchKit`：`Flashlight`（方头军用手电，`FX_Flashlight` 在灯口）、`Crowbar`（铁撬）、`Sack`（麻袋）、`Ledger` / `Ledger_Open`（登记簿合 / 开）、`Seal_Strip`（交叉封条，0..1 UV）。刺刀已经在 `PROP_JpRifle` 里，没有重复做。

## 第五幕 · 修谱道具 + 巡游道具

![第五幕道具：路祭、文房、印章、族谱终版、锣鼓、牙旗、长幡、龙灯、修谱长案](images/act45/act5_props.jpg)

| 资产 | 子物体 / 挂点 |
|---|---|
| `ENV_RepairTable` 修谱长案 2.6 × 0.8 × 0.82 | `Table`（含毛毡）、`Bench`、`Ruler_1/2`（铜压尺）、`Paste_Bowl`（浆糊碗 + 刷）、`Page_Repair_1..3`（有缺口、补了新纸，0..1 UV）、`Paper_Stack`、`Lamp`；`ANCHOR_Writer`（在 -Y 一侧）、`ANCHOR_Book`、`ANCHOR_BrushInk`、`ANCHOR_Seal`；`FX_Lamp`、`FX_Ink` |
| `PROP_BrushInk` 文房 | `Brush`、`Brush_Small`（原点在笔杆中点）、`BrushRest`（山形笔架）、`Inkstone`（带墨池）、`InkStick`、`WaterDropper`；`FX_InkDrip` |
| `PROP_Seal` 宗族印 | `Seal`（卧兽钮方印，原点在印面中心，可单独拿）、`SealPad_Box`（含红印泥）、`SealPad_Lid`、`Stamp_Mark`（盖好的红印，0..1 UV，可换印文贴图）；`FX_Stamp` |
| `PROP_Genealogy_Final` 修好的族谱 | 布局和名字与 `PROP_Genealogy` 一致：`Book_Closed`（整本厚度、新靛蓝书衣、新题签）、`Book_Open`、`Case` + `Case_Lid`（枢轴在后沿）、`Ribbon`（红绸带）；**`Slot_1..8`** 是摊开页上的八条竖格（0..1 UV），右页从右到左是 1—4，左页是 5—8；`FX_Glow` |
| `PROP_Offering` 路祭 | `Table`（红桌围）、`Pig`、`Chicken`、`Fish`（三牲，各带盘）、`Peaches`（面桃一座 11 个）、`Candle_L/R`、`PaperMoney`、`Censer`；`FX_Candle_L/R`、`FX_Incense`、`ANCHOR_Kneel` |
| `PROP_ParadeFlag_A/B/C` 姓氏旗 | A 大方旗（杆高 4.6 m，旗面 1.0 × 2.2）、B 三角牙旗（3.8 m，火焰锯齿边 `Fringe`）、C 长幡（3.4 m 丁字杆，燕尾，`Streamers`）。都有 `Pole` 和 `Cloth`（旗面单独，0..1 UV，背面镜像后也是正字），杆底在原点；`ANCHOR_Grip` 在 1.1 m |
| `PROP_DragonLantern` 拼字龙灯 | 龙头朝 -Y，龙身沿 +Y 排开，节距 1.25 m：`Head`、`Seg_01..08`、`Tail`、`Pearl`（龙珠），**原点都在各自提杆底**；`Seg_NN_Face` 是每节两侧的灯面（0..1 UV，换字，八节拼一句）；`ANCHOR_Carrier_00..09`；`FX_Head_Light`、`FX_Seg_NN_Light`、`FX_Pearl_Light` |
| `PROP_DrumGong` 锣鼓 | `DrumFrame`（两根 2.4 m 抬杠）、`Drum`、`Drumstick_L/R`、`Gong`（枢轴在吊绳顶，可以摆动）、`Gong_Handle`、`Gong_Mallet`、`Cymbal_L/R` |

`PROP_Genealogy_System` 的模型部分由几件已有资产组合而成：半本谱、谱匣、散页、墨迹 = `PROP_Genealogy`（第一幕）；8 个关键页槽和完整谱 = `PROP_Genealogy_Final`；印章 = `PROP_Seal`；散谱 = `PROP_ScatteredPages`。

## 第五幕 · 巡游场景

![汤和庙前：彩门、香亭、旗座、观礼凳、灯笼串](images/act45/temple_front.jpg)
![俯视](images/act45/temple_front_top.jpg)
![巡游主街 9 m 模块](images/act45/street_parade.jpg)

- `ENV_TempleFront`：原点在广场中心，庙在 +Y 一侧（汤和庙建筑 `BLD_ROC_Temple` 是地图里的，这里没有重做）。广场范围约 24 × 16 m，布置如下：
  - `Caimen` 彩门：在 -Y 入口，6.4 m 宽的三间扎彩牌楼，柱子缠红绿彩布。
  - `Caimen_Board` 门额：0..1 UV，可以换字。
  - `Xiangting` 香亭：带抬杠、小四坡顶，内置香炉，有 `FX_Incense`。
  - `FlagBases`：两侧共 8 对夹杆石，配 `ANCHOR_Flag_01..08`。
  - `Benches`：6 条观礼长凳，配 `ANCHOR_Bench_1..6`。
  - `NOCOL_Lantern_Lines`：灯笼串和三角彩旗串。
  - `COL_TempleFront`：碰撞。
  - 其他锚点：`ANCHOR_Offering`（放 `PROP_Offering`）、`ANCHOR_ParadeStart`、`ANCHOR_ParadeExit`、`ANCHOR_WangYan_Watch`、`ANCHOR_Elder_Watch`、`ANCHOR_cam_top`。
  - 鞭炮挂点：`FX_Firecracker_L/R`。
- `ENV_Street_Parade`：一段 9 m，沿 Y 方向（y ∈ [-4.5, 4.5]），首尾相接；街宽按地图主街 6 m 做，两侧竹竿在 x = ±3.35。
  - 子物体：`Poles`、`NOCOL_Bunting`（跨街彩旗串）、`NOCOL_Lanterns`（跨街灯笼串）、`FlagBases`（`ANCHOR_Flag_L1..L3 / R1..R3`）、`Banner_L/R`（沿街竖幅，0..1 UV，换字）、`COL_Street_Parade`。
  - 每段可以单独开关这几件来做变化。
  - 锚点 `ANCHOR_Path_In/Out`，挂点 `FX_Confetti`。

## 人物与动作

![人物：王砚 1945、王秉之 1945、巡游群众 A–F](images/act45/characters.jpg)

用 `rupu_char.build_character` 生成，配置在 `rupu_act45.A45_CAST`，扩展通过钩子注册（没有改 `rupu_char.py`）。全部是 22 骨 Humanoid，与第一幕共用动画。

| 资产 | 造型 |
|---|---|
| `CH_WangYan_1945` | 王砚 29 岁，同脸、同身高，换装：夏天浅灰白长衫、深色裤，袖口挽起（修谱用），**左臂黑纱**（为父亲戴孝），仍然斜挎相机包 |
| `NPC_WangBingzhi_1945` | 近 70 岁，比 1941 版更瘦更驼（矮 3 cm）。褪色灰褐长袍外罩黑马褂，戴瓜皮帽，白长须。拐杖用已有的 `PROP_Cane_Bingzhi` |
| `NPC_ParadeCrowd_A` | 举旗手：本白短褂、红头巾带、绑腿，腰前有旗兜 + 背带 |
| `NPC_ParadeCrowd_B` | 扛灯 / 舞龙手：靛蓝短褂、白毛巾包头、黄腰带、右肩垫布 |
| `NPC_ParadeCrowd_C` | 锣鼓手：深灰短褂、旧毡帽、斜挎锣带 |
| `NPC_ParadeCrowd_D` | 老人：灰绿长衫、灰短须、微驼，表情和善 |
| `NPC_ParadeCrowd_E` | 妇人：豆沙红袄、黑裙、低髻簪红绒花 |
| `NPC_ParadeCrowd_F` | 孩童：节庆红褂、冲天小辫、大头比例 |

六个群众共用一套 `_CROWD_BASE`（短褂、布鞋、红腰带），只换头饰、颜色和小配件，没有做成独立设计。

动作（`CH_WangYan_1941@A45_*`，24 fps，原地，没有根运动）：

![动作关键帧：抬旗、舞龙灯、敲锣、擂鼓、写字、盖印](images/act45/anims.jpg)

| 动作 | 用途 | 循环 |
|---|---|---|
| `A45_FlagWalkLoop` | 双手握竖直旗杆走路（举旗手） | 是，24 帧 |
| `A45_LanternWalkLoop` | 提杆举过头、杆头随步子画弧（舞龙；每节错开相位） | 是，32 帧 |
| `A45_GongLoop` | 左手提锣，右手敲（12 帧一下） | 是，24 帧 |
| `A45_DrumLoop` | 双槌交替擂鼓 | 是，20 帧 |
| `A45_WriteLoop` | 俯身站在案前写字，左手按纸，偶尔回砚舔墨 | 是，48 帧 |
| `A45_Stamp` | 取印 → 呵气 → 双手按下停住 → 收回 | 否，48 帧 |

## 给 A 的接入说明

- **破祠**：在 1941 冬的场景里，把 `BLD_INT_AncestralHall` 整体换成 `ENV_Shrine_Ruin_1941`（同原点、同朝向）。所有原来的 `ANCHOR_*` 都在。散页用 `ANCHOR_search_page_*` 摆，父亲照片放在 `ANCHOR_search_photo`。
- **藏谱点**放在 1941.4.28 的完整祠堂里：
  - 井：`ENV_Hide_Well` 放在 `ANCHOR_hide_well`，同时隐藏 `INT_Well`。
  - 夹墙：`ENV_Hide_Wall` 放在 `ANCHOR_hide_wall`，旋转让它的正面朝向祠堂内侧（东）。
  - 匾：`ENV_Hide_Plaque` 放在内景局部坐标 (0, 6.2, 0.9)。
  - 开合动作（抽砖、掀匾、抽栏石、摇辘轳）都靠旋转或平移固定名字的子物体，不需要骨骼。
- **换字**：`Cloth`、`Seg_NN_Face`、`Caimen_Board`、`Banner_L/R`、`Slot_N`、`Stamp_Mark`、`Plaque`、`Page_Repair_N` 都是 0..1 UV，换贴图就能换字。其余部件是 0.5—1 m 的盒式 UV。
- **新 Animator 状态**：在 `AC_Humanoid_Locomotion` 里加 6 个同名状态：`A45_FlagWalkLoop / A45_LanternWalkLoop / A45_GongLoop / A45_DrumLoop / A45_WriteLoop / A45_Stamp`，用法和第一幕一样，`CrossFade` 进入。
- **手持道具**（旗、龙灯节、锣、鼓槌、毛笔、印章）需要在团结里挂到手骨上。它们的握持点分别是：旗 `ANCHOR_Grip`；龙灯节的提杆底往上 1.0 m；毛笔和印章的物体原点。
- **舞龙**：10 个舞龙手各拿一节，各自播 `A45_LanternWalkLoop`，起始时间每人错开约 0.1 周期，节与节之间就会形成波浪。

## 重新生成

```bash
cd /Users/anruikang/Downloads/game_race
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/build_yongchang.py -- \
  --only ENV_Hide_Wall,ENV_Hide_Well,ENV_Hide_Plaque,ENV_Shrine_Ruin_1941,PROP_ScatteredPages,PROP_SearchDebris,PROP_JapaneseSearchKit,ENV_RepairTable,PROP_BrushInk,PROP_Seal,PROP_Genealogy_Final,PROP_Offering,PROP_ParadeFlag_A,PROP_ParadeFlag_B,PROP_ParadeFlag_C,PROP_DragonLantern,PROP_DrumGong,ENV_TempleFront,ENV_Street_Parade,CH_WangYan_1945,NPC_WangBingzhi_1945,NPC_ParadeCrowd_A,NPC_ParadeCrowd_B,NPC_ParadeCrowd_C,NPC_ParadeCrowd_D,NPC_ParadeCrowd_E,NPC_ParadeCrowd_F,CH_WangYan_1941@A45_FlagWalkLoop,CH_WangYan_1941@A45_LanternWalkLoop,CH_WangYan_1941@A45_GongLoop,CH_WangYan_1941@A45_DrumLoop,CH_WangYan_1941@A45_WriteLoop,CH_WangYan_1941@A45_Stamp \
  --force --preview <预览目录>
```

## 还没做

- 贴图：灯面字、旗面姓氏、匾字、印文、页槽的字都还没画。现在是纯色，UV 已经留好。
- `VFX_Dust`、雪、烛火、香烟这些特效只留了 `FX_*` 挂点，粒子由团结统一做。
- 破祠屋顶塌洞的断口只有正反两层面，没有做厚度，侧面看边缘是薄的，现在靠垂下的断椽遮挡。屋顶上没有铺雪。
- 龙灯节与节之间没有连接的布（节会各自运动，连布要做蒙皮）。
- 群众只有站姿 + 动作，没有做的部分：表情贴图；坐着观礼的姿势（长凳上有 `ANCHOR_Bench_*`，需要的话再加 sit 动作）。
