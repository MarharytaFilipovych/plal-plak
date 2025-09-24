#!/bin/bash

for i in {1..7}; do
    ./compiler.py ./test_cases/test_$i.txt
done

llc -filetype=obj -relocation-model=pic ./test_cases/test_7.ll -o test_7.o
llc -filetype=obj -relocation-model=pic ./test_cases/test_6.ll -o test_6.o
llc -filetype=obj -relocation-model=pic ./test_cases/test_7.ll -o test_7.o

clang -fPIE test_1.o -o test_1
clang -fPIE test_6.o -o test_6
clang -fPIE test_7.o -o test_7

./test_1
./test_6
./test_7