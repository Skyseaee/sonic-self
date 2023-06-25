package lexer

import (
	"code.skyseaee.com/sonic-self/TASK07/token"
)

type Lexer struct {
	data []byte

	offset int
	curr   rune
	pos    token.Position
	tokens chan token.Token
}

const eof = -1

func (l *Lexer) next() {
	if l.curr = l.peek(); l.curr == eof {
		return
	}

	l.offset++

	if l.curr == '\n' {
		l.pos.NextLine()
	} else {
		l.pos.Column++
	}
}

func (l *Lexer) peek() rune {
	if l.offset >= len(l.data) {
		return eof
	}

	return rune(l.data[l.offset])
}

func (l *Lexer) program() {
	for {
		var tok token.Type
		switch l.peek() {
		case eof:
			tok = token.Eof
		case '+':
			tok = token.Plus
		case '-':
			tok = token.Minus
		case '<':
			tok = token.LeftArrow
		case '>':
			tok = token.RightArrow
		case ',':
			tok = token.Comma
		case '.':
			tok = token.Period
		case '[':
			tok = token.LeftBracket
		case ']':
			tok = token.RightBracket
		default:
			l.next()
			continue
		}
		l.emit(tok)

		l.next()

		if tok == token.Eof {
			return
		}
	}
}

func (l *Lexer) emit(tok token.Type) {
	l.tokens <- token.Token{
		Type:     tok,
		Position: l.pos,
	}

	if tok == token.Eof {
		close(l.tokens)
	}
}

func Lex(data []byte) <-chan token.Token {
	l := Lexer{
		data:   data,
		pos:    token.Position{Line: 1, Column: 1},
		tokens: make(chan token.Token, 1),
	}

	go l.program()
	return l.tokens
}
