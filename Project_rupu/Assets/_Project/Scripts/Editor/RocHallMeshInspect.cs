#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Rupu.EditorTools
{
    public static class RocHallMeshInspect
    {
        [MenuItem("入谱/ROC 祖祠 Mesh 探针")]
        public static void Probe()
        {
            EditorSceneManager.OpenScene("Assets/Scenes/Act1_ROC.unity");
            GameObject hall = GameObject.Find("BLD_ROC_AncestralHall");
            if (hall == null) { Debug.Log("[HallMesh] missing"); return; }
            foreach (MeshFilter mf in hall.GetComponentsInChildren<MeshFilter>(true))
            {
                Mesh m = mf.sharedMesh;
                Debug.Log($"[HallMesh] filter={mf.name} mesh={m?.name} verts={m?.vertexCount} sub={m?.subMeshCount} bounds={m?.bounds} renderer={mf.GetComponent<Renderer>()?.sharedMaterials.Length}");
                if (m != null)
                {
                    for (int i = 0; i < m.subMeshCount; i++)
                        Debug.Log($"[HallMesh] sub{i} tris={m.GetTriangles(i).Length / 3} mat={mf.GetComponent<Renderer>()?.sharedMaterials[i]?.name}");
                }
            }
            foreach (MeshCollider mc in hall.GetComponentsInChildren<MeshCollider>(true))
            {
                Debug.Log($"[HallMesh] collider mesh={mc.sharedMesh?.name} verts={mc.sharedMesh?.vertexCount} bounds={mc.sharedMesh?.bounds}");
            }
        }
    }
}
#endif
