#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Rupu.EditorTools
{
    public static class RocHallInspect
    {
        [MenuItem("入谱/ROC 祖祠门/内部探针")]
        public static void Probe()
        {
            var scene = EditorSceneManager.OpenScene("Assets/Scenes/Act1_ROC.unity");
            GameObject hall = GameObject.Find("BLD_ROC_AncestralHall");
            if (hall == null)
            {
                Debug.Log("[HallProbe] hall missing");
                return;
            }

            Debug.Log($"[HallProbe] hall={hall.transform.position} children={hall.transform.childCount}");
            foreach (Transform t in hall.GetComponentsInChildren<Transform>(true))
            {
                if (t.name.ToLower().Contains("door") || t.name.ToLower().Contains("gate") || t.name.ToLower().Contains("wall") || t.name.ToLower().Contains("room") || t.name.ToLower().Contains("hall"))
                {
                    Debug.Log($"[HallProbe] {t.name} local={t.localPosition} world={t.position} scale={t.localScale}");
                }
            }

            foreach (Collider c in hall.GetComponentsInChildren<Collider>(true))
            {
                Debug.Log($"[HallProbe] collider {c.name} type={c.GetType().Name} enabled={c.enabled}");
            }
        }
    }
}
#endif
