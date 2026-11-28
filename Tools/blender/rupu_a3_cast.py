"""
《入谱》第三幕「守城」· 人物 + 动作 + 伤兵/遗体静态件
（Blender bpy，程序化；由 build_yongchang.py 统一生成/导出，recipes() 返回 {资产名: (分类, 生成函数)}）

对应 Docs/第三幕_建模清单.md §3.4 / §3.5 / §4.1 / §6。说明文档 Docs/act3_assets.md。

约定：
  - 人物沿用 rupu_char.build_character（Humanoid 22 骨，团结标准骨名）；配置写法同 rupu_act2.A2_CAST。
    第三幕人物都带 rupu_enemy 的插槽：SOCKET_Hand_R/L（武器零变换挂上）、SOCKET_Back、FX_Hit、FX_HitHead。
  - 动作资产 CH_WangYan_1941@A3_<动作>（共用骨架，自动收进 AC_Humanoid_Locomotion）。姿势写法同 rupu_a2_anim：
    _pose(L/R=(前抬, 外张), LF/RF=屈肘)、_legs(P, 大腿前抬, 小腿后屈, 脚)，持枪用 rupu_a2_anim.wield / reach 求解；
    每个关键帧经 rupu_act2._grounded 落地（脚/膝/身体刚好贴地）。
  - 枪：PROP_A3_Spear（王砚 / 义师枪兵，2.4 m）、PROP_A3_Spear_Agui（短一截，2.0 m）。原点 = 后手（右手）握点，
    +Z 朝枪头，挂 SOCKET_Hand_R 零变换；左手在动作里已经握在前面。
  - 动画事件、哪些片段循环：写在 Data/anim_events.json（RupuAnimEvents 在团结里写进 clip 导入设置）。
  - 伤兵 / 遗体静态件（PROP_A3_Wounded / PROP_A3_Corpse / PROP_A3_Stretcher_Wounded）：用对应人物摆好姿势后烘成静态网格，
    和可动的 NPC_A3_Wounded_* / NPC_A3_Corpse_* 是同一套姿势（A3_WoundedSit / A3_WoundedLie / A3_CorpseSide / A3_CorpseProne）。
  - 材质前缀 M_A3C_*。
"""
import math

import bpy
from mathutils import Matrix, Vector

import rupu_kit as K
import rupu_char as C
import rupu_act2 as A2
import rupu_a2_anim as AN
import rupu_enemy as E

K.PALETTE.update({
    "M_A3C_OldBand": "#5a4a40", "M_A3C_Patch": "#8a7e66", "M_A3C_AG_Coat": "#4a4a42", "M_A3C_AG_Pants": "#3f3a33",
    "M_A3C_RA_Ao": "#77736a", "M_A3C_RA_Skirt": "#4a4640", "M_A3C_Bundle": "#6e6250", "M_A3C_BundleKnot": "#4f4636",
    "M_A3C_RB_Ao": "#3e5458", "M_A3C_RB_Skirt": "#2e2b2a", "M_A3C_Swaddle": "#b8a888", "M_A3C_BabySkin": "#d0ae90",
    "M_A3C_RC_Coat": "#7a6a52", "M_A3C_RC_Pants": "#5a5040",
    "M_A3C_RD_Coat": "#6a6250", "M_A3C_RD_Pants": "#4e483e",
    "M_A3C_RE_Robe": "#6e6a5e", "M_A3C_RF_Ao": "#6a5442", "M_A3C_RF_Skirt": "#3a3632",
    "M_A3C_RG_Ao": "#8a4a3e", "M_A3C_RG_Skirt": "#3a3a36", "M_A3C_RG_Ribbon": "#9a3a2c",
    "M_A3C_RH_Coat": "#5e5a4c", "M_A3C_RH_Pants": "#4a4438",
    "M_A3C_WD_Coat": "#4a4a42", "M_A3C_Sling": "#d6d0c0", "M_A3C_Dirt": "#5a4e3e",
    "M_A3C_CO_Coat": "#4f4c44", "M_A3C_CO_Pants": "#3a3631",
    "M_A3C_SP_Coat": "#3e4a57", "M_A3C_BW_Coat": "#4a4a42", "M_A3C_SH_Coat": "#45505a",
    "M_A3C_CH_Robe": "#5e5a6a", "M_A3C_CH_Silk": "#7a6a8a", "M_A3C_CH_Cap": "#1e1c1a", "M_A3C_Jade": "#6f8a76",
    "M_A3C_Note": "#cbbd9e",
    "M_A3C_WZ_Robe": "#77756c", "M_A3C_WZ_Sash": "#3a3832",
    "M_A3C_MO_Ao": "#6a645a", "M_A3C_MO_Skirt": "#3a3834", "M_A3C_Skin_Pale": "#c2a890", "M_A3C_Rope": "#a08a5a",
    "M_A3C_WYB_Pad": "#5e5a48", "M_A3C_WYB_Strap": "#3e2f24", "M_A3C_Mud": "#5a4e3e",
    # 道具
    "M_A3C_SpearWood": "#6b5039", "M_A3C_SpearIron": "#4a4d4f", "M_A3C_SpearEdge": "#7a7d7e", "M_A3C_Tassel": "#8a3a30",
    "M_A3C_Pole": "#7a6648", "M_A3C_Basket": "#a8925e", "M_A3C_BasketDark": "#7a6640", "M_A3C_Goods": "#8a7a5a",
    "M_A2S_Rattan": "#8a7448", "M_A2S_RattanDark": "#5e4e32",
    "M_A3C_StretcherWood": "#6b5039", "M_A3C_StretcherCloth": "#9a8f78",
})

V = Vector
W = C.W
box, tube, ellipsoid, rings_mesh, _eu = C.box, C.tube, C.ellipsoid, C.rings_mesh, C._eu
_front, _band, _shell = A2._front, A2._band, A2._shell


# ====================================================================== 配件钩子
def ex_shoulder_patch(S, J, h, c, tw, hipsW):
    """右肩一块补丁（阿贵：穿的是王德留下的旧短褐）。"""
    S.add(*box(J["armR"] + V((0.02 * h, 0, 0.022 * h)), (0.07 * h, 0.085 * h, 0.012 * h)), "M_A3C_Patch",
          {"RightShoulder": 0.5, "Chest": 0.5})
    S.add(*box(J["armR"] + V((0.035 * h, -0.044 * h, -0.01 * h)), (0.05 * h, 0.006 * h, 0.05 * h)), "M_A3C_Patch",
          {"RightUpperArm": 0.6, "Chest": 0.4})


def ex_bundle(S, J, h, c, tw, hipsW):
    """背后包袱：布包 + 胸前打结的两道布带。"""
    cy = J["chest"].y + 0.1 * h
    S.add(*ellipsoid((0, cy, 0.66 * h), 0.12 * h, 0.06 * h, 0.1 * h, seg=8, rings=4), "M_A3C_Bundle", tw)
    _band(S, J, h, c, (0.08 * h, 0.81), (-0.02 * h, 0.7), 0.014, "M_A3C_BundleKnot", n=2)
    _band(S, J, h, c, (-0.08 * h, 0.81), (0.02 * h, 0.7), 0.014, "M_A3C_BundleKnot", n=2)
    S.add(*box(_front(J, h, c, 0.0, 0.7, 0.01), (0.03 * h, 0.012 * h, 0.025 * h)), "M_A3C_BundleKnot", tw)


def ex_swaddle(S, J, h, c, tw, hipsW):
    """胸前襁褓：斜挎背带兜着一个裹布的婴儿（头偏左）。"""
    p = _front(J, h, c, 0.0, 0.66, 0.05)
    S.add(*ellipsoid(p, 0.075 * h, 0.05 * h, 0.1 * h, seg=8, rings=4), "M_A3C_Swaddle", W("Chest"))
    S.add(*ellipsoid(p + V((0.045 * h, -0.01 * h, 0.08 * h)), 0.03 * h, 0.03 * h, 0.032 * h, seg=8, rings=4), "M_A3C_BabySkin",
          W("Chest"))
    _band(S, J, h, c, (-0.07 * h, 0.81), (0.07 * h, 0.55), 0.02, "M_A3C_BundleKnot", n=4)


def ex_belly(S, J, h, c, tw, hipsW):
    """孕妇：腹部隆起（罩在袄外）。"""
    p = _front(J, h, c, 0.0, 0.55, -0.02)
    S.add(*ellipsoid(p, 0.09 * h, 0.06 * h, 0.085 * h, seg=10, rings=5), c["top"], {"Spine": 0.6, "Hips": 0.4})


def ex_sling(S, J, h, c, tw, hipsW):
    """断臂伤兵：左前臂缠满绷带、挂在脖子吊带上；右上臂一道带血的绷带。"""
    a, b = J["elbowL"], J["wristL"]
    S.add(*tube(a, b, 0.034 * h, 0.03 * h, seg=8), "M_A3C_Sling", W("LeftLowerArm"))
    S.add(*box((a + b) / 2 + V((0, -0.031 * h, 0)), (0.03 * h, 0.004 * h, 0.02 * h)), "M_CH_Blood", W("LeftLowerArm"))
    _band(S, J, h, c, (0.03 * h, 0.82), (-0.08 * h, 0.66), 0.03, "M_A3C_Sling", n=3)
    a, b = J["armR"] + V((-0.04 * h, 0, 0)), J["armR"] + V((-0.09 * h, 0, 0))
    S.add(*tube(a, b, 0.034 * h, 0.034 * h, seg=8), "M_A3C_Sling", W("RightUpperArm"))


def ex_dirt(S, J, h, c, tw, hipsW):
    """战场泥污：衣服下摆、膝盖、胸前几块深色。"""
    for x, z, s in ((0.05, 0.47, 0.06), (-0.04, 0.62, 0.04), (0.0, 0.74, 0.03)):
        S.add(*box(_front(J, h, c, x * h, z, 0.002), (s * h, 0.004 * h, s * 0.8 * h)), "M_A3C_Mud", tw)
    for s, side in (("L", "Left"), ("R", "Right")):
        S.add(*box(J["knee" + s] + V((0, -0.05 * h, 0.01 * h)), (0.07 * h, 0.006 * h, 0.06 * h)), "M_A3C_Mud",
              W(side + "LowerLeg"))


def ex_rope_bind(S, J, h, c, tw, hipsW):
    """被绑：胸口和腰两道麻绳，背后打结（阿贵母亲绑在柱上；柱子是场景件）。"""
    b = c.get("bulk", 1.0)
    for z in (0.72, 0.58):
        rx, ry = A2._prof(z, c.get("outfit") == "robe")
        rr = [(V((0, C.spine_y(J, (z + d) * h), (z + d) * h)), rx * h * b * 1.12, ry * h * b * 1.18) for d in (-0.008, 0.008)]
        S.add(*rings_mesh(rr, seg=12, cap0=False, cap1=False), "M_A3C_Rope", tw)
    S.add(*box((0, J["chest"].y + 0.08 * h, 0.65 * h), (0.04 * h, 0.025 * h, 0.04 * h)), "M_A3C_Rope", tw)


def ex_battle(S, J, h, c, tw, hipsW):
    """战损王砚：左肩布护肩、右前臂绑带、斜背枪带（右肩到左胯）、衣服泥污。"""
    S.add(*box(J["armL"] + V((0.03 * h, 0, 0.02 * h)), (0.09 * h, 0.1 * h, 0.022 * h), rot=_eu(0, 18, 0)), "M_A3C_WYB_Pad",
          {"LeftShoulder": 0.4, "LeftUpperArm": 0.3, "Chest": 0.3})
    S.add(*box(J["armL"] + V((0.06 * h, 0, -0.02 * h)), (0.07 * h, 0.098 * h, 0.05 * h), rot=_eu(0, 30, 0)), "M_A3C_WYB_Pad",
          W("LeftUpperArm"))
    a, b = J["elbowR"] + V((-0.03 * h, 0, 0)), J["wristR"] + V((0.02 * h, 0, 0))
    for k in range(3):
        t0 = 0.1 + k * 0.3
        p = a.lerp(b, t0)
        S.add(*tube(p, p + (b - a) * 0.16, 0.03 * h, 0.028 * h, seg=8), "M_CH_Bandage", W("RightLowerArm"))
    _band(S, J, h, c, (-0.08 * h, 0.81), (0.09 * h, 0.5), 0.02, "M_A3C_WYB_Strap", n=5)
    S.add(*box((0.0, J["chest"].y + 0.075 * h, 0.66 * h), (0.02 * h, 0.006 * h, 0.36 * h), rot=_eu(0, 38, 0)), "M_A3C_WYB_Strap", tw)
    ex_dirt(S, J, h, c, tw, hipsW)


def ex_chen(S, J, h, c, tw, hipsW):
    """陈盐商：腰挂玉佩，前襟里露出一叠银票。"""
    S.add(*box((-0.06 * h, -0.085 * h * c.get("bulk", 1.0), 0.45 * h), (0.025 * h, 0.008 * h, 0.035 * h)), "M_A3C_Jade", hipsW)
    S.add(*tube((-0.06 * h, -0.085 * h * c.get("bulk", 1.0), 0.47 * h), (-0.06 * h, -0.085 * h * c.get("bulk", 1.0), 0.5 * h),
                0.003 * h, 0.003 * h, seg=4), "M_A2C_Tassel", hipsW)
    S.add(*box(_front(J, h, c, 0.04 * h, 0.7, 0.008), (0.05 * h, 0.006 * h, 0.03 * h), rot=_eu(0, -12, 0)), "M_A3C_Note", tw)


def ex_bow_back(S, J, h, c, tw, hipsW):
    """背弓：一张弓斜背在左肩后（弓手）。"""
    cy = J["chest"].y + 0.09 * h
    pts = []
    for i in range(7):
        t = i / 6
        a = math.radians(-60 + 120 * t)
        pts.append(V((0.22 * h * math.sin(a) * 0.9, cy + 0.03 * h * math.cos(a), 0.64 * h + 0.24 * h * math.sin(a) * 1.2)))
    for p0, p1 in zip(pts, pts[1:]):
        S.add(*tube(p0, p1, 0.009 * h, 0.009 * h, seg=5), "M_A2C_Quiver", tw)
    S.add(*tube(pts[0], pts[-1], 0.002 * h, 0.002 * h, seg=3), "M_A2C_Towel", tw)


C.EXTRA_HOOKS.update({"a3_shoulder_patch": ex_shoulder_patch, "a3_bundle": ex_bundle, "a3_swaddle": ex_swaddle,
                      "a3_belly": ex_belly, "a3_sling": ex_sling, "a3_dirt": ex_dirt, "a3_rope_bind": ex_rope_bind,
                      "a3_battle": ex_battle, "a3_chen": ex_chen, "a3_bow_back": ex_bow_back})


# ====================================================================== 人物配置
def _from(base, **kw):
    """从已有人物配置派生（复用骨架/身形/配件，换头换色）。"""
    src = dict(A2.A2_CAST.get(base) or C.CAST[base])
    ex = kw.pop("add_extras", [])
    rm = kw.pop("rm_extras", [])
    src.update(kw)
    src["extras"] = [e for e in src.get("extras", []) if e not in rm] + ex
    return src


_W = lambda **kw: dict(dict(outfit="robe", shoe="M_CH_ClothShoe", hem=0.03, flare=1.03), **kw)

A3_CAST = {
    # ---- P0
    "NPC_A3_Agui": _from("NPC_Militia_D", H=1.68, top="M_A3C_AG_Coat", pants="M_A3C_AG_Pants", hair="bun", band="M_A3C_OldBand",
                         brow_tilt=-6, bulk=0.92, rm_extras=["knife"], add_extras=["a3_shoulder_patch", "a3_dirt"],
                         desc="阿贵：17 岁义师，复用义师 D（灰纸甲、皮护臂、腰牌），换上王德留下的旧头巾、右肩补丁；短枪另为道具 PROP_A3_Spear_Agui"),
    "NPC_A3_Refugee_A": _W(H=1.50, top="M_A3C_RA_Ao", skirt="M_A3C_RA_Skirt", pants="M_A3C_RA_Skirt", hair="headscarf",
                           hair_mat="M_A3C_Bundle", skin="M_CH_Skin_Old", brow="M_CH_Hair_Grey", hunch=0.9, bulk=0.92,
                           brow_tilt=-10, extras=["a2_jiaoling", "ao_hem", "a3_bundle"],
                           desc="逃难老妇：70 岁，灰袄长裙、褐头巾、驼背、背包袱"),
    "NPC_A3_Refugee_B": _W(H=1.57, top="M_A3C_RB_Ao", skirt="M_A3C_RB_Skirt", pants="M_A3C_RB_Skirt", hair="a2_woman_pin",
                           bulk=0.9, brow_tilt=-8, bijia="M_A3C_RB_Skirt", bijia_bot=0.34,
                           extras=["a2_jiaoling", "ao_hem", "a3_swaddle"],
                           desc="抱孩妇人：25 岁，深青袄黑裙、高髻，胸前背带兜着襁褓"),
    "NPC_A3_Refugee_C": dict(H=1.30, head=1.15, outfit="jacket", top="M_A3C_RC_Coat", pants="M_A3C_RC_Pants", shoe="M_CH_Skin",
                             sash="M_A3C_RC_Pants", hair="a2_zongjiao", band="M_A3C_BundleKnot", bulk=0.9, cuff=1.15,
                             brow_tilt=-4, extras=["a2_jiaoling", "a2_patches"],
                             desc="半大男孩：12 岁，短褂卷裤、赤脚、总角，衣裤打补丁"),
    "NPC_A3_Refugee_D": _from("NPC_Laborer_C", H=1.64, top="M_A3C_RD_Coat", pants="M_A3C_RD_Pants", hair="a2_douli",
                              hat="M_CH_StrawHat", shoe="M_CH_Straw", add_extras=["a2_towel"],
                              desc="老农：60 岁，斗笠、破裤补丁、汗巾、背微驼；扁担另为道具 PROP_A3_CarryPole"),
    "CH_WangYan_1560_Battle": _from("CH_WangYan_1560", add_extras=["a3_battle"],
                                    desc="战损王砚 1560：同脸同高，加左肩布护肩、右前臂绑带、斜背枪带、泥污（W4—W8）"),
    # ---- P1 百姓
    "NPC_A3_Refugee_E": dict(H=1.66, outfit="robe", top="M_A3C_RE_Robe", pants="M_A3C_RE_Robe", shoe="M_CH_ClothShoe",
                             skin="M_CH_Skin_Old", hair="a2_wangjin", hair_mat="M_CH_Hair_Grey", brow="M_CH_Hair_White",
                             beard="long_white", hunch=0.6, bulk=0.9, cuff=1.3, extras=["a2_jiaoling", "a2_patches"],
                             desc="老翁：75 岁，灰旧长衫、白须、网巾、驼背；拐杖用 PROP_Staff_Elder"),
    "NPC_A3_Refugee_F": _W(H=1.56, top="M_A3C_RF_Ao", skirt="M_A3C_RF_Skirt", pants="M_A3C_RF_Skirt", hair="headscarf",
                           hair_mat="M_A2C_WA_Scarf", bulk=0.95, brow_tilt=-6, extras=["a2_jiaoling", "ao_hem", "a3_belly"],
                           desc="孕妇：褐袄长裙、包头巾、腹部隆起"),
    "NPC_A3_Refugee_G": _W(H=1.50, top="M_A3C_RG_Ao", skirt="M_A3C_RG_Skirt", pants="M_A3C_RG_Skirt", hair="braid",
                           ribbon="M_A3C_RG_Ribbon", bulk=0.85, brow_tilt=-8, head=1.05, extras=["a2_jiaoling", "ao_hem", "a2_patches"],
                           desc="少女：15 岁，旧红袄（褪色、带补丁）、长辫红头绳；与阿禾区分（阿禾是 1941 人物、短发）"),
    "NPC_A3_Refugee_H": _from("NPC_Laborer_A", H=1.70, top="M_A3C_RH_Coat", pants="M_A3C_RH_Pants", hair="a2_toujin",
                              cloth="M_A2C_Cloth_Blue", rm_extras=["a2_towel"], add_extras=["a2_shoulder_pad"],
                              desc="货郎：蓝灰头巾、右肩垫肩；扁担竹筐另为道具 PROP_A3_CarryPole"),
    # ---- P1 伤兵 / 遗体（可动的人形；静态件见 PROP_A3_Wounded / PROP_A3_Corpse）
    "NPC_A3_Wounded_A": _from("NPC_Militia_A", top="M_A3C_WD_Coat", rm_extras=["knife"], add_extras=["a3_sling", "a3_dirt"],
                              desc="断臂伤兵：义师 A 的布面甲，左前臂缠绷带吊在脖子上、右上臂绷带（不血腥：只有一小块暗色）"),
    "NPC_A3_Wounded_B": _from("NPC_Militia_B", hair="bandaged", rm_extras=["a2_quiver"], add_extras=["a3_dirt"],
                              desc="头伤伤兵：义师 B 的纸甲，头缠绷带额前一块暗色"),
    "NPC_A3_Corpse_A": _from("NPC_Militia_D", top="M_A3C_CO_Coat", pants="M_A3C_CO_Pants", rm_extras=["knife"],
                             add_extras=["a3_dirt"], desc="阵亡义师 A（侧卧，配 A3_CorpseSide；盖席 PROP_A3_CorpseCover）"),
    "NPC_A3_Corpse_B": _from("NPC_Laborer_B", top="M_A3C_CO_Coat", add_extras=["a3_dirt"],
                             desc="阵亡民夫 B（俯卧，配 A3_CorpseProne）"),
    # ---- P1 义师兵种
    "NPC_A3_Militia_Spear": _from("NPC_Militia_D", top="M_A3C_SP_Coat", hair="a2_douli", hat="M_CH_StrawHat", tassel="M_A2C_Tassel",
                                  rm_extras=["knife"], desc="义师枪兵：义师 D 改红缨斗笠、靛青短褐；持 PROP_A3_Spear"),
    "NPC_A3_Militia_Bow": _from("NPC_Militia_B", top="M_A3C_BW_Coat", add_extras=["a3_bow_back"],
                                desc="义师弓手：义师 B（纸甲、箭囊）加背弓；手持弓用 PROP_EN_Bow 的握法"),
    "NPC_A3_Militia_Shield": _from("NPC_Militia_C", top="M_A3C_SH_Coat", rm_extras=["a2_shield_back"], add_extras=["knife"],
                                   desc="义师牌手：义师 C（靛甲红缨笠），藤牌拿在左手 PROP_A3_RattanShield、右手短刀"),
    # ---- P1 W5 嫌疑人 / 阿贵母亲
    "NPC_A3_Chen": dict(H=1.68, outfit="robe", top="M_A3C_CH_Robe", pants="M_A3C_CH_Robe", shoe="M_CH_ClothShoe",
                        sash="M_A3C_CH_Silk", hair="a2_dongpo", hair_mat="M_A3C_CH_Cap", beard="goatee", bulk=1.32, cuff=1.35,
                        brow_tilt=-2, over="M_A3C_CH_Silk", extras=["a2_jiaoling", "a3_chen"],
                        desc="陈盐商：胖，紫灰绸衫、东坡巾、小胡子、玉佩、前襟露银票（W5 嫌疑人）"),
    "NPC_A3_WangZhi": dict(H=1.70, outfit="robe", top="M_A3C_WZ_Robe", pants="M_A3C_WZ_Robe", shoe="M_CH_ClothShoe",
                           sash="M_A3C_WZ_Sash", hair="a2_wangjin", beard="short_grey", brow="M_CH_Hair_Grey", bulk=0.8,
                           cuff=1.3, brow_tilt=12, extras=["a2_jiaoling", "a2_robe_sash"], robe_sash="M_A3C_WZ_Sash",
                           desc="王执：瘦、灰直裰、网巾、灰短须、眉头紧（W5 嫌疑人；手抖靠动作 A3_ElderBook 的颤动）"),
    "NPC_A3_Mother": _W(H=1.53, top="M_A3C_MO_Ao", skirt="M_A3C_MO_Skirt", pants="M_A3C_MO_Skirt", hair="back_bun",
                        hair_mat="M_CH_Hair_Grey", skin="M_A3C_Skin_Pale", hunch=0.5, bulk=0.82, brow_tilt=-12,
                        extras=["a2_jiaoling", "ao_hem", "a3_rope_bind"],
                        desc="阿贵母亲：病容（苍白肤色）、灰袄、灰发髻、瘦，胸腰两道绑绳（W5 回忆/救援；柱子是场景件）"),
}


def build_a3_character(name):
    c = A3_CAST[name]
    rig = C.build_character(name, c)
    h = c["H"]
    J = C.joints(h, c.get("hunch", 0.0), c.get("bulk", 1.0))
    E.add_sockets(rig, J, h)
    return rig


# ====================================================================== 动作
_X, _Y, _Z = AN._X, AN._Y, AN._Z
P_, LG = AN.P_, AN.LG
reach, wield, lunge, crouch, at_bone, _guard = AN.reach, AN.wield, AN.lunge, AN.crouch, AN.at_bone, AN._guard


def _retime(total, keys, segs):
    """片段改时：segs = [(原帧, 新帧), ...]（含 0 和末帧），分段线性映射。"""
    def m(f):
        for (a0, b0), (a1, b1) in zip(segs, segs[1:]):
            if a0 <= f <= a1:
                return round(b0 + (b1 - b0) * (f - a0) / max(1, a1 - a0))
        return f
    out, seen = [], set()
    for f, P, u in keys:
        g = m(f)
        if g in seen:
            continue
        seen.add(g)
        out.append((g, P, u))
    return segs[-1][1], out


def _cycle(T, step, upper, legs_amp=(26, 18, 10), lean=-0.02):
    """原地行走/跑循环：step(P, ph) 摆上身（可调用 wield/reach），腿按相位交替。"""
    th, kn, ft = legs_amp
    keys = []
    for ph in (0.0, 0.25, 0.5, 0.75, 1.0):
        P = P_(**upper(ph))
        a = "Left" if ph in (0.0, 0.25, 1.0) else "Right"
        b = "Right" if a == "Left" else "Left"
        if ph in (0.0, 0.5, 1.0):
            LG(P, th, kn, -6, a)
            LG(P, -th * 0.6, kn * 0.5, 8, b)
        else:
            LG(P, th * 0.3, 8, -2, a)
            LG(P, th * 0.2, kn * 2.6, 10, b)
        if step:
            step(P, ph)
        keys.append((round(ph * T), P, lean - (0.0 if ph in (0.25, 0.75) else 0.02)))
    return T, keys


# ---------------------------------------------------------------- 玩家 P0
def g_combat_idle_loop():
    return AN.g_spear_idle_loop()


def g_combat_walk():
    """持枪戒备走：上身保持中段架势（枪平端），原地迈步；Footstep@0/16。"""
    def up(ph):
        return dict(Hips=_Z(-22), Neck=_Z(12), Head=_X(-2) @ _Z(8), Chest=_X(-2) @ _Z(2 * math.sin(ph * 6.28)))

    def st(P, ph):
        wield(P, (-0.2, 0.0, 0.92 + 0.01 * math.cos(ph * 12.56)), (0.14, -1.0, 0.18), 0.56,
              q0r=(10, 10, 40, 0, 0), q0l=(60, -10, 40, 0, 0))
    return _cycle(32, st, up, (22, 16, 8))


def g_combat_run():
    """持枪跑：前倾，枪斜提在身右前（枪头低、朝前）；Footstep@0/12。"""
    def up(ph):
        return dict(Spine=_X(14), Chest=_X(4), Head=_X(-10), Hips=_Z(-10))

    def st(P, ph):
        wield(P, (-0.22, 0.04, 0.95), (0.2, -0.9, 0.15), 0.45, q0r=(20, 10, 60, 0, 0), q0l=(60, -10, 40, 0, 0))
    return _cycle(24, st, up, (40, 60, 14), lean=-0.05)


def g_spear_thrust1():
    return AN.g_spear_thrust()


def g_spear_thrust2():
    """二段：从一段收势直接拧腰向左前下方扎、带一下扫（第 11 帧命中）→ 收回戒备。"""
    return 28, [(0, _guard(), 0.0),
                (5, _guard(g=(-0.28, 0.1, 0.98), d=(-0.2, -1, 0.3), sep=0.6, Spine=_Z(-12), st=(22, 34, -14)), 0.0),
                (11, _guard(g=(-0.1, -0.34, 0.95), d=(0.22, -1, -0.05), sep=0.3, Spine=_X(14) @ _Z(10), Hips=_Z(-34),
                            Head=_X(-6), st=(40, 58, -28)), 0.0),
                (15, _guard(g=(-0.06, -0.3, 0.95), d=(0.4, -0.9, -0.05), sep=0.32, Spine=_X(12) @ _Z(16), Hips=_Z(-30),
                            st=(38, 56, -26)), 0.0),
                (28, _guard(), 0.0)]


def g_spear_sweep():
    return _retime(*AN.g_spear_sweep(), [(0, 0), (8, 10), (15, 18), (20, 23), (36, 36)])


def g_spear_heavy():
    """蓄力破防：枪举过右肩、枪头后指蓄力（0–22，可循环蓄力段）→ 第 28 帧斜劈砸下 → 收势。"""
    up = dict(Spine=_X(-6) @ _Z(-20), Chest=_Z(-10), Head=_Z(18))
    wind = _guard(g=(-0.3, 0.08, 1.32), d=(0.15, -0.55, 0.82), sep=0.35, st=(18, 30, -12), **up)
    wind2 = _guard(g=(-0.3, 0.12, 1.38), d=(0.12, -0.45, 0.88), sep=0.34, st=(18, 30, -12), **up)
    hit = _guard(g=(-0.12, -0.3, 1.05), d=(0.1, -0.85, -0.5), sep=0.34, Spine=_X(22) @ _Z(10), Head=_X(-8), st=(44, 62, -32))
    fol = _guard(g=(-0.1, -0.28, 0.98), d=(0.1, -0.8, -0.6), sep=0.34, Spine=_X(24) @ _Z(10), Head=_X(-6), st=(44, 62, -32))
    return 48, [(0, _guard(), 0.0), (12, wind, 0.0), (22, wind2, 0.0), (28, hit, 0.0), (34, fol, 0.0), (48, _guard(), 0.0)]


def _block(g=(-0.32, -0.3, 1.6), ch=-4):
    return _guard(g=g, d=(1, 0.05, 0.08), sep=0.6, Spine=_X(ch), Head=_X(2) @ _Z(8), st=(22, 40, -18))


def g_block_loop():
    """格挡：枪杆横架在额前（循环 24 帧，轻微顶动）。"""
    return 24, [(0, _block(), 0.0), (12, _block((-0.32, -0.31, 1.62), -5), 0.0), (24, _block(), 0.0)]


def g_parry():
    """完美弹反：枪杆从中段向右外侧一磕（第 4 帧 Parry），枪头顺势回指对手 → 戒备。"""
    return 24, [(0, _guard(), 0.0),
                (4, _guard(g=(-0.26, -0.18, 1.05), d=(-0.4, -0.85, 0.35), sep=0.38, Spine=_Z(-16), Head=_Z(14)), 0.0),
                (9, _guard(g=(-0.18, -0.22, 0.98), d=(0.2, -1, 0.15), sep=0.42, Spine=_X(8), st=(30, 44, -20)), 0.0),
                (24, _guard(), 0.0)]


def g_dodge():
    """闪避：压低身子向左后侧闪（位移由脚本移动 transform），第 14 帧落稳 → 起身戒备。"""
    low = _guard(g=(-0.2, 0.08, 0.7), d=(0.14, -1, 0.3), sep=0.55, Spine=_X(22) @ _Z(16), Chest=_Z(8),
                 Head=_X(-14), st=(36, 80, -34))
    crouch(low, 38, 76)
    return 24, [(0, _guard(), 0.0), (6, low, 0.0), (14, low, 0.0), (24, _guard(), 0.0)]


def g_hit():
    return AN.g_spear_hit()


def g_death():
    """死亡：胸口中招后仰 → 第 14 帧跪倒、枪脱手 → 第 26 帧侧倒在地（Death）→ 躺定。"""
    k0 = _guard()
    k1 = _guard(g=(-0.24, 0.14, 0.95), d=(0.1, -0.7, 0.7), sep=0.5, Spine=_X(-16), Chest=_X(-10), Head=_X(-14), st=(10, 16, -8))
    k2 = P_(Spine=_X(26), Chest=_X(10), Head=_X(16), L=(20, 10), LF=30, R=(26, 14), RF=36)
    LG(k2, 0, 90, 50)
    k3 = P_(Hips=_Y(80) @ _X(10), Spine=_X(10), Head=_Z(10) @ _X(6), L=(60, 30), LF=30, R=(40, -10), RF=50)
    LG(k3, 30, 50, 10, "Left")
    LG(k3, 10, 30, 10, "Right")
    k4 = P_(Hips=_Y(86) @ _X(12), Spine=_X(12), Neck=_Z(6), Head=_X(10), L=(70, 30), LF=24, R=(36, -10), RF=56)
    LG(k4, 34, 56, 10, "Left")
    LG(k4, 12, 34, 10, "Right")
    return 40, [(0, k0, 0.0), (5, k1, 0.0), (14, k2, 0.0), (26, k3, 0.0), (40, k4, 0.0)]


def g_execute():
    """处决：双手把枪高举、枪头朝前下（第 16 帧）→ 第 24 帧向前下方猛扎（Execute；跪地的对象在身前约 1.8 m，枪尖落在
    离地 0.35 m 左右）→ 拔出 → 收势。"""
    hi = P_(Spine=_X(-8), Chest=_X(-4), Head=_X(10))
    lunge(hi, 16, 26, -10)
    wield(hi, (-0.05, -0.2, 1.6), (0.0, -0.6, -0.8), 0.32, q0r=(150, 10, 60, 0, 0), q0l=(150, -10, 60, 0, 0))
    stab = P_(Spine=_X(30), Chest=_X(10), Head=_X(14))
    lunge(stab, 40, 70, -26)
    wield(stab, (-0.06, -0.35, 1.08), (0.0, -0.94, -0.34), 0.34, q0r=(80, 10, 40, 0, 0), q0l=(90, -10, 30, 0, 0))
    hold = P_(Spine=_X(32), Chest=_X(10), Head=_X(16))
    lunge(hold, 40, 70, -26)
    wield(hold, (-0.06, -0.33, 1.06), (0.0, -0.94, -0.34), 0.34, q0r=(80, 10, 40, 0, 0), q0l=(90, -10, 30, 0, 0))
    pull = P_(Spine=_X(10), Chest=_X(-2), Head=_X(8))
    lunge(pull, 24, 40, -16)
    wield(pull, (-0.1, -0.15, 1.15), (0.0, -0.9, -0.4), 0.34, q0r=(110, 10, 60, 0, 0), q0l=(120, -10, 50, 0, 0))
    return 48, [(0, _guard(), 0.0), (16, hi, 0.0), (24, stab, 0.0), (30, hold, 0.0), (36, pull, 0.0), (48, _guard(), 0.0)]


def g_cannon_fire():
    """点火开炮：同 A2_FireCannon（站位：炮尾火门在脚底原点左 0.5、前 1.0、高 0.87 m），改时为 40 帧，第 18 帧点火（CannonFire）。"""
    return _retime(*AN.g_fire_cannon(), [(0, 0), (16, 18), (30, 26), (64, 40)])


def g_winch_loop():
    """转水轮/绞盘：双手推横杆，前倾原地迈步（循环 24 帧；绞盘随脚本转）。"""
    return A2._step_cycle(24, lambda t: dict(L=(76, -6), LF=22, R=(76, -6), RF=22, Spine=_X(30), Chest=_X(6), Head=_X(-16)),
                          -0.07, 28)


def g_raise_flag():
    """升旗/挥旗：双手握竖旗杆从胸前举高（第 12 帧）→ 向左右各挥一次 → 立在身前。旗杆挂 SOCKET_Hand_R。"""
    def k(g, d, sp=0.0):
        P = P_(Spine=_X(sp), Head=_X(-10))
        LG(P, 10, 14, -4, "Left")
        return wield(P, g, d, 0.42, q0r=(40, 10, 70, 0, 0), q0l=(90, -10, 60, 0, 0), front="L")
    return 32, [(0, k((-0.05, -0.2, 0.95), (0, -0.1, 1)), 0.0), (12, k((-0.05, -0.22, 1.3), (0, -0.1, 1), -6), 0.0),
                (18, k((0.0, -0.22, 1.32), (-0.5, -0.1, 0.85), -6), 0.0), (24, k((-0.08, -0.22, 1.32), (0.5, -0.1, 0.85), -6), 0.0),
                (32, k((-0.05, -0.2, 1.1), (0, -0.05, 1)), 0.0)]


# ---------------------------------------------------------------- 玩家 P1
def g_pull_lever():
    """拉闸杆：双手握过头的杆（第 8 帧）→ 全身下坐往下拉（第 20 帧 Lever）→ 松手站直。"""
    a = P_(Spine=_X(-6), Head=_X(-14))
    reach(a, "R", (-0.08, -0.35, 1.85), (0, 0, 1), q0=(150, 10, 20, 0, 0))
    reach(a, "L", (0.08, -0.35, 1.85), (0, 0, 1), q0=(150, 10, 20, 0, 0))
    b = P_(Spine=_X(18), Head=_X(-4))
    crouch(b, 30, 56)
    reach(b, "R", (-0.08, -0.4, 1.15), (0, 0, 1), q0=(110, 10, 40, 0, 0))
    reach(b, "L", (0.08, -0.4, 1.15), (0, 0, 1), q0=(110, 10, 40, 0, 0))
    return 32, [(0, C._base(), 0.0), (8, a, 0.0), (20, b, 0.0), (26, b, 0.0), (32, C._base(), 0.0)]


def g_beat_drum():
    """擂鼓（循环 24 帧）：站在鼓前，两槌交替落在鼓面（鼓面中心在身前 0.55 m、高 1.05 m），第 6/18 帧击中。"""
    def k(rh, lh):
        P = P_(Spine=_X(6), Head=_X(4))
        LG(P, 8, 12, -4, "Left")
        reach(P, "R", (-0.12, -0.42, rh), (0.0, -0.6, 0.4), q0=(80, 10, 60, 0, 0))
        reach(P, "L", (0.12, -0.42, lh), (0.0, -0.6, 0.4), q0=(80, 10, 60, 0, 0))
        return P
    return 24, [(0, k(1.4, 1.1), 0.0), (6, k(1.08, 1.32), 0.0), (12, k(1.3, 1.4), 0.0), (18, k(1.32, 1.08), 0.0),
                (24, k(1.4, 1.1), 0.0)]


def g_carry_bucket():
    """提两桶水走（循环 32 帧）：两臂下垂略外张、肩下沉，桶挂 SOCKET_Hand_L/R。"""
    return A2._step_cycle(32, lambda t: dict(L=(4, 16), LF=6, R=(4, 16), RF=6, Spine=_X(4), Chest=_X(-2), LeftShoulder=_Y(-6),
                                             RightShoulder=_Y(6)), -0.03, 20)


def g_throw_water():
    """泼水：右手提桶梁、左手托桶底往后一荡（第 8 帧）→ 向前上方泼出（第 16 帧 Splash）→ 收回。"""
    back = P_(Spine=_X(10) @ _Z(-16), R=(-30, 10), RF=20, L=(-10, 0), LF=60)
    LG(back, 26, 40, -14, "Left")
    out = P_(Spine=_X(14) @ _Z(10), R=(110, 0), RF=10, L=(90, -10), LF=40, Head=_X(-6))
    lunge(out, 34, 50, -20)
    return 32, [(0, C._base(), 0.0), (8, back, 0.0), (16, out, 0.0), (20, out, 0.0), (32, C._base(), 0.0)]


def g_light_fuse():
    """点引信：蹲下、右手火绳伸向身前地面高 0.3 m 的引线（第 14 帧 Ignite）→ 起身后退一步。"""
    d = P_(Spine=_X(30), Head=_X(12), L=(20, 30), LF=40)
    crouch(d, 60, 110)
    reach(d, "R", (-0.1, -0.38, 0.72), (0, -0.6, -0.4), q0=(60, 10, 30, 0, 0))   # 未落地坐标（下蹲髋降约 0.35 m）
    up = P_(Spine=_X(-4), R=(30, 10), RF=40, Head=_X(-6))
    LG(LG(up, -14, 4, -10, "Right"), 4, 6, 0, "Left")
    return 36, [(0, C._base(), 0.0), (10, d, 0.0), (14, d, 0.0), (24, up, 0.0), (36, C._base(), 0.0)]


def g_plant_flag():
    """插旗：双手握竖杆举高（第 10 帧）→ 往身前地面一戳（第 18 帧 Plant）→ 松手退后看。"""
    def k(gz, sp):
        P = P_(Spine=_X(sp), Head=_X(-6))
        LG(P, 16, 24, -8, "Left")
        return wield(P, (-0.04, -0.32, gz), (0, -0.05, 1), 0.3, q0r=(60, 10, 60, 0, 0), q0l=(90, -10, 60, 0, 0), front="L")
    end = P_(Head=_X(-12), Chest=_X(-3))
    return 36, [(0, k(0.95, 0), 0.0), (10, k(1.35, -4), 0.0), (18, k(0.9, 14), 0.0), (24, k(0.9, 12), 0.0), (36, end, 0.0)]


def g_close_gate():
    """推门关门：双手平推门扇，侧身顶肩往前推（循环段 0–32；关上在第 32 帧）。"""
    return A2._step_cycle(32, lambda t: dict(L=(88, 6), LF=18, R=(88, 6), RF=18, Spine=_X(26), Chest=_X(4), Head=_X(-10)), -0.07, 30)


def g_help_up():
    """扶起：俯身右手伸向地上的人（第 10 帧握住）→ 往后一拉（第 22 帧）→ 站直。"""
    a = P_(Spine=_X(40), Chest=_X(10), Head=_X(10), L=(10, 10), LF=40)
    crouch(a, 30, 50)
    reach(a, "R", (-0.05, -0.5, 0.64), None, q0=(70, 10, 10, 0, 0))
    b = P_(Spine=_X(6), Chest=_X(-4), Head=_X(0), L=(10, 10), LF=30)
    LG(LG(b, -16, 6, -10, "Right"), 18, 24, -6, "Left")
    reach(b, "R", (-0.08, -0.45, 0.95), None, q0=(60, 10, 20, 0, 0))
    return 36, [(0, C._base(), 0.0), (10, a, 0.0), (22, b, 0.0), (36, C._base(), 0.0)]


def g_lookout():
    return AN.g_look_out_loop()


def g_kneel():
    """单膝跪（停在末帧）：记谱前 / 祭奠。"""
    k = P_(Spine=_X(14), Head=_X(16), L=(30, -10), LF=60, R=(20, 0), RF=30)
    LG(k, 80, 90, -10, "Left")
    LG(k, -10, 100, 40, "Right")
    return 24, [(0, C._base(), 0.0), (10, P_(Spine=_X(8)), 0.0), (24, k, 0.0)]


# ---------------------------------------------------------------- 义师
def g_ally_idle():
    """义师待机（循环 48 帧）：枪立在右手边，左手垂下，重心换脚。"""
    def k(sw):
        P = P_(L=(4, 6), LF=10, Spine=_Z(sw), Head=_Z(-sw * 2))
        reach(P, "R", (-0.26, -0.06, 1.05), (0, 0, 1), q0=(30, 20, 70, 0, 0))
        return P
    return 48, [(0, k(2), 0.0), (24, k(-2), 0.0), (48, k(2), 0.0)]


def g_ally_fight():
    """义师刺枪（36 帧，第 14 帧 AttackHit）：比玩家的一段刺慢。"""
    return AN.g_spear_thrust()          # 改时到 36 帧、命中 14 见 A3_SPEC


def g_ally_shoot():
    """弓手放箭（40 帧）：侧身、左臂前伸持弓、右手拉弦到腮（18–26 满弓）→ 第 28 帧放箭（AttackHit）。"""
    def k(rf, rside, rfwd):
        P = P_(Hips=_Z(-70), Neck=_Z(60), Head=_X(-2), L=(90, 0), LF=4, R=(rfwd, rside), RF=rf)
        LG(P, 10, 14, -4, "Left")
        LG(P, -6, 6, 2, "Right")
        return P
    rel = k(60, 30, 80)
    return 40, [(0, P_(L=(20, 10), LF=20), 0.0), (8, k(60, -10, 70), 0.0), (18, k(140, 0, 90), 0.0), (26, k(142, 0, 90), 0.0),
                (28, rel, 0.0), (40, P_(L=(20, 10), LF=20), 0.0)]


def g_ally_shield():
    """牌手盾撞（xlsx A3-A-34）：半蹲举藤牌（左手）→ 往回收身蓄力（第 12 帧）→ 第 21 帧连人带牌撞出（AttackHit）→ 收回举牌。"""
    def k(sp, lf, st, hold=(70, -20)):
        P = P_(Spine=_X(sp), Head=_X(-8), L=hold, LF=lf, R=(40, 10), RF=80)
        lunge(P, *st)
        return P
    guard = k(14, 70, (24, 40, -14))
    return 36, [(0, guard, 0.0), (12, k(4, 100, (14, 30, -10), (55, -30)), 0.0), (21, k(26, 40, (42, 60, -30), (85, -10)), 0.0),
                (26, k(24, 45, (40, 58, -28), (82, -10)), 0.0), (36, guard, 0.0)]


def g_ally_death():
    """义师阵亡：向前跪倒（第 14 帧）→ 扑地（第 24 帧 Death）。"""
    k1 = P_(Spine=_X(-12), Head=_X(-12), L=(40, 40), LF=20, R=(40, 40), RF=20)
    k2 = P_(Spine=_X(30), Chest=_X(10), Head=_X(10), L=(30, 10), LF=30, R=(30, 10), RF=30)
    LG(k2, 0, 90, 50)
    k3 = P_(Hips=_X(80), Spine=_X(6), Neck=_Z(60), Head=_X(-10), L=(150, 40), LF=30, R=(20, 30), RF=20)
    LG(k3, -10, 20, 40)
    return 36, [(0, C._base(), 0.0), (5, k1, 0.0), (14, k2, 0.0), (24, k3, 0.0), (36, k3, 0.0)]


def g_ally_carry():
    """抬担架 / 扛东西走（循环 32 帧）：双手在身侧低处握杆。"""
    return A2._step_cycle(32, lambda t: dict(L=(14, 6), LF=40, R=(14, 6), RF=40, Spine=_X(6), Head=_X(2)), -0.04, 20)


def g_ally_flee():
    """溃退（循环 16 帧）：弯腰快跑、回头看。"""
    up = lambda t: dict(Spine=_X(20), Neck=_Z(40), Head=_X(-4), L=(30, 20), LF=70, R=(-20, 20), RF=60)
    return A2._step_cycle(16, up, -0.06, 36)


def g_ally_cheer():
    """欢呼（循环 24 帧）：右手举兵器过头一下一下挥，左手握拳。"""
    return 24, [(0, P_(R=(160, 20), RF=20, L=(60, 20), LF=110, Head=_X(-14)), 0.0),
                (12, P_(R=(170, 10), RF=4, L=(70, 20), LF=110, Head=_X(-18), Chest=_X(-4)), 0.0),
                (24, P_(R=(160, 20), RF=20, L=(60, 20), LF=110, Head=_X(-14)), 0.0)]


# ---------------------------------------------------------------- 百姓
def g_civ_panic():
    """惊慌（循环 24 帧）：双手抱头、原地转头四顾。"""
    def k(n, sp):
        P = P_(Spine=_X(sp), Neck=_Z(n), Head=_X(6))
        for s, x in (("L", 0.07), ("R", -0.07)):
            reach(P, s, at_bone(P, "Head", (x, 0.02, 0.1)), None, q0=(120, 40, 130, 0, 0))
        return P
    return 24, [(0, k(30, 10), 0.0), (8, k(-20, 14), 0.0), (16, k(10, 8), 0.0), (24, k(30, 10), 0.0)]


def g_civ_run():
    return AN.g_flee_loop()


def g_civ_hide():
    return C.gesture_keys("CowerLoop")


def g_civ_carry():
    """背包袱 / 扛袋快走（循环 24 帧）：前倾，双手在胸前攥着包袱带。"""
    return A2._step_cycle(24, lambda t: dict(L=(40, -20), LF=110, R=(40, -20), RF=110, Spine=_X(18), Head=_X(-6)), -0.05, 26)


def g_civ_kneel():
    """跪地哀求（停在末帧）：双膝跪、双手合在胸前一下一下作揖。"""
    hands = dict(L=(60, -22), LF=100, R=(60, -22), RF=100)
    k = LG(P_(Spine=_X(14), Head=_X(-6), **hands), 0, 90, 60)
    return 36, [(0, C._base(), 0.0), (14, LG(P_(Spine=_X(6), **hands), 50, 90, -20), 0.0), (24, k, 0.0),
                (30, LG(P_(Spine=_X(26), Head=_X(4), **hands), 0, 90, 60), 0.0), (36, k, 0.0)]


def g_civ_grieve():
    """哀哭（循环 48 帧）：跪坐，俯身掩面，肩膀一抽一抽。"""
    def k(sp):
        P = P_(Spine=_X(sp), Chest=_X(14), Head=_X(24))
        LG(P, 0, 150, 70)
        for s, x in (("L", 0.04), ("R", -0.04)):
            reach(P, s, at_bone(P, "Head", (x, -0.1, 0.0)), None, q0=(120, -10, 140, 0, 0))
        return P
    return 48, [(0, k(30), 0.0), (12, k(36), 0.0), (24, k(30), 0.0), (36, k(36), 0.0), (48, k(30), 0.0)]


def g_civ_receive():
    """领粮：双手捧着往前伸（第 10 帧接住）→ 收回胸前、点头致谢（停在末帧）。"""
    a = P_(Spine=_X(14), Head=_X(4))
    reach(a, "R", (-0.08, -0.42, 1.0), (0, 0, 1), q0=(70, -10, 30, 0, 0))
    reach(a, "L", (0.08, -0.42, 1.0), (0, 0, 1), q0=(70, -10, 30, 0, 0))
    b = P_(Spine=_X(20), Head=_X(20), L=(40, -20), LF=100, R=(40, -20), RF=100)
    return 36, [(0, C._base(), 0.0), (10, a, 0.0), (18, P_(L=(40, -20), LF=100, R=(40, -20), RF=100), 0.0), (28, b, 0.0),
                (36, P_(L=(40, -20), LF=100, R=(40, -20), RF=100, Head=_X(6)), 0.0)]


def g_civ_child_cry():
    """孩子哭（循环 24 帧）：两手背揉眼睛、肩一耸一耸。"""
    def k(sp):
        P = P_(Spine=_X(sp), Head=_X(10))
        for s, x in (("L", 0.03), ("R", -0.03)):
            reach(P, s, at_bone(P, "Head", (x, -0.1, 0.03)), None, q0=(120, -10, 140, 0, 0))
        return P
    return 24, [(0, k(6), 0.0), (6, k(10), 0.0), (12, k(6), 0.0), (18, k(10), 0.0), (24, k(6), 0.0)]


# ---------------------------------------------------------------- 阿贵 / 王叔杲 / 族老
def g_agui_spear():
    """阿贵刺枪（第 14 帧 AttackHit）：架势低、手往回缩、刺得犹豫。"""
    g0 = lambda **kw: _guard(g=(-0.2, 0.08, 0.86), sep=0.5, Spine=_X(6), Head=_X(-8), st=(18, 30, -12), **kw)
    return 32, [(0, g0(), 0.0),
                (8, _guard(g=(-0.24, 0.16, 0.86), d=(0.14, -1, 0.24), sep=0.55, Spine=_X(2), st=(16, 28, -12)), 0.0),
                (14, _guard(g=(-0.16, -0.24, 0.94), d=(0.08, -1, 0.1), sep=0.36, Spine=_X(10), Head=_X(-6), st=(30, 46, -22)), 0.0),
                (20, _guard(g=(-0.18, -0.16, 0.92), d=(0.1, -1, 0.14), sep=0.4, Spine=_X(8), st=(26, 40, -18)), 0.0),
                (32, g0(), 0.0)]


def g_agui_kneel():
    """阿贵跪下（W5 认罪/W8）：枪扔在地上，双膝跪、低头、两手撑地（停在末帧）。"""
    k = P_(Spine=_X(36), Chest=_X(12), Head=_X(30), L=(70, -6), LF=10, R=(70, -6), RF=10)
    LG(k, 20, 110, 50)
    return 36, [(0, C._base(), 0.0), (14, LG(P_(Spine=_X(10), Head=_X(16)), 50, 90, -20), 0.0), (36, k, 0.0)]


def g_agui_fear():
    """阿贵害怕（循环 12 帧）：缩身握枪、枪头发抖、往后看。"""
    def k(d):
        P = P_(Spine=_X(10), Neck=_Z(20 + d * 4), Head=_X(4))
        crouch(P, 16, 30)
        return wield(P, (-0.18, 0.04, 0.9), (0.1 + d * 0.03, -1, 0.45), 0.4, q0r=(10, 10, 40, 0, 0), q0l=(60, -10, 40, 0, 0))
    return 12, [(0, k(0), 0.0), (3, k(1), 0.0), (6, k(-1), 0.0), (9, k(1), 0.0), (12, k(0), 0.0)]


def g_agui_run():
    """阿贵跑（循环 16 帧）：枪拖在右手、身子前倾。"""
    def st(P, ph):
        reach(P, "R", (-0.3, 0.05, 0.82), (0.2, -0.9, 0.3), q0=(10, 20, 30, 0, 0))
    return _cycle(16, st, lambda ph: dict(Spine=_X(16), Head=_X(-8), L=(40 * math.sin(ph * 6.28), 10), LF=80), (40, 60, 14), -0.05)


def g_shugao_report():
    """王叔杲禀报：上前半步、双手捧卷拱手（第 12 帧）→ 低头说话 → 直身。"""
    hold = dict(L=(70, -20), LF=100, R=(70, -20), RF=100)
    return 48, [(0, C._base(), 0.0), (12, LG(P_(Spine=_X(18), Head=_X(10), **hold), 12, 18, -6, "Left"), 0.0),
                (30, LG(P_(Spine=_X(14), Head=_X(4), **hold), 12, 18, -6, "Left"), 0.0), (48, P_(**hold, Head=_X(2)), 0.0)]


def g_shugao_key():
    """王叔杲交钥匙（W5）：右手从怀里掏出钥匙（第 10 帧）→ 伸手递出（第 20 帧 Give）→ 收手。钥匙挂 SOCKET_Hand_R。"""
    a = P_(R=(40, -30), RF=120, Head=_X(10))
    b = P_(Spine=_X(10), Head=_X(4))
    reach(b, "R", (-0.1, -0.5, 1.15), (0, -0.2, 1), q0=(80, 10, 20, 0, 0))
    return 36, [(0, C._base(), 0.0), (10, a, 0.0), (20, b, 0.0), (26, b, 0.0), (36, C._base(), 0.0)]


def g_elder_book():
    """族老翻愧顽簿（xlsx A3-A-53，48 帧）：双手捧簿到胸前（第 10 帧）→ 右手伸到左页翻过一页（第 20–30 帧）→ 低头看，手微抖。王执也用。"""
    def k(d, flip=None):
        P = P_(Spine=_X(6), Head=_X(18))
        reach(P, "L", (0.13, -0.32, 1.12 - d), (0, -0.3, 1), q0=(60, -20, 80, 0, 0))
        reach(P, "R", flip or (-0.13, -0.32, 1.12 + d), (0, -0.3, 1), q0=(60, -20, 80, 0, 0))
        return P
    return 48, [(0, P_(L=(30, -10), LF=60, R=(30, -10), RF=60), 0.0), (10, k(0), 0.0), (20, k(0, (0.08, -0.34, 1.16)), 0.0),
                (26, k(0, (-0.02, -0.36, 1.2)), 0.0), (30, k(0), 0.0), (36, k(0.006), 0.0), (42, k(-0.006), 0.0), (48, k(0), 0.0)]


def g_elder_accuse():
    """族老指认（W5）：右手抬起直指前方（第 14 帧 Accuse）→ 手指一点一点 → 拂袖收回。"""
    p = lambda ar: P_(Spine=_X(4), Chest=_X(-4), Head=_X(-8), R=ar, RF=4, L=(10, 10), LF=40)
    return 48, [(0, C._base(), 0.0), (14, p((95, 18)), 0.0), (20, p((90, 18)), 0.0), (26, p((96, 18)), 0.0), (32, p((90, 18)), 0.0),
                (40, P_(R=(30, -30), RF=90), 0.0), (48, C._base(), 0.0)]


# ---------------------------------------------------------------- 静态姿势（伤兵 / 遗体 / 被绑）
def p_wounded_sit():
    P = P_(Spine=_X(-18), Chest=_X(-4), Neck=_Z(18), Head=_X(16), L=(26, -20), LF=90, R=(10, 20), RF=20)
    LG(P, 80, 110, -20, "Left")
    LG(P, 70, 40, 10, "Right")
    return P


def p_wounded_lie():
    P = P_(Hips=_X(-88), Spine=_X(4), Neck=_Z(-10), Head=_X(-14), L=(-4, 22), LF=25, R=(-6, 20), RF=20)
    LG(P, 30, 50, 10, "Left")
    LG(P, 0, 4, 10, "Right")
    return P


def p_corpse_side():
    P = P_(Hips=_Y(84), Spine=_X(18), Chest=_X(6), Neck=_X(14), Head=_X(10), L=(80, 10), LF=60, R=(60, -20), RF=50)
    LG(P, 50, 70, 10, "Left")
    LG(P, 30, 50, 10, "Right")
    return P


def p_corpse_prone():
    P = P_(Hips=_X(88), Spine=_X(-4), Neck=_Z(70) @ _X(-14), Head=_X(-6), L=(150, 50), LF=40, R=(10, 30), RF=10)
    LG(P, 4, 20, 50, "Left")
    LG(P, -2, 8, 50, "Right")
    return P


def _static(fn):
    return lambda: (4, [(0, fn(), 0.0), (4, fn(), 0.0)])


def g_bound_loop():
    """被绑在柱上（循环 72 帧）：双臂反剪在身后、低头，身体微微晃（柱子中心在身后 0.15 m）。"""
    def k(sw, hd):
        return P_(L=(-34, -10), LF=60, R=(-34, -10), RF=60, Spine=_X(10) @ _Z(sw), Head=_X(hd), Neck=_Z(-sw * 2))
    return 72, [(0, k(0, 24), 0.0), (24, k(3, 28), 0.0), (48, k(-3, 22), 0.0), (72, k(0, 24), 0.0)]


A3_ANIM = {
    # 玩家 P0
    "A3_CombatIdleLoop": g_combat_idle_loop, "A3_CombatWalk": g_combat_walk, "A3_CombatRun": g_combat_run,
    "A3_SpearThrust1": g_spear_thrust1, "A3_SpearThrust2": g_spear_thrust2, "A3_SpearSweep": g_spear_sweep,
    "A3_SpearHeavy": g_spear_heavy, "A3_BlockLoop": g_block_loop, "A3_Parry": g_parry, "A3_Dodge": g_dodge,
    "A3_Hit": g_hit, "A3_Death": g_death, "A3_Execute": g_execute, "A3_CannonFire": g_cannon_fire,
    "A3_WinchLoop": g_winch_loop, "A3_RaiseFlag": g_raise_flag,
    # 玩家 P1
    "A3_PullLever": g_pull_lever, "A3_BeatDrum": g_beat_drum, "A3_CarryBucket": g_carry_bucket, "A3_ThrowWater": g_throw_water,
    "A3_LightFuse": g_light_fuse, "A3_PlantFlag": g_plant_flag, "A3_CloseGate": g_close_gate, "A3_HelpUp": g_help_up,
    "A3_Lookout": g_lookout, "A3_Kneel": g_kneel,
    # 义师
    "A3_AllyIdle": g_ally_idle, "A3_AllyFight": g_ally_fight, "A3_AllyShoot": g_ally_shoot, "A3_AllyShield": g_ally_shield,
    "A3_AllyDeath": g_ally_death, "A3_AllyCarry": g_ally_carry, "A3_AllyFlee": g_ally_flee, "A3_AllyCheer": g_ally_cheer,
    # 百姓
    "A3_CivPanic": g_civ_panic, "A3_CivRun": g_civ_run, "A3_CivHide": g_civ_hide, "A3_CivCarry": g_civ_carry,
    "A3_CivKneel": g_civ_kneel, "A3_CivGrieve": g_civ_grieve, "A3_CivReceive": g_civ_receive, "A3_CivChildCry": g_civ_child_cry,
    # 阿贵 / 王叔杲 / 族老
    "A3_AguiSpear": g_agui_spear, "A3_AguiKneel": g_agui_kneel, "A3_AguiFear": g_agui_fear, "A3_AguiRun": g_agui_run,
    "A3_ShugaoReport": g_shugao_report, "A3_ShugaoKey": g_shugao_key, "A3_ElderBook": g_elder_book,
    "A3_ElderAccuse": g_elder_accuse,
    # 静态姿势 / 被绑（伤兵、遗体、阿贵母亲）
    "A3_WoundedSit": _static(p_wounded_sit), "A3_WoundedLie": _static(p_wounded_lie),
    "A3_CorpseSide": _static(p_corpse_side), "A3_CorpseProne": _static(p_corpse_prone), "A3_BoundLoop": g_bound_loop,
}

# 帧数按 Docs/第三幕_建模清单.xlsx「动画」表（md 没写帧数的 P1 动作以 xlsx 为准）；值 = 新总帧数 或 分段映射 [(原帧, 新帧), ...]
A3_SPEC = {
    "A3_PullLever": 24, "A3_ThrowWater": 30, "A3_LightFuse": 24, "A3_PlantFlag": 28, "A3_CloseGate": 36, "A3_HelpUp": 32,
    "A3_Lookout": 48, "A3_Kneel": 40, "A3_AllyFight": [(0, 0), (12, 14), (30, 36)], "A3_AllyCheer": 32, "A3_AllyFlee": 28,
    "A3_CivPanic": 32, "A3_CivRun": 24, "A3_CivHide": 40, "A3_CivCarry": 32, "A3_CivKneel": 40, "A3_CivReceive": 32,
    "A3_CivChildCry": 40, "A3_AguiSpear": [(0, 0), (14, 16), (32, 36)], "A3_AguiKneel": 40, "A3_AguiFear": 32,
    "A3_AguiRun": 24, "A3_ShugaoKey": 32, "A3_ElderAccuse": 32,
}


def _spec(name, fn):
    sp = A3_SPEC.get(name)
    if sp is None:
        return fn

    def wrapped():
        T, keys = fn()
        segs = sp if isinstance(sp, list) else [(0, 0), (T, sp)]
        return _retime(T, keys, segs)
    return wrapped


C.GESTURE_HOOKS.update({k: A2._grounded(AN._filled(_spec(k, v))) for k, v in A3_ANIM.items()})


# ====================================================================== 道具：枪 / 扁担 / 藤牌
obj, tb, el, bx, anchor = A2.obj, A2.tb, A2.el, A2.bx, A2.anchor


def build_spear(name="Spear", L_front=1.9, L_back=0.5, tassel=True):
    """长枪：原点 = 后手握点，+Z 朝枪头；杆前 L_front、后 L_back。"""
    mb = K.MB()
    mb.cyl(0, 0, -L_back, L_front, 0.016, "M_A3C_SpearWood", seg=8, r_top=0.014)
    mb.cyl(0, 0, -L_back - 0.06, -L_back, 0.019, "M_A3C_SpearIron", seg=8)                 # 鐏
    mb.cyl(0, 0, L_front - 0.02, L_front + 0.07, 0.02, "M_A3C_SpearIron", seg=8)           # 銎
    if tassel:
        mb.cyl(0, 0, L_front - 0.12, L_front, 0.055, "M_A3C_Tassel", seg=10, r_top=0.018)
    z = L_front + 0.07
    mb.prism([(-0.03, z), (0.03, z), (0.0, z + 0.26)], "y", -0.006, 0.006, "M_A3C_SpearEdge")
    mb.prism([(-0.006, z), (0.006, z), (0.0, z + 0.26)], "x", -0.012, 0.012, "M_A3C_SpearIron")
    obj(mb, name, uv=0.3)
    anchor("ANCHOR_FrontGrip", (0, 0, 0.56), 0.05)
    anchor("FX_Tip", (0, 0, z + 0.24), 0.04, kind="SPHERE")


def build_spear_agui():
    """阿贵的短枪：比王砚的短一截（2.0 m）、没有枪缨、杆上缠一道旧布。"""
    build_spear("Spear", 1.6, 0.4, tassel=False)
    mb = K.MB()
    mb.cyl(0, 0, 0.9, 1.02, 0.019, "M_A3C_OldBand", seg=8)
    obj(mb, "Wrap", uv=0.3)


def build_carry_pole():
    """扁担 + 两只竹筐（老农 / 货郎）：原点 = 扁担中点（扛肩处），筐底在 -1.0 m。ANCHOR_Shoulder 对齐右肩。"""
    mb = K.MB()
    with mb.at(0, 0, 0, rx=0):
        tb(mb, (-0.85, 0, 0), (0.85, 0, 0), 0.025, "M_A3C_Pole", seg=6)
    for sx in (-1, 1):
        x = sx * 0.78
        for a in range(3):
            ang = 2 * math.pi * a / 3
            tb(mb, (x, 0, -0.02), (x + 0.17 * math.cos(ang), 0.17 * math.sin(ang), -0.7), 0.004, "M_A3C_Rope", seg=3)
        mb.cyl(x, 0, -1.0, -0.7, 0.16, "M_A3C_Basket", seg=10, r_top=0.2)
        mb.cyl(x, 0, -0.72, -0.69, 0.205, "M_A3C_BasketDark", seg=10)
        el(mb, (x, 0, -0.7), 0.17, 0.17, 0.08, "M_A3C_Goods", seg=8, rings=3, zmin=0.0)
    obj(mb, "CarryPole", uv=0.3)
    anchor("ANCHOR_Shoulder", (0, 0, 0.03), 0.05)


def build_rattan_shield():
    """藤牌：圆盘 0.75 m，正面（-Y）中间凸起，背面横把手。原点 = 把手（挂 SOCKET_Hand_L 零变换，盘面朝前）。"""
    mb = K.MB()
    R = 0.375
    with mb.at(0, -0.06, 0, rx=90):
        for i, (r0, r1, mat) in enumerate(((R, R * 0.8, "M_A2S_Rattan"), (R * 0.8, R * 0.55, "M_A2S_RattanDark"),
                                           (R * 0.55, R * 0.3, "M_A2S_Rattan"))):
            mb.cyl(0, 0, -0.02 * i, -0.02 * i + 0.03, r0, mat, seg=14, r_top=r1)
        mb.cyl(0, 0, 0.03, 0.08, R * 0.3, "M_A2S_RattanDark", seg=10, r_top=0.05)
    mb.box(-0.06, -0.03, -0.012, 0.06, 0.0, 0.012, "M_A3C_Pole")
    obj(mb, "Shield", uv=0.3)


# ====================================================================== 静态烘焙（伤兵 / 遗体）
def _bake(char, pose_name, out_name, loc=(0, 0, 0), rz=0.0, tris=1350):
    """用 char 的人物摆 pose_name 姿势（含落地修正）→ 烘成静态网格 out_name，放在 loc、绕 Z 转 rz 度。"""
    rig = C.build_character(char, A3_CAST[char])
    mesh = next(o for o in rig.children if o.type == "MESH")
    _, keys = C.GESTURE_HOOKS[pose_name]()
    f, P, up = keys[0]
    for b, R in P.items():
        C.set_rot(rig, b, R)
    rig.pose.bones["Hips"].location = (0, up, 0)
    bpy.context.view_layer.update()
    dg = bpy.context.evaluated_depsgraph_get()
    me = bpy.data.meshes.new_from_object(mesh.evaluated_get(dg), preserve_all_data_layers=True, depsgraph=dg)
    me.transform(mesh.matrix_world)
    ob = bpy.data.objects.new(out_name, me)
    bpy.context.scene.collection.objects.link(ob)
    for o in [rig] + list(rig.children_recursive):
        bpy.data.objects.remove(o, do_unlink=True)
    if tris and sum(len(p.vertices) - 2 for p in me.polygons) > tris:     # 两个人放进一个 Props（≤3k）时减面
        mod = ob.modifiers.new("dec", "DECIMATE")
        mod.ratio = tris / sum(len(p.vertices) - 2 for p in me.polygons)
        bpy.context.view_layer.update()
        dg = bpy.context.evaluated_depsgraph_get()
        me2 = bpy.data.meshes.new_from_object(ob.evaluated_get(dg), depsgraph=dg)
        ob.modifiers.remove(mod)
        ob.data = me2
    ob.location = loc
    ob.rotation_euler = (0, 0, math.radians(rz))
    bpy.context.view_layer.update()
    ob.data.transform(ob.matrix_basis)                  # 应用变换（规格要求旋转/缩放为 0/1）
    ob.matrix_basis = Matrix.Identity(4)
    return ob


def _mat_cloth(mb, x0, x1, y0, y1, z, sag, mat, n=6, drape=0.0):
    """盖布：网格片，中间高四周垂（简易覆盖，双面）。"""
    grid = []
    for j in range(n + 1):
        row = []
        for i in range(n + 1):
            u, v = i / n, j / n
            x, y = x0 + (x1 - x0) * u, y0 + (y1 - y0) * v
            edge = max(abs(u - 0.5), abs(v - 0.5)) * 2
            zz = z + sag * (1 - edge ** 2) - drape * max(0.0, edge - 0.7) / 0.3
            row.append(mb.addv([(x, y, max(0.01, zz))]))
        grid.append(row)
    for j in range(n):
        for i in range(n):
            q = [grid[j][i], grid[j][i + 1], grid[j + 1][i + 1], grid[j + 1][i]]
            mb.face(q, mat)
            mb.face(list(reversed(q)), mat)


def build_wounded():
    """伤兵静态件（2 个）：Wounded_Sit 靠墙坐（背后 +Y 0.35 m 处是墙）、Wounded_Lie 躺在地上铺的草席上。"""
    _bake("NPC_A3_Wounded_A", "A3_WoundedSit", "Wounded_Sit", (-0.7, 0, 0))
    _bake("NPC_A3_Wounded_B", "A3_WoundedLie", "Wounded_Lie", (0.9, 0, 0))
    mb = K.MB()
    mb.box(0.55, -0.95, 0, 1.25, 0.95, 0.015, "M_Thatch")
    obj(mb, "Mat", uv=0.5)
    anchor("ANCHOR_Wall", (-0.7, 0.35, 0), 0.1)
    anchor("ANCHOR_Tend_Sit", (-0.7, -0.75, 0), 0.1)
    anchor("ANCHOR_Tend_Lie", (0.3, 0, 0), 0.1)


def build_corpse():
    """遗体静态件（2 个，不血腥）：Corpse_Side 侧卧、Corpse_Prone 俯卧；各带一张可单独隐藏的盖席 Cover_*。"""
    a = _bake("NPC_A3_Corpse_A", "A3_CorpseSide", "Corpse_Side", (-0.8, 0, 0))
    b = _bake("NPC_A3_Corpse_B", "A3_CorpseProne", "Corpse_Prone", (0.8, 0, 0))
    for ob, nm in ((a, "Cover_Side"), (b, "Cover_Prone")):
        bb = [ob.matrix_world @ V(c) for c in ob.bound_box]
        x0, x1 = min(p.x for p in bb) - 0.12, max(p.x for p in bb) + 0.12
        y0, y1 = min(p.y for p in bb) - 0.12, max(p.y for p in bb) + 0.12
        top = max(p.z for p in bb)
        mb = K.MB()
        _mat_cloth(mb, x0, x1, y0, y1, top * 0.7, top * 0.3, "M_Thatch", n=8, drape=top * 1.0)
        obj(mb, nm, uv=0.5)


def build_stretcher_wounded():
    """担架伤兵：两根 2.2 m 抬杆 + 帆布 + 躺着的头伤伤兵。ANCHOR_Carry_F/B 是前后抬杆人站位（面朝 -Y 行进）。"""
    mb = K.MB()
    for x in (-0.3, 0.3):
        tb(mb, (x, -1.1, 0.5), (x, 1.1, 0.5), 0.025, "M_A3C_StretcherWood", seg=6)
        for y in (-0.8, 0.8):
            mb.box(x - 0.025, y - 0.025, 0.0, x + 0.025, y + 0.025, 0.5, "M_A3C_StretcherWood")
    for y in (-0.82, 0.82):
        tb(mb, (-0.3, y, 0.5), (0.3, y, 0.5), 0.018, "M_A3C_StretcherWood", seg=5)
    mb.box(-0.29, -0.85, 0.48, 0.29, 0.85, 0.5, "M_A3C_StretcherCloth")
    obj(mb, "Stretcher", uv=0.5)
    ob = _bake("NPC_A3_Wounded_B", "A3_WoundedLie", "Wounded", (0, 0, 0), rz=0)
    bb = [ob.matrix_world @ V(c) for c in ob.bound_box]
    cx, cy = (min(p.x for p in bb) + max(p.x for p in bb)) / 2, (min(p.y for p in bb) + max(p.y for p in bb)) / 2
    ob.data.transform(Matrix.Translation((-cx, -cy, 0.5)))
    anchor("ANCHOR_Carry_F", (0, -1.25, 0), 0.1)
    anchor("ANCHOR_Carry_B", (0, 1.25, 0), 0.1)


def build_bier():
    """担架 / 尸架：竹木架 + 白布（盖着的人形隆起），两根抬杆。"""
    mb = K.MB()
    for x in (-0.3, 0.3):
        tb(mb, (x, -1.15, 0.45), (x, 1.15, 0.45), 0.025, "M_A3C_StretcherWood", seg=6)
        for y in (-0.85, 0.85):
            mb.box(x - 0.025, y - 0.025, 0.0, x + 0.025, y + 0.025, 0.45, "M_A3C_StretcherWood")
    for y in (-0.85, -0.3, 0.3, 0.85):
        tb(mb, (-0.3, y, 0.45), (0.3, y, 0.45), 0.016, "M_A3C_StretcherWood", seg=5)
    obj(mb, "Bier", uv=0.5)
    cl = K.MB()
    _mat_cloth(cl, -0.36, 0.36, -0.95, 0.95, 0.5, 0.16, "M_CH_Bandage", n=8, drape=0.12)
    obj(cl, "Cloth", uv=0.5)
    anchor("ANCHOR_Carry_F", (0, -1.3, 0), 0.1)
    anchor("ANCHOR_Carry_B", (0, 1.3, 0), 0.1)


# ====================================================================== 注册
def recipes():
    R = {}
    for n in A3_CAST:
        R[n] = ("Characters", (lambda nm=n: build_a3_character(nm)))
    for k in A3_ANIM:
        R[f"CH_WangYan_1941@{k}"] = ("Characters", (lambda kk=k: C.build_gesture(kk)))
    R.update({
        "PROP_A3_Spear": ("Props", build_spear),
        "PROP_A3_Spear_Agui": ("Props", build_spear_agui),
        "PROP_A3_CarryPole": ("Props", build_carry_pole),
        "PROP_A3_RattanShield": ("Props", build_rattan_shield),
        "PROP_A3_Wounded": ("Props", build_wounded),
        "PROP_A3_Corpse": ("Props", build_corpse),
        "PROP_A3_Stretcher_Wounded": ("Props", build_stretcher_wounded),
        "PROP_A3_Bier": ("Props", build_bier),
    })
    return R
