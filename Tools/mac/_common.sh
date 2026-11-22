#!/usr/bin/env bash
# 公共变量与函数
set -euo pipefail
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
PROJECT="$REPO/Project_rupu"
BUILDS="$REPO/Builds"
VMRUN="/Applications/VMware Fusion.app/Contents/Library/vmrun"
VMX="${RUPU_VMX:-$HOME/Virtual Machines.localized/Windows 11 64-bit Arm.vmwarevm/Windows 11 64-bit Arm.vmx}"
BLENDER="${RUPU_BLENDER:-/Applications/Blender.app/Contents/MacOS/Blender}"

# 找团结编辑器可执行文件：$TUANJIE_EDITOR > 与 ProjectVersion.txt 匹配的版本 > 任一已装版本
find_editor() {
  if [[ -n "${TUANJIE_EDITOR:-}" ]]; then echo "$TUANJIE_EDITOR"; return; fi
  local want=""
  [[ -f "$PROJECT/ProjectSettings/ProjectVersion.txt" ]] && \
    want="$(awk '/m_EditorVersion:/{print $2}' "$PROJECT/ProjectSettings/ProjectVersion.txt")"
  local apps
  apps="$(find /Applications "$HOME/Applications" -maxdepth 6 \( -name 'Tuanjie.app' -o -name 'Unity.app' \) -type d 2>/dev/null | grep -i tuanjie || true)"
  [[ -z "$apps" ]] && return 1
  local pick=""
  if [[ -n "$want" ]]; then pick="$(echo "$apps" | grep -F "$want" | head -1 || true)"; fi
  [[ -z "$pick" ]] && pick="$(echo "$apps" | sort -V | tail -1)"
  local bin
  bin="$(find "$pick/Contents/MacOS" -maxdepth 1 -type f -perm -u+x | head -1)"
  [[ -n "$bin" ]] && echo "$bin"
}

# 加密 VM（Win11 + TPM）需要 VM 加密密码：export RUPU_VM_ENC_PASS=... 或
#   security add-generic-password -s rupu-vm-enc -a vm -w <加密密码>
VM_ENC_PASS="${RUPU_VM_ENC_PASS:-$(security find-generic-password -s rupu-vm-enc -w 2>/dev/null || true)}"
vmrun_() {
  if [[ -n "$VM_ENC_PASS" ]]; then "$VMRUN" -T fusion -vp "$VM_ENC_PASS" "$@"; else "$VMRUN" -T fusion "$@"; fi
}
vm_running() { "$VMRUN" list | grep -qF "$VMX"; }
