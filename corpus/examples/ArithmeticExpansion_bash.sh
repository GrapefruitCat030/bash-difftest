i=5
((i++))
echo $i

((result = 2 ** 3))

echo $(( value = 1 << 3 ))

a=4
b=5
(( min = (a < b) ? a : b ))
(( max = (a > b) ? a : b ))

count=0
(( count += 10 ))
echo $count

if (( a && b )); then
  echo "Both non-zero"
fi
