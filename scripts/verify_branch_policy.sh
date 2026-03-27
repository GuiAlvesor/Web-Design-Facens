#!/usr/bin/env bash
set -euo pipefail

required_branches=("main" "develop")

for branch in "${required_branches[@]}"; do
  if ! git show-ref --verify --quiet "refs/heads/${branch}"; then
    echo "❌ Branch obrigatória ausente: ${branch}"
    exit 1
  fi
done

if ! git merge-base --is-ancestor main develop; then
  echo "❌ Política violada: 'main' deve estar contida em 'develop'."
  echo "   Faça merge/rebase de main em develop para manter todo histórico de evolução em develop."
  exit 1
fi

ahead_count=$(git rev-list --right-only --count main...develop)
if [ "$ahead_count" -eq 0 ]; then
  echo "⚠️  develop não possui commits além da main."
  echo "   Isso é aceitável temporariamente, mas o desenvolvimento deve acontecer em develop."
else
  echo "✅ Política ok: main está contida em develop e o histórico de evolução está em develop."
fi

echo "Resumo de divergência (main...develop):"
git rev-list --left-right --count main...develop
