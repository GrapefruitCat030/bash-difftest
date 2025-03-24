|         Bash 数组语法         |          POSIX Shell 实现方法（变量名=数组名+序号）          |
| :---------------------------: | :----------------------------------------------------------: |
|      `arr=("a" "b" "c")`      | 手动拆分： `arr_0="a" arr_1="b" arr_2="c"` 需额外维护长度变量： `arr__len=3` |
|       `echo ${arr[1]}`        | `echo "$arr_1"` （注意：Bash索引从0开始，POSIX模拟时索引从1开始，因此Bash的`[1]`对应`arr_1`） |
|         `arr[2]="d"`          |              `arr_2="d"` （需要先确保长度足够）              |
|       `echo ${#arr[@]}`       |          `echo "$arr__len"` （需自行维护长度变量）           |
| `for i in "${arr[@]}"; do...` | 展开为：`for i in ""$arr_0" "$arr_1" "$arr_2" "$arr_3""; do...`  |
|         `"${arr[@]}"`         | 展开为： `"$arr_0" "$arr_1" "$arr_2"`  |
|        `"${!arr[@]}"`         |               生成索引序列： `seq 1 $arr__len`               |
|       `"${arr[@]:1:2}"`       | 手动选取元素： `i=2; end=3; while [ $i -le $end ]; do eval "echo \"\$arr_$i\""; i=$((i+1)); done` |
|         `arr+=("d")`          | 追加元素： `arr__len=$((arr__len + 1))` `eval "arr_${arr__len}=\"d\""` |
|        `unset arr[1]`         | 无法直接删除中间元素，需重建数组： `tmp_len=0` `for i in $(seq 1 $arr__len); do if [ $i -ne 2 ]; then tmp_len=$((tmp_len+1)); eval "tmp_$tmp_len=\$arr_$i"; fi; done` `arr__len=$tmp_len; arr_0="$tmp_1" arr_1="$tmp_2"...` |

