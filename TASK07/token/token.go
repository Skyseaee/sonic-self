package token

import "fmt"

type Position struct {
	Line   int
	Column int
}

type Token struct {
	Type
	Position
}

type Type int

const (
	Eof Type = iota

	Plus  // +
	Minus // -

	LeftArrow  // <
	RightArrow // >

	Comma  // ,
	Period // .

	LeftBracket  // [
	RightBracket // ]
)

var tokens = [...]string{
	Eof:          "EOF",
	Plus:         "+",
	Minus:        "-",
	LeftArrow:    "<",
	RightArrow:   ">",
	Comma:        ",",
	Period:       ".",
	LeftBracket:  "[",
	RightBracket: "]",
}

func (t Type) String() string {
	return tokens[t]
}

func (pos Position) String() string {
	return fmt.Sprintf("%d:%d", pos.Line, pos.Column)
}

func (pos *Position) NextLine() {
	pos.Line++
	pos.Column = 1
}
