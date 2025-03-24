echo "Hello" >output.log 2>&1

date >>log.txt 2>&1

{ ls; grep "pattern" file; } >results.txt 2>&1

(find /tmp -type f && wc -l) >>count.log 2>&1