| Bash Variable Assignment 特性           | Bash 特性语法示例                                   | POSIX Shell 等效实现方法                                     | 关键说明       |
| --------------------------------------- | :-------------------------------------------------- | :----------------------------------------------------------- | :------------- |
| 正常情况下，`+=`视为字符串追加          | `str="hello"; str+=" world"`<br />`numstr=5;num+=3` | `str="hello"; str="${str} world"`<br />`numstr=5;numstr=${numstr}3` | 手动拼接字符串 |
| 在declare -i 存在前提下，`+=`为算术赋值 | `declare -i num=5`<br />`....`<br />`num+=3`        | `num=5`<br />`num=$((num + 3))`                              | 手动算术扩展   |

