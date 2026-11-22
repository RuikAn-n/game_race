#!/usr/bin/env bash
# 启动 Win11 虚拟机，并（可选）在虚拟机桌面上直接运行最新构建。
#  - 构建目录 Builds/ 已作为共享文件夹 "RupuBuilds" 挂进 VM，无需拷贝
#  - 自动在 VM 里运行需要 Windows 账号：export RUPU_VM_USER=xxx RUPU_VM_PASS=xxx
#    （或存进钥匙串：security add-generic-password -s rupu-vm -a <用户名> -w <密码>）
#    没有账号时只启动 VM，你在 VM 里双击 RupuBuilds\run_latest.bat 即可
source "$(dirname "$0")/_common.sh"
if ! vm_running; then
  if [[ -z "$VM_ENC_PASS" ]]; then
    echo "→ VM 已加密且未提供加密密码：改用 Fusion 打开（会弹窗让你输入密码）"
    open -a "VMware Fusion" "$VMX"
    echo -n "→ 等待 VM 运行"; for i in $(seq 1 120); do vm_running && break; echo -n "."; sleep 2; done; echo
  else
    echo "→ 启动虚拟机…"; vmrun_ start "$VMX" gui
  fi
fi
if grep -q '^encryption' "$VMX" && [[ -z "$VM_ENC_PASS" ]]; then
  cat <<MSG
✓ VM 已打开。由于 VM 加密且脚本没有加密密码，无法自动挂载/启动，请二选一：
  a) 一次性手动：Fusion > 虚拟机 > 设置 > 共享 > 启用共享文件夹 > + 添加 $BUILDS（名称 RupuBuilds），
     之后在 VM 里双击 \\\\vmware-host\\Shared Folders\\RupuBuilds\\run_latest.bat
  b) 全自动：security add-generic-password -s rupu-vm-enc -a vm -w '<VM加密密码>'
             security add-generic-password -s rupu-vm -a '<Windows用户名>' -w '<Windows密码>'
MSG
  exit 0
fi
echo -n "→ 等待 VMware Tools"; for i in $(seq 1 90); do
  [[ "$(vmrun_ checkToolsState "$VMX" 2>/dev/null)" == "running" ]] && break; echo -n "."; sleep 2; done; echo
vmrun_ enableSharedFolders "$VMX" >/dev/null 2>&1 || true
# 动态挂载 Builds/ 为共享文件夹 RupuBuilds（已存在则只更新路径）
mkdir -p "$BUILDS"; cp -f "$REPO/Tools/windows/run_latest.bat" "$BUILDS/"
vmrun_ addSharedFolder "$VMX" RupuBuilds "$BUILDS" 2>/dev/null \
  || vmrun_ setSharedFolderState "$VMX" RupuBuilds "$BUILDS" writable

USER_="${RUPU_VM_USER:-}"; PASS_="${RUPU_VM_PASS:-}"
if [[ -z "$USER_" ]]; then
  USER_="$(security find-generic-password -s rupu-vm 2>/dev/null | awk -F'"' '/"acct"/{print $4}' || true)"
  [[ -n "$USER_" ]] && PASS_="$(security find-generic-password -s rupu-vm -w 2>/dev/null || true)"
fi
if [[ -z "$USER_" || -z "$PASS_" ]]; then
  echo "✓ VM 已就绪。请在 VM 内运行：\\\\vmware-host\\Shared Folders\\RupuBuilds\\run_latest.bat"; exit 0
fi
echo "→ 在 VM 桌面运行 Rupu.exe"
vmrun_ -gu "$USER_" -gp "$PASS_" runProgramInGuest "$VMX" -activeWindow -interactive -noWait \
  'C:\Windows\System32\cmd.exe' '/c "\\vmware-host\Shared Folders\RupuBuilds\run_latest.bat"'
echo "✓ 已发送启动命令；玩家日志在 VM 的 %USERPROFILE%\AppData\LocalLow\RupuTeam\入谱\Player.log"
