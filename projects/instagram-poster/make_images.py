"""x-poster/images の写真を、Instagram に出せる形(JPEG・縦横比 4:5〜1.91:1・幅1080以下)にして images/ に作る。

Instagram は 9:16 や 3:4 の縦長写真を断るので、中央で 4:5 に切り抜く。
既に作ってある写真は飛ばす。新しい写真を x-poster/images に足したら、これを実行する。
  python3 projects/instagram-poster/make_images.py
"""
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SRC = HERE.parent / "x-poster" / "images"  # ad-poster の写真は「イメージ」で本人撮影ではないので使わない
OUT = HERE / "images"

OUT.mkdir(exist_ok=True)
for p in sorted(f for f in SRC.iterdir() if f.suffix.lower() in (".jpg", ".jpeg", ".png")):
    o = OUT / (p.stem + ".jpg")
    if o.exists():
        continue
    im = Image.open(p).convert("RGB")
    w, h = im.size
    if w / h < 0.8:
        nh = round(w / 0.8)
        t = (h - nh) // 2
        im = im.crop((0, t, w, t + nh))
    elif w / h > 1.91:
        nw = round(h * 1.91)
        l = (w - nw) // 2
        im = im.crop((l, 0, l + nw, h))
    w, h = im.size
    if w > 1080:
        im = im.resize((1080, round(h * 1080 / w)), Image.LANCZOS)
    im.save(o, "JPEG", quality=88)
    print("作成:", o.name, im.size)
