#!/usr/bin/env bash
# 把 Tools/unity_seed 里的管线脚本拷进团结工程（工程由团结 Hub 用 Universal 3D 模板创建后执行一次；可重复执行以更新）
source "$(dirname "$0")/_common.sh"
[[ -d "$PROJECT/Assets" ]] || { echo "✗ 没有 $PROJECT/Assets —— 先在团结 Hub 新建工程：位置=$REPO，名称=Project_rupu，模板=Universal 3D"; exit 1; }
rsync -a "$REPO/Tools/unity_seed/Assets/" "$PROJECT/Assets/"
echo "✓ 已拷入 $PROJECT/Assets/_Rupu"
echo "  回到团结编辑器：菜单 入谱 > 初始化工程，再 入谱 > 创建美术测试场景"
