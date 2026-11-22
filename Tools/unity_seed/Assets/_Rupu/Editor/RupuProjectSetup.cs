// 《入谱》工程初始化 + 美术测试场景
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Rupu.EditorTools
{
    public static class RupuProjectSetup
    {
        static readonly string[] Folders =
        {
            "Assets/Art/Characters", "Assets/Art/Enemies", "Assets/Art/Bosses", "Assets/Art/Buildings",
            "Assets/Art/Props", "Assets/Art/Environments", "Assets/Art/UI", "Assets/Art/VFX",
            "Assets/Art/Cutscenes", "Assets/Art/EndingCards", "Assets/Art/Animations",
            "Assets/Audio/VO", "Assets/Audio/SFX", "Assets/Audio/BGM",
            "Assets/Scenes", "Assets/_Rupu/Scenes",
        };

        [MenuItem("入谱/初始化工程 (首次打开执行一次)", priority = 0)]
        public static void Init()
        {
            foreach (var f in Folders)
                if (!AssetDatabase.IsValidFolder(f)) Directory.CreateDirectory(f);

            PlayerSettings.companyName = "RupuTeam";
            PlayerSettings.productName = "入谱";
            PlayerSettings.colorSpace = ColorSpace.Linear;
            PlayerSettings.defaultScreenWidth = 1920;
            PlayerSettings.defaultScreenHeight = 1080;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;   // VM 内测试更方便；发布前改 FullScreenWindow
            PlayerSettings.resizableWindow = true;
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);
            EditorSettings.serializationMode = SerializationMode.ForceText;
            SetupURP();

            AssetDatabase.Refresh();
            Debug.Log("[Rupu] 初始化完成：目录、URP、PlayerSettings（1920x1080 窗口 / Linear / Mono）。");
        }

        const string SettingsDir = "Assets/_Rupu/Settings";

        // 创建 URP 资源并设为所有画质等级的渲染管线（已有则跳过）
        public static void SetupURP()
        {
            if (!AssetDatabase.IsValidFolder(SettingsDir)) AssetDatabase.CreateFolder("Assets/_Rupu", "Settings");
            var assetPath = SettingsDir + "/URP_Asset.asset";
            var urp = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>(assetPath);
            if (urp == null)
            {
                var data = ScriptableObject.CreateInstance<UniversalRendererData>();
                AssetDatabase.CreateAsset(data, SettingsDir + "/URP_Renderer.asset");
                urp = UniversalRenderPipelineAsset.Create(data);
                urp.shadowDistance = 60f;
                AssetDatabase.CreateAsset(urp, assetPath);
                AssetDatabase.SaveAssets();
            }
            // CreateInstance 出来的 RendererData 着色器引用为空，显式补全（重复执行也安全）
            const string urpPkg = "Packages/com.unity.render-pipelines.universal";
            foreach (var rd in AssetDatabase.LoadAllAssetsAtPath(SettingsDir + "/URP_Renderer.asset").OfType<UniversalRendererData>())
            {
                ResourceReloader.ReloadAllNullIn(rd, urpPkg);
                if (rd.postProcessData == null)
                    rd.postProcessData = AssetDatabase.LoadAssetAtPath<PostProcessData>(urpPkg + "/Runtime/Data/PostProcessData.asset");
                EditorUtility.SetDirty(rd);
            }
            GraphicsSettings.defaultRenderPipeline = urp;
            int current = QualitySettings.GetQualityLevel();
            for (int i = 0; i < QualitySettings.names.Length; i++)
            {
                QualitySettings.SetQualityLevel(i, false);
                QualitySettings.renderPipeline = urp;
            }
            QualitySettings.SetQualityLevel(current, false);
            AssetDatabase.SaveAssets();
        }

        // 命令行一次性初始化：-executeMethod Rupu.EditorTools.RupuProjectSetup.InitCLI
        public static void InitCLI()
        {
            Init();
            CreateArtTestScene();
            AssetDatabase.SaveAssets();
            EditorApplication.Exit(0);
        }

        [MenuItem("入谱/创建美术测试场景", priority = 1)]
        public static void CreateArtTestScene()
        {
            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            var scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);

            var ground = GameObject.CreatePrimitive(PrimitiveType.Plane);
            ground.name = "Ground_100m";
            ground.transform.localScale = new Vector3(10, 1, 10);

            // 比例参照：1m 立方体 + 1.75m 人
            var cube = GameObject.CreatePrimitive(PrimitiveType.Cube);
            cube.name = "REF_Cube_1m";
            cube.transform.position = new Vector3(-3, 0.5f, 0);

            // 玩家：胶囊 + CharacterController + 双视角控制器
            var player = GameObject.CreatePrimitive(PrimitiveType.Capsule);
            player.name = "Player_REF_1.75m";
            player.transform.localScale = new Vector3(0.6f, 0.875f, 0.6f);
            player.transform.position = new Vector3(0, 0.875f, -4);
            Object.DestroyImmediate(player.GetComponent<CapsuleCollider>());
            var cc = player.AddComponent<CharacterController>();
            cc.height = 2f; cc.radius = 0.5f;
            var nose = GameObject.CreatePrimitive(PrimitiveType.Cube);  // 指示正面 (+Z)
            nose.name = "Front_+Z";
            Object.DestroyImmediate(nose.GetComponent<BoxCollider>());
            nose.transform.SetParent(player.transform, false);
            nose.transform.localPosition = new Vector3(0, 0.6f, 0.5f);
            nose.transform.localScale = new Vector3(0.3f, 0.15f, 0.3f);

            var ctrl = player.AddComponent<Rupu.ArtTestController>();
            ctrl.cam = Camera.main;

            // 把人物/敌人/Boss/道具排成一排，便于检查比例/朝向/材质（建筑和地形看 永昌堡 场景；动画文件 @ 不排）
            var guids = AssetDatabase.FindAssets("t:Model", new[] { "Assets/Art" });
            float x = 0;
            var lineup = new GameObject("ArtLineup").transform;
            var ac = RupuCharacters.EnsureController();
            foreach (var g in guids)
            {
                var path = AssetDatabase.GUIDToAssetPath(g);
                if (path.Contains("/Buildings/") || path.Contains("/Environments/") || path.Contains("@")) continue;
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (prefab == null) continue;
                var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, lineup);
                go.transform.position = new Vector3(x, 0, 4);
                go.transform.rotation = Quaternion.Euler(0, 180, 0);
                var anim = go.GetComponent<Animator>();
                if (anim != null) anim.runtimeAnimatorController = ac;
                x += 2f;
            }

            var path0 = RupuBuild.ArtTestScene;
            EditorSceneManager.SaveScene(scene, path0);
            if (!EditorBuildSettings.scenes.Any(s => s.path == path0))
                EditorBuildSettings.scenes = EditorBuildSettings.scenes
                    .Append(new EditorBuildSettingsScene(path0, true)).ToArray();
            Debug.Log($"[Rupu] 美术测试场景已创建：{path0}，摆放了 {guids.Length} 个模型。");
        }
    }
}
