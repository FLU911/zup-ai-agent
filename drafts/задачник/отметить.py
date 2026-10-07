# -*- coding: utf-8 -*-
"""Отметить задание в реестре.

    python drafts/задачник/отметить.py 3.1 решено "что сделано"

Статусы: решено / частично / заблокировано / в работе / не начато.
"""
import io
import json
import os
import sys

РЕЕСТР = os.path.join(os.path.dirname(os.path.abspath(__file__)), "РЕЕСТР.json")

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


def главная():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    номер, статус = sys.argv[1], sys.argv[2]
    заметка = sys.argv[3] if len(sys.argv) > 3 else ""

    d = json.load(io.open(РЕЕСТР, encoding="utf-8"))
    найдено = False
    for з in d["задания"]:
        if з["номер"] == номер:
            з["статус"] = статус
            if заметка:
                з["примечание"] = заметка
            найдено = True
    if not найдено:
        print("Нет такого задания:", номер)
        return 1
    io.open(РЕЕСТР, "w", encoding="utf-8").write(
        json.dumps(d, ensure_ascii=False, indent=1))

    счёт = {}
    for з in d["задания"]:
        счёт[з["статус"]] = счёт.get(з["статус"], 0) + 1
    print("%s → %s" % (номер, статус))
    print("Итого:", ", ".join("%s %d" % (к, в) for к, в in sorted(счёт.items())))
    return 0


if __name__ == "__main__":
    sys.exit(главная())
