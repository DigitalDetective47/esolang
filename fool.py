from __future__ import annotations

from collections.abc import Callable
from sys import argv, stderr
from typing import Final


class FoolFunc(Callable):
    def __init__(self, func: Callable[[int], int], /) -> None:
        self.func = func

    def __add__(self, other: FoolFunc, /) -> FoolFunc:
        return FoolFunc(lambda x: self.func(x) or other.func(x))

    def __call__(self, value: int, /) -> int:
        return self.func(value)

    def __mul__(self, other: FoolFunc, /) -> FoolFunc:
        return FoolFunc(lambda x: other.func(self.func(x)))

    def __sub__(self, other: FoolFunc) -> FoolFunc:
        return FoolFunc(lambda x: self.func(x) and other.func(x))


tape: Final[list[int]] = [0]
pointer_location: int = 0


def shift_left(value: int, /) -> int:
    global pointer_location
    if pointer_location == 0:
        tape.insert(0, 0)
    else:
        pointer_location -= 1
    return value


def shift_right(value: int, /) -> int:
    global pointer_location
    pointer_location += 1
    if pointer_location == len(tape):
        tape.append(0)
    return value


def star(value: int, /) -> int:
    result = value ^ tape[pointer_location]
    tape[pointer_location] = result
    return result


function_table: Final[dict[str, FoolFunc]] = {
    "*": FoolFunc(star),
    "<": FoolFunc(shift_left),
    ">": FoolFunc(shift_right),
}

if len(argv) < 2:
    print(
        "Pass the location of the script to run as a command-line argument.",
        file=stderr,
    )
elif len(argv) > 2:
    print("Unknown command-line arguments passed.", file=stderr)
else:

    try:
        with open(argv[1]) as source:
            statements = source.readlines()
        for line_number, line_contents in tuple(enumerate(statements))[:-1]:
            statements[line_number] = line_contents[:-1]

        current_function_name: str
        function_code: str
        function_names: Final[list[str]] = []
        num_colons: int
        unclosed_parens: int
        for line_number, statement in enumerate(statements, 1):
            num_colons = statement.count(":")
            if num_colons > 1:
                raise SyntaxError(f"Multiple colons found on line {line_number}.")
            elif num_colons == 0:
                raise SyntaxError(f"Missing colon on line {line_number}.")
            current_function_name, function_code = statement.split(":", 1)
            if not frozenset(current_function_name).isdisjoint(frozenset("&().|")):
                raise SyntaxError(f"Invalid function name on line {line_number}")
            elif current_function_name in frozenset("*<>"):
                raise SyntaxError(
                    f"Attempted to overwrite default function {current_function_name} on line {line_number}."
                )
            try:
                raise SyntaxError(
                    f"Found multiple definitions for function {current_function_name}. (First 2 occurrences on lines {function_names.index(current_function_name)} & {line_number}.)"
                )
            except ValueError:
                # Means function name not in list, this should be raised each time.
                unclosed_parens = 0
                for char in statement:
                    if char == "(":
                        unclosed_parens += 1
                    elif char == ")":
                        unclosed_parens -= 1
                    if unclosed_parens < 0:
                        raise SyntaxError(
                            f"Unmatched parenthesis on line {line_number}."
                        )
                if unclosed_parens != 0:
                    raise SyntaxError(f"Unmatched parenthesis on line {line_number}.")
                function_names.append(current_function_name)
                function_table[current_function_name] = FoolFunc(lambda: None)
        if "main" not in function_names:
            raise SyntaxError("main function not found.")

        function_definition_expression: str
        is_function_name: bool
        for line_number, statement in enumerate(statements, 1):
            current_function_name, function_code = statement.split(":", 1)
            function_definition_expression = ""
            is_function_name = True
            for token in reversed(
                function_code.replace("&", ": - :")
                .replace("(", "(:")
                .replace(")", ":)")
                .replace(".", ": * :")
                .replace("|", ": + :")
                .split(":")
            ):
                if token == "(":
                    function_definition_expression += ")"
                elif token == ")":
                    function_definition_expression += "("
                else:
                    if is_function_name:
                        if token in function_table:
                            function_definition_expression += (
                                f"function_table[{token!r}]"
                            )
                        else:
                            raise SyntaxError(
                                f"Unrecognized function {token} on line {line_number}."
                            )
                    elif token in frozenset({" * ", " + ", " - "}):
                        function_definition_expression += token
                    else:
                        raise SyntaxError(f"Invalid syntax on line {line_number}")
                    is_function_name = not is_function_name
            function_table[current_function_name].func = eval(
                function_definition_expression
            )
    except OSError:
        print("There was an issue accessing the file you requested.", file=stderr)
    except SyntaxError as e:
        print(e, file=stderr)
    else:
        main_return: Final[int] = function_table["main"](1)
        print(f"...{''.join(map(str, tape))}... [{main_return}]")
