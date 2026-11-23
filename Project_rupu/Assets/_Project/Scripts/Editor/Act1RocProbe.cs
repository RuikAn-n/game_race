#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Rupu.EditorTools
{
    public static class Act1RocProbe
    {
        [MenuItem("入谱/Act1 ROC 探针")]
        public static void Probe()
        {
            var scene = EditorSceneManager.OpenScene("Assets/Scenes/Act1_ROC.unity");
            GameObject player = GameObject.Find("Act1_Player");
            GameObject camera = GameObject.Find("Act1_ROC_Camera");
            GameObject story = GameObject.Find("ACT1_ROC_STORY");
            GameObject huanhai = GameObject.Find("BLD_ROC_HuanhaiLou");
            GameObject hall = GameObject.Find("BLD_ROC_AncestralHall");
            Debug.Log($"[Act1ROCProbe] roots={scene.rootCount} player={player != null} camera={camera != null} story={story != null} hall={hall != null} huanhai={huanhai != null}");
            if (player != null) Debug.Log($"[Act1ROCProbe] player pos={player.transform.position}");
        }
    }
}
#endif
