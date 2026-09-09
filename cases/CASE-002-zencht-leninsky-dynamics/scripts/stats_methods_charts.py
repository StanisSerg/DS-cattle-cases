#!/usr/bin/env python3
"""Иллюстрации к дорожной карте статистических методов (stats_methods_roadmap_2026-09-09.md).

Три графика на данных CASE-002:
1. ITS (прерванный временной ряд): средний надой доящихся по срезам DairyPlan
   01.2025–09.2026, вертикаль на 10.06.2026, сегментные тренды до/после.
2. Bootstrap-иллюстрация для выбытия дойных: 25 событий (11 в диапазоне 2025,
   14 в 2026), нулевая модель — равновероятное распределение по двум равным
   диапазонам (83 дня); гистограмма разности + наблюдаемая разность.
3. Kaplan–Meier «дожитие в стаде» для двух когорт: доящиеся на срезе
   01.06.2025 и 10.06.2026, событие — забой в диапазоне 10.06–31.08 своего года,
   цензура — конец диапазона. Оговорка: для 2025 срез на 9 дней раньше диапазона.

Выход: charts/its_yield_trend.png, charts/bootstrap_cull_diff.png,
       charts/km_survival_cohorts.png
"""

import re
from datetime import date, timedelta
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np

CASE = Path(__file__).resolve().parent.parent
MD_DIR = CASE / "raw" / "excel" / "Excel-MD"
CHARTS = CASE / "charts"
CHARTS.mkdir(exist_ok=True)

INTERVENTION = date(2026, 6, 10)
WINDOW = 83  # дней: 10.06 → 31.08


def load_slice(d: date) -> dict:
    """номер -> (dim, prod, group, status); без гр.21 и строк без статуса."""
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


def load_culls():
    """(num, дата выбытия, способ, есть ли последний отёл) из архива выбытия."""
    md = MD_DIR / "2026-09-02_dairyplan_cull_archive.md"
    rows = []
    for line in md.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\| (\d{4}-\d{2}-\d{2}) \| (\d+) \| [^|]* \| [^|]* \| [^|]* \| [^|]* \| ([^|]*) \| ([^|]*) \|", line)
        if not m:
            continue
        d = date.fromisoformat(m.group(1))
        num = int(m.group(2))
        last_calv = m.group(3).strip()
        method = m.group(4).strip().upper()
        rows.append((num, d, method, last_calv not in ("—", "")))
    return rows


# ---------- 1. ITS ----------
def its_chart():
    dates, means = [], []
    for md in sorted(MD_DIR.glob("*_dairyplan_produktivnost.md")):
        d = date.fromisoformat(md.name[:10])
        sl = load_slice(d)
        prods = [p for _, (dim, p, g, s) in sl.items() if p and p > 0]
        if prods:
            dates.append(d)
            means.append(sum(prods) / len(prods))
    x = np.array([(d - dates[0]).days for d in dates])
    y = np.array(means)
    xi = (INTERVENTION - dates[0]).days
    before, after = x < xi, x >= xi

    fig, ax = plt.subplots(figsize=(10, 4.8))
    ax.plot(dates, y, "o-", ms=3.5, lw=1, color="#4472a8", label="средний надой доящихся (срез)")
    for mask, color, lbl in [(before, "#888", "тренд до 10.06"), (after, "#c0392b", "тренд после 10.06")]:
        k, b = np.polyfit(x[mask], y[mask], 1)
        xs = np.array([x[mask].min(), xi if mask is before else x[mask].max()])
        ax.plot([dates[0] + timedelta(days=int(v)) for v in xs], k * xs + b,
                "--", lw=2, color=color, label=lbl)
    ax.axvline(INTERVENTION, color="#c0392b", lw=1.2, alpha=0.7)
    ax.annotate("корректировка\nрациона 10.06.2026", xy=(INTERVENTION, ax.get_ylim()[1]),
                xytext=(8, -6), textcoords="offset points", fontsize=9, color="#c0392b", va="top")
    ax.set_title("ITS-иллюстрация: средний надой стада по срезам DairyPlan, 01.2025 – 09.2026")
    ax.set_ylabel("л/сут на корову")
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%m.%y"))
    ax.legend(fontsize=9, loc="lower right")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(CHARTS / "its_yield_trend.png", dpi=130)
    plt.close(fig)
    print(f"ITS: {len(dates)} срезов")


# ---------- 2. Bootstrap ----------
def bootstrap_chart():
    rng = np.random.default_rng(42)
    n_events, obs26 = 25, 14  # забой дойных 10.06–31.08: 2025 — 11, 2026 — 14
    sims = rng.binomial(n_events, 0.5, 20000)
    diffs = 2 * sims - n_events  # разность (2026 − 2025)
    obs_diff = 2 * obs26 - n_events
    p_two = (np.abs(diffs) >= abs(obs_diff)).mean()

    fig, ax = plt.subplots(figsize=(8, 4.2))
    ax.hist(diffs, bins=np.arange(diffs.min() - 0.5, diffs.max() + 1.5), color="#9db8d2", edgecolor="white")
    ax.axvline(obs_diff, color="#c0392b", lw=2)
    ax.annotate(f"наблюдаемая разность: +3\np(двусторонний) ≈ {p_two:.2f}",
                xy=(obs_diff, 0), xytext=(10, 200), textcoords="offset points",
                fontsize=10, color="#c0392b")
    ax.set_title("Bootstrap: выбытие дойных 10.06–31.08 (11 в 2025 против 14 в 2026)\n"
                 "H0: 25 событий равновероятны по равным диапазонам, 20 000 прогонов", fontsize=10)
    ax.set_xlabel("разность числа событий (2026 − 2025)")
    ax.set_ylabel("частота в симуляции")
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(CHARTS / "bootstrap_cull_diff.png", dpi=130)
    plt.close(fig)
    print(f"Bootstrap: p={p_two:.3f}")


# ---------- 3. Kaplan–Meier ----------
def km_curve(cohort_nums, events, start, end):
    """S(t) вручную: cohort — номера на старте; events — (num, дата); цензура = end."""
    ev_by_day = {}
    for num, d in events:
        if num in cohort_nums and start <= d <= end:
            ev_by_day.setdefault(d, 0)
            ev_by_day[d] += 1
    at_risk = len(cohort_nums)
    times, surv, s = [start], [1.0], 1.0
    for d in sorted(ev_by_day):
        s *= (1 - ev_by_day[d] / at_risk)
        at_risk -= ev_by_day[d]
        times.append(d)
        surv.append(s)
    times.append(end)
    surv.append(s)
    return times, surv


def km_chart():
    culls = load_culls()
    # забой дойных (с датой последнего отёла) — как в отчёте, часть 1
    events = [(num, d) for num, d, method, has_calv in culls if method == "ЗАБОЙ" and has_calv]

    specs = [
        (date(2025, 6, 1), date(2025, 6, 10), date(2025, 8, 31), "когорта 2025 (срез 01.06)"),
        (date(2026, 6, 10), date(2026, 6, 10), date(2026, 8, 31), "когорта 2026 (срез 10.06)"),
    ]
    fig, ax = plt.subplots(figsize=(8, 4.2))
    for slice_d, start, end, lbl in specs:
        cohort = {num for num, (dim, p, g, s) in load_slice(slice_d).items() if p and p > 0}
        times, surv = km_curve(cohort, events, start, end)
        xs = [(t - start).days for t in times]
        ax.step(xs, [v * 100 for v in surv], where="post", lw=2, label=f"{lbl}, N={len(cohort)}")
    ax.set_title("Kaplan–Meier: доля когорты, оставшейся в стаде\n"
                 "событие — забой дойной коровы, диапазон 10.06 → 31.08 своего года", fontsize=10)
    ax.set_xlabel("дней от начала диапазона")
    ax.set_ylabel("в стаде, %")
    ax.set_ylim(96, 100.5)
    ax.legend(fontsize=9)
    ax.grid(alpha=0.3)
    fig.tight_layout()
    fig.savefig(CHARTS / "km_survival_cohorts.png", dpi=130)
    plt.close(fig)
    print("KM: кривые построены")


if __name__ == "__main__":
    its_chart()
    bootstrap_chart()
    km_chart()
