#!/usr/bin/env bash
# 检查《入谱》Mac 开发环境
source "$(dirname "$0")/_common.sh"
set +e
ok(){ echo "  ✓ $*"; }; bad(){ echo "  ✗ $*"; }
echo "【基础】"
command -v git >/dev/null && ok "git $(git --version | awk '{print $3}')" || bad git
git lfs version >/dev/null 2>&1 && ok "$(git lfs version | cut -d' ' -f1)" || bad "git-lfs（brew install git-lfs && git lfs install）"
gh auth status >/dev/null 2>&1 && ok "gh 已登录" || bad "gh 未登录（gh auth login）"
echo "【建模】"
[[ -x "$BLENDER" ]] && ok "$("$BLENDER" --version 2>/dev/null | head -1)" || bad "Blender 未找到"
[[ -d /Applications/krita.app ]] && ok Krita || echo "  - Krita 未装（可选）"
ls -d /Applications/Audacity*.app >/dev/null 2>&1 && ok Audacity || echo "  - Audacity 未装（可选）"
echo "【团结引擎】"
EB="$(find_editor)"
if [[ -n "$EB" ]]; then
  ok "编辑器 $EB"
  APP="${EB%/Contents/MacOS/*}"
  if find "$APP/.." "$APP/Contents" -maxdepth 4 -type d -iname 'WindowsStandaloneSupport' 2>/dev/null | grep -q .; then
    ok "Windows Build Support 已安装"
  else bad "缺 Windows Build Support (Mono) 模块：团结 Hub > 安装 > 该版本 > 添加模块"; fi
else
  bad "未安装团结编辑器（见 README §1）"
fi
[[ -f "$PROJECT/ProjectSettings/ProjectVersion.txt" ]] && ok "工程 $(awk '/m_EditorVersion:/{print $2}' "$PROJECT/ProjectSettings/ProjectVersion.txt")" || echo "  - 工程 Project_rupu 尚未创建"
[[ -f "$PROJECT/Assets/_Rupu/Editor/RupuBuild.cs" ]] && ok "管线脚本已拷入工程" || echo "  - 管线脚本未拷入（Tools/mac/seed_unity_project.sh）"
echo "【Windows 测试】"
[[ -x "$VMRUN" ]] && ok "VMware Fusion $(defaults read '/Applications/VMware Fusion.app/Contents/Info.plist' CFBundleShortVersionString)" || bad "VMware Fusion"
[[ -f "$VMX" ]] && ok "VM: $(basename "$VMX")  内存 $(awk -F'"' '/^memsize/{print $2}' "$VMX")MB  vCPU $(awk -F'"' '/^numvcpus/{print $2}' "$VMX")" || bad "VM 未找到（RUPU_VMX=...）"
grep -q '^encryption' "$VMX" 2>/dev/null && { [[ -n "$VM_ENC_PASS" ]] && ok "VM 加密密码已配置" || echo "  - VM 已加密，未配置加密密码（自动化受限，见 README §3）"; }
echo "【网络】"
for h in unity.cn github.com; do
  code=$(curl -s -o /dev/null -m 10 -w '%{http_code}' "https://$h"); [[ "$code" =~ ^[23] ]] && ok "$h ($code)" || bad "$h 不可达 ($code)"
done
