grep "hello" <<< "hello world"

var_a=999
cat <<< "$var_a" 2>&1 > tmp.txt

wc -l <<< "$(ls)" | sort | uniq