#!/usr/bin/env python3
"""Аналитика структуры стада по дню в доении (DIM) и продуктивности групп (WP-118 Ф3).

Вход: raw/excel/Excel-MD/YYYY-MM-DD_dairyplan_produktivnost.md (пересчитанные таблицы).
Расчёт по каждой дате (доящееся стадо = без группы 21 «БРАК» и строк без статуса):
- средний DIM стада;
- структура по диапазонам DIM: 0–100 / 100–200 / 200+;
- средняя продуктивность каждого диапазона (по коровам с надоем > 0).
Выход: reports/herd_dim_structure.md + charts/herd_avg_dim.png
       + charts/herd_dim_structure.png + charts/herd_dim_productivity.png
"""

import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date

CASE = Path("/home/asus/IWE/DS-cattle-cases/cases/CASE-002-zencht-leninsky-dynamics")
MD_DIR = CASE / "raw" / "excel" / "Excel-MD"

records = []  # (data_date, group, status, dim, lact, prod)
for md in sorted(MD_DIR.glob("*_dairyplan_produktivnost.md")):
    d = date.fromisoformat(md.name[:10])
    for line in md.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (\d+) \| (\d*) \| ([^|]*) \| (-?\d+) \| (\d+) \| ([\d.]*) \|", line)
        if not m:
            continue
        records.append((
            d, m.group(2), m.group(3).strip(), int(m.group(4)), int(m.group(5)),
            float(m.group(6)) if m.group(6) else None,
        ))

if not records:
    sys.exit("нет данных")

dates = sorted({r[0] for r in records})
summary = []
for d in dates:
    herd = [r for r in records if r[0] == d and r[1] != "21" and r[2] != ""]
    n = len(herd)
    avg_dim = sum(r[3] for r in herd) / n
    bands = [
        [r for r in herd if r[3] <= 100],
        [r for r in herd if 100 < r[3] <= 200],
        [r for r in herd if r[3] > 200],
    ]
    band_rows = []
    for band in bands:
        milking = [r for r in band if r[5] is not None and r[5] > 0]
        avg_prod = sum(r[5] for r in milking) / len(milking) if milking else 0.0
        band_rows.append((len(band), len(milking), avg_prod))
    summary.append((d, n, avg_dim, *band_rows))

# --- md-отчёт ---
lines = [
    "---",
    "type: analytics",
    "source: raw/excel/Excel-MD/ (46 срезов DairyPlan, 2025-01-01 → 2026-09-02)",
    "wp: 118",
    "status: draft — на проверке пилота",
    "---",
    "",
    "# Структура стада по дню в доении и продуктивность групп — 01.2025 → 09.2026",
    "",
    "> Доящееся стадо = все строки среза, кроме группы 21 («БРАК») и строк без статуса.",
    "> DIM пересчитан на дату данных каждого среза (конвертер dairyplan_to_md.py).",
    "> Продуктивность группы = средний надой по коровам с надоем > 0 (в скобках — их число).",
    "> Диапазоны: свежие 0–100 дн, средние 100–200 дн, поздние 200+ дн.",
    "",
    "## Сводная таблица",
    "",
    "| Дата | Голов | Средний DIM | 0–100: гол (%) | надой | 100–200: гол (%) | надой | 200+: гол (%) | надой |",
    "|---|---|---|---|---|---|---|---|---|",
]
for d, n, avg_dim, b1, b2, b3 in summary:
    row = f"| {d.isoformat()} | {n} | {avg_dim:.0f} "
    for cnt, milk, prod in (b1, b2, b3):
        row += f"| {cnt} ({cnt/n*100:.0f}%) | {prod:.1f} ({milk}) "
    lines.append(row + "|")
lines += [
    "",
    "## Графики",
    "",
    "![Средний DIM стада](../../charts/herd_avg_dim.png)",
    "",
    "![Структура стада по DIM](../../charts/herd_dim_structure.png)",
    "",
    "![Продуктивность групп DIM](../../charts/herd_dim_productivity.png)",
    "",
]
(CASE / "reports" / "herd_dim_structure.md").write_text("\n".join(lines), encoding="utf-8")

# --- графики ---
xs = [s[0] for s in summary]
plt.rcParams["font.family"] = "DejaVu Sans"

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(xs, [s[2] for s in summary], marker="o", ms=3, lw=1.5, color="#1f6f8b")
ax.set_title("Средний день в доении (DIM) всего стада, КТ Зенченко")
ax.set_ylabel("Средний DIM, дней")
ax.grid(alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m.%y"))
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(CASE / "charts" / "herd_avg_dim.png", dpi=120)
plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 5))
p1 = [s[3][0] / s[1] * 100 for s in summary]
p2 = [s[4][0] / s[1] * 100 for s in summary]
p3 = [s[5][0] / s[1] * 100 for s in summary]
ax.stackplot(xs, p1, p2, p3, labels=["0–100 дн", "100–200 дн", "200+ дн"],
             colors=["#7dbb7d", "#f2c14e", "#d9534f"], alpha=0.9)
ax.set_title("Структура стада по дню в доении (доли от доящегося стада)")
ax.set_ylabel("Доля, %")
ax.set_ylim(0, 100)
ax.legend(loc="upper right")
ax.grid(alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m.%y"))
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(CASE / "charts" / "herd_dim_structure.png", dpi=120)
plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(xs, [s[3][2] for s in summary], marker="o", ms=3, lw=1.8, color="#4a8c4a", label="0–100 дн (свежие)")
ax.plot(xs, [s[4][2] for s in summary], marker="o", ms=3, lw=1.5, color="#c9930a", label="100–200 дн")
ax.plot(xs, [s[5][2] for s in summary], marker="o", ms=3, lw=1.5, color="#b03a3a", label="200+ дн")
ax.axvline(date(2026, 6, 1), color="#333", ls="--", lw=1, alpha=0.6)
ax.text(date(2026, 6, 3), ax.get_ylim()[0] + 1, "01.06.2026", fontsize=8, color="#333")
ax.set_title("Средняя продуктивность групп DIM (по коровам с надоем > 0), КТ Зенченко")
ax.set_ylabel("Средний надой, кг")
ax.legend(loc="upper right")
ax.grid(alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m.%y"))
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(CASE / "charts" / "herd_dim_productivity.png", dpi=120)
plt.close(fig)

first, last = summary[0], summary[-1]
print(f"срезов: {len(summary)}; записей: {len(records)}")
print(f"первый {first[0]}: {first[1]} гол, DIM {first[2]:.0f}, надой 0-100: {first[3][2]:.1f}")
print(f"последний {last[0]}: {last[1]} гол, DIM {last[2]:.0f}, надой 0-100: {last[3][2]:.1f}")
jun = [s for s in summary if s[0] >= date(2026, 6, 1)]
print("0-100 с 01.06.2026:", [(s[0].isoformat(), round(s[3][2], 1)) for s in jun])
