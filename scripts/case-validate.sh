#!/bin/bash
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
CASES_DIR="$ROOT/cases"
ERR=0
ERRORS=()

warn() {
  ERRORS+=("$1")
  echo "  ⚠ $1"
  ERR=1
}

validate_frontmatter() {
  local file="$1"
  for key in case_id date farm category status schema_version; do
    if ! grep -qE "^${key}:" "$file"; then
      warn "missing frontmatter key '$key' in $file"
    fi
  done

  # Проверка schema_version
  local sv
  sv="$(grep -E "^schema_version:" "$file" | sed 's/schema_version:[[:space:]]*//; s/["'"'"']//g' | tr -d ' ')"
  if [[ -n "$sv" && "$sv" != "1.0" ]]; then
    warn "unsupported schema_version '$sv' in $file (expected 1.0)"
  fi
}

validate_links() {
  local file="$1"
  local base
  local links
  base="$(dirname "$file")"
  links=$(grep -oE '\[([^]]+)\]\(([^)]+)\)' "$file" 2>/dev/null || true)
  while IFS= read -r match; do
    [[ -z "$match" ]] && continue
    link="${match#*](}"
    link="${link%)}"
    # strip angle brackets used for URLs with spaces
    link="${link#<}"
    link="${link%>}"
    # strip anchors
    link="${link%%#*}"
    [[ -z "$link" ]] && continue
    # skip external / absolute / mailto / anchors-only
    [[ "$link" == http* ]] && continue
    [[ "$link" == /* ]] && continue
    [[ "$link" == mailto* ]] && continue
    [[ "$link" == "CASE"*"→"* ]] && continue
    target="$base/$link"
    if [[ ! -e "$target" ]]; then
      echo "  ⚠ broken link in $file: '$link'"
    fi
  done <<< "$links"
}

validate_case() {
  local entry="$1"
  local name
  name="$(basename "$entry")"
  local file=""

  if [[ -f "$entry" && "$name" == *.md && "$name" != "README.md" && "$name" != "TEMPLATE-CASE.md" ]]; then
    file="$entry"
  elif [[ -d "$entry" ]]; then
    if [[ -f "$entry/$name.md" ]]; then
      file="$entry/$name.md"
    fi
  fi

  if [[ -z "$file" ]]; then
    warn "no main markdown file for $entry"
    return
  fi

  echo "Validating $name ..."

  [[ -f "$file" ]] || { warn "missing $file"; return; }

  validate_frontmatter "$file"

  if [[ -d "$entry" ]]; then
    [[ -d "$entry/raw" ]] || warn "missing $entry/raw"
    [[ -d "$entry/charts" ]] || warn "missing $entry/charts"
  fi

  # Report broken relative markdown links
  validate_links "$file"
}

if [[ "${1:-}" == "--all" || -z "${1:-}" ]]; then
  for entry in "$CASES_DIR"/*; do
    [[ -e "$entry" ]] || continue
    name="$(basename "$entry")"
    [[ "$name" == "README.md" ]] && continue
    [[ "$name" == "TEMPLATE-CASE.md" ]] && continue
    [[ "$name" == "index.yaml" ]] && continue
    validate_case "$entry"
  done
else
  validate_case "$CASES_DIR/$1"
fi

validate_index_consistency() {
  local index_file="$ROOT/cases/index.yaml"
  if [[ ! -f "$index_file" ]]; then
    warn "missing cases/index.yaml"
    return
  fi

  # Простая проверка: все директории кейсов есть в индексе
  for entry in "$CASES_DIR"/*; do
    [[ -e "$entry" ]] || continue
    local name
    name="$(basename "$entry")"
    [[ "$name" == "index.yaml" ]] && continue
    [[ "$name" == "README.md" ]] && continue
    [[ "$name" == "TEMPLATE-CASE.md" ]] && continue

    local case_id
    case_id="$(echo "$name" | grep -oE '^CASE-[0-9]{3}')"
    [[ -z "$case_id" ]] && continue

    if ! grep -qE "^- case_id: $case_id$" "$index_file"; then
      warn "case $case_id not found in cases/index.yaml"
    fi
  done
}

validate_index_consistency

if [[ $ERR -ne 0 ]]; then
  echo
  echo "Validation FAILED with ${#ERRORS[@]} issue(s)."
  exit 1
fi

echo "All cases OK."
