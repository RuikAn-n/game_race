// 《入谱》动画事件：把 Data/anim_events.json 写进各 FBX 的 clip 导入设置（管线导不进 FBX 的那部分）
//   菜单：入谱 / 人物 / 写入动画事件
//   命令行：-executeMethod Rupu.EditorTools.RupuAnimEvents.ApplyCLI
// 规则：
//   - JSON 的键 = FBX 文件名（不含扩展名），在 Assets/Art 下按名字找；帧号是 24 fps 原帧，换算成 clip 归一化时间。
//   - 只替换 JSON 里出现过的事件名，美术/程序在 Inspector 里另加的其他事件保留。可重复执行（幂等）。
//   - "loop": true/false 覆盖导入器按文件名猜的循环设置。
//   - 接收：动画物体上挂 Rupu.RupuAnimEventRelay（每个事件名都有同名方法），否则运行时会报「没有接收者」。
using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace Rupu.EditorTools
{
    public static class RupuAnimEvents
    {
        [MenuItem("入谱/人物/写入动画事件", priority = 46)]
        public static void ApplyMenu() => Apply();

        public static void ApplyCLI()
        {
            try { int n = Apply(); Debug.Log($"[RupuAnimEvents] 完成 {n} 个片段"); EditorApplication.Exit(0); }
            catch (Exception e) { Debug.LogException(e); EditorApplication.Exit(1); }
        }

        static string JsonPath => Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "Data", "anim_events.json"));

        public static int Apply()
        {
            var text = File.ReadAllText(JsonPath);
            var clips = ParseClips(text, out int fps);
            var known = new HashSet<string>(clips.Values.SelectMany(c => c.events.Select(e => e.Key)));
            var index = new Dictionary<string, string>();
            foreach (var g in AssetDatabase.FindAssets("t:Model", new[] { "Assets/Art" }))
            {
                var p = AssetDatabase.GUIDToAssetPath(g);
                index[Path.GetFileNameWithoutExtension(p)] = p;
            }
            int done = 0;
            var missing = new List<string>();
            AssetDatabase.StartAssetEditing();
            try
            {
                foreach (var kv in clips)
                {
                    if (!index.TryGetValue(kv.Key, out var path)) { missing.Add(kv.Key); continue; }
                    var mi = AssetImporter.GetAtPath(path) as ModelImporter;
                    if (mi == null) { missing.Add(kv.Key); continue; }
                    var arr = mi.clipAnimations;
                    if (arr == null || arr.Length == 0) arr = mi.defaultClipAnimations;
                    if (arr == null || arr.Length == 0) { missing.Add(kv.Key + "（无动画）"); continue; }
                    foreach (var c in arr)
                    {
                        float len = Mathf.Max(1f, c.lastFrame - c.firstFrame);
                        var keep = (c.events ?? new AnimationEvent[0]).Where(e => !known.Contains(e.functionName)).ToList();
                        foreach (var ev in kv.Value.events)
                        {
                            keep.Add(new AnimationEvent { functionName = ev.Key, time = Mathf.Clamp01((ev.Value - c.firstFrame) / len) });
                        }
                        c.events = keep.OrderBy(e => e.time).ToArray();
                        if (kv.Value.loop.HasValue) c.loopTime = kv.Value.loop.Value;
                    }
                    mi.clipAnimations = arr;
                    mi.SaveAndReimport();
                    done++;
                }
            }
            finally { AssetDatabase.StopAssetEditing(); }
            if (missing.Count > 0) Debug.LogWarning("[RupuAnimEvents] 没找到：" + string.Join("，", missing));
            Debug.Log($"[RupuAnimEvents] 写入 {done} / {clips.Count}（fps={fps}）");
            return done;
        }

        // ------------------------------------------------ 极简 JSON 读取（只认本文件的格式：clips → {events:[[名, 帧]...], loop}）
        class Entry { public List<KeyValuePair<string, float>> events = new List<KeyValuePair<string, float>>(); public bool? loop; }

        static Dictionary<string, Entry> ParseClips(string s, out int fps)
        {
            fps = 24;
            var m = System.Text.RegularExpressions.Regex.Match(s, "\"fps\"\\s*:\\s*(\\d+)");
            if (m.Success) fps = int.Parse(m.Groups[1].Value);
            var res = new Dictionary<string, Entry>();
            int ci = s.IndexOf("\"clips\"", StringComparison.Ordinal);
            if (ci < 0) return res;
            var rx = new System.Text.RegularExpressions.Regex(
                "\"([^\"]+@[^\"]+)\"\\s*:\\s*\\{\\s*\"events\"\\s*:\\s*\\[((?:\\s*\\[[^\\]]*\\]\\s*,?)*)\\s*\\]\\s*(?:,\\s*\"loop\"\\s*:\\s*(true|false))?",
                System.Text.RegularExpressions.RegexOptions.Singleline);
            var erx = new System.Text.RegularExpressions.Regex("\\[\\s*\"([^\"]+)\"\\s*,\\s*([0-9.]+)\\s*\\]");
            foreach (System.Text.RegularExpressions.Match cm in rx.Matches(s.Substring(ci)))
            {
                var e = new Entry();
                foreach (System.Text.RegularExpressions.Match em in erx.Matches(cm.Groups[2].Value))
                    e.events.Add(new KeyValuePair<string, float>(em.Groups[1].Value,
                        float.Parse(em.Groups[2].Value, System.Globalization.CultureInfo.InvariantCulture)));
                if (cm.Groups[3].Success) e.loop = cm.Groups[3].Value == "true";
                res[cm.Groups[1].Value] = e;
            }
            return res;
        }
    }
}
