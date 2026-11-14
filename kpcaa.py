from dataclasses import dataclass, field
import sys
from typing import NoReturn


class ProgramTypes: pass
class StackTypes: pass


@dataclass
class Cmd(ProgramTypes): command: str
@dataclass
class Num(ProgramTypes, StackTypes): data: int
@dataclass
class Ptr(ProgramTypes, StackTypes): ptr: int
class Nil(ProgramTypes, StackTypes): pass
nil = Nil()

Program = tuple[Cmd, *tuple[StackTypes, ...]]

class HeapTypes: pass
@dataclass
class Int(HeapTypes): data: int | None = None
@dataclass
class Array(HeapTypes):
    data: list[int] = field(default_factory=list)
    length: int = 0

class Kpcaaeths:
    def __init__(self, src: str):
        self.labels: dict[int, int] = {}
        self.program: list[tuple[int, Program]] = []
        self.tokens: list[tuple[int, list[str]]] = []
        self.stack: list[StackTypes] = []      # kcats
        self.heap: list[HeapTypes] = []        # paeh
        self.lineno: int = 0
        self.pc: int = 0
        self.tokenize(src)

    def error(self, message: str) -> NoReturn:
        print(f"line {self.lineno}: {message}", file=sys.stderr)
        sys.exit(1)

    def tokenize(self, src: str) -> None:
        result: list[tuple[int, list[str]]] = []
        for lineno, line in enumerate(src.splitlines(), start=1):
            line = line.strip()
            if not line:
                continue
            for stmt in line.split(";"):
                stmt = stmt.strip()
                if not stmt or stmt.startswith("'"):
                    continue
                tokens = stmt.split()
                if tokens:
                    result.append((lineno, tokens))
        self.tokens = result

    def parse(self) -> None:
        for lineno, parts in self.tokens:
            if parts[0] == "lab":
                n = int(parts[1])
                self.labels[n] = len(self.program)
                continue
            if not parts:
                continue
            self.lineno = lineno
            parsed: list[ProgramTypes] = [Cmd(parts[0])]
            for part in parts[1:]:
                if part == "nil":
                    parsed.append(nil)
                if part.isnumeric():
                    parsed.append(Num(int(part)))
                elif part.startswith('*') and part[1:].isnumeric():
                    parsed.append(Ptr(int(part[1:])))
                else:
                    self.error(f"Unexpected token: {part}")
            head = parsed[0]
            if not isinstance(head, Cmd):
                self.error("statement must start with Cmd")
            args: list[StackTypes] = []
            for a in parsed[1:]:
                if isinstance(a, (Num, Ptr)):
                    args.append(a)
                else:
                    self.error("arg must be Num or Ptr")
            stmt: Program = (head, *args)
            self.program.append((lineno, stmt))

    def execute(self) -> None:
        self.pc = 0
        while self.pc < len(self.program):
            lineno, stmt = self.program[self.pc]
            self.lineno = lineno
            head, *args = stmt
            self.pc += 1
            match head.command:
                case 'psh':
                    for arg in args:
                        self.stack.append(arg)
                case 'pop':
                    if not self.stack:
                        self.error("pop: stack underflow")
                    self.stack.pop()
                case 'mk':
                    if not args:
                        self.error("mk: missing type")
                    arg = args[0]
                    if not isinstance(arg, Num):
                        self.error(f"mk: expected Num, got {type(arg).__name__}")
                    match arg.data:
                        case 0:
                            self.heap.append(Int())
                        case 1:
                            self.heap.append(Array())
                        case _:
                            self.error(f"mk: unknown type {arg.data}")
                case 'len':
                    if len(args) < 2:
                        self.error("len: expected <addr> <length>")
                    addr, length = args[0], args[1]
                    if not isinstance(addr, Ptr):
                        self.error(f"len: expected Ptr addr, got {type(addr).__name__}")
                    if not isinstance(length, Num):
                        self.error(f"len: expected Num length, got {type(length).__name__}")
                    if addr.ptr >= len(self.heap):
                        self.error(f"len: heap index {addr.ptr} out of range")
                    targ = self.heap[addr.ptr]
                    if not isinstance(targ, Array):
                        self.error(f"len: target is not Array")
                    targ.length = length.data
                case 'sto':
                    if len(args) < 2:
                        self.error("sto: expected <addr> <value>")
                    addr, value = args[0], args[1]
                    if not isinstance(addr, Ptr):
                        self.error(f"sto: expected Ptr addr, got {type(addr).__name__}")
                    if not isinstance(value, Num):
                        self.error(f"sto: expected Num value, got {type(value).__name__}")
                    if addr.ptr >= len(self.heap):
                        self.error(f"sto: heap index {addr.ptr} out of range")
                    targ = self.heap[addr.ptr]
                    if isinstance(targ, Int):
                        targ.data = value.data
                    elif isinstance(targ, Array):
                        if len(targ.data) >= targ.length: # type: ignore
                            self.error("sto: array full")
                        targ.data.append(value.data) # type: ignore
                    else:
                        self.error(f"sto: unknown target {type(targ).__name__}")
                case 'sfc':
                    if not args:
                        self.error("sfc: missing ptr")
                    ptr = args[0]
                    if not isinstance(ptr, Ptr):
                        self.error(f"sfc: expected Ptr, got {type(ptr).__name__}")
                    if ptr.ptr >= len(self.heap):
                        self.error(f"sfc: heap index {ptr.ptr} out of range")
                    v = self.stack.pop()
                    if not isinstance(v, Num):
                        self.error(f"sfc: expected Num value, got {type(v).__name__}")
                    targ = self.heap[ptr.ptr]
                    if isinstance(targ, Int):
                        targ.data = v.data
                    elif isinstance(targ, Array):
                        if len(targ.data) >= targ.length: # type: ignore
                            self.error("sfc: array full")
                        targ.data.append(v.data) # type: ignore
                    else:
                        self.error("sfc: target is not Int or Array")
                case 'op':
                    cmd = self.stack.pop()
                    if not isinstance(cmd, Num):
                        self.error(f"op: expected num, got {type(cmd).__name__}")
                    match cmd.data:
                        case 0:
                            ptr = self.stack.pop()
                            if not isinstance(ptr, Ptr):
                                self.error(f"op: expected ptr, got {type(ptr).__name__}")
                            v = self.heap[ptr.ptr]
                            if isinstance(v, Array):
                                print(''.join(map(chr, v.data)), end='')
                            elif isinstance(v, Int):
                                print(chr(v.data), end='')
                        case 1:
                            ch = sys.stdin.read(1)
                            if ch == "":
                                self.error("op 1: end of input")
                            self.stack.append(Num(ord(ch)))
                        case 2:
                            ch = sys.stdin.read(1)
                            if ch == "":
                                self.error("op 2: end of input")
                            if ch.isdigit():
                                self.stack.append(Num(int(ch)))
                            else:
                                self.stack.append(nil)
                        case 3:
                            base = self.stack.pop()
                            if not isinstance(base, Num):
                                self.error(f"op 3: expected Num base, got {type(base).__name__}")
                            if base.data < 2 or base.data > 10:
                                self.error(f"op 3: base must be 2..10, got {base.data}")
                            ptr = self.stack.pop()
                            if not isinstance(ptr, Ptr):
                                self.error(f"op 3: expected Ptr, got {type(ptr).__name__}")
                            if ptr.ptr >= len(self.heap):
                                self.error(f"op 3: heap index {ptr.ptr} out of range")
                            src = self.heap[ptr.ptr]
                            if not isinstance(src, Int):
                                self.error(f"op 3: target is not Int")
                            if src.data is None:
                                self.error("op 3: Int has no value")

                            n = src.data
                            if n == 0:
                                digits = [48]
                            else:
                                negative = n < 0
                                v = -n if negative else n
                                digits = []
                                while v > 0:
                                    digits.append(48 + v % base.data)
                                    v //= base.data
                                if negative:
                                    digits.append(45)
                                digits.reverse()

                            arr = Array()
                            arr.length = len(digits)
                            arr.data = digits
                            self.heap.append(arr)
                        case _:
                            self.error(f"op: unknown opcode {cmd.data}")
                case 'loa':
                    if not args:
                        self.error("loa: missing ptr")
                    ptr = args[0]
                    if not isinstance(ptr, Ptr):
                        self.error(f"loa: expected Ptr, got {type(ptr).__name__}")
                    if ptr.ptr >= len(self.heap):
                        self.error(f"loa: heap index {ptr.ptr} out of range")
                    targ = self.heap[ptr.ptr]
                    if isinstance(targ, Int):
                        if targ.data is None:
                            self.error("loa: Int has no value")
                        self.stack.append(Num(targ.data))
                    elif isinstance(targ, Array):
                        self.stack.append(Ptr(ptr.ptr))
                    else:
                        self.error(f"loa: unknown heap type {type(targ).__name__}")
                case 'lat':
                    ptr = self.stack.pop()
                    if not isinstance(ptr, Ptr):
                        self.error(f"lat: expected Ptr, got {type(ptr).__name__}")
                    if ptr.ptr >= len(self.heap):
                        self.error(f"lat: heap index {ptr.ptr} out of range")
                    targ = self.heap[ptr.ptr]
                    if isinstance(targ, Int):
                        if targ.data is None:
                            self.error("lat: Int has no value")
                        self.stack.append(Num(targ.data))
                    elif isinstance(targ, Array):
                        self.stack.append(Ptr(ptr.ptr))
                    else:
                        self.error(f"lat: unknown heap type {type(targ).__name__}")
                case 'fre':
                    if not args:
                        self.error("fre: missing ptr")
                    ptr = args[0]
                    if not isinstance(ptr, Ptr):
                        self.error(f"fre: expected Ptr, got {type(ptr).__name__}")
                    if ptr.ptr >= len(self.heap):
                        self.error(f"fre: heap index {ptr.ptr} out of range")
                    del self.heap[ptr.ptr]

                case 'add':
                    a = self.stack.pop()
                    b = self.stack.pop()
                    if not isinstance(a, Num) or not isinstance(b, Num):
                        self.error("add: expected Num, Num")
                    self.stack.append(Num(a.data + b.data))
                case 'sub':
                    a = self.stack.pop()
                    b = self.stack.pop()
                    if not isinstance(a, Num) or not isinstance(b, Num):
                        self.error("sub: expected Num, Num")
                    self.stack.append(Num(b.data - a.data))
                case 'mul':
                    a = self.stack.pop()
                    b = self.stack.pop()
                    if not isinstance(a, Num) or not isinstance(b, Num):
                        self.error("mul: expected Num, Num")
                    self.stack.append(Num(a.data * b.data))
                case 'div':
                    a = self.stack.pop()
                    b = self.stack.pop()
                    if not isinstance(a, Num) or not isinstance(b, Num):
                        self.error("div: expected Num, Num")
                    if a.data == 0:
                        self.error("div: division by zero")
                    self.stack.append(Num(b.data // a.data))
                case 'mod':
                    a = self.stack.pop()
                    b = self.stack.pop()
                    if not isinstance(a, Num) or not isinstance(b, Num):
                        self.error("mod: expected Num, Num")
                    if a.data == 0:
                        self.error("mod: division by zero")
                    self.stack.append(Num(b.data % a.data))
                case 'ptr':
                    n = self.stack.pop()
                    if not isinstance(n, Num):
                        self.error(f"ptr: expected Num, got {type(n).__name__}")
                    if n.data < 0:
                        self.error(f"ptr: negative address {n.data}")
                    self.stack.append(Ptr(n.data))
                case 'gto':
                    if not args:
                        self.error("gto: missing label")
                    target = args[0]
                    if not isinstance(target, Num):
                        self.error(f"gto: expected Num, got {type(target).__name__}")
                    if target.data not in self.labels:
                        self.error(f"gto: unknown label {target.data}")
                    self.pc = self.labels[target.data]

                case 'giz':
                    if not args:
                        self.error("giz: missing label")
                    target = args[0]
                    if not isinstance(target, Num):
                        self.error(f"giz: expected Num, got {type(target).__name__}")
                    if target.data not in self.labels:
                        self.error(f"giz: unknown label {target.data}")
                    cond = self.stack.pop()
                    if not isinstance(cond, Num):
                        self.error(f"giz: expected Num cond, got {type(cond).__name__}")
                    if cond.data == 0:
                        self.pc = self.labels[target.data]

                case 'gin':
                    if not args:
                        self.error("gin: missing label")
                    target = args[0]
                    if not isinstance(target, Num):
                        self.error(f"gin: expected Num, got {type(target).__name__}")
                    if target.data not in self.labels:
                        self.error(f"gin: unknown label {target.data}")
                    if self.stack and self.stack[-1] is nil:
                        self.stack.pop()
                        self.pc = self.labels[target.data]
                case 'eq':
                    a = self.stack.pop()
                    b = self.stack.pop()
                    if not isinstance(a, Num) or not isinstance(b, Num):
                        self.error("eq: expected Num, Num")
                    self.stack.append(Num(1 if a.data == b.data else 0))
                case _:
                    self.error(f"unknown command: {head.command}")

    def run(self):
        self.parse()
        self.execute()

if __name__ == '__main__':
    fname = sys.argv[1]
    with open(fname, 'r', encoding='utf-8') as f:
        kpca = Kpcaaeths(f.read())
        kpca.run()