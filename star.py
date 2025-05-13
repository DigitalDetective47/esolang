from __future__ import annotations

from abc import ABC, abstractmethod
from itertools import product
from sys import argv, stderr
from typing import Any, Final, Optional

variable_banned_characters: Final[frozenset[str]] = frozenset("&*;=")


class Pointer:
    __slots__ = ("_deref_time", "_target")

    _deref_time: int
    _target: Pointer

    def __init__(self, target: Optional[Pointer] = None) -> None:
        """
        Create a new Pointer pointing at the specified target.
        If no target is specified, the new pointer will point at itself.
        """
        if target is None:
            target = self
        self._target = target
        self.dereference()

    def dereference(self) -> Pointer:
        global current_line
        self._deref_time = current_line
        return self._target

    def set_target(self, new_target: Pointer, /) -> None:
        self._target = new_target

    @property
    def last_dereferenced(self) -> int:
        return self._deref_time


class Expression(ABC):
    """An expression that resolves a pointer."""

    __slots__ = ()

    @abstractmethod
    def __call__(self) -> Pointer:
        pass


class VariableName(Expression):
    __slots__ = ("_name",)

    _name: str

    def __init__(self, name: str) -> None:
        if any(char in name for char in variable_banned_characters):
            raise ValueError("Illegal variable name")
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def __call__(self) -> Pointer:
        global variables
        return variables[self.name]

    def __eq__(self, other: Any, /) -> bool:
        return isinstance(other, VariableName) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r})"

    def __str__(self) -> str:
        return self.name


class Dereference(Expression):
    __slots__ = ("_subexp",)

    _subexp: Expression

    def __init__(self, sub_expression: Expression) -> None:
        self._subexp = sub_expression

    @property
    def sub_expression(self) -> Expression:
        return self._subexp

    def __call__(self) -> Pointer:
        return self.sub_expression().dereference()

    def __eq__(self, other: Any, /) -> bool:
        return (
            isinstance(other, Dereference)
            and self.sub_expression == other.sub_expression
        )

    def __hash__(self) -> int:
        return (3 * hash(self.sub_expression) + 5) % (1 << 64)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.sub_expression!r})"

    def __str__(self) -> str:
        return f"*{self.sub_expression}"


class Reference(Expression):
    __slots__ = ("_subexp",)

    _subexp: Expression

    def __init__(self, sub_expression: Expression) -> None:
        self._subexp = sub_expression

    @property
    def sub_expression(self) -> Expression:
        return self._subexp

    def __call__(self) -> Pointer:
        return Pointer(self.sub_expression())

    def __eq__(self, other: Any, /) -> bool:
        return (
            isinstance(other, Reference) and self.sub_expression == other.sub_expression
        )

    def __hash__(self) -> int:
        return (7 * hash(self.sub_expression) - 3) % (1 << 64)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.sub_expression!r})"

    def __str__(self) -> str:
        return f"&{self.sub_expression}"


class Statement(ABC):
    """A statement within a *lang program."""

    __slots__ = ()

    @abstractmethod
    def __call__(self) -> None:
        pass


class Blank(Statement):
    __slots__ = ()

    def __call__(self) -> None:
        pass

    def __eq__(self, other: Any, /) -> bool:
        return isinstance(other, Blank)

    def __hash__(self) -> int:
        return 0

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"

    def __str__(self) -> str:
        return ";"


class New(Statement):
    __slots__ = "_name"

    _name: str

    def __init__(self, name: str) -> None:
        VariableName(name)
        self._name = name

    @property
    def name(self) -> str:
        return self._name

    def __call__(self) -> None:
        global variables
        variables[self.name] = Pointer()

    def __eq__(self, other: Any, /) -> bool:
        return isinstance(other, New) and self.name == other.name

    def __hash__(self) -> int:
        return hash(self.name)

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r})"

    def __str__(self) -> str:
        return f"new *{self.name};"


class Assign(Statement):
    __slots__ = ("_derefs", "_exp", "_name")

    _derefs: int
    _exp: Expression
    _name: str

    def __init__(
        self, name: str, dereference_count: int, expression: Expression
    ) -> None:
        VariableName(name)
        self._derefs = dereference_count
        self._exp = expression
        self._name = name

    @property
    def dereference_count(self) -> int:
        """The number of dereferences on the left side of the assignment."""
        return self._derefs

    @property
    def expression(self) -> Expression:
        """The expression to be assigned."""
        return self._exp

    @property
    def name(self) -> str:
        """The variable name on the left side of the assignment."""
        return self._name

    def __call__(self) -> None:
        global variables
        if self.dereference_count == 0:
            variables[self.name] = self.expression()
        else:
            parent: Pointer = variables[self.name]
            for _ in range(1, self.dereference_count):
                parent = parent.dereference()
            parent.set_target(self.expression())

    def __eq__(self, other: Any, /) -> bool:
        return (
            isinstance(other, Assign)
            and self.dereference_count == other.dereference_count
            and self.expression == other.expression
            and self.name == other.name
        )

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.name!r}, {self.dereference_count!r}, {self.expression!r})"

    def __str__(self) -> str:
        return f"{'*' * self.dereference_count}{self.name} = {self.expression};"


class Back(Statement):
    __slots__ = ("_exp",)

    _exp: Expression

    def __init__(self, expression: Expression) -> None:
        self._exp = expression

    @property
    def expression(self) -> Expression:
        return self._exp

    def __call__(self) -> None:
        global current_line
        current_line = self.expression().last_dereferenced

    def __eq__(self, other: Any, /) -> bool:
        return isinstance(other, Back) and self.expression == other.expression

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.expression!r})"

    def __str__(self) -> str:
        return f"back {self.expression};"


class Out(Statement):
    __slots__ = ("_exp",)

    _exp: Expression

    def __init__(self, expression: Expression) -> None:
        self._exp = expression

    @property
    def expression(self) -> Expression:
        return self._exp

    def __call__(self) -> None:
        print(chr((self.expression().last_dereferenced + 1) % 128), end="")

    def __eq__(self, other: Any, /) -> bool:
        return isinstance(other, Out) and self.expression == other.expression

    __hash__ = None  # type: ignore[assignment]

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.expression!r})"

    def __str__(self) -> str:
        return f"out {self.expression};"


def parse_expression(text: str) -> Expression:
    name: str = text.lstrip("&*")
    expression: Expression = VariableName(name)
    for modifier in reversed(text[: -len(name)]):
        match modifier:
            case "&":
                expression = Reference(expression)
            case "*":
                expression = Dereference(expression)
    return expression


if len(argv) < 2:
    print(
        "Pass the location of the script to run as a command-line argument.",
        file=stderr,
    )
    quit(1)
elif len(argv) > 2:
    print("Unknown command-line arguments passed.", file=stderr)
    quit(1)

program: list[Statement] = []
try:
    with open(argv[1]) as source:
        for ln, line in enumerate(source, 1):
            line = line.removesuffix("\n")
            if not line:
                program.append(Blank())
                continue
            fragments: list[str] = line.split(";", 1)
            if len(fragments) < 2:
                raise SyntaxError(f"Missing semicolon on line {ln}")
            line = fragments[0]
            if not line:
                program.append(Blank())
                continue
            line.lstrip()
            if " = " in line:
                left, right = line.split(" = ", 1)
                dereference_count: int = left.count("*")
                name: str = left.lstrip("*")
                try:
                    program.append(
                        Assign(name, dereference_count, parse_expression(right))
                    )
                except ValueError:
                    raise SyntaxError(f"Illegal expression on line {ln}")
            elif line.startswith("new *"):
                try:
                    program.append(New(line.removeprefix("new *")))
                except ValueError:
                    raise NameError(f"Illegal variable name on line {ln}")
            elif line.startswith("back "):
                try:
                    program.append(Back(parse_expression(line.removeprefix("back "))))
                except ValueError:
                    raise NameError(f"Illegal expression name on line {ln}")
            elif line.startswith("out "):
                try:
                    program.append(Out(parse_expression(line.removeprefix("out "))))
                except ValueError:
                    raise NameError(f"Illegal expression name on line {ln}")
except OSError:
    print("There was an issue accessing the file you requested.", file=stderr)
    quit(1)
except (NameError, SyntaxError) as e:
    print(e, file=stderr)
    quit(1)
else:
    current_line: int = 0
    variables: dict[str, Pointer] = {}
    assert not any(
        char in name
        for name, char in product(variables.keys(), variable_banned_characters)
    )
    while current_line < len(program):
        try:
            program[current_line]()
        except KeyError as e:
            print(f"Undefined variable {e} referenced on line {current_line + 1}")
            quit(1)
        current_line += 1
