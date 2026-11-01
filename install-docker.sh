#!/usr/bin/env bash
# Explicitly invoked installer, official Docker apt repository; Ubuntu/Debian only.
set -euo pipefail
[[ $EUID -eq 0 ]] || { echo '请用 sudo bash install-docker.sh'; exit 1; }
source /etc/os-release
[[ "$ID" == ubuntu || "$ID" == debian ]] || { echo '仅支持 Ubuntu/Debian，请按 Docker 官方文档安装。'; exit 1; }
if command -v docker >/dev/null; then
  echo '检测到已有 Docker；请用对应安装来源补齐 Compose v2，避免替换已有安装。'
  exit 1
fi
apt-get update
apt-get install -y ca-certificates curl python3
install -m 0755 -d /etc/apt/keyrings
curl -fsSL "https://download.docker.com/linux/$ID/gpg" -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
printf 'Types: deb\nURIs: https://download.docker.com/linux/%s\nSuites: %s\nComponents: stable\nArchitectures: %s\nSigned-By: /etc/apt/keyrings/docker.asc\n' \
  "$ID" "${UBUNTU_CODENAME:-$VERSION_CODENAME}" "$(dpkg --print-architecture)" > /etc/apt/sources.list.d/docker.sources
apt-get update
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
systemctl enable --now docker
echo 'Docker 已安装。回到普通用户运行 bash setup.sh；无权限时可用 sudo bash setup.sh。'
