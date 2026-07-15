#!/bin/bash
# deploy.sh — AI Chat Assistant 部署脚本
# 由 CI/CD 拷贝到服务器后执行
set -e

echo "=== 开始部署 ==="
TEMP_DIR=/root/ai-chat-assistant-temp
TARBALL=/root/ai-chat-assistant-tarball.tar.gz
OLD_DIR=/root/ai-chat-assistant-old
TARGET_DIR=/root/ai-chat-assistant

cd /root
rm -f "$TARBALL"
DOWNLOAD_URL="https://github.com/zhu-app/ai-chat-assistant/archive/master.tar.gz"
echo "Downloading from $DOWNLOAD_URL ..."

if command -v curl >/dev/null 2>&1; then
  curl -sL --connect-timeout 15 --max-time 90 -o "$TARBALL" "$DOWNLOAD_URL" && echo "curl OK" || echo "curl failed"
fi
if [ ! -f "$TARBALL" ] || [ ! -s "$TARBALL" ]; then
  if command -v wget >/dev/null 2>&1; then
    wget -q --timeout=90 -O "$TARBALL" "$DOWNLOAD_URL" && echo "wget OK" || echo "wget failed"
  fi
fi
if [ ! -f "$TARBALL" ] || [ ! -s "$TARBALL" ]; then
  echo "ERROR: Failed to download tarball" >&2
  exit 1
fi

rm -rf "$TEMP_DIR"
mkdir -p "$TEMP_DIR"
tar -xzf "$TARBALL" -C "$TEMP_DIR" --strip-components=1 || { echo "ERROR: tar extraction failed" >&2; exit 1; }
rm -f "$TARBALL"
echo "Extracted OK"

cp "$TARGET_DIR/backend/data" "$TEMP_DIR/backend/" -r 2>/dev/null || true
cp "$TARGET_DIR/backend/.env.production" "$TEMP_DIR/backend/" 2>/dev/null || true
cp "$TARGET_DIR/backend/knowledge" "$TEMP_DIR/backend/" -r 2>/dev/null || true
echo "Data preserved"

if [ -f /tmp/env_config.txt ]; then
  cat /tmp/env_config.txt >> "$TEMP_DIR/backend/.env.production"
  echo "Env config merged"
fi

rm -rf "$OLD_DIR"
mv "$TARGET_DIR" "$OLD_DIR" 2>/dev/null || true
mv "$TEMP_DIR" "$TARGET_DIR"
echo "Directory swapped"

cd "$TARGET_DIR"
echo "Building and restarting..."
docker compose up -d --build || echo "docker compose failed"
docker image prune -f || true
rm -rf "$OLD_DIR" 2>/dev/null || true
echo "=== 部署完成 ==="
