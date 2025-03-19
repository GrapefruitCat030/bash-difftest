arr1=("a" "b" "c") 
diff <(ls dir1) <(ls dir2)
arr2=(1 2 3)
cat <(grep "pattern" file1) <(grep "pattern" file2) | sort
cat file | sed 's/foo/bar/g' > >(tee output.txt)