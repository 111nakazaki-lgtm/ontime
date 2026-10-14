"""X (Twitter) 投稿ツール。標準ライブラリのみ。

使い方:
  python post.py "投稿する文章"            # 確認だけ(投稿しない)
  python post.py "投稿する文章" --send     # 実際に投稿
  python post.py --queue queue.txt --send  # キューの先頭1行を投稿して消す

キューの行に写真をつけるときは、文章のあとに「 || 写真のファイル名」を書く(images/ の中のファイル。
カンマで区切ると最大4枚)。例:  神戸に行ってきた。 || kobe-01-be-kobe.jpg

認証情報は環境変数から読む(リポジトリには入れない):
  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
"""
import argparse
import base64
import hashlib
import hmac
import json
import mimetypes
import os
import secrets
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
import uuid

URL = "https://api.x.com/2/tweets"
MEDIA_V2 = "https://api.x.com/2/media/upload"
MEDIA_V1 = "https://upload.twitter.com/1.1/media/upload.json"
MAX_LEN = 280
MAX_IMAGES = 4
IMAGE_SEP = " || "
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


def multipart(fields, file_field, filename, data, ctype):
    boundary = "----x" + uuid.uuid4().hex
    parts = []
    for k, v in fields.items():
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
    parts.append(
        (f'--{boundary}\r\nContent-Disposition: form-data; name="{file_field}"; filename="{filename}"\r\n'
         f"Content-Type: {ctype}\r\n\r\n").encode() + data + b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode())
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def http(req, label):
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"{label} エラー {e.code}: {e.read().decode(errors='replace')}")


def x_upload(path: str, env: dict) -> str:
    """画像を X にアップロードして media_id を返す。v2 が使えなければ旧い方法(v1.1)を試す。"""
    name = os.path.basename(path)
    ctype = mimetypes.guess_type(name)[0] or "image/jpeg"
    with open(path, "rb") as f:
        data = f.read()
    body, ct = multipart({"media_category": "tweet_image", "media_type": ctype}, "media", name, data, ctype)
    req = urllib.request.Request(
        MEDIA_V2, data=body, method="POST",
        headers={"Authorization": oauth_header("POST", MEDIA_V2, env), "Content-Type": ct})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            j = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code not in (404, 410):
            sys.exit(f"X 画像アップロード エラー {e.code}: {e.read().decode(errors='replace')}")
        body, ct = multipart({"media_category": "tweet_image"}, "media", name, data, ctype)
        req = urllib.request.Request(
            MEDIA_V1, data=body, method="POST",
            headers={"Authorization": oauth_header("POST", MEDIA_V1, env), "Content-Type": ct})
        return str(http(req, "X 画像アップロード(v1.1)")["media_id_string"])
    return str(j.get("data", {}).get("id") or j.get("media_id_string"))


def send(text: str, env: dict, media_ids=None) -> dict:
    payload = {"text": text}
    if media_ids:
        payload["media"] = {"media_ids": list(media_ids)}
    req = urllib.request.Request(
        URL,
        data=json.dumps(payload).encode(),
        headers={"Authorization": oauth_header("POST", URL, env), "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"X API エラー {e.code}: {e.read().decode(errors='replace')}")


def split_images(line: str):
    """「文章 || a.jpg,b.jpg」を、文章と写真のファイル名の一覧に分ける。"""
    if IMAGE_SEP not in line:
        return line, []
    text, _, names = line.rpartition(IMAGE_SEP)
    return text, [n.strip() for n in names.split(",") if n.strip()][:MAX_IMAGES]


def pop_queue(path: str) -> str:
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

    text, names = split_images(text)
    base = os.path.dirname(os.path.abspath(a.queue)) if a.queue else os.getcwd()
    paths = [os.path.join(base, "images", n) for n in names]
    text = text.replace("\\n", "\n")  # キューの \n を改行に変える
    n = weighted_len(text)
    print(f"[{n}/{MAX_LEN}] {text}")
    if names:
        print("写真:", ", ".join(names))
    if n > MAX_LEN:
        sys.exit("長すぎます")
    if not a.send:
        print("(確認のみ。投稿するには --send)")
        return

    env = {k: os.environ.get(k, "") for k in KEYS}
    missing = [k for k in KEYS if not env[k]]
    if missing:
        sys.exit("環境変数が足りません: " + ", ".join(missing))
    found = [p for p in paths if os.path.exists(p)]
    if len(found) < len(paths):
        print("⚠ 見つからない写真があるので、見つかった分だけで投稿します")
    res = send(text, env, [x_upload(p, env) for p in found])
    print("投稿しました:", res.get("data", {}).get("id"))
    if rest is not None:  # 投稿に成功したあとだけキューから消す
        with open(a.queue, "w", encoding="utf-8") as f:
            f.write("\n".join(rest) + ("\n" if rest else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
