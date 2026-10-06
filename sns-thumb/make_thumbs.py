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


def make(photo, text, sub, size):
    w, h = size
    img = ImageOps.fit(ImageOps.exif_transpose(Image.open(photo)).convert("RGB"), size)

    # 下から暗くして白文字を読みやすくする
    grad = Image.new("L", (1, h))
    for y in range(h):
        grad.putpixel((0, y), int(200 * max(0, (y - h * 0.35) / (h * 0.65)) ** 1.2))
    shade = Image.new("RGB", size, (0, 0, 0))
    img = Image.composite(shade, img, grad.resize(size))

    d = ImageDraw.Draw(img)
    margin = int(w * 0.08)
    fsize = int(w * 0.09)
    font = load_font(fsize)
    lines = wrap(d, text, font, w - margin * 2)
    while len(lines) > 3 and fsize > 30:
        fsize -= 4
        font = load_font(fsize)
        lines = wrap(d, text, font, w - margin * 2)

    sub_font = load_font(int(fsize * 0.45))
    block_h = len(lines) * int(fsize * 1.25) + (int(fsize * 0.7) if sub else 0)
    y = h - margin - block_h
    for ln in lines:
        d.text((margin, y), ln, font=font, fill="white",
               stroke_width=max(2, fsize // 22), stroke_fill="black")
        y += int(fsize * 1.25)
    if sub:
        d.text((margin, y), sub, font=sub_font, fill=(235, 235, 235))
    return img


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("photo")
    ap.add_argument("text")
    ap.add_argument("--sub", default="")
    ap.add_argument("--out", default="out")
    a = ap.parse_args()
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    stem = Path(a.photo).stem
    for name, size in SIZES.items():
        path = out / f"{stem}_{name}.jpg"
        make(a.photo, a.text, a.sub, size).save(path, quality=92)
        print(path)


if __name__ == "__main__":
    main()
