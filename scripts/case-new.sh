#!/usr/bin/env bash
# case-new.sh — scaffold нового кейса в DS-cattle-cases
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
CASES_DIR="$REPO_DIR/cases"
TEMPLATE="$REPO_DIR/templates/TEMPLATE-CASE.md"

usage() {
    echo "Usage: $0 <CASE-NNN> <farm-slug> [category]"
    echo "Example: $0 CASE-003 my-farm nutrition"
    exit 1
}

if [ $# -lt 2 ]; then
    usage
fi

CASE_ID="$1"
SLUG="$2"
CATEGORY="${3:-nutrition}"

if [[ ! "$CASE_ID" =~ ^CASE-[0-9]{3}$ ]]; then
    echo "❌ case_id должен быть формата CASE-NNN (например, CASE-003)"
    exit 1
fi

if [[ ! "$SLUG" =~ ^[a-z0-9-]+$ ]]; then
    echo "❌ farm-slug должен содержать только строчные латинские буквы, цифры и дефис"
    exit 1
fi

CASE_DIR="$CASES_DIR/${CASE_ID}-${SLUG}"
CASE_FILE="$CASE_DIR/${CASE_ID}-${SLUG}.md"

if [ -e "$CASE_DIR" ]; then
    echo "❌ Кейс $CASE_DIR уже существует"
    exit 1
fi

mkdir -p "$CASE_DIR"/{raw,charts,reports,scripts,Rations}
cp "$TEMPLATE" "$CASE_FILE"

TODAY="$(date +%Y-%m-%d)"
REVIEW_DATE="$(date -d '+30 days' +%Y-%m-%d 2>/dev/null || date -v+30d +%Y-%m-%d 2>/dev/null || echo 'YYYY-MM-DD')"

# Заменяем CASE-XXX на реальный case_id, даты и категорию
# Важен порядок: сначала review_date, потом общие YYYY-MM-DD
sed -i "s/CASE-001/$CASE_ID/g" "$CASE_FILE"
sed -i "s/review_date: YYYY-MM-DD/review_date: $REVIEW_DATE/g" "$CASE_FILE"
sed -i "s/YYYY-MM-DD/$TODAY/g" "$CASE_FILE"
sed -i "s/\[metabolic|reproduction|nutrition|economics|management\]/$CATEGORY/g" "$CASE_FILE"

# Добавляем кейс в индекс
INDEX_FILE="$REPO_DIR/cases/index.yaml"
python3 - "$INDEX_FILE" "$CASE_ID" "$SLUG" "$CATEGORY" "$TODAY" "$REVIEW_DATE" <<'PY'
import sys
import yaml
from pathlib import Path

index_file = Path(sys.argv[1])
case_id = sys.argv[2]
slug = sys.argv[3]
category = sys.argv[4]
today = sys.argv[5]
review_date = sys.argv[6]

if index_file.exists():
    with open(index_file, 'r', encoding='utf-8') as f:
        data = yaml.safe_load(f) or {}
else:
    data = {'schema_version': '1.0', 'last_updated': today, 'cases': []}

data['last_updated'] = today

# Удаляем существующую запись, если есть
existing = [c for c in data.get('cases', []) if c.get('case_id') != case_id]

existing.append({
    'case_id': case_id,
    'slug': slug,
    'farm': '',
    'author': '',
    'category': category,
    'tags': [],
    'status': 'raw',
    'dl_ref': [],
    'rule_refs': [],
    'fpf_context': [],
    'pack_relations': {
        'related_entities': [],
        'related_methods': [],
        'related_sota': [],
        'related_dpf': [],
    },
    'created': today,
    'updated': today,
    'review_date': review_date if review_date != 'YYYY-MM-DD' else None,
})

data['cases'] = existing

with open(index_file, 'w', encoding='utf-8') as f:
    f.write('# Индекс кейсов DS-cattle-cases\n')
    f.write('# Генерируется автоматически через scripts/case-new.sh\n')
    f.write('# Ручное редактирование допускается, но при создании нового кейса индекс пересобирается.\n\n')
    yaml.dump(data, f, allow_unicode=True, sort_keys=False)
PY

echo "✅ Создан кейс: $CASE_DIR"
echo "   Основной файл: $CASE_FILE"
echo "   Далее:"
echo "   1. Заполните $CASE_FILE"
echo "   2. Положите сырые данные в $CASE_DIR/raw/"
echo "   3. Запустите: bash scripts/case-validate.sh $CASE_ID"
echo "   4. Проверьте и дополните запись в cases/index.yaml"

# Опциональный авто-коммит
if [ "${DS_CASES_AUTO_COMMIT:-}" = "true" ]; then
    cd "$REPO_DIR"
    git add "$CASE_DIR"
    git commit -m "feat(cases): add $CASE_ID ($SLUG)" --trailer "Co-Authored-By: Kimi <noreply@moonshot.ai>"
    git push origin main
    echo "✅ Запушено на GitHub"
fi
