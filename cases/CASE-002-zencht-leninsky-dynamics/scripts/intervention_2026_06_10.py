#!/usr/bin/env python3
"""Парный before/after анализ интервенции в рационы 10.06.2026 (WP-118 Ф3).

Вопрос: рост продуктивности после 10.06.2026 — эффект рациона или композиционный
эффект отёлов мая (аргумент зоотехника)?

Метод:
1. Когорта: коровы, доившиеся на 10.06.2026 (срез в день интервенции) и найденные
   в срезе 10.07.2026 (prod > 0 в обоих). Новые коровы (отёлы мая, вошедшие после)
   в когорту не входят по построению — композиционный эффект исключён.
2. Разбивка по DIM на 10.06: 0–60 (физиологический рост к пику), 60–150 (плато),
   150+ (физиологический спад). Ожидания по кривой лактации учтены разбивкой.
3. Контроль сезонности: те же окна 2025 года (срезы 01.06/20.06/01.07.2025 —
   среза 10.06.2025 нет, окно шире, честно помечено).
4. Идентичность коровы проверяется по сдвигу DIM между срезами (±2 дня от окна).

Выход: reports/intervention_2026-06-10.md + charts/intervention_2026-06-10.png
"""

import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from datetime import date

CASE = Path("/home/asus/IWE/DS-cattle-cases/cases/CASE-002-zencht-leninsky-dynamics")
MD_DIR = CASE / "raw" / "excel" / "Excel-MD"


def load(d: date) -> dict:
    """номер -> (dim, prod, group, status); без гр.21 и строк без статуса"""
    out = {}
    md = MD_DIR / f"{d.isoformat()}_dairyplan_produktivnost.md"
    for line in md.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (\d+) \| (\d*) \| ([^|]*) \| (-?\d+) \| (\d+) \| ([\d.]*) \|", line)
        if not m:
            continue
        grp, status = m.group(2), m.group(3).strip()
        if grp == "21" or not status:
            continue
        prod = float(m.group(6)) if m.group(6) else None
        out[int(m.group(1))] = (int(m.group(4)), prod, grp, status)
    return out


def pair_analysis(d0: date, d1: date):
    """Пары «тот же номер, prod>0 в обоих срезах», контроль сдвига DIM."""
    before, after = load(d0), load(d1)
    window = (d1 - d0).days
    pairs = []
    for num, (dim0, prod0, grp0, st0) in before.items():
        if num not in after:
            continue
        dim1, prod1, _, _ = after[num]
        if prod0 is None or prod1 is None or prod0 <= 0 or prod1 <= 0:
            continue
        if abs((dim1 - dim0) - window) > 2:
            continue  # DIM не сошёлся — запись сомнительна
        pairs.append((num, dim0, prod0, prod1))
    return pairs, len(before)


def band_stats(pairs):
    bands = {"0–60 (рост к пику)": lambda d: d <= 60,
             "60–150 (плато)": lambda d: 60 < d <= 150,
             "150+ (спад)": lambda d: d > 150}
    out = {}
    for name, f in bands.items():
        sel = [(p0, p1) for _, dim, p0, p1 in pairs if f(dim)]
        if not sel:
            out[name] = None
            continue
        deltas = [p1 - p0 for p0, p1 in sel]
        out[name] = dict(
            n=len(sel),
            avg0=sum(p0 for p0, _ in sel) / len(sel),
            avg1=sum(p1 for _, p1 in sel) / len(sel),
            delta=sum(deltas) / len(deltas),
            up=sum(1 for x in deltas if x > 0.05),
            down=sum(1 for x in deltas if x < -0.05),
        )
    total_d = [p1 - p0 for _, _, p0, p1 in pairs]
    out["ИТОГО"] = dict(
        n=len(pairs),
        avg0=sum(p for _, _, p, _ in pairs) / len(pairs),
        avg1=sum(p for _, _, _, p in pairs) / len(pairs),
        delta=sum(total_d) / len(total_d),
        up=sum(1 for x in total_d if x > 0.05),
        down=sum(1 for x in total_d if x < -0.05),
    )
    return out


# --- интервенция 2026 ---
pairs26, n_before26 = pair_analysis(date(2026, 6, 10), date(2026, 7, 10))
stats26 = band_stats(pairs26)

# --- контроль 2025 (окна: 01.06→01.07; среза 10.06.2025 нет) ---
pairs25, n_before25 = pair_analysis(date(2025, 6, 1), date(2025, 7, 1))
stats25 = band_stats(pairs25)


def fmt(stats):
    rows = []
    for name, s in stats.items():
        if s is None:
            rows.append(f"| {name} | 0 | — | — | — | — | — |")
            continue
        rows.append(
            f"| {name} | {s['n']} | {s['avg0']:.1f} | {s['avg1']:.1f} "
            f"| {s['delta']:+.1f} | {s['up']} ({s['up']/s['n']*100:.0f}%) | {s['down']} ({s['down']/s['n']*100:.0f}%) |"
        )
    return rows


lines = [
    "---",
    "type: analytics-causal",
    "intervention: изменение рационов 10.06.2026",
    "wp: 118",
    "status: draft — на проверке пилота",
    "---",
    "",
    "# Влияние интервенции 10.06.2026: эффект рациона vs эффект отёлов",
    "",
    "**Вопрос:** зоотехник считает, что рост продуктивности летом 2026 — не от изменения",
    "рационов 10.06, а от отёлов мая (в стадо вошли свежие высокопродуктивные коровы).",
    "",
    "**Метод:** парный before/after по одним и тем же коровам. В когорту входят только",
    "коровы, доившиеся на 10.06.2026 и найденные в срезе 10.07.2026 — коровы, вошедшие",
    "после отёлов мая, здесь отсутствуют по построению, значит композиционный эффект",
    "исключён. Ожидания по кривой лактации учтены разбивкой по DIM: свежие растут",
    "физиологически, поздние — падают. Контроль — то же окно 2025 года.",
    "",
    "## Интервенция 2026: 10.06 → 10.07 (30 дней)",
    "",
    f"Доящихся на 10.06.2026: {n_before26}; в паре (есть надой в обоих срезах, DIM сошёлся): {len(pairs26)}.",
    "",
    "| Когорта (DIM на 10.06) | N | Надой 10.06 | Надой 10.07 | Δ средн. | Выросли | Упали |",
    "|---|---|---|---|---|---|---|",
    *fmt(stats26),
    "",
    "## Контроль сезонности 2025: 01.06 → 01.07 (30 дней, среза 10.06.2025 нет)",
    "",
    f"Доящихся на 01.06.2025: {n_before25}; в паре: {len(pairs25)}.",
    "",
    "| Когорта (DIM на 01.06) | N | Надой 01.06 | Надой 01.07 | Δ средн. | Выросли | Упали |",
    "|---|---|---|---|---|---|---|",
    *fmt(stats25),
    "",
    "## График",
    "",
    "![Парный before/after](../../charts/intervention_2026-06-10.png)",
    "",
    "## Ограничения метода",
    "",
    "- Окно 2025 года сдвинуто на 10 дней раньше (нет среза 10.06.2025) — сравнение год-к-году приближённое.",
    "- Учтены только коровы с надоем > 0 в обоих срезах; ушедшие в сухостой/выбраковку между срезами выпадают (выживаемость).",
    "- Жара июля 2026 частично перекрывает окно — занижает эффект, не завышает.",
]

# --- темп роста новотельных (DIM 0–60) по всем парам соседних срезов ---
all_dates = sorted(f.name[:10] for f in MD_DIR.glob("*_dairyplan_produktivnost.md"))
growth = []  # (окно_конец, год, месяц_начала, темп кг/30дн, n)
for a, b in zip(all_dates, all_dates[1:]):
    d0, d1 = date.fromisoformat(a), date.fromisoformat(b)
    pairs, _ = pair_analysis(d0, d1)
    fresh = [(p0, p1) for _, dim, p0, p1 in pairs if dim <= 60]
    if len(fresh) < 10:
        continue
    window = (d1 - d0).days
    rate = (sum(p1 - p0 for p0, p1 in fresh) / len(fresh)) / window * 30
    growth.append((d1, d0.year, d0.month, rate, len(fresh)))

lines += [
    "",
    "## Темп роста новотельных коров (DIM 0–60), кг за 30 дней — вся история",
    "",
    "Парный прирост одних и тех же свежих коров между соседними срезами, нормирован на 30 дней.",
    "Новотельная растёт к пику физиологически — поэтому сравниваем темп с двумя базами:",
    "со своим прошлым (окна до 10.06.2026) и с теми же месяцами 2025 года.",
    "",
    "| Окно | Темп 2026, кг/30дн | То же окно 2025 | Δ |",
    "|---|---|---|---|",
]
for d1, y, m, rate, n in growth:
    if y != 2026 or d1 < date(2026, 3, 1):
        continue
    same25 = [g for g in growth if g[1] == 2025 and g[2] == m]
    r25 = f"{same25[0][3]:+.1f}" if same25 else "—"
    diff = f"{rate - same25[0][3]:+.1f}" if same25 else "—"
    mark = " **← после интервенции**" if d1 > date(2026, 6, 10) else ""
    lines.append(f"| …→{d1.isoformat()} | {rate:+.1f} | {r25} | {diff}{mark} |")
lines += [
    "",
    "![Темп роста новотельных](../../charts/fresh_growth_rate.png)",
    "",
    "## График",
    "",
    "![Парный before/after](../../charts/intervention_2026-06-10.png)",
    "",
]

(CASE / "reports" / "intervention_2026-06-10.md").write_text("\n".join(lines), encoding="utf-8")

# --- график: средние до/после по когортам, 2026 vs 2025 ---
fig, ax = plt.subplots(figsize=(10, 5.5))
names = ["0–60 (рост к пику)", "60–150 (плато)", "150+ (спад)"]
x = range(len(names))
w = 0.18
for i, (stats, year, color0, color1) in enumerate((
        (stats26, 2026, "#9ecbe0", "#1f6f8b"),
        (stats25, 2025, "#cccccc", "#666666"))):
    a0 = [stats[n]["avg0"] if stats[n] else 0 for n in names]
    a1 = [stats[n]["avg1"] if stats[n] else 0 for n in names]
    off = -0.2 + i * 0.4
    ax.bar([xi + off - w / 2 for xi in x], a0, width=w, color=color0, label=f"{year} до")
    ax.bar([xi + off + w / 2 for xi in x], a1, width=w, color=color1, label=f"{year} после")
ax.set_xticks(list(x))
ax.set_xticklabels(names, fontsize=10)
ax.set_ylabel("Средний надой, кг")
ax.set_title("Одни и те же коровы до и после окна интервенции (10.06→10.07.2026 vs 01.06→01.07.2025)")
ax.legend()
ax.grid(alpha=0.3, axis="y")
fig.tight_layout()
fig.savefig(CASE / "charts" / "intervention_2026-06-10.png", dpi=120)
plt.close(fig)

# --- график: темп роста новотельных, вся история ---
import matplotlib.dates as mdates
fig, ax = plt.subplots(figsize=(12, 5))
for year, color in ((2025, "#999999"), (2026, "#1f6f8b")):
    pts = [(g[0], g[3]) for g in growth if g[1] == year]
    ax.plot([p[0] for p in pts], [p[1] for p in pts], marker="o", ms=3.5, lw=1.6,
            color=color, label=str(year))
ax.axvline(date(2026, 6, 10), color="#b03a3a", ls="--", lw=1.4)
ax.text(date(2026, 6, 12), ax.get_ylim()[1] - 0.5, "интервенция 10.06.2026", fontsize=9, color="#b03a3a")
ax.set_title("Темп роста надоя новотельных коров (DIM 0–60), кг за 30 дней — парный прирост одних и тех же коров")
ax.set_ylabel("кг / 30 дней")
ax.legend()
ax.grid(alpha=0.3)
ax.xaxis.set_major_formatter(mdates.DateFormatter("%m.%y"))
fig.autofmt_xdate()
fig.tight_layout()
fig.savefig(CASE / "charts" / "fresh_growth_rate.png", dpi=120)
plt.close(fig)

print("=== темп роста новотельных (окна 2026 с 03.2026) ===")
for d1, y, m, rate, n in growth:
    if y == 2026 and d1 >= date(2026, 3, 1):
        same25 = [g for g in growth if g[1] == 2025 and g[2] == m]
        r25 = f"{same25[0][3]:+.1f}" if same25 else "—"
        print(f"…→{d1}: {rate:+.1f} кг/30дн (N={n}), 2025: {r25}")

print("=== 2026 (10.06→10.07) ===")
for n_, s in stats26.items():
    if s:
        print(f"{n_}: N={s['n']}, {s['avg0']:.1f} → {s['avg1']:.1f} ({s['delta']:+.1f}), up {s['up']/s['n']*100:.0f}%")
print("=== 2025 (01.06→01.07) ===")
for n_, s in stats25.items():
    if s:
        print(f"{n_}: N={s['n']}, {s['avg0']:.1f} → {s['avg1']:.1f} ({s['delta']:+.1f}), up {s['up']/s['n']*100:.0f}%")
