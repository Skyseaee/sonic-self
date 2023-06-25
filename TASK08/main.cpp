#include <iostream>
#include <fstream>
#include <vector>

#include "./lexer/lexer.cpp"
#include "./parser/parser.cpp"
#include "./opcode/compile.cpp"
#include "./opcode/vm.cpp"

using namespace std;

int main() {
    string filename = "./example/test01.txt";
    ifstream fin;
    fin.open(filename, ios::in);
    if(!fin.is_open()) {
        throw "file not found.";
    }

    char buff[30000] = {0};
    int len = 0;
    while(fin >> buff) {len++;}
    fin.close();
    vector<char> data(buff, buff + len);
    Lexer lex = Lexer(data);
    Parser parser = Parser(lex.tokens);
    vector<int> ins = Compile(parser.program());
    Run(ins);

    return 0;
}