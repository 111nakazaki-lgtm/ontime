# threads-poster

Threads に投稿する小さなツール(標準ライブラリのみ)。公式の Threads API を使う。

## 準備
1. https://developers.facebook.com でアプリを作り、Threads API を追加
2. 権限 `threads_basic` と `threads_content_publish` を付けてアクセストークンを発行
3. 次の2つを環境変数に入れる(リポジトリには入れない)
   `THREADS_ACCESS_TOKEN`(必須)、`THREADS_USER_ID`(省略可。空なら `me` = 自分のアカウント)
   ※ トークンは期限がある(長期トークンは約60日)。期限前に更新する

## 使い方
    python post.py "こんにちは"          # 確認のみ
    python post.py "こんにちは" --send   # 投稿
    python post.py --queue queue.txt --send

## 注意
- 1投稿は500文字まで。投稿数にも上限がある(公式を確認)
