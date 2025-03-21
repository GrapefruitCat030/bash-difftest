arr1=(1 "b" 3)
len=${#arr1[@]}
for i in (seq 1 $len);
do 
	echo ${arr1[1]}
done
arr2=(4 5)
echo ${arr2[0]}