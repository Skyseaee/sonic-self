#pragma once
#include <iostream>

#include "../instruction/instruction.cpp"
#include "../token/token.cpp"

#include <vector>
using namespace std;

string error_not_opened = "unexpected token ']', no open loop.";
string error_not_closed = "unexpected token EOF, loop not closed.";

class SyntaxError {
    Token tok;
    string errorMsg;

public:
    SyntaxError(int tok_s, int col, int line, string msg): tok(tok_s, col, line) {
        errorMsg = msg;
    }

    string errors() {
        return "parser: " + tok.ParsePos() + ": " + errorMsg;
    }
};

class Parser {
public:
    Token current;
    vector<Token> tokens;
    int index;

    Parser(vector<Token> tokens): current(0, 0, 0) {
        this->tokens = tokens;
        index = -1;
    }

    void next() {
        index++;
        current = tokens[index];
    }

    Chunk* program() {
        ChunkBuilder cb;
        vector<Token> loop_stack;

        while(true) {
            next();
            switch(current.type) {
            case Eof:
                break;
            case Plus:
                cb.changeValue(1);
            case Minus:
                cb.changeValue(-1);
            case LeftArrow:
                cb.changePointer(-1);
            case RightArrow:
                cb.changePointer(1);
            case Comma:
                cb.inputByte();
            case Period:
                cb.outputByte();
            case LeftBracket:
                loop_stack.emplace_back(current);
                cb.startLoop();
            case RightBracket:
                if(loop_stack.size() == 0) {
                    throw SyntaxError(current.type, current.pos.column, current.pos.line, error_not_opened).errors();
                }
                loop_stack.pop_back();
                cb.endLoop();
            default:
                throw "parser: invalid token from scanner";
            }
        }

        if(loop_stack.size() > 0) {
            throw SyntaxError(current.type, current.pos.column, current.pos.line, error_not_closed).errors();
        }

        return cb.finalize();
    }
};

