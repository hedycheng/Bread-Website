#!/usr/bin/env bash
# 一鍵發布：同步 Obsidian 已發布筆記 → 提交 → 推送到 GitHub（之後由 GitHub 自動更新網站）
#
# 用法：
#   ./publish.sh --vault "/path/to/你的Vault"   # 第一次，會記住 vault 位置
#   ./publish.sh                                 # 之後直接執行
set -euo pipefail
cd "$(dirname "$0")"

python3 scripts/sync_obsidian.py "$@"

git add -A
if git diff --cached --quiet; then
  echo "沒有任何變更，不需要發布。"
  exit 0
fi

git commit -m "發布更新 $(date '+%Y-%m-%d %H:%M')"
git push
echo "已推送。約 1–2 分鐘後網站會更新（可到 GitHub 的 Actions 分頁查看進度）。"
