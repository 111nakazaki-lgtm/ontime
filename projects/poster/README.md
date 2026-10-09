# poster

X と Threads への投稿を、ひとつにまとめたツール(標準ライブラリのみ)。
以前の x-poster / threads-poster / ad-poster / post-writer を統合したもの。

## 使い方
`--send` を付けない限り、確認だけで投稿はしない。

    python3 poster.py post "こんにちは" --to x --send   # 文章を指定して投稿(--to 省略で両方)
    python3 poster.py queue --send                      # 各キューの先頭1行を投稿して消す
    python3 poster.py ad --day 3                        # 3日目の広告を確認(--send --threads で投稿)
    python3 poster.py check                             # キューの全行が投稿できる長さか確認
    python3 -m unittest                                 # テスト(オフライン)

- X と Threads は独立して動く。片方が失敗してももう片方は投稿し、失敗した側のキューは消えない
- キューの行は、投稿に成功したあとだけ消える

## ファイル
| もの | 場所 |
|---|---|
| 入口(コマンド) | `poster.py` |
| X / Threads の API | `xapi.py` / `threadsapi.py`(共通の HTTP は `http_util.py`) |
| キュー | `queues/x.txt` `queues/threads.txt`(1行1投稿、`#`始まりは無視、`\n` は改行) |
| 広告 | `ad.py`、`ads.json`、`images/` |
| 下書きルール(毎日の補充) | `GUIDE.md` |
| 結果通知 | `notify.sh`(Issue「投稿ログ」にコメント) |
| 定期実行 | `.github/workflows/post.yml` |

## 定期実行(post.yml)
- 毎日 09:07 / 21:07 JST: queue(X と Threads)
- 毎日 12:37 JST: ad(広告。期間は `ads.json` の `start_date` から `days` 日)
- 手動実行は、`mode`(queue / ad)と `send` を選ぶ。ad は `threads` と `day`(試し用)も指定できる

## 準備(環境変数。リポジトリには入れない。Actions では Secrets)
- X: `X_API_KEY` `X_API_SECRET` `X_ACCESS_TOKEN` `X_ACCESS_SECRET`(アプリの権限は Read and Write。変えたら Access Token を発行し直す)
- Threads: `THREADS_ACCESS_TOKEN`(必須。長期トークンは約60日で期限切れ)、`THREADS_USER_ID`(省略可)
- 広告を Threads にも出すときの画像は、公開URL(raw.githubusercontent.com)から取り込む。画像があるブランチを `AD_IMAGE_BRANCH` で指定できる(無ければ実行中のブランチ)

## 注意
- 無料枠は投稿数の上限が小さい。上限や規約(自動化の表示ルール)は公式を確認
- 同じ文章の連続投稿は拒否されることがある。Threads は1投稿500文字まで
