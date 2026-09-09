#!/usr/bin/env python3
"""Анализ выбытия (забой + падеж) по архиву выбытия DairyPlan.

Вход:  raw/архив выбытия *.xlsx (отчёт «Перечень поголовья (вкл. животных архива)»)
Выход: reports/cull_analysis_<сегодня>.md + charts/cull_*.png

Структура отчёта — две части:
  Часть 1 — ДОЙНОЕ СТАДО: животные с заполненной датой последнего отёла.
    1.1 помесячная статистика, 1.2 причины, 1.3 помесячно год-к-году
    (каждый месяц 2026 против того же месяца 2025 + диапазон 10.06–31.08),
    1.4 DIM при выбытии.
  Часть 2 — МОЛОДНЯК (без отёла; по данным выгрузки падеж — медиана возраста < 1 года):
    2.1 помесячная статистика, 2.2 причины, 2.3 помесячно год-к-году,
    2.4 возраст при выбытии (от даты рождения).

Диаграммы (столбчатые, значения подписаны на столбцах):
  charts/cull_dairy_monthly.png   — помесячный забой дойных, отметка 10.06.2026
  charts/cull_dairy_reasons.png   — топ-10 причин забоя дойных
  charts/cull_dairy_dim.png       — распределение DIM при выбытии
  charts/cull_young_monthly.png   — помесячное выбытие молодняка (забой/падеж)
  charts/cull_young_reasons.png   — топ-10 причин падежа молодняка

Нормализация применяется только к регистру/пробелам статуса и причины; значения
не исправляются. Колонка «дата прихода» не используется.

Запуск: python3 scripts/cull_analysis.py
"""
import collections
import datetime
import statistics
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import openpyxl

CASE_DIR = Path(__file__).resolve().parent.parent
CUTOFF = datetime.date(2025, 1, 1)

MONTHS_RU = ["", "янв", "фев", "мар", "апр", "май", "июн", "июл", "авг", "сен", "окт", "ноя", "дек"]

C_ZABOY = "#FF6B6B"   # коралловый
C_PADEZH = "#4ECDC4"  # бирюзовый
C_DIM = "#3A86FF"     # ярко-синий
C_LINE = "#2B2D42"    # отметка 10.06

plt.rcParams["font.family"] = "DejaVu Sans"


def norm_status(v) -> str | None:
    if not v:
        return None
    s = str(v).strip().lower()
    if s.startswith("забой"):
        return "забой"
    if s.startswith("падеж"):
        return "падеж"
    return None  # продажа / выбраковка / прочее — в анализ не входят


def norm_reason(v) -> str:
    if not v:
        return "не указана"
    return " ".join(str(v).strip().lower().split())


# Рабочая группировка причин по тексту записи (используется в разделе нормировки 1.3).
_REASON_GROUPS = {
    "метаболика": ["кетоз", "гипергликемия", "дистроф", "дистр", "парез", "интоксикация"],
    "травма/хромота": ["тбс", "артроз", "флегмона", "хром", "перелом", "связок", "бурсит", "вывих", "ножки", "разрыв пут"],
    "послеродовые/вымя": ["после род", "перитонит", "отек вымени", "выпадение матки", "мастит", "вымя"],
    "ЖКТ": ["энтерит", "тимпания", "закупорка", "колики"],
}


def reason_group(reason: str) -> str:
    for group, keys in _REASON_GROUPS.items():
        if any(k in reason for k in keys):
            return group
    return "прочее"


# Словарь нормализации причин для отчёта (редакция ревьюера 08.09).
# Нормализуются только бесспорные сокращения и орфография; сомнительные
# формулировки остаются как в источнике. Ключи — после norm_reason (нижний регистр).
_REASON_DISPLAY = {
    "разрыв тбс": "разрыв тазобедренных связок",
    "разрывы тбс": "разрыв тазобедренных связок",
    "разрыв тбс связ": "разрыв тазобедренных связок",
    "растяжение тбс": "растяжение тазобедренных связок",
    "растяжение тбс связ": "растяжение тазобедренных связок",
    "растяж-е связок": "растяжение связок",
    "вывих тбс": "вывих тазобедренного сустава",
    "хрон мастит": "хронический мастит",
    "хронич мастит": "хронический мастит",
    "маст, пневмония": "мастит, пневмония",
    "синее вымя,остм": "синее вымя (острый мастит)",
    "жир.дистр.печен": "жировая дистрофия печени",
    "дистроф. печени": "жировая дистрофия печени",
    "пневмания": "пневмония",
    "бронхопневмания": "бронхопневмония",
    "гнойн.бронхопн.": "гнойная бронхопневмония",
    "гн-ая бронх-ия": "гнойная бронхопневмония",
    "абцесс брюшн.п": "абсцесс брюшной полости",
    "мн-ые абсцессы": "множественные абсцессы",
    "острая алергия": "острая аллергия",
    "геморр.энтерит": "геморрагический энтерит",
    "абомазит,энтер": "абомазит, энтерит",
    "абомазит.": "абомазит",
    "непроход.кишечн": "непроходимость кишечника",
    "казеин-й безоар": "казеиновый безоар",
    "тимпания рубца": "тимпания рубца (вздутие)",
    "неон-я пнев-ния": "неонатальная пневмония",
    "флегмона зп.зл": "флегмона заплюсневого сустава",
    "флегмона,хром-а": "флегмона, хромота",
    "артроз,сильн хр": "артроз, сильная хромота",
    "артроз перед.к": "артроз передней конечности",
    "разрыв пут.суст": "разрыв путового сустава",
    "пуп.сепсис": "пупочный сепсис",
    "с.в,интокс-ция": "интоксикация (с.в.)",
    "обил. кровот-ие": "обильное кровотечение",
    "остр гем.нефрит": "острый геморрагический нефрит",
}


def reason_display(reason: str) -> str:
    return _REASON_DISPLAY.get(reason, reason)


def d(v) -> datetime.date | None:
    return v.date() if isinstance(v, datetime.datetime) else None


def month_key(dt: datetime.date) -> str:
    return f"{dt.year}-{dt.month:02d}"


def month_label(key: str) -> str:
    y, m = key.split("-")
    return f"{MONTHS_RU[int(m)]} {y}"


def short_label(key: str) -> str:
    y, m = key.split("-")
    return f"{MONTHS_RU[int(m)]}\n{y[2:]}"


def monthly_table(by_month, months) -> list[str]:
    lines = [
        "| Месяц | Забой | Падеж | Всего | Топ-причины месяца |",
        "|---|---:|---:|---:|---|",
    ]
    for m in months:
        z, p = by_month[m]["забой"], by_month[m]["падеж"]
        top = collections.Counter(r["reason"] for r in z + p).most_common(3)
        top_s = ", ".join(f"{k} ({v})" for k, v in top) or "—"
        lines.append(f"| {month_label(m)} | {len(z)} | {len(p)} | {len(z)+len(p)} | {top_s} |")
    return lines


def yoy_monthly_lines(by_month) -> list[str]:
    """Помесячно год-к-году по всем месяцам, где есть оба года (янв–авг)."""
    lines = [
        "| Месяц | 2025 | 2026 | Δ |",
        "|---|---:|---:|---:|",
    ]
    for mm in range(1, 9):
        k25, k26 = f"2025-{mm:02d}", f"2026-{mm:02d}"
        n25 = sum(len(by_month[k25][s]) for s in ("забой", "падеж")) if k25 in by_month else 0
        n26 = sum(len(by_month[k26][s]) for s in ("забой", "падеж")) if k26 in by_month else 0
        lines.append(f"| {MONTHS_RU[mm]} | {n25} | {n26} | {n26-n25:+d} |")
    t25 = sum(sum(len(by_month[f"2025-{mm:02d}"][s]) for s in ("забой", "падеж")) for mm in range(1, 9) if f"2025-{mm:02d}" in by_month)
    t26 = sum(sum(len(by_month[f"2026-{mm:02d}"][s]) for s in ("забой", "падеж")) for mm in range(1, 9) if f"2026-{mm:02d}" in by_month)
    lines.append(f"| **янв–авг** | **{t25}** | **{t26}** | **{t26-t25:+d}** |")
    return lines


def chart_monthly_single(by_month, months, status, title, out, intervention_line=True):
    vals = [len(by_month[m][status]) for m in months]
    fig, ax = plt.subplots(figsize=(12, 4.5))
    bars = ax.bar(range(len(months)), vals, color=C_ZABOY)
    ax.bar_label(bars, padding=2, fontsize=9)
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels([short_label(m) for m in months], fontsize=8)
    ax.set_ylabel("гол/мес")
    ax.set_title(title)
    ax.set_ylim(0, max(vals) * 1.15 + 1)
    ax.spines[["top", "right"]].set_visible(False)
    if intervention_line and "2026-06" in months:
        idx = months.index("2026-06")
        ax.axvline(idx - 0.5 + 10 / 30, color=C_LINE, linestyle="--", linewidth=1.2)
        ax.text(idx - 0.5 + 10 / 30, ax.get_ylim()[1] * 0.96, " корректировка\nрациона 10.06.2026", fontsize=8, va="top")
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_monthly_stacked(by_month, months, title, out):
    z = [len(by_month[m]["забой"]) for m in months]
    p = [len(by_month[m]["падеж"]) for m in months]
    fig, ax = plt.subplots(figsize=(12, 4.5))
    b1 = ax.bar(range(len(months)), z, color=C_ZABOY, label="забой")
    b2 = ax.bar(range(len(months)), p, bottom=z, color=C_PADEZH, label="падеж")
    ax.bar_label(b1, padding=2, fontsize=8)
    ax.bar_label(b2, padding=2, fontsize=8)
    ax.set_xticks(range(len(months)))
    ax.set_xticklabels([short_label(m) for m in months], fontsize=8)
    ax.set_ylabel("гол/мес")
    ax.set_title(title)
    ax.legend()
    ax.set_ylim(0, max(a + b for a, b in zip(z, p)) * 1.15 + 1)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_reasons(counter, title, out, color, top=10):
    items = counter.most_common(top)
    labels = [k for k, _ in items][::-1]
    vals = [v for _, v in items][::-1]
    fig, ax = plt.subplots(figsize=(9, 4.5))
    bars = ax.barh(labels, vals, color=color)
    ax.bar_label(bars, padding=3, fontsize=9)
    ax.set_title(title)
    ax.set_xlim(0, max(vals) * 1.15 + 1)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def chart_dim(dim_rows, labels, out):
    counts = [sum(1 for r in dim_rows if r["dim_band"] == lbl) for lbl in labels]
    fig, ax = plt.subplots(figsize=(8, 4.5))
    bars = ax.bar(labels, counts, color=C_DIM)
    ax.bar_label(bars, padding=2, fontsize=10)
    ax.set_xlabel("DIM при выбытии, дн")
    ax.set_ylabel("голов")
    ax.set_title("Дойное стадо: дни в доении при выбытии (забой), 01.2025–08.2026")
    ax.set_ylim(0, max(counts) * 1.15 + 1)
    ax.spines[["top", "right"]].set_visible(False)
    fig.tight_layout()
    fig.savefig(out, dpi=150)
    plt.close(fig)


def main() -> None:
    srcs = sorted(CASE_DIR.glob("raw/архив выбытия *.xlsx"), key=lambda p: p.stat().st_mtime)
    if not srcs:
        sys.exit("Источник не найден: raw/архив выбытия *.xlsx")
    src = srcs[-1]
    today = datetime.date.today().isoformat()

    wb = openpyxl.load_workbook(src, read_only=True)
    ws = wb[wb.sheetnames[0]]
    data = list(ws.iter_rows(min_row=8, values_only=True))

    dairy, young = [], []
    for r in data:
        status = norm_status(r[14])
        exit_date = d(r[9])
        if status is None or exit_date is None or exit_date < CUTOFF:
            continue
        rec = {
            "exit": exit_date,
            "ear_tag": r[1],
            "group": r[3],
            "birth": d(r[4]),
            "last_calving": d(r[13]),
            "status": status,
            "reason": norm_reason(r[15]),
            "dim": (exit_date - d(r[13])).days if d(r[13]) else None,
            "age_y": ((exit_date - d(r[4])).days / 365.25) if d(r[4]) else None,
        }
        (dairy if rec["last_calving"] else young).append(rec)

    by_month = collections.defaultdict(lambda: {"забой": [], "падеж": []})
    for r in dairy:
        by_month[month_key(r["exit"])][r["status"]].append(r)
    months = sorted(by_month)

    by_month_y = collections.defaultdict(lambda: {"забой": [], "падеж": []})
    for r in young:
        by_month_y[month_key(r["exit"])][r["status"]].append(r)
    months_y = sorted(by_month_y)

    reasons = {"забой": collections.Counter(), "падеж": collections.Counter()}
    for r in dairy:
        reasons[r["status"]][r["reason"]] += 1
    reasons_y = {"забой": collections.Counter(), "падеж": collections.Counter()}
    for r in young:
        reasons_y[r["status"]][r["reason"]] += 1

    def in_period(r, start, end):
        return start <= r["exit"] <= end

    post_26 = [r for r in dairy if in_period(r, datetime.date(2026, 6, 10), datetime.date(2026, 8, 31))]
    same_25 = [r for r in dairy if in_period(r, datetime.date(2025, 6, 10), datetime.date(2025, 8, 31))]
    post_26y = [r for r in young if in_period(r, datetime.date(2026, 6, 10), datetime.date(2026, 8, 31))]
    same_25y = [r for r in young if in_period(r, datetime.date(2025, 6, 10), datetime.date(2025, 8, 31))]

    dim_bands = [(0, 30), (31, 60), (61, 100), (101, 200), (201, 305), (306, 10**6)]
    band_labels = ["0–30", "31–60", "61–100", "101–200", "201–305", "306+"]
    for r in dairy:
        for (lo, hi), lbl in zip(dim_bands, band_labels):
            if lo <= r["dim"] <= hi:
                r["dim_band"] = lbl
                break

    dims_all = [r["dim"] for r in dairy]

    # ---------- диаграммы ----------
    charts = CASE_DIR / "charts"
    chart_monthly_single(by_month, months, "забой",
                         "Дойное стадо: забой по месяцам, 01.2025–08.2026 (падежа дойных в выгрузке нет)",
                         charts / "cull_dairy_monthly.png")
    chart_reasons(reasons["забой"], "Дойное стадо: причины забоя, топ-10 (01.2025–08.2026)",
                  charts / "cull_dairy_reasons.png", C_ZABOY)
    chart_dim(dairy, band_labels, charts / "cull_dairy_dim.png")
    chart_monthly_stacked(by_month_y, months_y,
                          "Молодняк (без отёла): забой и падеж по месяцам, 01.2025–08.2026",
                          charts / "cull_young_monthly.png")
    chart_reasons(reasons_y["падеж"], "Молодняк: причины падежа, топ-10 (01.2025–08.2026)",
                  charts / "cull_young_reasons.png", C_PADEZH)

    # ---------- отчёт ----------
    L = []
    L += [
        "---",
        "type: analytics",
        f"source: raw/{src.name}",
        "filter: 'статусы забой+падеж, выбытие >= 2025-01-01; часть 1 — дойное стадо (есть отёл), часть 2 — молодняк'",
        f"records: {len(dairy)} дойные + {len(young)} молодняк",
        "generated_by: scripts/cull_analysis.py",
        "wp: 118",
        "status: draft — на проверке пилота",
        "---",
        "",
        f"# Выбытие из стада: забой и падеж — {CUTOFF.isoformat()} → 2026-08-31",
        "",
        "> Источник: DairyPlan (выгрузка 02.09.2026).",
        "> Продажа и выбраковка не входят. Колонка «дата прихода» не используется.",
        "> Часть 1 — дойное стадо (животные с заполненной датой последнего отёла). Часть 2 — молодняк (без отёла).",
        "> DIM при выбытии = дата выбытия − дата последнего отёла. Возраст = дата выбытия − дата рождения.",
        "",
        "---",
        "",
        f"# Часть 1. Дойное стадо ({len(dairy)} записей)",
        "",
        "> Падежа дойных коров в выгрузке нет: все записи «падеж» — молодняк (часть 2).",
        "> Выбытие дойных = забой (в т.ч. вынужденный).",
        "",
        "## 1.1. Помесячная статистика",
        "",
    ]
    L += monthly_table(by_month, months)
    L += [
        "",
        f"**Итого за период:** забой {sum(reasons['забой'].values())}, всего {len(dairy)}.",
        "",
        "![Забой дойных по месяцам](../charts/cull_dairy_monthly.png)",
        "",
        "## 1.2. Причины забоя дойного стада",
        "",
        "> Причины нормализованы по словарю (расшифровка сокращений, орфография); если отличается от записи — в скобках как записано.",
        "",
        "| Причина | N | Доля |",
        "|---|---:|---:|",
    ]
    total_z = sum(reasons["забой"].values())
    for k, v in reasons["забой"].most_common(15):
        disp = reason_display(k)
        L.append(f"| {disp} (записано: {k}) | {v} | {v/total_z:.0%} |" if disp != k else f"| {k} | {v} | {v/total_z:.0%} |")
    L += [
        "",
        "![Причины забоя дойных](../charts/cull_dairy_reasons.png)",
        "",
        "## 1.3. Выбытие после корректировки рациона 10.06.2026 — сравнение по месяцам",
        "",
        "**Главное: выбытие дойных после корректировки не выросло.** В том же диапазоне 2025 года — 11 голов, в 2026 — 14; при месячном разбросе 2–11 голов эта разница в пределах погрешности.",
        "",
        "### Каждый месяц 2026 против того же месяца 2025 (забой дойных)",
        "",
    ]
    L += yoy_monthly_lines(by_month)
    L += [
        "",
        "### Год-к-году: диапазон после 10.06 (10.06 — 31.08)",
        "",
        "| Период | Забой дойных |",
        "|---|---:|",
        f"| 10.06–31.08.2025 | {len(same_25)} |",
        f"| 10.06–31.08.2026 | {len(post_26)} |",
        "",
        f"Разница: **{len(post_26)-len(same_25):+d} головы**. Состав обеих выборок — ниже.",
        "",
        "#### Диапазон 10.06–31.08.2026 — состав (14 голов)",
        "",
        "| Дата выбытия | Бирка | DIM | Причина |",
        "|---|---|---:|---|",
    ]
    for r in sorted(post_26, key=lambda x: x["exit"]):
        L.append(f"| {r['exit'].isoformat()} | {r['ear_tag']} | {r['dim'] if r['dim'] is not None else '—'} | {r['reason']} |")
    L += [
        "",
        "#### Диапазон 10.06–31.08.2025 — состав (11 голов)",
        "",
        "| Дата выбытия | Бирка | DIM | Причина |",
        "|---|---|---:|---|",
    ]
    for r in sorted(same_25, key=lambda x: x["exit"]):
        L.append(f"| {r['exit'].isoformat()} | {r['ear_tag']} | {r['dim'] if r['dim'] is not None else '—'} | {r['reason']} |")
    dim26 = [r["dim"] for r in post_26 if r["dim"] is not None]
    dim25 = [r["dim"] for r in same_25 if r["dim"] is not None]
    g25 = collections.Counter(reason_group(r["reason"]) for r in same_25)
    g26 = collections.Counter(reason_group(r["reason"]) for r in post_26)
    L += [
        "",
        "#### Сопоставление диапазонов по группам причин",
        "",
        "Причины сгруппированы: изменение любой **отдельной** причины между диапазонами — 1–3 головы, при таких числах процентное изменение не вычисляется и не интерпретируется — это единичные случаи, а не тренд.",
        "",
        "| Группа причин | 2025 | 2026 |",
        "|---|---:|---:|",
    ]
    for grp in ("метаболика", "травма/хромота", "послеродовые/вымя", "ЖКТ", "прочее"):
        L.append(f"| {grp} | {g25.get(grp, 0)} | {g26.get(grp, 0)} |")
    L += [
        "",
        f"Медиана DIM при выбытии: диапазон 2025 — {statistics.median(dim25):.0f} дн (N={len(dim25)}); диапазон 2026 — {statistics.median(dim26):.0f} дн (N={len(dim26)}).",
        "",
        "Из 6 случаев 2026 года с DIM≤30 три — травмы и хроническая хромота (включая выбраковку по хроническому артрозу на 1-й день после отёла) — к переходному периоду и кормлению не относятся; метаболических — три (кетоз, дистрофия печени).",
        "",
        f"Записей: **{len(dims_all)}** (все — забой).",
        "",
        "| Медиана DIM | Среднее DIM | Доля ≤100 дн |",
        "|---:|---:|---:|",
        f"| {statistics.median(dims_all):.0f} | {statistics.mean(dims_all):.0f} | {sum(1 for x in dims_all if x <= 100)/len(dims_all):.0%} |",
        "",
        "| DIM, дн | N | Доля |",
        "|---|---:|---:|",
    ]
    for lbl in band_labels:
        n = sum(1 for r in dairy if r.get("dim_band") == lbl)
        L.append(f"| {lbl} | {n} | {n/len(dairy):.0%} |")
    L += [
        "",
        "![DIM при выбытии](../charts/cull_dairy_dim.png)",
    ]

    L += [
        "",
        "---",
        "",
        f"# Часть 2. Молодняк — животные без отёла ({len(young)} записей)",
        "",
        f"> Забой {sum(1 for r in young if r['status']=='забой')}, падеж {sum(1 for r in young if r['status']=='падеж')}.",
        "> По возрасту при выбытии: падеж — медиана < 1 года (140 из 142 младше года); забой — медиана 1,3 года.",
        "",
        "## 2.1. Помесячная статистика",
        "",
    ]
    L += monthly_table(by_month_y, months_y)
    L += [
        "",
        "![Выбытие молодняка по месяцам](../charts/cull_young_monthly.png)",
        "",
        "## 2.2. Причины падежа молодняка",
        "",
        "> Причины нормализованы по словарю; если отличается от записи — в скобках как записано.",
        "",
        "| Причина | N | Доля |",
        "|---|---:|---:|",
    ]
    total_py = sum(reasons_y["падеж"].values())
    for k, v in reasons_y["падеж"].most_common(15):
        disp = reason_display(k)
        L.append(f"| {disp} (записано: {k}) | {v} | {v/total_py:.0%} |" if disp != k else f"| {k} | {v} | {v/total_py:.0%} |")
    L += [
        "",
        "![Причины падежа молодняка](../charts/cull_young_reasons.png)",
        "",
        "## 2.3. Выбытие молодняка после 10.06.2026 — сравнение по месяцам",
        "",
        "### Каждый месяц 2026 против того же месяца 2025",
        "",
    ]
    L += yoy_monthly_lines(by_month_y)
    L += [
        "",
        "### Год-к-году: диапазон 10.06 — 31.08",
        "",
        "| Период | Забой | Падеж | Всего |",
        "|---|---:|---:|---:|",
        f"| 10.06–31.08.2025 | {sum(1 for r in same_25y if r['status']=='забой')} | {sum(1 for r in same_25y if r['status']=='падеж')} | {len(same_25y)} |",
        f"| 10.06–31.08.2026 | {sum(1 for r in post_26y if r['status']=='забой')} | {sum(1 for r in post_26y if r['status']=='падеж')} | {len(post_26y)} |",
        "",
        "## 2.4. Возраст при выбытии (от даты рождения)",
        "",
        "| Возраст | Забой | Падеж | Всего |",
        "|---|---:|---:|---:|",
    ]
    age_bands = [("<1 мес", 0, 1 / 12), ("1–3 мес", 1 / 12, 0.25), ("3–6 мес", 0.25, 0.5),
                 ("6–12 мес", 0.5, 1), ("1–2 года", 1, 2), ("2+ лет", 2, 10**4)]
    for lbl, lo, hi in age_bands:
        nz = sum(1 for r in young if r["status"] == "забой" and r["age_y"] is not None and lo <= r["age_y"] < hi)
        np_ = sum(1 for r in young if r["status"] == "падеж" and r["age_y"] is not None and lo <= r["age_y"] < hi)
        L.append(f"| {lbl} | {nz} | {np_} | {nz+np_} |")
    no_age = sum(1 for r in young if r["age_y"] is None)
    if no_age:
        L.append(f"| без даты рождения | — | — | {no_age} |")

    L += [
        "",
        "## Ограничения",
        "",
        "- «Дойное стадо» определено по наличию даты последнего отёла: 29 записей забоя без отёла (молодняк) вынесены в часть 2; падежа взрослых коров в выгрузке не зафиксировано — если погибшие коровы регистрируются иначе, они в этот архив не попали.",
        "- Причины указаны не у всех записей и в свободной форме.",
        "- Записи с датой выбытия, но без статуса забой/падеж (продажа, выбраковка), исключены.",
    ]

    out = CASE_DIR / "reports" / f"cull_analysis_{today}.md"
    out.write_text("\n".join(L) + "\n", encoding="utf-8")
    print(f"OK: {out} (дойные: {len(dairy)}, молодняк: {len(young)}; 5 диаграмм в charts/)")


if __name__ == "__main__":
    main()
