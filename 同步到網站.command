#!/bin/bash
# ─────────────────────────────────────────────────────────────
#  雙擊執行：把 Obsidian 裡標記 publish: true 的筆記，同步到網站資料夾
#  做完之後會自動打開 GitHub Desktop，你只要按 Commit 和 Push 就會上線
# ─────────────────────────────────────────────────────────────

cd "$(dirname "$0")" || exit 1
HERE="$(pwd)"
CONF="$HOME/.bread-website.conf"

finish() {
  echo
  read -r -p "按 Enter 關閉視窗…" _
  exit "${1:-0}"
}

pick_folder() {   # 彈出選資料夾視窗；$1 是提示文字
  command -v osascript >/dev/null 2>&1 || return 1
  osascript -e "POSIX path of (choose folder with prompt \"$1\")" 2>/dev/null | sed 's:/$::'
}

# 讀取上次記住的設定（環境變數優先，方便測試）
SAVED_VAULT=""; SAVED_REPO=""
[ -f "$CONF" ] && . "$CONF"
VAULT="${VAULT:-$SAVED_VAULT}"
REPO="${REPO:-$SAVED_REPO}"

echo "=== 同步 Obsidian 筆記到網站 ==="
echo

# 1. 找到網站資料夾（這個檔案放在網站資料夾裡就會自動找到）
if [ -f "$HERE/scripts/sync_obsidian.py" ]; then
  REPO="$HERE"
fi
if [ -z "$REPO" ] || [ ! -f "$REPO/scripts/sync_obsidian.py" ]; then
  echo "請選擇網站資料夾（就是用 GitHub Desktop 下載下來的 Bread-Website 資料夾）…"
  REPO="$(pick_folder "請選擇網站資料夾（Bread-Website）")"
fi
if [ -z "$REPO" ] || [ ! -f "$REPO/scripts/sync_obsidian.py" ]; then
  echo "找不到網站資料夾，或它裡面沒有 scripts/sync_obsidian.py。"
  finish 1
fi

# 2. 找到 Obsidian vault
if [ -z "$VAULT" ] || [ ! -d "$VAULT" ]; then
  echo "請選擇你的 Obsidian vault 資料夾（就是裡面有 Publish 資料夾的那個）…"
  VAULT="$(pick_folder "請選擇你的 Obsidian vault 資料夾")"
fi
if [ -z "$VAULT" ] || [ ! -d "$VAULT" ]; then
  echo "沒有選擇 vault 資料夾，已取消。"
  finish 1
fi

printf 'SAVED_VAULT=%q\nSAVED_REPO=%q\n' "$VAULT" "$REPO" > "$CONF"

# 3. 確認電腦有 Python
if ! python3 --version >/dev/null 2>&1; then
  echo "這台電腦還沒有 Python。剛剛應該跳出了「安裝開發人員工具」的視窗，"
  echo "請按「安裝」，等它裝完（需要幾分鐘），再重新雙擊這個檔案。"
  finish 1
fi

# 4. 補上 .gitignore（避免把 Mac 的 .DS_Store 之類的雜檔送上 GitHub）
if [ ! -f "$REPO/.gitignore" ]; then
  printf 'public/\nresources/_gen/\n.hugo_build.lock\nscripts/.vault-path\n.DS_Store\nThumbs.db\n' > "$REPO/.gitignore"
fi

export OBSIDIAN_VAULT="$VAULT"

# 5. 先預覽，不寫入任何東西
echo "Vault：$VAULT"
echo "網站：$REPO"
echo
echo "--- 預覽：這次會發布的內容 ---"
if ! python3 "$REPO/scripts/sync_obsidian.py" --dry-run; then
  echo
  echo "預覽時發生問題，請看上面的訊息。"
  finish 1
fi
echo "-------------------------------"
echo
echo "沒標記 publish: true 的筆記不會出現在上面的清單，也不會被碰。"
read -r -p "確認要同步嗎？按 Enter 繼續，要取消請直接關閉這個視窗。" _

# 6. 真的同步
echo
python3 "$REPO/scripts/sync_obsidian.py" || finish 1

# 7. 打開 GitHub Desktop
echo
echo "同步完成。接下來："
echo "  1) 在 GitHub Desktop 左下角填一句摘要（例如：新增一篇書摘）"
echo "  2) 按藍色按鈕 Commit to main"
echo "  3) 按上方 Push origin"
echo "約 1–2 分鐘後網站就會更新。"
if command -v open >/dev/null 2>&1; then
  open -a "GitHub Desktop" "$REPO" 2>/dev/null || echo "（找不到 GitHub Desktop，請手動打開它。）"
fi
finish 0
