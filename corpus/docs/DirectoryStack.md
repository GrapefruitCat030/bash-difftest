| Bash 目录栈语法示例  | POSIX Shell 等效实现方法（手动模拟）       | 关键说明               |
| :------------------- | :----------------------------------------- | :--------------------- |
| `pushd /path/to/dir` | `dirstack_push /path/to/dir`（自定义函数） | 需手动维护目录栈变量   |
| `popd`               | `dirstack_pop`（自定义函数）               | 从栈中移除目录并切换   |
| `dirs`               | `printf "%s\n" "$DIRSTACK"`                | 手动打印目录栈内容     |
| `cd ~+3`             | `cd "$(dirstack_get 3)"`（自定义函数）     | 通过索引访问栈中目录   |
| `echo ~-2`           | `echo "$(dirstack_get -2)"`                | 负数索引需反向计算位置 |

### 实现步骤（需在脚本中定义以下函数和变量）：

#### 1. **初始化目录栈变量**

```
DIRSTACK="$PWD"
```

#### 2. **自定义 `dirstack_push` 函数**

```
dirstack_push() {
  target_dir="$1"
  cd "$target_dir" || return 1
  DIRSTACK="$PWD:${DIRSTACK}" 
}
```

#### 3. **自定义 `dirstack_pop` 函数**

```
dirstack_pop() {
  top_dir="${DIRSTACK%%:*}"
  remaining_stack="${DIRSTACK#*:}"
  if [ "$remaining_stack" = "$DIRSTACK" ]; then
    echo "Error: Directory stack empty." >&2
    return 1
  fi
  cd "$top_dir" || return 1
  DIRSTACK="$remaining_stack"
}
```

#### 4. **自定义 `dirstack_get` 函数（索引访问）**

```
dirstack_get() {
  index=$1
  echo "$DIRSTACK" | tr ':' '\n' > dirstack.$$
  if [ "$index" -lt 0 ]; then
    total=$(wc -l < /tmp/dirstack.$$)
    index=$((total + index + 1)) 
  fi
  awk "NR == $index" dirstack.$$
  rm dirstack.$$
}
```