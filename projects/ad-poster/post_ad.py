"""広告(画像つき)を、毎日1回、ランダムに1枚選んで投稿するツール。標準ライブラリのみ。

使い方:
  python post_ad.py                 # 今日の広告を確認だけ(投稿しない)
  python post_ad.py --send          # X に投稿
  python post_ad.py --send --threads  # X と Threads に投稿
  python post_ad.py --day 3         # 3日目の広告を確認(日付を指定して試す)
  python post_ad.py --force         # 期間外でも動かす

選び方: 8枚を、シャッフルした順番で、1日1枚ずつ出す。8日で一巡したら、別の順番でもう一巡。
同じ画像が、2日続けて出ることは、ない。期間(start_date から days 日)を過ぎたら、何もしない。
"""
import argparse
import datetime as dt
import json
import mimetypes
import os
import random
import sys
import time
import uuid
import urllib.error
import urllib.parse
import urllib.request

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(HERE, "..", "x-poster"))
import post as xpost  # noqa: E402  (X の署名・文字数の数え方を使い回す)

JST = dt.timezone(dt.timedelta(hours=9))
X_TWEET = "https://api.x.com/2/tweets"
X_MEDIA_V2 = "https://api.x.com/2/media/upload"
X_MEDIA_V1 = "https://upload.twitter.com/1.1/media/upload.json"
THREADS = "https://graph.threads.net/v1.0"
RAW = "https://raw.githubusercontent.com/{repo}/{branch}/projects/ad-poster/images/{name}"


def load():
    with open(os.path.join(HERE, "ads.json"), encoding="utf-8") as f:
        return json.load(f)


def day_index(cfg, today=None):
    today = today or dt.datetime.now(JST).date()
    return (today - dt.date.fromisoformat(cfg["start_date"])).days


def pick(n, count, seed=20261010):
    """n日目に出す広告の番号。8枚を一巡ごとにシャッフルし、巡の境目でも同じ画像が続かないようにする。"""
    def order(cycle):
        o = random.Random(seed + cycle).sample(range(count), count)
        return o
    cycle, pos = divmod(n, count)
    o = order(cycle)
    if cycle > 0 and pos == 0 and o[0] == order(cycle - 1)[-1]:
        o[0], o[1] = o[1], o[0]
        return o[0]
    if cycle > 0 and pos == 1 and o[0] == order(cycle - 1)[-1]:
        return o[0]  # 入れ替え後の2番目(元の先頭)
    return o[pos]


def multipart(fields, file_field, filename, data, ctype):
    boundary = "----ad" + uuid.uuid4().hex
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


def x_upload(path, env):
    name = os.path.basename(path)
    ctype = mimetypes.guess_type(name)[0] or "image/jpeg"
    data = open(path, "rb").read()
    body, ct = multipart({"media_category": "tweet_image", "media_type": ctype}, "media", name, data, ctype)
    req = urllib.request.Request(
        X_MEDIA_V2, data=body, method="POST",
        headers={"Authorization": xpost.oauth_header("POST", X_MEDIA_V2, env), "Content-Type": ct})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            j = json.load(r)
    except urllib.error.HTTPError as e:
        if e.code not in (404, 410):
            sys.exit(f"X 画像アップロード エラー {e.code}: {e.read().decode(errors='replace')}")
        # v2 が使えない場合は、旧い方法(v1.1)を試す
        body, ct = multipart({"media_category": "tweet_image"}, "media", name, data, ctype)
        req = urllib.request.Request(
            X_MEDIA_V1, data=body, method="POST",
            headers={"Authorization": xpost.oauth_header("POST", X_MEDIA_V1, env), "Content-Type": ct})
        j = http(req, "X 画像アップロード(v1.1)")
        return str(j["media_id_string"])
    return str(j.get("data", {}).get("id") or j.get("media_id_string"))


def x_post(text, media_id, env):
    req = urllib.request.Request(
        X_TWEET, method="POST",
        data=json.dumps({"text": text, "media": {"media_ids": [media_id]}}).encode(),
        headers={"Authorization": xpost.oauth_header("POST", X_TWEET, env), "Content-Type": "application/json"})
    return http(req, "X 投稿").get("data", {}).get("id")


def threads_post(text, image_url, token, uid="me"):
    def call(path, params):
        req = urllib.request.Request(f"{THREADS}/{path}", data=urllib.parse.urlencode(params).encode(), method="POST")
        return http(req, "Threads")
    made = call(f"{uid}/threads", {"media_type": "IMAGE", "image_url": image_url, "text": text, "access_token": token})
    time.sleep(8)  # 画像の取り込みを待つ
    return call(f"{uid}/threads_publish", {"creation_id": made["id"], "access_token": token}).get("id")


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--send", action="store_true")
    ap.add_argument("--threads", action="store_true", help="Threads にも投稿する")
    ap.add_argument("--day", type=int, help="n日目として扱う(試し用)")
    ap.add_argument("--force", action="store_true", help="期間外でも動かす")
    a = ap.parse_args(argv)

    cfg = load()
    n = a.day if a.day is not None else day_index(cfg)
    if not a.force and not (0 <= n < cfg["days"]):
        print(f"期間外です(n={n}、期間は {cfg['days']} 日)。何も投稿しません")
        return
    n = max(n, 0)
    ad = cfg["ads"][pick(n, len(cfg["ads"]))]
    path = os.path.join(HERE, "images", ad["image"])
    text = ad["text"]
    w = xpost.weighted_len(text)
    print(f"[{n + 1}日目] 画像: {ad['image']} / 文字数: {w}/{xpost.MAX_LEN}\n{text}")
    if w > xpost.MAX_LEN:
        sys.exit("長すぎます")
    if not os.path.exists(path):
        sys.exit(f"画像がありません: {path}")
    if not a.send:
        print("(確認のみ。投稿するには --send)")
        return

    env = {k: os.environ.get(k, "") for k in xpost.KEYS}
    missing = [k for k in xpost.KEYS if not env[k]]
    if missing:
        sys.exit("環境変数が足りません: " + ", ".join(missing))
    media_id = x_upload(path, env)
    print("X: 投稿しました:", x_post(text, media_id, env))

    if a.threads:
        token = os.environ.get("THREADS_ACCESS_TOKEN", "")
        if not token:
            sys.exit("Threads: THREADS_ACCESS_TOKEN がありません")
        repo = os.environ.get("GITHUB_REPOSITORY", "111nakazaki-lgtm/ontime")
        branch = os.environ.get("AD_IMAGE_BRANCH", "claude/integration-mwd91k")
        url = RAW.format(repo=repo, branch=branch, name=urllib.parse.quote(ad["image"]))
        print("Threads: 投稿しました:", threads_post(text, url, token, os.environ.get("THREADS_USER_ID") or "me"))


if __name__ == "__main__":
    main(sys.argv[1:])
