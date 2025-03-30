#!/bin/bash
# 主初始化脚本

set -e  # 遇到错误立即退出

echo "===== 初始化 bash-difftest 项目 ====="

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SCRIPTS_DIR="$PROJECT_ROOT/scripts"

# 确保所有脚本有执行权限
chmod +x "$SCRIPTS_DIR"/*.sh
chmod +x "$SCRIPTS_DIR"/*.py

# 1. 检查配置文件和创建必要的目录
echo "================= step 1: 检查配置目录...     ================="
"$SCRIPTS_DIR/check_dir.sh"
echo

# 2. 安装覆盖率工具
echo "================= step 2: 安装覆盖率工具...   ================="
"$SCRIPTS_DIR/setup_coverage.sh"
echo

# 3. Python依赖
echo "================= step 3: 安装Python依赖...   ================="
pip install -r "$PROJECT_ROOT/requirements.txt"
echo

# 4. 下载并编译shell
echo "================= step 4: 下载并编译shell...  ================="
"$SCRIPTS_DIR/setup_shells.sh"
echo

# 5. tree-sitter-bash
echo "================= step 5: tree-sitter-bash...================="
TREE_SITTER_DIR="$PROJECT_ROOT/tree-sitter-bash"
if [ -d "$TREE_SITTER_DIR" ]; then
  echo "tree-sitter-bash has already been cloned. Pulling latest changes!"
  cd "$TREE_SITTER_DIR"
  git pull
  cd "$PROJECT_ROOT"
else
  echo "clone tree-sitter-bash now ..."
  git clone https://github.com/tree-sitter/tree-sitter-bash.git "$TREE_SITTER_DIR"
fi

# 6. seeds generator 配置
echo "================= step 6: seeds generator... ================="
"$SCRIPTS_DIR/setup_seeds_generator.sh"

echo 
echo "===== 初始化完成! ====="