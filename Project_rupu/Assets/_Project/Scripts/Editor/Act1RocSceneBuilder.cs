#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Rupu.EditorTools
{
    public static class Act1RocSceneBuilder
    {
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
            Transform story = root.transform;

            Material lip = Mat("Act1ROCLip", new Color(0.33f, 0.27f, 0.20f));
            Material paper = Mat("Act1ROCPaper", new Color(0.78f, 0.69f, 0.52f));
            Material cloth = Mat("Act1ROCCloth", new Color(0.48f, 0.07f, 0.04f));
            Material stone = Mat("Act1ROCStone", new Color(0.30f, 0.29f, 0.25f));

            // 祠堂前的玩家：从院门进来，朝祖祠
            GameObject player = new GameObject("Act1_Player");
            player.transform.position = new Vector3(-20f, 0.15f, 16f);
            CharacterController controller = player.AddComponent<CharacterController>();
            controller.center = new Vector3(0f, 1f, 0f);
            controller.height = 2f;
            controller.radius = 0.35f;
            Act1Player walker = player.AddComponent<Act1Player>();
            walker.startYaw = 0f;

            GameObject bodyModel = LoadModel("Assets/Art/Characters/CH_WangYan_1941/CH_WangYan_1941.fbx", player.transform, Vector3.zero, Quaternion.identity);
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
            walker.director = null;

            GameObject systems = new GameObject("Act1_Systems");
            Act1Director director = systems.AddComponent<Act1Director>();
            director.player = walker;
            walker.director = director;

            // 祖祠内部/门前
            GameObject pages = MakeInteractable(story, "Interact_残谱拼合", "pages", "残谱拼合", "按住 E 拼合散页", new Vector3(-20f, 0.9f, 30f), 2.8f, 1.8f);
            GameObject clan = MakeInteractable(story, "Interact_族亲", "clan", "族亲", "按住 E 听族亲怎么说", new Vector3(-20f, 0.9f, 27.5f), 3.2f, 1f);
            GameObject memorial = MakeInteractable(story, "Interact_父亲灵位", "memorial", "父亲灵位", "按住 E 给父亲上炷香", new Vector3(-20f, 0.9f, 36f), 2.8f, 1.4f);
            GameObject flag = MakeInteractable(story, "Interact_残旗入谱", "flag", "倒下的旗杆", "按住 E 触摸旗杆旧血", new Vector3(108f, 0.9f, 40f), 3.5f, 1.6f);

            GameObject jiao = MakeFaction(story, "Interact_交谱派", "faction_jiao", "交谱派", new Vector3(-25f, 0.9f, 33f));
            GameObject shao = MakeFaction(story, "Interact_烧谱派", "faction_shao", "烧谱派", new Vector3(-15f, 0.9f, 33f));
            GameObject cang = MakeFaction(story, "Interact_藏谱派", "faction_cang", "藏谱派", new Vector3(-20f, 0.9f, 40f));

            director.flagPoint = flag.GetComponent<Act1Interactable>();
            director.clanPoint = clan.GetComponent<Act1Interactable>();
            director.memorialPoint = memorial.GetComponent<Act1Interactable>();
            director.pagesPoint = pages.transform;
            director.factionPoints.Add(jiao.GetComponent<Act1Interactable>());
            director.factionPoints.Add(shao.GetComponent<Act1Interactable>());
            director.factionPoints.Add(cang.GetComponent<Act1Interactable>());

            // 关键 NPC：族老（NPC_ClanElder + 手杖）在院门口迎王砚；族长王秉之（+ 拐）在祖宗牌位前
            GameObject elder = ClanNpc(story, "NPC_ClanElder", "Elder_族老", new Vector3(-20f, 0f, 17.5f), 180f, walker.transform);
            HoldProp(elder, "Assets/Art/Props/PROP_Staff_Elder/PROP_Staff_Elder.fbx", new Vector3(0.38f, 0f, 0.12f), 0f);
            GameObject leader = ClanNpc(story, "NPC_WangBingzhi", "ClanLeader_王秉之", new Vector3(-20f, 0f, 44f), 180f, walker.transform);
            HoldProp(leader, "Assets/Art/Props/PROP_Cane_Bingzhi/PROP_Cane_Bingzhi.fbx", new Vector3(0.36f, 0f, 0.14f), 90f);
            director.elderStop = new GameObject("ElderStop").transform;
            director.elderStop.SetParent(story, false);
            director.elderStop.position = new Vector3(-21.8f, 0f, 26.2f);

            // 族亲（冷遇/亲善）：互动点两侧。左边皱眉的族叔，右边驼背的族婶婆带着孙子
            ClanNpc(story, "NPC_ClanUncle", "Clan_族中冷遇", new Vector3(-23.2f, 0f, 27.8f), 90f, walker.transform);
            ClanNpc(story, "NPC_ClanGranny", "Clan_族中亲善", new Vector3(-16.8f, 0f, 27.8f), 270f, walker.transform);
            ClanNpc(story, "NPC_ClanBoy", "Clan_孩童", new Vector3(-16.1f, 0f, 27.0f), 270f, walker.transform);

            // 日本军官与士兵用临时制服人形；模型待资源补齐
            GameObject officer = SimplePerson(story, "ShrineOfficer", new Vector3(-20f, 1f, 28f), new Color(0.34f, 0.32f, 0.22f));
            GameObject guardA = SimplePerson(story, "ShrineGuardA", new Vector3(-22f, 1f, 29f), new Color(0.30f, 0.30f, 0.22f));
            GameObject guardB = SimplePerson(story, "ShrineGuardB", new Vector3(-18f, 1f, 29f), new Color(0.30f, 0.30f, 0.22f));

            // 三派人物（祠堂三拨人）：交谱派族老在西、烧谱派青年在东、藏谱派妇人带女儿在牌位前
            GameObject jiaoActor = ClanNpc(story, "NPC_ClanJiao", "Faction_交谱派族老", new Vector3(-25f, 0f, 32f), 90f, walker.transform);
            GameObject shaoActor = ClanNpc(story, "NPC_ClanShao", "Faction_烧谱派青年", new Vector3(-15f, 0f, 32f), 270f, walker.transform);
            GameObject cangActor = ClanNpc(story, "NPC_ClanCang", "Faction_藏谱派妇人", new Vector3(-20.5f, 0f, 39f), 180f, walker.transform);
            ClanNpc(story, "NPC_ClanGirl", "Faction_藏谱派之女", new Vector3(-19.5f, 0f, 39.4f), 180f, walker.transform);

            director.elder = elder != null ? elder.transform : null;
            director.clanLeader = leader != null ? leader.transform : null;
            director.shrineOfficer = officer.transform;
            director.shrineGuards = new[] { guardA.transform, guardB.transform };
            director.factionActors = new[] { jiaoActor.transform, shaoActor.transform, cangActor.transform };
            director.streetExit = new GameObject("StreetExit").transform;
            director.streetExit.position = new Vector3(-20f, 0f, 20f);
            // 人物原点在脚底：聚拢中心和族长停步点都贴地（y=0），否则会浮空
            director.factionCenter = new Vector3(-20f, 0f, 33f);
            director.clanStop = new Vector3(-20f, 0f, 32f);

            // 桌椅/祭台/牌位
            Box(story, "Shrine_Table", new Vector3(-20f, 0.75f, 30f), new Vector3(3.2f, 0.15f, 1.2f), lip);
            Box(story, "Father_Tablet", new Vector3(-20f, 1.65f, 36f), new Vector3(0.55f, 1f, 0.16f), lip);
            Box(story, "Father_Ink", new Vector3(-20f, 1.55f, 36.08f), new Vector3(0.4f, 0.1f, 0.02f), cloth);
            Box(story, "Ancestor_Left", new Vector3(-22f, 3.2f, 40f), new Vector3(0.42f, 0.8f, 0.14f), stone);
            Box(story, "Ancestor_Right", new Vector3(-18f, 3.2f, 40f), new Vector3(0.42f, 0.8f, 0.14f), stone);
            Box(story, "Shrine_Incense", new Vector3(-20f, 1.1f, 35.2f), new Vector3(0.4f, 0.25f, 0.4f), stone);
            BuildShrineEntrance(story, lip);

            // 街市：暴行、砸门、火光、旗杆
            GameObject street = new GameObject("StreetEvent");
            street.transform.SetParent(story, false);
            street.transform.position = new Vector3(2f, 1f, 40f);
            Act1StreetEvent streetEvent = street.AddComponent<Act1StreetEvent>();
            GameObject streetOfficer = SimplePerson(story, "StreetOfficer", new Vector3(8f, 1f, 40f), new Color(0.34f, 0.32f, 0.22f));
            GameObject streetBully = SimplePerson(story, "StreetBully", new Vector3(0f, 1f, 42f), new Color(0.30f, 0.30f, 0.22f));
            GameObject vendor = SimplePerson(story, "Vendor", new Vector3(-4f, 1f, 41f), new Color(0.30f, 0.22f, 0.14f));
            GameObject basket = Box(story, "Basket", new Vector3(-4f, 0.25f, 42f), new Vector3(0.7f, 0.4f, 0.7f), lip);
            GameObject sword = Box(story, "Officer_Sword", new Vector3(8.2f, 1.2f, 40.2f), new Vector3(0.05f, 1.2f, 0.05f), stone);
            streetEvent.director = director;
            streetEvent.player = walker;
            streetEvent.officer = streetOfficer.transform;
            streetEvent.bully = streetBully.transform;
            streetEvent.vendor = vendor.transform;
            streetEvent.basket = basket;
            streetEvent.sword = sword;
            streetEvent.triggerPoint = new GameObject("StreetTrigger").transform;
            streetEvent.triggerPoint.position = new Vector3(2f, 1f, 40f);
            streetEvent.triggerRadius = 4f;

            GameObject doorEvent = new GameObject("DoorBreakEvent");
            doorEvent.transform.SetParent(story, false);
            doorEvent.transform.position = new Vector3(46f, 1f, 40f);
            Act1DoorBreak doorBreak = doorEvent.AddComponent<Act1DoorBreak>();
            GameObject looter = SimplePerson(story, "Looter", new Vector3(44f, 1f, 39f), new Color(0.30f, 0.30f, 0.22f));
            GameObject door = Box(story, "BrokenDoor", new Vector3(46f, 1.4f, 42f), new Vector3(1.8f, 2.8f, 0.2f), lip);
            GameObject loot = Box(story, "Loot", new Vector3(44f, 0.35f, 41f), new Vector3(0.8f, 0.6f, 0.7f), lip);
            doorBreak.director = director;
            doorBreak.player = walker;
            doorBreak.soldier = looter.transform;
            doorBreak.door = door.transform;
            doorBreak.loot = loot.transform;
            doorBreak.triggerPoint = new GameObject("DoorTrigger").transform;
            doorBreak.triggerPoint.position = new Vector3(46f, 1f, 40f);
            doorBreak.triggerRadius = 4f;

            GameObject fire = new GameObject("BurningStreet");
            fire.transform.SetParent(story, false);
            fire.transform.position = new Vector3(62f, 1f, 40f);
            Act1Fire burning = fire.AddComponent<Act1Fire>();
            burning.radius = 4f;

            CreatePlanes(story);
            CreateFlag(story, flag.transform.position);

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
            Debug.Log("[Act1ROC] 已生成 Act1_ROC.unity：ROC 全景 + 第一幕剧情");
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

        private static GameObject MakeFaction(Transform parent, string name, string id, string label, Vector3 pos)
        {
            GameObject go = MakeInteractable(parent, name, id, label, "按住 E 听" + label + "说话", pos, 3.2f, 1f);
            return go;
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

        /// <summary>族亲/三派：人物 FBX + 走路控制器 + 面向玩家 + 胶囊碰撞（按模型高度）。模型缺失时退回胶囊占位。</summary>
        private static GameObject ClanNpc(Transform parent, string asset, string name, Vector3 feet, float yaw, Transform player)
        {
            GameObject go = LoadModel($"Assets/Art/Characters/{asset}/{asset}.fbx", parent, Vector3.zero, Quaternion.identity);
            if (go == null) return SimplePerson(parent, name, feet + Vector3.up, new Color(0.3f, 0.28f, 0.24f));
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
            actor.player = player;
            return go;
        }

        /// <summary>手杖/拐：立在人物身旁，挂在人物下面跟着走。</summary>
        private static void HoldProp(GameObject owner, string path, Vector3 local, float yaw)
        {
            if (owner == null) return;
            GameObject prop = LoadModel(path, owner.transform, local, Quaternion.Euler(0f, yaw, 0f));
            if (prop != null) prop.name = System.IO.Path.GetFileNameWithoutExtension(path);
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

        private static void BuildShrineEntrance(Transform story, Material frameMaterial)
        {
            GameObject hall = GameObject.Find("BLD_ROC_AncestralHall");
            if (hall != null)
            {
                CutShrineDoor(hall);
                // ROC 的祖祠是一个封闭 MeshCollider；改成前门可进、四面有墙。
                foreach (Collider collider in hall.GetComponentsInChildren<Collider>(true))
                {
                    collider.enabled = false;
                }
            }

            // 门洞留在 x=-20 附近，宽约 5.5m
            BoxBlocker(story, "HallWall_FrontLeft", new Vector3(-26.6f, 2.5f, 23.2f), new Vector3(6.8f, 5f, 0.6f));
            BoxBlocker(story, "HallWall_FrontRight", new Vector3(-13.4f, 2.5f, 23.2f), new Vector3(6.8f, 5f, 0.6f));
            BoxBlocker(story, "HallWall_Left", new Vector3(-29.8f, 2.5f, 42f), new Vector3(0.6f, 5f, 38f));
            BoxBlocker(story, "HallWall_Right", new Vector3(-10.2f, 2.5f, 42f), new Vector3(0.6f, 5f, 38f));
            BoxBlocker(story, "HallWall_Back", new Vector3(-20f, 2.5f, 60.2f), new Vector3(20f, 5f, 0.6f));

            // 门框与黑暗门洞：门洞不挡路，给玩家一个明确的入口
            Box(story, "Shrine_DoorFrame_L", new Vector3(-23.1f, 2.2f, 23.5f), new Vector3(0.35f, 4.4f, 0.5f), frameMaterial);
            Box(story, "Shrine_DoorFrame_R", new Vector3(-16.9f, 2.2f, 23.5f), new Vector3(0.35f, 4.4f, 0.5f), frameMaterial);
            Box(story, "Shrine_DoorFrame_Top", new Vector3(-20f, 4.35f, 23.5f), new Vector3(6.6f, 0.35f, 0.5f), frameMaterial);
            Box(story, "Shrine_Threshold", new Vector3(-20f, 0.1f, 23.6f), new Vector3(6f, 0.2f, 0.8f), frameMaterial);

            GameObject lightObject = new GameObject("Shrine_InteriorLight");
            lightObject.transform.SetParent(story, false);
            lightObject.transform.position = new Vector3(-20f, 3.2f, 33f);
            Light lamp = lightObject.AddComponent<Light>();
            lamp.type = LightType.Point;
            lamp.color = new Color(1f, 0.72f, 0.42f);
            lamp.range = 14f;
            lamp.intensity = 1.5f;
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
                var keep = new System.Collections.Generic.List<int>(triangles.Length);
                for (int i = 0; i < triangles.Length; i += 3)
                {
                    Vector3 a = vertices[triangles[i]];
                    Vector3 b = vertices[triangles[i + 1]];
                    Vector3 c = vertices[triangles[i + 2]];
                    Vector3 center = (a + b + c) / 3f;

                    // 祖祠本地坐标：前墙在 z≈-18.7，门洞留在中间偏下。
                    bool inDoor = center.z < -16.4f && center.z > -20.6f
                                  && Mathf.Abs(center.x) < 3.2f
                                  && center.y < 4.1f;
                    if (!inDoor)
                    {
                        keep.Add(triangles[i]);
                        keep.Add(triangles[i + 1]);
                        keep.Add(triangles[i + 2]);
                    }
                }
                cut.SetTriangles(keep, sub);
            }

            cut.RecalculateBounds();
            const string meshPath = "Assets/Art/Buildings/BLD_ROC_AncestralHall/BLD_ROC_AncestralHall_Open.asset";
            if (AssetDatabase.LoadAssetAtPath<Mesh>(meshPath) != null) AssetDatabase.DeleteAsset(meshPath);
            AssetDatabase.CreateAsset(cut, meshPath);
            filter.sharedMesh = cut;
            Debug.Log($"[Act1ROC] 祖祠门洞已切开：{meshPath}");
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

        private static void CreateFlag(Transform parent, Vector3 position)
        {
            GameObject pole = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
            pole.name = "Fallen_Flag_Pole";
            pole.transform.SetParent(parent, false);
            pole.transform.position = position + new Vector3(-2f, 0.8f, 0f);
            pole.transform.localScale = new Vector3(0.08f, 3f, 0.08f);
            pole.transform.rotation = Quaternion.Euler(0f, 0f, 72f);
            Renderer r = pole.GetComponent<Renderer>();
            if (r != null) r.sharedMaterial = Mat("FlagPole", new Color(0.18f, 0.12f, 0.07f));
            GameObject cloth = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cloth.name = "Fallen_Flag_Cloth";
            cloth.transform.SetParent(parent, false);
            cloth.transform.position = position + new Vector3(0.7f, 1.2f, 0f);
            cloth.transform.localScale = new Vector3(1.6f, 0.04f, 1f);
            Renderer cr = cloth.GetComponent<Renderer>();
            if (cr != null) cr.sharedMaterial = Mat("FlagCloth", new Color(0.48f, 0.07f, 0.04f));
        }

        private static void CreatePlanes(Transform parent)
        {
            // 复用简化模型，不另做飞机美术；待正式模型替换
            for (int i = 0; i < 3; i++)
            {
                GameObject plane = new GameObject("JapanesePlane_" + i);
                plane.transform.SetParent(parent, false);
                plane.transform.position = new Vector3(-20 + i * 40f, 40f + i * 2f, 40f);
                Box(plane.transform, "Body", Vector3.zero, new Vector3(3f, 0.5f, 0.5f), Mat("PlaneBody", new Color(0.25f, 0.27f, 0.23f)));
                Box(plane.transform, "Wing", new Vector3(0f, 0f, 1.4f), new Vector3(0.6f, 0.08f, 3f), Mat("PlaneWing", new Color(0.25f, 0.27f, 0.23f)));
                Act1Plane mover = plane.AddComponent<Act1Plane>();
                mover.radius = 38f + i * 6f;
                mover.height = 40f + i * 3f;
                mover.center = new Vector3(0f, 0f, 50f);
                mover.phase = i * 2f;
            }
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
