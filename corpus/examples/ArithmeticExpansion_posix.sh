i=5
i=$((i + 1))
echo "$i" 

result=$((2 * 2 * 2))

value=$((1 * 2 * 2 * 2)) 

a=4
b=5 
min=$((a < b ? a : b))
max=$((a > b ? a : b)) 

count=0
count=$((count + 10))
echo $count

if [ "$a" -ne 0 ] && [ "$b" -ne 0 ]; then
  echo "Both non-zero"
fi

