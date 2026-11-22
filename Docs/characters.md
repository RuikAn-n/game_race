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
