"""X と Threads への投稿を、ひとつにまとめたツール。標準ライブラリのみ。

使い方(--send を付けない限り、確認だけで投稿はしない):
  python3 poster.py post "文章" [--to x,threads] [--send]   # 文章を指定して投稿
  python3 poster.py queue [--to x,threads] [--send]         # キューの先頭1行を投稿して消す
  python3 poster.py ad [--threads] [--day N] [--force] [--send]  # 今日の広告(画像つき)を X(と Threads)へ
  python3 poster.py check                                    # 両方のキューの全行が投稿できる長さか確かめる
"""
import argparse
import os
import sys

import ad
import postqueue
import threadsapi
import xapi
from errors import PostError

TARGETS = {"x": xapi, "threads": threadsapi}
LABEL = {"x": "X", "threads": "Threads"}


def parse_targets(value):
    names = [t.strip() for t in value.split(",") if t.strip()]
    bad = [t for t in names if t not in TARGETS]
    if bad or not names:
        raise SystemExit(f"--to は x と threads から選んでください: {value}")
    return names


def post_one(name, text, send, queue_path=None, skip_unset=False):
    """1つの宛先に投稿する。キューから取った場合は、成功したあとだけ消す。"""
    api = TARGETS[name]
    out = lambda msg: print(f"[{name}] {msg}")
    rest = None
    if queue_path:
        text, rest = postqueue.pop(queue_path)
        if text is None:
            out("キューが空です。何も投稿しません")
            return
    text = postqueue.decode(text)  # キューの \n を改行に変える
    n = api.measure(text)
    out(f"{n}/{api.MAX_LEN}字: {text}")
    if n > api.MAX_LEN:
        raise PostError("長すぎます")
    if not send:
        out("(確認のみ。投稿するには --send)")
        return

    env = api.read_env()
    missing = [k for k in api.KEYS if not env[k]]
    if missing and skip_unset and len(missing) == len(api.KEYS):
        out(f"{LABEL[name]} のシークレット未設定のためスキップ")
        return
    if missing:
        raise PostError("環境変数が足りません: " + ", ".join(missing))
    out(f"投稿しました: {api.send(text, env)}")
    if rest is not None:
        postqueue.write(queue_path, rest)


def run_targets(names, text, send, use_queue, skip_unset):
    """宛先ごとに独立して実行する。片方が失敗しても、もう片方は投稿する。"""
    failed = False
    for name in names:
        try:
            post_one(name, text, send, postqueue.path_for(name) if use_queue else None, skip_unset)
        except PostError as e:
            print(f"[{name}] エラー: {e}")
            failed = True
    return 1 if failed else 0


def check():
    bad = 0
    for name, api in TARGETS.items():
        count, longs = postqueue.too_long(postqueue.path_for(name), api.measure, api.MAX_LEN)
        for n, line in longs:
            bad += 1
            print(f"[{name}] 長すぎ {n}/{api.MAX_LEN}: {line[:30]}…")
        print(f"{name}: {count}本")
    return 1 if bad else 0


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("post", help="文章を指定して投稿")
    p.add_argument("text")
    q = sub.add_parser("queue", help="キューの先頭1行を投稿して消す")
    for s in (p, q):
        s.add_argument("--to", default="x,threads", help="宛先(x,threads のカンマ区切り。既定は両方)")
        s.add_argument("--send", action="store_true", help="実際に投稿する")
        s.add_argument("--skip-unset", action="store_true", help="シークレット未設定の宛先はスキップする")
    a_ = sub.add_parser("ad", help="今日の広告(画像つき)を投稿")
    a_.add_argument("--send", action="store_true", help="実際に投稿する")
    a_.add_argument("--threads", action="store_true", help="Threads にも投稿する")
    a_.add_argument("--day", type=int, help="n日目として扱う(試し用)")
    a_.add_argument("--force", action="store_true", help="期間外でも動かす")
    sub.add_parser("check", help="キューの長さを確認")

    a = ap.parse_args(argv)
    if a.cmd == "check":
        return check()
    if a.cmd == "ad":
        try:
            ad.run(a.send, a.threads, a.day, a.force)
        except PostError as e:
            print(f"エラー: {e}")
            return 1
        return 0
    return run_targets(parse_targets(a.to), getattr(a, "text", None), a.send, a.cmd == "queue", a.skip_unset)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
