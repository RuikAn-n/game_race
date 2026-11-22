// 《入谱》导入规则：只在资产"第一次导入"时套默认值，之后美术在 Inspector 里改的设置不会被覆盖。
// 规则来源：Docs/asset_spec.md（B 执行手册 §3）
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
