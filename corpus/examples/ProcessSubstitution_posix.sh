# basic example 1: simple commands
tmp1=$(mktemp)
ls dir1 > "$tmp1"
tmp2=$(mktemp)
ls dir2 > "$tmp2"
diff "$tmp1" "$tmp2"
rm -f "$tmp1" "$tmp2"

# basic example 2: mutiple commands
tmp3=$(mktemp)
(echo "foo1"; 
   cat <<< "foo2" 
) > "$tmp3"
tmp4=$(mktemp)
echo "bar1" > "$tmp4"
diff "$tmp3" "$tmp4"
rm -f "$tmp3" "$tmp4"

# output process substitution
tmp5=$(mktemp)
cat file | sed 's/foo/bar/g' > "$tmp5"
(tee output.txt) < "$tmp5"
rm -f "$tmp5"

# input and output process substitution
tmp6=$(mktemp)
cat <(echo "process substitution") > "$tmp6"
(tee output.txt; echo done) < "$tmp6"
rm -f "$tmp6"

# nested case: only the outermost is processed 
tmp7=$(mktemp)
cat <(echo "D") > "$tmp7"
tmp8=$(mktemp)
echo "E" > "$tmp8"
diff "$tmp7" "$tmp8"
rm -f "$tmp7" "$tmp8"

# with pipeline
tmp9=$(mktemp)
grep "pattern" file1 > "$tmp9"
tmp10=$(mktemp)
grep "pattern" file2 > "$tmp10"
cat "$tmp9" "$tmp10" | sort
rm -f "$tmp9" "$tmp10"

# with redirection
tmp11=$(mktemp)
grep "pattern" file1 > "$tmp11"
tmp12=$(mktemp)
grep "pattern" file2 > "$tmp12"
cat "$tmp11" "$tmp12" > output.txt
rm -f "$tmp11" "$tmp12"

# with pipeline and redirection
tmp13=$(mktemp)
grep "pattern" file1 > "$tmp13"
tmp14=$(mktemp)
grep "pattern" file2 > "$tmp14"
cat "$tmp13" "$tmp14" | sort > output.txt
rm -f "$tmp13" "$tmp14"