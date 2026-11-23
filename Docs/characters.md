# 主要人物（第一批：白模 + Humanoid + 基础动画）

![人物合影（待机/走/跑采样）](images/map/chars_03_posed_3q.jpg)

| T 姿势（左→右） | 在场景里 |
|---|---|
| ![](images/map/chars_01_tpose.jpg) | ![](images/map/MING_14_cast_north_gate.jpg) |

左→右：王砚 1941、王砚 1560、王沛（枪）、王叔杲（算盘）、王德、王秉之（拐）。

| 资产 | 清单 ID | 身高 | 造型 | 摆放 |
|---|---|---|---|---|
| `CH_WangYan_1941` | CHR_WangYan_1941 | 1.75 | 照相馆学徒：灰蓝长衫、布鞋、斜挎相机包、短发 | 1941 场景玩家，码头下船 |
| `CH_WangYan_1560` | CHR_WangYan_1560 | 1.75 | 同脸；明制短褐、布带、绑腿、草鞋、腰间谱袋、发髻 | 1560 场景玩家，祖祠前庭 |
| `NPC_WangPei` | CHR_WangPei | 1.78 | 62 岁老将：深肤短须灰发、旧皮札甲 + 披膊 + 甲裙、褪红衬袍、木腰牌「沛」；长枪 `PROP_Spear_Pei` 2.6 m（褪红枪缨） | 1560 北门内「看船」，枪立在身旁 |
| `NPC_WangShugao` | CHR_WangShugao | 1.72 | 41 岁建堡者：清瘦、蓝灰长衫、方巾、山羊须、腰插建堡图卷；算盘 `PROP_Abacus`（13 档） | 1560 祖祠前庭 |
| `NPC_WangDe` | CHR_WangDe | 1.72 | 20 岁义师：靛青短打、绑腿、草鞋、短刀、木腰牌「德」 | 1560 北门，随王沛 |
| `NPC_WangBingzhi` | CHR_WangBingzhi | 1.70 | 60+：瘦、背微驼、深褐长袍、瓜皮帽、白长须；木拐 `PROP_Cane_Bingzhi` | 1941 祖祠前 |

- **面数**：每人 1.0–1.6k 三角面（清单里的面数规格这一批先不管，后续细化时再加）。
- **骨架**：22 根骨骼，团结 Humanoid 标准命名，导入后 Avatar 自动映射。6 个人物和 3 个动画文件都检查过：全部是有效的 Humanoid。
- **动画**：`CH_WangYan_1941@Idle / @Walk / @Run`，所有人共用（Humanoid 重定向）。控制器 `Assets/Art/Animations/AC_Humanoid_Locomotion.controller` 用 `Speed` 参数混合，阈值为 0 / 1.8 / 5。
- **绑定**：分段低模，每段刚性绑定一根骨骼；长衫下摆按左右腿混合权重，走路时会跟腿摆。
- **脸**：按项目约定不做写实脸，五官只是几块小几何体，之后换表情贴图。
- **生成**：`Tools/blender/rupu_char.py`（造型配置在 `CAST` 表里：身高、服装、颜色、发型、胡子、配件），由 `Tools/mac/build_yongchang.sh` 统一生成和导出。场景里的摆放写在 `Data/map/era_kits.json` 的 `cast` 表里。

后续：Mixamo 动作（说话、跪拜、拔刀、枪顿地、拨算盘……）按 `<模型>@<动作>.fbx` 放进来，就能直接给所有人用；6 个表情 blendshape、LOD、贴图属于下一轮细化。

## 第二批：1941 族亲（第一幕祠堂：族老、三派、冷遇/亲善、老少）

![族亲合影（待机/走/跑采样）](images/map/clan_03_posed_3q.jpg)

| T 姿势（左→右） | 在 Act1_ROC 祠堂里（去掉屋顶俯视） |
|---|---|
| ![](images/map/clan_01_tpose.jpg) | ![](images/map/act1_clan_top.jpg) |

| 资产 | 清单 ID / 文本角色 | 身高 | 造型 | Act1_ROC 站位 |
|---|---|---|---|---|
| `NPC_ClanElder` | CHR_Elder · 族老 | 1.68 | 65 岁，黑褐长衫外罩黑马褂、念珠、灰短发短须、背微弯；手杖 `PROP_Staff_Elder` | 院门口迎王砚 → 带路进祠堂停在门内 |
| `NPC_ClanJiao` | CHR_Jiao · 交谱派族老 | 1.70 | 55 岁微胖，石青长衫、圆眼镜、山羊须、腰夹账本 | 祠堂西侧 |
| `NPC_ClanShao` | CHR_Shao · 烧谱派青年 | 1.76 | 22 岁，黑短打、褪红腰带、绑腿、皱眉，背后插未点的火把 | 祠堂东侧 |
| `NPC_ClanCang` | CHR_Cang · 藏谱派妇人 | 1.58 | 42 岁，深青灰袄 + 黑长裙、脑后低髻，斜背包袱 | 牌位前 |
| `NPC_ClanGirl` | CHR_Townsperson 女 · 族中少女 | 1.50 | 14 岁，旧红袄蓝裤、长辫红头绳 | 藏谱派妇人身边（母女） |
| `NPC_ClanUncle` | CHR_Townsperson 男 · 族中冷遇 | 1.72 | 45 岁，灰短褂、旧毡帽、皱眉 | 族亲互动点西侧 |
| `NPC_ClanGranny` | CHR_Townsperson 老 · 族中亲善 | 1.55 | 68 岁，靛蓝袄黑裙、白发低髻、黑抹额、驼背、眉梢下垂 | 族亲互动点东侧 |
| `NPC_ClanBoy` | CHR_Townsperson 少 · 族中孩童 | 1.18 | 8 岁，褪黄短褂、大头比例 | 跟着族婶婆 |

- 规格同第一批：每人 0.9–1.4k 三角面，22 骨 Humanoid（8 人均已验证为有效 Avatar），共用 Idle/Walk/Run。
- 生成器新增造型参数：`head`（孩童头身比）、`brow_tilt`（皱眉/和善）、`skirt`+`flare`+`ao_hem`（女装袄裙）、发型 `back_bun` / `braid` / `brim_hat`，配件 `magua` `beads` `glasses` `ledger` `torch` `bundle`。
- 合影：菜单 入谱 > 人物 > 族亲合影截图（或 `RupuCharacters.LineupCLI`，会同时出 `chars_*` 和 `clan_*`）。

### 第一幕祠堂里的接入（`Act1RocSceneBuilder`，菜单 入谱 > 第一幕 > 用 ROC 永昌堡场景生成）

- 胶囊占位全部换成上面的模型；族老不再借用王秉之模型；王秉之（族长）带拐。日本军官/士兵、街市人物仍是胶囊，待后续建模。
- 每个族亲挂 `Act1ClanActor`：玩家走近 4.5 m 内会转身面向王砚；被剧情移动时（族老带路、族长上前、三派争吵聚拢）按位移驱动 `Speed`，播走路动画而不是滑行。
- 修正：族长停步点、三派聚拢中心贴地（原来按胶囊中心 y=1 设置，换成脚底原点模型后会浮空）；争吵镜头看向祠堂里的聚拢中心（原来是灰盒场景的坐标）；族老停在门内 `ElderStop`，不再走进供桌。

![祠堂内（编辑模式下为 T 姿势，运行时为待机）](images/map/act1_clan_inside.jpg)
