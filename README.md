# 我的閱讀筆記（Hugo + Obsidian + GitHub Pages）

在 Obsidian 寫作，把筆記屬性 `publish` 勾成 true，執行一個指令，網站就會自動更新。

- 網站：Hugo 靜態網站，免費部署在 GitHub Pages
- 寫作：Obsidian（原稿永遠在你自己的 vault 裡）
- 隱私：**只有標記 `publish: true` 的筆記會被複製**，vault 裡其他私人筆記完全不會碰

---

## 一、第一次設定（約 15 分鐘）

### 1. 上傳到 GitHub

1. 到 GitHub 建立新的 repository，例如 `reading-notes`，設為 **Public**（免費帳號的 GitHub Pages 通常需要公開 repo），**不要**勾選 README。
2. 在這個資料夾打開終端機，依序執行（把 `你的帳號` 換掉）：

```bash
git init -b main
git add -A
git commit -m "第一次提交"
git remote add origin https://github.com/你的帳號/reading-notes.git
git push -u origin main
```

### 2. 開啟 GitHub Pages

repository 頁面 → **Settings** → **Pages** → **Build and deployment** → **Source** 選 **GitHub Actions**。

然後到 **Actions** 分頁，若第一次執行失敗，點進去按 **Re-run all jobs**。約 1–2 分鐘後，網址會是：

`https://你的帳號.github.io/reading-notes/`

### 3. 改成你的網站資訊

編輯 `hugo.toml`：`title`（網站名稱）、`params.description`（一句話介紹）、`params.author`（頁尾顯示的名字）。
再編輯 `content/about.md` 寫自我介紹。

### 4. 刪除範例文章

刪掉這三個檔案（它們只是用來預覽版面）：

- `content/excerpts/sample-excerpt.md`
- `content/reviews/sample-review.md`
- `content/info/sample-info.md`

---

## 二、Obsidian 設定

1. 在 vault 裡建立資料夾結構（資料夾名稱就是網站分類的網址）：

```
你的Vault/
└── Publish/
    ├── excerpts/   ← 書摘
    ├── reviews/    ← 心得
    └── info/       ← 資訊
```

2. （建議）設定 → 核心外掛 → 開啟「範本」，把本專案 `obsidian-templates/` 裡的三個檔案複製到你的範本資料夾。之後新增筆記時插入範本，就有現成的屬性。
3. 每篇文章的屬性（檔案最上面）：

```yaml
---
title: 文章標題
date: 2026-11-19
book: 書名          # 書摘、心得用，可留空
author: 作者        # 可留空
rating: 4           # 1–5 顆星，可留空
tags: [小說, 日本]
publish: false      # 改成 true 才會發布
---
```

沒有填 `title` 會用檔名，沒有填 `date` 會用檔案修改日期。

### 同步時會自動轉換

| Obsidian 寫法 | 網站上 |
|---|---|
| `[[另一篇筆記]]`、`[[筆記\|顯示文字]]` | 站內連結（對方沒發布就只留文字） |
| `![[圖片.png]]` | 自動複製圖片並顯示 |
| `==重點==` | 螢光標記 |
| `> [!note] 標題` | 提示框 |
| `%%私人註解%%` | 移除，不會公開 |

---

## 三、日常發布

1. 在 Obsidian 寫好文章，把 `publish` 改成 `true`。
2. 在這個專案資料夾執行：

```bash
./publish.sh --vault "/你的/Vault/路徑"    # 第一次，之後會記住
./publish.sh                                # 之後只要這一行
```

3. 約 1–2 分鐘後網站更新。

沒有 bash 的話（例如 Windows），可以手動執行：

```bash
python3 scripts/sync_obsidian.py --vault "C:\路徑\你的Vault"
git add -A
git commit -m "發布更新"
git push
```

**取消發布**：把 `publish` 改回 `false`（或刪除該檔案），再執行一次 `./publish.sh`，文章就會從網站消失。

> ⚠️ **隱私提醒**：這是公開 repo，推送過的內容會留在 git 歷史裡。**不要把私人內容的 `publish` 設成 true 後再推送**；取消發布只能讓它從網站消失，無法抹除歷史紀錄。想先確認會發布什麼，可以用 `python3 scripts/sync_obsidian.py --dry-run` 預覽。

---

## 四、在本機預覽（選用）

安裝 Hugo（Mac：`brew install hugo`；其他系統見 https://gohugo.io/installation/），然後：

```bash
python3 scripts/sync_obsidian.py
hugo server
```

打開 http://localhost:1313 就能看到網站，存檔後會自動重新整理。

---

## 五、常見問題

**文章沒有出現在網站上？**
確認：① `publish` 是 `true`；② 檔案在 `Publish/` 底下的子資料夾（`excerpts`、`reviews`、`info`）；③ 有執行 `./publish.sh` 並推送成功；④ GitHub 的 Actions 分頁顯示綠色勾勾。

**Actions 顯示 "Get Pages site failed"？**
還沒完成「二、開啟 GitHub Pages」的設定，把 Source 選成 GitHub Actions 後重新執行。

**想換外觀？**
版面在 `layouts/`，樣式在 `assets/css/main.css`，顏色和字型都集中在檔案最上面的變數。

**想綁自己的網域？**
買好網域後，到 repository → Settings → Pages → Custom domain 填入，再依畫面說明到網域商設定 DNS。完成後把 `hugo.toml` 的 `baseURL` 改成你的網域。

---

## 六、專案結構

```
hugo.toml              網站設定
content/               網站內容（同步腳本會寫入這裡）
layouts/               版型
assets/css/main.css    樣式
static/images/         圖片（同步腳本會寫入這裡）
scripts/sync_obsidian.py   Obsidian 同步腳本
publish.sh             一鍵發布
obsidian-templates/    給 Obsidian 的範本
.github/workflows/     GitHub 自動部署
```

之後可以再加：按讚、電子報訂閱、站內搜尋、自動產生 Threads / Instagram 短版貼文。
