# fix-threads-fetcher Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修復 Threads 匿名 fetcher（行動版指紋）並加上 og fallback 降級鏈與相關串文污染防護。

**Architecture:** 單檔 CLI 腳本 `scripts/fetch_threads_post.py`。主管道改行動版瀏覽器 context（實測可繞過匿名封鎖）；Relay 抽取失敗時降級 stdlib HTTP GET 抓 og meta 產出 partial 輸出；退出碼三態（0 完整 / 3 partial / 2 全失敗）。解析層演算法與輸出目錄契約不變。

**Tech Stack:** Python 3.12+、Playwright（既有）、stdlib `urllib.request` + `html`（og fallback，零新依賴）、pytest。

**對應 tasks.md**：Task 1 → tasks §1.1；Task 2 → §2.1；Task 3 → §2.2；Task 4-6 → §3.1-3.3；Task 7 → §4.1-4.3。

**測試指令**（repo 根執行）：`python -m pytest tests/test_fetch_threads_post.py -v`（新測試全加在此檔，沿用其既有 `sys.path.insert` import 機制：`import fetch_threads_post as ftp` 形式以該檔開頭實際寫法為準，下述測試碼假設模組別名 `ftp`）。

---

### Task 1: 釘住 classify 對他人頂層非回覆貼文的行為

**Files:**
- Test: `tests/test_fetch_threads_post.py`

背景：實測行動版頁面會載入「相關串文」，他人的頂層非回覆貼文混進 Relay 資料。`classify()`（`scripts/fetch_threads_post.py:37-61`）對 `is_reply` falsy 的節點不看作者一律回 `"A"`。本 task 用 characterization test 把這個行為釘住，作為 Task 3 防護的動機文件。

- [ ] **Step 1: 寫 characterization test**

```python
def test_classify_foreign_top_level_nonreply_returns_A():
    """行動版頁面的「相關串文」節點：他人頂層非回覆貼文，classify 現行為回 A。

    這是污染來源的文件化——A 段的作者過濾防護（drop_foreign_main_posts）
    因此存在。若未來 classify 改為回 E，本測試與防護一起調整。
    """
    foreign = {
        "pk": "99",
        "code": "FOREIGN1",
        "caption": {"text": "unrelated recommended post"},
        "user": {"username": "someone_else"},
        "text_post_app_info": {"is_reply": False},
    }
    assert ftp.classify(foreign, "main_author") == "A"
```

- [ ] **Step 2: 跑測試，預期直接 PASS（釘現況）**

Run: `python -m pytest tests/test_fetch_threads_post.py::test_classify_foreign_top_level_nonreply_returns_A -v`
Expected: PASS（classify 現行為即回 A；若 FAIL 表示對現況理解錯誤，回頭修 design D5）

- [ ] **Step 3: Commit**

```bash
git add tests/test_fetch_threads_post.py
git commit -m "test: pin classify behavior for foreign top-level non-reply posts"
```

---

### Task 2: fetch_page 行動版 context（含可測的指紋契約）

**Files:**
- Modify: `scripts/fetch_threads_post.py:242-259`（`fetch_page`）+ 模組層常數 + 新純函式
- Test: `tests/test_fetch_threads_post.py`

Codex ④：Playwright 網路行為不 mock（design D6），但「建 context 的參數」是純本地契約，可測。做法：把 context kwargs 抽成純函式 `mobile_context_kwargs()`，`fetch_page` 用它，測試斷言指紋正確且無登入態鍵。

- [ ] **Step 1: 寫失敗測試（指紋契約）**

```python
def test_mobile_context_kwargs_is_anonymous_mobile():
    kw = ftp.mobile_context_kwargs()
    assert kw["user_agent"] == ftp.MOBILE_UA
    assert "iPhone" in ftp.MOBILE_UA
    assert kw["viewport"] == {"width": 390, "height": 844}
    assert kw["is_mobile"] is True
    # 匿名鐵律：絕不帶登入態
    assert "storage_state" not in kw
    assert "cookies" not in kw
```

- [ ] **Step 2: 跑測試確認 FAIL**

Run: `python -m pytest tests/test_fetch_threads_post.py -k mobile_context_kwargs -v`
Expected: FAIL — no attribute `mobile_context_kwargs`

- [ ] **Step 3: 加模組層常數 `MOBILE_UA` + `mobile_context_kwargs()`**

在 `_RELAY_QUERY_MARKER`（`:97`）附近加：

```python
# 2026-07-05 起 Threads 對桌面匿名流量一律導向 logged-out feed；
# 行動版 UA + is_mobile 實測仍可取得完整 Relay 資料（見 openspec change fix-threads-fetcher）。
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
)


def mobile_context_kwargs() -> dict:
    """Playwright new_context kwargs for anonymous mobile fetch (design D1).

    抽成純函式使指紋契約可單測，無需 mock Chromium。刻意不含
    storage_state / cookies——匿名鐵律。
    """
    return {
        "user_agent": MOBILE_UA,
        "viewport": {"width": 390, "height": 844},
        "is_mobile": True,
    }
```

- [ ] **Step 4: 跑測試確認 PASS**

Run: `python -m pytest tests/test_fetch_threads_post.py -k mobile_context_kwargs -v`
Expected: PASS

- [ ] **Step 5: 改 `fetch_page` 用該函式**

```python
            ctx = browser.new_context(**mobile_context_kwargs())
```

（docstring 的 "Anonymous browsing — no cookies, no login." 保留並補一句 "Mobile fingerprint — desktop anonymous access is blocked since 2026-07."）

- [ ] **Step 6: 跑全套測試確認零回歸**

Run: `python -m pytest tests/test_fetch_threads_post.py -v`
Expected: 全 PASS（解析層不受影響）

- [ ] **Step 7: Commit**

```bash
git add scripts/fetch_threads_post.py tests/test_fetch_threads_post.py
git commit -m "fix: use mobile browser fingerprint to bypass anonymous desktop block"
```

---

### Task 3: A 段作者過濾防護（drop_foreign_main_posts）

**Files:**
- Modify: `scripts/fetch_threads_post.py`（新純函式 + `main()` 接線 `:314` 附近）
- Test: `tests/test_fetch_threads_post.py`

- [ ] **Step 1: 寫失敗測試**

```python
def _mk(username, code, is_reply=False, reply_to=None):
    info = {"is_reply": is_reply}
    if reply_to:
        info["reply_to_author"] = {"username": reply_to}
    return {
        "pk": code, "code": code,
        "caption": {"text": f"text-{code}"},
        "user": {"username": username},
        "text_post_app_info": info,
    }


def test_drop_foreign_main_posts_removes_foreign_A_keeps_rest():
    main_author = "azuma"
    own_a = (_mk("azuma", "OWN1"), "A")
    foreign_a = (_mk("stranger", "FOR1"), "A")
    own_b = (_mk("azuma", "OWN2", is_reply=True, reply_to="azuma"), "B")
    foreign_d = (_mk("other", "OTH1", is_reply=True, reply_to="azuma"), "D")
    result = ftp.drop_foreign_main_posts(
        [own_a, foreign_a, own_b, foreign_d], main_author
    )
    assert own_a in result
    assert foreign_a not in result
    assert own_b in result
    assert foreign_d in result


def test_drop_foreign_main_posts_missing_user_dropped():
    ghost = ({"pk": "g", "code": "G1", "caption": {"text": "x"}, "user": {}}, "A")
    assert ftp.drop_foreign_main_posts([ghost], "azuma") == []
```

- [ ] **Step 2: 跑測試確認 FAIL**

Run: `python -m pytest tests/test_fetch_threads_post.py -k drop_foreign -v`
Expected: FAIL — `AttributeError: module 'fetch_threads_post' has no attribute 'drop_foreign_main_posts'`

- [ ] **Step 3: 實作純函式**

加在 `filter_by_flags`（`:138-149`）後面：

```python
def drop_foreign_main_posts(
    posts_with_class: list[tuple[dict, str]],
    main_author: str,
) -> list[tuple[dict, str]]:
    """Drop class-A nodes not authored by `main_author`.

    行動版頁面會載入「相關串文」推薦區塊，他人的頂層非回覆貼文會被
    classify 標成 A（見 test_classify_foreign_top_level_nonreply_returns_A）。
    這些不是主文，不應進入輸出與 counts/segments 統計。

    已知邊界（design D5 / Codex ③）：只擋「他人」A 段，擋不了「同作者但
    非本串」的推薦貼文。實測 8 條未觀察到此情形——本 step 先做 username
    過濾；code 錨定見 Step 3b 的 apply 時判斷。
    """
    return [
        (p, c)
        for p, c in posts_with_class
        if c != "A"
        or ((p.get("user") or {}).get("username") or "") == main_author
    ]
```

> **Step 3b（apply 時判斷，非阻斷）**：實作時檢查 walk_posts 抽出的節點是否帶可識別主串的欄位（如 thread root pk / permalink / 與 URL `code` 對應的 root code）。若有且成本低，把 A 段進一步限制在同一串以擋「同作者非本串」推薦；若 Relay 無此欄位，接受此邊界並在 design D5「已知邊界」下記一句「Relay 無 root 欄位，未加 code 錨定」。此判斷不阻斷 Task 3 完成。

- [ ] **Step 4: `main()` 接線——classify 之後、counts 之前**

`:314` 的 `classified = [...]` 之後插入：

```python
    classified = [(p, classify(p, username)) for p in posts]
    classified = drop_foreign_main_posts(classified, username)
```

（counts / segments / filtered 全部下游自動吃到過濾後的清單，統計不含污染節點。）

- [ ] **Step 5: 跑全套測試**

Run: `python -m pytest tests/test_fetch_threads_post.py -v`
Expected: 全 PASS

- [ ] **Step 6: Commit**

```bash
git add scripts/fetch_threads_post.py tests/test_fetch_threads_post.py
git commit -m "feat: drop foreign class-A posts (related-threads pollution guard)"
```

---

### Task 4: og meta 解析函式（extract_og_fields）

**Files:**
- Modify: `scripts/fetch_threads_post.py`（新純函式）
- Test: `tests/test_fetch_threads_post.py`

- [ ] **Step 1: 寫失敗測試**

```python
OG_FIXTURE = (
    '<html><head>'
    '<meta property="og:title" content="&#x6fa4;哥 (@lingyu9683) on Threads" />'
    '<meta property="og:description" content="&#x6700;近&#x7684;&#x8cbc;&#x6587;&#x5167;&#x6587; line1&#x0a;line2" />'
    '</head><body></body></html>'
)

# Codex ⑤：屬性順序反轉（content 在 property 前）+ 單引號，parser 須仍可解
OG_FIXTURE_REORDERED = (
    "<meta content='&#x6700;近&#x7684;&#x5167;&#x6587;' property='og:description'>"
)


def test_extract_og_fields_unescapes_entities():
    og = ftp.extract_og_fields(OG_FIXTURE)
    assert og is not None
    assert og["title"].startswith("澤哥")
    assert og["description"].startswith("最近的貼文內文 line1")


def test_extract_og_fields_attr_order_and_single_quotes():
    og = ftp.extract_og_fields(OG_FIXTURE_REORDERED)
    assert og is not None
    assert og["description"].startswith("最近的內文")


def test_extract_og_fields_missing_description_returns_none():
    assert ftp.extract_og_fields("<html><head></head></html>") is None
    assert (
        ftp.extract_og_fields(
            '<meta property="og:description" content="" />'
        )
        is None
    )
```

- [ ] **Step 2: 跑測試確認 FAIL**

Run: `python -m pytest tests/test_fetch_threads_post.py -k extract_og -v`
Expected: FAIL — no attribute `extract_og_fields`

- [ ] **Step 3: 實作**

模組頂部 import 區（`:13-18`）加 `import html as _html_lib`（避免與函式內 `html` 變數名衝突）。函式加在 `extract_relay_json` 後面。屬性順序無關解析（Codex ⑤）：逐個 `<meta>` tag 抽 `property=og:*` 與 `content=`，順序與單雙引號皆容忍。

```python
_META_TAG_RE = re.compile(r"<meta\b[^>]*>", re.IGNORECASE)
_OG_PROP_RE = re.compile(r"""property=["']og:(title|description)["']""", re.IGNORECASE)
_OG_CONTENT_RE = re.compile(r"""content=["'](.*?)["']""", re.IGNORECASE | re.DOTALL)


def extract_og_fields(html: str) -> dict | None:
    """Extract og:title / og:description from raw post-page HTML.

    og fallback 語意（design D2）：og:description 為必要欄位——缺失或空值
    回 None（表示連降級內容都沒有）。內容經 HTML entity unescape。
    屬性順序（property/content 誰在前）與單雙引號皆容忍（Codex ⑤）。
    注意：og:description 可能被 Threads 截斷（實測 ~150 字）且不含作者自串；
    author guard（是否採用 og）由 main() 依 og:title 判斷（design D7）。
    """
    found: dict[str, str] = {}
    for tag in _META_TAG_RE.findall(html):
        pm = _OG_PROP_RE.search(tag)
        cm = _OG_CONTENT_RE.search(tag)
        if pm and cm:
            found[pm.group(1).lower()] = _html_lib.unescape(cm.group(1))
    desc = found.get("description")
    if not desc:
        return None
    return {"title": found.get("title", ""), "description": desc}
```

- [ ] **Step 4: 跑測試確認 PASS**

Run: `python -m pytest tests/test_fetch_threads_post.py -k extract_og -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_threads_post.py tests/test_fetch_threads_post.py
git commit -m "feat: add og meta extraction for fallback channel"
```

---

### Task 5: og fallback HTTP 取回（fetch_og_fallback）+ partial 渲染（render_partial_markdown）

**Files:**
- Modify: `scripts/fetch_threads_post.py`
- Test: `tests/test_fetch_threads_post.py`（render 有測試；HTTP 函式依 D6 不自動測）

- [ ] **Step 1: 寫 render_partial_markdown 失敗測試**

```python
def test_render_partial_markdown_has_partial_frontmatter():
    og = {"title": "澤哥 (@lingyu9683) on Threads", "description": "內文摘要"}
    meta = {
        "author": "lingyu9683",
        "code": "DISnS0JJywN",
        "url": "https://www.threads.net/@lingyu9683/post/DISnS0JJywN",
        "fetched_at": "2026-07-05T12:00:00+00:00",
    }
    md = ftp.render_partial_markdown(og, meta)
    head, body = md.split("---\n", 2)[1], md.split("---\n", 2)[2]
    assert "partial: true" in head
    assert "author: lingyu9683" in head
    assert "內文摘要" in body
    assert "og fallback" in body
```

- [ ] **Step 2: 跑測試確認 FAIL**

Run: `python -m pytest tests/test_fetch_threads_post.py -k render_partial -v`
Expected: FAIL — no attribute `render_partial_markdown`

- [ ] **Step 3: 實作兩個函式**

加在 `render_markdown` 後面：

```python
def render_partial_markdown(og: dict, meta: dict) -> str:
    """Render a partial post.md from og fallback fields.

    Frontmatter 與完整版共用 author/code/url/fetched_at 四鍵，
    另加 `partial: true`（design D3）供下游辨識降級品質。
    """
    lines = ["---"]
    for key in ("author", "code", "url", "fetched_at"):
        lines.append(f"{key}: {meta[key]}")
    lines.append("partial: true")
    lines.append("---")
    lines.append("")
    lines.append(f"## [A] @{meta['author']} · {meta['code']} (og fallback)")
    lines.append("")
    lines.append(og["description"])
    lines.append("")
    return "\n".join(lines)
```

加在 `fetch_page` 後面：

```python
def fetch_og_fallback(url: str, timeout: float = 20.0) -> str | None:
    """Single anonymous HTTP GET with mobile UA; returns HTML or None on error.

    降級管道刻意不開 browser（design D2）：og meta 是伺服端渲染的 SEO
    資產，純 GET 即可取得；任何網路/HTTP 錯誤一律回 None，由呼叫端
    走既有 exit 2 路徑。
    """
    import urllib.error
    import urllib.request

    req = urllib.request.Request(url, headers={"User-Agent": MOBILE_UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.read().decode("utf-8", errors="replace")
    except (urllib.error.URLError, OSError, ValueError):
        return None
```

- [ ] **Step 4: 跑測試確認 PASS**

Run: `python -m pytest tests/test_fetch_threads_post.py -k render_partial -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_threads_post.py tests/test_fetch_threads_post.py
git commit -m "feat: add og fallback HTTP fetch and partial markdown renderer"
```

---

### Task 6: write_output 支援無 relay payload

**Files:**
- Modify: `scripts/fetch_threads_post.py:203-239`（`write_output`）
- Test: `tests/test_fetch_threads_post.py`

- [ ] **Step 1: 寫失敗測試**

```python
def test_write_output_none_relay_skips_relay_json(tmp_path):
    meta = {
        "author": "u1",
        "code": "C1",
        "url": "https://www.threads.net/@u1/post/C1",
        "fetched_at": "2026-07-05T12:00:00+00:00",
    }
    out = ftp.write_output(tmp_path, meta, "# md", None, None)
    assert (out / "post.md").exists()
    assert (out / "meta.json").exists()
    assert not (out / "relay.json").exists()
```

- [ ] **Step 2: 跑測試確認 FAIL**

Run: `python -m pytest tests/test_fetch_threads_post.py -k none_relay -v`
Expected: FAIL — `json.dumps(None)` 會寫出 `null` 的 relay.json，`not exists` 斷言失敗

- [ ] **Step 3: 改 `write_output`**

簽名改為 `relay_payload: dict | None`，relay.json 寫入段改為：

```python
    if relay_payload is not None:
        (out_dir / "relay.json").write_text(
            json.dumps(relay_payload, ensure_ascii=False),
            encoding="utf-8",
        )
```

（docstring B1 note 補一句："When `relay_payload` is None (og fallback), relay.json is omitted."）

- [ ] **Step 4: 跑全套測試**

Run: `python -m pytest tests/test_fetch_threads_post.py -v`
Expected: 全 PASS（既有 write_output 測試傳真 dict，不受影響）

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_threads_post.py tests/test_fetch_threads_post.py
git commit -m "feat: make relay.json optional in write_output for partial outputs"
```

---

### Task 7: main() 降級鏈接線 + exit code 三態

**Files:**
- Modify: `scripts/fetch_threads_post.py:295-308`（`main()` 的 `relay is None` 分支）
- Test: `tests/test_fetch_threads_post.py`（monkeypatch 網路函式）

- [ ] **Step 1: 寫失敗測試（monkeypatch fetch_page / fetch_og_fallback）**

```python
NO_RELAY_HTML = "<html><head></head><body>logged out feed</body></html>"


def test_main_og_fallback_exits_3(tmp_path, monkeypatch):
    monkeypatch.setattr(ftp, "fetch_page", lambda url, screenshot=True: (NO_RELAY_HTML, None))
    monkeypatch.setattr(ftp, "fetch_og_fallback", lambda url: OG_FIXTURE)
    rc = ftp.main([
        "https://www.threads.net/@lingyu9683/post/DISnS0JJywN",
        "--no-screenshot", "--out", str(tmp_path),
    ])
    assert rc == 3
    out_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and d.name != "_debug"]
    assert len(out_dirs) == 1
    meta = json.loads((out_dirs[0] / "meta.json").read_text(encoding="utf-8"))
    assert meta["fetch_mode"] == "og_fallback"
    assert "partial: true" in (out_dirs[0] / "post.md").read_text(encoding="utf-8")
    assert not (out_dirs[0] / "relay.json").exists()


def test_main_og_also_dead_exits_2_with_debug_dump(tmp_path, monkeypatch):
    monkeypatch.setattr(ftp, "fetch_page", lambda url, screenshot=True: (NO_RELAY_HTML, None))
    monkeypatch.setattr(ftp, "fetch_og_fallback", lambda url: None)
    rc = ftp.main([
        "https://www.threads.net/@lingyu9683/post/DISnS0JJywN",
        "--no-screenshot", "--out", str(tmp_path),
    ])
    assert rc == 2
    assert list((tmp_path / "_debug").glob("*_nomatch.html"))


# Codex ①：og 有內文但 title 不含 URL 作者（logged-out feed / 錯誤頁偽裝）→ exit 2，不產 partial
WRONG_AUTHOR_OG = (
    '<meta property="og:title" content="Threads" />'
    '<meta property="og:description" content="&#x767b;入以查看更多內容" />'
)


def test_main_og_wrong_author_exits_2_no_partial(tmp_path, monkeypatch):
    monkeypatch.setattr(ftp, "fetch_page", lambda url, screenshot=True: (NO_RELAY_HTML, None))
    monkeypatch.setattr(ftp, "fetch_og_fallback", lambda url: WRONG_AUTHOR_OG)
    rc = ftp.main([
        "https://www.threads.net/@lingyu9683/post/DISnS0JJywN",
        "--no-screenshot", "--out", str(tmp_path),
    ])
    assert rc == 2
    # author guard 擋下 → 不得產出 partial 目錄，走 debug dump
    out_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and d.name != "_debug"]
    assert out_dirs == []
    assert list((tmp_path / "_debug").glob("*_nomatch.html"))
```

（測試檔頂部若尚無 `import json`，補上。）

- [ ] **Step 2: 跑測試確認 FAIL**

Run: `python -m pytest tests/test_fetch_threads_post.py -k "og_fallback_exits or og_also_dead or og_wrong_author" -v`
Expected: `test_main_og_fallback_exits_3` FAIL（現行 relay None 直接 return 2）；`test_main_og_also_dead_exits_2_with_debug_dump` 與 `test_main_og_wrong_author_exits_2_no_partial` 可能已 PASS（既有 exit 2 行為）

- [ ] **Step 3: 改 `main()` 的 `relay is None` 分支**

`:295-308` 改為：

```python
    relay = extract_relay_json(html)
    if relay is None:
        # 降級鏈（design D2/D4/D7）：主管道拿不到 Relay → 試 og fallback。
        og_html = fetch_og_fallback(args.url)
        og = extract_og_fields(og_html) if og_html else None
        # D7 author guard：og:title 須含 (@url_author)，否則視為 logged-out
        # feed / 錯誤頁偽裝，不得產 partial（避免掩蓋主管道壞損信號）。
        if og is not None and f"(@{username})" in og.get("title", ""):
            meta = {
                "author": username,
                "code": code,
                "url": args.url,
                "fetched_at": datetime.datetime.now(datetime.UTC).isoformat(),
                "fetch_mode": "og_fallback",
                "og_title": og["title"],
            }
            md = render_partial_markdown(og, meta)
            out_dir = write_output(args.out, meta, md, None, shot)
            print(
                f"PARTIAL: relay unavailable, og fallback wrote {out_dir}",
                file=sys.stderr,
            )
            return 3
        # I4: Meta schema drift detection signal.（og 為 None 或未過 author
        # guard 皆落此）（以下既有 debug dump 區塊不動）
```

既有 debug dump 區塊（`debug_dir = ...` 到 `return 2`）原樣保留在後面。

- [ ] **Step 4: 跑全套測試**

Run: `python -m pytest tests/test_fetch_threads_post.py -v`
Expected: 全 PASS

- [ ] **Step 5: Commit**

```bash
git add scripts/fetch_threads_post.py tests/test_fetch_threads_post.py
git commit -m "feat: wire og fallback chain with 0/3/2 exit code contract"
```

---

### Task 8: 文件更新 + 手動 smoke

**Files:**
- Modify: `scripts/fetch_threads_post.py:1-10`（模組 docstring）
- Modify: `README.md`（若有 fetcher 段落；無則略過）

- [ ] **Step 1: 更新模組 docstring**

`:1-10` 的 docstring 改為：

```python
"""Fetch a Threads post + classified threads/replies via Playwright + Relay JSON.

Uses a mobile browser fingerprint (MOBILE_UA + is_mobile) — since 2026-07
Threads redirects anonymous *desktop* traffic to the logged-out feed.

Fallback chain: when Relay data is unavailable, a single anonymous HTTP GET
extracts og:title/og:description into a partial output (post.md frontmatter
`partial: true`, meta.json `fetch_mode: "og_fallback"`, no relay.json).

Exit codes: 0 = full success · 3 = partial (og fallback) · 2 = total failure
(HTML dumped to drafts/library/_debug/ for schema-drift inspection) · 1 = bad URL.
Callers (vault-side line-import / source-capture) can branch on exit code alone.
NOTE: vault-side runners must be taught exit 3 separately (migration note in
openspec/changes/fix-threads-fetcher/design.md §Migration Plan).

Prototype usage:

    pip install -e ".[dev,prototype]"
    playwright install chromium
    python scripts/fetch_threads_post.py "https://www.threads.com/@user/post/CODE"

Output: drafts/library/{YYYY-MM-DD}_{author}_{code}/{post.md, meta.json, relay.json, screenshot.png}
"""
```

- [ ] **Step 2: 檢查 README 是否提及 fetcher**

Run: `grep -n "fetch_threads_post" README.md`
若有命中：在該段補一句退出碼契約（0/3/2）與行動版指紋說明；無命中則跳過。

- [ ] **Step 3: 跑全套測試（最終回歸）**

Run: `python -m pytest tests/ -v`
Expected: 全 PASS（含官方 API 側測試零回歸）

- [ ] **Step 4: Commit**

```bash
git add scripts/fetch_threads_post.py README.md
git commit -m "docs: document mobile fingerprint, fallback chain and exit codes"
```

- [~] **Step 5（deferred，人工）: 真實 URL smoke 3-5 條**

從 vault `7、專案/LINE收藏搶救/state.json` 的 threads 條目抽 3-5 條不同型態（純文字、多圖、影片、含作者自串），逐條跑：

```bash
python scripts/fetch_threads_post.py "<url>" --no-screenshot --out drafts/library
echo "exit=$?"
```

檢查：exit 0、post.md A+B 段完整、無他人貼文混入 A 段、meta.json counts 合理。挑一條手動改壞 `_RELAY_QUERY_MARKER`（暫時）驗 partial 路徑後還原。此步為 live-environment 檢查，依 verify §7 規則記錄等效自動測試對照（exit 3 路徑已有 monkeypatch 測試覆蓋；行動版真頁面結構為真空窗，無等效自動測）。

---

## Self-Review 紀錄

- Spec coverage：spec 四條 Requirement ↔ Task 2（mobile fingerprint + 指紋契約測試）、Task 3（author filtering）、Task 4-7（og fallback + author guard + partial 輸出 + exit codes）、退出碼互斥 scenario ↔ Task 7 測試。✓
- Placeholder scan：無 TBD/TODO；所有測試與實作碼皆完整給出。✓
- Type consistency：`mobile_context_kwargs` / `drop_foreign_main_posts` / `extract_og_fields` / `fetch_og_fallback` / `render_partial_markdown` 簽名在 Task 2/3/4/5/7 間一致；`write_output(relay_payload=None)` 與 Task 6 修改對齊。✓
- Codex 修正落點：① author guard → Task 7 Step 3 + `test_main_og_wrong_author_exits_2_no_partial`；② exit code SHALL 措辭 → spec 已改「fetcher SHALL 回傳互斥退出碼」；③ 同作者邊界 → Task 3 Step 3b apply 判斷；④ 指紋契約可測 → Task 2 `mobile_context_kwargs` + 測試；⑤ og 正則放寬 → Task 4 屬性順序無關 + `test_extract_og_fields_attr_order_and_single_quotes`；⑥⑦ → design/spec 措辭已修。✓
