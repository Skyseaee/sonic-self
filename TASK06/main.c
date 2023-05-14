/*
根据读入的源代码，使用 switch-case 语句实现 Brainfuck 的 8 个指令，包括：+，-，>，<，.，,，[，]。
>：将指针右移。如果指针已经达到数组的末尾，则返回出错。
<：将指针左移。如果指针已经达到数组的开头，则返回出错。
+：将指针所指的内存块的值加1。
-：将指针所指的内存块的值减1。
.：输出指针所指的内存块的值。（ASCII码）
,：等待输入，并将输入的字符存储到指针所指的内存块中。（ASCII码）
[：如果指针所指的内存块的值为0，则跳转到对应的’]‘之后；否则继续执行下一个指令。
]：如果指针所指的内存块的值不为0，则跳转到对应的’['之后；否则继续执行下一个指令。
*/

/*
实现brainf * ck的词法分析以及语法分析器
*/

#include <stdio.h>

int main() {
    char array[30000] = {};
    char input[1000]; // source code
    char *ptr = array;

    printf("please input source written by Brainfuck: \n");
    fgets(input, 1000, stdin);

    for(char *p = input; *p; p++) {
        switch (*p) {
            case '>': ptr++; break;
            case '<': ptr--; break;
            case '+': (*ptr)++; break;
            case '-': (*ptr)--; break;
            case '.': putchar(*ptr); break;
            case ',': *ptr = getchar(); break;
            case '[': {
                char *temp = p;
                while(*ptr) {
                    p++;
                    while(*p) {
                        if (*p == '[') p++;
                        else if (*p == ']') {
                            if (--temp == p) break;
                            else p++;
                        }
                    }
                }
                break;
            }
            case ']': {
                char *temp = p;
                while(*ptr) {
                    p--;
                    while( p >= input) {
                        if (*p == ']') p--;
                        else if (*p == '[') {
                            if (++temp == p) break;
                            else p--;
                        }
                    }
                }
                break;
            }
            default:
                printf("ERR: invaild alphabet: %s", *p);
                return -1;
        }
    }
    return 0;
}