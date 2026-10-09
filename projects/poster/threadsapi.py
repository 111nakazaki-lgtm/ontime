"""Threads API(公式)。標準ライブラリのみ。認証情報は環境変数から読む(リポジトリには入れない)。

  THREADS_ACCESS_TOKEN (必須。長期トークンは約60日で期限が切れる)
  THREADS_USER_ID      (省略可。空なら自分のアカウント "me" に投稿)
"""
import os
import time
import urllib.parse
import urllib.request

from http_util import http

NAME = "threads"
BASE = "https://graph.threads.net/v1.0"
MAX_LEN = 500
KEYS = ["THREADS_ACCESS_TOKEN"]
measure = len


def read_env() -> dict:
    env = {k: os.environ.get(k, "") for k in KEYS}
    env["THREADS_USER_ID"] = os.environ.get("THREADS_USER_ID", "")
    return env


def call(path: str, params: dict) -> dict:
    req = urllib.request.Request(
        f"{BASE}/{path}", data=urllib.parse.urlencode(params).encode(), method="POST")
    return http(req, "Threads API", timeout=30)


def send(text: str, env: dict, image_url: str = None) -> str:
    """文章を投稿して投稿IDを返す。image_url(公開URL)を渡すと画像つきで投稿する。"""
    uid, token = env["THREADS_USER_ID"] or "me", env["THREADS_ACCESS_TOKEN"]
    # 1) 投稿の下書き(コンテナ)を作る  2) 公開する
    params = {"media_type": "TEXT", "text": text, "access_token": token}
    if image_url:
        params.update(media_type="IMAGE", image_url=image_url)
    created = call(f"{uid}/threads", params)
    if image_url:
        time.sleep(8)  # 画像の取り込みを待つ
    done = call(f"{uid}/threads_publish", {"creation_id": created["id"], "access_token": token})
    return done.get("id", "")
