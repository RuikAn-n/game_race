#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Rupu.EditorTools
{
    public static class RocProbe
    {
        [MenuItem("入谱/ROC 探针")]
        public static void Probe()
        {
            var scene = EditorSceneManager.OpenScene("Assets/_Rupu/Scenes/Map_Yongchang_ROC.unity");
            int renderers = 0;
            int cameras = 0;
            int lights = 0;
            int missing = 0;
            foreach (GameObject root in scene.GetRootGameObjects())
            {
                renderers += root.GetComponentsInChildren<Renderer>(true).Length;
                cameras += root.GetComponentsInChildren<Camera>(true).Length;
                lights += root.GetComponentsInChildren<Light>(true).Length;
                foreach (Transform t in root.GetComponentsInChildren<Transform>(true))
                {
                    if (t.name.StartsWith("BLD_ROC_AncestralHall") || t.name.StartsWith("BLD_ROC_HuanhaiLou") || t.name.StartsWith("CH_WangYan"))
                    {
                        Debug.Log($"[ROCProbe] {t.name} @ {t.position}");
                    }
                }
            }
            Debug.Log($"[ROCProbe] scene={scene.name} roots={scene.rootCount} renderers={renderers} cameras={cameras} lights={lights}");
        }
    }
}
#endif
