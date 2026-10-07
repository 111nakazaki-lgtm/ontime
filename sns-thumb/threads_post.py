#!/usr/bin/env python3
"""Threads に画像つきで投稿する(公式 Threads API)。

環境変数: THREADS_ACCESS_TOKEN, THREADS_USER_ID
画像は、公開リポジトリにpush済みのサムネの raw URL を使う。

  python threads_post.py out/2026-10-07/xxx_threads.jpg "本文"            # 確認のみ(投稿しない)
  python threads_post.py - "本文" --publish                              # 文章だけを投稿
  python threads_post.py out/2026-10-07/xxx_threads.jpg "本文" --publish  # 実際に投稿
  python threads_post.py --refresh                                        # トークン更新(60日ごと)
"""
import argparse
import os
import sys
import time

import requests

API = "https://graph.threads.net/v1.0"
RAW = "https://raw.githubusercontent.com/111nakazaki-lgtm/ontime/{branch}/sns-thumb/{path}"
BRANCH = "ccr-2e557d9b-b8flao"


def env(name):
    v = os.environ.get(name)
    if not v:
        sys.exit(f"環境変数 {name} が未設定です。")
    return v


def check(r):
    if not r.ok:
        sys.exit(f"Threads API エラー {r.status_code}: {r.text}")
    return r.json()


def refresh():
    j = check(requests.get("https://graph.threads.net/refresh_access_token", params={
        "grant_type": "th_refresh_token", "access_token": env("THREADS_ACCESS_TOKEN")}))
    print("新しいトークン(シークレットを置き換えてください):", j["access_token"])
    print("有効秒数:", j.get("expires_in"))


def post(path, text, publish):
    if len(text) > 500:
        sys.exit("Threads の本文は500字までです。")
    text_only = path == "-"
    params = {"media_type": "TEXT", "text": text}
    if not text_only:
        url = RAW.format(branch=BRANCH, path=path.replace("\\", "/"))
        head = requests.head(url, timeout=30)
        if head.status_code != 200:
            sys.exit(f"画像が公開URLで見えません({head.status_code}): {url}\n先に push してください。")
        print("画像URL:", url)
        params = {"media_type": "IMAGE", "image_url": url, "text": text}
    print("本文:", text)
    if not publish:
        print("(確認のみ。--publish を付けると投稿します)")
        return
    uid, tok = env("THREADS_USER_ID"), env("THREADS_ACCESS_TOKEN")
    c = check(requests.post(f"{API}/{uid}/threads", data={**params, "access_token": tok}))
    time.sleep(10 if not text_only else 3)  # コンテナ処理待ち
    p = check(requests.post(f"{API}/{uid}/threads_publish", data={
        "creation_id": c["id"], "access_token": tok}))
    print("投稿しました。ID:", p["id"])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("path", nargs="?")
    ap.add_argument("text", nargs="?")
    ap.add_argument("--publish", action="store_true")
    ap.add_argument("--refresh", action="store_true")
    a = ap.parse_args()
    if a.refresh:
        return refresh()
    if not (a.path and a.text):
        ap.error("path と text が必要です")
    post(a.path, a.text, a.publish)


if __name__ == "__main__":
    main()
