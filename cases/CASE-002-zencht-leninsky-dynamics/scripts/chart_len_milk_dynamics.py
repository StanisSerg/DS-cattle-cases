#!/usr/bin/env python3
"""Совмещённый график Ж/К №2 (Ленинский): удой на голову + реализация молока.

Период: 2026-06-08 — 2026-08-19 (майские точки — только контекст, не входят).
Верх (синий): удой на дойную корову — замеры, скользящее среднее (3 дня),
    линейный тренд (пунктир), средняя продуктивность (горизонталь с подписью).
Низ (зелёный): реализация молока — замеры, скользящее среднее (3 дня),
    линейный тренд (пунктир).
Ось дат: первая и последняя даты обязательно, промежуточные — каждые 2 недели.
Источник: raw/milk_dynamics_Len_2026-05.md
Выход: charts/milk_yield_realization_Len_2026-06_08.png
"""

from pathlib import Path
import sys

import matplotlib
matplotlib.use('Agg')
import matplotlib.dates as mdates
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))
from analyze_productivity_dynamics import parse_md_table, RAW_DIR, trend_per_week

CASE_DIR = Path(__file__).resolve().parent.parent
CHARTS_DIR = CASE_DIR / 'charts'
CHARTS_DIR.mkdir(exist_ok=True)

BLUE = '#1f77b4'
GREEN = '#2ca02c'
START = pd.Timestamp('2026-06-08')
ROLL_WINDOW = '3D'  # скользящее среднее за 3 дня (календарных)


def add_trend(ax, series, color, label_fmt):
    """Линейный тренд (МНК) пунктиром; label_fmt с {k7} — наклон в неделю."""
    x = (series.index - series.index[0]).days.values.astype(float)
    k7 = trend_per_week(series.to_frame('y'), 'y')
    k = k7 / 7
    b = series.mean() - k * x.mean()
    ax.plot(series.index, k * x + b, '--', color=color, lw=1.5,
            label=label_fmt.format(k7=k7))


def main():
    df = parse_md_table(RAW_DIR / 'milk_dynamics_Len_2026-05.md')
    df = df[df.index >= START]

    fig, axes = plt.subplots(2, 1, figsize=(12, 8), sharex=True)

    # --- Верх: удой на голову (синий) ---
    ax = axes[0]
    y = df['yield_l'].dropna()
    ax.plot(y.index, y.values, 'o', color=BLUE, alpha=0.35, ms=4, label='замеры')
    roll = y.rolling(ROLL_WINDOW, min_periods=1).mean()
    ax.plot(roll.index, roll.values, '-', color=BLUE, lw=2,
            label='скользящее среднее (3 дня)')
    add_trend(ax, y, BLUE, 'тренд {k7:+.2f} л/нед')
    mean_y = y.mean()
    ax.axhline(mean_y, ls=':', color=BLUE, alpha=0.8, lw=1.2,
               label=f'средняя продуктивность {mean_y:.1f} л')
    # подписи значений через одну точку
    for i, (d, v) in enumerate(y.items()):
        if i % 2 == 0:
            ax.annotate(f'{v:.1f}', xy=(d, v), xytext=(0, 5), textcoords='offset points',
                        fontsize=7, color=BLUE, ha='center', alpha=0.85)
    ax.set_ylabel('Удой на дойную корову, л/сут')
    ax.set_title('Ж/К №2 (Ленинский): продуктивность и реализация, 08.06.2026 — 19.08.2026')
    ax.legend(loc='lower right', fontsize=9)
    ax.grid(alpha=0.3)
    ax.margins(y=0.12)  # запас сверху/снизу, чтобы подписи не упирались в рамку
    ax.tick_params(labelbottom=True)  # даты и на верхнем графике

    # --- Низ: реализация (зелёный) ---
    ax2 = axes[1]
    r = (df['milk_kg'] / 1000).dropna()
    ax2.plot(r.index, r.values, 'o', color=GREEN, alpha=0.35, ms=4, label='замеры')
    roll_r = r.rolling(ROLL_WINDOW, min_periods=1).mean()
    ax2.plot(roll_r.index, roll_r.values, '-', color=GREEN, lw=2,
             label='скользящее среднее (3 дня)')
    add_trend(ax2, r, GREEN, 'тренд {k7:+.2f} тыс. кг/нед')
    for i, (d, v) in enumerate(r.items()):  # подписи значений через одну точку
        if i % 2 == 0:
            ax2.annotate(f'{v:.1f}', xy=(d, v), xytext=(0, 5), textcoords='offset points',
                         fontsize=7, color=GREEN, ha='center', alpha=0.85)
    ax2.set_ylabel('Реализация, тыс. кг/сут')
    ax2.legend(loc='lower right', fontsize=9)
    ax2.grid(alpha=0.3)
    ax2.margins(y=0.12)  # запас сверху/снизу, чтобы подписи не упирались в рамку

    # Даты: первая и последняя обязательно + каждые 2 недели между ними
    first, last = df.index[0], df.index[-1]
    ticks = [first]
    t = first + pd.Timedelta(days=14)
    while t < last - pd.Timedelta(days=7):  # не вплотную к последней дате
        ticks.append(t)
        t += pd.Timedelta(days=14)
    ticks.append(last)
    ax2.set_xticks(ticks)
    ax2.xaxis.set_major_formatter(mdates.DateFormatter('%d.%m.%Y'))
    plt.setp(ax.get_xticklabels(), rotation=30, ha='right')
    plt.setp(ax2.get_xticklabels(), rotation=30, ha='right')

    out = CHARTS_DIR / 'milk_yield_realization_Len_2026-06_08.png'
    fig.savefig(out, bbox_inches='tight', facecolor='white', dpi=150)
    print('saved:', out)


if __name__ == '__main__':
    main()
