| Bash 进程替换语法        | Bash 进程替换语法示例                       | POSIX Shell 对应转换实现方法                                 |
| ------------------------ | ------------------------------------------- | ------------------------------------------------------------ |
| 输入进程替换：单个命令   | command <(cmd)                              | 1. `tmp=$(mktemp)` <br> 2. `(cmd) > "$tmp"` <br> 3. `command "$tmp"` <br> 4. `rm -f "$tmp"` |
| 输入进程替换：多命令列表 | command <(cmd1; cmd2; cmd3)                 | 1. `tmp=$(mktemp)` <br> 2. `(cmd1; cmd2; cmd3) > "$tmp"` <br> 3. `command "$tmp"` <br> 4. `rm -f "$tmp"` |
| 多个输入进程替换         | command <(cmd_seq1) <(cmd_seq2) <(cmd_seq3) | 1. `tmp1=$(mktemp); tmp2=$(mktemp)` <br> 2. `(cmd_seq1) > "$tmp1"; (cmd_seq2) > "$tmp2"; (cmd_seq3) > "$tmp3"` <br> 3. `command "$tmp1" "$tmp2" "$tmp3"` <br> 4. `rm -f "$tmp1" "$tmp2" "$tmp3"` |
| 输出进程替换             | cmd1 > >(cmd_sequence)                      | 1. `tmp=$(mktemp)` <br/> 2. `cmd1 > "$tmp"` <br/> 3. `(cmd_sequence) < "$tmp"` <br/> 4. `rm -f "$tmp"` |
| 进程替换后接管道         | cmd1 <(cmd_sequence) \| cmd2                | 1. `tmp=$(mktemp)` <br> 2. `(cmd_sequence) > "$tmp"` <br> 3. `cmd1 "$tmp" | cmd2` <br> 4. `rm -f "$tmp"` |
| 进程替换后接重定向       | cmd1 <(cmd_sequence) > outfile              | 1. `tmp=$(mktemp)` <br> 2. `(cmd_sequence) > "$tmp"` <br> 3. `cmd1 "$tmp" > outfile` <br> 4. `rm -f "$tmp"` |
| 进程替换后接管道和重定向 | cmd1 <(cmd_sequence) \| cmd2 > outfile      | 1. `tmp=$(mktemp)` <br/> 2. `(cmd_sequence) > "$tmp"` <br/> 3. `cmd1 "$tmp" | cmd2 > outfile` <br/> 4. `rm -f "$tmp"` |