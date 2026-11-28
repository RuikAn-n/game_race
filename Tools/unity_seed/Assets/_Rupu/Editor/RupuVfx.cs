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
//
// 第二至五幕（BuildActs()，同一菜单/命令一起生成）。「一次性」的 loop=false、不自动播放，脚本里 ps.Play()：
//   第二幕 筑堡：PF_VFX_SandPuff 沙盘扬沙(一次) PF_VFX_WallRise 墙线隆起尘浪(一次，沿本地 X 8m)
//               PF_VFX_StoneSparks 凿石火星(一次) PF_VFX_MortarSplash 灰浆溅(一次) PF_VFX_RamDust 夯土尘(一次)
//               PF_VFX_InkBloom 墨迹晕开(一次) PF_VFX_PaperPages 纸页翻飞(循环) PF_VFX_StampPuff 盖印朱红(一次)
//               PF_VFX_WaterFlow 水门水流(循环，沿本地 +Z 流) PF_VFX_Chimney 炊烟(循环)
//   第三幕 守城：PF_VFX_Blood 血(一次) PF_VFX_Splinters 破片/门板碎裂(一次) PF_VFX_WaterSplash 泼水灭火(一次)
//               PF_VFX_FirePotBurst 火罐炸开(一次) PF_VFX_FireSpread 火势蔓延(循环，本地 4×4m 区域，改 shape 可放大)
//               PF_VFX_BattleSmoke 战场灰烟(循环) PF_VFX_ArrowTrail 箭矢尾迹(TrailRenderer，挂在箭上)
//   第四幕 寻谱：PF_VFX_Dust 废墟浮尘(循环) PF_VFX_Snow 1941 冬落雪(循环，挂相机)
//   第三幕补充 12 个 PF_VFX_A3_*：见下面 BuildAct3()
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

        [MenuItem("入谱/特效/生成全部特效", priority = 70)]
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
            BuildActs(soft, alpha, add);
            AssetDatabase.SaveAssets();
            Debug.Log("[VFX] 特效已生成：" + Dir);
        }


        // ------------------------------------------------------------ 第二至五幕
        static void BuildActs(Texture2D soft, Material alpha, Material add)
        {
            // ---- 第二幕 筑堡
            Save("PF_VFX_SandPuff", go =>
            {
                var ps = PS(go, alpha, 1.6f, 0.9f, 0.18f, 120, new Color(0.72f, 0.64f, 0.5f, 0.6f), ParticleSystemSimulationSpace.World);
                Burst(ps, 60); Gravity(ps, 0.25f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Hemisphere; sh.radius = 0.25f;
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                Grow(ps, 1f, 2.5f); Fade(ps, new Color(0.72f, 0.64f, 0.5f), 0.6f);
            });
            Save("PF_VFX_WallRise", go =>
            {
                var ps = PS(go, alpha, 2.2f, 1.6f, 0.8f, 300, new Color(0.6f, 0.55f, 0.46f, 0.55f), ParticleSystemSimulationSpace.World);
                Burst(ps, 160); Gravity(ps, 0.1f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(8f, 0.3f, 0.6f);
                var v = ps.velocityOverLifetime; v.enabled = true; v.space = ParticleSystemSimulationSpace.Local;
                v.x = new ParticleSystem.MinMaxCurve(-0.4f, 0.4f); v.y = new ParticleSystem.MinMaxCurve(1.2f, 2.4f); v.z = new ParticleSystem.MinMaxCurve(-0.8f, 0.8f);
                var main = ps.main; main.startSpeed = 0f;
                Grow(ps, 1f, 3f); Fade(ps, new Color(0.6f, 0.55f, 0.46f), 0.55f);
            });
            Save("PF_VFX_StoneSparks", go =>
            {
                var ps = PS(go, add, 0.35f, 4f, 0.03f, 60, new Color(1f, 0.75f, 0.35f, 1f), ParticleSystemSimulationSpace.World);
                Burst(ps, 24); Gravity(ps, 1.2f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 45f; sh.radius = 0.02f;
                Stretch(go, 0.04f);
                Fade(ps, new Color(1f, 0.7f, 0.3f), 1f);
                var chips = Child(go, "Chips");
                var cps = PS(chips, alpha, 0.8f, 2.2f, 0.04f, 30, new Color(0.62f, 0.6f, 0.56f, 1f), ParticleSystemSimulationSpace.World);
                Burst(cps, 10); Gravity(cps, 1.5f);
                var csh = cps.shape; csh.shapeType = ParticleSystemShapeType.Cone; csh.angle = 35f; csh.radius = 0.02f;
            });
            Save("PF_VFX_MortarSplash", go =>
            {
                var ps = PS(go, alpha, 0.7f, 2.2f, 0.07f, 60, new Color(0.86f, 0.84f, 0.78f, 1f), ParticleSystemSimulationSpace.World);
                Burst(ps, 30); Gravity(ps, 1.4f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Hemisphere; sh.radius = 0.08f;
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                Collide(ps, 0.6f);
            });
            Save("PF_VFX_RamDust", go =>
            {
                var ps = PS(go, alpha, 1.4f, 1.5f, 0.35f, 80, new Color(0.55f, 0.46f, 0.34f, 0.65f), ParticleSystemSimulationSpace.World);
                Burst(ps, 40); Gravity(ps, 0.05f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Circle; sh.radius = 0.3f; sh.radiusThickness = 0f;
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                var v = ps.velocityOverLifetime; v.enabled = true; v.space = ParticleSystemSimulationSpace.Local;
                v.x = new ParticleSystem.MinMaxCurve(0f); v.y = new ParticleSystem.MinMaxCurve(0f); v.z = new ParticleSystem.MinMaxCurve(0.3f, 0.8f);
                Grow(ps, 1f, 3f); Fade(ps, new Color(0.55f, 0.46f, 0.34f), 0.65f);
            });
            Save("PF_VFX_InkBloom", go =>
            {
                var ps = PS(go, alpha, 1.8f, 0.04f, 0.05f, 20, new Color(0.06f, 0.05f, 0.05f, 0.9f), ParticleSystemSimulationSpace.Local);
                Burst(ps, 8);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Circle; sh.radius = 0.02f;
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                var r = go.GetComponent<ParticleSystemRenderer>(); r.renderMode = ParticleSystemRenderMode.HorizontalBillboard;
                Grow(ps, 0.3f, 3f);
                var c = ps.colorOverLifetime; c.enabled = true;
                var g = new Gradient();
                g.SetKeys(new[] { new GradientColorKey(new Color(0.05f, 0.05f, 0.05f), 0f), new GradientColorKey(new Color(0.12f, 0.11f, 0.1f), 1f) },
                          new[] { new GradientAlphaKey(0.95f, 0f), new GradientAlphaKey(0.85f, 0.7f), new GradientAlphaKey(0f, 1f) });
                c.color = g;
            });
            Save("PF_VFX_PaperPages", go =>
            {
                var ps = PS(go, alpha, 5f, 0.6f, 0.18f, 30, new Color(0.86f, 0.8f, 0.68f, 1f), ParticleSystemSimulationSpace.World);
                Emit(ps, 3); Gravity(ps, 0.02f);
                var main = ps.main; main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(2f, 0.5f, 2f);
                var n = ps.noise; n.enabled = true; n.strength = 0.6f; n.frequency = 0.5f;
                var rot = ps.rotationOverLifetime; rot.enabled = true; rot.z = new ParticleSystem.MinMaxCurve(-3f, 3f);
                Fade(ps, new Color(0.86f, 0.8f, 0.68f), 1f);
            });
            Save("PF_VFX_StampPuff", go =>
            {
                var ps = PS(go, alpha, 0.6f, 0.5f, 0.05f, 30, new Color(0.7f, 0.16f, 0.12f, 0.8f), ParticleSystemSimulationSpace.Local);
                Burst(ps, 16);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Circle; sh.radius = 0.04f; sh.radiusThickness = 0f;
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                var v = ps.velocityOverLifetime; v.enabled = true; v.space = ParticleSystemSimulationSpace.Local;
                v.x = new ParticleSystem.MinMaxCurve(0f); v.y = new ParticleSystem.MinMaxCurve(0f); v.z = new ParticleSystem.MinMaxCurve(0.05f, 0.15f);
                Grow(ps, 1f, 2f); Fade(ps, new Color(0.7f, 0.16f, 0.12f), 0.8f);
            });
            Save("PF_VFX_WaterFlow", go =>
            {
                var ps = PS(go, alpha, 1.6f, 3f, 0.35f, 400, new Color(0.62f, 0.72f, 0.72f, 0.45f), ParticleSystemSimulationSpace.World);
                Emit(ps, 140); Gravity(ps, 0.3f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(3f, 0.2f, 0.1f);
                var v = ps.velocityOverLifetime; v.enabled = true; v.space = ParticleSystemSimulationSpace.Local;
                v.x = new ParticleSystem.MinMaxCurve(0f); v.y = new ParticleSystem.MinMaxCurve(0f); v.z = new ParticleSystem.MinMaxCurve(2.5f, 3.5f);
                var main = ps.main; main.startSpeed = 0f;
                Stretch(go, 0.15f);
                Fade(ps, new Color(0.62f, 0.72f, 0.72f), 0.45f);
                var foam = Child(go, "Foam");
                foam.transform.localPosition = new Vector3(0f, -0.3f, 3.5f);
                var fps = PS(foam, alpha, 1.2f, 0.6f, 0.5f, 120, new Color(0.88f, 0.9f, 0.88f, 0.5f), ParticleSystemSimulationSpace.World);
                Emit(fps, 40);
                var fsh = fps.shape; fsh.shapeType = ParticleSystemShapeType.Box; fsh.scale = new Vector3(3f, 0.1f, 0.6f);
                Grow(fps, 1f, 2f); Fade(fps, new Color(0.88f, 0.9f, 0.88f), 0.5f);
            });
            Save("PF_VFX_Chimney", go =>
            {
                var ps = PS(go, alpha, 7f, 0.5f, 0.4f, 80, new Color(0.7f, 0.7f, 0.68f, 0.35f), ParticleSystemSimulationSpace.World);
                Emit(ps, 6);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 6f; sh.radius = 0.15f;
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                Grow(ps, 1f, 6f); Fade(ps, new Color(0.7f, 0.7f, 0.68f), 0.35f);
                var v = ps.velocityOverLifetime; v.enabled = true; v.space = ParticleSystemSimulationSpace.World;
                v.x = new ParticleSystem.MinMaxCurve(0.3f); v.y = new ParticleSystem.MinMaxCurve(0f); v.z = new ParticleSystem.MinMaxCurve(0.15f);
                var n = ps.noise; n.enabled = true; n.strength = 0.25f; n.frequency = 0.3f;
            });
            // ---- 第三幕 守城
            Save("PF_VFX_Blood", go =>
            {
                var ps = PS(go, alpha, 0.6f, 2.5f, 0.06f, 40, new Color(0.36f, 0.08f, 0.07f, 1f), ParticleSystemSimulationSpace.World);
                Burst(ps, 18); Gravity(ps, 1.6f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 30f; sh.radius = 0.03f;
                Collide(ps, 1f);
            });
            Save("PF_VFX_Splinters", go =>
            {
                var ps = PS(go, alpha, 1.4f, 5f, 0.12f, 60, new Color(0.42f, 0.32f, 0.22f, 1f), ParticleSystemSimulationSpace.World);
                Burst(ps, 36); Gravity(ps, 1.3f);
                var main = ps.main; main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
                main.startSize3D = true;
                main.startSizeX = new ParticleSystem.MinMaxCurve(0.04f, 0.08f); main.startSizeY = new ParticleSystem.MinMaxCurve(0.2f, 0.45f);
                main.startSizeZ = new ParticleSystem.MinMaxCurve(0.04f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(1.5f, 2f, 0.1f);
                var rot = ps.rotationOverLifetime; rot.enabled = true; rot.z = new ParticleSystem.MinMaxCurve(-8f, 8f);
                Collide(ps, 0.4f);
                var dust = Child(go, "Dust");
                var dps = PS(dust, alpha, 1.5f, 1.2f, 0.6f, 40, new Color(0.5f, 0.45f, 0.38f, 0.5f), ParticleSystemSimulationSpace.World);
                Burst(dps, 20);
                var dsh = dps.shape; dsh.shapeType = ParticleSystemShapeType.Box; dsh.scale = new Vector3(1.5f, 2f, 0.2f);
                Grow(dps, 1f, 3f); Fade(dps, new Color(0.5f, 0.45f, 0.38f), 0.5f);
            });
            Save("PF_VFX_WaterSplash", go =>
            {
                var ps = PS(go, alpha, 0.8f, 4f, 0.12f, 120, new Color(0.7f, 0.8f, 0.8f, 0.7f), ParticleSystemSimulationSpace.World);
                Burst(ps, 70); Gravity(ps, 1.3f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 18f; sh.radius = 0.15f;
                Stretch(go, 0.08f);
                var steam = Child(go, "Steam");
                steam.transform.localPosition = new Vector3(0f, 0f, 2.5f);
                var sps = PS(steam, alpha, 2.5f, 1f, 0.8f, 40, new Color(0.88f, 0.88f, 0.86f, 0.45f), ParticleSystemSimulationSpace.World);
                Burst(sps, 18);
                var ssh = sps.shape; ssh.shapeType = ParticleSystemShapeType.Sphere; ssh.radius = 0.6f;
                Grow(sps, 1f, 3f); Fade(sps, new Color(0.88f, 0.88f, 0.86f), 0.45f);
            });
            Save("PF_VFX_FirePotBurst", go =>
            {
                var ps = PS(go, add, 0.5f, 4f, 0.9f, 80, new Color(1f, 0.55f, 0.15f, 1f), ParticleSystemSimulationSpace.World);
                Burst(ps, 50);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Sphere; sh.radius = 0.2f;
                Grow(ps, 1f, 2f); Fade(ps, new Color(1f, 0.5f, 0.15f), 1f);
                var smoke = Child(go, "Smoke");
                var sps = PS(smoke, alpha, 2.5f, 1.2f, 1.2f, 40, new Color(0.12f, 0.11f, 0.1f, 0.6f), ParticleSystemSimulationSpace.World);
                Burst(sps, 18);
                var ssh = sps.shape; ssh.shapeType = ParticleSystemShapeType.Sphere; ssh.radius = 0.5f;
                Grow(sps, 1f, 3f); Fade(sps, new Color(0.12f, 0.11f, 0.1f), 0.6f);
                var oil = Child(go, "Oil");
                var ops = PS(oil, add, 1.0f, 3f, 0.12f, 40, new Color(1f, 0.62f, 0.2f, 1f), ParticleSystemSimulationSpace.World);
                Burst(ops, 24); Gravity(ops, 1.2f);
                var osh = ops.shape; osh.shapeType = ParticleSystemShapeType.Hemisphere; osh.radius = 0.2f;
                oil.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                Collide(ops, 0.3f);
                AddLight(go, new Color(1f, 0.55f, 0.2f), 8f, 3f, Vector3.zero);
            });
            Save("PF_VFX_FireSpread", go =>
            {
                var ps = PS(go, add, 0.9f, 1.2f, 0.7f, 300, new Color(1f, 0.55f, 0.15f, 0.85f), ParticleSystemSimulationSpace.World);
                Emit(ps, 90);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(4f, 4f, 0.2f);
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                Grow(ps, 1f, 0.2f); Fade(ps, new Color(1f, 0.5f, 0.15f), 0.9f);
                var n = ps.noise; n.enabled = true; n.strength = 0.5f; n.frequency = 1.2f;
                var smoke = Child(go, "Smoke");
                smoke.transform.localPosition = new Vector3(0f, 0f, 1f);
                var sps = PS(smoke, alpha, 5f, 1.4f, 1.4f, 100, new Color(0.12f, 0.11f, 0.1f, 0.5f), ParticleSystemSimulationSpace.World);
                Emit(sps, 12);
                var ssh = sps.shape; ssh.shapeType = ParticleSystemShapeType.Box; ssh.scale = new Vector3(4f, 4f, 0.2f);
                Grow(sps, 1f, 3.5f); Fade(sps, new Color(0.12f, 0.11f, 0.1f), 0.5f);
                AddLight(go, new Color(1f, 0.5f, 0.2f), 10f, 2.4f, new Vector3(0f, 0f, 1f));
            });
            Save("PF_VFX_BattleSmoke", go =>
            {
                var ps = PS(go, alpha, 10f, 0.6f, 3f, 60, new Color(0.42f, 0.41f, 0.39f, 0.35f), ParticleSystemSimulationSpace.World);
                Emit(ps, 4);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(10f, 1f, 10f);
                Grow(ps, 1f, 2.5f); Fade(ps, new Color(0.42f, 0.41f, 0.39f), 0.35f);
                var n = ps.noise; n.enabled = true; n.strength = 0.3f; n.frequency = 0.15f;
            });
            Save("PF_VFX_ArrowTrail", go =>
            {
                var tr = go.AddComponent<TrailRenderer>();
                tr.time = 0.25f; tr.minVertexDistance = 0.2f;
                tr.widthCurve = new AnimationCurve(new Keyframe(0f, 0.04f), new Keyframe(1f, 0f));
                var g = new Gradient();
                g.SetKeys(new[] { new GradientColorKey(new Color(0.9f, 0.88f, 0.82f), 0f), new GradientColorKey(new Color(0.9f, 0.88f, 0.82f), 1f) },
                          new[] { new GradientAlphaKey(0.5f, 0f), new GradientAlphaKey(0f, 1f) });
                tr.colorGradient = g; tr.sharedMaterial = alpha; tr.shadowCastingMode = ShadowCastingMode.Off;
            });
            // ---- 第四幕 寻谱（1941 冬）
            Save("PF_VFX_Dust", go =>
            {
                var ps = PS(go, alpha, 9f, 0.05f, 0.04f, 150, new Color(0.85f, 0.8f, 0.7f, 0.35f), ParticleSystemSimulationSpace.World);
                Emit(ps, 14);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(10f, 4f, 10f);
                go.transform.localPosition = new Vector3(0f, 2f, 0f);
                var n = ps.noise; n.enabled = true; n.strength = 0.08f; n.frequency = 0.3f;
                Fade(ps, new Color(0.85f, 0.8f, 0.7f), 0.35f);
            });
            Save("PF_VFX_Snow", go =>
            {
                var ps = PS(go, alpha, 6f, 0f, 0.05f, 2500, new Color(0.92f, 0.92f, 0.9f, 0.8f), ParticleSystemSimulationSpace.World);
                Emit(ps, 380);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(36f, 0.5f, 36f);
                go.transform.localPosition = new Vector3(0f, 12f, 6f);
                var v = ps.velocityOverLifetime; v.enabled = true; v.space = ParticleSystemSimulationSpace.World;
                v.x = new ParticleSystem.MinMaxCurve(-0.4f, 0.2f); v.y = new ParticleSystem.MinMaxCurve(-2.2f, -1.6f); v.z = new ParticleSystem.MinMaxCurve(0.1f);
                var n = ps.noise; n.enabled = true; n.strength = 0.3f; n.frequency = 0.4f;
                var col = ps.collision; col.enabled = true; col.type = ParticleSystemCollisionType.World;
                col.mode = ParticleSystemCollisionMode.Collision3D; col.quality = ParticleSystemCollisionQuality.Low;
                col.lifetimeLoss = 1f; col.bounce = 0f; col.maxCollisionShapes = 64;
            });
            BuildAct3(alpha, add);
        }

        // ------------------------------------------------------------ 第三幕补充（Docs/第三幕_建模清单.md §8.1，Docs/act3_assets.md）
        //   PF_VFX_A3_ArrowVolley 12 支箭齐射(一次，沿本地 +Z 抛物线)  PF_VFX_A3_RockFall 落石 + 尘(一次，向下)
        //   PF_VFX_A3_OilPour 油流(循环，向下) + 子物体 FireLine 火线(循环，沿本地 X 3m，脚本按需打开)
        //   PF_VFX_A3_WaterBurst 开闸水柱(循环，沿本地 +Z)  PF_VFX_A3_Steam 蒸汽(循环)  PF_VFX_A3_GateSplinter 门板碎裂(一次，大块)
        //   PF_VFX_A3_WallCollapse 缺口塌落：石块 + 大尘(一次，8m 宽)  PF_VFX_A3_InkLine 墨迹逐行出现(一次，沿本地 -Y 一行)
        //   PF_VFX_A3_RainSplash 雨打石面/水面溅点(循环，10×10m)  PF_VFX_A3_CrowdDust 百姓跑动扬尘(循环，挂在人群中心)
        //   PF_VFX_A3_FlagRip 旗面撕裂碎布(一次)  PF_VFX_A3_BloodMist 暗色点状血雾(一次，不血腥)
        static void BuildAct3(Material alpha, Material add)
        {
            Save("PF_VFX_A3_ArrowVolley", go =>
            {
                var ps = PS(go, alpha, 1.6f, 22f, 0.05f, 24, new Color(0.3f, 0.25f, 0.2f, 1f), ParticleSystemSimulationSpace.World);
                Burst(ps, 12); Gravity(ps, 1.0f);
                var main = ps.main; main.startSpeed = new ParticleSystem.MinMaxCurve(19f, 24f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(6f, 0.5f, 0.5f);
                go.transform.localRotation = Quaternion.Euler(-25f, 0f, 0f);
                var r = go.GetComponent<ParticleSystemRenderer>();
                r.renderMode = ParticleSystemRenderMode.Stretch; r.velocityScale = 0.04f; r.lengthScale = 6f;
                Collide(ps, 1f);
                var tr = ps.trails; tr.enabled = true; tr.lifetime = 0.15f; tr.widthOverTrail = new ParticleSystem.MinMaxCurve(0.4f);
                tr.colorOverLifetime = new ParticleSystem.MinMaxGradient(new Color(0.9f, 0.88f, 0.82f, 0.35f));
                go.GetComponent<ParticleSystemRenderer>().trailMaterial = alpha;
            });
            Save("PF_VFX_A3_RockFall", go =>
            {
                var ps = PS(go, alpha, 2f, 1f, 0.3f, 20, new Color(0.45f, 0.44f, 0.4f, 1f), ParticleSystemSimulationSpace.World);
                Burst(ps, 8); Gravity(ps, 2f);
                var main = ps.main; main.startSize = new ParticleSystem.MinMaxCurve(0.2f, 0.4f);
                main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(1.2f, 0.6f, 0.4f);
                var rot = ps.rotationOverLifetime; rot.enabled = true; rot.z = new ParticleSystem.MinMaxCurve(-5f, 5f);
                Collide(ps, 0.3f);
                var dust = Child(go, "Dust");
                dust.transform.localPosition = new Vector3(0f, -6f, 0f);
                var dps = PS(dust, alpha, 2.5f, 1.5f, 1.2f, 40, new Color(0.55f, 0.5f, 0.42f, 0.5f), ParticleSystemSimulationSpace.World);
                Burst(dps, 24);
                var main2 = dps.main; main2.startDelay = 0.9f;
                var dsh = dps.shape; dsh.shapeType = ParticleSystemShapeType.Sphere; dsh.radius = 1f;
                Grow(dps, 1f, 3f); Fade(dps, new Color(0.55f, 0.5f, 0.42f), 0.5f);
            });
            Save("PF_VFX_A3_OilPour", go =>
            {
                var ps = PS(go, alpha, 0.8f, 0.5f, 0.06f, 80, new Color(0.12f, 0.1f, 0.06f, 0.9f), ParticleSystemSimulationSpace.World);
                Emit(ps, 60); Gravity(ps, 1.5f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 3f; sh.radius = 0.03f;
                go.transform.localRotation = Quaternion.Euler(90f, 0f, 0f);
                Stretch(go, 0.1f); Collide(ps, 1f);
                var fl = Child(go, "FireLine");
                fl.transform.localRotation = Quaternion.Euler(-180f, 0f, 0f);
                var fps = PS(fl, add, 0.8f, 1f, 0.4f, 160, new Color(1f, 0.55f, 0.15f, 0.85f), ParticleSystemSimulationSpace.World);
                Emit(fps, 60);
                var fsh = fps.shape; fsh.shapeType = ParticleSystemShapeType.Box; fsh.scale = new Vector3(3f, 0.3f, 0.1f);
                Grow(fps, 1f, 0.2f); Fade(fps, new Color(1f, 0.5f, 0.15f), 0.9f);
                var fmain = fps.main; fmain.playOnAwake = false;
            });
            Save("PF_VFX_A3_WaterBurst", go =>
            {
                var ps = PS(go, alpha, 1.2f, 7f, 0.35f, 400, new Color(0.62f, 0.72f, 0.72f, 0.6f), ParticleSystemSimulationSpace.World);
                Emit(ps, 220); Gravity(ps, 0.8f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(4f, 1.2f, 0.2f);
                Grow(ps, 1f, 2.5f); Fade(ps, new Color(0.7f, 0.8f, 0.8f), 0.6f);
                Stretch(go, 0.05f);
                var foam = Child(go, "Foam");
                foam.transform.localPosition = new Vector3(0f, -0.8f, 3f);
                var fps = PS(foam, alpha, 1.5f, 1.5f, 0.6f, 120, new Color(0.88f, 0.9f, 0.9f, 0.5f), ParticleSystemSimulationSpace.World);
                Emit(fps, 40);
                var fsh = fps.shape; fsh.shapeType = ParticleSystemShapeType.Box; fsh.scale = new Vector3(4f, 0.2f, 1.5f);
                Fade(fps, new Color(0.9f, 0.92f, 0.92f), 0.5f);
            });
            Save("PF_VFX_A3_Steam", go =>
            {
                var ps = PS(go, alpha, 3f, 1.2f, 0.6f, 80, new Color(0.9f, 0.9f, 0.88f, 0.45f), ParticleSystemSimulationSpace.World);
                Emit(ps, 14);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Cone; sh.angle = 18f; sh.radius = 0.4f;
                go.transform.localRotation = Quaternion.Euler(-90f, 0f, 0f);
                Grow(ps, 1f, 4f); Fade(ps, new Color(0.9f, 0.9f, 0.88f), 0.45f);
                var n = ps.noise; n.enabled = true; n.strength = 0.4f; n.frequency = 0.5f;
            });
            Save("PF_VFX_A3_GateSplinter", go =>
            {
                var ps = PS(go, alpha, 1.8f, 6f, 0.2f, 40, new Color(0.38f, 0.28f, 0.2f, 1f), ParticleSystemSimulationSpace.World);
                Burst(ps, 20); Gravity(ps, 1.4f);
                var main = ps.main; main.startSize3D = true;
                main.startSizeX = new ParticleSystem.MinMaxCurve(0.08f, 0.16f); main.startSizeY = new ParticleSystem.MinMaxCurve(0.5f, 1.1f);
                main.startSizeZ = new ParticleSystem.MinMaxCurve(0.05f);
                main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(4f, 4f, 0.2f);
                var rot = ps.rotationOverLifetime; rot.enabled = true; rot.z = new ParticleSystem.MinMaxCurve(-6f, 6f);
                Collide(ps, 0.2f);
            });
            Save("PF_VFX_A3_WallCollapse", go =>
            {
                var ps = PS(go, alpha, 2.5f, 2f, 0.5f, 60, new Color(0.5f, 0.5f, 0.46f, 1f), ParticleSystemSimulationSpace.World);
                Burst(ps, 30); Gravity(ps, 1.6f);
                var main = ps.main; main.startSize = new ParticleSystem.MinMaxCurve(0.25f, 0.7f);
                main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(8f, 3f, 1f);
                go.transform.localPosition = new Vector3(0f, 5f, 0f);
                Collide(ps, 0.2f);
                var dust = Child(go, "Dust");
                dust.transform.localPosition = new Vector3(0f, -4f, 0f);
                var dps = PS(dust, alpha, 5f, 2f, 3f, 80, new Color(0.6f, 0.56f, 0.48f, 0.55f), ParticleSystemSimulationSpace.World);
                Burst(dps, 40);
                var dsh = dps.shape; dsh.shapeType = ParticleSystemShapeType.Box; dsh.scale = new Vector3(9f, 2f, 3f);
                Grow(dps, 1f, 3f); Fade(dps, new Color(0.6f, 0.56f, 0.48f), 0.55f);
            });
            Save("PF_VFX_A3_InkLine", go =>
            {
                var ps = PS(go, alpha, 4f, 0f, 0.012f, 200, new Color(0.08f, 0.07f, 0.06f, 0.95f), ParticleSystemSimulationSpace.Local);
                var main = ps.main; main.loop = false; main.playOnAwake = false; main.duration = 1.6f;
                var e = ps.emission; e.enabled = true; e.rateOverTime = 90f;
                // 一条 0.24 m 的边，发射点沿边匀速扫过一次（1.6 s）＝墨迹从右往左一笔写出；粒子停留 4 s
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.SingleSidedEdge; sh.radius = 0.12f;
                sh.radiusMode = ParticleSystemShapeMultiModeValue.Loop; sh.radiusSpeed = 0.625f;
                main.startSpeed = 0f;
                Grow(ps, 0.6f, 1.2f);
            });
            Save("PF_VFX_A3_RainSplash", go =>
            {
                var ps = PS(go, alpha, 0.25f, 0.8f, 0.06f, 600, new Color(0.8f, 0.84f, 0.86f, 0.5f), ParticleSystemSimulationSpace.World);
                Emit(ps, 400); Gravity(ps, 0.6f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(10f, 0.05f, 10f);
                var main = ps.main; main.startSpeed = new ParticleSystem.MinMaxCurve(0.4f, 1.2f);
                Grow(ps, 0.5f, 1.6f); Fade(ps, new Color(0.85f, 0.88f, 0.9f), 0.5f);
            });
            Save("PF_VFX_A3_CrowdDust", go =>
            {
                var ps = PS(go, alpha, 2.5f, 0.4f, 0.8f, 80, new Color(0.62f, 0.56f, 0.46f, 0.3f), ParticleSystemSimulationSpace.World);
                Emit(ps, 12);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(6f, 0.2f, 6f);
                Grow(ps, 1f, 2.2f); Fade(ps, new Color(0.62f, 0.56f, 0.46f), 0.3f);
            });
            Save("PF_VFX_A3_FlagRip", go =>
            {
                var ps = PS(go, alpha, 3f, 2f, 0.15f, 30, new Color(0.6f, 0.22f, 0.17f, 1f), ParticleSystemSimulationSpace.World);
                Burst(ps, 14); Gravity(ps, 0.15f);
                var main = ps.main; main.startRotation = new ParticleSystem.MinMaxCurve(0f, Mathf.PI * 2f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Box; sh.scale = new Vector3(0.9f, 0.7f, 0.05f);
                var n = ps.noise; n.enabled = true; n.strength = 0.8f; n.frequency = 0.6f;
                var rot = ps.rotationOverLifetime; rot.enabled = true; rot.z = new ParticleSystem.MinMaxCurve(-3f, 3f);
                Fade(ps, new Color(0.6f, 0.22f, 0.17f), 1f);
            });
            Save("PF_VFX_A3_BloodMist", go =>
            {
                var ps = PS(go, alpha, 0.5f, 1.2f, 0.05f, 30, new Color(0.26f, 0.1f, 0.09f, 0.8f), ParticleSystemSimulationSpace.World);
                Burst(ps, 12); Gravity(ps, 0.3f);
                var sh = ps.shape; sh.shapeType = ParticleSystemShapeType.Sphere; sh.radius = 0.08f;
                Grow(ps, 1f, 2f); Fade(ps, new Color(0.26f, 0.1f, 0.09f), 0.8f);
            });
        }

        /// <summary>一次性爆发：不循环、不预热、不自动播放，脚本里调用 Play()。</summary>
        static void Burst(ParticleSystem ps, int count)
        {
            var main = ps.main; main.loop = false; main.prewarm = false; main.playOnAwake = false;
            main.duration = 0.2f;
            var e = ps.emission; e.enabled = true; e.rateOverTime = 0f;
            e.SetBursts(new[] { new ParticleSystem.Burst(0f, (short)count) });
        }

        static void Gravity(ParticleSystem ps, float g)
        {
            var main = ps.main; main.gravityModifier = g;
        }

        static void Stretch(GameObject go, float velocityScale)
        {
            var r = go.GetComponent<ParticleSystemRenderer>();
            r.renderMode = ParticleSystemRenderMode.Stretch; r.velocityScale = velocityScale; r.lengthScale = 1f;
        }

        static void Collide(ParticleSystem ps, float lifetimeLoss)
        {
            var col = ps.collision; col.enabled = true; col.type = ParticleSystemCollisionType.World;
            col.mode = ParticleSystemCollisionMode.Collision3D; col.quality = ParticleSystemCollisionQuality.Low;
            col.bounce = 0.05f; col.dampen = 0.8f; col.lifetimeLoss = lifetimeLoss; col.maxCollisionShapes = 32;
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
