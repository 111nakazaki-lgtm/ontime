"""X (Twitter) API。標準ライブラリのみ。認証情報は環境変数から読む(リポジトリには入れない)。

  X_API_KEY, X_API_SECRET, X_ACCESS_TOKEN, X_ACCESS_SECRET
"""
import base64
import hashlib
import hmac
import json
import mimetypes
import os
import secrets
import time
import urllib.error
import urllib.parse
import urllib.request

from errors import PostError
from http_util import http, multipart

NAME = "x"
URL = "https://api.x.com/2/tweets"
MEDIA_V2 = "https://api.x.com/2/media/upload"
MEDIA_V1 = "https://upload.twitter.com/1.1/media/upload.json"
MAX_LEN = 280
KEYS = ["X_API_KEY", "X_API_SECRET", "X_ACCESS_TOKEN", "X_ACCESS_SECRET"]


def measure(text: str) -> int:
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


def read_env() -> dict:
    return {k: os.environ.get(k, "") for k in KEYS}


def send(text: str, env: dict, image: str = None) -> str:
    """文章を投稿して投稿IDを返す。image にファイルのパスを渡すと画像つきで投稿する。"""
    body = {"text": text}
    if image:
        body["media"] = {"media_ids": [upload(image, env)]}
    req = urllib.request.Request(
        URL, data=json.dumps(body).encode(), method="POST",
        headers={"Authorization": oauth_header("POST", URL, env), "Content-Type": "application/json"})
    return http(req, "X API", timeout=30).get("data", {}).get("id")


def upload(path: str, env: dict) -> str:
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
            raise PostError(f"X 画像アップロード エラー {e.code}: {e.read().decode(errors='replace')}")
        # v2 が使えない場合は、旧い方法(v1.1)を試す
        body, ct = multipart({"media_category": "tweet_image"}, "media", name, data, ctype)
        req = urllib.request.Request(
            MEDIA_V1, data=body, method="POST",
            headers={"Authorization": oauth_header("POST", MEDIA_V1, env), "Content-Type": ct})
        return str(http(req, "X 画像アップロード(v1.1)")["media_id_string"])
    return str(j.get("data", {}).get("id") or j.get("media_id_string"))
