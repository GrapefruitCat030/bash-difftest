| Bash 进程替换语法         | POSIX Shell 实现方法（临时文件）                             |
| :------------------------ | :----------------------------------------------------------- |
| `command <(cmd1)`         | 1. 创建临时文件 2. 运行 `cmd1 > tmpfile` 3. 运行 `command tmpfile` 4. 删除临时文件 |
| `command <(cmd1) <(cmd2)` | 1. 创建两个临时文件 2. 运行 `cmd1 > tmp1` 和 `cmd2 > tmp2` 3. 运行 `command tmp1 tmp2` 4. 删除临时文件 |
| `cmd1 > >(cmd2)`          | 转化为管道，cmd1 \| cmd2    |