// 《入谱》永昌堡总地图：按布局 JSON 生成场景（同一布局，按年代换建筑与材质）
//
//   菜单：入谱 / 永昌堡 / 生成民国场景 (1941)
//         入谱 / 永昌堡 / 生成明代场景 (1560，缺的明代模型用民国占位)
//         入谱 / 永昌堡 / 截图 (Builds/screens)
//   命令行：-executeMethod Rupu.EditorTools.RupuMapBuilder.BuildROCCLI
//           -executeMethod Rupu.EditorTools.RupuMapBuilder.CaptureCLI   （不要加 -nographics）
//
// 数据源（仓库根目录，不在 Assets 里）：
//   Data/map/yongchang_layout.json   布局（Tools/map/gen_layout.py 生成）
//   Data/map/era_kits.json           kind -> 各年代模型
//   Data/map/era_materials.json      语义材质 -> 各年代颜色
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Rupu.EditorTools
{
    public static class RupuMapBuilder
    {
        // ------------------------------------------------------------ 数据结构（字段名与 JSON 一致）
        [Serializable] public class Rect4 { public float x0, z0, x1, z1; }
        [Serializable] public class Meta { public float plan_scale, water_level, sea_x, hill_x; public Rect4 bounds; public Rect4 town; }
        [Serializable] public class WallPiece { public string id, kind, side, name; public float x, y, z, rot; }
        [Serializable] public class Water { public string id, name, kind; public float x0, z0, x1, z1, bottom; }
        [Serializable] public class Bridge { public string id, kind, name; public float x, z, rot, span; }
        [Serializable] public class Plot { public string id, kind, name, eras; public float x, y, z, rot, w, d; }
        [Serializable] public class Step { public string id, kind, name; public float x, z, rot; }
        [Serializable] public class Tree { public string kind; public float x, z, rot, s; }
        [Serializable] public class P2 { public float x, z; }
        [Serializable] public class PoleChain { public string id, eras; public P2[] points; }
        [Serializable] public class Anchor { public string id, note; public float x, y, z, rot; }
        [Serializable]
        public class Layout
        {
            public Meta meta; public WallPiece[] wall; public Water[] water; public Bridge[] bridges; public Plot[] plots;
            public Step[] steps; public Tree[] trees; public PoleChain[] poles; public Anchor[] anchors;
        }
        [Serializable] public class Kit { public string kind; public string[] roc; public string[] ming; }
        [Serializable] public class NeutralKit { public string kind, asset; }
        [Serializable] public class Kits { public Kit[] kits; public NeutralKit[] neutral; public string[] env; }
        [Serializable] public class MatDef { public string name, roc, ming; public float smooth; }
        [Serializable] public class Mats { public MatDef[] materials; }

        public const string SceneDir = "Assets/_Rupu/Scenes";
        public static string ScenePath(string era) => $"{SceneDir}/Map_Yongchang_{era}.unity";
        static string RepoRoot => Path.GetFullPath(Path.Combine(Application.dataPath, "..", ".."));
        static string DataPath(string f) => Path.Combine(RepoRoot, "Data", "map", f);

        static T Load<T>(string file) => JsonUtility.FromJson<T>(File.ReadAllText(DataPath(file)));

        // ------------------------------------------------------------ 菜单 / 命令行
        [MenuItem("入谱/永昌堡/生成民国场景 (1941)", priority = 20)]
        public static void BuildROCMenu() => Build("ROC", true);

        [MenuItem("入谱/永昌堡/生成明代场景 (1560，缺的明代模型用民国占位)", priority = 21)]
        public static void BuildMINGMenu() => Build("MING", true);

        [MenuItem("入谱/永昌堡/截图 (Builds/screens)", priority = 40)]
        public static void CaptureMenu() => Capture(ScenePath("ROC"));

        public static void BuildROCCLI() { RunCLI(() => Build("ROC", false)); }
        public static void BuildMINGCLI() { RunCLI(() => Build("MING", false)); }
        public static void CaptureCLI() { RunCLI(() => Capture(ScenePath("ROC"))); }
        public static void BuildAndCaptureCLI() { RunCLI(() => { Build("ROC", false); Capture(ScenePath("ROC")); }); }
        /// <summary>两个年代都生成并截图（明代缺的模型用民国占位，用来验证「同布局换建筑」流程）。</summary>
        public static void BuildAllCLI()
        {
            RunCLI(() =>
            {
                Build("MING", false); Capture(ScenePath("MING"), "MING_", 3);
                Build("ROC", false); Capture(ScenePath("ROC"));
                Validate(ScenePath("ROC"));
            });
        }

        static void RunCLI(Action a)
        {
            try { a(); EditorApplication.Exit(0); }
            catch (Exception e) { Debug.LogException(e); EditorApplication.Exit(1); }
        }

        // ------------------------------------------------------------ 生成
        static Dictionary<string, Material> matLib;
        static Dictionary<string, GameObject> prefabCache;
        static int missingCount;

        public static void Build(string era, bool interactive)
        {
            if (interactive && !EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            var lay = Load<Layout>("yongchang_layout.json");
            var kits = Load<Kits>("era_kits.json");
            var mats = Load<Mats>("era_materials.json");
            prefabCache = new Dictionary<string, GameObject>();
            missingCount = 0;
            matLib = BuildMaterialLibrary(mats, era);
            bool roc = era == "ROC";

            var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
            var root = new GameObject($"Map_Yongchang_{era}").transform;
            Transform G(string n) { var t = new GameObject(n).transform; t.SetParent(root, false); return t; }
            var gEnv = G("Env"); var gWall = G("Wall"); var gBridge = G("Bridges"); var gSteps = G("CanalSteps");
            var gBld = G("Buildings"); var gTree = G("Trees"); var gPole = G("Poles"); var gAnchor = G("Anchors"); var gBounds = G("Bounds");

            // 地形
            foreach (var e in kits.env) Place(e, gEnv, Vector3.zero, 0, e, true);

            var neutral = kits.neutral.ToDictionary(k => k.kind, k => k.asset);
            var kitMap = kits.kits.ToDictionary(k => k.kind, k => k);

            // 城墙（按方位分组）
            var sideRoots = new Dictionary<string, Transform>();
            foreach (var w in lay.wall)
            {
                if (!sideRoots.TryGetValue(w.side, out var sr))
                {
                    sr = new GameObject("Wall_" + w.side).transform; sr.SetParent(gWall, false); sideRoots[w.side] = sr;
                }
                var name = string.IsNullOrEmpty(w.name) ? $"{w.id}_{w.kind}" : $"{w.id}_{w.name}";
                Place(neutral[w.kind], sr, new Vector3(w.x, w.y, w.z), w.rot, name, true);
            }
            foreach (var b in lay.bridges)
                Place(neutral[b.kind], gBridge, new Vector3(b.x, 0, b.z), b.rot, $"{b.id}_{b.name}", true);
            foreach (var s in lay.steps)
                Place(neutral[s.kind], gSteps, new Vector3(s.x, 0, s.z), s.rot, $"{s.id}_{s.name}", true);

            // 建筑位
            int fallback = 0;
            foreach (var p in lay.plots)
            {
                if (!string.IsNullOrEmpty(p.eras) && !p.eras.Split(',').Contains(era)) continue;
                if (!kitMap.TryGetValue(p.kind, out var kit)) { Debug.LogWarning($"[Map] 未知 kind {p.kind}"); continue; }
                var list = roc ? kit.roc : (kit.ming != null && kit.ming.Length > 0 ? kit.ming : null);
                if (list == null) { list = kit.roc; fallback++; }
                if (list == null || list.Length == 0) continue;
                var asset = list[(int)(Hash(p.id) % (uint)list.Length)];
                var slot = new GameObject(string.IsNullOrEmpty(p.name) ? $"{p.id}_{p.kind}" : $"{p.id}_{p.name}");
                slot.transform.SetParent(gBld, false);
                slot.transform.SetPositionAndRotation(new Vector3(p.x, p.y, p.z), Quaternion.Euler(0, p.rot, 0));
                var ms = slot.AddComponent<MapSlot>();
                ms.id = p.id; ms.kind = p.kind; ms.displayName = p.name; ms.eras = p.eras;
                Place(asset, slot.transform, Vector3.zero, 0, asset, false);
                SetStatic(slot);
            }

            // 树
            foreach (var t in lay.trees)
            {
                var go = Place(neutral[t.kind], gTree, new Vector3(t.x, 0, t.z), t.rot, t.kind, true);
                if (go != null) go.transform.localScale = Vector3.one * t.s;
            }

            // 电线杆 + 电线（民国）
            if (roc && kitMap.TryGetValue("pole", out var poleKit))
                foreach (var ch in lay.poles) BuildPoleChain(ch, poleKit.roc[0], gPole);

            // 挂点
            foreach (var a in lay.anchors)
            {
                var go = new GameObject(a.id);
                go.transform.SetParent(gAnchor, false);
                go.transform.SetPositionAndRotation(new Vector3(a.x, a.y, a.z), Quaternion.Euler(0, a.rot, 0));
                var ma = go.AddComponent<MapAnchor>(); ma.id = a.id; ma.note = a.note;
            }

            BuildBounds(lay, gBounds);
            SetupLighting(era);
            var spawn = lay.anchors.FirstOrDefault(a => a.id == (roc ? "spawn_1941" : "spawn_1560"));
            SetupPlayer(spawn);
            CheckAxes(gEnv);

            Directory.CreateDirectory(SceneDir);
            var path = ScenePath(era);
            EditorSceneManager.SaveScene(scene, path);
            AddToBuild(path, roc);
            int plots = gBld.childCount;
            Debug.Log($"[Map] 已生成 {path}：城墙 {lay.wall.Length}、桥 {lay.bridges.Length}、建筑 {plots}、树 {lay.trees.Length}、挂点 {lay.anchors.Length}；" +
                      $"缺模型 {missingCount}；明代占位 {fallback}。");
        }

        static uint Hash(string s)
        {
            uint h = 2166136261;
            foreach (char c in s) { h ^= c; h *= 16777619; }
            return h;
        }

        static GameObject LoadModel(string asset)
        {
            if (prefabCache.TryGetValue(asset, out var go)) return go;
            string cat = asset.StartsWith("BLD_") ? "Buildings" : asset.StartsWith("PROP_") ? "Props" :
                         asset.StartsWith("ENV_") ? "Environments" : "Props";
            var path = $"Assets/Art/{cat}/{asset}/{asset}.fbx";
            go = AssetDatabase.LoadAssetAtPath<GameObject>(path);
            if (go == null) { Debug.LogWarning($"[Map] 缺模型 {path}（先运行 Tools/mac/build_yongchang.sh）"); missingCount++; }
            prefabCache[asset] = go;
            return go;
        }

        static GameObject Place(string asset, Transform parent, Vector3 pos, float rot, string name, bool setStatic)
        {
            var prefab = LoadModel(asset);
            if (prefab == null) return null;
            var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, parent);
            go.name = name;
            go.transform.localPosition = pos;
            go.transform.localRotation = Quaternion.Euler(0, rot, 0);
            RemapMaterials(go);
            SetupColliders(go);
            if (setStatic) SetStatic(go);
            return go;
        }

        // 碰撞约定：有 COL_* 子物体时只用它们做碰撞（并去掉渲染）；否则所有非 NOCOL_* 网格加 MeshCollider
        static void SetupColliders(GameObject go)
        {
            var mfs = go.GetComponentsInChildren<MeshFilter>(true);
            bool hasCol = mfs.Any(m => m.name.StartsWith("COL_"));
            foreach (var mf in mfs)
            {
                if (mf.sharedMesh == null) continue;
                bool isCol = mf.name.StartsWith("COL_");
                if (isCol)
                {
                    var r = mf.GetComponent<MeshRenderer>();
                    if (r) UnityEngine.Object.DestroyImmediate(r);
                }
                if ((hasCol && !isCol) || mf.name.StartsWith("NOCOL_")) continue;
                var mc = mf.gameObject.AddComponent<MeshCollider>();
                mc.sharedMesh = mf.sharedMesh;
            }
            foreach (var r in go.GetComponentsInChildren<MeshRenderer>(true))
                if (r.name.StartsWith("NOCOL_Water") || r.name.Contains("_Surface")) r.shadowCastingMode = ShadowCastingMode.Off;
        }

        static void SetStatic(GameObject go)
        {
            var flags = StaticEditorFlags.BatchingStatic | StaticEditorFlags.OccluderStatic | StaticEditorFlags.OccludeeStatic;
            foreach (var t in go.GetComponentsInChildren<Transform>(true))
                GameObjectUtility.SetStaticEditorFlags(t.gameObject, flags);
        }

        // ------------------------------------------------------------ 材质库
        const string MatRoot = "Assets/Art/Materials";

        static Dictionary<string, Material> BuildMaterialLibrary(Mats mats, string era)
        {
            var dir = $"{MatRoot}/{era}";
            Directory.CreateDirectory(dir);
            var grain = GrainTexture();
            var lit = Shader.Find("Universal Render Pipeline/Lit");
            var unlit = Shader.Find("Universal Render Pipeline/Unlit");
            var lib = new Dictionary<string, Material>();
            foreach (var m in mats.materials)
            {
                var path = $"{dir}/{m.name}.mat";
                var mat = AssetDatabase.LoadAssetAtPath<Material>(path);
                bool isWire = m.name == "M_Wire";
                if (mat == null)
                {
                    mat = new Material(isWire ? unlit : lit);
                    AssetDatabase.CreateAsset(mat, path);
                }
                ColorUtility.TryParseHtmlString(era == "ROC" ? m.roc : m.ming, out var c);
                mat.SetColor("_BaseColor", c);
                mat.color = c;
                if (!isWire)
                {
                    mat.SetFloat("_Smoothness", m.smooth);
                    mat.SetFloat("_Metallic", 0f);
                    if (!m.name.Contains("Water")) { mat.SetTexture("_BaseMap", grain); mat.mainTexture = grain; }
                }
                mat.enableInstancing = true;
                EditorUtility.SetDirty(mat);
                lib[m.name] = mat;
            }
            AssetDatabase.SaveAssets();
            return lib;
        }

        static string CleanMatName(string n)
        {
            n = n.Replace(" (Instance)", "");
            int dot = n.LastIndexOf('.');
            if (dot > 0 && n.Length - dot == 4 && int.TryParse(n.Substring(dot + 1), out _)) n = n.Substring(0, dot);
            return n;
        }

        static void RemapMaterials(GameObject go)
        {
            foreach (var r in go.GetComponentsInChildren<Renderer>(true))
            {
                var ms = r.sharedMaterials;
                bool changed = false;
                for (int i = 0; i < ms.Length; i++)
                {
                    if (ms[i] == null) continue;
                    if (matLib.TryGetValue(CleanMatName(ms[i].name), out var m)) { ms[i] = m; changed = true; }
                }
                if (changed) r.sharedMaterials = ms;
            }
        }

        // 纸纹：可平铺的值噪声，亮度 0.86~1.0，乘在基础色上
        static Texture2D GrainTexture()
        {
            var path = $"{MatRoot}/T_PaperGrain_D.png";
            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            if (tex != null) return tex;
            Directory.CreateDirectory(MatRoot);
            const int N = 512;
            var t = new Texture2D(N, N, TextureFormat.RGB24, false);
            var rnd = new System.Random(1941);
            float[] Lattice(int p) { var a = new float[p * p]; for (int i = 0; i < a.Length; i++) a[i] = (float)rnd.NextDouble(); return a; }
            var octs = new[] { (8, 0.45f), (32, 0.3f), (128, 0.25f) };
            var lats = octs.Select(o => Lattice(o.Item1)).ToArray();
            var px = new Color[N * N];
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float v = 0;
                    for (int o = 0; o < octs.Length; o++)
                    {
                        int p = octs[o].Item1;
                        float fx = (float)x / N * p, fy = (float)y / N * p;
                        int x0 = (int)fx, y0 = (int)fy;
                        float tx = fx - x0, ty = fy - y0;
                        tx = tx * tx * (3 - 2 * tx); ty = ty * ty * (3 - 2 * ty);
                        var L = lats[o];
                        float a = L[(y0 % p) * p + x0 % p], b = L[(y0 % p) * p + (x0 + 1) % p];
                        float c = L[((y0 + 1) % p) * p + x0 % p], d = L[((y0 + 1) % p) * p + (x0 + 1) % p];
                        v += Mathf.Lerp(Mathf.Lerp(a, b, tx), Mathf.Lerp(c, d, tx), ty) * octs[o].Item2;
                    }
                    float g = 0.86f + 0.14f * v;
                    px[y * N + x] = new Color(g, g * 0.985f, g * 0.96f);
                }
            t.SetPixels(px);
            File.WriteAllBytes(path, t.EncodeToPNG());
            AssetDatabase.ImportAsset(path);
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }

        // ------------------------------------------------------------ 电线杆
        static void BuildPoleChain(PoleChain ch, string asset, Transform parent)
        {
            var chain = new GameObject(ch.id).transform;
            chain.SetParent(parent, false);
            var pts = ch.points.Select(p => new Vector3(p.x, 0, p.z)).ToArray();
            var poles = new List<Transform>();
            for (int i = 0; i < pts.Length; i++)
            {
                var dir = (i < pts.Length - 1 ? pts[i + 1] - pts[i] : pts[i] - pts[i - 1]);
                float yaw = Mathf.Atan2(dir.x, dir.z) * Mathf.Rad2Deg;
                var go = Place(asset, chain, pts[i], yaw, $"Pole_{i:00}", true);
                if (go) poles.Add(go.transform);
            }
            var wireMat = matLib.TryGetValue("M_Wire", out var wm) ? wm : null;
            var offs = new[] { new Vector3(-0.8f, 6.78f, 0), new Vector3(-0.35f, 6.78f, 0), new Vector3(0.35f, 6.78f, 0), new Vector3(0.8f, 6.78f, 0) };
            for (int i = 0; i + 1 < poles.Count; i++)
                foreach (var o in offs)
                {
                    var a = poles[i].TransformPoint(o);
                    var b = poles[i + 1].TransformPoint(o);
                    var w = new GameObject("Wire").AddComponent<LineRenderer>();
                    w.transform.SetParent(chain, false);
                    const int seg = 10;
                    w.positionCount = seg + 1;
                    for (int k = 0; k <= seg; k++)
                    {
                        float t = (float)k / seg;
                        w.SetPosition(k, Vector3.Lerp(a, b, t) + Vector3.down * (0.45f * 4 * t * (1 - t)));
                    }
                    w.widthMultiplier = 0.03f;
                    w.shadowCastingMode = ShadowCastingMode.Off;
                    w.sharedMaterial = wireMat;
                }
        }

        // ------------------------------------------------------------ 边界 / 灯光 / 玩家
        static void BuildBounds(Layout lay, Transform parent)
        {
            float x0 = lay.meta.hill_x - 70, x1 = lay.meta.sea_x + 16, z0 = lay.meta.bounds.z0 + 2, z1 = lay.meta.bounds.z1 - 2;
            void Wall(string n, Vector3 c, Vector3 s)
            {
                var go = new GameObject(n);
                go.transform.SetParent(parent, false);
                go.transform.position = c;
                go.AddComponent<BoxCollider>().size = s;
            }
            float cx = (x0 + x1) / 2, cz = (z0 + z1) / 2, w = x1 - x0, d = z1 - z0;
            Wall("Bound_N", new Vector3(cx, 50, z1 + 1), new Vector3(w + 4, 220, 2));
            Wall("Bound_S", new Vector3(cx, 50, z0 - 1), new Vector3(w + 4, 220, 2));
            Wall("Bound_W", new Vector3(x0 - 1, 50, cz), new Vector3(2, 220, d + 4));
            Wall("Bound_E", new Vector3(x1 + 1, 50, cz), new Vector3(2, 220, d + 4));
        }

        static void SetupLighting(string era)
        {
            bool roc = era == "ROC";
            var sunGo = new GameObject("Sun");
            var sun = sunGo.AddComponent<Light>();
            sun.type = LightType.Directional;
            sun.shadows = LightShadows.Soft;
            sun.intensity = roc ? 1.05f : 1.35f;
            sun.color = roc ? new Color(0.88f, 0.9f, 0.86f) : new Color(1f, 0.93f, 0.82f);
            sunGo.transform.rotation = Quaternion.Euler(roc ? 42f : 50f, -35f, 0);
            RenderSettings.sun = sun;
            RenderSettings.ambientMode = AmbientMode.Trilight;
            RenderSettings.ambientSkyColor = roc ? new Color(0.62f, 0.66f, 0.64f) : new Color(0.7f, 0.68f, 0.62f);
            RenderSettings.ambientEquatorColor = roc ? new Color(0.5f, 0.53f, 0.5f) : new Color(0.58f, 0.54f, 0.47f);
            RenderSettings.ambientGroundColor = roc ? new Color(0.3f, 0.31f, 0.28f) : new Color(0.34f, 0.3f, 0.25f);
            RenderSettings.fog = true;
            RenderSettings.fogMode = FogMode.Linear;
            RenderSettings.fogColor = roc ? new Color(0.66f, 0.69f, 0.66f) : new Color(0.8f, 0.76f, 0.68f);
            RenderSettings.fogStartDistance = roc ? 90f : 160f;
            RenderSettings.fogEndDistance = roc ? 750f : 1100f;
            RenderSettings.skybox = null;
            // 阴影：俯视要看得远，同时压住近处的阴影条纹（shadow acne）
            var urp = GraphicsSettings.defaultRenderPipeline as UniversalRenderPipelineAsset;
            if (urp != null)
            {
                var so = new SerializedObject(urp);
                void SetF(string n, float v) { var sp = so.FindProperty(n); if (sp != null) sp.floatValue = v; }
                void SetI(string n, int v) { var sp = so.FindProperty(n); if (sp != null) sp.intValue = v; }
                SetF("m_ShadowDistance", 160f);
                SetI("m_ShadowCascadeCount", 4);
                SetI("m_MainLightShadowmapResolution", 4096);
                SetF("m_ShadowDepthBias", 1.6f);
                SetF("m_ShadowNormalBias", 1.2f);
                SetI("m_SoftShadowQuality", 2);
                so.ApplyModifiedPropertiesWithoutUndo();
                EditorUtility.SetDirty(urp);
                AssetDatabase.SaveAssets();
            }
        }

        static void SetupPlayer(Anchor spawn)
        {
            var camGo = new GameObject("Main Camera");
            camGo.tag = "MainCamera";
            var cam = camGo.AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = RenderSettings.fogColor;
            cam.farClipPlane = 2000f;
            cam.nearClipPlane = 0.2f;
            camGo.AddComponent<AudioListener>();

            var player = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            player.name = "Player_REF_1.75m";
            player.transform.localScale = new Vector3(0.6f, 0.875f, 0.6f);
            var p = spawn != null ? new Vector3(spawn.x, spawn.y + 1.0f, spawn.z) : new Vector3(0, 1, 0);
            player.transform.SetPositionAndRotation(p, Quaternion.Euler(0, spawn != null ? spawn.rot : 0, 0));
            UnityEngine.Object.DestroyImmediate(player.GetComponent<CapsuleCollider>());
            var cc = player.AddComponent<CharacterController>();
            cc.height = 2f; cc.radius = 0.5f; cc.stepOffset = 0.35f; cc.slopeLimit = 50f;
            var ctrl = player.AddComponent<ArtTestController>();
            ctrl.cam = cam;
            camGo.transform.position = p + new Vector3(0, 3, -5);
        }

        // 轴向自检：罗山在堡西，团结里山体包围盒中心应在 x<0
        static void CheckAxes(Transform env)
        {
            var hills = env.Cast<Transform>().FirstOrDefault(t => t.name.StartsWith("ENV_Luoshan"));
            if (hills == null) return;
            var rs = hills.GetComponentsInChildren<Renderer>();
            if (rs.Length == 0) return;
            var b = rs[0].bounds;
            foreach (var r in rs) b.Encapsulate(r.bounds);
            if (b.center.x < 0) Debug.Log($"[Map] 轴向检查通过：罗山中心 x={b.center.x:0}（西）");
            else Debug.LogError($"[Map] 轴向错误：罗山中心 x={b.center.x:0}，应在西侧（x<0）。检查 FBX 导出轴设置。");
        }

        static void AddToBuild(string path, bool first)
        {
            var list = EditorBuildSettings.scenes.Where(s => s.path != path).ToList();
            var e = new EditorBuildSettingsScene(path, true);
            if (first) list.Insert(0, e); else list.Add(e);
            EditorBuildSettings.scenes = list.ToArray();
        }

        // ------------------------------------------------------------ 可走性自检
        public static void ValidateCLI() { RunCLI(() => { if (!Validate(ScenePath("ROC"))) throw new Exception("可走性检查未通过"); }); }

        [MenuItem("入谱/永昌堡/可走性自检", priority = 41)]
        public static void ValidateMenu() => Validate(ScenePath("ROC"));

        /// <summary>用 CharacterController 在几条关键路线上走一遍：穿城门、上马道登城、过桥、从河里爬上河埠头。</summary>
        public static bool Validate(string scenePath)
        {
            EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
            Physics.SyncTransforms();
            var go = new GameObject("WalkTester");
            var cc = go.AddComponent<CharacterController>();
            cc.height = 1.8f; cc.radius = 0.35f; cc.center = new Vector3(0, 0.9f, 0); cc.stepOffset = 0.35f; cc.slopeLimit = 50f;
            bool all = true;
            bool Walk(string name, Vector3 start, Vector3[] via, Func<Vector3, bool> ok)
            {
                cc.enabled = false; go.transform.position = start; cc.enabled = true;
                foreach (var target in via)
                {
                    for (int i = 0; i < 2000; i++)
                    {
                        var d = target - go.transform.position; d.y = 0;
                        if (d.magnitude < 0.3f) break;
                        cc.Move(d.normalized * 0.12f + Vector3.down * 0.3f);
                    }
                }
                var p = go.transform.position;
                bool pass = ok(p);
                Debug.Log($"[Map] 可走性 {(pass ? "通过" : "失败")}：{name}，终点 {p}");
                all &= pass;
                return pass;
            }
            // 1 通市门：堡内 -> 门洞 -> 护城河桥 -> 北官道
            Walk("穿通市门出城过护城河", new Vector3(4, 0.5f, 165), new[] { new Vector3(4, 0, 220) }, p => p.z > 218 && p.y > -0.2f);
            // 2 环海门 + 瓮城 -> 东护城河桥 -> 码头路
            Walk("穿环海门、瓮城到码头路", new Vector3(95, 0.5f, 40), new[] { new Vector3(170, 0, 40) }, p => p.x > 168);
            // 3 马道登城（通市门西侧马道，向东抬升）再上走道
            Walk("上马道登城", new Vector3(-24, 0.5f, 180.5f), new[] { new Vector3(-6.5f, 0, 180.5f), new Vector3(-6.5f, 0, 185f), new Vector3(-30, 0, 185f) },
                 p => p.y > 6.8f && p.x < -28);
            // 4 北巷过上河桥
            Walk("北巷过上河桥", new Vector3(-58, 0.5f, 110), new[] { new Vector3(-22, 0, 110) }, p => p.x > -23 && p.y > -0.2f);
            // 5 落水后从上河河埠头爬上西岸
            Walk("从上河河埠头上岸", new Vector3(-39, -1.4f, -150), new[] { new Vector3(-50, 0, -150) }, p => p.x < -46 && p.y > -0.2f);
            // 6 走到城墙外不能穿墙
            Walk("城墙不可穿越", new Vector3(30, 0.5f, 170), new[] { new Vector3(30, 0, 200) }, p => p.z < 183);
            UnityEngine.Object.DestroyImmediate(go);
            Debug.Log(all ? "[Map] 可走性检查全部通过" : "[Map] 可走性检查有失败项");
            return all;
        }

        // ------------------------------------------------------------ 截图
        public struct Shot { public string name; public Vector3 pos, look; public float fov; public bool noFog; }

        public static void Capture(string scenePath, string prefix = "", int maxShots = 99)
        {
            EditorSceneManager.OpenScene(scenePath, OpenSceneMode.Single);
            var outDir = Path.Combine(RepoRoot, "Builds", "screens");
            Directory.CreateDirectory(outDir);
            DynamicGI.UpdateEnvironment();
            var shots = new[]
            {
                new Shot { name = "01_overview_topdown", pos = new Vector3(0, 640, -40), look = new Vector3(0, 0, 0), fov = 50, noFog = true },
                new Shot { name = "02_overview_se", pos = new Vector3(260, 230, -330), look = new Vector3(0, 0, 10), fov = 45, noFog = true },
                new Shot { name = "03_strategy_view", pos = new Vector3(20, 70, -40), look = new Vector3(0, 0, 20), fov = 50 },
                new Shot { name = "04_huanhai_from_dock_road", pos = new Vector3(196, 1.7f, 40), look = new Vector3(113, 9, 40), fov = 55 },
                new Shot { name = "05_main_street", pos = new Vector3(4, 1.7f, 150), look = new Vector3(4, 2.5f, 60), fov = 60 },
                new Shot { name = "06_zuci_front", pos = new Vector3(-12, 1.7f, 10), look = new Vector3(-20, 4, 30), fov = 62 },
                new Shot { name = "07_shanghe_canal", pos = new Vector3(-36, 2.0f, -70), look = new Vector3(-40, 0.5f, 0), fov = 60 },
                new Shot { name = "08_wall_walk", pos = new Vector3(60, 8.9f, 185.5f), look = new Vector3(-40, 8, 185), fov = 60 },
                new Shot { name = "09_east_watergate", pos = new Vector3(78, 3.5f, -44), look = new Vector3(113, 2, -56), fov = 60 },
                new Shot { name = "10_tonshi_gate_outside", pos = new Vector3(4, 1.7f, 232), look = new Vector3(4, 7, 185), fov = 60 },
                new Shot { name = "11_wengcheng_top", pos = new Vector3(150, 30, 70), look = new Vector3(118, 4, 40), fov = 55 },
                new Shot { name = "12_west_gate_hills", pos = new Vector3(-100, 1.7f, 12), look = new Vector3(-200, 15, 12), fov = 60 },
            };
            var go = new GameObject("CaptureCam");
            var cam = go.AddComponent<Camera>();
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = RenderSettings.fogColor;
            cam.farClipPlane = 3000f;
            cam.nearClipPlane = 0.2f;
            var rt = new RenderTexture(1920, 1080, 24, RenderTextureFormat.ARGB32) { antiAliasing = 4 };
            cam.targetTexture = rt;
            var tex = new Texture2D(1920, 1080, TextureFormat.RGB24, false);
            foreach (var s in shots.Take(maxShots))
            {
                go.transform.position = s.pos;
                go.transform.LookAt(s.look);
                cam.fieldOfView = s.fov;
                bool fog = RenderSettings.fog;
                if (s.noFog) RenderSettings.fog = false;
                cam.Render();
                RenderSettings.fog = fog;
                RenderTexture.active = rt;
                tex.ReadPixels(new Rect(0, 0, 1920, 1080), 0, 0);
                tex.Apply();
                File.WriteAllBytes(Path.Combine(outDir, prefix + s.name + ".png"), tex.EncodeToPNG());
            }
            RenderTexture.active = null;
            cam.targetTexture = null;
            UnityEngine.Object.DestroyImmediate(go);
            rt.Release();
            Debug.Log($"[Map] 截图已保存到 {outDir}");
        }
    }
}
