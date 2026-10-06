# claude.ai の「ルーティン」に貼り付ける指示文(Google ドライブ版)

設定: 毎日 6:50 (Asia/Tokyo) / コネクタ: Google Drive / リポジトリ: 111nakazaki-lgtm/ontime

---

リポジトリ 111nakazaki-lgtm/ontime の sns-thumb/ を使って、今日のSNS用サムネを作ってください。目的はフォロワー2,000人です。作業はブランチ ccr-2e557d9b-b8flao で行い、main には触れないでください。

写真の取得元は Google ドライブの専用フォルダ「SNS写真(自動投稿用)」(フォルダID: 1wd8hhvBnam1NpCKxA6M98E6M4vWjbFV1)だけです。それ以外のドライブのファイルは、検索・閲覧・ダウンロードしないでください(仕事等の個人ファイルがあります)。

1. sns-thumb/README.md を読む。
2. 専用フォルダ内の画像のうち、sns-thumb/used.txt に無いものを対象にする。無ければ「新しい写真がありません」と報告して終了。
3. 写真を見て、目を止める・保存したくなるものを1〜3枚選ぶ(ピンぼけ・暗い・顔が大きいものは避ける)。
4. 短い日本語の一言(全角20字前後)を考え、python3 sns-thumb/make_thumbs.py <写真> "<一言>" --out sns-thumb/out/<YYYY-MM-DD> で書き出す。
5. sns-thumb/out/<日付>/captions.md に、Instagram/Threads/X/note 別の投稿文と、おすすめ投稿時間を書く。
6. 使った写真を used.txt に追記し、commit して push(PRは作らない)。
7. 自動投稿はユーザーの承認があるまでしない。フォロワー購入・ボット・転載・スクレイピングはしない。
