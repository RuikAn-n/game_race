#!/usr/bin/env bash
# 不用共享文件夹，把最新构建通过 VMware 内网发给虚拟机。
# 只监听 VMware 虚拟网卡（bridge100/101），局域网访问不到。Ctrl+C 停止。
source "$(dirname "$0")/_common.sh"
PORT="${RUPU_PORT:-8624}"
[[ -f "$BUILDS/Windows/Rupu.exe" ]] || { echo "✗ 先构建：Tools/mac/build_win.sh"; exit 1; }
OUT="$BUILDS/serve"; mkdir -p "$OUT"
rm -f "$OUT/Rupu_Windows.zip"
(cd "$BUILDS/Windows" && zip -qr -9 "$OUT/Rupu_Windows.zip" . -x '*_DoNotShip/*')
cp -f "$REPO/Tools/windows/get_and_run.ps1" "$OUT/"
IPS=$(ifconfig | awk '/^bridge1[0-9][0-9]:/{b=1;next} /^[a-z]/{b=0} b&&/inet /{print $2}')
[[ -n "$IPS" ]] || { echo "✗ 找不到 VMware 虚拟网卡，VM 开着吗？"; exit 1; }
PIDS=()
for ip in $IPS; do
  python3 -m http.server "$PORT" --bind "$ip" --directory "$OUT" >/dev/null 2>&1 & PIDS+=($!)
done
trap 'kill ${PIDS[*]} 2>/dev/null' EXIT
echo "✓ 已发布 $(du -h "$OUT/Rupu_Windows.zip" | cut -f1)。在 VM 里按 Win+R，粘贴下面任一行回车（哪个能连上用哪个）："
for ip in $IPS; do
  echo "  powershell -ExecutionPolicy Bypass -c \"iex (iwr http://$ip:$PORT/get_and_run.ps1 -UseBasicParsing).Content\""
done
echo "（Ctrl+C 停止服务）"
wait
