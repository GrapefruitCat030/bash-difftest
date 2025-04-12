arr=("a" "b" "c")
echo ${arr[1]}
arr[2]="d"
echo ${#arr[@]}
echo ${arr[@]}
arr+=("d")

for i in ${arr[@]}; do
    echo $i
done

arr+=(4 $(
   c=3
) 1)