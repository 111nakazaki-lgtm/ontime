---
name: agent34-check
description: 34体エージェント環境の点検。「34体チェック」「agent34 check」「キットの点検」と言われたとき、またはキットの導入直後・更新後に、エージェントとスキルが正しく入って動くかを確かめたいときに使う。
---

# agent34-check — 導入状態を点検する

キットが正しく入り、実際に動くことを確かめる。直せる不具合はその場で直す。

## 1. ファイルの点検（検証スクリプト）

使える方を実行する。どちらも読み取りだけを行う。

- bash が使える場合: `sh ~/.claude/agent34-kit/payload/scripts/verify.sh`
- Windows で PowerShell を使う場合: `powershell -NoProfile -ExecutionPolicy Bypass -File "$HOME\.claude\agent34-kit\payload\scripts\verify.ps1"`

最後の行が `RESULT: PASS` なら合格。`FAIL` の行があれば内容を読み、次のように直してからもう一度実行する（最大3回）。

| FAIL の内容 | 直し方 |
|---|---|
| missing file / content differs | インストールスクリプト（同じフォルダの `install.sh` または `install.ps1`）をもう一度実行する |
| CLAUDE.md markers / block | 同上（ブロックだけが入れ直される。ほかの記述は残る） |
| privacy pattern | 該当ファイルと行を確認し、ユーザーに報告する。勝手に消さない |

`WARN ... same name` が出たら、同じ名前の別ファイルがあるとユーザーに伝える（消すかどうかはユーザーが決める）。

## 2. 動作の点検（実際に呼び出す）

モデル区分ごとに1体ずつ、短い依頼で呼び出す。3つは同時に出してよい。

| 区分 | エージェント | 依頼の例 |
|---|---|---|
| haiku | `explore` | 「`~/.claude/agents` にある .md ファイルの数を数えて、数字だけ答えて」 |
| sonnet | `verifier` | 「1+1=2 が正しいかを確かめ、合格か不合格かを1行で答えて」 |
| opus | `architect` | 「設定ファイルを1つにまとめる利点を1文で答えて」 |

- 3体とも答えが返れば合格
- 「そのエージェントは無い」と出たら、Claude Code を一度終了して開き直す必要がある。ユーザーに「再起動してから、もう一度『34体チェック』と入力してください」と伝える
- opus だけ使えないときは、契約プランで使えない可能性がある。`~/.claude/agents` の該当ファイルの `model: opus` を `model: sonnet` に変える方法をユーザーに案内する（変えると検証スクリプトは「content differs」を出すが、意図した変更なので問題ない）

## 3. スキルの点検

利用できるスキルの一覧に、次の15個が出ているかを確かめる: `ultrawork` `ralph` `autopilot` `ralplan` `team` `tdd` `deslop` `deep-interview` `deep-analyze` `deepsearch` `ultrathink` `ccg` `cancelomc` `agent34-reference` `agent34-check`

出ていないものがあれば、再起動後にもう一度確かめる。

## 4. 報告

次の形で、日本語で短く報告する。

- ファイルの点検: 合格 / 不合格（直した内容）
- 動作の点検: haiku・sonnet・opus それぞれの結果
- スキルの点検: 15個中いくつ認識されたか
- 個人情報の点検: 検証スクリプトの privacy scan の結果
- 残っている作業（あれば）
