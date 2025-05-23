| Bash Arithmetic Expansion 特性示例       | POSIX Shell 等效实现方法                        | 关键说明                          |
| :--------------------------------------- | :---------------------------------------------- | :-------------------------------- |
| `(( i++ ))` 或 `$(( i++ ))`              | `i=$((i + 1))`                                  | 自增/自减需分解为独立操作         |
| `(( a = 2 ** 3 ))`或 `$(( a = 2 ** 3 ))` | `a=$((2 * 2 * 2))`                              | 幂运算需手动展开或依赖 `bc` 命令  |
| `(( b = 1 << 3 ))`或 `$(( b = 1 << 3 ))` | `b=$((1 * 2 * 2 * 2))`                          | 位运算需转换为等效数学计算        |
| `(( x = (a > b) ? a : b ))`              | `x=$((a > b ? a : b))`                          | 三元运算符在 POSIX 算术扩展中可用 |
| `(( var += 5 ))`或 `$(( var += 5 ))`     | `var=$((var + 5))`                              | 复合赋值需展开为完整表达式        |
| `if (( a && b )); then ...`              | `if [ "$a" -ne 0 ] && [ "$b" -ne 0 ]; then ...` | 逻辑运算需转换为条件测试          |
| `printf "%d" $((0x10))`                  | `printf "%d" $((16#10))`                        | 进制字面量需用 【基数#值】 格式   |

