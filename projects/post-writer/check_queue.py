"""キューの全行が投稿できる長さか確かめる。長すぎる行は先頭に来るとキューが止まるため。"""
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
QUEUES = {
    "x": (ROOT / "projects/x-poster/queue.txt", 280,
          lambda t: sum(1 if ord(c) <= 0x10FF or 0x2000 <= ord(c) <= 0x200D else 2 for c in t)),
    "threads": (ROOT / "projects/threads-poster/queue.txt", 500, len),
}

bad = 0
for name, (path, limit, measure) in QUEUES.items():
    lines = [l.rstrip("\n") for l in path.open(encoding="utf-8")]
    posts = [l for l in lines if l.strip() and not l.startswith("#")]
    for l in posts:
        n = measure(l.replace("\\n", "\n"))
        if n > limit:
            bad += 1
            print(f"[{name}] 長すぎ {n}/{limit}: {l[:30]}…")
    print(f"{name}: {len(posts)}本")
sys.exit(1 if bad else 0)
