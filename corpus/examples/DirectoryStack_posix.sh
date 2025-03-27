dirstack_push /tmp
dirstack_push /usr
echo "$DIRSTACK" 

dirstack_pop
pwd 

cd "$(dirstack_get 2)"

echo "$(dirstack_get -1)"