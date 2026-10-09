"""オフラインで動くテスト: python3 -m unittest -v (projects/poster で実行)"""
import contextlib
import io
import os
import tempfile
import unittest
from unittest import mock

import ad
import poster
import postqueue
import threadsapi
import xapi
from errors import PostError


class QueueTest(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        postqueue.write(self.path, ["# コメント", "", "一本目\\n改行", "二本目"])

    def tearDown(self):
        os.unlink(self.path)

    def test_pop_skips_comments_and_blank(self):
        text, rest = postqueue.pop(self.path)
        self.assertEqual(text, "一本目\\n改行")
        self.assertEqual(rest, ["# コメント", "", "二本目"])
        self.assertEqual(postqueue.decode(text), "一本目\n改行")

    def test_empty_queue(self):
        postqueue.write(self.path, ["# だけ"])
        self.assertEqual(postqueue.pop(self.path), (None, None))

    def test_too_long(self):
        count, longs = postqueue.too_long(self.path, len, 3)
        self.assertEqual(count, 2)
        self.assertEqual([n for n, _ in longs], [6])


class PostTest(unittest.TestCase):
    def setUp(self):
        fd, self.path = tempfile.mkstemp(suffix=".txt")
        os.close(fd)
        postqueue.write(self.path, ["A", "B"])
        self.addCleanup(os.unlink, self.path)

    def run_one(self, send, env, skip_unset=False, fail=False):
        api = poster.TARGETS["x"]
        with mock.patch.object(api, "read_env", return_value=env), \
                mock.patch.object(api, "send", side_effect=PostError("boom") if fail else None,
                                  return_value="123"), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            poster.post_one("x", None, send, self.path, skip_unset)
        return out.getvalue()

    full = {k: "v" for k in xapi.KEYS}

    def test_dry_run_keeps_queue(self):
        self.run_one(False, self.full)
        self.assertEqual(postqueue.read(self.path), ["A", "B"])

    def test_success_pops_queue(self):
        self.assertIn("投稿しました: 123", self.run_one(True, self.full))
        self.assertEqual(postqueue.read(self.path), ["B"])

    def test_failure_keeps_queue(self):
        with self.assertRaises(PostError):
            self.run_one(True, self.full, fail=True)
        self.assertEqual(postqueue.read(self.path), ["A", "B"])

    def test_skip_when_all_unset(self):
        self.assertIn("スキップ", self.run_one(True, {k: "" for k in xapi.KEYS}, skip_unset=True))
        self.assertEqual(postqueue.read(self.path), ["A", "B"])

    def test_partly_unset_is_error(self):
        env = dict(self.full, X_API_KEY="")
        with self.assertRaises(PostError):
            self.run_one(True, env, skip_unset=True)

    def test_one_target_failing_does_not_stop_other(self):
        calls = []
        def fake(name, *a, **k):
            calls.append(name)
            if name == "x":
                raise OSError("x down")
        with mock.patch.object(poster, "post_one", side_effect=fake), \
                contextlib.redirect_stdout(io.StringIO()) as out:
            rc = poster.run_targets(["x", "threads"], None, True, True, True)
        self.assertEqual(calls, ["x", "threads"])
        self.assertEqual(rc, 1)
        self.assertIn("[x] エラー: x down", out.getvalue())


class AdTest(unittest.TestCase):
    def test_no_repeat_and_full_cycles(self):
        n = len(ad.load()["ads"])
        seq = [ad.pick(i, n) for i in range(n * 5)]
        for c in range(5):
            self.assertEqual(sorted(seq[c * n:(c + 1) * n]), list(range(n)))
        self.assertTrue(all(a != b for a, b in zip(seq, seq[1:])))

    def test_every_ad_has_image_and_fits(self):
        for item in ad.load()["ads"]:
            self.assertTrue(os.path.exists(os.path.join(ad.HERE, "images", item["image"])), item["image"])
            self.assertLessEqual(xapi.measure(item["text"]), xapi.MAX_LEN)

    def test_out_of_period(self):
        out = []
        ad.run(False, day=999, out=out.append)
        self.assertIn("期間外", out[0])


class RealQueuesTest(unittest.TestCase):
    def test_all_queued_posts_fit(self):
        self.assertEqual(poster.check(), 0)


if __name__ == "__main__":
    unittest.main()
