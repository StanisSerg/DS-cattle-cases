#!/usr/bin/env python3
"""Аналитика структуры стада по дню в доении (DIM) по массиву таблиц DairyPlan (WP-118 Ф3).

Вход: raw/excel/Excel-MD/YYYY-MM-DD_dairyplan_produktivnost.md (пересчитанные таблицы).
Расчёт: по каждой дате — средний DIM доящегося стада (без группы 21 «БРАК» и строк
без статуса) и структура по диапазонам DIM: 0–100 / 100–200 / 200+.
Выход: reports/herd_dim_structure.md + charts/herd_avg_dim.png + charts/herd_dim_structure.png
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

records = []  # (data_date, group, status, dim)
for md in sorted(MD_DIR.glob("*_dairyplan_produktivnost.md")):
    d = date.fromisoformat(md.name[:10])
    for line in md.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (\d+) \| (\d*) \| ([^|]*) \| (-?\d+) \| (\d+) \|", line)
        if not m:
            continue
        num, grp, status, dim, lact = m.group(1), m.group(2), m.group(3).strip(), int(m.group(4)), int(m.group(5))
        records.append((d, grp, status, dim))

if not records:
    sys.exit("нет данных")

dates = sorted({r[0] for r in records})
summary = []
for d in dates:
    herd = [r for r in records if r[0] == d and r[1] != "21" and r[2] != ""]
    n = len(herd)
    avg = sum(r[3] for r in herd) / n
    b1 = sum(1 for r in herd if r[3] <= 100)
    b2 = sum(1 for r in herd if 100 < r[3] <= 200)
    b3 = sum(1 for r in herd if r[3] > 200)
    summary.append((d, n, avg, b1, b2, b3))

# --- md-отчёт ---
lines = [
    "---",
    "type: analytics",
    "source: raw/excel/Excel-MD/ (46 срезов DairyPlan, 2025-01-01 → 2026-09-02)",
    "wp: 118",
    "status: draft — на проверке пилота",
    "---",
    "",
    "# Структура стада по дню в доении (DIM) — динамика 01.2025 → 09.2026",
    "",
    "> Доящееся стадо = все строки среза, кроме группы 21 («БРАК») и строк без статуса.",
    "> DIM пересчитан на дату данных каждого среза (конвертер dairyplan_to_md.py).",
    "> Диапазоны: свежие 0–100 дн, средние 100–200 дн, поздние 200+ дн.",
    "",
    "## Сводная таблица",
    "",
    "| Дата | Голов | Средний DIM | 0–100 дн | % | 100–200 дн | % | 200+ дн | % |",
    "|---|---|---|---|---|---|---|---|---|",
]
for d, n, avg, b1, b2, b3 in summary:
    lines.append(
        f"| {d.isoformat()} | {n} | {avg:.0f} | {b1} | {b1/n*100:.1f}% | {b2} | {b2/n*100:.1f}% | {b3} | {b3/n*100:.1f}% |"
    )
lines += [
    "",
    "## Графики",
    "",
    "![Средний DIM стада](../../charts/herd_avg_dim.png)",
    "",
    "![Структура стада по DIM](../../charts/herd_dim_structure.png)",
    "",
]
(CASE / "reports").mkdir(exist_ok=True)
(CASE / "reports" / "herd_dim_structure.md").write_text("\n".join(lines), encoding="utf-8")

# --- графики ---
xs = [s[0] for s in summary]
avg = [s[2] for s in summary]
p1 = [s[3] / s[1] * 100 for s in summary]
p2 = [s[4] / s[1] * 100 for s in summary]
p3 = [s[5] / s[1] * 100 for s in summary]

plt.rcParams["font.family"] = "DejaVu Sans"
fig, ax = plt.subplots(figsize=(12, 5))
ax.plot(xs, avg, marker="o", ms=3, lw=1.5, color="#1f6f8b")
ax.set_title("Средний день в доении (DIM) всего стада, КТ Зенченко")
ax.set_ylabel("Средний DIM, дней")
ax.grid(alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m.%y"))
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(CASE / "charts" / "herd_avg_dim.png", dpi=120)
plt.close(fig)

fig, ax = plt.subplots(figsize=(12, 5))
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

first, last = summary[0], summary[-1]
print(f"срезов: {len(summary)}; записей: {len(records)}")
print(f"первый {first[0]}: {first[1]} гол, средний DIM {first[2]:.0f}, 200+: {first[5]/first[1]*100:.1f}%")
print(f"последний {last[0]}: {last[1]} гол, средний DIM {last[2]:.0f}, 200+: {last[5]/last[1]*100:.1f}%")
