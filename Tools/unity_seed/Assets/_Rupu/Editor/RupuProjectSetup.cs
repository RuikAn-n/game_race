// 《入谱》工程初始化 + 美术测试场景
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;

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

            AssetDatabase.Refresh();
            Debug.Log("[Rupu] 初始化完成：目录、PlayerSettings（1920x1080 窗口 / Linear / Mono）。");
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

            // 把 Assets/Art 下所有模型排成一排，便于检查比例/朝向/材质
            var guids = AssetDatabase.FindAssets("t:Model", new[] { "Assets/Art" });
            float x = 0;
            var lineup = new GameObject("ArtLineup").transform;
            foreach (var g in guids)
            {
                var path = AssetDatabase.GUIDToAssetPath(g);
                var prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path);
                if (prefab == null) continue;
                var go = (GameObject)PrefabUtility.InstantiatePrefab(prefab, lineup);
                go.transform.position = new Vector3(x, 0, 4);
                x += 3f;
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
