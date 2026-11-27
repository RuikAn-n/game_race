// 《入谱》导入规则：只在资产"第一次导入"时套默认值，之后美术在 Inspector 里改的设置不会被覆盖。
// 规则来源：Docs/asset_spec.md（B 执行手册 §3）
using System.Collections.Generic;
using System.Text.RegularExpressions;
using UnityEditor;
using UnityEngine;

namespace Rupu.EditorTools
{
    public class RupuArtImporter : AssetPostprocessor
    {
        static bool IsArt(string p) => p.StartsWith("Assets/Art/");
        static bool IsHumanoid(string p) =>
            p.StartsWith("Assets/Art/Characters/") || p.StartsWith("Assets/Art/Enemies/") ||
            p.StartsWith("Assets/Art/Bosses/");   // 赤焰/鬼倭都是人形：复用人形动画，特殊招式再单做

        void OnPreprocessModel()
        {
            if (!IsArt(assetPath) || !assetImporter.importSettingsMissing) return;
            var mi = (ModelImporter)assetImporter;
            mi.globalScale = 1f;
            mi.useFileScale = true;
            mi.isReadable = false;
            mi.meshCompression = ModelImporterMeshCompression.Off;
            mi.addCollider = false;
            mi.materialImportMode = ModelImporterMaterialImportMode.ImportViaMaterialDescription;

            if (IsHumanoid(assetPath))
            {
                // Mixamo / 标准人形骨架 -> Humanoid，动画可在 NPC 与敌人之间复用
                mi.animationType = ModelImporterAnimationType.Human;
                mi.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
            }
            else
            {
                mi.animationType = ModelImporterAnimationType.None;
                mi.importAnimation = false;
            }
        }

        // ------------------------------------------------------------ LOD（Docs/act2_city_lod.md）
        // rupu_pipeline.py 导出 BLD_MING_* 时自动带 LOD：<原名>_LOD0，其下子物体 NOCOL_<原名>_LOD1 / _LOD2。
        // 这里每次导入都（重新）建一个 LODGroup 放在模型根上，并把 _LOD0 后缀去掉，让物体名和没有 LOD 时一样
        // （脚本按名字找门扇、屋顶等不受影响）。不在任何一级里的网格（小件、NOCOL_ 旗面、COL_）始终显示。
        static readonly Regex LodRx = new Regex(@"_LOD(\d+)$", RegexOptions.IgnoreCase);
        // 各级切换的屏占比（物体高度 / 屏幕高度）。最后一级 0 = 永不剔除（俯视指挥要看到全城）。
        public static readonly float[] LodScreenHeights = { 0.30f, 0.10f, 0f };

        void OnPostprocessModel(GameObject root)
        {
            if (!IsArt(assetPath)) return;
            var levels = new SortedDictionary<int, List<Renderer>>();
            void Add(int lv, Renderer r)
            {
                if (!levels.TryGetValue(lv, out var list)) levels[lv] = list = new List<Renderer>();
                if (!list.Contains(r)) list.Add(r);
            }
            foreach (var r in root.GetComponentsInChildren<Renderer>(true))
            {
                var m = LodRx.Match(r.gameObject.name);
                if (!m.Success) continue;
                int lv = int.Parse(m.Groups[1].Value);
                Add(lv, r);
                // LOD1+ 挂在 LOD0 下面；FBX 只有一个根时团结会把根节点并进模型根并改成文件名，所以按父物体认 LOD0
                if (lv > 0 && r.transform.parent != null)
                {
                    var pr = r.transform.parent.GetComponent<Renderer>();
                    if (pr != null && !LodRx.IsMatch(pr.gameObject.name)) Add(0, pr);
                }
            }
            if (!levels.ContainsKey(0) || levels.Count < 2) return;

            foreach (var g in root.GetComponentsInChildren<LODGroup>(true)) UnityEngine.Object.DestroyImmediate(g);
            foreach (var r in levels[0])
                if (r.gameObject != root) r.gameObject.name = LodRx.Replace(r.gameObject.name, "");

            var lods = new List<LOD>();
            int i = 0;
            foreach (var kv in levels)
            {
                int n = LodScreenHeights.Length;
                float h = i == levels.Count - 1 ? 0f
                        : i < n - 1 ? LodScreenHeights[i]
                        : LodScreenHeights[n - 2] * Mathf.Pow(0.5f, i - n + 2);   // 超过 3 级时逐级减半
                lods.Add(new LOD(h, kv.Value.ToArray()));
                i++;
            }
            var group = root.AddComponent<LODGroup>();
            group.fadeMode = LODFadeMode.None;
            group.SetLODs(lods.ToArray());
            group.RecalculateBounds();
        }

        void OnPreprocessAnimation()
        {
            if (!IsArt(assetPath) || !assetImporter.importSettingsMissing) return;
            var mi = (ModelImporter)assetImporter;
            var clips = mi.defaultClipAnimations;
            if (clips == null || clips.Length == 0) return;
            foreach (var c in clips)
            {
                string n = (c.name + " " + assetPath).ToLowerInvariant();
                if (n.Contains("idle") || n.Contains("walk") || n.Contains("run") || n.Contains("loop"))
                    c.loopTime = true;
                // 根运动全部烘进姿势（Original）：跪下/坐倒的髋高变化作用在身体上，动作不漂移、不自转。
                // 角色位移一律由脚本移动 transform，不用根运动。
                c.lockRootHeightY = true; c.keepOriginalPositionY = true;
                c.lockRootRotation = true; c.keepOriginalOrientation = true;
                c.lockRootPositionXZ = true; c.keepOriginalPositionXZ = true;
            }
            mi.clipAnimations = clips;
        }

        void OnPreprocessTexture()
        {
            if (!IsArt(assetPath) || !assetImporter.importSettingsMissing) return;
            var ti = (TextureImporter)assetImporter;
            string lower = assetPath.ToLowerInvariant();
            if (lower.Contains("/ui/") || lower.Contains("/endingcards/") || lower.Contains("/cutscenes/"))
            {
                ti.textureType = TextureImporterType.Sprite;
                ti.mipmapEnabled = false;
                ti.maxTextureSize = 4096;
            }
            else if (lower.Contains("_n.") || lower.Contains("_normal"))
            {
                ti.textureType = TextureImporterType.NormalMap;
                ti.maxTextureSize = 2048;
            }
            else
            {
                ti.textureType = TextureImporterType.Default;
                ti.sRGBTexture = !(lower.Contains("_mask") || lower.Contains("_orm") || lower.Contains("_rough"));
                ti.mipmapEnabled = true;
                ti.maxTextureSize = 2048;
            }
            ti.textureCompression = TextureImporterCompression.Compressed;
        }

        void OnPreprocessAudio()
        {
            if (!assetPath.StartsWith("Assets/Audio/") || !assetImporter.importSettingsMissing) return;
            var ai = (AudioImporter)assetImporter;
            var s = ai.defaultSampleSettings;
            if (assetPath.StartsWith("Assets/Audio/BGM/"))
            {
                s.loadType = AudioClipLoadType.Streaming;
                s.compressionFormat = AudioCompressionFormat.Vorbis;
                s.quality = 0.7f;
            }
            else
            {
                s.loadType = AudioClipLoadType.DecompressOnLoad;
                ai.forceToMono = assetPath.StartsWith("Assets/Audio/VO/");
            }
            ai.defaultSampleSettings = s;
        }
    }
}
