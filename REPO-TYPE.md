# Тип репозитория

**Тип**: `DS/cases`
**Система (SoI)**: Созидатель
**Содержание**: raw-facts, cases, farm-data
**Для кого**: агенты + пилот
**Source-of-truth**: yes (canonical cases)

## Upstream dependencies

- `PACK-cattle-science` — методы, шаблоны, ontology
- `DS-cattle-operations` — operational context, decisions

## Downstream outputs

- `DS-cattle-operations/decisions/` — decision layers
- `PACK-*/pack/rules/` — обобщённые правила

## Non-goals

- Хранение финальных правил (→ Pack)
- Хранение operational decisions (→ DS-cattle-operations)
- Хранение кода приложений (→ instrument repos)
