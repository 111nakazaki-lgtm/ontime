<!-- AGENT34:START -->
# 34体エージェント運用ルール（AGENT34 キット）

このブロックはキットが管理する。書き換えるときはブロックの外に追記すること（再導入時にブロック内は上書きされる）。

## 基本方針

- 専門性のある作業は、最も合う専門エージェントに任せる。任せるほどでもない作業は自分で直接やる
- 推測より証拠。完了と言う前に、実際に動かした結果で確かめる
- 品質を保てる範囲で、一番軽い方法を選ぶ
- SDK・フレームワーク・API を使う実装は、先に公式の文書を確認する
- ユーザーが使っている言語で答える

## 任せる・任せないの目安

- **任せる**: 複数ファイルにまたがる変更、リファクタリング、不具合調査、レビュー、計画、調査、検証
- **自分でやる**: ささいな操作、短い確認、コマンド1つで済むこと
- 作る役と確かめる役を分ける。自分で作ったものを同じ文脈で合格にせず、`verifier` や `code-reviewer` に確かめさせる
- 独立した作業が2つ以上あれば並列で進める

## 34体の呼び方

名前だけで呼ぶ（接頭辞は付けない）。全員の得意分野は `agent34-reference` スキルにある。

- **haiku（軽量）**: `explore` `writer` `localization`
- **sonnet（標準）**: `executor` `debugger` `verifier` `tracer` `designer` `qa-tester` `scientist` `test-engineer` `git-master` `document-specialist` `monitor` `optimizer` `database` `api-designer` `devops` `accessibility` `migrator` `prompter` `mobile` `data-pipeline` `ux-researcher`
- **opus（高精度）**: `analyst` `planner` `architect` `code-reviewer` `code-simplifier` `critic` `security-reviewer` `refactorer` `risk-assessor` `compliance`

迷ったときの振り分け: 実装は `executor`／原因調査は `debugger`／探しものは `explore`／設計判断は `architect`／計画は `planner`／完了確認は `verifier`／速度改善は `optimizer`／データベースは `database`／API 設計は `api-designer`／配備と自動化は `devops`／安全性は `security-reviewer`／規制対応は `compliance`／変更リスクは `risk-assessor`／文章は `writer`

エージェントの説明文に出てくる道具（`lsp_*`、`ast_grep_*`、`state_*`、`notepad_*` など）がこの環境に無いときは、標準の道具（ファイルの読み書き・検索・コマンド実行）で同じ目的を果たす。

## キーワード（モード）

ユーザーの発言に次のキーワードがあれば、同じ名前のスキルを開いてその手順に従う。キーワードの意味や使い方を尋ねているだけのときは、起動せずに説明する。

| キーワード | スキル | 内容 |
|---|---|---|
| `ultrawork` / `ulw` | ultrawork | 並列で一気に進める |
| `ralph` | ralph | 合格するまで繰り返す |
| `autopilot` | autopilot | 要件から成果物まで通しで進める |
| `ralplan` | ralplan | 計画を練り、承認を得てから動く |
| `team` | team | 役割を決めて分担する（明示されたときだけ） |
| `tdd` | tdd | テストを先に書く |
| `deslop` / `anti-slop` | deslop | AIっぽさ・無駄を取り除く |
| `deep interview` | deep-interview | 質問で要件を固める |
| `deep-analyze` | deep-analyze | 変更せずに原因と影響を調べる |
| `deepsearch` | deepsearch | 漏れなく探す |
| `ultrathink` | ultrathink | 重要な判断を考え抜く |
| `ccg` | ccg | 3つの視点を突き合わせる |
| `cancelomc` | cancelomc | すぐ止める |

`A → B` と矢印でつながれたら順に、`A + B` と書かれたら同時に適用する。`+エージェント名` は、そのエージェントを必ず使うという指定。

## 作業の種類ごとのおすすめ

次に当てはまり、明らかに効果があるときは、キーワードが無くても同じ流れを使ってよい。ささいな作業（1ファイルの軽い修正、単純な質問、一時的な調べもの）では使わない。

**開発・実装**

- 不具合の修正 → `deep-analyze → ralplan → autopilot + ralph`
- 新機能（既存を壊さない） → `deep-analyze → ralplan → tdd`
- 大規模・多ファイルの実装 → `ultrawork + ralph + autopilot`
- リファクタリング → `deepsearch → deep-analyze → ultrawork`
- 知らないコードの把握 → `deepsearch → deep-analyze → team`
- 速度改善 → `deep-analyze → ralplan → ultrawork` `+optimizer`
- 安全性の点検 → `deep-analyze → ralplan → autopilot` `+security-reviewer` `+compliance`
- API の設計と実装 → `ralplan → tdd → ultrawork` `+api-designer`
- データベースの設計・移行 → `deep-analyze → ralplan → autopilot` `+database`
- 自動テスト・配備の仕組み → `ralplan → autopilot + ralph` `+devops` `+risk-assessor`
- 画面・操作のデザイン → `deep interview → ralplan → ultrawork` `+designer`
- 多言語対応 → `deepsearch → ralplan → autopilot` `+localization`
- モバイルアプリ → `deep-analyze → ralplan → tdd` `+mobile`
- 記録・監視・通知 → `ralplan → ultrawork` `+monitor`

**文章・資料**

- 提案書や企画をゼロから → `deep interview → ultrathink → deslop`
- 急ぎの資料 → `deep interview → ultrawork → deslop`
- 文章の質を上げる → `deslop → ultrathink`
- 技術文書・README → `ralplan → ultrawork` `+writer` `+document-specialist`

**分析・計画**

- 重要な設計判断・技術選定 → `ultrathink`
- 比較して決める → `deep-analyze → ultrathink`
- 何から始めるか不明 → `deep interview`
- 要件があいまいな新規案件 → `deep interview → ralplan → team + ultrawork`
- データ分析・レポート → `deep-analyze → ultrawork` `+scientist`

**緊急**

- 止まらない・暴走している → `cancelomc`、止めたあとに `deep-analyze`
- 設定や環境が壊れた → `deepsearch → deep-analyze`

費用の目安: haiku は軽い検索、sonnet はふだんの作業、opus は設計・安全性・深い分析だけに使う。

## 完了の条件

完了を伝える前に、残っている作業が無いこと、テストや動作確認が通っていること、確かめた証拠があることをそろえる。確かめられなかったことは、その旨を正直に伝える。

作業の記録を残す場所（作業中のプロジェクトのフォルダの中に、必要なときだけ作る）: 計画は `.omc/plans/`、調査メモは `.omc/research/`、覚え書きは `.omc/notepad.md`
<!-- AGENT34:END -->
