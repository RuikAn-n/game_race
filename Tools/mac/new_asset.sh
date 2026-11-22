#!/usr/bin/env bash
# 新建符合规格的 .blend：Tools/mac/new_asset.sh Characters NPC_WangYan
source "$(dirname "$0")/_common.sh"
[[ $# -eq 2 ]] || { echo "用法: $0 <Characters|Enemies|Bosses|Buildings|Props|Environments> <资产名>"; exit 1; }
"$BLENDER" -b --factory-startup -P "$REPO/Tools/blender/rupu_pipeline.py" -- --new-template "$1" "$2" 2>&1 | grep -E '^\['
open -a Blender "$REPO/ArtSource/$1/$2.blend"
