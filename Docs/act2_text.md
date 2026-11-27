# 第二幕 · 文字贴图：族约碑、族约木牌、义师名录、匾额、旗、灯笼

依据：[`第二幕_策划对照与建模缺口.md`](第二幕_策划对照与建模缺口.md) §5 P0「族约碑」「义师名录」「文字贴图」，§9 第五步第 1、3、4 项；条款和名录的规则见 [`入谱_第二幕_筑堡_策划案_v1.md`](入谱_第二幕_筑堡_策划案_v1.md) §6、§7、§9。

生成脚本是 `Tools/blender/rupu_a2_text.py`。它用的是「包装配方」：先调用原来的生成函数（`rupu_act2` / `rupu_ming_civic` 里的源码没有改），再在匾、旗、纸面前面 2–5 mm 处加一块贴字面片，或者换掉原来的「墨块」「刻块」几何。

- 文字用 Blender 文字对象渲染，字体取自 `/System/Library/Fonts/Supplemental/Songti.ttc` 中的宋体繁体（Bold 用于碑和匾，Regular 用于名录手写）。字形只烘进贴图，字体文件不入库、不分发；从 .ttc 拆出来的临时 .ttf 放在 `Builds/tmp/a2_text/`，这个目录被 git 忽略。
- 碑、匾、名录都是明代的东西，所以用繁体。排版是竖排、从右往左读；匾额是横排，同样从右往左。
- 贴图都是方形 PNG（1024 或 2048）。表面不是方形时，字在贴图里会被拉伸，贴回表面后恢复方正。材质是 Principled BSDF，Base Color 接贴图、默认值设为白色，所以导入团结后不会被乘暗。材质前缀 `M_A2T_*`。
- 原配方从 `build_yongchang.RECIPES` 里取，因此能接在前面模块的包装之后。后面的模块（`rupu_a2_site` / `rupu_a2_city` 等）如果也包装同一个资产，也应从 `RECIPES` 里取原配方，这样贴字不会被覆盖。

```bash
cd /Users/anruikang/Downloads/game_race
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/build_yongchang.py -- \
  --only ENV_Stele,PROP_Covenant,PROP_Roster,BLD_MING_AncestralHall,BLD_MING_GateTower,BLD_MING_HuanhaiLou,ENV_NorthGate_Build,ENV_WangHouse,PROP_Flag_Wang,PROP_Lantern_Wang --force
# 文档预览图（贴图着色近景，读上面生成的 .blend）
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/rupu_a2_text.py -- --shots <输出目录>
```

## 1. 族约碑 `ENV_Stele`

| | |
|---|---|
| ![](images/act2/text_stele.jpg) | ![](images/act2/text_stele_slots.jpg) |

预览图中，槽 1 已刻成第 1 条，槽 2 凿到第二下，刻的是第 3 条，槽 3 还是空白。

碑上已经刻好的内容是一块贴图（`NOCOL_TXT_Stele_Face`），原来的刻字方块已经删掉：

- 碑额（`NOCOL_TXT_Stele_Title`）：「王氏族約」2×2 排，右列「王氏」，左列「族約」。
- 总纲两列：「倭患日亟闔族築堡以衛桑梓」「約成刻石子孫世守毋敢有違」。
- 落款：「嘉靖三十九年春王氏合族公立」。
- 三个条款槽外面各有一圈细刻线，表示这里是留给条款的位置。

### 条款（策划案 §6，id 与 `clan_term_*` 的取值一致）

| id | 碑文（繁） | 意思 |
|---|---|---|
| 1 | 助築者免徭役三年 | 助筑者免徭役三年 |
| 2 | 守城死者祠中留名 | 守城死者，祠中留名 |
| 3 | 三更後不得開城門 | 三更后不得开城门 |
| 4 | 鹽場歸公牙行不得抽 | 盐场归公，牙行不得抽 |
| 5 | 寇至婦孺先撤入祠 | 妇孺先撤（倭寇来时妇孺先撤进祠堂） |
| 6 | 匠人日給雙糧 | 匠人日给双粮 |

### 凿碑三态：子物体方案

每个槽下面有 6 条 × 3 态 = 18 片子物体，再加原来的空白面。团结里只需要 SetActive，不用换材质：

```
Clause_1 / Clause_2 / Clause_3          （槽，右起；空物体，原点在槽中心）
  Clause_N_Blank                        空白石面（一直显示，在最底下）
  Clause_N_T{1..6}_Hit1                 第一下：前 1/3 的字刻成，第 2 个 1/3 只有斑驳凿痕和石屑
  Clause_N_T{1..6}_Hit2                 第二下：前 2/3 刻成，最后 1/3 是凿痕
  Clause_N_T{1..6}_Carved               第三下：全部刻成
```

![凿三下：第 4 条 Hit1 → Hit2 → Carved](images/act2/text_stele_states.jpg)

接入方法：开场时把每个槽的 18 片全部隐藏。玩家选中第 t 条、落到第 n 个槽后，按凿击节奏依次显示 `Clause_n_Tt_Hit1` → `Clause_n_Tt_Hit2` → `Clause_n_Tt_Carved`，显示下一态时隐藏上一态。每一下都对齐 `CH_WangYan_1941@A2_ChiselLoop` 第 10 帧的落锤，同时在 `FX_Chisel_n` 放火星。王砚站在 `ANCHOR_Carver`。三态的贴图是三张 6 列图集（每列一条），对应材质 `M_A2T_Stele_Hit1` / `M_A2T_Stele_Hit2` / `M_A2T_Stele_Carved`。凿痕用暗色凹刻颜色加斜光高光做出来，没有法线贴图。

## 2. 族约木牌 `PROP_Covenant`

![](images/act2/text_covenant.jpg)

族约共十章。`Board_01..06` 就是上面六条，可以选（排序同 id）；`Board_07..10` 是不上碑的四章：「敬祖宗睦族人」「子弟勤耕讀」「禁賭博鬥毆」「修譜毋遺一人」。每块牌的右上角用朱笔写章次「第一」到「第十」。原来的墨块已删掉，字贴在子物体 `NOCOL_TXT_Board_NN` 上，会跟着牌子一起拿起、放下。

## 3. 义师名录 `PROP_Roster`

![](images/act2/text_roster.jpg)

预览图的状态是：右页写了 11 个名字，第 10、11 列跳过，留下空白格，第 14 列写到一半。

**纸面**：纸纹、朱丝栏（已褪色）、双线边框，每页 15 列，分上下两栏。上栏写身份和名字，名字不论两字还是三字都拉到同样的长度。下栏写年岁和殁注，殁注用朱笔。读序是右页从外沿往书脊，然后左页从书脊往外沿，所以第 1 名在右页最右边，第 30 名在左页最左边。纸面贴在 `Roster_Open` 下面的 `NOCOL_TXT_Roster_PageR/L` 上。

**每个名字槽**：

```
InkRow_NN（NN = 01..30，空物体，在该列顶端）
  InkRow_NN_S1 .. _S4        这一列从上到下分 4 段，依次显示 = 书写进度（5 秒一名 → 每段 1.25 秒）
  InkRow_NN_Skip             空白格「□□□」：这一名被跳过，之后就一直显示它，不能再写（空行不能补）
  InkRow_29_Nameless_S1..S4  只有 29、30 两列有：王德、王沛的遗体没抢回（殉难段选「护民撤祠堂」），
  InkRow_30_Nameless_S1..S4  名字写成「無名」
```

- 所有片默认隐藏。写第 NN 名时按 1.25 秒一段依次显示 S1 到 S4。写的时候可以同时播 `A2_WriteLoop`，笔尖位置在 `InkRow_NN` 往下。
- 墨会变淡（策划案 §7）：另有 `T_PROP_Roster_InkFaded_D`，纸底与 Ink 完全一样，墨只剩 45%。隔天的名字，用 MaterialPropertyBlock 把那几片的 `_BaseMap` 换成这张；不要直接调材质颜色，否则分段片会比底下的纸面亮或暗，出现方块接缝。
- 贴图与材质对应：`T_PROP_Roster_Page_D`（空页）对应 `M_A2T_Roster_Page`；`T_PROP_Roster_Ink_D`（30 名写满）对应 `M_A2T_Roster_Ink`；`T_PROP_Roster_Skip_D` 对应 `M_A2T_Roster_Skip`；`T_PROP_Roster_Nameless_D` 对应 `M_A2T_Roster_Nameless`。几张贴图共用同一张纸底，所以分段片盖在纸面上看不出接缝。
- `Seal_Mark` 是盖印后显示的印迹，是一方白文「王氏宗祠」（贴图 `T_PROP_Roster_Seal_D`）。它的位置在左页下栏第 24–27 列的空处，这几列没有殁注。
- 合起来的名册 `Roster_Closed` 有题签「永昌義師名錄」（`NOCOL_TXT_Roster_Slip`）。

### 30 个名字（嘉靖年间永昌堡王氏族人与乡勇；王姓为主，夹几户帮工的外姓）

| # | 名录（繁） | 简体 | 身份 | 年岁 | 殁注（朱笔） |
|---|---|---|---|---|---|
| 1 | 王汝明 | 王汝明 | 乡勇 | 24 | |
| 2 | 王大順 | 王大顺 | 民夫 | 31 | |
| 3 | 王阿四 | 王阿四 | 民夫 | 19 | |
| 4 | 王叔通 | 王叔通 | 乡勇 | 28 | |
| 5 | 王二郎 | 王二郎 | 石匠 | 40 | |
| 6 | 陳阿福 | 陈阿福 | 民夫 | 35 | |
| 7 | 王汝良 | 王汝良 | 乡勇 | 22 | |
| 8 | 王福 | 王福 | 乡勇 | 26 | **北門歿**（随王沛出城断后） |
| 9 | 王小乙 | 王小乙 | 民夫 | 17 | **墜架歿**（工地坠落） |
| 10 | 王光祖 | 王光祖 | 夯匠 | 38 | |
| 11 | 林阿七 | 林阿七 | 木匠 | 33 | |
| 12 | 王汝貴 | 王汝贵 | 乡勇 | 25 | |
| 13 | 王三官 | 王三官 | 民夫 | 29 | |
| 14 | 王叔遠 | 王叔远 | 乡勇 | 30 | |
| 15 | 王阿狗 | 王阿狗 | 民夫 | 16 | |
| 16 | 王長春 | 王长春 | 铁匠 | 42 | |
| 17 | 王汝成 | 王汝成 | 弓手 | 23 | |
| 18 | 周大 | 周大 | 民夫 | 45 | |
| 19 | 王四九 | 王四九 | 民夫 | 50 | **石壓歿**（被石料压死） |
| 20 | 王叔達 | 王叔达 | 牌手 | 27 | |
| 21 | 王細弟 | 王细弟 | 民夫 | 18 | |
| 22 | 王汝忠 | 王汝忠 | 乡勇 | 21 | |
| 23 | 王阿保 | 王阿保 | 民夫 | 32 | |
| 24 | 王光明 | 王光明 | 石匠 | 36 | |
| 25 | 王大用 | 王大用 | 乡勇 | 29 | |
| 26 | 黃阿三 | 黄阿三 | 民夫 | 20 | |
| 27 | 王五十 | 王五十 | 民夫 | 34 | |
| 28 | 王汝和 | 王汝和 | 乡勇 | 24 | **巡海歿** |
| 29 | 王德 | 王德 | 义师 | 20 | **北門歿**（无名版：「無名」） |
| 30 | 王沛 | 王沛 | 义师 | 62 | **北門歿**（无名版：「無名」） |

- 「只记死者」时只写第 8、9、19、28、29、30 列，其余列留空，最后都会显示成 `_Skip`。
- 王德、王沛排在最后，因为殉难之后才写他们。`named_pei` / `named_de` 写原名；`nameless_2` 写 `_Nameless`。
- 王福是殉难段里第三个死的人（策划案 §9「三人无论怎么选都会死」）。
- 名字和身份都是虚构的演绎：族人名字用「汝 / 叔 / 光」几个字辈，民夫多用「阿某」、排行或数目字作名，这是明代常见的叫法。

## 4. 匾额 / 旗 / 中堂（包装明代建筑）

| 资产 | 子物体 | 内容 |
|---|---|---|
| `BLD_MING_AncestralHall` | `NOCOL_TXT_Gate`（门厅大门匾） | 王氏宗祠 |
| | `NOCOL_TXT_Hall`（正厅檐下） | 追遠堂 |
| `BLD_MING_GateTower` | `NOCOL_TXT_Gate_TongShi` / `_YingChuan` / `_ZhenShan`（上层门匾，三片前后叠放，各差 1.5 mm） | 通市門（北）/ 迎川門（南）/ 鎮山門（西）。三座城门共用一个模型，所以**团结里每座门只留对应的一片**。默认最前面的是通市门 |
| | `NOCOL_TXT_Inner`（底层穿堂匾） | 永昌堡 |
| `BLD_MING_HuanhaiLou` | `NOCOL_Plaque_Gate` + 字（匾板挂在二层檐枋正面） | 環海樓 |
| | `NOCOL_TXT_Flag_Front` / `_Back`（旗杆上的旗面） | 「王」字旗 |
| `ENV_NorthGate_Build` | `Closure` 下的 `NOCOL_TXT_Closure`（合龙石，跟着 Closure 一起显示和隐藏） | 右起：嘉靖庚申冬 / 北垣合龍 / 王氏闔族立 |
| `ENV_WangHouse` | `NOCOL_TXT_GateLintel`（门屋门额） | 世澤綿長 |
| | `NOCOL_TXT_Hall`（正厅明间横披下） | 敦本堂 |
| | `NOCOL_TXT_ZhongTang`（中堂匾） | 清白傳家 |
| | `NOCOL_TXT_Scroll`（中堂画） | 一个大「守」字，题款「嘉靖庚申叔杲書」，钤朱印 |
| | `NOCOL_TXT_Couplet_R` / `_L`（对联，面向中堂时右为上联） | 耕讀傳家久 / 詩書繼世長 |

| | |
|---|---|
| ![](images/act2/text_ancestral_gate.jpg) | ![](images/act2/text_ancestral_hall.jpg) |
| ![](images/act2/text_gatetower.jpg) | ![](images/act2/text_huanhai.jpg) |
| ![](images/act2/text_closure.jpg) | ![](images/act2/text_wanghouse_gate.jpg) |

![王宅中堂：匾、守字中堂、对联](images/act2/text_wanghouse_hall.jpg)

匾的做法是黑褐漆底，加木色边框和一道金线，字是褪金色，字面有剥落。各匾的位置靠「材质 + 位置」查找：在原物体里找 `M_Plaque` / `M_Flag` / `M_Paper` 面的连通块，取离提示坐标最近的那块。所以原模块就算挪动了几十厘米，贴字也能跟过去；如果找不到，会打印 `[a2_text] 找不到…` 并跳过，不会报错。

**环海楼的原匾被挡住了**：原匾在 y −3.86、z 6.8–7.2，正前方 0.55 m 处的檐枋（y −4.4..−4.1，z 6.85–7.15）把它几乎整块挡住。所以另做了一块匾板 `NOCOL_Plaque_Gate`（3.0 × 0.9 m），挂在檐枋正面，原匾留着没动。以后改 `rupu_ming_civic.r_huanhai` 时，如果把原匾挪到看得见的地方，就把 `PLAQUES` 里的 `HANG` 换回 `M_Plaque`。

## 5. 新道具

| 资产 | 三角面 | 子物体 | 说明 |
|---|---|---|---|
| `PROP_Flag_Wang` | 238 | `Pole`（夹杆石 + 4.6 m 杉杆 + 铜顶）、`NOCOL_Flag`（1.2 × 1.6 旗面，两面，带一点风吹的起伏）、`ANCHOR_FlagTop` | 义师「王」字旗：朱底、黑色火焰牙边、靠杆一侧黑旗袖、纸色圆心黑「王」。原点在夹杆石底中心，旗面从 x=0 往 +X 飘。**敌台用这面旗**：`BLD_Wall_DiTai` 是民国和明代共用的几何，不能直接加旗，所以由场景在敌台顶插这个道具。北门工地、城门也能用 |
| `PROP_Lantern_Wang` | 400 | `Lantern_Body`（纸面：篾骨、上下朱边、前后各一个「王」）、`Lantern_Caps`（上下木圈 + 提梁）、`Stick`（提杆，挂起来用时隐藏）、`ANCHOR_Hang`、`ANCHOR_Hold`、`FX_Light` | 明代纸灯笼，给 `NPC_MingWoman_B`（提灯）、祠堂门口、夜里记名的场景用。原点在灯底中心 |

| | | |
|---|---|---|
| ![](images/act2/text_flag.jpg) | ![](images/act2/text_huanhai_flag.jpg) | ![](images/act2/text_lantern.jpg) |

![合起来的名册题签](images/act2/text_roster_closed.jpg)

## 6. 贴图清单

| 资产目录 | 贴图 |
|---|---|
| `Environments/ENV_Stele` | `T_ENV_Stele_Face_D`（2048）、`T_ENV_Stele_Title_D`（1024）、`T_ENV_Stele_Clauses_{Hit1,Hit2,Carved}_D`（2048，6 列图集） |
| `Props/PROP_Covenant` | `T_PROP_Covenant_Boards_D`（2048，5×2 图集） |
| `Props/PROP_Roster` | `T_PROP_Roster_{Page,Ink,InkFaded,Skip,Nameless}_D`（2048，摊开两页）、`T_PROP_Roster_Seal_D`、`T_PROP_Roster_Slip_D`（1024） |
| `Buildings/BLD_MING_AncestralHall` | `T_BLD_MING_AncestralHall_{Gate,Hall}_D` |
| `Buildings/BLD_MING_GateTower` | `T_BLD_MING_GateTower_Gate_{TongShi,YingChuan,ZhenShan}_D`、`T_BLD_MING_GateTower_Inner_D` |
| `Buildings/BLD_MING_HuanhaiLou` | `T_BLD_MING_HuanhaiLou_{Gate,Flag}_D` |
| `Environments/ENV_NorthGate_Build` | `T_ENV_NorthGate_Build_Closure_D` |
| `Environments/ENV_WangHouse` | `T_ENV_WangHouse_{GateLintel,Hall,ZhongTang,Scroll,Couplet_R,Couplet_L}_D` |
| `Props/PROP_Flag_Wang`、`Props/PROP_Lantern_Wang` | `T_PROP_Flag_Wang_D`、`T_PROP_Lantern_Wang_D` |

建筑和匾额用 1024，碑、名录、木牌用 2048。

## 7. 没做的

- 沙盘上的文字：三议题纸卡 `Card_*`、牙签小旗都只有 2–5 cm，属于沙盘那一组的活，这里没碰。
- 田契 `PROP_Deed` 和图卷 `PROP_Blueprint` 的契文和图注、木名牌 `NameTag_*` 的名字、腰牌「沛」：这次的清单里没有列，几何上仍然是墨块。
- 建筑的 LOD（如果有）不带贴字面片，远处看不清字，也就没有必要带。
- 汤和庙、民居、店铺的匾和幌子：不属于第二幕的范围。
- 法线贴图：凿痕和金字的立体感都是画在颜色贴图里的。
