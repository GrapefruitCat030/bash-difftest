#!/bin/bash
arr1=(1 "2" 3)
diff <(echo ${arr1[1]}) <(echo "2") | tee output.txt

