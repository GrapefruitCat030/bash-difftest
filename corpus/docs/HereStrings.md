| Bash Here Strings 语法 | POSIX Shell 实现方法（here documents）                       |
| :-------------------- | :----------------------------------------------------------- |
| `command <<< word`    | 1.使用临时变量存储word 2.在 Here-Document 中引用该变量 `command << EOF \n` `$word \n` `EOF \n` |

