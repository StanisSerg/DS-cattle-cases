#!/usr/bin/env python3
"""Экспорт полного отчёта в PDF (weasyprint).

Вход:  reports/Отчет_ЖК2_итоговый_полный_2026-09-08.md (сборник build_full_report.py)
Выход: reports/Отчет_ЖК2_итоговый_полный_2026-09-08.pdf

Графики разрешаются относительно reports/ (ссылки ../charts/...).
Запуск: python3 scripts/export_full_report_pdf.py
"""
from pathlib import Path

import markdown
from weasyprint import CSS, HTML

REPORTS = Path(__file__).resolve().parent.parent / "reports"
SRC = REPORTS / "Отчет_ЖК2_итоговый_полный_2026-09-08.md"
OUT = REPORTS / "Отчет_ЖК2_итоговый_полный_2026-09-08.pdf"

CSS_TEXT = """
@page {
    size: A4;
    margin: 1.8cm;
    @bottom-center { content: counter(page); font-family: "DejaVu Sans"; font-size: 9pt; color: #666; }
}
body { font-family: "DejaVu Serif", serif; font-size: 10.5pt; line-height: 1.45; color: #222; text-align: justify; hyphens: auto; }
h1, h2, h3, h4 { font-family: "DejaVu Sans", sans-serif; color: #111; page-break-after: avoid; text-align: left; hyphens: none; }
h1 { font-size: 17pt; }
h2 { font-size: 13.5pt; margin-top: 1.1em; }
h3 { font-size: 11.5pt; margin-top: 1em; }
table { border-collapse: collapse; width: 100%; font-size: 9pt; margin: 0.6em 0; page-break-inside: auto; }
th, td { border: 0.5pt solid #999; padding: 2.5pt 5pt; text-align: left; vertical-align: top; }
th { background: #eef1f4; font-family: "DejaVu Sans", sans-serif; }
tr { page-break-inside: avoid; }
.wide-table table { table-layout: fixed; font-size: 7.5pt; }
.wide-table th, .wide-table td { padding: 1.5pt 2pt; overflow-wrap: break-word; }
img { max-width: 100%; }
blockquote { color: #555; border-left: 2.5pt solid #ccc; margin-left: 0; padding-left: 0.8em; }
code { font-family: "DejaVu Sans Mono", monospace; font-size: 9pt; }
hr { border: none; border-top: 0.5pt solid #aaa; margin: 1.2em 0; }
"""


def main() -> None:
    text = SRC.read_text(encoding="utf-8")
    body = markdown.markdown(text, extensions=["tables", "fenced_code", "md_in_html"])
    html = f"<!DOCTYPE html><html lang='ru'><head><meta charset='utf-8'></head><body>{body}</body></html>"
    HTML(string=html, base_url=str(REPORTS)).write_pdf(str(OUT), stylesheets=[CSS(string=CSS_TEXT)])
    print(f"OK: {OUT}")


if __name__ == "__main__":
    main()
