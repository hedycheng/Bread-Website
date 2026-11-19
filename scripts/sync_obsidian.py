#!/usr/bin/env python3
"""
把 Obsidian vault 裡「標記為已發布」的筆記同步到 Hugo 網站的 content/。

規則（保護隱私）：
  * 只會讀取 vault 裡的 Publish/ 資料夾（可用 --publish-folder 改名）。
  * 只有檔案開頭屬性含 `publish: true` 的筆記才會被複製，其餘一律不碰。
    （也接受 `published: true`，但輸出時會移除，因為 Hugo 把 published 當成日期欄位。）
  * vault 的其他地方（私人筆記）完全不會被讀取內容，只會為了找圖片而掃描檔名。

轉換內容：
  * [[雙向連結]]、[[筆記|顯示文字]]  → 站內連結（對方未發布則只留文字）
  * ![[圖片.png]]                    → 複製圖片到 static/images/ 並嵌入
  * ==螢光標記==                     → <mark>螢光標記</mark>
  * %%Obsidian 註解%%                → 移除
  * 缺少 title / date 時自動補上（檔名、檔案修改日期）

用法：
  python3 scripts/sync_obsidian.py --vault "/path/to/你的Vault"   # 第一次，會記住路徑
  python3 scripts/sync_obsidian.py                                 # 之後直接執行
  python3 scripts/sync_obsidian.py --dry-run                       # 只預覽，不寫入

只使用 Python 標準函式庫，不需要安裝任何套件。
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import shutil
import sys
import urllib.parse
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONTENT = ROOT / "content"
IMAGES = ROOT / "static" / "images"
MANIFEST = ROOT / "scripts" / "synced-manifest.json"   # 記錄哪些檔案是同步產生的（要提交到 git）
VAULT_FILE = ROOT / "scripts" / ".vault-path"          # 記住 vault 位置（不提交）

IMAGE_EXT = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".svg", ".avif"}
SKIP_DIRS = {".obsidian", ".git", ".trash", "node_modules"}

FM_RE = re.compile(r"\A---[ \t]*\r?\n(.*?)\r?\n---[ \t]*(?:\r?\n|\Z)", re.S)


# ───────────────────────── 屬性（frontmatter）─────────────────────────

def split_frontmatter(text: str) -> tuple[str, str]:
    m = FM_RE.match(text)
    if not m:
        return "", text
    return m.group(1), text[m.end():]


def fm_get(fm: str, key: str) -> str | None:
    m = re.search(rf"^{re.escape(key)}[ \t]*:[ \t]*(.*)$", fm, re.M)
    if not m:
        return None
    return m.group(1).strip().strip("\"'")


PUBLISH_KEYS = ("publish", "published")


def is_published(fm: str) -> bool:
    for key in PUBLISH_KEYS:
        value = fm_get(fm, key)
        if value is not None and value.lower() in {"true", "yes", "y", "1"}:
            return True
    return False


def strip_publish_keys(fm: str) -> str:
    """輸出時移除發布開關；Hugo 會把 published 當成日期，留著會讓建置失敗。"""
    lines = [ln for ln in fm.split("\n") if not re.match(rf"^({'|'.join(PUBLISH_KEYS)})[ \t]*:", ln)]
    return "\n".join(lines)


# ───────────────────────── 內文轉換 ─────────────────────────

def transform_outside_code(text: str, fn) -> str:
    """只對「不在程式碼區塊／行內程式碼」的文字套用 fn。"""
    out: list[str] = []
    fence: str | None = None
    for line in text.split("\n"):
        m = re.match(r"^\s*(`{3,}|~{3,})", line)
        if m:
            marker = m.group(1)[0] * 3
            if fence is None:
                fence = marker
            elif line.strip().startswith(fence):
                fence = None
            out.append(line)
            continue
        if fence is not None:
            out.append(line)
            continue
        parts = re.split(r"(`+[^`\n]*`+)", line)
        out.append("".join(p if (len(p) > 1 and p.startswith("`") and p.endswith("`")) else fn(p) for p in parts))
    return "\n".join(out)


class Synced:
    """一次同步過程中的狀態。"""

    def __init__(self, vault: Path, publish_dir: Path, dry_run: bool):
        self.vault = vault
        self.publish_dir = publish_dir
        self.dry_run = dry_run
        self.notes: dict[str, str] = {}          # 小寫的筆記名稱 → 目的地（如 /excerpts/foo.md）
        self.images_index: dict[str, Path] = {}  # 檔名 → vault 內實際位置
        self.copied_images: dict[str, Path] = {}  # static/images 內的檔名 → 來源
        self.warnings: list[str] = []

    # ── 索引 ──
    def build_image_index(self) -> None:
        for dirpath, dirnames, filenames in os.walk(self.vault):
            dirnames[:] = [d for d in dirnames if d not in SKIP_DIRS]
            for name in filenames:
                if Path(name).suffix.lower() in IMAGE_EXT:
                    self.images_index.setdefault(name.lower(), Path(dirpath) / name)

    def register_note(self, src: Path, dest_rel: str, title: str | None) -> None:
        dest = "/" + dest_rel.replace("\\", "/")
        self.notes[src.stem.lower()] = dest
        if title:
            self.notes.setdefault(title.lower(), dest)

    # ── 圖片 ──
    def place_image(self, source: Path) -> str:
        safe = re.sub(r"\s+", "-", source.name)
        name = safe
        owner = self.copied_images.get(name)
        if owner is not None and owner != source:
            name = hashlib.md5(str(source).encode()).hexdigest()[:6] + "-" + safe
        self.copied_images[name] = source
        if not self.dry_run:
            IMAGES.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, IMAGES / name)
        return "/images/" + urllib.parse.quote(name)

    def find_image(self, ref: str, note_dir: Path) -> Path | None:
        ref = urllib.parse.unquote(ref.strip())
        for candidate in (note_dir / ref, self.vault / ref):
            if candidate.is_file():
                return candidate
        return self.images_index.get(Path(ref).name.lower())

    # ── 轉換主流程 ──
    def convert_body(self, body: str, note_path: Path) -> str:
        note_dir = note_path.parent

        body = re.sub(r"%%.*?%%", "", body, flags=re.S)  # Obsidian 註解

        def embed(m: re.Match) -> str:
            target, alias = m.group(1).strip(), (m.group(2) or "").strip()
            if Path(target).suffix.lower() in IMAGE_EXT:
                src = self.find_image(target, note_dir)
                if src is None:
                    self.warnings.append(f"{note_path.name}：找不到圖片 {target}")
                    return ""
                alt = "" if re.fullmatch(r"\d+(x\d+)?", alias) else alias
                return f"![{alt}]({self.place_image(src)})"
            return link(m)  # 嵌入其他筆記 → 改成連結

        def link(m: re.Match) -> str:
            target = m.group(1).strip()
            heading = (m.group(2) or "").lstrip("#").strip() if m.re.groups >= 3 and m.group(2) and m.group(2).startswith("#") else ""
            alias = (m.group(m.re.groups) or "").strip()
            name = target.split("/")[-1].split("#")[0]
            text = alias or (heading and f"{name} › {heading}") or name
            dest = self.notes.get(name.lower())
            if dest is None:
                self.warnings.append(f"{note_path.name}：連結 [[{target}]] 的對象沒有發布，已改成純文字")
                return text
            return f"[{text}](<{dest}>)"

        def std_image(m: re.Match) -> str:
            alt, ref = m.group(1), m.group(2)
            src = self.find_image(ref, note_dir)
            if src is None:
                self.warnings.append(f"{note_path.name}：找不到圖片 {ref}")
                return m.group(0)
            return f"![{alt}]({self.place_image(src)})"

        def inline(text: str) -> str:
            text = re.sub(r"!\[\[([^\[\]|]+?)(?:\|([^\[\]]*))?\]\]", embed, text)
            text = re.sub(r"\[\[([^\[\]|#]+)(#[^\[\]|]*)?(?:\|([^\[\]]*))?\]\]", link, text)
            text = re.sub(r"!\[([^\]]*)\]\((?!https?://|/|data:)([^)\s]+)\)", std_image, text)
            text = re.sub(r"==([^=\n]+?)==", r"<mark>\1</mark>", text)
            return text

        return transform_outside_code(body, inline)


def add_missing_fields(fm: str, note_path: Path) -> str:
    fm = strip_publish_keys(fm)
    extra = []
    if fm_get(fm, "title") is None:
        extra.append("title: " + json.dumps(note_path.stem, ensure_ascii=False))
    if fm_get(fm, "date") is None:
        mtime = datetime.fromtimestamp(note_path.stat().st_mtime)
        extra.append("date: " + mtime.strftime("%Y-%m-%d"))
    return fm + ("\n" + "\n".join(extra) if extra else "")


# ───────────────────────── 清單與清理 ─────────────────────────

def load_manifest() -> list[str]:
    if MANIFEST.exists():
        try:
            return json.loads(MANIFEST.read_text(encoding="utf-8")).get("files", [])
        except (json.JSONDecodeError, OSError):
            return []
    return []


def remove_previous(files: list[str], dry_run: bool) -> None:
    """刪除上次同步產生的檔案，這樣取消發布的筆記也會從網站消失。"""
    for rel in files:
        path = (ROOT / rel).resolve()
        inside = CONTENT.resolve() in path.parents or IMAGES.resolve() in path.parents
        if inside and path.is_file() and not dry_run:
            path.unlink()
    if dry_run:
        return
    for base in (CONTENT, IMAGES):
        for dirpath, _, _ in sorted(os.walk(base), key=lambda x: -len(x[0])):
            p = Path(dirpath)
            if p != base and p != CONTENT / "" and not any(p.iterdir()):
                p.rmdir()


def resolve_vault(arg: str | None) -> Path:
    raw = arg or os.environ.get("OBSIDIAN_VAULT")
    if not raw and VAULT_FILE.exists():
        raw = VAULT_FILE.read_text(encoding="utf-8").strip()
    if not raw:
        sys.exit("請用 --vault 指定 Obsidian vault 的資料夾路徑（第一次指定後會自動記住）。")
    vault = Path(raw).expanduser().resolve()
    if not vault.is_dir():
        sys.exit(f"找不到 vault 資料夾：{vault}")
    return vault


def main() -> None:
    ap = argparse.ArgumentParser(description="同步 Obsidian 已發布筆記到 Hugo 網站")
    ap.add_argument("--vault", help="Obsidian vault 資料夾路徑")
    ap.add_argument("--publish-folder", default="Publish", help="vault 內放待發布筆記的資料夾名稱（預設 Publish）")
    ap.add_argument("--dry-run", action="store_true", help="只顯示會做什麼，不實際寫入")
    args = ap.parse_args()

    vault = resolve_vault(args.vault)
    publish_dir = vault / args.publish_folder
    if not publish_dir.is_dir():
        sys.exit(f"vault 裡找不到「{args.publish_folder}」資料夾：{publish_dir}\n"
                 f"請先在 vault 建立它，並在裡面放 excerpts、reviews、info 子資料夾。")
    if args.vault and not args.dry_run:
        VAULT_FILE.write_text(str(vault), encoding="utf-8")

    state = Synced(vault, publish_dir, args.dry_run)
    state.build_image_index()

    # 第一輪：找出所有已發布的筆記，建立連結對照表
    published: list[tuple[Path, str, str, str]] = []  # (來源, 目的相對路徑, 屬性, 內文)
    skipped = 0
    for src in sorted(publish_dir.rglob("*.md")):
        if any(part in SKIP_DIRS for part in src.relative_to(publish_dir).parts):
            continue
        text = src.read_text(encoding="utf-8")
        fm, body = split_frontmatter(text)
        if not is_published(fm):
            skipped += 1
            continue
        rel = src.relative_to(publish_dir)
        if rel.name == "_index.md":
            state.warnings.append(f"略過 {rel}：_index.md 請直接在網站專案的 content/ 裡編輯")
            continue
        dest_rel = (Path("content") / rel).as_posix()
        site_rel = rel.as_posix()
        state.register_note(src, site_rel, fm_get(fm, "title"))
        published.append((src, dest_rel, fm, body))

    # 清掉上次同步的內容，再寫入這次的
    previous = load_manifest()
    remove_previous(previous, args.dry_run)

    written: list[str] = []
    for src, dest_rel, fm, body in published:
        out_fm = add_missing_fields(fm, src)
        out_body = state.convert_body(body, src)
        dest = ROOT / dest_rel
        if not args.dry_run:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(f"---\n{out_fm}\n---\n{out_body}", encoding="utf-8", newline="\n")
        written.append(dest_rel)

    written += [f"static/images/{name}" for name in sorted(state.copied_images)]
    if not args.dry_run:
        MANIFEST.write_text(json.dumps({"files": written}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    note_count = len(published)
    print(f"{'（預覽）' if args.dry_run else ''}同步完成：{note_count} 篇已發布、{skipped} 篇未發布（已略過）、{len(state.copied_images)} 張圖片。")
    for w in state.warnings:
        print("  注意：" + w)


if __name__ == "__main__":
    main()
