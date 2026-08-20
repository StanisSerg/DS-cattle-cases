# Стандарт графиков динамики молока (CASE-xxx)

Эталонная реализация: `cases/CASE-002-zencht-leninsky-dynamics/scripts/chart_len_milk_dynamics.py`.
Итоговый вид согласован пилотом 2026-08-20 — новые графики делать по этому рецепту без итераций правок.

## Запуск

```bash
cd cases/CASE-NNN-slug/scripts
/home/asus/IWE/.tmp-tools/case-charts-venv/bin/python chart_<имя>.py
```

(venv с matplotlib: `.tmp-tools/case-charts-venv`; системный python matplotlib не имеет.)

## Обязательные параметры

| Элемент | Значение |
|---|---|
| Период | с даты-стартa кейса (напр. 2026-06-08); ранние «контекстные» точки не включаем |
| Макет | `plt.subplots(2, 1, figsize=(12, 8), sharex=True)` — удой сверху, реализация снизу |
| Верхний график (удой, л/сут) | цвет `#1f77b4` (синий) |
| Нижний график (реализация, тыс. кг/сут) | цвет `#2ca02c` (зелёный); кг → тыс. кг делением на 1000 |
| Замеры | точки `'o'`, `alpha=0.35, ms=4` |
| Скользящее среднее | окно **3 календарных дня**: `series.rolling('3D', min_periods=1).mean()`, сплошная линия `lw=2` |
| Тренд | линейный (МНК), пунктир `'--'`, `lw=1.5`; в легенде наклон в неделю (`тренд +0.14 л/нед`) |
| Средняя продуктивность | `axhline` точками `ls=':'`, значение — **в легенде**, не надписью на поле |
| Подписи значений у точек | **через одну точку** (`i % 2 == 0`), `fontsize=7`, `alpha=0.85`, смещение `(0, 5)` pt |
| Отступы по Y | `ax.margins(y=0.12)` — подписи не упираются в рамку |
| Легенда | `loc='lower right', fontsize=9` |
| Сетка | `ax.grid(alpha=0.3)` |

## Ось дат

- Первая и последняя даты — **обязательно**.
- Промежуточные — каждые 14 дней, но не ближе 7 дней к последней (иначе подписи налезают):

```python
ticks = [first]
t = first + pd.Timedelta(days=14)
while t < last - pd.Timedelta(days=7):
    ticks.append(t)
    t += pd.Timedelta(days=14)
ticks.append(last)
ax2.set_xticks(ticks)
```

- Формат `%d.%m.%Y`, поворот 30° (`plt.setp(ax.get_xticklabels(), rotation=30, ha='right')`).
- Подписи дат на **обоих** графиках: `ax.tick_params(labelbottom=True)` для верхнего.

## Прочее

- `matplotlib.use('Agg')` до импорта pyplot (headless).
- Заголовок: `<Ферма>: продуктивность и реализация, DD.MM.YYYY — DD.MM.YYYY`.
- Сохранение: `dpi=150, bbox_inches='tight', facecolor='white'` в `charts/`.
- Имя файла: `<метрики>_<farm>_<период>.png`, напр. `milk_yield_realization_Len_2026-06_08.png`.
- Данные — из `raw/milk_dynamics_*.md`, парсинг через `parse_md_table` из `analyze_productivity_dynamics.py`.
