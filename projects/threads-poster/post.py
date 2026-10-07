"""Threads 投稿ツール。標準ライブラリのみ。

使い方:
  python post.py "投稿する文章"            # 確認だけ(投稿しない)
  python post.py "投稿する文章" --send     # 実際に投稿
  python post.py --queue queue.txt --send  # キューの先頭1行を投稿して消す

認証情報は環境変数から読む(リポジトリには入れない):
  THREADS_ACCESS_TOKEN (必須)
  THREADS_USER_ID      (省略可。空なら自分のアカウント "me" に投稿)
"""
import argparse
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://graph.threads.net/v1.0"
MAX_LEN = 500
KEYS = ["THREADS_ACCESS_TOKEN"]


def call(path: str, params: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}/{path}", data=urllib.parse.urlencode(params).encode(), method="POST"
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Threads API エラー {e.code}: {e.read().decode(errors='replace')}")


def send(text: str, env: dict) -> str:
    uid, token = env["THREADS_USER_ID"] or "me", env["THREADS_ACCESS_TOKEN"]
    # 1) 投稿の下書き(コンテナ)を作る  2) 公開する
    created = call(f"{uid}/threads", {"media_type": "TEXT", "text": text, "access_token": token})
    done = call(f"{uid}/threads_publish", {"creation_id": created["id"], "access_token": token})
    return done.get("id", "")


def pop_queue(path: str):
    with open(path, encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f]
    for i, l in enumerate(lines):
        if l.strip() and not l.startswith("#"):
            return l, lines[:i] + lines[i + 1:]
    return None, None


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?")
    ap.add_argument("--queue")
    ap.add_argument("--send", action="store_true", help="実際に投稿する")
    a = ap.parse_args(argv)

    rest = None
    if a.queue:
        text, rest = pop_queue(a.queue)
        if text is None:
            print("キューが空です。何も投稿しません")
            return
    elif a.text:
        text = a.text
    else:
        ap.error("text か --queue が必要です")

    text = text.replace("\\n", "\n")  # キューの \n を改行に変える
    print(f"[{len(text)}/{MAX_LEN}] {text}")
    if len(text) > MAX_LEN:
        sys.exit("長すぎます")
    if not a.send:
        print("(確認のみ。投稿するには --send)")
        return

    env = {k: os.environ.get(k, "") for k in KEYS}
    env["THREADS_USER_ID"] = os.environ.get("THREADS_USER_ID", "")
    missing = [k for k in KEYS if not env[k]]
    if missing:
        sys.exit("環境変数が足りません: " + ", ".join(missing))
    print("投稿しました:", send(text, env))
    if rest is not None:  # 投稿に成功したあとだけキューから消す
        with open(a.queue, "w", encoding="utf-8") as f:
            f.write("\n".join(rest) + ("\n" if rest else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
