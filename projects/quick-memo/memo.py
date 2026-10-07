import sys
from datetime import datetime
from pathlib import Path

FILE = Path(__file__).with_name("memo.txt")


def main(argv):
    if argv:
        with FILE.open("a", encoding="utf-8") as f:
            f.write(f"{datetime.now():%Y-%m-%d %H:%M} {' '.join(argv)}\n")
    elif FILE.exists():
        print(FILE.read_text(encoding="utf-8"), end="")


if __name__ == "__main__":
    main(sys.argv[1:])
