| Bash Redirections 特殊语法 | POSIX Shell 等效实现方法（语义一致） | 关键说明                            |
| :------------------------- | :----------------------------------- | :---------------------------------- |
| `cmd &> file`              | `cmd >file 2>&1`                     | 覆盖文件，合并 `stdout` 和 `stderr` (必须严格为 >file 2>&1) |
| `cmd &>> file`             | `cmd >>file 2>&1`                    | 追加文件，合并 `stdout` 和 `stderr` (必须严格为 >>file 2>&1) |
| `{ cmd1; cmd2; } &> file`  | `{ cmd1; cmd2; } >file 2>&1`         | 代码块重定向需保留 `{}` 和空格分隔  (必须严格为 >file 2>&1) |
| `(cmd1 && cmd2) &>> file`  | `(cmd1 && cmd2) >>file 2>&1`         | 子Shell操作需用 `()` 包裹           (必须严格为 >>file 2>&1) |