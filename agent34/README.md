# AGENT34 キット（Windows 向け導入手順）

34体の専門エージェントと13モードを、PC全体（`%USERPROFILE%\.claude`）に導入するキットです。
このリポジトリにはキット本体と手順だけを置き、プロジェクトのファイルには影響しません。

## 導入手順（PC で一度だけ）

1. このリポジトリを取得（clone / pull）する
2. PC で Claude Code を開き、`agent34/AGENT34-KIT.md` を添付して次のように送信する
   > このキットの手順どおりに構築してください
3. Claude Code が展開・導入・検証（`RESULT: PASS`）まで自動で行う（Windows では PowerShell 版を使用）
4. Claude Code を一度終了して開き直し、「34体チェック」と入力する

## 補足

- 書き込み先は `%USERPROFILE%\.claude` のみ。`settings.json` は変更されない
- 同名の既存ファイルは `agent34-kit\backup-日時\` に退避される
- 詳しい使い方: `AGENT34-導入手順と使い方ガイド.pdf`
- 止めたいときは `cancelomc`

## かんたん起動（Windows）

`START-AGENT34.bat` をダブルクリックすると、Claude Code が起動してキットの構築が始まります（`claude` コマンドが入っていること）。
許可を求められたら、`%USERPROFILE%\.claude` への書き込みとキット付属スクリプトの実行だけ許可してください。終わったら Claude Code を開き直して「34体チェック」と入力します。
