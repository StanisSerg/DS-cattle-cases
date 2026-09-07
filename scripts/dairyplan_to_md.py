#!/usr/bin/env python3
"""Конвертация Excel-отчёта DairyPlan «Мол. продуктивность» в md-таблицу кейса.

Правила обработки (WP-118, решения пилота 2026-09-07):
- дата данных берётся из имени файла (YYYY-MM-DD.xlsx);
- DairyPlan считает «День лактации» до даты выгрузки отчёта (по умолчанию — день
  запуска скрипта), поэтому из значения вычитается число дней между датой данных
  и датой выгрузки;
- если вычитание даёт отрицательный результат — программа зафиксировала день
  лактации на событии (перевод в сухостой, выбраковка), значение уже реальное:
  оставляем исходное и перечисляем таких коров в примечании;
- столбцы «Пик продуктивности» и «Пик прод-ть день» опускаются;
- служебные строки (пустые, итог «T NNN») пропускаются.

Использование:
  python3 dairyplan_to_md.py <case_dir> <xlsx> [--report-date YYYY-MM-DD]

Пример:
  python3 dairyplan_to_md.py cases/CASE-002-zencht-leninsky-dynamics \
      cases/CASE-002-zencht-leninsky-dynamics/raw/excel/2025-01-01.xlsx
"""

import argparse
import re
import sys
from datetime import date
from pathlib import Path

import openpyxl


def main() -> int:
    parser = argparse.ArgumentParser(description="DairyPlan xlsx → md-таблица кейса")
    parser.add_argument("case_dir", type=Path, help="папка кейса (с raw/ внутри)")
    parser.add_argument("xlsx", type=Path, help="Excel-отчёт DairyPlan (имя = дата данных)")
    parser.add_argument("--report-date", type=date.fromisoformat, default=date.today(),
                        help="дата выгрузки отчёта (default: сегодня)")
    args = parser.parse_args()

    m = re.fullmatch(r"(\d{4}-\d{2}-\d{2})\.xlsx", args.xlsx.name)
    if not m:
        print(f"ошибка: имя файла должно быть YYYY-MM-DD.xlsx, получено: {args.xlsx.name}")
        return 1
    data_date = date.fromisoformat(m.group(1))
    delta = (args.report_date - data_date).days
    if delta < 0:
        print(f"ошибка: дата данных {data_date} позже даты выгрузки {args.report_date}")
        return 1

    out_path = args.case_dir / "raw" / f"dairyplan_produktivnost_{m.group(1)}.md"

    wb = openpyxl.load_workbook(args.xlsx, data_only=True)
    ws = wb.worksheets[0]

    rows = []
    skipped = []
    for r in ws.iter_rows(min_row=6, values_only=True):
        num, dim = r[0], r[3]
        if not isinstance(num, (int, float)) or not isinstance(dim, (int, float)):
            skipped.append(r)
            continue
        dim_int = int(dim)
        fixed_event = dim_int - delta < 0
        rows.append((
            int(num),
            r[1] if r[1] is not None else "",
            r[2] if r[2] else "",
            dim_int if fixed_event else dim_int - delta,
            int(r[4]) if r[4] is not None else "",
            fixed_event,
        ))

    fixed = [r for r in rows if r[5]]

    lines = [
        "---",
        "type: raw-table",
        f"source: raw/excel/{args.xlsx.name} (DairyPlan, «Мол. продуктивность»)",
        f"data_date: {data_date.isoformat()}",
        f"report_generated: {args.report_date.isoformat()}",
        f"day_shift: -{delta} (День лактации пересчитан на дату данных)",
        "wp: 118",
        "---",
        "",
        f"# Молочная продуктивность стада — данные на {data_date.strftime('%d.%m.%Y')}",
        "",
        f"> День лактации пересчитан: DairyPlan считал до даты выгрузки ({args.report_date.strftime('%d.%m.%Y')}), вычтено {delta} дн.",
        "> Столбцы «Пик продуктивности» и «Пик прод-ть день» опущены (решение пилота).",
        f"> Строк: {len(rows)} животных. Пропущено служебных строк: {len(skipped)}.",
    ]
    if fixed:
        nums = ", ".join(str(r[0]) for r in fixed)
        lines.append(
            f"> Для {len(fixed)} коров ({nums}) день лактации оставлен исходным: "
            "программа зафиксировала его на событии (перевод в сухостой / выбраковка), пересчёт не применялся."
        )
    lines += [
        "",
        "| Номер животного | Группа | Статус | День лактации | Номер лактации |",
        "|---|---|---|---|---|",
    ]
    for r in rows:
        lines.append(f"| {r[0]} | {r[1]} | {r[2]} | {r[3]} | {r[4]} |")
    lines.append("")

    out_path.write_text("\n".join(lines), encoding="utf-8")
    print(f"written: {out_path}")
    print(f"rows: {len(rows)}, fixed: {len(fixed)}, skipped: {len(skipped)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
