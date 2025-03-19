arr1=("a" "b" "c")

tmp1=$(mktemp)
ls dir1 > "$tmp1"
tmp2=$(mktemp)
ls dir2 > "$tmp2"
diff "$tmp1" "$tmp2"
rm -f "$tmp1" "$tmp2"

arr2=(1 2 3)

tmp3=$(mktemp)
grep "pattern" file1 > "$tmp3"
tmp4=$(mktemp)
grep "pattern" file2 > "$tmp4"
cat "$tmp3" "$tmp4" | sort
rm -f "$tmp3" "$tmp4"

tmp5=$(mktemp)
sed 's/foo/bar/g' file > "$tmp5"
tee output.txt < "$tmp5"
rm -f "$tmp5"