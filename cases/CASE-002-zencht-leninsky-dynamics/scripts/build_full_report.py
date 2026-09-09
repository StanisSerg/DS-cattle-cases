#!/usr/bin/env python3
"""Сборка полного отчёта: итоговый отчёт + приложения 1–3 одним файлом.

Вход:
  reports/Отчет_ЖК2_итоговый_2026-09-08.md  — основной текст (frontmatter снимается)
  reports/herd_dim_structure.md             — Приложение 1
  reports/cull_analysis_2026-09-08.md       — Приложение 2
  reports/2026-09-02-kazakhstan-ketones-explanation.pdf — Приложение 3 (текст извлекается markitdown)
Выход: reports/Отчет_ЖК2_итоговый_полный_2026-09-08.md

Запуск: python3 scripts/build_full_report.py
"""
import re
import sys
from pathlib import Path

CASE = Path(__file__).resolve().parent.parent
REPORTS = CASE / "reports"

OUT = REPORTS / "Отчет_ЖК2_итоговый_полный_2026-09-08.md"

APPENDICES = [
    ("Приложение 1. Доказательная аналитика продуктивности", REPORTS / "herd_dim_structure.md"),
    ("Приложение 2. Выбытие из стада (забой и падеж)", REPORTS / "cull_analysis_2026-09-08.md"),
]
APPENDIX3_MD = Path("/home/asus/IWE/PACK-cattle-science/dept-practices/problems/2026-09-02-kazakhstan-ketones-explanation.md")


def strip_frontmatter(text: str) -> str:
    return re.sub(r"\A---\n.*?\n---\n+", "", text, flags=re.S).strip()


def read_md(path: Path) -> str:
    return strip_frontmatter(path.read_text(encoding="utf-8"))


def main() -> None:
    main_report = read_md(REPORTS / "Отчет_ЖК2_итоговый_2026-09-08.md")

    parts = [main_report]
    for title, path in APPENDICES:
        parts.append(f'<div style="page-break-before: always;"></div>\n\n# {title}\n\n{read_md(path)}')

    ketones = read_md(APPENDIX3_MD)
    parts.append(
        '<div style="page-break-before: always;"></div>\n\n'
        "# Приложение 3. Мониторинг кетонов ранней лактации\n\n"
        f"> Источник: `reports/{APPENDIX3_MD.name[:-3]}.pdf` (PDF) / исходный текст — PACK-cattle-science/dept-practices/problems/{APPENDIX3_MD.name}.\n\n{ketones}"
    )

    OUT.write_text("\n\n".join(parts) + "\n", encoding="utf-8")
    print(f"OK: {OUT}")


if __name__ == "__main__":
    main()
