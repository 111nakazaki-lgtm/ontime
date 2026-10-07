#!/usr/bin/env python3
"""写真 + 文章 から、SNSごとのサイズのサムネを書き出す。

使い方:
  python make_thumbs.py 写真.jpg "大きく載せる一言" [--sub "小さい補足"] [--out out]
"""
import argparse
import sys
from pathlib import Path

from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

SIZES = {
    "instagram": (1080, 1350),
    "threads": (1080, 1350),
    "x": (1600, 900),
    "note": (1280, 670),
}
FONT_CANDIDATES = [
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Bold.ttc",
    "C:/Windows/Fonts/meiryob.ttc",
    "C:/Windows/Fonts/YuGothB.ttc",
    "/System/Library/Fonts/ヒラギノ角ゴシック W8.ttc",
    "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
    "/usr/share/fonts/opentype/ipafont-gothic/ipag.ttf",
]


def load_font(size):
    for p in FONT_CANDIDATES:
        if Path(p).exists():
            return ImageFont.truetype(p, size)
    sys.exit("日本語フォントが見つかりません。FONT_CANDIDATES に追加してください。")


def wrap(draw, text, font, max_w):
    lines, cur = [], ""
    for ch in text:
        if ch == "\n" or draw.textlength(cur + ch, font=font) > max_w:
            lines.append(cur)
            cur = "" if ch == "\n" else ch
        else:
            cur += ch
    if cur:
        lines.append(cur)
    return lines


def make(photo, text, sub, size, crop_left=0.0):
    w, h = size
    src = ImageOps.exif_transpose(Image.open(photo)).convert("RGB")
    if crop_left:
        src = src.crop((int(src.width * crop_left), 0, src.width, src.height))

    portrait = h > w
    if portrait:
        # 背景はぼかした拡大写真。写真本体は切らずに幅いっぱいに載せ、下に文字の帯を作る
        img = ImageOps.fit(src, size).filter(ImageFilter.GaussianBlur(30))
        img = Image.blend(img, Image.new("RGB", size, (0, 0, 0)), 0.35)
        ph = int(src.height * w / src.width)
        img.paste(src.resize((w, ph)), (0, int(h * 0.06)))
        fsize = int(w * 0.075)
    else:
        img = ImageOps.fit(src, size)
        grad = Image.new("L", (1, h))
        for y in range(h):
            grad.putpixel((0, y), int(210 * max(0, (y - h * 0.72) / (h * 0.28)) ** 1.1))
        img = Image.composite(Image.new("RGB", size, (0, 0, 0)), img, grad.resize(size))
        fsize = int(w * 0.04)

    d = ImageDraw.Draw(img)
    margin = int(w * 0.06)
    font = load_font(fsize)
    lines = wrap(d, text, font, w - margin * 2)
    max_lines = 2 if portrait else 1
    while len(lines) > max_lines and fsize > 24:
        fsize -= 3
        font = load_font(fsize)
        lines = wrap(d, text, font, w - margin * 2)

    sub_font = load_font(int(fsize * 0.5))
    lh = int(fsize * 1.25)
    block_h = len(lines) * lh + (int(fsize * 0.8) if sub else 0)
    y = h - margin - block_h
    for ln in lines:
        d.text((margin, y), ln, font=font, fill="white",
               stroke_width=max(2, fsize // 22), stroke_fill="black")
        y += lh
    if sub:
        d.text((margin, y), sub, font=sub_font, fill=(240, 240, 240))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("text")
    ap.add_argument("--sub", default="")
    ap.add_argument("--out", default="out")
    ap.add_argument("--crop-left", type=float, default=0.0,
                    help="左端を切り落とす割合(0.12=左12%%。写り込んだ人物を除く用)")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(a.photo).stem
    for name, size in SIZES.items():
        path = out / f"{stem}_{name}.jpg"
        make(a.photo, a.text, a.sub, size, a.crop_left).save(path, quality=92)
        print(path)


if __name__ == "__main__":
    main()
