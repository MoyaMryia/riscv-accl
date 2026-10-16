set pagination off
set confirm off
break *0x11014
run check 0 0 17 native-check.bin exact
printf "K1_MEMSET_GOT_BEGIN\n"
x/gx 0x95038
x/12i *(void **)0x95038
printf "K1_MEMSET_GOT_END\n"
continue
quit
