#!/bin/bash
# 检查配置文件中各个目录是否存在，不存在则创建

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CONFIG_FILE="$PROJECT_ROOT/configs/conf.json"

if [ ! -f "$CONFIG_FILE" ]; then
  echo "error: configure has no found - $CONFIG_FILE"
  exit 1
fi

echo "=============== check config ==============="

DIRECTORIES=(
  "src/prompt/templates"
  "corpus/docs"  
  "corpus/examples"  
  "corpus"
  "seeds"
  "src/mutation_chain/mutators"
  "results/posix_code"
  "results/reports"
  "shell"
  "shell/bin"
)

echo "=============== check directories ==============="
for dir in "${DIRECTORIES[@]}"; do
  if [[ ! -d "$PROJECT_ROOT/$dir" ]]; then
    mkdir -p "$PROJECT_ROOT/$dir"
    echo "Create: $dir"
  else
    echo "Exist: $dir"
  fi
done

echo "=============== check directories done ==============="