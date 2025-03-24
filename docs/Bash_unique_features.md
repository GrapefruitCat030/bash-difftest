# Bash Features

```
Bash Features
  6.1 Invoking Bash
  6.2 Bash Startup Files
  6.3 Interactive Shells
    6.3.1 What is an Interactive Shell?
    6.3.2 Is this Shell Interactive?
    6.3.3 Interactive Shell Behavior
  6.4 Bash Conditional Expressions
  6.5 Shell Arithmetic
  6.6 Aliases
  6.7 Arrays
  6.8 The Directory Stack
    6.8.1 Directory Stack Builtins
  6.9 Controlling the Prompt
  6.10 The Restricted Shell
  6.11 Bash POSIX Mode
  6.12 Shell Compatibility Mode
```

## 6.4 Bash Conditional Expressions

> 对应前面 Compound Commands 部分的拓展，双括号条件表达式

- `[[ ]]`双括号条件测试结构
- 扩展的字符串比较操作符（如`=~`用于正则表达式匹配）
- 文件测试操作符扩展（如`-v`变量存在测试）

## 6.5 Shell Arithmetic

> 同样对应前面 Compound Commands 部分的拓展，算术表达式，但不止在条件表达式中用到

- `(( ))`算术求值结构
- 扩展的运算符（如`**`、`++`、`--`等C风格操作符）
- 位操作和逻辑操作

## 6.6 Aliases

- 别名扩展在某些方面超出POSIX标准

## 6.7 Arrays

- 索引数组支持（POSIX不支持）
- 关联数组支持（即哈希表键值对）
- 复杂的数组操作（切片、连接等）
- 数组操作：
  - 切片：${array[@]:start:length}。
  - 连接：${array[@]}。
  - 获取数组长度：${#array[@]}。

## 6.8 The Directory Stack

- 目录栈
- `pushd`、`popd`、`dirs`命令
- 波浪号扩展：支持~+n和~-n访问目录栈中的目录。