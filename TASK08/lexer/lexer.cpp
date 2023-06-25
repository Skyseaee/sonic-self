#pragma once
#include <iostream>
#include <vector>
#include "../token/token.cpp"
using namespace std;

static const int eof = -1;

class Lexer {
public:
    vector<char> data;
    int offset;
    char curr;
    Position pos;
    vector<Token> tokens;

    Lexer(vector<char> data): pos(0, 0) {
        offset = 0;
        curr = '.';
        this -> data = data;
    }

    char peek() {
        if(offset >= data.size()) {
            return eof;
        }

        return data[offset];
    }

    void next() {
        char curr = this->peek();
        if(curr == eof) {
            return;
        }

        offset++;
        if(curr == '\n') {
            pos.NextLine();
        } else {
            pos.column++;
        }
    }

    void emit(int token) {
        Token tok = Token(token, 1, 1);
        tokens.emplace_back(tok);
    }

    void program() {
        while(true){
            int tok;
            switch (peek())
            {
            case eof:
                tok = Eof;
            case '+':
                tok = Plus;
            case '-':
                tok = Minus;
            case '<':
                tok = LeftArrow;
            case '>':
                tok = RightArrow;
            case ',':
                tok = Comma;
            case '.':
                tok = Period;
            case '[':
                tok = LeftBracket;
            case ']':
                tok = RightBracket;
            default:
                next();
                continue;
            }
            emit(tok);
            next();

            if(tok == Eof) {
                return;
            }
        }
    }
};

