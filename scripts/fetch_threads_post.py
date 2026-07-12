"""Fetch a Threads post + classified threads/replies via Playwright + Relay JSON.

Main path uses an authenticated persistent-profile Chromium context (no mobile
UA spoof) — since 2026-07 Threads redirects anonymous *desktop* traffic to the
logged-out feed, so fetches rely on a logged-in browser profile instead.

Fallback chain: when Relay data is unavailable, a single anonymous HTTP GET
fetches og meta only to check for a login wall (no partial output is ever
produced — og fallback content is too degraded to trust; see Task 4).

Exit codes: 0 = full success · 2 = total failure (HTML optionally dumped to
drafts/library/_debug/ via --debug-dump for schema-drift inspection) ·
1 = bad args (bad URL, missing URL, unknown/conflicting flags — argparse usage
errors included) · 4 = auth required (login session invalid/missing, detected
either from the main fetch or from the anonymous og fallback) ·
5 = operational failure (profile lock in use, I/O error, browser engine error —
NOT a stand-in for programming bugs like TypeError/KeyError/AssertionError).
Callers (vault-side line-import / source-capture) can branch on exit code alone.

Prototype usage:

    pip install -e ".[dev,prototype]"
    playwright install chromium
    python scripts/fetch_threads_post.py "https://www.threads.com/@user/post/CODE"

Output: drafts/library/{YYYY-MM-DD}_{author}_{code}/{post.md, meta.json, relay.json, screenshot.png}
"""
from __future__ import annotations

import argparse
import datetime
import html as _html_lib
import json
import os
import pathlib
import re
import sys
import urllib.parse as _urlparse
from dataclasses import dataclass
from html.parser import HTMLParser
from typing import Literal


_URL_RE = re.compile(
    r"threads\.(?:com|net)/@([\w.-]+)/post/([A-Za-z0-9_-]+)"
)


def parse_url(url: str) -> tuple[str, str]:
    """Return (username, code) extracted from a Threads post URL.

    Raises ValueError when the URL does not match the expected shape.
    """
    m = _URL_RE.search(url)
    if not m:
        raise ValueError(f"Not a Threads post URL: {url}")
    return m.group(1), m.group(2)


def classify(post: dict, main_author: str) -> str:
    """Classify a Relay post node into A/B/C/D/E.

    Schema: `is_reply` and `reply_to_author` are nested inside
    `post["text_post_app_info"]` in real Threads Relay payloads.

    A: main post (is_reply is False / missing)
    B: author-thread-extension — is_reply, author == main, reply_to == main
    C: author-replies-to-commenter — is_reply, author == main, reply_to != main
    D: other-user top-level reply — is_reply, author != main, reply_to == main
    E: deep reply / unknown — everything else
    """
    info = post.get("text_post_app_info") or {}
    if not info.get("is_reply"):
        return "A"
    author = (post.get("user") or {}).get("username") or ""
    reply_to_obj = info.get("reply_to_author") or {}
    reply_to = reply_to_obj.get("username") or ""
    if author == main_author and reply_to == main_author:
        return "B"
    if author == main_author and reply_to != main_author:
        return "C"
    if author != main_author and reply_to == main_author:
        return "D"
    return "E"


def walk_posts(data) -> list[dict]:
    """Recursively collect post-like dicts from a parsed Relay JSON blob.

    A node qualifies as a post only if it's a dict containing **all four** keys:
    `pk` (post primary key), `code`, `caption` (dict), `user` (dict). The `pk`
    requirement (I1) guards against preview/reference fragments that share the
    other three keys but do not carry the post PK — those would otherwise
    classify as false "A" main posts.

    Does not dedupe — callers handle that via `{p["code"]: p for p in ...}`
    because the same post can appear under multiple Relay query results.
    """
    found: list[dict] = []

    def _walk(node):
        if isinstance(node, dict):
            if (
                "pk" in node
                and "code" in node
                and isinstance(node.get("caption"), dict)
                and isinstance(node.get("user"), dict)
            ):
                found.append(node)
            for v in node.values():
                _walk(v)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    _walk(data)
    return found


# 2026-07-05 起 Threads 對桌面匿名流量一律導向 logged-out feed。主抓取路徑已改用
# 登入態 persistent context（見 authenticated_context_kwargs），不再靠行動 UA 偽裝；
# 本常數僅供 fetch_og_fallback 的匿名 HTTP GET 使用。
MOBILE_UA = (
    "Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1"
)


def authenticated_context_kwargs() -> dict:
    """Context kwargs for authenticated persistent-profile fetch (design D2).

    棄行動 UA 偽裝（登入態下跨引擎不一致＝風控訊號）；僅固定 locale/timezone。
    """
    return {"locale": "zh-TW", "timezone_id": "Asia/Taipei"}


_RELAY_QUERY_MARKER = "BarcelonaPostPageDirectQuery"
# I3: 匹配任何含 data-sjs 屬性的 <script>；屬性順序由 runtime 檢查以相容 Meta 變動。
_SCRIPT_RE = re.compile(
    r'<script([^>]*\bdata-sjs\b[^>]*)>(.*?)</script>',
    re.DOTALL,
)


def extract_relay_json(html: str) -> dict | None:
    """Return the parsed JSON of the `<script data-sjs>` whose content contains
    the Relay query marker and yields the **most post-shaped nodes** when walked.

    Implementation note: Threads 頁面通常有 7 支 script 都含 marker（query 定義、
    cache reference、metadata、實際結果），只有其中一支是實際查詢結果並內含
    post records。不可取「第一個含 marker」——必須對所有 candidate 跑
    `walk_posts` 計數，取最大。

    Accepts `data-sjs` attribute in any order relative to `type=` (I3). Requires
    both `data-sjs` **and** `type="application/json"`. Returns None if no marker
    script parses or all parsed scripts yield 0 post-shaped nodes.
    """
    best: dict | None = None
    best_count = 0
    for match in _SCRIPT_RE.finditer(html):
        attrs = match.group(1)
        if 'type="application/json"' not in attrs:
            continue
        payload = match.group(2)
        if _RELAY_QUERY_MARKER not in payload:
            continue
        try:
            parsed = json.loads(payload)
        except json.JSONDecodeError:
            continue
        count = len(walk_posts(parsed))
        if count > best_count:
            best = parsed
            best_count = count
    return best


class _OGMetaParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.og: dict[str, str] = {}

    def handle_starttag(self, tag, attrs):
        if tag != "meta":
            return
        d = dict(attrs)
        prop = d.get("property", "")
        if prop in ("og:title", "og:description", "og:url") and d.get("content"):
            self.og[prop[len("og:"):]] = d["content"]


def extract_og_fields(html: str) -> dict | None:
    """Extract og:title / og:description from raw post-page HTML.

    og fallback 語意（design D2）：og:description 為必要欄位——缺失或空值
    回 None（表示連降級內容都沒有）。內容經 HTML entity unescape。
    屬性順序（property/content 誰在前）與單雙引號皆容忍（Codex ⑤）；用
    stdlib html.parser 解析，故 content 內含 ASCII 單引號或 `>` 亦不截斷。
    注意：og:description 可能被 Threads 截斷（實測 ~150 字）且不含作者自串；
    author guard（是否採用 og）由 main() 依 og:title 判斷（design D7）。
    """
    parser = _OGMetaParser()
    parser.feed(html)
    desc = parser.og.get("description")
    if not desc:
        return None
    return {
        "title": _html_lib.unescape(parser.og.get("title", "")),
        "description": _html_lib.unescape(desc),
    }


def extract_og_meta(html: str) -> dict:
    """Return og title/description/url (unescaped); missing keys omitted.

    與 extract_og_fields 不同：不把「缺 description」當 None——detect_auth_failure
    只需 title/url，登入牆頁面常無 description。沿用 _OGMetaParser 故容忍
    屬性順序與單雙引號（既有 test_extract_og_fields_* 契約）。
    """
    parser = _OGMetaParser()
    parser.feed(html)
    return {k: _html_lib.unescape(v) for k, v in parser.og.items()}


_LOGIN_TITLE_RE = re.compile(r"log ?in|登入", re.IGNORECASE)
_AUTH_PATH_RE = re.compile(r"^/(login|checkpoint|challenge)(/|$)", re.IGNORECASE)
_LOGIN_FORM_RE = re.compile(r"""type=['\"]password['\"]|name=['\"]password['\"]""", re.IGNORECASE)
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


def filter_by_flags(
    posts_with_class: list[tuple[dict, str]],
    include_replies: bool,
    include_self_replies: bool,
) -> list[tuple[dict, str]]:
    """Filter classified posts. Default keeps A + B only. E is always dropped."""
    kept = {"A", "B"}
    if include_replies:
        kept.add("D")
    if include_self_replies:
        kept.add("C")
    return [(p, c) for p, c in posts_with_class if c in kept]


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


def _extract_snippet(post: dict) -> str:
    """Extract long-form text from snippet_attachment_info if present.

    Threads stores extended text in text_post_app_info.snippet_attachment_info.
    text_fragments.fragments[].plaintext. Returns concatenated plaintext or "".
    """
    info = (post.get("text_post_app_info") or {})
    snippet = info.get("snippet_attachment_info") or {}
    frags = (snippet.get("text_fragments") or {}).get("fragments") or []
    return "".join(f.get("plaintext", "") for f in frags)


def render_markdown(
    posts_with_class: list[tuple[dict, str]],
    meta: dict,
) -> str:
    """Render a markdown document with YAML frontmatter + sections per class.

    Sections appear in A -> B -> C -> D order; E is ignored. Within a section,
    posts are sorted by `taken_at` ascending.
    """
    lines = ["---"]
    for key in ("author", "code", "url", "fetched_at"):
        lines.append(f"{key}: {meta[key]}")
    lines.append("---")
    lines.append("")

    by_class: dict[str, list[dict]] = {"A": [], "B": [], "C": [], "D": []}
    for p, c in posts_with_class:
        if c in by_class:
            by_class[c].append(p)

    for cls in ("A", "B", "C", "D"):
        for p in sorted(by_class[cls], key=lambda q: q.get("taken_at") or 0):
            username = (p.get("user") or {}).get("username", "")
            code = p.get("code", "")
            body = (p.get("caption") or {}).get("text", "") or ""
            snippet = _extract_snippet(p)
            lines.append(f"## [{cls}] @{username} · {code}")
            lines.append("")
            lines.append(body)
            if snippet:
                lines.append("")
                lines.append("---")
                lines.append("")
                lines.append(snippet)
            lines.append("")

    return "\n".join(lines)


def write_output(
    out_root: pathlib.Path,
    meta: dict,
    markdown: str,
    relay_payload: dict | None,
    screenshot: bytes | None,
) -> pathlib.Path:
    """Write post.md / meta.json / relay.json / screenshot.png into
    `out_root/{date}_{author}_{code}/`.

    Returns the directory path. `fetched_at` must be an ISO 8601 timestamp
    whose first 10 chars form the date prefix.

    B1 note: meta.json contains the summary only (author/code/url/fetched_at/
    counts/kept/segments). The raw Relay payload is written to `relay.json` as
    a sibling, keeping meta.json human-readable and small. When `relay_payload`
    is None, relay.json is omitted (covered by unit tests).
    """
    date = meta["fetched_at"][:10]
    out_dir = out_root / f"{date}_{meta['author']}_{meta['code']}"
    out_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / "post.md").write_text(markdown, encoding="utf-8")

    (out_dir / "meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    if relay_payload is not None:
        (out_dir / "relay.json").write_text(
            json.dumps(relay_payload, ensure_ascii=False),
            encoding="utf-8",
        )

    if screenshot:
        (out_dir / "screenshot.png").write_bytes(screenshot)

    return out_dir


@dataclass
class FetchResult:
    html: str
    screenshot: bytes | None
    final_url: str
    auth_status: Literal["ok", "auth_required"]  # 收窄型別，拼字錯誤不靜默落 ok


def _default_profile_dir() -> pathlib.Path:
    base = os.environ.get("LOCALAPPDATA") or os.path.expanduser("~")
    return pathlib.Path(base) / "threads-pipeline" / "threads-profile"


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
                # 輪詢至 Relay payload 出現或逾時，不在首個 data-sjs 即擷取
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


def run_login(profile_dir: pathlib.Path) -> int:
    """Headed login flow: open the persistent profile at /login and wait for
    the user to complete auth (incl. 2FA) before closing the context.

    No fetch happens here — this only seeds/refreshes the browser profile's
    cookies so later `fetch_page` calls run authenticated (design D1/D2).
    """
    from playwright.sync_api import sync_playwright

    lock = ProfileLock(profile_dir)
    lock.acquire()
    try:
        with sync_playwright() as p:
            ctx = p.chromium.launch_persistent_context(
                user_data_dir=str(pathlib.Path(profile_dir).resolve()),
                headless=False,
                **authenticated_context_kwargs(),
            )
            try:
                ctx.new_page().goto("https://www.threads.com/login", wait_until="domcontentloaded")
                print("在瀏覽器完成登入（含 2FA），完成後回終端按 Enter...", file=sys.stderr)
                input()
                return 0
            finally:
                ctx.close()
    finally:
        lock.release()


class _ArgParser(argparse.ArgumentParser):
    """argparse usage error → exit 1（不得沿用預設 SystemExit(2)，會撞內容失敗碼）。"""

    def error(self, message):
        self.print_usage(sys.stderr)
        print(f"ERROR: {message}", file=sys.stderr)
        raise SystemExit(1)


def main(argv: list[str] | None = None) -> int:
    """Wrapper：把「界定的 operational 例外」統一轉 exit 5，argparse usage error 轉 exit 1。

    只捕捉 ProfileLock 占用(RuntimeError)、I/O(OSError)、瀏覽器引擎錯誤(PlaywrightError)。
    TypeError/KeyError/AssertionError 等程式缺陷不得偽裝成 exit 5（否則測試假綠、真 bug 被藏）。
    """
    try:
        from playwright.sync_api import Error as PlaywrightError
    except ImportError:
        # playwright 缺席時的 dummy：永遠不會被 raise，僅讓 except tuple 合法。
        # 不可用空 tuple——except (..., ()) 會在 catch 時拋 TypeError，
        # operational 例外反而 crash 而非回 exit 5。
        class PlaywrightError(Exception):  # type: ignore[no-redef]
            pass

    try:
        return _run(argv)
    except SystemExit as exc:
        return exc.code if isinstance(exc.code, int) else 1
    except (RuntimeError, OSError, PlaywrightError) as exc:
        print(f"OPERATIONAL: {exc}", file=sys.stderr)
        return 5


def _run(argv: list[str] | None = None) -> int:
    ap = _ArgParser(
        description="Fetch a Threads post + classified threads/replies into drafts/library/"
    )
    ap.add_argument(
        "url",
        nargs="?",
        help="Threads post URL (https://www.threads.com/@user/post/CODE); "
        "omit for --login/--auth-check-only",
    )
    ap.add_argument(
        "--include-replies",
        action="store_true",
        help="Include other users' top-level replies (class D)",
    )
    ap.add_argument(
        "--include-self-replies",
        action="store_true",
        help="Include author's replies to commenters (class C)",
    )
    ap.add_argument("--no-screenshot", action="store_true", help="Skip page screenshot")
    ap.add_argument(
        "--out",
        type=pathlib.Path,
        default=pathlib.Path("drafts/library"),
        help="Output root (default: drafts/library)",
    )
    ap.add_argument(
        "--profile",
        type=pathlib.Path,
        default=_default_profile_dir(),
        help="Persistent browser profile dir (login session)",
    )
    ap.add_argument("--headless", action="store_true", help="Run headless (default headed)")
    ap.add_argument(
        "--debug-dump",
        action="store_true",
        help="On content failure, dump HTML to _debug",
    )
    mode = ap.add_mutually_exclusive_group()
    mode.add_argument(
        "--login", action="store_true", help="Headed login to init profile; no fetch"
    )
    mode.add_argument(
        "--auth-check-only",
        action="store_true",
        help="Verify session (0 ok / 4 need login)",
    )
    args = ap.parse_args(argv)

    if not args.login and not args.auth_check_only and not args.url:
        print("ERROR: url required (or use --login / --auth-check-only)", file=sys.stderr)
        return 1

    if args.login:
        return run_login(args.profile)   # operational 例外由 main wrapper 捕捉
    if args.auth_check_only:
        # goto 首頁：requested_url 無 code → detector 情境化訊號不啟用，
        # 已登入首頁（og:url=首頁、無表單）正確回 ok
        result = fetch_page(
            "https://www.threads.com/", screenshot=False,
            profile_dir=args.profile, headless=args.headless,
        )
        rc = 4 if result.auth_status == "auth_required" else 0
        print(f"AUTH-CHECK: {'need login' if rc else 'session ok'}", file=sys.stderr)
        return rc

    try:
        username, code = parse_url(args.url)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    print(f"Fetching {args.url} ...", file=sys.stderr)
    result = fetch_page(
        args.url,
        screenshot=not args.no_screenshot,
        profile_dir=args.profile,
        headless=args.headless,
    )
    if result.auth_status == "auth_required":
        print("AUTH: login session invalid — re-run with --login", file=sys.stderr)
        return 4
    html, shot = result.html, result.screenshot

    relay = extract_relay_json(html)
    if relay is None:
        # 降級鏈（design D2/D4）：主管道拿不到 Relay → 試 og fallback，
        # 僅用來偵測「連匿名 og 都看到登入牆」——不再產 partial 輸出（Task 4）。
        og_html = fetch_og_fallback(args.url)
        # 必須傳 requested_url，否則 og:url 首頁的情境化訊號不啟用，
        # 「僅 og:url 首頁」的登入牆會錯回 exit 2 而非 exit 4。
        # 注意：這裡 final_url 等同 requested_url（urllib GET 不追蹤 redirect
        # 後的實際 URL，final_url 參數直接吃 args.url）——故 _AUTH_PATH_RE
        # 與「req_code not in final_url」這兩條路徑訊號在本分支天然 inert，
        # 實際判斷靠 og:title 登入字樣 / og:url 首頁 / 登入表單這三條訊號。
        if og_html and detect_auth_failure(args.url, og_html, requested_url=args.url) == "auth_required":
            print("AUTH: anonymous og shows login wall — re-run with --login", file=sys.stderr)
            return 4
        # I4: Meta schema drift detection signal（僅 --debug-dump 時落檔）。
        if args.debug_dump:
            debug_dir = args.out / "_debug"
            debug_dir.mkdir(parents=True, exist_ok=True)
            ts = datetime.datetime.now(datetime.UTC).strftime("%Y%m%dT%H%M%SZ")
            debug_file = debug_dir / f"{ts}_{code}_nomatch.html"
            debug_file.write_text(html[:500_000], encoding="utf-8")
        print(
            f"ERROR: no {_RELAY_QUERY_MARKER} in HTML (use --debug-dump to inspect)",
            file=sys.stderr,
        )
        return 2

    raw_posts = walk_posts(relay)
    deduped = {p["code"]: p for p in raw_posts if p.get("code")}
    posts = list(deduped.values())

    classified = [(p, classify(p, username)) for p in posts]
    classified = drop_foreign_main_posts(classified, username)
    filtered = filter_by_flags(
        classified,
        include_replies=args.include_replies,
        include_self_replies=args.include_self_replies,
    )

    counts = {c: sum(1 for _, cc in classified if cc == c) for c in "ABCDE"}
    # B1 / D7: segments 摘要取代把整份 Relay 塞進 meta.json 的舊設計。
    segments = [
        {
            "code": p.get("code"),
            "class": c,
            "author": (p.get("user") or {}).get("username"),
            "taken_at": p.get("taken_at"),
        }
        for p, c in classified
    ]
    meta = {
        "author": username,
        "code": code,
        "url": args.url,
        "fetched_at": datetime.datetime.now(datetime.UTC).isoformat(),
        "counts": counts,
        "kept": len(filtered),
        "segments": segments,
    }

    md = render_markdown(filtered, meta)
    out_dir = write_output(args.out, meta, md, relay, shot)
    print(
        f"Wrote {out_dir} (total: {len(posts)}, kept: {len(filtered)}, counts: {counts})",
        file=sys.stderr,
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
