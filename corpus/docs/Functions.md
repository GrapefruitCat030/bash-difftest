| Bash Functions 语法特性示例 | POSIX Shell 等效实现方法（dash兼容）                 |
| :------------------------- | :--------------------------------------------------- |
| `function func { ... }`    | `func() { ... }`（删除 `function` 关键字，添加括号, 注意函数体可能存在换行） |
| `function func() { ... }`  | `func() { ... }` （删除 `function` 关键字, 注意函数体可能存在换行）          |