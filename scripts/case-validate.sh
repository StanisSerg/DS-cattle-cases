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
  for key in case_id date farm category status; do
    if ! grep -qE "^${key}:" "$file"; then
      warn "missing frontmatter key '$key' in $file"
    fi
  done
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
    validate_case "$entry"
  done
else
  validate_case "$CASES_DIR/$1"
fi

if [[ $ERR -ne 0 ]]; then
  echo
  echo "Validation FAILED with ${#ERRORS[@]} issue(s)."
  exit 1
fi

echo "All cases OK."
