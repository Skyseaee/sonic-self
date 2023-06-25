#pragma once
#include <iostream>
using namespace std;

typedef int Opcode;

const Opcode InputByte = 1;    // [code] [offset]
const Opcode OutputByte = 2;    // [code] [offset]
const Opcode ChangeValue = 3;  // [code] [offset] [amount]
const Opcode SetValue = 4;     // [code] [offset] [amount]
const Opcode JumpIfZero = 5;   // [code] [offset] [jump-offset]
const Opcode JumpIfNotZero = 6; // [code] [offset] [jump-offset]