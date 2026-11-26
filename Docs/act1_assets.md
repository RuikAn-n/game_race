# 第一幕 1941 · P0 资产与场景接入

依据：[`入谱_当前建模缺口清单.md`](入谱_当前建模缺口清单.md) 第一节（P0）、[`入谱_第一幕_人物文本.md`](入谱_第一幕_人物文本.md)。
全部是程序化白模（低模、纯色材质），按 `CLAUDE.md` 的资产规范出 FBX，已在 `Data/asset_manifest.csv` 登记。

![主街：日军军官盘问王砚，菜摊、告示墙、横幅](images/act1/play_street_push.jpg)

## P0 完成情况

| 清单项 | 状态 | 资产 |
|---|---|---|
| 1.1 族老 `CHR_Elder` | ✅ | `NPC_ClanElder` + 手杖 `PROP_Staff_Elder`（不再借用王秉之） |
| 1.1 日本军官 | ✅ | `NPC_JpOfficer`（祠堂、街市各一个实例） |
| 1.1 日本兵 3 变体 | ✅ | `NPC_JpSoldier_A`（步枪兵）/ `_B`（搜捕兵）/ `_C`（巡逻兵） |
| 1.1 三派 | ✅ | `NPC_ClanJiao` / `NPC_ClanShao` / `NPC_ClanCang`（见 [characters.md](characters.md)） |
| 1.1 小贩 2 变体 | ✅ | `NPC_VendorVeg`（菜贩）/ `NPC_VendorGoods`（杂货） |
| 1.1 街坊/族人 6—8 模块 | ✅ 8 个 | 族亲 `NPC_ClanUncle/Granny/Boy/Girl` + 街坊 `NPC_TownOldMan/Woman/Injured/Refugee`（男/老/少/女/伤/逃难） |
| 1.1 父亲王世清（2D） | ✅ | `PROP_FatherPhoto`：渲染的旧照片贴图 `T_FatherPhoto_D.png` + 相框，立在供桌上 |
| 1.2 族谱套件 | ✅ | `PROP_Genealogy`：半本谱（合/开）、谱匣+盖、三张散页、拼合页、父名墨污 |
| 1.2 日军飞机 | ✅ | `PROP_JapanesePlane`：螺旋桨子物体转动、翼尖尾迹 |
| 1.2 残旗 | ✅ | `PROP_FallenFlag`：三级石阶 + 旗座 + 6 m 旗杆倒地 + 破旗 + 旧血 |
| 1.2 香案套件 | ✅ | `PROP_IncenseSet`（场景里只用三炷香，炉/烛台/供果用内景自带的） |
| 1.2 王砚相机 | ✅ 资产 | `PROP_Camera_1941`（人物身上已有相机包，场景里暂不单独摆） |
| 1.2 日军武器 | ✅ | `PROP_JpRifle`（含刺刀）、`PROP_JpSword`（刀/鞘分开）、`PROP_JpAmmoBox` |
| 1.2 摊货 | ✅ | `PROP_VendorGoods`：扁担菜筐、鱼、米袋、陶罐、杆秤 |
| 1.2 幡/横幅/日军旗 | ✅ | `PROP_Banner_Shrine` / `PROP_Banner_Street` / `PROP_Flag_Japan` |
| 1.2 铺门/箱子 | ✅ | `PROP_Door_Loot`：两扇门（枢轴在门轴，可踹开）+ 樟木箱 |
| 1.2 父亲墨污牌位 | ✅ | `PROP_Tablet_Father`：`Name`（金字）/ `Ink`（墨污）两态，替换内景里的同位牌位 |
| 1.3 燃烧铺面 2—3 状态 | ✅ 2 态 | `ENV_Fire_Shop`：`State_Burning` / `State_Burnt` + 门前焦木 |
| 1.3 被炸铺面 3 种 | ✅ | `ENV_Ruin_A`（断墙）/ `_B`（屋顶塌落）/ `_C`（弹坑） |
| 1.3 商贩摊 3 种 | ✅ | `ENV_VendorStall_Veg` / `_Snack` / `_Goods` |
| 1.3 街市道具 | ✅ | `PROP_NoticeWall` / `PROP_Postbox` / `PROP_StreetLamp` / `PROP_Bollards` / `PROP_BambooBaskets`（电线杆、树原有） |
| 1.3 哨卡道具 | ✅ | `ENV_Checkpoint_Props`：沙袋墙、拒马、横杆 + 日军旗 |
| 1.3 环海楼室内 | ⚠️ 未接入 | 第一幕不进环海楼（剧本只到楼前石阶倒旗），残旗套件已接在环海门内；内景留给第二/三幕军议 |
| 1.4 动画 10 项 | ✅ 12 个 | 见下「动作」 |
| 1.5 VFX 8 项 | ✅ | 见下「特效」 |

祠堂内景 `BLD_INT_AncestralHall`（另一会话做的白模）已接入第一幕，替换原来「切开 ROC 外壳 + 隐形墙」的做法。

## 人物

![街市人物：日军军官、三个日本兵、两个小贩、四个街坊](images/act1/street_02_posed.jpg)

| 资产 | 身高 | 造型 |
|---|---|---|
| `NPC_JpOfficer` | 1.72 | 40 岁，黄呢军服、大檐帽红帽箍、白手套、圆眼镜、马靴、左胯军刀 |
| `NPC_JpSoldier_A` | 1.66 | 钢盔、绑腿、子弹盒、刺刀鞘、三八式斜背 |
| `NPC_JpSoldier_B` | 1.68 | 战斗帽带护颈布、徒手（踹门、推人） |
| `NPC_JpSoldier_C` | 1.64 | 钢盔、背囊毛毯卷、水壶、三八式斜背 |
| `NPC_VendorVeg` | 1.68 | 50 岁，卷袖短褂、斗笠、蓝围裙、草鞋 |
| `NPC_VendorGoods` | 1.64 | 60 岁，青灰短衫、旧瓜皮帽、灰短须、土黄围裙 |
| `NPC_TownOldMan` | 1.64 | 70 岁，白发长须、驼背 |
| `NPC_TownWoman` | 1.57 | 35 岁，灰紫袄黑裙、包头巾 |
| `NPC_TownInjured` | 1.70 | 头缠渗血绷带、右臂吊带 |
| `NPC_TownRefugee` | 1.70 | 斗笠、绑腿、背铺盖卷和包袱 |

规格同前两批：每人 1.0–1.5k 三角面，22 骨 Humanoid（全部验证为有效 Avatar）。生成器 `Tools/blender/rupu_char.py` 新增：头饰 `helmet` / `field_cap(_flaps)` / `peaked_cap` / `straw_hat` / `headscarf` / `bandaged`，`glove` 手套，配件 `boards`（肩章领章）`gunto` `pouches` `bayonet` `rifle_back` `backpack` `canteen` `apron` `sling` `bedroll`。

父亲照片是把一个只用于渲染的王世清人物（`rupu_act1.FATHER_CFG`，不出 3D 资产）渲成半身像，再调成深褐旧照片：

<img src="images/act1/T_FatherPhoto.jpg" width="220">

## 道具与环境

| | | |
|---|---|---|
| ![](images/act1/prev_PROP_Genealogy.jpg) 族谱套件 | ![](images/act1/prev_PROP_JapanesePlane.jpg) 日机 | ![](images/act1/prev_PROP_FallenFlag.jpg) 残旗 |
| ![](images/act1/prev_ENV_Fire_Shop.jpg) 燃烧铺面（两态叠在一起） | ![](images/act1/prev_PROP_Door_Loot.jpg) 铺门 + 箱子 | ![](images/act1/prev_ENV_Checkpoint_Props.jpg) 哨卡 |
| ![](images/act1/prev_PROP_IncenseSet.jpg) 香案套件 | ![](images/act1/prev_PROP_VendorGoods.jpg) 摊货 | ![](images/act1/prev_ENV_VendorStall_Snack.jpg) 小吃摊 |
| ![](images/act1/prev_ENV_Ruin_B.jpg) 屋顶塌落 | ![](images/act1/prev_PROP_JpSword.jpg) 军刀 | ![](images/act1/prev_PROP_Tablet_Father.jpg) 墨污牌位 |

生成脚本 `Tools/blender/rupu_act1.py`（注册进 `build_yongchang.py`）。约定：
- 会动/会切状态的部件是**固定名字的子物体**（`Book_Open`、`Page_1..3`、`Door_L/R`、`Chest_Lid`、`Pole`、`Propeller`、`State_Burning`……），团结里按名字找。
- `FX_*` 空物体是特效挂点（烛火、香烟、火、烟、尾迹、路灯）。
- `rupu_kit.MB.at()` 新增 `rx/ry` 参数（绕 X/Y 旋转），旧调用不受影响。

## 动作（Humanoid 共用）

![12 个动作重定向到不同人物](images/act1/gestures_03_posed_3q.jpg)

`CH_WangYan_1941@<动作>.fbx`，所有人共用；在 `AC_Humanoid_Locomotion` 里是同名状态（无连线），脚本用 `CrossFade("<动作>")` 进入、`CrossFade("Locomotion")` 回走跑。

| 动作 | 清单项 | 用在 |
|---|---|---|
| `TalkLoop` | ANIM_Elder_Talk | 所有说话的人：对白标题匹配时自动播（族老、族长、三派、族亲、军官、日本兵、小贩） |
| `Beckon` | ANIM_Elder_Lead | 族老「跟我来」先招手再转身带路（带路行走用 Walk） |
| `AttentionLoop` | ANIM_Officer_Enter | 军官、士兵进门站定后立正；哨兵 |
| `DrawSword` | ANIM_Officer_DrawSword | 街市军官拔刀指王砚（军刀挂右手，拔刀时出现；放行后收起） |
| `Push` | ANIM_Soldier_Push | 日本兵推小贩、踹铺门 |
| `Fall` | ANIM_Vendor_Fall | 小贩被推坐倒在地 |
| `IncenseBow` / `KneelPray` | ANIM_Wang_Incense | 王砚上香三拜（香随之点上）；跪拜备用 |
| `TouchFlag` | ANIM_Wang_TouchFlag | 王砚半蹲伸手触旗 |
| `ArgueLoop` | ANIM_Crowd_Argue | 春祭三派争吵 |
| `WatchLoop` / `CowerLoop` | ANIM_Crowd_Watch | 街坊围观；事件发生时躲闪，过后恢复围观 |

导入设置：`RupuArtImporter` 把人形片段的根运动全部烘进姿势（Original），跪下/坐倒的髋高才会作用到身体上，动作也不会漂移。

## 特效

`Tools/unity_seed/Assets/_Rupu/Editor/RupuVfx.cs`（菜单 入谱 > 特效 > 生成第一幕特效），输出 `Assets/Art/VFX/PF_VFX_*.prefab`。材质用 URP `Particles/Unlit` 存成资产，打包时着色器一定会带上（原来 `Act1Fire` 用 `Shader.Find("Particles/Standard Unlit")`，URP 下不可用）。

| 预制体 | 清单项 | 用在 |
|---|---|---|
| `PF_VFX_Rain` | VFX_Rain | 挂在相机上跟玩家；粒子碰屋顶即消失，室内不下雨 |
| `PF_VFX_IncenseSmoke` | VFX_IncenseSmoke | 三炷香，上香时出现 |
| `PF_VFX_Candle` | VFX_Candle | 供桌两支蜡烛（带小点光） |
| `PF_VFX_PaperAsh` | VFX_PaperAsh | 正厅里飘的纸灰 |
| `PF_VFX_Fire` + `PF_VFX_FireSmoke` | VFX_FireSmoke | 燃烧铺面三处火 + 黑烟柱 |
| （模型材质） | VFX_FlagBlood | 旧血做在 `PROP_FallenFlag` 的旗面和石阶上 |
| `PF_VFX_PlaneTrail` | VFX_PlaneTrail | 日机翼尖尾迹 |
| `PF_VFX_PropellerDisc` | VFX_PlanePropeller | 螺旋桨虚影（桨叶本身由 `Act1Plane` 绕机身轴转） |

## 场景接入（`Act1_ROC.unity`）

| 祠堂（去屋顶俯视） | 供桌：父亲照片、烛火、散页 |
|---|---|
| ![](images/act1/act1_p0_shrine_top.jpg) | ![](images/act1/act1_p0_altar.jpg) |
| 军官带兵进祠堂（运行中） | 春祭争吵（运行中） |
| ![](images/act1/play_officer.jpg) | ![](images/act1/play_argue.jpg) |
| 砸门之后：门被踹开、箱子拖到街上 | 街尾火场 |
| ![](images/act1/play_door_after.jpg) | ![](images/act1/act1_p0_fire.jpg) |
| 环海门校场：哨卡、废墟、残旗 | 残旗石阶 |
| ![](images/act1/act1_p0_plaza.jpg) | ![](images/act1/act1_p0_flag.jpg) |

生成：菜单 入谱 > 第一幕 > 用 ROC 永昌堡场景生成（`Act1RocSceneBuilder.Create`）。要点：

- **祠堂**：`BLD_INT_AncestralHall` 放在 ROC 祖祠同一位置（-20, 42，转 180°），ROC 外壳隐藏；互动点/站位取内景的 `ANCHOR_*`。藏谱派锚点正好在上香蒲团上，往院子方向让了 2.2 m。人物用向下射线贴地（院子 0 m、月台/正厅 0.9 m）。
- **军官进门**：`Act1Director.officerEntryOffset` 设为 (0,0,-6)，从南边祠堂门进出（原来写死 +Z，在 ROC 祠堂里会从正厅后面走出来）。
- **NPC**：都挂 `Act1ClanActor`（`Assets/_Project/Scripts/Story/`）：说话时 Talk、被剧情移动时走路并朝前、常态动作（围观/立正/躲闪）、玩家走近转身。`Act1Director` 每换一句对白调用 `Act1ClanActor.Speak(标题)`。
- **道具状态**：`Act1Director.showOnIncense`（上香点香）、`showOnPagesMended` / `hideOnPagesMended`（散页 → 摊开的半本谱 + 拼合页）。
- **街市**：主街菜摊 + 被推倒的菜贩 + 拔刀军官 + 巡逻兵；砸门挪到下河桥东 P0095 铺面门口（原坐标在桥面上）；街尾火场把 P0094 铺面换成燃烧铺面（原火点在路中间）；环海门校场放废墟、弹坑、哨卡；残旗套件在环海门内侧城墙下。
- 模型或预制体缺失时自动退回胶囊/方块占位，场景照样能生成和运行。

验收：批处理里进 Play 自动推进整幕（族老带路 → 族亲 → 上香 → 军官 → 拼谱 → 三派 → 争吵 → 街市盘问 → 砸门 → 火场 → 触旗），运行时报错 0；Windows 包构建成功。

## 重新生成

```bash
# 人物 / 动作 / 道具 / 环境（已存在的 .blend 默认跳过，--force 覆盖）
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/build_yongchang.py -- --only NPC_JpOfficer,PROP_Genealogy,...
# 特效、人物合影（含 street_*、gestures_* 截图）
T=/Applications/Tuanjie/Hub/Editor/2022.3.62t18/Tuanjie.app/Contents/MacOS/Tuanjie
$T -batchmode -quit -projectPath "$PWD/Project_rupu" -executeMethod Rupu.EditorTools.RupuVfx.BuildCLI -logFile Builds/logs/vfx.log </dev/null
$T -batchmode -quit -projectPath "$PWD/Project_rupu" -executeMethod Rupu.EditorTools.RupuCharacters.LineupCLI -logFile Builds/logs/chars.log </dev/null
# 第一幕场景
$T -batchmode -quit -projectPath "$PWD/Project_rupu" -executeMethod Rupu.EditorTools.Act1RocSceneBuilder.Create -logFile Builds/logs/act1.log </dev/null
```

## P1 完成情况

依据：[`入谱_当前建模缺口清单.md`](入谱_当前建模缺口清单.md) 第二节（第一幕 P1）。生成脚本 `Tools/blender/rupu_act1p1.py`（材质前缀 `M_P1_*`，人物 `M_P1C_*`，钩子 `P1_*`）。全部 `[OK]` 导出到 `Project_rupu/Assets/Art/<分类>/<名>/`，**还没导入团结、没接场景**。

| 清单项 | 状态 | 资产（三角面） |
|---|---|---|
| `CHR_Townsperson` 扩展 6—8 | ✅ 8 个 | `NPC_TownMother`（1232）/ `NPC_TownPorter`（1132）/ `NPC_TownBeggar`（1388）/ `NPC_TownStudent`（1168）/ `NPC_TownShopkeeper`（1416）/ `NPC_TownOldWoman`（1198）/ `NPC_TownToddler`（1116）/ `NPC_TownRefugeeWoman`（1260） |
| `PROP_StreetFood` 2 | ✅ | `PROP_StreetFood_Noodle` 面担（976）/ `PROP_StreetFood_Steamer` 蒸笼+油锅早点摊（1248） |
| `PROP_Load` 2 | ✅ | `PROP_Load_Pole` 逃难挑子（426）/ `PROP_Load_Cart` 独轮车装家当（854） |
| `PROP_JapaneseFlag` 2 | ✅ | `PROP_Flag_Japan_Pole` 哨卡高杆旭日旗（492）/ `PROP_Flag_Japan_Wall` 门楣横挂 + 交叉小旗（372）；原有 `PROP_Flag_Japan` 不变 |
| `PROP_WantedPoster` 3 | ✅ 带文字贴图 | `PROP_Poster_A` 布告·刚贴（192）/ `_B` 通缉·撕破（1172）/ `_C` 告示·雨湿（608） |
| `ENV_BombCrater` 2 | ✅ | `ENV_BombCrater_A` 路面小坑积水（600）/ `_B` 靠墙大坑 + 炸塌的墙（874） |
| `ENV_Barricade` 3 | ✅ | `ENV_Barricade_A` 家具门板堆（1300）/ `_B` 铁丝网 + 木桩（3592）/ `_C` 沙袋矮墙带射击口（2908） |
| `PROP_Bicycle` | ✅ | `PROP_Bicycle`（1624） |
| `PROP_Rickshaw` | ✅ | `PROP_Rickshaw`（1320），车身枢轴在车轴 |
| `PROP_Telephone` | ✅ | `PROP_Telephone` 野战电话 + 交换机 + 线轴（912） |
| `PROP_Suitcase` | ✅ | `PROP_Suitcase`（492），`Lid` 开/合 |

### 街坊（8 个，与 P0 的 8 个区分）

![P1 街坊：母亲、挑夫、乞丐、学生、掌柜、老太太、幼童、逃难妇人（最右 1.75 m 参考）](images/act1/p1_townsfolk.jpg)

| 资产 | 身高 | 造型 |
|---|---|---|
| `NPC_TownMother` | 1.58 | 28 岁，浅灰蓝大襟袄深蓝裤、低髻银簪，胸前背带兜襁褓婴儿 |
| `NPC_TownPorter` | 1.74 | 壮，深灰短褂挽袖（露前臂）、裤腿卷到膝、草鞋，额扎汗巾、颈搭汗巾、右肩垫肩 |
| `NPC_TownBeggar` | 1.63 | 瘦驼，补丁破短褂、草绳腰带、破布条下摆、赤脚、乱发花白短须，左胯破碗 |
| `NPC_TownStudent` | 1.73 | 18 岁，深藏青立领学生装、五颗铜扣、学生帽、斜挎帆布书包 |
| `NPC_TownShopkeeper` | 1.66 | 胖（bulk 1.24），驼色长衫外罩黑缎马甲、怀表链、礼帽、八字胡 |
| `NPC_TownOldWoman` | 1.47 | 75 岁，矮小背驼，黑风帽缀玉抹额、扎裤脚，左臂挎竹篮 |
| `NPC_TownToddler` | 1.02 | 4 岁，大头比例、棉袄、虎头帽（额前「王」字纹）、银长命锁 |
| `NPC_TownRefugeeWoman` | 1.60 | 土灰短袄、绑腿草鞋、下巴打结的方头巾、背篓装铺盖、胸前包袱 |

都是 `rupu_char.build_character` + 本模块注册的钩子（发型 `P1_student_cap/P1_tiger_cap/P1_hood/P1_towel/P1_messy/P1_fedora/P1_kerchief`，配件 `P1_baby/P1_hairpin/P1_shoulder_pad/P1_rags/P1_student/P1_vest/P1_mustache/P1_basket_arm/P1_lock/P1_back_basket`），22 骨 Humanoid，共用 `CH_WangYan_1941@*` 动作，没有新动作。

### 道具与环境

![小吃摊、挑子、独轮车、日旗、电话、皮箱](images/act1/p1_props_a.jpg)

![告示三张、自行车、黄包车（停放态）、独轮车](images/act1/p1_props_b.jpg)

![弹坑两种、街垒三种](images/act1/p1_env.jpg)

告示纸面贴图（1024，`T_Poster_<A|B|C>_D.png`，在资产目录里）：文字竖排右起，A「佈告」宵禁令（昭和十六年 + 朱印），B「通緝」木刻画像，C「告示」领良民证（墨往下流、水渍）：

![告示贴图](images/act1/p1_poster_textures.jpg)

### 子物体 / 挂点 / 锚点（团结里按名字找）

| 资产 | 子物体 | FX / ANCHOR |
|---|---|---|
| `PROP_StreetFood_Noodle` | `Stall`、`Pot_Lid`（锅盖，可揭） | `FX_Steam`（锅上）、`FX_StoveFire`（灶口）、`FX_StoveSmoke`（烟囱）；`ANCHOR_Vendor`、`ANCHOR_Customer_1/2`（长凳） |
| `PROP_StreetFood_Steamer` | `Stall`、`Steamer_Lid` | `FX_Steam`（蒸笼顶）、`FX_OilSmoke`（油锅）、`FX_StoveFire_1/2`；`ANCHOR_Vendor`、`ANCHOR_Customer_1/2` |
| `PROP_Load_Pole` | `Load` | `ANCHOR_Shoulder`（扁担中点，高 1.34）。放地上两筐着地；挑起时整体上抬，让 `ANCHOR_Shoulder` 对齐挑夫右肩（1.74 m 的挑夫约 +0.1 m，右肩在人物 -X 侧约 0.18 m） |
| `PROP_Load_Cart` | `Cart`、`Wheel`（枢轴在轮轴，绕本地 X 转） | `ANCHOR_Pusher`（车把后方） |
| `PROP_Flag_Japan_Pole` | `Pole`、`Cloth`（旗面，枢轴在杆顶挂点，可加风动） | — |
| `PROP_Flag_Japan_Wall` | `Flag_Hung`、`Bracket`、`Flag_Crossed_L/R` | 原点 = 墙面上横挂旗的下沿中点，墙在背后；只要一种就隐藏另一组 |
| `PROP_Poster_A/B/C` | `Poster`（正面贴图 + 背面纸背色）；B 另有 `Paper_Remnants`；C 另有 `NOCOL_WetStain`（墙上水痕，低于原点 0.36 m，pivot 警告可忽略） | `ANCHOR_Read`（纸前 0.9 m）。原点 = 纸下沿中点、贴墙面；纸厚度 3 mm 内，直接贴墙放 |
| `ENV_BombCrater_A/B` | `Crater`（坑底只低于地面 3 cm，靠土沿堆高做出深度） | B 的墙在背后（团结 -Z 侧） |
| `ENV_Barricade_A` | `Barricade`、`COL_Barricade` | — |
| `ENV_Barricade_B` | `Posts`、`Sign`、`NOCOL_Wire`（铁丝不加碰撞）、`COL_Fence`（整体挡人） | — |
| `ENV_Barricade_C` | `Sandbags` | `ANCHOR_Loophole_1/2`（射击口后的踏板上，朝前） |
| `PROP_Bicycle` | `Frame`、`Wheel_F`、`Wheel_R`（枢轴在轴心） | — |
| `PROP_Rickshaw` | `Body`（枢轴在车轴）、`Wheel_L/R` | `ANCHOR_Puller`（车杠前端）、`ANCHOR_Seat`。默认停放态：车杠着地、车身后仰 21°；拉起 = `Body` 绕本地 X 转回 21°（车杠水平，把手高约 0.78 m），正负以车杠前端抬起为准 |
| `PROP_Telephone` | `Table`、`Phone`、`Handset`（可拿起）、`Crank`、`Switchboard`、`Reel_Stand`、`Reel`（枢轴在轴心）、`NOCOL_Wires` | `ANCHOR_Operator`（操作员站位，面朝桌） |
| `PROP_Suitcase` | `Case`、`Contents`、`Lid`（枢轴在后沿铰链） | 合 = `Lid` 旋转 0；开 = 绕本地 X 向后翻约 105° |

### 给 A 的接入说明

- 8 个新街坊直接用 `AC_Humanoid_Locomotion` + `Act1ClanActor`，常态动作用 `WatchLoop` / `CowerLoop`；母亲、老太太、逃难妇人适合放逃难队伍，学生和掌柜放告示墙前，乞丐放街角，挑夫配 `PROP_Load_Pole`。
- 告示贴图要随 FBX 一起导入（`T_Poster_*_D.png` 和 FBX 在同一目录，材质名 `M_P1_Poster_A/B/C`）；贴图文字用思源宋体（SIL OFL）渲染，只是位图，不随仓库分发字体。
- 道具类 `PROP_StreetFood_*` 尺寸接近摊位，可替换主街上的 `ENV_VendorStall_Snack` 或并排摆；`ENV_Barricade_*` 和 `PROP_Flag_Japan_Pole` 适合环海门校场哨卡和封锁街口。
- 旋转部件（车轮、线轴、皮箱盖、车身）都已把枢轴放在转轴上，物体本身旋转为 0。

### 重新生成

```bash
/Applications/Blender.app/Contents/MacOS/Blender -b --factory-startup -P Tools/blender/build_yongchang.py -- \
  --only NPC_TownMother,NPC_TownPorter,NPC_TownBeggar,NPC_TownStudent,NPC_TownShopkeeper,NPC_TownOldWoman,NPC_TownToddler,NPC_TownRefugeeWoman,PROP_StreetFood_Noodle,PROP_StreetFood_Steamer,PROP_Load_Pole,PROP_Load_Cart,PROP_Flag_Japan_Pole,PROP_Flag_Japan_Wall,PROP_Poster_A,PROP_Poster_B,PROP_Poster_C,ENV_BombCrater_A,ENV_BombCrater_B,ENV_Barricade_A,ENV_Barricade_B,ENV_Barricade_C,PROP_Bicycle,PROP_Rickshaw,PROP_Telephone,PROP_Suitcase --force
```

告示贴图在生成 `PROP_Poster_*` 时一起重渲（需要本机有思源宋体 `~/Library/Fonts/SourceHanSerifCN-Heavy.otf`，或 Songti；都没有时退回墨块）。

## 还没做（P1 及以后）

- 表情贴图、LOD、正式贴图；手指骨（现在拳头一块）。
- ~~街坊扩展、黄包车/自行车/挑担、告示通缉文字贴图~~：P1 已做（见上「P1 完成情况」），待导入团结并接进 `Act1_ROC` 场景。
- P1 小吃摊/旗/告示/街垒/弹坑/车辆的场景摆放；告示「张贴/撕下」交互；旗面风动、车轮转动脚本。
- 环海楼内景接入（第二/三幕军议）；燃烧铺面「烧尽」态用于第四幕 1941 冬。
