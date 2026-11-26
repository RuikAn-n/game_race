// 《入谱》人物接入：Humanoid 检查、共用移动动画控制器、玩家（王砚）与 NPC 摆放、人物合影截图
//   菜单：入谱 / 人物 / 检查 Humanoid、人物合影截图
//   命令行：-executeMethod Rupu.EditorTools.RupuCharacters.LineupCLI
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Animations;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Playables;

namespace Rupu.EditorTools
{
    public static class RupuCharacters
    {
        public const string ControllerPath = "Assets/Art/Animations/AC_Humanoid_Locomotion.controller";
        public const string AnimBase = "CH_WangYan_1941";          // 动画来源：CH_WangYan_1941@Idle/Walk/Run.fbx
        public static readonly string[] Cast =
            { "CH_WangYan_1941", "CH_WangYan_1560", "NPC_WangPei", "NPC_WangShugao", "NPC_WangDe", "NPC_WangBingzhi" };
        // 1941 族亲（第一幕祠堂）：族老、三派、族中冷遇/亲善、孩童、少女
        public static readonly string[] ClanCast =
            { "NPC_ClanElder", "NPC_ClanJiao", "NPC_ClanShao", "NPC_ClanCang", "NPC_ClanUncle", "NPC_ClanGranny", "NPC_ClanBoy", "NPC_ClanGirl" };
        // 1941 日军、小贩、街坊（第一幕街市）
        public static readonly string[] StreetCast =
            { "NPC_JpOfficer", "NPC_JpSoldier_A", "NPC_JpSoldier_B", "NPC_JpSoldier_C", "NPC_VendorVeg", "NPC_VendorGoods",
              "NPC_TownOldMan", "NPC_TownWoman", "NPC_TownInjured", "NPC_TownRefugee" };

        public static string ModelPath(string asset)
        {
            string cat = asset.StartsWith("PROP_") ? "Props" : asset.StartsWith("BLD_") ? "Buildings" : "Characters";
            return $"Assets/Art/{cat}/{asset}/{asset}.fbx";
        }

        public static AnimationClip Clip(string action)
        {
            var path = $"Assets/Art/Characters/{AnimBase}@{action}/{AnimBase}@{action}.fbx";
            return AssetDatabase.LoadAllAssetsAtPath(path).OfType<AnimationClip>()
                                .FirstOrDefault(c => !c.name.StartsWith("__preview__"));
        }

        /// <summary>Speed 参数驱动的 Idle/Walk/Run 混合树（ArtTestController 会写 Speed）。</summary>
        public static RuntimeAnimatorController EnsureController()
        {
            Directory.CreateDirectory(Path.GetDirectoryName(ControllerPath));
            var idle = Clip("Idle"); var walk = Clip("Walk"); var run = Clip("Run");
            if (idle == null || walk == null || run == null)
            {
                Debug.LogWarning("[Chars] 缺少动画片段 CH_WangYan_1941@Idle/Walk/Run，先运行 Tools/mac/build_yongchang.sh");
                return null;
            }
            AssetDatabase.DeleteAsset(ControllerPath);
            var ac = AnimatorController.CreateAnimatorControllerAtPath(ControllerPath);
            ac.AddParameter("Speed", AnimatorControllerParameterType.Float);
            var state = ac.CreateBlendTreeInController("Locomotion", out var tree, 0);
            tree.blendType = BlendTreeType.Simple1D;
            tree.blendParameter = "Speed";
            tree.useAutomaticThresholds = false;
            tree.AddChild(idle, 0f);
            tree.AddChild(walk, 1.8f);
            tree.AddChild(run, 5f);
            ac.layers[0].stateMachine.defaultState = state;
            // 动作状态（无连线）：脚本里 Animator.CrossFadeInFixedTime("<动作名>") 进入，CrossFade("Locomotion") 回到走跑。
            // 名字带 Loop 的循环播放；其余一次性动作播完停在最后一帧（跪下、倒地、拔刀指人）。
            var sm = ac.layers[0].stateMachine;
            int row = 0;
            foreach (var g in AllGestures())
            {
                var clip = Clip(g);
                if (clip == null) { Debug.LogWarning($"[Chars] 缺少动作片段 {AnimBase}@{g}"); continue; }
                var s = sm.AddState(g, new Vector3(300, 60 * row++, 0));
                s.motion = clip;
                s.writeDefaultValues = true;
            }
            AssetDatabase.SaveAssets();
            return ac;
        }

        /// <summary>全部共用动作：第一幕 Gestures 在前，其余各幕（Assets/Art/Characters/CH_WangYan_1941@*/ 里除 Idle/Walk/Run 外）按名字排序追加。</summary>
        public static string[] AllGestures()
        {
            var extra = Directory.Exists("Assets/Art/Characters")
                ? Directory.GetDirectories("Assets/Art/Characters", AnimBase + "@*")
                           .Select(d => Path.GetFileName(d).Substring(AnimBase.Length + 1))
                           .Where(a => a != "Idle" && a != "Walk" && a != "Run" && !Gestures.Contains(a))
                           .OrderBy(a => a, StringComparer.Ordinal)
                : Enumerable.Empty<string>();
            return Gestures.Concat(extra).ToArray();
        }

        /// <summary>第一幕动作（Tools/blender/rupu_char.py 的 GESTURES，同名状态）。</summary>
        public static readonly string[] Gestures =
            { "TalkLoop", "ArgueLoop", "CowerLoop", "WatchLoop", "AttentionLoop", "Beckon", "IncenseBow", "KneelPray",
              "TouchFlag", "DrawSword", "Push", "Fall" };

        public static GameObject Instantiate(string asset, Transform parent, Vector3 pos, float rot, RuntimeAnimatorController ac)
        {
            var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath(asset));
            if (prefab == null) { Debug.LogWarning("[Chars] 缺模型 " + ModelPath(asset)); return null; }
            var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
            go.transform.SetPositionAndRotation(pos, Quaternion.Euler(0, rot, 0));
            var anim = go.GetComponent<Animator>();
            if (anim != null)
            {
                anim.runtimeAnimatorController = ac;
                anim.applyRootMotion = false;
                anim.cullingMode = AnimatorCullingMode.CullUpdateTransforms;
            }
            foreach (var r in go.GetComponentsInChildren<SkinnedMeshRenderer>()) r.updateWhenOffscreen = false;
            return go;
        }

        /// <summary>玩家：空物体 + CharacterController（脚底为原点）+ 王砚模型 + 测试用双视角控制器。</summary>
        public static GameObject CreatePlayer(string asset, Vector3 feet, float rot, Camera cam, RuntimeAnimatorController ac)
        {
            var player = new GameObject("Player_" + asset);
            player.transform.SetPositionAndRotation(feet + Vector3.up * 0.05f, Quaternion.Euler(0, rot, 0));
            var cc = player.AddComponent<CharacterController>();
            cc.height = 1.75f; cc.radius = 0.32f; cc.center = new Vector3(0, 0.875f, 0);
            cc.stepOffset = 0.35f; cc.slopeLimit = 50f;
            var model = Instantiate(asset, player.transform, player.transform.position, rot, ac);
            if (model == null)
            {   // 模型缺失时退回胶囊
                var cap = GameObject.CreatePrimitive(PrimitiveType.Capsule);
                UnityEngine.Object.DestroyImmediate(cap.GetComponent<CapsuleCollider>());
                cap.transform.SetParent(player.transform, false);
                cap.transform.localPosition = new Vector3(0, 0.875f, 0);
                cap.transform.localScale = new Vector3(0.6f, 0.875f, 0.6f);
            }
            var ctrl = player.AddComponent<ArtTestController>();
            ctrl.cam = cam;
            ctrl.tpHeight = 2.35f;      // 原点在脚底：相机看向约 1.5 m 高
            return player;
        }

        public static GameObject PlaceNPC(string asset, Transform parent, Vector3 pos, float rot, RuntimeAnimatorController ac)
        {
            var go = Instantiate(asset, parent, pos, rot, ac);
            if (go == null) return null;
            var col = go.AddComponent<CapsuleCollider>();
            col.center = new Vector3(0, 0.88f, 0); col.height = 1.76f; col.radius = 0.3f;
            return go;
        }

        // ------------------------------------------------------------ 检查
        [MenuItem("入谱/人物/检查 Humanoid", priority = 60)]
        public static bool CheckAvatars()
        {
            bool ok = true;
            foreach (var a in Cast.Concat(ClanCast).Concat(StreetCast).Concat(new[] { AnimBase + "@Idle", AnimBase + "@Walk", AnimBase + "@Run" }))
            {
                var path = a.Contains("@") ? $"Assets/Art/Characters/{a}/{a}.fbx" : ModelPath(a);
                var av = AssetDatabase.LoadAllAssetsAtPath(path).OfType<Avatar>().FirstOrDefault();
                bool good = av != null && av.isValid && av.isHuman;
                ok &= good;
                var mi = AssetImporter.GetAtPath(path) as ModelImporter;
                Debug.Log($"[Chars] {a}: Avatar {(good ? "有效 Humanoid" : "无效")}  动画类型 {mi?.animationType}");
            }
            foreach (var k in new[] { "Idle", "Walk", "Run" })
            {
                var c = Clip(k);
                if (c == null) { Debug.Log($"[Chars] 片段 {k}: 缺失"); ok = false; continue; }
                var b = AnimationUtility.GetCurveBindings(c);
                Debug.Log($"[Chars] 片段 {k}: 名称 {c.name} 时长 {c.length:0.00}s humanMotion {c.humanMotion} 循环 {c.isLooping} 曲线 {b.Length} " +
                          string.Join(",", b.Take(6).Select(x => x.propertyName)));
            }
            return ok;
        }

        // ------------------------------------------------------------ 第三幕：敌人 / Boss 控制器
        public const string CombatControllerPath = "Assets/Art/Animations/AC_Combat.controller";

        /// <summary>
        /// 敌人和 Boss 共用的控制器：Locomotion（共用 Idle/Walk/Run）+ Assets/Art/{Enemies,Bosses}/*@*/ 的全部片段，
        /// 状态名 = @ 后的动作名（EN_SwordAttack1、BS_GuiwoPhaseChange……，见 Docs/act3_enemies.md）。无连线，脚本 CrossFade 进入。
        /// </summary>
        [MenuItem("入谱/人物/生成敌人与 Boss 动画控制器", priority = 62)]
        public static RuntimeAnimatorController EnsureCombatController()
        {
            var idle = Clip("Idle"); var walk = Clip("Walk"); var run = Clip("Run");
            if (idle == null || walk == null || run == null) { Debug.LogWarning("[Chars] 缺少 Idle/Walk/Run"); return null; }
            Directory.CreateDirectory(Path.GetDirectoryName(CombatControllerPath));
            AssetDatabase.DeleteAsset(CombatControllerPath);
            var ac = AnimatorController.CreateAnimatorControllerAtPath(CombatControllerPath);
            ac.AddParameter("Speed", AnimatorControllerParameterType.Float);
            var state = ac.CreateBlendTreeInController("Locomotion", out var tree, 0);
            tree.blendType = BlendTreeType.Simple1D; tree.blendParameter = "Speed"; tree.useAutomaticThresholds = false;
            tree.AddChild(idle, 0f); tree.AddChild(walk, 1.8f); tree.AddChild(run, 5f);
            var sm = ac.layers[0].stateMachine;
            sm.defaultState = state;
            int row = 0, n = 0;
            foreach (var root in new[] { "Assets/Art/Enemies", "Assets/Art/Bosses" })
            {
                if (!Directory.Exists(root)) continue;
                foreach (var d in Directory.GetDirectories(root, "*@*").OrderBy(x => x, StringComparer.Ordinal))
                {
                    var asset = Path.GetFileName(d);
                    var action = asset.Substring(asset.IndexOf('@') + 1);
                    if (sm.states.Any(st => st.state.name == action)) continue;
                    var clip = AssetDatabase.LoadAllAssetsAtPath($"{d}/{asset}.fbx").OfType<AnimationClip>()
                                            .FirstOrDefault(c => !c.name.StartsWith("__preview__"));
                    if (clip == null) { Debug.LogWarning("[Chars] 缺片段 " + asset); continue; }
                    var s = sm.AddState(action, new Vector3(300 + 260 * (row / 20), 60 * (row % 20), 0));
                    row++; n++;
                    s.motion = clip; s.writeDefaultValues = true;
                }
            }
            AssetDatabase.SaveAssets();
            Debug.Log($"[Chars] AC_Combat：{n} 个战斗动作状态");
            return ac;
        }

        public static void ControllersCLI()
        {
            try
            {
                var a = EnsureController(); var b = EnsureCombatController();
                var sm = ((AnimatorController)a).layers[0].stateMachine;
                Debug.Log($"[Chars] AC_Humanoid_Locomotion：{sm.states.Length} 个状态");
                EditorApplication.Exit(a != null && b != null ? 0 : 1);
            }
            catch (Exception e) { Debug.LogException(e); EditorApplication.Exit(1); }
        }

        /// <summary>检查 Characters/Enemies/Bosses 下所有人形模型（不含 @动画）的 Avatar 是否有效。</summary>
        public static void AvatarsCLI()
        {
            int ok = 0; var bad = new System.Collections.Generic.List<string>();
            foreach (var root in new[] { "Assets/Art/Characters", "Assets/Art/Enemies", "Assets/Art/Bosses" })
                foreach (var d in Directory.GetDirectories(root).Where(x => !Path.GetFileName(x).Contains("@")))
                {
                    var n = Path.GetFileName(d);
                    var av = AssetDatabase.LoadAllAssetsAtPath($"{d}/{n}.fbx").OfType<Avatar>().FirstOrDefault();
                    if (av != null && av.isValid && av.isHuman) ok++; else bad.Add(n);
                }
            Debug.Log($"[Chars] Humanoid Avatar 有效 {ok} 个；无效/缺失 {bad.Count} 个：{string.Join(",", bad)}");
            EditorApplication.Exit(bad.Count == 0 ? 0 : 1);
        }

        // ------------------------------------------------------------ 合影截图
        [MenuItem("入谱/人物/人物合影截图 (Builds/screens)", priority = 61)]
        public static void LineupMenu() => Lineup();

        public static void LineupCLI()
        {
            try { CheckAvatars(); Lineup(); ClanLineup(); StreetLineup(); GestureLineup(); EditorApplication.Exit(0); }
            catch (Exception e) { Debug.LogException(e); EditorApplication.Exit(1); }
        }

        [MenuItem("入谱/人物/族亲合影截图 (Builds/screens)", priority = 62)]
        public static void ClanLineup() => LineupOf(ClanCast, "clan");

        [MenuItem("入谱/人物/街市人物合影截图 (Builds/screens)", priority = 63)]
        public static void StreetLineup() => LineupOf(StreetCast, "street");

        /// <summary>12 个第一幕动作各取一帧（循环动作取中段，一次性动作取末帧），检查重定向到不同体型后是否正常。</summary>
        [MenuItem("入谱/人物/第一幕动作截图 (Builds/screens)", priority = 64)]
        public static void GestureLineup()
        {
            var who = new[] { "NPC_ClanElder", "NPC_ClanShao", "NPC_TownWoman", "NPC_TownOldMan", "NPC_JpOfficer", "NPC_ClanElder",
                              "CH_WangYan_1941", "CH_WangYan_1941", "CH_WangYan_1941", "NPC_JpOfficer", "NPC_JpSoldier_B", "NPC_VendorVeg" };
            var times = Gestures.Select(g => g.EndsWith("Loop") ? 0.3f : g == "IncenseBow" || g == "Beckon" ? 0.3f : 0.99f).ToArray();
            LineupOf(who, "gestures", Gestures, times);
        }

        public static void Lineup() => LineupOf(Cast, "chars");

        static void LineupOf(string[] cast, string prefix, string[] clipNames = null, float[] clipTimes = null)
        {
            var ac = EnsureController();
            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
            ground.transform.localScale = Vector3.one * 3;
            var gm = new Material(Shader.Find("Universal Render Pipeline/Lit"));
            gm.SetColor("_BaseColor", new Color(0.75f, 0.71f, 0.63f));
            ground.GetComponent<Renderer>().sharedMaterial = gm;
            var sun = new GameObject("Sun").AddComponent<Light>();
            sun.type = LightType.Directional; sun.shadows = LightShadows.Soft; sun.intensity = 1.2f;
            sun.transform.rotation = Quaternion.Euler(40, 150, 0);
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = new Color(0.7f, 0.72f, 0.7f);
            RenderSettings.ambientEquatorColor = new Color(0.55f, 0.55f, 0.52f);
            RenderSettings.ambientGroundColor = new Color(0.35f, 0.33f, 0.3f);
            RenderSettings.fog = false;

            var gos = new GameObject[cast.Length];
            for (int i = 0; i < cast.Length; i++)
                gos[i] = Instantiate(cast[i], null, new Vector3((i - (cast.Length - 1) / 2f) * 1.1f, 0, 0), 180, ac);
            float dist = Mathf.Max(9.5f, cast.Length * 1.15f);       // 人多时相机拉远
            // 道具：王沛的枪立在身旁，王秉之的拐、王叔杲的算盘
            void Prop(string a, Vector3 p, Vector3 e)
            {
                var pr = AssetDatabase.LoadAssetAtPath<GameObject>(ModelPath(a));
                if (pr == null) return;
                var g = (GameObject)PrefabUtility.InstantiatePrefab(pr);
                g.transform.SetPositionAndRotation(p, Quaternion.Euler(e));
            }
            if (prefix == "chars")
            {
                Prop("PROP_Spear_Pei", gos[2] ? gos[2].transform.position + new Vector3(-0.45f, 0, -0.1f) : Vector3.zero, Vector3.zero);
                Prop("PROP_Cane_Bingzhi", gos[5] ? gos[5].transform.position + new Vector3(-0.4f, 0, -0.15f) : Vector3.zero, new Vector3(0, 90, 0));
                Prop("PROP_Abacus", gos[3] ? gos[3].transform.position + new Vector3(0, 0, -0.6f) : Vector3.zero, Vector3.zero);
            }
            else if (prefix == "clan")
            {   // 族老的手杖
                Prop("PROP_Staff_Elder", gos[0] ? gos[0].transform.position + new Vector3(-0.4f, 0, -0.12f) : Vector3.zero, Vector3.zero);
            }

            var outDir = Path.Combine(Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..")), "Builds", "screens");
            Directory.CreateDirectory(outDir);
            var cam = new GameObject("Cam").AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0.66f, 0.69f, 0.66f);
            cam.fieldOfView = 30;
            var rt = new RenderTexture(1920, 1080, 24) { antiAliasing = 4 };
            cam.targetTexture = rt;
            var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
            void Shot(string name, Vector3 pos, Vector3 look)
            {
                cam.transform.position = pos; cam.transform.LookAt(look);
                cam.Render();
                RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0); tex.Apply();
                File.WriteAllBytes(Path.Combine(outDir, name + ".png"), tex.EncodeToPNG());
                RenderTexture.active = null;
            }
            Shot(prefix + "_01_tpose", new Vector3(0, 1.3f, -dist), new Vector3(0, 0.95f, 0));

            // 用 PlayableGraph 在编辑器里求值 Humanoid 片段（验证重定向到每个人物）：默认待机 / 走 / 跑 交替，或按 clipNames 逐个
            var clips = clipNames != null ? clipNames.Select(Clip).ToArray()
                                          : new[] { Clip("Idle"), Clip("Walk"), Clip("Idle"), Clip("Walk"), Clip("Run"), Clip("Idle") };
            float[] times = { 0.5f, 0.25f, 1.0f, 0.75f, 0.2f, 1.5f };   // 秒；clipTimes 则为片段长度的比例
            var graphs = new System.Collections.Generic.List<UnityEngine.Playables.PlayableGraph>();
            for (int i = 0; i < gos.Length; i++)
            {
                var an = gos[i] ? gos[i].GetComponent<Animator>() : null;
                if (an == null || clips[i % clips.Length] == null) continue;
                var g = UnityEngine.Playables.PlayableGraph.Create("lineup" + i);
                var output = UnityEngine.Animations.AnimationPlayableOutput.Create(g, "anim", an);
                var cp = UnityEngine.Animations.AnimationClipPlayable.Create(g, clips[i % clips.Length]);
                output.SetSourcePlayable(cp);
                cp.SetTime(clipTimes != null ? clipTimes[i % clipTimes.Length] * clips[i % clips.Length].length : times[i % times.Length]);
                var ua = an.GetBoneTransform(HumanBodyBones.LeftUpperArm);
                var before = ua ? ua.rotation.eulerAngles : Vector3.zero;
                g.Evaluate();
                Debug.Log($"[Chars] 求值 {gos[i].name}: isHuman {an.isHuman} 左上臂 {before} -> {(ua ? ua.rotation.eulerAngles : Vector3.zero)}");
                // 编辑器里蒙皮不会自动刷新：烘焙成静态网格再截图
                foreach (var smr in gos[i].GetComponentsInChildren<SkinnedMeshRenderer>())
                {
                    var baked = new Mesh();
                    smr.BakeMesh(baked);
                    var bg = new GameObject(smr.name + "_Baked");
                    bg.transform.SetPositionAndRotation(smr.transform.position, smr.transform.rotation);
                    bg.AddComponent<MeshFilter>().sharedMesh = baked;
                    bg.AddComponent<MeshRenderer>().sharedMaterials = smr.sharedMaterials;
                    smr.enabled = false;
                }
                graphs.Add(g);
            }
            Shot(prefix + "_02_posed", new Vector3(0, 1.3f, -dist), new Vector3(0, 0.95f, 0));
            Shot(prefix + "_03_posed_3q", new Vector3(5.5f, 2.2f, -6.5f), new Vector3(0, 0.9f, 0));
            foreach (var g in graphs) g.Destroy();
            cam.targetTexture = null;
            rt.Release();
            Debug.Log("[Chars] 人物合影已保存到 " + outDir);
        }
    }
}
