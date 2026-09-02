#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Собирает все уникальные шаги проекта в один feature-файл.

Зачем. `check_syntax` проверяет ОДИН файл за вызов, а feature-файлов
в проекте под две сотни. Этот скрипт собирает из них все уникальные
строки шагов в один сводный файл — и вся проверка укладывается в один
вызов MCP.

Как пользоваться:

    python drafts/инструменты/собрать-шаги-для-проверки.py

Дальше в Claude Code или OpenCode, ОБЯЗАТЕЛЬНО двумя вызовами:

    open_feature_file(filePath=".../drafts/tmp/сводная-проверка.feature")
    check_syntax(filePath=".../drafts/tmp/сводная-проверка.feature")

БЕЗ open_feature_file результат врёт: Vanessa отдаёт разбор того файла,
что остался у неё в редакторе с прошлого раза. Проверено 02.09.2026 —
свежесобранный файл сначала отрапортовал «проблем нет», а после
open_feature_file в нём же нашлось 566 несуществующих шагов.

Рядом кладётся карта.json: номер строки в сводном файле → где этот шаг
встречается в проекте. По ней ошибки возвращаются к исходным файлам.
"""

import io
import json
import os
import glob

КОРЕНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ВЫХОД = os.path.join(КОРЕНЬ, "drafts", "tmp", "сводная-проверка.feature")
КАРТА = os.path.join(КОРЕНЬ, "drafts", "tmp", "карта.json")

# строки, с которых начинается шаг Gherkin
НАЧАЛА = ("И ", "Дано ", "Когда ", "Тогда ", "Затем ", "Если ",
          "Иначе", "КонецЕсли", "Для ", "КонецЦикла")
# служебные строки, шагами не являющиеся
ПРОПУСК = ("#", "@", "|", "*")


def собрать():
    шаблоны = ["drafts/словари/*.feature", ".claude/skills/*/*.feature",
               "authoring/**/*.feature", "drafts/инструменты/*.feature"]
    файлы = []
    for ш in шаблоны:
        файлы += glob.glob(os.path.join(КОРЕНЬ, ш), recursive=True)
    файлы = sorted(set(файлы))

    шаги = {}
    for ф in файлы:
        текст = io.open(ф, encoding="utf-8-sig").read().replace("\r\n", "\n")
        for н, строка in enumerate(текст.split("\n"), 1):
            s = строка.strip()
            if not s or s.startswith(ПРОПУСК):
                continue
            if not s.startswith(НАЧАЛА):
                continue
            шаги.setdefault(s, []).append([os.path.relpath(ф, КОРЕНЬ), н])

    порядок = list(шаги)
    строки = ["#language: ru", "", "Функционал: сводная проверка шагов",
              "", "Сценарий: все шаги проекта"]
    строки += ["\t" + s for s in порядок]

    os.makedirs(os.path.dirname(ВЫХОД), exist_ok=True)
    io.open(ВЫХОД, "w", encoding="utf-8-sig", newline="").write("\n".join(строки))
    # +6: пять строк шапки плюс единица за нумерацию с единицы
    json.dump({str(i + 6): шаги[s] for i, s in enumerate(порядок)},
              io.open(КАРТА, "w", encoding="utf-8"), ensure_ascii=False)

    print("файлов прочитано: %d" % len(файлы))
    print("уникальных шагов: %d" % len(порядок))
    print("собрано: %s" % ВЫХОД)
    print("карта:   %s" % КАРТА)


if __name__ == "__main__":
    собрать()
