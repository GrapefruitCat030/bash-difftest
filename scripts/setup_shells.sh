#!/bin/bash
# 下载并编译bash和dash shell，添加gcov参数

set -e  # 遇到错误立即退出

# 获取项目根目录
PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
SHELL_DIR="$PROJECT_ROOT/shell"
BASH_VERSION="5.2"
DASH_VERSION="0.5.12"

# 创建shell目录
mkdir -p "$SHELL_DIR"
cd "$SHELL_DIR"

echo "=== 安装带gcov flag的shell ==="

# 下载并编译bash
if [ ! -d "$SHELL_DIR/bash-$BASH_VERSION" ]; then
  echo "下载 bash-$BASH_VERSION..."
  wget "https://ftp.gnu.org/gnu/bash/bash-$BASH_VERSION.tar.gz"
  tar -xzf "bash-$BASH_VERSION.tar.gz"
  rm "bash-$BASH_VERSION.tar.gz"
  
  echo "编译bash (带gcov支持)..."
  cd "bash-$BASH_VERSION"
  
  # 配置bash，启用gcov覆盖率统计
  ./configure --prefix="$SHELL_DIR" \
    CFLAGS="-g -O0 -fprofile-arcs -ftest-coverage" \
    LDFLAGS="-fprofile-arcs"
  
  make -j$(nproc)
  make install
  cd "$SHELL_DIR"
else
  echo "bash-$BASH_VERSION 已存在，跳过下载和编译。"
fi

# 下载并编译dash (作为POSIX shell)
if [ ! -d "$SHELL_DIR/dash-$DASH_VERSION" ]; then
  echo "下载 dash-$DASH_VERSION..."
  wget "http://gondor.apana.org.au/~herbert/dash/files/dash-$DASH_VERSION.tar.gz"
  tar -xzf "dash-$DASH_VERSION.tar.gz"
  rm "dash-$DASH_VERSION.tar.gz"
  
  echo "编译dash (带gcov支持)..."
  cd "dash-$DASH_VERSION"
  
  # 配置dash，启用gcov覆盖率统计
  ./configure --prefix="$SHELL_DIR" \
    CFLAGS="-g -O0 -fprofile-arcs -ftest-coverage" \
    LDFLAGS="-fprofile-arcs"
  
  make -j$(nproc)
  make install
  cd "$SHELL_DIR"
else
  echo "dash-$DASH_VERSION 已存在，跳过下载和编译。"
fi

# 创建符号链接，处理配置文件中的两种路径
echo "创建shell符号链接..."

# 为项目根目录下的bin创建符号链接
mkdir -p "$PROJECT_ROOT/bin"
ln -sf "$SHELL_DIR/bin/bash" "$PROJECT_ROOT/bin/bash"
ln -sf "$SHELL_DIR/bin/dash" "$PROJECT_ROOT/bin/sh"

echo "Shell安装和符号链接创建完成。"