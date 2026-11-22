#!/usr/bin/env bash
# 一键：Mac 交叉编译 Windows -> 启动 VM -> 在 VM 里运行
source "$(dirname "$0")/_common.sh"
"$REPO/Tools/mac/build_win.sh" "$@"
"$REPO/Tools/mac/vm_run.sh"
