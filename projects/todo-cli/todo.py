import json
import sys
from pathlib import Path

DB = Path(__file__).with_name("todos.json")


def load():
    return json.loads(DB.read_text(encoding="utf-8")) if DB.exists() else []


def save(items):
    DB.write_text(json.dumps(items, ensure_ascii=False, indent=2), encoding="utf-8")


def main(argv):
    items = load()
    cmd = argv[0] if argv else "list"
    if cmd == "add" and len(argv) > 1:
        items.append({"text": " ".join(argv[1:]), "done": False})
        save(items)
    elif cmd == "done" and len(argv) > 1 and argv[1].isdigit():
        i = int(argv[1]) - 1
        if 0 <= i < len(items):
            items[i]["done"] = True
            save(items)
    elif cmd != "list":
        print("usage: todo.py [list | add TEXT | done N]")
        return 1
    for n, t in enumerate(items, 1):
        print(f"{n}. [{'x' if t['done'] else ' '}] {t['text']}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
