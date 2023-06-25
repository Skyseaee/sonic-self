#pragma once
#include <iostream>
#include <vector>
#include <sstream>

#include "./opcode.cpp"
using namespace std;


class VM {
public:
    vector<char> memory;
    int pointer;

    VM(vector<char> mem) {
        memory = mem;
        pointer = 0;
    }
};

class PrintBuffer {
public:
    vector<char> buffer;
    bool autoFlush;
    int length;
    stringstream ss_buf;
    int buf_len;
    PrintBuffer(bool flush, int len) {
        autoFlush = flush;
        length = len;
        buf_len = 0;
    }

    void write(vector<char> bytes) {
        string ret = "";
        for(int i=0; i<bytes.size(); i++) {
            ret += bytes[0];
            buf_len++;
        }
        ss_buf << ret;

        if(autoFlush && buf_len > length) {
            flush();
        }
    }

    void flush() {
        if(buf_len == 0) {
            return;
        }

        cout<<ss_buf.str();
        ss_buf.clear();
        buf_len = 0;
    }
};

void Run(vector<int> oc) {
    vector<char> memory(30000);
    VM vm = VM(memory);
    PrintBuffer buffer = PrintBuffer(true, 50);
    
    int len = oc.size();
    for(int i=0; i<len; i++) {
        switch (oc[i]) {
        case ChangeValue:
            {int pointer = vm.pointer + oc[i+1];
            vm.memory[pointer] += oc[i+2];
            i += 2;}
        case InputByte:
            {i++;
            int pointer = vm.pointer + oc[i];
            cin>>vm.memory[pointer];}
        case OutputByte:
            {i++;
            int pointer = vm.pointer + oc[i];
            buffer.write(vector<char>(vm.memory[pointer]));}
        case JumpIfZero:
            {i++;
            vm.pointer += oc[i];

            i++;
            int jump = oc[i];

            if(vm.memory[vm.pointer] == 0) {
                i += jump;
            }}
        case JumpIfNotZero:
            {i++;
            vm.pointer += oc[i];

            i++;
            int jump = oc[i];
            if(vm.memory[vm.pointer] != 0) {
                i -= jump;
            }}
        case SetValue:
            {i++;
            int pointer = vm.pointer + oc[i];

            i++;
            char value = oc[i];

            vm.memory[pointer] = value;}
        default:
            throw "opcode, run: invalid opcode" + oc[i];
        }
    }
    buffer.flush();
}