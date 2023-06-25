# sonic-self
尝试实现sonic项目

> require python = 3.10

the grammar of Pl0:
```shell
program = block "." ;

block = [ "const" ident "=" number {"," ident "=" number} ";"]
        [ "var" ident {"," ident} ";"]
        { "procedure" ident ";" block ";" } statement ;

statement = [ ident ":=" expression | "call" ident 
              | "?" ident | "!" expression 
              | "begin" statement {";" statement } "end" 
              | "if" condition "then" statement 
              | "while" condition "do" statement ];

condition = "odd" expression |
            expression ("="|"#"|"<"|"<="|">"|">=") expression ;

expression = [ "+"|"-"] term { ("+"|"-") term};

term = factor {("*"|"/") factor};

factor = ident | number | "(" expression ")";
```

TASK01: 2023/3/6
新建仓库并初始化readme文件

TASK02: 2023/3/13
针对pl0，实现简单的编译器前端

TASK03: 2023/3/20
初步实现pl0编译器的整个流程

TASK07：2023/05/08
初步实现brainfuck的编译器
Lexer：将输入的brainfuck转变成对应的token
Parser：将token转变成tree