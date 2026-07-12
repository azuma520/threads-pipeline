"""Unit tests for scripts/fetch_threads_post.py pure functions."""
from __future__ import annotations

import json
import pathlib
import sys

import pytest

# script 不在 package，走路徑 import
_ROOT = pathlib.Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

import fetch_threads_post as ftp  # noqa: E402  # pyright: ignore[reportMissingImports]


class TestParseUrl:
    def test_standard_com_url(self):
        assert ftp.parse_url(
            "https://www.threads.com/@kanisleo328/post/DXO2PlPEoOQ"
        ) == ("kanisleo328", "DXO2PlPEoOQ")

    def test_threads_net_domain(self):
        assert ftp.parse_url(
            "https://www.threads.net/@user_name/post/ABC123"
        ) == ("user_name", "ABC123")

    def test_with_query_string(self):
        assert ftp.parse_url(
            "https://www.threads.com/@foo.bar/post/XYZ?igsh=abc"
        ) == ("foo.bar", "XYZ")

    def test_invalid_raises(self):
        with pytest.raises(ValueError):
            ftp.parse_url("https://example.com/not-threads")


class TestClassify:
    MAIN = "kanisleo328"

    def _mk(self, is_reply, author, reply_to=None):
        # Schema 實測：is_reply / reply_to_author 皆巢在 text_post_app_info 裡。
        info = {"is_reply": is_reply}
        if reply_to:
            info["reply_to_author"] = {"username": reply_to}
        return {
            "user": {"username": author},
            "text_post_app_info": info,
        }

    def test_a_main_post(self):
        assert ftp.classify(self._mk(False, self.MAIN), self.MAIN) == "A"

    def test_b_author_thread_extension(self):
        assert ftp.classify(self._mk(True, self.MAIN, self.MAIN), self.MAIN) == "B"

    def test_c_author_replies_commenter(self):
        assert ftp.classify(self._mk(True, self.MAIN, "someone_else"), self.MAIN) == "C"

    def test_d_other_user_top_level_reply(self):
        assert ftp.classify(self._mk(True, "bob", self.MAIN), self.MAIN) == "D"

    def test_e_deep_reply(self):
        assert ftp.classify(self._mk(True, "bob", "alice"), self.MAIN) == "E"

    def test_missing_reply_to_author_treated_as_e(self):
        # is_reply=True but no reply_to_author → cannot classify → E
        post = {
            "user": {"username": "bob"},
            "text_post_app_info": {"is_reply": True},
        }
        assert ftp.classify(post, self.MAIN) == "E"

    def test_missing_is_reply_key_treated_as_a(self):
        # I5: commit to prototype behavior — absent is_reply → "A"（與明文 False 同）。
        # 包含 text_post_app_info 不存在、或存在但缺 is_reply 兩種情境。
        assert ftp.classify({"user": {"username": self.MAIN}}, self.MAIN) == "A"
        assert ftp.classify(
            {"user": {"username": self.MAIN}, "text_post_app_info": {}},
            self.MAIN,
        ) == "A"


_FIXTURE = _ROOT / "tests" / "fixtures" / "relay_kanisleo_DXO2PlPEoOQ.json"


class TestWalkPosts:
    def _post_node(self, code, is_reply=False):
        # 實測 Threads Relay post 形狀：pk + code + caption(dict) + user(dict)
        # + text_post_app_info(巢 is_reply / reply_to_author)。
        return {
            "pk": f"pk_{code}",
            "code": code,
            "caption": {"text": f"hello {code}"},
            "user": {"username": "u"},
            "text_post_app_info": {"is_reply": is_reply},
        }

    def test_flat_list(self):
        data = {"posts": [self._post_node("c1")]}
        assert len(ftp.walk_posts(data)) == 1

    def test_nested_deeply(self):
        data = {"a": {"b": {"c": [self._post_node("c1"), self._post_node("c2")]}}}
        found = ftp.walk_posts(data)
        assert {p["code"] for p in found} == {"c1", "c2"}

    def test_rejects_non_post_nodes(self):
        data = {"caption": "just a string", "user": "not-a-dict"}
        assert ftp.walk_posts(data) == []

    def test_handles_list_at_root(self):
        data = [self._post_node("c1"), {"unrelated": 1}]
        assert len(ftp.walk_posts(data)) == 1

    def test_rejects_node_without_pk(self):
        # I1: guard against false positives. Threads 的 preview / quoted reference
        # 有時以相似 shape 嵌入但缺 pk（post primary key）。缺 pk 視為非真 post。
        node_without_pk = {
            "code": "preview",
            "caption": {"text": "preview text"},
            "user": {"username": "u"},
            # 刻意缺 pk
        }
        assert ftp.walk_posts({"x": node_without_pk}) == []

    def test_includes_nested_post_with_pk(self):
        # I1: 貼文 A 內嵌 quoted_post（也帶 pk）時，外層和內層都應取。
        main = self._post_node("outer", is_reply=False)
        quoted = self._post_node("quoted", is_reply=False)
        main["quoted_post"] = quoted
        found = ftp.walk_posts(main)
        assert {p["code"] for p in found} == {"outer", "quoted"}

    @pytest.mark.skipif(not _FIXTURE.exists(), reason="real Relay fixture missing; run Task 0 Step 6")
    def test_real_fixture_yields_at_least_12_posts(self):
        # I2: schema-drift regression anchor. Handoff 18:07-D 驗證 @kanisleo328/post/DXO2PlPEoOQ
        # 共 12 個 post code。若 Meta 改欄位名（如 is_reply / caption / user）此 test 首先紅燈。
        data = json.loads(_FIXTURE.read_text(encoding="utf-8"))
        found = ftp.walk_posts(data)
        codes = {p.get("code") for p in found if p.get("code")}
        assert len(codes) >= 12, f"expected ≥12 unique codes, got {len(codes)}"


class TestExtractRelayJson:
    # 含 1 個 post-shaped node（pk + code + caption + user 四件齊），walk_posts 計數 = 1
    _POST_NODE = (
        '{"pk":"pk_c1","code":"c1","caption":{"text":"x"},"user":{"username":"u"},'
        '"text_post_app_info":{"is_reply":false}}'
    )
    # 含 2 個 post-shaped node（main + quoted），walk_posts 計數 = 2
    _TWO_POSTS = (
        '{"main":{"pk":"pk_c1","code":"c1","caption":{"text":"x"},"user":{"username":"u"},'
        '"text_post_app_info":{"is_reply":false},'
        '"quoted_post":{"pk":"pk_c2","code":"c2","caption":{"text":"y"},"user":{"username":"v"},'
        '"text_post_app_info":{"is_reply":false}}}}'
    )

    def test_finds_barcelona_query(self):
        # 唯一 marker script，回傳那份。
        html = (
            '<html><body>'
            '<script type="application/json" data-sjs>{"other":"data"}</script>'
            '<script type="application/json" data-sjs>'
            '{"require":[["foo","bar"]],"marker":"BarcelonaPostPageDirectQuery",'
            f'"data":{self._POST_NODE}}}'
            '</script>'
            '</body></html>'
        )
        result = ftp.extract_relay_json(html)
        assert result is not None
        assert result["marker"] == "BarcelonaPostPageDirectQuery"

    def test_picks_script_with_most_post_nodes(self):
        html = (
            '<html><body>'
            '<script type="application/json" data-sjs>'
            '{"id":"A","note":"BarcelonaPostPageDirectQuery metadata only"}'
            '</script>'
            '<script type="application/json" data-sjs>'
            f'{{"id":"B","marker":"BarcelonaPostPageDirectQuery","d":{self._POST_NODE}}}'
            '</script>'
            '<script type="application/json" data-sjs>'
            f'{{"id":"C","marker":"BarcelonaPostPageDirectQuery","d":{self._TWO_POSTS}}}'
            '</script>'
            '</body></html>'
        )
        result = ftp.extract_relay_json(html)
        assert result is not None
        assert result["id"] == "C"

    def test_returns_none_when_absent(self):
        html = '<html><body><script>nothing</script></body></html>'
        assert ftp.extract_relay_json(html) is None

    def test_skips_scripts_with_invalid_json(self):
        html = (
            '<html><body>'
            '<script type="application/json" data-sjs>not json BarcelonaPostPageDirectQuery</script>'
            '<script type="application/json" data-sjs>'
            f'{{"marker":"BarcelonaPostPageDirectQuery","d":{self._POST_NODE}}}'
            '</script>'
            '</body></html>'
        )
        result = ftp.extract_relay_json(html)
        assert result is not None
        assert result["marker"] == "BarcelonaPostPageDirectQuery"

    def test_attributes_in_reversed_order(self):
        # I3
        html = (
            '<html><body>'
            '<script data-sjs data-content-len="123" type="application/json">'
            f'{{"marker":"BarcelonaPostPageDirectQuery","payload":42,"d":{self._POST_NODE}}}'
            '</script>'
            '</body></html>'
        )
        result = ftp.extract_relay_json(html)
        assert result is not None
        assert result["payload"] == 42

    def test_returns_none_when_marker_present_but_no_posts(self):
        html = (
            '<html><body>'
            '<script type="application/json" data-sjs>'
            '{"id":"A","note":"BarcelonaPostPageDirectQuery metadata only"}'
            '</script>'
            '<script type="application/json" data-sjs>'
            '{"id":"B","note":"BarcelonaPostPageDirectQuery another ref"}'
            '</script>'
            '</body></html>'
        )
        assert ftp.extract_relay_json(html) is None

    def test_ignores_data_sjs_without_json_type(self):
        html = (
            '<html><body>'
            '<script data-sjs type="text/javascript">'
            'window.x = {"marker":"BarcelonaPostPageDirectQuery"};'
            '</script>'
            '</body></html>'
        )
        assert ftp.extract_relay_json(html) is None


class TestFilterByFlags:
    ITEMS = [
        ({"code": "a1"}, "A"),
        ({"code": "b1"}, "B"),
        ({"code": "c1"}, "C"),
        ({"code": "d1"}, "D"),
        ({"code": "e1"}, "E"),
    ]

    def test_default_keeps_a_b_only(self):
        out = ftp.filter_by_flags(self.ITEMS, include_replies=False, include_self_replies=False)
        assert [p["code"] for p, _ in out] == ["a1", "b1"]

    def test_include_replies_adds_d(self):
        out = ftp.filter_by_flags(self.ITEMS, include_replies=True, include_self_replies=False)
        assert [p["code"] for p, _ in out] == ["a1", "b1", "d1"]

    def test_include_self_replies_adds_c(self):
        out = ftp.filter_by_flags(self.ITEMS, include_replies=False, include_self_replies=True)
        assert [p["code"] for p, _ in out] == ["a1", "b1", "c1"]

    def test_e_is_always_dropped(self):
        out = ftp.filter_by_flags(self.ITEMS, include_replies=True, include_self_replies=True)
        assert all(cls != "E" for _, cls in out)


class TestRenderMarkdown:
    META = {
        "author": "foo",
        "code": "c1",
        "url": "https://www.threads.com/@foo/post/c1",
        "fetched_at": "2026-04-24T10:00:00+00:00",
    }

    def _p(self, code, text, ts, username="foo"):
        return {
            "code": code,
            "caption": {"text": text},
            "user": {"username": username},
            "taken_at": ts,
        }

    def test_includes_frontmatter(self):
        md = ftp.render_markdown([(self._p("c1", "hello", 100), "A")], self.META)
        assert md.startswith("---\n")
        assert "author: foo" in md
        assert "code: c1" in md

    def test_groups_by_class_order_a_b_c_d(self):
        items = [
            (self._p("d1", "other reply", 300, username="bob"), "D"),
            (self._p("b1", "author thread", 200), "B"),
            (self._p("a1", "main", 100), "A"),
        ]
        md = ftp.render_markdown(items, self.META)
        a_pos = md.index("[A]")
        b_pos = md.index("[B]")
        d_pos = md.index("[D]")
        assert a_pos < b_pos < d_pos

    def test_orders_by_taken_at_within_class(self):
        items = [
            (self._p("b2", "second", 200), "B"),
            (self._p("b1", "first", 100), "B"),
        ]
        md = ftp.render_markdown(items, self.META)
        assert md.index("first") < md.index("second")

    def test_handles_missing_caption_text(self):
        item = ({"code": "x", "caption": {}, "user": {"username": "foo"}, "taken_at": 1}, "A")
        md = ftp.render_markdown([item], self.META)
        assert "[A] @foo" in md  # does not crash, renders empty body


class TestWriteOutput:
    META = {
        "author": "foo",
        "code": "c1",
        "url": "https://www.threads.com/@foo/post/c1",
        "fetched_at": "2026-04-24T10:00:00+00:00",
        "counts": {"A": 1, "B": 0, "C": 0, "D": 0, "E": 0},
        "kept": 1,
        "segments": [
            {"code": "c1", "class": "A", "author": "foo", "taken_at": 100},
        ],
    }

    def test_writes_all_four_files(self, tmp_path):
        out = ftp.write_output(
            tmp_path, self.META, "# md body", {"relay": "payload"}, b"png-bytes"
        )
        assert out.parent == tmp_path
        assert out.name == "2026-04-24_foo_c1"
        assert (out / "post.md").read_text(encoding="utf-8") == "# md body"
        assert (out / "screenshot.png").read_bytes() == b"png-bytes"

        meta_parsed = json.loads((out / "meta.json").read_text(encoding="utf-8"))
        assert meta_parsed["author"] == "foo"
        assert meta_parsed["segments"][0]["class"] == "A"
        # B1: relay raw payload MUST NOT leak into meta.json
        assert "relay" not in meta_parsed

        relay_parsed = json.loads((out / "relay.json").read_text(encoding="utf-8"))
        assert relay_parsed == {"relay": "payload"}

    def test_skips_screenshot_when_none(self, tmp_path):
        out = ftp.write_output(tmp_path, self.META, "# x", {}, None)
        assert not (out / "screenshot.png").exists()
        # 仍要寫 post.md、meta.json、relay.json
        assert (out / "post.md").exists()
        assert (out / "meta.json").exists()
        assert (out / "relay.json").exists()

    def test_creates_parent_dirs(self, tmp_path):
        nested = tmp_path / "a" / "b"
        out = ftp.write_output(nested, self.META, "# x", {}, None)
        assert out.parent == nested
        assert (out / "post.md").exists()

    def test_relay_json_can_be_empty_dict(self, tmp_path):
        out = ftp.write_output(tmp_path, self.META, "# x", {}, None)
        assert json.loads((out / "relay.json").read_text(encoding="utf-8")) == {}


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


def test_authenticated_context_kwargs_no_mobile_spoof():
    kw = ftp.authenticated_context_kwargs()
    assert "user_agent" not in kw or "iPhone" not in kw.get("user_agent", "")
    assert kw.get("is_mobile") is not True
    assert kw.get("locale") == "zh-TW"


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


def test_extract_og_fields_content_with_ascii_single_quote():
    og = ftp.extract_og_fields(
        '<meta property="og:description" content="Don\'t miss this (@u) post" />'
    )
    assert og is not None
    assert og["description"] == "Don't miss this (@u) post"


def test_extract_og_fields_content_with_gt_char():
    og = ftp.extract_og_fields(
        '<meta property="og:description" content="a > b comparison" />'
    )
    assert og is not None
    assert og["description"] == "a > b comparison"


def test_extract_og_meta_gets_url_and_title_without_description():
    html = ('<meta property="og:title" content="Threads • Log in" />'
            '<meta content="https://www.threads.com/" property="og:url">')
    og = ftp.extract_og_meta(html)  # 新函式：不要求 description
    assert og["title"] == "Threads • Log in"
    assert og["url"] == "https://www.threads.com/"


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


def test_detect_auth_failure_logged_in_homepage_static_login_ogtitle_returns_none():
    # dogfood 實證回歸：已登入首頁 og:title 仍是「Threads • 登入」（靜態 crawler tag）
    # 但帶非零 NON_FACEBOOK_USER_ID → 不得誤判
    html = ('<meta property="og:title" content="Threads • 登入" />'
            '<script>{"NON_FACEBOOK_USER_ID":"17841464204254967"}</script>')
    assert ftp.detect_auth_failure(
        "https://www.threads.com/", html, requested_url="https://www.threads.com/") is None


def test_detect_auth_failure_anonymous_homepage_zero_viewer_id_exits_auth():
    # 匿名首頁：NON_FACEBOOK_USER_ID 為 "0" → 正向訊號不啟用 → og:title 登入照常觸發
    html = ('<meta property="og:title" content="Threads • 登入" />'
            '<script>{"NON_FACEBOOK_USER_ID":"0"}</script>')
    assert ftp.detect_auth_failure("https://www.threads.com/", html) == "auth_required"


def test_detect_auth_failure_checkpoint_overrides_viewer_id():
    # checkpoint/challenge 優先於正向訊號：已登入但被挑戰仍要 auth_required
    html = '<script>{"NON_FACEBOOK_USER_ID":"17841464204254967"}</script>'
    assert ftp.detect_auth_failure("https://www.threads.com/checkpoint/1", html) == "auth_required"


def test_detect_auth_failure_ig_user_eimu_variant_returns_none():
    html = ('<meta property="og:title" content="Threads • Log in" />'
            '<script>{"IG_USER_EIMU":"17841464204254967"}</script>')
    assert ftp.detect_auth_failure(
        "https://www.threads.com/@u/post/X", html) is None


def test_fetchresult_fields():
    r = ftp.FetchResult(html="<h1>x</h1>", screenshot=None,
                        final_url="https://www.threads.com/@u/post/X", auth_status="ok")
    assert r.html == "<h1>x</h1>" and r.auth_status == "ok"


def test_default_profile_dir_under_localappdata(monkeypatch, tmp_path):
    monkeypatch.setenv("LOCALAPPDATA", str(tmp_path))
    p = ftp._default_profile_dir()
    assert p == tmp_path / "threads-pipeline" / "threads-profile"


def test_profile_lock_rejects_concurrent(tmp_path):
    ftp.ProfileLock(tmp_path).acquire()
    with pytest.raises(RuntimeError, match="in use"):
        ftp.ProfileLock(tmp_path).acquire()


def test_profile_lock_release_allows_reacquire(tmp_path):
    lock = ftp.ProfileLock(tmp_path)
    lock.acquire()
    lock.release()
    ftp.ProfileLock(tmp_path).acquire()  # 不 raise


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


NO_RELAY_HTML = "<html><head></head><body>logged out feed</body></html>"


def _fake_fetch(url, screenshot=True, *, profile_dir=None, headless=False):
    return ftp.FetchResult(html=NO_RELAY_HTML, screenshot=None, final_url=url, auth_status="ok")


def test_main_og_no_longer_produces_partial(tmp_path, monkeypatch):
    # Task 4: og fallback 不再產 partial（品質太差不可信）。relay 失敗 +
    # og 有內文但非登入牆 → exit 2，且完全不建立輸出目錄。
    monkeypatch.setattr(ftp, "fetch_page", _fake_fetch)
    monkeypatch.setattr(ftp, "fetch_og_fallback", lambda url: OG_FIXTURE)
    rc = ftp.main([
        "https://www.threads.net/@lingyu9683/post/DISnS0JJywN",
        "--no-screenshot", "--out", str(tmp_path), "--profile", str(tmp_path / "p"),
    ])
    assert rc == 2
    out_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and d.name not in ("_debug", "p")]
    assert out_dirs == []  # 無 partial 目錄


def test_main_og_fallback_login_wall_exits_4(tmp_path, monkeypatch):
    # og fallback 僅 og:url 首頁（無 title/form）→ 需情境化訊號（requested_url）
    # 才判為登入牆 → exit 4
    monkeypatch.setattr(ftp, "fetch_page", _fake_fetch)
    monkeypatch.setattr(
        ftp, "fetch_og_fallback",
        lambda url: '<meta property="og:url" content="https://www.threads.com/" />',
    )
    rc = ftp.main([
        "https://www.threads.net/@lingyu9683/post/DISnS0JJywN",
        "--no-screenshot", "--out", str(tmp_path), "--profile", str(tmp_path / "p"),
    ])
    assert rc == 4
    out_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and d.name not in ("_debug", "p")]
    assert out_dirs == []


def test_main_og_also_dead_exits_2_with_debug_dump(tmp_path, monkeypatch):
    # --debug-dump 有給時，relay+og 皆失敗要落 debug html
    monkeypatch.setattr(ftp, "fetch_page", _fake_fetch)
    monkeypatch.setattr(ftp, "fetch_og_fallback", lambda url: None)
    rc = ftp.main([
        "https://www.threads.net/@lingyu9683/post/DISnS0JJywN",
        "--no-screenshot", "--out", str(tmp_path), "--profile", str(tmp_path / "p"),
        "--debug-dump",
    ])
    assert rc == 2
    assert list((tmp_path / "_debug").glob("*_nomatch.html"))


def test_main_debug_dump_off_by_default_no_debug_file(tmp_path, monkeypatch):
    # Task 4: debug dump 改 gated——不給 --debug-dump 時，即使內容失敗也不得寫檔
    monkeypatch.setattr(ftp, "fetch_page", _fake_fetch)
    monkeypatch.setattr(ftp, "fetch_og_fallback", lambda url: None)
    rc = ftp.main([
        "https://www.threads.net/@lingyu9683/post/DISnS0JJywN",
        "--no-screenshot", "--out", str(tmp_path), "--profile", str(tmp_path / "p"),
    ])
    assert rc == 2
    assert not (tmp_path / "_debug").exists()


# og 有內文但不是登入牆（也不含明確作者/貼文訊號）→ 落一般失敗 exit 2，不產 partial
WRONG_AUTHOR_OG = (
    '<meta property="og:title" content="Threads" />'
    '<meta property="og:description" content="&#x767b;入以查看更多內容" />'
)


def test_main_og_non_login_wall_content_exits_2_no_partial(tmp_path, monkeypatch):
    monkeypatch.setattr(ftp, "fetch_page", _fake_fetch)
    monkeypatch.setattr(ftp, "fetch_og_fallback", lambda url: WRONG_AUTHOR_OG)
    rc = ftp.main([
        "https://www.threads.net/@lingyu9683/post/DISnS0JJywN",
        "--no-screenshot", "--out", str(tmp_path), "--profile", str(tmp_path / "p"),
    ])
    assert rc == 2
    # og 內容判不出登入牆 → 不得產出 partial 目錄（partial 已徹底移除）
    out_dirs = [d for d in tmp_path.iterdir() if d.is_dir() and d.name not in ("_debug", "p")]
    assert out_dirs == []


# --- Task 3: CLI 契約（url 可選 + exit 4/5） ---

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


def test_main_operational_failure_exits_5_without_playwright(tmp_path, monkeypatch):
    # playwright 缺席（ImportError fallback 路徑）時 operational 例外仍須回 5，
    # 不得因 except tuple 含非例外物件而 TypeError crash。
    monkeypatch.setitem(sys.modules, "playwright.sync_api", None)  # 強制 import 失敗

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
    # argparse usage error 不得用預設 SystemExit(2)（撞內容失敗碼）
    rc = ftp.main(["--no-such-flag"])
    assert rc == 1


def test_main_login_and_authcheck_conflict_exits_1(tmp_path):
    # 兩模式旗標互斥，同時給 → exit 1（非靜默選 login）
    rc = ftp.main(["--login", "--auth-check-only", "--profile", str(tmp_path / "p")])
    assert rc == 1


# --- Task 4: --login / --auth-check-only 真行為 ---


def test_main_login_does_not_fetch(tmp_path, monkeypatch):
    monkeypatch.setattr(
        ftp, "fetch_page",
        lambda *a, **k: (_ for _ in ()).throw(AssertionError("no fetch")),
    )
    monkeypatch.setattr(ftp, "run_login", lambda profile_dir: 0)
    assert ftp.main(["--login", "--profile", str(tmp_path / "p")]) == 0


def test_main_login_operational_failure_exits_5(tmp_path, monkeypatch):
    # --login 路徑的 operational 例外（e.g. profile lock）也須經 main wrapper 轉 5，
    # 不只是一般抓取路徑（見 test_main_operational_failure_exits_5）。
    def _boom(profile_dir):
        raise RuntimeError("locked")
    monkeypatch.setattr(ftp, "run_login", _boom)
    assert ftp.main(["--login", "--profile", str(tmp_path / "p")]) == 5


def test_main_auth_check_logged_in_exits_0(tmp_path, monkeypatch):
    # 已登入首頁：無登入表單 → 0
    def _fake(url, screenshot=True, *, profile_dir=None, headless=False):
        return ftp.FetchResult(
            html="<div>feed</div>", final_url="https://www.threads.com/",
            screenshot=None, auth_status="ok",
        )
    monkeypatch.setattr(ftp, "fetch_page", _fake)
    assert ftp.main(["--auth-check-only", "--profile", str(tmp_path / "p")]) == 0


def test_main_auth_check_logged_out_exits_4(tmp_path, monkeypatch):
    def _fake(url, screenshot=True, *, profile_dir=None, headless=False):
        return ftp.FetchResult(
            html='<input type="password">', final_url="https://www.threads.com/",
            screenshot=None, auth_status="auth_required",
        )
    monkeypatch.setattr(ftp, "fetch_page", _fake)
    assert ftp.main(["--auth-check-only", "--profile", str(tmp_path / "p")]) == 4
