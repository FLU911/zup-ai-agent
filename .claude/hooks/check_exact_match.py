#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""PreToolUse: не пускает set_value без явного exact_match.

Причина — 28.08.2026 половина вечера ушла на диагностику пустой ведомости.
set_value по умолчанию ищет по ПОДСТРОКЕ в списке выбора и молча
подставляет не тот элемент справочника, рапортуя об успехе.
Подробности: drafts/ЛОВУШКА-set_value-exact_match.md

Блокируется отсутствие ключа, а не значение false. Если подстрочный
поиск нужен осознанно — напиши exact_match: false, и хук пропустит.
Смысл в том, чтобы выбор был сделан, а не забыт.
"""
import io, json, sys

# Консоль Windows по умолчанию cp1251 — без этого причина отказа
# приходит крякозябрами.
try:
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8",
                                  errors="replace", newline="")
except Exception:
    pass


def offenders(tool_name, tool_input):
    """Список описаний действий set_value без ключа exact_match."""
    bad = []

    if tool_name.endswith("manage_form_elements"):
        if tool_input.get("action") == "set_value" and "exact_match" not in tool_input:
            bad.append(tool_input.get("element_name") or "<без имени>")

    elif tool_name.endswith("execute_form_actions"):
        raw = tool_input.get("actions_json") or "[]"
        try:
            actions = json.loads(raw) if isinstance(raw, str) else raw
        except Exception:
            return bad  # не наше дело — пусть падает штатно
        if not isinstance(actions, list):
            return bad
        for i, a in enumerate(actions):
            if not isinstance(a, dict):
                continue
            if a.get("action") == "set_value" and "exact_match" not in a:
                bad.append(f"#{i + 1} {a.get('element_name') or '<без имени>'}")

    return bad


def main():
    try:
        data = json.loads(sys.stdin.buffer.read().decode("utf-8", errors="replace"))
    except Exception:
        return  # не смогли разобрать — не мешаем

    tool_name = data.get("tool_name") or ""
    tool_input = data.get("tool_input") or {}
    if not isinstance(tool_input, dict):
        return

    bad = offenders(tool_name, tool_input)
    if not bad:
        return

    reason = (
        "set_value без exact_match: " + ", ".join(bad) + ".\n"
        "По умолчанию идёт поиск ПО ПОДСТРОКЕ — в поле молча встанет "
        "другой элемент справочника, а инструмент отрапортует об успехе.\n"
        "Добавь exact_match: true. Если подстрочный поиск нужен осознанно — "
        "напиши exact_match: false явно.\n"
        "См. drafts/ЛОВУШКА-set_value-exact_match.md"
    )
    out = {
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }
    sys.stdout.write(json.dumps(out, ensure_ascii=False))


if __name__ == "__main__":
    main()
