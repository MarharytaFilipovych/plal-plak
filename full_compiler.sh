#!/bin/bash

mkdir -p llm
mkdir -p obj
mkdir -p exe

for i in {1..6} {11..16} {22..31}; do
    echo "Testing test_$i..."
    python3 -m compiler.compiler ./test_cases/test_$i.txt ./llm/test_$i.ll
    if [ $? -ne 0 ]; then
        echo "ERROR: test_$i should have compiled successfully!"
        exit 1
    fi
    llc -filetype=obj -relocation-model=pic ./llm/test_$i.ll -o ./obj/test_$i.o
    clang -fPIE ./obj/test_$i.o -o ./exe/test_$i
    ./exe/test_$i
    echo ""
done

for i in {7..10} {17..21} {32..36}; do
    echo "Testing test_$i (should fail)..."
    python3 -m compiler.compiler ./test_cases/test_$i.txt ./llm/test_$i.ll
    if [ $? -eq 0 ]; then
        echo "ERROR: test_$i should have failed compilation!"
        exit 1
    else
        echo "test_$i failed as expected"
    fi
    echo ""
done

echo "All tests passed!"