#!/usr/bin/env bash
# 室内场景白模：祠堂内景 + 环海楼内景（Blender 无界面）
#
#   Tools/mac/build_interiors.sh                     # 只生成缺失的 .blend
#   Tools/mac/build_interiors.sh --force             # 覆盖（会丢掉这两个 .blend 里的手改！）
#   Tools/mac/build_interiors.sh --force --preview Docs/images/interiors   # 同时出预览图
#   Tools/mac/build_interiors.sh --only BLD_INT_HuanhaiLou --force
source "$(dirname "$0")/_common.sh"
"$BLENDER" -b --factory-startup -P "$REPO/Tools/blender/build_interiors.py" -- "$@" 2>&1 | grep -E '^\[(OK|FAIL|ERROR|WARN|skip)'
