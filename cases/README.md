# Cases / Кейсы

> Canonical source-of-truth для сырых фактов с фермы.  
> Формат: вход → действие → результат

## Структура кейса

Каждый кейс — это **одно наблюдение** или **одна ситуация**:
- Проблема с конкретным животным
- Групповое событие
- Эксперимент/вмешательство

```
cases/CASE-NNN-slug/
  CASE-NNN-slug.md   # основной файл
  raw/               # исходные данные
  charts/            # визуализации
  reports/           # отчёты
  scripts/           # скрипты генерации
```

## Конвейер

```
CASE → DL → RULE
  ↓      ↓      ↓
Факты  Решение  Знание
```

**CASE сам по себе — ещё не система.**  
Это сырой материал для извлечения решений.

## Создание нового кейса

```bash
bash scripts/case-new.sh CASE-NNN farm-slug category
```

## Валидация

```bash
bash scripts/case-validate.sh --all
```

## Именование файлов

```
cases/CASE-NNN-{краткое-описание}.md          # простой кейс
cases/CASE-NNN-{краткое-описание}/            # кейс с подпапками
```

## Список кейсов

| # | Название | Статус | Категория |
|---|----------|--------|-----------|
| 001 | [BHB 1.6 — стандартная терапия неэффективна](CASE-001-bhb-threshold/CASE-001-bhb-threshold.md) | processed | metabolic |
| 002 | [КТ Зенченко МТК Ленинский](CASE-002-zencht-leninsky-dynamics/CASE-002-zencht-leninsky-dynamics.md) | processed | nutrition |
| COMPLEX-001 | [Смешанный метаболический кейс](CASE-COMPLEX-001-mixed-metabolic/CASE-COMPLEX-001-mixed-metabolic.md) | processed | metabolic |

---

*Не делай кейсы и не превращай их в правила = потеря знания*
