# Bash Basic Shell Features

> 针对Bash Reference Manual 的文档，下面给出在Bash Basic Shell Features之上对POSIX标准进行了扩展的语法特性。

```
Bash Basic Shell Features
  3.1 Shell Syntax
    3.1.1 Shell Operation
    3.1.2 Quoting
      3.1.2.1 Escape Character
      3.1.2.2 Single Quotes
      3.1.2.3 Double Quotes
      3.1.2.4 ANSI-C Quoting
      3.1.2.5 Locale-Specific Translation
    3.1.3 Comments
  3.2 Shell Commands
    3.2.1 Reserved Words
    3.2.2 Simple Commands
    3.2.3 Pipelines
    3.2.4 Lists of Commands
    3.2.5 Compound Commands
      3.2.5.1 Looping Constructs
      3.2.5.2 Conditional Constructs
      3.2.5.3 Grouping Commands
    3.2.6 Coprocesses
    3.2.7 GNU Parallel
  3.3 Shell Functions
  3.4 Shell Parameters
    3.4.1 Positional Parameters
    3.4.2 Special Parameters
  3.5 Shell Expansions
    3.5.1 Brace Expansion
    3.5.2 Tilde Expansion
    3.5.3 Shell Parameter Expansion
    3.5.4 Command Substitution
    3.5.5 Arithmetic Expansion
    3.5.6 Process Substitution
    3.5.7 Word Splitting
    3.5.8 Filename Expansion
      3.5.8.1 Pattern Matching
    3.5.9 Quote Removal
  3.6 Redirections
    3.6.1 Redirecting Input
    3.6.2 Redirecting Output
    3.6.3 Appending Redirected Output
    3.6.4 Redirecting Standard Output and Standard Error
    3.6.5 Appending Standard Output and Standard Error
    3.6.6 Here Documents
    3.6.7 Here Strings
    3.6.8 Duplicating File Descriptors
    3.6.9 Moving File Descriptors
    3.6.10 Opening File Descriptors for Reading and Writing
  3.7 Executing Commands
    3.7.1 Simple Command Expansion
    3.7.2 Command Search and Execution
    3.7.3 Command Execution Environment
    3.7.4 Environment
    3.7.5 Exit Status
    3.7.6 Signals
  3.8 Shell Scripts
```



## 3.1 Shell Syntax

- **3.1.2.4 ANSI-C Quoting**：`$'string'`语法允许使用C语言风格的转义序列
- **3.1.2.5 Locale-Specific Translation**：`$"string"`语法用于本地化支持
- **3.1.3 注释**：Bash支持以`#`开头的行内注释

## 3.2 Shell Commands

- **3.2.1 保留字**：Bash有更多保留字，如`select`、`time`、`[[ ]]`、`(( ))`等非POSIX标准
- **3.2.3 管道**：Bash支持`|&`作为`2>&1 |`的简写形式
- **3.2.5 Compound Commands**：
  - `select`语句完全是Bash扩展
  - `(( ))`算术条件结构
  - `[[ ]]`扩展测试命令（比标准的`[ ]`或`test`更强大）
  - C风格的for循环：`for ((expr1; expr2; expr3))`
- **3.2.6 Coprocesses**：`coproc`命令及其语法完全是Bash扩展
- **3.2.7 GNU Parallel**：Bash对GNU Parallel的集成支持

## 3.3 Shell Functions

- Bash支持两种函数声明语法：POSIX标准的`name() {}`和Bash扩展的`function name {}`
- local关键字：用于定义局部变量，限制变量作用域在函数内部。POSIX不支持local，只能使用全局变量。(但Ubuntu20.04自带的dash支持。)

## 3.4 Shell Parameters

- **3.4.2 Special Parameters**：Bash对某些特殊参数有扩展行为，如
  - `EPOCHSECONDS`/`EPOCHREALTIME` 获取秒/微秒级时间戳
  - 这些是Bash特有的特殊变量，POSIX标准下需使用`date +%s`命令

## 3.5 Shell Expansions

- **3.5.1 Brace Expansion**：大括号扩展，`{a,b,c}`和`{1..10}`等模式是Bash扩展

  - 基本字符串扩展：{a,b,c}
  - 数字序列扩展：{1..10}
  - 字符序列扩展：{a..z}
  - 嵌套扩展
  - 步长扩展：{start..end..step}

- **3.5.3 Shell参数扩展**

  ：扩展了多种参数处理形式：

  - `${parameter:offset:length}` - 子字符串提取
  - `${var/pattern/replacement} ` - 模式替换
  - `${var^}`, `${var^^}` - 大小写转换
  - `${var@operator}` - 参数变换操作符
  - `${!var}` 间接变量引用（动态变量名解析）

- **3.5.5 算术扩展**：Bash支持更多的运算符和C风格的算术表达式

- **3.5.6 进程替换**：`<(command)`和`>(command)`语法

- **3.5.8 文件名扩展**：

  - 扩展通配符模式，`shopt -s extglob`
  - `**`递归目录通配符（开启`globstar`选项时）
  - 大小写不敏感匹配（`nocaseglob`选项）

## 3.6 Redirections

- **3.6.4/3.6.5/3.6.10**：`&>`作为`>file 2>&1`的简写，`&>>`作为`>>file 2>&1`的简写
- **3.6.7 Here Strings**：`<<<`重定向操作符
- **3.6.10 Opening File Descriptors for Reading and Writing**：打开用于读写的文件描述符，`&>`和`>>`等高级重定向

## 3.7 Executing Commands

- **3.7.1/3.7.2**：Bash提供了更多的内建命令
- **3.7.3 命令执行环境**：Bash提供更丰富的环境控制
- **3.7.4 环境**：支持额外的环境变量和环境设置
- **3.7.5 退出状态**：Bash特有的`pipefail`选项，用于检测管道中的失败
- **3.7.6 信号**：
  - 虽然基本信号处理是标准的，但Bash提供了更多灵活性

## 3.8 Shell Scripts

- Bash特有的`set`选项，如`-o pipefail`、`-o errexit`的扩展行为
- shopt命令用于设置shell选项
- 调试特性：`trap DEBUG`、`caller`等命令
- Bash支持更多的内置调试工具和选项



