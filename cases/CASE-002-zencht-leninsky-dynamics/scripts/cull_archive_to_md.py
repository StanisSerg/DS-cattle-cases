#!/usr/bin/env python3
"""Конвертер архива выбытия DairyPlan (xlsx) → md-таблица.

Вход:  raw/архив выбытия <дата>.xlsx (отчёт «Перечень поголовья (вкл. животных архива)»)
Выход: raw/excel/Excel-MD/<дата выгрузки>_dairyplan_cull_archive.md

Структура xlsx (Лист1, данные с 8-й строки):
  кол0  № животного (внутр.)
  кол1  номер бирки
  кол3  группа
  кол4  дата рождения
  кол6  дата прихода (покупки)
  кол9  дата выбытия
  кол13 дата последнего отёла
  кол14 способ выбытия (ЗАБОЙ / Продажа / Падеж / ВЫБРАКОВКА — регистр как в источнике)
  кол15 причина / примечание

Фильтр: дата выбытия >= CUTOFF. Значения не исправляются (регистр, пробелы — как в источнике).

Запуск: python3 scripts/cull_archive_to_md.py
"""
import collections
import datetime
import sys
from pathlib import Path

import openpyxl

CASE_DIR = Path(__file__).resolve().parent.parent
CUTOFF = datetime.datetime(2025, 1, 1)


def find_source() -> Path:
    candidates = sorted(CASE_DIR.glob("raw/архив выбытия *.xlsx"), key=lambda p: p.stat().st_mtime)
    if not candidates:
        sys.exit("Источник не найден: raw/архив выбытия *.xlsx")
    return candidates[-1]


def fmt_date(v) -> str:
    return v.strftime("%Y-%m-%d") if isinstance(v, datetime.datetime) else "—"


def fmt(v) -> str:
    if v is None or v == "":
        return "—"
    return str(v).replace("|", "\\|").strip()


def main() -> None:
    src = find_source()
    export_date = src.stem.split()[-1]  # «2.09.2026»
    day, month, year = export_date.split(".")
    date_iso = f"{year}-{int(month):02d}-{int(day):02d}"

    wb = openpyxl.load_workbook(src, read_only=True)
    ws = wb[wb.sheetnames[0]]
    data = list(ws.iter_rows(min_row=8, values_only=True))

    culled = [r for r in data if isinstance(r[9], datetime.datetime) and r[9] >= CUTOFF]
    culled.sort(key=lambda r: r[9])

    out = CASE_DIR / "raw" / "excel" / "Excel-MD" / f"{date_iso}_dairyplan_cull_archive.md"
    ways = collections.Counter(fmt(r[14]) for r in culled)
    with_reason = sum(1 for r in culled if r[15])

    lines = [
        "---",
        "type: raw-table",
        f"source: raw/{src.name}",
        f"export_date: {date_iso}",
        f'filter: "дата выбытия >= {CUTOFF.date()}"',
        f"records: {len(culled)}",
        "generated_by: scripts/cull_archive_to_md.py",
        "---",
        "",
        f"# Архив выбытия — {date_iso} (DairyPlan, «Перечень поголовья вкл. архив»)",
        "",
        f"> Источник: `{src.relative_to(CASE_DIR)}`. Записей с датой выбытия от {CUTOFF.date()}: **{len(culled)}**",
        f"> (диапазон {fmt_date(culled[0][9])} → {fmt_date(culled[-1][9])}). Из них с указанной причиной: {with_reason}.",
        "> Способы выбытия как в источнике (регистр не нормализован): "
        + ", ".join(f"{k} — {v}" for k, v in ways.most_common()) + ".",
        "> Группы и причины — как в выгрузке, без интерпретации.",
        "",
        "| Дата выбытия | № животного | Бирка | Гр | Дата рождения | Дата прихода | Последний отёл | Способ | Причина |",
        "|---|---|---|---|---|---|---|---|---|",
    ]
    for r in culled:
        lines.append(
            "| " + " | ".join([
                fmt_date(r[9]),
                fmt(r[0]),
                fmt(r[1]),
                fmt(r[3]),
                fmt_date(r[4]),
                fmt_date(r[6]),
                fmt_date(r[13]),
                fmt(r[14]),
                fmt(r[15]),
            ]) + " |"
        )

    out.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"OK: {out} ({len(culled)} записей)")


if __name__ == "__main__":
    main()
