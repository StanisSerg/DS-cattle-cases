#!/usr/bin/env python3
"""Сравнение продуктивности по группам (Ленинский) по всем визитам.

Источник: raw/group_productivity_visit01_*.md (один файл = один визит).
Выход: charts/group_productivity_comparison.png
"""

import re
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import numpy as np

CASE_DIR = Path(__file__).resolve().parent.parent
RAW_DIR = CASE_DIR / 'raw'
CHARTS_DIR = CASE_DIR / 'charts'
CHARTS_DIR.mkdir(exist_ok=True)

# цвета по визитам (в хронологическом порядке)
COLORS = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']


def parse_visit(path: Path) -> dict:
    """Группа -> продуктивность (л/сут)."""
    date = re.search(r'(\d{4}-\d{2}-\d{2})', path.name).group(1)
    data = {}
    for line in path.read_text(encoding='utf-8').splitlines():
        m = re.match(r'\|\s*(\d+)\s*\|', line)
        if not m:
            continue
        cells = [c.strip() for c in line.strip().strip('|').split('|')]
        try:
            data[int(cells[0])] = float(cells[4].replace(',', '.'))
        except (ValueError, IndexError):
            continue
    return date, data


def main():
    visits = sorted(parse_visit(p) for p in RAW_DIR.glob('group_productivity_visit01_*.md'))
    groups = sorted({g for _, d in visits for g in d})

    x = np.arange(len(groups))
    width = 0.8 / len(visits)
    fig, ax = plt.subplots(figsize=(20, 9))

    for i, (date, data) in enumerate(visits):
        vals = [data.get(g, np.nan) for g in groups]
        bars = ax.bar(x + i * width - 0.4 + width / 2, vals, width,
                      label=date, color=COLORS[i % len(COLORS)])
        for bar, v in zip(bars, vals):
            if not np.isnan(v):
                ax.annotate(f'{v:.1f}', xy=(bar.get_x() + bar.get_width() / 2, v),
                            xytext=(0, 3), textcoords='offset points',
                            ha='center', fontsize=6.5, alpha=0.85)

    ax.set_xticks(x)
    ax.set_xticklabels(groups)
    ax.set_xlabel('Группа')
    ax.set_ylabel('Продуктивность, л/сут')
    ax.set_title('Сравнение продуктивности по группам, Ленинский')
    ax.legend(fontsize=10)
    ax.grid(axis='y', alpha=0.3)
    ax.margins(y=0.08)

    out = CHARTS_DIR / 'group_productivity_comparison.png'
    fig.savefig(out, bbox_inches='tight', facecolor='white', dpi=150)
    print('saved:', out)


if __name__ == '__main__':
    main()
