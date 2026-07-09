#!/usr/bin/env python3
"""Генерация визуализаций для CASE-002 из обновлённых xlsx-данных."""

import os
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd

# ---------------------------------------------------------------------------
# Пути
# ---------------------------------------------------------------------------
CASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = CASE_DIR / 'raw'
CHARTS_DIR = CASE_DIR / 'charts'
CHARTS_DIR.mkdir(exist_ok=True)

plt.rcParams['font.size'] = 12
plt.rcParams['figure.dpi'] = 150

COLORS = {'Ж/К №1': '#1f77b4', 'Ж/К №2': '#ff7f0e'}


def save(fig, name):
    path = CHARTS_DIR / name
    fig.savefig(path, bbox_inches='tight', facecolor='white')
    plt.close(fig)
    print('saved:', path)


# ---------------------------------------------------------------------------
# Загрузка данных
# ---------------------------------------------------------------------------
def load_dynamics():
    df = pd.read_excel(RAW_DIR / 'Зенченко Динамика производства.xlsx', sheet_name='Лист1', header=1)
    df = df.dropna(subset=['Дата', 'Комплекс']).copy()
    df = df.drop_duplicates(subset=['Дата', 'Комплекс'], keep='last')
    df['Дата'] = pd.to_datetime(df['Дата']).dt.normalize()
    df = df.sort_values(['Комплекс', 'Дата']).reset_index(drop=True)
    df = df.rename(columns={
        'Дойные ': 'Дойные',
        'Удой на корову': 'Удой',
        'Реализация': 'Реализация'
    })
    return df


def load_groups():
    df = pd.read_excel(RAW_DIR / 'Группы.xlsx', sheet_name='Лист1', header=None)
    # Строка 1 (индекс 1) содержит даты: col 2 = 2026-07-07, col 4 = 2026-06-09
    df = df.iloc[3:, [1, 2, 3, 4, 5]].copy()
    df.columns = ['Группа', 'DIM_конец', 'Продуктивность_конец', 'DIM_начало', 'Продуктивность_начало']
    df = df.dropna(subset=['Группа'])
    df['Группа'] = df['Группа'].astype(int).astype(str)
    for col in ['DIM_конец', 'Продуктивность_конец', 'DIM_начало', 'Продуктивность_начало']:
        df[col] = pd.to_numeric(df[col], errors='coerce')
    return df.reset_index(drop=True)


def load_sita_tmr():
    """Возвращает DataFrame с физической структурой TMR группы 2 (2026-07-08)."""
    df = pd.read_excel(RAW_DIR / 'Сита.xlsx', sheet_name='Лист1', header=None)
    # сита 1-4, масса и доля для двух просевов
    rows = df.iloc[4:8, [1, 2, 3, 5, 6]].copy()
    rows.columns = ['Сито', 'Масса_1', 'Доля_1', 'Масса_2', 'Доля_2']
    rows['Сито'] = rows['Сито'].astype(int)
    for col in ['Масса_1', 'Доля_1', 'Масса_2', 'Доля_2']:
        rows[col] = pd.to_numeric(rows[col], errors='coerce')
    rows['Доля_средняя'] = (rows['Доля_1'] + rows['Доля_2']) / 2 * 100
    return rows.reset_index(drop=True)


# ---------------------------------------------------------------------------
# Графики
# ---------------------------------------------------------------------------
def chart_individual_complex(df, complex_name):
    data = df[df['Комплекс'] == complex_name].sort_values('Дата')
    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(data['Дата'], data['Удой'], color=COLORS[complex_name], marker='o', label='Удой на корову')
    ax1.set_ylabel('Удой на корову, л/сут', color=COLORS[complex_name])
    ax1.tick_params(axis='y', labelcolor=COLORS[complex_name])
    ax1.grid(True, linestyle='--', alpha=0.5)

    ax2 = ax1.twinx()
    ax2.plot(data['Дата'], data['Реализация'], color=COLORS[complex_name], marker='s',
             linestyle='--', alpha=0.7, label='Реализация')
    ax2.set_ylabel('Реализация, л/сут', color=COLORS[complex_name])
    ax2.tick_params(axis='y', labelcolor=COLORS[complex_name])

    plt.title(f'Динамика производства: {complex_name}')
    fig.autofmt_xdate()
    suffix = '1' if complex_name == 'Ж/К №1' else '2'
    save(fig, f'Ж_К_№{suffix}_individual.png')


def chart_yield_comparison(df):
    fig, ax = plt.subplots(figsize=(12, 5))
    for comp in df['Комплекс'].unique():
        data = df[df['Комплекс'] == comp].sort_values('Дата')
        ax.plot(data['Дата'], data['Удой'], marker='o', label=comp, color=COLORS[comp])
    ax.set_ylabel('Удой на корову, л/сут')
    ax.set_title('Сравнение продуктивности на голову')
    ax.legend(title='Комплекс')
    ax.grid(True, linestyle='--', alpha=0.5)
    fig.autofmt_xdate()
    save(fig, 'Зенченко_продуктивность_на_голову.png')


def chart_realization(df):
    fig, ax = plt.subplots(figsize=(12, 5))
    for comp in df['Комплекс'].unique():
        data = df[df['Комплекс'] == comp].sort_values('Дата')
        ax.plot(data['Дата'], data['Реализация'], marker='o', label=comp, color=COLORS[comp])
    ax.set_ylabel('Реализация, л/сут')
    ax.set_title('Сравнение реализации молока')
    ax.legend(title='Комплекс')
    ax.grid(True, linestyle='--', alpha=0.5)
    fig.autofmt_xdate()
    save(fig, 'Зенченко_реализация.png')


def chart_herd_size(df):
    fig, ax = plt.subplots(figsize=(12, 5))
    for comp in df['Комплекс'].unique():
        data = df[df['Комплекс'] == comp].sort_values('Дата')
        ax.plot(data['Дата'], data['Дойные'], marker='o', label=comp, color=COLORS[comp])
    ax.set_ylabel('Количество дойных голов')
    ax.set_title('Динамика дойного поголовья')
    ax.legend(title='Комплекс')
    ax.grid(True, linestyle='--', alpha=0.5)
    fig.autofmt_xdate()
    save(fig, 'Зенченко_дойное_поголовье.png')


def chart_yield_difference(df):
    p1 = df[df['Комплекс'] == 'Ж/К №1'][['Дата', 'Удой']].rename(columns={'Удой': 'Удой_1'})
    p2 = df[df['Комплекс'] == 'Ж/К №2'][['Дата', 'Удой']].rename(columns={'Удой': 'Удой_2'})
    merged = pd.merge(p1, p2, on='Дата', how='outer').sort_values('Дата')
    merged['Разница'] = merged['Удой_2'] - merged['Удой_1']

    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(merged['Дата'], merged['Разница'], marker='o', color='#2ca02c')
    ax.axhline(0, color='black', linestyle='--', linewidth=1)
    ax.set_ylabel('л/сут')
    ax.set_title('Разница по продуктивности (Ж/К №2 − Ж/К №1)')
    ax.grid(True, linestyle='--', alpha=0.5)
    fig.autofmt_xdate()
    save(fig, 'Зенченко_разница_между_фермами.png')


def chart_scatter(df):
    fig, ax = plt.subplots(figsize=(10, 7))
    for comp in df['Комплекс'].unique():
        data = df[df['Комплекс'] == comp]
        ax.scatter(data['Удой'], data['Реализация'], s=data['Дойные'] / 3,
                   alpha=0.6, label=comp, color=COLORS[comp], edgecolors='black')
    ax.set_xlabel('Удой на корову, л/сут')
    ax.set_ylabel('Реализация, л/сут')
    ax.set_title('Реализация vs продуктивность\n(размер точки ∝ дойному поголовью)')
    ax.legend(title='Комплекс')
    ax.grid(True, linestyle='--', alpha=0.5)
    save(fig, 'Зенченко_scatter.png')


def chart_indices(df):
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))

    for comp in df['Комплекс'].unique():
        data = df[df['Комплекс'] == comp].sort_values('Дата')
        base_yield = data.iloc[0]['Удой']
        base_real = data.iloc[0]['Реализация']
        idx_yield = data['Удой'] / base_yield * 100
        idx_real = data['Реализация'] / base_real * 100

        axes[0].plot(data['Дата'], idx_yield, marker='o', label=comp, color=COLORS[comp])
        axes[1].plot(data['Дата'], idx_real, marker='o', label=comp, color=COLORS[comp])

    axes[0].axhline(100, color='black', linestyle='--', linewidth=1)
    axes[0].set_ylabel('Индекс')
    axes[0].set_title('Индекс продуктивности (начало периода = 100)')
    axes[0].legend(title='Комплекс')
    axes[0].grid(True, linestyle='--', alpha=0.5)

    axes[1].axhline(100, color='black', linestyle='--', linewidth=1)
    axes[1].set_ylabel('Индекс')
    axes[1].set_title('Индекс реализации (начало периода = 100)')
    axes[1].legend(title='Комплекс')
    axes[1].grid(True, linestyle='--', alpha=0.5)

    fig.autofmt_xdate()
    save(fig, 'Зенченко_индексы.png')


def chart_rolling(df):
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    window = 7

    for comp in df['Комплекс'].unique():
        data = df[df['Комплекс'] == comp].sort_values('Дата').set_index('Дата')
        roll_yield = data['Удой'].rolling(window=window, min_periods=1).mean()
        roll_real = data['Реализация'].rolling(window=window, min_periods=1).mean()

        axes[0].plot(roll_yield.index, roll_yield, marker='o', label=comp, color=COLORS[comp])
        axes[1].plot(roll_real.index, roll_real, marker='o', label=comp, color=COLORS[comp])

    axes[0].set_ylabel('л/сут')
    axes[0].set_title(f'Скользящее среднее за {window} дней: продуктивность на голову')
    axes[0].legend(title='Комплекс')
    axes[0].grid(True, linestyle='--', alpha=0.5)

    axes[1].set_ylabel('л/сут')
    axes[1].set_title(f'Скользящее среднее за {window} дней: реализация')
    axes[1].legend(title='Комплекс')
    axes[1].grid(True, linestyle='--', alpha=0.5)

    fig.autofmt_xdate()
    save(fig, 'Зенченко_скользящее_среднее.png')


def chart_combined(df):
    fig, axes = plt.subplots(2, 1, figsize=(12, 10))
    for idx, comp in enumerate(['Ж/К №1', 'Ж/К №2']):
        ax1 = axes[idx]
        data = df[df['Комплекс'] == comp].sort_values('Дата')
        ax1.plot(data['Дата'], data['Удой'], color=COLORS[comp], marker='o', label='Удой на корову')
        ax1.set_ylabel('Удой на корову, л/сут', color=COLORS[comp])
        ax1.tick_params(axis='y', labelcolor=COLORS[comp])
        ax1.set_title(comp)
        ax1.grid(True, linestyle='--', alpha=0.5)

        ax2 = ax1.twinx()
        ax2.plot(data['Дата'], data['Реализация'], color=COLORS[comp], marker='s',
                 linestyle='--', alpha=0.7, label='Реализация')
        ax2.set_ylabel('Реализация, л/сут', color=COLORS[comp])
        ax2.tick_params(axis='y', labelcolor=COLORS[comp])

    fig.autofmt_xdate()
    save(fig, 'Зенченко_совмещенный_график.png')


def chart_groups(groups):
    x = range(len(groups))
    width = 0.35
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar([i - width / 2 for i in x], groups['Продуктивность_начало'], width,
           label='09.06.2026', color='#1f77b4')
    ax.bar([i + width / 2 for i in x], groups['Продуктивность_конец'], width,
           label='07.07.2026', color='#ff7f0e')
    ax.set_xticks(x)
    ax.set_xticklabels(groups['Группа'])
    ax.set_xlabel('Группа')
    ax.set_ylabel('Продуктивность, л/сут')
    ax.set_title('Сравнение продуктивности по группам')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5, axis='y')
    save(fig, 'groups_comparison_bars.png')

    # delta
    groups['Дельта'] = groups['Продуктивность_конец'] - groups['Продуктивность_начало']
    fig, ax = plt.subplots(figsize=(12, 5))
    colors = ['#2ca02c' if v >= 0 else '#d62728' for v in groups['Дельта']]
    ax.bar(groups['Группа'], groups['Дельта'], color=colors)
    ax.axhline(0, color='black', linestyle='--', linewidth=1)
    ax.set_xlabel('Группа')
    ax.set_ylabel('Изменение, л/сут')
    ax.set_title('Изменение продуктивности по группам (07.07.2026 − 09.06.2026)')
    ax.grid(True, linestyle='--', alpha=0.5, axis='y')
    save(fig, 'groups_delta.png')


def chart_sita_tmr(sita):
    fig, ax = plt.subplots(figsize=(8, 5))
    x = range(len(sita))
    width = 0.35
    ax.bar([i - width / 2 for i in x], sita['Доля_1'] * 100, width, label='1 просев', color='#1f77b4')
    ax.bar([i + width / 2 for i in x], sita['Доля_2'] * 100, width, label='2 просев', color='#ff7f0e')
    ax.set_xticks(x)
    ax.set_xticklabels(sita['Сито'])
    ax.set_xlabel('Сито')
    ax.set_ylabel('Доля, %')
    ax.set_title('Физическая структура TMR группы 2 (2026-07-08)')
    ax.legend()
    ax.grid(True, linestyle='--', alpha=0.5, axis='y')
    save(fig, 'sita_tmr_group2.png')


# ---------------------------------------------------------------------------
# main
# ---------------------------------------------------------------------------
def main():
    df = load_dynamics()
    groups = load_groups()
    sita = load_sita_tmr()

    chart_individual_complex(df, 'Ж/К №1')
    chart_individual_complex(df, 'Ж/К №2')
    chart_yield_comparison(df)
    chart_realization(df)
    chart_herd_size(df)
    chart_yield_difference(df)
    chart_scatter(df)
    chart_indices(df)
    chart_rolling(df)
    chart_combined(df)
    chart_groups(groups)
    chart_sita_tmr(sita)


if __name__ == '__main__':
    main()
