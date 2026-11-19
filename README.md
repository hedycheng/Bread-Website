# 我的閱讀筆記（Hugo + Obsidian + GitHub Pages）

在 Obsidian 寫作，把筆記屬性 `publish` 設成 true，雙擊同步，網站就會自動更新。

- 網站：Hugo 靜態網站，免費部署在 GitHub Pages
- 寫作：Obsidian（原稿永遠在你自己的 vault 裡）
- 隱私：**只有標記 `publish: true` 的筆記會被複製**，vault 裡其他私人筆記完全不會碰

---

## 一、四個分類

一篇文章只屬於一個分類。寫完問自己「這篇主要在做什麼？」

| 分類 | Obsidian 資料夾 | 判斷問題 | 例子 |
|---|---|---|---|
| **閱讀** | `Publish/reading` | 在講某本書嗎？ | 書摘、書評、心得 |
| **遊記** | `Publish/travel` | 在講我去過的地方、發生過的事嗎？ | 旅行紀錄、散步 |
| **隨筆** | `Publish/essays` | 是我的想法或感受嗎？ | 不針對書或旅行的想法 |
| **指南** | `Publish/guides` | 是別人可以照著做、照著找的整理嗎？ | 申請流程、推薦清單 |

**邊界提醒**：寫成「我去了這家店，感覺如何」的故事放遊記；整理成「推薦哪幾家、地址、特色」的清單放指南。

主題用**標籤**分，不要用分類：例如 `書摘`、`書評`、`小說`、`荷蘭`、`流程`、`清單`。

另外網站會自動產生三種索引頁（在每頁頁尾可以點）：
- **依標籤**：所有標籤
- **依書名**：同一本書的所有文章集中在一起（來自 `book` 屬性）
- **依地點**：同一個地方的所有文章集中在一起（來自 `place` 屬性）

---

## 二、Obsidian 設定

### 資料夾

在 vault 裡建立（名稱要用英文、完全照寫）：

```
Publish/
  ├ reading/
  ├ travel/
  ├ essays/
  └ guides/
```

### 範本

設定 → 核心外掛 → 開啟「範本」，把本專案 `obsidian-templates/` 的四個檔案放進你的範本資料夾。新增筆記後，用指令面板（Command + P）選「範本：插入範本」。

### 每個分類的屬性

放在檔案最上面。`publish: true` 才會發布。

**閱讀**
```yaml
---
title: 文章標題        # 沒填會用檔名
date: 2026-11-19
book: 書名            # 同一本書的文章會集中在「書」的索引
author: 作者
rating: 4             # 1–5，可留空
tags: [書摘]          # 書摘、書評、隨想…
publish: true
---
```

**遊記**
```yaml
---
title: 京都的下午
date: 2026-11-19
place: [日本, 京都]    # 多個地點用中括號，單一地點也可以直接寫 place: 京都
trip_date: 2026 年 10 月
tags: [散步]
publish: true
---
```

**隨筆**
```yaml
---
title: 標題
date: 2026-11-19
tags: []
publish: true
---
```

**指南**
```yaml
---
title: 申請某某證的方式
date: 2026-11-19
updated: 2026-11-19   # 每次修訂就改這個日期，文章會顯示「最後更新」
tags: [流程]          # 流程、清單…
publish: true
---
```

### 同步時會自動轉換

| Obsidian 寫法 | 網站上 |
|---|---|
| `[[另一篇筆記]]`、`[[筆記\|顯示文字]]` | 站內連結（對方沒發布就只留文字） |
| `![[圖片.png]]` | 自動複製圖片並顯示 |
| `==重點==` | 螢光標記 |
| `> [!note] 標題` | 提示框 |
| `%%私人註解%%` | 移除，不會公開 |

筆記放在 `Publish` 裡**不是這四個分類的資料夾**時，會被略過並提醒你。

---

## 三、日常發布（Mac）

1. 在 Obsidian 寫好文章，把 `publish` 改成 `true`。
2. 雙擊網站資料夾裡的 **`同步到網站.command`**。
   - 第一次會讓你選 Obsidian vault 資料夾，之後會記住。
   - 它會先列出「這次會發布哪些文章」，你確認後按 Enter 才會真的同步。
3. 完成後會自動打開 GitHub Desktop：填一句摘要 → **Commit to main** → **Push origin**。
4. 約 1–2 分鐘後網站更新。

第一次雙擊如果跳出「無法打開，因為無法驗證開發者」，在檔案上按**右鍵 → 打開 → 打開**。
如果跳出安裝「開發人員工具」的視窗，按安裝並等它完成，再重新雙擊一次。

不想用雙擊的話，也可以在終端機手動執行：

```bash
python3 scripts/sync_obsidian.py --vault "/你的/Vault/路徑"
```

**取消發布**：把 `publish` 改回 `false`（或刪除該檔案），再同步一次，文章就會從網站消失。

> ⚠️ **隱私提醒**：這是公開 repo，推送過的內容會留在 git 歷史裡。**不要把私人內容的 `publish` 設成 true 再推送**；取消發布只能讓它從網站消失，無法抹除歷史紀錄。想先確認會發布什麼，可以加 `--dry-run` 預覽，雙擊工具本來就會先預覽。

---

## 四、改網站名稱和說明

編輯 `hugo.toml`：`title`（網站名稱）、`params.description`（一句話介紹）、`params.author`（頁尾顯示的名字）。
再編輯 `content/about.md` 寫自我介紹。

範例文章（檔名開頭是 `sample-`）可以直接刪除：
`content/reading/sample-reading.md`、`content/travel/sample-travel.md`、`content/essays/sample-essay.md`、`content/guides/sample-guide.md`

---

## 五、在本機預覽（選用）

安裝 Hugo（Mac：`brew install hugo`），然後：

```bash
python3 scripts/sync_obsidian.py
hugo server
```

打開 http://localhost:1313 就能看到網站。

---

## 六、常見問題

**文章沒有出現在網站上？**
確認：① `publish` 是 `true`；② 筆記放在 `Publish/reading`、`travel`、`essays`、`guides` 其中一個；③ 有 Commit 並 Push；④ GitHub 的 Actions 分頁是綠色勾勾。

**想換外觀？**
版面在 `layouts/`，樣式在 `assets/css/main.css`，顏色和字型集中在檔案最上面的變數。

**想綁自己的網域？**
買好網域後，到 repository → Settings → Pages → Custom domain 填入，再到網域商設定 DNS。完成後把 `hugo.toml` 的 `baseURL` 改成你的網域。

**想新增或改名分類？**
分類就是 `content/` 底下有 `_index.md` 的資料夾。新增一個資料夾和 `_index.md`，再到 `hugo.toml` 的 `[[menus.main]]` 加一項，並在 Obsidian 建同名資料夾即可。

---

## 七、專案結構

```
hugo.toml              網站設定
content/               網站內容（同步腳本會寫入分類資料夾）
layouts/               版型
assets/css/main.css    樣式
static/images/         圖片（同步腳本會寫入這裡）
scripts/sync_obsidian.py   Obsidian 同步腳本
同步到網站.command     Mac 雙擊同步
obsidian-templates/    給 Obsidian 的範本
.github/workflows/     GitHub 自動部署
```
