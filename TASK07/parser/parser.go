package parser

import (
	"fmt"

	"code.skyseaee.com/sonic-self/TASK07/instruction"
	"code.skyseaee.com/sonic-self/TASK07/token"
)

func Parse(tokens <-chan token.Token) (*instruction.Chunk, error) {
	p := parser{tokens: tokens}
	return p.program()
}

type parser struct {
	tokens  <-chan token.Token
	current token.Token
}

type SyntaxError struct {
	Token   token.Token
	message error
}

func (e SyntaxError) Error() string {
	return fmt.Sprintf("parser: %s: %v", e.Token.Position, e.message)
}

var (
	ErrNotOpened = fmt.Errorf("unexpected token ']', no open loop.")
	ErrNotClosed = fmt.Errorf("unexpected token EOF, loop not closed.")
)

func (p *parser) next() {
	p.current = <-p.tokens
}

func (p *parser) program() (*instruction.Chunk, error) {
	var c instruction.ChunkBuilder
	var stack []token.Token // loop stack

Parserloop:
	for {
		switch p.next(); p.current.Type {
		case token.Eof:
			break Parserloop
		case token.Plus:
			c.ChangeValue(1)
		case token.Minus:
			c.ChangeValue(-1)
		case token.LeftArrow:
			c.ChangePointer(-1)
		case token.RightArrow:
			c.ChangePointer(1)
		case token.Comma:
			c.InputByte()
		case token.Period:
			c.OutputByte()
		case token.LeftBracket:
			stack = append(stack, p.current)
			c.StartLoop()
		case token.RightBracket:
			if len(stack) == 0 {
				return nil, &SyntaxError{p.current, ErrNotOpened}
			}
			stack = stack[:len(stack)-1]
			c.EndLoop()

		default:
			panic("parser: invalid token from scanner")
		}
	}

	if len(stack) > 0 {
		return nil, &SyntaxError{stack[len(stack)-1], ErrNotClosed}
	}

	return c.Finalized(), nil
}
