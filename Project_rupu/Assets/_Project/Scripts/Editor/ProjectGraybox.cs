#if UNITY_EDITOR
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace Rupu.EditorTools
{
    public static class ProjectGraybox
    {
        [MenuItem("入谱/创建灰盒城")]
        public static void Create()
        {
            UnityEngine.SceneManagement.Scene scene = EditorSceneManager.NewScene(NewSceneSetup.DefaultGameObjects, NewSceneMode.Single);
            GameObject root = new GameObject("GRAYBOX_永昌堡");
            Transform t = root.transform;

            Material earth = Mat("Earth", new Color(0.28f, 0.25f, 0.20f));
            Material stone = Mat("Stone", new Color(0.42f, 0.40f, 0.34f));
            Material dark = Mat("Dark", new Color(0.16f, 0.15f, 0.13f));
            Material wood = Mat("Wood", new Color(0.30f, 0.19f, 0.10f));

            Box("Ground", t, new Vector3(0f, -0.5f, 0f), new Vector3(180f, 1f, 130f), earth);

            BuildWallNS(t, "N", 1f, stone, dark, wood);
            BuildWallNS(t, "S", -1f, stone, dark, wood);
            BuildWallEW(t, "E", 1f, stone, dark, wood);
            BuildWallEW(t, "W", -1f, stone, dark, wood);

            Box("Walkway_N", t, new Vector3(0f, 8.45f, 55f), new Vector3(160f, 0.4f, 6f), stone);
            Box("Walkway_S", t, new Vector3(0f, 8.45f, -55f), new Vector3(160f, 0.4f, 6f), stone);
            Box("Walkway_E", t, new Vector3(80f, 8.45f, 0f), new Vector3(6f, 0.4f, 110f), stone);
            Box("Walkway_W", t, new Vector3(-80f, 8.45f, 0f), new Vector3(6f, 0.4f, 110f), stone);

            BuildStairs(t, new Vector3(-18f, 0f, 51f), stone);
            BuildStairs(t, new Vector3(76f, 0f, -10f), stone);

            Camera camera = Camera.main;
            if (camera != null)
            {
                camera.transform.position = new Vector3(0f, 48f, -74f);
                camera.transform.rotation = Quaternion.Euler(28f, 0f, 0f);
                camera.farClipPlane = 300f;
            }

            EditorSceneManager.SaveScene(scene, "Assets/Scenes/Graybox.unity");
            AssetDatabase.Refresh();
            Debug.Log("[Graybox] 已创建 Assets/Scenes/Graybox.unity");
        }

        private static void BuildWallNS(Transform parent, string id, float side, Material stone, Material dark, Material wood)
        {
            float z = 57.5f * side;
            float segment = 74.5f;
            Box($"Wall_{id}_L", parent, new Vector3(-42.75f, 4f, z), new Vector3(segment, 8f, 10f), stone);
            Box($"Wall_{id}_R", parent, new Vector3(42.75f, 4f, z), new Vector3(segment, 8f, 10f), stone);
            Box($"Plinth_{id}", parent, new Vector3(0f, 0.4f, z), new Vector3(168f, 0.8f, 10f), dark);

            Box($"Gate_{id}_L", parent, new Vector3(-8f, 6f, z), new Vector3(5f, 12f, 10f), stone);
            Box($"Gate_{id}_R", parent, new Vector3(8f, 6f, z), new Vector3(5f, 12f, 10f), stone);
            Box($"Gate_{id}_Beam", parent, new Vector3(0f, 11.5f, z), new Vector3(11f, 1.2f, 10f), stone);
            Box($"Gate_{id}_Roof", parent, new Vector3(0f, 13f, z), new Vector3(21f, 1f, 11f), dark);
            Box($"Gate_{id}_Opening", parent, new Vector3(0f, 2.5f, z - 5.05f * side), new Vector3(10f, 5f, 0.12f), dark);
            Box($"Gate_{id}_Door", parent, new Vector3(0f, 2.5f, z - 4.9f * side), new Vector3(9f, 5f, 0.25f), wood);
        }

        private static void BuildWallEW(Transform parent, string id, float side, Material stone, Material dark, Material wood)
        {
            float x = 80f * side;
            float segment = 49.5f;
            Box($"Wall_{id}_N", parent, new Vector3(x, 4f, 30.25f), new Vector3(10f, 8f, segment), stone);
            Box($"Wall_{id}_S", parent, new Vector3(x, 4f, -30.25f), new Vector3(10f, 8f, segment), stone);
            Box($"Plinth_{id}", parent, new Vector3(x, 0.4f, 0f), new Vector3(10f, 0.8f, 112f), dark);

            Box($"Gate_{id}_N", parent, new Vector3(x, 6f, 8f), new Vector3(10f, 12f, 5f), stone);
            Box($"Gate_{id}_S", parent, new Vector3(x, 6f, -8f), new Vector3(10f, 12f, 5f), stone);
            Box($"Gate_{id}_Beam", parent, new Vector3(x, 11.5f, 0f), new Vector3(10f, 1.2f, 11f), stone);
            Box($"Gate_{id}_Roof", parent, new Vector3(x, 13f, 0f), new Vector3(11f, 1f, 21f), dark);
            Box($"Gate_{id}_Opening", parent, new Vector3(x - 5.05f * side, 2.5f, 0f), new Vector3(0.12f, 5f, 10f), dark);
            Box($"Gate_{id}_Door", parent, new Vector3(x - 4.9f * side, 2.5f, 0f), new Vector3(0.25f, 5f, 9f), wood);
        }

        private static void BuildStairs(Transform parent, Vector3 start, Material material)
        {
            for (int i = 0; i < 8; i++)
            {
                Box($"Stair_{i}", parent, start + new Vector3(0f, i * 1f + 0.25f, i * 1.2f), new Vector3(6f, 0.5f, 1.2f), material);
            }
        }

        private static GameObject Box(string name, Transform parent, Vector3 position, Vector3 scale, Material material)
        {
            GameObject go = GameObject.CreatePrimitive(PrimitiveType.Cube);
            go.name = name;
            go.transform.SetParent(parent, false);
            go.transform.position = position;
            go.transform.localScale = scale;
            Renderer renderer = go.GetComponent<Renderer>();
            if (renderer != null) renderer.sharedMaterial = material;
            return go;
        }

        private static Material Mat(string name, Color color)
        {
            Shader shader = Shader.Find("Standard");
            Material material = new Material(shader != null ? shader : Shader.Find("Diffuse"));
            material.name = name;
            material.color = color;
            return material;
        }
    }
}
#endif
