# basic example 1: simple commands
tmp1=$(mktemp)
ls dir1 > "$tmp1"
tmp2=$(mktemp)
ls dir2 > "$tmp2"
diff "$tmp1" "$tmp2"
rm -f "$tmp1" "$tmp2"

# basic example 2: mutiple commands
tmp3=$(mktemp)
(echo "D"; 
   cat <<< "foo" 
) > "$tmp3"
tmp4=$(mktemp)
echo "E" > "$tmp4"
diff "$tmp3" "$tmp4"
rm -f "$tmp3" "$tmp4"

# output process substitution
cat file | sed 's/foo/bar/g' | tee output.txt

# nested case: only the outermost is processed 
tmp_6=$(mktemp)
cat <(echo "D") > "$tmp_6"
tmp_7=$(mktemp)
echo "E" > "$tmp7"
diff "$tmp6" "$tmp_7"
rm -f "$tmp_6" "$tmp_7"

# with pipeline
tmp7=$(mktemp)
grep "pattern" file1 > "$tmp7"
tmp8=$(mktemp)
grep "pattern" file2 > "$tmp8"
cat "$tmp7" "$tmp8" | sort
rm -f "$tmp7" "$tmp8"

# with redirection
tmp9=$(mktemp)
grep "pattern" file1 > "$tmp9"
tmp10=$(mktemp)
grep "pattern" file2 > "$tmp10"
cat "$tmp9" "$tmp10" > output.txt
rm -f "$tmp9" "$tmp10"

# with pipeline and redirection
tmp11=$(mktemp)
grep "pattern" file1 > "$tmp11"
tmp12=$(mktemp)
grep "pattern" file2 > "$tmp12"
cat "$tmp11" "$tmp12" | sort > output.txt
rm -f "$tmp11" "$tmp12"