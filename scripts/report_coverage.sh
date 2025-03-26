#!/bin/bash
# 生成覆盖率报告

set -e  # 遇到错误立即退出

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHELL_DIR="$PROJECT_ROOT/shell"
BASH_VERSION="5.2"
DASH_VERSION="0.5.12"


echo "=== 生成覆盖率报告 ==="

# 生成bash覆盖率报告
echo "gen [bash] coverage report..."
cd "$SHELL_DIR/bash-$BASH_VERSION"

gcov *.c
lcov --capture --directory . --output-file bash_coverage.info --no-external
genhtml bash_coverage.info --output-directory bash_coverage_report

echo "bash coverage report has been generated. see $SHELL_DIR/bash_coverage_report"

# 生成dash覆盖率报告
echo "gen [dash] coverage report..."
cd "$SHELL_DIR/dash-$DASH_VERSION/src"

gcov *.c
lcov --capture --directory . --output-file dash_coverage.info --no-external
genhtml dash_coverage.info --output-directory dash_coverage_report

echo "dash coverage report has been generated. see $SHELL_DIR/dash_coverage_report"

echo "=== 生成完成 ==="
