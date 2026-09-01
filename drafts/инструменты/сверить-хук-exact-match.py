# -*- coding: utf-8 -*-
"""
Сверка двух проверок exact_match: питоновской и джаваскриптовой.

Запрет на `set_value` без явного `exact_match` живёт в двух копиях —
хук Claude Code `.claude/hooks/check_exact_match.py` и плагин OpenCode
`.opencode/plugin/exact-match.js`. Копии нужны потому, что инструменты
устроены по-разному: один читает JSON со stdin, другой перехватывает
вызов инструмента внутри процесса.

Две копии расходятся молча: правишь одну, вторая продолжает жить своей
жизнью, и одна и та же модель на одной и той же базе ведёт себя
по-разному в зависимости от того, чем её запустили. Этот скрипт
превращает молчаливое расхождение в громкое.

Запуск из корня проекта:

    python drafts/инструменты/сверить-хук-exact-match.py

Нужен node в PATH. Возвращает 0, если обе копии согласны на всех
случаях, и 1, если хотя бы на одном разошлись.
"""

import io
import json
import os
import pathlib
import subprocess
import sys

КОРЕНЬ = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
ХУК = os.path.join(КОРЕНЬ, ".claude", "hooks", "check_exact_match.py")
ПЛАГИН = os.path.join(КОРЕНЬ, ".opencode", "plugin", "exact-match.js")

# ── случаи: (описание, имя инструмента, аргументы, ожидаем блокировку) ──
СЛУЧАИ = [
    ("set_value без exact_match",
     "manage_form_elements",
     {"action": "set_value", "element_name": "Организация", "value": "Крон-Ц"},
     True),

    ("set_value с exact_match: true",
     "manage_form_elements",
     {"action": "set_value", "element_name": "Организация", "exact_match": True},
     False),

    ("set_value с exact_match: false — осознанный выбор, пропускаем",
     "manage_form_elements",
     {"action": "set_value", "element_name": "Организация", "exact_match": False},
     False),

    ("другое действие того же инструмента",
     "manage_form_elements",
     {"action": "click_button", "element_name": "ФормаСоздать"},
     False),

    ("цепочка: во второй строке set_value без exact_match",
     "execute_form_actions",
     {"actions_json": json.dumps([
         {"action": "click_button", "element_name": "ФормаСоздать"},
         {"action": "set_value", "element_name": "СпособВыплаты", "value": "Аванс"},
     ], ensure_ascii=False)},
     True),

    ("цепочка: все set_value с exact_match",
     "execute_form_actions",
     {"actions_json": json.dumps([
         {"action": "set_value", "element_name": "Организация", "exact_match": True},
         {"action": "input_text", "element_name": "Дата", "value": "31.01.2026"},
     ], ensure_ascii=False)},
     False),

    ("цепочка без set_value вовсе",
     "execute_form_actions",
     {"actions_json": json.dumps([
         {"action": "click_button", "element_name": "Заполнить"},
     ], ensure_ascii=False)},
     False),

    ("битый actions_json — не наше дело, пусть падает штатно",
     "execute_form_actions",
     {"actions_json": "{это не json"},
     False),

    ("посторонний инструмент",
     "get_table_data",
     {"object_name": "НачислениеЗарплаты"},
     False),
]

# Разбор аргументов ВНЕ try: иначе опечатка в обвязке выглядит как
# срабатывание плагина, и сверка радостно врёт про расхождение.
JS_ОБВЯЗКА = """
import { ExactMatch } from %s
const хвост = process.argv.slice(-2)
const tool = хвост[0]
const args = JSON.parse(хвост[1])
const плагин = await ExactMatch({})
try {
  await плагин["tool.execute.before"]({ tool }, { args })
  console.log("PASS")
} catch (e) {
  console.log("BLOCK")
}
"""


def через_питон(инструмент, аргументы):
    полное = "mcp__VA__" + инструмент
    вход = json.dumps({"tool_name": полное, "tool_input": аргументы}, ensure_ascii=False)
    п = subprocess.run([sys.executable, ХУК], input=вход.encode("utf-8"),
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    вывод = п.stdout.decode("utf-8", "replace").strip()
    if not вывод:
        return "PASS", ""
    ответ = json.loads(вывод)
    решение = ответ.get("hookSpecificOutput", {}).get("permissionDecision")
    причина = ответ.get("hookSpecificOutput", {}).get("permissionDecisionReason", "")
    return ("BLOCK" if решение == "deny" else "PASS"), причина


def через_node(инструмент, аргументы):
    # На Windows ESM-загрузчик node принимает только file:// — обычный
    # путь вида C:\... он считает протоколом «c:» и падает.
    ссылка = json.dumps(pathlib.Path(ПЛАГИН).as_uri())
    скрипт = JS_ОБВЯЗКА % ссылка
    п = subprocess.run(["node", "--input-type=module", "-e", скрипт,
                        "--", "va_" + инструмент,
                        json.dumps(аргументы, ensure_ascii=False)],
                       stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    вывод = п.stdout.decode("utf-8", "replace").strip()
    if вывод not in ("PASS", "BLOCK"):
        строки = п.stderr.decode("utf-8", "replace").strip().split("\n")
        внятные = [с for с in строки if "Error" in с or "error" in с]
        return "ОШИБКА", (внятные or строки or ["node молчит"])[0].strip()
    return вывод, ""


def главная():
    for путь in (ХУК, ПЛАГИН):
        if not os.path.exists(путь):
            print("Не найден файл: %s" % путь)
            return 1

    расхождений = 0
    print("%-52s %-8s %-8s %s" % ("случай", "python", "node", "итог"))
    print("-" * 80)

    for описание, инструмент, аргументы, ждём_блок in СЛУЧАИ:
        п_решение, _ = через_питон(инструмент, аргументы)
        н_решение, ошибка = через_node(инструмент, аргументы)
        ожидание = "BLOCK" if ждём_блок else "PASS"

        if н_решение == "ОШИБКА":
            итог = "node не запустился: " + ошибка
            расхождений += 1
        elif п_решение != н_решение:
            итог = "РАСХОЖДЕНИЕ"
            расхождений += 1
        elif п_решение != ожидание:
            итог = "обе не так, ждали " + ожидание
            расхождений += 1
        else:
            итог = "ок"

        print("%-52s %-8s %-8s %s" % (описание[:52], п_решение, н_решение, итог))

    print()
    if расхождений:
        print("Расхождений: %d. Копии разъехались — править обе." % расхождений)
        return 1
    print("Обе копии согласны на всех %d случаях." % len(СЛУЧАИ))
    return 0


if __name__ == "__main__":
    sys.exit(главная())
