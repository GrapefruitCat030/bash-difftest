#!/bin/bash
# 下载gcov相关工具

set -e  # 遇到错误立即退出

echo "=== 安装覆盖率工具 ==="

echo "检查覆盖率工具是否已安装..."
if [ -x "$(command -v lcov)" ]; then
  echo "lcov has already been installed. Skip."
else
  echo "lcov has not been installed. Start installing..."
  apt-get install -y lcov
fi

if [ -x "$(command -v genhtml)" ]; then
  echo "genhtml has already been installed. Skip."
else
  echo "genhtml has not been installed. Start installing..."
  apt-get install -y lcov
fi

echo "=== 安装完成 ==="
