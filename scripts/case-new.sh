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

mkdir -p "$CASE_DIR"/{raw,charts,reports,scripts}
cp "$TEMPLATE" "$CASE_FILE"

TODAY="$(date +%Y-%m-%d)"
# Заменяем CASE-XXX на реальный case_id, даты и категорию
sed -i "s/CASE-001/$CASE_ID/g" "$CASE_FILE"
sed -i "s/YYYY-MM-DD/$TODAY/g" "$CASE_FILE"
sed -i "s/\[metabolic|reproduction|nutrition|economics|management\]/$CATEGORY/g" "$CASE_FILE"

echo "✅ Создан кейс: $CASE_DIR"
echo "   Основной файл: $CASE_FILE"
echo "   Далее:"
echo "   1. Заполните $CASE_FILE"
echo "   2. Положите сырые данные в $CASE_DIR/raw/"
echo "   3. Запустите: bash scripts/case-validate.sh $CASE_ID"

# Опциональный авто-коммит
if [ "${DS_CASES_AUTO_COMMIT:-}" = "true" ]; then
    cd "$REPO_DIR"
    git add "$CASE_DIR"
    git commit -m "feat(cases): add $CASE_ID ($SLUG)" --trailer "Co-Authored-By: Kimi <noreply@moonshot.ai>"
    git push origin main
    echo "✅ Запушено на GitHub"
fi
