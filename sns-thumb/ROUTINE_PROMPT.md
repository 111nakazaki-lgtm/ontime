# claude.ai の「ルーティン」に貼り付ける指示文

## 設定
- 繰り返し: 毎日 6:50 (Asia/Tokyo)
- リポジトリ: 111nakazaki-lgtm/ontime(ブランチ ccr-2e557d9b-b8flao)
- コネクタ: Google Drive
- 環境変数(環境の設定で保存。この文書には書かない): `THREADS_ACCESS_TOKEN` / `THREADS_USER_ID`

## 貼り付ける指示文(この線の下から最後まで)

---

リポジトリ 111nakazaki-lgtm/ontime の sns-thumb/ を使って、今日のSNS用サムネを作り、Threadsに自動投稿してください。目的は、ユーザーのSNS(X・Instagram・Threads・note)のフォロワーを2,000人に増やすことです。作業はブランチ ccr-2e557d9b-b8flao で行い、main には触れないでください。ユーザーは、Threadsへの自動投稿を明示的に許可しています。

【写真の取得元】Google ドライブの専用フォルダ「SNS写真(自動投稿用)」(フォルダID: 1wd8hhvBnam1NpCKxA6M98E6M4vWjbFV1)だけです。それ以外のドライブのファイルは、検索・閲覧・ダウンロードしないでください(仕事等の個人ファイルがあります)。

手順:
1. 最新のブランチを取得し、sns-thumb/README.md と sns-thumb/SERIES_MINA.md を読む。
2. 専用フォルダ内の画像のうち、sns-thumb/used.txt に載っていない(ファイル名またはID)ものを対象にする。対象が無ければ、sns-thumb/out/ にある、sns-thumb/posted.txt に載っていないサムネのフォルダから1つ選んで、手順7へ進む。それも無ければ「新しい写真も未投稿のサムネもありません」と報告して終了(何もコミットしない)。
3. 対象の写真をダウンロードして、実際に見て、フォロワーが増えやすいものを1〜3枚選ぶ(ピンぼけ・暗すぎるものは避ける)。ダウンロードした原本は、リポジトリにコミットしない(公開リポジトリのため)。
   - 子どもの顔が分かる実写の写真は、使わない・コミットしない・投稿しない。報告に「イラスト化が必要な写真があります」と書く。
   - 子どもを元にしたアニメ風のイラスト(ミーナちゃんシリーズ)は、サムネと投稿文は作ってよいが、自動投稿はしない(ユーザーが個別に許可するまで)。
   - 写り込んだ人物や、場所が分かる物(表札、住所、自宅の室内など)は、--crop-left / --crop-right / --crop-top / --crop-bottom で切り取る。切り取れない場合は使わない。
4. 各画像に、短くて目を引く日本語の一言を考える。画像にすでに一言が入っているイラストは、文字を重ねない(text に "" を渡す)。
5. python3 sns-thumb/make_thumbs.py <写真> "<一言>" --sub "<補足>" --out sns-thumb/out/<今日の日付YYYY-MM-DD>-<短い名前> で書き出し、出力画像を実際に見て、人物の顔・文字が切れていないか、子どもが写っていないかを確認する。Pillowが無ければ pip install pillow。
6. 同じフォルダの captions.md に、SNS別投稿文(Instagram / Threads / X / note)を日本語で書く。Threadsの本文は500字以内、問いかけで終える。
7. 使った写真名とIDを sns-thumb/used.txt に追記し、commit して ccr-2e557d9b-b8flao に push する(PRは作らない)。画像が公開URLで見えるようになってから、次へ進む。
8. Threadsへの自動投稿: 環境変数 THREADS_ACCESS_TOKEN と THREADS_USER_ID が両方設定されている場合だけ、1日1投稿を上限に、今日の最良の1枚(…_threads.jpg)を、captions.md の Threads 本文で投稿する。
   - コマンド: python3 sns-thumb/threads_post.py <画像パス> "<本文>" --publish
   - 先に --publish を付けずに実行して、画像の公開URLが見えることを確かめる。
   - 投稿に成功したら、フォルダ名と投稿IDを sns-thumb/posted.txt に追記して commit・push する。
   - トークンが未設定なら、投稿せず「Threadsのトークンが未設定のため投稿していません」と報告する。
   - トークンや、エラー内容に含まれる秘密情報は、ログ・コミット・報告に絶対に書かない。
9. 最後に、選んだ写真、一言、保存場所、投稿したか(投稿ID)を短く報告する。

Instagram・X・noteへの自動投稿は、まだ設定されていないので行わない(captions.md の文面を用意するだけ)。フォロワー購入・ボット・相互フォロー自動化・他人の投稿や写真の転載・スクレイピングはしない。
