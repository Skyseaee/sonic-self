#pragma once
#include <iostream>
#include <vector>
#include "../instruction/instruction.cpp"
using namespace std;

vector<int> Compile(Chunk* c) {
    vector<int> dst;
    vector<int> stack;

    int len = c->Len();
    for(int i=0; i<len; i++) {
        instruction is = c->ins[i];
        is.Append(dst, stack);
    }

    if(stack.size() > 0) {
        throw "opcode, compile: unexpected end of chunk, unpaired StartLoop instruction";
    }

    return dst;
}