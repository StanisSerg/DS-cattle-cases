# DS-cattle-cases

> **Тип репозитория:** DS (Data Space)  
> **Назначение:** Canonical source-of-truth для сырых кейсов (cases) по крупному рогатому скоту.  
> **Конвейер:** `CASE → DL → RULE`

## Что здесь хранится

- `cases/` — сырые факты с фермы: одно наблюдение, одна ситуация, одно вмешательство.
- `templates/` — шаблоны для создания новых кейсов.
- `scripts/` — автоматизация: `case-new`, `case-validate`.
- `.github/workflows/` — CI-проверка структуры кейсов.

## Быстрый старт

```bash
# Создать новый кейс
bash scripts/case-new.sh CASE-003 my-farm nutrition

# Проверить один кейс
bash scripts/case-validate.sh CASE-003

# Проверить все кейсы
bash scripts/case-validate.sh --all
```

## Структура кейса

```
cases/CASE-NNN-slug/
  CASE-NNN-slug.md   # основной файл кейса
  raw/               # исходные данные (xlsx, pdf, txt)
  charts/            # визуализации (png)
  reports/           # отчёты (md, docx)
  scripts/           # скрипты генерации графиков
  Rations/           # изменения в рационах (AMTS, PDF, XLSX)
```

## Связь с другими слоями

```
cases/CASE-NNN/
    ↓ (порождает)
decisions/DL-NNN.md
    ↓ (формализуется в)
PACK-*/pack/rules/RULE-NNN.md
    ↓ (применяется к следующему)
cases/CASE-NNN+1/
```

## Правила

1. Каждый кейс — одно наблюдение или одно вмешательство.
2. `status`: `raw` → `processed` → `archived`.
3. Сырые данные хранятся в `raw/`, никаких вычислений «на коленке» в основном md.
4. Автоматизация через `scripts/case-new.sh`; ручное создание — только в исключительных случаях.

---

*Подробности для агентов:* `CLAUDE.md` | `AGENTS.md`
