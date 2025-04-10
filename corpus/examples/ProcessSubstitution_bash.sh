# input process substitution: basic example 1
diff <(ls dir1) <(ls dir2)

# input process substitution: basic example 2
diff <(echo "D"; 
   cat <<< "foo" 
) <(echo "E")

# output process substitution (this wrong)
cat file | sed 's/foo/bar/g' > >(tee output.txt)

# nested case 
diff <(cat <(echo "D")) <(echo "E")

# with pipeline
cat <(grep "pattern" file1) <(grep "pattern" file2) | sort

# with redirection
cat <(grep "pattern" file1) <(grep "pattern" file2) > output.txt

# with pipeline and redirection
cat <(grep "pattern" file1) <(grep "pattern" file2) | sort > output.txt
