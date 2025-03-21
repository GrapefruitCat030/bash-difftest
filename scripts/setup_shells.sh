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

if [ ! -d "$SHELL_DIR/bash-$BASH_VERSION" ]; then
  echo "downloading sources code: bash-$BASH_VERSION..."
  wget "https://ftp.gnu.org/gnu/bash/bash-$BASH_VERSION.tar.gz"
  tar -xvzf "bash-$BASH_VERSION.tar.gz"
  rm "bash-$BASH_VERSION.tar.gz"

  echo "config and compile [bash]"
  cd "bash-$BASH_VERSION"
  
  # 配置bash编译，启用gcov
  CFLAGS="-fprofile-arcs -ftest-coverage -O0 -g" LDFLAGS="-lgcov" ./configure --prefix="$SHELL_DIR/bash-$BASH_VERSION" 
  
  make -j$(nproc) # cpu core for parallel make
  cd "$SHELL_DIR"
else
  echo "bash-$BASH_VERSION has already been downloaded and compiled. Skip."
fi

# 下载并编译dash (作为POSIX shell)
if [ ! -d "$SHELL_DIR/dash-$DASH_VERSION" ]; then
  echo "downloading sources code: dash-$DASH_VERSION..."
  wget "http://gondor.apana.org.au/~herbert/dash/files/dash-$DASH_VERSION.tar.gz"
  tar -xzf "dash-$DASH_VERSION.tar.gz"
  rm "dash-$DASH_VERSION.tar.gz"
  
  echo "config and compile [dash]"
  cd "dash-$DASH_VERSION"
  
  # 配置dash，启用gcov
  CFLAGS="-fprofile-arcs -ftest-coverage -O0 -g" LDFLAGS="-lgcov" ./configure --prefix="$SHELL_DIR/dash-$DASH_VERSION" 
  
  make -j$(nproc)
  cd "$SHELL_DIR"
else
  echo "dash-$DASH_VERSION has already been downloaded and compiled. Skip."
fi

echo "=== 安装完成 ==="