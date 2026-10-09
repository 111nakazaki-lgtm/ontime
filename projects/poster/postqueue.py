"""キューファイル(1行1投稿、#で始まる行は無視、文中の \\n は改行)の読み書きと長さの確認。"""
import os

HERE = os.path.dirname(os.path.abspath(__file__))


def path_for(name: str) -> str:
    return os.path.join(HERE, "queues", f"{name}.txt")


def is_post(line: str) -> bool:
    return bool(line.strip()) and not line.startswith("#")


def read(path: str):
    with open(path, encoding="utf-8") as f:
        return [l.rstrip("\n") for l in f]


def pop(path: str):
    """先頭の投稿と、それを除いた残りの行を返す。空なら (None, None)。"""
    lines = read(path)
    for i, l in enumerate(lines):
        if is_post(l):
            return l, lines[:i] + lines[i + 1:]
    return None, None


def write(path: str, lines) -> None:
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + ("\n" if lines else ""))


def decode(line: str) -> str:
    return line.replace("\\n", "\n")


def too_long(path: str, measure, limit: int):
    """キューの中で長すぎる投稿を (文字数, 行) で返す。先頭に来るとキューが止まるため。"""
    posts = [l for l in read(path) if is_post(l)]
    return len(posts), [(measure(decode(l)), l) for l in posts if measure(decode(l)) > limit]
