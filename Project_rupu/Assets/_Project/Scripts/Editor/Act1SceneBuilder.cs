#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Rupu.EditorTools
{
    public static class Act1SceneBuilder
    {
        [MenuItem("入谱/第一幕/重建 1941 归堡")]
        public static void Create()
        {
            if (EditorApplication.isPlaying)
            {
                EditorUtility.DisplayDialog("先退出 Play", "不能在 Play 模式生成场景。请先停止 Play，再执行。", "知道了");
                return;
            }
            UnityEngine.SceneManagement.Scene scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
            GameObject root = new GameObject("ACT1_1941");
            Transform t = root.transform;

            Material earth = Mat("Earth", new Color(0.16f, 0.15f, 0.13f), 0.05f);
            Material wetStone = Mat("WetStone", new Color(0.21f, 0.21f, 0.19f), 0.4f);
            Material wood = Mat("Wood", new Color(0.18f, 0.11f, 0.06f), 0.1f);
            Material plaster = Mat("Plaster", new Color(0.50f, 0.47f, 0.40f), 0.05f);
            Material stone = Mat("Stone", new Color(0.30f, 0.28f, 0.23f), 0.12f);
            Material tile = Mat("Tile", new Color(0.09f, 0.09f, 0.08f), 0.2f);
            Material cloth = Mat("Cloth", new Color(0.46f, 0.07f, 0.04f), 0.05f);
            Material paper = Mat("Paper", new Color(0.80f, 0.72f, 0.55f), 0f);
            Material black = Mat("Black", new Color(0.025f, 0.025f, 0.02f), 0f);
            Material brass = Mat("Brass", new Color(0.45f, 0.34f, 0.14f), 0.5f);
            Material olive = Mat("Olive", new Color(0.24f, 0.26f, 0.18f), 0.05f);
            Material skin = Mat("Skin", new Color(0.48f, 0.38f, 0.28f), 0f);
            Material green = Mat("Green", new Color(0.12f, 0.17f, 0.11f), 0f);

            BuildShrine(t, earth, wood, plaster, stone, tile, cloth, paper, black, brass);
            BuildCourtyard(t, wetStone, plaster, stone, wood, cloth, black);
            BuildStreet(t, earth, wetStone, plaster, stone, tile, wood, cloth, paper, black, green);
            BuildHuanhai(t, stone, tile, wood, cloth, black);
            BuildPlanes(t);
            BuildRain(t);

            GameObject elder = NpcRaw(t, "Elder_族老", new Vector3(0f, 1f, 24f), new Color(0.16f, 0.14f, 0.11f), new Color(0.10f, 0.09f, 0.07f));
            GameObject shrineOfficer = NpcRaw(t, "Shrine_Officer", new Vector3(3f, 1f, 13.5f), new Color(0.31f, 0.29f, 0.20f), new Color(0.16f, 0.15f, 0.11f));
            Box("Shrine_Officer_Sword", shrineOfficer.transform, new Vector3(0.55f, 0.7f, 0.75f), new Vector3(0.06f, 1.4f, 0.06f), new Color(0.18f, 0.18f, 0.17f)).transform.localRotation = Quaternion.Euler(0f, 0f, -20f);
            GameObject shrineGuardA = NpcRaw(t, "Shrine_Guard_A", new Vector3(0.5f, 1f, 12.5f), new Color(0.32f, 0.31f, 0.22f), new Color(0.17f, 0.16f, 0.12f));
            GameObject shrineGuardB = NpcRaw(t, "Shrine_Guard_B", new Vector3(5.5f, 1f, 14.5f), new Color(0.32f, 0.31f, 0.22f), new Color(0.17f, 0.16f, 0.12f));

            GameObject officer = NpcRaw(t, "Japanese_Officer", new Vector3(0f, 1f, 44f), new Color(0.30f, 0.29f, 0.20f), new Color(0.16f, 0.15f, 0.11f));
            GameObject sword = Box("Officer_Sword", officer.transform, new Vector3(0.55f, 0.55f, 0.8f), new Vector3(0.06f, 1.5f, 0.06f), new Color(0.20f, 0.20f, 0.19f));
            sword.transform.localPosition = new Vector3(0.55f, 0.7f, 0.75f);
            sword.transform.localRotation = Quaternion.Euler(0f, 0f, -25f);
            sword.SetActive(false);
            GameObject bully = NpcRaw(t, "Japanese_Bully", new Vector3(-2.2f, 1f, 43.5f), new Color(0.34f, 0.33f, 0.23f), new Color(0.18f, 0.17f, 0.12f));
            GameObject vendor = GameObject.Find("Vendor_0_Person");
            GameObject basket = GameObject.Find("Vendor_0_Basket_0");
            GameObject streetEventObject = new GameObject("StreetEvent");
            streetEventObject.transform.SetParent(t, false);
            streetEventObject.transform.position = new Vector3(0f, 1f, 40f);
            Act1StreetEvent streetEvent = streetEventObject.AddComponent<Act1StreetEvent>();

            GameObject looter = NpcRaw(t, "Japanese_Looter", new Vector3(-6.4f, 1f, 69f), new Color(0.34f, 0.33f, 0.23f), new Color(0.18f, 0.17f, 0.12f));
            GameObject lootDoor = GameObject.Find("House_L_3_Door");
            GameObject lootBox = Box("Loot_Box", t, new Vector3(-8f, 0.35f, 68.6f), new Vector3(0.8f, 0.6f, 0.7f), wood);
            GameObject doorBreakObject = new GameObject("DoorBreakEvent");
            doorBreakObject.transform.SetParent(t, false);
            doorBreakObject.transform.position = new Vector3(0f, 1f, 58f);
            Act1DoorBreak doorBreak = doorBreakObject.AddComponent<Act1DoorBreak>();

            GameObject fire = new GameObject("Burning_Shop");
            fire.transform.SetParent(t, false);
            fire.transform.position = new Vector3(-10f, 1f, 87f);
            Act1Fire burning = fire.AddComponent<Act1Fire>();
            burning.radius = 3.5f;
            burning.height = 5f;
            Box("Burning_Beam_1", fire.transform, new Vector3(0f, 2.5f, 0f), new Vector3(4f, 0.3f, 0.3f), new Color(0.25f, 0.12f, 0.06f)).transform.localRotation = Quaternion.Euler(0f, 0f, 20f);
            Box("Burning_Beam_2", fire.transform, new Vector3(2f, 1.5f, 1f), new Vector3(3f, 0.25f, 0.25f), new Color(0.22f, 0.10f, 0.05f)).transform.localRotation = Quaternion.Euler(25f, 0f, -18f);

            GameObject pages = new GameObject("Interact_残谱拼合");
            pages.transform.SetParent(t, false);
            pages.transform.position = new Vector3(0f, 1f, -2f);
            Act1Interactable pagesInteract = pages.AddComponent<Act1Interactable>();
            pagesInteract.id = "pages";
            pagesInteract.label = "残谱拼合";
            pagesInteract.prompt = "按住 E 拼合三张散页";
            pagesInteract.radius = 2.8f;
            pagesInteract.holdDuration = 1.8f;

            GameObject jiao = FactionPoint(t, "Interact_交谱派", "faction_jiao", "交谱派", "按住 E 听交谱派说话", new Vector3(-7f, 1f, -5f));
            GameObject shao = FactionPoint(t, "Interact_烧谱派", "faction_shao", "烧谱派", "按住 E 听烧谱派说话", new Vector3(7f, 1f, -5f));
            GameObject cang = FactionPoint(t, "Interact_藏谱派", "faction_cang", "藏谱派", "按住 E 听藏谱派说话", new Vector3(0f, 1f, -7.5f));

            GameObject flag = new GameObject("Interact_残旗入谱");
            flag.transform.SetParent(t, false);
            flag.transform.position = new Vector3(0f, 1f, 103f);
            Act1Interactable flagInteract = flag.AddComponent<Act1Interactable>();
            flagInteract.id = "flag";
            flagInteract.label = "倒下的旗杆";
            flagInteract.prompt = "按住 E 触摸旗杆上的旧血";
            flagInteract.radius = 3.4f;
            flagInteract.holdDuration = 1.6f;

            GameObject clan = new GameObject("Interact_族亲");
            clan.transform.SetParent(t, false);
            clan.transform.position = new Vector3(0f, 1f, 22f);
            Act1Interactable clanInteract = clan.AddComponent<Act1Interactable>();
            clanInteract.id = "clan";
            clanInteract.label = "族亲";
            clanInteract.prompt = "按住 E 听族亲怎么说";
            clanInteract.radius = 3.4f;
            clanInteract.holdDuration = 1f;

            GameObject memorial = new GameObject("Interact_父亲灵位");
            memorial.transform.SetParent(t, false);
            memorial.transform.position = new Vector3(0f, 1f, -9f);
            Act1Interactable memorialInteract = memorial.AddComponent<Act1Interactable>();
            memorialInteract.id = "memorial";
            memorialInteract.label = "父亲灵位";
            memorialInteract.prompt = "按住 E 给父亲上炷香";
            memorialInteract.radius = 2.8f;
            memorialInteract.holdDuration = 1.4f;

            GameObject systems = new GameObject("Act1_Systems");
            Act1Director director = systems.AddComponent<Act1Director>();
            director.flagPoint = flagInteract;
            director.clanPoint = clanInteract;
            director.memorialPoint = memorialInteract;
            director.factionPoints.Add(jiao.GetComponent<Act1Interactable>());
            director.factionPoints.Add(shao.GetComponent<Act1Interactable>());
            director.factionPoints.Add(cang.GetComponent<Act1Interactable>());

            GameObject jiao1 = GameObject.Find("Faction_Jiao_1");
            GameObject jiao2 = GameObject.Find("Faction_Jiao_2");
            GameObject shao1 = GameObject.Find("Faction_Shao_1");
            GameObject shao2 = GameObject.Find("Faction_Shao_2");
            GameObject cang1 = GameObject.Find("Faction_Cang_1");
            GameObject cang2 = GameObject.Find("Faction_Cang_2");
            GameObject leader = GameObject.Find("ClanLeader");
            director.factionActors = new[]
            {
                jiao1 != null ? jiao1.transform : null,
                jiao2 != null ? jiao2.transform : null,
                shao1 != null ? shao1.transform : null,
                shao2 != null ? shao2.transform : null,
                cang1 != null ? cang1.transform : null,
                cang2 != null ? cang2.transform : null
            };
            director.clanLeader = leader != null ? leader.transform : null;

            GameObject player = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            player.name = "Act1_Player";
            player.transform.position = new Vector3(0f, 1f, 28f);
            player.transform.localScale = new Vector3(0.8f, 1f, 0.8f);
            Object.DestroyImmediate(player.GetComponent<CapsuleCollider>());
            CharacterController controller = player.AddComponent<CharacterController>();
            controller.center = new Vector3(0f, 1f, 0f);
            controller.height = 2f;
            controller.radius = 0.35f;
            Act1Player walker = player.AddComponent<Act1Player>();
            walker.director = director;
            walker.startYaw = 180f;
            director.player = walker;
            director.elder = elder.transform;
            director.shrineOfficer = shrineOfficer.transform;
            director.shrineGuards = new[] { shrineGuardA.transform, shrineGuardB.transform };
            streetEvent.director = director;
            streetEvent.player = walker;
            streetEvent.officer = officer.transform;
            streetEvent.bully = bully.transform;
            streetEvent.vendor = vendor != null ? vendor.transform : null;
            streetEvent.sword = sword;
            streetEvent.basket = basket;
            doorBreak.player = walker;
            doorBreak.director = director;
            doorBreak.soldier = looter.transform;
            doorBreak.door = lootDoor != null ? lootDoor.transform : null;
            doorBreak.loot = lootBox.transform;

            Camera camera = Camera.main;
            if (camera != null)
            {
                camera.transform.position = new Vector3(0f, 2.4f, 31f);
                camera.transform.rotation = Quaternion.Euler(8f, 180f, 0f);
                camera.farClipPlane = 320f;
            }

            pagesInteract.player = walker;
            pagesInteract.director = director;
            flagInteract.player = walker;
            flagInteract.director = director;
            clanInteract.player = walker;
            clanInteract.director = director;
            memorialInteract.player = walker;
            memorialInteract.director = director;
            foreach (Act1Interactable point in director.factionPoints)
            {
                point.player = walker;
                point.director = director;
            }

            RenderSettings.ambientLight = new Color(0.16f, 0.17f, 0.18f);
            RenderSettings.fog = true;
            RenderSettings.fogColor = new Color(0.18f, 0.19f, 0.20f);
            RenderSettings.fogMode = FogMode.ExponentialSquared;
            RenderSettings.fogDensity = 0.012f;
            RenderSettings.skybox = null;

            Light sun = FindDirectional();
            if (sun != null)
            {
                sun.intensity = 0.5f;
                sun.color = new Color(0.62f, 0.66f, 0.72f);
                sun.shadows = LightShadows.Soft;
                sun.transform.rotation = Quaternion.Euler(40f, -25f, 0f);
            }

            AddPointLight(t, "Shrine_Warm", new Vector3(0f, 3.2f, -7f), new Color(0.95f, 0.58f, 0.26f), 1.8f, 11f);
            AddPointLight(t, "Altar_Candle", new Vector3(0f, 2.4f, -10.5f), new Color(1f, 0.46f, 0.18f), 1.4f, 6f);
            AddPointLight(t, "Courtyard_Lantern", new Vector3(0f, 3.5f, 22f), new Color(0.9f, 0.45f, 0.2f), 0.8f, 8f);

            EditorSceneManager.SaveScene(scene, "Assets/Scenes/Act1_1941.unity");
            EditorBuildSettings.scenes = new[]
            {
                new EditorBuildSettingsScene("Assets/Scenes/Act1_1941.unity", true),
                new EditorBuildSettingsScene("Assets/Scenes/Graybox.unity", true)
            };
            AssetDatabase.SaveAssets();
            Debug.Log("[Act1] 已重建：大祠堂/香火/三拨人/民国街市/日军/飞机/远处环海楼");
        }

        private static void BuildShrine(Transform t, Material earth, Material wood, Material plaster, Material stone, Material tile, Material cloth, Material paper, Material black, Material brass)
        {
            Box("Shrine_Floor", t, new Vector3(0f, -0.1f, -2f), new Vector3(20f, 0.2f, 24f), earth);
            Box("Shrine_Wall_Back", t, new Vector3(0f, 3f, -14f), new Vector3(20f, 6f, 0.5f), plaster);
            Box("Shrine_Wall_L", t, new Vector3(-10f, 3f, -2f), new Vector3(0.5f, 6f, 24f), plaster);
            Box("Shrine_Wall_R", t, new Vector3(10f, 3f, -2f), new Vector3(0.5f, 6f, 24f), plaster);
            Box("Shrine_Wall_Front_L", t, new Vector3(-6.5f, 3f, 10f), new Vector3(7f, 6f, 0.5f), plaster);
            Box("Shrine_Wall_Front_R", t, new Vector3(6.5f, 3f, 10f), new Vector3(7f, 6f, 0.5f), plaster);
            Box("Shrine_Roof", t, new Vector3(0f, 6.2f, -2f), new Vector3(21f, 0.4f, 25f), tile);
            Box("Shrine_Gate_L", t, new Vector3(-2.4f, 2.4f, 10.2f), new Vector3(1.4f, 4.8f, 0.5f), wood);
            Box("Shrine_Gate_R", t, new Vector3(2.4f, 2.4f, 10.2f), new Vector3(1.4f, 4.8f, 0.5f), wood);
            Box("Shrine_Gate_Lintel", t, new Vector3(0f, 4.8f, 10.2f), new Vector3(6.2f, 0.6f, 0.6f), wood);
            Box("Shrine_Plaque", t, new Vector3(0f, 5.4f, 10.25f), new Vector3(3.6f, 0.6f, 0.12f), black);

            Box("Altar_Dais", t, new Vector3(0f, 0.25f, -11.8f), new Vector3(14f, 0.5f, 3f), stone);
            Box("Altar_Dais_2", t, new Vector3(0f, 0.5f, -11.2f), new Vector3(11f, 0.5f, 2f), stone);
            Box("Altar_Table", t, new Vector3(0f, 1.35f, -11.4f), new Vector3(6f, 1.2f, 1.2f), wood);
            Box("Altar_Back", t, new Vector3(0f, 3.4f, -13.75f), new Vector3(12f, 4.4f, 0.35f), wood);
            Box("Altar_Plaque", t, new Vector3(0f, 4.8f, -13.5f), new Vector3(5f, 0.85f, 0.12f), cloth);
            Box("Altar_Incense", t, new Vector3(0f, 2.1f, -11.2f), new Vector3(0.7f, 0.35f, 0.7f), brass);

            for (int row = 0; row < 6; row++)
            {
                for (int col = -5; col <= 5; col++)
                {
                    float z = -12.9f + row * 0.42f;
                    float x = col * 0.42f;
                    Box($"Tablet_{row}_{col}", t, new Vector3(x, 2.55f + row * 0.05f, z), new Vector3(0.22f, 0.52f, 0.1f), (row + col) % 2 == 0 ? wood : black);
                }
            }

            Box("Father_Memorial_Table", t, new Vector3(0f, 0.78f, -9.5f), new Vector3(2.2f, 0.15f, 0.8f), wood);
            Box("Father_Memorial_Leg_L", t, new Vector3(-0.9f, 0.39f, -9.5f), new Vector3(0.14f, 0.78f, 0.14f), wood);
            Box("Father_Memorial_Leg_R", t, new Vector3(0.9f, 0.39f, -9.5f), new Vector3(0.14f, 0.78f, 0.14f), wood);
            Box("Father_Tablet", t, new Vector3(0f, 1.55f, -9.5f), new Vector3(0.5f, 1.0f, 0.14f), wood);
            Box("Father_Tablet_Ink", t, new Vector3(0f, 1.46f, -9.42f), new Vector3(0.36f, 0.1f, 0.02f), black);
            Box("Father_Incense", t, new Vector3(0f, 1.02f, -9.3f), new Vector3(0.35f, 0.28f, 0.35f), brass);

            Box("Ancestor_Shelf", t, new Vector3(0f, 3.25f, -12.45f), new Vector3(6f, 0.2f, 1f), wood);
            Box("Ancestor_Pei_Tablet", t, new Vector3(-1.4f, 3.8f, -12.45f), new Vector3(0.42f, 0.9f, 0.14f), brass);
            Box("Ancestor_Shugao_Tablet", t, new Vector3(1.4f, 3.8f, -12.45f), new Vector3(0.42f, 0.9f, 0.14f), brass);

            Box("Shrine_Table", t, new Vector3(0f, 0.8f, -2f), new Vector3(3.4f, 0.15f, 1.3f), wood);            Box("Table_Leg_L", t, new Vector3(-1.5f, 0.4f, -2f), new Vector3(0.16f, 0.8f, 0.16f), wood);
            Box("Table_Leg_R", t, new Vector3(1.5f, 0.4f, -2f), new Vector3(0.16f, 0.8f, 0.16f), wood);
            Box("Shrine_Paper_A", t, new Vector3(-0.6f, 1f, -2f), new Vector3(0.75f, 0.02f, 0.95f), paper);
            Box("Shrine_Paper_B", t, new Vector3(0f, 1.01f, -2.05f), new Vector3(0.75f, 0.02f, 0.95f), paper);
            Box("Shrine_Paper_C", t, new Vector3(0.6f, 1.02f, -1.95f), new Vector3(0.75f, 0.02f, 0.95f), paper);
            Box("Genealogy_Box", t, new Vector3(1.6f, 1.15f, -2f), new Vector3(0.6f, 0.3f, 0.45f), wood);

            Box("Shrine_Bench_L", t, new Vector3(-6.2f, 0.55f, -2f), new Vector3(1.1f, 0.25f, 8f), wood);
            Box("Shrine_Bench_R", t, new Vector3(6.2f, 0.55f, -2f), new Vector3(1.1f, 0.25f, 8f), wood);
            Box("Banner_L", t, new Vector3(-9.4f, 3.6f, -2f), new Vector3(0.08f, 3.6f, 1.2f), cloth);
            Box("Banner_R", t, new Vector3(9.4f, 3.6f, -2f), new Vector3(0.08f, 3.6f, 1.2f), cloth);
            Box("Spring_Banner_Torn", t, new Vector3(0f, 3.4f, 8.8f), new Vector3(9f, 1.5f, 0.05f), cloth);
            Box("Lantern_L", t, new Vector3(-5f, 4.1f, 8.5f), new Vector3(0.5f, 0.65f, 0.5f), cloth);
            Box("Lantern_R", t, new Vector3(5f, 3.9f, 8.5f), new Vector3(0.5f, 0.65f, 0.5f), cloth);

            Box("ClanLeader_Table", t, new Vector3(-4.5f, 0.6f, -8f), new Vector3(0.7f, 1.1f, 0.5f), wood);
            Npc(t, "ClanLeader", new Vector3(-4.5f, 1f, -8f), new Color(0.12f, 0.10f, 0.08f), cloth);
            Npc(t, "Shrine_Guard", new Vector3(6.8f, 1f, -7f), new Color(0.18f, 0.20f, 0.22f), cloth);

            // 墙与墙的接缝：四角加柱、墙顶压条、墙脚勒脚，避免明显缺口
            Box("Shrine_Corner_SW", t, new Vector3(-10f, 3f, -14f), new Vector3(1.2f, 6f, 1.2f), wood);
            Box("Shrine_Corner_SE", t, new Vector3(10f, 3f, -14f), new Vector3(1.2f, 6f, 1.2f), wood);
            Box("Shrine_Corner_NW", t, new Vector3(-10f, 3f, 10f), new Vector3(1.2f, 6f, 1.2f), wood);
            Box("Shrine_Corner_NE", t, new Vector3(10f, 3f, 10f), new Vector3(1.2f, 6f, 1.2f), wood);
            Box("Shrine_WallCap_Back", t, new Vector3(0f, 6.1f, -14f), new Vector3(21f, 0.35f, 1.1f), tile);
            Box("Shrine_WallCap_L", t, new Vector3(-10f, 6.1f, -2f), new Vector3(1.1f, 0.35f, 25f), tile);
            Box("Shrine_WallCap_R", t, new Vector3(10f, 6.1f, -2f), new Vector3(1.1f, 0.35f, 25f), tile);
            Box("Shrine_Plinth", t, new Vector3(0f, 0.12f, -2f), new Vector3(21f, 0.24f, 25f), stone);

            for (int i = 0; i < 4; i++)
            {
                float z = -9f + i * 5.5f;
                Box($"Shrine_Column_L_{i}", t, new Vector3(-8.6f, 3f, z), new Vector3(0.45f, 6f, 0.45f), wood);
                Box($"Shrine_Column_R_{i}", t, new Vector3(8.6f, 3f, z), new Vector3(0.45f, 6f, 0.45f), wood);
                Box($"Shrine_Beam_{i}", t, new Vector3(0f, 5.75f, z), new Vector3(18f, 0.32f, 0.42f), wood);
            }

            BuildIncense(t);
        }

        private static void BuildIncense(Transform t)
        {
            GameObject incense = new GameObject("Incense_Smoke");
            incense.transform.SetParent(t, false);
            incense.transform.position = new Vector3(0f, 2.1f, -11.2f);

            ParticleSystem ps = incense.AddComponent<ParticleSystem>();
            ParticleSystem.MainModule main = ps.main;
            main.duration = 6f;
            main.loop = true;
            main.startLifetime = 5f;
            main.startSpeed = 0.35f;
            main.startSize = 0.45f;
            main.maxParticles = 180;
            main.startColor = new Color(0.72f, 0.68f, 0.60f, 0.22f);
            main.gravityModifier = -0.02f;

            ParticleSystem.EmissionModule emission = ps.emission;
            emission.rateOverTime = 16f;

            ParticleSystem.ShapeModule shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Cone;
            shape.angle = 12f;
            shape.radius = 0.12f;

            ParticleSystem.ColorOverLifetimeModule color = ps.colorOverLifetime;
            color.enabled = true;
            Gradient gradient = new Gradient();
            gradient.SetKeys(
                new[] { new GradientColorKey(new Color(0.8f, 0.76f, 0.68f), 0f), new GradientColorKey(new Color(0.55f, 0.53f, 0.48f), 1f) },
                new[] { new GradientAlphaKey(0.28f, 0f), new GradientAlphaKey(0.05f, 1f) });
            color.color = gradient;

            ParticleSystemRenderer renderer = incense.GetComponent<ParticleSystemRenderer>();
            Shader shader = Shader.Find("Particles/Standard Unlit");
            if (shader != null) renderer.material = new Material(shader);
        }

        private static void BuildCourtyard(Transform t, Material wetStone, Material plaster, Material stone, Material wood, Material cloth, Material black)
        {
            Box("Courtyard_Ground", t, new Vector3(0f, -0.08f, 21f), new Vector3(26f, 0.16f, 22f), wetStone);
            Box("Courtyard_Wall_L", t, new Vector3(-13f, 1.8f, 21f), new Vector3(0.4f, 3.6f, 22f), plaster);
            Box("Courtyard_Wall_R", t, new Vector3(13f, 1.8f, 21f), new Vector3(0.4f, 3.6f, 22f), plaster);
            Box("Courtyard_Gate_L", t, new Vector3(-5f, 2f, 32f), new Vector3(8f, 4f, 0.4f), plaster);
            Box("Courtyard_Gate_R", t, new Vector3(5f, 2f, 32f), new Vector3(8f, 4f, 0.4f), plaster);
            Box("Courtyard_Gate_Lintel", t, new Vector3(0f, 4f, 32f), new Vector3(3f, 0.5f, 0.5f), wood);
            Box("Courtyard_Gate_Roof", t, new Vector3(0f, 4.4f, 32f), new Vector3(18f, 0.3f, 2.5f), black);
            Box("Courtyard_Path", t, new Vector3(0f, 0.01f, 21f), new Vector3(3.5f, 0.04f, 22f), stone);

            Box("Well_Ring", t, new Vector3(-8.5f, 0.5f, 17f), new Vector3(1.8f, 1f, 1.8f), stone);
            Box("Well_Dark", t, new Vector3(-8.5f, 0.55f, 17f), new Vector3(1.2f, 0.05f, 1.2f), black);
            Box("Brazier", t, new Vector3(8.5f, 0.7f, 17f), new Vector3(1.3f, 1.4f, 1.3f), black);
            Box("Brazier_Coal", t, new Vector3(8.5f, 1.42f, 17f), new Vector3(1f, 0.1f, 1f), new Color(0.22f, 0.05f, 0.02f));

            Npc(t, "Faction_Jiao_1", new Vector3(-7.2f, 1f, -5.5f), new Color(0.20f, 0.24f, 0.30f), cloth);
            Npc(t, "Faction_Jiao_2", new Vector3(-6.2f, 1f, -4.8f), new Color(0.20f, 0.24f, 0.30f), cloth);
            Npc(t, "Faction_Shao_1", new Vector3(7.2f, 1f, -5.5f), new Color(0.34f, 0.10f, 0.06f), cloth);
            Npc(t, "Faction_Shao_2", new Vector3(6.2f, 1f, -4.8f), new Color(0.34f, 0.10f, 0.06f), cloth);
            Npc(t, "Faction_Cang_1", new Vector3(0f, 1f, -7.8f), new Color(0.10f, 0.16f, 0.12f), cloth);
            Npc(t, "Faction_Cang_2", new Vector3(-1f, 1f, -7.3f), new Color(0.10f, 0.16f, 0.12f), cloth);

            Box("Faction_Jiao_Bundle", t, new Vector3(-7.2f, 0.35f, -6.2f), new Vector3(1f, 0.6f, 0.8f), cloth);
            Box("Faction_Shao_Table", t, new Vector3(7.2f, 0.5f, -6.2f), new Vector3(1.8f, 0.2f, 1.1f), wood);
            Box("Faction_Shao_Paper", t, new Vector3(7.2f, 0.62f, -6.2f), new Vector3(1.4f, 0.03f, 0.8f), new Color(0.72f, 0.64f, 0.50f));
            Box("Faction_Cang_Cloth", t, new Vector3(0f, 0.4f, -8.8f), new Vector3(1.4f, 0.6f, 0.9f), new Color(0.10f, 0.15f, 0.11f));

            NpcRaw(t, "Clan_Cold", new Vector3(-4f, 1f, 22f), new Color(0.22f, 0.20f, 0.18f), new Color(0.12f, 0.11f, 0.10f));
            NpcRaw(t, "Clan_Kind", new Vector3(4f, 1f, 22f), new Color(0.30f, 0.24f, 0.18f), new Color(0.16f, 0.13f, 0.10f));

            Box("Courtyard_Banner_L", t, new Vector3(-10f, 3.2f, 25f), new Vector3(0.08f, 3f, 0.8f), cloth);
            Box("Courtyard_Banner_R", t, new Vector3(10f, 3.2f, 27f), new Vector3(0.08f, 3f, 0.8f), cloth);
        }

        private static void BuildStreet(Transform t, Material earth, Material wetStone, Material plaster, Material stone, Material tile, Material wood, Material cloth, Material paper, Material black, Material green)
        {
            Box("Street_Ground", t, new Vector3(0f, -0.12f, 72f), new Vector3(52f, 0.2f, 82f), earth);
            for (int i = 0; i < 34; i++)
            {
                Box($"Street_Slab_{i}", t, new Vector3(0f, 0.02f, 33f + i * 2.2f), new Vector3(5f, 0.06f, 2f), wetStone);
            }

            for (int i = 0; i < 7; i++)
            {
                float z = 40f + i * 10f;
                House(t, $"House_L_{i}", new Vector3(-14f, 0f, z), 10f, 8f, 4.2f + (i % 3) * 0.7f, plaster, tile, wood, cloth);
                House(t, $"House_R_{i}", new Vector3(14f, 0f, z + 4f), 10f, 8f, 4.5f + (i % 2) * 0.8f, plaster, tile, wood, cloth);
            }

            Box("Ruin_Shop_Wall", t, new Vector3(-10f, 1.6f, 87f), new Vector3(8f, 3.2f, 0.4f), plaster);
            Box("Ruin_Shop_Beam", t, new Vector3(-10f, 3.4f, 85f), new Vector3(8f, 0.35f, 3f), wood);
            Box("Ruin_Rubble_1", t, new Vector3(-6f, 0.3f, 84f), new Vector3(1.6f, 0.6f, 1.2f), stone);
            Box("Ruin_Rubble_2", t, new Vector3(-12f, 0.25f, 85f), new Vector3(1.2f, 0.5f, 1.5f), stone);

            Box("Notice_Wall", t, new Vector3(6f, 1.5f, 35f), new Vector3(4f, 3f, 0.25f), plaster);
            Box("Notice_Paper_1", t, new Vector3(5.2f, 1.9f, 34.8f), new Vector3(0.7f, 0.9f, 0.02f), paper);
            Box("Notice_Paper_2", t, new Vector3(6.4f, 1.55f, 34.8f), new Vector3(0.8f, 0.6f, 0.02f), paper);
            Box("Notice_Red_Seal", t, new Vector3(5.3f, 1.7f, 34.77f), new Vector3(0.2f, 0.2f, 0.01f), cloth);

            for (int i = 0; i < 7; i++)
            {
                float z = 38f + i * 10f;
                Box($"Banner_L_{i}", t, new Vector3(-4.5f, 4.4f, z), new Vector3(0.08f, 3f, 0.8f), cloth);
                Box($"Banner_R_{i}", t, new Vector3(4.5f, 4.4f, z + 4f), new Vector3(0.08f, 3f, 0.8f), cloth);
            }

            for (int i = 0; i < 6; i++)
            {
                Box($"Pole_{i}", t, new Vector3(-7.5f + i * 3f, 2.5f, 36f), new Vector3(0.12f, 5f, 0.12f), black);
                Box($"Pole_Cross_{i}", t, new Vector3(-7.5f + i * 3f, 4.4f, 36f), new Vector3(1.4f, 0.08f, 0.08f), black);
            }

            for (int i = 0; i < 5; i++)
            {
                float z = 44f + i * 12f;
                Vendor(t, new Vector3(i % 2 == 0 ? -5f : 5f, 0f, z), wood, cloth, stone, i);
            }

            for (int i = 0; i < 12; i++)
            {
                float z = 42f + i * 5f;
                float x = i % 2 == 0 ? -3.2f : 3.2f;
                GameObject soldier = NpcRaw(t, $"Japanese_Soldier_{i}", new Vector3(x, 1f, z), new Color(0.38f, 0.37f, 0.26f), new Color(0.22f, 0.20f, 0.14f));
                Box($"Rifle_{i}", soldier.transform, new Vector3(0.35f, 0.2f, 0.15f), new Vector3(0.06f, 1.4f, 0.06f), black);
                if (i % 2 == 0)
                {
                    Act1Patrol patrol = soldier.AddComponent<Act1Patrol>();
                    patrol.zMin = z - 2f;
                    patrol.zMax = z + 2f;
                    patrol.speed = 0.7f;
                }
            }

            Tree(t, new Vector3(-17f, 0f, 38f), green, wood);
            Tree(t, new Vector3(17f, 0f, 52f), green, wood);
            Tree(t, new Vector3(-17f, 0f, 76f), green, wood);
            Tree(t, new Vector3(17f, 0f, 98f), green, wood);
        }

        private static void BuildHuanhai(Transform t, Material stone, Material tile, Material wood, Material cloth, Material black)
        {
            Box("Street_End_Ground", t, new Vector3(0f, -0.1f, 108f), new Vector3(30f, 0.2f, 16f), stone);
            Box("Huanhai_Base", t, new Vector3(0f, 5f, 118f), new Vector3(24f, 10f, 10f), stone);
            Box("Huanhai_Door", t, new Vector3(0f, 2.2f, 112.8f), new Vector3(4.4f, 4.4f, 0.25f), black);
            Box("Huanhai_Tier2", t, new Vector3(0f, 11f, 118f), new Vector3(17f, 2.6f, 7f), stone);
            Box("Huanhai_Roof1", t, new Vector3(0f, 10.3f, 118f), new Vector3(27f, 0.5f, 12f), tile);
            Box("Huanhai_Roof2", t, new Vector3(0f, 12.5f, 118f), new Vector3(20f, 0.5f, 9f), tile);
            Box("Huanhai_Plaque", t, new Vector3(0f, 7.4f, 112.7f), new Vector3(4.6f, 0.8f, 0.12f), cloth);
            Box("Huanhai_Window_L", t, new Vector3(-6.5f, 6.2f, 112.75f), new Vector3(1.5f, 1.2f, 0.1f), wood);
            Box("Huanhai_Window_R", t, new Vector3(6.5f, 6.2f, 112.75f), new Vector3(1.5f, 1.2f, 0.1f), wood);

            // 倒下的旗杆：根部仍在旗座里，杆身斜倒在石阶上
            GameObject flagRoot = new GameObject("Fallen_Flag_Root");
            flagRoot.transform.SetParent(t, false);
            flagRoot.transform.position = new Vector3(-3.2f, 0.15f, 103f);
            flagRoot.transform.rotation = Quaternion.Euler(0f, 0f, 72f);
            GameObject flagPole = Box("Fallen_Flag_Pole", flagRoot.transform, Vector3.zero, new Vector3(0.13f, 6f, 0.13f), wood);
            flagPole.transform.localPosition = new Vector3(0f, 3f, 0f);
            Box("Fallen_Flag_Cloth", flagRoot.transform, new Vector3(0.8f, 5.1f, 0f), new Vector3(2.1f, 0.04f, 1.3f), cloth);
            Box("Fallen_Flag_Blood", flagRoot.transform, new Vector3(0.4f, 5.16f, 0.05f), new Vector3(0.7f, 0.02f, 0.45f), new Color(0.18f, 0.03f, 0.02f));
            Box("Fallen_Flag_Base", t, new Vector3(-3.2f, 0.2f, 103f), new Vector3(1.4f, 0.4f, 1.4f), stone);
        }

        private static void BuildPlanes(Transform t)
        {
            for (int i = 0; i < 4; i++)
            {
                GameObject plane = new GameObject($"Japanese_Plane_{i}");
                plane.transform.SetParent(t, false);
                plane.transform.position = new Vector3(-45f + i * 35f, 18f + i * 2f, 50f + i * 15f);
                plane.transform.localScale = new Vector3(2.2f, 2.2f, 2.2f);
                Box("Fuselage", plane.transform, Vector3.zero, new Vector3(4.5f, 0.8f, 0.8f), new Color(0.25f, 0.27f, 0.23f));
                Box("Wing_L", plane.transform, new Vector3(0f, 0f, 2.1f), new Vector3(1f, 0.12f, 4.4f), new Color(0.25f, 0.27f, 0.23f));
                Box("Wing_R", plane.transform, new Vector3(0f, 0f, -2.1f), new Vector3(1f, 0.12f, 4.4f), new Color(0.25f, 0.27f, 0.23f));
                Box("Tail", plane.transform, new Vector3(-2.1f, 0.4f, 0f), new Vector3(1.2f, 1.2f, 0.12f), new Color(0.20f, 0.22f, 0.19f));
                Box("Red_Circle_L", plane.transform, new Vector3(0f, 0.09f, 3.2f), new Vector3(1.1f, 0.02f, 1.1f), new Color(0.62f, 0.04f, 0.02f));
                Box("Red_Circle_R", plane.transform, new Vector3(0f, 0.09f, -3.2f), new Vector3(1.1f, 0.02f, 1.1f), new Color(0.62f, 0.04f, 0.02f));
                Box("Contrail_1", plane.transform, new Vector3(-5.2f, 0f, 0f), new Vector3(8f, 0.22f, 0.36f), new Color(0.62f, 0.64f, 0.64f));
                Box("Contrail_2", plane.transform, new Vector3(-11f, 0f, 0f), new Vector3(7f, 0.14f, 0.24f), new Color(0.68f, 0.70f, 0.70f));
                GameObject propeller = Box("Propeller", plane.transform, new Vector3(2.6f, 0f, 0f), new Vector3(0.08f, 1.7f, 0.16f), new Color(0.16f, 0.16f, 0.15f));
                propeller.transform.localPosition = new Vector3(2.6f, 0f, 0f);
                Box("Propeller_2", propeller.transform, Vector3.zero, new Vector3(1f, 0.08f, 0.16f), new Color(0.16f, 0.16f, 0.15f));
                Act1Plane mover = plane.AddComponent<Act1Plane>();
                mover.radius = 36f + i * 5f;
                mover.height = 40f + i * 2f;
                mover.speed = 0.045f + i * 0.004f;
                mover.phase = i * 1.55f;
                mover.center = new Vector3(0f, 0f, 50f);
            }
        }

        private static void BuildRain(Transform t)
        {
            GameObject rain = new GameObject("Rain_1941");
            rain.transform.SetParent(t, false);
            rain.transform.position = new Vector3(0f, 13f, 70f);

            ParticleSystem ps = rain.AddComponent<ParticleSystem>();
            ParticleSystem.MainModule main = ps.main;
            main.duration = 5f;
            main.loop = true;
            main.startLifetime = 1.1f;
            main.startSpeed = 18f;
            main.startSize = 0.035f;
            main.maxParticles = 3000;
            main.gravityModifier = 1.4f;
            main.startColor = new Color(0.55f, 0.62f, 0.70f, 0.5f);

            ParticleSystem.EmissionModule emission = ps.emission;
            emission.rateOverTime = 1000f;

            ParticleSystem.ShapeModule shape = ps.shape;
            shape.shapeType = ParticleSystemShapeType.Box;
            shape.scale = new Vector3(46f, 1f, 80f);

            ParticleSystemRenderer renderer = rain.GetComponent<ParticleSystemRenderer>();
            Shader shader = Shader.Find("Particles/Standard Unlit");
            if (shader != null) renderer.material = new Material(shader);
            renderer.renderMode = ParticleSystemRenderMode.Stretch;
            renderer.velocityScale = 0.08f;
        }

        private static GameObject FactionPoint(Transform parent, string name, string id, string label, string prompt, Vector3 position)
        {
            GameObject go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = position;
            Act1Interactable interact = go.AddComponent<Act1Interactable>();
            interact.id = id;
            interact.label = label;
            interact.prompt = prompt;
            interact.radius = 3.2f;
            interact.holdDuration = 1f;
            return go;
        }

        private static void House(Transform t, string name, Vector3 position, float width, float depth, float height, Material plaster, Material tile, Material wood, Material cloth)
        {
            Box($"{name}_Body", t, position + new Vector3(0f, height * 0.5f, 0f), new Vector3(width, height, depth), plaster);
            Box($"{name}_Roof", t, position + new Vector3(0f, height + 0.3f, 0f), new Vector3(width + 1.4f, 0.4f, depth + 1.4f), tile);
            Box($"{name}_Upper", t, position + new Vector3(0f, height + 0.9f, 0f), new Vector3(width * 0.65f, 1.4f, depth * 0.7f), plaster);
            Box($"{name}_Door", t, position + new Vector3(width * 0.5f, 1.1f, 0f), new Vector3(0.15f, 2.2f, 1.4f), wood);
            Box($"{name}_Window", t, position + new Vector3(width * 0.5f, 2.8f, -1.3f), new Vector3(0.12f, 0.9f, 1.2f), wood);
            Box($"{name}_UpperWindow", t, position + new Vector3(width * 0.36f, height + 0.9f, 0f), new Vector3(0.12f, 0.8f, 1f), wood);
            Box($"{name}_Awning", t, position + new Vector3(width * 0.5f + 0.8f, 3.1f, 0f), new Vector3(1.4f, 0.08f, 2.4f), cloth);
            Box($"{name}_Step", t, position + new Vector3(width * 0.5f + 0.4f, 0.1f, 0f), new Vector3(1f, 0.2f, 1.8f), wood);
        }

        private static void Vendor(Transform t, Vector3 position, Material wood, Material cloth, Material stone, int index)
        {
            Box($"Vendor_{index}_Table", t, position + new Vector3(0f, 0.7f, 0f), new Vector3(2.4f, 0.15f, 1.2f), wood);
            Box($"Vendor_{index}_Leg_L", t, position + new Vector3(-1f, 0.35f, 0f), new Vector3(0.1f, 0.7f, 0.1f), wood);
            Box($"Vendor_{index}_Leg_R", t, position + new Vector3(1f, 0.35f, 0f), new Vector3(0.1f, 0.7f, 0.1f), wood);
            Box($"Vendor_{index}_Awning", t, position + new Vector3(0f, 2.3f, 0f), new Vector3(2.8f, 0.08f, 1.5f), cloth);
            Box($"Vendor_{index}_Post_L", t, position + new Vector3(-1.2f, 1.2f, 0.5f), new Vector3(0.08f, 2.4f, 0.08f), wood);
            Box($"Vendor_{index}_Post_R", t, position + new Vector3(1.2f, 1.2f, 0.5f), new Vector3(0.08f, 2.4f, 0.08f), wood);
            for (int i = 0; i < 3; i++)
            {
                Box($"Vendor_{index}_Basket_{i}", t, position + new Vector3(-0.6f + i * 0.6f, 0.9f, 0f), new Vector3(0.35f, 0.25f, 0.35f), stone);
            }
            Npc(t, $"Vendor_{index}_Person", position + new Vector3(0f, 1f, -1.1f), new Color(0.24f, 0.20f, 0.14f), cloth);
        }

        private static void Tree(Transform t, Vector3 position, Material green, Material wood)
        {
            Box("Tree_Trunk", t, position + new Vector3(0f, 1.4f, 0f), new Vector3(0.3f, 2.8f, 0.3f), wood);
            Box("Tree_Crown", t, position + new Vector3(0f, 3.5f, 0f), new Vector3(3f, 2.4f, 3f), green);
        }

        private static GameObject Npc(Transform t, string name, Vector3 position, Color color, Material cloth)
        {
            return NpcRaw(t, name, position, color, color);
        }

        private static GameObject NpcRaw(Transform t, string name, Vector3 position, Color coat, Color cap)
        {
            GameObject body = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            body.name = name;
            body.transform.SetParent(t, false);
            body.transform.position = position;
            body.transform.localScale = new Vector3(0.55f, 1f, 0.55f);
            Renderer renderer = body.GetComponent<Renderer>();
            if (renderer != null)
            {
                Material material = new Material(Shader.Find("Standard"));
                material.color = coat;
                renderer.sharedMaterial = material;
            }

            GameObject head = GameObject.CreatePrimitive(PrimitiveType.Sphere);
            head.name = name + "_Head";
            head.transform.SetParent(body.transform, false);
            head.transform.localPosition = new Vector3(0f, 1.28f, 0f);
            head.transform.localScale = new Vector3(0.55f, 0.55f, 0.55f);
            Renderer headRenderer = head.GetComponent<Renderer>();
            if (headRenderer != null) headRenderer.sharedMaterial = Mat("Skin", new Color(0.48f, 0.38f, 0.28f), 0f);

            Box("Cap", body.transform, new Vector3(0f, 1.48f, 0f), new Vector3(0.55f, 0.12f, 0.55f), cap);
            return body;
        }

        private static GameObject Box(string name, Transform parent, Vector3 position, Vector3 scale, Material material)
        {
            return Box(name, parent, position, scale, material.color);
        }

        private static GameObject Box(string name, Transform parent, Vector3 position, Vector3 scale, Color color)
        {
            GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.position = position;
            go.transform.localScale = scale;
            Renderer renderer = go.GetComponent<Renderer>();
            if (renderer != null)
            {
                Material material = new Material(Shader.Find("Standard"));
                material.color = color;
                renderer.sharedMaterial = material;
            }
            return go;
        }

        private static Material Mat(string name, Color color, float smoothness)
        {
            Shader shader = Shader.Find("Standard");
            Material material = new Material(shader != null ? shader : Shader.Find("Diffuse"));
            material.name = name;
            material.color = color;
            material.SetFloat("_Glossiness", smoothness);
            return material;
        }

        private static Light FindDirectional()
        {
            foreach (Light light in Object.FindObjectsOfType<Light>())
            {
                if (light.type == LightType.Directional) return light;
            }
            return null;
        }

        private static void AddPointLight(Transform parent, string name, Vector3 position, Color color, float intensity, float range)
        {
            GameObject go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.position = position;
            Light light = go.AddComponent<Light>();
            light.type = LightType.Point;
            light.color = color;
            light.intensity = intensity;
            light.range = range;
            light.shadows = LightShadows.Soft;
        }
    }
}
#endif
