#!/usr/bin/env python3
"""Анализ темпов роста продуктивности Ж/К №2 (Ленинский) vs Ж/К №1 (Рублёвка).

Источники: raw/milk_dynamics_Len_2026-05.md, raw/milk_dynamics_Rubl_2026-05.md
Выход: статистика в stdout (matplotlib в среде отсутствует — графики не строятся).
"""

import re
from pathlib import Path

import numpy as np
import pandas as pd

CASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = CASE_DIR / 'raw'


def parse_md_table(path: Path) -> pd.DataFrame:
    """Парсинг md-таблицы динамики молока в DataFrame."""
    rows = []
    for line in path.read_text(encoding='utf-8').splitlines():
        m = re.match(r'\|\s*(2026-\d{2}-\d{2})\s*\|', line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        # Дата | Дойных голов | Реализация, кг | Удой, л | Жир, % | T день | T ночь | Примечания
        def num(s):
            s = s.replace(',', '.').replace('—', '').replace('+', '').strip()
            try:
                return float(s)
            except ValueError:
                return None
        rows.append({
            'date': pd.Timestamp(m.group(1)),
            'cows': num(cells[1]),
            'milk_kg': num(cells[2]),
            'yield_l': num(cells[3]),
            'fat': num(cells[4]),
            't_day': num(cells[5]) if len(cells) > 5 else None,
        })
    return pd.DataFrame(rows).set_index('date').sort_index()


def trend_per_week(df: pd.DataFrame, col: str) -> float:
    """Наклон линейного тренда (МНК), единиц в неделю."""
    d = df[col].dropna()
    x = (d.index - d.index[0]).days.values.astype(float)
    k, _b = np.polyfit(x, d.values, 1)
    return k * 7


# Точка отсчёта начала работы — 2026-06-08 (база перед интервенцией 10.06).
# Майские точки (02.05, 22.05) — только контекст, в расчёт темпов не входят.
BASELINE = ('2026-06-08', '2026-06-08')

PERIODS = {
    'База (08.06)': ('2026-06-08', '2026-06-08'),
    'Июнь после интервенции (11–30.06)': ('2026-06-11', '2026-06-30'),
    'Июль (01–31.07)': ('2026-07-01', '2026-07-31'),
    'Август (13–19.08)': ('2026-08-01', '2026-08-31'),
}


def period_stats(df: pd.DataFrame) -> pd.DataFrame:
    out = []
    for name, (start, end) in PERIODS.items():
        sub = df.loc[start:end]
        if len(sub) == 0:
            continue
        row = {
            'Период': name,
            'n': len(sub),
            'Удой, л': round(sub['yield_l'].mean(), 1),
            'Реализация, тыс. кг': round(sub['milk_kg'].mean() / 1000, 1),
            'Жир, %': round(sub['fat'].mean(), 2),
            'Дойные, гол.': int(round(sub['cows'].mean(), 0)),
        }
        if len(sub) >= 3:
            row['Тренд, л/нед'] = f"{trend_per_week(sub, 'yield_l'):+.2f}"
        out.append(row)
    return pd.DataFrame(out)


def main():
    len2 = parse_md_table(RAW_DIR / 'milk_dynamics_Len_2026-05.md')
    rubl = parse_md_table(RAW_DIR / 'milk_dynamics_Rubl_2026-05.md')

    for name, df in [('Ж/К №2 (Ленинский)', len2), ('Ж/К №1 (Рублёвка)', rubl)]:
        work = df.loc[BASELINE[0]:]  # период работы от точки отсчёта 08.06
        print(f'\n=== {name} ===')
        print(f'Точка отсчёта: {BASELINE[0]}; данные до {work.index.max().date()}, замеров: {len(work)}')
        print(period_stats(work).to_string(index=False))
        print(f'Тренд удоя за период работы (08.06 → 19.08): {trend_per_week(work, "yield_l"):+.2f} л/сут в неделю')
        # Рост от точки отсчёта (08.06) к августу
        base = work.loc[BASELINE[0]:BASELINE[1], 'yield_l'].iloc[0]
        last = work.loc['2026-08-01':'2026-08-31', 'yield_l'].mean()
        print(f'Рост 08.06 → август (сред.): {base:.1f} → {last:.1f} л/сут ({last - base:+.1f} л, {(last / base - 1) * 100:+.1f} %)')
        # Темп реализации
        base_r = work.loc[BASELINE[0]:BASELINE[1], 'milk_kg'].iloc[0] / 1000
        last_r = work.loc['2026-08-01':'2026-08-31', 'milk_kg'].mean() / 1000
        print(f'Реализация 08.06 → август: {base_r:.1f} → {last_r:.1f} тыс. кг/сут ({(last_r / base_r - 1) * 100:+.1f} %)')
        # Корреляция удоя с дневной температурой
        sub = work[['yield_l', 't_day']].dropna()
        print(f'Корреляция удоя с T днём: {sub["yield_l"].corr(sub["t_day"]):.2f} (n={len(sub)})')

    # Разрыв Ж/К №2 − Ж/К №1 по общим датам (от точки отсчёта 08.06)
    j = len2[['yield_l']].join(rubl[['yield_l']], lsuffix='_len', rsuffix='_rubl', how='inner')
    j = j.loc[BASELINE[0]:]
    j['gap'] = j['yield_l_len'] - j['yield_l_rubl']
    print('\n=== Разрыв Ж/К №2 − Ж/К №1 (л/сут), по общим датам ===')
    print(f'средний: {j["gap"].mean():+.2f} | мин: {j["gap"].min():+.2f} ({j["gap"].idxmin().date()}) | '
          f'макс: {j["gap"].max():+.2f} ({j["gap"].idxmax().date()}) | на 19.08: {j["gap"].iloc[-1]:+.2f}')
    for name, (s, e) in PERIODS.items():
        sub = j.loc[s:e]
        if len(sub):
            print(f'  {name}: средний разрыв {sub["gap"].mean():+.2f} л')


if __name__ == '__main__':
    main()
