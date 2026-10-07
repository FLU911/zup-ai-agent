// Плагин OpenCode: не пускает set_value без явного exact_match.
//
// Это ЗЕРКАЛО хука Claude Code .claude/hooks/check_exact_match.py.
// Правишь одно — правь второе, иначе два инструмента начнут вести себя
// по-разному на одной и той же базе. После правки прогони сверку:
//   python drafts/инструменты/сверить-хук-exact-match.py
//
// Причина запрета — 28.08.2026, половина вечера на диагностику пустой
// ведомости. set_value по умолчанию ищет по ПОДСТРОКЕ в списке выбора и
// молча подставляет не тот элемент справочника, рапортуя об успехе.
// Подробности: drafts/ЛОВУШКА-set_value-exact_match.md
//
// Блокируется ОТСУТСТВИЕ ключа, а не значение false. Нужен подстрочный
// поиск — напиши exact_match: false, и плагин пропустит. Смысл в том,
// чтобы выбор был сделан, а не забыт.

const ПРИЧИНА = [
  "По умолчанию идёт поиск ПО ПОДСТРОКЕ — в поле молча встанет другой",
  "элемент справочника, а инструмент отрапортует об успехе.",
  "Добавь exact_match: true. Если подстрочный поиск нужен осознанно —",
  "напиши exact_match: false явно.",
  "См. drafts/ЛОВУШКА-set_value-exact_match.md",
].join("\n")

function нарушители(имяИнструмента, аргументы) {
  const плохие = []
  if (!аргументы || typeof аргументы !== "object") return плохие

  if (имяИнструмента.endsWith("manage_form_elements")) {
    if (аргументы.action === "set_value" && !("exact_match" in аргументы)) {
      плохие.push(аргументы.element_name || "<без имени>")
    }
    return плохие
  }

  if (имяИнструмента.endsWith("execute_form_actions")) {
    const сырое = аргументы.actions_json ?? "[]"
    let действия
    try {
      действия = typeof сырое === "string" ? JSON.parse(сырое) : сырое
    } catch {
      return плохие // не наше дело — пусть падает штатно
    }
    if (!Array.isArray(действия)) return плохие
    действия.forEach((д, i) => {
      if (!д || typeof д !== "object") return
      if (д.action === "set_value" && !("exact_match" in д)) {
        плохие.push(`#${i + 1} ${д.element_name || "<без имени>"}`)
      }
    })
  }

  return плохие
}

export const ExactMatch = async () => ({
  "tool.execute.before": async (input, output) => {
    const плохие = нарушители(input.tool || "", output.args)
    if (плохие.length === 0) return
    throw new Error(
      `set_value без exact_match: ${плохие.join(", ")}.\n${ПРИЧИНА}`,
    )
  },
})
