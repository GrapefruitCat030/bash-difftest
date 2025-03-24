echo "Hello" &> output.log

date &>> log.txt

{ ls; grep "pattern" file; } &> results.txt

(find /tmp -type f && wc -l) &>> count.log