"""Instagram 投稿ツール。標準ライブラリのみ。

Instagram は写真が必須。キューの1行は「キャプション || 写真のファイル名」。
カンマで区切ると最大10枚のカルーセルになる。例:  神戸に行ってきた。 || kobe-03-nankinmachi.jpg

使い方:
  python post.py --queue queue.txt          # 先頭の1行を確認だけ(投稿しない)
  python post.py --queue queue.txt --send   # 先頭の1行を投稿して消す

写真は images/ に置いた JPEG。Instagram は写真を URL で取りに来るので、
このリポジトリ(公開)の raw URL を渡す。images/ の写真は push 済みである必要がある。
縦横比は 4:5(縦長)〜 1.91:1(横長)の範囲。外れると Instagram に断られる。

認証情報は環境変数から読む(リポジトリには入れない):
  INSTAGRAM_ACCESS_TOKEN (必須)
  INSTAGRAM_USER_ID      (省略可。空なら自分のアカウント "me" に投稿)
"""
import argparse
import json
import os
import sys
import time
import urllib.error
import urllib.parse
import urllib.request

BASE = "https://graph.instagram.com/v23.0"
MAX_LEN = 2200
MAX_TAGS = 30
MAX_IMAGES = 10
IMAGE_SEP = " || "
KEYS = ["INSTAGRAM_ACCESS_TOKEN"]
# 写真の公開URLの元。GitHub Actions では自動で今のリポジトリとブランチになる
REPO = os.environ.get("GITHUB_REPOSITORY", "111nakazaki-lgtm/ontime")
BRANCH = os.environ.get("GITHUB_REF_NAME", "claude/integration-mwd91k")
IMAGE_DIR = "projects/instagram-poster/images"


def call(method: str, path: str, params: dict) -> dict:
    data = urllib.parse.urlencode(params)
    if method == "GET":
        req = urllib.request.Request(f"{BASE}/{path}?{data}")
    else:
        req = urllib.request.Request(f"{BASE}/{path}", data=data.encode(), method="POST")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            return json.load(r)
    except urllib.error.HTTPError as e:
        sys.exit(f"Instagram API エラー {e.code}: {e.read().decode(errors='replace')}")


def image_url(name: str) -> str:
    return f"https://raw.githubusercontent.com/{REPO}/{BRANCH}/{IMAGE_DIR}/{urllib.parse.quote(name)}"


def wait_ready(cid: str, token: str):
    """下書き(コンテナ)の準備ができるまで待つ。Instagram が写真を取りに行くのに時間がかかる"""
    for _ in range(12):
        st = call("GET", cid, {"fields": "status_code", "access_token": token}).get("status_code")
        if st == "FINISHED":
            return
        if st in ("ERROR", "EXPIRED"):
            sys.exit(f"Instagram の下書きが {st} になりました(写真の形式や縦横比を確認)")
        time.sleep(5)
    sys.exit("Instagram の下書きが準備できませんでした(時間切れ)")


def send(caption: str, names: list, env: dict) -> str:
    uid, token = env["INSTAGRAM_USER_ID"] or "me", env["INSTAGRAM_ACCESS_TOKEN"]
    # 1) 下書き(コンテナ)を作る  2) 準備できるまで待つ  3) 公開する
    if len(names) == 1:
        cid = call("POST", f"{uid}/media",
                   {"image_url": image_url(names[0]), "caption": caption, "access_token": token})["id"]
    else:
        children = []
        for n in names:
            c = call("POST", f"{uid}/media",
                     {"image_url": image_url(n), "is_carousel_item": "true", "access_token": token})["id"]
            wait_ready(c, token)
            children.append(c)
        cid = call("POST", f"{uid}/media", {"media_type": "CAROUSEL", "children": ",".join(children),
                                             "caption": caption, "access_token": token})["id"]
    wait_ready(cid, token)
    return call("POST", f"{uid}/media_publish", {"creation_id": cid, "access_token": token}).get("id", "")


def split_images(line: str):
    """「文章 || a.jpg,b.jpg」を、文章と写真のファイル名の一覧に分ける。"""
    if IMAGE_SEP not in line:
        return line, []
    text, _, names = line.rpartition(IMAGE_SEP)
    return text, [n.strip() for n in names.split(",") if n.strip()]


def pop_queue(path: str):
    with open(path, encoding="utf-8") as f:
        lines = [l.rstrip("\n") for l in f]
    for i, l in enumerate(lines):
        if l.strip() and not l.startswith("#"):
            return l, lines[:i] + lines[i + 1:]
    return None, None


def problems(text: str, names: list, base: str) -> list:
    """投稿できない理由の一覧。空なら投稿できる"""
    out = []
    if not names:
        out.append("写真がない(Instagram は写真が必須)")
    if len(names) > MAX_IMAGES:
        out.append(f"写真が多すぎる {len(names)}/{MAX_IMAGES}")
    for n in names:
        if not n.lower().endswith((".jpg", ".jpeg")):
            out.append(f"JPEG ではない: {n}")
        elif not os.path.exists(os.path.join(base, "images", n)):
            out.append(f"写真が見つからない: {n}")
    if len(text) > MAX_LEN:
        out.append(f"長すぎる {len(text)}/{MAX_LEN}")
    if text.count("#") > MAX_TAGS:
        out.append(f"ハッシュタグが多すぎる(最大{MAX_TAGS})")
    return out


def main(argv):
    ap = argparse.ArgumentParser()
    ap.add_argument("--queue", required=True)
    ap.add_argument("--send", action="store_true", help="実際に投稿する")
    a = ap.parse_args(argv)

    line, rest = pop_queue(a.queue)
    if line is None:
        print("キューが空です。何も投稿しません")
        return
    text, names = split_images(line)
    text = text.replace("\\n", "\n")  # キューの \n を改行に変える
    print(f"[{len(text)}/{MAX_LEN}] {text}")
    print("写真:", ", ".join(names) or "(なし)")
    bad = problems(text, names, os.path.dirname(os.path.abspath(a.queue)))
    if bad:
        sys.exit("エラー: " + " / ".join(bad))
    if not a.send:
        print("(確認のみ。投稿するには --send)")
        return

    env = {k: os.environ.get(k, "") for k in KEYS}
    env["INSTAGRAM_USER_ID"] = os.environ.get("INSTAGRAM_USER_ID", "")
    missing = [k for k in KEYS if not env[k]]
    if missing:
        sys.exit("環境変数が足りません: " + ", ".join(missing))
    print("投稿しました:", send(text, names, env))
    with open(a.queue, "w", encoding="utf-8") as f:  # 投稿に成功したあとだけキューから消す
        f.write("\n".join(rest) + ("\n" if rest else ""))


if __name__ == "__main__":
    main(sys.argv[1:])
