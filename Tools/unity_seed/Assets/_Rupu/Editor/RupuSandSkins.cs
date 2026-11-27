// 《入谱》第二幕沙盘皮肤：同一个沙盘 prefab 三套皮肤（策划案 §4.4）。1560 = 导入的原材质；本脚本从导入后的 M_A2_* 材质复制出
//   1941（偏灰、低饱和、叠积灰遮罩）和 1945（在 1941 基础上更暗，蒙布 Cover_1945 也随之变旧）两套 .mat。
//   菜单：入谱 / 第二幕 / 生成沙盘皮肤（1941 · 1945）
//   命令行：-executeMethod Rupu.EditorTools.RupuSandSkins.BuildCLI
//   输入：ENV_SandTable.fbx、PROP_Sand_*.fbx 里内嵌（或已 Remap 出去）的 M_A2_* 材质；
//         Assets/Art/Environments/ENV_SandTable/T_SandTable_Dust_Mask.png（Blender 生成，RGB = A = 积灰量，可平铺）
//   输出：Assets/Art/Environments/ENV_SandTable/Skins/<材质名>_1941.mat、<材质名>_1945.mat（可重复执行，已有的就地更新）
//   用法（A）：切皮肤时遍历沙盘下所有 Renderer，把 sharedMaterials 里名为 X 的换成 Skins/X_1941（或 _1945）；
//             1941 另外隐藏 Rim_Corner_FL、显示 Rim_Broken_FL_1941 / SandSpill_1941；1945 显示 Cover_1945。
//   积灰用 URP Lit 自带的 Detail：_DetailMask（读 A 通道）+ _DetailAlbedoMap（同一张图），_DETAIL_SCALED，
//   积灰处提亮、干净处略暗；不需要自定义着色器。
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace Rupu.EditorTools
{
    public static class RupuSandSkins
    {
        public const string Dir = "Assets/Art/Environments/ENV_SandTable/Skins";
        public const string MaskPath = "Assets/Art/Environments/ENV_SandTable/T_SandTable_Dust_Mask.png";

        static readonly string[] Sources =
        {
            "Assets/Art/Environments/ENV_SandTable/ENV_SandTable.fbx",
            "Assets/Art/Props/PROP_Sand_Wall/PROP_Sand_Wall.fbx",
            "Assets/Art/Props/PROP_Sand_Gate/PROP_Sand_Gate.fbx",
            "Assets/Art/Props/PROP_Sand_Tower/PROP_Sand_Tower.fbx",
            "Assets/Art/Props/PROP_Sand_House/PROP_Sand_House.fbx",
            "Assets/Art/Props/PROP_Sand_Flags/PROP_Sand_Flags.fbx",
        };

        static readonly Color Dust1941 = new Color(0.68f, 0.66f, 0.61f);   // 灰土色（gamma 空间）

        [MenuItem("入谱/第二幕/生成沙盘皮肤（1941 · 1945）", priority = 80)]
        public static void BuildMenu() => Build();

        public static void BuildCLI()
        {
            try { Build(); EditorApplication.Exit(0); }
            catch (Exception e) { Debug.LogException(e); EditorApplication.Exit(1); }
        }

        public static void Build()
        {
            Directory.CreateDirectory(Dir);
            AssetDatabase.Refresh();
            var mask = PrepareMask();
            var lit = Shader.Find("Universal Render Pipeline/Lit");
            var src = CollectSourceMaterials();
            if (src.Count == 0)
                throw new Exception("[RupuSandSkins] 没找到 M_A2_* 材质：先把 ENV_SandTable / PROP_Sand_* 的 FBX 导入工程");
            int n = 0;
            foreach (var kv in src)
            {
                Make(kv.Value, kv.Key, 1941, lit, mask);
                Make(kv.Value, kv.Key, 1945, lit, mask);
                n += 2;
            }
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
            Debug.Log($"[RupuSandSkins] 已生成/更新 {n} 个材质（{src.Count} 个源材质 × 1941/1945）→ {Dir}；积灰遮罩：{(mask != null ? MaskPath : "缺失，只调了颜色")}");
        }

        /// <summary>材质名 → 源材质（FBX 内嵌子资产，或 Remap 到外部的 .mat）。只收 M_A2_ 开头的。</summary>
        public static Dictionary<string, Material> CollectSourceMaterials()
        {
            var map = new Dictionary<string, Material>();
            foreach (var p in Sources)
            {
                if (AssetDatabase.LoadMainAssetAtPath(p) == null)
                {
                    Debug.LogWarning($"[RupuSandSkins] 缺少 {p}，跳过");
                    continue;
                }
                var mats = new List<Material>();
                mats.AddRange(AssetDatabase.LoadAllAssetsAtPath(p).OfType<Material>());
                if (AssetImporter.GetAtPath(p) is ModelImporter mi)
                    mats.AddRange(mi.GetExternalObjectMap().Values.OfType<Material>());
                foreach (var m in mats)
                {
                    if (m == null) continue;
                    var name = CleanName(m.name);
                    if (!name.StartsWith("M_A2_") || name.EndsWith("_1941") || name.EndsWith("_1945")) continue;
                    if (!map.ContainsKey(name)) map[name] = m;
                }
            }
            return map;
        }

        static string CleanName(string n)
        {
            n = n.Replace(" (Instance)", "");
            int dot = n.LastIndexOf('.');
            if (dot > 0 && n.Length - dot == 4 && int.TryParse(n.Substring(dot + 1), out _)) n = n.Substring(0, dot);
            return n;
        }

        static Texture2D PrepareMask()
        {
            var ti = AssetImporter.GetAtPath(MaskPath) as TextureImporter;
            if (ti == null)
            {
                Debug.LogWarning($"[RupuSandSkins] 缺少积灰遮罩 {MaskPath}（Blender 重新生成 ENV_SandTable 会写出）");
                return null;
            }
            bool dirty = false;
            if (ti.sRGBTexture) { ti.sRGBTexture = false; dirty = true; }
            if (ti.wrapMode != TextureWrapMode.Repeat) { ti.wrapMode = TextureWrapMode.Repeat; dirty = true; }
            if (ti.alphaSource != TextureImporterAlphaSource.FromInput) { ti.alphaSource = TextureImporterAlphaSource.FromInput; dirty = true; }
            if (ti.textureType != TextureImporterType.Default) { ti.textureType = TextureImporterType.Default; dirty = true; }
            if (dirty) ti.SaveAndReimport();
            return AssetDatabase.LoadAssetAtPath<Texture2D>(MaskPath);
        }

        static Color BaseColor(Material m)
        {
            if (m.HasProperty("_BaseColor")) return m.GetColor("_BaseColor");
            if (m.HasProperty("_Color")) return m.GetColor("_Color");
            return Color.white;
        }

        static Texture BaseMap(Material m)
        {
            if (m.HasProperty("_BaseMap") && m.GetTexture("_BaseMap") != null) return m.GetTexture("_BaseMap");
            if (m.HasProperty("_MainTex")) return m.GetTexture("_MainTex");
            return null;
        }

        /// <summary>1941：饱和度 ×0.45、向灰土色靠 35%、略压暗（积灰细节会再提亮）；1945：在 1941 上再 ×0.7。</summary>
        public static Color SkinColor(Color c, int era)
        {
            Color.RGBToHSV(c, out float h, out float s, out float v);
            var g = Color.HSVToRGB(h, s * 0.45f, v);
            g = Color.Lerp(g, Dust1941, 0.35f) * 0.88f;
            if (era == 1945) g *= 0.7f;
            g.a = c.a;
            return g;
        }

        static void Make(Material src, string srcName, int era, Shader lit, Texture2D mask)
        {
            var path = $"{Dir}/{srcName}_{era}.mat";
            var tex = BaseMap(src);
            var col = BaseColor(src);
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            bool isNew = m == null;
            if (isNew) m = new Material(src);
            else m.CopyPropertiesFromMaterial(src);
            if (lit != null && m.shader != lit) m.shader = lit;
            m.name = $"{srcName}_{era}";

            var c = SkinColor(col, era);
            m.SetColor("_BaseColor", c);
            if (tex != null) m.SetTexture("_BaseMap", tex);
            if (m.HasProperty("_Smoothness")) m.SetFloat("_Smoothness", srcName.Contains("Water") ? (era == 1941 ? 0.25f : 0.15f) : 0.06f);
            if (m.HasProperty("_Metallic")) m.SetFloat("_Metallic", 0f);

            // 积灰：Detail Mask（A 通道）+ Detail Albedo（同一张图），scaled 模式：积灰处 ×(1+s)，干净处略暗
            bool detail = mask != null && m.HasProperty("_DetailMask") && m.HasProperty("_DetailAlbedoMap");
            if (detail)
            {
                float scale = era == 1941 ? 0.6f : 0.4f;
                m.SetTexture("_DetailMask", mask);
                m.SetTexture("_DetailAlbedoMap", mask);
                m.SetTextureScale("_DetailAlbedoMap", Vector2.one);
                m.SetFloat("_DetailAlbedoMapScale", scale);
                m.DisableKeyword("_DETAIL_MULX2");
                m.EnableKeyword("_DETAIL_SCALED");
            }
            else
            {
                m.DisableKeyword("_DETAIL_MULX2");
                m.DisableKeyword("_DETAIL_SCALED");
            }
            m.enableInstancing = true;

            if (isNew) AssetDatabase.CreateAsset(m, path);
            else EditorUtility.SetDirty(m);
        }
    }
}
