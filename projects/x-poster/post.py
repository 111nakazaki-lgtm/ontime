"""X (Twitter) 投稿ツール。標準ライブラリのみ。

使い方:
  python post.py "投稿する文章"            # 確認だけ(投稿しない)
  python post.py "投稿する文章" --send     # 実際に投稿
  python post.py --queue queue.txt --send  # キューの先頭1行を投稿して消す

認証情報は環境変数から読む(リポジトリには入れない):
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
"""
import argparse
import base64
import hashlib
import hmac
import json
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

URL = "https://api.x.com/2/tweets"
MAX_LEN = 280
KEYS = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"]


def weighted_len(text: str) -> int:
    """X の文字数は、日本語など全角は2、半角は1として数える(URL は考慮しない簡易版)。"""
    return sum(1 if ord(c) <= 0x10FF or 0x2000 <= ord(c) <= 0x200D else 2 for c in text)


def quote(s: str) -> str:
    return urllib.parse.quote(s, safe="~")


def oauth_header(method: str, url: str, env: dict, nonce=None, ts=None) -> str:
    params = {
        "oauth_consumer_key": env["X_API_KEY"],
        "oauth_nonce": nonce or secrets.token_hex(16),
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": ts or str(int(time.time())),
        "oauth_token": env["X_ACCESS_TOKEN"],
        "oauth_version": "1.0",
    }
    norm = "&".join(f"{quote(k)}={quote(v)}" for k, v in sorted(params.items()))
    base = "&".join([method.upper(), quote(url), quote(norm)])
    key = f"{quote(env['X_API_SECRET'])}&{quote(env['X_ACCESS_SECRET'])}"
    sig = base64.b64encode(hmac.new(key.encode(), base.encode(), hashlib.sha1).digest()).decode()
    params["oauth_signature"] = sig
    return "OAuth " + ", ".join(f'{quote(k)}="{quote(v)}"' for k, v in sorted(params.items()))


def send(text: str, env: dict) -> dict:
    req = urllib.request.Request(
        URL,
        data=json.dumps({"text": text}).encode(),
        headers={"Authorization": oauth_header("POST", URL, env), "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"X API エラー {e.code}: {e.read().decode(errors='replace')}")


def pop_queue(path: str) -> str:
    with open(path, encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f]
    for i, l in enumerate(lines):
        if l.strip() and not l.startswith("#"):
            return l, lines[:i] + lines[i + 1:]
    sys.exit("キューが空です")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("text", nargs="?")
    ap.add_argument("--queue")
    ap.add_argument("--send", action="store_true", help="実際に投稿する")
    a = ap.parse_args(argv)

    rest = None
    if a.queue:
        text, rest = pop_queue(a.queue)
    elif a.text:
        text = a.text
    else:
        ap.error("text か --queue が必要です")

    n = weighted_len(text)
    print(f"[{n}/{MAX_LEN}] {text}")
    if n > MAX_LEN:
        sys.exit("長すぎます")
    if not a.send:
        print("(確認のみ。投稿するには --send)")
        return

    env = {k: os.environ.get(k, "") for k in KEYS}
    missing = [k for k in KEYS if not env[k]]
    if missing:
        sys.exit("環境変数が足りません: " + ", ".join(missing))
    res = send(text, env)
    print("投稿しました:", res.get("data", {}).get("id"))
    if rest is not None:  # 投稿に成功したあとだけキューから消す
        with open(a.queue, "w", encoding="utf-8") as f:
            f.write("\n".join(rest) + ("\n" if rest else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
