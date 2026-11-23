#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Rupu.EditorTools
{
    public static class RocInspect
    {
        [MenuItem("入谱/ROC 细查")]
        public static void Inspect()
        {
            var scene = EditorSceneManager.OpenScene("Assets/_Rupu/Scenes/Map_Yongchang_ROC.unity");
            foreach (GameObject root in scene.GetRootGameObjects())
            {
                Debug.Log($"[ROCInspect] ROOT {root.name}");
                if (root.name.Contains("Camera") || root.name.Contains("Player") || root.name.Contains("Systems") || root.name.Contains("Map"))
                {
                    Dump(root.transform, 0);
                }
            }

            DumpNamed("BLD_ROC_AncestralHall");
            DumpNamed("BLD_ROC_HuanhaiLou");
            DumpNamed("CH_WangYan_1941");
        }

        private static void DumpNamed(string name)
        {
            GameObject go = GameObject.Find(name);
            if (go == null) { Debug.Log($"[ROCInspect] missing {name}"); return; }
            Renderer[] renderers = go.GetComponentsInChildren<Renderer>();
            Bounds bounds = new Bounds(go.transform.position, Vector3.zero);
            bool first = true;
            foreach (Renderer r in renderers)
            {
                if (first) { bounds = r.bounds; first = false; }
                else bounds.Encapsulate(r.bounds);
            }
            Debug.Log($"[ROCInspect] {name} pos={go.transform.position} bounds center={bounds.center} size={bounds.size}");
            foreach (Transform child in go.transform)
            {
                Debug.Log($"[ROCInspect]   child {child.name} @ {child.position}");
            }
        }

        private static void Dump(Transform t, int depth)
        {
            if (depth > 2) return;
            Debug.Log($"[ROCInspect] {new string(' ', depth * 2)}{t.name} @ {t.position}");
            foreach (Transform c in t) Dump(c, depth + 1);
        }
    }
}
#endif
