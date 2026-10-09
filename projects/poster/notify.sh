#!/usr/bin/env bash
# 投稿結果を Issue「投稿ログ」にコメントして通知する(@メンションで通知が届く)。
# 使い方: notify.sh queue|ad ログファイル     必要な環境変数: GH_TOKEN OWNER RUN_URL
set -u
mode="$1"; log="$2"

# summary 見出し ログ  — ログの内容から1行にまとめる
summary() {
  f="$1"
  if [ ! -s "$f" ]; then echo "⚠️ 記録なし(実行されませんでした)"
  elif grep -q "投稿しました" "$f"; then echo "✅ 投稿しました — $(head -1 "$f")"
  elif grep -q "キューが空" "$f"; then echo "⚪ キューが空(投稿なし)"
  elif grep -q "期間外" "$f"; then echo "⚪ 期間外(投稿なし)"
  elif grep -q "スキップ" "$f"; then echo "⚪ スキップ(シークレット未設定)"
  else echo "❌ 失敗 — $(grep -m1 'エラー' "$f" || tail -n 1 "$f")"; fi
}

now="$(TZ=Asia/Tokyo date '+%m/%d %H:%M')"
if [ "$mode" = "ad" ]; then
  body="@${OWNER} 広告投稿の結果です(${now} JST)

- 広告: $(summary "$log")"
else
  grep '^\[x\]' "$log" > /tmp/x.log || true
  grep '^\[threads\]' "$log" > /tmp/threads.log || true
  body="@${OWNER} 定期投稿の結果です(${now} JST)

- X: $(summary /tmp/x.log)
- Threads: $(summary /tmp/threads.log)"
fi
body="${body}

詳細: ${RUN_URL}"

num=$(gh issue list --state open --search '投稿ログ in:title' --json number --jq '.[0].number // empty')
if [ -z "$num" ]; then
  num=$(gh issue create --title "投稿ログ" --body "定期投稿の結果を、ここにコメントで残します。" | grep -o '[0-9]*$')
fi
gh issue comment "$num" --body "$body"
