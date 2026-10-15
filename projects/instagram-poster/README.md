# instagram-poster

Instagram に写真つきで投稿する小さなツール(標準ライブラリのみ)。公式の Instagram API(Instagram ログイン)を使う。

## 準備(本人がやること)
1. Instagram アカウントを「プロアカウント」(ビジネス or クリエイター)に切り替える(アプリの設定 → アカウントの種類とツール)
2. https://developers.facebook.com のアプリ(Threads 用と同じアプリでよい)に「Instagram」を追加し、
   「Instagramログインによる API 設定」でアカウントを追加してアクセストークンを発行する。
   権限は `instagram_business_basic` と `instagram_business_content_publish`
3. GitHub の Settings → Secrets and variables → Actions に次を登録する(リポジトリには入れない)
   `INSTAGRAM_ACCESS_TOKEN`(必須)、`INSTAGRAM_USER_ID`(トークン発行画面に出る数字の ID。省略時は `me`)
   ※ 長期トークンは約60日で切れる。期限前に更新する

シークレットが未登録のあいだ、定期実行はこの手順をスキップする(投稿しない)。

## キューの書き方
    神戸に行ってきた。\n街の空気が好きや。 || kobe-03-nankinmachi.jpg
    大阪の夕景。 || 01-osaka-sunset.jpg,02-castle-autumn.jpg   ← カルーセル(最大10枚)

- 写真は `images/` の JPEG。Instagram は raw.githubusercontent.com の URL から写真を取りに来るので、push 済みであること
- 縦横比は 4:5 〜 1.91:1。9:16 や 3:4 の縦長写真はそのままだと断られる(`images/` の写真は 4:5 に切り抜き済み)
- キャプションは 2200 文字・ハッシュタグ 30 個まで
- 投稿は1日1回(夜 21:07 JST の定期実行だけ)。API の上限は 24 時間に 100 件

## 使い方
    python post.py --queue queue.txt          # 先頭の1行を確認のみ
    python post.py --queue queue.txt --send   # 投稿して消す
