# instagram-poster

Instagram への投稿は Metricool 経由(本人の Metricool に Instagram @nakazakl1209 を接続済み)。
GitHub Actions では投稿しない。Claude が毎日1本、queue.txt の先頭を Metricool で 21:00 JST に予約する。

- `queue.txt`: 投稿の待ち行列。「キャプション || 写真1.jpg,写真2.jpg」(カンマ区切りで最大10枚のカルーセル)
- `videos/`: リール用の縦動画(9:16・H.264・音声トラックあり・3秒以上)。queue の行で `|| 動画.mp4` と書くと、Metricool に instagramData type REEL で予約する(URL は images/ でなく videos/)
- `posted.txt`: 予約した投稿の記録
- `images/`: Instagram 用の写真。`make_images.py` が x-poster/images の写真を 4:5〜1.91:1 の JPEG にして作る
  (Instagram は 9:16 や 3:4 の縦長写真を断る)。Metricool には raw.githubusercontent.com の URL で渡すので、push 済みであること
- 書き方のルールは `projects/post-writer/GUIDE.md` の Instagram の節
