"""広告(画像つき)を、毎日1回、ランダムに1枚選んで投稿する。

選び方: 8枚を、シャッフルした順番で、1日1枚ずつ出す。8日で一巡したら、別の順番でもう一巡。
同じ画像が、2日続けて出ることは、ない。期間(ads.json の start_date から days 日)を過ぎたら、何もしない。
"""
import datetime as dt
import json
import os
import random
import urllib.parse

import threadsapi
import xapi
from errors import PostError

HERE = os.path.dirname(os.path.abspath(__file__))
JST = dt.timezone(dt.timedelta(hours=9))
RAW = "https://raw.githubusercontent.com/{repo}/{branch}/projects/poster/images/{name}"


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


def image_url(name):
    """Threads は画像を公開URLから取り込む。画像のあるブランチは AD_IMAGE_BRANCH、無ければ実行中のブランチ。"""
    repo = os.environ.get("GITHUB_REPOSITORY", "111nakazaki-lgtm/ontime")
    branch = os.environ.get("AD_IMAGE_BRANCH") or os.environ.get("GITHUB_REF_NAME") or "main"
    return RAW.format(repo=repo, branch=branch, name=urllib.parse.quote(name))


def run(send, threads=False, day=None, force=False, out=print):
    cfg = load()
    n = day if day is not None else day_index(cfg)
    if not force and not (0 <= n < cfg["days"]):
        out(f"期間外です(n={n}、期間は {cfg['days']} 日)。何も投稿しません")
        return
    n = max(n, 0)
    ad = cfg["ads"][pick(n, len(cfg["ads"]))]
    path = os.path.join(HERE, "images", ad["image"])
    text = ad["text"]
    w = xapi.measure(text)
    out(f"[{n + 1}日目] 画像: {ad['image']} / 文字数: {w}/{xapi.MAX_LEN}\n{text}")
    if w > xapi.MAX_LEN:
        raise PostError("長すぎます")
    if not os.path.exists(path):
        raise PostError(f"画像がありません: {path}")
    if not send:
        out("(確認のみ。投稿するには --send)")
        return

    env = xapi.read_env()
    missing = [k for k in xapi.KEYS if not env[k]]
    if missing:
        raise PostError("環境変数が足りません: " + ", ".join(missing))
    out("X: 投稿しました: " + str(xapi.send(text, env, image=path)))

    if threads:
        tenv = threadsapi.read_env()
        if not tenv["THREADS_ACCESS_TOKEN"]:
            raise PostError("Threads: THREADS_ACCESS_TOKEN がありません")
        out("Threads: 投稿しました: " + str(threadsapi.send(text, tenv, image_url=image_url(ad["image"]))))
