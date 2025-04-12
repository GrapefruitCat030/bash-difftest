str="hello"; str=${str}" world"
echo $str

a=${a}"6t^E!"
a=${a}3
echo $a

# declare b as an integer
b=5
b=$((b + 3))
echo $b

c=5
c=${c}3
echo $c

d=${d}"$(echo "hello")"
echo $d