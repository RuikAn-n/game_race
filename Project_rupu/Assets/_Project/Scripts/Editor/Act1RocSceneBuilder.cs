#if UNITY_EDITOR
using System.Collections.Generic;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Rupu.EditorTools
{
    /// <summary>
    /// 第一幕（1941 归堡）实景场景：在 ROC 永昌堡全图上叠剧情。
    /// - 祠堂用室内白模 BLD_INT_AncestralHall 替换 ROC 外壳，互动点/站位取它的 ANCHOR_*；
    /// - 人物全部是正式模型（族老/三派/族亲/日军/小贩/街坊），NPC 挂 Act1ClanActor（说话、动作、走路、面向玩家）；
    /// - 道具：族谱套件、香、父亲墨污牌位与照片、残旗石阶、日机、军刀/步枪、摊货、铺门与箱子；
    /// - 街市：小摊三种、燃烧铺面、被炸废墟、弹坑、路灯/告示/邮筒/石墩、哨卡；特效 PF_VFX_*。
    /// 模型缺失时退回胶囊/方块占位，场景仍然能跑。
    /// </summary>
    public static class Act1RocSceneBuilder
    {
        const string Chars = "Assets/Art/Characters";
        const string Props = "Assets/Art/Props";
        const string VfxDir = "Assets/Art/VFX";
        static Transform story;
        static Transform playerT;

        [MenuItem("入谱/第一幕/用 ROC 永昌堡场景生成")]
        public static void Create()
        {
            if (EditorApplication.isPlaying)
            {
                EditorUtility.DisplayDialog("先退出 Play", "不能在 Play 模式生成场景。请先停止 Play，再执行。", "知道了");
                return;
            }
            UnityEngine.SceneManagement.Scene scene = EditorSceneManager.OpenScene("Assets/_Rupu/Scenes/Map_Yongchang_ROC.unity");
            EditorSceneManager.SaveScene(scene, "Assets/Scenes/Act1_ROC.unity");

            DisableOldPlayerAndCast();
            GameObject root = new GameObject("ACT1_ROC_STORY");
            story = root.transform;

            Material lip = Mat("Act1ROCLip", new Color(0.33f, 0.27f, 0.20f));
            Material stone = Mat("Act1ROCStone", new Color(0.30f, 0.29f, 0.25f));

            // ---------------------------------------------------------------- 玩家（祖祠前庭，朝北看祠堂门）
            GameObject player = new GameObject("Act1_Player");
            player.transform.position = new Vector3(-20f, 0.15f, 16f);
            CharacterController controller = player.AddComponent<CharacterController>();
            controller.center = new Vector3(0f, 1f, 0f);
            controller.height = 2f;
            controller.radius = 0.35f;
            Act1Player walker = player.AddComponent<Act1Player>();
            walker.startYaw = 0f;
            playerT = player.transform;

            GameObject bodyModel = LoadModel($"{Chars}/CH_WangYan_1941/CH_WangYan_1941.fbx", player.transform, Vector3.zero, Quaternion.identity);
            if (bodyModel != null) bodyModel.name = "WangYan_Visual";
            SetupAnimator(bodyModel);

            GameObject cameraObject = new GameObject("Act1_ROC_Camera");
            cameraObject.tag = "MainCamera";
            Camera camera = cameraObject.AddComponent<Camera>();
            camera.fieldOfView = 60f;
            camera.farClipPlane = 400f;
            camera.clearFlags = CameraClearFlags.SolidColor;
            camera.backgroundColor = new Color(0.34f, 0.36f, 0.37f);
            cameraObject.AddComponent<UniversalAdditionalCameraData>();
            cameraObject.AddComponent<AudioListener>();

            GameObject systems = new GameObject("Act1_Systems");
            Act1Director director = systems.AddComponent<Act1Director>();
            director.player = walker;
            walker.director = director;

            // ---------------------------------------------------------------- 祠堂
            Shrine shrine = BuildShrine(lip, stone);

            GameObject pages = MakeInteractable(story, "Interact_残谱拼合", "pages", "残谱拼合", "按住 E 拼合散页", shrine.pagesPoint, 2.8f, 1.8f);
            GameObject clan = MakeInteractable(story, "Interact_族亲", "clan", "族亲", "按住 E 听族亲怎么说", shrine.clanPoint, 3.2f, 1f);
            GameObject memorial = MakeInteractable(story, "Interact_父亲灵位", "memorial", "父亲灵位", "按住 E 给父亲上炷香", shrine.prayPoint, 2.8f, 1.4f);

            // 族老（NPC_ClanElder + 手杖）在院门口迎王砚；族长王秉之（+ 拐）在正厅
            GameObject elder = Npc("NPC_ClanElder", "Elder_族老", new Vector3(-20f, 0f, 17.5f), 180f, "族老");
            HoldProp(elder, $"{Props}/PROP_Staff_Elder/PROP_Staff_Elder.fbx", new Vector3(0.38f, 0f, 0.12f), 0f);
            GameObject leader = Npc("NPC_WangBingzhi", "ClanLeader_王秉之", shrine.leaderStart, 180f, "王秉之");
            HoldProp(leader, $"{Props}/PROP_Cane_Bingzhi/PROP_Cane_Bingzhi.fbx", new Vector3(0.36f, 0f, 0.14f), 90f);
            director.elderStop = Marker("ElderStop", shrine.elderStop);

            // 族亲（冷遇/亲善）：互动点两侧。左边皱眉的族叔，右边驼背的族婶婆带着孙子
            Vector3 kin = shrine.clanPoint;
            Npc("NPC_ClanUncle", "Clan_族中冷遇", Ground(kin + new Vector3(-1.8f, 0f, 0.3f)), 90f, "族中冷遇");
            Npc("NPC_ClanGranny", "Clan_族中亲善", Ground(kin + new Vector3(1.8f, 0f, 0.6f)), 270f, "族中亲善");
            Npc("NPC_ClanBoy", "Clan_孩童", Ground(kin + new Vector3(2.4f, 0f, -0.2f)), 270f);

            // 三派（祠堂三拨人）：交谱派族老在西、烧谱派青年在东、藏谱派妇人带女儿在供桌前（让开上香的蒲团）
            GameObject jiaoActor = Npc("NPC_ClanJiao", "Faction_交谱派族老", shrine.jiao, 90f, "交谱派");
            GameObject shaoActor = Npc("NPC_ClanShao", "Faction_烧谱派青年", shrine.shao, 270f, "烧谱派");
            GameObject cangActor = Npc("NPC_ClanCang", "Faction_藏谱派妇人", shrine.cang, 180f, "藏谱派");
            Npc("NPC_ClanGirl", "Faction_藏谱派之女", Ground(shrine.cang + new Vector3(0.85f, 0f, 0.2f)), 180f);

            GameObject jiao = MakeFaction("Interact_交谱派", "faction_jiao", "交谱派", Toward(shrine.jiao, shrine.argueCenter, 1.1f));
            GameObject shao = MakeFaction("Interact_烧谱派", "faction_shao", "烧谱派", Toward(shrine.shao, shrine.argueCenter, 1.1f));
            GameObject cang = MakeFaction("Interact_藏谱派", "faction_cang", "藏谱派", shrine.cang + new Vector3(0f, 0f, -1.0f));

            // 日本军官 + 两名士兵：从祠堂门进来，站定在门厅（剧本：站定后才开口）
            GameObject officer = Npc("NPC_JpOfficer", "ShrineOfficer_日本军官", shrine.officer, 0f, "日本军官");
            GameObject guardA = Npc("NPC_JpSoldier_A", "ShrineGuard_A", shrine.soldierL, 0f, null, false);
            GameObject guardB = Npc("NPC_JpSoldier_B", "ShrineGuard_B", shrine.soldierR, 0f, null, false);

            director.flagPoint = null;
            director.clanPoint = clan.GetComponent<Act1Interactable>();
            director.memorialPoint = memorial.GetComponent<Act1Interactable>();
            director.pagesPoint = pages.transform;
            director.factionPoints.Add(jiao.GetComponent<Act1Interactable>());
            director.factionPoints.Add(shao.GetComponent<Act1Interactable>());
            director.factionPoints.Add(cang.GetComponent<Act1Interactable>());
            director.elder = elder != null ? elder.transform : null;
            director.clanLeader = leader != null ? leader.transform : null;
            director.shrineOfficer = officer.transform;
            director.shrineGuards = new[] { guardA.transform, guardB.transform };
            director.factionActors = new[] { jiaoActor.transform, shaoActor.transform, cangActor.transform };
            director.streetExit = Marker("StreetExit", new Vector3(-20f, 0f, 20f));
            director.factionCenter = shrine.argueCenter;
            director.clanStop = shrine.leaderStop;
            director.officerEntryOffset = new Vector3(0f, 0f, -6f);     // ROC 祠堂门朝南
            director.showOnIncense = shrine.showOnIncense;
            director.showOnPagesMended = shrine.showOnPages;
            director.hideOnPagesMended = shrine.hideOnPages;

            // ---------------------------------------------------------------- 街市：暴行、砸门、火光、旗杆
            BuildStreet(director, walker, lip, stone);

            // 残旗：环海门内的石阶上斜倒的旗杆（PROP_FallenFlag），互动点在旗面旧血旁
            Vector3 flagPos = BuildFallenFlag(stone);
            GameObject flag = MakeInteractable(story, "Interact_残旗入谱", "flag", "倒下的旗杆", "按住 E 触摸旗杆旧血", flagPos, 3.5f, 1.6f);
            director.flagPoint = flag.GetComponent<Act1Interactable>();

            CreatePlanes();

            // 雨：挂在相机上跟着玩家，打到屋顶就消失
            Vfx("PF_VFX_Rain", cameraObject.transform, Vector3.zero, Quaternion.identity, false);   // 保留预制体里相机上方 12 m 的偏移

            // Camera 与玩家绑定
            cameraObject.transform.SetParent(player.transform, false);
            cameraObject.transform.localPosition = new Vector3(0f, 1.75f, -3.4f);
            cameraObject.transform.localRotation = Quaternion.Euler(8f, 0f, 0f);
            walker.enabled = true;

            // UI 目标与交互对象
            SetInteractableRefs(pages, walker, director);
            SetInteractableRefs(clan, walker, director);
            SetInteractableRefs(memorial, walker, director);
            SetInteractableRefs(flag, walker, director);
            foreach (Act1Interactable p in director.factionPoints) SetInteractableRefs(p.gameObject, walker, director);

            // 场景光/雾
            RenderSettings.skybox = null;
            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(0.35f, 0.36f, 0.34f);
            RenderSettings.fogDensity = 0.006f;
            Light sun = FindSun();
            if (sun != null) sun.intensity = 0.8f;

            EditorSceneManager.SaveScene(scene, "Assets/Scenes/Act1_ROC.unity");
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene("Assets/Scenes/Act1_ROC.unity", true),
                new EditorBuildSettingsScene("Assets/Scenes/Act1_1941.unity", true),
                new EditorBuildSettingsScene("Assets/_Rupu/Scenes/Map_Yongchang_ROC.unity", true)
            };
            AssetDatabase.SaveAssets();
            Debug.Log("[Act1ROC] 已生成 Act1_ROC.unity：ROC 全景 + 祠堂内景 + 第一幕剧情（正式人物/道具/特效）");
        }

        // ==================================================================== 祠堂
        class Shrine
        {
            public Vector3 pagesPoint, clanPoint, prayPoint, elderStop, leaderStart, leaderStop, argueCenter;
            public Vector3 jiao, shao, cang, officer, soldierL, soldierR;
            public GameObject[] showOnIncense = new GameObject[0], showOnPages = new GameObject[0], hideOnPages = new GameObject[0];
        }

        static Shrine BuildShrine(Material lip, Material stone)
        {
            var s = new Shrine();
            GameObject rocHall = GameObject.Find("BLD_ROC_AncestralHall");
            GameObject hall = null;
            if (rocHall != null)
            {
                Transform t = rocHall.transform;
                hall = RupuMapBuilder.PlaceForStory("BLD_INT_AncestralHall", t.parent, t.localPosition, t.localEulerAngles.y, "BLD_INT_AncestralHall");
            }
            if (hall == null)
            {   // 没有室内白模：退回旧做法（切开 ROC 外壳的门洞 + 方块道具）
                BuildShrineEntranceFallback(lip);
                s.pagesPoint = new Vector3(-20f, 0.9f, 30f); s.clanPoint = new Vector3(-20f, 0.9f, 27.5f); s.prayPoint = new Vector3(-20f, 0.9f, 36f);
                s.elderStop = new Vector3(-21.8f, 0f, 26.2f); s.leaderStart = new Vector3(-20f, 0f, 44f); s.leaderStop = new Vector3(-20f, 0f, 32f);
                s.argueCenter = new Vector3(-20f, 0f, 33f); s.jiao = new Vector3(-25f, 0f, 32f); s.shao = new Vector3(-15f, 0f, 32f);
                s.cang = new Vector3(-20.5f, 0f, 39f); s.officer = new Vector3(-20f, 0f, 28f); s.soldierL = new Vector3(-22f, 0f, 29f);
                s.soldierR = new Vector3(-18f, 0f, 29f);
                Box(story, "Shrine_Table", new Vector3(-20f, 0.75f, 30f), new Vector3(3.2f, 0.15f, 1.2f), lip);
                return s;
            }
            rocHall.SetActive(false);
            Physics.SyncTransforms();
            Vector3 A(string n) { Transform a = FindDeep(hall.transform, "ANCHOR_" + n); return a != null ? a.position : hall.transform.position; }

            s.pagesPoint = A("pages_join");
            s.prayPoint = A("pray");
            s.clanPoint = A("courtyard_kin");
            s.elderStop = A("elder_lead");
            s.leaderStart = A("wangbingzhi");
            s.officer = A("officer");
            s.soldierL = A("soldier_L");
            s.soldierR = A("soldier_R");
            s.jiao = A("faction_jiao");
            s.shao = A("faction_shao");
            // 锚点里藏谱派正好站在上香的蒲团上：往前（院子方向）让 2.2 m，母女站在月台前沿
            s.cang = Ground(A("faction_cang") + new Vector3(0f, 0f, -2.2f));
            s.argueCenter = Ground(new Vector3(s.prayPoint.x, 0f, (s.jiao.z + s.cang.z) * 0.5f));
            s.leaderStop = Ground(s.argueCenter + new Vector3(0f, 0f, 0.9f));

            // 父亲牌位：用 PROP_Tablet_Father（墨污状态），替换内景里的同位牌位
            Transform oldTablet = FindDeep(hall.transform, "INT_Tablet_WangShiqing");
            Vector3 tabletBase = A("tablet_father") - new Vector3(0f, 0.3f, 0f);
            GameObject tablet = LoadModel($"{Props}/PROP_Tablet_Father/PROP_Tablet_Father.fbx", story, Vector3.zero, Quaternion.identity);
            if (tablet != null)
            {
                if (oldTablet != null) oldTablet.gameObject.SetActive(false);
                tablet.name = "Father_Tablet_墨污";
                tablet.transform.SetPositionAndRotation(tabletBase, Quaternion.Euler(0f, 180f, 0f));
                SetChildActive(tablet, "Name", false);     // 1941：名字被墨涂黑
                SetChildActive(tablet, "Ink", true);
            }
            // 父亲照片：立在供桌右侧，挨着牌位
            GameObject photo = LoadModel($"{Props}/PROP_FatherPhoto/PROP_FatherPhoto.fbx", story, Vector3.zero, Quaternion.identity);
            if (photo != null)
            {
                photo.name = "Father_Photo_王世清";
                photo.transform.SetPositionAndRotation(A("altar") + new Vector3(1.15f, 0.005f, -0.1f), Quaternion.Euler(0f, 195f, 0f));
                ApplyPhotoTexture(photo);
            }

            // 香：三炷香插在香案的大香炉里，上香时才点上（香烟特效随之出现）；供桌上两支蜡烛有烛火
            var incense = new List<GameObject>();
            GameObject set = LoadModel($"{Props}/PROP_IncenseSet/PROP_IncenseSet.fbx", story, Vector3.zero, Quaternion.identity);
            if (set != null)
            {
                set.name = "Incense_上香";
                Transform sticks = FindDeep(set.transform, "Incense_Sticks");
                // 只留香，其余（炉、烛台、供果）内景供桌上已经有
                foreach (Transform c in set.transform) if (c != sticks && c.GetComponent<Renderer>() != null) c.gameObject.SetActive(false);
                set.transform.SetPositionAndRotation(s.pagesPoint + new Vector3(0f, 0.18f, 0.05f), Quaternion.Euler(0f, 180f, 0f));
                if (sticks != null)
                {
                    GameObject smoke = Vfx("PF_VFX_IncenseSmoke", sticks, Vector3.zero, Quaternion.identity, false);
                    if (smoke != null) smoke.transform.position = sticks.position + Vector3.up * 0.3f;
                    sticks.gameObject.SetActive(false);
                    incense.Add(sticks.gameObject);
                }
            }
            s.showOnIncense = incense.ToArray();
            Vector3 altar = A("altar");
            foreach (float dx in new[] { -0.85f, 0.85f })
                Vfx("PF_VFX_Candle", story, altar + new Vector3(dx, 0.47f, 0.0f), Quaternion.identity, true);

            // 族谱：王砚把半本谱摊在香案上，三张散页拼回一页（父名墨污）
            var showPages = new List<GameObject>();
            var hidePages = new List<GameObject>();
            GameObject gen = LoadModel($"{Props}/PROP_Genealogy/PROP_Genealogy.fbx", story, Vector3.zero, Quaternion.identity);
            if (gen != null)
            {
                gen.name = "Genealogy_英桥王氏族谱";
                gen.transform.SetPositionAndRotation(s.pagesPoint, Quaternion.Euler(0f, 180f, 0f));
                void Put(string child, Vector3 world, bool startActive, List<GameObject> list)
                {
                    Transform c = FindDeep(gen.transform, child);
                    if (c == null) return;
                    c.position = world;
                    c.gameObject.SetActive(startActive);
                    list?.Add(c.gameObject);
                }
                Vector3 top = s.pagesPoint + new Vector3(0f, 0.005f, 0f);
                foreach (string c in new[] { "Book_Closed", "Case", "Case_Lid" }) SetChildActive(gen, c, false);   // 谱匣内景供桌上已有
                Put("Book_Open", top + new Vector3(0.62f, 0f, 0.05f), false, showPages);
                Put("Page_Joined", top + new Vector3(-0.62f, 0f, 0.05f), false, showPages);
                Put("Ink_Father", top + new Vector3(-0.66f, 0f, 0.05f), false, showPages);
                Put("Page_1", top + new Vector3(-0.5f, 0f, -0.1f), true, hidePages);
                Put("Page_2", top + new Vector3(-0.78f, 0f, 0.12f), true, hidePages);
                Put("Page_3", top + new Vector3(0.55f, 0f, -0.12f), true, hidePages);
            }
            s.showOnPages = showPages.ToArray();
            s.hideOnPages = hidePages.ToArray();

            // 幡、纸灰、灯
            foreach (float dx in new[] { -4.6f, 4.6f })
            {
                GameObject b = LoadModel($"{Props}/PROP_Banner_Shrine/PROP_Banner_Shrine.fbx", story, Vector3.zero, Quaternion.identity);
                if (b != null) b.transform.SetPositionAndRotation(Ground(new Vector3(s.prayPoint.x + dx, 0f, s.prayPoint.z - 3.2f)), Quaternion.Euler(0f, 180f, 0f));
            }
            Vfx("PF_VFX_PaperAsh", story, s.argueCenter + new Vector3(0f, -1.5f, 0f), Quaternion.identity, true);
            AddPointLight("Shrine_HallLight", new Vector3(s.prayPoint.x, s.prayPoint.y + 3.2f, s.prayPoint.z + 1f), new Color(1f, 0.72f, 0.42f), 13f, 1.6f);
            AddPointLight("Shrine_CourtLight", new Vector3(s.clanPoint.x + 3f, 3.2f, s.clanPoint.z - 2f), new Color(0.85f, 0.8f, 0.72f), 12f, 0.8f);
            return s;
        }

        static void ApplyPhotoTexture(GameObject photo)
        {
            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>($"{Props}/PROP_FatherPhoto/T_FatherPhoto_D.png");
            Transform face = FindDeep(photo.transform, "Photo");
            if (tex == null || face == null) return;
            var r = face.GetComponent<Renderer>();
            if (r == null) return;
            const string path = Props + "/PROP_FatherPhoto/M_FatherPhoto.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null)
            {
                m = new Material(Shader.Find("Universal Render Pipeline/Lit"));
                AssetDatabase.CreateAsset(m, path);
            }
            m.SetTexture("_BaseMap", tex);
            m.SetColor("_BaseColor", Color.white);
            m.SetFloat("_Smoothness", 0.35f);
            EditorUtility.SetDirty(m);
            r.sharedMaterial = m;
        }

        // ==================================================================== 街市
        static void BuildStreet(Act1Director director, Act1Player walker, Material lip, Material stone)
        {
            // ---- 主街（通市门—横街，x 1~7）：日本兵欺压小贩，军官拔刀盘问王砚
            GameObject street = new GameObject("StreetEvent");
            street.transform.SetParent(story, false);
            street.transform.position = new Vector3(2f, 0f, 40f);
            Act1StreetEvent streetEvent = street.AddComponent<Act1StreetEvent>();
            GameObject streetOfficer = Npc("NPC_JpOfficer", "StreetOfficer_日本军官", new Vector3(8f, 0f, 40f), 270f, "日本军官", false);
            GameObject streetBully = Npc("NPC_JpSoldier_B", "StreetBully_日本兵", new Vector3(0f, 0f, 42f), 270f, "日本兵", false);
            GameObject vendor = Npc("NPC_VendorVeg", "Vendor_菜贩", new Vector3(-4f, 0f, 41f), 90f, "小贩", false);
            Prop("ENV_VendorStall_Veg", new Vector3(-2.3f, 0f, 37.6f), 90f, true);
            Prop("PROP_BambooBaskets", new Vector3(-2.6f, 0f, 35.3f), 30f, false);
            GameObject goods = LoadModel($"{Props}/PROP_VendorGoods/PROP_VendorGoods.fbx", story, new Vector3(-3.2f, 0f, 42.4f), Quaternion.Euler(0f, 90f, 0f));
            Transform basket = goods != null ? FindDeep(goods.transform, "Pole_Baskets") : null;
            GameObject sword = AttachSword(streetOfficer, stone);
            streetEvent.director = director;
            streetEvent.player = walker;
            streetEvent.officer = streetOfficer.transform;
            streetEvent.bully = streetBully.transform;
            streetEvent.vendor = vendor.transform;
            streetEvent.basket = basket != null ? basket.gameObject : Box(story, "Basket", new Vector3(-4f, 0.25f, 42f), new Vector3(0.7f, 0.4f, 0.7f), lip);
            streetEvent.sword = sword;
            streetEvent.triggerPoint = Marker("StreetTrigger", new Vector3(2f, 1f, 40f));
            streetEvent.triggerRadius = 4f;
            streetEvent.officerStop = new Vector3(1.6f, 0f, 40.4f);
            streetEvent.bystanders = new[]
            {
                Actor(Npc("NPC_TownWoman", "Town_妇女", new Vector3(-2.2f, 0f, 45.2f), 120f, null, false, "WatchLoop")),
                Actor(Npc("NPC_TownOldMan", "Town_老汉", new Vector3(7.0f, 0f, 46.0f), 230f, null, false, "WatchLoop")),
            };
            // 主街巡逻兵（Act1Patrol 沿 z 来回走）
            GameObject patrol = Npc("NPC_JpSoldier_C", "Patrol_巡逻兵", new Vector3(5.6f, 0f, 30f), 0f, null, false);
            Act1Patrol walk = patrol.AddComponent<Act1Patrol>();
            walk.zMin = 26f; walk.zMax = 52f; walk.speed = 1.1f;

            // ---- 横街东：砸门抢箱（P0095 铺面门口，下河桥东）
            Vector3 shopFront = new Vector3(55.75f, 0f, 36.7f);
            GameObject doorKit = LoadModel($"{Props}/PROP_Door_Loot/PROP_Door_Loot.fbx", story, shopFront, Quaternion.identity);
            GameObject doorEvent = new GameObject("DoorBreakEvent");
            doorEvent.transform.SetParent(story, false);
            doorEvent.transform.position = shopFront + new Vector3(0f, 0f, 3f);
            Act1DoorBreak doorBreak = doorEvent.AddComponent<Act1DoorBreak>();
            GameObject looter = Npc("NPC_JpSoldier_A", "Looter_日本兵", new Vector3(51.8f, 0f, 39.6f), 90f, null, false);
            doorBreak.director = director;
            doorBreak.player = walker;
            doorBreak.soldier = looter.transform;
            if (doorKit != null)
            {
                doorKit.name = "ShopDoor_铺门";
                doorBreak.doorLeaves = new[] { FindDeep(doorKit.transform, "Door_L"), FindDeep(doorKit.transform, "Door_R") };
                Transform chest = FindDeep(doorKit.transform, "Chest");
                Transform lid = FindDeep(doorKit.transform, "Chest_Lid");
                if (chest != null && lid != null) lid.SetParent(chest, true);
                doorBreak.loot = chest;
            }
            else
            {
                doorBreak.door = Box(story, "BrokenDoor", shopFront + new Vector3(0f, 1.4f, 0f), new Vector3(1.8f, 2.8f, 0.2f), lip).transform;
                doorBreak.loot = Box(story, "Loot", shopFront + new Vector3(-1.5f, 0.35f, 1f), new Vector3(0.8f, 0.6f, 0.7f), lip).transform;
            }
            doorBreak.kickPoint = shopFront + new Vector3(0f, 0f, 1.3f);
            doorBreak.triggerPoint = Marker("DoorTrigger", shopFront + new Vector3(0f, 1f, 3.3f));
            doorBreak.triggerRadius = 4.5f;
            doorBreak.bystanders = new[]
            {
                Actor(Npc("NPC_TownInjured", "Town_伤者", new Vector3(52.2f, 0f, 42.6f), 160f, null, false, "WatchLoop")),
                Actor(Npc("NPC_TownRefugee", "Town_逃难者", new Vector3(60.5f, 0f, 42.4f), 200f, null, false, "WatchLoop")),
            };

            // ---- 街尾火场：P0094 铺面换成燃烧铺面（火、黑烟、火光、哭喊）
            GameObject oldShop = FindByPrefix("P0094");
            Vector3 firePos = new Vector3(72.38f, 0f, 45.9f);
            GameObject fireShop = Prop("ENV_Fire_Shop", firePos, 180f, true);
            if (fireShop != null)
            {
                if (oldShop != null) oldShop.SetActive(false);
                SetChildActive(fireShop, "State_Burnt", false);
                foreach (Transform fx in fireShop.GetComponentsInChildren<Transform>(true))
                {
                    if (fx.name.StartsWith("FX_Fire")) Vfx("PF_VFX_Fire", fx, Vector3.zero, Quaternion.identity, false);
                    else if (fx.name == "FX_Smoke") Vfx("PF_VFX_FireSmoke", fx, Vector3.zero, Quaternion.identity, false);
                }
            }
            GameObject fire = new GameObject("BurningStreet");
            fire.transform.SetParent(story, false);
            fire.transform.position = firePos + new Vector3(0f, 1f, -3f);
            Act1Fire burning = fire.AddComponent<Act1Fire>();
            burning.radius = 4f;
            burning.buildFlames = fireShop == null;
            Actor(Npc("NPC_TownWoman", "Town_火场妇女", new Vector3(68.2f, 0f, 39.2f), 40f, null, false, "CowerLoop"));

            // ---- 小摊、街道道具
            Prop("ENV_VendorStall_Snack", new Vector3(36f, 0f, 42.1f), 180f, true);
            Prop("ENV_VendorStall_Goods", new Vector3(64f, 0f, 37.9f), 0f, true);
            Npc("NPC_VendorGoods", "Vendor_杂货摊主", new Vector3(64f, 0f, 37.9f), 0f, null, false, "CowerLoop");
            Prop("PROP_NoticeWall", new Vector3(-0.2f, 0f, 34.2f), 90f, true);
            Prop("PROP_Postbox", new Vector3(7.2f, 0f, 45.8f), 270f, true);
            Prop("PROP_Banner_Street", new Vector3(4f, 0f, 33f), 0f, false);
            foreach (float x in new[] { 30f, 66.5f, 81f }) Prop("PROP_StreetLamp", new Vector3(x, 0f, 36.7f), 0f, false);
            Prop("PROP_Bollards", new Vector3(44.8f, 0f, 40f), 90f, true);
            Prop("PROP_Bollards", new Vector3(51.2f, 0f, 40f), 90f, true);

            // ---- 环海门校场：被炸废墟、弹坑、日军哨卡
            Prop("ENV_Ruin_C", new Vector3(88f, 0f, 33.5f), 0f, true);
            Prop("ENV_Ruin_B", new Vector3(85f, 0f, 49.5f), 180f, true);
            Prop("ENV_Ruin_A", new Vector3(98f, 0f, 31f), 0f, true);
            Prop("ENV_Checkpoint_Props", new Vector3(93f, 0f, 49.5f), 180f, true);
            Prop("PROP_Flag_Japan", new Vector3(96.2f, 0f, 50.6f), 0f, true);
            Prop("PROP_JpAmmoBox", new Vector3(90.6f, 0f, 49.8f), 15f, true);
            GameObject rifle = Prop("PROP_JpRifle", new Vector3(91.2f, 0f, 50.3f), 0f, false);
            if (rifle != null) rifle.transform.rotation = Quaternion.Euler(-12f, 20f, 0f);      // 靠在弹药箱上
            Npc("NPC_JpSoldier_A", "Checkpoint_哨兵", new Vector3(93.5f, 0f, 47.4f), 180f, null, false, "AttentionLoop");
            Npc("NPC_TownRefugee", "Town_废墟逃难者", new Vector3(86.6f, 0f, 37.2f), 300f, null, false, "WatchLoop");
        }

        /// <summary>军刀拿在军官右手（先藏起来，拔刀时出现）。</summary>
        static GameObject AttachSword(GameObject officer, Material fallback)
        {
            Animator an = officer != null ? officer.GetComponentInChildren<Animator>() : null;
            Transform hand = an != null && an.isHuman ? an.GetBoneTransform(HumanBodyBones.RightHand) : null;
            Transform fore = an != null && an.isHuman ? an.GetBoneTransform(HumanBodyBones.RightLowerArm) : null;
            GameObject kit = LoadModel($"{Props}/PROP_JpSword/PROP_JpSword.fbx", story, Vector3.zero, Quaternion.identity);
            Transform blade = kit != null ? FindDeep(kit.transform, "Sword") : null;
            if (hand == null || fore == null || blade == null)
            {
                if (kit != null) Object.DestroyImmediate(kit);
                GameObject box = Box(story, "Officer_Sword", new Vector3(8.2f, 1.2f, 40.2f), new Vector3(0.05f, 1.2f, 0.05f), fallback);
                box.SetActive(false);
                return box;
            }
            PrefabUtility.UnpackPrefabInstance(kit, PrefabUnpackMode.Completely, InteractionMode.AutomatedAction);
            Vector3 dir = (hand.position - fore.position).normalized;       // 绑定姿势下手的指向 = 刀身方向
            blade.SetParent(hand, true);
            blade.rotation = Quaternion.FromToRotation(Vector3.up, dir);
            blade.position = hand.position + dir * 0.02f;
            blade.name = "Gunto_军刀";
            Object.DestroyImmediate(kit);
            blade.gameObject.SetActive(false);
            return blade.gameObject;
        }

        static Vector3 BuildFallenFlag(Material stone)
        {
            Vector3 pos = new Vector3(106f, 0f, 46f);
            GameObject kit = Prop("PROP_FallenFlag", pos, 270f, true);
            if (kit == null)
            {   // 占位：圆柱 + 方块
                GameObject pole = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                pole.name = "Fallen_Flag_Pole";
                pole.transform.SetParent(story, false);
                pole.transform.position = pos + new Vector3(-2f, 0.8f, 0f);
                pole.transform.localScale = new Vector3(0.08f, 3f, 0.08f);
                pole.transform.rotation = Quaternion.Euler(0f, 0f, 72f);
                pole.GetComponent<Renderer>().sharedMaterial = Mat("FlagPole", new Color(0.18f, 0.12f, 0.07f));
                return pos + new Vector3(0f, 0.9f, 0f);
            }
            kit.name = "FallenFlag_残旗";
            Transform blood = FindDeep(kit.transform, "Blood_Steps");
            return (blood != null ? blood.position : pos) + new Vector3(0f, 0.9f, 0f);
        }

        static void CreatePlanes()
        {
            for (int i = 0; i < 3; i++)
            {
                GameObject plane = LoadModel($"{Props}/PROP_JapanesePlane/PROP_JapanesePlane.fbx", story, Vector3.zero, Quaternion.identity);
                float yaw = 0f;
                if (plane == null)
                {   // 占位：方块飞机（沿 X）
                    plane = new GameObject("JapanesePlane_" + i);
                    plane.transform.SetParent(story, false);
                    Material m = Mat("PlaneBody", new Color(0.25f, 0.27f, 0.23f));
                    Box(plane.transform, "Body", Vector3.zero, new Vector3(3f, 0.5f, 0.5f), m);
                    Box(plane.transform, "Wing", new Vector3(0f, 0f, 1.4f), new Vector3(0.6f, 0.08f, 3f), m);
                    yaw = 90f;
                }
                else
                {
                    plane.name = "JapanesePlane_" + i;
                    foreach (Transform t in plane.GetComponentsInChildren<Transform>(true))
                        if (t.name.StartsWith("FX_Trail")) Vfx("PF_VFX_PlaneTrail", t, Vector3.zero, Quaternion.identity, false);
                    Transform prop = FindDeep(plane.transform, "Propeller");
                    if (prop != null)
                    {
                        GameObject disc = Vfx("PF_VFX_PropellerDisc", plane.transform, Vector3.zero, Quaternion.identity, false);
                        if (disc != null) disc.transform.position = prop.position;
                    }
                }
                plane.transform.position = new Vector3(-20 + i * 40f, 40f + i * 2f, 40f);
                Act1Plane mover = plane.AddComponent<Act1Plane>();
                mover.radius = 38f + i * 6f;
                mover.height = 40f + i * 3f;
                mover.center = new Vector3(0f, 0f, 50f);
                mover.phase = i * 2f;
                mover.modelYawOffset = yaw;
            }
        }

        // ==================================================================== 工具
        /// <summary>族亲/三派/日军/街坊：人物 FBX + 走跑与动作控制器 + Act1ClanActor + 胶囊碰撞；模型缺失时退回胶囊占位。</summary>
        static GameObject Npc(string asset, string name, Vector3 feet, float yaw, string speaker = null, bool facePlayer = true, string ambient = "")
        {
            GameObject go = LoadModel($"{Chars}/{asset}/{asset}.fbx", story, Vector3.zero, Quaternion.identity);
            if (go == null) return SimplePerson(story, name, feet + Vector3.up, new Color(0.3f, 0.28f, 0.24f));
            go.name = name;
            go.transform.SetPositionAndRotation(feet, Quaternion.Euler(0f, yaw, 0f));
            SetupAnimator(go);
            float height = 0.8f;
            foreach (Renderer r in go.GetComponentsInChildren<Renderer>()) height = Mathf.Max(height, r.bounds.max.y - feet.y);
            CapsuleCollider col = go.AddComponent<CapsuleCollider>();
            col.center = new Vector3(0f, height * 0.5f, 0f);
            col.height = height;
            col.radius = Mathf.Min(0.3f, height * 0.22f);
            Act1ClanActor actor = go.AddComponent<Act1ClanActor>();
            actor.player = playerT;
            actor.speakerTitles = string.IsNullOrEmpty(speaker) ? new string[0] : new[] { speaker };
            actor.facePlayer = facePlayer;
            actor.ambient = ambient ?? "";
            return go;
        }

        static Act1ClanActor Actor(GameObject go) => go != null ? go.GetComponent<Act1ClanActor>() : null;

        /// <summary>道具/环境：PROP_* 直接放（保留模型自带颜色），ENV_*/需要碰撞的走地图同一套材质库与碰撞约定。</summary>
        static GameObject Prop(string asset, Vector3 pos, float yaw, bool collide)
        {
            GameObject go;
            if (collide)
                go = RupuMapBuilder.PlaceForStory(asset, story, pos, yaw, asset, "ROC", false);
            else
            {
                string cat = asset.StartsWith("ENV_") ? "Environments" : "Props";
                go = LoadModel($"Assets/Art/{cat}/{asset}/{asset}.fbx", story, pos, Quaternion.Euler(0f, yaw, 0f));
            }
            if (go == null) Debug.LogWarning("[Act1ROC] 缺资产 " + asset);
            return go;
        }

        static GameObject Vfx(string prefab, Transform parent, Vector3 pos, Quaternion rot, bool worldPos)
        {
            var p = AssetDatabase.LoadAssetAtPath<GameObject>($"{VfxDir}/{prefab}.prefab");
            if (p == null) { Debug.LogWarning("[Act1ROC] 缺特效 " + prefab + "（菜单 入谱 > 特效 > 生成第一幕特效）"); return null; }
            var go = (GameObject)PrefabUtility.InstantiatePrefab(p, parent);
            if (worldPos) go.transform.position = pos + go.transform.localPosition;
            return go;
        }

        static void AddPointLight(string name, Vector3 pos, Color c, float range, float intensity)
        {
            GameObject lightObject = new GameObject(name);
            lightObject.transform.SetParent(story, false);
            lightObject.transform.position = pos;
            Light lamp = lightObject.AddComponent<Light>();
            lamp.type = LightType.Point;
            lamp.color = c;
            lamp.range = range;
            lamp.intensity = intensity;
        }

        /// <summary>从 2.8 m 高往下打射线找地面（低于屋顶；忽略人物胶囊），找不到就用 y=0。</summary>
        static Vector3 Ground(Vector3 p)
        {
            Physics.SyncTransforms();
            float best = 0f;
            bool hit = false;
            foreach (RaycastHit h in Physics.RaycastAll(new Vector3(p.x, 2.8f, p.z), Vector3.down, 6f, ~0, QueryTriggerInteraction.Ignore))
            {
                if (h.collider is CapsuleCollider || h.collider is CharacterController) continue;
                if (!hit || h.point.y > best) { best = h.point.y; hit = true; }
            }
            return new Vector3(p.x, hit ? best : 0f, p.z);
        }

        static Vector3 Toward(Vector3 from, Vector3 to, float d)
        {
            Vector3 v = to - from; v.y = 0f;
            return from + v.normalized * d + new Vector3(0f, 0.9f, 0f);
        }

        static Transform Marker(string name, Vector3 pos)
        {
            Transform t = new GameObject(name).transform;
            t.SetParent(story, false);
            t.position = pos;
            return t;
        }

        static Transform FindDeep(Transform root, string name)
        {
            foreach (Transform t in root.GetComponentsInChildren<Transform>(true)) if (t.name == name) return t;
            return null;
        }

        static void SetChildActive(GameObject root, string child, bool on)
        {
            Transform t = root != null ? FindDeep(root.transform, child) : null;
            if (t != null) t.gameObject.SetActive(on);
        }

        static GameObject FindByPrefix(string prefix)
        {
            foreach (Transform t in Object.FindObjectsOfType<Transform>()) if (t.name.StartsWith(prefix)) return t.gameObject;
            return null;
        }

        private static void DisableOldPlayerAndCast()
        {
            GameObject oldPlayer = GameObject.Find("Player_CH_WangYan_1941");
            if (oldPlayer != null) oldPlayer.SetActive(false);
            GameObject oldCamera = GameObject.Find("Main Camera");
            if (oldCamera != null) oldCamera.SetActive(false);
            GameObject cast = GameObject.Find("Cast");
            if (cast != null) cast.SetActive(false);
        }

        private static GameObject MakeInteractable(Transform parent, string name, string id, string label, string prompt, Vector3 pos, float radius, float hold)
        {
            GameObject go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = pos;
            Act1Interactable i = go.AddComponent<Act1Interactable>();
            i.id = id;
            i.label = label;
            i.prompt = prompt;
            i.radius = radius;
            i.holdDuration = hold;
            return go;
        }

        private static GameObject MakeFaction(string name, string id, string label, Vector3 pos)
        {
            return MakeInteractable(story, name, id, label, "按住 E 听" + label + "说话", pos, 3.2f, 1f);
        }

        private static void SetInteractableRefs(GameObject go, Act1Player player, Act1Director director)
        {
            Act1Interactable i = go.GetComponent<Act1Interactable>();
            if (i == null) return;
            i.player = player;
            i.director = director;
        }

        private static void SetupAnimator(GameObject model)
        {
            if (model == null) return;
            Animator animator = model.GetComponentInChildren<Animator>();
            if (animator == null) return;
            RuntimeAnimatorController controller = AssetDatabase.LoadAssetAtPath<RuntimeAnimatorController>("Assets/Art/Animations/AC_Humanoid_Locomotion.controller");
            if (controller != null)
            {
                animator.runtimeAnimatorController = controller;
                animator.applyRootMotion = false;
            }
        }

        /// <summary>手杖/拐：立在人物身旁，挂在人物下面跟着走。</summary>
        private static void HoldProp(GameObject owner, string path, Vector3 local, float yaw)
        {
            if (owner == null) return;
            GameObject prop = LoadModel(path, owner.transform, local, Quaternion.Euler(0f, yaw, 0f));
            if (prop != null) prop.name = System.IO.Path.GetFileNameWithoutExtension(path);
        }

        private static GameObject LoadModel(string path, Transform parent, Vector3 localPosition, Quaternion localRotation)
        {
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (prefab == null)
            {
                Debug.LogWarning("[Act1ROC] 模型缺失 " + path);
                return null;
            }
            GameObject go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
            go.transform.localPosition = localPosition;
            go.transform.localRotation = localRotation;
            go.transform.localScale = Vector3.one;
            return go;
        }

        private static GameObject SimplePerson(Transform parent, string name, Vector3 position, Color color)
        {
            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            body.name = name;
            body.transform.SetParent(parent, false);
            body.transform.position = position;
            body.transform.localScale = new Vector3(0.55f, 1f, 0.55f);
            Renderer renderer = body.GetComponent<Renderer>();
            if (renderer != null) renderer.sharedMaterial = Mat(name + "_Mat", color);
            return body;
        }

        // ---- 旧做法（没有 BLD_INT_AncestralHall 时）：切开 ROC 外壳门洞 + 隐形墙
        private static void BuildShrineEntranceFallback(Material frameMaterial)
        {
            GameObject hall = GameObject.Find("BLD_ROC_AncestralHall");
            if (hall != null)
            {
                CutShrineDoor(hall);
                foreach (Collider collider in hall.GetComponentsInChildren<Collider>(true)) collider.enabled = false;
            }
            BoxBlocker(story, "HallWall_FrontLeft", new Vector3(-26.6f, 2.5f, 23.2f), new Vector3(6.8f, 5f, 0.6f));
            BoxBlocker(story, "HallWall_FrontRight", new Vector3(-13.4f, 2.5f, 23.2f), new Vector3(6.8f, 5f, 0.6f));
            BoxBlocker(story, "HallWall_Left", new Vector3(-29.8f, 2.5f, 42f), new Vector3(0.6f, 5f, 38f));
            BoxBlocker(story, "HallWall_Right", new Vector3(-10.2f, 2.5f, 42f), new Vector3(0.6f, 5f, 38f));
            BoxBlocker(story, "HallWall_Back", new Vector3(-20f, 2.5f, 60.2f), new Vector3(20f, 5f, 0.6f));
            Box(story, "Shrine_DoorFrame_L", new Vector3(-23.1f, 2.2f, 23.5f), new Vector3(0.35f, 4.4f, 0.5f), frameMaterial);
            Box(story, "Shrine_DoorFrame_R", new Vector3(-16.9f, 2.2f, 23.5f), new Vector3(0.35f, 4.4f, 0.5f), frameMaterial);
            Box(story, "Shrine_DoorFrame_Top", new Vector3(-20f, 4.35f, 23.5f), new Vector3(6.6f, 0.35f, 0.5f), frameMaterial);
            AddPointLight("Shrine_InteriorLight", new Vector3(-20f, 3.2f, 33f), new Color(1f, 0.72f, 0.42f), 14f, 1.5f);
        }

        private static void CutShrineDoor(GameObject hall)
        {
            MeshFilter filter = hall.GetComponentInChildren<MeshFilter>();
            if (filter == null || filter.sharedMesh == null) return;
            Mesh source = filter.sharedMesh;
            Mesh cut = Object.Instantiate(source);
            cut.name = source.name + "_OpenDoor";
            Vector3[] vertices = source.vertices;
            for (int sub = 0; sub < source.subMeshCount; sub++)
            {
                int[] triangles = source.GetTriangles(sub);
                var keep = new List<int>(triangles.Length);
                for (int i = 0; i < triangles.Length; i += 3)
                {
                    Vector3 center = (vertices[triangles[i]] + vertices[triangles[i + 1]] + vertices[triangles[i + 2]]) / 3f;
                    // 祖祠本地坐标：前墙在 z≈-18.7，门洞留在中间偏下。
                    bool inDoor = center.z < -16.4f && center.z > -20.6f && Mathf.Abs(center.x) < 3.2f && center.y < 4.1f;
                    if (!inDoor) { keep.Add(triangles[i]); keep.Add(triangles[i + 1]); keep.Add(triangles[i + 2]); }
                }
                cut.SetTriangles(keep, sub);
            }
            cut.RecalculateBounds();
            const string meshPath = "Assets/Art/Buildings/BLD_ROC_AncestralHall/BLD_ROC_AncestralHall_Open.asset";
            if (AssetDatabase.LoadAssetAtPath<Mesh>(meshPath) != null) AssetDatabase.DeleteAsset(meshPath);
            AssetDatabase.CreateAsset(cut, meshPath);
            filter.sharedMesh = cut;
        }

        private static void BoxBlocker(Transform parent, string name, Vector3 position, Vector3 scale)
        {
            GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.position = position;
            go.transform.localScale = scale;
            Renderer renderer = go.GetComponent<Renderer>();
            if (renderer != null) renderer.enabled = false;
        }

        private static Light FindSun()
        {
            foreach (Light light in Object.FindObjectsOfType<Light>())
            {
                if (light.type == LightType.Directional) return light;
            }
            return null;
        }

        private static GameObject Box(Transform parent, string name, Vector3 position, Vector3 scale, Material material)
        {
            GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.position = position;
            go.transform.localScale = scale;
            Renderer r = go.GetComponent<Renderer>();
            if (r != null) r.sharedMaterial = material;
            return go;
        }

        private static Material Mat(string name, Color color)
        {
            Shader shader = Shader.Find("Universal Render Pipeline/Lit");
            if (shader == null) shader = Shader.Find("Standard");
            Material material = new Material(shader);
            material.name = name;
            material.color = color;
            if (material.HasProperty("_BaseColor")) material.SetColor("_BaseColor", color);
            return material;
        }
    }
}
#endif
