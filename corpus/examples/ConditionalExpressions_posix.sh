a="hello"
b="hello"
if [ "$a" = "$b" ]; then
    echo "Match 1"
fi

a="apple"
if [ "$a" = a* ]; then
    echo "Match 2"
fi

a="hello"
b="world"
if [ "$a" != "$b" ]; then
    echo "Match 3"
fi

a="12345"
if echo "$a" | grep -Eq "^[0-9]+$"; then
    echo "Match 4"
fi

if ! echo "m90&" | grep -Eq "^'6'$"; then
   echo haha
fi

a="apple"
b="banana"
if [ "$a" \< "$b" ]; then
    echo "Match 5"
fi

a="zebra"
b="yellow"
if [ "$a" \> "$b" ]; then
    echo "Match 6"
fi

a=5
b=6
if [ "$a" -eq 5 ] && [ "$b" -eq 6 ]; then
    echo "Match 7"
fi

a=5
b=7
if [ "$a" -eq 5 ] || [ "$b" -eq 6 ]; then
    echo "Match 8"
fi

a=5
if [ ! "$a" -eq 6 ]; then
    echo "Match 9"
fi

a=1
b=2
c=3
if [ "$a" -eq 6 ] && { [ "$b" -eq 2 ] || [ "$c" -eq 3 ]; }; then
    echo "No Match"
else
    echo "Match 9.5"
fi

myvar="exists"
if [ -n "${myvar+x}" ]; then
    echo "Match 10"
fi

echo "test" > testfile
file="testfile"
if [ -r "$file" ] && [ -s "$file" ]; then
    echo "Match 11"
fi
rm testfile

var="something"
if [ -n "$var" ]; then
    echo "Match 12"
fi

var="something"
if [ -n "$var" ] && [ "$var" != "foo" ]; then
    echo "Match 13"
fi

count=5
if [ "$count" -gt 0 ]; then
    echo "Match 14"
fi

var="test"
if [ -n "$var" ]; then
    echo "Match 15"
fi

emptyvar=""
var_with_spaces="hello world"
if [ "$emptyvar" = "" ]; then
    echo "Match 16"
fi
if [ "$var_with_spaces" = "hello world" ]; then
    echo "Match 17"
fi