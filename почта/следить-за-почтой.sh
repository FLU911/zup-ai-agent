#!/usr/bin/env bash
# Наблюдатель за входящей почтой 1С (вариант для bash).
#
# Каждые N секунд просит агента выполнить один тик по регламенту
# ЦИКЛ-мониторинг-почты.md. Работает и с Claude Code, и с OpenCode:
#
#   ./следить-за-почтой.sh                 # claude, интервал из настроек
#   ./следить-за-почтой.sh opencode        # opencode
#   ./следить-за-почтой.sh claude 300      # свой интервал, секунды
#   ODIN_TIK=1 ./следить-за-почтой.sh      # один тик и выход
#
# Останавливается по Ctrl+C.
#
# Имена переменных латиницей не по вкусу, а по необходимости: bash
# разрешает в именах только латиницу, цифры и подчёркивание. С кириллицей
# скрипт падал на первой же строке: «ИНСТРУМЕНТ=claude: command not found».

set -u

TOOL="${1:-claude}"
MAIL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$MAIL_DIR")"
SETTINGS="$MAIL_DIR/настройки.json"

if [ ! -f "$SETTINGS" ]; then
    echo "Нет файла настройки.json."
    echo "Скопируйте настройки.example.json в настройки.json и впишите свои адреса."
    exit 1
fi

INTERVAL="${2:-}"
if [ -z "$INTERVAL" ]; then
    INTERVAL=$(python -c "import json,io;print(json.load(io.open(r'$SETTINGS',encoding='utf-8')).get('интервал-проверки-секунд',60))" 2>/dev/null || echo 60)
fi

TASK="Выполни один тик почтового цикла строго по регламенту почта/ЦИКЛ-мониторинг-почты.md.
Коротко: подключить клиент тестирования, забрать почту командой «Отправить и получить»
в журнале «Взаимодействия», сравнить входящие с почта/обработанные.json.
Если есть новое письмо с адреса из белого списка в почта/настройки.json — выполнить
задание по правилам CLAUDE.md, ответить письмом, убедиться что оно ушло, обновить
почта/обработанные.json и почта/журнал.md.
Новых писем нет — ничего не делать и ничего не писать."

tick() {
    echo "[$(date +%H:%M:%S)] проверяю почту ($TOOL)"
    cd "$PROJECT_ROOT" || return 1
    if [ "$TOOL" = "claude" ]; then
        claude -p "$TASK" || echo "тик не удался"
    else
        opencode run --auto --dir "$PROJECT_ROOT" "$TASK" || echo "тик не удался"
    fi
}

if [ "${ODIN_TIK:-}" = "1" ]; then
    tick
    exit 0
fi

echo "Слежу за почтой: $TOOL, каждые $INTERVAL с. Ctrl+C — остановить."
while true; do
    tick
    sleep "$INTERVAL"
done
