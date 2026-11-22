#!/usr/bin/env bash
# 永昌堡总地图一键流水线：布局 -> Blender 白模/地形 -> 团结场景（民国+明代）-> 截图
#
#   Tools/mac/build_yongchang.sh                 # 只生成缺失的 .blend；重导地形；重建场景与截图
#   Tools/mac/build_yongchang.sh --force         # 覆盖全部程序化 .blend（会丢掉在这些 .blend 里的手改！）
#   Tools/mac/build_yongchang.sh --scene-only    # 只重建团结场景与截图（改了 era_*.json 颜色/套件时用）
#
# 团结编辑器打开同一工程时 batchmode 会被锁：关掉编辑器，或在编辑器里点 入谱 > 永昌堡 > 生成民国场景。
source "$(dirname "$0")/_common.sh"
FORCE=""; SCENE_ONLY=0
for a in "$@"; do
  case "$a" in
    --force) FORCE="--force" ;;
    --scene-only) SCENE_ONLY=1 ;;
  esac
done
mkdir -p "$BUILDS/logs"

if [[ $SCENE_ONLY -eq 0 ]]; then
  echo "→ 1/3 布局"
  python3 "$REPO/Tools/map/gen_layout.py" | tail -4
  echo "→ 2/3 Blender 资产（地形类 ENV_* 每次都按布局重导）"
  "$BLENDER" -b --factory-startup -P "$REPO/Tools/blender/build_yongchang.py" -- $FORCE 2>&1 | grep -E '^\[(OK|FAIL|ERROR|WARN|skip)' | grep -v '^\[skip\] ENV_' || true
  "$BLENDER" -b --factory-startup -P "$REPO/Tools/blender/build_yongchang.py" -- --force \
    --only ENV_Yongchang_Ground,ENV_Yongchang_Water,ENV_Yongchang_FieldsIn,ENV_Yongchang_FieldsOut,ENV_Luoshan_Hills 2>&1 \
    | grep -E '^\[(OK|FAIL|ERROR)' || true
fi

echo "→ 3/3 团结场景 + 截图"
"$REPO/Tools/mac/seed_unity_project.sh" >/dev/null
EDITOR_BIN="$(find_editor)" || { echo "✗ 找不到团结编辑器"; exit 1; }
LOG="$BUILDS/logs/map_$(date +%Y%m%d_%H%M%S).log"
set +e
"$EDITOR_BIN" -batchmode -quit -projectPath "$PROJECT" \
  -executeMethod Rupu.EditorTools.RupuMapBuilder.BuildAllCLI -logFile "$LOG" </dev/null
CODE=$?
set -e
grep -E "^\[Map\]|error CS" "$LOG" || true
if [[ $CODE -eq 0 ]]; then
  echo "✓ 场景：Project_rupu/Assets/_Rupu/Scenes/Map_Yongchang_{ROC,MING}.unity   截图：Builds/screens/"
else
  echo "✗ 失败（exit $CODE），日志：$LOG"; exit 1
fi
