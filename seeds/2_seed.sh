arr1=(1 "b" 3)
len=${#arr1[@]}
for i in ${arr1[@]};
do 
	echo ${arr1[1]}
done
arr2=(4 5)
echo ${arr2[0]}