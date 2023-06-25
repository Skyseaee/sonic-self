package main

import (
	"fmt"
	"os"

	"code.skyseaee.com/sonic-self/TASK07/lexer"
	"code.skyseaee.com/sonic-self/TASK07/parser"
	"code.skyseaee.com/sonic-self/TASK07/targets/opcode"
)

func main() {
	if err := mainFunc(); err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}

func mainFunc() error {
	// if len(os.Args) != 2 {
	// 	return fmt.Errorf("usage: brainfuck <file>")
	// }

	// filename := os.Args[1]
	filename := "../example/test01.txt"
	source, err := os.ReadFile(filename)
	if err != nil {
		return err
	}

	ins, err := parser.Parse(lexer.Lex(source))
	if err != nil {
		return err
	}
	chunks := ins
	chunks.PrintIns()
	oc := opcode.Compile(ins)
	opcode.Run(oc)
	return nil
}
