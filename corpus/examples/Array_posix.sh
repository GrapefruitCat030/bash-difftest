arr_0="a" arr_1="b" arr_2="c" arr__len=3
echo "$arr_1"
arr_2="d"
echo "$arr__len"
echo "$arr_0" "$arr_1" "$arr_2"
arr_3="d"; arr__len=$((3 + 1))

for i in ""$arr_0" "$arr_1" "$arr_2" "$arr_3""; do
    echo $i
done