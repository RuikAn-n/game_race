#!/usr/bin/env bash
# 批量把 ArtSource 下所有 .blend 重新导出为 FBX（改了规格后全量重导用）
source "$(dirname "$0")/_common.sh"
fail=0
while IFS= read -r -d '' f; do
  [[ "$f" == *"/_Templates/"* ]] && continue
  echo "== $f"
  "$BLENDER" -b --factory-startup "$f" -P "$REPO/Tools/blender/rupu_pipeline.py" -- --export 2>&1 | grep -E '^\[' || fail=1
done < <(find "$REPO/ArtSource" -name '*.blend' -print0)
exit $fail
