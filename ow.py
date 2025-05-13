from collections.abc import Callable, Iterable
from fractions import Fraction as num
from functools import partial
from itertools import repeat
from math import ceil
from random import randrange
from sys import argv, stderr
from types import LambdaType
from typing import Any, Final, SupportsIndex, TypeAlias, TypeVar, overload

from typing_extensions import Self


_T = TypeVar("_T", bool, num, str, type)


class ProgramRaisable(Exception):
    __slots__ = ("desc", "name")

    def __init__(self, name: str, desc: str) -> None:
        self.desc = desc
        self.name = name


class ProgramError(ProgramRaisable):
    """An error was found within the ONE WAY program."""


class ProgramException(ProgramRaisable, RuntimeError):
    """An exception occured within the ONE WAY program."""


value: TypeAlias = bool | num | str | type
stack: TypeAlias = list[value]
command: TypeAlias = Callable[[stack], None]

primary: Final[stack] = []
secondary: Final[stack] = []


def _get(stack_: stack, t: type[_T]) -> _T:
    try:
        x: Final[_T] = stack_.pop()
    except IndexError:
        raise ProgramException("PopException", "cannot pop from empty stack")
    if isinstance(x, t):
        return x
    else:
        raise ProgramException(
            "TypeException",
            f"recieved value of type {_repr(type(x))} (expected {_repr(t)})",
        )


add: Final[command] = lambda stack_: stack_.append(
    _get(stack_, num) + _get(stack_, num)
)


and_: Final[command] = lambda stack_: stack_.append(
    _get(stack_, bool) and _get(stack_, bool)
)


def chr_(stack_: stack) -> None:
    x: Final[num] = _get(stack_, num)
    if x.denominator != 1 or not 0 <= x.numerator <= 1114111:
        raise ProgramException(
            "UnicodeException", f'"{_repr(x)}" is not a valid Unicode code point'
        )
    else:
        stack_.append(chr(x.numerator))


concat: Final[command] = lambda stack_: stack_.append(
    _get(stack_, str) + _get(stack_, str)
)


def divide(stack_: stack) -> None:
    try:
        stack_.append(_get(stack_, num) / _get(stack_, num))
    except ZeroDivisionError:
        raise ProgramException("ZeroDivisionException", "cannot divide by 0")


def drop(stack_: stack) -> None:
    _get(stack_, object)


dupe: Final[command] = lambda stack_: stack_.extend(repeat(_get(stack_, object), 2))


def equal(stack_: stack) -> None:
    a: Final[Any] = _get(stack_, object)
    b: Final[Any] = _get(stack_, object)
    stack_.append(type(a) == type(b) and a == b)


def _eval(x: str) -> value:
    match x:
        case "bool":
            return bool
        case "false":
            return False
        case "num":
            return num
        case "str":
            return str
        case "true":
            return True
        case "type":
            return type
        case _:
            if x.startswith('"'):
                i: int = 1
                r: str = ""
                while i < len(x):
                    if x[i] == "\\":
                        try:
                            match x[i + 1]:
                                case "n":
                                    r += "\n"
                                case "\\":
                                    r += "\\"
                                case _:
                                    raise SyntaxError
                        except IndexError:
                            raise SyntaxError
                        else:
                            i += 2
                    else:
                        r += x[i]
                        i += 1
                return r
            else:
                s: bool = False
                for i, c in enumerate(x.removeprefix("-")):
                    if c == "." or c == "/":
                        if s:
                            raise SyntaxError
                        else:
                            s = True
                    elif not 48 <= ord(c) <= 57:
                        raise SyntaxError
                try:
                    return num(x)
                except (ValueError, ZeroDivisionError):
                    raise SyntaxError


def eval_(stack_: stack) -> None:
    x: Final[str] = _get(stack_, str)
    try:
        stack_.append(_eval(x))
    except SyntaxError:
        raise ProgramException("LiteralException", f'"{x}" is not a valid literal')


flip: Final[command] = lambda stack_: secondary.append(_get(primary, object))


greater: Final[command] = lambda stack_: stack_.append(
    _get(stack_, num) > _get(stack_, num)
)


input_: Final[command] = lambda stack_: stack_.append(input())


len_: Final[command] = lambda stack_: stack_.append(num(len(_get(stack_, str))))


less: Final[command] = lambda stack_: stack_.append(
    _get(stack_, num) < _get(stack_, num)
)


multiply: Final[command] = lambda stack_: stack_.append(
    _get(stack_, num) * _get(stack_, num)
)


not_: Final[command] = lambda stack_: stack_.append(not _get(stack_, bool))


or_: Final[command] = lambda stack_: stack_.append(
    _get(stack_, bool) or _get(stack_, bool)
)


def ord_(stack_: stack) -> None:
    x: Final[str] = _get(stack_, str)
    if len(x) == 1:
        stack_.append(num(ord(x)))
    else:
        raise ProgramException(
            "LengthException", f"recieved string of length {len(x)} (expected 1)"
        )


print_: Final[command] = lambda stack_: print(_get(stack_, str), end="")


push: Final[Callable[[value, stack], None]] = lambda value_, stack_: stack_.append(
    value_
)


def random(stack_: stack) -> None:
    a: Final[num] = _get(stack_, num)
    b: Final[num] = _get(stack_, num)
    if a == b:
        raise ProgramException("RangeException", "random range is of size 0")
    s: Final[num] = _get(stack_, num)
    if s == 0:
        raise ProgramException("StepSizeException", "step size cannot be 0")
    elif (b > a) == (s > 0):
        stack_.append(a + randrange(ceil((b - a) / s)) * s)
    else:
        raise ProgramException(
            "StepSizeException", "step size sign must match boundary difference sign"
        )


def _repr(x: value, /) -> str:
    if isinstance(x, bool):
        return "true" if x else "false"
    elif isinstance(x, num):
        return (
            str(x.numerator) if x.denominator == 1 else f"{x.numerator}/{x.denominator}"
        )
    elif isinstance(x, str):
        return '"' + x.replace("\\", "\\\\").replace("\n", "\\n")
    elif issubclass(x, num):
        return "num"
    else:
        return x.__name__


repr_: Final[command] = lambda stack_: stack_.append(_repr(_get(stack_, object)))


split: Final[command] = lambda stack_: stack_.extend(reversed(_get(stack_, str)))


subtract: Final[command] = lambda stack_: stack_.append(
    _get(stack_, num) - _get(stack_, num)
)


typeof: Final[command] = lambda stack_: stack_.append(type(_get(stack_, object)))


nop: Final[LambdaType] = lambda *args, **kwargs: None


class Block(list[command], command):
    __slots__ = ()

    def __call__(self, stack_: stack) -> None:
        for command in self:
            command(stack_)


class if_(Block):
    __slots__ = ()

    def __call__(self, stack_: stack) -> None:
        if _get(stack_, bool):
            for command in self:
                command(stack_)


class if_else(Block):
    __slots__ = ("_else_slice", "_if_slice")

    def __init__(self, _if: if_, /) -> None:
        super().__init__(_if)
        self._else_slice = slice(len(_if), None)
        self._if_slice = slice(len(_if))

    def __call__(self, stack_: stack) -> None:
        for command in self[self._if_slice if _get(stack_, bool) else self._else_slice]:
            command(stack_)


class second(Block):
    __slots__ = ()

    def append(self, __object: command) -> None:
        if isinstance(__object, second):
            raise ProgramError("SecondError", "cannot nest second blocks")
        else:
            return super().append(__object)

    def __call__(self, stack_: stack) -> None:
        for command in self:
            command(secondary)

    def extend(self, __iterable: Iterable[command]) -> None:
        if any(map(partial(isinstance, __class_or_tuple=second), __iterable)):
            raise ProgramError("SecondError", "cannot nest second blocks")
        else:
            return super().extend(__iterable)

    def __iadd__(self, __x: Iterable[command]) -> Self:
        if any(map(partial(isinstance, __class_or_tuple=second), __x)):
            raise ProgramError("SecondError", "cannot nest second blocks")
        else:
            return super().__iadd__(__x)

    def insert(self, __index: SupportsIndex, __object: command) -> None:
        if isinstance(__object, second):
            raise ProgramError("SecondError", "cannot nest second blocks")
        else:
            return super().insert(__index, __object)

    @overload
    def __setitem__(self, __i: SupportsIndex, __o: command) -> None:
        pass

    @overload
    def __setitem__(self, __s: slice, __o: Iterable[command]) -> None:
        pass

    def __setitem__(self, __i: SupportsIndex | slice, __o: command | Iterable[command]):
        if (
            any(map(partial(isinstance, __class_or_tuple=second), __o))
            if isinstance(__i, slice)
            else isinstance(__o, second)
        ):
            raise ProgramError("SecondError", "cannot nest second blocks")
        else:
            return super().__setitem__(__i, __o)


class while_(Block):
    __slots__ = ()

    def __call__(self, stack_: stack) -> None:
        while _get(stack_, bool):
            for command in self:
                command(stack_)


if len(argv) < 2:
    print(
        "Pass the location of the script to run as a command-line argument.",
        file=stderr,
    )
elif len(argv) > 2:
    print("Unknown command-line arguments passed.", file=stderr)
else:
    try:
        with open(argv[1]) as source_file:
            source: Final[list[str]] = [
                line.replace("\n", "")
                for line in source_file.readlines()
                if line != "\n"
            ]
    except OSError:
        print("There was an issue accessing the file you requested.", file=stderr)
    else:
        main: Final[Block] = Block()
        try:
            target: Block
            for line_number, line in enumerate(source, 1):
                target = main
                while line.startswith("  "):
                    try:
                        target = target[-1]
                    except (IndexError, TypeError):
                        raise ProgramError("IndentationError", "unexpected indent")
                    else:
                        line = line[2:]
                if line.startswith("push "):
                    try:
                        target.append(partial(push, _eval(line[5:])))
                    except SyntaxError:
                        raise ProgramError(
                            "LiteralError", f'"{line[5:]}" is not a valid literal'
                        )
                elif line == "else":
                    if isinstance(target[-1], if_):
                        target[-1] = if_else(target[-1])
                    else:
                        raise ProgramError("ElseError", "else must have a matching if")
                else:
                    try:
                        target.append(
                            {
                                "add": add,
                                "and": and_,
                                "chr": chr_,
                                "concat": concat,
                                "divide": divide,
                                "drop": drop,
                                "dupe": dupe,
                                "equal": equal,
                                "eval": eval_,
                                "flip": flip,
                                "greater": greater,
                                "if": if_(),
                                "input": input_,
                                "len": len_,
                                "less": less,
                                "multiply": multiply,
                                "not": not_,
                                "or": or_,
                                "ord": ord_,
                                "print": print_,
                                "random": random,
                                "repr": repr_,
                                "second": second(),
                                "split": split,
                                "subtract": subtract,
                                "typeof": typeof,
                                "while": while_(),
                            }[line]
                        )
                    except KeyError:
                        raise ProgramError(
                            "CommandError", f'"{line}" is not a recognized command'
                        )
            main(primary)
        except ProgramRaisable as e:
            print(f"{e.name}#{line_number}: {e.desc}", file=stderr)
            if isinstance(e, ProgramException):
                print("Primary stack_ [", file=stderr)
                for v in reversed(primary):
                    print("  " + _repr(v), file=stderr)
                print("]\nSecondary stack: [", file=stderr)
                for v in reversed(secondary):
                    print("  " + _repr(v), file=stderr)
                print("]", file=stderr)
