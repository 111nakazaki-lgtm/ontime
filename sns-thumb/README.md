# sns-thumb

写真 + 一言 から、Instagram / Threads / X / note 用のサムネを書き出します。

## 毎日の流れ
1. 携帯の写真を Google ドライブ等で同期し、`inbox/` に置く
2. Claude が写真を選び、文章(フォロワー約2,000人向けの親しみやすいトーン)を考える
3. `python make_thumbs.py inbox/写真.jpg "一言" --sub "補足"` で書き出し
4. `out/` の画像を確認してから投稿(最初は手動確認)

## 出力サイズ
- instagram / threads: 1080x1350
- x: 1600x900
- note(記事アイキャッチ): 1280x670

## 必要なもの
- Python 3 と Pillow (`pip install pillow`)
- 日本語フォント(見つからない場合は `make_thumbs.py` の `FONT_CANDIDATES` に追加)

## 注意
他人の投稿・写真の転載や SNS のスクレイピングはしない方針です。
自分で撮った写真と、公式 API を使った自分のアカウントの投稿に限ります。
