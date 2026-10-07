# x-poster

X に投稿する小さなツール(標準ライブラリのみ)。

## 準備
1. https://developer.x.com でアプリを作り、権限を **Read and Write** にする
2. 次の4つを環境変数に入れる(リポジトリには入れない)
   `X_API_KEY` `X_API_SECRET` `X_ACCESS_TOKEN` `X_ACCESS_SECRET`
   ※ 権限を変えたあとは Access Token を発行し直す

## 使い方
    python post.py "こんにちは"          # 確認のみ
    python post.py "こんにちは" --send   # 投稿
    python post.py --queue queue.txt --send

## 注意
- 無料枠は投稿数の上限が小さい。上限や規約(自動化の表示ルール)は公式を確認
- 同じ文章の連続投稿は拒否されることがある
