import copy
import string
import ctypes
from enum import IntEnum
from typing import NamedTuple
from PeachPy.peachpy.x86_64 import *
from PeachPy.peachpy.x86_64 import abi
from PeachPy.peachpy.x86_64.operand import *
from PeachPy.peachpy.x86_64.registers import rsp

TEST_PROGRAM = """
var a, b, n, t;
begin
    ?n;
    a := 0;
    b := 1;
    while n > 0 do
    begin
        !b;
        n := n - 1;
        t := a + b;
        a := b;
        b := t
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

dll = ctypes.CDLL(None)
dll.dlsym.restype = ctypes.c_ulong

fn_putchar = dll.dlsym(None, ctypes.create_string_buffer(b'putchar'))
assert fn_putchar, 'putchar not found'

class Token(NamedTuple):
    ty: TokenKind
    val: int | str

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

        elif self.s[self.i] in '=#*+-/,;.()?!':
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


class AstEvalContext(NamedTuple):
    vars: dict[str, int | None]
    procs: dict[str, 'Block | list[Ir]']
    consts: dict[str, int]


class IrOpCode(IntEnum):
    Add = 0
    Sub = 1
    Mul = 2
    Div = 3
    Neg = 4 # 取反
    Eq = 5
    Ne = 6
    Lt = 7
    Lte = 8
    Gt = 9
    Gte = 10
    Odd = 11
    LoadVar = 12
    LoadLit = 13
    Store = 14
    Jump = 15 # 无条件跳转
    BrFalse = 16 # 有条件跳转
    DefVar = 17
    DefLit = 18
    DefProc = 19
    Call = 20
    Input = 100
    Output = 101
    Halt = 255


class Ir(NamedTuple):
    op: IrOpCode
    args: str | int | None = None
    value: list['Ir'] | int | None = None


class Factor(NamedTuple):
    value: any

    def asm(self, ctx: AstEvalContext):
        if isinstance(self.value, int):
            MOV(rax, self.value)
            PUSH(rax)
        elif isinstance(self.value, str):
            if (key := self.value) in ctx.vars:
                pass
            elif self.value in ctx.consts:
                MOV(rax, ctx.consts[self.value])
                PUSH(rax)
            else:
                raise RuntimeError('undefined symbol: ' + self.value)
        elif isinstance(self.value, Expression):
            self.value.asm(ctx)
        else:
            raise RuntimeError('invalid factor value')

    def gen(self, buf: list[Ir]):
        if isinstance(self.value, int):
            buf.append(Ir(IrOpCode.LoadLit, self.value))
        elif isinstance(self.value, str):
            buf.append(Ir(IrOpCode.LoadVar, self.value))
        elif isinstance(self.value, Expression):
            self.value.gen(buf)
        else:
            raise RuntimeError('invalid factor value')

    def eval(self, ctx: AstEvalContext) -> int | None:
        if isinstance(self.value, int):
            return self.value
        elif isinstance(self.value, str):
            if (key := self.value) in ctx.vars:
                ret = ctx.vars[self.value]
                if ret is None:
                    raise RuntimeError('variable %s referenced before initialize' % key)
                else:
                    return ret
            elif self.value in ctx.consts:
                return ctx.consts[self.value]
            else:
                raise RuntimeError('undefined symbol: ' + self.value)
        elif isinstance(self.value, Expression):
            val = self.value.eval(ctx)
            assert val is not None, 'invalid expression val'
            return val
        else:
            raise RuntimeError('invalid factor value')


class Term(NamedTuple):
    lhs: Factor
    rhs: list[tuple[str, Factor]]

    def asm(self):
        self.lhs.asm()
        for op, rhs in self.rhs:
            rhs.asm()
            POP(rcx) # 先POP右值
            POP(rax)
            if op == '*':
                IMUL(rax, rcx)
                PUSH(rax)
            elif op == '/':
                IDIV(rcx)
                PUSH(rax)
            else:
                raise RuntimeError('invalid expression operator')

    def gen(self, buf: list[Ir]):
        self.lhs.gen(buf)

        for op, rhs in self.rhs:
            rhs.gen(buf)

            if op == '*':
                buf.append(Ir(IrOpCode.Mul))
            elif op == '/':
                buf.append(Ir(IrOpCode.Div))
            else:
                raise RuntimeError('invalid expression operator')

    def eval(self, ctx: AstEvalContext) -> int | None:
        ret = self.lhs.eval(ctx)
        assert ret is not None, 'invalid expression lhs'

        for op, rhs in self.rhs:
            val = rhs.eval(ctx)
            assert val is not None, 'invalid expression rhs'

            if op == '*':
                ret *= val
            elif op == '/':
                if val == 0:
                    raise RuntimeError('division error')
                ret /= val
            else:
                raise RuntimeError('invalid expression operator')

        return ret


class Expression(NamedTuple):
    mod: str
    lhs: Term
    rhs: list[tuple[str, Term]]

    def asm(self):
        self.lhs.asm()

        if self.mod == '-':
            NEG(MemoryOperand(rsp, 8))
        elif self.mod not in {'+', ''}:
            raise RuntimeError('invalid expression sign ' + self.mod)

        for op, rhs in self.rhs:
            rhs.asm()
            POP(rcx)
            POP(rax)
            if op == '+':
                ADD(rax, rcx)
                PUSH(rax)
            elif op == '-':
                SUB(rax, rcx)
                PUSH(rax)
            else:
                raise RuntimeError('invalid expression operator')

    def gen(self, buf: list[Ir]):
        self.lhs.gen(buf)
        if self.mod == '-':
            buf.append(Ir(IrOpCode.Neg))
        elif self.mod not in {'+', ''}:
            raise RuntimeError('invalid expression sign ' + self.mod)

        for op, rhs in self.rhs:
            rhs.gen(buf)

            if op == '+':
                buf.append(Ir(IrOpCode.Add))
            elif op == '-':
                buf.append(Ir(IrOpCode.Sub))
            else:
                raise RuntimeError('invalid expression operator')

    def eval(self, ctx: AstEvalContext) -> int | None:
        if self.mod == '-':
            sign = -1
        elif self.mod in {'+', ''}:
            sign = 1
        else:
            raise RuntimeError('invalid expression sign ' + self.mod)

        ret = self.lhs.eval(ctx) * sign
        assert ret is not None, 'invalid expression lhs'

        for op, rhs in self.rhs:
            val = rhs.eval(ctx)
            assert val is not None, 'invalid expression rhs'

            if op == '+':
                ret += val
            elif op == '-':
                ret -= val
            else:
                raise RuntimeError('invalid expression operator')

        return ret


class Const(NamedTuple):
    name: str
    value: int


class Assign(NamedTuple):
    name: str
    expr: Expression

    def asm(self):
        self.expr.asm()

    def gen(self, buf: list[Ir]):
        self.expr.gen(buf)
        buf.append(Ir(IrOpCode.Store, self.name))

    def eval(self, ctx: AstEvalContext) -> int | None:
        if self.name not in ctx.vars:
            raise RuntimeError('undefined variable: ' + self.name)

        val = self.expr.eval(ctx)
        assert val is not None, 'invalid assignment expression'

        ctx.vars[self.name] = val
        return None


class Call(NamedTuple):
    name: str

    def gen(self, buf: list[Ir]):
        buf.append(Ir(IrOpCode.Call, self.name))

    def eval(self, ctx: AstEvalContext) -> int | None:
        if self.name not in ctx.procs:
            raise RuntimeError('call name not found')
        proc = ctx.procs[self.name]
        assert isinstance(proc, Procedure), 'invalid proc'
        return proc.eval(ctx)
        # temp_ctx = copy.deepcopy(ctx)
        # # 调用block
        # block.eval(temp_ctx)
        # # 更新ctx里的变量, 新的覆盖旧的
        # for name, value in temp_ctx.vars:
        #     if name in ctx.vars:
        #         ctx.vars[name] = value
        #
        # return None


class InputOutput(NamedTuple):
    name: str
    is_input: bool

    def gen(self, buf: list[Ir]):
        if not self.is_input:
            buf.append(Ir(IrOpCode.LoadVar, self.name))
            buf.append(Ir(IrOpCode.Output))
        else:
            buf.append(Ir(IrOpCode.Input))
            buf.append(Ir(IrOpCode.Store, self.name))

    def eval(self, ctx: AstEvalContext):
        if not self.is_input:
            print(Factor(self.name).eval(ctx))
        elif self.name in ctx.vars:
            ctx.vars[self.name] = int(input())
            return None
        else:
            raise RuntimeError('undefined variable: ' + self.name)


class Statement(NamedTuple):
    stmt: any

    def asm(self):
        self.stmt.asm()

    def gen(self, buf: list[Ir]):
        self.stmt.gen(buf)

    def eval(self, ctx: AstEvalContext) -> int | None:
        self.stmt.eval(ctx)
        return None


class Begin(NamedTuple):
    body: list[Statement]

    def asm(self):
        for stmt in self.body:
            stmt.asm()

    def gen(self, buf: list[Ir]):
        for stmt in self.body:
            stmt.gen(buf)

    def eval(self, ctx: AstEvalContext):
        for stmt in self.body:
            stmt.eval(ctx)


class OddCondition(NamedTuple):
    expr: Expression

    def asm(self):
        self.expr.asm()
        AND(MemoryOperand(rax, 8), 1)

    def gen(self, buf: list[Ir]):
        self.expr.gen(buf)
        buf.append(Ir(IrOpCode.Odd))

    def eval(self, ctx: AstEvalContext) -> int | None:
        val = self.expr.eval(ctx)
        assert val is not None, 'invalid odd condition expression'

        return val & 1


class StdCondition(NamedTuple):
    op: str
    lhs: Expression
    rhs: Expression

    def asm(self):
        self.lhs.asm()
        self.rhs.asm()
        POP(rax)
        POP(rcx)
        CMP(rax, rcx)

        if self.op == '>':
            SETG(rax)
        elif self.op == '>=':
            SETGE(rax)
        elif self.op == '<':
            SETL(rax)
        elif self.op == '<=':
            SETLE(rax)
        elif self.op == '==':
            SETE(rax)
        elif self.op == '#':
            SETNE(rax)
        else:
            raise RuntimeError('invalid std condition operation ' + self.op)
        PUSH(rax)

    def gen(self, buf: list[Ir]):
        self.lhs.gen(buf)
        self.rhs.gen(buf)

        if self.op == '>':
            buf.append(Ir(IrOpCode.Gt))
        elif self.op == '>=':
            buf.append(Ir(IrOpCode.Gte))
        elif self.op == '<':
            buf.append(Ir(IrOpCode.Lt))
        elif self.op == '<=':
            buf.append(Ir(IrOpCode.Lte))
        elif self.op == '==':
            buf.append(Ir(IrOpCode.Eq))
        elif self.op == '#':
            buf.append(Ir(IrOpCode.Ne))
        else:
            raise RuntimeError('invalid std condition operation ' + self.op)

    def eval(self, ctx: AstEvalContext) -> int | None:
        lhs = self.lhs.eval(ctx)
        rhs = self.rhs.eval(ctx)
        assert lhs is not None, 'invalid lhs expression'
        assert rhs is not None, 'invalid rhs expression'

        if self.op == '>':
            return 1 if lhs > rhs else 0
        elif self.op == '>=':
            return 1 if lhs >= rhs else 0
        elif self.op == '<':
            return 1 if lhs < rhs else 0
        elif self.op == '<=':
            return 1 if lhs <= rhs else 0
        elif self.op == '==':
            return 1 if lhs == rhs else 0
        elif self.op == '!=':
            return 1 if lhs != rhs else 0
        else:
            raise RuntimeError('invalid std condition operation ' + self.op)


class Condition(NamedTuple):
    cond: OddCondition | StdCondition

    def asm(self):
        self.cond.asm()

    def gen(self, buf: list[Ir]):
        self.cond.gen(buf)

    def eval(self, ctx: AstEvalContext) -> int | None:
        return self.cond.eval(ctx)


class If(NamedTuple):
    cond: Condition
    then: Statement

    def asm(self):
        pass # TODO

    def gen(self, buf: list[Ir]):
        self.cond.gen(buf)
        i = len(buf)
        buf.append(Ir(IrOpCode.BrFalse))
        self.then.gen(buf)
        buf[i] = Ir(IrOpCode.BrFalse, len(buf))

    def eval(self, ctx: AstEvalContext):
        val = self.cond.eval(ctx)
        assert val is not None, 'invalid if condition expression'

        if val != 0:
            self.then.eval(ctx)


class While(NamedTuple):
    cond: Condition
    do: Statement

    def gen(self, buf: list[Ir]):
        i = len(buf)
        self.cond.gen(buf)
        j = len(buf)
        buf.append(Ir(IrOpCode.BrFalse))
        self.do.gen(buf)
        buf.append(Ir(IrOpCode.Jump, i))
        buf[j] = Ir(IrOpCode.BrFalse, len(buf))

    def eval(self, ctx: AstEvalContext):
        while True:
            val = self.cond.eval(ctx)
            assert val is not None, 'invalid if condition expression'

            if val == 0:
                break
            else:
               self.do.eval(ctx)


class Procedure(NamedTuple):
    name: str
    body: 'Block'

    def asm(self):
        pass # TODO

    def gen(self, buf: list[Ir]):
        self.body.gen(buf)

    def eval(self, ctx: AstEvalContext) -> int | None:
        if not isinstance(self.body, Block):
            raise RuntimeError('invalid procedure body.')
        ctx.procs[self.name] = self.body
        return None


class Block(NamedTuple):
    consts: list[Const]
    vars: list[str]
    procs: list[Procedure]
    stmt: Statement

    def asm(self):
        pass

    def gen(self, buf: list[Ir]):
        for cc in self.consts:
            buf.append(Ir(IrOpCode.DefLit, cc.name, cc.value))
        for vv in self.vars:
            buf.append(Ir(IrOpCode.DefVar, vv))
        for pp in self.procs:
            proc = []
            pp.gen(proc)
            buf.append(Ir(IrOpCode.DefProc, pp.name, proc))
        self.stmt.gen(buf)

    def eval(self, ctx: AstEvalContext) -> int | None:
        for cc in self.consts:
            if cc.name in ctx.consts:
                raise RuntimeError('const redefinition ' + cc.name)
            else:
                ctx.consts[cc.name] = cc.value

        for vv in self.vars:
            if vv in ctx.vars or vv in ctx.consts:
                raise RuntimeError('variable redefinition ' + vv)
            else:
                ctx.vars[vv] = None

        for pp in self.procs:
            ctx.procs[pp.name] = pp

        self.stmt.eval(ctx)
        return None


class Program(NamedTuple):
    block: Block

    def gen(self, buf: list[Ir]):
        self.block.gen(buf)
        buf.append(Ir(IrOpCode.Halt))

    def eval(self, ctx: AstEvalContext) -> int | None:
        return self.block.eval(ctx)


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

    def expect(self, ty: TokenKind, val: str | int | None = None):
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
            var = self.var()

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
            return Statement(While(cond, self.statement()))

        elif self.check(TokenKind.Op, '?'):
            name = self.lx.next()
            ty = name.ty

            if ty != TokenKind.Name:
                raise SyntaxError('name expected')
            else:
                return Statement(InputOutput(name.val, True))
        elif self.check(TokenKind.Op, '!'):
            name = self.lx.next()
            ty = name.ty

            if ty != TokenKind.Name:
                raise SyntaxError('name expected')
            else:
                return Statement(InputOutput(name.val, False))

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
                rhs.append(('+', self.factor()))
            elif self.check(TokenKind.Op, '-'):
                rhs.append(('-', self.factor()))
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


def ir_eval(buf: list[Ir], ctx: AstEvalContext):
    pc = 0
    sp = []

    while pc < len(buf):
        ir = buf[pc]
        pc += 1

        # 出栈 压栈
        if ir.op == IrOpCode.Add:
            v2 = sp.pop()
            v1 = sp.pop()
            sp.append(v1 + v2)

        elif ir.op == IrOpCode.Sub:
            v2 = sp.pop()
            v1 = sp.pop()
            sp.append(v1 - v2)

        elif ir.op == IrOpCode.Mul:
            v2 = sp.pop()
            v1 = sp.pop()
            sp.append(v1 * v2)

        elif ir.op == IrOpCode.Div:
            v2 = sp.pop()
            v1 = sp.pop()

            if v2 == 0:
                raise RuntimeError('division by zero')
            else:
                sp.append(v1 / v2)

        elif ir.op == IrOpCode.Neg:
            sp[-1] = -sp[-1]

        elif ir.op == IrOpCode.Eq:
            v2 = sp.pop()
            v1 = sp.pop()
            sp.append(int(v1 == v2))

        elif ir.op == IrOpCode.Ne:
            v2 = sp.pop()
            v1 = sp.pop()
            sp.append(int(v1 != v2))

        elif ir.op == IrOpCode.Lt:
            v2 = sp.pop()
            v1 = sp.pop()
            sp.append(int(v1 < v2))

        elif ir.op == IrOpCode.Lte:
            v2 = sp.pop()
            v1 = sp.pop()
            sp.append(int(v1 <= v2))

        elif ir.op == IrOpCode.Gt:
            v2 = sp.pop()
            v1 = sp.pop()
            sp.append(int(v1 > v2))

        elif ir.op == IrOpCode.Gte:
            v2 = sp.pop()
            v1 = sp.pop()
            sp.append(int(v1 >= v2))

        elif ir.op == IrOpCode.Odd:
            sp[-1] = sp[-1] & 1

        elif ir.op == IrOpCode.LoadVar:
            if not isinstance(ir.args, str):
                raise RuntimeError('invalid loadvar args')

            elif ir.args in ctx.vars:
                key = ir.args
                val = ctx.vars[key]

                if val is None:
                    raise RuntimeError('variable %s referenced before initialization' % key)
                else:
                    sp.append(val)

            elif ir.args in ctx.consts:
                sp.append(ctx.consts[ir.args])

            else:
                raise RuntimeError('undefined variable: ' + ir.args)

        elif ir.op == IrOpCode.LoadLit:
            if not isinstance(ir.args, int):
                raise RuntimeError('invalid loadvar args')
            else:
                sp.append(ir.args)

        elif ir.op == IrOpCode.Store:
            if not isinstance(ir.args, str):
                raise RuntimeError('invalid store args')
            elif ir.args not in ctx.vars:
                raise RuntimeError('undefined variable: ' + ir.args)
            else:
                ctx.vars[ir.args] = sp.pop()

        elif ir.op == IrOpCode.Jump:
            if not isinstance(ir.args, int):
                raise RuntimeError('invalid jump args')
            elif 0 <= ir.args < len(buf):
                pc = ir.args
            else:
                raise RuntimeError('branch out of bounds')

        elif ir.op == IrOpCode.BrFalse:
            if not sp.pop():
                if not isinstance(ir.args, int):
                    raise RuntimeError('invalid brfalse args')
                elif 0 <= ir.args < len(buf):
                    pc = ir.args
                else:
                    raise RuntimeError('branch out of bounds')

        elif ir.op == IrOpCode.DefVar:
            if not isinstance(ir.args, str):
                raise RuntimeError('invalid defvar args')
            elif ir.args in ctx.vars or ir.args in ctx.procs or ir.args in ctx.consts:
                raise RuntimeError('variable redeclared: ' + ir.args)
            else:
                ctx.vars[ir.args] = None

        elif ir.op == IrOpCode.DefLit:
            if not isinstance(ir.args, str) or not isinstance(ir.value, int):
                raise RuntimeError('invalid deflit args')
            elif ir.args in ctx.vars or ir.args in ctx.procs or ir.args in ctx.consts:
                raise RuntimeError('variable redeclared: ' + ir.args)
            else:
                ctx.consts[ir.args] = ir.value

        elif ir.op == IrOpCode.DefProc:
            if not isinstance(ir.args, str) or not isinstance(ir.value, list):
                raise RuntimeError('invalid defproc args')
            elif ir.args in ctx.vars or ir.args in ctx.procs or ir.args in ctx.consts:
                raise RuntimeError('variable redeclare: ' + ir.args)
            else:
                ctx.procs[ir.args] = ir.value

        elif ir.op == IrOpCode.Call:
            if ir.args not in ctx.procs:
                raise RuntimeError('procedure called not existed.')
            else:
                block = ctx.procs[ir.args]
                temp_ctx = copy.deepcopy(ctx)
                temp_buf = copy.deepcopy(block)
                ir_eval(temp_buf, temp_ctx)
                for k, v in temp_ctx.vars.items():
                    if k in ctx.vars:
                        ctx.vars[k] = v

        elif ir.op == IrOpCode.Input:
            sp.append(int(input()))

        elif ir.op == IrOpCode.Output:
            print(sp.pop())

        elif ir.op == IrOpCode.Halt:
            break

        else:
            raise RuntimeError('invalid instruction')


def ir_asm(buf: list[Ir]) -> bytes:
    brtab = {}
    pctab = []
    littab = {}
    vartab = {}

    nbuf = [
        PUSH(rbp),
        MOV(rbp, rsp),
        None,
        PUSH(r15),
    ]

    for i, ir in enumerate(buf):
        pc = len(nbuf)
        pctab.append(pc)

        match ir.op:
            case IrOpCode.Add:
                nbuf.append(POP(rax)) # 抛出右值
                nbuf.append(ADD([rsp], rax)) # 操作内存 加
            case IrOpCode.Sub:
                nbuf.append(POP(rax))
                nbuf.append(SUB([rsp], rax))
            case IrOpCode.Mul:
                nbuf.append(POP(rcx))
                nbuf.append(MOV(rax, [rsp]))
                nbuf.append(IMUL(rcx))
                nbuf.append(MOV([rsp], rax))
            case IrOpCode.Div:
                nbuf.append(POP(rcx))
                nbuf.append(MOV(rax, [rsp]))
                nbuf.append(IDIV(rcx))
                nbuf.append(MOV([rsp], rax))
            case IrOpCode.Neg:
                nbuf.append(NEG(MemoryOperand(rax, 8)))
            case IrOpCode.Eq | IrOpCode.Ne | IrOpCode.Lt | IrOpCode.Lte | IrOpCode.Gt | IrOpCode.Gte:
                POP(rcx)
                CMP([rsp], rcx)
                match ir.op:
                    case IrOpCode.Eq: nbuf.append(SETE([rsp]))
                    case IrOpCode.Ne: nbuf.append(SETNE([rsp]))
                    case IrOpCode.Lt: nbuf.append(SETL([rsp]))
                    case IrOpCode.Lte: nbuf.append(SETLE([rsp]))
                    case IrOpCode.Gt: nbuf.append(SETG([rsp]))
                    case IrOpCode.Gte: nbuf.append(SETGE([rsp]))
            case IrOpCode.Odd:
                nbuf.append(AND(MemoryOperand(rsp, 8), 1))
            case IrOpCode.LoadVar:
                if not isinstance(ir.args, str):
                    raise RuntimeError('invalid loadvar args')
                elif ir.args in littab:
                    nbuf.append(MOV(rax, ir.args))
                    nbuf.append(PUSH(rax))
                    continue
                elif ir.args in vartab:
                    nbuf.append(MOV(rax, [rbp - vartab[ir.args] * 8 - 8]))
                    nbuf.append(PUSH(rax))
                else:
                    raise RuntimeError('undefined variable: ' + ir.args)

            case IrOpCode.LoadLit:
                if not isinstance(ir.args, str) or not isinstance(ir.value, int):
                    raise RuntimeError('invalid deflit args')
                nbuf.append(MOV(rax, ir.args))
                nbuf.append(PUSH(rax))
            case IrOpCode.Store:
                if not isinstance(ir.args, str):
                    raise RuntimeError('invalid store args')
                elif ir.args not in vartab:
                    raise RuntimeError('undefined variable: ' + ir.args)
                else:
                    nbuf.append(POP(rax))
                    nbuf.append(MOV([rbp - vartab[ir.args] * 8 - 8], rax))

            case IrOpCode.Jump:
                if not isinstance(ir.args, int):
                    raise RuntimeError('invalid jump args')

                if not (0 <= ir.args < len(buf)):
                    raise RuntimeError('branch out of bounds')

                nbuf.append(JMP(RIPRelativeOffset(0)))
                brtab[pc] = ir.args

            case IrOpCode.BrFalse:
                if not isinstance(ir.args, int):
                    raise RuntimeError('invalid brfalse args')
                if not (0 <= ir.args < len(buf)):
                    raise RuntimeError('branch out of bounds')

                nbuf.append(POP(rax))
                nbuf.append(TEST(rax, rax))
                brtab[pc] = ir.args
                nbuf.append(JZ(RIPRelativeOffset(0)))

            case IrOpCode.DefVar:
                if not isinstance(ir.args, str):
                    raise RuntimeError('invalid defvar args')
                elif ir.args in littab or ir.args in vartab:
                    raise RuntimeError('const redeclared: ' + ir.args)
                else:
                    vartab[ir.args] = len(vartab)

            case IrOpCode.DefLit:
                if not isinstance(ir.args, str) or not isinstance(ir.value, int):
                    raise RuntimeError('invalid deflit args')
                elif ir.args in littab or ir.args in vartab:
                    raise RuntimeError('const redeclared: ' + ir.args)
                else:
                    littab[ir.args] = ir.value

            case IrOpCode.DefProc:
                raise NotImplementedError('implement this.') #TODO
            case IrOpCode.Input:
                pass
            case IrOpCode.Output:
                nbuf.append(POP(rdi))
                nbuf.append(MOV(r15, fn_putchar))
                nbuf.append(CALL(r15))
            case IrOpCode.Halt:
                break
            case _:
                raise RuntimeError("invalid instruction.")
    stack_size = len(vartab) * 8
    nbuf[nbuf.index(None)] = SUB(rsp, len(vartab) * 8)
    nbuf.extend([
        POP(r15),
        ADD(rsp, stack_size),
        POP(rbp),
        RET()
    ])

    func = Function('pl0_asm', ())
    func.add_instruction(nbuf)
    func.finalize(abi.detect()).encode().load()()

def main():
    ps = Parser(Lexer(TEST_PROGRAM))
    buf = []
    ast = ps.program()
    ast.gen(buf)
    ir_eval(buf, AstEvalContext({}, {}, {}))


if __name__ == '__main__':
    main()