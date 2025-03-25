printf "%s\n" "hello world" | grep "hello"

var_a=999
printf "%s\n" "$var_a" | cat 2>&1 > tmp.txt

printf "%s\n" "$(ls)" | wc -l | sort | uniq 