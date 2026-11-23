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

## 还没做（P1 及以后）

- 表情贴图、LOD、正式贴图；手指骨（现在拳头一块）。
- 街坊扩展、黄包车/自行车/挑担、告示通缉文字贴图。
- 环海楼内景接入（第二/三幕军议）；燃烧铺面「烧尽」态用于第四幕 1941 冬。
