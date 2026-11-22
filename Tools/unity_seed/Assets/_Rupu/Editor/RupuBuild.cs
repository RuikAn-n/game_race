// 《入谱》Windows 构建入口：菜单 + 命令行
// 命令行（Mac 上交叉编译 Win64，Mono 后端）：
//   Tuanjie -batchmode -quit -projectPath Project_rupu -buildTarget Win64 \
//           -executeMethod Rupu.EditorTools.RupuBuild.BuildWindowsCLI [-rupuOut <dir>] [-rupuDev]
using System;
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Rupu.EditorTools
{
    public static class RupuBuild
    {
        public const string ArtTestScene = "Assets/_Rupu/Scenes/ArtTest.unity";

        static string DefaultOutDir =>
            Path.GetFullPath(Path.Combine(Application.dataPath, "..", "..", "Builds", "Windows"));

        [MenuItem("入谱/构建 Windows x64 (Development)", priority = 100)]
        public static void BuildWindowsDevMenu() => Build(DefaultOutDir, true);

        [MenuItem("入谱/构建 Windows x64 (Release)", priority = 101)]
        public static void BuildWindowsReleaseMenu() => Build(DefaultOutDir, false);

        public static void BuildWindowsCLI()
        {
            var args = Environment.GetCommandLineArgs();
            string outDir = DefaultOutDir;
            int i = Array.IndexOf(args, "-rupuOut");
            if (i >= 0 && i + 1 < args.Length) outDir = Path.GetFullPath(args[i + 1]);
            bool dev = args.Contains("-rupuDev");
            bool ok = Build(outDir, dev);
            EditorApplication.Exit(ok ? 0 : 1);
        }

        static string[] CollectScenes()
        {
            var scenes = EditorBuildSettings.scenes.Where(s => s.enabled && File.Exists(s.path))
                                                   .Select(s => s.path).ToArray();
            if (scenes.Length == 0 && File.Exists(ArtTestScene)) scenes = new[] { ArtTestScene };
            return scenes;
        }

        public static bool Build(string outDir, bool development)
        {
            var scenes = CollectScenes();
            if (scenes.Length == 0)
            {
                Debug.LogError("[Rupu] Build Settings 里没有场景，也没有 " + ArtTestScene + "。先执行 入谱/创建美术测试场景。");
                return false;
            }

            // Mac 主机交叉编译 Windows 只能用 Mono（IL2CPP for Windows 需要 Windows 主机）
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);

            Directory.CreateDirectory(outDir);
            var opts = new BuildPlayerOptions
            {
                scenes = scenes,
                locationPathName = Path.Combine(outDir, "Rupu.exe"),
                target = BuildTarget.StandaloneWindows64,
                targetGroup = BuildTargetGroup.Standalone,
                options = development ? (BuildOptions.Development | BuildOptions.AllowDebugging) : BuildOptions.None,
            };

            BuildReport report = BuildPipeline.BuildPlayer(opts);
            var s = report.summary;
            string msg = $"[Rupu] 构建 {s.result}  错误 {s.totalErrors}  警告 {s.totalWarnings}  " +
                         $"大小 {s.totalSize / (1024 * 1024)} MB  用时 {s.totalTime}  -> {opts.locationPathName}";
            File.WriteAllText(Path.Combine(outDir, "build_info.txt"),
                $"{DateTime.Now:yyyy-MM-dd HH:mm:ss}\n{msg}\nscenes: {string.Join(", ", scenes)}\ndev: {development}\n");
            if (s.result == BuildResult.Succeeded) Debug.Log(msg); else Debug.LogError(msg);
            return s.result == BuildResult.Succeeded;
        }
    }
}
