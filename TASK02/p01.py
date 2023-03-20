import string
from enum import IntEnum
from typing import NamedTuple, List, Tuple

TEST_PROGRAM = """
var i, s;
begin 
    i := 0; s:= 0;
    while i < 5 do
    begin
        i := i + 1;
        s := s + i * i
    end
end.
"""


class TokenKind(IntEnum):
    Op = 0
    Num = 1
    Name = 2
    KeyWord = 3
    Eof = 4


IDENT_FIRST = string.ascii_letters + '_'
IDENT_REMAIN = string.ascii_letters + string.digits + '_'
KEYWORD_SET = {
    'const',
    'var',
    'procedure',
    'call',
    'begin',
    'end',
    'if',
    'then',
    'while',
    'do',
    'odd'
}


class Token(NamedTuple):
    ty: TokenKind
    val: any
    # int for num, str for other

    @classmethod
    def op(cls, op: str) -> 'Token':
        return cls(ty=TokenKind.Op, val=op)

    @classmethod
    def num(cls, num: int) -> 'Token':
        return cls(ty=TokenKind.Num, val=num)

    @classmethod
    def name(cls, name: str) -> 'Token':
        return cls(ty=TokenKind.Name, val=name)

    @classmethod
    def keyword(cls, keyword: str) -> 'Token':
        return cls(ty=TokenKind.KeyWord, val=keyword)

    @classmethod
    def eof(cls) -> 'Token':
        return cls(ty=TokenKind.Eof, val=0)


class Lexer:
    i: int
    s: str

    def __init__(self, src: str):
        self.i = 0
        self.s = src

    @property
    def eof(self) -> bool:
        return self.i >= len(self.s)

    def _skip_blank(self):
        while not self.eof and self.s[self.i].isspace():
            self.i += 1

    def next(self) -> Token:
        val = ''
        self._skip_blank()

        if self.eof:
            return Token.eof()

        elif self.s[self.i].isdigit():
            while self.s[self.i].isdigit():
                val += self.s[self.i]
                self.i += 1
            return Token.num(int(val))

        elif self.s[self.i] in IDENT_FIRST:
            while self.s[self.i] in IDENT_REMAIN:
                val += self.s[self.i]
                self.i += 1

            if val in KEYWORD_SET:
                return Token.keyword(val)
            else:
                return Token.name(val)

        elif self.s[self.i] in '=#*+-/,;.()':
            ch = self.s[self.i]
            self.i += 1
            return Token.op(ch)

        elif self.s[self.i] == ':':
            self.i += 1
            if self.eof or self.s[self.i] != '=':
                raise SyntaxError(' "=" expected')
            self.i += 1
            return Token.op(':=')

        elif self.s[self.i] in '<>':
            ch = self.s[self.i]
            self.i += 1
            if not self.eof and self.s[self.i] == '=':
                self.i += 1
                return Token.op(ch + '=')
            else:
                return Token.op(ch)

        else:
            raise SyntaxError("invaild charset " + repr(self.s[self.i]))


class Factor(NamedTuple):
    value: any


class Term(NamedTuple):
    lhs: Factor
    rhs: List[Tuple[str, Factor]]


class Expression(NamedTuple):
    mod: str
    lhs: Term
    rhs: List[Tuple[str, Term]]


class Const(NamedTuple):
    name: str
    value: int


class Assign(NamedTuple):
    name: str
    expr: Expression


class Call(NamedTuple):
    name: str


class Statement(NamedTuple):
    stmt: any


class Begin(NamedTuple):
    body: List[Statement]


class OddCondition(NamedTuple):
    expr: Expression


class StdCondition(NamedTuple):
    op: str
    lhs: Expression
    rhs: Expression


class Condition(NamedTuple):
    cond: any


class If(NamedTuple):
    cond: Condition
    then: Statement


class While(NamedTuple):
    cond: Condition
    then: Statement


class Procedure(NamedTuple):
    name: str
    body: any


class Block(NamedTuple):
    consts: List[Const]
    vars: List[str]
    procs: List[Procedure]
    stmt: Statement


class Program(NamedTuple):
    block: Block


class Parser:
    lx: Lexer

    def __init__(self, lx: Lexer):
        self.lx = lx

    def check(self, ty: TokenKind, val) -> bool:
        p = self.lx.i
        tk = self.lx.next()

        if tk.ty == ty and tk.val == val:
            return True

        self.lx.i = p
        return False

    def expect(self, ty, val: any):
        tk = self.lx.next()
        tty, tval = tk.ty, tk.val

        if tty != ty:
            raise SyntaxError('%s expected, got %s' % (ty, tty))

        if val is not None:
            if tval != val:
                raise SyntaxError('"%s" expected, got "%s"' % (tval, val))

    def program(self):
        block = self.block()
        self.expect(TokenKind.Op, '.')
        return Program(block)

    def block(self):
        var = []
        const = []
        proc = []

        if self.check(TokenKind.KeyWord, 'const'):
            const = self.const()

        if self.check(TokenKind.KeyWord, 'var'):
            const = self.var()

        while self.check(TokenKind.KeyWord, 'procedure'):
            proc.append(self.procedure())

        stat = self.statement()
        return Block(const, var, proc, stat)

    def const(self):
        ret = []
        while True:
            ident = self.lx.next()
            name = ident.ty
            if name != TokenKind.Name:
                raise SyntaxError('name expected')

            self.expect(TokenKind.Op, '=')
            num = self.lx.next()

            if num.ty != TokenKind.Num:
                raise SyntaxError('num expected')
            else:
                ret.append(Const(ident.val, num.val))
            if self.check(TokenKind.Op, ';'):
                return ret
            else:
                self.expect(TokenKind.Op, ',')

    def var(self):
        ret = []
        while True:
            name = self.lx.next()
            ty = name.ty
            if ty != TokenKind.Name:
                raise SyntaxError('name expected')
            else:
                ret.append(name.val)
            if self.check(TokenKind.Op, ';'):
                return ret
            else:
                self.expect(TokenKind.Op, ',')

    # TODO
    def procedure(self):
        ident = self.lx.next()
        ty = ident.ty
        if ty != TokenKind.Name:
            raise SyntaxError('name expected')

        if not self.check(TokenKind.Op, ';'):
            raise SyntaxError('";" expected')

        block = self.block()
        if not self.check(TokenKind.Op, ';'):
            raise SyntaxError('";" expected')

        return Procedure(ident.val, block)

    def statement(self):
        if self.check(TokenKind.KeyWord, 'call'):
            ident = self.lx.next()
            if ident.ty != TokenKind.Name:
                raise SyntaxError('name expected')
            else:
                return Statement(Call(ident))

        elif self.check(TokenKind.KeyWord, 'begin'):
            body = []
            while True:
                body.append(self.statement())

                if self.check(TokenKind.KeyWord, 'end'):
                    break
                else:
                    self.expect(TokenKind.Op, ';')
            return Statement(Begin(body))

        elif self.check(TokenKind.KeyWord, 'if'):
            cond = self.condition()
            self.expect(TokenKind.KeyWord, 'then')
            return Statement(If(cond, self.statement()))

        elif self.check(TokenKind.KeyWord, 'while'):
            cond = self.condition()
            self.expect(TokenKind.KeyWord, 'do')
            return Statement(If(cond, self.statement()))
        else:
            tk = self.lx.next()
            ty = tk.ty

            if ty != TokenKind.Name:
                raise SyntaxError('name expected')

            self.expect(TokenKind.Op, ':=')
            return Statement(Assign(tk.val, self.expression()))

    def condition(self):
        if self.check(TokenKind.KeyWord, 'odd'):
            return Condition(self.odd_condition())
        else:
            return Condition(self.std_condition())

    def odd_condition(self):
        return OddCondition(self.expression())

    def std_condition(self):
        lhs = self.expression()
        cmp = self.lx.next()
        if cmp.ty != TokenKind.Op:
            raise SyntaxError('op expected')

        if cmp.val not in {'=', '#', '<=', '>=', '<', '>'}:
            raise SyntaxError('condition operator invaild')
        rhs = self.expression()
        return StdCondition(cmp.val, lhs, rhs)

    def expression(self):
        if self.check(TokenKind.Op, '+'):
            mod = '+'
        elif self.check(TokenKind.Op, '-'):
            mod = '-'
        else:
            mod = ''

        lhs = self.term()
        rhs = []
        while True:
            if self.check(TokenKind.Op, '+'):
                rhs.append(('+', self.term()))
            elif self.check(TokenKind.Op, '-'):
                rhs.append(('-', self.term()))
            else:
                return Expression(mod, lhs, rhs)

    def term(self):
        rhs = []
        lhs = self.factor()
        while True:
            if self.check(TokenKind.Op, '*'):
                rhs.append(('*', self.term()))
            elif self.check(TokenKind.Op, '/'):
                rhs.append(('/', self.term()))
            else:
                return Term(lhs, rhs)

    def factor(self):
        tk = self.lx.next()
        ty, val = tk.ty, tk.val

        if ty in {TokenKind.Num, TokenKind.Name}:
            return Factor(val)

        if ty != TokenKind.Op or val != '(':
            raise SyntaxError('( need')
        expr = self.expression()
        self.expect(TokenKind.Op, ')')
        return Factor(expr)

ps = Parser(Lexer(TEST_PROGRAM))
print(ps.program())