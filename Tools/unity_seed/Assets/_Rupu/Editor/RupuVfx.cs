// 《入谱》第一幕特效：在编辑器里生成粒子预制体（材质用 URP Particles/Unlit 存成资产，打包时着色器一定会带上）
//   菜单：入谱 / 特效 / 生成第一幕特效
//   命令行：-executeMethod Rupu.EditorTools.RupuVfx.BuildCLI
//   输出：Assets/Art/VFX/PF_VFX_*.prefab、M_VFX_*.mat、T_VFX_Soft.png
//
//   PF_VFX_Rain          雨（挂在相机上跟随玩家）          PF_VFX_IncenseSmoke 香火烟
//   PF_VFX_Candle        烛火 + 小点光                    PF_VFX_PaperAsh     飘落的纸灰（残谱/春祭）
//   PF_VFX_Fire          火焰 + 火星 + 火光（街尾火场）     PF_VFX_FireSmoke    大股黑烟柱
//   PF_VFX_PlaneTrail    飞机翼尖尾迹（TrailRenderer）      PF_VFX_PropellerDisc 螺旋桨虚影盘
//   旗面旧血直接做在 PROP_FallenFlag 模型上（M_PR_Blood），不另做特效。
using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using UnityEngine.Rendering;

namespace Rupu.EditorTools
{
    public static class RupuVfx
    {
        public const string Dir = "Assets/Art/VFX";

        [MenuItem("入谱/特效/生成第一幕特效", priority = 70)]
        public static void BuildMenu() => Build();

        public static void BuildCLI()
        {
            try { Build(); EditorApplication.Exit(0); }
            catch (Exception e) { Debug.LogException(e); EditorApplication.Exit(1); }
        }

        public static string PrefabPath(string name) => $"{Dir}/{name}.prefab";

        public static void Build()
        {
            Directory.CreateDirectory(Dir);
            var soft = SoftTexture();
            var alpha = Mat("M_VFX_Alpha", soft, false);
            var add = Mat("M_VFX_Add", soft, true);

            Save("PF_VFX_Rain", go =>
            {
                var ps = PS(go, alpha, 1.1f, 0f, 0.025f, 4000, new Color(0.78f, 0.8f, 0.82f, 0.32f), ParticleSystemSimulationSpace.World);
                Emit(ps, 2600);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(36f, 0.5f, 36f);
                go.transform.localPosition = new Vector3(0f, 12f, 6f);
                var v = ps.velocityOverLifetime; v.enabled = true; v.space = ParticleSystemSimulationSpace.World;
                v.x = new ParticleSystem.MinMaxCurve(-1.2f); v.y = new ParticleSystem.MinMaxCurve(-15f); v.z = new ParticleSystem.MinMaxCurve(0.4f);
                var r = go.GetComponent<ParticleSystemRenderer>();
                r.renderMode = ParticleSystemRenderMode.Stretch; r.velocityScale = 0.06f; r.lengthScale = 1f;
                // 打到屋顶/地面即消失：祠堂、街屋里不会下雨
                var col = ps.collision; col.enabled = true; col.type = ParticleSystemCollisionType.World;
                col.mode = ParticleSystemCollisionMode.Collision3D; col.quality = ParticleSystemCollisionQuality.Low;
                col.lifetimeLoss = 1f; col.bounce = 0f; col.maxCollisionShapes = 64;
            });
            Save("PF_VFX_IncenseSmoke", go =>
            {
                var ps = PS(go, alpha, 4.5f, 0.22f, 0.07f, 60, new Color(0.82f, 0.8f, 0.76f, 0.4f), ParticleSystemSimulationSpace.World);
                Emit(ps, 7);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 4f; sh.radius = 0.02f;
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                Grow(ps, 1f, 7f); Fade(ps, new Color(0.85f, 0.83f, 0.78f), 0.45f);
                var n = ps.noise; n.enabled = true; n.strength = 0.12f; n.frequency = 0.6f;
            });
            Save("PF_VFX_Candle", go =>
            {
                var ps = PS(go, add, 0.35f, 0.06f, 0.05f, 30, new Color(1f, 0.62f, 0.22f, 0.9f), ParticleSystemSimulationSpace.Local);
                Emit(ps, 14);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 2f; sh.radius = 0.004f;
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                Grow(ps, 1f, 0.3f); Fade(ps, new Color(1f, 0.55f, 0.2f), 0.9f);
                AddLight(go, new Color(1f, 0.66f, 0.35f), 2.2f, 0.7f, new Vector3(0f, 0f, 0.05f));
            });
            Save("PF_VFX_PaperAsh", go =>
            {
                var ps = PS(go, alpha, 7f, 0.15f, 0.05f, 80, new Color(0.25f, 0.23f, 0.21f, 0.85f), ParticleSystemSimulationSpace.World);
                Emit(ps, 5);
                var main = ps.main; main.startSize = new ParticleSystem.MinMaxCurve(0.025f, 0.07f); main.gravityModifier = 0.015f;
                main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
                var col = new ParticleSystem.MinMaxGradient(new Color(0.22f, 0.2f, 0.18f, 0.9f), new Color(0.75f, 0.32f, 0.14f, 0.9f));
                main.startColor = col;
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(4f, 0.5f, 4f);
                go.transform.localPosition = new Vector3(0f, 3f, 0f);
                var n = ps.noise; n.enabled = true; n.strength = 0.35f; n.frequency = 0.4f;
                var rot = ps.rotationOverLifetime; rot.enabled = true; rot.z = new ParticleSystem.MinMaxCurve(-2f, 2f);
            });
            Save("PF_VFX_Fire", go =>
            {
                var ps = PS(go, add, 1.0f, 1.6f, 0.9f, 220, new Color(1f, 0.55f, 0.15f, 0.85f), ParticleSystemSimulationSpace.World);
                Emit(ps, 70);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 12f; sh.radius = 0.9f;
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                Grow(ps, 1f, 0.15f);
                var c = ps.colorOverLifetime; c.enabled = true;
                var g = new Gradient();
                g.SetKeys(new[] { new GradientColorKey(new Color(1f, 0.82f, 0.35f), 0f), new GradientColorKey(new Color(0.85f, 0.25f, 0.06f), 0.5f),
                                  new GradientColorKey(new Color(0.3f, 0.05f, 0.02f), 1f) },
                          new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(0.95f, 0.12f), new GradientAlphaKey(0f, 1f) });
                c.color = g;
                var n = ps.noise; n.enabled = true; n.strength = 0.5f; n.frequency = 1.2f;
                var embers = Child(go, "Embers");
                var eps = PS(embers, add, 2.5f, 2.5f, 0.05f, 120, new Color(1f, 0.6f, 0.2f, 1f), ParticleSystemSimulationSpace.World);
                Emit(eps, 18);
                var esh = eps.shape; esh.shapeType = ParticleSystemShapeType.Cone; esh.angle = 25f; esh.radius = 1f;
                var en = eps.noise; en.enabled = true; en.strength = 1f; en.frequency = 0.8f;
                Fade(eps, new Color(1f, 0.5f, 0.15f), 1f);
                var smoke = Child(go, "Smoke");
                smoke.transform.localPosition = new Vector3(0f, 0f, 1.2f);
                var sps = PS(smoke, alpha, 5f, 1.4f, 1.2f, 80, new Color(0.12f, 0.11f, 0.1f, 0.55f), ParticleSystemSimulationSpace.World);
                Emit(sps, 10);
                var ssh = sps.shape; ssh.shapeType = ParticleSystemShapeType.Cone; ssh.angle = 15f; ssh.radius = 0.8f;
                Grow(sps, 1f, 3.5f); Fade(sps, new Color(0.12f, 0.11f, 0.1f), 0.55f);
                AddLight(go, new Color(1f, 0.5f, 0.2f), 9f, 2.4f, new Vector3(0f, 0f, 1f));
            });
            Save("PF_VFX_FireSmoke", go =>
            {
                var ps = PS(go, alpha, 9f, 2.2f, 2.2f, 120, new Color(0.1f, 0.09f, 0.085f, 0.6f), ParticleSystemSimulationSpace.World);
                Emit(ps, 9);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 10f; sh.radius = 1.5f;
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                Grow(ps, 1f, 3.5f); Fade(ps, new Color(0.1f, 0.09f, 0.085f), 0.6f);
                var v = ps.velocityOverLifetime; v.enabled = true; v.space = ParticleSystemSimulationSpace.World;
                v.x = new ParticleSystem.MinMaxCurve(0.6f); v.y = new ParticleSystem.MinMaxCurve(0f); v.z = new ParticleSystem.MinMaxCurve(0.3f);
                var n = ps.noise; n.enabled = true; n.strength = 0.6f; n.frequency = 0.25f;
            });
            Save("PF_VFX_PlaneTrail", go =>
            {
                var tr = go.AddComponent<TrailRenderer>();
                tr.time = 1.4f; tr.minVertexDistance = 0.5f;
                tr.widthCurve = new AnimationCurve(new Keyframe(0f, 0.22f), new Keyframe(1f, 0f));
                var g = new Gradient();
                g.SetKeys(new[] { new GradientColorKey(new Color(0.9f, 0.9f, 0.88f), 0f), new GradientColorKey(new Color(0.8f, 0.8f, 0.8f), 1f) },
                          new[] { new GradientAlphaKey(0.45f, 0f), new GradientAlphaKey(0f, 1f) });
                tr.colorGradient = g;
                tr.sharedMaterial = alpha;
                tr.shadowCastingMode = ShadowCastingMode.Off;
            });
            Save("PF_VFX_PropellerDisc", go =>
            {
                var disc = GameObject.CreatePrimitive(PrimitiveType.Cylinder);
                UnityEngine.Object.DestroyImmediate(disc.GetComponent<Collider>());
                disc.name = "Disc";
                disc.transform.SetParent(go.transform, false);
                disc.transform.localScale = new Vector3(2.5f, 0.005f, 2.5f);
                disc.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);       // 圆盘法线 = 本地 +Z（机身轴）
                var m = Mat("M_VFX_PropDisc", soft, false, new Color(0.15f, 0.14f, 0.13f, 0.18f));
                var r = disc.GetComponent<MeshRenderer>();
                r.sharedMaterial = m; r.shadowCastingMode = ShadowCastingMode.Off;
            });
            AssetDatabase.SaveAssets();
            Debug.Log("[VFX] 第一幕特效已生成：" + Dir);
        }

        // ------------------------------------------------------------ 工具
        static void Save(string name, Action<GameObject> setup)
        {
            var go = new GameObject(name);
            setup(go);
            PrefabUtility.SaveAsPrefabAsset(go, PrefabPath(name));
            UnityEngine.Object.DestroyImmediate(go);
        }

        static GameObject Child(GameObject parent, string name)
        {
            var c = new GameObject(name);
            c.transform.SetParent(parent.transform, false);
            return c;
        }

        static ParticleSystem PS(GameObject go, Material mat, float life, float speed, float size, int max, Color color,
                                 ParticleSystemSimulationSpace space)
        {
            var ps = go.AddComponent<ParticleSystem>();
            var main = ps.main;
            main.loop = true; main.prewarm = true; main.playOnAwake = true;
            main.startLifetime = new ParticleSystem.MinMaxCurve(life * 0.75f, life);
            main.startSpeed = new ParticleSystem.MinMaxCurve(speed * 0.7f, speed);
            main.startSize = new ParticleSystem.MinMaxCurve(size * 0.7f, size);
            main.startColor = color;
            main.maxParticles = max;
            main.simulationSpace = space;
            main.scalingMode = ParticleSystemScalingMode.Hierarchy;
            var r = go.GetComponent<ParticleSystemRenderer>();
            r.sharedMaterial = mat;
            r.shadowCastingMode = ShadowCastingMode.Off;
            r.receiveShadows = false;
            return ps;
        }

        static void Emit(ParticleSystem ps, float rate)
        {
            var e = ps.emission; e.enabled = true; e.rateOverTime = rate;
        }

        static void Grow(ParticleSystem ps, float from, float to)
        {
            var s = ps.sizeOverLifetime; s.enabled = true;
            float k = Mathf.Max(from, to);
            s.size = new ParticleSystem.MinMaxCurve(k, new AnimationCurve(new Keyframe(0f, from / k), new Keyframe(1f, to / k)));
        }

        static void Fade(ParticleSystem ps, Color c, float a)
        {
            var col = ps.colorOverLifetime; col.enabled = true;
            var g = new Gradient();
            g.SetKeys(new[] { new GradientColorKey(c, 0f), new GradientColorKey(c, 1f) },
                      new[] { new GradientAlphaKey(0f, 0f), new GradientAlphaKey(a, 0.15f), new GradientAlphaKey(0f, 1f) });
            col.color = g;
        }

        static void AddLight(GameObject go, Color c, float range, float intensity, Vector3 local)
        {
            var l = Child(go, "Light").AddComponent<Light>();
            l.type = LightType.Point; l.color = c; l.range = range; l.intensity = intensity; l.shadows = LightShadows.None;
            l.transform.localPosition = local;
        }

        static Material Mat(string name, Texture2D tex, bool additive, Color? tint = null)
        {
            var path = $"{Dir}/{name}.mat";
            var shader = Shader.Find("Universal Render Pipeline/Particles/Unlit");
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (m == null) { m = new Material(shader); AssetDatabase.CreateAsset(m, path); }
            m.shader = shader;
            m.SetTexture("_BaseMap", tex);
            m.SetColor("_BaseColor", tint ?? Color.white);
            m.SetFloat("_Surface", 1f);
            m.SetFloat("_Blend", additive ? 2f : 0f);
            m.SetFloat("_SrcBlend", (float)BlendMode.SrcAlpha);
            m.SetFloat("_DstBlend", additive ? (float)BlendMode.One : (float)BlendMode.OneMinusSrcAlpha);
            m.SetFloat("_ZWrite", 0f);
            m.SetOverrideTag("RenderType", "Transparent");
            m.EnableKeyword("_SURFACE_TYPE_TRANSPARENT");
            m.renderQueue = (int)RenderQueue.Transparent;
            EditorUtility.SetDirty(m);
            return m;
        }

        /// <summary>柔边圆点贴图（64×64，白色、alpha 从中心到边缘衰减），所有粒子共用。</summary>
        static Texture2D SoftTexture()
        {
            var path = $"{Dir}/T_VFX_Soft.png";
            var tex = AssetDatabase.LoadAssetAtPath<Texture2D>(path);
            if (tex != null) return tex;
            const int N = 64;
            var t = new Texture2D(N, N, TextureFormat.RGBA32, false);
            for (int y = 0; y < N; y++)
                for (int x = 0; x < N; x++)
                {
                    float dx = (x + 0.5f) / N * 2f - 1f, dy = (y + 0.5f) / N * 2f - 1f;
                    float a = Mathf.Clamp01(1f - Mathf.Sqrt(dx * dx + dy * dy));
                    t.SetPixel(x, y, new Color(1f, 1f, 1f, a * a));
                }
            File.WriteAllBytes(path, t.EncodeToPNG());
            AssetDatabase.ImportAsset(path);
            var ti = (TextureImporter)AssetImporter.GetAtPath(path);
            ti.alphaIsTransparency = true; ti.wrapMode = TextureWrapMode.Clamp; ti.mipmapEnabled = false;
            ti.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(path);
        }
    }
}
