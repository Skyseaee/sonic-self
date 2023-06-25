#pragma once
#include <iostream>
#include <unordered_map>
#include <string>
using namespace std;

class Position {
public:
    int line;
    int column;

    Position(int line, int col) {
        this->line = line;
        this->column = col;
    }

    string String() {
        return line + ":" + column;
    }

    void NextLine() {
        line++;
        column = 1;
    }
};

class Token {
public:
    int type;
    Position pos;

    Token(int type, int line, int col): pos(line, col) {
        this->type = type;
    }

    string String() {
        string tokens[] = {"EOF", "+", "-", "<", ">", ",", ".", "[", "]"};
        return tokens[type];
    }

    string ParsePos() {
        return pos.column + "-" + pos.line;
    }
};

const int Eof = 0;
const int Plus = 1;
const int Minus = 2;
const int LeftArrow = 3;
const int RightArrow = 4;
const int Comma = 5;
const int Period = 6;
const int LeftBracket = 7;
const int RightBracket = 8;

