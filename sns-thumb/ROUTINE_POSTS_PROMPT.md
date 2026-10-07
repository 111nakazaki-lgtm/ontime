# claude.ai の「ルーティン」に貼り付ける指示文(Threads の文章投稿・毎朝/毎晩)

## 設定(ルーティンを2つ作る)
- 朝: 毎日 7:30 (Asia/Tokyo) → 指示文の「SLOT」を `morning` にする
- 夜: 毎日 21:00 (Asia/Tokyo) → 指示文の「SLOT」を `night` にする
- リポジトリ: 111nakazaki-lgtm/ontime(ブランチ ccr-2e557d9b-b8flao)
- 環境変数(環境の設定で保存。この文書には書かない): `THREADS_ACCESS_TOKEN` / `THREADS_USER_ID`

## 貼り付ける指示文(この線の下から最後まで)

---

リポジトリ 111nakazaki-lgtm/ontime のブランチ ccr-2e557d9b-b8flao で作業してください(main には触れない)。目的は、ユーザー(中崎恵介)の Threads のフォロワー増加です。ユーザーは、Threads への自動投稿を明示的に許可しています。

SLOT = morning   ← 夜のルーティンでは night に書き換える

手順:
1. 最新のブランチを取得し、sns-thumb/threads/PERSONA.md を読む。
2. cd sns-thumb && python3 post_next.py --slot <SLOT> を実行して、投稿できる文章があるか確認する(確認のみ)。
3. 「投稿できる文章がありません」と出た場合は、PERSONA.md のルールを守って、新しい投稿を3〜5本、sns-thumb/threads/queue/ に追加する。
   - ファイル名: 連番-短い名前.txt。1行目に `slot: morning` か `slot: night`、2行目に `verified: yes` か `verified: no`、3行目に `---`、その後に本文。
   - 本文は、PERSONA.md の「使ってよい事実」と、一般的な意見だけで書く。出来事や数字を作らない。作ってしまう場合は `verified: no` にする。
   - 追加したら commit して push し、手順2に戻る。
4. 環境変数 THREADS_ACCESS_TOKEN と THREADS_USER_ID が両方設定されている場合だけ、python3 post_next.py --slot <SLOT> --publish で投稿する。
   - 1日の上限: 朝1本、夜1本(合計2本)。同じ slot で、今日すでに posted.txt に記録がある場合は、投稿しない。
   - 投稿に成功したら、sns-thumb/threads/posted.txt の更新を commit して push する。
   - トークンが未設定なら、投稿せず「Threadsのトークンが未設定のため投稿していません」と報告する。
   - トークンや、エラー内容に含まれる秘密情報は、ログ・コミット・報告に絶対に書かない。
5. 最後に、選んだ投稿のタイトル(ファイル名)と、投稿したか(投稿ID)を、短く報告する。

verified: no の投稿は、絶対に投稿しない。売り込み・他人の批判・愚痴は書かない。フォロワー購入・ボット・相互フォロー自動化はしない。
