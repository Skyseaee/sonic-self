#include <stdio.h>
#include <string.h>

typedef struct Position {
    /* data */
    int line;
    int column;
};


typedef struct Token {
    /* data */
    int type;
    Position pos;
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

int FindNum(char *p) {
    switch (*p) {
    case '+': return Plus;
    case '-': return Minus;
    case '<': return LeftArrow;
    case '>': return RightArrow;
    case ',': return Comma;
    case '.': return Period;
    case '[': return LeftBracket;
    case ']': return RightBracket;
    default:
        return -1;
    }
}

void NextLine(Position* pos) {
    pos->line++;
    pos->column = 1;
}