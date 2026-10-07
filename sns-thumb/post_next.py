#!/usr/bin/env python3
"""threads/queue から、次の1本を選んで Threads に投稿する(文章のみ)。

  python post_next.py --slot morning            # 確認のみ(投稿しない)
  python post_next.py --slot night --publish    # 実際に投稿

選ぶ条件: slot が一致 / verified: yes / threads/posted.txt に未記録。
verified: no の投稿(体験の細部を本人が未確認のもの)は、絶対に投稿しない。
"""
import argparse
import subprocess
import sys
from pathlib import Path

BASE = Path(__file__).parent / "threads"
POSTED = BASE / "posted.txt"


def load(p):
    head, _, body = p.read_text().partition("\n---\n")
    meta = dict(line.split(": ", 1) for line in head.splitlines() if ": " in line)
    return meta, body.strip()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--slot", required=True, choices=["morning", "night"])
    ap.add_argument("--publish", action="store_true")
    a = ap.parse_args()
    done = set(POSTED.read_text().split()) if POSTED.exists() else set()
    for p in sorted((BASE / "queue").glob("*.txt")):
        meta, body = load(p)
        if p.stem in done or meta.get("slot") != a.slot or meta.get("verified") != "yes":
            continue
        print(f"選んだ投稿: {p.stem}")
        cmd = [sys.executable, str(Path(__file__).parent / "threads_post.py"), "-", body]
        if a.publish:
            cmd.append("--publish")
        r = subprocess.run(cmd)
        if r.returncode == 0 and a.publish:
            with POSTED.open("a") as f:
                f.write(p.stem + "\n")
        sys.exit(r.returncode)
    print(f"{a.slot} 枠で、投稿できる(verified: yes・未投稿の)文章がありません。補充してください。")
    sys.exit(3)


if __name__ == "__main__":
    main()
