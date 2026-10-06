---
name: agent34-reference
description: 34体の専門エージェントと各モードの早見表。どのエージェントに頼むか迷ったとき、エージェントの一覧・得意分野・モデル区分を確認したいとき、キーワードや組み合わせの一覧を見たいときに使う。
---

# agent34-reference — 34体とモードの早見表

## 34体の専門エージェント

呼ぶときは名前だけを使う（接頭辞は付けない）。「編集」が「不可」のエージェントは調べて報告するだけで、ファイルは書き換えない。

| エージェント | 分類 | 得意なこと | 区分 | 編集 |
|---|---|---|---|---|
| `analyst` | 計画・設計 | 要件の抜け・隠れた前提・範囲外を洗い出す | opus | 不可 |
| `planner` | 計画・設計 | 手順と完了条件を組み立て、実行計画を作る | opus | 可 |
| `architect` | 計画・設計 | 設計判断、構造の見直し、難しい不具合への助言 | opus | 不可 |
| `critic` | 計画・設計 | 計画や案の弱点を多角的に批判・点検する | opus | 不可 |
| `executor` | 実装 | 指示された変更を最小の差分で実装する | sonnet | 可 |
| `debugger` | 実装 | 不具合・ビルドエラーの根本原因を突き止めて直す | sonnet | 可 |
| `tracer` | 実装 | 複数の仮説を証拠で比べ、原因をたどる | sonnet | 可 |
| `refactorer` | 実装 | 大規模な構造の組み替えと技術的負債の解消 | opus | 可 |
| `code-simplifier` | 実装 | 動作を変えずにコードを読みやすく整える | opus | 可 |
| `migrator` | 実装 | フレームワーク更新や仕様変更に伴う移行 | sonnet | 可 |
| `optimizer` | 実装 | 計測にもとづく速度・メモリの改善 | sonnet | 可 |
| `verifier` | 品質 | 完了条件を証拠で確かめ、合否を判定する | sonnet | 可 |
| `qa-tester` | 品質 | 実際に動かして操作し、動作を確かめる | sonnet | 可 |
| `test-engineer` | 品質 | テスト方針の設計とテストの作成・安定化 | sonnet | 可 |
| `code-reviewer` | 品質 | 重要度つきのコードレビュー（正しさ・保守性） | opus | 不可 |
| `security-reviewer` | 品質 | 脆弱性・秘密情報・危険な書き方の点検 | opus | 不可 |
| `risk-assessor` | 品質 | 変更の影響範囲と戻しにくさの評価 | opus | 不可 |
| `compliance` | 品質 | 個人情報保護・決済・監査などの規制対応の確認 | opus | 不可 |
| `accessibility` | 品質 | 画面のアクセシビリティ（WCAG）の点検と修正案 | sonnet | 一部 |
| `database` | 専門領域 | テーブル設計、クエリ改善、移行計画 | sonnet | 可 |
| `api-designer` | 専門領域 | API の設計、版管理、仕様書づくり | sonnet | 可 |
| `devops` | 専門領域 | 自動テスト・配備の仕組み、コンテナ構成 | sonnet | 可 |
| `monitor` | 専門領域 | ログ・計測・追跡・通知の設計 | sonnet | 可 |
| `data-pipeline` | 専門領域 | データの取り込み・加工・連携処理 | sonnet | 可 |
| `mobile` | 専門領域 | iOS・Android・React Native の開発 | sonnet | 可 |
| `designer` | 専門領域 | 画面と操作のデザインと実装 | sonnet | 可 |
| `ux-researcher` | 専門領域 | 使いやすさの分析、つまずく箇所の特定 | sonnet | 不可 |
| `prompter` | 専門領域 | AI への指示文（プロンプト）の設計と改善 | sonnet | 可 |
| `scientist` | 専門領域 | データ分析と統計にもとづく検証 | sonnet | 不可 |
| `explore` | 調査・文章 | ファイルやコードを素早く探して全体像をつかむ | haiku | 不可 |
| `document-specialist` | 調査・文章 | 公式文書・外部資料を調べて根拠を示す | sonnet | 不可 |
| `writer` | 調査・文章 | README・手順書・説明文を書く | haiku | 可 |
| `localization` | 調査・文章 | 多言語対応と翻訳、地域ごとの調整 | haiku | 可 |
| `git-master` | 調査・文章 | コミットの整理、履歴の管理 | sonnet | 可 |

「編集」の「一部」は、既存のファイルの修正はできるが、新しいファイルの作成はできないという意味です。

### モデル区分の考え方

- **haiku**（軽量・安い）: すぐ終わる検索や短い文章
- **sonnet**（標準）: 実装・調査・検証などふだんの作業
- **opus**（高精度・高い）: 設計、深い分析、重要なレビュー

## モード（キーワード）

| キーワード | ひとことで | 向いている場面 |
|---|---|---|
| `ultrawork`（`ulw`） | 並列で一気に進める | 独立した作業がいくつもあるとき |
| `ralph` | 合格するまで繰り返す | 途中で止まらず、やりきってほしいとき |
| `autopilot` | 要件から成果物まで通しで進める | まるごと任せたいとき |
| `ralplan` | 計画を練り、承認を得てから動く | 実行前に計画を確認したいとき |
| `team` | 役割を決めて分担する | 複数の作業を担当制で進めたいとき |
| `tdd` | テストを先に書く | 既存の動きを壊したくないとき |
| `deslop` | AIっぽさ・無駄を取り除く | 文章やコードをすっきりさせたいとき |
| `deep interview` | 質問で要件を固める | 何から始めるか決まっていないとき |
| `deep-analyze` | 変更せずに原因と影響を調べる | 直す前に状況をつかみたいとき |
| `deepsearch` | 漏れなく探す | 関係する箇所を全部洗い出したいとき |
| `ultrathink` | 重要な判断を考え抜く | 技術選定や比較検討をするとき |
| `ccg` | 3つの視点を突き合わせる | 設定方法や方針を多面的に確かめたいとき |
| `cancelomc` | すぐ止める | 止まらない・思っていない動きをしているとき |

## 定番の組み合わせ

| 場面 | 組み合わせ |
|---|---|
| 不具合を直す | `deep-analyze → ralplan → autopilot + ralph` |
| 新機能を足す（既存を壊さない） | `deep-analyze → ralplan → tdd` |
| 計画を確認してから安全に足す | `ralplan → tdd` |
| 大規模・多ファイルの実装 | `ultrawork + ralph + autopilot` |
| リファクタリング | `deepsearch → deep-analyze → ultrawork` |
| 知らないコードを把握する | `deepsearch → deep-analyze → team` |
| 遅い処理を速くする | `deep-analyze → ralplan → ultrawork +optimizer` |
| 安全性を点検する | `deep-analyze → ralplan → autopilot +security-reviewer` |
| API を設計して作る | `ralplan → tdd → ultrawork +api-designer` |
| データベースを設計・移行する | `deep-analyze → ralplan → autopilot +database` |
| 自動テスト・配備の仕組みを作る | `ralplan → autopilot + ralph +devops +risk-assessor` |
| 画面をデザインする | `deep interview → ralplan → ultrawork +designer` |
| 提案書・企画をゼロから作る | `deep interview → ultrathink → deslop` |
| 急ぎで資料を作る | `deep interview → ultrawork → deslop` |
| 文章の質を上げる | `deslop → ultrathink` |
| 技術文書・README を作る | `ralplan → ultrawork +writer` |
| 比較して決める | `deep-analyze → ultrathink` |
| 要件があいまいな新規案件 | `deep interview → ralplan → team + ultrawork` |
| データを分析して報告する | `deep-analyze → ultrawork +scientist` |
| 止まらない・暴走している | `cancelomc`、止めたあとに `deep-analyze` |

詳しい使い方は `~/.claude/agent34-kit/GUIDE.md` にある。
