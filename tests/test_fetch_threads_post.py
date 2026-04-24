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
