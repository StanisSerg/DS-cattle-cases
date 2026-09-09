#!/usr/bin/env python3
"""График «до/после» по производственным группам Ж/К №2 (Ленинский).

Вход: raw/group_productivity_visit01_<дата>.md (замеры DairyPlan по группам).
Выход: charts/groups_before_after_<дата1>_<дата2>.png — парные столбцы
(первый и последний замер), значения подписаны, Δ над парой.

Запуск: python3 scripts/chart_groups_before_after.py
"""
import re
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

CASE_DIR = Path(__file__).resolve().parent.parent
GROUPS = ["1", "2", "3", "4", "5", "6", "7", "8", "9", "15", "19", "22"]

C_BEFORE = "#8D99AE"  # до — нейтральный
C_AFTER = "#3A86FF"   # после — ярко-синий

plt.rcParams["font.family"] = "DejaVu Sans"


def load_visit(path: Path) -> dict:
    out = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        m = re.match(r"\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*(\d+)\s*\|\s*[\d-]+\s*\|\s*([\d,]+)\s*\|", line)
        if m:
            grp, heads, dim, prod = m.groups()
            out[grp] = {"heads": int(heads), "dim": int(dim), "prod": float(prod.replace(",", "."))}
    return out


def main() -> None:
    visits = sorted(CASE_DIR.glob("raw/group_productivity_visit01_*.md"))
    first, last = load_visit(visits[0]), load_visit(visits[-1])
    d1 = visits[0].stem.split("_")[-1]
    d2 = visits[-1].stem.split("_")[-1]

    groups = [g for g in GROUPS if g in last]
    before = [first.get(g, {}).get("prod") for g in groups]
    after = [last[g]["prod"] for g in groups]

    x = range(len(groups))
    w = 0.38
    fig, ax = plt.subplots(figsize=(12, 5.5))
    b1 = ax.bar([i - w / 2 for i in x], [v if v is not None else 0 for v in before], w,
                color=C_BEFORE, label=f"{d1} (до)")
    b2 = ax.bar([i + w / 2 for i in x], after, w, color=C_AFTER, label=f"{d2} (после)")
    for rect, v in zip(b1, before):
        if v is not None:
            ax.annotate(f"{v:.1f}", (rect.get_x() + rect.get_width() / 2, v),
                        xytext=(0, 2), textcoords="offset points", ha="center", fontsize=9)
    ax.bar_label(b2, fmt="%.1f", padding=2, fontsize=9)
    for i, g in enumerate(groups):
        if before[i] is not None:
            delta = after[i] - before[i]
            ax.text(i, max(after[i], before[i]) + 1.6, f"{delta:+.1f}",
                    ha="center", fontsize=10, fontweight="bold",
                    color="#2B2D42")
        else:
            ax.text(i, after[i] + 1.6, "новая", ha="center", fontsize=8, color="#2B2D42")
    ax.set_xticks(list(x))
    ax.set_xticklabels([f"гр {g}\nDIM {last[g]['dim']}, {last[g]['heads']} г." for g in groups],
                       fontsize=7.5)
    ax.set_ylabel("Надой, л/сут")
    ax.set_ylim(0, max(after) * 1.2)
    ax.spines[["top", "right"]].set_visible(False)
    ax.axhline(0, color="#888888", linewidth=0.8)
    ax.legend()
    ax.set_title(f"Продуктивность по группам: {d1} → {d2} (Δ над парой столбцов)")
    fig.tight_layout()
    out = CASE_DIR / "charts" / f"groups_before_after_{d1}_{d2}.png"
    fig.savefig(out, dpi=150)
    plt.close(fig)
    print(f"OK: {out}")


if __name__ == "__main__":
    main()
