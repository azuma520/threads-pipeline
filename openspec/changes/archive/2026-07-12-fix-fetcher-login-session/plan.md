# Fetcher 登入態修復 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `fetch_threads_post.py` 從匿名行動指紋抓取改為登入態 persistent-profile 抓取，新增登入失效偵測（exit 4）與 operational 失敗碼（exit 5），並徹底移除 og partial（exit 3 停用）。

**Architecture:** Relay 解析邏輯（walk/classify/render，~350 行）不動。改動集中在 browser 建立（匿名 launch → `launch_persistent_context` + 專用 profile）、指紋（棄行動 UA）、失效偵測（新 `detect_auth_failure` + `FetchResult` + exit 4）、operational 捕捉（exit 5）、og partial 移除。

**Tech Stack:** Python 3.13、Playwright（sync API，既有依賴）、pytest、argparse。

> 執行環境：所有指令從 `D:/threads-pipeline` 執行；測試 `python -m pytest tests/test_fetch_threads_post.py -v`。模組別名 `ftp`。**每個 commit 前跑完整測試檔**（不只篩選子集），確保無中間壞版本（Review Codex #7）。

> **本 plan 已納入 Codex gpt-5.6-sol 規劃審查 10 條修訂**（2026-07-12）。逐條對應見各 Task 標註。

---

### Task 1: 擴充 OG parser + 登入失效偵測 + FetchResult + os/profile 預設

**Files:**
- Modify: `scripts/fetch_threads_post.py`
- Test: `tests/test_fetch_threads_post.py`

> Review 修訂：#3（補 `import os`）、#5（用擴充 `_OGMetaParser` 而非弱 regex；補 og:url/登入表單訊號）、#1（不用首頁 path 判 auth）。

- [ ] **Step 1: 確認 import**

檔頂 import 區（`fetch_threads_post.py:26-33` 附近）確認並補齊：`import os`、`from dataclasses import dataclass`（若缺）。

- [ ] **Step 2: 寫失敗測試（擴充 OG parser 取 url）**

```python
def test_extract_og_meta_gets_url_and_title_without_description():
    html = ('<meta property="og:title" content="Threads • Log in" />'
            '<meta content="https://www.threads.com/" property="og:url">')
    og = ftp.extract_og_meta(html)  # 新函式：不要求 description
    assert og["title"] == "Threads • Log in"
    assert og["url"] == "https://www.threads.com/"
```

- [ ] **Step 3: 擴充 `_OGMetaParser` + 新增 `extract_og_meta`**

改 `_OGMetaParser.handle_starttag`（`fetch_threads_post.py:179-185`）納入 `og:url`，並新增不要求 description 的取值函式：

```python
    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        d = dict(attrs)
        prop = d.get("property", "")
        if prop in ("og:title", "og:description", "og:url") and d.get("content"):
            self.og[prop[len("og:"):]] = d["content"]


def extract_og_meta(html: str) -> dict:
    """Return og title/description/url (unescaped); missing keys omitted.

    與 extract_og_fields 不同：不把「缺 description」當 None——detect_auth_failure
    只需 title/url，登入牆頁面常無 description。沿用 _OGMetaParser 故容忍
    屬性順序與單雙引號（既有 test_extract_og_fields_* 契約）。
    """
    parser = _OGMetaParser()
    parser.feed(html)
    return {k: _html_lib.unescape(v) for k, v in parser.og.items()}
```

（`extract_og_fields` 維持原樣不動——它的 description-必要語意仍被既有測試依賴。）

- [ ] **Step 4: 跑測試確認通過**

Run: `python -m pytest tests/test_fetch_threads_post.py -k "extract_og" -v`
Expected: 既有 extract_og_fields 測試 + 新 extract_og_meta 全 passed

- [ ] **Step 5: 寫 detect_auth_failure 測試**

```python
def test_detect_auth_failure_login_title():
    html = '<meta property="og:title" content="Threads • Log in" />'
    assert ftp.detect_auth_failure("https://www.threads.com/@u/post/X", html) == "auth_required"

def test_detect_auth_failure_checkpoint_url():
    assert ftp.detect_auth_failure("https://www.threads.com/checkpoint/1", "<html></html>") == "auth_required"

def test_detect_auth_failure_login_url():
    assert ftp.detect_auth_failure("https://www.threads.com/login", "<html></html>") == "auth_required"

def test_detect_auth_failure_og_url_homepage_redirect():
    # 抓貼文卻被重導：og:url 指向首頁（需傳 requested_url 才觸發情境化訊號）
    html = '<meta property="og:url" content="https://www.threads.com/" />'
    url = "https://www.threads.com/@u/post/X"
    assert ftp.detect_auth_failure(url, html, requested_url=url) == "auth_required"

def test_detect_auth_failure_final_url_left_post():
    # 抓貼文但 final_url 已不含 code → 被重導離開
    html = "<html></html>"
    assert ftp.detect_auth_failure(
        "https://www.threads.com/somewhere", html,
        requested_url="https://www.threads.com/@u/post/ABC123") == "auth_required"

def test_detect_auth_failure_login_form():
    html = '<form><input type="password" name="pass"></form>'
    assert ftp.detect_auth_failure("https://www.threads.com/@u/post/X", html) == "auth_required"

def test_detect_auth_failure_normal_post_returns_none():
    url = "https://www.threads.com/@lingyu9683/post/DISnS0JJywN"
    html = ('<meta property="og:title" content="澤哥 (@lingyu9683) on Threads" />'
            f'<meta property="og:url" content="{url}" />')
    assert ftp.detect_auth_failure(url, html, requested_url=url) is None

def test_detect_auth_failure_logged_in_homepage_returns_none():
    # 關鍵回歸（Review C1）：auth-check goto 首頁，已登入首頁 og:url=首頁、無表單
    # requested_url=首頁（無 code）→ 情境化訊號不啟用 → None（不誤判）
    html = '<meta property="og:url" content="https://www.threads.com/" /><div>feed</div>'
    assert ftp.detect_auth_failure(
        "https://www.threads.com/", html, requested_url="https://www.threads.com/") is None

def test_detect_auth_failure_ignores_og_description_keyword():
    url = "https://www.threads.com/@u/post/X"
    html = ('<meta property="og:title" content="Threads" />'
            '<meta property="og:description" content="登入以查看更多內容" />'
            f'<meta property="og:url" content="{url}" />')
    assert ftp.detect_auth_failure(url, html, requested_url=url) is None
```

- [ ] **Step 6: 實作 detect_auth_failure**

在 `extract_og_meta` 後加入（**不含首頁 final-url path 判定**，Review #1）：

```python
import urllib.parse as _urlparse

_LOGIN_TITLE_RE = re.compile(r"log ?in|登入", re.IGNORECASE)
_AUTH_PATH_RE = re.compile(r"^/(login|checkpoint|challenge)(/|$)", re.IGNORECASE)
_LOGIN_FORM_RE = re.compile(r"""type=['"]password['"]|name=['"]password['"]""", re.IGNORECASE)
_THREADS_HOSTS = {"www.threads.com", "threads.com", "www.threads.net", "threads.net"}


def _is_threads_homepage(url: str) -> bool:
    p = _urlparse.urlparse(url)
    return p.netloc in _THREADS_HOSTS and (p.path or "/") == "/"


def detect_auth_failure(final_url: str, html: str, *, requested_url: str | None = None) -> str | None:
    """Return "auth_required" if the page is a login wall / checkpoint, else None.

    通用訊號（兩情境皆安全）：final URL 為 /login|/checkpoint|/challenge、
    og:title 登入字樣、頁面含登入表單。

    情境化訊號（僅當 requested_url 是「貼文」時啟用，Review C1/M1）：og:url 指向
    首頁、或 final_url 已不含 requested 貼文 code——代表抓貼文被重導離開。
    auth-check 模式 goto 首頁（requested 非貼文）**不**觸發這兩條，故已登入首頁
    （og:url=首頁、無表單）正確回 None，不誤判（Review C1）。

    刻意不採「final URL 落在首頁 path」與 og:description 關鍵字（Review #1）。
    """
    if _AUTH_PATH_RE.match(_urlparse.urlparse(final_url).path or "/"):
        return "auth_required"
    og = extract_og_meta(html)
    if _LOGIN_TITLE_RE.search(og.get("title", "")):
        return "auth_required"
    if _LOGIN_FORM_RE.search(html):
        return "auth_required"
    # 情境化：僅抓貼文（requested_url 可解析出 code）才把首頁重導視為 auth
    req_code = None
    if requested_url:
        try:
            _, req_code = parse_url(requested_url)
        except ValueError:
            req_code = None
    if req_code:
        if og.get("url") and _is_threads_homepage(og["url"]):
            return "auth_required"
        if req_code not in final_url:
            return "auth_required"
    return None
```

> `fetch_page` 抓貼文時呼叫 `detect_auth_failure(final_url, html, requested_url=url)`；auth-check goto 首頁時 requested_url=首頁（parse_url 無 code）→ 情境化訊號不啟用。

- [ ] **Step 7: 跑測試確認通過**

Run: `python -m pytest tests/test_fetch_threads_post.py -k "detect_auth_failure" -v`
Expected: 7 passed

- [ ] **Step 8: FetchResult + _default_profile_dir + 測試**

```python
def test_fetchresult_fields():
    r = ftp.FetchResult(html="<h1>x</h1>", screenshot=None,
                        final_url="https://www.threads.com/@u/post/X", auth_status="ok")
    assert r.html == "<h1>x</h1>" and r.auth_status == "ok"

def test_default_profile_dir_under_localappdata(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    p = ftp._default_profile_dir()
    assert p == tmp_path / "threads-pipeline" / "threads-profile"
```

實作（`fetch_page` 之前）：

```python
from typing import Literal  # 檔頂 import 區（Review M2）

@dataclass
class FetchResult:
    html: str
    screenshot: bytes | None
    final_url: str
    auth_status: Literal["ok", "auth_required"]  # 收窄型別，拼字錯誤不靜默落 ok


def _default_profile_dir() -> pathlib.Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return pathlib.Path(base) / "threads-pipeline" / "threads-profile"
```

- [ ] **Step 9: 跑完整測試檔 + commit**

Run: `python -m pytest tests/test_fetch_threads_post.py -v`
Expected: 全 passed（既有 + 新增，無中間壞版本）

```bash
git add scripts/fetch_threads_post.py tests/test_fetch_threads_post.py
git commit -m "feat(fetcher): og:url parser, detect_auth_failure, FetchResult, profile default"
```

---

### Task 2: persistent context + Relay 輪詢 + ProfileLock + 同步接 main

**Files:**
- Modify: `scripts/fetch_threads_post.py`
- Test: `tests/test_fetch_threads_post.py`

> Review 修訂：#7（同步接 main，profile_dir 給預設，每 commit 綠）、#8（Relay 輪詢非首個 data-sjs）、#6（operational 捕捉先鋪路）。

- [ ] **Step 1: 寫 authenticated_context_kwargs 測試**

```python
def test_authenticated_context_kwargs_no_mobile_spoof():
    kw = ftp.authenticated_context_kwargs()
    assert "user_agent" not in kw or "iPhone" not in kw.get("user_agent", "")
    assert kw.get("is_mobile") is not True
    assert kw.get("locale") == "zh-TW"
```

- [ ] **Step 2: 跑測試確認失敗 → 實作**

取代 `mobile_context_kwargs`（`fetch_threads_post.py:120-130`），刪除 `MOBILE_UA` 常數的偽裝用途（保留常數供 og fallback GET header，或一併移除——確認 `fetch_og_fallback` 是否還用；用則保留常數）：

```python
def authenticated_context_kwargs() -> dict:
    """Context kwargs for authenticated persistent-profile fetch (design D2).
    棄行動 UA 偽裝（登入態下跨引擎不一致＝風控訊號）；僅固定 locale/timezone。
    """
    return {"locale": "zh-TW", "timezone_id": "Asia/Taipei"}
```

**同步刪除舊匿名測試**（Review H4，不延後到 Task 5，否則本 Task commit 會 `AttributeError`）：移除 `tests/test_fetch_threads_post.py` 的 `test_mobile_context_kwargs_is_anonymous_mobile`（`test_fetch_threads_post.py:386-394`），因 `mobile_context_kwargs` 已被取代。

Run: `python -m pytest tests/test_fetch_threads_post.py -k authenticated_context -v` → passed
Run: `python -m pytest tests/test_fetch_threads_post.py -v` → 全綠（確認無殘留呼叫 mobile_context_kwargs）

- [ ] **Step 3: ProfileLock 測試 + 實作**

```python
def test_profile_lock_rejects_concurrent(tmp_path):
    import pytest
    ftp.ProfileLock(tmp_path).acquire()
    with pytest.raises(RuntimeError, match="in use"):
        ftp.ProfileLock(tmp_path).acquire()

def test_profile_lock_release_allows_reacquire(tmp_path):
    lock = ftp.ProfileLock(tmp_path); lock.acquire(); lock.release()
    ftp.ProfileLock(tmp_path).acquire()  # 不 raise
```

```python
class ProfileLock:
    """單實例鎖（design Risk）：lockfile 而非 Chromium SingletonLock（異常終止殘留）。"""
    def __init__(self, profile_dir: pathlib.Path):
        self._path = pathlib.Path(profile_dir) / ".threads_fetch.lock"

    def acquire(self) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with open(self._path, "x") as fd:
                fd.write(datetime.datetime.now(datetime.UTC).isoformat())
        except FileExistsError as exc:
            raise RuntimeError(
                f"profile {self._path.parent} in use (lock {self._path}); "
                f"確認無其他 fetcher 執行後手動刪除 lock 檔"
            ) from exc

    def release(self) -> None:
        self._path.unlink(missing_ok=True)
```

Run: `python -m pytest tests/test_fetch_threads_post.py -k profile_lock -v` → 2 passed

- [ ] **Step 4: 改 fetch_page 用 persistent context + Relay 輪詢，回 FetchResult**

取代 `fetch_page`（`fetch_threads_post.py:356-374`）。`profile_dir` 有預設值（Review #7，使 main 舊呼叫不立即壞）；Relay 等待改**輪詢 `extract_relay_json`**（Review #8）：

```python
def fetch_page(
    url: str,
    screenshot: bool = True,
    *,
    profile_dir: pathlib.Path | None = None,
    headless: bool = False,
) -> FetchResult:
    """Load `url` via authenticated persistent-profile chromium (design D1/D2)."""
    from playwright.sync_api import sync_playwright

    profile_dir = profile_dir or _default_profile_dir()
    lock = ProfileLock(profile_dir)
    lock.acquire()
    try:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(pathlib.Path(profile_dir).resolve()),
                headless=headless,
                **authenticated_context_kwargs(),
            )
            try:
                page = ctx.new_page()
                page.goto(url, wait_until="domcontentloaded", timeout=30_000)
                # Review #8：輪詢至 Relay payload 出現或逾時，不在首個 data-sjs 即擷取
                html = page.content()
                deadline = 8_000
                waited = 0
                while extract_relay_json(html) is None and waited < deadline:
                    page.wait_for_timeout(500)
                    waited += 500
                    html = page.content()
                final_url = page.url
                shot = page.screenshot(full_page=False) if screenshot else None
                auth = detect_auth_failure(final_url, html, requested_url=url) or "ok"
                return FetchResult(html=html, screenshot=shot,
                                   final_url=final_url, auth_status=auth)
            finally:
                ctx.close()
    finally:
        lock.release()
```

- [ ] **Step 5: 同步接 main 的 fetch_page 呼叫（避免中間壞版本，Review #7）**

改 `main` 中呼叫（`fetch_threads_post.py:426`）並解構 FetchResult；此步同時處理 auth exit 4（完整 CLI 在 Task 3，這裡先讓既有測試綠）：

```python
    result = fetch_page(args.url, screenshot=not args.no_screenshot)
    if result.auth_status == "auth_required":
        print("AUTH: login session invalid — re-run with --login", file=sys.stderr)
        return 4
    html, shot = result.html, result.screenshot
    relay = extract_relay_json(html)
```

同步更新既有 3 個 main 測試的 monkeypatch（tuple → FetchResult），確保本步測試綠：

```python
def _fake_fetch(url, screenshot=True, *, profile_dir=None, headless=False):
    return ftp.FetchResult(html=NO_RELAY_HTML, screenshot=None, final_url=url, auth_status="ok")
# 三個 test_main_og_* 的 monkeypatch.setattr(ftp, "fetch_page", _fake_fetch)
```

- [ ] **Step 6: 跑完整測試檔 + commit**

Run: `python -m pytest tests/test_fetch_threads_post.py -v`
Expected: 全 passed（含遷移後 main 測試）

```bash
git add scripts/fetch_threads_post.py tests/test_fetch_threads_post.py
git commit -m "feat(fetcher): persistent-profile fetch_page w/ relay poll, ProfileLock, drop mobile spoof"
```

---

### Task 3: CLI 參數（url 可選）+ exit 4/5 契約

**Files:**
- Modify: `scripts/fetch_threads_post.py`（`main` argparse + 例外捕捉）
- Test: `tests/test_fetch_threads_post.py`

> Review 修訂：#4（url `nargs="?"`）、#6（exit 5 operational 捕捉）。

- [ ] **Step 1: 寫測試（exit 4 auth、exit 5 profile 占用、url 可選）**

```python
LOGIN_WALL_HTML = '<meta property="og:title" content="Threads • Log in" />'

def test_main_auth_required_exits_4(tmp_path, monkeypatch):
    def _fake(url, screenshot=True, *, profile_dir=None, headless=False):
        return ftp.FetchResult(html=LOGIN_WALL_HTML, screenshot=None,
                               final_url="https://www.threads.com/@u/post/X", auth_status="auth_required")
    monkeypatch.setattr(ftp, "fetch_page", _fake)
    rc = ftp.main(["https://www.threads.net/@u/post/X", "--no-screenshot",
                   "--out", str(tmp_path), "--profile", str(tmp_path / "p")])
    assert rc == 4
    assert not (tmp_path / "_debug").exists()

def test_main_operational_failure_exits_5(tmp_path, monkeypatch):
    def _boom(*a, **k):
        raise RuntimeError("profile ... in use")
    monkeypatch.setattr(ftp, "fetch_page", _boom)
    rc = ftp.main(["https://www.threads.net/@u/post/X", "--no-screenshot",
                   "--out", str(tmp_path), "--profile", str(tmp_path / "p")])
    assert rc == 5

def test_main_missing_url_general_mode_exits_1(tmp_path):
    rc = ftp.main(["--no-screenshot", "--out", str(tmp_path)])
    assert rc == 1

def test_main_unknown_flag_exits_1(tmp_path):
    # Review H3：argparse usage error 不得用預設 SystemExit(2)（撞內容失敗碼）
    rc = ftp.main(["--no-such-flag"])
    assert rc == 1

def test_main_login_and_authcheck_conflict_exits_1(tmp_path):
    # 複審 Medium：兩模式旗標互斥，同時給 → exit 1（非靜默選 login）
    rc = ftp.main(["--login", "--auth-check-only", "--profile", str(tmp_path / "p")])
    assert rc == 1
```

- [ ] **Step 2: 跑測試確認失敗 → 實作 argparse override + main wrapper**

先把 `main` 拆為 wrapper（Review H2/H3）：argparse usage error 映射 exit 1、最外層統一捕捉 operational（涵蓋 login/fetch/output/debug 全部 I/O，不只 fetch）。既有 `main(argv)` 主體改名為 `_run(argv)`，新增：

```python
class _ArgParser(argparse.ArgumentParser):
    def error(self, message):                      # Review H3
        print(f"ERROR: {message}", file=sys.stderr)
        raise SystemExit(1)                        # 非預設的 SystemExit(2)


def main(argv: list[str] | None = None) -> int:    # Review H2：最外層 operational 網
    # 複審 High：只捕捉「界定的 operational 例外」——ProfileLock 占用(RuntimeError)、
    # I/O(OSError)、瀏覽器引擎錯誤(PlaywrightError)。TypeError/KeyError/AssertionError
    # 等程式缺陷不得偽裝成 exit 5（否則測試假綠、真 bug 被藏）。
    try:
        from playwright.sync_api import Error as PlaywrightError
    except ImportError:
        PlaywrightError = ()
    try:
        return _run(argv)
    except SystemExit as exc:                       # argparse error(1) 等
        return exc.code if isinstance(exc.code, int) else 1
    except (RuntimeError, OSError, PlaywrightError) as exc:
        print(f"OPERATIONAL: {exc}", file=sys.stderr); return 5
```

`_run` 內用 `_ArgParser`（取代 `argparse.ArgumentParser`），`url` 改可選、新增旗標（`fetch_threads_post.py:399-416`）：

```python
    ap = _ArgParser(description="Fetch a Threads post ...")
    ap.add_argument("url", nargs="?", help="Threads post URL (omit for --login/--auth-check-only)")
    # ...既有 --include-replies / --include-self-replies / --no-screenshot / --out...
    ap.add_argument("--profile", type=pathlib.Path, default=_default_profile_dir(),
                    help="Persistent browser profile dir (login session)")
    ap.add_argument("--headless", action="store_true", help="Run headless (default headed)")
    ap.add_argument("--debug-dump", action="store_true", help="On content failure, dump HTML to _debug")
    # 複審 Medium：--login 與 --auth-check-only 互斥，同時給 → argparse error → exit 1
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument("--login", action="store_true", help="Headed login to init profile; no fetch")
    mode.add_argument("--auth-check-only", action="store_true", help="Verify session (0 ok / 4 need login)")
    args = ap.parse_args(argv)
```

一般模式缺 URL → exit 1（在 parse_url 前）：

```python
    if not args.login and not args.auth_check_only and not args.url:
        print("ERROR: url required (or use --login / --auth-check-only)", file=sys.stderr)
        return 1
```

`_run` 內的 `fetch_page(...)` 呼叫**不**需自己包 try/except——operational 例外統一由上面的 `main` wrapper 捕捉轉 exit 5（Review H2，涵蓋 login/fetch/output/debug）。把 Task 2 Step 5 臨時加在 main 的 auth 檢查改為傳入 profile/headless：

```python
    result = fetch_page(args.url, screenshot=not args.no_screenshot,
                        profile_dir=args.profile, headless=args.headless)
    if result.auth_status == "auth_required":
        print("AUTH: login session invalid — re-run with --login", file=sys.stderr)
        return 4
    html, shot = result.html, result.screenshot
```

- [ ] **Step 3: 跑完整測試檔 + commit**

Run: `python -m pytest tests/test_fetch_threads_post.py -v`
Expected: 全 passed

```bash
git add scripts/fetch_threads_post.py tests/test_fetch_threads_post.py
git commit -m "feat(fetcher): optional url + exit 4/5 contract (auth + operational)"
```

---

### Task 4: --login / --auth-check-only 早退 + og partial 移除 + debug 旗標

**Files:**
- Modify: `scripts/fetch_threads_post.py`
- Test: `tests/test_fetch_threads_post.py`

> Review 修訂：#2（og partial 徹底移除）、#1（auth-check 用登入表單非首頁 URL）、#10（debug dump 旗標）。

- [ ] **Step 1: 寫測試（--login 不抓、auth-check、og partial 已移除）**

```python
def test_main_login_does_not_fetch(tmp_path, monkeypatch):
    monkeypatch.setattr(ftp, "fetch_page", lambda *a, **k: (_ for _ in ()).throw(AssertionError("no fetch")))
    monkeypatch.setattr(ftp, "run_login", lambda profile_dir: 0)
    assert ftp.main(["--login", "--profile", str(tmp_path / "p")]) == 0

def test_main_auth_check_logged_in_exits_0(tmp_path, monkeypatch):
    # 已登入首頁：無登入表單 → 0
    def _fake(url, screenshot=True, *, profile_dir=None, headless=False):
        return ftp.FetchResult(html="<div>feed</div>", final_url="https://www.threads.com/",
                               screenshot=None, auth_status="ok")
    monkeypatch.setattr(ftp, "fetch_page", _fake)
    assert ftp.main(["--auth-check-only", "--profile", str(tmp_path / "p")]) == 0

def test_main_auth_check_logged_out_exits_4(tmp_path, monkeypatch):
    def _fake(url, screenshot=True, *, profile_dir=None, headless=False):
        return ftp.FetchResult(html='<input type="password">', final_url="https://www.threads.com/",
                               screenshot=None, auth_status="auth_required")
    monkeypatch.setattr(ftp, "fetch_page", _fake)
    assert ftp.main(["--auth-check-only", "--profile", str(tmp_path / "p")]) == 4
```

改寫既有 `test_main_og_fallback_exits_3`（Review #2）為「不產 partial」：

```python
def test_main_og_no_longer_produces_partial(tmp_path, monkeypatch):
    # relay 失敗 + og 過舊 author guard：不再產 partial，走 exit 2（非登入牆）
    def _fake(url, screenshot=True, *, profile_dir=None, headless=False):
        return ftp.FetchResult(html=NO_RELAY_HTML, final_url=url, screenshot=None, auth_status="ok")
    monkeypatch.setattr(ftp, "fetch_page", _fake)
    monkeypatch.setattr(ftp, "fetch_og_fallback", lambda url: OG_FIXTURE)
    rc = ftp.main(["https://www.threads.net/@lingyu9683/post/DISnS0JJywN",
                   "--no-screenshot", "--out", str(tmp_path), "--profile", str(tmp_path / "p")])
    assert rc == 2
    out_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and d.name not in ("_debug", "p")]
    assert out_dirs == []  # 無 partial 目錄

def test_main_og_fallback_login_wall_exits_4(tmp_path, monkeypatch):
    # 複審 R4 High：og fallback 僅 og:url 首頁（無 title/form）→ 需情境化訊號 → exit 4
    def _fake(url, screenshot=True, *, profile_dir=None, headless=False):
        return ftp.FetchResult(html=NO_RELAY_HTML, final_url=url, screenshot=None, auth_status="ok")
    monkeypatch.setattr(ftp, "fetch_page", _fake)
    monkeypatch.setattr(ftp, "fetch_og_fallback",
                        lambda url: '<meta property="og:url" content="https://www.threads.com/" />')
    rc = ftp.main(["https://www.threads.net/@u/post/ABC123",
                   "--no-screenshot", "--out", str(tmp_path), "--profile", str(tmp_path / "p")])
    assert rc == 4
```

- [ ] **Step 2: 跑測試確認失敗 → 實作 run_login + 早退**

`run_login`（單測 monkeypatch，dogfood 實跑）：

```python
def run_login(profile_dir: pathlib.Path) -> int:
    from playwright.sync_api import sync_playwright
    lock = ProfileLock(profile_dir); lock.acquire()
    try:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(pathlib.Path(profile_dir).resolve()),
                headless=False, **authenticated_context_kwargs())
            try:
                ctx.new_page().goto("https://www.threads.com/login", wait_until="domcontentloaded")
                print("在瀏覽器完成登入（含 2FA），完成後回終端按 Enter...", file=sys.stderr)
                input()
                return 0
            finally:
                ctx.close()
    finally:
        lock.release()
```

`main` 解析 args 後、缺 URL 檢查後插入早退：

```python
    if args.login:
        return run_login(args.profile)   # operational 例外由 main wrapper 捕捉（Review H2）
    if args.auth_check_only:
        # goto 首頁：requested_url 無 code → detector 情境化訊號不啟用，
        # 已登入首頁（og:url=首頁、無表單）正確回 ok（Review C1）
        result = fetch_page("https://www.threads.com/", screenshot=False,
                            profile_dir=args.profile, headless=args.headless)
        rc = 4 if result.auth_status == "auth_required" else 0
        print(f"AUTH-CHECK: {'need login' if rc else 'session ok'}", file=sys.stderr)
        return rc
```

- [ ] **Step 3: 移除 og partial 路徑 + debug dump 改旗標**

改 relay 失敗分支（`fetch_threads_post.py:429-463`）：刪 exit-3 partial（`render_partial_markdown`/`write_output` partial 呼叫），登入牆 og → exit 4，其餘 → exit 2（dump 僅 `--debug-dump` 時）：

```python
    relay = extract_relay_json(html)
    if relay is None:
        og_html = fetch_og_fallback(args.url)
        # 複審 R4 High：必須傳 requested_url，否則 og:url 首頁的情境化訊號不啟用，
        # 「僅 og:url 首頁」的登入牆會錯回 exit 2 而非 exit 4
        if og_html and detect_auth_failure(args.url, og_html, requested_url=args.url) == "auth_required":
            print("AUTH: anonymous og shows login wall — re-run with --login", file=sys.stderr)
            return 4
        if args.debug_dump:
            debug_dir = args.out / "_debug"; debug_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
            (debug_dir / f"{ts}_{code}_nomatch.html").write_text(html[:500_000], encoding="utf-8")
        print(f"ERROR: no {_RELAY_QUERY_MARKER} in HTML (use --debug-dump to inspect)", file=sys.stderr)
        return 2
```

`render_partial_markdown` 函式本體可留（不再被呼叫）或刪；若刪需一併移除其測試。優先**刪函式與其測試**保持 DRY，確認無其他呼叫點：`grep -n render_partial_markdown scripts/ tests/`。

- [ ] **Step 4: 跑完整測試檔 + commit**

Run: `python -m pytest tests/test_fetch_threads_post.py -v`
Expected: 全 passed

```bash
git add scripts/fetch_threads_post.py tests/test_fetch_threads_post.py
git commit -m "feat(fetcher): --login/--auth-check early-exit, remove og partial, gate debug dump"
```

---

### Task 5: 清理殘留 + 文件同步

**Files:**
- Modify: `tests/test_fetch_threads_post.py`、`README.md`、`CLAUDE.md`

- [ ] **Step 1: 刪殘留匿名測試 + 確認無孤兒引用**

移除 `test_mobile_context_kwargs_is_anonymous_mobile`。
Run: `grep -rn "mobile_context_kwargs\|render_partial_markdown\|def main.*exits_3" scripts/ tests/`
Expected: 無殘留呼叫（僅可能的 deprecated alias，一併清）

- [ ] **Step 2: 跑完整測試檔**

Run: `python -m pytest tests/test_fetch_threads_post.py -v` → 全 passed

- [ ] **Step 3: 更新文件**

`CLAUDE.md` Project Structure 補 `scripts/fetch_threads_post.py` + `tests/test_fetch_threads_post.py`；新增「Fetcher 登入態」段：`--login` 建 profile、`--auth-check-only` 驗證、預設 headed、exit code 表（0 成功 / 4 需登入 / 2 內容失敗 / 1 參數錯 / 5 operational）。README 同步 CLI 用法。

- [ ] **Step 4: commit**

```bash
git add tests/test_fetch_threads_post.py README.md CLAUDE.md
git commit -m "docs+test: drop anonymous remnants, document login-session CLI + exit codes"
```

---

### Task 6: 使用者 dogfood 實測（apply 末，需使用者在場）

> 需真實 Threads 帳號與瀏覽器，無法單測——標 dogfood。verify.md §7 對照此處與自動測試等價性。

- [ ] **Step 1: 建 profile** — `python scripts/fetch_threads_post.py --login --profile "$LOCALAPPDATA/threads-pipeline/threads-profile"`，在瀏覽器登入（含 2FA）按 Enter。
- [ ] **Step 2: 驗 session** — `python scripts/fetch_threads_post.py --auth-check-only`，Expected exit 0 `session ok`。
- [ ] **Step 3: 單條真實抓取** — 用已知存活貼文（如 `@leen_0622`）headed 抓取，確認 `post.md` 含主帖 + 作者自回覆（B 段），exit 0。
- [ ] **Step 4: 驗 exit 4 熔斷** — 空白 profile 目錄抓取 → 登入牆 → exit 4，不產出、不 dump。
- [ ] **Step 5: 驗 exit 5** — 同 profile 併發啟動第二個 fetcher → exit 5（profile in use）。
