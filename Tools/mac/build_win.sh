#!/usr/bin/env bash
# Mac 上无界面交叉编译 Windows x64（Mono）。用法：Tools/mac/build_win.sh [--release]
# 注意：团结编辑器若已打开同一工程，batchmode 会因工程锁失败 —— 这时请用菜单 入谱 > 构建 Windows。
source "$(dirname "$0")/_common.sh"
EDITOR_BIN="$(find_editor)" || { echo "✗ 找不到团结编辑器（可设置 TUANJIE_EDITOR=.../Contents/MacOS/Tuanjie）"; exit 1; }
DEV="-rupuDev"; [[ "${1:-}" == "--release" ]] && DEV=""
mkdir -p "$BUILDS/Windows" "$BUILDS/logs"
LOG="$BUILDS/logs/build_$(date +%Y%m%d_%H%M%S).log"
echo "→ 编辑器: $EDITOR_BIN"
echo "→ 日志:   $LOG"
set +e
"$EDITOR_BIN" -batchmode -nographics -quit \
  -projectPath "$PROJECT" -buildTarget Win64 \
  -executeMethod Rupu.EditorTools.RupuBuild.BuildWindowsCLI \
  -rupuOut "$BUILDS/Windows" $DEV -logFile "$LOG"
CODE=$?
set -e
grep -E "\[Rupu\]|error CS|Build Finished|BuildFailedException" "$LOG" | tail -20 || true
if [[ $CODE -eq 0 && -f "$BUILDS/Windows/Rupu.exe" ]]; then
  echo "✓ 构建成功：$BUILDS/Windows/Rupu.exe（VM 内路径 \\\\vmware-host\\Shared Folders\\RupuBuilds\\Windows\\Rupu.exe）"
else
  echo "✗ 构建失败（exit $CODE），完整日志：$LOG"; exit 1
fi
