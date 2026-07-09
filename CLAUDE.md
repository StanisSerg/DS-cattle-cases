# CLAUDE.md — Инструкции для DS-cattle-cases

> **Тип репозитория:** DS/cases  
> **Назначение:** Canonical source-of-truth для сырых кейсов по КРС  
> **Связь:** upstream — PACK-cattle-science (методы); downstream — decisions и rules

## Архитектура: CASE → DL → RULE

```
┌─────────────────────────────────────────────────────────────┐
│                    DS-cattle-cases                          │
├─────────────────────────────────────────────────────────────┤
│  cases/          templates/         scripts/                │
│  (сырые факты)   (шаблоны)          (автоматизация)         │
│       ↓                                                       │
│   CASE-001 ──→    DL-001 ──→ │
│       ↓              ↓                                      │
│   Валидация      Формализация                               │
│       ↓              ↓                                      │
└───────┴──────────────┴──────────────────────────────────────┘
        ↓
┌─────────────────────────────────────────────────────────────┐
│              PACK-cattle-science / other PACKs              │
│              pack/rules/                                    │
│              (обобщённые знания)                            │
└─────────────────────────────────────────────────────────────┘
```

## Правила работы с cases

1. **Создание кейса** — только через `bash scripts/case-new.sh CASE-NNN farm-slug [category]`.
2. **Структура кейса**:
   - `CASE-NNN-slug.md` — основной файл;
   - `raw/` — исходные данные;
   - `charts/` — графики;
   - `reports/` — отчёты;
   - `scripts/` — скрипты генерации;
   - `Rations/` — изменения в рационах.
3. **Статусы кейса:** `raw` → `processed` → `archived`.
4. **Валидация** перед коммитом: `bash scripts/case-validate.sh --all`.

## Automation

- `scripts/case-new.sh` — scaffold нового кейса.
- `scripts/case-validate.sh` — проверка структуры и completeness.
- `.github/workflows/validate-case.yml` — CI-гейт.

## Naming convention

```
cases/CASE-NNN-{краткое-описание}.md          # простой кейс
cases/CASE-NNN-{краткое-описание}/            # кейс с подпапками
```

## Cross-links

- Ссылки на Pack: `../../PACK-cattle-science/pack/rules/RULE-XXX.md`
- Ссылки на decisions: `DL-XXX.md`
