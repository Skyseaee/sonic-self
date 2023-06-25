#pragma once
#include <iostream>
#include <string>
#include <vector>
#include "../opcode/opcode.cpp"
using namespace std;

class instruction {
public:
    virtual string Instruction();
    virtual int MemOffset();
    virtual bool Loop() {
        return false;
    };
    virtual void OptiPush(vector<instruction>& ins) {
        return;
    };
    virtual void SubPush_val(vector<instruction>& ins, instruction prev) {
        return;
    };
    virtual void SubPush_set(vector<instruction>& ins) {
        return;
    };
    virtual int GetX() {
        return -1;
    };
    virtual int GetOffset() {
        return -1;
    };
    virtual vector<instruction> Loops(vector<instruction> ins, int start) {
        return vector<instruction>();
    };
    virtual void Append(vector<int>& dst, vector<int>& stack);
};

class Set: public instruction {
public:
    char X;
    int Offset;

    Set(char x, int off) {
        this->X = x;
        this->Offset = off;
    }

    string Instruction() {
        return "Set " + X + string(" at ") + to_string(Offset);
    }

    int MemOffset() {
        return Offset;
    }

    void Append(vector<int>& dst, vector<int>& stack) {
        dst.emplace_back(SetValue);
        dst.emplace_back(Offset);
        dst.emplace_back(X);
    }

    bool Loop() {
        return X == 0;
    }

    void SubPush_val(vector<instruction> ins, instruction prev) {
        ins.pop_back();
        ins.emplace_back(Set(prev.GetX() + X, Offset));
    }

    void SubPush_set(vector<instruction> ins) {
        ins.pop_back();
    }
};

class Value: public instruction {
public:
    char X;
    int Offset;

    Value(char x, int off) {
        X = x;
        Offset = off;
    }

    string Instruction() {
        return "Change Value at " + Offset + string(" by ") + X;
    }

    int MemOffset() {
        return Offset;
    }

    void Append(vector<int>& dst, vector<int>& stack) {
        dst.emplace_back(ChangeValue);
        dst.emplace_back(Offset);
        dst.emplace_back(X);
    }

    void SubPush_val(vector<instruction>& ins, instruction prev) {
        ins.pop_back();
        int t = prev.GetX() + X;
        if(t != 0) {
            ins.emplace_back(Value(t, Offset));
        }
    }

    void SubPush_set(vector<instruction>& ins) {
        ins.pop_back();
    }

    void OptiPush(vector<instruction>& ins) {
        if(X == 0) {
            return;
        }

        instruction prev = ins[ins.size()-1];
        prev.SubPush_val(ins, prev);
    }

    int GetX() {
        return X;
    }

    int GetOffset() {
        return Offset;
    }

    vector<instruction> Loops(vector<instruction> ins, int start) {
        vector<instruction> res;
        res.emplace_back(Set(0, start + Offset));
        return res;
    }
};

class Input: public instruction {
public:
    int Offset;

    Input(int off) {
        Offset = off;
    }

    string Instruction() {
        return "Input Byte at " + Offset;
    }

    int MemOffset() {
        return Offset;
    }

    void Append(vector<int>& dst, vector<int>& stack) {
        dst.emplace_back(InputByte);
        dst.emplace_back(Offset);
    }

    void SubPush_set(vector<instruction>& ins) {
        ins.pop_back();
    }

    void OptiPush(vector<instruction>& ins) {
        instruction prev = ins[ins.size()-1];
        prev.SubPush_set(ins);
    }
};

class Output: public instruction {
public:
    int Offset;

    Output(int off) {
        Offset = off;
    }

    string Instruction() {
        return "Output Byte at " + Offset;
    }

    int MemOffset() {
        return Offset;
    }

    void Append(vector<int>& dst, vector<int>& stack) {
        dst.emplace_back(OutputByte);
        dst.emplace_back(Offset);
    }
};

class StartLoop: public instruction {
public:
    int Offset;

    StartLoop(int off) {
        Offset = off;
    }

    string Instruction() {
        return "Start Loop at " + Offset;
    }

    int MemOffset() {
        return Offset;
    }

    void Append(vector<int>& dst, vector<int>& stack) {
        dst.emplace_back(JumpIfZero);
        dst.emplace_back(Offset);
        dst.emplace_back(0);

        stack.emplace_back(dst.size());
    }
};

class EndLoop: public instruction {
public:
    int Offset;
    
    EndLoop(int off) {
        Offset = off;
    }

    string Instruction() {
        return "End Loop at " + Offset;
    }

    int MemOffset() {
        return Offset;
    }

    void Append(vector<int>& dst, vector<int>& stack) {
        if(stack.size() == 0) {
            throw "opcode, compile: unexpected Endloop instruction.";
        }
        
        dst.emplace_back(JumpIfNotZero);
        dst.emplace_back(Offset);
        dst.emplace_back(0);

        int start = stack[stack.size()-1];
        stack.pop_back();

        int diff = dst.size() - start;
        dst[dst.size()-1] = diff;
        dst[start - 1] = diff;
    }

    bool Loop() {
        return true;
    }
};

class Chunk {
public:
    vector<instruction> ins;

    Chunk(vector<instruction> ins) {
        this->ins = ins;
    }

    int Len() {
        return ins.size();
    }

    instruction get_ins_by_index(int i) {
        return ins[i];
    }

    string GetString() {
        string res;
        int len = ins.size();
        for(int i=0; i<len; i++) {
            res += "    " + i + get_ins_by_index(i).Instruction() + "\n";
        }

        return res;
    }

    void PrintIns() {
        for(int i=0; i<ins.size(); i++) {
            cout<<i<<" : "<<ins[i].Instruction()<<endl;
        }
    }
};


class ChunkBuilder {
public:
    vector<instruction> ins;
    vector<int> loopStack;
    bool finalized;
    int offset;

    bool isFinalized() {
        return finalized;
    }

    bool canFinalized() {
        return loopStack.size() == 0;
    }

    Chunk* finalize() {
        if(!canFinalized()) {
		    throw "chunk build: can't finalize chunk because of unclosed loops";
	    }
        finalized = true;
        Chunk ck = Chunk(ins);
        return &ck;
    }

    bool isRedundantLoop(int pos, int offset) {
        instruction ins = this->ins[pos-1];

        if(pos == 0) {
            return true;
        }

        if(ins.MemOffset()!=offset) {
            return false;
        }

        return ins.Loop();
    }

    void assertNotFinalized() {
        if(this->finalized) {
            throw "chunk builder: chunk has already been finalized.";
        }
    }

    instruction last() {
        if(ins.size() == 0) {
            throw "chunk builder: nothing to pop.";
        }

        return ins[ins.size()-1];
    }

    void pop() {
        if(ins.size() == 0) {
            return;
        }

        ins.pop_back();
    }

    void optimizedPush(instruction i) {
        try {
            instruction in = last();
            if(in.MemOffset()  == i.MemOffset()) {
                i.OptiPush(ins);
            }
        } catch(const std::exception& e) {
            
        }
        ins.emplace_back(i);
    }

    vector<instruction> optimizeLoopBody(vector<instruction> i, int start, int end) {
        vector<instruction> res;
        if(end == 0) {
            if(i.size() == 1) {
                i[0].Loops(ins, start);
            }
        }
        return res;
    }

    void changeValue(char by) {
        assertNotFinalized();
        optimizedPush(Value(by, offset));
    }

    void changePointer(int change) {
        assertNotFinalized();
        offset += change;
    }

    void inputByte() {
        assertNotFinalized();
        optimizedPush(Input(offset));
    }

    void outputByte() {
        assertNotFinalized();
        ins.emplace_back(Output(offset));
    }

    void startLoop() {
        assertNotFinalized();

        loopStack.emplace_back(ins.size());
        ins.emplace_back(StartLoop(offset));
    }

    void endLoop() {
        assertNotFinalized();

        if(loopStack.size() == 0) {
            throw "chunk builder: unexpected EndLoop";
        }

        int last = loopStack.size() - 1;
        int start = loopStack[last];
        loopStack.pop_back();

        // TODO
        vector<instruction>::const_iterator Begin = ins.begin();
        vector<instruction>::const_iterator First = ins.begin() + start + 1;
        vector<instruction>::const_iterator Half = ins.begin() + start - 1;
        vector<instruction>::const_iterator End = ins.end();
        vector<instruction> body(First, End);
        int off = ins[start].MemOffset();

        if(isRedundantLoop(start, offset)) {
            ins = vector<instruction>(Begin, Half);
            offset = off;
            return;
        }

        vector<instruction> temp = optimizeLoopBody(body, off, offset);
        if(temp.size() != 0) {
            ins = vector<instruction>(Begin, Half);
            for(int i=0; i<temp.size(); i++) {
                ins.emplace_back(temp[i]);
            }
            offset = off;
            return;
        }

        // optimization failed
        ins.emplace_back(EndLoop(offset));
        offset = 0;
    }
};