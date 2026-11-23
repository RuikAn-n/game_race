#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Rupu.EditorTools
{
    public static class Act1RocOpen
    {
        private const string ScenePath = "Assets/Scenes/Act1_ROC.unity";

        [MenuItem("入谱/打开 Act1 ROC 场景（自动退出 Play）", priority = 0)]
        public static void Open()
        {
            if (EditorApplication.isPlaying)
            {
                EditorApplication.isPlaying = false;
                EditorApplication.delayCall += OpenWhenEditMode;
                return;
            }

            OpenWhenEditMode();
        }

        private static void OpenWhenEditMode()
        {
            if (EditorApplication.isPlaying)
            {
                EditorApplication.delayCall += OpenWhenEditMode;
                return;
            }

            if (!System.IO.File.Exists(ScenePath))
            {
                EditorUtility.DisplayDialog("场景缺失", "找不到 " + ScenePath, "知道了");
                return;
            }

            if (!EditorSceneManager.SaveCurrentModifiedScenesIfUserWantsTo()) return;
            EditorSceneManager.OpenScene(ScenePath, OpenSceneMode.Single);
            Debug.Log("[Act1ROC] 已打开 Act1_ROC.unity");
        }

        [MenuItem("入谱/停止 Play 并回到编辑模式", priority = 1)]
        public static void StopPlay()
        {
            EditorApplication.isPlaying = false;
            EditorApplication.delayCall += () =>
            {
                if (!EditorApplication.isPlaying)
                {
                    Debug.Log("[Rupu] 已退出 Play，可打开场景或生成资产。");
                }
            };
        }
    }
}
#endif
