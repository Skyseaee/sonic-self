#ifndef __ABC_H__
#define __ABC_H__
//以上是为了防止头文件被多次包含，可以省略，最好有，名字任意，保证唯一即可
typedef struct Position {
    /* data */
    int line;
    int column;
}POS;

typedef struct Token {
    /* data */
    int type;
    Position pos;
}token;


int FindNum(char *p);

void NextLine(Position* pos);


#endif